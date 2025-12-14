"""Модуль для поиска арбитражных возможностей между DMarket и другими платформами.

Используется для автоматического поиска предметов, которые можно купить
на одной площадке и продать на другой с прибылью.

Supports Dependency Injection via IDMarketAPI Protocol interface.

Документация DMarket API: https://docs.dmarket.com/v1/swagger.html
"""

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING, Any

from src.dmarket.arbitrage import (
    GAMES,
    ArbitrageTrader,
    arbitrage_boost,
    arbitrage_mid,
    arbitrage_pro,
)
from src.dmarket.dmarket_api import DMarketAPI  # Нужен для создания нового клиента
from src.dmarket.item_filters import ItemFilters
from src.dmarket.liquidity_analyzer import LiquidityAnalyzer

# Import from scanner submodules (R-2 refactoring)
from src.dmarket.scanner import ARBITRAGE_LEVELS, GAME_IDS, ScannerCache, ScannerFilters
from src.utils.rate_limiter import RateLimiter
from src.utils.sentry_breadcrumbs import add_trading_breadcrumb


if TYPE_CHECKING:
    from src.interfaces import IDMarketAPI

# Настройка логирования
logger = logging.getLogger(__name__)

# Определяем публичный интерфейс модуля
__all__ = [
    "ArbitrageScanner",
    "auto_trade_items",
    "check_user_balance",
    "find_arbitrage_opportunities_async",
    "find_multi_game_arbitrage_opportunities",
    "scan_game_for_arbitrage",
    "scan_multiple_games",
]

# Создаем ограничитель скорости запросов
rate_limiter = RateLimiter(is_authorized=True)

# GAME_IDS and ARBITRAGE_LEVELS are now imported from src.dmarket.scanner
# (R-2 refactoring: removed duplicate definitions)


class ArbitrageScanner:
    """Класс для сканирования арбитражных возможностей между DMarket и другими платформами.

    Основные возможности:
    - Поиск предметов для арбитража в разных режимах (низкий, средний, высокий профит)
    - Поддержка нескольких игр (CS:GO, Dota 2, Rust, TF2 и др.)
    - Кеширование результатов для оптимизации запросов к API
    - Автоматическая торговля найденными предметами
    - Настройка ограничений для управления рисками

    Supports Dependency Injection via IDMarketAPI Protocol interface.

    Пример использования:
        scanner = ArbitrageScanner()
        opportunities = await scanner.scan_game("csgo", "medium", 10)
    """

    def __init__(
        self,
        api_client: "IDMarketAPI | None" = None,
        enable_liquidity_filter: bool = True,
        enable_competition_filter: bool = True,
        max_competition: int = 3,
        item_filters: "ItemFilters | None" = None,
    ) -> None:
        """Инициализирует сканер арбитража.

        Args:
            api_client: DMarket API клиент (implements IDMarketAPI Protocol)
                        или None для создания нового при необходимости
            enable_liquidity_filter: Включить фильтрацию по ликвидности
            enable_competition_filter: Включить фильтрацию по конкуренции buy orders
            max_competition: Максимально допустимое количество конкурирующих ордеров
            item_filters: Фильтры предметов (ItemFilters) для blacklist/whitelist

        """
        self.api_client = api_client
        # Используем ScannerCache из scanner/ модуля (R-2 refactoring)
        self._scanner_cache = ScannerCache(ttl=300, max_size=1000)
        # Используем ScannerFilters из scanner/ модуля (R-2 refactoring)
        self._scanner_filters = ScannerFilters(item_filters)

        # Инициализация анализатора ликвидности
        self.liquidity_analyzer: LiquidityAnalyzer | None = None
        self.enable_liquidity_filter = enable_liquidity_filter

        # Параметры фильтрации по конкуренции
        self.enable_competition_filter = enable_competition_filter
        self.max_competition = max_competition  # Максимум конкурентных ордеров

        # Параметры фильтрации по ликвидности
        self.min_liquidity_score = 60  # Минимальный балл ликвидности
        self.min_sales_per_week = 5  # Минимум продаж в неделю
        self.max_time_to_sell_days = 7  # Максимальное время продажи

        # Ограничения для управления рисками
        self.min_profit = 0.5  # Минимальная прибыль в USD
        self.max_price = 50.0  # Максимальная цена покупки в USD
        self.max_trades = 5  # Максимальное количество сделок за раз

        # Статистика работы
        self.total_scans = 0
        self.total_items_found = 0
        self.successful_trades = 0
        self.total_profit = 0.0

    @property
    def cache_ttl(self) -> int:
        """Время жизни кеша (делегирует к ScannerCache)."""
        return self._scanner_cache.ttl

    @cache_ttl.setter
    def cache_ttl(self, value: int) -> None:
        """Установить время жизни кеша."""
        self._scanner_cache.ttl = value

    def _get_cached_results(self, cache_key: tuple[Any, ...]) -> list[dict[str, Any]] | None:
        """Получает результаты из кеша через ScannerCache.

        Args:
            cache_key: Ключ кеша (game, mode, price_from, price_to)

        Returns:
            Список предметов из кеша или None, если кеш устарел/отсутствует

        """
        # ScannerCache.get() сам конвертирует tuple в string через _make_key()
        return self._scanner_cache.get(cache_key)

    def _save_to_cache(self, cache_key: str | tuple[Any, ...], items: list[dict[str, Any]]) -> None:
        """Сохраняет результаты в кеш через ScannerCache.

        Args:
            cache_key: Ключ кеша
            items: Список предметов для кеширования

        """
        # ScannerCache.set() сам конвертирует tuple в string через _make_key()
        self._scanner_cache.set(cache_key, items)
        logger.debug(f"Кэшировано {len(items)} предметов для {cache_key}")

    async def get_api_client(self) -> DMarketAPI:
        """Получает экземпляр DMarketAPI клиента.

        Returns:
            Экземпляр DMarketAPI, существующий или новый

        """
        if self.api_client is None:
            # Создаем новый клиент с ключами из переменных окружения
            self.api_client = DMarketAPI(
                public_key=os.getenv("DMARKET_PUBLIC_KEY", ""),
                secret_key=os.getenv("DMARKET_SECRET_KEY", ""),
                api_url=os.getenv("DMARKET_API_URL", "https://api.dmarket.com"),
                max_retries=3,
            )

        # Инициализируем анализатор ликвидности если включен
        if self.enable_liquidity_filter and self.liquidity_analyzer is None:
            self.liquidity_analyzer = LiquidityAnalyzer(
                api_client=self.api_client,
                min_sales_per_week=self.min_sales_per_week,
                max_time_to_sell_days=self.max_time_to_sell_days,
                min_liquidity_score=self.min_liquidity_score,
            )

        return self.api_client

    async def scan_game(
        self,
        game: str,
        mode: str = "medium",
        max_items: int = 20,
        price_from: float | None = None,
        price_to: float | None = None,
    ) -> list[dict[str, Any]]:
        """Сканирует одну игру для поиска арбитражных возможностей.

        Args:
            game: Код игры (например, "csgo", "dota2", "rust", "tf2")
            mode: Режим поиска ("low", "medium", "high")
            max_items: Максимальное количество предметов в результате
            price_from: Минимальная цена предмета (в USD)
            price_to: Максимальная цена предмета (в USD)

        Returns:
            Список найденных предметов для арбитража

        """
        # Добавляем breadcrumb для отслеживания сканирования
        add_trading_breadcrumb(
            action="scan_game_started",
            game=game,
            level=mode,
            max_items=max_items,
            price_from=price_from,
            price_to=price_to,
        )

        # Создаем ключ кеша
        cache_key = (game, mode, price_from or 0, price_to or float("inf"))

        # Проверяем кеш
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            logger.debug(f"Использую кэшированные данные для {game} в режиме {mode}")
            add_trading_breadcrumb(
                action="scan_game_cache_hit",
                game=game,
                level=mode,
                cached_items=len(cached_results),
            )
            return cached_results[:max_items]

        try:
            # Увеличиваем счетчик сканирований
            self.total_scans += 1

            # Соблюдаем ограничения API
            await rate_limiter.wait_if_needed("market")

            # Пробуем два метода поиска арбитражных возможностей:
            # 1. Встроенные функции для быстрого поиска
            # 2. ArbitrageTrader для более детального поиска

            # Инициализируем items перед использованием
            items: list[Any] = []

            # Метод 1: Используем встроенные функции
            if price_from is None and price_to is None:
                try:
                    if mode == "low":
                        items = arbitrage_boost(game)
                    elif mode == "medium":
                        items = arbitrage_mid(game)
                    elif mode == "high":
                        items = arbitrage_pro(game)
                    else:
                        # По умолчанию используем средний режим
                        items = arbitrage_mid(game)

                    # Если нашли достаточно предметов, переходим к фильтрации
                    # Раньше здесь был ранний выход, но теперь мы хотим применить фильтр ликвидности ко всем предметам
                except Exception as e:
                    logger.warning(
                        f"Ошибка при использовании встроенных функций арбитража: {e!s}",
                    )
                    items = []

            # Метод 2: Используем ArbitrageTrader для более детального поиска
            try:
                # Определяем диапазоны прибыли в зависимости от режима
                min_profit = 1.0
                max_profit = 5.0

                if mode == "medium":
                    min_profit = 5.0
                    max_profit = 20.0
                elif mode == "high":
                    min_profit = 20.0
                    max_profit = 100.0

                # Определяем диапазоны цен, если не указаны явно
                current_price_from = price_from
                current_price_to = price_to

                if price_from is None and price_to is None:
                    if mode == "low":
                        current_price_to = 20.0  # До $20 для низкого режима
                    elif mode == "medium":
                        current_price_from = 20.0
                        current_price_to = 100.0  # $20-$100 для среднего режима
                    elif mode == "high":
                        current_price_from = 100.0  # От $100 для высокого режима

                # Создаем ArbitrageTrader для поиска предметов
                trader = ArbitrageTrader()

                # Получаем предметы с маркета с учетом фильтров
                items_from_trader = await trader.find_profitable_items(
                    game=game,
                    min_profit_percentage=min_profit,  # Минимальный процент прибыли
                    max_items=100,
                    min_price=current_price_from or 1.0,
                    max_price=current_price_to or 100.0,
                )

                # Фильтруем и стандартизируем формат данных
                items.extend(
                    self._standardize_items(
                        items_from_trader,
                        game,
                        min_profit,
                        max_profit,
                    ),
                )
            except Exception as e:
                logger.warning(f"Ошибка при использовании ArbitrageTrader: {e!s}")

            # Сортируем все найденные предметы по прибыльности (от большей к меньшей)
            items.sort(key=lambda x: x.get("profit", 0), reverse=True)

            # Если включен фильтр ликвидности, проверяем топ предметов
            if self.enable_liquidity_filter and self.liquidity_analyzer:
                # Берем больше предметов для проверки, так как часть отсеется
                candidates = items[: max_items * 2]

                # Фильтруем через анализатор ликвидности
                # Это добавит метрики ликвидности и удалит неликвидные предметы
                results = await self.liquidity_analyzer.filter_liquid_items(candidates, game=game)
            else:
                # Если фильтр выключен, просто берем топ по прибыли
                results = items

            # Ограничиваем количество предметов в результате
            results = results[:max_items]

            # Добавляем breadcrumb об успешном сканировании
            add_trading_breadcrumb(
                action="scan_game_completed",
                game=game,
                level=mode,
                items_found=len(results),
                liquidity_filter=self.enable_liquidity_filter,
            )

            # Сохраняем в кэш
            self._save_to_cache(cache_key, results)

            # Обновляем статистику
            self.total_items_found += len(results)

            return results
        except Exception as e:
            logger.exception(f"Ошибка при сканировании игры {game}: {e!s}")
            # Добавляем breadcrumb об ошибке
            add_trading_breadcrumb(
                action="scan_game_error",
                game=game,
                level=mode,
                error=str(e),
            )
            return []

    def _standardize_items(
        self,
        items: list[Any],
        game: str,
        min_profit: float,
        max_profit: float,
    ) -> list[dict[str, Any]]:
        """Приводит предметы к стандартному формату и фильтрует по прибыли.

        Args:
            items: Список предметов из разных источников
            game: Код игры
            min_profit: Минимальная прибыль
            max_profit: Максимальная прибыль

        Returns:
            Список стандартизированных предметов

        """
        standardized_items = []

        for item in items:
            # Проверяем, не является ли item кортежем
            if isinstance(item, tuple):
                # Преобразуем кортеж в словарь
                item_dict = {
                    "name": item[0] if len(item) > 0 else "Unknown item",
                    "buy_price": item[1] if len(item) > 1 else 0,
                    "sell_price": item[2] if len(item) > 2 else 0,
                    "profit": item[3] if len(item) > 3 else 0,
                    "profit_percentage": item[4] if len(item) > 4 else 0,
                    "itemId": "",
                    "game": game,
                }
                item = item_dict

            # Теперь безопасно используем get()
            profit = item.get("profit", 0)
            if isinstance(profit, str) and "$" in profit:
                profit = float(profit.replace("$", "").strip())

            if min_profit <= profit <= max_profit:
                # Приводим к единому формату данных
                standardized_items.append(
                    {
                        "title": item.get("name", item.get("title", "Unknown item")),
                        "price": {
                            "amount": int(item.get("buy_price", 0) * 100),
                        },  # В центах
                        "profit": profit,
                        "profit_percent": item.get("profit_percentage", 0),
                        "itemId": item.get("itemId", item.get("id", "")),
                        "game": game,
                        "fee": item.get("fee", 7.0),
                        "liquidity": item.get("liquidity", "medium"),
                    },
                )

        return standardized_items

    async def scan_multiple_games(
        self,
        games: list[str] | None = None,
        mode: str = "medium",
        max_items_per_game: int = 10,
        price_from: float | None = None,
        price_to: float | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Сканирует несколько игр для поиска арбитражных возможностей.

        Args:
            games: Список кодов игр для сканирования (по умолчанию все доступные)
            mode: Режим поиска ("low", "medium", "high")
            max_items_per_game: Максимальное количество предметов на игру
            price_from: Минимальная цена предмета (в USD)
            price_to: Максимальная цена предмета (в USD)

        Returns:
            Словарь с кодами игр и списками найденных предметов

        """
        if games is None:
            games = list(GAMES.keys())

        results: dict[str, list[dict[str, Any]]] = {}

        # Создаем задачи для параллельного сканирования игр
        tasks = []
        for game in games:
            try:
                logger.info(
                    f"Поиск арбитражных возможностей для {game} в режиме {mode}",
                )

                # Сканируем игру с указанными параметрами
                task = asyncio.create_task(
                    self.scan_game(
                        game=game,
                        mode=mode,
                        max_items=max_items_per_game,
                        price_from=price_from,
                        price_to=price_to,
                    ),
                )
                tasks.append((game, task))
            except Exception as e:
                logger.exception(f"Ошибка при создании задачи для игры {game}: {e!s}")
                results[game] = []

        # Ждём завершения всех задач
        for game, task in tasks:
            try:
                items = await task
                results[game] = items
                logger.info(f"Найдено {len(items)} предметов для {game}")
            except Exception as e:
                logger.exception(f"Ошибка при сканировании игры {game}: {e!s}")
                results[game] = []

        return results

    async def check_user_balance(self) -> dict[str, Any]:
        """Проверяет баланс пользователя DMarket с расширенной диагностикой.

        Returns:
            Словарь с балансом и детальной информацией

        """
        min_required_balance = 1.0  # Минимальный требуемый баланс в USD

        try:
            # Получаем API-клиент
            api_client = await self.get_api_client()

            # Получаем информацию о балансе через API в соответствии с документацией
            balance_response = await api_client._request(
                method="GET",
                path="/account/v1/balance",
                params={},
            )

            if not balance_response:
                logger.error("Не удалось получить баланс пользователя (пустой ответ)")
                return {
                    "has_funds": False,
                    "balance": 0.0,
                    "available_balance": 0.0,
                    "total_balance": 0.0,
                    "min_required": min_required_balance,
                    "error": True,
                    "error_message": "Пустой ответ от API при запросе баланса",
                    "display_message": "Не удалось получить баланс (пустой ответ)",
                    "diagnosis": "api_error",
                }

            # Проверяем на наличие ошибки в ответе
            # ВАЖНО: balance_response может быть False (bool) при ошибке API
            if not isinstance(balance_response, dict):
                error_message = "Не удалось получить баланс (некорректный ответ API)"
                logger.error(f"Ошибка при получении баланса: {error_message}")

                diagnosis = "unknown_error"
                display_message = "Ошибка при получении баланса"

                return {
                    "has_funds": False,
                    "balance": 0.0,
                    "available_balance": 0.0,
                    "total_balance": 0.0,
                    "min_required": min_required_balance,
                    "error": True,
                    "error_message": str(error_message),
                    "display_message": display_message,
                    "diagnosis": diagnosis,
                }

            # Теперь мы ЗНАЕМ что balance_response - это dict
            if "error" in balance_response or not balance_response.get("usd"):
                # ВАЖНО: balance_response["error"] может быть bool, не dict!
                # Поэтому берем "message" напрямую из balance_response
                error_message = balance_response.get("message", "Неизвестная ошибка")
                logger.error(f"Ошибка при получении баланса: {error_message}")

                diagnosis = "unknown_error"
                display_message = "Ошибка при получении баланса"

                # Определяем тип ошибки для диагностики
                if (
                    "unauthorized" in str(error_message).lower()
                    or "авторизации" in str(error_message).lower()
                ):
                    diagnosis = "auth_error"
                    display_message = "Ошибка авторизации: проверьте ключи API"
                elif (
                    "ключи" in str(error_message).lower() or "api key" in str(error_message).lower()
                ):
                    diagnosis = "missing_keys"
                    display_message = "Отсутствуют ключи API"
                elif (
                    "timeout" in str(error_message).lower() or "время" in str(error_message).lower()
                ):
                    diagnosis = "timeout_error"
                    display_message = "Таймаут при запросе баланса: возможны проблемы с сетью"
                elif "404" in str(error_message) or "не найден" in str(error_message).lower():
                    diagnosis = "endpoint_error"
                    display_message = "Ошибка API: эндпоинт баланса недоступен"

                return {
                    "has_funds": False,
                    "balance": 0.0,
                    "available_balance": 0.0,
                    "total_balance": 0.0,
                    "min_required": min_required_balance,
                    "error": True,
                    "error_message": str(error_message),
                    "display_message": display_message,
                    "diagnosis": diagnosis,
                }

            # Извлекаем значения баланса из полученных данных
            # DMarket API возвращает баланс в формате {"usd": {"available": 1000, "frozen": 200}}
            usd_balance = balance_response.get("usd", {})
            available_amount = usd_balance.get("available", 0)
            frozen_amount = usd_balance.get("frozen", 0)

            # Преобразуем из центов в доллары
            available_balance = float(available_amount) / 100
            frozen_balance = float(frozen_amount) / 100
            total_balance = available_balance + frozen_balance

            # Проверяем, достаточно ли средств на балансе
            has_funds = available_balance >= min_required_balance

            # Собираем дополнительную диагностическую информацию
            diagnosis = "sufficient_funds" if has_funds else "insufficient_funds"

            # Формируем сообщение для пользователя
            if has_funds:
                display_message = (
                    f"Баланс DMarket: ${available_balance:.2f} USD (достаточно для арбитража)"
                )
            else:
                # Различаем случаи полного отсутствия средств и недостаточного баланса
                if available_balance <= 0:
                    display_message = f"На балансе DMarket нет средств. Необходимо минимум ${min_required_balance:.2f} USD"
                    diagnosis = "zero_balance"
                else:
                    display_message = (
                        f"Недостаточно средств на балансе DMarket.\n"
                        f"Доступно: ${available_balance:.2f} USD\n"
                        f"Необходимо минимум: ${min_required_balance:.2f} USD"
                    )

                # Если есть заблокированные средства, указываем на это
                if frozen_balance > 0.01:  # Если различие значимое
                    display_message += f"\nЗаблокировано: ${frozen_balance:.2f} USD"
                    diagnosis = "funds_frozen"

            # Формируем финальный результат
            logger.info(
                f"Результат проверки баланса: has_funds={has_funds}, "
                f"balance=${available_balance:.2f}, available=${available_balance:.2f}, "
                f"total=${total_balance:.2f}, diagnosis={diagnosis}",
            )

            return {
                "has_funds": has_funds,
                "balance": available_balance,
                "available_balance": available_balance,
                "total_balance": total_balance,
                "frozen_balance": frozen_balance,
                "min_required": min_required_balance,
                "error": False,
                "error_message": "",
                "display_message": display_message,
                "diagnosis": diagnosis,
            }

        except Exception as e:
            logger.exception(f"Неожиданная ошибка при проверке баланса: {e!s}")
            import traceback

            logger.exception(f"Стек вызовов: {traceback.format_exc()}")

            return {
                "has_funds": False,
                "balance": 0.0,
                "available_balance": 0.0,
                "total_balance": 0.0,
                "min_required": min_required_balance,
                "error": True,
                "error_message": str(e),
                "display_message": f"Ошибка при проверке баланса: {e!s}",
                "diagnosis": "exception",
            }

    async def auto_trade_items(
        self,
        items_by_game: dict[str, list[dict[str, Any]]],
        min_profit: float | None = None,
        max_price: float | None = None,
        max_trades: int | None = None,
        risk_level: str = "medium",
    ) -> tuple[int, int, float]:
        """Автоматически торгует предметами, найденными в арбитраже.

        Args:
            items_by_game: Словарь с предметами по играм
            min_profit: Минимальная прибыль для покупки (в USD)
            max_price: Максимальная цена покупки (в USD)
            max_trades: Максимальное количество сделок за один запуск
            risk_level: Уровень риска (low, medium, high)

        Returns:
            Кортеж (количество покупок, количество продаж, общая прибыль)

        """
        # Используем значения по умолчанию, если не указаны
        min_profit = min_profit or self.min_profit
        max_price = max_price or self.max_price
        max_trades = max_trades or self.max_trades

        # Получаем API-клиент
        api_client = await self.get_api_client()

        # Проверяем баланс пользователя
        balance_data = await self.check_user_balance()
        balance = balance_data.get("balance", 0.0)
        has_funds = balance_data.get("has_funds", False)

        if not has_funds or balance < 1.0:
            logger.warning(
                f"Автоторговля невозможна: недостаточно средств (${balance:.2f})",
            )
            return 0, 0, 0.0

        # Настройки управления рисками в зависимости от уровня
        if risk_level == "low":
            max_trades = min(max_trades, 2)  # Не более 2 сделок
            max_price = min(max_price, 20.0)  # Не более $20 за предмет
            min_profit = max(min_profit, 1.0)  # Минимум $1 прибыли
        elif risk_level == "medium":
            max_trades = min(max_trades, 5)  # Не более 5 сделок
            max_price = min(max_price, 50.0)  # Не более $50 за предмет
        elif risk_level == "high":
            max_price = min(max_price, balance * 0.8)  # Не более 80% баланса

        # Лимит на общую сумму торговли
        total_trade_limit = balance * 0.9  # Не использовать более 90% баланса

        logger.info(
            f"Параметры торговли: риск = {risk_level}, баланс = ${balance:.2f}, "
            f"макс. сделок = {max_trades}, макс. цена = ${max_price:.2f}",
        )

        # Создаем ArbitrageTrader для выполнения торговли
        trader = ArbitrageTrader(api_client=self.api_client)
        trader.set_trading_limits(
            max_trade_value=max_price,
            daily_limit=total_trade_limit,
        )

        purchases = 0
        sales = 0
        total_profit = 0.0
        trades_count = 0
        remaining_balance = balance

        # Собираем все предметы из всех игр в один список для сортировки
        all_items = []
        for game_code, items in items_by_game.items():
            for item in items:
                item["game"] = game_code
                all_items.append(item)

        # Сортируем по прибыльности (от большей к меньшей)
        sorted_items = sorted(
            all_items,
            key=lambda x: x.get("profit", 0),
            reverse=True,
        )

        # Проходим по отсортированному списку и торгуем предметами
        for item in sorted_items:
            # Проверяем лимиты
            if trades_count >= max_trades:
                logger.info(f"Достигнут лимит сделок ({max_trades})")
                break

            if remaining_balance < 1.0:
                logger.info("Недостаточно баланса для продолжения торговли")
                break

            # Проверяем, соответствует ли предмет критериям
            buy_price = item.get("price", {}).get("amount", 0) / 100.0  # Цена в USD
            profit = item.get("profit", 0)

            if buy_price > max_price:
                logger.debug(
                    f"Предмет '{item.get('title', '')}' пропущен: цена ${buy_price:.2f} выше лимита ${max_price:.2f}",
                )
                continue

            if profit < min_profit:
                logger.debug(
                    f"Предмет '{item.get('title', '')}' пропущен: прибыль ${profit:.2f} ниже минимальной ${min_profit:.2f}",
                )
                continue

            if buy_price > remaining_balance:
                logger.debug(
                    f"Предмет '{item.get('title', '')}' пропущен: цена ${buy_price:.2f} выше остатка баланса ${remaining_balance:.2f}",
                )
                continue

            # Пробуем купить предмет
            try:
                # Получаем текущую цену и проверяем, не изменилась ли она
                updated_item = await self._get_current_item_data(
                    item_id=item.get("itemId", ""),
                    game=item.get("game", "csgo"),
                    api_client=api_client,
                )

                if not updated_item:
                    logger.warning(
                        f"Предмет '{item.get('title', '')}' недоступен (не найден)",
                    )
                    continue

                current_price = updated_item.get("price", buy_price)
                if current_price > buy_price * 1.05:  # Цена выросла более чем на 5%
                    logger.warning(
                        f"Предмет '{item.get('title', '')}' пропущен: цена выросла с ${buy_price:.2f} до ${current_price:.2f}",
                    )
                    continue

                # Покупаем предмет
                purchase_result = await self._purchase_item(
                    item_id=item.get("itemId", ""),
                    max_price=buy_price * 1.02,  # Допускаем небольшое повышение цены
                    api_client=api_client,
                )

                if purchase_result.get("success", False):
                    purchases += 1
                    remaining_balance -= buy_price
                    logger.info(
                        f"Успешно куплен предмет '{item.get('title', '')}' за ${buy_price:.2f}",
                    )

                    # Пробуем сразу выставить на продажу
                    sell_price = buy_price + profit
                    sell_result = await self._list_item_for_sale(
                        item_id=purchase_result.get("new_item_id", ""),
                        price=sell_price,
                        api_client=api_client,
                    )

                    if sell_result.get("success", False):
                        sales += 1
                        total_profit += profit
                        logger.info(
                            f"Предмет '{item.get('title', '')}' выставлен на продажу за ${sell_price:.2f} (прибыль ${profit:.2f})",
                        )
                    else:
                        logger.warning(
                            f"Не удалось выставить предмет '{item.get('title', '')}' на продажу: {sell_result.get('error', 'Неизвестная ошибка')}",
                        )
                else:
                    logger.warning(
                        f"Не удалось купить предмет '{item.get('title', '')}': {purchase_result.get('error', 'Неизвестная ошибка')}",
                    )

                # Увеличиваем счетчик сделок независимо от результата
                trades_count += 1

                # Делаем небольшую паузу между сделками
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.exception(
                    f"Ошибка при торговле предметом '{item.get('title', '')}': {e!s}",
                )
                trades_count += 1

        # Обновляем статистику
        self.successful_trades += sales
        self.total_profit += total_profit

        # Возвращаем результаты торговли
        logger.info(
            f"Итоги торговли: куплено {purchases}, выставлено на продажу {sales}, ожидаемая прибыль ${total_profit:.2f}",
        )
        return purchases, sales, total_profit

    async def _get_current_item_data(
        self,
        item_id: str,
        game: str,
        api_client: DMarketAPI,
    ) -> dict[str, Any] | None:
        """Получает текущие данные о предмете через API.

        Args:
            item_id: ID предмета
            game: Код игры
            api_client: API-клиент

        Returns:
            Словарь с данными о предмете или None в случае ошибки

        """
        try:
            # Запрос на получение информации о предмете через API
            result = await api_client._request(
                method="GET",
                path="/exchange/v1/market/items",
                params={
                    "itemId": item_id,
                    "gameId": game,
                },
            )

            if not result or "objects" not in result or not result["objects"]:
                return None

            # Берем первый предмет из результатов
            item_data = result["objects"][0]

            # Преобразуем цену из центов в доллары
            price_data = item_data.get("price", {})
            price = float(price_data.get("USD", 0)) / 100

            return {
                "itemId": item_id,
                "price": price,
                "title": item_data.get("title", ""),
                "game": game,
            }
        except Exception as e:
            logger.exception(f"Ошибка при получении данных о предмете {item_id}: {e}")
            return None

    async def _purchase_item(
        self,
        item_id: str,
        max_price: float,
        api_client: DMarketAPI,
    ) -> dict[str, Any]:
        """Покупает предмет через API.

        Args:
            item_id: ID предмета
            max_price: Максимальная цена покупки (в USD)
            api_client: API-клиент

        Returns:
            Словарь с результатом покупки

        """
        try:
            # Покупаем предмет через API согласно документации
            purchase_data = await api_client._request(
                method="POST",
                path="/exchange/v1/offers/create",
                data={
                    "targets": [
                        {
                            "itemId": item_id,
                            "price": {
                                "amount": int(max_price * 100),  # Конвертируем в центы
                                "currency": "USD",
                            },
                        },
                    ],
                },
            )

            if "error" in purchase_data:
                return {
                    "success": False,
                    "error": purchase_data.get("error", {}).get(
                        "message",
                        "Неизвестная ошибка при покупке",
                    ),
                }

            # Успешная покупка - получаем ID нового предмета в инвентаре
            if purchase_data.get("items"):
                new_item_id = purchase_data["items"][0].get("itemId", "")
                return {
                    "success": True,
                    "new_item_id": new_item_id,
                    "price": max_price,
                    "purchase_data": purchase_data,
                }

            return {
                "success": False,
                "error": "Не удалось получить ID купленного предмета",
            }
        except Exception as e:
            logger.exception(f"Ошибка при покупке предмета {item_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _list_item_for_sale(
        self,
        item_id: str,
        price: float,
        api_client: DMarketAPI,
    ) -> dict[str, Any]:
        """Выставляет предмет на продажу через API.

        Args:
            item_id: ID предмета
            price: Цена продажи (в USD)
            api_client: API-клиент

        Returns:
            Словарь с результатом выставления на продажу

        """
        try:
            # Выставляем предмет на продажу через API согласно документации
            sell_data = await api_client._request(
                method="POST",
                path="/exchange/v1/user/items/sell",
                data={
                    "itemId": item_id,
                    "price": {
                        "amount": int(price * 100),  # Конвертируем в центы
                        "currency": "USD",
                    },
                },
            )

            if "error" in sell_data:
                return {
                    "success": False,
                    "error": sell_data.get("error", {}).get(
                        "message",
                        "Неизвестная ошибка при выставлении на продажу",
                    ),
                }

            return {
                "success": True,
                "price": price,
                "sell_data": sell_data,
            }
        except Exception as e:
            logger.exception(
                f"Ошибка при выставлении предмета {item_id} на продажу: {e}",
            )
            return {"success": False, "error": str(e)}

    def get_level_config(self, level: str) -> dict[str, Any]:
        """Получить конфигурацию для уровня арбитража.

        Args:
            level: Название уровня (boost, standard, high и т.д.)

        Returns:
            Словарь с конфигурацией уровня

        Raises:
            ValueError: Если уровень не существует

        """
        if level not in ARBITRAGE_LEVELS:
            raise ValueError(f"Неизвестный уровень арбитража: {level}")
        return ARBITRAGE_LEVELS[level]

    # _get_from_cache удалён - используем ScannerCache через _scanner_cache (R-2)

    async def scan_level(
        self,
        level: str,
        game: str = "csgo",
        max_results: int = 10,
        use_cache: bool = True,
        use_aggregated_api: bool = True,
    ) -> list[dict[str, Any]]:
        """Сканировать возможности арбитража для конкретного уровня.

        Args:
            level: Уровень арбитража (boost, standard, high)
            game: Код игры
            max_results: Максимальное количество результатов
            use_cache: Использовать кеширование
            use_aggregated_api: Использовать API v1.1.0 aggregated-prices для оптимизации

        Returns:
            Список возможностей арбитража

        """
        config = self.get_level_config(level)
        cache_key = f"scan_level_{game}_{level}"

        # Проверка поддерживаемых игр
        if game not in GAME_IDS:
            raise ValueError(f"Игра '{game}' не поддерживается")

        if use_cache:
            # Используем ScannerCache через _scanner_cache (R-2 refactoring)
            cached = self._scanner_cache.get(cache_key)
            if cached is not None:
                return cached[:max_results]

        # Получаем game_id для API
        game_id = GAME_IDS.get(game, game)
        price_from, price_to = config["price_range"]

        # Конвертируем цены из USD в центы
        price_from_cents = int(price_from * 100)
        price_to_cents = int(price_to * 100)

        # Вызываем API напрямую
        items_response = await self.api_client.get_market_items(
            game=game_id,
            price_from=price_from_cents,
            price_to=price_to_cents,
            limit=max_results * 3,  # Берем больше, т.к. часть отфильтруется
        )

        items = items_response.get("objects", [])

        # Применяем пользовательские фильтры (R-2 refactoring)
        items = self._scanner_filters.apply_filters(items, game)

        # Используем aggregated-prices для эффективного получения данных о ликвидности
        if use_aggregated_api and items:
            try:
                # Получаем названия всех предметов
                titles = [item.get("title") for item in items if item.get("title")]

                # Получаем агрегированные данные одним запросом
                aggregated = await self.api_client.get_aggregated_prices_bulk(
                    game=game,
                    titles=titles[:100],  # Ограничение API
                    limit=len(titles[:100]),
                )

                if aggregated and "aggregatedPrices" in aggregated:
                    # Создаем карту ликвидности: title -> liquidity_data
                    liquidity_map = {}
                    for price_data in aggregated["aggregatedPrices"]:
                        title = price_data["title"]
                        offer_count = price_data.get("offerCount", 0)
                        order_count = price_data.get("orderCount", 0)

                        # Рассчитываем простой показатель ликвидности
                        # Больше офферов и ордеров = выше ликвидность
                        liquidity_score = min(100, (offer_count + order_count) * 2)

                        liquidity_map[title] = {
                            "offer_count": offer_count,
                            "order_count": order_count,
                            "liquidity_score": liquidity_score,
                            "is_liquid": offer_count >= 5 and order_count >= 3,
                        }

                    # Обогащаем items данными о ликвидности
                    for item in items:
                        title = item.get("title")
                        if title in liquidity_map:
                            item["_liquidity"] = liquidity_map[title]

            except Exception as e:
                logger.warning(
                    f"Ошибка при получении aggregated prices: {e}, "
                    "продолжаем без данных о ликвидности"
                )

        # Анализируем каждый предмет
        results = []
        for item in items:
            analysis = await self._analyze_item(item, config, game)
            if analysis:
                results.append(analysis)
                if len(results) >= max_results:
                    break

        # Сохраняем в кеш через ScannerCache (R-2 refactoring)
        self._save_to_cache(cache_key, results)
        return results[:max_results]

    async def _analyze_item(
        self,
        item: dict[str, Any],
        config: dict[str, Any],
        game: str,
    ) -> dict[str, Any] | None:
        """Анализировать предмет на предмет прибыльности.

        Args:
            item: Данные о предмете
            config: Конфигурация уровня
            game: Код игры

        Returns:
            Словарь с данными о возможности или None

        """
        try:
            # Convert price to float (API sometimes returns string)
            price_value = item.get("price", {}).get("USD", 0)
            price_usd = float(price_value) / 100 if price_value else 0.0
            price_from, price_to = config["price_range"]

            # Проверяем диапазон цен
            if not (price_from <= price_usd <= price_to):
                return None

            # Получаем suggestedPrice или рассчитываем наценку 20%
            # Convert suggested price to float (API sometimes returns string)
            suggested_value = item.get("suggestedPrice", {}).get("USD", 0)
            suggested_price_cents = float(suggested_value) if suggested_value else 0.0
            if suggested_price_cents > 0:
                suggested_price = suggested_price_cents / 100
            else:
                suggested_price = price_usd * 1.2

            # Рассчитываем фактическую прибыль
            profit_usd = suggested_price - price_usd
            profit_percent = (profit_usd / price_usd * 100) if price_usd > 0 else 0

            # Проверяем минимальный процент прибыли
            min_profit_percent = config["min_profit_percent"]
            if profit_percent < min_profit_percent:
                return None

            # Проверяем данные ликвидности из aggregated API (если есть)
            liquidity_data = {}
            if "_liquidity" in item:
                liq = item["_liquidity"]
                liquidity_data = {
                    "offer_count": liq["offer_count"],
                    "order_count": liq["order_count"],
                    "liquidity_score": liq["liquidity_score"],
                    "is_liquid": liq["is_liquid"],
                }

                # Фильтруем неликвидные предметы если включен фильтр
                if self.enable_liquidity_filter:
                    if not liq["is_liquid"]:
                        logger.debug(
                            f"Предмет '{item.get('title')}' отфильтрован: "
                            f"низкая ликвидность (offer_count={liq['offer_count']}, "
                            f"order_count={liq['order_count']})"
                        )
                        return None

            # Анализ ликвидности через старый метод (фоллбэк)
            elif self.enable_liquidity_filter and self.liquidity_analyzer:
                try:
                    item_title = item.get("title", "")
                    game_id = GAME_IDS.get(game, game)
                    metrics = await self.liquidity_analyzer.analyze_item_liquidity(
                        item_title=item_title,
                        game=game_id,
                        days_history=30,
                    )

                    # Фильтруем по минимальному баллу ликвидности
                    if metrics.liquidity_score < self.min_liquidity_score:
                        logger.debug(
                            f"Предмет '{item_title}' отфильтрован: "
                            f"низкая ликвидность ({metrics.liquidity_score})"
                        )
                        return None

                    # Фильтруем по времени продажи
                    max_days = self.max_time_to_sell_days
                    if metrics.avg_time_to_sell_days > max_days:
                        logger.debug(
                            f"Предмет '{item_title}' отфильтрован: "
                            f"долго продается "
                            f"({metrics.avg_time_to_sell_days} дн)"
                        )
                        return None

                    # Получаем описание ликвидности
                    liquidity_description = self.liquidity_analyzer.get_liquidity_description(
                        metrics.liquidity_score
                    )

                    # Добавляем данные ликвидности в результат
                    liquidity_data = {
                        "liquidity_score": metrics.liquidity_score,
                        "sales_per_week": metrics.sales_per_week,
                        "time_to_sell_days": metrics.avg_time_to_sell_days,
                        "price_stability": metrics.price_stability,
                        "liquidity_description": liquidity_description,
                        "is_liquid": metrics.is_liquid,
                    }
                except Exception as e:
                    logger.debug(f"Ошибка анализа ликвидности: {e}")
                    # Продолжаем без данных ликвидности

            result = {
                "item": item,
                "buy_price": price_usd,
                "suggested_price": suggested_price,
                "profit": profit_usd,
                "expected_profit": profit_usd,
                "profit_percent": profit_percent,
                "game": game,
            }

            # Добавляем данные ликвидности если они есть
            if liquidity_data:
                result.update(liquidity_data)

            # Проверяем конкуренцию buy orders если включен фильтр
            if self.enable_competition_filter and self.api_client:
                try:
                    item_title = item.get("title", "")
                    if item_title:
                        game_id = GAME_IDS.get(game, game)
                        competition = await self.api_client.get_buy_orders_competition(
                            game_id=game_id,
                            title=item_title,
                        )

                        competition_level = competition.get("competition_level", "unknown")
                        total_orders = competition.get("total_orders", 0)
                        total_amount = competition.get("total_amount", 0)

                        # Фильтруем предметы с высокой конкуренцией
                        if total_orders > self.max_competition:
                            logger.debug(
                                f"Предмет '{item_title}' отфильтрован: "
                                f"высокая конкуренция ({total_orders} ордеров > "
                                f"{self.max_competition} макс)"
                            )
                            return None

                        # Добавляем данные о конкуренции в результат
                        result["competition"] = {
                            "level": competition_level,
                            "total_orders": total_orders,
                            "total_amount": total_amount,
                            "best_price": competition.get("best_price", 0.0),
                            "average_price": competition.get("average_price", 0.0),
                        }

                except Exception as e:
                    logger.debug(f"Ошибка проверки конкуренции для '{item.get('title')}': {e}")
                    # При ошибке продолжаем без данных о конкуренции

        except Exception as e:
            logger.debug(f"Ошибка анализа предмета: {e}")
            return None
        else:
            return result

    async def scan_all_levels(
        self,
        game: str = "csgo",
        max_results_per_level: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """Сканировать все уровни арбитража для игры.

        Args:
            game: Код игры
            max_results_per_level: Макс. результатов на уровень

        Returns:
            Словарь {level: results}

        """
        results = {}
        for level in ARBITRAGE_LEVELS:
            level_results = await self.scan_level(
                level=level,
                game=game,
                max_results=max_results_per_level,
            )
            results[level] = level_results
        return results

    async def find_best_opportunities(
        self,
        game: str = "csgo",
        top_n: int = 10,
        min_level: str | None = None,
        max_level: str | None = None,
    ) -> list[dict[str, Any]]:
        """Найти лучшие возможности арбитража.

        Args:
            game: Код игры
            top_n: Максимум результатов
            min_level: Минимальный уровень (boost, standard, high)
            max_level: Максимальный уровень (boost, standard, high)

        Returns:
            Список лучших возможностей

        Raises:
            ValueError: Если указан несуществующий уровень

        """
        if min_level and min_level not in ARBITRAGE_LEVELS:
            raise ValueError(f"Неизвестный уровень: {min_level}")
        if max_level and max_level not in ARBITRAGE_LEVELS:
            raise ValueError(f"Неизвестный уровень: {max_level}")

        # Определяем уровни для сканирования
        levels_to_scan = list(ARBITRAGE_LEVELS.keys())
        if min_level:
            min_index = levels_to_scan.index(min_level)
            levels_to_scan = levels_to_scan[min_index:]
        if max_level:
            max_index = levels_to_scan.index(max_level)
            levels_to_scan = levels_to_scan[: max_index + 1]

        # Собираем результаты
        results = []
        for level in levels_to_scan:
            level_results = await self.scan_level(level, game, top_n * 2)
            results.extend(level_results)

        # Сортируем по profit_percent
        sorted_results = sorted(
            results,
            key=lambda x: x.get("profit_percent", 0),
            reverse=True,
        )
        return sorted_results[:top_n]

    def get_level_stats(self) -> dict[str, dict[str, int]]:
        """Получить статистику по уровням.

        Returns:
            Словарь со статистикой по уровням

        """
        stats = {}
        for level, config in ARBITRAGE_LEVELS.items():
            price_range = config["price_range"]
            if isinstance(price_range, tuple) and len(price_range) == 2:
                _min_price, max_price = price_range
            else:
                max_price = 0.0
            stats[level] = {
                "name": config["name"],
                "min_profit": config["min_profit_percent"],
                "max_profit": max_price,
                "price_range": config["price_range"],
            }
        return stats

    async def get_market_overview(
        self,
        game: str = "csgo",
    ) -> dict[str, Any]:
        """Получить обзор рынка для игры.

        Args:
            game: Код игры

        Returns:
            Словарь с обзором рынка

        """
        try:
            api = await self.get_api_client()
            items = await api.get_market_items(game=game, limit=100)

            total_items = len(items.get("objects", []))

            # Подсчитываем прибыльные предметы и лучший процент прибыли
            total_opportunities = 0
            best_profit_percent = 0.0
            best_level = None
            results_by_level = {}
            prices = []

            for item in items.get("objects", []):
                price_usd = item.get("price", {}).get("USD", 0) / 100
                prices.append(price_usd)

                # Проверяем, есть ли suggestedPrice и больше ли она
                suggested = item.get("suggestedPrice", {}).get("USD", 0) / 100
                if suggested > price_usd:
                    total_opportunities += 1
                    profit_percent = (suggested - price_usd) / price_usd * 100
                    if profit_percent > best_profit_percent:
                        best_profit_percent = profit_percent
                        # Определяем лучший уровень по профиту
                        for level, cfg in ARBITRAGE_LEVELS.items():
                            if cfg["min_profit_percent"] <= profit_percent:
                                best_level = level

                    # Распределяем по уровням
                    for level, cfg in ARBITRAGE_LEVELS.items():
                        price_range = cfg["price_range"]
                        if isinstance(price_range, tuple) and len(price_range) == 2:
                            price_from, price_to = price_range
                            if price_from <= price_usd <= price_to:
                                if level not in results_by_level:
                                    results_by_level[level] = 0
                                results_by_level[level] += 1

            avg_price = sum(prices) / len(prices) if prices else 0.0

            return {
                "game": game,
                "total_items": total_items,
                "total_opportunities": total_opportunities,
                "best_profit_percent": best_profit_percent,
                "best_level": best_level,
                "results_by_level": results_by_level,
                "average_price": avg_price,
                "scanned_at": time.time(),
                "timestamp": time.time(),
            }
        except Exception as e:
            logger.exception(f"Ошибка получения обзора рынка: {e}")
            return {
                "game": game,
                "total_items": 0,
                "total_opportunities": 0,
                "average_price": 0.0,
                "error": str(e),
            }

    def get_statistics(self) -> dict[str, Any]:
        """Возвращает статистику работы сканера.

        Returns:
            Словарь со статистикой

        """
        # Получаем статистику кеша через ScannerCache (R-2 refactoring)
        cache_stats = self._scanner_cache.get_statistics()
        return {
            "total_scans": self.total_scans,
            "total_items_found": self.total_items_found,
            "successful_trades": self.successful_trades,
            "total_profit": self.total_profit,
            "cache_size": cache_stats["size"],
            "cache_ttl": cache_stats["ttl"],
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
        }

    def clear_cache(self) -> None:
        """Очищает кеш результатов сканирования."""
        self._scanner_cache.clear()
        logger.info("Кеш результатов сканирования очищен")


# Функции-обертки для обратной совместимости


async def find_arbitrage_opportunities_async(
    game: str,
    mode: str = "medium",
    max_items: int = 20,
) -> list[dict[str, Any]]:
    """Асинхронно находит арбитражные возможности для игры.

    Args:
        game: Код игры (например, csgo, dota2, rust, tf2)
        mode: Режим поиска (low, medium, high)
        max_items: Максимальное количество предметов в результате

    Returns:
        Список предметов, подходящих для арбитража

    """
    scanner = ArbitrageScanner()
    return await scanner.scan_game(game, mode, max_items)


async def find_multi_game_arbitrage_opportunities(
    games: list[str] | None = None,
    mode: str = "medium",
    max_items_per_game: int = 10,
) -> dict[str, list[dict[str, Any]]]:
    """Находит арбитражные возможности для нескольких игр.

    Args:
        games: Список кодов игр
        mode: Режим поиска (low, medium, high)
        max_items_per_game: Максимальное количество предметов на каждую игру

    Returns:
        Словарь с кодами игр и списками подходящих предметов

    """
    if games is None:
        games = ["csgo", "dota2", "rust", "tf2"]
    scanner = ArbitrageScanner()
    return await scanner.scan_multiple_games(games, mode, max_items_per_game)


async def scan_game_for_arbitrage(
    game: str,
    mode: str = "medium",
    max_items: int = 20,
    price_from: float | None = None,
    price_to: float | None = None,
    dmarket_api: DMarketAPI | None = None,
) -> list[dict[str, Any]]:
    """Сканирует одну игру для арбитража (обратная совместимость).

    Args:
        game: Код игры (например, "csgo", "dota2", "rust", "tf2")
        mode: Режим поиска ("low", "medium", "high")
        max_items: Максимальное количество предметов в результате
        price_from: Минимальная цена предмета (в USD)
        price_to: Максимальная цена предмета (в USD)
        dmarket_api: Экземпляр API DMarket или None для создания нового

    Returns:
        Список найденных предметов для арбитража

    """
    scanner = ArbitrageScanner(api_client=dmarket_api)
    return await scanner.scan_game(game, mode, max_items, price_from, price_to)


async def scan_multiple_games(
    games: list[str] | None = None,
    mode: str = "medium",
    max_items_per_game: int = 10,
    price_from: float | None = None,
    price_to: float | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Сканирует несколько игр для арбитража (обратная совместимость).

    Args:
        games: Список кодов игр для сканирования
        mode: Режим поиска ("low", "medium", "high")
        max_items_per_game: Максимальное количество предметов на игру
        price_from: Минимальная цена предмета (в USD)
        price_to: Максимальная цена предмета (в USD)

    Returns:
        Словарь с кодами игр и списками найденных предметов

    """
    if games is None:
        games = ["csgo", "dota2", "rust", "tf2"]
    scanner = ArbitrageScanner()
    return await scanner.scan_multiple_games(
        games,
        mode,
        max_items_per_game,
        price_from,
        price_to,
    )


async def check_user_balance(dmarket_api: DMarketAPI) -> dict[str, Any]:
    """Проверяет баланс DMarket (обратная совместимость).

    Args:
        dmarket_api: Экземпляр DMarketAPI для запроса

    Returns:
        Словарь с балансом и детальной информацией

    """
    scanner = ArbitrageScanner(api_client=dmarket_api)
    return await scanner.check_user_balance()


async def auto_trade_items(
    items_by_game: dict[str, list[dict[str, Any]]],
    min_profit: float = 0.5,  # мин. прибыль в USD
    max_price: float = 50.0,  # макс. цена покупки в USD
    dmarket_api: DMarketAPI | None = None,
    max_trades: int = 5,  # максимальное количество сделок
    risk_level: str = "medium",  # уровень риска (low, medium, high)
) -> tuple[int, int, float]:
    """Автоматически торгует предметами (обратная совместимость).

    Args:
        items_by_game: Словарь с предметами по играм
        min_profit: Минимальная прибыль для покупки (в USD)
        max_price: Максимальная цена покупки (в USD)
        dmarket_api: Экземпляр DMarketAPI для операций
        max_trades: Максимальное количество сделок за один запуск
        risk_level: Уровень риска (low, medium, high)

    Returns:
        Кортеж (количество покупок, количество продаж, общая прибыль)

    """
    scanner = ArbitrageScanner(api_client=dmarket_api)
    return await scanner.auto_trade_items(
        items_by_game=items_by_game,
        min_profit=min_profit,
        max_price=max_price,
        max_trades=max_trades,
        risk_level=risk_level,
    )

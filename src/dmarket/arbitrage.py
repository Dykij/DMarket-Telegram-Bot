"""Модуль с функциями для арбитража на платформе DMarket."""

import asyncio
import logging
import os
import time
import traceback
from datetime import datetime
from typing import Any

from .dmarket_api import DMarketAPI


# Настройка логирования
logger = logging.getLogger(__name__)

# Тип для результатов арбитража
SkinResult = dict[str, Any]

# Игры, поддерживаемые в арбитраже
GAMES = {
    "csgo": "CS2",
    "dota2": "Dota 2",
    "tf2": "Team Fortress 2",
    "rust": "Rust",
}

# Комиссии DMarket по категориям предметов
DEFAULT_FEE = 0.07  # 7% стандартная комиссия
LOW_FEE = 0.02  # 2% для ликвидных предметов
HIGH_FEE = 0.10  # 10% для редких предметов

# Лимиты запросов по умолчанию
DEFAULT_LIMIT = 100
MAX_RETRIES = 3

# Кеширование результатов поиска для улучшения производительности
# Ключ: (game, mode, min_price, max_price)
# Значение: (items, timestamp)
_arbitrage_cache: dict[
    tuple[str, str, float, float],
    tuple[list[SkinResult], float],
] = {}
_cache_ttl = 300  # Время жизни кеша в секундах (5 минут)

# Минимальная прибыль в процентах для различных режимов арбитража
MIN_PROFIT_PERCENT = {
    "low": 3.0,  # Низкая прибыль (3-5%)
    "medium": 5.0,  # Средняя прибыль (5-10%)
    "high": 10.0,  # Высокая прибыль (10-15%)
    "boost": 1.5,  # Режим разгона баланса (1.5-3%)
    "pro": 15.0,  # Профессиональный арбитраж (15%+)
}

# Диапазоны цен для различных режимов арбитража
PRICE_RANGES = {
    "low": (1.0, 5.0),  # $1-$5
    "medium": (5.0, 20.0),  # $5-$20
    "high": (20.0, 100.0),  # $20-$100
    "boost": (0.5, 3.0),  # $0.5-$3
    "pro": (100.0, 1000.0),  # $100-$1000
}


def _get_cached_results(
    cache_key: tuple[str, str, float, float],
) -> list[SkinResult] | None:
    """Получить кэшированные результаты арбитража.

    Args:
        cache_key: Ключ кэша (game, mode, min_price, max_price)

    Returns:
        Список предметов из кэша или None, если кэш устарел

    """
    if cache_key not in _arbitrage_cache:
        return None

    items, timestamp = _arbitrage_cache[cache_key]
    current_time = time.time()

    # Проверяем, не устарел ли кэш
    if current_time - timestamp > _cache_ttl:
        return None

    return items


def _save_to_cache(
    cache_key: tuple[str, str, float, float],
    items: list[SkinResult],
) -> None:
    """Сохранить результаты в кэш.

    Args:
        cache_key: Ключ кэша (game, mode, min_price, max_price)
        items: Список предметов для кэширования

    """
    _arbitrage_cache[cache_key] = (items, time.time())
    logger.debug(f"Кэшировано {len(items)} предметов для {cache_key[0]}")


async def fetch_market_items(
    game: str = "csgo",
    limit: int = 100,
    price_from: float | None = None,
    price_to: float | None = None,
    dmarket_api: DMarketAPI | None = None,
) -> list[dict[str, Any]]:
    """Получить реальные предметы с DMarket через API.

    Args:
        game: Код игры (csgo, dota2, tf2, rust)
        limit: Максимальное число возвращаемых предметов
        price_from: Минимальная цена в USD
        price_to: Максимальная цена в USD
        dmarket_api: Существующий экземпляр API или None для создания нового

    Returns:
        Список предметов с маркетплейса

    """
    if dmarket_api is None:
        public_key = os.environ.get("DMARKET_PUBLIC_KEY", "")
        secret_key = os.environ.get("DMARKET_SECRET_KEY", "")
        api_url = os.environ.get("DMARKET_API_URL", "https://api.dmarket.com")

        if not public_key or not secret_key:
            logger.error("Отсутствуют ключи API DMarket")
            return []

        dmarket_api = DMarketAPI(
            public_key,
            secret_key,
            api_url,
            max_retries=MAX_RETRIES,
        )

    try:
        # Преобразуем цены из USD в центы для API
        price_from_cents = int(price_from * 100) if price_from else None
        price_to_cents = int(price_to * 100) if price_to else None

        # Получаем предметы с рынка с учетом возможных повторных попыток
        async with dmarket_api:
            data = await dmarket_api.get_market_items(
                game=game,
                limit=limit,
                price_from=price_from_cents,
                price_to=price_to_cents,
            )

        return data.get("objects", [])
    except Exception as e:
        logger.exception(f"Ошибка при получении предметов: {e!s}")
        return []


async def _find_arbitrage_async(
    min_profit: float,
    max_profit: float,
    game: str = "csgo",
    price_from: float | None = None,
    price_to: float | None = None,
) -> list[SkinResult]:
    """Находит предметы с прибылью в указанном диапазоне.

    Args:
        min_profit: Минимальная прибыль в USD
        max_profit: Максимальная прибыль в USD
        game: Код игры (csgo, dota2, tf2, rust)
        price_from: Минимальная цена предмета в USD
        price_to: Максимальная цена предмета в USD

    Returns:
        Список предметов с прогнозируемой прибылью

    """
    # Создаем ключ для кэша
    cache_key = (
        game,
        f"{min_profit}-{max_profit}",
        price_from or 0,
        price_to or float("inf"),
    )

    # Проверяем кэш
    cached_results = _get_cached_results(cache_key)
    if cached_results:
        logger.debug(f"Использую кэшированные данные для {cache_key[0]}")
        return cached_results

    results = []
    # Сначала получаем все предметы с маркета
    items = await fetch_market_items(
        game=game,
        limit=DEFAULT_LIMIT,
        price_from=price_from,
        price_to=price_to,
    )

    for item in items:
        try:
            # Получаем текущую цену покупки (переводим центы в доллары)
            buy_price = float(item["price"]["amount"]) / 100

            # Получаем предполагаемую цену продажи
            # Если есть цена suggestedPrice, используем ее, иначе делаем наценку
            if "suggestedPrice" in item:
                sell_price = float(item["suggestedPrice"]["amount"]) / 100
            else:
                # Наценка от 10% до 15% в зависимости от ликвидности
                markup = 1.1
                if "extra" in item and "popularity" in item["extra"]:
                    popularity = item["extra"]["popularity"]
                    # Более популярные предметы могут иметь меньшую наценку
                    if popularity > 0.7:  # Высокая популярность
                        markup = 1.1  # 10%
                    elif popularity > 0.4:  # Средняя популярность
                        markup = 1.12  # 12%
                    else:  # Низкая популярность
                        markup = 1.15  # 15%
                sell_price = buy_price * markup

            # Определяем комиссию на основе ликвидности предмета
            liquidity = "medium"  # По умолчанию средняя ликвидность
            if "extra" in item and "popularity" in item["extra"]:
                popularity = item["extra"]["popularity"]
                if popularity > 0.7:
                    liquidity = "high"
                elif popularity < 0.4:
                    liquidity = "low"

            fee = DEFAULT_FEE
            if liquidity == "high":
                fee = LOW_FEE
            elif liquidity == "low":
                fee = HIGH_FEE

            # Расчет потенциальной прибыли
            profit = sell_price * (1 - fee) - buy_price
            profit_percent = (profit / buy_price) * 100 if buy_price > 0 else 0

            # Если прибыль в заданном диапазоне, добавляем предмет в результаты
            if min_profit <= profit <= max_profit:
                results.append(
                    {
                        "name": item.get("title", item.get("name", "Unknown")),
                        "buy": f"${buy_price:.2f}",
                        "sell": f"${sell_price:.2f}",
                        "profit": f"${profit:.2f}",
                        "profit_percent": f"{profit_percent:.1f}",
                        "fee": f"{int(fee * 100)}%",
                        "itemId": item.get("itemId", ""),
                        "market_hash_name": item.get("title", ""),
                        "liquidity": liquidity,
                        "game": game,
                    },
                )
        except Exception as e:
            logger.warning(f"Ошибка при обработке предмета: {e!s}")
            continue

    # Сортируем по прибыли (по убыванию)
    results = sorted(
        results,
        key=lambda x: (
            float(x["profit"].replace("$", ""))
            if isinstance(x["profit"], str)
            else x.get("profit", 0)
        ),
        reverse=True,
    )

    # Сохраняем результаты в кэш
    _save_to_cache(cache_key, results)

    return results


async def arbitrage_boost_async(
    game: str = "csgo",
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int | None = None,
    api_client: "DMarketAPI | None" = None,
) -> list[SkinResult]:
    """Скины с прибылью $1–5

    Args:
        game: Код игры (csgo, dota2, tf2, rust)
        min_price: Минимальная цена предмета (не используется, для совместимости)
        max_price: Максимальная цена предмета (не используется, для совместимости)
        limit: Максимальное количество результатов (не используется, для совместимости)
        api_client: Опциональный клиент DMarket API (не используется, для совместимости)

    Returns:
        Список предметов с низкой прибылью

    """
    return await _find_arbitrage_async(1, 5, game, min_price, max_price)


async def arbitrage_mid_async(
    game: str = "csgo",
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int | None = None,
    api_client: "DMarketAPI | None" = None,
) -> list[SkinResult]:
    """Скины с прибылью $5–20

    Args:
        game: Код игры (csgo, dota2, tf2, rust)
        min_price: Минимальная цена предмета (не используется, для совместимости)
        max_price: Максимальная цена предмета (не используется, для совместимости)
        limit: Максимальное количество результатов (не используется, для совместимости)
        api_client: Опциональный клиент DMarket API (не используется, для совместимости)

    Returns:
        Список предметов со средней прибылью

    """
    return await _find_arbitrage_async(5, 20, game, min_price, max_price)


async def arbitrage_pro_async(
    game: str = "csgo",
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int | None = None,
    api_client: "DMarketAPI | None" = None,
) -> list[SkinResult]:
    """Скины с прибылью $20–100

    Args:
        game: Код игры (csgo, dota2, tf2, rust)
        min_price: Минимальная цена предмета (не используется, для совместимости)
        max_price: Максимальная цена предмета (не используется, для совместимости)
        limit: Максимальное количество результатов (не используется, для совместимости)
        api_client: Опциональный клиент DMarket API (не используется, для совместимости)

    Returns:
        Список предметов с высокой прибылью

    """
    return await _find_arbitrage_async(20, 100, game, min_price, max_price)


# Для обратной совместимости предоставляем синхронные версии
def arbitrage_boost(game: str = "csgo") -> list[SkinResult]:
    """Синхронная версия arbitrage_boost_async для совместимости"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(arbitrage_boost_async(game))


def arbitrage_mid(game: str = "csgo") -> list[SkinResult]:
    """Синхронная версия arbitrage_mid_async для совместимости"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(arbitrage_mid_async(game))


def arbitrage_pro(game: str = "csgo") -> list[SkinResult]:
    """Синхронная версия arbitrage_pro_async для совместимости"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(arbitrage_pro_async(game))


async def find_arbitrage_opportunities_async(
    min_profit_percentage: float = 10.0,
    max_results: int = 5,
    game: str = "csgo",
    price_from: float | None = None,
    price_to: float | None = None,
) -> list[dict[str, Any]]:
    """Находит арбитражные возможности с минимальной прибылью и максимальным
    количеством результатов.

    Args:
        min_profit_percentage: Минимальный процент прибыли
        max_results: Максимальное количество результатов
        game: Код игры (csgo, dota2, tf2, rust)
        price_from: Минимальная цена предмета в USD
        price_to: Максимальная цена предмета в USD

    Returns:
        Список арбитражных возможностей

    """
    # Создаем ключ для кэша
    cache_key = (
        game,
        f"arb-{min_profit_percentage}",
        price_from or 0,
        price_to or float("inf"),
    )

    # Проверяем кэш
    cached_results = _get_cached_results(cache_key)
    if cached_results:
        logger.debug(f"Использую кэшированные возможности для {game}")
        return cached_results[:max_results]

    try:
        # Получаем предметы с рынка
        items = await fetch_market_items(
            game=game,
            limit=100,
            price_from=price_from,
            price_to=price_to,
        )

        opportunities = []
        for item in items:
            try:
                # Получаем цену покупки
                buy_price = float(item["price"]["amount"]) / 100

                # Получаем предполагаемую цену продажи
                if "suggestedPrice" in item:
                    sell_price = float(item["suggestedPrice"]["amount"]) / 100
                else:
                    # По умолчанию наценка 15%
                    sell_price = buy_price * 1.15

                # Определяем комиссию на основе ликвидности предмета
                liquidity = "medium"
                if "extra" in item and "popularity" in item["extra"]:
                    popularity = item["extra"]["popularity"]
                    if popularity > 0.7:
                        liquidity = "high"
                    elif popularity < 0.4:
                        liquidity = "low"

                fee = DEFAULT_FEE
                if liquidity == "high":
                    fee = LOW_FEE
                elif liquidity == "low":
                    fee = HIGH_FEE

                # Расчет потенциальной прибыли
                profit_amount = sell_price * (1 - fee) - buy_price
                profit_percentage = (profit_amount / buy_price) * 100

                # Если процент прибыли достаточный, добавляем возможность
                if profit_percentage >= min_profit_percentage:
                    opportunities.append(
                        {
                            "item_title": item.get("title", "Unknown"),
                            "market_from": "DMarket",
                            "market_to": (
                                "Steam Market" if game == "csgo" else "Game Market"
                            ),
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "profit_amount": profit_amount,
                            "profit_percentage": profit_percentage,
                            "itemId": item.get("itemId", ""),
                            "fee": fee,
                            "game": game,
                        },
                    )
            except Exception as e:
                logger.warning(
                    f"Ошибка при обработке арбитражной возможности: {e!s}",
                )
                continue

        # Сортируем по проценту прибыли (по убыванию)
        sorted_opportunities = sorted(
            opportunities,
            key=lambda x: x["profit_percentage"],
            reverse=True,
        )

        # Сохраняем в кэш
        _save_to_cache(cache_key, sorted_opportunities)

        # Возвращаем лимитированное количество результатов
        return sorted_opportunities[:max_results]
    except Exception as e:
        logger.exception(f"Ошибка при поиске арбитражных возможностей: {e!s}")
        return []


def find_arbitrage_opportunities(
    min_profit_percentage: float = 10.0,
    max_results: int = 5,
    game: str = "csgo",
) -> list[dict[str, Any]]:
    """Синхронная версия find_arbitrage_opportunities_async для совместимости."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        find_arbitrage_opportunities_async(
            min_profit_percentage,
            max_results,
            game,
        ),
    )


class ArbitrageTrader:
    """Класс для автоматического поиска и исполнения арбитражных сделок."""

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        api_url: str = "https://api.dmarket.com",
        max_retries: int = 3,
        connection_timeout: float = 5.0,
        pool_limits: int = 10,
        retry_codes: list[int] | None = None,
    ) -> None:
        """Инициализация трейдера.

        Args:
            public_key: DMarket API public key
            secret_key: DMarket API secret key
            api_url: DMarket API URL
            max_retries: Максимальное количество повторных попыток
            connection_timeout: Таймаут соединения в секундах
            pool_limits: Лимит соединений в пуле
            retry_codes: HTTP коды для повторных попыток

        """
        self.public_key = public_key or os.environ.get("DMARKET_PUBLIC_KEY", "")
        self.secret_key = secret_key or os.environ.get("DMARKET_SECRET_KEY", "")
        self.api_url = api_url or os.environ.get(
            "DMARKET_API_URL",
            "https://api.dmarket.com",
        )

        # Создаем API-клиент с улучшенными параметрами
        self.api = DMarketAPI(
            self.public_key,
            self.secret_key,
            self.api_url,
            max_retries=max_retries,
            connection_timeout=connection_timeout,
            pool_limits=pool_limits,
            retry_codes=retry_codes or [429, 500, 502, 503, 504],
        )

        # Параметры трейдера
        self.min_profit_percentage = 5.0  # Минимальный процент прибыли (5%)
        self.active = False
        self.transaction_history = []
        self.current_game = "csgo"

        # Переменные для управления рисками
        self.max_trade_value = 100.0  # Максимальная стоимость одной сделки в USD
        self.daily_limit = 500.0  # Дневной лимит торговли в USD
        self.daily_traded = 0.0  # Сколько торговали сегодня
        self.last_day_reset = time.time()  # Для сброса дневного счетчика

        # Для отслеживания неудачных сделок и паузы при частых ошибках
        self.error_count = 0
        self.last_error_time = 0
        self.pause_until = 0

    async def check_balance(self) -> tuple[bool, float]:
        """Проверяет баланс аккаунта.

        Returns:
            Кортеж (достаточно средств, текущий баланс)

        """
        try:
            async with self.api:
                balance_data = await self.api.get_user_balance()

            if not balance_data or "usd" not in balance_data:
                logger.error("Не удалось получить данные о балансе")
                return False, 0.0

            balance = float(balance_data["usd"]["amount"]) / 100  # центы в доллары

            # Проверяем, достаточно ли средств для минимальной сделки
            if balance < 1.0:  # Предполагаем минимальную сумму сделки $1
                logger.warning(f"Недостаточно средств на балансе: ${balance:.2f}")
                return False, balance

            return True, balance
        except Exception as e:
            logger.exception(f"Ошибка при проверке баланса: {e!s}")
            return False, 0.0

    async def _reset_daily_limits(self) -> None:
        """Сбрасывает дневные лимиты, если прошли сутки."""
        current_time = time.time()
        # Если прошло более 24 часов с момента последнего сброса
        if current_time - self.last_day_reset > 86400:  # 86400 секунд = 24 часа
            self.daily_traded = 0.0
            self.last_day_reset = current_time
            logger.info("Дневные лимиты торговли сброшены")

    async def _check_trading_limits(self, trade_value: float) -> bool:
        """Проверяет, не превышены ли лимиты торговли.

        Args:
            trade_value: Стоимость предстоящей сделки в USD

        Returns:
            True если сделка допустима, False если лимиты превышены

        """
        # Сначала сбрасываем дневные лимиты при необходимости
        await self._reset_daily_limits()

        # Проверка на максимальную стоимость одной сделки
        if trade_value > self.max_trade_value:
            logger.warning(
                f"Сделка на ${trade_value:.2f} превышает максимальный "
                f"лимит ${self.max_trade_value:.2f}",
            )
            return False

        # Проверка на дневной лимит торговли
        if self.daily_traded + trade_value > self.daily_limit:
            logger.warning(
                f"Сделка на ${trade_value:.2f} превысит дневной "
                f"лимит ${self.daily_limit:.2f}",
            )
            return False

        return True

    async def _handle_trading_error(self) -> None:
        """Обрабатывает ошибку торговли и управляет частотой повторных попыток."""
        current_time = time.time()
        self.error_count += 1
        self.last_error_time = current_time

        # Если накопилось много ошибок за короткое время
        if self.error_count >= 3 and current_time - self.last_error_time < 300:
            # Делаем паузу на 15 минут
            self.pause_until = current_time + 900  # 900 секунд = 15 минут
            logger.warning(
                "Слишком много ошибок торговли, пауза на 15 минут",
            )
        elif self.error_count >= 10:
            # При накоплении 10 ошибок - пауза на 1 час
            self.pause_until = current_time + 3600  # 3600 секунд = 1 час
            logger.warning(
                "Достигнут лимит ошибок торговли, пауза на 1 час",
            )
            # Сбрасываем счетчик ошибок
            self.error_count = 0

    async def _can_trade_now(self) -> bool:
        """Проверяет, можно ли торговать прямо сейчас.

        Returns:
            True если торговля разрешена, False если нужна пауза

        """
        current_time = time.time()

        # Если установлена пауза и она еще не истекла
        if current_time < self.pause_until:
            logger.info(
                f"Торговля на паузе, осталось "
                f"{int((self.pause_until - current_time) / 60)} минут",
            )
            return False

        # Сброс паузы, если время истекло
        if self.pause_until > 0 and current_time >= self.pause_until:
            self.pause_until = 0
            self.error_count = 0
            logger.info("Пауза в торговле закончилась")

        return True

    async def find_profitable_items(
        self,
        game: str = "csgo",
        min_profit_percentage: float = 5.0,
        max_items: int = 50,
        min_price: float = 1.0,
        max_price: float = 100.0,
    ) -> list[dict[str, Any]]:
        """Найти выгодные предметы для арбитража.

        Args:
            game: Название игры (csgo, dota2, tf2, rust)
            min_profit_percentage: Минимальный процент прибыли
            max_items: Максимальное количество предметов для анализа
            min_price: Минимальная цена предметов для анализа
            max_price: Максимальная цена предметов для анализа

        Returns:
            Список выгодных предметов для арбитража

        """
        try:
            logger.info(
                f"🔍 Поиск арбитражных возможностей для {game}: "
                f"мин. цена=${min_price:.2f}, макс. цена=${max_price:.2f}, "
                f"мин. прибыль={min_profit_percentage}%"
            )

            # Получаем предметы с рынка
            async with self.api:
                items = await self.api.get_market_items(
                    game=game,
                    limit=max_items,
                    price_from=min_price,  # get_market_items сам конвертирует в центы
                    price_to=max_price,
                )

            logger.debug(f"📦 Получен ответ API: {items.keys() if items else 'None'}")

            # DMarket API возвращает предметы в поле "objects" согласно документации
            objects = items.get("objects", items.get("items", []))

            if not objects:
                logger.warning(
                    f"⚠️ Не найдено предметов для игры {game} в диапазоне "
                    f"${min_price:.2f}-${max_price:.2f}"
                )
                return []

            logger.info(f"✅ Найдено {len(objects)} предметов для анализа")
            profitable_items = []

            for item in objects:
                try:
                    # Получаем текущую цену покупки
                    buy_price = float(item["price"]["amount"]) / 100

                    # Получаем предполагаемую цену продажи
                    suggested_price = 0.0

                    # Пытаемся получить предлагаемую цену из API
                    async with self.api:
                        price_data = await self.api.get_price_info(
                            item.get("title", ""),
                            game,
                        )

                        if price_data and "recommendedPrice" in price_data:
                            suggested_price = (
                                float(
                                    price_data["recommendedPrice"],
                                )
                                / 100
                            )

                    if not suggested_price:
                        # Если нет предлагаемой цены, используем наценку
                        suggested_price = buy_price * 1.15  # +15%

                    # Рассчитываем комиссию и прибыль
                    liquidity = "medium"
                    if "extra" in item and "popularity" in item["extra"]:
                        popularity = item["extra"]["popularity"]
                        if popularity > 0.7:
                            liquidity = "high"
                        elif popularity < 0.4:
                            liquidity = "low"

                    fee = DEFAULT_FEE
                    if liquidity == "high":
                        fee = LOW_FEE
                    elif liquidity == "low":
                        fee = HIGH_FEE

                    profit = suggested_price * (1 - fee) - buy_price
                    profit_percentage = (profit / buy_price) * 100

                    # Если предмет выгоден - добавляем в список
                    if profit_percentage >= min_profit_percentage:
                        profitable_items.append(
                            {
                                "name": item.get("title", item.get("name", "Unknown")),
                                "buy_price": buy_price,
                                "sell_price": suggested_price,
                                "profit": profit,
                                "profit_percentage": profit_percentage,
                                "fee": fee * 100,
                                "itemId": item.get("itemId", ""),
                                "market_hash_name": item.get("title", ""),
                                "game": game,
                            },
                        )
                except Exception as e:
                    logger.warning(
                        f"Ошибка при обработке предмета: {e!s}",
                    )
                    continue

            # Сортируем по проценту прибыли (по убыванию)
            return sorted(
                profitable_items,
                key=lambda x: x["profit_percentage"],
                reverse=True,
            )
        except Exception as e:
            logger.exception(
                f"Ошибка при поиске выгодных предметов: {e!s}",
            )
            return []

    async def execute_arbitrage_trade(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        """Выполнить арбитражную сделку (купить и продать предмет).

        Args:
            item: Информация о предмете для сделки

        Returns:
            Результат операции

        """
        # Результат операции
        result = {
            "success": False,
            "item_name": item["name"],
            "buy_price": item["buy_price"],
            "sell_price": item["sell_price"],
            "profit": item["profit"],
            "errors": [],
        }

        try:
            # Проверяем, возможна ли торговля сейчас
            if not await self._can_trade_now():
                result["errors"].append("Торговля временно на паузе")
                return result

            # Проверяем баланс
            has_funds, balance = await self.check_balance()
            if not has_funds:
                result["errors"].append(f"Недостаточно средств: ${balance:.2f}")
                return result

            # Проверяем лимиты торговли
            if not await self._check_trading_limits(item["buy_price"]):
                result["errors"].append(
                    f"Превышены лимиты торговли: ${item['buy_price']:.2f}",
                )
                return result

            # 1. Покупаем предмет
            async with self.api:
                buy_result = await self.api.buy_item(
                    market_hash_name=item["market_hash_name"],
                    price=item["buy_price"],
                    game=item["game"],
                )

            if not buy_result or "error" in buy_result:
                error_msg = buy_result.get("error", "Неизвестная ошибка")
                result["errors"].append(f"Ошибка при покупке: {error_msg}")
                # Обрабатываем ошибку для управления частотой попыток
                await self._handle_trading_error()
                return result

            # Получаем ID предмета из результата покупки
            item_id = buy_result.get("itemId")
            if not item_id:
                result["errors"].append(
                    "Не удалось получить ID предмета после покупки",
                )
                return result

            # Обновляем дневной лимит торговли
            self.daily_traded += item["buy_price"]

            # Даем время на обновление инвентаря
            await asyncio.sleep(3)

            # 2. Продаем предмет
            async with self.api:
                sell_result = await self.api.sell_item(
                    item_id=item_id,
                    price=item["sell_price"],
                    game=item["game"],
                )

            if not sell_result or "error" in sell_result:
                error_msg = sell_result.get("error", "Неизвестная ошибка")
                result["errors"].append(f"Ошибка при продаже: {error_msg}")
                # Даже если продажа не удалась, предмет уже куплен
                result["bought"] = True
                # Обрабатываем ошибку для управления частотой попыток
                await self._handle_trading_error()
                return result

            # Сделка выполнена успешно
            result["success"] = True
            result["transaction_id"] = sell_result.get("transactionId", "unknown")

            # Записываем в историю транзакций
            transaction_record = {
                "item_name": item["name"],
                "buy_price": item["buy_price"],
                "sell_price": item["sell_price"],
                "profit": item["profit"],
                "profit_percentage": item["profit_percentage"],
                "game": item["game"],
                "timestamp": time.time(),
            }
            self.transaction_history.append(transaction_record)

            # Сбрасываем счетчик ошибок при успешной сделке
            self.error_count = 0

            return result

        except Exception as e:
            logger.exception(f"Ошибка при выполнении сделки: {e!s}")
            result["errors"].append(f"Произошла ошибка: {e!s}")
            await self._handle_trading_error()
            return result

    async def start_auto_trading(
        self,
        game: str = "csgo",
        min_profit_percentage: float = 5.0,
        max_concurrent_trades: int = 1,
    ) -> tuple[bool, str]:
        """Запустить автоматическую торговлю.

        Args:
            game: Название игры (csgo, dota2, tf2, rust)
            min_profit_percentage: Минимальный процент прибыли
            max_concurrent_trades: Максимальное количество одновременных сделок

        Returns:
            Кортеж (успех, сообщение)

        """
        if self.active:
            return False, "Автоматическая торговля уже запущена"

        # Проверяем баланс перед запуском
        has_funds, balance = await self.check_balance()
        if not has_funds:
            return False, f"Недостаточно средств для торговли: ${balance:.2f}"

        # Устанавливаем параметры
        self.active = True
        self.current_game = game
        self.min_profit_percentage = min_profit_percentage

        # Запускаем автоторговлю в отдельной задаче
        asyncio.create_task(
            self._auto_trading_loop(
                game,
                min_profit_percentage,
                max_concurrent_trades,
            ),
        )

        return True, (
            f"Автоторговля запущена для {GAMES.get(game, game)}, "
            f"мин. прибыль: {min_profit_percentage}%"
        )

    async def stop_auto_trading(self) -> tuple[bool, str]:
        """Остановить автоматическую торговлю.

        Returns:
            Кортеж (успех, сообщение)

        """
        if not self.active:
            return False, "Автоматическая торговля не запущена"

        self.active = False
        return True, "Автоторговля остановлена"

    async def _auto_trading_loop(
        self,
        game: str,
        min_profit_percentage: float,
        max_concurrent_trades: int,
    ) -> None:
        """Основной цикл автоторговли.

        Args:
            game: Название игры
            min_profit_percentage: Минимальный процент прибыли
            max_concurrent_trades: Максимальное количество одновременных сделок

        """
        while self.active:
            try:
                # Проверяем, возможна ли торговля сейчас
                if not await self._can_trade_now():
                    await asyncio.sleep(60)  # Ожидаем минуту перед повторной проверкой
                    continue

                # Проверяем баланс перед поиском
                has_funds, balance = await self.check_balance()
                if not has_funds:
                    logger.warning(
                        f"Недостаточно средств для торговли: ${balance:.2f}, "
                        f"ожидание 5 минут",
                    )
                    await asyncio.sleep(300)  # Ждем 5 минут
                    continue

                # Находим выгодные предметы
                profitable_items = await self.find_profitable_items(
                    game=game,
                    min_profit_percentage=min_profit_percentage,
                    max_items=100,
                    min_price=1.0,
                    max_price=min(
                        balance * 0.8,
                        self.max_trade_value,
                    ),  # Не более 80% баланса
                )

                if profitable_items:
                    logger.info(
                        f"Найдено {len(profitable_items)} выгодных предметов",
                    )

                    # Берем самые выгодные предметы для торговли
                    items_to_trade = []
                    remaining_balance = balance

                    # Выбираем предметы с учетом баланса
                    for item in profitable_items:
                        # Проверяем лимиты
                        if (
                            await self._check_trading_limits(item["buy_price"])
                            and item["buy_price"] <= remaining_balance
                        ):
                            items_to_trade.append(item)
                            remaining_balance -= item["buy_price"]

                            if len(items_to_trade) >= max_concurrent_trades:
                                break

                    if items_to_trade:
                        # Выполняем сделки последовательно для лучшего контроля
                        for item in items_to_trade:
                            trade_result = await self.execute_arbitrage_trade(item)
                            # Небольшая пауза между сделками
                            await asyncio.sleep(5)

                            # Если произошла ошибка, делаем более длинную паузу
                            if not trade_result["success"]:
                                await asyncio.sleep(30)
                    else:
                        logger.info(
                            "Нет подходящих предметов для торговли с текущими "
                            "ограничениями",
                        )
                else:
                    logger.info("Не найдено выгодных предметов для торговли")

                # Пауза между циклами проверки
                await asyncio.sleep(60)  # Проверяем каждую минуту

            except Exception as e:
                logger.exception(f"Ошибка в цикле автоторговли: {e!s}")
                # Небольшая пауза при ошибке
                await asyncio.sleep(30)

    def get_transaction_history(self) -> list[dict[str, Any]]:
        """Получить историю транзакций.

        Returns:
            Список транзакций

        """
        return self.transaction_history

    def set_trading_limits(
        self,
        max_trade_value: float | None = None,
        daily_limit: float | None = None,
    ) -> None:
        """Установить лимиты торговли.

        Args:
            max_trade_value: Максимальная стоимость одной сделки
            daily_limit: Дневной лимит торговли

        """
        if max_trade_value is not None:
            self.max_trade_value = max_trade_value

        if daily_limit is not None:
            self.daily_limit = daily_limit

        logger.info(
            f"Установлены лимиты торговли: макс. сделка ${self.max_trade_value:.2f}, "
            f"дневной лимит ${self.daily_limit:.2f}",
        )

    def get_status(self) -> dict[str, Any]:
        """Получить текущий статус торговли.

        Returns:
            Словарь с информацией о статусе

        """
        # Вычисляем общую прибыль
        total_profit = (
            sum(t["profit"] for t in self.transaction_history)
            if self.transaction_history
            else 0.0
        )

        # Определяем, на паузе ли торговля
        on_pause = time.time() < self.pause_until
        pause_minutes = int((self.pause_until - time.time()) / 60) if on_pause else 0

        return {
            "active": self.active,
            "current_game": self.current_game,
            "game_name": GAMES.get(self.current_game, self.current_game),
            "min_profit_percentage": self.min_profit_percentage,
            "transactions_count": len(self.transaction_history),
            "total_profit": total_profit,
            "daily_traded": self.daily_traded,
            "daily_limit": self.daily_limit,
            "max_trade_value": self.max_trade_value,
            "error_count": self.error_count,
            "on_pause": on_pause,
            "pause_minutes": pause_minutes,
        }

    async def get_current_item_data(
        self,
        item_id: str,
        game: str = "csgo",
    ) -> dict[str, Any] | None:
        """Получает текущую информацию о предмете.

        Args:
            item_id: Идентификатор предмета
            game: Код игры

        Returns:
            Словарь с информацией о предмете или None в случае ошибки

        """
        try:
            # Запрос на получение информации о предмете через эндпоинт по документации
            async with self.api:
                result = await self.api._request(
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

    async def purchase_item(
        self,
        item_id: str,
        max_price: float,
        dmarket_api: DMarketAPI | None = None,
    ) -> dict[str, Any]:
        """Покупает предмет на маркетплейсе.

        Args:
            item_id: Идентификатор предмета для покупки
            max_price: Максимальная цена покупки в USD
            dmarket_api: Опциональный API-клиент (если None, используется внутренний)

        Returns:
            Словарь с результатом операции

        """
        api = dmarket_api or self.api

        try:
            # Покупаем предмет через API используя эндпоинт из документации
            async with api:
                purchase_data = await api._request(
                    method="POST",
                    path="/exchange/v1/offers/create",
                    data={
                        "targets": [
                            {
                                "itemId": item_id,
                                "price": {
                                    "amount": int(max_price * 100),
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

    async def list_item_for_sale(
        self,
        item_id: str,
        price: float,
        dmarket_api: DMarketAPI | None = None,
    ) -> dict[str, Any]:
        """Выставляет предмет на продажу.

        Args:
            item_id: Идентификатор предмета для продажи
            price: Цена продажи в USD
            dmarket_api: Опциональный API-клиент (если None, используется внутренний)

        Returns:
            Словарь с результатом операции

        """
        api = dmarket_api or self.api

        try:
            # Выставляем предмет на продажу через API используя эндпоинт из документации
            async with api:
                sell_data = await api._request(
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


async def find_arbitrage_items(
    game: str,
    mode: str = "mid",
    min_price: float = 1.0,
    max_price: float = 100.0,
    limit: int = 20,
    api_client: DMarketAPI | None = None,
) -> list[SkinResult]:
    """Находит предметы для арбитража.

    Args:
        game: Код игры (csgo, dota2, tf2, rust)
        mode: Режим арбитража (low, mid, pro)
        min_price: Минимальная цена предмета
        max_price: Максимальная цена предмета
        limit: Максимальное количество результатов
        api_client: Опциональный клиент DMarket API

    Returns:
        Список найденных предметов для арбитража

    """
    if mode in {"low", "boost"}:
        results = await arbitrage_boost_async(
            game,
            min_price,
            max_price,
            limit,
            api_client,
        )
    elif mode == "mid":
        results = await arbitrage_mid_async(
            game,
            min_price,
            max_price,
            limit,
            api_client,
        )
    elif mode == "pro":
        results = await arbitrage_pro_async(
            game,
            min_price,
            max_price,
            limit,
            api_client,
        )
    else:
        # По умолчанию используем средний режим
        results = await arbitrage_mid_async(
            game,
            min_price,
            max_price,
            limit,
            api_client,
        )

    # Проверяем и преобразуем результаты, если они в формате кортежа
    processed_results = []
    for item in results:
        if isinstance(item, tuple):
            # Преобразуем кортеж в словарь с нужными ключами
            item_dict = {
                "market_hash_name": item[0] if len(item) > 0 else "",
                "buy_price": item[1] if len(item) > 1 else 0,
                "sell_price": item[2] if len(item) > 2 else 0,
                "profit": item[3] if len(item) > 3 else 0,
                "profit_percent": item[4] if len(item) > 4 else 0,
            }
            processed_results.append(item_dict)
        else:
            processed_results.append(item)

    return processed_results


async def find_arbitrage_opportunities_advanced(
    api_client: DMarketAPI,
    mode: str = "normal",
    game: str = "csgo",
    max_items: int = 100,
    min_profit_percent: float | None = None,
    price_from: float | None = None,
    price_to: float | None = None,
) -> list[dict[str, Any]]:
    """Ищет арбитражные возможности на DMarket.

    Args:
        api_client: Экземпляр API клиента DMarket
        mode: Режим арбитража (normal, best, low, medium, high, boost, pro)
              или game_X для конкретной игры (где X - код игры)
        game: Идентификатор игры (csgo, dota2, rust, tf2) -
              используется если не указан в mode как game_X
        max_items: Максимальное количество предметов для анализа
        min_profit_percent: Минимальная прибыль в процентах
        price_from: Минимальная цена предмета
        price_to: Максимальная цена предмета

    Returns:
        List[Dict[str, Any]]: Список возможностей для арбитража

    """
    start_time = time.time()
    logger.info(f"Запуск поиска арбитражных возможностей (режим: {mode}, игра: {game})")

    # Обработка режима игры (если указан как game_X)
    if mode.startswith("game_") and len(mode) > 5:
        game = mode[5:]  # Извлекаем код игры из mode (например, game_csgo -> csgo)
        mode = "normal"  # Устанавливаем стандартный режим

    # Приведение режима к стандартному формату
    if mode == "normal":
        mode = "medium"
    elif mode == "best":
        mode = "high"

    # Проверяем корректность параметров с подробным логированием ошибок
    if game not in GAMES:
        logger.warning(
            f"Неизвестная игра: {game}. Доступные игры: {', '.join(GAMES.keys())}. Используется csgo.",
        )
        game = "csgo"

    if mode not in MIN_PROFIT_PERCENT and mode not in [
        "low",
        "medium",
        "high",
        "boost",
        "pro",
    ]:
        logger.warning(
            f"Неизвестный режим: {mode}. Доступные режимы: {', '.join(MIN_PROFIT_PERCENT.keys())}. "
            f"Используется medium.",
        )
        mode = "medium"

    # Устанавливаем параметры поиска
    min_profit = min_profit_percent or MIN_PROFIT_PERCENT.get(mode, 5.0)

    # Определяем диапазон цен на основе режима, если не указаны явно
    if price_from is None and price_to is None:
        price_range = PRICE_RANGES.get(mode, (1.0, 100.0))
        price_from = price_range[0]
        price_to = price_range[1]

    # Устанавливаем значения по умолчанию, если не указаны
    price_lower = price_from if price_from is not None else 1.0
    price_upper = price_to if price_to is not None else 100.0

    logger.info(
        f"Поиск арбитражных возможностей для {GAMES.get(game, game)} в режиме {mode} "
        f"(мин. прибыль: {min_profit:.1f}%, диапазон цен: ${price_lower:.2f}-${price_upper:.2f})",
    )

    # Проверяем кэш
    cache_key = (game, mode, price_lower, price_upper, min_profit)
    cached_results = _get_arbitrage_cache(cache_key)
    if cached_results:
        logger.info(f"Найдено {len(cached_results)} возможностей в кэше")
        return cached_results

    try:
        # Получаем предметы маркета
        market_items = await api_client.get_all_market_items(
            game=game,
            max_items=max_items,
            price_from=price_lower,
            price_to=price_upper,
            sort="price",
        )

        if not market_items:
            logger.warning(
                f"Не найдены предметы на маркете для {game} "
                f"в диапазоне ${price_lower:.2f}-${price_upper:.2f}",
            )
            return []

        logger.info(f"Получено {len(market_items)} предметов для анализа")

        # Группируем предметы по названию для анализа
        grouped_items = _group_items_by_name(market_items)

        # Анализируем возможности для арбитража
        opportunities = []
        total_items_analyzed = 0

        for item_name, items in grouped_items.items():
            # Если в группе меньше 2 предметов, арбитраж невозможен
            if len(items) < 2:
                continue

            total_items_analyzed += 1

            # Сортируем по возрастанию цены
            items.sort(key=lambda x: x.get("price", {}).get("USD", 0))

            # Анализируем разницу между самым дешевым и остальными предметами
            cheapest = items[0]
            cheapest_price = cheapest.get("price", {}).get("USD", 0) / 100

            # Получаем данные о предмете для определения комиссии
            item_rarity = cheapest.get("extra", {}).get("rarity", "")
            item_type = cheapest.get("extra", {}).get("category", "")
            item_popularity = cheapest.get("extra", {}).get("popularity", 0.5)

            # Определяем комиссию на основе характеристик предмета
            commission_percent = _calculate_commission(
                item_rarity,
                item_type,
                item_popularity,
                game,
            )

            # Проверяем остальные предметы
            for item in items[1:]:
                sell_price = item.get("price", {}).get("USD", 0) / 100

                # Рассчитываем прибыль с учетом комиссий
                gross_profit = sell_price - cheapest_price
                commission_amount = sell_price * commission_percent / 100
                net_profit = gross_profit - commission_amount
                profit_percent = (net_profit / cheapest_price) * 100

                # Если прибыль превышает минимальный порог
                if profit_percent >= min_profit and net_profit > 0:
                    opportunity = {
                        "item_name": item_name,
                        "buy_price": cheapest_price,
                        "sell_price": sell_price,
                        "profit": net_profit,
                        "profit_percent": profit_percent,
                        "commission_percent": commission_percent,
                        "commission_amount": commission_amount,
                        "buy_item_id": cheapest.get("itemId"),
                        "sell_item_id": item.get("itemId"),
                        "game": game,
                        "rarity": item_rarity,
                        "type": item_type,
                        "popularity": item_popularity,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Добавляем изображение предмета, если доступно
                    if "imageUrl" in cheapest:
                        opportunity["image_url"] = cheapest.get("imageUrl")

                    # Добавляем ссылки на покупку и продажу
                    buy_id = cheapest.get("itemId", "")
                    sell_id = item.get("itemId", "")

                    if buy_id:
                        opportunity["buy_link"] = (
                            f"https://dmarket.com/ingame-items/item-list/{game}-skins?userOfferId={buy_id}"
                        )
                    if sell_id:
                        opportunity["sell_link"] = (
                            f"https://dmarket.com/ingame-items/item-list/{game}-skins?userOfferId={sell_id}"
                        )

                    opportunities.append(opportunity)

        # Сортируем возможности по проценту прибыли (от большего к меньшему)
        opportunities.sort(key=lambda x: x["profit_percent"], reverse=True)

        # Логируем статистику поиска
        elapsed_time = time.time() - start_time
        logger.info(
            f"Найдено {len(opportunities)} арбитражных возможностей из {total_items_analyzed} "
            f"проанализированных предметов за {elapsed_time:.2f} сек.",
        )

        # Обрезаем список до разумного размера для возврата
        max_return = min(50, len(opportunities))
        result = opportunities[:max_return]

        # Сохраняем результат в кэш
        _save_arbitrage_cache(cache_key, result)

        return result

    except Exception as e:
        logger.exception(f"Ошибка при поиске арбитражных возможностей: {e}")
        logger.exception(traceback.format_exc())
        return []


def _calculate_commission(
    rarity: str,
    item_type: str,
    popularity: float,
    game: str,
) -> float:
    """Рассчитывает комиссию для предмета на основе его характеристик.

    Args:
        rarity: Редкость предмета
        item_type: Тип предмета
        popularity: Популярность предмета (0-1)
        game: Код игры

    Returns:
        float: Процент комиссии

    """
    # Базовая комиссия DMarket
    base_commission = 7.0  # 7%

    # Корректировка на основе редкости
    if rarity.lower() in [
        "covert",
        "extraordinary",
        "contraband",
        "ancient",
        "mythical",
        "immortal",
        "arcana",
    ]:
        rarity_factor = 1.1  # Увеличиваем комиссию для редких предметов
    elif rarity.lower() in ["consumer", "industrial", "common"]:
        rarity_factor = 0.9  # Уменьшаем для обычных предметов
    else:
        rarity_factor = 1.0

    # Корректировка на основе типа предмета
    if item_type.lower() in ["knife", "gloves", "rare_special"]:
        type_factor = 1.2  # Ножи и перчатки имеют повышенную комиссию
    elif item_type.lower() in ["sticker", "container", "key"]:
        type_factor = 0.9  # Стикеры и контейнеры часто имеют меньшую комиссию
    else:
        type_factor = 1.0

    # Корректировка на основе популярности
    if popularity > 0.8:
        popularity_factor = 0.85  # Популярные предметы продаются быстрее
    elif popularity < 0.3:
        popularity_factor = 1.15  # Непопулярные предметы могут иметь высокую комиссию
    else:
        popularity_factor = 1.0

    # Корректировка на основе игры
    if game == "csgo":
        game_factor = 1.0  # Стандартная комиссия для CS:GO
    elif game == "dota2":
        game_factor = 1.05  # Немного выше для Dota 2
    elif game == "rust":
        game_factor = 1.1  # Выше для Rust
    else:
        game_factor = 1.0

    # Рассчитываем итоговую комиссию
    commission = (
        base_commission * rarity_factor * type_factor * popularity_factor * game_factor
    )

    # Ограничиваем диапазон (2% - 15%)
    return max(2.0, min(15.0, commission))


def _get_arbitrage_cache(cache_key: tuple) -> list[dict[str, Any]] | None:
    """Получает кэшированные результаты арбитража.

    Args:
        cache_key: Ключ кэша

    Returns:
        Optional[List[Dict[str, Any]]]: Кэшированные результаты или None

    """
    global _arbitrage_cache

    if cache_key not in _arbitrage_cache:
        return None

    items, timestamp = _arbitrage_cache[cache_key]

    # Проверяем актуальность кэша
    if time.time() - timestamp > _cache_ttl:
        return None

    return items


def _save_arbitrage_cache(cache_key: tuple, items: list[dict[str, Any]]) -> None:
    """Сохраняет результаты арбитража в кэш.

    Args:
        cache_key: Ключ кэша
        items: Результаты для кэширования

    """
    global _arbitrage_cache

    # Ограничиваем размер кэша
    if len(_arbitrage_cache) > 20:
        # Удаляем самые старые записи
        oldest_keys = sorted(
            _arbitrage_cache.keys(),
            key=lambda k: _arbitrage_cache[k][1],
        )[:5]
        for key in oldest_keys:
            del _arbitrage_cache[key]

    _arbitrage_cache[cache_key] = (items, time.time())
    logger.debug(f"Сохранено {len(items)} возможностей в кэш с ключом {cache_key[0:2]}")


def _group_items_by_name(
    items: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Группирует предметы по названию.

    Args:
        items: Список предметов

    Returns:
        Dict[str, List[Dict[str, Any]]]: Предметы, сгруппированные по названию

    """
    grouped = {}

    for item in items:
        name = item.get("title", "")
        if not name:
            continue

        if name not in grouped:
            grouped[name] = []

        grouped[name].append(item)

    return grouped

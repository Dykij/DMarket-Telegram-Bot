"""Модуль для управления таргетами (buy orders) на DMarket.

Таргеты - это заявки на покупку предметов по указанной цене.
Когда продавец выставляет предмет по цене таргета или ниже,
происходит автоматическая покупка.

Основные возможности:
- Создание таргетов с указанием цены и атрибутов
- Управление активными таргетами
- Автоматическое создание умных таргетов
- Мониторинг исполненных таргетов
"""

import asyncio
import logging
import re
import time
from typing import Any

from src.dmarket.dmarket_api import DMarketAPI
from src.dmarket.liquidity_analyzer import LiquidityAnalyzer


logger = logging.getLogger(__name__)


class TargetManager:
    """Менеджер для работы с таргетами (buy orders) на DMarket.

    Таргеты позволяют создавать заявки на покупку предметов по заданной цене.
    При появлении подходящего предмета происходит автоматическая покупка.

    Attributes:
        api: Экземпляр DMarket API клиента

    """

    def __init__(
        self,
        api_client: DMarketAPI,
        enable_liquidity_filter: bool = True,
    ) -> None:
        """Инициализация менеджера таргетов.

        Args:
            api_client: Настроенный клиент DMarket API
            enable_liquidity_filter: Включить фильтрацию по ликвидности

        """
        self.api = api_client
        self.enable_liquidity_filter = enable_liquidity_filter
        self.liquidity_analyzer = None

        if self.enable_liquidity_filter:
            self.liquidity_analyzer = LiquidityAnalyzer(api_client=self.api)

        logger.info("TargetManager инициализирован")

    async def create_target(
        self,
        game: str,
        title: str,
        price: float,
        amount: int = 1,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Создать таргет (buy order) для предмета.

        Args:
            game: Код игры (csgo, dota2, tf2, rust)
            title: Полное название предмета
            price: Цена покупки в USD
            amount: Количество предметов (макс: 100)
            attrs: Дополнительные атрибуты (float, phase, paintSeed)

        Returns:
            Результат создания таргета

        Example:
            >>> manager = TargetManager(api)
            >>> result = await manager.create_target(
            ...     game="csgo", title="AK-47 | Redline (Field-Tested)", price=8.00, amount=1
            ... )

        """
        logger.info(
            f"Создание таргета: {title} по цене ${price:.2f} (игра: {game})",
        )

        # Валидация параметров
        if price <= 0:
            msg = f"Цена должна быть больше 0, получено: {price}"
            raise ValueError(msg)

        if price > 100000:
            msg = f"Цена не может превышать $100,000, получено: {price}"
            raise ValueError(msg)

        # Проверка на количество знаков после запятой (макс 2)
        if round(price, 2) != price:
            msg = f"Цена не может иметь более 2 знаков после запятой, получено: {price}"
            raise ValueError(msg)

        if amount <= 0 or amount > 100:
            msg = f"Количество должно быть от 1 до 100, получено: {amount}"
            raise ValueError(
                msg,
            )

        if not title or not title.strip():
            msg = "Название предмета не может быть пустым"
            raise ValueError(msg)

        # Конвертируем игру в gameId
        game_ids = {
            "csgo": "a8db",
            "dota2": "9a92",
            "tf2": "tf2",
            "rust": "rust",
        }
        game_id = game_ids.get(game.lower(), game)

        # Формируем данные таргета
        target_data = {
            "Title": title,
            "Amount": amount,
            "Price": {
                "Amount": int(price * 100),  # Конвертируем в центы
                "Currency": "USD",
            },
        }

        # Добавляем атрибуты если указаны
        if attrs:
            self._validate_attributes(game, attrs)
            target_data["Attrs"] = attrs
            logger.debug(f"Добавлены атрибуты: {attrs}")

        try:
            # Создаем таргет через API
            result = await self.api.create_targets(
                game_id=game_id,
                targets=[target_data],
            )

            if result and "Result" in result and result["Result"]:
                target_result = result["Result"][0]
                logger.info(
                    f"Таргет создан успешно: {target_result.get('TargetID', 'unknown')}",
                )
                return {
                    "success": True,
                    "target_id": target_result.get("TargetID"),
                    "title": title,
                    "price": price,
                    "amount": amount,
                    "game": game,
                    "status": target_result.get("Status", "Created"),
                }

            logger.error(f"Некорректный ответ при создании таргета: {result}")
            return {"success": False, "error": "Некорректный ответ от API"}

        except Exception as e:
            logger.exception(f"Ошибка при создании таргета: {e!s}")
            return {"success": False, "error": str(e)}

    async def get_user_targets(
        self,
        game: str,
        status: str = "active",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Получить список таргетов пользователя.

        Args:
            game: Код игры (csgo, dota2, tf2, rust)
            status: Статус таргетов ('active', 'inactive', 'all')
            limit: Максимальное количество результатов

        Returns:
            Список таргетов пользователя

        Example:
            >>> targets = await manager.get_user_targets("csgo", "active")
            >>> for target in targets:
            ...     print(f"{target['title']}: ${target['price']:.2f}")

        """
        logger.info(f"Получение таргетов для {game} со статусом {status}")

        # Конвертируем игру в gameId
        game_ids = {
            "csgo": "a8db",
            "dota2": "9a92",
            "tf2": "tf2",
            "rust": "rust",
        }
        game_id = game_ids.get(game.lower(), game)

        # Определяем статус фильтра
        status_filter = None
        if status == "active":
            status_filter = "TargetStatusActive"
        elif status == "inactive":
            status_filter = "TargetStatusInactive"

        try:
            result = await self.api.get_user_targets(
                game_id=game_id,
                status=status_filter,
                limit=limit,
            )

            if not result or "Items" not in result:
                logger.warning(f"Не найдено таргетов для {game}")
                return []

            targets = []
            for item in result["Items"]:
                price_data = item.get("Price", {})
                price = float(price_data.get("Amount", 0)) / 100

                targets.append(
                    {
                        "target_id": item.get("TargetID"),
                        "title": item.get("Title"),
                        "price": price,
                        "amount": item.get("Amount", 1),
                        "status": item.get("Status"),
                        "game": game,
                        "created_at": item.get("CreatedAt"),
                        "attributes": item.get("Attrs", {}),
                    },
                )

            logger.info(f"Найдено {len(targets)} таргетов")
            return targets

        except Exception as e:
            logger.exception(f"Ошибка при получении таргетов: {e!s}")
            return []

    async def delete_target(self, target_id: str) -> bool:
        """Удалить таргет по ID.

        Args:
            target_id: Идентификатор таргета

        Returns:
            True если удаление успешно, False в противном случае

        Example:
            >>> success = await manager.delete_target("target_123")
            >>> if success:
            ...     print("Таргет удален")

        """
        logger.info(f"Удаление таргета: {target_id}")

        try:
            result = await self.api.delete_targets(target_ids=[target_id])

            if result and "Result" in result and result["Result"]:
                delete_result = result["Result"][0]
                status = delete_result.get("Status")

                if status == "Deleted":
                    logger.info(f"Таргет {target_id} успешно удален")
                    return True

                logger.warning(
                    f"Таргет {target_id} не удален, статус: {status}",
                )
                return False

            logger.error(f"Некорректный ответ при удалении таргета: {result}")
            return False

        except Exception as e:
            logger.exception(f"Ошибка при удалении таргета {target_id}: {e!s}")
            return False

    async def delete_all_targets(
        self,
        game: str,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Удалить все активные таргеты для игры.

        Args:
            game: Код игры
            confirm: Подтверждение удаления (защита от случайного удаления)

        Returns:
            Результат операции с количеством удаленных таргетов

        Example:
            >>> result = await manager.delete_all_targets("csgo", confirm=True)
            >>> print(f"Удалено таргетов: {result['deleted_count']}")

        """
        if not confirm:
            logger.warning("Попытка удалить все таргеты без подтверждения")
            return {
                "success": False,
                "error": "Требуется подтверждение для удаления всех таргетов",
            }

        logger.info(f"Удаление всех таргетов для {game}")

        # Получаем все активные таргеты
        targets = await self.get_user_targets(game, status="active")

        if not targets:
            return {
                "success": True,
                "deleted_count": 0,
                "message": "Нет активных таргетов для удаления",
            }

        deleted_count = 0
        failed_count = 0

        for target in targets:
            success = await self.delete_target(target["target_id"])
            if success:
                deleted_count += 1
            else:
                failed_count += 1

            # Небольшая задержка между удалениями для rate limiting
            await asyncio.sleep(0.5)

        logger.info(
            f"Удалено {deleted_count} таргетов, не удалось: {failed_count}",
        )

        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "total": len(targets),
        }

    async def get_targets_by_title(
        self,
        game: str,
        title: str,
    ) -> list[dict[str, Any]]:
        """Получить все таргеты для конкретного предмета.

        Показывает, какие buy orders существуют для данного предмета
        от всех пользователей (агрегированные данные).

        Args:
            game: Код игры
            title: Название предмета

        Returns:
            Список таргетов для предмета

        Example:
            >>> targets = await manager.get_targets_by_title("csgo", "AK-47 | Redline (Field-Tested)")
            >>> for target in targets:
            ...     print(f"Цена: ${target['price']:.2f}, Количество: {target['amount']}")

        """
        logger.info(f"Поиск таргетов для '{title}' в {game}")

        # Конвертируем игру в gameId
        game_ids = {
            "csgo": "a8db",
            "dota2": "9a92",
            "tf2": "tf2",
            "rust": "rust",
        }
        game_id = game_ids.get(game.lower(), game)

        try:
            result = await self.api.get_targets_by_title(
                game_id=game_id,
                title=title,
            )

            if not result or "orders" not in result:
                logger.info(f"Не найдено таргетов для '{title}'")
                return []

            targets = []
            for order in result["orders"]:
                price = float(order.get("price", 0)) / 100

                targets.append(
                    {
                        "title": order.get("title"),
                        "price": price,
                        "amount": order.get("amount", 0),
                        "attributes": order.get("attributes", {}),
                    },
                )

            logger.info(f"Найдено {len(targets)} таргетов для '{title}'")
            return targets

        except Exception as e:
            logger.exception(
                f"Ошибка при поиске таргетов для '{title}': {e!s}",
            )
            return []

    async def create_smart_targets(
        self,
        game: str,
        items: list[dict[str, Any]],
        price_reduction_percent: float = 5.0,
        max_targets: int = 10,
        use_aggregated_prices: bool = True,
        min_liquidity_score: int = 50,
    ) -> list[dict[str, Any]]:
        """Автоматически создать умные таргеты для списка предметов.

        Умные таргеты создаются на основе текущей рыночной цены
        с заданным процентом снижения для повышения вероятности исполнения.

        Args:
            game: Код игры
            items: Список предметов с названиями
            price_reduction_percent: Процент снижения от рыночной цены
                (по умолчанию 5%)
            max_targets: Максимальное количество таргетов для создания
            use_aggregated_prices: Использовать API v1.1.0 aggregated-prices
                для эффективности
            min_liquidity_score: Минимальный балл ликвидности (0-100)

        Returns:
            Список результатов создания таргетов

        Example:
            >>> items = [
            ...     {"title": "AK-47 | Redline (Field-Tested)"},
            ...     {"title": "AWP | Asiimov (Field-Tested)"},
            ... ]
            >>> results = await manager.create_smart_targets("csgo", items, price_reduction_percent=5.0)

        """
        logger.info(
            f"Создание {len(items)} умных таргетов для {game} "
            f"с снижением цены на {price_reduction_percent}%",
        )

        results = []
        created_count = 0

        # Используем новый API v1.1.0 для массового получения цен (эффективнее)
        if use_aggregated_prices and len(items) > 1:
            try:
                titles = [
                    str(item.get("title")) for item in items[:max_targets] if item.get("title")
                ]

                # Получаем агрегированные цены одним запросом
                aggregated = await self.api.get_aggregated_prices_bulk(
                    game=game,
                    titles=titles,
                    limit=len(titles),
                )

                if aggregated and "aggregatedPrices" in aggregated:
                    price_map = {
                        price_data["title"]: float(price_data["offerBestPrice"]) / 100
                        for price_data in aggregated["aggregatedPrices"]
                    }

                    # Создаем таргеты на основе агрегированных цен
                    for item in items[:max_targets]:
                        title = item.get("title")
                        if not title or title not in price_map:
                            continue

                        # Проверка ликвидности
                        if self.enable_liquidity_filter and self.liquidity_analyzer:
                            try:
                                metrics = await self.liquidity_analyzer.analyze_item_liquidity(
                                    item_title=title,
                                    game=game,
                                )
                                if metrics.liquidity_score < min_liquidity_score:
                                    logger.info(
                                        f"Пропущен предмет '{title}': "
                                        f"низкая ликвидность "
                                        f"({metrics.liquidity_score})"
                                    )
                                    continue
                            except Exception as e:
                                logger.warning(f"Ошибка проверки ликвидности для '{title}': {e}")

                        market_price = price_map[title]
                        target_price = market_price * (1 - price_reduction_percent / 100)
                        target_price = max(0.10, round(target_price, 2))

                        logger.info(
                            f"Создание таргета для '{title}': "
                            f"рынок ${market_price:.2f} -> "
                            f"таргет ${target_price:.2f}",
                        )

                        # Автоматическое извлечение атрибутов если не указаны
                        target_attrs = item.get("attrs")
                        if not target_attrs:
                            target_attrs = self._extract_attributes_from_title(game, title)
                            if target_attrs:
                                logger.info(
                                    f"Автоматически извлечены атрибуты для '{title}': {target_attrs}"
                                )

                        result = await self.create_target(
                            game=game,
                            title=title,
                            price=target_price,
                            amount=item.get("amount", 1),
                            attrs=target_attrs,
                        )

                        results.append(result)
                        if result.get("success"):
                            created_count += 1

                        await asyncio.sleep(0.5)

                    logger.info(
                        f"Создано {created_count} из {len(items)} умных таргетов (aggregated API)",
                    )
                    return results

            except Exception as e:
                logger.warning(
                    f"Ошибка при использовании aggregated prices: {e!s}, "
                    "переключаюсь на стандартный метод"
                )

        # Фоллбэк: стандартный метод (по одному запросу на предмет)
        for item in items[:max_targets]:
            title = item.get("title")
            if not title:
                logger.warning(f"Пропущен предмет без названия: {item}")
                continue

            # Проверка ликвидности
            if self.enable_liquidity_filter and self.liquidity_analyzer:
                try:
                    metrics = await self.liquidity_analyzer.analyze_item_liquidity(
                        item_title=title,
                        game=game,
                    )
                    if metrics.liquidity_score < min_liquidity_score:
                        logger.info(
                            f"Пропущен предмет '{title}': "
                            f"низкая ликвидность ({metrics.liquidity_score})"
                        )
                        continue
                except Exception as e:
                    logger.warning(f"Ошибка проверки ликвидности для '{title}': {e}")

            try:
                # Получаем текущую рыночную цену
                market_items = await self.api.get_market_items(
                    game=game,
                    title=title,
                    limit=1,
                    sort="price",
                )

                if not market_items or "objects" not in market_items or not market_items["objects"]:
                    logger.warning(
                        f"Не найден предмет на маркете: {title}",
                    )
                    results.append(
                        {
                            "title": title,
                            "success": False,
                            "error": "Предмет не найден на маркете",
                        },
                    )
                    continue

                # Получаем цену первого (самого дешевого) предмета
                cheapest = market_items["objects"][0]
                market_price = float(cheapest["price"]["USD"]) / 100

                # Рассчитываем цену таргета
                target_price = market_price * (1 - price_reduction_percent / 100)

                # Минимальная цена $0.10
                target_price = max(0.10, round(target_price, 2))

                logger.info(
                    f"Создание таргета для '{title}': "
                    f"рынок ${market_price:.2f} -> "
                    f"таргет ${target_price:.2f}",
                )

                # Автоматическое извлечение атрибутов если не указаны
                target_attrs = item.get("attrs")
                if not target_attrs:
                    target_attrs = self._extract_attributes_from_title(game, title)
                    if target_attrs:
                        logger.info(
                            f"Автоматически извлечены атрибуты для '{title}': {target_attrs}"
                        )

                # Создаем таргет
                result = await self.create_target(
                    game=game,
                    title=title,
                    price=target_price,
                    amount=item.get("amount", 1),
                    attrs=target_attrs,
                )

                results.append(result)

                if result.get("success"):
                    created_count += 1

                # Задержка для rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                logger.exception(f"Ошибка при создании таргета для '{title}': {e!s}")
                results.append(
                    {"title": title, "success": False, "error": str(e)},
                )

        logger.info(
            f"Создано {created_count} из {len(items)} умных таргетов",
        )

        return results

    async def get_closed_targets(
        self,
        limit: int = 50,
        status: str | None = None,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Получить историю закрытых таргетов.

        Args:
            limit: Максимальное количество результатов
            status: Фильтр по статусу ('successful', 'reverted',
                'trade_protected')
            days: Количество дней истории (по умолчанию 7)

        Returns:
            Список закрытых таргетов

        Example:
            >>> closed = await manager.get_closed_targets(limit=20, status="successful")
            >>> for target in closed:
            ...     print(f"{target['title']}: ${target['price']:.2f}")

        """
        logger.info(
            f"Получение истории закрытых таргетов (лимит: {limit}, дни: {days})",
        )

        try:
            # Рассчитываем временные рамки
            current_time = int(time.time())
            days_ago = current_time - (days * 24 * 60 * 60)

            result = await self.api.get_closed_targets(
                limit=limit,
                status=status,
                from_timestamp=days_ago,
                to_timestamp=current_time,
            )

            if not result or "Trades" not in result:
                logger.info("Не найдено закрытых таргетов")
                return []

            targets = []
            for trade in result["Trades"]:
                price_data = trade.get("Price", {})
                price = float(price_data.get("Amount", 0)) / 100

                targets.append(
                    {
                        "target_id": trade.get("TargetID"),
                        "title": trade.get("Title"),
                        "price": price,
                        "status": trade.get("Status"),
                        "closed_at": trade.get("ClosedAt"),
                        "created_at": trade.get("CreatedAt"),
                    },
                )

            logger.info(f"Найдено {len(targets)} закрытых таргетов")
            return targets

        except Exception as e:
            logger.exception(f"Ошибка при получении истории таргетов: {e!s}")
            return []

    async def get_target_statistics(
        self,
        game: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """Получить статистику по таргетам.

        Args:
            game: Код игры
            days: Период для статистики в днях

        Returns:
            Словарь со статистикой

        Example:
            >>> stats = await manager.get_target_statistics("csgo", days=30)
            >>> print(f"Успешных: {stats['successful_count']}")
            >>> print(f"Средняя цена: ${stats['average_price']:.2f}")

        """
        logger.info(f"Получение статистики таргетов для {game} за {days} дней")

        # Получаем активные таргеты
        active = await self.get_user_targets(game, status="active")

        # Получаем закрытые таргеты
        closed = await self.get_closed_targets(limit=100, days=days)

        # Фильтруем успешные
        successful = [t for t in closed if t.get("status") == "successful"]

        # Рассчитываем статистику
        stats = {
            "game": game,
            "period_days": days,
            "active_count": len(active),
            "closed_count": len(closed),
            "successful_count": len(successful),
            "success_rate": ((len(successful) / len(closed) * 100) if closed else 0.0),
            "average_price": (
                sum(t["price"] for t in successful) / len(successful) if successful else 0.0
            ),
            "total_spent": sum(t["price"] for t in successful),
        }

        logger.info(
            f"Статистика: активных {stats['active_count']}, "
            f"успешных {stats['successful_count']}, "
            f"успешность {stats['success_rate']:.1f}%",
        )

        return stats

    async def analyze_target_competition(
        self,
        game: str,
        title: str,
    ) -> dict[str, Any]:
        """Анализ конкуренции для создания таргета (API v1.1.0).

        Использует новый эндпоинт targets-by-title для анализа
        существующих buy orders и определения оптимальной цены таргета.

        Args:
            game: Код игры
            title: Название предмета

        Returns:
            Словарь с анализом конкуренции

        Example:
            >>> analysis = await manager.analyze_target_competition(
            ...     "csgo", "AK-47 | Redline (Field-Tested)"
            ... )
            >>> print(f"Конкурентов: {analysis['total_orders']}")
            >>> print(f"Лучшая цена: ${analysis['best_price']:.2f}")
            >>> print(f"Рекомендуемая цена: ${analysis['recommended_price']:.2f}")

        """
        logger.info(f"Анализ конкуренции для '{title}' в {game}")

        try:
            # Получаем существующие таргеты для предмета
            existing_targets = await self.get_targets_by_title(game, title)

            # Получаем агрегированные данные о ценах
            aggregated = await self.api.get_aggregated_prices_bulk(
                game=game,
                titles=[title],
                limit=1,
            )

            analysis: dict[str, Any] = {
                "title": title,
                "game": game,
                "total_orders": len(existing_targets),
                "best_price": 0.0,
                "average_price": 0.0,
                "market_offer_price": 0.0,
                "recommended_price": 0.0,
                "competition_level": "low",
                "strategy": "",
            }

            best_price = 0.0

            # Анализируем существующие таргеты
            if existing_targets:
                prices = [float(t["price"]) for t in existing_targets]
                best_price = max(prices)
                analysis["best_price"] = best_price
                analysis["average_price"] = sum(prices) / len(prices)

                # Определяем уровень конкуренции
                if len(existing_targets) < 5:
                    analysis["competition_level"] = "low"
                elif len(existing_targets) < 15:
                    analysis["competition_level"] = "medium"
                else:
                    analysis["competition_level"] = "high"

            # Получаем рыночную цену
            if aggregated and "aggregatedPrices" in aggregated:
                price_data = aggregated["aggregatedPrices"][0]
                market_offer_price = float(price_data["offerBestPrice"]) / 100
                analysis["market_offer_price"] = market_offer_price

                # Рассчитываем рекомендуемую цену
                if best_price > 0:
                    # Если есть конкуренты, ставим чуть выше лучшей цены
                    analysis["recommended_price"] = round(
                        min(
                            best_price + 0.10,
                            market_offer_price * 0.95,
                        ),
                        2,
                    )
                    analysis["strategy"] = (
                        f"Рекомендуется цена выше лучшего таргета (${best_price:.2f}) но ниже рынка"
                    )
                else:
                    # Нет конкурентов, ставим на 5-7% ниже рынка
                    analysis["recommended_price"] = round(market_offer_price * 0.93, 2)
                    analysis["strategy"] = (
                        "Конкурентов нет, рекомендуется 7% снижение от рыночной цены"
                    )

            logger.info(
                f"Анализ завершен: конкурентов {analysis['total_orders']}, "
                f"рекомендуемая цена ${analysis['recommended_price']:.2f}"
            )

            return analysis

        except Exception as e:
            logger.exception(f"Ошибка при анализе конкуренции для '{title}': {e!s}")
            return {
                "title": title,
                "error": str(e),
            }

    async def assess_competition(
        self,
        game: str,
        title: str,
        max_competition: int = 3,
        price_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Оценить уровень конкуренции для создания buy order.

        Позволяет определить, стоит ли создавать таргет для данного предмета
        на основе количества существующих buy orders.

        Args:
            game: Код игры (csgo, dota2, tf2, rust)
            title: Название предмета
            max_competition: Максимально допустимое количество конкурирующих ордеров.
                Если ордеров больше - рекомендуется пропустить предмет.
            price_threshold: Порог цены для фильтрации (в USD).
                Если указан, учитываются только ордера с ценой >= порога.

        Returns:
            Dict[str, Any]: Результат оценки конкуренции

        Response format:
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "game": "csgo",
                "should_proceed": True/False,
                "competition_level": "low" | "medium" | "high",
                "total_orders": 5,
                "total_amount": 15,
                "best_price": 8.50,
                "recommendation": "Низкая конкуренция - рекомендуется создать таргет",
                "suggested_price": 8.55,  # Рекомендуемая цена (чуть выше лучшего ордера)
            }

        Example:
            >>> result = await manager.assess_competition(
            ...     game="csgo",
            ...     title="AK-47 | Redline (Field-Tested)",
            ...     max_competition=3
            ... )
            >>> if result["should_proceed"]:
            ...     await manager.create_target(...)
            >>> else:
            ...     print(f"Пропускаем: {result['recommendation']}")

        """
        logger.info(
            f"Оценка конкуренции для '{title}' (игра: {game}, макс. конкуренция: {max_competition})"
        )

        # Конвертируем игру в gameId
        game_ids = {
            "csgo": "a8db",
            "dota2": "9a92",
            "tf2": "tf2",
            "rust": "rust",
        }
        game_id = game_ids.get(game.lower(), game)

        try:
            # Получаем данные о конкуренции через API
            competition = await self.api.get_buy_orders_competition(
                game_id=game_id,
                title=title,
                price_threshold=price_threshold,
            )

            # Извлекаем ключевые метрики
            total_orders = competition.get("total_orders", 0)
            total_amount = competition.get("total_amount", 0)
            competition_level = competition.get("competition_level", "unknown")
            best_price = competition.get("best_price", 0.0)
            average_price = competition.get("average_price", 0.0)

            # Определяем, стоит ли продолжать
            should_proceed = total_orders <= max_competition

            # Формируем рекомендацию
            if total_orders == 0:
                recommendation = "Нет конкурентов - отличная возможность для таргета"
                suggested_price = None  # Нужно получить рыночную цену отдельно
            elif should_proceed:
                recommendation = (
                    f"Низкая конкуренция ({total_orders} ордеров) - "
                    "рекомендуется создать таргет"
                )
                # Предлагаем цену на $0.05-$0.10 выше лучшего ордера для приоритета
                suggested_price = round(best_price + 0.05, 2) if best_price > 0 else None
            else:
                recommendation = (
                    f"Высокая конкуренция ({total_orders} ордеров, "
                    f"{total_amount} заявок) - рекомендуется пропустить или "
                    f"увеличить цену выше ${best_price:.2f}"
                )
                # Предлагаем цену на 3-5% выше лучшего ордера для "перебивания"
                suggested_price = round(best_price * 1.03, 2) if best_price > 0 else None

            result = {
                "title": title,
                "game": game,
                "should_proceed": should_proceed,
                "competition_level": competition_level,
                "total_orders": total_orders,
                "total_amount": total_amount,
                "best_price": best_price,
                "average_price": average_price,
                "recommendation": recommendation,
                "suggested_price": suggested_price,
                "max_competition_threshold": max_competition,
                "raw_data": competition,
            }

            logger.info(
                f"Результат оценки для '{title}': "
                f"proceed={should_proceed}, level={competition_level}, "
                f"orders={total_orders}"
            )

            return result

        except Exception as e:
            logger.exception(f"Ошибка при оценке конкуренции для '{title}': {e}")
            return {
                "title": title,
                "game": game,
                "should_proceed": False,  # При ошибке лучше не рисковать
                "competition_level": "unknown",
                "total_orders": 0,
                "total_amount": 0,
                "best_price": 0.0,
                "average_price": 0.0,
                "recommendation": f"Ошибка при оценке: {e}. Рекомендуется повторить позже.",
                "suggested_price": None,
                "error": str(e),
            }

    async def filter_low_competition_items(
        self,
        game: str,
        items: list[dict[str, Any]],
        max_competition: int = 3,
    ) -> list[dict[str, Any]]:
        """Фильтрует список предметов, оставляя только с низкой конкуренцией.

        Args:
            game: Код игры
            items: Список предметов для проверки (каждый должен иметь поле 'title')
            max_competition: Максимально допустимое количество конкурирующих ордеров

        Returns:
            Список предметов с низкой конкуренцией (добавляется поле 'competition')

        Example:
            >>> items = [
            ...     {"title": "AK-47 | Redline (Field-Tested)", "price": 8.50},
            ...     {"title": "AWP | Asiimov (Field-Tested)", "price": 45.00},
            ... ]
            >>> filtered = await manager.filter_low_competition_items("csgo", items)
            >>> for item in filtered:
            ...     print(f"{item['title']}: конкуренция {item['competition']['competition_level']}")

        """
        logger.info(
            f"Фильтрация {len(items)} предметов по конкуренции (макс: {max_competition})"
        )

        filtered_items = []

        for item in items:
            title = item.get("title")
            if not title:
                logger.warning(f"Пропущен предмет без названия: {item}")
                continue

            # Оцениваем конкуренцию для каждого предмета
            competition = await self.assess_competition(
                game=game,
                title=title,
                max_competition=max_competition,
            )

            if competition.get("should_proceed", False):
                # Добавляем данные о конкуренции к предмету
                item_with_competition = {**item, "competition": competition}
                filtered_items.append(item_with_competition)
                logger.debug(
                    f"✓ Предмет '{title}' прошел фильтр: "
                    f"{competition['total_orders']} ордеров"
                )
            else:
                logger.debug(
                    f"✗ Предмет '{title}' отфильтрован: "
                    f"{competition['total_orders']} ордеров (> {max_competition})"
                )

            # Небольшая задержка для rate limiting
            await asyncio.sleep(0.3)

        logger.info(
            f"Фильтрация завершена: {len(filtered_items)}/{len(items)} "
            f"предметов с низкой конкуренцией"
        )

        return filtered_items

    def _validate_attributes(self, game: str, attrs: dict[str, Any]) -> None:
        """Валидация атрибутов таргета.

        Args:
            game: Код игры
            attrs: Словарь атрибутов

        Raises:
            ValueError: Если атрибуты невалидны
        """
        if not attrs:
            return

        # Валидация для CS:GO/CS2
        if game in ("csgo", "a8db", "cs2"):
            # Проверка floatPartValue
            if "floatPartValue" in attrs:
                try:
                    float_val = float(attrs["floatPartValue"])
                    if not (0 <= float_val <= 1):
                        raise ValueError("floatPartValue должен быть от 0 до 1")
                except (TypeError, ValueError):
                    raise ValueError("floatPartValue должен быть числом")

            # Проверка paintSeed
            if "paintSeed" in attrs:
                try:
                    seed = int(attrs["paintSeed"])
                    if seed < 0:
                        raise ValueError("paintSeed должен быть положительным")
                except (TypeError, ValueError):
                    raise ValueError("paintSeed должен быть целым числом")

    def _extract_attributes_from_title(self, game: str, title: str) -> dict[str, Any]:
        """Извлечение атрибутов из названия предмета.

        Args:
            game: Код игры
            title: Название предмета

        Returns:
            Словарь атрибутов
        """
        attrs = {}

        if game in ("csgo", "a8db", "cs2"):
            # Извлечение фазы (Doppler)
            # Пример: "Karambit | Doppler (Factory New) Phase 2"
            phase_match = re.search(r"Phase\s+(\d+)", title, re.IGNORECASE)
            if phase_match:
                attrs["phase"] = f"Phase {phase_match.group(1)}"

            # Ruby / Sapphire / Black Pearl / Emerald
            if "Ruby" in title:
                attrs["phase"] = "Ruby"
            elif "Sapphire" in title:
                attrs["phase"] = "Sapphire"
            elif "Black Pearl" in title:
                attrs["phase"] = "Black Pearl"
            elif "Emerald" in title:
                attrs["phase"] = "Emerald"

        return attrs

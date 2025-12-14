"""Менеджер таргетов (buy orders) на DMarket.

Основной класс для управления таргетами.
"""

import logging
import time
from typing import TYPE_CHECKING, Any

from src.dmarket.liquidity_analyzer import LiquidityAnalyzer

from .competition import (
    analyze_target_competition,
    assess_competition,
    filter_low_competition_items,
)
from .validators import GAME_IDS, extract_attributes_from_title, validate_attributes


if TYPE_CHECKING:
    from src.interfaces import IDMarketAPI


logger = logging.getLogger(__name__)


class TargetManager:
    """Менеджер для работы с таргетами (buy orders) на DMarket.

    Таргеты позволяют создавать заявки на покупку предметов по заданной цене.
    При появлении подходящего предмета происходит автоматическая покупка.

    Supports Dependency Injection via IDMarketAPI Protocol interface.

    Attributes:
        api: Экземпляр DMarket API клиента (implements IDMarketAPI Protocol)

    """

    def __init__(
        self,
        api_client: "IDMarketAPI",
        enable_liquidity_filter: bool = True,
    ) -> None:
        """Инициализация менеджера таргетов.

        Args:
            api_client: DMarket API клиент (implements IDMarketAPI Protocol)
            enable_liquidity_filter: Включить фильтрацию по ликвидности

        """
        self.api = api_client
        self.enable_liquidity_filter = enable_liquidity_filter
        self.liquidity_analyzer: LiquidityAnalyzer | None = None

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

        """
        logger.info(
            f"Создание таргета: {title} по цене ${price:.2f} (игра: {game})",
        )

        # Валидация параметров
        if not title or not title.strip():
            msg = "Название предмета не может быть пустым"
            raise ValueError(msg)

        if price <= 0:
            msg = f"Цена должна быть больше 0, получено: {price}"
            raise ValueError(msg)

        if amount < 1 or amount > 100:
            msg = f"Количество должно быть от 1 до 100, получено: {amount}"
            raise ValueError(msg)

        # Валидация атрибутов
        validate_attributes(game, attrs)

        # Конвертируем игру в gameId
        game_id = GAME_IDS.get(game.lower(), game)

        # Извлекаем атрибуты из названия, если не указаны
        if not attrs:
            attrs = extract_attributes_from_title(game, title)

        # Конвертируем цену в центы
        price_cents = int(price * 100)

        # Формируем тело запроса
        body = {
            "gameId": game_id,
            "title": title,
            "price": str(price_cents),
            "amount": str(amount),
        }

        # Добавляем атрибуты, если есть
        if attrs:
            body["attrs"] = attrs

        try:
            result = await self.api.create_target(body)
            logger.info(f"Таргет создан успешно: {result}")
            return result
        except Exception as e:
            logger.exception(f"Ошибка при создании таргета: {e}")
            raise

    async def get_user_targets(
        self,
        game: str | None = None,
        status: str = "active",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Получить таргеты пользователя.

        Args:
            game: Код игры (опционально)
            status: Статус таргетов (active, inactive, all)
            limit: Максимальное количество
            offset: Смещение для пагинации

        Returns:
            Список таргетов

        """
        logger.info(f"Получение таргетов: game={game}, status={status}")

        try:
            params: dict[str, Any] = {
                "limit": limit,
                "offset": offset,
            }

            if game:
                game_id = GAME_IDS.get(game.lower(), game)
                params["gameId"] = game_id

            if status != "all":
                params["status"] = status

            result = await self.api.get_user_targets(params)

            targets = result.get("items", [])
            logger.info(f"Получено {len(targets)} таргетов")

            return targets

        except Exception as e:
            logger.exception(f"Ошибка при получении таргетов: {e}")
            return []

    async def delete_target(self, target_id: str) -> bool:
        """Удалить таргет по ID.

        Args:
            target_id: ID таргета

        Returns:
            True если успешно, False иначе

        """
        logger.info(f"Удаление таргета: {target_id}")

        try:
            await self.api.delete_target(target_id)
            logger.info(f"Таргет {target_id} удален")
            return True
        except Exception as e:
            logger.exception(f"Ошибка при удалении таргета {target_id}: {e}")
            return False

    async def delete_all_targets(
        self,
        game: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Удалить все активные таргеты.

        Args:
            game: Код игры (опционально, если не указан - удалит все)
            dry_run: Если True, только покажет что будет удалено

        Returns:
            Результат удаления

        """
        logger.info(f"Удаление всех таргетов: game={game}, dry_run={dry_run}")

        targets = await self.get_user_targets(game=game, status="active")

        if dry_run:
            return {
                "dry_run": True,
                "would_delete": len(targets),
                "targets": targets[:10],  # Показываем первые 10
            }

        deleted = 0
        failed = 0

        for target in targets:
            target_id = target.get("id")
            if target_id:
                if await self.delete_target(target_id):
                    deleted += 1
                else:
                    failed += 1

        return {
            "deleted": deleted,
            "failed": failed,
            "total": len(targets),
        }

    async def get_targets_by_title(
        self,
        game: str,
        title: str,
    ) -> list[dict[str, Any]]:
        """Получить существующие таргеты для предмета.

        Args:
            game: Код игры
            title: Название предмета

        Returns:
            Список таргетов

        """
        logger.info(f"Поиск таргетов для '{title}' в {game}")

        try:
            game_id = GAME_IDS.get(game.lower(), game)
            result = await self.api.get_targets_by_title(game=game_id, title=title)
            return result.get("items", [])
        except Exception as e:
            logger.exception(f"Ошибка при поиске таргетов: {e}")
            return []

    async def create_smart_targets(
        self,
        game: str,
        items: list[dict[str, Any]],
        profit_margin: float = 0.15,
        max_targets: int = 10,
        check_competition: bool = True,
    ) -> list[dict[str, Any]]:
        """Создать умные таргеты на основе списка предметов.

        Автоматически рассчитывает оптимальную цену с учетом:
        - Текущей рыночной цены
        - Желаемой маржи прибыли
        - Комиссии DMarket (7%)
        - Конкуренции (опционально)

        Args:
            game: Код игры
            items: Список предметов с ценами
            profit_margin: Желаемая маржа прибыли (по умолчанию 15%)
            max_targets: Максимальное количество таргетов
            check_competition: Проверять конкуренцию перед созданием

        Returns:
            Список результатов создания

        """
        logger.info(
            f"Создание умных таргетов: {len(items)} предметов, "
            f"маржа {profit_margin * 100:.0f}%, макс {max_targets}"
        )

        results = []
        created = 0

        for item in items[:max_targets]:
            title = item.get("title")
            market_price = item.get("price", 0)

            if not title or market_price <= 0:
                continue

            # Рассчитываем цену покупки
            # Целевая цена = рыночная цена / (1 + маржа + комиссия)
            commission = 0.07  # 7% комиссия DMarket
            target_price = round(market_price / (1 + profit_margin + commission), 2)

            # Проверяем конкуренцию
            if check_competition:
                competition = await self.assess_competition(
                    game=game,
                    title=title,
                    max_competition=3,
                )

                if not competition.get("should_proceed", False):
                    logger.info(f"Пропуск '{title}': высокая конкуренция")
                    results.append({
                        "title": title,
                        "status": "skipped",
                        "reason": "high_competition",
                        "competition": competition,
                    })
                    continue

                # Если есть лучшая цена конкурентов, корректируем
                best_price = competition.get("best_price", 0)
                if best_price > target_price:
                    target_price = round(best_price + 0.05, 2)

            try:
                result = await self.create_target(
                    game=game,
                    title=title,
                    price=target_price,
                    amount=1,
                )
                results.append({
                    "title": title,
                    "status": "created",
                    "price": target_price,
                    "result": result,
                })
                created += 1

                # Задержка между созданиями
                await self._delay(0.5)

            except Exception as e:
                results.append({
                    "title": title,
                    "status": "error",
                    "error": str(e),
                })

        logger.info(f"Создано {created}/{len(items)} умных таргетов")
        return results

    async def get_closed_targets(
        self,
        limit: int = 50,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Получить историю закрытых таргетов.

        Args:
            limit: Максимальное количество
            days: Период в днях

        Returns:
            Список закрытых таргетов

        """
        logger.info(f"Получение истории таргетов за {days} дней")

        try:
            # Рассчитываем временной диапазон
            end_time = int(time.time())
            start_time = end_time - (days * 24 * 60 * 60)

            result = await self.api.get_closed_targets(
                limit=limit,
                start_time=start_time,
                end_time=end_time,
            )

            targets = []
            for trade in result.get("trades", []):
                targets.append({
                    "id": trade.get("TargetID"),
                    "title": trade.get("Title"),
                    "price": float(trade.get("Price", 0)) / 100,
                    "game": trade.get("GameID"),
                    "status": trade.get("Status"),
                    "closed_at": trade.get("ClosedAt"),
                    "created_at": trade.get("CreatedAt"),
                })

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
            f"успешность {stats['success_rate']:.1f}%"
        )

        return stats

    async def analyze_target_competition(
        self,
        game: str,
        title: str,
    ) -> dict[str, Any]:
        """Анализ конкуренции для создания таргета.

        Args:
            game: Код игры
            title: Название предмета

        Returns:
            Словарь с анализом конкуренции

        """
        return await analyze_target_competition(self.api, game, title)

    async def assess_competition(
        self,
        game: str,
        title: str,
        max_competition: int = 3,
        price_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Оценить уровень конкуренции для создания buy order.

        Args:
            game: Код игры
            title: Название предмета
            max_competition: Максимально допустимое количество ордеров
            price_threshold: Порог цены для фильтрации

        Returns:
            Результат оценки конкуренции

        """
        return await assess_competition(self.api, game, title, max_competition, price_threshold)

    async def filter_low_competition_items(
        self,
        game: str,
        items: list[dict[str, Any]],
        max_competition: int = 3,
        request_delay: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Фильтрует список предметов по конкуренции.

        Args:
            game: Код игры
            items: Список предметов
            max_competition: Максимально допустимое количество ордеров
            request_delay: Задержка между запросами

        Returns:
            Список предметов с низкой конкуренцией

        """
        return await filter_low_competition_items(
            self.api, game, items, max_competition, request_delay
        )

    async def _delay(self, seconds: float) -> None:
        """Задержка между операциями."""
        import asyncio

        await asyncio.sleep(seconds)


__all__ = [
    "TargetManager",
]

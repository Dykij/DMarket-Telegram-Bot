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
import time
from typing import Any

from .dmarket_api import DMarketAPI


logger = logging.getLogger(__name__)


class TargetManager:
    """Менеджер для работы с таргетами (buy orders) на DMarket.

    Таргеты позволяют создавать заявки на покупку предметов по заданной цене.
    При появлении подходящего предмета происходит автоматическая покупка.

    Attributes:
        api: Экземпляр DMarket API клиента

    """

    def __init__(self, api_client: DMarketAPI) -> None:
        """Инициализация менеджера таргетов.

        Args:
            api_client: Настроенный клиент DMarket API

        """
        self.api = api_client
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
            ...     game='csgo',
            ...     title='AK-47 | Redline (Field-Tested)',
            ...     price=8.00,
            ...     amount=1
            ... )

        """
        logger.info(
            f"Создание таргета: {title} по цене ${price:.2f} (игра: {game})",
        )

        # Валидация параметров
        if price <= 0:
            msg = f"Цена должна быть больше 0, получено: {price}"
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
            >>> targets = await manager.get_user_targets('csgo', 'active')
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
            >>> success = await manager.delete_target('target_123')
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
            >>> result = await manager.delete_all_targets('csgo', confirm=True)
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
            >>> targets = await manager.get_targets_by_title(
            ...     'csgo',
            ...     'AK-47 | Redline (Field-Tested)'
            ... )
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
    ) -> list[dict[str, Any]]:
        """Автоматически создать умные таргеты для списка предметов.

        Умные таргеты создаются на основе текущей рыночной цены
        с заданным процентом снижения для повышения вероятности исполнения.

        Args:
            game: Код игры
            items: Список предметов с названиями
            price_reduction_percent: Процент снижения от рыночной цены (по умолчанию 5%)
            max_targets: Максимальное количество таргетов для создания

        Returns:
            Список результатов создания таргетов

        Example:
            >>> items = [
            ...     {'title': 'AK-47 | Redline (Field-Tested)'},
            ...     {'title': 'AWP | Asiimov (Field-Tested)'}
            ... ]
            >>> results = await manager.create_smart_targets(
            ...     'csgo',
            ...     items,
            ...     price_reduction_percent=5.0
            ... )

        """
        logger.info(
            f"Создание {len(items)} умных таргетов для {game} "
            f"с снижением цены на {price_reduction_percent}%",
        )

        results = []
        created_count = 0

        for item in items[:max_targets]:
            title = item.get("title")
            if not title:
                logger.warning(f"Пропущен предмет без названия: {item}")
                continue

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
                    f"рынок ${market_price:.2f} -> таргет ${target_price:.2f}",
                )

                # Создаем таргет
                result = await self.create_target(
                    game=game,
                    title=title,
                    price=target_price,
                    amount=item.get("amount", 1),
                    attrs=item.get("attrs"),
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
            status: Фильтр по статусу ('successful', 'reverted', 'trade_protected')
            days: Количество дней истории (по умолчанию 7)

        Returns:
            Список закрытых таргетов

        Example:
            >>> closed = await manager.get_closed_targets(limit=20, status='successful')
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
            >>> stats = await manager.get_target_statistics('csgo', days=30)
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

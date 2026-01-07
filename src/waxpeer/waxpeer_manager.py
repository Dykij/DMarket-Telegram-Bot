"""
Waxpeer Manager - Менеджер торговли на Waxpeer.

Управляет полным жизненным циклом предмета:
покупка на DMarket -> листинг на Waxpeer -> авто-репрайсинг -> продажа.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog

from src.waxpeer.waxpeer_api import WaxpeerAPI, WaxpeerGame


logger = structlog.get_logger(__name__)


@dataclass
class CS2RareFilters:
    """Фильтры для определения редких CS2 скинов."""

    # Float Value пороги
    factory_new_low: float = 0.01  # Double Zero
    factory_new_ultra: float = 0.001  # Triple Zero
    minimal_wear_low: float = 0.0705  # Редкий MW
    battle_scarred_high: float = 0.95  # Blackiimov и подобные

    # Наклейки
    min_sticker_price_usd: float = 50.0
    target_sticker_groups: list[str] = field(
        default_factory=lambda: [
            "Katowice 2014",
            "Katowice 2015",
            "Cologne 2014",
            "Crown (Foil)",
            "Howling Dawn",
            "(Holo)",
            "(Gold)",
        ]
    )

    # Doppler фазы (премиум)
    doppler_phases: list[str] = field(
        default_factory=lambda: [
            "Ruby",
            "Sapphire",
            "Emerald",
            "Black Pearl",
            "Phase 2",
            "Phase 4",
        ]
    )

    # Fade процент
    fade_percentage_min: float = 95.0


@dataclass
class ListingConfig:
    """Конфигурация листинга."""

    # Наценки
    default_markup_percent: float = 10.0  # +10% по умолчанию
    rare_item_markup_percent: float = 25.0  # +25% для редких
    ultra_rare_markup_percent: float = 40.0  # +40% для ультра-редких

    # Undercut
    undercut_amount_usd: float = 0.01  # $0.01

    # Минимальная прибыль
    min_profit_percent: float = 5.0

    # Репрайсинг
    reprice_interval_minutes: int = 30
    max_price_drops: int = 5  # Макс. снижений цены
    price_drop_percent: float = 2.0  # Снижение на 2% каждый раз


@dataclass
class ListedItem:
    """Отслеживание выставленного предмета."""

    asset_id: str
    name: str
    buy_price: Decimal
    list_price: Decimal
    listed_at: datetime
    waxpeer_item_id: str | None = None
    price_drops: int = 0
    is_rare: bool = False
    rare_reason: str | None = None


class WaxpeerManager:
    """
    Менеджер для управления торговлей на Waxpeer.

    Функции:
    - Автоматический листинг после покупки на DMarket
    - Умное ценообразование на основе редкости
    - Авто-репрайсинг (undercut конкурентов)
    - Отслеживание продаж и прибыли
    """

    def __init__(
        self,
        api_key: str,
        filters: CS2RareFilters | None = None,
        listing_config: ListingConfig | None = None,
    ) -> None:
        """
        Инициализация менеджера.

        Args:
            api_key: API ключ Waxpeer
            filters: Фильтры для редких предметов
            listing_config: Конфигурация листинга
        """
        self.api_key = api_key
        self.filters = filters or CS2RareFilters()
        self.config = listing_config or ListingConfig()

        # Отслеживание выставленных предметов
        self._listed_items: dict[str, ListedItem] = {}

        # Статистика
        self._total_listed = 0
        self._total_sold = 0
        self._total_profit = Decimal(0)

    def _evaluate_item_rarity(self, item_data: dict[str, Any]) -> tuple[bool, str | None, float]:
        """
        Оценка редкости предмета CS2.

        Args:
            item_data: Данные о предмете

        Returns:
            Tuple: (is_rare, reason, markup_multiplier)
        """
        title = item_data.get("title", "")
        float_value = item_data.get("float_value", item_data.get("float", 1.0))
        stickers = item_data.get("stickers", [])

        # === Float Value Check ===
        # Triple Zero (0.00x)
        if float_value < self.filters.factory_new_ultra:
            return True, f"Ultra Low Float: {float_value:.6f}", 0.40

        # Double Zero (0.0x)
        if float_value < self.filters.factory_new_low:
            return True, f"Low Float: {float_value:.4f}", 0.25

        # Blackiimov / High BS
        if float_value > self.filters.battle_scarred_high:
            return True, f"High Float (Blackiimov): {float_value:.4f}", 0.20

        # === Sticker Check ===
        if stickers:
            for sticker in stickers:
                sticker_name = (
                    sticker.get("name", "") if isinstance(sticker, dict) else str(sticker)
                )
                for rare_group in self.filters.target_sticker_groups:
                    if rare_group.lower() in sticker_name.lower():
                        # Katowice 2014 Holo = JACKPOT
                        if (
                            "katowice 2014" in sticker_name.lower()
                            and "holo" in sticker_name.lower()
                        ):
                            return True, f"JACKPOT Sticker: {sticker_name}", 0.50

                        return True, f"Rare Sticker: {sticker_name}", 0.20

        # === Doppler Phase Check ===
        if "doppler" in title.lower():
            for phase in self.filters.doppler_phases:
                if phase.lower() in title.lower():
                    # Ruby/Sapphire/Emerald = ULTRA RARE
                    if phase in {"Ruby", "Sapphire", "Emerald", "Black Pearl"}:
                        return True, f"Premium Doppler: {phase}", 0.50
                    return True, f"Doppler {phase}", 0.15

        # === Fade Check ===
        if "fade" in title.lower():
            # Проверка паттерна на высокий Fade
            pattern_id = item_data.get("pattern_id", 0)
            if pattern_id and pattern_id <= 50:  # Высокие Fade
                return True, f"High Fade Pattern: {pattern_id}", 0.20

        return False, None, 0.0

    def _calculate_listing_price(
        self,
        buy_price: Decimal,
        market_min_price: Decimal | None,
        is_rare: bool,
        markup_multiplier: float,
    ) -> Decimal:
        """
        Расчет цены листинга.

        Args:
            buy_price: Цена покупки
            market_min_price: Минимальная цена на рынке
            is_rare: Редкий ли предмет
            markup_multiplier: Множитель наценки

        Returns:
            Цена для листинга
        """
        # Базовая наценка
        if is_rare:
            base_markup = Decimal(str(1 + markup_multiplier))
        else:
            base_markup = Decimal(str(1 + self.config.default_markup_percent / 100))

        # Цена с наценкой от покупки
        price_from_buy = buy_price * base_markup

        # Если есть рыночная цена, используем undercut
        if market_min_price and not is_rare:
            undercut_price = market_min_price - Decimal(str(self.config.undercut_amount_usd))

            # Проверяем минимальную прибыль
            min_acceptable = buy_price * Decimal(str(1 + self.config.min_profit_percent / 100))

            if undercut_price >= min_acceptable:
                return undercut_price

        return price_from_buy

    async def list_cs2_item(
        self,
        asset_id: str,
        item_name: str,
        buy_price: float,
        item_data: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], Decimal, bool, str | None]:
        """
        Выставление CS2 скина на Waxpeer.

        Args:
            asset_id: Steam Asset ID
            item_name: Название предмета
            buy_price: Цена покупки в USD
            item_data: Дополнительные данные о предмете

        Returns:
            Tuple: (api_response, listing_price, is_rare, rare_reason)
        """
        buy_price_decimal = Decimal(str(buy_price))

        # Оценка редкости
        is_rare = False
        rare_reason = None
        markup_multiplier = 0.0

        if item_data:
            is_rare, rare_reason, markup_multiplier = self._evaluate_item_rarity(item_data)

        async with WaxpeerAPI(self.api_key) as api:
            # Получаем рыночную цену
            market_price = await api.get_item_price(item_name)

            # Рассчитываем цену листинга
            listing_price = self._calculate_listing_price(
                buy_price_decimal,
                market_price,
                is_rare,
                markup_multiplier,
            )

            # Листим предмет
            response = await api.list_single_item(
                item_id=asset_id,
                price_usd=listing_price,
                game=WaxpeerGame.CS2,
            )

            # Сохраняем информацию
            self._listed_items[asset_id] = ListedItem(
                asset_id=asset_id,
                name=item_name,
                buy_price=buy_price_decimal,
                list_price=listing_price,
                listed_at=datetime.now(),
                is_rare=is_rare,
                rare_reason=rare_reason,
            )

            self._total_listed += 1

            logger.info(
                "waxpeer_item_listed",
                asset_id=asset_id,
                name=item_name,
                buy_price=float(buy_price_decimal),
                list_price=float(listing_price),
                is_rare=is_rare,
                rare_reason=rare_reason,
            )

            return response, listing_price, is_rare, rare_reason

    async def auto_undercut(self) -> list[dict[str, Any]]:
        """
        Автоматический undercut всех активных листингов.

        Returns:
            Список изменений цен
        """
        changes = []

        async with WaxpeerAPI(self.api_key) as api:
            my_items = await api.get_my_items()

            for item in my_items:
                # Проверяем, есть ли в нашем трекере
                tracked = self._listed_items.get(item.item_id)

                # Пропускаем редкие - не демпингуем
                if tracked and tracked.is_rare:
                    continue

                # Получаем рыночную цену
                market_price = await api.get_item_price(item.name)

                if not market_price:
                    continue

                # Если наша цена выше минимальной - снижаем
                if item.price > market_price:
                    new_price = market_price - Decimal(str(self.config.undercut_amount_usd))

                    # Проверяем минимальную прибыль
                    if tracked:
                        min_price = tracked.buy_price * Decimal(
                            str(1 + self.config.min_profit_percent / 100)
                        )
                        if new_price < min_price:
                            continue

                        tracked.price_drops += 1

                    await api.edit_item_price(item.item_id, new_price)

                    changes.append({
                        "item_id": item.item_id,
                        "name": item.name,
                        "old_price": float(item.price),
                        "new_price": float(new_price),
                    })

                    logger.info(
                        "waxpeer_price_undercut",
                        item_id=item.item_id,
                        name=item.name,
                        old_price=float(item.price),
                        new_price=float(new_price),
                    )

                # Небольшая задержка между запросами
                await asyncio.sleep(0.5)

        return changes

    async def check_scarcity_mode(self, item_name: str, threshold: int = 3) -> bool:
        """
        Проверка режима дефицита.

        Если на рынке меньше threshold предметов,
        можно выставить выше рынка.

        Args:
            item_name: Название предмета
            threshold: Порог дефицита

        Returns:
            True если предмет в дефиците
        """
        async with WaxpeerAPI(self.api_key) as api:
            data = await api.get_market_prices([item_name])
            items_count = len(data.get("items", []))
            return items_count < threshold

    async def get_status(self) -> dict[str, Any]:
        """
        Получение полного статуса.

        Returns:
            Словарь со статусом
        """
        async with WaxpeerAPI(self.api_key) as api:
            balance = await api.get_balance()
            my_items = await api.get_my_items()
            is_online = await api.check_online_status()

            total_listed_value = sum(item.price for item in my_items)

            return {
                "balance_usd": float(balance.wallet),
                "items_listed": len(my_items),
                "total_listed_value": float(total_listed_value),
                "is_online": is_online,
                "session_stats": {
                    "total_listed": self._total_listed,
                    "total_sold": self._total_sold,
                    "total_profit": float(self._total_profit),
                },
                "tracked_items": len(self._listed_items),
            }

    async def get_telegram_status(self) -> str:
        """
        Получение статуса для Telegram.

        Returns:
            Форматированная строка статуса
        """
        status = await self.get_status()

        online_emoji = "🟢" if status["is_online"] else "🔴"

        return (
            f"💰 **Waxpeer Status**\n"
            f"{online_emoji} Статус: {'Online' if status['is_online'] else 'Offline'}\n"
            f"💵 Баланс: ${status['balance_usd']:.2f}\n"
            f"📦 В продаже: {status['items_listed']} скинов\n"
            f"💎 Общая стоимость: ${status['total_listed_value']:.2f}\n"
            f"\n📊 **Статистика сессии:**\n"
            f"• Выставлено: {status['session_stats']['total_listed']}\n"
            f"• Продано: {status['session_stats']['total_sold']}\n"
            f"• Прибыль: ${status['session_stats']['total_profit']:.2f}"
        )

    async def sync_with_sales(self) -> list[dict[str, Any]]:
        """
        Синхронизация с историей продаж для учета прибыли.

        Returns:
            Список новых продаж
        """
        async with WaxpeerAPI(self.api_key) as api:
            sales = await api.get_recent_sales(limit=20)

            new_sales = []
            for sale in sales:
                asset_id = sale.get("item_id", "")
                if asset_id in self._listed_items:
                    tracked = self._listed_items[asset_id]
                    sold_price = Decimal(str(sale.get("price", 0) / 1000))
                    profit = sold_price - tracked.buy_price

                    self._total_sold += 1
                    self._total_profit += profit

                    new_sales.append({
                        "name": tracked.name,
                        "buy_price": float(tracked.buy_price),
                        "sold_price": float(sold_price),
                        "profit": float(profit),
                        "is_rare": tracked.is_rare,
                    })

                    # Удаляем из трекинга
                    del self._listed_items[asset_id]

                    logger.info(
                        "waxpeer_item_sold",
                        name=tracked.name,
                        buy_price=float(tracked.buy_price),
                        sold_price=float(sold_price),
                        profit=float(profit),
                    )

            return new_sales

    async def start_auto_reprice_loop(self, interval_minutes: int | None = None) -> None:
        """
        Запуск цикла авто-репрайсинга.

        Args:
            interval_minutes: Интервал между проверками
        """
        interval = interval_minutes or self.config.reprice_interval_minutes

        logger.info("waxpeer_reprice_loop_started", interval_minutes=interval)

        while True:
            try:
                # Синхронизация продаж
                await self.sync_with_sales()

                # Авто-undercut
                changes = await self.auto_undercut()

                if changes:
                    logger.info(
                        "waxpeer_reprice_complete",
                        changes_count=len(changes),
                    )

            except Exception as e:
                logger.exception("waxpeer_reprice_error", error=str(e))

            await asyncio.sleep(interval * 60)

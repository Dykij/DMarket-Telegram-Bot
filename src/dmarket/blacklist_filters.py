"""Черный список и фильтры для ArbitrageScanner.

Этот модуль содержит фильтры для отсеивания "мусорных" предметов,
которые показывают ложный профит или имеют низкую ликвидность.
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)

# Список запрещенных категорий и ключевых слов
BLACKLIST_KEYWORDS = [
    "souvenir",
    "sticker |",
    "patch |",
    "graffiti |",
    "sealed graffiti",
    "collectible pin",
    "music kit",
    "autograph capsule",
    "souvenir package",
]

# Список редких паттернов, которые сложно оценить
PATTERN_KEYWORDS = [
    "katowice 2014",
    "kato 14",
    "ibuypower",
    "titan holo",
    "reason gaming",
    "vox eminor",
]


class ItemBlacklistFilter:
    """Фильтр черного списка для предметов."""

    def __init__(
        self,
        enable_keyword_filter: bool = True,
        enable_float_filter: bool = True,
        enable_sticker_boost_filter: bool = True,
        enable_pattern_filter: bool = False,
    ):
        """Инициализирует фильтр черного списка.

        Args:
            enable_keyword_filter: Включить фильтр по ключевым словам
            enable_float_filter: Включить фильтр по износу (float)
            enable_sticker_boost_filter: Включить фильтр "переплаты за наклейки"
            enable_pattern_filter: Включить фильтр редких паттернов
        """
        self.enable_keyword_filter = enable_keyword_filter
        self.enable_float_filter = enable_float_filter
        self.enable_sticker_boost_filter = enable_sticker_boost_filter
        self.enable_pattern_filter = enable_pattern_filter

    def is_blacklisted(self, item: dict[str, Any]) -> bool:
        """Проверяет, находится ли предмет в черном списке.

        Args:
            item: Словарь с данными предмета

        Returns:
            True если предмет в черном списке, False иначе
        """
        title = item.get("title", "").lower()

        # 1. Проверка по ключевым словам
        if self.enable_keyword_filter:
            if any(word in title for word in BLACKLIST_KEYWORDS):
                logger.debug(f"⏭ Blacklist (keyword): {title}")
                return True

        # 2. Проверка на редкие флоты (если бот не умеет их перепродавать дороже)
        # Например, очень изношенные "BS" скины часто висят долго
        if self.enable_float_filter:
            profit_percent = item.get("profit_percent", 0)
            if "battle-scarred" in title and profit_percent < 20:
                logger.debug(f"⏭ Blacklist (BS low profit): {title}")
                return True

        # 3. Проверка на "переплату за наклейки"
        # DMarket часто завышает цену, если на скине есть дешевые наклейки
        if self.enable_sticker_boost_filter:
            extra = item.get("extra", {})
            if extra.get("stickers") and item.get("price_is_boosted"):
                logger.debug(f"⏭ Blacklist (sticker boost): {title}")
                return True

        # 4. Проверка на редкие паттерны (опционально)
        # Эти предметы могут иметь завышенную цену из-за редкого паттерна
        if self.enable_pattern_filter:
            if any(pattern in title for pattern in PATTERN_KEYWORDS):
                logger.debug(f"⏭ Blacklist (rare pattern): {title}")
                return True

        return False


class ItemLiquidityFilter:
    """Фильтр ликвидности для предметов."""

    def __init__(
        self,
        min_sales_24h: int = 3,
        min_avg_sales_per_day: float = 0.3,
        max_overprice_ratio: float = 1.5,
    ):
        """Инициализирует фильтр ликвидности.

        Args:
            min_sales_24h: Минимальное количество продаж за 24 часа
            min_avg_sales_per_day: Минимальное среднее количество продаж в день
            max_overprice_ratio: Максимальное отношение текущей цены к рекомендуемой
        """
        self.min_sales_24h = min_sales_24h
        self.min_avg_sales_per_day = min_avg_sales_per_day
        self.max_overprice_ratio = max_overprice_ratio

    def is_liquid(self, item: dict[str, Any]) -> bool:
        """Проверяет ликвидность предмета.

        Args:
            item: Словарь с данными предмета

        Returns:
            True если предмет ликвидный, False иначе
        """
        title = item.get("title", "Unknown")

        # 1. Фильтр по объему продаж (если API отдает данные о продажах за 24ч)
        stats = item.get("statistics", {})
        sales_24h = stats.get("sales24h", 0)

        if sales_24h < self.min_sales_24h:
            logger.debug(f"⏭ Low liquidity (sales_24h={sales_24h}): {title}")
            return False

        # 2. Фильтр по средним продажам в день
        avg_sales = stats.get("avg_sales_per_day", 0)

        if avg_sales < self.min_avg_sales_per_day:
            logger.debug(f"⏭ Low liquidity (avg_sales={avg_sales:.2f}): {title}")
            return False

        # 3. Фильтр по разнице цен (Overpriced)
        # Если цена на 50% выше рекомендуемой — это манипуляция ценой
        suggested_price_data = item.get("suggestedPrice", {})
        current_price_data = item.get("price", {})

        # Поддержка разных форматов API
        if isinstance(suggested_price_data, dict):
            suggested_price = suggested_price_data.get("amount", 0)
        else:
            suggested_price = suggested_price_data or 0

        if isinstance(current_price_data, dict):
            current_price = current_price_data.get("amount", 0)
        else:
            current_price = current_price_data or 0

        if suggested_price > 0:
            overprice_ratio = current_price / suggested_price
            if overprice_ratio > self.max_overprice_ratio:
                logger.debug(f"⏭ Overpriced (ratio={overprice_ratio:.2f}): {title}")
                return False

        return True


class ItemQualityFilter:
    """Комбинированный фильтр качества предметов."""

    def __init__(
        self,
        blacklist_filter: ItemBlacklistFilter | None = None,
        liquidity_filter: ItemLiquidityFilter | None = None,
    ):
        """Инициализирует комбинированный фильтр.

        Args:
            blacklist_filter: Фильтр черного списка (создается по умолчанию)
            liquidity_filter: Фильтр ликвидности (создается по умолчанию)
        """
        self.blacklist_filter = blacklist_filter or ItemBlacklistFilter()
        self.liquidity_filter = liquidity_filter or ItemLiquidityFilter()

    def filter_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Фильтрует список предметов.

        Args:
            items: Список предметов для фильтрации

        Returns:
            Отфильтрованный список предметов
        """
        filtered = []
        stats = {
            "total": len(items),
            "blacklisted": 0,
            "illiquid": 0,
            "passed": 0,
        }

        for item in items:
            # Проверка черного списка
            if self.blacklist_filter.is_blacklisted(item):
                stats["blacklisted"] += 1
                continue

            # Проверка ликвидности
            if not self.liquidity_filter.is_liquid(item):
                stats["illiquid"] += 1
                continue

            filtered.append(item)
            stats["passed"] += 1

        logger.info(
            f"🔍 Filter results: {stats['passed']}/{stats['total']} items passed "
            f"(blacklisted: {stats['blacklisted']}, illiquid: {stats['illiquid']})"
        )

        return filtered

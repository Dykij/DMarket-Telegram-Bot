"""Черный список и фильтры для ArbitrageScanner.

Этот модуль содержит ОБЯЗАТЕЛЬНЫЕ фильтры для отсеивания "мусорных" предметов,
которые показывают ложный профит или имеют низкую ликвидность.

ВАЖНО: Blacklist - это ОБЯЗАТЕЛЬНЫЙ фильтр!
- Предметы из blacklist НИКОГДА не покупаются
- Это защита от убыточных сделок
- В отличие от Whitelist (рекомендательный), Blacklist - строгий запрет

Категории фильтрации:
1. BLACKLIST_KEYWORDS - запрещённые ключевые слова (souvenir, sticker и т.д.)
2. PATTERN_KEYWORDS - редкие паттерны, сложные для оценки (Katowice 2014 и т.д.)
3. Фильтр износа (Battle-Scarred с низким профитом)
4. Фильтр переплаты за наклейки

Updated: January 2026
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)

# ОБЯЗАТЕЛЬНЫЙ список запрещенных категорий и ключевых слов
# Предметы с этими словами НИКОГДА не покупаются
# Updated: January 2026
BLACKLIST_KEYWORDS = [
    # ===== SOUVENIR ПРЕДМЕТЫ (НИЗКАЯ ЛИКВИДНОСТЬ) =====
    "souvenir",
    "souvenir package",
    "souvenir case",

    # ===== НАКЛЕЙКИ И ГРАФФИТИ (НИЗКИЙ ПРОФИТ) =====
    "sticker |",
    "patch |",
    "graffiti |",
    "sealed graffiti",
    "charm |",  # Новые чармы 2025+
    "pin |",

    # ===== КОЛЛЕКЦИОННЫЕ ПРЕДМЕТЫ (НЕСТАБИЛЬНЫЕ ЦЕНЫ) =====
    "collectible pin",
    "music kit",
    "music kit |",
    "autograph capsule",
    "stattrak™ music kit",
    "stattrak music kit",
    "tournament sticker",
    "autograph sticker",

    # ===== КОНТЕЙНЕРЫ И КАПСУЛЫ (СЛОЖНАЯ ОЦЕНКА) =====
    "sticker capsule",
    "patch pack",
    "graffiti box",
    "gift package",
    "weapon case",  # Старые кейсы - низкая ликвидность

    # ===== RUST - НЕЛИКВИДНЫЕ КАТЕГОРИИ =====
    "blueprint",
    "note",
    "photograph",
    "cassette",

    # ===== DOTA 2 - НЕЛИКВИДНЫЕ КАТЕГОРИИ =====
    "gem",
    "inscribed gem",
    "prismatic gem",
    "ethereal gem",
    "kinetic gem",
    "spectator gem",
    "autograph",
    "loading screen",
    "hud skin",
    "announcer",
    "weather",
    "terrain",
    "effigy",
    "emoticon",
    "player card",
    "fantasy item",
    "compendium",

    # ===== TF2 - НЕЛИКВИДНЫЕ КАТЕГОРИИ =====
    "crate",  # Старые крейты
    "salvaged crate",
    "festive crate",
    "robo crate",
    "strange bacon grease",
    "paint can",
    "name tag",
    "description tag",
    "decal tool",
    "gift wrap",
    "backpack expander",
    "dueling mini-game",
    "noise maker",
    "secret saxton",

    # ===== ОБЩИЕ НЕЛИКВИДНЫЕ ПАТТЕРНЫ =====
    "well-worn",  # Сложно продать быстро
    # Note: "battle-scarred" handled separately by float_filter (allows high profit)
    "vanilla",  # Ванильные ножи - особый рынок
]

# ОБЯЗАТЕЛЬНЫЙ список редких паттернов, которые сложно оценить
# Цены на эти предметы могут быть искусственно завышены
# Updated: January 2026
PATTERN_KEYWORDS = [
    # ===== KATOWICE 2014 (ЭКСТРЕМАЛЬНЫЕ ЦЕНЫ) =====
    "katowice 2014",
    "kato 14",
    "kato14",
    "katowice14",

    # ===== РЕДКИЕ КОМАНДЫ (МАНИПУЛЯЦИИ С ЦЕНАМИ) =====
    "ibuypower",
    "ibp holo",
    "titan holo",
    "reason gaming",
    "vox eminor",
    "lgb esports",
    "hellraisers holo",
    "dignitas holo",
    "natus vincere holo",
    "complexity holo",
    "mouseports holo",
    "fnatic holo",
    "ldlc holo",
    "ninjas in pyjamas holo",
    "clan-mystik holo",
    "3dmax holo",

    # ===== РЕДКИЕ ПАТТЕРНЫ (СЛОЖНАЯ ОЦЕНКА) =====
    "blue gem",
    "case hardened",  # Только синие паттерны рискованны
    "fade 100%",
    "max fade",
    "fire & ice",
    "fire and ice",
    "black pearl",
    "ruby",
    "sapphire",
    "emerald",
    "phase",  # Doppler phases требуют особой оценки

    # ===== CROWN FOIL И ДРУГИЕ ДОРОГИЕ НАКЛЕЙКИ =====
    "crown foil",
    "crown (foil)",
    "flammable foil",
    "headhunter foil",
    "swag foil",
    "howling dawn",
    "nelu the bear",
    "phoenix foil",

    # ===== DOTA 2 РЕДКОСТИ =====
    "golden",  # Golden versions могут быть переоценены
    "platinum",
    "crimson",
    "legacy",  # Legacy courier gems
]

# Новый 2026: Список предметов с историей scam/манипуляций
SCAM_RISK_KEYWORDS = [
    "contraband",  # Редкие запрещенные скины
    "discontinued",  # Снятые с производства
    "exclusive",  # Эксклюзивные промо
    "limited",  # Лимитированные издания
    "one of a kind",  # Уникальные предметы
    "1/1",  # Единственные в своем роде
    "factory new★",  # Подозрительная маркировка
]


class ItemBlacklistFilter:
    """Фильтр черного списка для предметов."""

    def __init__(
        self,
        enable_keyword_filter: bool = True,
        enable_float_filter: bool = True,
        enable_sticker_boost_filter: bool = True,
        enable_pattern_filter: bool = False,
        enable_scam_risk_filter: bool = True,
    ):
        """Инициализирует фильтр черного списка.

        Args:
            enable_keyword_filter: Включить фильтр по ключевым словам
            enable_float_filter: Включить фильтр по износу (float)
            enable_sticker_boost_filter: Включить фильтр "переплаты за наклейки"
            enable_pattern_filter: Включить фильтр редких паттернов
            enable_scam_risk_filter: Включить фильтр scam-рисков (2026)
        """
        self.enable_keyword_filter = enable_keyword_filter
        self.enable_float_filter = enable_float_filter
        self.enable_sticker_boost_filter = enable_sticker_boost_filter
        self.enable_pattern_filter = enable_pattern_filter
        self.enable_scam_risk_filter = enable_scam_risk_filter

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

        # 5. Проверка на scam-риски (2026)
        # Предметы с историей манипуляций или мошенничества
        if self.enable_scam_risk_filter:
            if any(risk in title for risk in SCAM_RISK_KEYWORDS):
                logger.debug(f"⏭ Blacklist (scam risk): {title}")
                return True

        return False

    def get_blacklist_reason(self, item: dict[str, Any]) -> str | None:
        """Получает причину блокировки предмета.

        Args:
            item: Словарь с данными предмета

        Returns:
            Причина блокировки или None если предмет не заблокирован
        """
        title = item.get("title", "").lower()

        if self.enable_keyword_filter:
            for word in BLACKLIST_KEYWORDS:
                if word in title:
                    return f"Keyword: {word}"

        if self.enable_float_filter:
            profit_percent = item.get("profit_percent", 0)
            if "battle-scarred" in title and profit_percent < 20:
                return "Battle-Scarred with low profit"

        if self.enable_sticker_boost_filter:
            extra = item.get("extra", {})
            if extra.get("stickers") and item.get("price_is_boosted"):
                return "Sticker price boost detected"

        if self.enable_pattern_filter:
            for pattern in PATTERN_KEYWORDS:
                if pattern in title:
                    return f"Rare pattern: {pattern}"

        if self.enable_scam_risk_filter:
            for risk in SCAM_RISK_KEYWORDS:
                if risk in title:
                    return f"Scam risk: {risk}"

        return None


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

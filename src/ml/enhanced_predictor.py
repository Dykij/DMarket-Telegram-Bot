"""Улучшенный прогнозатор цен с расширенными моделями.

Улучшения на основе профессиональных торговых систем:
1. RandomForest и XGBoost ансамбли
2. Расширенный Feature Engineering
3. Pipeline для защиты от ошибок API
4. Поддержка всех игр: CS2, Dota 2, TF2, Rust

Все библиотеки бесплатные (scikit-learn, xgboost опционально).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
import logging
from pathlib import Path
import pickle
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class GameType(StrEnum):
    """Поддерживаемые игры."""

    CS2 = "cs2"
    CSGO = "csgo"  # Алиас для CS2
    DOTA2 = "dota2"
    TF2 = "tf2"
    RUST = "rust"


class ItemRarity(StrEnum):
    """Редкость предмета."""

    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    MIL_SPEC = "mil_spec"
    RESTRICTED = "restricted"
    CLASSIFIED = "classified"
    COVERT = "covert"
    CONTRABAND = "contraband"
    IMMORTAL = "immortal"  # Dota 2
    ARCANA = "arcana"  # Dota 2
    UNUSUAL = "unusual"  # TF2


class ItemCondition(StrEnum):
    """Состояние предмета (CS2/Rust)."""

    FACTORY_NEW = "factory_new"
    MINIMAL_WEAR = "minimal_wear"
    FIELD_TESTED = "field_tested"
    WELL_WORN = "well_worn"
    BATTLE_SCARRED = "battle_scarred"


@dataclass
class EnhancedFeatures:
    """Расширенные признаки для улучшенной ML модели.

    Включает все базовые признаки + новые:
    - Relative Strength (отношение к индексу рынка)
    - Time Since Last Sale
    - Float/Pattern Score
    - Game-specific признаки
    """

    # === Базовые ценовые признаки ===
    current_price: float
    price_mean_7d: float = 0.0
    price_std_7d: float = 0.0
    price_min_7d: float = 0.0
    price_max_7d: float = 0.0

    # Изменение цены
    price_change_1h: float = 0.0
    price_change_24h: float = 0.0
    price_change_7d: float = 0.0

    # Технические индикаторы
    rsi: float = 50.0
    volatility: float = 0.0
    momentum: float = 0.0

    # Ликвидность
    sales_count_24h: int = 0
    sales_count_7d: int = 0
    avg_sales_per_day: float = 0.0

    # Временные признаки
    hour_of_day: int = 0
    day_of_week: int = 0
    is_weekend: bool = False
    is_peak_hours: bool = False

    # Рыночные условия
    market_depth: float = 0.0
    competition_level: float = 0.0

    # === НОВЫЕ ПРИЗНАКИ ===

    # Relative Strength - отношение цены к индексу рынка игры
    relative_strength: float = 1.0  # >1 = выше рынка, <1 = ниже рынка
    market_index_change: float = 0.0  # % изменения индекса рынка

    # Time Since Last Sale - секунды с последней продажи
    time_since_last_sale: float = 0.0  # секунды
    avg_time_between_sales: float = 0.0  # средний интервал между продажами

    # Float/Pattern Score (для CS2, Rust)
    float_value: float = 0.0  # 0.0-1.0 для CS2
    float_percentile: float = 50.0  # Процентиль float (0-100)
    pattern_index: int = 0  # Индекс паттерна
    pattern_score: float = 0.0  # Оценка редкости паттерна (0-1)

    # Sticker/Charm value (CS2)
    sticker_value: float = 0.0  # Дополнительная стоимость от стикеров
    sticker_count: int = 0

    # Game-specific
    game_type: GameType = GameType.CS2
    item_rarity: ItemRarity = ItemRarity.MIL_SPEC
    item_condition: ItemCondition = ItemCondition.FIELD_TESTED

    # Dota 2 specific
    gem_count: int = 0  # Количество гемов
    inscribed_count: int = 0  # Количество надписей

    # TF2 specific
    is_unusual: bool = False
    effect_value: float = 0.0  # Стоимость эффекта

    # Rust specific
    has_skin: bool = True

    # === DMarket Bonus/Discount признаки (новые из API документации) ===
    # Cumulative Discount - скидка от DMarket
    dmarket_discount: float = 0.0  # Процент скидки (0-100)
    # price.bonus - бонус от DMarket
    dmarket_bonus: float = 0.0  # В USD
    # Флаг "выгодной сделки" по внутренней статистике DMarket
    has_dmarket_discount: bool = False

    # === Lock Status признаки (трейд-бан) ===
    # lockStatus: 0 = доступен сразу, 1 = заблокирован
    lock_status: int = 0
    lock_days_remaining: int = 0
    # Рассчитанный дисконт за lock (3-5%)
    lock_discount: float = 0.0

    # Мета-признаки
    data_quality_score: float = 1.0
    feature_timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_array(self) -> np.ndarray:
        """Преобразовать признаки в numpy массив для ML модели."""
        return np.array([
            # Базовые
            self.current_price,
            self.price_mean_7d,
            self.price_std_7d,
            self.price_change_1h,
            self.price_change_24h,
            self.price_change_7d,
            self.rsi,
            self.volatility,
            self.momentum,
            self.sales_count_24h,
            self.avg_sales_per_day,
            self.hour_of_day,
            self.day_of_week,
            1.0 if self.is_weekend else 0.0,
            1.0 if self.is_peak_hours else 0.0,
            self.market_depth,
            self.competition_level,
            # Новые
            self.relative_strength,
            self.market_index_change,
            self.time_since_last_sale,
            self.avg_time_between_sales,
            self.float_value,
            self.float_percentile,
            self.pattern_score,
            self.sticker_value,
            self.sticker_count,
            self._game_to_numeric(),
            self._rarity_to_numeric(),
            self._condition_to_numeric(),
            self.gem_count,
            1.0 if self.is_unusual else 0.0,
            self.effect_value,
            # DMarket Bonus/Discount (из API документации)
            self.dmarket_discount,
            self.dmarket_bonus,
            1.0 if self.has_dmarket_discount else 0.0,
            # Lock Status
            float(self.lock_status),
            float(self.lock_days_remaining),
            self.lock_discount,
        ], dtype=np.float64)

    def _game_to_numeric(self) -> float:
        """Преобразовать игру в число."""
        game_map = {
            GameType.CS2: 1.0,
            GameType.CSGO: 1.0,
            GameType.DOTA2: 2.0,
            GameType.TF2: 3.0,
            GameType.RUST: 4.0,
        }
        return game_map.get(self.game_type, 1.0)

    def _rarity_to_numeric(self) -> float:
        """Преобразовать редкость в число."""
        rarity_map = {
            ItemRarity.CONSUMER: 0.1,
            ItemRarity.INDUSTRIAL: 0.2,
            ItemRarity.MIL_SPEC: 0.3,
            ItemRarity.RESTRICTED: 0.5,
            ItemRarity.CLASSIFIED: 0.7,
            ItemRarity.COVERT: 0.9,
            ItemRarity.CONTRABAND: 1.0,
            ItemRarity.IMMORTAL: 0.85,
            ItemRarity.ARCANA: 1.0,
            ItemRarity.UNUSUAL: 0.95,
        }
        return rarity_map.get(self.item_rarity, 0.3)

    def _condition_to_numeric(self) -> float:
        """Преобразовать состояние в число."""
        condition_map = {
            ItemCondition.FACTORY_NEW: 1.0,
            ItemCondition.MINIMAL_WEAR: 0.8,
            ItemCondition.FIELD_TESTED: 0.6,
            ItemCondition.WELL_WORN: 0.4,
            ItemCondition.BATTLE_SCARRED: 0.2,
        }
        return condition_map.get(self.item_condition, 0.6)

    @classmethod
    def feature_names(cls) -> list[str]:
        """Получить список названий признаков."""
        return [
            # Базовые
            "current_price",
            "price_mean_7d",
            "price_std_7d",
            "price_change_1h",
            "price_change_24h",
            "price_change_7d",
            "rsi",
            "volatility",
            "momentum",
            "sales_count_24h",
            "avg_sales_per_day",
            "hour_of_day",
            "day_of_week",
            "is_weekend",
            "is_peak_hours",
            "market_depth",
            "competition_level",
            # Новые
            "relative_strength",
            "market_index_change",
            "time_since_last_sale",
            "avg_time_between_sales",
            "float_value",
            "float_percentile",
            "pattern_score",
            "sticker_value",
            "sticker_count",
            "game_type",
            "item_rarity",
            "item_condition",
            "gem_count",
            "is_unusual",
            "effect_value",
        ]


class EnhancedFeatureExtractor:
    """Расширенный экстрактор признаков с поддержкой всех игр."""

    # Пиковые часы торговли (UTC)
    PEAK_HOURS_START = 14
    PEAK_HOURS_END = 21

    # RSI параметры
    RSI_PERIOD = 14

    # Индексы рынка по играм (примерные базовые значения)
    MARKET_INDICES: dict[GameType, float] = {
        GameType.CS2: 100.0,
        GameType.CSGO: 100.0,
        GameType.DOTA2: 50.0,
        GameType.TF2: 30.0,
        GameType.RUST: 40.0,
    }

    def __init__(self):
        """Инициализация экстрактора признаков."""
        self._market_index_cache: dict[GameType, float] = dict(self.MARKET_INDICES)
        self._last_sales_cache: dict[str, datetime] = {}

    def update_market_index(self, game: GameType, index_value: float):
        """Обновить индекс рынка для игры.

        Args:
            game: Тип игры
            index_value: Значение индекса
        """
        self._market_index_cache[game] = index_value

    def extract_features(
        self,
        item_name: str,
        current_price: float,
        game: GameType = GameType.CS2,
        price_history: list[tuple[datetime, float]] | None = None,
        sales_history: list[dict[str, Any]] | None = None,
        market_offers: list[dict[str, Any]] | None = None,
        item_data: dict[str, Any] | None = None,
    ) -> EnhancedFeatures:
        """Извлечь расширенные признаки для предмета.

        Args:
            item_name: Название предмета
            current_price: Текущая цена
            game: Тип игры
            price_history: История цен [(timestamp, price), ...]
            sales_history: История продаж
            market_offers: Текущие предложения на рынке
            item_data: Дополнительные данные о предмете (float, stickers, etc)

        Returns:
            EnhancedFeatures с расширенными признаками
        """
        features = EnhancedFeatures(
            current_price=current_price,
            game_type=game,
        )

        # Временные признаки
        now = datetime.utcnow()
        features.hour_of_day = now.hour
        features.day_of_week = now.weekday()
        features.is_weekend = features.day_of_week >= 5
        features.is_peak_hours = (
            self.PEAK_HOURS_START <= features.hour_of_day < self.PEAK_HOURS_END
        )

        # Базовые ценовые признаки
        if price_history and len(price_history) > 0:
            features = self._extract_price_features(features, price_history, now)
        else:
            features.data_quality_score *= 0.5

        # Признаки продаж
        if sales_history and len(sales_history) > 0:
            features = self._extract_sales_features(features, sales_history, now)
        else:
            features.data_quality_score *= 0.7

        # Рыночные признаки
        if market_offers and len(market_offers) > 0:
            features = self._extract_market_features(features, market_offers)
        else:
            features.data_quality_score *= 0.8

        # Relative Strength
        features = self._extract_relative_strength(features, game)

        # Game-specific признаки
        if item_data:
            features = self._extract_game_specific_features(
                features, game, item_data, item_name
            )

        return features

    def _extract_price_features(
        self,
        features: EnhancedFeatures,
        price_history: list[tuple[datetime, float]],
        now: datetime,
    ) -> EnhancedFeatures:
        """Извлечь ценовые признаки из истории."""
        cutoff_7d = now - timedelta(days=7)
        cutoff_24h = now - timedelta(hours=24)
        cutoff_1h = now - timedelta(hours=1)

        prices_7d = [p for ts, p in price_history if ts >= cutoff_7d]
        prices_24h = [p for ts, p in price_history if ts >= cutoff_24h]
        prices_1h = [p for ts, p in price_history if ts >= cutoff_1h]

        if prices_7d:
            features.price_mean_7d = float(np.mean(prices_7d))
            features.price_std_7d = float(np.std(prices_7d)) if len(prices_7d) > 1 else 0.0
            features.price_min_7d = min(prices_7d)
            features.price_max_7d = max(prices_7d)

            if features.price_mean_7d > 0:
                features.volatility = features.price_std_7d / features.price_mean_7d

        # Изменение цены
        if prices_7d and len(prices_7d) >= 2:
            first_price = prices_7d[0]
            if first_price > 0:
                features.price_change_7d = (
                    (features.current_price - first_price) / first_price
                ) * 100

        if prices_24h and len(prices_24h) >= 2:
            first_price = prices_24h[0]
            if first_price > 0:
                features.price_change_24h = (
                    (features.current_price - first_price) / first_price
                ) * 100

        if prices_1h and len(prices_1h) >= 2:
            first_price = prices_1h[0]
            if first_price > 0:
                features.price_change_1h = (
                    (features.current_price - first_price) / first_price
                ) * 100

        # RSI
        if len(prices_7d) >= self.RSI_PERIOD:
            features.rsi = self._calculate_rsi(prices_7d)

        # Momentum
        if len(prices_24h) >= 2:
            features.momentum = self._calculate_momentum(prices_24h)

        return features

    def _extract_sales_features(
        self,
        features: EnhancedFeatures,
        sales_history: list[dict[str, Any]],
        now: datetime,
    ) -> EnhancedFeatures:
        """Извлечь признаки из истории продаж с учётом времени."""
        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)

        sales_24h = 0
        sales_7d = 0
        sale_times: list[datetime] = []

        for sale in sales_history:
            sale_time = sale.get("timestamp") or sale.get("date")
            if isinstance(sale_time, str):
                try:
                    sale_time = datetime.fromisoformat(sale_time.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
            elif isinstance(sale_time, (int, float)):
                sale_time = datetime.utcfromtimestamp(sale_time)

            if sale_time:
                sale_times.append(sale_time)
                if sale_time >= cutoff_7d:
                    sales_7d += 1
                    if sale_time >= cutoff_24h:
                        sales_24h += 1

        features.sales_count_24h = sales_24h
        features.sales_count_7d = sales_7d
        features.avg_sales_per_day = sales_7d / 7.0 if sales_7d > 0 else 0.0

        # Time Since Last Sale (НОВОЕ)
        if sale_times:
            last_sale = max(sale_times)
            features.time_since_last_sale = (now - last_sale).total_seconds()

            # Среднее время между продажами
            if len(sale_times) >= 2:
                sorted_times = sorted(sale_times)
                intervals = [
                    (sorted_times[i + 1] - sorted_times[i]).total_seconds()
                    for i in range(len(sorted_times) - 1)
                ]
                features.avg_time_between_sales = float(np.mean(intervals))

        return features

    def _extract_market_features(
        self,
        features: EnhancedFeatures,
        market_offers: list[dict[str, Any]],
    ) -> EnhancedFeatures:
        """Извлечь признаки из текущих предложений."""
        features.market_depth = float(len(market_offers))

        price_range_low = features.current_price * 0.95
        price_range_high = features.current_price * 1.05

        competitive_offers = 0
        for offer in market_offers:
            offer_price = offer.get("price", {})
            if isinstance(offer_price, dict):
                price = float(offer_price.get("USD", 0)) / 100
            else:
                price = float(offer_price) / 100 if offer_price else 0

            if price_range_low <= price <= price_range_high:
                competitive_offers += 1

        if len(market_offers) > 0:
            features.competition_level = competitive_offers / len(market_offers)

        return features

    def _extract_relative_strength(
        self,
        features: EnhancedFeatures,
        game: GameType,
    ) -> EnhancedFeatures:
        """Рассчитать Relative Strength относительно индекса рынка."""
        market_index = self._market_index_cache.get(game, 100.0)

        if market_index > 0 and features.price_mean_7d > 0:
            # Нормализуем цену относительно индекса
            # RS = (цена / средняя цена по рынку) * 100
            features.relative_strength = features.current_price / market_index

        return features

    def _extract_game_specific_features(
        self,
        features: EnhancedFeatures,
        game: GameType,
        item_data: dict[str, Any],
        item_name: str,
    ) -> EnhancedFeatures:
        """Извлечь game-specific признаки."""
        if game in (GameType.CS2, GameType.CSGO):
            features = self._extract_cs2_features(features, item_data, item_name)
        elif game == GameType.DOTA2:
            features = self._extract_dota2_features(features, item_data)
        elif game == GameType.TF2:
            features = self._extract_tf2_features(features, item_data, item_name)
        elif game == GameType.RUST:
            features = self._extract_rust_features(features, item_data)

        return features

    def _extract_cs2_features(
        self,
        features: EnhancedFeatures,
        item_data: dict[str, Any],
        item_name: str,
    ) -> EnhancedFeatures:
        """Извлечь CS2-специфичные признаки (float, stickers, patterns)."""
        # Float value
        float_value = item_data.get("float", item_data.get("floatvalue", 0.0))
        if float_value:
            features.float_value = float(float_value)
            # Рассчитываем процентиль (чем ниже float, тем лучше)
            features.float_percentile = (1 - features.float_value) * 100

        # Pattern index
        pattern_index = item_data.get("pattern", item_data.get("paintindex", 0))
        if pattern_index:
            features.pattern_index = int(pattern_index)
            # Оценка редкости паттерна (упрощённо)
            features.pattern_score = self._calculate_pattern_score(
                item_name, features.pattern_index
            )

        # Stickers
        stickers = item_data.get("stickers", [])
        if stickers:
            features.sticker_count = len(stickers)
            features.sticker_value = self._calculate_sticker_value(stickers)

        # Condition parsing from name
        features.item_condition = self._parse_condition(item_name)

        # Rarity parsing
        features.item_rarity = self._parse_rarity(item_data)

        return features

    def _extract_dota2_features(
        self,
        features: EnhancedFeatures,
        item_data: dict[str, Any],
    ) -> EnhancedFeatures:
        """Извлечь Dota 2-специфичные признаки."""
        # Gems
        gems = item_data.get("gems", [])
        if gems:
            features.gem_count = len(gems)

        # Inscribed games
        inscribed = item_data.get("inscribed_games", item_data.get("inscriptions", []))
        if inscribed:
            features.inscribed_count = len(inscribed) if isinstance(inscribed, list) else 1

        # Rarity
        rarity = item_data.get("rarity", "").lower()
        if "arcana" in rarity:
            features.item_rarity = ItemRarity.ARCANA
        elif "immortal" in rarity:
            features.item_rarity = ItemRarity.IMMORTAL
        elif "mythical" in rarity:
            features.item_rarity = ItemRarity.CLASSIFIED
        elif "legendary" in rarity:
            features.item_rarity = ItemRarity.COVERT
        else:
            features.item_rarity = ItemRarity.MIL_SPEC

        return features

    def _extract_tf2_features(
        self,
        features: EnhancedFeatures,
        item_data: dict[str, Any],
        item_name: str,
    ) -> EnhancedFeatures:
        """Извлечь TF2-специфичные признаки."""
        # Unusual check
        if "unusual" in item_name.lower():
            features.is_unusual = True
            features.item_rarity = ItemRarity.UNUSUAL

            # Effect value (упрощённо)
            effect = item_data.get("effect", "")
            features.effect_value = self._calculate_effect_value(effect)

        return features

    def _extract_rust_features(
        self,
        features: EnhancedFeatures,
        item_data: dict[str, Any],
    ) -> EnhancedFeatures:
        """Извлечь Rust-специфичные признаки."""
        # Has skin
        features.has_skin = item_data.get("has_skin", True)

        # Condition if applicable
        condition = item_data.get("condition", "")
        if condition:
            features.item_condition = self._parse_condition(condition)

        return features

    def _calculate_rsi(self, prices: list[float]) -> float:
        """Рассчитать RSI (Relative Strength Index)."""
        if len(prices) < 2:
            return 50.0

        changes = np.diff(prices)
        gains = np.maximum(changes, 0)
        losses = np.abs(np.minimum(changes, 0))

        period = min(self.RSI_PERIOD, len(changes))
        avg_gain = np.mean(gains[-period:]) if len(gains) >= period else np.mean(gains)
        avg_loss = np.mean(losses[-period:]) if len(losses) >= period else np.mean(losses)

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(np.clip(rsi, 0, 100))

    def _calculate_momentum(self, prices: list[float]) -> float:
        """Рассчитать momentum (скорость изменения цены)."""
        if len(prices) < 2:
            return 0.0

        period = min(10, len(prices) - 1)
        old_price = prices[-(period + 1)]
        current_price = prices[-1]

        if old_price == 0:
            return 0.0

        return ((current_price - old_price) / old_price) * 100

    def _calculate_pattern_score(self, item_name: str, pattern_index: int) -> float:
        """Оценка редкости паттерна (упрощённо)."""
        # Известные редкие паттерны
        name_lower = item_name.lower()

        # Case Hardened blue gems
        if "case hardened" in name_lower:
            if pattern_index in [661, 387, 955]:  # Tier 1 blue gems
                return 1.0
            elif pattern_index in [321, 555, 828, 868, 179]:  # Tier 2
                return 0.8
            elif 100 <= pattern_index <= 200:
                return 0.3
            return 0.1

        # Fade
        if "fade" in name_lower:
            if pattern_index >= 95:  # Full fade
                return 0.9
            elif pattern_index >= 90:
                return 0.7
            return 0.3

        # Default
        return 0.1

    def _calculate_sticker_value(self, stickers: list[dict[str, Any]]) -> float:
        """Оценка стоимости стикеров (упрощённо)."""
        total_value = 0.0

        for sticker in stickers:
            name = sticker.get("name", "").lower()

            # Katowice 2014 Holo
            if "katowice 2014" in name and "holo" in name:
                total_value += 5000  # Примерная стоимость
            elif "katowice 2014" in name:
                total_value += 500
            # Titan Holo
            elif "titan" in name and "holo" in name:
                total_value += 3000
            # iBUYPOWER Holo
            elif "ibuypower" in name and "holo" in name:
                total_value += 10000
            # Обычные стикеры
            else:
                total_value += 1

        return total_value

    def _calculate_effect_value(self, effect: str) -> float:
        """Оценка стоимости TF2 эффекта."""
        effect_lower = effect.lower()

        # High-tier effects
        high_tier = ["burning flames", "scorching flames", "sunbeams"]
        if any(e in effect_lower for e in high_tier):
            return 1.0

        # Mid-tier effects
        mid_tier = ["purple energy", "green energy", "cloudy moon"]
        if any(e in effect_lower for e in mid_tier):
            return 0.6

        return 0.3

    def _parse_condition(self, text: str) -> ItemCondition:
        """Парсить состояние из текста."""
        text_lower = text.lower()

        if "factory new" in text_lower or "fn" in text_lower:
            return ItemCondition.FACTORY_NEW
        elif "minimal wear" in text_lower or "mw" in text_lower:
            return ItemCondition.MINIMAL_WEAR
        elif "field-tested" in text_lower or "ft" in text_lower:
            return ItemCondition.FIELD_TESTED
        elif "well-worn" in text_lower or "ww" in text_lower:
            return ItemCondition.WELL_WORN
        elif "battle-scarred" in text_lower or "bs" in text_lower:
            return ItemCondition.BATTLE_SCARRED

        return ItemCondition.FIELD_TESTED

    def _parse_rarity(self, item_data: dict[str, Any]) -> ItemRarity:
        """Парсить редкость из данных предмета."""
        rarity = item_data.get("rarity", "").lower()

        if "covert" in rarity or "red" in rarity:
            return ItemRarity.COVERT
        elif "classified" in rarity or "pink" in rarity:
            return ItemRarity.CLASSIFIED
        elif "restricted" in rarity or "purple" in rarity:
            return ItemRarity.RESTRICTED
        elif "mil-spec" in rarity or "blue" in rarity:
            return ItemRarity.MIL_SPEC
        elif "industrial" in rarity:
            return ItemRarity.INDUSTRIAL
        elif "consumer" in rarity:
            return ItemRarity.CONSUMER
        elif "contraband" in rarity:
            return ItemRarity.CONTRABAND

        return ItemRarity.MIL_SPEC


class MLPipeline:
    """Pipeline для безопасной обработки данных и предсказаний.

    Защищает от ошибок API: пустые строки, некорректные значения и т.д.
    """

    def __init__(self):
        """Инициализация pipeline."""
        self._scaler = None
        self._imputer = None
        self._is_fitted = False

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Обучить и трансформировать данные."""
        try:
            from sklearn.impute import SimpleImputer
            from sklearn.preprocessing import StandardScaler

            # Imputer для замены NaN
            self._imputer = SimpleImputer(strategy="median")
            X_imputed = self._imputer.fit_transform(X)

            # Scaler для нормализации
            self._scaler = StandardScaler()
            X_scaled = self._scaler.fit_transform(X_imputed)

            self._is_fitted = True
            return X_scaled

        except ImportError:
            logger.warning("sklearn not available, using basic cleaning")
            return self._basic_clean(X)

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Трансформировать данные."""
        if not self._is_fitted:
            return self._basic_clean(X)

        try:
            X_imputed = self._imputer.transform(X)
            X_scaled = self._scaler.transform(X_imputed)
            return X_scaled
        except Exception:
            return self._basic_clean(X)

    def _basic_clean(self, X: np.ndarray) -> np.ndarray:
        """Базовая очистка данных без sklearn."""
        # Заменяем NaN и Inf
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        return X


class EnhancedPricePredictor:
    """Улучшенный прогнозатор с ансамблем моделей.

    Использует:
    - RandomForestRegressor (ансамбль деревьев)
    - XGBoost (если доступен)
    - Ridge Regression (fallback)
    - Pipeline для защиты от ошибок
    """

    MODEL_VERSION = "2.0.0"
    RETRAIN_THRESHOLD = 100

    def __init__(
        self,
        model_path: str | Path | None = None,
        user_balance: float = 100.0,
        game: GameType = GameType.CS2,
    ):
        """Инициализация прогнозатора.

        Args:
            model_path: Путь для сохранения/загрузки модели
            user_balance: Текущий баланс пользователя (USD)
            game: Основная игра для прогнозирования
        """
        self.model_path = Path(model_path) if model_path else None
        self.user_balance = user_balance
        self.game = game

        # Экстрактор признаков
        self.feature_extractor = EnhancedFeatureExtractor()

        # Pipeline
        self.pipeline = MLPipeline()

        # Модели (ленивая инициализация)
        self._random_forest = None
        self._xgboost = None
        self._gradient_boost = None
        self._ridge = None
        self._models_initialized = False

        # Данные для обучения
        self._training_data_X: list[np.ndarray] = []
        self._training_data_y: list[float] = []
        self._new_samples_count = 0

        # Кэш прогнозов
        self._prediction_cache: dict[str, tuple[datetime, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)

        # Загрузка модели, если есть
        if self.model_path and self.model_path.exists():
            self._load_model()

    def _init_models(self):
        """Инициализация ML моделей."""
        if self._models_initialized:
            return

        try:
            from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
            from sklearn.linear_model import Ridge

            # RandomForest - основная модель (ансамбль деревьев)
            self._random_forest = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1,
                random_state=42,
            )

            # Gradient Boosting - вторая модель
            self._gradient_boost = GradientBoostingRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
            )

            # Ridge Regression - быстрый fallback
            self._ridge = Ridge(alpha=1.0)

            # XGBoost (опционально)
            try:
                from xgboost import XGBRegressor

                self._xgboost = XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    objective="reg:squarederror",
                    n_jobs=-1,
                    random_state=42,
                )
                logger.info("XGBoost initialized successfully")
            except ImportError:
                logger.info("XGBoost not available, using sklearn models only")
                self._xgboost = None

            self._models_initialized = True
            logger.info("Enhanced ML models initialized successfully")

        except ImportError as e:
            logger.warning(f"sklearn not available: {e}")
            self._models_initialized = False

    def set_user_balance(self, balance: float):
        """Установить баланс пользователя."""
        self.user_balance = max(0.0, balance)

    def set_game(self, game: GameType):
        """Установить игру."""
        self.game = game

    def predict(
        self,
        item_name: str,
        current_price: float,
        game: GameType | None = None,
        price_history: list[tuple[datetime, float]] | None = None,
        sales_history: list[dict[str, Any]] | None = None,
        market_offers: list[dict[str, Any]] | None = None,
        item_data: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Прогнозировать будущую цену предмета.

        Args:
            item_name: Название предмета
            current_price: Текущая цена
            game: Тип игры (если не указан, использует self.game)
            price_history: История цен
            sales_history: История продаж
            market_offers: Текущие предложения
            item_data: Дополнительные данные (float, stickers, etc)
            use_cache: Использовать кэш

        Returns:
            Dict с прогнозами и рекомендациями
        """
        game = game or self.game

        # Проверяем кэш
        cache_key = f"{game.value}:{item_name}:{current_price:.2f}"
        if use_cache and cache_key in self._prediction_cache:
            cached_time, cached_pred = self._prediction_cache[cache_key]
            if datetime.utcnow() - cached_time < self._cache_ttl:
                return cached_pred

        # Извлекаем признаки
        features = self.feature_extractor.extract_features(
            item_name=item_name,
            current_price=current_price,
            game=game,
            price_history=price_history,
            sales_history=sales_history,
            market_offers=market_offers,
            item_data=item_data,
        )

        # Прогнозирование
        prediction = self._make_prediction(item_name, features)

        # Кэшируем результат
        self._prediction_cache[cache_key] = (datetime.utcnow(), prediction)

        return prediction

    def _make_prediction(
        self,
        item_name: str,
        features: EnhancedFeatures,
    ) -> dict[str, Any]:
        """Выполнить прогнозирование."""
        current_price = features.current_price

        # Пробуем использовать ML модели
        if self._has_trained_models():
            predicted_1h, std_1h = self._ensemble_predict(features, horizon_hours=1)
            predicted_24h, std_24h = self._ensemble_predict(features, horizon_hours=24)
            predicted_7d, std_7d = self._ensemble_predict(features, horizon_hours=168)
        else:
            # Fallback: статистические методы
            predicted_1h, std_1h = self._statistical_predict(features, horizon_hours=1)
            predicted_24h, std_24h = self._statistical_predict(features, horizon_hours=24)
            predicted_7d, std_7d = self._statistical_predict(features, horizon_hours=168)

        # Рассчитываем уверенность
        relative_std = std_24h / current_price if current_price > 0 else 1.0
        confidence_score = self._calculate_confidence(features, relative_std)

        # Генерируем рекомендацию
        recommendation, reasoning = self._generate_recommendation(
            current_price=current_price,
            predicted_24h=predicted_24h,
            confidence_score=confidence_score,
            features=features,
        )

        return {
            "item_name": item_name,
            "game": features.game_type.value,
            "current_price": current_price,
            "predicted_price_1h": round(predicted_1h, 2),
            "predicted_price_24h": round(predicted_24h, 2),
            "predicted_price_7d": round(predicted_7d, 2),
            "price_range_1h": (round(max(0, predicted_1h - std_1h), 2), round(predicted_1h + std_1h, 2)),
            "price_range_24h": (round(max(0, predicted_24h - std_24h), 2), round(predicted_24h + std_24h, 2)),
            "price_range_7d": (round(max(0, predicted_7d - std_7d), 2), round(predicted_7d + std_7d, 2)),
            "confidence_score": round(confidence_score, 2),
            "confidence_level": self._score_to_level(confidence_score),
            "recommendation": recommendation,
            "reasoning": reasoning,
            "expected_profit_24h_percent": round(((predicted_24h - current_price) / current_price) * 100, 2) if current_price > 0 else 0,
            "model_version": self.MODEL_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            # Game-specific info
            "float_value": features.float_value if features.game_type in (GameType.CS2, GameType.CSGO) else None,
            "pattern_score": features.pattern_score if features.game_type in (GameType.CS2, GameType.CSGO) else None,
            "sticker_value": features.sticker_value if features.game_type in (GameType.CS2, GameType.CSGO) else None,
            "relative_strength": round(features.relative_strength, 3),
            "time_since_last_sale_hours": round(features.time_since_last_sale / 3600, 1) if features.time_since_last_sale > 0 else None,
        }

    def _has_trained_models(self) -> bool:
        """Проверить, есть ли обученные модели."""
        if not self._models_initialized:
            return False
        try:
            return hasattr(self._random_forest, "n_estimators_")
        except (AttributeError, TypeError):
            return False

    def _ensemble_predict(
        self,
        features: EnhancedFeatures,
        horizon_hours: int,
    ) -> tuple[float, float]:
        """Ансамблевый прогноз с использованием всех моделей."""
        X = features.to_array().reshape(1, -1)
        X = self.pipeline.transform(X)

        predictions = []
        weights = []

        # RandomForest
        try:
            rf_pred = self._random_forest.predict(X)[0]
            predictions.append(rf_pred)
            weights.append(0.35)
        except Exception:
            pass

        # XGBoost (если доступен)
        if self._xgboost is not None:
            try:
                xgb_pred = self._xgboost.predict(X)[0]
                predictions.append(xgb_pred)
                weights.append(0.35)
            except Exception:
                pass

        # Gradient Boosting
        try:
            gb_pred = self._gradient_boost.predict(X)[0]
            predictions.append(gb_pred)
            weights.append(0.20)
        except Exception:
            pass

        # Ridge
        try:
            ridge_pred = self._ridge.predict(X)[0]
            predictions.append(ridge_pred)
            weights.append(0.10)
        except Exception:
            pass

        if not predictions:
            return features.current_price, features.current_price * 0.1

        # Нормализуем веса
        total_weight = sum(weights[:len(predictions)])
        weights = [w / total_weight for w in weights[:len(predictions)]]

        # Взвешенное среднее
        prediction = sum(p * w for p, w in zip(predictions, weights))

        # Стандартное отклонение
        if len(predictions) >= 2:
            std = float(np.std(predictions))
        else:
            std = abs(predictions[0] - features.current_price) * 0.1

        # Масштабирование по горизонту
        if horizon_hours > 24:
            std *= 1.2

        return float(prediction), float(std)

    def _statistical_predict(
        self,
        features: EnhancedFeatures,
        horizon_hours: int,
    ) -> tuple[float, float]:
        """Статистический прогноз без ML."""
        current_price = features.current_price

        # Базовый прогноз: продолжение текущего тренда
        hourly_change = features.price_change_24h / 24
        trend_factor = 1 + (hourly_change * horizon_hours / 100)

        # Коррекция по RSI
        if features.rsi > 70:
            rsi_factor = 0.98
        elif features.rsi < 30:
            rsi_factor = 1.02
        else:
            rsi_factor = 1.0

        # Коррекция по momentum
        momentum_factor = 1 + (features.momentum * 0.001)

        # Итоговый прогноз
        prediction = current_price * trend_factor * rsi_factor * momentum_factor

        # Стандартное отклонение
        base_std = current_price * max(features.volatility, 0.02)
        horizon_multiplier = 1 + (horizon_hours / 24) * 0.5
        std = base_std * horizon_multiplier

        return float(prediction), float(std)

    def _calculate_confidence(
        self,
        features: EnhancedFeatures,
        relative_std: float,
    ) -> float:
        """Рассчитать уверенность в прогнозе."""
        confidence = 1.0

        # Волатильность
        if features.volatility > 0.2:
            confidence *= 0.6
        elif features.volatility > 0.1:
            confidence *= 0.8

        # Качество данных
        confidence *= features.data_quality_score

        # Относительный std
        if relative_std > 0.2:
            confidence *= 0.5
        elif relative_std > 0.1:
            confidence *= 0.7

        # Ликвидность
        if features.sales_count_24h > 10:
            confidence *= 1.1
        elif features.sales_count_24h < 2:
            confidence *= 0.8

        # Relative Strength
        if 0.8 <= features.relative_strength <= 1.2:
            confidence *= 1.05  # Стабильный относительно рынка

        return float(np.clip(confidence, 0.0, 1.0))

    def _score_to_level(self, score: float) -> str:
        """Преобразовать числовую уверенность в уровень."""
        if score >= 0.85:
            return "very_high"
        elif score >= 0.70:
            return "high"
        elif score >= 0.50:
            return "medium"
        elif score >= 0.30:
            return "low"
        else:
            return "very_low"

    def _generate_recommendation(
        self,
        current_price: float,
        predicted_24h: float,
        confidence_score: float,
        features: EnhancedFeatures,
    ) -> tuple[str, str]:
        """Генерировать рекомендацию."""
        if current_price <= 0:
            return "hold", "Invalid price data"

        expected_change = ((predicted_24h - current_price) / current_price) * 100

        # Адаптация к балансу
        balance_factor = self._get_balance_factor()

        # Пороги
        strong_buy_threshold = 8.0 * balance_factor
        buy_threshold = 5.0 * balance_factor
        sell_threshold = -5.0 * balance_factor
        strong_sell_threshold = -8.0 * balance_factor

        # Можем ли позволить покупку
        can_afford = current_price <= self.user_balance * 0.3

        reasoning_parts = []

        if expected_change >= strong_buy_threshold and confidence_score >= 0.6:
            if can_afford:
                recommendation = "strong_buy"
                reasoning_parts.append(f"Expected growth: {expected_change:.1f}%")
            else:
                recommendation = "buy"
                reasoning_parts.append("Strong signal but exceeds position limit")
        elif expected_change >= buy_threshold and confidence_score >= 0.5:
            if can_afford:
                recommendation = "buy"
                reasoning_parts.append(f"Expected growth: {expected_change:.1f}%")
            else:
                recommendation = "hold"
                reasoning_parts.append("Good signal but exceeds budget")
        elif expected_change <= strong_sell_threshold and confidence_score >= 0.6:
            recommendation = "strong_sell"
            reasoning_parts.append(f"Expected drop: {expected_change:.1f}%")
        elif expected_change <= sell_threshold and confidence_score >= 0.5:
            recommendation = "sell"
            reasoning_parts.append(f"Expected decline: {expected_change:.1f}%")
        else:
            recommendation = "hold"
            reasoning_parts.append("No clear signal")

        # Game-specific context
        game_context = self._get_game_context(features)
        if game_context:
            reasoning_parts.append(game_context)

        # Market context
        if features.is_weekend:
            reasoning_parts.append("Weekend: lower liquidity")
        if features.relative_strength > 1.2:
            reasoning_parts.append("Outperforming market")
        elif features.relative_strength < 0.8:
            reasoning_parts.append("Underperforming market")

        return recommendation, "; ".join(reasoning_parts)

    def _get_balance_factor(self) -> float:
        """Получить фактор адаптации к балансу."""
        if self.user_balance < 50:
            return 1.5
        elif self.user_balance < 100:
            return 1.3
        elif self.user_balance < 300:
            return 1.0
        elif self.user_balance < 500:
            return 0.9
        else:
            return 0.8

    def _get_game_context(self, features: EnhancedFeatures) -> str | None:
        """Получить игровой контекст для рекомендации."""
        if features.game_type in (GameType.CS2, GameType.CSGO):
            if features.float_value > 0 and features.float_value < 0.01:
                return "Low float (FN)"
            if features.sticker_value > 100:
                return f"Sticker value: ${features.sticker_value:.0f}"
            if features.pattern_score > 0.8:
                return "Rare pattern detected"
        elif features.game_type == GameType.DOTA2:
            if features.gem_count > 0:
                return f"Has {features.gem_count} gems"
        elif features.game_type == GameType.TF2:
            if features.is_unusual:
                return f"Unusual effect value: {features.effect_value:.1f}"

        return None

    def add_training_example(
        self,
        features: EnhancedFeatures,
        actual_future_price: float,
    ):
        """Добавить пример для обучения."""
        X = features.to_array()
        y = actual_future_price

        self._training_data_X.append(X)
        self._training_data_y.append(y)
        self._new_samples_count += 1

        if self._new_samples_count >= self.RETRAIN_THRESHOLD:
            self.train()

    def train(self, force: bool = False):
        """Обучить модели на накопленных данных."""
        if len(self._training_data_X) < 10 and not force:
            logger.warning("Not enough training data (minimum 10 samples)")
            return

        self._init_models()

        if not self._models_initialized:
            logger.warning("ML models not available")
            return

        X = np.array(self._training_data_X)
        y = np.array(self._training_data_y)

        try:
            # Pipeline fit
            X_processed = self.pipeline.fit_transform(X)

            # Обучаем модели
            self._random_forest.fit(X_processed, y)
            self._gradient_boost.fit(X_processed, y)
            self._ridge.fit(X_processed, y)

            if self._xgboost is not None:
                self._xgboost.fit(X_processed, y)

            self._new_samples_count = 0
            logger.info(f"Models trained on {len(X)} samples")

            if self.model_path:
                self._save_model()

        except Exception as e:
            logger.exception(f"Training failed: {e}")

    def _save_model(self):
        """Сохранить модели на диск."""
        if not self.model_path:
            return

        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "random_forest": self._random_forest,
                "gradient_boost": self._gradient_boost,
                "ridge": self._ridge,
                "xgboost": self._xgboost,
                "pipeline": self.pipeline,
                "training_data_X": self._training_data_X,
                "training_data_y": self._training_data_y,
                "version": self.MODEL_VERSION,
            }
            with open(self.model_path, "wb") as f:
                pickle.dump(data, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.exception(f"Failed to save model: {e}")

    def _load_model(self):
        """Загрузить модели с диска."""
        if not self.model_path or not self.model_path.exists():
            return

        try:
            with open(self.model_path, "rb") as f:
                data = pickle.load(f)

            self._random_forest = data.get("random_forest")
            self._gradient_boost = data.get("gradient_boost")
            self._ridge = data.get("ridge")
            self._xgboost = data.get("xgboost")
            self.pipeline = data.get("pipeline", MLPipeline())
            self._training_data_X = data.get("training_data_X", [])
            self._training_data_y = data.get("training_data_y", [])
            self._models_initialized = True

            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.exception(f"Failed to load model: {e}")

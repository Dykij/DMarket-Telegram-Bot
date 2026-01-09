"""Unified Strategy System - единая система стратегий для поиска предметов.

Этот модуль объединяет все стратегии поиска предметов в единую систему:

1. **Cross-Platform Arbitrage** - DMarket → Waxpeer/Steam
   - Instant arbitrage (без лока)
   - Trade lock arbitrage (инвестиции с локом)

2. **Intramarket Arbitrage** - внутри одной платформы
   - Price anomaly detection
   - Underpriced items finder
   - Mean reversion strategy

3. **Float Value Arbitrage** - на основе флоата
   - Premium float finder (низкий/высокий флоат)
   - Quartile analysis (покупка ниже Q1)
   - Float range orders

4. **Pattern/Phase Arbitrage** - редкие паттерны
   - Case Hardened Blue Gems
   - Doppler phases (Ruby/Sapphire/BP/Emerald)
   - Fade patterns

5. **Target System** - система Buy Orders
   - Smart targets с конкуренцией
   - Float-filtered targets
   - Pattern-filtered targets

6. **Smart Market Finder** - комплексный анализ
   - Trending items
   - Quick flip opportunities
   - Value investments

7. **Enhanced Scanner** - продвинутый сканер
   - Sales history analysis
   - External price comparison
   - Liquidity scoring

Каждая стратегия реализует общий интерфейс `IFindingStrategy`
для единообразного использования в боте.

Author: DMarket Telegram Bot
Created: January 2026
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog


if TYPE_CHECKING:
    from src.dmarket.dmarket_api import DMarketAPI
    from src.waxpeer.waxpeer_api import WaxpeerAPI

logger = structlog.get_logger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class StrategyType(StrEnum):
    """Типы стратегий поиска."""

    CROSS_PLATFORM_ARBITRAGE = "cross_platform"
    INTRAMARKET_ARBITRAGE = "intramarket"
    FLOAT_VALUE_ARBITRAGE = "float_value"
    PATTERN_PHASE_ARBITRAGE = "pattern_phase"
    TARGET_SYSTEM = "target_system"
    SMART_MARKET_FINDER = "smart_market"
    ENHANCED_SCANNER = "enhanced_scanner"
    TRENDING_ITEMS = "trending_items"
    QUICK_FLIP = "quick_flip"


class RiskLevel(StrEnum):
    """Уровень риска для возможности."""

    VERY_LOW = "very_low"  # Мгновенный арбитраж
    LOW = "low"  # Арбитраж с коротким локом
    MEDIUM = "medium"  # Инвестиции 3-7 дней
    HIGH = "high"  # Редкие предметы, длинный лок
    VERY_HIGH = "very_high"  # Паттерны, коллекционные


class OpportunityStatus(StrEnum):
    """Статус возможности."""

    ACTIVE = "active"  # Актуальная возможность
    EXPIRED = "expired"  # Истекла
    PURCHASED = "purchased"  # Куплено
    FAILED = "failed"  # Неудачная попытка
    PENDING = "pending"  # В обработке


class ActionType(StrEnum):
    """Тип рекомендуемого действия."""

    BUY_NOW = "buy_now"  # Купить сейчас
    CREATE_TARGET = "create_target"  # Создать таргет
    WATCH = "watch"  # Наблюдать
    CREATE_ADVANCED_ORDER = "create_advanced_order"  # Расширенный ордер
    SKIP = "skip"  # Пропустить


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class OpportunityScore:
    """Комплексная оценка возможности."""

    profit_score: float  # 0-100, оценка прибыльности
    liquidity_score: float  # 0-100, оценка ликвидности
    risk_score: float  # 0-100, оценка риска (выше = рискованнее)
    confidence_score: float  # 0-100, уверенность в оценке
    time_score: float  # 0-100, оценка времени продажи

    @property
    def total_score(self) -> float:
        """Общая оценка с весами."""
        weights = {
            "profit": 0.30,
            "liquidity": 0.25,
            "risk": 0.20,  # Инвертируем (100 - risk)
            "confidence": 0.15,
            "time": 0.10,
        }
        return (
            self.profit_score * weights["profit"]
            + self.liquidity_score * weights["liquidity"]
            + (100 - self.risk_score) * weights["risk"]
            + self.confidence_score * weights["confidence"]
            + self.time_score * weights["time"]
        )


@dataclass
class UnifiedOpportunity:
    """Унифицированная структура возможности для всех стратегий."""

    # Идентификация
    id: str
    title: str
    game: str

    # Стратегия и тип
    strategy_type: StrategyType
    action_type: ActionType

    # Цены
    buy_price: Decimal
    sell_price: Decimal
    profit_usd: Decimal
    profit_percent: Decimal

    # Оценки
    score: OpportunityScore
    risk_level: RiskLevel

    # Статус
    status: OpportunityStatus = OpportunityStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None

    # Дополнительные данные специфичные для стратегии
    metadata: dict[str, Any] = field(default_factory=dict)

    # Float Value (для float стратегий)
    float_value: float | None = None
    float_min: float | None = None
    float_max: float | None = None

    # Pattern/Phase (для pattern стратегий)
    pattern_id: int | None = None
    phase: str | None = None

    # Trade Lock
    trade_lock_days: int = 0

    # Ликвидность
    daily_sales: int | None = None
    offers_count: int = 0
    orders_count: int = 0

    # Источники цен
    source_platform: str = "dmarket"
    target_platform: str | None = None

    # Рекомендации
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Конвертация в словарь для сериализации."""
        return {
            "id": self.id,
            "title": self.title,
            "game": self.game,
            "strategy_type": self.strategy_type.value,
            "action_type": self.action_type.value,
            "buy_price": float(self.buy_price),
            "sell_price": float(self.sell_price),
            "profit_usd": float(self.profit_usd),
            "profit_percent": float(self.profit_percent),
            "total_score": self.score.total_score,
            "risk_level": self.risk_level.value,
            "status": self.status.value,
            "trade_lock_days": self.trade_lock_days,
            "float_value": self.float_value,
            "pattern_id": self.pattern_id,
            "phase": self.phase,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class StrategyConfig:
    """Конфигурация стратегии."""

    # Общие параметры
    game: str = "csgo"
    min_price: Decimal = Decimal("1.0")
    max_price: Decimal = Decimal("100.0")
    min_profit_percent: Decimal = Decimal("5.0")
    min_profit_usd: Decimal = Decimal("0.30")
    limit: int = 50

    # Риск и ликвидность
    max_risk_level: RiskLevel = RiskLevel.MEDIUM
    min_liquidity_score: float = 30.0
    min_daily_sales: int = 3

    # Trade Lock
    max_trade_lock_days: int = 7

    # Float фильтры
    float_min: float | None = None
    float_max: float | None = None

    # Pattern фильтры
    pattern_ids: list[int] | None = None
    phases: list[str] | None = None

    # Кэширование
    cache_ttl_seconds: int = 300  # 5 минут

    def to_dict(self) -> dict[str, Any]:
        """Конвертация в словарь."""
        return {
            "game": self.game,
            "min_price": float(self.min_price),
            "max_price": float(self.max_price),
            "min_profit_percent": float(self.min_profit_percent),
            "min_profit_usd": float(self.min_profit_usd),
            "limit": self.limit,
            "max_risk_level": self.max_risk_level.value,
            "min_liquidity_score": self.min_liquidity_score,
            "min_daily_sales": self.min_daily_sales,
            "max_trade_lock_days": self.max_trade_lock_days,
            "float_min": self.float_min,
            "float_max": self.float_max,
            "pattern_ids": self.pattern_ids,
            "phases": self.phases,
        }


# ============================================================================
# Strategy Interface
# ============================================================================


class IFindingStrategy(ABC):
    """Абстрактный интерфейс для всех стратегий поиска."""

    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """Тип стратегии."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Человекочитаемое имя стратегии."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Описание стратегии."""

    @abstractmethod
    async def find_opportunities(
        self,
        config: StrategyConfig,
    ) -> list[UnifiedOpportunity]:
        """Найти возможности по данной конфигурации.

        Args:
            config: Конфигурация поиска

        Returns:
            Список унифицированных возможностей
        """

    @abstractmethod
    def validate_config(self, config: StrategyConfig) -> bool:
        """Проверить валидность конфигурации для этой стратегии.

        Args:
            config: Конфигурация для проверки

        Returns:
            True если конфигурация валидна
        """

    def get_default_config(self) -> StrategyConfig:
        """Получить дефолтную конфигурацию для стратегии.

        Returns:
            Дефолтная конфигурация
        """
        return StrategyConfig()


# ============================================================================
# Strategy Implementations
# ============================================================================


class CrossPlatformArbitrageStrategy(IFindingStrategy):
    """Стратегия кросс-платформенного арбитража (DMarket → Waxpeer)."""

    def __init__(
        self,
        dmarket_api: "DMarketAPI",
        waxpeer_api: "WaxpeerAPI | None" = None,
    ) -> None:
        """Инициализация стратегии.

        Args:
            dmarket_api: DMarket API клиент
            waxpeer_api: Waxpeer API клиент (опционально)
        """
        self.dmarket_api = dmarket_api
        self.waxpeer_api = waxpeer_api

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.CROSS_PLATFORM_ARBITRAGE

    @property
    def name(self) -> str:
        return "Cross-Platform Arbitrage"

    @property
    def description(self) -> str:
        return (
            "Поиск арбитражных возможностей между DMarket и Waxpeer. "
            "Покупаем дешевле на DMarket, продаем дороже на Waxpeer."
        )

    def validate_config(self, config: StrategyConfig) -> bool:
        """Проверка конфигурации."""
        return not (
            config.min_price < Decimal("0.5")
            or config.min_profit_percent < Decimal("3.0")
        )

    async def find_opportunities(
        self,
        config: StrategyConfig,
    ) -> list[UnifiedOpportunity]:
        """Найти кросс-платформенные возможности."""
        from src.dmarket.cross_platform_arbitrage import CrossPlatformScanner

        try:
            scanner = CrossPlatformScanner(
                dmarket_api=self.dmarket_api,
                waxpeer_api=self.waxpeer_api,
            )

            # Используем существующий сканер
            results = await scanner.scan_full_market(
                min_price=float(config.min_price),
                max_price=float(config.max_price),
                min_roi_percent=float(config.min_profit_percent),
                max_lock_days=config.max_trade_lock_days,
                limit=config.limit,
            )

            # Конвертируем в унифицированный формат
            opportunities = []
            for item in results:
                opp = self._convert_to_unified(item, config)
                if opp:
                    opportunities.append(opp)

            return opportunities

        except ImportError:
            logger.warning("CrossPlatformScanner not available")
            return []
        except Exception as e:
            logger.exception("cross_platform_scan_error")
            return []

    def _convert_to_unified(
        self,
        item: dict[str, Any],
        config: StrategyConfig,
    ) -> UnifiedOpportunity | None:
        """Конвертировать результат в унифицированный формат."""
        try:
            buy_price = Decimal(str(item.get("dmarket_price", 0)))
            sell_price = Decimal(str(item.get("waxpeer_price", 0)))
            profit_usd = sell_price * Decimal("0.94") - buy_price  # После комиссии
            profit_percent = (profit_usd / buy_price * 100) if buy_price > 0 else Decimal(0)

            lock_days = item.get("trade_lock_days", 0)
            risk_level = self._calculate_risk_level(lock_days, profit_percent)

            score = OpportunityScore(
                profit_score=min(float(profit_percent) * 5, 100),
                liquidity_score=item.get("liquidity_score", 50),
                risk_score=lock_days * 10 if lock_days > 0 else 5,
                confidence_score=80 if sell_price > 0 else 50,
                time_score=100 - (lock_days * 10),
            )

            action = ActionType.BUY_NOW if lock_days == 0 else ActionType.WATCH

            return UnifiedOpportunity(
                id=item.get("item_id", ""),
                title=item.get("title", "Unknown"),
                game=config.game,
                strategy_type=self.strategy_type,
                action_type=action,
                buy_price=buy_price,
                sell_price=sell_price,
                profit_usd=profit_usd,
                profit_percent=profit_percent,
                score=score,
                risk_level=risk_level,
                trade_lock_days=lock_days,
                source_platform="dmarket",
                target_platform="waxpeer",
                daily_sales=item.get("daily_sales"),
                metadata=item,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.debug("conversion_error", error=str(e))
            return None

    def _calculate_risk_level(
        self,
        lock_days: int,
        profit_percent: Decimal,
    ) -> RiskLevel:
        """Рассчитать уровень риска."""
        if lock_days == 0 and profit_percent > Decimal(10):
            return RiskLevel.VERY_LOW
        if lock_days <= 3:
            return RiskLevel.LOW
        if lock_days <= 7:
            return RiskLevel.MEDIUM
        return RiskLevel.HIGH


class FloatValueArbitrageStrategy(IFindingStrategy):
    """Стратегия арбитража на основе Float Value."""

    def __init__(self, dmarket_api: "DMarketAPI") -> None:
        """Инициализация стратегии."""
        self.dmarket_api = dmarket_api

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FLOAT_VALUE_ARBITRAGE

    @property
    def name(self) -> str:
        return "Float Value Arbitrage"

    @property
    def description(self) -> str:
        return (
            "Поиск предметов с премиальным Float Value (низкий/высокий). "
            "Такие предметы продаются коллекционерам с премией 50-200%."
        )

    def validate_config(self, config: StrategyConfig) -> bool:
        """Проверка конфигурации."""
        if config.float_min is not None and config.float_max is not None:
            if config.float_min >= config.float_max:
                return False
        return True

    def get_default_config(self) -> StrategyConfig:
        """Дефолтная конфигурация для float стратегии."""
        return StrategyConfig(
            min_price=Decimal("5.0"),
            max_price=Decimal("200.0"),
            min_profit_percent=Decimal("20.0"),  # Премиальные флоаты
            float_min=0.0,
            float_max=0.18,  # Low float для FT
        )

    async def find_opportunities(
        self,
        config: StrategyConfig,
    ) -> list[UnifiedOpportunity]:
        """Найти float arbitrage возможности."""
        from src.dmarket.float_value_arbitrage import FloatValueArbitrage

        try:
            float_arb = FloatValueArbitrage(api_client=self.dmarket_api)

            results = await float_arb.find_float_arbitrage_opportunities(
                game=config.game,
                min_price=float(config.min_price),
                max_price=float(config.max_price),
                float_min=config.float_min or 0.0,
                float_max=config.float_max or 1.0,
                min_premium_percent=float(config.min_profit_percent),
                limit=config.limit,
            )

            opportunities = []
            for item in results:
                opp = self._convert_to_unified(item, config)
                if opp:
                    opportunities.append(opp)

            return opportunities

        except ImportError:
            logger.warning("FloatValueArbitrage not available")
            return []
        except Exception as e:
            logger.exception("float_scan_error")
            return []

    def _convert_to_unified(
        self,
        item: dict[str, Any],
        config: StrategyConfig,
    ) -> UnifiedOpportunity | None:
        """Конвертировать результат в унифицированный формат."""
        try:
            buy_price = Decimal(str(item.get("price", 0)))
            premium_multiplier = Decimal(str(item.get("premium_multiplier", 1.0)))
            sell_price = buy_price * premium_multiplier
            profit_usd = sell_price - buy_price
            profit_percent = (profit_usd / buy_price * 100) if buy_price > 0 else Decimal(0)

            float_val = item.get("float_value", 0.5)
            risk_level = RiskLevel.MEDIUM  # Float trading has moderate risk

            score = OpportunityScore(
                profit_score=min(float(profit_percent) * 2, 100),
                liquidity_score=60,  # Float items have lower liquidity
                risk_score=40,
                confidence_score=item.get("confidence", 70),
                time_score=50,  # Takes time to find collector
            )

            return UnifiedOpportunity(
                id=item.get("item_id", ""),
                title=item.get("title", "Unknown"),
                game=config.game,
                strategy_type=self.strategy_type,
                action_type=ActionType.CREATE_ADVANCED_ORDER,
                buy_price=buy_price,
                sell_price=sell_price,
                profit_usd=profit_usd,
                profit_percent=profit_percent,
                score=score,
                risk_level=risk_level,
                float_value=float_val,
                float_min=config.float_min,
                float_max=config.float_max,
                metadata=item,
                notes=[
                    f"Float: {float_val:.6f}",
                    f"Premium: {premium_multiplier:.1f}x",
                ],
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.debug("float_conversion_error", error=str(e))
            return None


class IntramarketArbitrageStrategy(IFindingStrategy):
    """Стратегия внутримаркетного арбитража."""

    def __init__(self, dmarket_api: "DMarketAPI") -> None:
        """Инициализация стратегии."""
        self.dmarket_api = dmarket_api

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.INTRAMARKET_ARBITRAGE

    @property
    def name(self) -> str:
        return "Intramarket Arbitrage"

    @property
    def description(self) -> str:
        return (
            "Поиск аномалий цен внутри DMarket. "
            "Покупаем занижённые предметы, продаём по рыночной цене."
        )

    def validate_config(self, config: StrategyConfig) -> bool:
        """Проверка конфигурации."""
        return config.min_profit_percent >= Decimal("3.0")

    async def find_opportunities(
        self,
        config: StrategyConfig,
    ) -> list[UnifiedOpportunity]:
        """Найти внутримаркетные возможности."""
        from src.dmarket.intramarket_arbitrage import (
            find_price_anomalies,
            find_trending_items,
        )

        opportunities = []

        try:
            # Поиск ценовых аномалий
            anomalies = await find_price_anomalies(
                api_client=self.dmarket_api,
                game=config.game,
                min_price=float(config.min_price),
                max_price=float(config.max_price),
                limit=config.limit,
            )

            for item in anomalies:
                opp = self._convert_anomaly_to_unified(item, config)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.exception("intramarket_scan_error")

        try:
            # Поиск трендовых предметов
            trending = await find_trending_items(
                api_client=self.dmarket_api,
                game=config.game,
                min_price=float(config.min_price),
                max_price=float(config.max_price),
                limit=config.limit // 2,
            )

            for item in trending:
                opp = self._convert_trending_to_unified(item, config)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.exception("trending_scan_error")

        return opportunities

    def _convert_anomaly_to_unified(
        self,
        item: dict[str, Any],
        config: StrategyConfig,
    ) -> UnifiedOpportunity | None:
        """Конвертировать аномалию в унифицированный формат."""
        try:
            buy_price = Decimal(str(item.get("price", 0)))
            suggested = Decimal(str(item.get("suggested_price", buy_price)))
            profit_usd = suggested * Decimal("0.93") - buy_price  # 7% комиссия
            profit_percent = (profit_usd / buy_price * 100) if buy_price > 0 else Decimal(0)

            if profit_percent < config.min_profit_percent:
                return None

            score = OpportunityScore(
                profit_score=min(float(profit_percent) * 5, 100),
                liquidity_score=item.get("liquidity_score", 70),
                risk_score=20,  # Intramarket is lower risk
                confidence_score=item.get("anomaly_confidence", 75),
                time_score=80,  # Usually quick sells
            )

            return UnifiedOpportunity(
                id=item.get("item_id", ""),
                title=item.get("title", "Unknown"),
                game=config.game,
                strategy_type=self.strategy_type,
                action_type=ActionType.BUY_NOW,
                buy_price=buy_price,
                sell_price=suggested,
                profit_usd=profit_usd,
                profit_percent=profit_percent,
                score=score,
                risk_level=RiskLevel.LOW,
                source_platform="dmarket",
                target_platform="dmarket",
                metadata=item,
                notes=[f"Anomaly type: {item.get('anomaly_type', 'underpriced')}"],
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.debug("anomaly_conversion_error", error=str(e))
            return None

    def _convert_trending_to_unified(
        self,
        item: dict[str, Any],
        config: StrategyConfig,
    ) -> UnifiedOpportunity | None:
        """Конвертировать трендовый предмет в унифицированный формат."""
        try:
            buy_price = Decimal(str(item.get("price", 0)))
            trend_growth = Decimal(str(item.get("trend_growth", 0.05)))
            sell_price = buy_price * (1 + trend_growth)
            profit_usd = sell_price * Decimal("0.93") - buy_price
            profit_percent = (profit_usd / buy_price * 100) if buy_price > 0 else Decimal(0)

            if profit_percent < config.min_profit_percent:
                return None

            score = OpportunityScore(
                profit_score=min(float(profit_percent) * 3, 100),
                liquidity_score=item.get("liquidity_score", 60),
                risk_score=35,  # Trending has moderate risk
                confidence_score=item.get("trend_confidence", 65),
                time_score=60,
            )

            return UnifiedOpportunity(
                id=item.get("item_id", ""),
                title=item.get("title", "Unknown"),
                game=config.game,
                strategy_type=self.strategy_type,
                action_type=ActionType.WATCH,
                buy_price=buy_price,
                sell_price=sell_price,
                profit_usd=profit_usd,
                profit_percent=profit_percent,
                score=score,
                risk_level=RiskLevel.MEDIUM,
                source_platform="dmarket",
                target_platform="dmarket",
                metadata=item,
                notes=[
                    f"Trend: +{float(trend_growth) * 100:.1f}%",
                    "Investment opportunity",
                ],
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.debug("trending_conversion_error", error=str(e))
            return None


class SmartMarketFinderStrategy(IFindingStrategy):
    """Стратегия умного поиска на рынке."""

    def __init__(self, dmarket_api: "DMarketAPI") -> None:
        """Инициализация стратегии."""
        self.dmarket_api = dmarket_api

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.SMART_MARKET_FINDER

    @property
    def name(self) -> str:
        return "Smart Market Finder"

    @property
    def description(self) -> str:
        return (
            "Комплексный поиск возможностей с учетом множества факторов: "
            "ликвидность, тренды, история продаж, волатильность."
        )

    def validate_config(self, config: StrategyConfig) -> bool:
        """Проверка конфигурации."""
        return True

    async def find_opportunities(
        self,
        config: StrategyConfig,
    ) -> list[UnifiedOpportunity]:
        """Найти умные возможности."""
        from src.dmarket.smart_market_finder import SmartMarketFinder

        try:
            finder = SmartMarketFinder(api_client=self.dmarket_api)

            results = await finder.find_best_opportunities(
                game=config.game,
                min_price=float(config.min_price),
                max_price=float(config.max_price),
                limit=config.limit,
                min_confidence=float(config.min_liquidity_score),
            )

            opportunities = []
            for item in results:
                opp = self._convert_to_unified(item, config)
                if opp:
                    opportunities.append(opp)

            return opportunities

        except Exception as e:
            logger.exception("smart_finder_error")
            return []

    def _convert_to_unified(
        self,
        item: Any,  # MarketOpportunity dataclass
        config: StrategyConfig,
    ) -> UnifiedOpportunity | None:
        """Конвертировать результат в унифицированный формат."""
        try:
            buy_price = Decimal(str(item.current_price))
            sell_price = Decimal(str(item.suggested_price))
            profit_usd = Decimal(str(item.profit_potential))
            profit_percent = Decimal(str(item.profit_percent))

            if profit_percent < config.min_profit_percent:
                return None

            score = OpportunityScore(
                profit_score=min(float(profit_percent) * 4, 100),
                liquidity_score=item.liquidity_score,
                risk_score=self._risk_string_to_score(item.risk_level),
                confidence_score=item.confidence_score,
                time_score=70,
            )

            action = self._opportunity_type_to_action(item.opportunity_type)
            risk_level = self._string_to_risk_level(item.risk_level)

            return UnifiedOpportunity(
                id=item.item_id,
                title=item.title,
                game=item.game,
                strategy_type=self.strategy_type,
                action_type=action,
                buy_price=buy_price,
                sell_price=sell_price,
                profit_usd=profit_usd,
                profit_percent=profit_percent,
                score=score,
                risk_level=risk_level,
                offers_count=item.offers_count,
                orders_count=item.orders_count,
                source_platform="dmarket",
                metadata={
                    "opportunity_type": str(item.opportunity_type),
                    "category": item.category,
                    "rarity": item.rarity,
                },
                notes=item.notes or [],
            )
        except (AttributeError, TypeError, ValueError) as e:
            logger.debug("smart_conversion_error", error=str(e))
            return None

    def _risk_string_to_score(self, risk: str) -> float:
        """Конвертировать строку риска в оценку."""
        mapping = {"low": 20, "medium": 50, "high": 80}
        return mapping.get(risk.lower(), 50)

    def _string_to_risk_level(self, risk: str) -> RiskLevel:
        """Конвертировать строку в RiskLevel."""
        mapping = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
        }
        return mapping.get(risk.lower(), RiskLevel.MEDIUM)

    def _opportunity_type_to_action(self, opp_type: Any) -> ActionType:
        """Конвертировать тип возможности в действие."""
        type_str = str(opp_type).lower()
        if "quick_flip" in type_str:
            return ActionType.BUY_NOW
        if "target" in type_str:
            return ActionType.CREATE_TARGET
        if "investment" in type_str:
            return ActionType.WATCH
        return ActionType.BUY_NOW


# ============================================================================
# Unified Strategy Manager
# ============================================================================


class UnifiedStrategyManager:
    """Менеджер для управления всеми стратегиями."""

    def __init__(
        self,
        dmarket_api: "DMarketAPI",
        waxpeer_api: "WaxpeerAPI | None" = None,
    ) -> None:
        """Инициализация менеджера.

        Args:
            dmarket_api: DMarket API клиент
            waxpeer_api: Waxpeer API клиент (опционально)
        """
        self.dmarket_api = dmarket_api
        self.waxpeer_api = waxpeer_api

        # Инициализируем все стратегии
        self._strategies: dict[StrategyType, IFindingStrategy] = {}
        self._init_strategies()

        logger.info(
            "unified_strategy_manager_initialized",
            strategies_count=len(self._strategies),
        )

    def _init_strategies(self) -> None:
        """Инициализировать все доступные стратегии."""
        # Cross-platform (DMarket → Waxpeer)
        self._strategies[StrategyType.CROSS_PLATFORM_ARBITRAGE] = (
            CrossPlatformArbitrageStrategy(
                dmarket_api=self.dmarket_api,
                waxpeer_api=self.waxpeer_api,
            )
        )

        # Float Value Arbitrage
        self._strategies[StrategyType.FLOAT_VALUE_ARBITRAGE] = (
            FloatValueArbitrageStrategy(dmarket_api=self.dmarket_api)
        )

        # Intramarket Arbitrage
        self._strategies[StrategyType.INTRAMARKET_ARBITRAGE] = (
            IntramarketArbitrageStrategy(dmarket_api=self.dmarket_api)
        )

        # Smart Market Finder
        self._strategies[StrategyType.SMART_MARKET_FINDER] = (
            SmartMarketFinderStrategy(dmarket_api=self.dmarket_api)
        )

    def get_strategy(self, strategy_type: StrategyType) -> IFindingStrategy | None:
        """Получить стратегию по типу.

        Args:
            strategy_type: Тип стратегии

        Returns:
            Экземпляр стратегии или None
        """
        return self._strategies.get(strategy_type)

    def list_strategies(self) -> list[dict[str, Any]]:
        """Получить список всех доступных стратегий.

        Returns:
            Список с информацией о стратегиях
        """
        return [
            {
                "type": strategy_type.value,
                "name": strategy.name,
                "description": strategy.description,
            }
            for strategy_type, strategy in self._strategies.items()
        ]

    async def scan_with_strategy(
        self,
        strategy_type: StrategyType,
        config: StrategyConfig | None = None,
    ) -> list[UnifiedOpportunity]:
        """Сканировать с использованием конкретной стратегии.

        Args:
            strategy_type: Тип стратегии
            config: Конфигурация (если None - используется дефолтная)

        Returns:
            Список найденных возможностей
        """
        strategy = self.get_strategy(strategy_type)
        if not strategy:
            logger.error("strategy_not_found", strategy_type=strategy_type.value)
            return []

        if config is None:
            config = strategy.get_default_config()

        if not strategy.validate_config(config):
            logger.error("invalid_config", strategy_type=strategy_type.value)
            return []

        logger.info(
            "starting_strategy_scan",
            strategy=strategy_type.value,
            config=config.to_dict(),
        )

        opportunities = await strategy.find_opportunities(config)

        logger.info(
            "strategy_scan_complete",
            strategy=strategy_type.value,
            found=len(opportunities),
        )

        return opportunities

    async def scan_all_strategies(
        self,
        config: StrategyConfig | None = None,
        strategy_types: list[StrategyType] | None = None,
    ) -> dict[StrategyType, list[UnifiedOpportunity]]:
        """Сканировать всеми стратегиями.

        Args:
            config: Общая конфигурация
            strategy_types: Список типов стратегий (если None - все)

        Returns:
            Словарь с результатами по каждой стратегии
        """
        if strategy_types is None:
            strategy_types = list(self._strategies.keys())

        results: dict[StrategyType, list[UnifiedOpportunity]] = {}

        for strategy_type in strategy_types:
            opportunities = await self.scan_with_strategy(strategy_type, config)
            results[strategy_type] = opportunities

        return results

    async def find_best_opportunities_combined(
        self,
        config: StrategyConfig | None = None,
        top_n: int = 20,
    ) -> list[UnifiedOpportunity]:
        """Найти лучшие возможности из всех стратегий.

        Args:
            config: Конфигурация
            top_n: Количество лучших возможностей

        Returns:
            Отсортированный список лучших возможностей
        """
        all_results = await self.scan_all_strategies(config)

        # Объединяем все возможности
        all_opportunities: list[UnifiedOpportunity] = []
        for opportunities in all_results.values():
            all_opportunities.extend(opportunities)

        # Сортируем по общему score
        all_opportunities.sort(key=lambda x: x.score.total_score, reverse=True)

        # Убираем дубликаты по item_id
        seen_ids: set[str] = set()
        unique_opportunities: list[UnifiedOpportunity] = []
        for opp in all_opportunities:
            if opp.id not in seen_ids:
                seen_ids.add(opp.id)
                unique_opportunities.append(opp)

        return unique_opportunities[:top_n]


# ============================================================================
# Factory Functions
# ============================================================================


def create_strategy_manager(
    dmarket_api: "DMarketAPI",
    waxpeer_api: "WaxpeerAPI | None" = None,
) -> UnifiedStrategyManager:
    """Создать менеджер стратегий.

    Args:
        dmarket_api: DMarket API клиент
        waxpeer_api: Waxpeer API клиент

    Returns:
        Экземпляр UnifiedStrategyManager
    """
    return UnifiedStrategyManager(
        dmarket_api=dmarket_api,
        waxpeer_api=waxpeer_api,
    )


def get_strategy_config_preset(preset_name: str) -> StrategyConfig:
    """Получить пресет конфигурации.

    Доступные пресеты:
    - "boost": Низкие цены, быстрый оборот ($0.50-$3)
    - "standard": Стандартные цены ($3-$15)
    - "medium": Средние цены ($15-$50)
    - "advanced": Высокие цены ($50-$200)
    - "pro": Премиальные предметы ($200+)
    - "float_premium": Float арбитраж
    - "instant_arb": Мгновенный арбитраж без лока
    - "investment": Инвестиционные возможности

    Args:
        preset_name: Название пресета

    Returns:
        StrategyConfig с предустановленными параметрами
    """
    presets = {
        "boost": StrategyConfig(
            min_price=Decimal("0.50"),
            max_price=Decimal("3.00"),
            min_profit_percent=Decimal("10.0"),
            min_profit_usd=Decimal("0.15"),
            max_trade_lock_days=0,
            limit=100,
        ),
        "standard": StrategyConfig(
            min_price=Decimal("3.00"),
            max_price=Decimal("15.00"),
            min_profit_percent=Decimal("8.0"),
            min_profit_usd=Decimal("0.30"),
            max_trade_lock_days=3,
            limit=50,
        ),
        "medium": StrategyConfig(
            min_price=Decimal("15.00"),
            max_price=Decimal("50.00"),
            min_profit_percent=Decimal("7.0"),
            min_profit_usd=Decimal("1.00"),
            max_trade_lock_days=5,
            limit=30,
        ),
        "advanced": StrategyConfig(
            min_price=Decimal("50.00"),
            max_price=Decimal("200.00"),
            min_profit_percent=Decimal("6.0"),
            min_profit_usd=Decimal("3.00"),
            max_trade_lock_days=7,
            limit=20,
        ),
        "pro": StrategyConfig(
            min_price=Decimal("200.00"),
            max_price=Decimal("10000.00"),
            min_profit_percent=Decimal("5.0"),
            min_profit_usd=Decimal("10.00"),
            max_trade_lock_days=8,
            max_risk_level=RiskLevel.HIGH,
            limit=10,
        ),
        "float_premium": StrategyConfig(
            min_price=Decimal("10.00"),
            max_price=Decimal("500.00"),
            min_profit_percent=Decimal("20.0"),
            float_min=0.0,
            float_max=0.18,
            max_risk_level=RiskLevel.MEDIUM,
            limit=30,
        ),
        "instant_arb": StrategyConfig(
            min_price=Decimal("1.00"),
            max_price=Decimal("100.00"),
            min_profit_percent=Decimal("5.0"),
            min_profit_usd=Decimal("0.30"),
            max_trade_lock_days=0,
            min_daily_sales=5,
            limit=50,
        ),
        "investment": StrategyConfig(
            min_price=Decimal("5.00"),
            max_price=Decimal("200.00"),
            min_profit_percent=Decimal("15.0"),
            max_trade_lock_days=8,
            max_risk_level=RiskLevel.HIGH,
            limit=30,
        ),
    }

    return presets.get(preset_name, StrategyConfig())


# ============================================================================
# Multi-Game Support
# ============================================================================

# Поддерживаемые игры на DMarket
SUPPORTED_GAMES = ["csgo", "dota2", "tf2", "rust"]

# Эмодзи для игр
GAME_EMOJIS = {
    "csgo": "🔫",
    "dota2": "⚔️",
    "tf2": "🎩",
    "rust": "🏚️",
}

# Названия игр для отображения
GAME_NAMES = {
    "csgo": "CS:GO / CS2",
    "dota2": "Dota 2",
    "tf2": "Team Fortress 2",
    "rust": "Rust",
}


def get_game_specific_config(game: str, base_preset: str = "standard") -> StrategyConfig:
    """Получить конфигурацию специфичную для игры.

    Каждая игра имеет свои особенности рынка:
    - CS:GO: Float value, паттерны, stickers, большой рынок
    - Dota 2: Immortals, Arcana, gems, стили
    - TF2: Unusual hats, killstreak, странные предметы
    - Rust: Skins с паттернами, ограниченные предметы

    Args:
        game: Код игры (csgo, dota2, tf2, rust)
        base_preset: Базовый пресет для параметров цены

    Returns:
        StrategyConfig адаптированный под игру
    """
    base = get_strategy_config_preset(base_preset)

    # Специфичные настройки для каждой игры
    game_adjustments = {
        "csgo": {
            # CS:GO - самый большой рынок, много арбитража
            "min_profit_percent": Decimal("5.0"),
            "min_daily_sales": 3,
            "limit": 50,
        },
        "dota2": {
            # Dota 2 - меньше рынок, но есть редкие предметы
            "min_profit_percent": Decimal("7.0"),
            "min_daily_sales": 2,
            "limit": 30,
            # Dota предметы часто дешевле
            "max_price": min(base.max_price, Decimal("100.0")),
        },
        "tf2": {
            # TF2 - уникальный рынок с unusual эффектами
            "min_profit_percent": Decimal("8.0"),
            "min_daily_sales": 1,
            "limit": 20,
            # TF2 предметы обычно дешевле
            "max_price": min(base.max_price, Decimal("50.0")),
        },
        "rust": {
            # Rust - быстрорастущий рынок
            "min_profit_percent": Decimal("6.0"),
            "min_daily_sales": 2,
            "limit": 30,
        },
    }

    adjustments = game_adjustments.get(game, {})

    return StrategyConfig(
        game=game,
        min_price=base.min_price,
        max_price=adjustments.get("max_price", base.max_price),
        min_profit_percent=adjustments.get("min_profit_percent", base.min_profit_percent),
        min_profit_usd=base.min_profit_usd,
        limit=adjustments.get("limit", base.limit),
        max_risk_level=base.max_risk_level,
        min_liquidity_score=base.min_liquidity_score,
        min_daily_sales=adjustments.get("min_daily_sales", base.min_daily_sales),
        max_trade_lock_days=base.max_trade_lock_days,
        float_min=base.float_min,
        float_max=base.float_max,
        pattern_ids=base.pattern_ids,
        phases=base.phases,
        cache_ttl_seconds=base.cache_ttl_seconds,
    )


async def scan_all_games(
    strategy_manager: UnifiedStrategyManager,
    base_preset: str = "standard",
    games: list[str] | None = None,
    top_n_per_game: int = 10,
) -> dict[str, list[UnifiedOpportunity]]:
    """Сканировать все игры на арбитражные возможности.

    Args:
        strategy_manager: Менеджер стратегий
        base_preset: Базовый пресет для настроек
        games: Список игр для сканирования (по умолчанию все)
        top_n_per_game: Количество лучших возможностей на игру

    Returns:
        Словарь с возможностями по играм
    """
    if games is None:
        games = SUPPORTED_GAMES

    results: dict[str, list[UnifiedOpportunity]] = {}

    for game in games:
        if game not in SUPPORTED_GAMES:
            continue

        config = get_game_specific_config(game, base_preset)

        try:
            opportunities = await strategy_manager.find_best_opportunities_combined(
                config=config,
                top_n=top_n_per_game,
            )
            results[game] = opportunities

            logger.info(
                "game_scan_complete",
                game=game,
                found=len(opportunities),
            )
        except Exception as e:
            logger.exception(f"game_scan_error: {game}", error=str(e))
            results[game] = []

    return results


async def scan_all_games_combined(
    strategy_manager: UnifiedStrategyManager,
    base_preset: str = "standard",
    games: list[str] | None = None,
    top_n: int = 30,
) -> list[UnifiedOpportunity]:
    """Сканировать все игры и вернуть объединённый список лучших возможностей.

    Args:
        strategy_manager: Менеджер стратегий
        base_preset: Базовый пресет
        games: Список игр
        top_n: Общее количество лучших возможностей

    Returns:
        Отсортированный список лучших возможностей из всех игр
    """
    game_results = await scan_all_games(
        strategy_manager=strategy_manager,
        base_preset=base_preset,
        games=games,
        top_n_per_game=top_n // len(games or SUPPORTED_GAMES) + 5,
    )

    # Объединяем все возможности
    all_opportunities: list[UnifiedOpportunity] = []
    for game_opportunities in game_results.values():
        all_opportunities.extend(game_opportunities)

    # Сортируем по score
    all_opportunities.sort(key=lambda x: x.score.total_score, reverse=True)

    # Убираем дубликаты
    seen_ids: set[str] = set()
    unique: list[UnifiedOpportunity] = []
    for opp in all_opportunities:
        if opp.id not in seen_ids:
            seen_ids.add(opp.id)
            unique.append(opp)

    return unique[:top_n]


# ============================================================================
# Game-Specific Strategies
# ============================================================================


# Dota 2 специфичные паттерны и типы предметов
DOTA2_VALUABLE_TYPES = [
    "Arcana",  # Аркана - самые ценные
    "Immortal",  # Иммортал предметы
    "Genuine",  # Подлинные
    "Unusual Courier",  # Необычные курьеры
    "Golden",  # Золотые версии
]

# TF2 специфичные эффекты и типы
TF2_VALUABLE_EFFECTS = [
    "Burning Flames",
    "Scorching Flames",
    "Sunbeams",
    "Circling Hearts",
    "Energy Orb",
]

TF2_VALUABLE_TYPES = [
    "Unusual",  # С эффектами
    "Strange",  # Со счётчиком
    "Killstreak",  # С полосой убийств
    "Australium",  # Австралиум версии
]

# Rust специфичные категории
RUST_VALUABLE_CATEGORIES = [
    "Garage Door",  # Дорогие двери
    "Metal Door",
    "AK-47",  # Популярные оружия
    "LR-300",
    "M249",
    "Rock",  # Редкие скины камней
]


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "DOTA2_VALUABLE_TYPES",
    "GAME_EMOJIS",
    "GAME_NAMES",
    "RUST_VALUABLE_CATEGORIES",
    "SUPPORTED_GAMES",
    "TF2_VALUABLE_EFFECTS",
    "TF2_VALUABLE_TYPES",
    "ActionType",
    "CrossPlatformArbitrageStrategy",
    "FloatValueArbitrageStrategy",
    "IFindingStrategy",
    "IntramarketArbitrageStrategy",
    "OpportunityScore",
    "OpportunityStatus",
    "RiskLevel",
    "SmartMarketFinderStrategy",
    "StrategyConfig",
    "StrategyType",
    "UnifiedOpportunity",
    "UnifiedStrategyManager",
    "create_strategy_manager",
    "get_game_specific_config",
    "get_strategy_config_preset",
    "scan_all_games",
    "scan_all_games_combined",
]

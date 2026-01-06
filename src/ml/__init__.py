"""ML/AI модуль для прогнозирования цен на DMarket.

Этот модуль предоставляет адаптивные ML модели для:
- Прогнозирования цен предметов
- Определения оптимального времени покупки/продажи
- Классификации рисков сделок
- Адаптации к текущему балансу пользователя

Используемые библиотеки (все бесплатные):
- scikit-learn: основные ML модели (RandomForest, GradientBoosting, Ridge)
- XGBoost: продвинутый gradient boosting (опционально)
- NumPy: математические операции
- Собственные адаптивные алгоритмы

Поддерживаемые игры:
- CS2 (Counter-Strike 2) / CSGO
- Dota 2
- TF2 (Team Fortress 2)
- Rust
"""

from src.ml.price_predictor import (
    AdaptivePricePredictor,
    PricePrediction,
    PredictionConfidence,
)
from src.ml.trade_classifier import (
    AdaptiveTradeClassifier,
    TradeSignal,
    RiskLevel,
)
from src.ml.balance_adapter import (
    BalanceAdaptiveStrategy,
    StrategyRecommendation,
)
from src.ml.feature_extractor import (
    MarketFeatureExtractor,
    PriceFeatures,
)
from src.ml.enhanced_predictor import (
    EnhancedPricePredictor,
    EnhancedFeatureExtractor,
    EnhancedFeatures,
    GameType,
    ItemRarity,
    ItemCondition,
    MLPipeline,
)

__all__ = [
    # Price Predictor (базовый)
    "AdaptivePricePredictor",
    "PricePrediction",
    "PredictionConfidence",
    # Enhanced Price Predictor (улучшенный)
    "EnhancedPricePredictor",
    "EnhancedFeatureExtractor",
    "EnhancedFeatures",
    "GameType",
    "ItemRarity",
    "ItemCondition",
    "MLPipeline",
    # Trade Classifier
    "AdaptiveTradeClassifier",
    "TradeSignal",
    "RiskLevel",
    # Balance Adapter
    "BalanceAdaptiveStrategy",
    "StrategyRecommendation",
    # Feature Extractor
    "MarketFeatureExtractor",
    "PriceFeatures",
]

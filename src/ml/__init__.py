"""ML/AI модуль для прогнозирования цен на DMarket.

Этот модуль предоставляет адаптивные ML модели для:
- Прогнозирования цен предметов
- Определения оптимального времени покупки/продажи
- Классификации рисков сделок
- Адаптации к текущему балансу пользователя
- Автоматической настройки гиперпараметров (ModelTuner)
- Обнаружения аномалий и манипуляций
- Умных рекомендаций по покупке/продаже

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

Документация: docs/ML_AI_GUIDE.md
"""

from src.ml.balance_adapter import (
    BalanceAdaptiveStrategy,
    StrategyRecommendation,
)
from src.ml.enhanced_predictor import (
    EnhancedFeatureExtractor,
    EnhancedFeatures,
    EnhancedPricePredictor,
    GameType,
    ItemCondition,
    ItemRarity,
    MLPipeline,
)
from src.ml.feature_extractor import (
    MarketFeatureExtractor,
    PriceFeatures,
)
from src.ml.model_tuner import (
    AutoMLSelector,
    CVStrategy,
    EvaluationResult,
    ModelTuner,
    ScoringMetric,
    TuningResult,
)
from src.ml.price_predictor import (
    AdaptivePricePredictor,
    PredictionConfidence,
    PricePrediction,
)
from src.ml.trade_classifier import (
    AdaptiveTradeClassifier,
    RiskLevel,
    TradeSignal,
)
from src.ml.anomaly_detection import (
    AnomalyDetector,
    AnomalyResult,
    AnomalyType,
    AnomalySeverity,
    create_anomaly_detector,
)
from src.ml.smart_recommendations import (
    SmartRecommendations,
    ItemRecommendation,
    RecommendationBatch,
    RecommendationType,
    RiskLevel as RecommendationRiskLevel,
    create_smart_recommendations,
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
    # Model Tuner (автонастройка)
    "ModelTuner",
    "AutoMLSelector",
    "CVStrategy",
    "ScoringMetric",
    "TuningResult",
    "EvaluationResult",
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
    # Anomaly Detection
    "AnomalyDetector",
    "AnomalyResult",
    "AnomalyType",
    "AnomalySeverity",
    "create_anomaly_detector",
    # Smart Recommendations
    "SmartRecommendations",
    "ItemRecommendation",
    "RecommendationBatch",
    "RecommendationType",
    "RecommendationRiskLevel",
    "create_smart_recommendations",
]

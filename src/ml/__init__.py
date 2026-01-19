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

from src.ml.anomaly_detection import (
    AnomalyDetector,
    AnomalyResult,
    AnomalySeverity,
    AnomalyType,
    create_anomaly_detector,
)
from src.ml.balance_adapter import BalanceAdaptiveStrategy, StrategyRecommendation
from src.ml.data_scheduler import MLDataScheduler, SchedulerConfig, SchedulerState, TaskType
from src.ml.enhanced_predictor import (
    EnhancedFeatureExtractor,
    EnhancedFeatures,
    EnhancedPricePredictor,
    GameType,
    ItemCondition,
    ItemRarity,
    MLPipeline,
)
from src.ml.feature_extractor import MarketFeatureExtractor, PriceFeatures
from src.ml.model_tuner import (
    AutoMLSelector,
    CVStrategy,
    EvaluationResult,
    ModelTuner,
    ScoringMetric,
    TuningResult,
)

# Real Data Training Modules (новые модули для обучения на реальных данных API)
from src.ml.price_normalizer import NormalizedPrice, PriceNormalizer, PriceSource
from src.ml.price_predictor import AdaptivePricePredictor, PredictionConfidence, PricePrediction
from src.ml.real_price_collector import (
    CollectedPrice,
    CollectionResult,
    CollectionStatus,
    GameType as CollectorGameType,
    RealPriceCollector,
)
from src.ml.smart_recommendations import (
    ItemRecommendation,
    RecommendationBatch,
    RecommendationType,
    RiskLevel as RecommendationRiskLevel,
    SmartRecommendations,
    create_smart_recommendations,
)
from src.ml.trade_classifier import AdaptiveTradeClassifier, RiskLevel, TradeSignal
from src.ml.training_data_manager import DatasetMetadata, TrainingDataManager, TrainingDataset


__all__ = [
    # Price Predictor (базовый)
    "AdaptivePricePredictor",
    # Trade Classifier
    "AdaptiveTradeClassifier",
    # Anomaly Detection
    "AnomalyDetector",
    "AnomalyResult",
    "AnomalySeverity",
    "AnomalyType",
    "AutoMLSelector",
    # Balance Adapter
    "BalanceAdaptiveStrategy",
    "CVStrategy",
    "CollectedPrice",
    "CollectionResult",
    "CollectionStatus",
    "CollectorGameType",
    "DatasetMetadata",
    "EnhancedFeatureExtractor",
    "EnhancedFeatures",
    # Enhanced Price Predictor (улучшенный)
    "EnhancedPricePredictor",
    "EvaluationResult",
    "GameType",
    "ItemCondition",
    "ItemRarity",
    "ItemRecommendation",
    # Data Scheduler - автоматический сбор и переобучение
    "MLDataScheduler",
    "MLPipeline",
    # Feature Extractor
    "MarketFeatureExtractor",
    # Model Tuner (автонастройка)
    "ModelTuner",
    "NormalizedPrice",
    "PredictionConfidence",
    "PriceFeatures",
    # ═══════════════════════════════════════════════════════════════════
    # Real Data Training (обучение на реальных данных с API)
    # ═══════════════════════════════════════════════════════════════════
    # Price Normalizer - нормализация цен с разных платформ
    "PriceNormalizer",
    "PricePrediction",
    "PriceSource",
    # Real Price Collector - сбор реальных цен с DMarket, Waxpeer, Steam
    "RealPriceCollector",
    "RecommendationBatch",
    "RecommendationRiskLevel",
    "RecommendationType",
    "RiskLevel",
    "SchedulerConfig",
    "SchedulerState",
    "ScoringMetric",
    # Smart Recommendations
    "SmartRecommendations",
    "StrategyRecommendation",
    "TaskType",
    "TradeSignal",
    # Training Data Manager - управление обучающими данными
    "TrainingDataManager",
    "TrainingDataset",
    "TuningResult",
    "create_anomaly_detector",
    "create_smart_recommendations",
]

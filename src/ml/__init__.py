"""ML/AI модуль для прогнозирования цен на DMarket.

Этот модуль предоставляет адаптивные ML модели для:
- Прогнозирования цен предметов
- Определения оптимального времени покупки/продажи
- Классификации рисков сделок
- Адаптации к текущему балансу пользователя

Используемые библиотеки (все бесплатные):
- scikit-learn: основные ML модели
- NumPy: математические операции
- Собственные адаптивные алгоритмы
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

__all__ = [
    # Price Predictor
    "AdaptivePricePredictor",
    "PricePrediction",
    "PredictionConfidence",
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

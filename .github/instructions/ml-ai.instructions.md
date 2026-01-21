# ML/AI Instructions

> Применяется к файлам: `src/ml/**/*.py`, `src/ai/**/*.py`, `src/utils/skill_*.py`

## SkillsMP.com Integration

### Skill Orchestrator
```python
from src.utils.skill_orchestrator import SkillOrchestrator

orchestrator = SkillOrchestrator()

# Pipeline с context passing
result = await orchestrator.execute_pipeline([
    {"skill": "predictor", "method": "predict", "args": ["$context.item"]},
    {"skill": "classifier", "method": "classify", "args": ["$prev"]},
], initial_context={"item": item_data})
```

### Skill Profiler
```python
from src.utils.skill_profiler import profile_skill, SkillProfiler

# Декоратор для профилирования
@profile_skill("my-function", track_percentiles=True)
async def my_function():
    ...

# Получение метрик
profiler = SkillProfiler()
stats = profiler.get_stats("my-function")
# stats = {"p50": 10.5, "p95": 25.2, "p99": 50.1, "count": 1000}
```

### Ensemble Builder
```python
from src.ml.model_tuner import EnsembleBuilder

# Создание ансамбля моделей
ensemble = EnsembleBuilder(models=[model1, model2, model3])
ensemble.fit(X_train, y_train)

# Auto-weights based on validation performance
predictions = ensemble.predict(X_test)
```

## ML Model Guidelines

### Feature Engineering
```python
# Обязательные фичи для арбитража
features = [
    "price_usd",           # Цена в долларах
    "suggested_price_usd", # Рекомендованная цена
    "profit_margin",       # Маржа профита
    "daily_volume",        # Объем продаж/день
    "price_volatility",    # Волатильность за 7 дней
    "liquidity_score",     # Оценка ликвидности 0-100
    "days_on_market",      # Дней на рынке
]
```

### Model Training
```python
from sklearn.model_selection import cross_val_score
import structlog

logger = structlog.get_logger(__name__)

async def train_model(X, y, model):
    """Train ML model with validation."""
    # Cross-validation
    scores = cross_val_score(model, X, y, cv=5)

    logger.info(
        "model_training_complete",
        mean_score=scores.mean(),
        std_score=scores.std(),
        model_type=type(model).__name__
    )

    return model.fit(X, y)
```

## Concept Drift Detection

```python
from src.ml.anomaly_detection import detect_concept_drift

# Проверка дрифта каждые 24 часа
drift_detected = await detect_concept_drift(
    reference_data=historical_predictions,
    current_data=recent_predictions,
    threshold=0.05
)

if drift_detected:
    logger.warning("concept_drift_detected", action="retrain_model")
    await trigger_model_retraining()
```

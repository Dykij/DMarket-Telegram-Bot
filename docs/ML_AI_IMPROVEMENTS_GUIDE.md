# 🚀 ML/AI Improvements Guide

Руководство по новым ML/AI улучшениям на основе анализа SkillsMP.com.

## 📋 Содержание

1. [Skill Orchestrator](#skill-orchestrator)
2. [Skill Profiler](#skill-profiler)
3. [EnsembleBuilder](#ensemblebuilder)
4. [AdvancedFeatureSelector](#advancedfeaturesel)
5. [Примеры использования](#примеры-использования)

---

## Skill Orchestrator

**Файл**: `src/utils/skill_orchestrator.py`

Модуль для комбинирования ML модулей в pipelines с передачей контекста.

### Возможности

- ✅ Pipeline execution с context passing
- ✅ Параллельное выполнение независимых skills
- ✅ Метрики выполнения
- ✅ Поддержка токенов `$prev` и `$context`
- ✅ Обработка ошибок и fallback

### Использование

```python
from src.utils.skill_orchestrator import SkillOrchestrator, get_orchestrator

# Создать orchestrator
orchestrator = SkillOrchestrator()

# Зарегистрировать skills
orchestrator.register_skill("price_predictor", price_predictor)
orchestrator.register_skill("anomaly_detector", anomaly_detector)
orchestrator.register_skill("trade_classifier", classifier)

# Выполнить skill
result = await orchestrator.execute_skill(
    skill_name="price_predictor",
    method_name="predict",
    args=["AK-47 | Redline"],
)

# Создать и выполнить pipeline
pipeline = [
    {"skill": "price_predictor", "method": "predict", "args": ["$context.item_name"]},
    {"skill": "anomaly_detector", "method": "check", "args": ["$prev"]},
    {"skill": "trade_classifier", "method": "classify", "args": ["$prev"]},
]

result = await orchestrator.execute_pipeline(
    pipeline,
    initial_context={"item_name": "AK-47 | Redline", "current_price": 15.0},
)

print(f"Status: {result.status}")
print(f"Final result: {result.final_result}")

# Параллельное выполнение
results = await orchestrator.execute_parallel([
    {"skill": "predictor", "method": "predict", "args": ["item1"]},
    {"skill": "predictor", "method": "predict", "args": ["item2"]},
    {"skill": "predictor", "method": "predict", "args": ["item3"]},
])

# Получить метрики
metrics = orchestrator.get_metrics()
print(f"Total executions: {metrics['total_executions']}")
print(f"Success rate: {metrics['successful_executions'] / metrics['total_executions'] * 100}%")
```

### Токены для context passing

| Токен | Описание |
|-------|----------|
| `$prev` | Результат предыдущего шага |
| `$context` | Весь контекст |
| `$context.key` | Значение ключа из контекста |

---

## Skill Profiler

**Файл**: `src/utils/skill_profiler.py`

Модуль для профилирования производительности ML модулей.

### Возможности

- ✅ Latency percentiles (p50, p95, p99)
- ✅ Throughput calculation
- ✅ Memory monitoring (с psutil)
- ✅ Automatic bottleneck detection
- ✅ Decorator и context manager API

### Использование

#### Декоратор

```python
from src.utils.skill_profiler import profile_skill

@profile_skill("ai-arbitrage-predictor")
async def predict_opportunities(items):
    # ...processing...
    return opportunities

# Метрики собираются автоматически
```

#### Context Manager

```python
from src.utils.skill_profiler import get_profiler

profiler = get_profiler()

# Sync
with profiler.profile("price_predictor", "batch_predict", items_count=100):
    result = predictor.batch_predict(items)

# Async
async with profiler.aprofile("ai_coordinator", "analyze"):
    result = await ai.analyze_item(item)
```

#### Получение метрик

```python
profiler = get_profiler()

# Метрики одного skill
metrics = profiler.get_skill_metrics("ai-arbitrage-predictor")
print(f"P99 Latency: {metrics['latency_p99_ms']}ms")
print(f"Throughput: {metrics['throughput_per_sec']} items/sec")
print(f"Success rate: {metrics['success_rate']}%")

# Общая сводка
summary = profiler.get_summary()
print(f"Total skills: {summary['total_skills_profiled']}")
print(f"Slowest skill: {summary['slowest_skill']}")

# Выявление bottlenecks
bottlenecks = profiler.identify_bottlenecks(latency_threshold_ms=100.0)
for b in bottlenecks:
    print(f"⚠️ {b['skill_name']}: {b['issue']} - {b['recommendation']}")
```

### Метрики

| Метрика | Описание |
|---------|----------|
| `latency_p50_ms` | Медианная latency |
| `latency_p95_ms` | 95-й перцентиль latency |
| `latency_p99_ms` | 99-й перцентиль latency |
| `throughput_per_sec` | Items per second |
| `success_rate` | Процент успешных выполнений |
| `memory_peak_bytes` | Пиковое использование памяти |

---

## EnsembleBuilder

**Файл**: `src/ml/model_tuner.py`

Класс для создания ensemble моделей с автоматическим расчётом весов.

### Возможности

- ✅ VotingRegressor с автоматическими весами
- ✅ Комбинирует RandomForest, GradientBoosting, Ridge, XGBoost
- ✅ Веса на основе CV performance

### Использование

```python
from src.ml.model_tuner import EnsembleBuilder

builder = EnsembleBuilder(cv_folds=5, random_state=42)

# Создать ensemble с автоматическими весами
ensemble = builder.create_voting_ensemble(
    X_train, y_train,
    include_xgboost=True,
)

# Предсказание
predictions = ensemble.predict(X_test)

# С кастомными весами
ensemble = builder.create_voting_ensemble(
    X_train, y_train,
    include_xgboost=False,
    weights=[0.5, 0.3, 0.2],  # rf, gb, ridge
)
```

---

## AdvancedFeatureSelector

**Файл**: `src/ml/model_tuner.py`

Класс для продвинутого отбора признаков.

### Возможности

- ✅ SelectFromModel (на основе feature importance)
- ✅ Recursive Feature Elimination (RFE)
- ✅ Feature importance анализ (RF, permutation)

### Использование

#### SelectFromModel

```python
from src.ml.model_tuner import AdvancedFeatureSelector

selector = AdvancedFeatureSelector(random_state=42)

# Отбор по медианной важности
X_selected, selected_names = selector.select_from_model(
    X, y,
    feature_names=feature_names,
    threshold="median",
)

# Отбор топ-N признаков
X_selected, selected_names = selector.select_from_model(
    X, y,
    feature_names=feature_names,
    max_features=10,
)

print(f"Selected features: {selected_names}")
```

#### Recursive Feature Elimination

```python
X_selected, selected_names, rankings = selector.recursive_feature_elimination(
    X, y,
    feature_names=feature_names,
    n_features_to_select=10,
)

# rankings показывает порядок удаления признаков
for name, rank in sorted(rankings.items(), key=lambda x: x[1]):
    print(f"{name}: rank {rank}")
```

#### Feature Importance

```python
# RandomForest importance
importance = selector.get_feature_importance(
    X, y,
    feature_names=feature_names,
    method="random_forest",
)

# Permutation importance
importance = selector.get_feature_importance(
    X, y,
    feature_names=feature_names,
    method="permutation",
)

# Top 10 features
for name, score in list(importance.items())[:10]:
    print(f"{name}: {score:.4f}")
```

---

## Примеры использования

### Полный ML Pipeline

```python
from src.ml.model_tuner import AdvancedFeatureSelector, EnsembleBuilder, ModelTuner
from src.utils.skill_orchestrator import SkillOrchestrator
from src.utils.skill_profiler import get_profiler, profile_skill

# 1. Feature selection
selector = AdvancedFeatureSelector()
X_selected, selected_features = selector.select_from_model(
    X, y,
    feature_names=feature_names,
    max_features=15,
)
print(f"Selected {len(selected_features)} features")

# 2. Build ensemble
builder = EnsembleBuilder()
ensemble = builder.create_voting_ensemble(X_selected, y)

# 3. Wrap with profiling
@profile_skill("price-ensemble")
async def predict_prices(items_features):
    return ensemble.predict(items_features)

# 4. Use in orchestrator
orchestrator = SkillOrchestrator()
orchestrator.register_skill("feature_selector", selector)
orchestrator.register_skill("ensemble", ensemble)

# 5. Execute and monitor
async with get_profiler().aprofile("full_pipeline"):
    result = await orchestrator.execute_pipeline([
        {"skill": "ensemble", "method": "predict", "args": [X_test]},
    ])

# 6. Check performance
bottlenecks = get_profiler().identify_bottlenecks()
```

### Integration с существующими модулями

```python
from src.dmarket.ai_arbitrage_predictor import AIArbitragePredictor
from src.ml.llama_integration import LlamaIntegration
from src.utils.skill_orchestrator import SkillOrchestrator

# Register existing modules
orchestrator = SkillOrchestrator()
orchestrator.register_skill("arbitrage", AIArbitragePredictor())
orchestrator.register_skill("llama", LlamaIntegration())

# Define AI-powered arbitrage pipeline
pipeline = [
    {"skill": "arbitrage", "method": "predict", "args": ["$context.items"]},
    {"skill": "llama", "method": "analyze_market", "args": ["csgo", "$prev"]},
]

result = await orchestrator.execute_pipeline(
    pipeline,
    initial_context={"items": market_items},
)
```

---

## Ссылки

- [SkillsMP.com](https://skillsmp.com) - источник best practices
- [scikit-learn VotingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.VotingRegressor.html)
- [scikit-learn SelectFromModel](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectFromModel.html)
- [scikit-learn RFE](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html)

---

**Создано**: Январь 2026  
**Автор**: GitHub Copilot  
**Тесты**: 62 тестов ✅

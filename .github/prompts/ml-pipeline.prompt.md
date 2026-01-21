# ML Pipeline Prompt

Use this prompt when working with ML/AI pipeline orchestration and profiling.

## Context

This project uses:
- `SkillOrchestrator` for pipeline execution with context passing
- `SkillProfiler` for performance profiling with latency percentiles
- `EnsembleBuilder` for VotingRegressor ensembles
- `AdvancedFeatureSelector` for feature selection

## Pipeline Pattern

```python
from src.utils.skill_orchestrator import SkillOrchestrator
from src.utils.skill_profiler import profile_skill, SkillProfiler

# Create orchestrator
orchestrator = SkillOrchestrator()

# Register skills
orchestrator.register_skill("predictor", PricePredictor())
orchestrator.register_skill("classifier", TradeClassifier())

# Execute pipeline with context passing
result = await orchestrator.execute_pipeline([
    {"skill": "predictor", "method": "predict", "args": ["$context.item"]},
    {"skill": "classifier", "method": "classify", "args": ["$prev"]},
], initial_context={"item": "AK-47 | Redline"})
```

## Profiling Pattern

```python
from src.utils.skill_profiler import profile_skill, SkillProfiler

# Decorator for async functions
@profile_skill("my-skill-name")
async def my_async_function(data):
    # Your logic here
    return result

# Get metrics
profiler = SkillProfiler()
metrics = profiler.get_metrics("my-skill-name")
print(f"p50: {metrics.latency_p50}ms")
print(f"p95: {metrics.latency_p95}ms")
print(f"p99: {metrics.latency_p99}ms")
print(f"throughput: {metrics.throughput}/sec")
```

## Ensemble Pattern

```python
from src.ml.model_tuner import EnsembleBuilder

# Build ensemble with auto-weights
builder = EnsembleBuilder()
ensemble = builder.build_voting_ensemble(X_train, y_train)

# Predict
predictions = ensemble.predict(X_test)
```

## Feature Selection Pattern

```python
from src.ml.model_tuner import AdvancedFeatureSelector

# Select features
selector = AdvancedFeatureSelector()
selected_features = selector.select_features(
    X_train, y_train,
    method="select_from_model",  # or "rfe", "permutation"
    n_features=10
)
```

## Best Practices

1. **Always use `@profile_skill` decorator** for ML functions to track performance
2. **Use `$prev` token** to pass result from previous step in pipeline
3. **Use `$context.key` token** to access initial context values
4. **Handle CancelledError** properly in async functions (it's BaseException, not Exception)
5. **Check percentiles** (p95, p99) to identify performance bottlenecks

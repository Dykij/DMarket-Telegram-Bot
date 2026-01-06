# ML/AI System Documentation

Полное руководство по машинному обучению в DMarket Trading Bot.

## Содержание

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [Компоненты](#компоненты)
4. [Алгоритмы](#алгоритмы)
5. [Feature Engineering](#feature-engineering)
6. [Настройка моделей](#настройка-моделей)
7. [Best Practices](#best-practices)
8. [API Reference](#api-reference)
9. [Примеры использования](#примеры-использования)
10. [FAQ](#faq)

---

## Обзор

ML система бота использует **scikit-learn** - бесплатную и открытую библиотеку машинного обучения. Выбор scikit-learn обоснован:

| Критерий | Оценка |
|----------|--------|
| **Бесплатность** | ✅ 100% бесплатно, Apache 2.0 лицензия |
| **Стабильность** | ✅ Используется в 90% торговых ботов |
| **Интерпретируемость** | ✅ Понятные модели и feature importance |
| **Офлайн работа** | ✅ Не требует API или интернета |
| **Производительность** | ✅ Оптимизирован для CPU, поддержка GPU через XGBoost |

### Почему не Deep Learning?

В торговле **стабильность важнее сложности**:

- ✅ Классический ML (scikit-learn) - предсказуемый, быстрый, интерпретируемый
- ❌ Deep Learning - требует много данных, медленный, "чёрный ящик"

---

## Архитектура

```
src/ml/
├── __init__.py                 # Экспорт основных классов
├── feature_extractor.py        # Извлечение признаков
├── price_predictor.py          # Базовый прогнозатор
├── enhanced_predictor.py       # Улучшенный прогнозатор (ансамбль)
├── trade_classifier.py         # Классификатор сигналов
├── balance_adapter.py          # Адаптация к балансу
└── model_tuner.py              # Автонастройка гиперпараметров
```

### Поток данных

```
Рыночные данные → Feature Extractor → ML Pipeline → Прогноз → Рекомендация
                         ↓
                   [32 признака]
                         ↓
              ┌─────────────────────┐
              │   Ансамбль моделей  │
              │  ┌───────────────┐  │
              │  │ RandomForest  │──┤
              │  │     35%       │  │
              │  └───────────────┘  │
              │  ┌───────────────┐  │
              │  │   XGBoost     │──┤
              │  │     35%       │  │
              │  └───────────────┘  │
              │  ┌───────────────┐  │
              │  │ GradientBoost │──┤
              │  │     20%       │  │
              │  └───────────────┘  │
              │  ┌───────────────┐  │
              │  │    Ridge      │──┤
              │  │     10%       │  │
              │  └───────────────┘  │
              └─────────────────────┘
                         ↓
                 Взвешенный прогноз
```

---

## Компоненты

### 1. Feature Extractor

Извлекает **32 признака** из рыночных данных:

```python
from src.ml import EnhancedFeatureExtractor, GameType

extractor = EnhancedFeatureExtractor()

features = extractor.extract_features(
    item_name="AK-47 | Redline (FT)",
    current_price=15.0,
    game=GameType.CS2,
    price_history=price_history,  # [(datetime, price), ...]
    sales_history=sales_history,  # [{"timestamp": ..., "price": ...}, ...]
    market_offers=market_offers,  # Текущие офферы
    item_data={
        "float": 0.18,
        "stickers": [{"name": "Katowice 2014"}],
    }
)
```

#### Категории признаков

| Категория | Признаки | Описание |
|-----------|----------|----------|
| **Ценовые** | current_price, price_mean_7d, price_std_7d | Базовая ценовая статистика |
| **Изменения** | price_change_1h, price_change_24h, price_change_7d | Процентные изменения |
| **Технические** | rsi, volatility, momentum | RSI, волатильность, момент |
| **Ликвидность** | sales_count_24h, avg_sales_per_day | Активность продаж |
| **Временные** | hour_of_day, day_of_week, is_weekend, is_peak_hours | Время торговли |
| **Рыночные** | market_depth, competition_level | Глубина рынка |
| **Relative Strength** | relative_strength, market_index_change | Относительно индекса |
| **Time Since Sale** | time_since_last_sale, avg_time_between_sales | Время между продажами |
| **Game-specific** | float_value, pattern_score, sticker_value, gem_count | Специфичные для игры |

### 2. Price Predictor (Базовый)

```python
from src.ml import AdaptivePricePredictor

predictor = AdaptivePricePredictor(
    model_path="models/price_model.pkl",
    user_balance=100.0
)

prediction = predictor.predict(
    item_name="AK-47 | Redline",
    current_price=15.0,
    price_history=price_history,
)

print(f"24h прогноз: ${prediction.predicted_price_24h}")
print(f"Рекомендация: {prediction.buy_recommendation}")
print(f"Уверенность: {prediction.confidence}")
```

### 3. Enhanced Predictor (Улучшенный)

Использует ансамбль из 4 моделей:

```python
from src.ml import EnhancedPricePredictor, GameType

predictor = EnhancedPricePredictor(
    user_balance=500.0,
    game=GameType.CS2
)

prediction = predictor.predict(
    item_name="AWP | Dragon Lore (FN)",
    current_price=5000.0,
    game=GameType.CS2,
    item_data={
        "float": 0.01,
        "stickers": [
            {"name": "iBUYPOWER (Holo) | Katowice 2014"}
        ]
    }
)

# Результат включает:
# - predicted_price_1h, predicted_price_24h, predicted_price_7d
# - confidence_score (0-1)
# - recommendation: "strong_buy", "buy", "hold", "sell", "strong_sell"
# - reasoning: "Expected growth: 8.5%; Low float (FN)"
# - float_value, pattern_score, sticker_value (для CS2)
```

### 4. Trade Classifier

Классификатор торговых сигналов:

```python
from src.ml import AdaptiveTradeClassifier

classifier = AdaptiveTradeClassifier(
    risk_profile="moderate",  # conservative, moderate, aggressive
    user_balance=200.0
)

signal = classifier.classify(
    current_price=10.0,
    predicted_price=11.5,
    confidence=0.8,
    volatility=0.05,
    liquidity_score=0.7
)

print(f"Сигнал: {signal.signal}")  # strong_buy
print(f"Риск: {signal.risk_level}")  # medium
print(f"Размер позиции: {signal.position_size}%")  # 20%
```

### 5. Balance Adapter

Адаптация стратегии к балансу:

```python
from src.ml import BalanceAdaptiveStrategy

strategy = BalanceAdaptiveStrategy(user_balance=50.0)
recommendation = strategy.get_recommendation()

print(f"Категория: {recommendation.balance_category}")  # SMALL
print(f"Мин. профит: {recommendation.min_profit_threshold}%")  # 12%
print(f"Макс. позиция: {recommendation.max_position_percent}%")  # 30%
print(f"Макс. позиций: {recommendation.max_concurrent_positions}")  # 2
```

#### Категории баланса

| Категория | Баланс | Мин. профит | Макс. позиция | Макс. позиций | Стратегия |
|-----------|--------|-------------|---------------|---------------|-----------|
| MICRO | <$20 | 15% | 50% | 1 | Агрессивный рост |
| SMALL | $20-100 | 12% | 30% | 2 | Быстрые сделки |
| MEDIUM | $100-500 | 7% | 20% | 4 | Баланс |
| LARGE | $500-2000 | 5% | 15% | 8 | Диверсификация |
| WHALE | >$2000 | 3% | 10% | 15 | Сохранение капитала |

### 6. Model Tuner (NEW)

Автоматическая настройка гиперпараметров:

```python
from src.ml import ModelTuner, CVStrategy, ScoringMetric

tuner = ModelTuner(
    cv_strategy=CVStrategy.TIME_SERIES,  # Для временных рядов
    cv_folds=5,
    scoring=ScoringMetric.MAE,
)

# Настройка RandomForest
result = tuner.tune_random_forest(X_train, y_train)
print(result.summary())
# Model: RandomForestRegressor
# Best Score: 0.0234
# Best Params: {'n_estimators': 100, 'max_depth': 10, ...}

# Сравнение моделей
results = tuner.compare_models(X, y)
for name, eval_result in results.items():
    print(f"{name}: MAE={eval_result.mean_test_score:.4f}")
```

---

## Алгоритмы

### RandomForest (35% веса)

**Почему:** Ансамбль из сотен деревьев решений, устойчив к аномалиям.

```python
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(
    n_estimators=100,   # 100 деревьев
    max_depth=10,       # Глубина дерева
    min_samples_split=5,
    min_samples_leaf=2,
    n_jobs=-1,          # Все CPU
    random_state=42,
)
```

**Преимущества:**
- Не переобучается на случайных всплесках
- Feature importance "из коробки"
- Параллельное обучение

### XGBoost (35% веса)

**Почему:** Лучшее предсказание резких изменений тренда.

```python
from xgboost import XGBRegressor

model = XGBRegressor(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="reg:squarederror",
    n_jobs=-1,
)
```

**Преимущества:**
- Быстрее GradientBoosting в 10x
- Early stopping
- Регуляризация

### GradientBoosting (20% веса)

**Почему:** Стабильный baseline, хорошо работает на малых данных.

```python
from sklearn.ensemble import GradientBoostingRegressor

model = GradientBoostingRegressor(
    n_estimators=50,
    max_depth=3,
    learning_rate=0.1,
    min_samples_split=5,
)
```

### Ridge Regression (10% веса)

**Почему:** Быстрый fallback, линейная интерпретация.

```python
from sklearn.linear_model import Ridge

model = Ridge(alpha=1.0)
```

---

## Feature Engineering

### Новые признаки (на основе рекомендаций)

#### 1. Relative Strength

Отношение цены предмета к индексу рынка:

```python
relative_strength = current_price / market_index

# RS > 1.0 - предмет выше рынка
# RS < 1.0 - предмет ниже рынка
```

**Использование:** Если рынок растёт, а предмет стоит - сигнал к продаже.

#### 2. Time Since Last Sale

Секунды с последней продажи:

```python
time_since_last_sale = (now - last_sale_time).total_seconds()
```

**Использование:** Большое время = низкая ликвидность.

#### 3. Float/Pattern Score (CS2)

Оценка редкости float и паттерна:

```python
# Float percentile (чем ниже float, тем лучше)
float_percentile = (1 - float_value) * 100

# Pattern score
if "case hardened" in name.lower():
    if pattern_index in [661, 387, 955]:  # Blue gems
        pattern_score = 1.0
    elif pattern_index in [321, 555]:
        pattern_score = 0.8
```

#### 4. Sticker Value (CS2)

Оценка стоимости стикеров:

```python
STICKER_VALUES = {
    "ibuypower (holo) | katowice 2014": 10000,
    "titan (holo) | katowice 2014": 3000,
    "katowice 2014": 500,
}
```

### Game-Specific Features

| Игра | Признаки |
|------|----------|
| CS2/CSGO | float_value, float_percentile, pattern_index, pattern_score, sticker_count, sticker_value |
| Dota 2 | gem_count, inscribed_count, item_rarity (arcana/immortal) |
| TF2 | is_unusual, effect_value |
| Rust | has_skin, condition |

---

## Настройка моделей

### Cross-Validation

Используем **TimeSeriesSplit** для временных рядов (цены):

```python
from sklearn.model_selection import TimeSeriesSplit

cv = TimeSeriesSplit(n_splits=5)

# Важно: НЕ перемешиваем данные для временных рядов!
```

**Почему TimeSeriesSplit:**
- Сохраняет хронологический порядок
- Обучение на прошлом, валидация на будущем
- Предотвращает "заглядывание в будущее"

### GridSearchCV

Автоматический подбор гиперпараметров:

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, 15],
    "learning_rate": [0.05, 0.1, 0.2],
}

search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    cv=TimeSeriesSplit(5),
    scoring="neg_mean_absolute_error",
    n_jobs=-1,
)

search.fit(X, y)
print(search.best_params_)
```

### Pipeline

Защита от утечки данных:

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    ("model", RandomForestRegressor()),
])

# Pipeline применяет preprocessing внутри каждого fold CV
```

---

## Best Practices

### 1. Предотвращение переобучения

```python
# Проверка train/test gap
eval_result = tuner.evaluate_model(model, X, y)
if eval_result.is_overfitting():
    print("⚠️ Модель переобучена!")
```

### 2. Обработка пропусков

```python
# Всегда используем Pipeline с Imputer
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("model", model),
])
```

### 3. Масштабирование признаков

```python
# StandardScaler для моделей, чувствительных к масштабу
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", Ridge()),
])
```

### 4. Feature Importance

```python
# Анализ важности признаков
importances = model.feature_importances_
feature_names = EnhancedFeatures.feature_names()

for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1])[:10]:
    print(f"{name}: {imp:.4f}")
```

### 5. Регулярное переобучение

```python
# Автоматическое переобучение после 100 новых примеров
predictor.add_training_example(features, actual_price)
# Вызовет train() когда накопится 100 примеров
```

---

## API Reference

### EnhancedPricePredictor

```python
class EnhancedPricePredictor:
    def __init__(
        self,
        model_path: str | Path | None = None,
        user_balance: float = 100.0,
        game: GameType = GameType.CS2,
    ) -> None: ...
    
    def predict(
        self,
        item_name: str,
        current_price: float,
        game: GameType | None = None,
        price_history: list[tuple[datetime, float]] | None = None,
        sales_history: list[dict] | None = None,
        market_offers: list[dict] | None = None,
        item_data: dict | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]: ...
    
    def add_training_example(
        self,
        features: EnhancedFeatures,
        actual_future_price: float,
    ) -> None: ...
    
    def train(self, force: bool = False) -> None: ...
```

### ModelTuner

```python
class ModelTuner:
    def __init__(
        self,
        cv_strategy: CVStrategy = CVStrategy.TIME_SERIES,
        cv_folds: int = 5,
        scoring: ScoringMetric = ScoringMetric.MAE,
        n_jobs: int = -1,
        random_state: int = 42,
    ) -> None: ...
    
    def tune_random_forest(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: dict | None = None,
        use_randomized: bool = False,
        n_iter: int = 50,
    ) -> TuningResult: ...
    
    def compare_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        models: list[str] | None = None,
    ) -> dict[str, EvaluationResult]: ...
```

---

## Примеры использования

### Полный цикл прогнозирования

```python
from src.ml import (
    EnhancedPricePredictor,
    EnhancedFeatureExtractor,
    GameType,
    ModelTuner,
)

# 1. Инициализация
predictor = EnhancedPricePredictor(
    model_path="models/enhanced_model.pkl",
    user_balance=500.0,
    game=GameType.CS2,
)

# 2. Прогноз
prediction = predictor.predict(
    item_name="AK-47 | Case Hardened (MW)",
    current_price=50.0,
    game=GameType.CS2,
    item_data={
        "float": 0.09,
        "pattern": 661,  # Blue Gem
    }
)

print(f"Текущая цена: ${prediction['current_price']}")
print(f"Прогноз 24h: ${prediction['predicted_price_24h']}")
print(f"Диапазон: ${prediction['price_range_24h']}")
print(f"Уверенность: {prediction['confidence_level']}")
print(f"Рекомендация: {prediction['recommendation']}")
print(f"Причина: {prediction['reasoning']}")

# 3. Добавление примера для обучения (после реальной продажи)
actual_price = 55.0  # Реальная цена через 24h
features = predictor.feature_extractor.extract_features(...)
predictor.add_training_example(features, actual_price)
```

### Настройка и выбор лучшей модели

```python
from src.ml import ModelTuner, AutoMLSelector

# Автоматический выбор
selector = AutoMLSelector(
    cv_folds=5,
    time_budget_seconds=300,
)

best_model, results = selector.select_best_model(X_train, y_train)

# Рекомендации
for rec in selector.get_recommendations(results):
    print(rec)
# ✅ Best model: xgboost (Score: 0.0234)
# 💡 XGBoost is fast. Consider early stopping in production.
```

### Multi-Game Support

```python
# CS2
cs2_prediction = predictor.predict(
    item_name="AWP | Asiimov (FT)",
    current_price=45.0,
    game=GameType.CS2,
    item_data={"float": 0.25}
)

# Dota 2
predictor.set_game(GameType.DOTA2)
dota_prediction = predictor.predict(
    item_name="Dragonclaw Hook",
    current_price=400.0,
    game=GameType.DOTA2,
    item_data={"rarity": "immortal", "gems": [...]}
)

# TF2
tf2_prediction = predictor.predict(
    item_name="Unusual Burning Flames Team Captain",
    current_price=2000.0,
    game=GameType.TF2,
    item_data={"effect": "burning flames"}
)

# Rust
rust_prediction = predictor.predict(
    item_name="AK-47 Skin",
    current_price=5.0,
    game=GameType.RUST,
)
```

---

## FAQ

### Q: Нужен ли GPU для ML?

**A:** Нет. Все модели работают на CPU. XGBoost поддерживает GPU, но это опционально.

### Q: Как много данных нужно для обучения?

**A:** Минимум 100 примеров. Рекомендуется 1000+ для стабильных прогнозов.

### Q: Как часто переобучать модели?

**A:** Автоматически после 100 новых примеров или раз в неделю.

### Q: Какая точность прогнозов?

**A:** MAE ~2-5% от цены при достаточных данных. Зависит от ликвидности.

### Q: Работает ли с новыми предметами?

**A:** Да, но с меньшей уверенностью. Используются статистические методы.

### Q: Безопасно ли использовать pickle для моделей?

**A:** Только загружайте модели из доверенных источников (ваши собственные).

---

## Ссылки

- [scikit-learn Documentation](https://scikit-learn.org/stable/)
- [Cross-Validation Guide](https://scikit-learn.org/stable/modules/cross_validation.html)
- [GridSearchCV Guide](https://scikit-learn.org/stable/modules/grid_search.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Machine Learning Mastery](https://machinelearningmastery.com/)

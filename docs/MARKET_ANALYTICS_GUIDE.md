# 📊 Market Analytics Guide

**Версия**: 1.0
**Дата**: 23 ноября 2025 г.

---

## 📋 Обзор

Модуль расширенной аналитики предоставляет статистический анализ рынка, обнаружение трендов и алгоритмы предсказания цен для торговли на DMarket.

### Основные возможности

- ✅ **Технические индикаторы** - RSI, MACD, Bollinger Bands
- ✅ **Расчет справедливой цены** - на основе исторических данных
- ✅ **Определение трендов** - восходящий, нисходящий, боковой
- ✅ **Предсказание падения цен** - на основе множественных сигналов
- ✅ **Анализ ликвидности** - оценка торговой активности
- ✅ **Уровни поддержки/сопротивления** - ключевые ценовые уровни
- ✅ **Торговые рекомендации** - комплексные insights

---

## 🎯 Технические индикаторы

### RSI (Relative Strength Index)

**Индекс относительной силы** - измеряет импульс изменения цен.

**Интерпретация:**
- RSI > 70 → **Перекуплено** (вероятно падение)
- RSI < 30 → **Перепродано** (вероятно рост)
- RSI ≈ 50 → **Нейтрально**

```python
from src.utils.market_analytics import TechnicalIndicators

prices = [10.5, 11.2, 10.8, 11.5, 12.0, 11.8, 12.5]

rsi_value = TechnicalIndicators.rsi(prices, period=14)

if rsi_value:
    if rsi_value > 70:
        print("⚠️ Перекуплено - возможно падение цены")
    elif rsi_value < 30:
        print("✅ Перепродано - хорошее время для покупки")
    else:
        print("➖ Нейтрально")
```

### MACD (Moving Average Convergence Divergence)

**Схождение-расхождение скользящих средних** - показывает взаимосвязь между двумя скользящими средними.

**Интерпретация:**
- MACD > Signal → **Бычий тренд** (покупка)
- MACD < Signal → **Медвежий тренд** (продажа)
- Histogram > 0 → **Усиление тренда**

```python
macd_data = TechnicalIndicators.macd(
    prices,
    fast_period=12,
    slow_period=26,
    signal_period=9
)

if macd_data:
    if macd_data["macd"] > macd_data["signal"]:
        print("📈 Бычий сигнал - рассмотреть покупку")
    else:
        print("📉 Медвежий сигнал - рассмотреть продажу")

    print(f"MACD: {macd_data['macd']:.2f}")
    print(f"Signal: {macd_data['signal']:.2f}")
    print(f"Histogram: {macd_data['histogram']:.2f}")
```

### Bollinger Bands

**Полосы Боллинджера** - измеряют волатильность рынка.

**Интерпретация:**
- Цена у верхней полосы → **Потенциально перекуплено**
- Цена у нижней полосы → **Потенциально перепродано**
- Узкие полосы → **Низкая волатильность** (возможен прорыв)

```python
bb = TechnicalIndicators.bollinger_bands(prices, period=20, std_dev=2.0)

if bb:
    current_price = prices[-1]

    print(f"Upper Band: ${bb['upper']:.2f}")
    print(f"Middle Band: ${bb['middle']:.2f}")
    print(f"Lower Band: ${bb['lower']:.2f}")

    if current_price > bb['upper']:
        print("⚠️ Цена выше верхней полосы - возможна коррекция")
    elif current_price < bb['lower']:
        print("✅ Цена ниже нижней полосы - возможен отскок")
```

---

## 💰 Расчет справедливой цены

### Методы расчета

#### 1. Среднее арифметическое (Mean)

```python
from src.utils.market_analytics import MarketAnalyzer, PricePoint
from datetime import datetime, UTC

analyzer = MarketAnalyzer(min_data_points=30)

price_history = [
    PricePoint(datetime.now(UTC), 10.5),
    PricePoint(datetime.now(UTC), 11.0),
    PricePoint(datetime.now(UTC), 10.8),
    # ... больше данных
]

fair_price = analyzer.calculate_fair_price(
    price_history,
    method="mean"
)

print(f"Справедливая цена (среднее): ${fair_price:.2f}")
```

#### 2. Медиана (Median)

Устойчива к выбросам:

```python
fair_price = analyzer.calculate_fair_price(
    price_history,
    method="median"
)

print(f"Справедливая цена (медиана): ${fair_price:.2f}")
```

#### 3. Volume-Weighted (VWAP)

**Рекомендуется** - учитывает объемы торгов:

```python
price_history_with_volume = [
    PricePoint(datetime.now(UTC), 10.5, volume=100),
    PricePoint(datetime.now(UTC), 11.0, volume=150),
    PricePoint(datetime.now(UTC), 10.8, volume=80),
    # ... больше данных
]

fair_price = analyzer.calculate_fair_price(
    price_history_with_volume,
    method="volume_weighted"
)

print(f"Справедливая цена (VWAP): ${fair_price:.2f}")
```

### Использование в торговле

```python
current_price = 12.50
fair_price = analyzer.calculate_fair_price(price_history)

deviation = ((current_price - fair_price) / fair_price) * 100

if deviation > 5:
    print(f"❌ Переоценен на {deviation:.1f}% - НЕ покупать")
elif deviation < -5:
    print(f"✅ Недооценен на {abs(deviation):.1f}% - хорошая покупка")
else:
    print(f"➖ Цена близка к справедливой ({deviation:.1f}%)")
```

---

## 📈 Определение трендов

### Алгоритм

Использует краткосрочную и долгосрочную скользящие средние:

```python
trend = analyzer.detect_trend(
    price_history,
    short_period=7,   # 7 дней
    long_period=30    # 30 дней
)

print(f"Тренд: {trend}")  # BULLISH, BEARISH, или NEUTRAL
```

### Интерпретация

```python
from src.utils.market_analytics import TrendDirection

if trend == TrendDirection.BULLISH:
    print("📈 Восходящий тренд - рассмотреть покупку")
elif trend == TrendDirection.BEARISH:
    print("📉 Нисходящий тренд - избегать покупки")
else:
    print("➖ Боковой тренд - ждать сигнала")
```

---

## 🔮 Предсказание падения цен

### Комплексный анализ

Использует RSI, MACD, тренд и Bollinger Bands:

```python
prediction = analyzer.predict_price_drop(
    price_history,
    threshold=0.65  # Порог уверенности 65%
)

print(f"Предсказание падения: {prediction['prediction']}")
print(f"Уверенность: {prediction['confidence']:.1%}")
print(f"Рекомендация: {prediction['recommendation']}")

# Детальные сигналы
for indicator, data in prediction['signals'].items():
    print(f"{indicator}: {data['signal']} (вес: {data['weight']})")
```

### Пример использования в боте

```python
async def check_price_before_buy(item_id: str, price: float):
    """Проверить прогноз цены перед покупкой."""

    # Получить историю
    price_history = await db.get_price_history(item_id, days=30)

    # Анализ
    prediction = analyzer.predict_price_drop(price_history)

    if prediction['prediction'] and prediction['confidence'] > 0.7:
        # Высокая вероятность падения цены
        logger.warning(
            "Price likely to drop",
            item_id=item_id,
            confidence=prediction['confidence']
        )

        await notifier.send_notification(
            user_id=user.telegram_id,
            message=f"⚠️ Предсказание падения цены!\n"
                    f"Предмет: {item_id}\n"
                    f"Уверенность: {prediction['confidence']:.1%}\n"
                    f"Рекомендация: {prediction['recommendation']}",
            priority="HIGH"
        )

        return False  # НЕ покупать

    return True  # Можно покупать
```

---

## 🎯 Уровни поддержки и сопротивления

### Расчет

```python
levels = analyzer.calculate_support_resistance(
    price_history,
    window=5  # Окно для поиска экстремумов
)

print("Уровни поддержки:")
for support in levels['support']:
    print(f"  ${support:.2f}")

print("\nУровни сопротивления:")
for resistance in levels['resistance']:
    print(f"  ${resistance:.2f}")
```

### Использование в торговле

```python
current_price = 12.50
support_levels = levels['support']
resistance_levels = levels['resistance']

# Найти ближайшую поддержку
nearest_support = max([s for s in support_levels if s < current_price], default=0)

# Найти ближайшее сопротивление
nearest_resistance = min([r for r in resistance_levels if r > current_price], default=float('inf'))

print(f"Ближайшая поддержка: ${nearest_support:.2f}")
print(f"Ближайшее сопротивление: ${nearest_resistance:.2f}")

# Рекомендации
distance_to_support = ((current_price - nearest_support) / current_price) * 100
distance_to_resistance = ((nearest_resistance - current_price) / current_price) * 100

if distance_to_support < 3:
    print("✅ Близко к поддержке - хорошее время для покупки")
elif distance_to_resistance < 3:
    print("⚠️ Близко к сопротивлению - рассмотреть продажу")
```

---

## 💧 Анализ ликвидности

### Метрики

```python
liquidity = analyzer.analyze_liquidity(
    price_history,
    recent_period=7  # Последние 7 дней
)

print(f"Оценка ликвидности: {liquidity['score']:.2f}")
print(f"Средний дневной объем: {liquidity['avg_daily_volume']}")
print(f"Тренд объема: {liquidity['volume_trend']}")
print(f"Стабильность объема: {liquidity['volume_consistency']:.2%}")
```

### Интерпретация

```python
if liquidity['score'] > 0.7:
    print("✅ Высокая ликвидность - легко купить/продать")
elif liquidity['score'] > 0.4:
    print("➖ Средняя ликвидность")
else:
    print("❌ Низкая ликвидность - возможны проблемы с продажей")
```

---

## 🧠 Комплексные торговые insights

### Генерация рекомендаций

```python
insights = analyzer.generate_trading_insights(
    price_history,
    current_price=12.50
)

# Общая рекомендация
print(f"Рекомендация: {insights['overall']['recommendation']}")
print(f"Оценка: {insights['overall']['score']}")

# Справедливая цена
if 'fair_price' in insights:
    fp = insights['fair_price']
    print(f"\nСправедливая цена: ${fp['value']:.2f}")
    print(f"Отклонение: {fp['deviation_percent']:.1f}%")
    print(f"Переоценен: {fp['is_overpriced']}")
    print(f"Недооценен: {fp['is_underpriced']}")

# Тренд
print(f"\nТренд: {insights['trend']['direction']}")

# Предсказание
pred = insights['price_prediction']
print(f"\nПрогноз падения: {pred['prediction']}")
print(f"Уверенность: {pred['confidence']:.1%}")

# Ликвидность
liq = insights['liquidity']
print(f"\nЛиквидность: {liq['score']:.2f}")
```

### Автоматические решения

```python
async def should_buy_item(item_id: str, price: float) -> bool:
    """Решить, стоит ли покупать предмет на основе аналитики."""

    # Получить данные
    price_history = await db.get_price_history(item_id, days=30)

    # Анализ
    insights = analyzer.generate_trading_insights(price_history, price)

    recommendation = insights['overall']['recommendation']

    # Решение
    if recommendation in ['STRONG BUY', 'BUY']:
        logger.info(
            "Buy recommended",
            item_id=item_id,
            recommendation=recommendation,
            score=insights['overall']['score']
        )
        return True

    elif recommendation in ['STRONG SELL', 'SELL']:
        logger.warning(
            "Buy NOT recommended",
            item_id=item_id,
            recommendation=recommendation
        )
        return False

    else:  # HOLD
        # Дополнительные проверки
        if insights.get('fair_price', {}).get('is_underpriced'):
            return True  # Покупать если недооценен

        return False  # Иначе не покупать
```

---

## 📊 Пример: Полный анализ предмета

```python
async def analyze_item(item_title: str):
    """Полный анализ предмета."""

    # 1. Получить данные
    price_history = await db.get_price_history_by_title(
        item_title,
        days=30
    )

    current_price = await api_client.get_current_price(item_title)

    # 2. Создать анализатор
    analyzer = MarketAnalyzer(min_data_points=30)

    # 3. Генерировать insights
    insights = analyzer.generate_trading_insights(
        price_history,
        current_price
    )

    # 4. Форматировать отчет
    report = f"""
📊 Анализ: {item_title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Цена
├─ Текущая: ${current_price:.2f}
├─ Справедливая: ${insights['fair_price']['value']:.2f}
└─ Отклонение: {insights['fair_price']['deviation_percent']:.1f}%

📈 Тренд: {insights['trend']['direction']}

🔮 Прогноз
├─ Падение цены: {"Да" if insights['price_prediction']['prediction'] else "Нет"}
├─ Уверенность: {insights['price_prediction']['confidence']:.1%}
└─ Рекомендация: {insights['price_prediction']['recommendation']}

💧 Ликвидность: {insights['liquidity']['score']:.2f}

🎯 Уровни
├─ Поддержка: ${min(insights['support_resistance']['support'], default=0):.2f}
└─ Сопротивление: ${max(insights['support_resistance']['resistance'], default=0):.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ИТОГО: {insights['overall']['recommendation']}
Оценка: {insights['overall']['score']}/6
"""

    # 5. Отправить в Telegram
    await notifier.send_notification(
        user_id=user.telegram_id,
        message=report,
        category="analytics"
    )

    return insights
```

---

## 🧪 Тестирование

### Unit тесты

```python
import pytest
from src.utils.market_analytics import (
    MarketAnalyzer,
    PricePoint,
    TechnicalIndicators,
    TrendDirection
)

def test_rsi_overbought():
    """Тест RSI для перекупленного рынка."""
    # Растущие цены
    prices = [10 + i * 0.5 for i in range(20)]

    rsi = TechnicalIndicators.rsi(prices)

    assert rsi is not None
    assert rsi > 70  # Перекуплено

def test_fair_price_calculation():
    """Тест расчета справедливой цены."""
    analyzer = MarketAnalyzer()

    history = [
        PricePoint(datetime.now(UTC), 10.0, volume=100),
        PricePoint(datetime.now(UTC), 11.0, volume=150),
        PricePoint(datetime.now(UTC), 10.5, volume=120),
    ] * 10  # 30 точек

    fair_price = analyzer.calculate_fair_price(history, method="mean")

    assert fair_price is not None
    assert 10.0 <= fair_price <= 11.0

def test_trend_detection():
    """Тест определения тренда."""
    analyzer = MarketAnalyzer()

    # Восходящий тренд
    rising_prices = [
        PricePoint(datetime.now(UTC), 10 + i * 0.1)
        for i in range(40)
    ]

    trend = analyzer.detect_trend(rising_prices)
    assert trend == TrendDirection.BULLISH
```

---

## 🛡️ Best Practices

### 1. Минимум данных

```python
# Всегда проверяйте достаточность данных
MIN_DATA_POINTS = 30

if len(price_history) < MIN_DATA_POINTS:
    logger.warning("Insufficient data for analysis")
    return None
```

### 2. Обработка None

```python
# Индикаторы могут вернуть None
rsi = TechnicalIndicators.rsi(prices)

if rsi is None:
    logger.warning("Cannot calculate RSI")
    return {"signal": SignalType.HOLD}

# Продолжить анализ
```

### 3. Комбинирование сигналов

```python
# НЕ полагайтесь на один индикатор
# Комбинируйте несколько сигналов

signals = []

rsi = TechnicalIndicators.rsi(prices)
if rsi and rsi < 30:
    signals.append("BUY")

macd = TechnicalIndicators.macd(prices)
if macd and macd["macd"] > macd["signal"]:
    signals.append("BUY")

# Решение на основе большинства
buy_signals = sum(1 for s in signals if s == "BUY")
if buy_signals >= 2:
    return SignalType.BUY
```

### 4. Логирование

```python
# Логируйте все анализы для отладки
logger.info(
    "Analysis completed",
    item_id=item_id,
    current_price=current_price,
    fair_price=fair_price,
    recommendation=recommendation
)
```

---

## 📚 Ссылки

- [Technical Analysis](https://www.investopedia.com/technical-analysis-4689657)
- [RSI Indicator](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD Indicator](https://www.investopedia.com/terms/m/macd.asp)
- [Bollinger Bands](https://www.investopedia.com/terms/b/bollingerbands.asp)

---

**Версия**: 1.0
**Последнее обновление**: 23 ноября 2025 г.

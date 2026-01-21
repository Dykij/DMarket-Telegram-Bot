# Arbitrage Instructions

> Применяется к файлам: `src/dmarket/**/*.py`, `src/waxpeer/**/*.py`

## Формулы расчета прибыли

### DMarket внутренний арбитраж
```python
# Цены в ЦЕНТАХ
profit_cents = suggested_price - buy_price - (suggested_price * 0.07)
profit_percent = (profit_cents / buy_price) * 100
```

### DMarket → Waxpeer кросс-платформенный
```python
# DMarket: центы, Waxpeer: милы
dmarket_usd = dmarket_price / 100
waxpeer_usd = waxpeer_price / 1000
net_profit = (waxpeer_usd * 0.94) - dmarket_usd  # 6% комиссия Waxpeer
roi = (net_profit / dmarket_usd) * 100
```

## 5 Уровней арбитража

| Уровень | Диапазон | Min Profit |
|---------|----------|------------|
| boost | $0.50-$3 | 15% |
| standard | $3-$10 | 10% |
| medium | $10-$30 | 7% |
| advanced | $30-$100 | 5% |
| pro | $100+ | 3% |

## Обязательные проверки

```python
async def validate_arbitrage(item: ArbitrageItem) -> bool:
    """Валидация арбитражной возможности."""
    # 1. Проверка цены
    if item.price <= 0:
        return False

    # 2. Проверка профита
    if item.profit_percent < 3.0:
        return False

    # 3. Проверка ликвидности
    if item.daily_volume < 5:
        return False

    # 4. Проверка blacklist
    if await is_blacklisted(item.title):
        return False

    return True
```

## Rate Limiting

```python
from aiolimiter import AsyncLimiter

# DMarket: 30 req/min
dmarket_limiter = AsyncLimiter(30, 60)

# Waxpeer: 60 req/min
waxpeer_limiter = AsyncLimiter(60, 60)

async def api_call():
    async with dmarket_limiter:
        return await client.get(url)
```

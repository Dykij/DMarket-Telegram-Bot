# AGENTS.md — DMarket API Module

> Специфичные инструкции для работы с модулем DMarket API.
> Общие правила: см. корневой `/AGENTS.md`

## 🔑 Критически важно

### Цены в ЦЕНТАХ, не долларах!

```python
# ✅ Правильно - API работает с центами
price_cents = 1050  # = $10.50
price_usd = price_cents / 100

# Создание таргета
await api.create_targets(targets=[{
    "Title": "AK-47 | Redline",
    "Price": {"Amount": 1050, "Currency": "USD"},  # $10.50
    "Amount": 1
}])

# ❌ НЕПРАВИЛЬНО - передача долларов напрямую
price = 10.50  # Будет интерпретировано как 10 центов!
```

### Rate Limiting (30 req/min)

```python
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(max_rate=30, time_period=60)

async def api_call():
    async with rate_limiter:
        return await client.get(url)
```

### HMAC-SHA256 Аутентификация

```python
# Заголовки запроса
headers = {
    "X-Api-Key": public_key,
    "X-Sign-Date": str(int(time.time())),
    "X-Request-Sign": hmac_signature
}

# Строка для подписи
string_to_sign = f"{timestamp}{method}{path}{body}"
signature = hmac.new(secret_key.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest()
```

## 📊 Уровни арбитража

| Уровень | Цены (USD) | Цены (центы) | Мин. прибыль |
|---------|------------|--------------|--------------|
| `boost` | $0.50-$3 | 50-300 | 1.5-3% |
| `standard` | $3-$10 | 300-1000 | 3-7% |
| `medium` | $10-$30 | 1000-3000 | 5-10% |
| `advanced` | $30-$100 | 3000-10000 | 7-15% |
| `pro` | $100+ | 10000+ | 10%+ |

## 🎮 Коды игр

| Игра | gameId | Фильтры |
|------|--------|---------|
| CS:GO/CS2 | `a8db` | float, stattrak, souvenir, exterior |
| Dota 2 | `9a92` | hero, rarity, quality, slot |
| TF2 | `tf2` | class, quality, killstreak, australium |
| Rust | `rust` | category, rarity |

## 📁 Ключевые файлы

| Файл | Размер | Назначение |
|------|--------|------------|
| `dmarket_api.py` | ~127KB | Основной API клиент |
| `arbitrage_scanner.py` | ~75KB | 5-уровневый сканер |
| `targets.py` | ~35KB | Управление Buy Orders |
| `game_filters.py` | - | Фильтры по играм |
| `schemas.py` | ~17KB | Pydantic валидация |

## ⚡ Паттерны использования

### Получение баланса
```python
balance = await api.get_balance()
usd = int(balance["usd"]) / 100  # Центы → USD
```

### Сканирование арбитража
```python
scanner = ArbitrageScanner(api_client, cache)
opportunities = await scanner.scan_level(
    level="standard",
    game="csgo",
    min_profit_percent=5.0
)
```

### Создание таргета
```python
result = await target_manager.create_target(
    game="a8db",
    title="AK-47 | Redline (Field-Tested)",
    price=8.00,  # Конвертируется в 800 центов внутри
    amount=1
)
```

## ⚠️ Типичные ошибки

1. **Передача USD вместо центов** — самая частая ошибка
2. **Игнорирование rate limit** — HTTP 429
3. **Устаревший timestamp** — ошибка подписи (>2 мин)
4. **Синхронные вызовы** — блокировка event loop

## 🧪 Тестирование

```python
# Использовать VCR.py для API тестов
@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_get_balance():
    api = DMarketAPI(public_key="test", secret_key="test")
    balance = await api.get_balance()
    assert "usd" in balance
```

---

*См. также: `docs/DMARKET_API_FULL_SPEC.md` для полной спецификации API*

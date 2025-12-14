# AGENTS.md — src/utils/

> 📖 Инструкции для AI-агентов при работе с модулем `utils/`
> Полная документация: `.github/copilot-instructions.md`

## 🎯 Назначение модуля

`src/utils/` — **системные утилиты** для DMarket Telegram Bot:

- Конфигурация и настройки
- Исключения и обработка ошибок
- Rate limiting и Circuit Breaker
- Кэширование (Memory + Redis)
- Мониторинг и логирование
- WebSocket клиенты
- База данных

## 📁 Ключевые файлы

### Конфигурация

| Файл            | Описание            | Важные детали                                               |
| --------------- | ------------------- | ----------------------------------------------------------- |
| `config.py`     | Pydantic Settings   | Dataclass конфиги: BotConfig, DMarketConfig, DatabaseConfig |
| `exceptions.py` | Иерархия исключений | BaseAppException → APIError, ValidationError                |

### Rate Limiting и защита

| Файл                     | Описание                  | Важные детали                                  |
| ------------------------ | ------------------------- | ---------------------------------------------- |
| `rate_limiter.py`        | Контроль частоты запросов | DMarket: 2 rps market, 1 rps trade, 5 rps user |
| `api_circuit_breaker.py` | Circuit Breaker паттерн   | Защита от каскадных сбоев                      |
| `retry_decorator.py`     | Повторные попытки         | Exponential backoff для flaky API              |

### Кэширование

| Файл              | Описание           | TTL по умолчанию |
| ----------------- | ------------------ | ---------------- |
| `memory_cache.py` | In-memory TTLCache | 300 сек (5 мин)  |
| `redis_cache.py`  | Redis distributed  | Настраивается    |

### Мониторинг

| Файл                    | Описание           | Интеграции                |
| ----------------------- | ------------------ | ------------------------- |
| `sentry_integration.py` | Error tracking     | Sentry SDK                |
| `sentry_breadcrumbs.py` | Context tracking   | Breadcrumbs для debug     |
| `prometheus_metrics.py` | Метрики            | Prometheus exporter       |
| `health_monitor.py`     | Health checks      | Liveness/Readiness probes |
| `logging_utils.py`      | Structured logging | structlog JSON формат     |

### База данных

| Файл               | Описание           | ORM                   |
| ------------------ | ------------------ | --------------------- |
| `database.py`      | Session management | SQLAlchemy 2.0 async  |
| `state_manager.py` | State persistence  | Checkpoints, recovery |

### WebSocket

| Файл                    | Описание        | Паттерн            |
| ----------------------- | --------------- | ------------------ |
| `reactive_websocket.py` | Event-driven WS | Observable pattern |
| `websocket_client.py`   | Base WS client  | Auto-reconnection  |

### Аналитика

| Файл                      | Описание           | Функции                    |
| ------------------------- | ------------------ | -------------------------- |
| `market_analytics.py`     | Технический анализ | RSI, MACD, SMA             |
| `market_analyzer.py`      | Market analysis    | Trends, support/resistance |
| `market_visualizer.py`    | Charts generation  | matplotlib/plotly          |
| `price_analyzer.py`       | Price analysis     | Fair price calculation     |
| `price_sanity_checker.py` | Price validation   | Anomaly detection          |

## ⚠️ Критические правила

### 1. Rate Limiting — ОБЯЗАТЕЛЬНО

```python
# ✅ Правильно - через RateLimiter
async with rate_limiter.acquire("market"):
    result = await api.get_items()

# ❌ Неправильно - прямой вызов без лимитера
result = await api.get_items()  # Риск 429 ошибки!
```

**DMarket API лимиты:**

- `market` — 2 запроса/сек
- `trade` — 1 запрос/сек
- `user` — 5 запросов/сек
- `balance` — 10 запросов/сек

### 2. Circuit Breaker — для внешних API

```python
from src.utils.api_circuit_breaker import circuit_breaker

# ✅ Правильно
@circuit_breaker(failure_threshold=5, timeout=60)
async def call_external_api():
    ...

# ❌ Неправильно - без защиты
async def call_external_api():  # Риск каскадного сбоя!
    ...
```

### 3. Исключения — используй иерархию

```python
from src.utils.exceptions import APIError, ValidationError, RateLimitError

# ✅ Правильно - специфичное исключение
raise APIError(
    message="DMarket API error",
    code=ErrorCode.API_ERROR,
    details={"status": 429, "endpoint": "/market/items"}
)

# ❌ Неправильно - голое Exception
raise Exception("API error")  # Теряется контекст!
```

**Иерархия исключений:**

```
BaseAppException
├── APIError            # Ошибки внешних API
├── ValidationError     # Ошибки валидации данных
├── AuthError           # Ошибки аутентификации
├── RateLimitError      # Превышение лимитов
├── NetworkError        # Сетевые ошибки
├── DatabaseError       # Ошибки БД
└── BusinessLogicError  # Бизнес-логика
```

### 4. Кэширование — выбирай правильный тип

```python
# Memory cache — для локальных данных
from src.utils.memory_cache import TTLCache

cache = TTLCache(maxsize=1000, ttl=300)

# Redis cache — для distributed данных
from src.utils.redis_cache import RedisCache

redis_cache = RedisCache(url="redis://localhost:6379")
```

**Когда что использовать:**

| Сценарий                | Решение        |
| ----------------------- | -------------- |
| Данные одного инстанса  | `memory_cache` |
| Shared между инстансами | `redis_cache`  |
| Высокая частота доступа | `memory_cache` |
| Большой объем данных    | `redis_cache`  |

### 5. Логирование — structlog формат

```python
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# ✅ Правильно - структурированный лог
logger.info(
    "operation_completed",
    user_id=123,
    duration_ms=450,
    items_count=25
)

# ❌ Неправильно - строковая интерполяция
logger.info(f"Completed for user {user_id}")  # Теряется структура!
```

### 6. Конфигурация — через Config класс

```python
from src.utils.config import Config

config = Config.load()

# ✅ Правильно
api_key = config.dmarket.api_key
db_url = config.database.url

# ❌ Неправильно - os.getenv напрямую
api_key = os.getenv("API_KEY")  # Нет валидации!
```

## 🧪 Тестирование

### Fixtures для utils

```python
@pytest.fixture
def mock_rate_limiter():
    """Мок RateLimiter для тестов."""
    limiter = AsyncMock(spec=RateLimiter)
    limiter.acquire = AsyncMock(return_value=AsyncContextManager())
    return limiter

@pytest.fixture
def mock_circuit_breaker():
    """Circuit breaker в закрытом состоянии."""
    cb = AsyncMock()
    cb.state = CircuitBreakerState.CLOSED
    return cb
```

### Тесты для исключений

```python
def test_api_error_serialization():
    """Тест сериализации APIError."""
    error = APIError(
        message="Test error",
        code=ErrorCode.API_ERROR,
        details={"key": "value"}
    )

    result = error.to_dict()

    assert result["code"] == 2000
    assert result["message"] == "Test error"
    assert result["details"] == {"key": "value"}
```

## 📊 Метрики и мониторинг

### Prometheus метрики

```python
from src.utils.prometheus_metrics import (
    api_requests_total,
    api_request_duration,
    cache_hits_total,
)

# Инкремент счетчика
api_requests_total.labels(endpoint="market", status="success").inc()

# Запись времени
with api_request_duration.labels(endpoint="market").time():
    await make_request()
```

### Sentry breadcrumbs

```python
from src.utils.sentry_breadcrumbs import add_breadcrumb

add_breadcrumb(
    category="api",
    message="Fetching market items",
    level="info",
    data={"game": "csgo", "limit": 100}
)
```

## 🔗 Зависимости модуля

**Внешние:**

- `aiolimiter` — async rate limiting
- `redis` — Redis клиент
- `structlog` — structured logging
- `sentry-sdk` — error tracking
- `prometheus-client` — метрики
- `sqlalchemy[asyncio]` — async ORM

**Внутренние:**

- `src.models` — модели данных для БД
- `src.dmarket` — DMarket API клиент

## 📚 Документация

- [CACHING_GUIDE.md](../../docs/CACHING_GUIDE.md) — стратегии кэширования
- [ERROR_HANDLING_GUIDE.md](../../docs/ERROR_HANDLING_GUIDE.md) — обработка ошибок
- [MONITORING_GUIDE.md](../../docs/MONITORING_GUIDE.md) — мониторинг и алерты
- [logging_and_error_handling.md](../../docs/logging_and_error_handling.md) — логирование

---

*Файл соответствует стандарту [AGENTS.md](https://agents.md)*

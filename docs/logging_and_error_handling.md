# 📝 Logging and Error Handling Guide

**Версия**: 1.0.0
**Последнее обновление**: 28 декабря 2025 г.

---

## 📋 Обзор

Руководство по логированию и обработке ошибок в DMarket Telegram Bot.

## 🔧 Структурированное логирование

Проект использует **structlog** для структурированного JSON логирования.

### Базовое использование

```python
import structlog

logger = structlog.get_logger(__name__)

# Информационное сообщение
logger.info(
    "arbitrage_scan_completed",
    game="csgo",
    opportunities_found=15,
    scan_duration_ms=1250
)

# Предупреждение
logger.warning(
    "rate_limit_approaching",
    current_calls=25,
    max_calls=30
)

# Ошибка
logger.error(
    "api_request_failed",
    endpoint="/marketplace-api/v1/items",
    status_code=500,
    error="Internal Server Error"
)
```

### Уровни логирования

| Уровень | Использование |
|---------|---------------|
| `DEBUG` | Детальная отладка, трассировка |
| `INFO` | Общая информация о работе |
| `WARNING` | Предупреждения, нестандартные ситуации |
| `ERROR` | Ошибки, требующие внимания |
| `CRITICAL` | Критические ошибки, сбои |

### Конфигурация

```python
# src/utils/logging_utils.py
import structlog

def configure_logging(log_level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

## ⚠️ Обработка ошибок

### Иерархия исключений

```python
# src/utils/exceptions.py

class DMarketBotError(Exception):
    """Базовое исключение бота."""
    pass

class APIError(DMarketBotError):
    """Ошибка API DMarket."""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)

class AuthenticationError(APIError):
    """Ошибка аутентификации."""
    pass

class RateLimitError(APIError):
    """Превышен лимит запросов."""
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)

class ValidationError(DMarketBotError):
    """Ошибка валидации данных."""
    pass
```

### Обработка в коде

```python
from src.utils.exceptions import APIError, RateLimitError

async def fetch_market_data(item_id: str):
    try:
        response = await api.get_item(item_id)
        return response
    except RateLimitError as e:
        logger.warning(
            "rate_limit_exceeded",
            retry_after=e.retry_after
        )
        await asyncio.sleep(e.retry_after)
        return await fetch_market_data(item_id)
    except APIError as e:
        logger.error(
            "api_error",
            status_code=e.status_code,
            item_id=item_id
        )
        raise
```

## 🔄 Retry механизм

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

## 📊 Sentry интеграция

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    send_default_pii=False
)

# Добавление контекста
sentry_sdk.set_user({"id": user_id})
sentry_sdk.set_tag("game", "csgo")
```

## 🛡️ Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api():
    return await api.request()
```

---

**Подробнее**: [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)

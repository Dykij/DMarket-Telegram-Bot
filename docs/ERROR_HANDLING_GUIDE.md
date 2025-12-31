# Error Handling and Monitoring Guide

**Last updated**: December 28, 2025  
**Status**: ✅ Production Ready

---

## 📋 Overview

This guide covers the comprehensive error handling and monitoring infrastructure implemented in the DMarket Telegram Bot, including:

- **Retry mechanisms** with exponential backoff
- **Sentry integration** for production error tracking
- **Error boundaries** for Telegram handlers
- **Graceful error recovery**

---

## 🔄 Retry Mechanisms

### Retry Decorator

The `@retry_on_failure` decorator provides automatic retry logic for functions that may fail temporarily.

**Module**: `src/utils/retry_decorator.py`

#### Basic Usage

```python
from src.utils.retry_decorator import retry_on_failure, retry_api_call

# Generic retry with custom exceptions
@retry_on_failure(
    max_attempts=3,
    min_wait=2.0,
    max_wait=10.0,
    retry_on=(NetworkError, ConnectionError)
)
async def fetch_data():
    # Your code here
    return await api.get_data()

# API-specific retry (pre-configured)
@retry_api_call(max_attempts=5, min_wait=1.0, max_wait=30.0)
async def get_market_items():
    return await dmarket_api.get_market_items()
```

#### How It Works

1. **Exponential Backoff**: Wait time increases exponentially between retries
2. **Selective Retry**: Only retries on specified exception types
3. **Logging**: Automatically logs retry attempts and final failures
4. **Configurable**: Customize attempts, wait times, and retry conditions

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_attempts` | int | 3 | Maximum number of retry attempts |
| `min_wait` | float | 2.0 | Minimum wait time between retries (seconds) |
| `max_wait` | float | 10.0 | Maximum wait time between retries (seconds) |
| `multiplier` | float | 1.0 | Multiplier for exponential backoff |
| `retry_on` | tuple | NetworkError, ConnectionError, TimeoutError | Exception types to retry on |

#### Pre-configured Decorators

##### `@retry_api_call`

Pre-configured for API calls, retries on:
- `NetworkError`
- `RateLimitError`
- `ConnectionError`
- `TimeoutError`

```python
@retry_api_call(max_attempts=5)
async def critical_api_operation():
    return await api.perform_operation()
```

---

## 📊 Sentry Integration

### Overview

Sentry provides real-time error tracking, performance monitoring, and release tracking for production environments.

**Module**: `src/utils/sentry_integration.py`

### Initialization

Sentry is automatically initialized in `src/main.py` when running in production mode.

```python
from src.utils.sentry_integration import init_sentry

init_sentry(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    release="1.0.0",
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of profiles
)
```

### Environment Variables

Add to your `.env` file:

```bash
# Sentry DSN (get from Sentry dashboard)
SENTRY_DSN=https://xxx@sentry.io/xxx

# Release version for tracking
SENTRY_RELEASE=1.0.0

# Environment (production, staging, development)
SENTRY_ENVIRONMENT=production
```

### Capturing Exceptions

#### Automatic Capture

The `@telegram_error_boundary` decorator automatically captures exceptions:

```python
from src.utils.telegram_error_handlers import telegram_error_boundary

@telegram_error_boundary()
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Errors are automatically captured in Sentry
    pass
```

#### Manual Capture

```python
from src.utils.sentry_integration import capture_exception

try:
    risky_operation()
except Exception as e:
    capture_exception(
        e,
        level="error",
        tags={"operation": "arbitrage_scan"},
        extra={"item_count": 100}
    )
```

### Breadcrumbs

Add context to error reports:

```python
from src.utils.sentry_integration import add_breadcrumb

add_breadcrumb(
    message="User started arbitrage scan",
    category="user_action",
    level="info",
    data={"user_id": 12345, "game": "csgo"}
)
```

### User Context

Associate errors with specific users:

```python
from src.utils.sentry_integration import set_user_context

set_user_context(
    user_id=12345,
    username="trader_pro",
    subscription="premium"
)
```

### Performance Monitoring

Track transaction performance:

```python
from src.utils.sentry_integration import set_transaction_name

set_transaction_name("arbitrage_scan_csgo")
```

---

## 🛡️ Error Boundaries for Telegram Handlers

### Overview

Error boundaries provide comprehensive error handling for Telegram bot handlers, including:

- Automatic exception catching
- User-friendly error messages
- Sentry integration
- Context logging

**Module**: `src/utils/telegram_error_handlers.py`

### The `@telegram_error_boundary` Decorator

#### Basic Usage

```python
from src.utils.telegram_error_handlers import telegram_error_boundary
from telegram import Update
from telegram.ext import ContextTypes

@telegram_error_boundary(
    user_friendly_message="❌ Failed to perform scan"
)
async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handler logic
    pass
```

#### Features

1. **Automatic Error Catching**: Catches all exceptions
2. **User Notifications**: Sends friendly error messages to users
3. **Context Logging**: Logs user_id, command, parameters
4. **Sentry Integration**: Automatically captures errors in Sentry
5. **Error Type Handling**: Different responses for different error types

#### Error Type Responses

| Error Type | User Message | Sentry Level |
|------------|-------------|--------------|
| `ValidationError` | ❌ Ошибка валидации: {details} | warning |
| `AuthenticationError` | ❌ Ошибка аутентификации. Проверьте API ключи | error |
| `RateLimitError` | ⏳ Превышен лимит запросов. Попробуйте через {N} секунд | warning |
| `APIError` | ❌ Ошибка при обращении к API DMarket | error |
| `Exception` (generic) | Custom user message | error |

### BaseHandler Class

For more complex handlers, extend `BaseHandler`:

```python
from src.utils.telegram_error_handlers import BaseHandler
from telegram import Update

class MyHandler(BaseHandler):
    def __init__(self):
        super().__init__(logger_name="MyHandler")
    
    @telegram_error_boundary()
    async def handle_command(self, update: Update, context):
        # Validate user
        if not await self.validate_user(update):
            return
        
        # Your logic here
        
        # Safe reply (handles both messages and callbacks)
        await self.safe_reply(
            update,
            "✅ Operation completed"
        )
```

---

## 🔧 Configuration

### Retry Settings

Customize retry behavior in your code:

```python
from src.utils.retry_decorator import retry_on_failure

# Aggressive retry for critical operations
@retry_on_failure(
    max_attempts=10,
    min_wait=1.0,
    max_wait=60.0,
    multiplier=2.0
)
async def critical_operation():
    pass

# Quick fail for non-critical operations
@retry_on_failure(
    max_attempts=2,
    min_wait=0.5,
    max_wait=1.0
)
async def optional_operation():
    pass
```

### Sentry Configuration

Configure Sentry behavior:

```python
# In src/main.py or your initialization code
init_sentry(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    release="1.0.0",
    traces_sample_rate=0.2,  # 20% of transactions
    profiles_sample_rate=0.1,  # 10% of profiles
    debug=False,  # Enable for debugging
)
```

---

## 📝 Best Practices

### 1. Use Retry for Transient Failures

✅ **DO**: Use retry for network errors, timeouts, rate limits
```python
@retry_api_call()
async def fetch_market_data():
    return await api.get_market_items()
```

❌ **DON'T**: Use retry for validation errors, authentication errors
```python
# Bad - validation errors won't be fixed by retrying
@retry_on_failure()
async def validate_user_input(data):
    if not data:
        raise ValidationError("No data")
```

### 2. Add Context to Error Captures

✅ **DO**: Provide rich context
```python
capture_exception(
    e,
    tags={"operation": "buy_item", "game": "csgo"},
    extra={"item_id": "xxx", "price": 10.50}
)
```

❌ **DON'T**: Capture without context
```python
capture_exception(e)
```

### 3. Use Error Boundaries Consistently

✅ **DO**: Apply to all Telegram handlers
```python
@telegram_error_boundary()
async def every_handler(update, context):
    pass
```

❌ **DON'T**: Mix error handling approaches
```python
# Bad - inconsistent error handling
async def some_handler(update, context):
    try:
        # manual try-catch
    except:
        # inconsistent with other handlers
```

### 4. Log Meaningful Information

✅ **DO**: Log actionable information
```python
logger.error(
    "Failed to buy item",
    extra={
        "item_id": "xxx",
        "price": 10.50,
        "user_id": 12345,
        "error": str(e)
    }
)
```

❌ **DON'T**: Log without context
```python
logger.error("Error occurred")
```

---

## 🧪 Testing Error Handling

### Testing Retry Logic

```python
import pytest
from src.utils.retry_decorator import retry_on_failure
from src.utils.exceptions import NetworkError

@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    call_count = 0
    
    @retry_on_failure(max_attempts=3, min_wait=0.1)
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise NetworkError("Temporary failure")
        return "success"
    
    result = await flaky_function()
    
    assert result == "success"
    assert call_count == 2
```

### Testing Error Boundaries

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.utils.telegram_error_handlers import telegram_error_boundary

@pytest.mark.asyncio
async def test_error_boundary_catches_exception():
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    @telegram_error_boundary()
    async def failing_handler(update, context):
        raise ValueError("Test error")
    
    # Should not raise, should send error message
    await failing_handler(update, None)
    
    update.message.reply_text.assert_called_once()
```

---

## 🚀 Production Checklist

Before deploying to production:

- [ ] Set `SENTRY_DSN` in environment variables
- [ ] Set `SENTRY_RELEASE` to current version
- [ ] Set `SENTRY_ENVIRONMENT=production`
- [ ] Apply `@telegram_error_boundary` to all Telegram handlers
- [ ] Use `@retry_api_call` for critical API operations
- [ ] Configure appropriate retry settings for your workload
- [ ] Test error handling in staging environment
- [ ] Verify Sentry receives test errors
- [ ] Set up Sentry alerts and notifications
- [ ] Document your error handling strategy

---

## 📚 Related Documentation

- [Tenacity Library Documentation](https://tenacity.readthedocs.io/)
- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [DMarket API Error Codes](https://docs.dmarket.com/v1/swagger.html)
- [Testing Guide](TESTING_GUIDE.md)

---

## 🔗 Quick Links

- **Retry Decorator**: `src/utils/retry_decorator.py`
- **Sentry Integration**: `src/utils/sentry_integration.py`
- **Error Handlers**: `src/utils/telegram_error_handlers.py`
- **Tests**: `tests/utils/test_retry_decorator.py`

---

**Version**: 1.0  
**Author**: DMarket Bot Development Team  
**Last Review**: December 4, 2025

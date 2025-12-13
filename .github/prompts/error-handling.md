# Error Handling - Правила обработки ошибок

## Основные принципы

### 1. НЕ используй голый except
```python
# ❌ НЕПРАВИЛЬНО
try:
    result = await api.fetch_data()
except:
    pass

# ✅ Правильно - конкретные типы исключений
try:
    result = await api.fetch_data()
except httpx.HTTPStatusError as e:
    logger.error("http_error", status=e.response.status_code)
    raise
except httpx.RequestError as e:
    logger.error("request_error", error=str(e))
    raise
```

### 2. Используй structlog с контекстом
```python
import structlog

logger = structlog.get_logger(__name__)

async def process_order(order_id: str, user_id: int) -> None:
    logger.info("processing_order", order_id=order_id, user_id=user_id)

    try:
        result = await execute_order(order_id)
        logger.info("order_completed", order_id=order_id, result=result)
    except Exception as e:
        logger.error(
            "order_failed",
            order_id=order_id,
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### 3. Retry с tenacity
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
)
async def fetch_with_retry(url: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### 4. Кастомные исключения проекта
```python
class DMarketError(Exception):
    """Базовое исключение для DMarket операций."""
    pass

class RateLimitError(DMarketError):
    """Превышен лимит запросов API."""
    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")

class InsufficientFundsError(DMarketError):
    """Недостаточно средств для операции."""
    def __init__(self, required: float, available: float) -> None:
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient funds: need ${required:.2f}, have ${available:.2f}"
        )

class ItemNotFoundError(DMarketError):
    """Предмет не найден на маркете."""
    pass
```

### 5. Обработка HTTP статусов
```python
async def handle_api_response(response: httpx.Response) -> dict:
    """Обработать ответ API с правильными исключениями."""

    if response.status_code == 200:
        return response.json()

    if response.status_code == 401:
        raise DMarketError("Invalid API credentials")

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise RateLimitError(retry_after=retry_after)

    if response.status_code == 404:
        raise ItemNotFoundError("Resource not found")

    if response.status_code >= 500:
        raise DMarketError(f"Server error: {response.status_code}")

    # Неожиданный статус
    response.raise_for_status()
```

### 6. Context manager для cleanup
```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def managed_api_client() -> AsyncGenerator[DMarketClient, None]:
    """Context manager с гарантированным cleanup."""
    client = DMarketClient(public_key, secret_key)
    try:
        yield client
    finally:
        await client.close()

# Использование
async def main() -> None:
    async with managed_api_client() as client:
        balance = await client.get_balance()
```

### 7. Circuit Breaker паттерн
```python
from src.utils.api_circuit_breaker import APICircuitBreaker

circuit_breaker = APICircuitBreaker(
    failure_threshold=5,
    reset_timeout=60.0
)

async def protected_api_call() -> dict:
    async with circuit_breaker:
        return await risky_api_operation()
```

## Telegram Bot обработка ошибок

```python
from telegram import Update
from telegram.ext import ContextTypes

async def command_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик команды с правильной обработкой ошибок."""

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    try:
        result = await process_command(user_id)
        await update.message.reply_text(f"✅ Готово: {result}")

    except RateLimitError as e:
        await update.message.reply_text(
            f"⏳ Слишком много запросов. Подождите {e.retry_after} сек."
        )

    except InsufficientFundsError as e:
        await update.message.reply_text(
            f"💰 Недостаточно средств: нужно ${e.required:.2f}"
        )

    except DMarketError as e:
        logger.error("dmarket_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Ошибка DMarket. Попробуйте позже."
        )

    except Exception as e:
        logger.exception("unexpected_error", user_id=user_id)
        await update.message.reply_text(
            "❌ Произошла неожиданная ошибка."
        )
```

## Чеклист для code review

- [ ] Нет голых `except:` или `except Exception:`
- [ ] Все ошибки логируются с контекстом
- [ ] Используются конкретные типы исключений
- [ ] Retry логика для сетевых операций
- [ ] Информативные сообщения об ошибках для пользователя
- [ ] Resources закрываются в finally/context manager

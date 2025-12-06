# Python Best Practices для DMarket Bot

## 🎯 Основные принципы

### 1. Асинхронность (Async/Await)

**ВСЕГДА используй async/await для I/O операций:**

```python
# ✅ Правильно
async def fetch_data(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ Неправильно
def fetch_data(url: str) -> dict:
    response = requests.get(url)
    return response.json()
```

### 2. Типизация

**Используй аннотации типов везде:**

```python
# ✅ Правильно
from typing import TypeAlias

PriceData: TypeAlias = dict[str, float | int]

async def get_price(item_id: str, currency: str = "USD") -> PriceData | None:
    """Получить цену предмета."""
    ...

# ❌ Неправильно
async def get_price(item_id, currency="USD"):
    ...
```

### 3. Структурированное логирование

**Используй structlog с контекстом:**

```python
# ✅ Правильно
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "order_processed",
    order_id=order_id,
    user_id=user_id,
    amount=amount,
    currency="USD"
)

# ❌ Неправильно
print(f"Order {order_id} processed for user {user_id}")
```

### 4. Обработка ошибок

**Используй retry логику и специфичные исключения:**

```python
# ✅ Правильно
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def api_call(url: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("http_error", url=url, status=e.response.status_code)
        raise
    except httpx.RequestError as e:
        logger.error("request_error", url=url, error=str(e))
        raise

# ❌ Неправильно
async def api_call(url: str):
    try:
        response = await client.get(url)
        return response.json()
    except:
        print("Error")
```

## 📝 Docstrings

**Используй Google Style:**

```python
async def calculate_profit(
    buy_price: float,
    sell_price: float,
    fee_percent: float = 7.0
) -> float:
    """Рассчитать прибыль от арбитража с учетом комиссии.

    Args:
        buy_price: Цена покупки предмета в USD
        sell_price: Цена продажи предмета в USD
        fee_percent: Процент комиссии площадки (по умолчанию 7%)

    Returns:
        Чистая прибыль от арбитража в USD

    Raises:
        ValueError: Если цены отрицательные

    Example:
        >>> await calculate_profit(10.0, 15.0, 7.0)
        3.95
    """
    if buy_price < 0 or sell_price < 0:
        raise ValueError("Prices cannot be negative")

    fee = sell_price * (fee_percent / 100)
    return sell_price - buy_price - fee
```

## 🔒 Безопасность

**НЕ логируй секреты:**

```python
# ✅ Правильно
def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}***{api_key[-4:]}"

logger.info("api_call", key=mask_api_key(api_key))

# ❌ Неправильно
logger.info(f"API key: {api_key}")
```

## 📊 Тестирование

**Используй AAA паттерн:**

```python
@pytest.mark.asyncio
async def test_get_balance_returns_valid_balance():
    """Тест проверяет корректный возврат баланса."""
    # Arrange
    api_client = DMarketAPI(public_key="test", secret_key="test")

    # Act
    balance = await api_client.get_balance()

    # Assert
    assert balance is not None
    assert "USD" in balance
    assert balance["USD"] >= 0
```

## 🎨 Форматирование

**Используй Ruff для форматирования:**

- Максимальная длина строки: 88 символов
- Двойные кавычки для строк
- Trailing commas в списках
- Сортировка импортов

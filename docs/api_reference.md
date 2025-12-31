# API Reference

**Версия**: 1.0.0
**Последнее обновление**: 28 декабря 2025 г.

---

## DMarket API Client

The DMarket API client provides a comprehensive interface to the DMarket marketplace API with built-in rate limiting, caching, and error handling.

### Class: DMarketAPI

#### Constructor

```python
DMarketAPI(
    public_key: str,
    secret_key: str,
    api_url: str = "https://api.dmarket.com",
    max_retries: int = 3,
    connection_timeout: float = 30.0,
    enable_cache: bool = True
)
```

**Parameters:**
- `public_key`: Your DMarket API public key
- `secret_key`: Your DMarket API secret key
- `api_url`: DMarket API base URL
- `max_retries`: Maximum number of retries for failed requests
- `connection_timeout`: Connection timeout in seconds
- `enable_cache`: Enable response caching

#### Methods

##### Balance Operations

**`async get_balance() -> Dict[str, Any]`**

Get user's account balance.

```python
balance = await api.get_balance()
print(f"Balance: ${balance['balance']:.2f}")
```

**Returns:**
```python
{
    "balance": 100.50,
    "available_balance": 95.25,
    "total_balance": 100.50,
    "has_funds": True,
    "error": False
}
```

##### Market Operations

**`async get_market_items(game: str, limit: int = 100, **kwargs) -> Dict[str, Any]`**

Get items from the marketplace.

**Parameters:**
- `game`: Game identifier (e.g., "csgo", "dota2")
- `limit`: Maximum number of items to return
- `offset`: Pagination offset
- `currency`: Price currency ("USD", "EUR")
- `price_from`: Minimum price filter
- `price_to`: Maximum price filter
- `title`: Filter by item title
- `sort`: Sort order ("price", "price_desc", "date")

```python
items = await api.get_market_items(
    game="csgo",
    limit=50,
    price_from=5.0,
    price_to=100.0,
    sort="price"
)
```

**`async get_all_market_items(game: str, max_items: int = 1000, **kwargs) -> List[Dict[str, Any]]`**

Get all market items using automatic pagination.

```python
all_items = await api.get_all_market_items(
    game="csgo",
    max_items=500
)
```

##### Trading Operations

**`async buy_item(item_id: str, price: float, game: str = "csgo") -> Dict[str, Any]`**

Purchase an item from the marketplace.

```python
result = await api.buy_item(
    item_id="item_12345",
    price=25.50,
    game="csgo"
)
```

**`async sell_item(item_id: str, price: float, game: str = "csgo") -> Dict[str, Any]`**

List an item for sale.

```python
result = await api.sell_item(
    item_id="item_67890",
    price=30.75,
    game="csgo"
)
```

##### Inventory Operations

**`async get_user_inventory(game: str = "csgo", limit: int = 100, offset: int = 0) -> Dict[str, Any]`**

Get user's inventory items.

```python
inventory = await api.get_user_inventory(
    game="csgo",
    limit=50
)
```

##### Analytics Operations

**`async get_sales_history(game: str, title: str, days: int = 7) -> Dict[str, Any]`**

Get sales history for an item.

**`async get_item_price_history(game: str, title: str, period: str = "last_month") -> Dict[str, Any]`**

Get price history for an item.

**`async get_market_aggregated_prices(game: str, title: str = None) -> Dict[str, Any]`**

Get aggregated market prices.

##### Cache Management

**`async clear_cache() -> None`**

Clear all cached responses.

**`async clear_cache_for_endpoint(endpoint: str) -> None`**

Clear cache for specific endpoint.

#### Context Manager Usage

```python
async with DMarketAPI(public_key, secret_key) as api:
    balance = await api.get_balance()
    items = await api.get_market_items("csgo")
```

## Configuration Management

### Class: Config

#### Loading Configuration

```python
# Load from environment variables only
config = Config.load()

# Load from YAML file + environment variables
config = Config.load("config/production.yaml")
```

#### Configuration Sections

**BotConfig**
- `token`: Telegram bot token
- `username`: Bot username
- `webhook_url`: Webhook URL for production
- `webhook_secret`: Webhook secret key

**DMarketConfig**
- `api_url`: DMarket API URL
- `public_key`: API public key
- `secret_key`: API secret key
- `rate_limit`: API rate limit (requests per minute)

**DatabaseConfig**
- `url`: Database connection URL
- `echo`: Enable SQL query logging
- `pool_size`: Connection pool size
- `max_overflow`: Maximum connection overflow

**SecurityConfig**
- `allowed_users`: List of allowed user IDs
- `admin_users`: List of admin user IDs

## Database Operations

### Class: DatabaseManager

#### Initialization

```python
db = DatabaseManager("postgresql://user:pass@localhost/db")
await db.init_database()
```

#### User Management

**`async get_or_create_user(telegram_id: int, **kwargs) -> User`**

Get existing user or create new one.

```python
user = await db.get_or_create_user(
    telegram_id=123456789,
    username="john_doe",
    first_name="John",
    last_name="Doe"
)
```

#### Logging

**`async log_command(user_id: UUID, command: str, **kwargs) -> None`**

Log bot command execution.

```python
await db.log_command(
    user_id=user.id,
    command="/balance",
    success=True,
    execution_time_ms=250
)
```

#### Market Data

**`async save_market_data(item_id: str, game: str, item_name: str, price_usd: float, **kwargs) -> None`**

Save market data for analytics.

```python
await db.save_market_data(
    item_id="item_123",
    game="csgo",
    item_name="AK-47 | Redline",
    price_usd=12.50,
    volume_24h=150
)
```

## Analytics & Visualization

### Class: ChartGenerator

#### Chart Types

**`create_price_history_chart(price_data: List[Dict], title: str) -> io.BytesIO`**

Generate price history line chart.

**`create_market_overview_chart(items_data: List[Dict], title: str) -> io.BytesIO`**

Generate market overview bar chart.

**`create_arbitrage_opportunities_chart(opportunities: List[Dict], title: str) -> io.BytesIO`**

Generate arbitrage opportunities chart.

**`create_volume_analysis_chart(volume_data: List[Dict], title: str) -> io.BytesIO`**

Generate trading volume analysis chart.

#### Usage Example

```python
from src.utils.analytics import ChartGenerator

generator = ChartGenerator()
price_data = [
    {"date": "2023-01-01", "price": 10.50},
    {"date": "2023-01-02", "price": 11.25},
    # ... more data
]

chart = generator.create_price_history_chart(
    price_data=price_data,
    title="AK-47 Price History"
)

# Send chart via Telegram
await context.bot.send_photo(
    chat_id=update.effective_chat.id,
    photo=chart
)
```

### Class: MarketAnalyzer

#### Statistical Analysis

**`calculate_price_statistics(price_data: List[float]) -> Dict[str, float]`**

Calculate comprehensive price statistics.

```python
stats = MarketAnalyzer.calculate_price_statistics([10.5, 11.2, 9.8, 12.1])
# Returns: mean, median, std, min, max, q25, q75, range, cv
```

**`detect_price_trends(price_data: List[Dict], window: int = 5) -> Dict[str, Any]`**

Detect price trends using moving averages.

**`find_support_resistance_levels(price_data: List[float]) -> Dict[str, List[float]]`**

Find support and resistance levels.

## Error Handling

### Exception Classes

**DMarketAPIError**: Base exception for API errors
**AuthenticationError**: Invalid API credentials
**RateLimitError**: API rate limit exceeded
**ValidationError**: Invalid input parameters

### Error Response Format

```python
{
    "error": True,
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "status_code": 429,
    "retry_after": 60
}
```

## Rate Limiting

The API client includes built-in rate limiting to respect DMarket's API limits:

- **Default Limits**: 30 requests per minute
- **Automatic Backoff**: Exponential backoff on rate limit errors
- **Per-Endpoint Limits**: Different limits for different endpoints

## Caching

### Cache Types

- **Short TTL** (30s): Frequently changing data (market items, balance)
- **Medium TTL** (5m): Moderately stable data (aggregated prices)
- **Long TTL** (30m): Stable data (historical prices, metadata)

### Cache Management

```python
# Clear all cache
await api.clear_cache()

# Clear specific endpoint cache
await api.clear_cache_for_endpoint("/marketplace-api/v1/items")

# Disable caching for specific request
items = await api.get_market_items("csgo", force_refresh=True)
```

## Logging

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning messages for unusual situations
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause application failure

### Structured Logging

```python
from src.utils.logging_utils import BotLogger

logger = BotLogger(__name__)

# Log command execution
logger.log_command(
    user_id=123456789,
    command="/balance",
    success=True,
    execution_time=250
)

# Log API call
logger.log_api_call(
    endpoint="/account/v1/balance",
    method="GET",
    status_code=200,
    response_time=0.5
)
```

## Testing

### Test Fixtures

```python
# Use provided fixtures in tests
@pytest_asyncio.async_test
async def test_my_function(test_config, mock_dmarket_api, test_database):
    # Test implementation
    pass
```

### Mocking Examples

```python
from unittest.mock import patch, AsyncMock

# Mock API response
with patch.object(api, '_request') as mock_request:
    mock_request.return_value = {"balance": 100.0}
    balance = await api.get_balance()
    assert balance["balance"] == 100.0
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_dmarket_api.py -v

# Run tests in parallel
pytest -n auto
```

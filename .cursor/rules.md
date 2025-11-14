---
alwaysApply: true
---

# 🤖 Cursor AI Rules: DMarket Telegram Bot

## 🎯 Project Overview

**Goal**: Professional Telegram bot for DMarket platform - real-time market data, analytics, trading automation, alerts, and portfolio tracking.

**Tech Stack**:

- **Python**: 3.9+ with strict async/await
- **Telegram**: python-telegram-bot v20+
- **HTTP**: httpx (async only)
- **Database**: asyncpg (PostgreSQL) / aiosqlite (fallback)
- **Validation**: pydantic v2
- **Cache**: redis-py (optional)
- **Monitoring**: Sentry SDK

**Entry Point**: `src/main.py`

**Project Structure**:

```
src/
├── dmarket/          # DMarket API client & business logic
├── telegram_bot/     # Bot handlers, menus, keyboards
├── utils/            # Config, DB, logging, exceptions
└── main.py           # Application entry point
tests/                # Pytest tests (≥80% coverage)
docs/                 # Essential documentation only
config/               # YAML configs
data/                 # Runtime data, DB files
logs/                 # Application logs
scripts/              # Utility scripts
```

---

## 🚫 CRITICAL: What NOT to Do

### ❌ Never Create These Files

- **NO** summary/report files after tasks (e.g., `SUMMARY.md`, `REPORT.md`, `CHANGES.md`)
- **NO** markdown documentation files unless explicitly requested
- **NO** temporary test/debug scripts in project root
- **NO** backup files (`.bak`, `.old`, etc.)
- **NO** hardcoded credentials or secrets in any file

### ❌ Never Do This

- **NO** synchronous I/O operations (use `async def` + `await`)
- **NO** `requests` library (use `httpx` async)
- **NO** `time.sleep()` (use `asyncio.sleep()`)
- **NO** missing type hints on functions/methods
- **NO** bare `except:` clauses
- **NO** global mutable state (use dependency injection)
- **NO** commented-out code blocks (delete them)

---

## ✅ Coding Standards

### Async/Await - MANDATORY

```python
# ✅ CORRECT
async def get_market_data(game: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/market/{game}")
        return response.json()

# ❌ WRONG
def get_market_data(game: str) -> dict[str, Any]:
    import requests
    response = requests.get(f"/api/market/{game}")
    return response.json()
```

### Type Hints - MANDATORY

```python
# ✅ CORRECT
async def process_items(
    items: list[dict[str, Any]],
    min_price: float,
    callback: Callable[[dict], Awaitable[None]] | None = None,
) -> list[str]:
    results: list[str] = []
    for item in items:
        if item.get("price", 0) >= min_price:
            results.append(item["title"])
            if callback:
                await callback(item)
    return results

# ❌ WRONG - no type hints
async def process_items(items, min_price, callback=None):
    results = []
    # ...
```

### Error Handling - Use Custom Exceptions

```python
# ✅ CORRECT
from src.utils.exceptions import APIError, RateLimitExceeded

async def fetch_data() -> dict[str, Any]:
    try:
        return await api.get_data()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimitExceeded("Too many requests", retry_after=60)
        raise APIError(f"API error: {e}", status_code=e.response.status_code)

# ❌ WRONG - bare except
async def fetch_data():
    try:
        return await api.get_data()
    except:
        return {}
```

### Logging - Structured & Lazy

```python
# ✅ CORRECT
logger.info("Processing %d items for user %s", len(items), user_id)
logger.error("Failed to fetch data", extra={"user_id": user_id, "game": game})

# ❌ WRONG - f-strings in logs
logger.info(f"Processing {len(items)} items for user {user_id}")
```

---

## 📦 Pydantic Models - REQUIRED for API

```python
from pydantic import BaseModel, Field, validator

class MarketItemResponse(BaseModel):
    """DMarket API response model."""

    title: str
    price: int = Field(gt=0, description="Price in cents")
    game_id: str
    item_id: str
    available: bool = True

    @validator("price")
    def validate_price(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @property
    def price_usd(self) -> float:
        """Convert price from cents to USD."""
        return self.price / 100
```

---

## 🗃️ Database - Async Only

```python
# ✅ CORRECT - asyncpg
async def get_user_settings(user_id: int) -> dict[str, Any] | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_settings WHERE user_id = $1",
            user_id,
        )
        return dict(row) if row else None

# ✅ CORRECT - aiosqlite
async def get_user_settings(user_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect("data/bot.db") as db:
        async with db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
```

---

## 🔐 Security - CRITICAL

### Environment Variables

```python
# ✅ CORRECT
from src.utils.config import Config

config = Config.load()
api_key = config.dmarket.public_key  # From .env

# ❌ WRONG
api_key = "dmarket_pk_12345"  # Hardcoded!
```

### Input Validation

```python
# ✅ CORRECT
from telegram import Update
from telegram.ext import ContextTypes

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    try:
        price = float(user_input)
        if price < 0 or price > 100000:
            await update.message.reply_text("Price must be between 0 and 100000")
            return
    except ValueError:
        await update.message.reply_text("Invalid price format")
        return
```

---

## 🧪 Testing - pytest + pytest-asyncio

```python
import pytest
from src.dmarket.dmarket_api import DMarketAPI

@pytest.mark.asyncio
async def test_get_balance(mock_httpx_client):
    """Test balance retrieval."""
    api = DMarketAPI(public_key="test", secret_key="test")

    mock_httpx_client.get.return_value.json.return_value = {
        "balance": 10000,
        "currency": "USD",
    }

    balance = await api.get_balance()

    assert balance["balance"] == 10000
    assert balance["currency"] == "USD"
```

**Coverage Requirement**: ≥80% for all new code

```bash
pytest --cov=src --cov-report=html
```

---

## 📝 Documentation Rules

### Code Comments

```python
# ✅ CORRECT - docstrings only
async def calculate_profit(
    buy_price: float,
    sell_price: float,
    fee_rate: float = 0.07,
) -> float:
    """Calculate profit after DMarket fees.

    Args:
        buy_price: Purchase price in USD
        sell_price: Selling price in USD
        fee_rate: DMarket fee rate (default 7%)

    Returns:
        Net profit in USD
    """
    return (sell_price * (1 - fee_rate)) - buy_price

# ❌ WRONG - unnecessary comments
async def calculate_profit(buy_price, sell_price, fee_rate=0.07):
    # Calculate the selling price after fees
    after_fee = sell_price * (1 - fee_rate)
    # Subtract the buy price
    profit = after_fee - buy_price
    # Return the result
    return profit
```

### File-Level Documentation

- Only add docstrings at module level if the module purpose is not obvious
- **NEVER** create separate markdown files for code summaries
- Keep documentation in code via docstrings

---

## 🔧 Configuration Management

```python
# config.yaml
database:
  url: ${DATABASE_URL:sqlite:///data/dmarket_bot.db}
  pool_size: 10

dmarket:
  api_url: https://api.dmarket.com
  rate_limit:
    requests_per_minute: 60
    burst: 10

telegram:
  token: ${TELEGRAM_BOT_TOKEN}
  allowed_users: ${ALLOWED_USERS:[]}

logging:
  level: ${LOG_LEVEL:INFO}
  format: json
  file: logs/dmarket_bot.log
```

```python
# src/utils/config.py
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = 10

class DMarketConfig(BaseModel):
    api_url: str = "https://api.dmarket.com"
    public_key: str
    secret_key: str

class Config(BaseSettings):
    database: DatabaseConfig
    dmarket: DMarketConfig

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
```

---

## 🚀 Performance Optimization

### Rate Limiting

```python
from src.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter(
    requests_per_minute=60,
    burst=10,
)

async def api_call():
    await rate_limiter.wait_if_needed("market")
    return await client.get("/api/market")
```

### Caching (Redis Optional)

```python
from redis.asyncio import Redis
import json

cache = Redis.from_url("redis://localhost:6379")

async def get_market_items_cached(game: str) -> list[dict]:
    cache_key = f"market:{game}"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from API
    items = await api.get_market_items(game)

    # Cache for 5 minutes
    await cache.setex(cache_key, 300, json.dumps(items))

    return items
```

---

## 🎨 Code Style

### Formatting

- **Black**: Line length 100
- **Ruff**: All rules enabled
- **isort**: Profile black

```bash
# Run before commit
black src/ tests/ --line-length 100
ruff check src/ tests/ --fix
mypy src/
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## 📊 Monitoring & Logging

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration

sentry_sdk.init(
    dsn=config.sentry_dsn,
    environment=config.environment,
    integrations=[AsyncioIntegration()],
    traces_sample_rate=0.1,
)
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "arbitrage_opportunity_found",
    user_id=user_id,
    game=game,
    profit=profit_usd,
    item_name=item_name,
)
```

---

## 🔄 CI/CD - GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run linters
        run: |
          black --check src/ tests/
          ruff check src/ tests/
          mypy src/

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📚 Essential File References

### Exception Handling

- **Location**: `src/utils/exceptions.py`
- **Usage**: Import `APIError`, `RateLimitExceeded`, `ValidationError`, etc.

### Rate Limiting

- **Location**: `src/utils/rate_limiter.py`
- **Usage**: Global `RateLimiter` instance for DMarket API

### Database

- **Location**: `src/utils/database.py`
- **Usage**: `DatabaseManager` with async pool

### Config

- **Location**: `src/utils/config.py`
- **Usage**: `Config.load()` to get all settings

### Logging

- **Location**: `src/utils/logging_utils.py`
- **Usage**: `setup_logging()` and `get_logger()`

---

## 🤖 Cursor AI Behavior Guidelines

### When Writing Code

1. **Always** use `async def` for I/O operations
2. **Always** add type hints to functions
3. **Always** use custom exceptions from `src.utils.exceptions`
4. **Always** validate user input
5. **Always** use pydantic models for API data
6. **Never** create summary/report files after completing tasks
7. **Never** use synchronous HTTP libraries

### When Suggesting Changes

1. **Prefer** refactoring over adding new files
2. **Prefer** built-in types over custom classes
3. **Prefer** composition over inheritance
4. **Suggest** tests for new functionality
5. **Suggest** error handling for edge cases

### When Asked to Document

1. **Write** docstrings in code
2. **Update** existing docs/ files if needed
3. **Never** create new markdown files unless explicitly requested
4. **Never** create `SUMMARY.md`, `REPORT.md`, `CHANGES.md`, etc.

### Response Format

- Provide code examples directly
- Explain changes inline with comments
- Keep responses concise but complete
- No need for "work completed" reports

---

## 📖 External References

- **DMarket API**: <https://docs.dmarket.com/v1/swagger.json>
- **Telegram Bot API**: <https://core.telegram.org/bots/api>
- **Python-telegram-bot**: <https://docs.python-telegram-bot.org/>
- **Asyncpg**: <https://magicstack.github.io/asyncpg/>
- **Aiosqlite**: <https://aiosqlite.omnilib.dev/>
- **Pydantic**: <https://docs.pydantic.dev/latest/>
- **HTTPX**: <https://www.python-httpx.org/>
- **Pytest-asyncio**: <https://pytest-asyncio.readthedocs.io/>

---

## 🎯 Quick Checklist for Every Task

- [ ] All functions have type hints
- [ ] Using `async def` for I/O operations
- [ ] Exceptions from `src.utils.exceptions`
- [ ] Pydantic models for API data
- [ ] Input validation present
- [ ] Tests added/updated (if needed)
- [ ] No hardcoded secrets
- [ ] No summary files created
- [ ] Code formatted with black
- [ ] Passes ruff and mypy checks

---

**Last Updated**: 2024-11-14
**Reload Rules**: Cmd/Ctrl + Shift + P → "Cursor: Reload Rules"

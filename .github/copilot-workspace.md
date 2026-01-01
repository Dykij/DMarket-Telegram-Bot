# GitHub Copilot Workspace Context - DMarket Bot

## Project Type & Technologies

```yaml
project_type: telegram-bot
primary_language: python
python_version: "3.11+"
async_framework: asyncio
http_client: httpx
telegram_framework: python-telegram-bot 22.0+
database: PostgreSQL/SQLite + SQLAlchemy 2.0
cache: Redis + aiocache
testing: pytest 8.4+
linters: ["ruff 0.8+", "mypy 1.14+ strict"]
apis:
  - name: DMarket API
    version: v1.1.0
    auth: HMAC-SHA256
    rate_limit: 30 req/min
    price_unit: cents
  - name: Telegram Bot API
    version: "9.2"
```

## Code Patterns (Auto-apply)

### 1. API Call Pattern
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx
import structlog

logger = structlog.get_logger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def api_call_template(url: str, params: dict | None = None) -> dict:
    """Template for all API calls in this project."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "api_http_error",
                url=url,
                status_code=e.response.status_code,
                response=e.response.text
            )
            raise
        except httpx.RequestError as e:
            logger.error("api_request_error", url=url, error=str(e))
            raise
```

### 2. Command Handler Pattern (Telegram)
```python
from telegram import Update
from telegram.ext import ContextTypes
import structlog

logger = structlog.get_logger(__name__)

async def command_handler_template(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Template for Telegram command handlers."""
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    logger.info("command_received", command="template", user_id=user_id)

    try:
        # Command logic here
        result = await process_command(user_id)

        await update.message.reply_text(
            f"✅ Success: {result}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(
            "command_failed",
            command="template",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )
```

### 3. Test Pattern (pytest)
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_function_condition_expected_result():
    """Test description following AAA pattern."""
    # Arrange
    mock_api = AsyncMock()
    mock_api.method.return_value = {"key": "value"}

    # Act
    result = await function_under_test(mock_api)

    # Assert
    assert result["key"] == "value"
    mock_api.method.assert_called_once()
```

## DMarket API Price Conversion

**CRITICAL**: Always convert between cents and dollars correctly!

```python
# Price conversion utilities (use these ALWAYS)
def cents_to_dollars(cents: int) -> float:
    """Convert DMarket API price (cents) to dollars."""
    return cents / 100

def dollars_to_cents(dollars: float) -> int:
    """Convert dollars to DMarket API price (cents)."""
    return int(dollars * 100)

# Example usage
api_price = 1500  # cents from API
display_price = cents_to_dollars(api_price)  # $15.00

user_price = 25.50  # dollars from user input
api_price = dollars_to_cents(user_price)  # 2550 cents for API
```

## Common Mistakes to Avoid

### ❌ WRONG Examples

```python
# 1. WRONG - synchronous I/O
def fetch_data():
    response = requests.get(url)
    return response.json()

# 2. WRONG - no type hints
async def process(item):
    return item.price * 2

# 3. WRONG - bare except
try:
    result = await api.call()
except:  # NEVER!
    return None

# 4. WRONG - price confusion
price = 15  # Is this cents or dollars? UNCLEAR!

# 5. WRONG - no logging context
logger.info("Error occurred")

# 6. WRONG - test without AAA
async def test_something():
    result = await func()
    assert result
```

### ✅ CORRECT Examples

```python
# 1. CORRECT - async I/O
async def fetch_data() -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# 2. CORRECT - with type hints
async def process(item: Item) -> float:
    return item.price * 2

# 3. CORRECT - specific exception handling
try:
    result = await api.call()
except httpx.HTTPError as e:
    logger.error("api_error", error=str(e))
    raise

# 4. CORRECT - clear price units
price_cents = 1500  # DMarket API
price_dollars = 15.0  # User display

# 5. CORRECT - structured logging with context
logger.info(
    "processing_item",
    item_id=item.id,
    user_id=user.id,
    price=item.price
)

# 6. CORRECT - AAA pattern test
@pytest.mark.asyncio
async def test_process_item_with_valid_data_returns_success():
    # Arrange
    item = Item(id="123", price=1000)

    # Act
    result = await process(item)

    # Assert
    assert result == 2000
```

## Project File Structure Context

When suggesting imports or creating new files:

```
src/
├── dmarket/              # DMarket API integration
│   ├── dmarket_api.py   # Main API client
│   ├── arbitrage_scanner.py  # 5-level scanner
│   ├── targets.py       # Buy Orders management
│   └── game_filters.py  # CS:GO, Dota 2, TF2, Rust
├── telegram_bot/         # Telegram bot
│   ├── commands/        # Command handlers
│   ├── handlers/        # Message/callback handlers
│   └── keyboards.py     # Inline keyboards
├── utils/                # Utilities
│   ├── config.py        # Configuration (Pydantic)
│   ├── rate_limiter.py  # API rate limiting
│   └── logging_utils.py # Structured logging
└── models/               # SQLAlchemy models

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
├── e2e/                 # E2E tests (Phase 2)
└── conftest.py          # Pytest fixtures
```

## Import Suggestions

### For API calls:
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from src.utils.rate_limiter import rate_limiter
```

### For Telegram handlers:
```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import structlog
from src.utils.config import config
```

### For tests:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.dmarket.dmarket_api import DMarketAPI
```

### For data validation:
```python
from pydantic import BaseModel, Field, field_validator
from typing import TypeAlias
```

## Git Commit Message Templates

Use these for commit message generation:

```
feat(arbitrage): add support for CS2 items
fix(api): handle 429 rate limit correctly
docs(readme): update installation steps
refactor(scanner): simplify level filtering logic
test(targets): add edge case tests for buy orders
chore(deps): update httpx to 0.28.0
```

## Environment Variables Reference

When suggesting configuration:

```bash
# Required
TELEGRAM_BOT_TOKEN=
DMARKET_PUBLIC_KEY=
DMARKET_SECRET_KEY=

# Safety
DRY_RUN=true  # Always true by default!

# Optional
DATABASE_URL=sqlite:///data/dmarket_bot.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
SENTRY_DSN=
```

## Performance Optimization Patterns

### Parallel API Calls
```python
import asyncio

async def fetch_multiple_items(item_ids: list[str]) -> list[dict]:
    """Fetch multiple items in parallel."""
    tasks = [fetch_item(item_id) for item_id in item_ids]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Batch Processing
```python
async def process_items_batch(
    items: list[Item],
    batch_size: int = 100
) -> list[Result]:
    """Process items in batches for better performance."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await process_batch(batch)
        results.extend(batch_results)
    return results
```

### Caching Pattern
```python
from aiocache import cached

@cached(ttl=300)  # Cache for 5 minutes
async def get_market_items(game: str) -> list[dict]:
    """Fetch market items with caching."""
    return await api.get_items(game)
```

## Code Review Checklist

When reviewing code, check:

- [ ] All I/O operations use async/await
- [ ] All functions have type hints
- [ ] Error handling is specific (no bare except)
- [ ] Logging includes context (structlog)
- [ ] Secrets are not hardcoded
- [ ] Tests follow AAA pattern
- [ ] DMarket prices handled correctly (cents vs dollars)
- [ ] Rate limiting is respected (30 req/min)
- [ ] DRY_RUN mode checked before real trades

## Useful Commands for Chat

```bash
# Run tests
pytest tests/ -v

# Type check
mypy src/

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Coverage
pytest --cov=src --cov-report=html

# Run bot
python -m src.main

# Debug mode
DEBUG=true python -m src.main
```

---

**Context Version**: 1.0
**Last Updated**: January 2026
**For**: VS Code Insiders + GitHub Copilot

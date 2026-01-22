# DMarket Telegram Bot - Claude Code Instructions

## Project Overview

Telegram bot for trading and analytics on DMarket and Waxpeer marketplaces. Written in Python 3.11+ with async/await patterns.

## Tech Stack

- **Language**: Python 3.11+ (3.12+ recommended)
- **Framework**: python-telegram-bot 22.0+
- **HTTP Client**: httpx 0.28+ (async)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async)
- **Cache**: Redis + aiocache
- **Logging**: structlog (JSON structured)
- **Testing**: pytest 8.4+ with pytest-asyncio
- **Linting**: Ruff 0.8+, MyPy 1.14+ (strict)

## Project Structure

```
src/
├── dmarket/         # DMarket API client, arbitrage, targets
├── waxpeer/         # Waxpeer P2P API client
├── telegram_bot/    # Bot handlers, keyboards, localization
├── utils/           # Rate limiting, caching, logging
└── models/          # SQLAlchemy models

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── e2e/             # End-to-end tests
```

## Code Conventions

### Async/Await
- **ALWAYS** use `async def` for I/O operations
- Use `asyncio.gather()` for parallel execution
- Use `httpx.AsyncClient` for HTTP (not requests)

### Type Annotations
```python
# ✅ Correct (Python 3.11+ syntax)
def get_items(game: str) -> list[dict[str, Any]]: ...
def get_price(item_id: str) -> float | None: ...

# ❌ Wrong (legacy syntax)
def get_items(game: str) -> List[Dict[str, Any]]: ...
def get_price(item_id: str) -> Optional[float]: ...
```

### Error Handling
```python
# ✅ Correct - specific exceptions
try:
    response = await client.get(url)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.error("http_error", status=e.response.status_code)
    raise

# ❌ Wrong - bare except
try:
    response = await client.get(url)
except:
    pass
```

### Logging
```python
import structlog
logger = structlog.get_logger(__name__)

# Include context
logger.info("item_purchased", item_id=item_id, price=price, user_id=user_id)
```

## DMarket API Specifics

- **Prices in CENTS**: 1000 = $10.00 USD
- **Commission**: 7% on sales
- **Rate limit**: 30 requests/minute
- **Auth**: HMAC-SHA256 signatures

```python
# Price conversion
price_usd = api_response["price"]["USD"] / 100  # cents to dollars
```

## Waxpeer API Specifics

- **Prices in MILS**: 1000 mils = $1.00 USD
- **Commission**: 6% on sales
- **Auth**: API key in header

```python
# Price conversion
price_usd = api_response["price"] / 1000  # mils to dollars
```

## Commands

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/unit/test_arbitrage.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

## Rules for Claude

1. **Never modify** files in `.github/agents/` directory
2. **Always** add type annotations to new functions
3. **Always** use async/await for HTTP requests
4. **Never** log sensitive data (API keys, tokens)
5. **Always** follow AAA pattern in tests (Arrange, Act, Assert)
6. **Use** early returns to reduce nesting (max 3 levels)
7. **Keep** functions under 50 lines
8. **Add** docstrings to public functions (Google style)
9. **Use Context7 MCP** when generating code with library/API documentation

## Context7 MCP Integration

Claude Code should use Context7 MCP for up-to-date library documentation:

```
Always use Context7 MCP when I need library/API documentation, 
code generation, setup or configuration steps.
```

### Key Libraries with Context7 IDs

| Category | Library | Context7 ID |
|----------|---------|-------------|
| HTTP | httpx | `/encode/httpx` |
| Telegram | python-telegram-bot | `/python-telegram-bot/python-telegram-bot` |
| Database | SQLAlchemy | `/sqlalchemy/sqlalchemy` |
| Validation | Pydantic | `/pydantic/pydantic` |
| Testing | pytest | `/pytest-dev/pytest` |
| Logging | structlog | `/hynek/structlog` |
| Async | anyio | `/agronholm/anyio` |
| Redis | redis-py | `/redis/redis-py` |
| Security | cryptography | `/pyca/cryptography` |
| ML | scikit-learn | `/scikit-learn/scikit-learn` |
| Linting | ruff | `/astral-sh/ruff` |
| Types | mypy | `/python/mypy` |

### Usage Example

```
Создай async HTTP клиент с retry логикой. use library /encode/httpx for API and docs.
```

Full library list: `docs/AI_TOOLS_CONFIG.md`

## Known Issues

- Some legacy tests use cents format `{"usd": 10000}` - migrate to `{"balance": 100.0}`
- Rate limiting can cause 429 errors during peak hours
- WebSocket reconnection needs exponential backoff

## References

- Main docs: `docs/README.md`
- API spec: `docs/DMARKET_API_FULL_SPEC.md`
- Arbitrage guide: `docs/ARBITRAGE.md`
- Security: `SECURITY.md`

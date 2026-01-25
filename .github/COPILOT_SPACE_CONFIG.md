# 🚀 GitHub Copilot Space Configuration

## 📋 Quick Setup

1. Open: https://github.com/copilot/spaces/Dykij/1
2. Copy text between `=== START ===` and `=== END ===` markers below
3. Paste into Space Instructions field
4. Add recommended **Sources** (see below)

---

## 📝 Instructions for Space (Copy Below - ~3500 chars)

=== START COPY HERE ===

You are an expert Python developer for DMarket Telegram Bot - a trading/analytics bot for DMarket and Waxpeer game item marketplaces.

## Tech Stack
- Python 3.11+ (3.12+ recommended), async/await everywhere
- python-telegram-bot 22.0+, httpx 0.28+ (async HTTP)
- PostgreSQL + SQLAlchemy 2.0 (async), Redis + aiocache
- structlog (JSON logging), pytest 8.4+ with pytest-asyncio
- Ruff 0.8+ (linting), MyPy 1.14+ (strict types)

## Code Rules

### Async (MANDATORY)
- ALWAYS use async def for I/O operations
- Use asyncio.gather() for parallel execution
- Use httpx.AsyncClient (NOT requests library)

### Types (MANDATORY)
- Python 3.11+ syntax: list[str], dict[str, int], str | None
- NOT legacy syntax: List[str], Optional[str]

### Error Handling
- Never use bare except: - catch specific exceptions
- Log with structlog context: logger.error("msg", item_id=id, error=str(e))

### Testing (AAA Pattern)
- Arrange, Act, Assert
- Names: test_<function>_<condition>_<result>
- Use pytest-asyncio for async tests

## API Reference

### DMarket API
- Prices in CENTS: 1000 = $10.00 USD
- Commission: 7% on sales
- Rate limit: 30 req/min
- Auth: HMAC-SHA256
- Conversion: price_usd = response["price"]["USD"] / 100
- Profit formula: profit = suggested_price - buy_price - (suggested_price * 0.07)

### Waxpeer API
- Prices in MILS: 1000 mils = $1.00 USD
- Commission: 6% on sales
- Auth: X-API-KEY header
- Conversion: price_usd = response["price"] / 1000
- Cross-platform profit: net_profit = (waxpeer_price * 0.94) - dmarket_price

## Project Structure
src/
├── dmarket/         # API client, arbitrage, targets
├── waxpeer/         # Waxpeer P2P client
├── telegram_bot/    # Handlers, keyboards, i18n
├── utils/           # Rate limit, cache, logging
└── models/          # SQLAlchemy models
tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── e2e/             # E2E tests

## Commands
- pytest tests/ -v                           # Run tests
- pytest --cov=src --cov-report=term-missing # Coverage
- ruff check src/ tests/                     # Lint
- ruff format src/ tests/                    # Format
- mypy src/                                  # Type check
- python -m src.main                         # Run bot

## Safety Rules
- DRY_RUN=true by default (no real trades)
- Never log API keys/tokens
- Always HTTPS for external requests
- Validate all user input

## Code Style
- Max function length: 50 lines
- Max nesting: 3 levels (use early returns)
- Google-style docstrings for public functions
- Use dataclasses/Pydantic for data models

## Key Files Reference
- src/dmarket/dmarket_api.py - Main DMarket API client with HMAC auth
- src/dmarket/arbitrage_scanner.py - 5-level arbitrage scanner (boost/standard/medium/advanced/pro)
- src/dmarket/targets.py - Buy order management system
- src/waxpeer/waxpeer_api.py - Waxpeer P2P integration
- src/telegram_bot/handlers/ - All Telegram command handlers
- src/utils/rate_limiter.py - API rate limiting with aiolimiter

## Arbitrage Levels
- boost: $0.50-$3, min 15% profit
- standard: $3-$10, min 10% profit
- medium: $10-$30, min 7% profit
- advanced: $30-$100, min 5% profit
- pro: $100+, min 3% profit

## Common Patterns
- Use @cached decorator for caching (TTL 300s default)
- Use CircuitBreaker for API resilience
- Use tenacity for retry logic with exponential backoff
- Use structlog.get_logger(__name__) for logging

=== END COPY HERE ===

---

## 📁 Recommended Sources

### Core Files (MUST ADD)
Add these to your Space for essential context:

| File/Folder | Purpose |
|-------------|---------|
| `src/dmarket/dmarket_api.py` | DMarket API client |
| `src/dmarket/arbitrage_scanner.py` | Arbitrage logic |
| `src/dmarket/targets.py` | Target management |
| `src/waxpeer/waxpeer_api.py` | Waxpeer API client |
| `src/telegram_bot/` | Bot handlers folder |
| `src/utils/` | Utilities folder |

### Documentation (RECOMMENDED)
| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `docs/ARBITRAGE.md` | Arbitrage guide |
| `docs/DMARKET_API_FULL_SPEC.md` | DMarket API spec |
| `docs/WAXPEER_API_SPEC.md` | Waxpeer API spec |
| `CLAUDE.md` | Code conventions |
| `.github/copilot-instructions.md` | Full Copilot context |

### Configuration Files
| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, Ruff, MyPy settings |
| `.env.example` | Environment variables |
| `docker-compose.yml` | Services configuration |

### Tests (For Reference)
| File/Folder | Purpose |
|-------------|---------|
| `tests/conftest.py` | Test fixtures |
| `tests/unit/` | Unit test examples |

---

## 🎯 Use Cases for This Space

### 1. Code Generation
Ask Copilot to generate:
- New API endpoints
- Telegram bot handlers
- Arbitrage strategies
- Test cases

### 2. Code Review
Paste code for review of:
- Type annotations
- Error handling
- Async patterns
- Security issues

### 3. Documentation
Generate or improve:
- Docstrings
- README sections
- API documentation
- User guides

### 4. Debugging
Describe issues and get:
- Root cause analysis
- Fix suggestions
- Best practices

---

## 📌 Example Prompts

### Generate New Handler
```
Create a new Telegram bot handler for /portfolio command that shows user's current inventory with prices and profit calculations.
```

### Add Arbitrage Feature
```
Add a new arbitrage level called "ultra" for items over $500 with 2% minimum profit margin.
```

### Write Tests
```
Write pytest tests for the ArbitrageScanner.calculate_profit method covering edge cases.
```

### Review Code
```
Review this code for async patterns, error handling, and type annotations:
[paste code]
```

---

## 🔧 Advanced Configuration

### MCP Server Integration (VS Code/IDE)

To use this Space in your IDE, add to your MCP config:

```json
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "X-MCP-Toolsets": "default,copilot_spaces"
      }
    }
  }
}
```

### Space Sharing

- **Personal**: Only you can access
- **Organization**: Share with team members
- **Public (View-only)**: Anyone can view instructions

---

## 📚 Additional Resources

- [Copilot Spaces Documentation](https://docs.github.com/en/copilot/how-tos/provide-context/use-copilot-spaces)
- [DMarket Bot Documentation](docs/README.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Guidelines](SECURITY.md)

---

**Last Updated**: January 2026
**Repository**: https://github.com/Dykij/DMarket-Telegram-Bot

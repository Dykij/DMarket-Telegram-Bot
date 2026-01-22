# 🚀 GitHub Copilot Space Configuration

This document provides ready-to-use instructions and source recommendations for configuring your **GitHub Copilot Space** at https://github.com/copilot/spaces

## 📋 Quick Setup Guide

### Step 1: Open Your Space
Go to: https://github.com/copilot/spaces/Dykij/1

### Step 2: Add Instructions
Copy the **Instructions** section below into your Space's instructions field.

### Step 3: Add Sources
Add the recommended files and folders from the **Sources** section.

---

## 📝 Instructions (Copy to Space)

```
You are an expert Python developer working on the DMarket Telegram Bot project.

## Project Overview
A Telegram bot for trading and analytics on DMarket and Waxpeer game item marketplaces.

## Tech Stack
- Python 3.11+ (3.12+ recommended)
- python-telegram-bot 22.0+ (async)
- httpx 0.28+ for async HTTP
- PostgreSQL + SQLAlchemy 2.0 (async)
- Redis + aiocache for caching
- structlog for JSON logging
- pytest 8.4+ with pytest-asyncio
- Ruff 0.8+ for linting, MyPy 1.14+ strict mode

## Code Conventions

### 1. Async/Await (MANDATORY)
- ALWAYS use `async def` for I/O operations
- Use `asyncio.gather()` for parallel execution
- Use `httpx.AsyncClient` for HTTP requests (NOT requests)

### 2. Type Annotations (MANDATORY)
- Use Python 3.11+ syntax: `list[str]`, `dict[str, int]`, `str | None`
- NOT legacy: `List[str]`, `Optional[str]`

### 3. Error Handling
- Never use bare `except:`
- Catch specific exceptions
- Log errors with structlog context

### 4. Testing
- Follow AAA pattern: Arrange, Act, Assert
- Use descriptive names: `test_<function>_<condition>_<result>`
- Use pytest-asyncio for async tests

## API Specifics

### DMarket API
- Prices in CENTS: 1000 = $10.00 USD
- Commission: 7% on sales
- Rate limit: 30 requests/minute
- Auth: HMAC-SHA256 signatures

### Waxpeer API
- Prices in MILS: 1000 mils = $1.00 USD
- Commission: 6% on sales
- Auth: API key in X-API-KEY header

### Arbitrage Formula
```python
# DMarket internal
profit = suggested_price - buy_price - (suggested_price * 0.07)

# DMarket → Waxpeer cross-platform
net_profit = (waxpeer_price * 0.94) - dmarket_price
```

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

## Commands
```bash
# Tests
pytest tests/ -v
pytest --cov=src --cov-report=term-missing

# Lint & Format
ruff check src/ tests/
ruff format src/ tests/

# Type Check
mypy src/

# Run Bot
python -m src.main
```

## Safety
- DRY_RUN=true by default (no real trades)
- Never log API keys or tokens
- Always use HTTPS for external requests
```

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

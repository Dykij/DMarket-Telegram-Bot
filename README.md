# 🤖 DMarket Telegram Bot

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml)
[![Code Quality](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/quality.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/quality.yml)
[![Coverage](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/coverage.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/coverage.yml)
[![codecov](https://codecov.io/gh/Dykij/DMarket-Telegram-Bot/branch/main/graph/badge.svg)](https://codecov.io/gh/Dykij/DMarket-Telegram-Bot)
![License](https://img.shields.io/badge/license-MIT-blue)
![Code Style](https://img.shields.io/badge/code%20style-ruff-orange)
![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
[![Release](https://img.shields.io/github/v/release/Dykij/DMarket-Telegram-Bot)](https://github.com/Dykij/DMarket-Telegram-Bot/releases)

A comprehensive Telegram bot for DMarket platform operations, market analytics, and automated trading opportunities. Built with modern Python, async/await, and enterprise-grade architecture.

## 🌟 Features

### 📊 Market Analytics

- **Real-time Market Data**: Live prices, volume, and market trends
- **Price History Visualization**: Interactive charts and graphs
- **Market Statistics**: Comprehensive analytics and insights
- **Multi-game Support**: CS:GO, Dota 2, TF2, Rust, and more

### 💰 Trading & Arbitrage

- **Arbitrage Scanner**: Find profitable trading opportunities
- **Auto-trading**: Automated buy/sell operations
- **Price Alerts**: Custom notifications for price changes
- **Portfolio Tracking**: Monitor your investments

### 🔧 Advanced Features

- **Multi-language Support**: English, Russian, and more
- **Database Analytics**: Historical data storage and analysis
- **Rate Limiting**: Respectful API usage
- **Error Recovery**: Robust error handling and retry logic
- **Webhook Support**: Production-ready webhook integration

### 🛡️ Security & Performance

- **DRY_RUN Mode**: Safe testing without real trades (enabled by default)
- **Encrypted API Keys**: Secure credential management
- **Rate Limiting**: Built-in API throttling
- **Caching**: Intelligent response caching
- **Monitoring**: Comprehensive logging and metrics

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher (3.11+ recommended)
- Telegram Bot Token ([create one with @BotFather](https://t.me/BotFather))
- DMarket API Keys ([get them here](https://dmarket.com/profile/api))
- PostgreSQL (recommended) or SQLite for development

### 1-Minute Setup

```bash
# Clone the repository
git clone https://github.com/your-username/dmarket-telegram-bot.git
cd dmarket-telegram-bot

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Initialize database
python scripts/init_db.py

# Validate configuration
python scripts/validate_config.py

# Run health check
python scripts/health_check.py

# Run the bot
python -m src.main
```

## 📦 Installation

### Method 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/your-username/dmarket-telegram-bot.git
cd dmarket-telegram-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .

# Initialize database with Alembic
python scripts/init_db.py

# Or manually with Alembic
alembic upgrade head
```

### Method 2: Docker Installation

```bash
# Clone and build
git clone https://github.com/your-username/dmarket-telegram-bot.git
cd dmarket-telegram-bot

# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot
```

### Method 3: One-Click Deployment

#### Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### DigitalOcean

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/your-username/dmarket-telegram-bot/tree/main)

### Development Dependencies

For development and testing:

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run quality checks
make qa
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Required: Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=your_bot_username

# Required: DMarket API Configuration
DMARKET_PUBLIC_KEY=your_dmarket_public_key_here
DMARKET_SECRET_KEY=your_dmarket_secret_key_here
DMARKET_API_URL=https://api.dmarket.com

# Optional: Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/dmarket_bot
# For SQLite: sqlite:///data/dmarket_bot.db

# Optional: Security Configuration
ALLOWED_USERS=123456789,987654321  # Comma-separated user IDs
ADMIN_USERS=123456789              # Comma-separated admin IDs

# Optional: Advanced Configuration
LOG_LEVEL=INFO
WEBHOOK_URL=https://your-domain.com/webhook
SENTRY_DSN=your_sentry_dsn_for_error_tracking
```

### Configuration File

Alternatively, use a YAML configuration file:

```yaml
# config/local.yaml
bot:
  token: "your_telegram_bot_token"
  username: "your_bot_username"

dmarket:
  api_url: "https://api.dmarket.com"
  public_key: "your_public_key"
  secret_key: "your_secret_key"
  rate_limit: 30

database:
  url: "sqlite:///data/dmarket_bot.db"

security:
  allowed_users: ["123456789"]
  admin_users: ["123456789"]
```

Run with config file:

```bash
python -m src.main --config config/local.yaml
```

### Configuration Validation

Before running the bot, validate your configuration:

```bash
# Validate all settings
python scripts/validate_config.py

# This will check:
# - Required environment variables
# - API key formats
# - Database connectivity
# - File permissions
# - Network accessibility
```

### Health Checks

Run comprehensive health checks:

```bash
# Check all services
python scripts/health_check.py

# This will verify:
# - Telegram API connectivity
# - DMarket API availability
# - Database connection
# - Redis connection (if configured)
```

### API Keys Setup

#### 1. Telegram Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the provided token to your `.env` file

#### 2. DMarket API Keys

1. Visit [DMarket Profile](https://dmarket.com/profile/api)
2. Create new API credentials
3. Copy Public Key and Secret Key to your `.env` file
4. **Important**: Keep your secret key secure and never commit it to git

## 📱 Usage

### ⚠️ Important: Trading Safety Mode

By default, the bot operates in **DRY_RUN mode** for your safety:

- 🔵 **DRY_RUN=true (default)**: Bot simulates all trades without spending real money
- 🔴 **DRY_RUN=false**: Bot makes REAL trades with your balance

**Before switching to live trading:**

1. Test for at least 48-72 hours in DRY_RUN mode
2. Review all logs marked with `[DRY-RUN]` or `[LIVE]`
3. Read the [Security Guide](docs/SECURITY.md)
4. Start with small amounts

To change mode, edit `.env`:

```env
DRY_RUN=false  # ⚠️ Use with caution!
```

### Bot Commands

#### Basic Commands

- `/start` - Welcome message and main menu
- `/help` - Show all available commands
- `/balance` - Check your DMarket balance
- `/market <game>` - Browse market items (e.g., `/market csgo`)

#### Market Analysis

- `/stats <item_name>` - Get item statistics and price history
- `/trends <game>` - Show market trends for a game
- `/top <game>` - Top items by volume/price
- `/arbitrage` - Find arbitrage opportunities

#### Trading Operations

- `/buy <item_id> <price>` - Buy an item
- `/sell <item_id> <price>` - Sell an item
- `/inventory` - View your inventory
- `/orders` - View active orders

#### Alerts & Notifications

- `/alert <item> <price>` - Set price alert
- `/alerts` - Manage your alerts
- `/notify on/off` - Toggle notifications

#### Analytics & Visualization

- `/chart <item>` - Generate price chart
- `/portfolio` - Portfolio analysis
- `/report` - Generate market report

### Usage Examples

```
# Check CS:GO market
/market csgo

# Set price alert for AK-47 Redline
/alert "AK-47 | Redline (Field-Tested)" 12.50

# View price chart for AWP Asiimov
/chart "AWP | Asiimov (Field-Tested)"

# Find arbitrage opportunities
/arbitrage
```

### Web Interface

The bot also provides a web interface for advanced features:

```
# Access via webapp command
/webapp
```

Features include:

- Advanced market filtering
- Bulk operations
- Detailed analytics
- Trading history

## 🛠️ Development

### Project Structure

```
DMarket-Telegram-Bot/
├── 📁 src/                    # Исходный код
│   ├── 📁 dmarket/            # DMarket API клиент
│   │   ├── arbitrage.py
│   │   ├── arbitrage_scanner.py
│   │   ├── auto_arbitrage.py
│   │   ├── dmarket_api.py
│   │   ├── game_filters.py
│   │   ├── sales_history.py
│   │   ├── targets.py
│   │   └── filters/          # Фильтры игр (CS:GO, Dota 2, TF2, Rust)
│   ├── 📁 telegram_bot/       # Telegram бот
│   │   ├── commands/         # Команды бота
│   │   ├── handlers/         # Обработчики событий
│   │   ├── enhanced_bot.py   # Основной бот
│   │   ├── keyboards.py      # Клавиатуры
│   │   ├── localization.py   # Локализация (RU, EN)
│   │   └── notifier.py       # Уведомления
│   ├── 📁 models/             # Модели SQLAlchemy 2.0
│   │   ├── user.py
│   │   ├── target.py
│   │   └── trading.py
│   ├── 📁 utils/              # Утилиты
│   │   ├── analytics.py      # Аналитика
│   │   ├── config.py         # Конфигурация (Pydantic)
│   │   ├── database.py       # Менеджер БД
│   │   ├── logging_utils.py  # Структурированное логирование
│   │   ├── rate_limiter.py   # Rate limiting
│   │   └── websocket_client.py  # WebSocket клиент
│   └── 📄 main.py             # Точка входа
├── 📁 tests/                  # Тесты (pytest)
│   ├── 📄 test_main.py
│   ├── 📄 test_config.py
│   ├── 📄 test_dmarket_api.py
│   └── 📄 conftest.py         # Фикстуры
├── 📁 alembic/                # Миграции БД
│   ├── versions/             # Файлы миграций
│   ├── env.py
│   └── BEST_PRACTICES.md
├── 📁 scripts/                # Утилиты
│   ├── init_db.py            # Инициализация БД
│   ├── validate_config.py    # Валидация конфигурации
│   └── health_check.py       # Проверка здоровья
├── 📁 docs/                   # Документация
│   ├── ARBITRAGE.md          # Руководство по арбитражу
│   ├── ARCHITECTURE.md       # Архитектура
│   ├── QUICK_START.md        # Быстрый старт
│   └── api_reference.md      # API справочник
├── 📁 config/                 # Конфигурация
├── 📁 data/                   # Данные
└── 📁 logs/                   # Логи
```

### Development Workflow

```bash
# Setup development environment
make setup

# Initialize database
python scripts/init_db.py

# Validate configuration
python scripts/validate_config.py

# Run health checks
python scripts/health_check.py

# 🧪 Run Debug Suite (REQUIRED before deployment)
python scripts/debug_suite.py

# Run quality checks
make qa

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Run the bot in development mode
make run
```

### Database Management

#### Initialize Database

```bash
# Using init script (recommended)
python scripts/init_db.py

# Or manually with Alembic
alembic upgrade head
```

#### Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

#### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Pre-flight Checks

Before running the bot in production:

```bash
# 1. Validate configuration
python scripts/validate_config.py

# 2. Check service connectivity
python scripts/health_check.py

# 3. 🧪 Run Debug Suite (MANDATORY BEFORE DEPLOYMENT)
python scripts/debug_suite.py
# This script performs 6 critical tests:
# - DMarket API connection + balance check
# - Database connection and schema validation
# - User management operations
# - Real market data and profit calculations
# - Order simulation in DRY-RUN mode
# - Telegram notification delivery

# 4. Run database migrations
python scripts/init_db.py

# 5. Run tests
pytest --cov=src

# 6. Check code quality
ruff check src/ tests/
mypy src/
```

**⚠️ IMPORTANT**: Always run `python scripts/debug_suite.py` before every deployment to prevent costly errors!

### Adding New Features

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Implement Feature**
   - Add code to appropriate module
   - Include comprehensive tests
   - Update documentation

3. **Test Thoroughly**

   ```bash
   make test-cov
   make lint
   ```

4. **Submit Pull Request**
   - Use the provided PR template
   - Include description and tests
   - Ensure CI passes

### Code Style

We use modern Python best practices:

- **Type Hints**: All functions have type annotations
- **Async/Await**: Asynchronous programming throughout
- **Error Handling**: Comprehensive error handling and logging
- **Testing**: 80%+ test coverage required
- **Documentation**: Docstrings for all public functions

### 🔄 CI/CD Pipeline

The project uses GitHub Actions for automated testing and deployment:

#### Workflows

1. **CI Pipeline** - Runs on every push/PR
   - ✅ Ruff linting and formatting
   - ✅ MyPy type checking
   - ✅ Tests on Python 3.10, 3.11, 3.12
   - ✅ Security scan (Bandit, Safety)

2. **Code Quality** - Detailed quality checks
   - ✅ Complexity analysis
   - ✅ Automated PR comments

3. **Coverage** - Test coverage reports
   - ✅ Codecov integration
   - ✅ Coverage diff on PRs
   - ✅ Minimum 80% coverage enforced

4. **Release** - Automated releases
   - ✅ Docker image build (multi-platform)
   - ✅ GitHub Container Registry
   - ✅ Automatic changelog generation

#### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

📖 **Full CI/CD Documentation**: [docs/CI_CD_GUIDE.md](docs/CI_CD_GUIDE.md)
🚀 **Quick Start**: [docs/CI_CD_QUICKSTART.md](docs/CI_CD_QUICKSTART.md)

### 🧪 Debug Suite - Pre-Deployment Testing

**CRITICAL**: Run Debug Suite before every deployment to production!

The Debug Suite (`scripts/debug_suite.py`) performs comprehensive system checks:

#### What it Tests

1. **🌐 DMarket API Connection**
   - Validates API credentials
   - Checks balance availability
   - Warns if balance < $1.00

2. **🗄️ Database Connection**
   - Tests PostgreSQL/SQLite connectivity
   - Validates database schema
   - Ensures migrations are applied

3. **👤 User Management**
   - Creates/retrieves test user
   - Validates database operations
   - Tests user data persistence

4. **📊 Market Data & Profit Calculation**
   - Fetches real market items
   - Tests price parsing
   - Validates profit calculation logic

5. **🛒 Order Simulation (DRY-RUN)**
   - Simulates buy order creation
   - Logs BUY_INTENT for auditing
   - Tests without spending real money

6. **📱 Telegram Notifications**
   - Validates bot token
   - Tests message delivery
   - Checks bot permissions

#### Running Debug Suite

```bash
# Basic usage
python scripts/debug_suite.py

# Expected output:
# ======================================================================
# 🧪 DMARKET BOT DEBUG SUITE
# ======================================================================
# ⏰ Время запуска: 2025-11-23 15:30:45
# 🔧 Режим: DRY-RUN ✅
# ======================================================================
#
# [1/6] 🌐 Подключение к DMarket API...
#    ✅ Подключение успешно
#    💰 Баланс: $100.50
#    💵 Доступно для вывода: $95.25
#
# [2/6] 🗄️  Подключение к базе данных...
#    ✅ Подключение к БД успешно
#
# ... (остальные тесты)
#
# ======================================================================
# 📊 ИТОГОВЫЙ ОТЧЁТ
# ======================================================================
# ✅ Успешных тестов: 6/6
# ❌ Провалившихся тестов: 0/6
#
# 🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!
# ✅ Бот готов к запуску.
# ======================================================================
```

#### When to Run

- ✅ **Before every production deployment**
- ✅ After changing API credentials
- ✅ After database schema changes
- ✅ After major code refactoring
- ✅ Weekly for health monitoring

#### Exit Codes

- `0` - All tests passed ✅
- `1` - At least one test failed ❌

Use in CI/CD:

```bash
python scripts/debug_suite.py || exit 1
```

### Architecture Overview

```mermaid
graph TB
    A[Telegram User] --> B[Telegram Bot API]
    B --> C[Bot Handlers]
    C --> D[DMarket API Client]
    C --> E[Database Manager]
    C --> F[Analytics Engine]
    D --> G[DMarket API]
    E --> H[PostgreSQL/SQLite]
    F --> I[Chart Generator]
```

## 📚 API Documentation

**Comprehensive guides available in `/docs`:**

### 🚀 Getting Started
- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running in 5 minutes
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and components
- **[Deployment Guide](docs/deployment.md)** - Production deployment

### 📖 API & Technical Reference
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[DMarket API Specification](docs/DMARKET_API_FULL_SPEC.md)** - Full DMarket API docs
- **[API Coverage Matrix](docs/API_COVERAGE_MATRIX.md)** - 80% coverage, 46 endpoints mapped
- **[Data Structures Guide](docs/DATA_STRUCTURES_GUIDE.md)** - Algorithm complexity & performance

### 🎯 Trading & Performance
- **[Multi-Level Arbitrage](docs/MULTI_LEVEL_ARBITRAGE_GUIDE.md)** - Trading strategies
- **[Optimization Roadmap](docs/OPTIMIZATION_ROADMAP.md)** - 10-100x speedup opportunities

### 🧪 Development
- **[Testing Guide](docs/testing_guide.md)** - How to run and write tests
- **[Security Best Practices](docs/SECURITY.md)** - Secure your bot
- **[VS Code Setup](docs/vscode_setup.md)** - IDE configuration
- **[GitHub Copilot Guide](docs/github_copilot_guide.md)** - AI-assisted development with Copilot CLI

### DMarket API Client

```python
from src.dmarket import DMarketAPI

# Initialize client
api = DMarketAPI(
    public_key="your_public_key",
    secret_key="your_secret_key"
)

# Get market items
items = await api.get_market_items(
    game="csgo",
    limit=50,
    price_from=5.0,
    price_to=100.0
)

# Get user balance
balance = await api.get_balance()
print(f"Balance: ${balance['balance']:.2f}")
```

### Telegram Bot Integration

```python
from src.telegram_bot import DMarketBot
from src.utils.config import Config

# Load configuration
config = Config.load()

# Initialize bot
bot = DMarketBot(config=config)
await bot.initialize()
await bot.start()
```

### Database Operations

```python
from src.utils.database import DatabaseManager

# Initialize database
db = DatabaseManager("postgresql://...")
await db.init_database()

# Create user
user = await db.get_or_create_user(
    telegram_id=123456789,
    username="testuser"
)

# Log command
await db.log_command(
    user_id=user.id,
    command="/balance",
    success=True
)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_dmarket_api.py

# Run in parallel
pytest -n auto
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **API Tests**: DMarket API integration testing
- **Bot Tests**: Telegram bot handler testing

### Mocking & Fixtures

```python
# Example test with fixtures
@pytest_asyncio.async_test
async def test_get_balance(mock_dmarket_api):
    balance = await mock_dmarket_api.get_balance()
    assert balance["error"] is False
    assert balance["balance"] > 0
```

## 🚀 Deployment

### Production Deployment

#### Docker Deployment

```bash
# Build production image
docker build -t dmarket-bot .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

#### Server Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment variables
export TELEGRAM_BOT_TOKEN="..."
export DMARKET_PUBLIC_KEY="..."
export DATABASE_URL="postgresql://..."

# Run with process manager
pm2 start src/main.py --name dmarket-bot
```

### Environment Setup

#### Production Environment Variables

```bash
# Production configuration
export NODE_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost:5432/dmarket_prod
export REDIS_URL=redis://localhost:6379
export SENTRY_DSN=your_sentry_dsn
export WEBHOOK_URL=https://your-domain.com/webhook
```

### Monitoring & Logging

- **Application Metrics**: Built-in Prometheus metrics
- **Error Tracking**: Sentry integration
- **Log Management**: Structured JSON logging
- **Health Checks**: `/health` endpoint for monitoring

### Security Considerations

- **API Keys**: Store in environment variables or secret management
- **Database**: Use connection pooling and SSL
- **Rate Limiting**: Implemented for all external APIs
- **Input Validation**: All user inputs are validated
- **Error Handling**: No sensitive data in error messages

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Contribution Guide

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/AmazingFeature`
3. **Commit changes**: `git commit -m 'Add AmazingFeature'`
4. **Push to branch**: `git push origin feature/AmazingFeature`
5. **Open Pull Request**

### Development Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Write comprehensive tests (80%+ coverage)
- Include type hints for all functions
- Update documentation for new features
- Use conventional commits for commit messages

### Community

- 🐛 [Report Bugs](https://github.com/your-username/dmarket-telegram-bot/issues/new?template=bug_report.md)
- 💡 [Request Features](https://github.com/your-username/dmarket-telegram-bot/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/your-username/dmarket-telegram-bot/discussions)
- 📧 [Contact Maintainers](mailto:maintainers@example.com)

## � Production Readiness Checklist

**⚠️ КРИТИЧЕСКИ ВАЖНО**: Перед запуском на реальных деньгах выполните **ВСЕ** пункты этого чеклиста!

### 📋 Обязательные шаги перед запуском

#### 1. Тестирование (48-72 часа минимум)

- [ ] **DRY_RUN режим включен** (`DRY_RUN=true` в `.env`)
- [ ] **Бот протестирован минимум 48-72 часа** без критических ошибок
- [ ] **debug_suite.py выполнен успешно** (см. [DEBUG_WORKFLOW.md](docs/DEBUG_WORKFLOW.md))
- [ ] **Все integration тесты проходят** (`pytest tests/integration/`)
- [ ] **Логи проверены на отсутствие ошибок** (см. `logs/dmarket_bot.log`)
- [ ] **Метрики Sentry в норме** (если настроено)

```bash
# Запуск финальной проверки
python scripts/debug_suite.py --production-check
```

#### 2. Конфигурация безопасных лимитов

- [ ] **Торговые лимиты установлены**:
  - `MAX_TRADE_VALUE` <= $50 (первую неделю)
  - `DAILY_TRADE_LIMIT` <= $500
  - `MIN_PROFIT_PERCENT` >= 3.0%
- [ ] **Защита от убытков настроена**:
  - `STOP_LOSS_PERCENT` = 10.0%
  - `MAX_CONSECUTIVE_LOSSES` = 5
- [ ] **Контроль баланса установлен**:
  - `MIN_BALANCE_THRESHOLD` >= $10
  - `BALANCE_CHECK_INTERVAL` = 300 (5 мин)
- [ ] **MAX_CONCURRENT_TRADES** = 3 (не более)

#### 3. Система мониторинга

- [ ] **Sentry настроен** для отслеживания ошибок
- [ ] **Telegram алерты работают**:
  - Тест: `/test_alerts` отправляет уведомление
  - Критические события настроены (баланс, убытки)
- [ ] **Email уведомления** (опционально, но рекомендуется)
- [ ] **Логирование работает корректно**:
  - `logs/dmarket_bot.log` создается
  - Ротация логов настроена
  - `LOG_LEVEL=INFO` (не DEBUG в production!)

```bash
# Проверка системы алертов
python scripts/test_alerts.py
```

#### 4. Резервное копирование

- [ ] **Автоматический бэкап БД настроен** (ежедневно в 3:00 AM)
- [ ] **Бэкап конфигурации .env** (в безопасном месте!)
- [ ] **План восстановления готов** (см. [DEBUG_WORKFLOW.md](docs/DEBUG_WORKFLOW.md))
- [ ] **Тестовое восстановление проведено** (убедитесь, что бэкапы рабочие!)

```bash
# Настройка cron для автобэкапа
0 3 * * * /path/to/scripts/backup_database.sh
```

#### 5. Финальная проверка

- [ ] **Начальный баланс записан** (`python scripts/record_initial_balance.py`)
- [ ] **Доступ к серверу есть** для экстренной остановки
- [ ] **Контакты экстренной поддержки добавлены** в `.env`
- [ ] **Документация прочитана**:
  - [SECURITY.md](docs/SECURITY.md) - Безопасность
  - [DEBUG_WORKFLOW.md](docs/DEBUG_WORKFLOW.md) - Отладка и запуск
  - [QUICK_START.md](docs/QUICK_START.md) - Быстрый старт

### ⚠️ Переключение на реальную торговлю

**ТОЛЬКО** после выполнения всех пунктов выше:

```bash
# 1. Отредактировать .env
nano .env

# 2. Изменить (ВНИМАТЕЛЬНО!):
# DRY_RUN=false  # ⚠️ РЕАЛЬНАЯ ТОРГОВЛЯ!

# 3. Перезапустить бота
systemctl restart dmarket-bot
# или
docker-compose restart bot

# 4. НЕМЕДЛЕННО проверить логи
tail -f logs/dmarket_bot.log

# 5. Проверить первые 5 минут:
# - Логи показывают [LIVE] вместо [DRY-RUN]
# - Нет критических ошибок
# - Баланс отображается корректно
```

### 📅 Что проверять ежедневно

#### Утренний чек (5 минут)

- [ ] **Баланс DMarket** соответствует ожидаемому
- [ ] **Нет критических ошибок** в Sentry/логах
- [ ] **Бот активен** и отвечает на `/status`
- [ ] **Последние сделки** были прибыльными
- [ ] **API DMarket доступен** (проверить через `/health`)

```bash
# Быстрая проверка здоровья
curl http://localhost:8000/health
```

#### Вечерний чек (10 минут)

- [ ] **Ежедневный отчет** (`python scripts/generate_daily_report.py`)
- [ ] **Общая прибыль/убыток** за день
- [ ] **Все сделки** прошли в рамках лимитов
- [ ] **Нет зацикливаний** (покупка одного предмета)
- [ ] **Анализ убыточных сделок** (если есть)

```bash
# Генерация отчета
python scripts/generate_daily_report.py --date $(date +%Y-%m-%d)
```

#### Еженедельный чек (30 минут)

- [ ] **Полный аудит** всех сделок за неделю
- [ ] **Здоровье базы данных** (`python scripts/check_database_health.py`)
- [ ] **Обновление зависимостей** (если есть патчи безопасности)
- [ ] **Ротация логов** (`find logs/ -name "*.log" -mtime +30 -delete`)
- [ ] **Бэкап всех данных** вручную (помимо автоматического)
- [ ] **Анализ эффективности** стратегий

### 🚨 Красные флаги - остановить торговлю НЕМЕДЛЕННО!

Остановите бота **СРАЗУ** если:

1. 🔴 **Баланс резко упал** (>10% за час)
2. 🔴 **5+ убыточных сделок подряд**
3. 🔴 **DMarket API ошибки** 429/500/503
4. 🔴 **Необычно высокие цены** (в 2-3 раза выше рынка)
5. 🔴 **Бот покупает одно и то же** (зацикливание)
6. 🔴 **Нет прибыльных сделок 24+ часа**
7. 🔴 **Sentry показывает критические ошибки**
8. 🔴 **Дневной лимит исчерпан раньше времени**

**Экстренная остановка:**

```bash
# Метод 1: Telegram
/stop_trading
/cancel_all_targets

# Метод 2: Сервер
systemctl stop dmarket-bot
# или
docker-compose down

# Метод 3: Переключить обратно
nano .env  # DRY_RUN=true
systemctl restart dmarket-bot
```

### 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи**: `logs/dmarket_bot.log`
2. **Проверьте Sentry**: Трейсы ошибок
3. **Создайте Issue**: [GitHub Issues](https://github.com/Dykij/DMarket-Telegram-Bot/issues)
4. **Экстренная помощь**: См. `.env` → `EMERGENCY_CONTACT_*`

**Подробнее:**
- 🐛 [DEBUG_WORKFLOW.md](docs/DEBUG_WORKFLOW.md) - Полное руководство по отладке
- 🔒 [SECURITY.md](docs/SECURITY.md) - Безопасная торговля
- 🚀 [QUICK_START.md](docs/QUICK_START.md) - Быстрый старт

---

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DMarket](https://dmarket.com/) for providing the marketplace API
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the excellent Telegram bot framework
- [httpx](https://github.com/encode/httpx) for modern async HTTP client
- All contributors who have helped improve this project

## 📊 Статистика проекта

- **Языки**: Python 3.10+ (3.11+ рекомендуется)
- **Версия проекта**: 1.0.0
- **Фреймворк**: python-telegram-bot 20.7+
- **База данных**: PostgreSQL (production), SQLite (dev)
- **Async**: Full async/await с asyncio
- **Тестирование**: pytest 7.4+, 85%+ покрытие (цель)
- **Качество кода**: Ruff 0.8+, Black 24+, MyPy 1.11+ (strict mode)
- **ORM**: SQLAlchemy 2.0+
- **HTTP**: httpx 0.27+ (async)
- **CI/CD**: GitHub Actions (4 workflow)
- **Лицензия**: MIT

---

<div align="center">
  <strong>⭐ Star this repo if you find it useful!</strong>
  <br>
  <em>Made with ❤️ for the DMarket trading community</em>
</div>

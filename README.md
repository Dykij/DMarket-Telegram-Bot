# 🤖 DMarket Telegram Bot

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
[![CI/CD Pipeline](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml)
[![Code Quality](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/code-quality.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/code-quality.yml)
[![Python Tests](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/python-tests.yml)
[![Security Scan](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/security-scan.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/security-scan.yml)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
![Docker](https://img.shields.io/badge/docker-ready-blue)

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
- Python 3.9 or higher
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
dmarket-telegram-bot/
├── 📁 src/                    # Source code
│   ├── 📁 dmarket/            # DMarket API client
│   ├── 📁 telegram_bot/       # Telegram bot handlers
│   ├── 📁 models/             # Database models (SQLAlchemy)
│   ├── 📁 utils/              # Utility functions
│   └── 📄 main.py             # Application entry point
├── 📁 tests/                  # Test suite
│   ├── 📄 test_main.py        # Application tests
│   ├── 📄 test_config.py      # Configuration tests
│   └── 📄 conftest.py         # Test fixtures
├── 📁 alembic/                # Database migrations
│   ├── 📁 versions/           # Migration files
│   ├── 📄 env.py              # Migration environment
│   └── 📄 alembic.ini         # Alembic configuration
├── 📁 scripts/                # Utility scripts
│   ├── 📄 init_db.py          # Database initialization
│   ├── 📄 validate_config.py  # Configuration validator
│   └── 📄 health_check.py     # Service health checker
├── 📁 docs/                   # Documentation
├── 📁 config/                 # Configuration files
├── 📁 data/                   # Data storage
└── 📁 logs/                   # Log files
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

# 3. Run database migrations
python scripts/init_db.py

# 4. Run tests
pytest --cov=src

# 5. Check code quality
ruff check src/ tests/
mypy src/
```

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DMarket](https://dmarket.com/) for providing the marketplace API
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the excellent Telegram bot framework
- [httpx](https://github.com/encode/httpx) for modern async HTTP client
- All contributors who have helped improve this project

## 📊 Project Stats

- **Languages**: Python 3.9+
- **Framework**: python-telegram-bot 20+
- **Database**: PostgreSQL, SQLite
- **Testing**: pytest, 80%+ coverage
- **Code Quality**: Black, Ruff, MyPy
- **CI/CD**: GitHub Actions
- **License**: MIT

---

<div align="center">
  <strong>⭐ Star this repo if you find it useful!</strong>
  <br>
  <em>Made with ❤️ for the DMarket trading community</em>
</div>

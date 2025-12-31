# Configuration Files Reference

> **Last Updated**: December 31, 2025  
> **Status**: All configs verified and up-to-date ✅

This document provides a comprehensive overview of all configuration files in the project.

---

## 📋 Table of Contents

- [Python Project](#python-project)
- [Development Tools](#development-tools)
- [Application Config](#application-config)
- [Docker & Deployment](#docker--deployment)
- [IDE & Editor](#ide--editor)
- [Data Files](#data-files)

---

## 🐍 Python Project

### pyproject.toml
**Purpose**: Main Python project configuration (PEP 621)  
**Location**: Root directory  
**Contains**:
- Project metadata (name, version, dependencies)
- Tool configurations:
  - `[tool.ruff]` - Linter and formatter (v0.8.6+)
  - `[tool.mypy]` - Type checker (v1.15.0+)
  - `[tool.pytest]` - Testing framework
  - `[tool.coverage]` - Code coverage
  - `[tool.bandit]` - Security scanner

**Key Features**:
- Modern Python 3.11+ support
- Strict type checking configuration
- 85%+ coverage target
- Security checks with Bandit

**Example**:
```toml
[project]
name = "dmarket-bot"
version = "1.0.0"
requires-python = ">=3.11"
```

### requirements.in
**Purpose**: Source file for pip-compile  
**Location**: Root directory  
**Usage**: 
```bash
pip-compile requirements.in
pip install -r requirements.txt
```

**Structure**:
- Core dependencies (telegram-bot, httpx, aiohttp)
- Database & caching (SQLAlchemy, Redis)
- Data analysis (pandas, numpy, matplotlib)
- Security (cryptography, PyNaCl)
- Development tools (ruff, mypy, pytest)

---

## 🛠️ Development Tools

### .pre-commit-config.yaml
**Purpose**: Git pre-commit hooks configuration  
**Location**: Root directory  
**Hooks**:
- **Ruff** (v0.8.6) - Linting and formatting
- **MyPy** (v1.15.0) - Type checking
- **Bandit** (v1.7.10) - Security scanning
- **PyUpgrade** (v3.20.0) - Syntax modernization
- **Basic checks** - Trailing whitespace, YAML validation, etc.

**Installation**:
```bash
pip install pre-commit
pre-commit install
```

**Manual Run**:
```bash
pre-commit run --all-files
```

### .gitignore
**Purpose**: Specify files to ignore in git  
**Location**: Root directory  
**Excludes**:
- Python artifacts (`__pycache__`, `*.pyc`)
- Virtual environments (`.venv/`, `venv/`)
- IDE files (`.vscode/`, `.idea/`)
- Test reports (`coverage.xml`, `bandit-report.json`)
- Data files (`data/*.json`)
- Logs (`*.log`)
- Secrets (`.env`, `*.key`)

**Recent Updates**:
- Added `bandit-report.json` (Dec 31, 2025)

### .yamllint.yml
**Purpose**: YAML file linting rules  
**Location**: Root directory  
**Usage**:
```bash
yamllint .
```

### cSpell.json
**Purpose**: Spell checker configuration  
**Location**: Root directory  
**Custom Dictionary**:
- Technical terms (asyncio, pytest, mypy)
- DMarket-specific terms
- Russian transliterations

---

## ⚙️ Application Config

### config/config.yaml
**Purpose**: Main application configuration  
**Location**: `config/` directory  
**Contains**:
- API endpoints
- Rate limiting settings
- Cache configuration
- Logging levels

**Example**:
```yaml
api:
  base_url: "https://api.dmarket.com"
  rate_limit: 30  # requests per minute
  
cache:
  ttl: 300  # seconds
  backend: "redis"
```

### config/feature_flags.yaml
**Purpose**: Feature flag configuration  
**Location**: `config/` directory  
**Usage**: Enable/disable features without code changes

**Example**:
```yaml
features:
  advanced_filters:
    enabled: true
    rollout: 100  # percentage
  
  auto_trading:
    enabled: false
```

### config/auto_sell.yaml
**Purpose**: Auto-sell feature configuration  
**Location**: `config/` directory  
**Contains**:
- Sell strategies
- Price thresholds
- Item filters

### config/item_filters.yaml
**Purpose**: Item filtering rules  
**Location**: `config/` directory  
**Filters**:
- Game-specific filters (CS:GO, Dota 2, etc.)
- Price ranges
- Quality levels
- Popularity thresholds

---

## 🐳 Docker & Deployment

### docker-compose.yml
**Purpose**: Docker services orchestration  
**Location**: Root directory  
**Services**:
- `bot` - Telegram bot application
- `postgres` - PostgreSQL database
- `redis` - Redis cache
- `prometheus` - Monitoring (optional)

**Usage**:
```bash
docker-compose up -d
docker-compose logs -f bot
docker-compose down
```

### Dockerfile
**Purpose**: Docker image build instructions  
**Location**: Root directory  
**Features**:
- Multi-stage build (smaller image)
- Python 3.12+ base
- Non-root user
- Health checks

### ecosystem.config.js
**Purpose**: PM2 process manager configuration  
**Location**: Root directory  
**Features**:
- Auto-restart on crash
- Memory limit monitoring
- Log rotation
- Graceful shutdown

**Usage**:
```bash
pm2 start ecosystem.config.js --env production
pm2 logs dmarket-bot
pm2 reload ecosystem.config.js
```

### Makefile
**Purpose**: Build automation and common tasks  
**Location**: Root directory  
**Commands**:
```bash
make help          # Show all commands
make setup         # Full setup
make install       # Install dependencies
make test          # Run tests
make lint          # Run linters
make format        # Format code
make docker-build  # Build Docker image
```

---

## 💻 IDE & Editor

### .vscode/settings.json
**Purpose**: VS Code workspace settings  
**Location**: `.vscode/` directory  
**Features**:
- Python interpreter path
- Ruff configuration
- MyPy integration
- Test discovery

### .vscode/extensions.json
**Purpose**: Recommended VS Code extensions  
**Location**: `.vscode/` directory  
**Extensions**:
- `ms-python.python` - Python support
- `charliermarsh.ruff` - Ruff linter
- `ms-python.mypy-type-checker` - MyPy
- `GitHub.copilot` - AI assistant

### .config/pyrightconfig.json
**Purpose**: Pyright type checker configuration  
**Location**: `.config/` directory  
**Settings**:
- Python version
- Type checking mode
- Include/exclude paths

---

## 📊 Data Files

### data/user_profiles.json
**Purpose**: User profile storage (runtime data)  
**Location**: `data/` directory  
**Format**:
```json
{
  "123456789": {
    "created_at": 1735689600,
    "access_level": "basic",
    "settings": {
      "language": "ru",
      "notifications": true
    }
  }
}
```

**Note**: This file is gitignored and created at runtime.

### data/user_alerts.json
**Purpose**: User alert configurations  
**Location**: `data/` directory  
**Auto-generated**: Yes

---

## 🔍 Database

### alembic.ini
**Purpose**: Alembic database migrations configuration  
**Location**: Root directory  
**Usage**:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

---

## 📝 File Hierarchy

```
DMarket-Telegram-Bot/
├── 📄 pyproject.toml              # Main Python config
├── 📄 requirements.in             # Dependencies source
├── 📄 requirements.txt            # Compiled dependencies
├── 📄 .pre-commit-config.yaml    # Git hooks
├── 📄 .gitignore                  # Git exclusions
├── 📄 .yamllint.yml               # YAML linting
├── 📄 alembic.ini                 # DB migrations
├── 📄 docker-compose.yml          # Docker orchestration
├── 📄 Dockerfile                  # Docker build
├── 📄 ecosystem.config.js         # PM2 config
├── 📄 Makefile                    # Build automation
├── 📄 cSpell.json                 # Spell checker
│
├── 📁 .vscode/
│   ├── settings.json              # VS Code settings
│   └── extensions.json            # Recommended extensions
│
├── 📁 .config/
│   └── pyrightconfig.json         # Pyright config
│
├── 📁 config/
│   ├── config.yaml                # Main app config
│   ├── feature_flags.yaml         # Feature flags
│   ├── auto_sell.yaml             # Auto-sell config
│   └── item_filters.yaml          # Item filters
│
├── 📁 data/                       # Runtime data (gitignored)
│   ├── user_profiles.json         # User profiles
│   └── user_alerts.json           # User alerts
│
└── 📁 .github/workflows/          # CI/CD configs
    ├── ci.yml
    ├── python-tests.yml
    └── security-scan.yml
```

---

## 🔄 Update History

| Date | Config | Change |
|------|--------|--------|
| 2025-12-31 | .gitignore | Added `bandit-report.json` |
| 2025-12-31 | pyproject.toml | Updated Bandit skips |
| 2025-12-31 | Multiple | Removed duplicate user_profiles.json |
| 2025-12-13 | .pre-commit-config.yaml | Updated to Ruff 0.8.6 |
| 2025-12-13 | pyproject.toml | Updated MyPy to 1.15.0 |

---

## ✅ Verification Checklist

Use this checklist to verify all configs are correct:

- [ ] `pyproject.toml` - All tools configured
- [ ] `.pre-commit-config.yaml` - Latest hook versions
- [ ] `.gitignore` - Excludes generated files
- [ ] `config/*.yaml` - App configs valid
- [ ] `docker-compose.yml` - Services configured
- [ ] `Makefile` - Commands work
- [ ] No duplicate config files
- [ ] No `setup.py` or `setup.cfg` (use pyproject.toml)

---

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

2. **Setup pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Configure application**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run tests**:
   ```bash
   make test
   ```

5. **Start application**:
   ```bash
   make run
   # or
   docker-compose up
   ```

---

## 📞 Support

For configuration issues:
1. Check this document
2. Review `pyproject.toml` comments
3. See GitHub workflows in `.github/workflows/`
4. Open an issue on GitHub

**Documentation**: See `docs/` directory for more guides.

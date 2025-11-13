# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- 📁 Created `.config/README.md` explaining new configuration structure
- 📦 Consolidated all package metadata in `pyproject.toml` (PEP 621)
- 🔧 Unified all tool configurations in single `pyproject.toml` file
- 📝 Updated documentation to reflect new structure

### Changed

- ⚡ **BREAKING**: Moved `pyproject.toml` from `.config/` to project root
- 🔄 Replaced Black with Ruff format for code formatting
- 🧹 Removed duplicate configuration files:
  - `.config/pytest.ini` (consolidated into `pyproject.toml`)
  - `.config/setup.py` (migrated to `pyproject.toml`)
  - `.config/setup.cfg` (obsolete)
  - `.config/linters/.ruff.toml` (merged into `pyproject.toml`)
  - `.config/linters/.black.toml` (replaced by Ruff format)
  - `.config/linters/.pylintrc` (replaced by Ruff)
  - `.config/type-checkers/mypy.ini` (merged into `pyproject.toml`)
- 🗑️ Removed unused GitHub Actions workflows:
  - `ci-go.yml`, `ci-js.yml`, `ci-php.yml` (wrong language)
  - `ci-python-project.yml` (duplicate)
  - `example-workflow.yml` (template)
- 🔧 Updated `.github/workflows/code-quality.yml` to use Ruff format instead of Black
- 📚 Updated `docs/code_quality_tools_guide.md` with new configuration paths

### Removed

- ❌ Black as standalone formatter (now using `ruff format`)
- ❌ Duplicate configuration files across `.config/` directory
- ❌ Obsolete GitHub Actions workflows for non-Python languages

### Fixed

- 🐛 Configuration conflicts from duplicate files
- 🔧 Improved clarity by having single source of truth for configurations

### Migration Notes

- All configurations now in `pyproject.toml` at project root
- Use `ruff format` instead of `black`
- All tools read from `pyproject.toml` automatically
- No action required for existing installations

---

## [0.1.0] - 2025-11-13

### Added

- 🔐 Comprehensive security guide (SECURITY.md)
- 🏗️ Architecture documentation (ARCHITECTURE.md)
- 🎯 Multi-level arbitrage system with 5 trading levels
- 🤖 Target management system (Buy Orders)
- 📊 Real-time price monitoring with WebSocket
- 🧪 Enhanced test coverage (85%+)
- 🔧 Advanced performance optimization tools
- 📝 Structured logging with JSON output
- 🌐 Multi-language support (RU, EN, ES, DE)
- 🐳 Docker and docker-compose configuration
- 📈 Market analysis and sales history tracking

### Changed

- ⚡ Upgraded to async/await throughout the codebase
- 🔄 Improved DMarket API client with retry logic
- 📱 Enhanced Telegram bot with inline keyboards
- 🛠️ Migrated to Ruff + Black + MyPy for code quality
- 🗄️ Updated database models with SQLAlchemy 2.0
- ♻️ Refactored project structure for better modularity

### Deprecated

- 📝 Old implementation plan documents
- 🗑️ Legacy CI/CD setup guides
- 📄 Duplicate quality improvement docs

### Security

- 🔒 API key encryption in database
- ✅ Input validation for all user inputs
- 🚫 Rate limiting to prevent API abuse
- 🛡️ Secure error handling without data leakage
- 🔑 Environment-based secret management

## [1.0.0] - 2024-10-12

### Added

- Initial release of DMarket Telegram Bot
- Basic DMarket API integration
- Telegram bot with essential commands
- Market analytics and arbitrage detection
- Docker containerization
- Basic configuration management
- Essential documentation

### Features

- `/balance` - Check DMarket account balance
- `/market` - Browse market items
- `/arbitrage` - Find trading opportunities
- `/stats` - Get market statistics
- Basic error handling and logging
- Multi-game support (CS:GO, Dota 2, etc.)

---

## Release Planning

### v1.1.0 (Planned)

- [ ] Advanced portfolio tracking
- [ ] Real-time price alerts via WebSocket
- [ ] Mobile-responsive web interface
- [ ] Advanced charting with technical indicators
- [ ] Multi-language support expansion
- [ ] Performance optimizations

### v1.2.0 (Planned)

- [ ] Machine learning price predictions
- [ ] Advanced arbitrage strategies
- [ ] Social features (sharing trades, leaderboards)
- [ ] Integration with other marketplaces
- [ ] Advanced risk management tools
- [ ] API webhooks for external integrations

### v2.0.0 (Future)

- [ ] Complete UI/UX redesign
- [ ] Advanced trading algorithms
- [ ] Institutional features
- [ ] Comprehensive mobile app
- [ ] Advanced analytics dashboard
- [ ] Enterprise deployment options

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- Portfolio management system with P&L tracking and risk analysis
- Backtesting framework for trading strategies
- High-frequency trading mode with balance-stop mechanism
- Discord webhook integration for notifications
- Auto-seller with dynamic pricing and stop-loss

### Changed
- Refactored large modules into smaller, maintainable packages
- Improved type hints and MyPy coverage
- Enhanced error handling and retry logic

### Fixed
- All test failures resolved (2348/2348 tests passing)
- Rate limiting and circuit breaker improvements
- API client stability enhancements

## [1.0.0] - 2025-12-14

### Added
- Initial release of DMarket Telegram Bot
- Multi-level arbitrage scanning (5 levels)
- Target management system (Buy Orders)
- Real-time price monitoring via WebSocket
- Multi-game support (CS:GO, Dota 2, TF2, Rust)
- Market analytics and liquidity analysis
- Internationalization (RU, EN, ES, DE)
- API key encryption and security
- Rate limiting and circuit breaker
- Sentry integration for monitoring
- Comprehensive test suite (2348 tests)

### Security
- API key encryption for user credentials
- Rate limiting to prevent abuse
- Circuit breaker for API protection
- DRY_RUN mode for safe testing

[Unreleased]: https://github.com/Dykij/DMarket-Telegram-Bot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Dykij/DMarket-Telegram-Bot/releases/tag/v1.0.0

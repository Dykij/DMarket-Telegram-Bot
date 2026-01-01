# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added - Phase 2: Infrastructure Improvements (January 2026)
- **E2E Tests**: New end-to-end test suite for critical workflows
  - `tests/e2e/test_arbitrage_flow.py` - Complete arbitrage workflow testing (395 lines)
  - `tests/e2e/test_target_management_flow.py` - Target management E2E tests (450+ lines)
  - Tests cover: scanning, trade execution, notifications, multi-level/multi-game flows
- **Updated Copilot Instructions**: Version 5.0 with Phase 2 guidelines
  - Added Code Readability Guidelines section
  - Early returns pattern examples
  - E2E testing best practices
  - Performance optimization guidance (profiling, batching, caching)
  - Function complexity limits (max 50 lines, max 3 nesting levels)
- **Documentation improvements**: Updated dates to January 1, 2026
  - Improved README.md with project status
  - All docs/ files updated with Phase 2 information

### Changed
- **Test Coverage Goal**: Increased from 85% to 90% (Phase 2 target)
- **Code Style**: Enforcing early returns pattern to reduce nesting
- **Performance Focus**: Profiling required before optimization

### Improved
- **Code Readability**:
  - Function length limit enforced (50 lines max)
  - Nesting depth limit (3 levels max)
  - Descriptive variable names required
  - Docstrings for complex functions (>3 params)
- **Testing Strategy**:
  - E2E tests for critical user flows
  - Pytest markers properly configured (e2e, unit, integration)
  - Parallel test execution support

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
- Comprehensive test suite (372 test files)
- Portfolio management system with P&L tracking
- Backtesting framework for trading strategies
- High-frequency trading mode with balance-stop mechanism
- Discord webhook integration for notifications
- Auto-seller with dynamic pricing and stop-loss

### Security
- API key encryption for user credentials
- Rate limiting to prevent abuse
- Circuit breaker for API protection
- DRY_RUN mode for safe testing

[Unreleased]: https://github.com/Dykij/DMarket-Telegram-Bot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Dykij/DMarket-Telegram-Bot/releases/tag/v1.0.0

# 📦 Migration Guide: Refactored Modules

**Date**: January 2026
**Status**: Phase 2 Complete - Ready for Migration

---

## Overview

This guide describes how to migrate from original modules to their refactored versions created during Phase 2.

## Benefits of Refactored Modules

✅ **Code Readability**: Functions < 50 lines, nesting < 3 levels
✅ **Early Returns**: Clearer control flow
✅ **Better Performance**: Batch processing, optimized caching
✅ **Maintainability**: Smaller, focused functions
✅ **Type Safety**: Complete type annotations

---

## Module Mapping

### DMarket API Modules

| Original                           | Refactored                                    | Status  |
| ---------------------------------- | --------------------------------------------- | ------- |
| `src/dmarket/dmarket_api.py`       | `src/dmarket/dmarket_api_refactored.py`       | ✅ Ready |
| `src/dmarket/api/client.py`        | `src/dmarket/api/client_refactored.py`        | ✅ Ready |
| `src/dmarket/arbitrage_scanner.py` | `src/dmarket/arbitrage_scanner_refactored.py` | ✅ Ready |
| `src/dmarket/market_analysis.py`   | `src/dmarket/market_analysis_refactored.py`   | ✅ Ready |
| `src/dmarket/auto_trader.py`       | `src/dmarket/auto_trader_refactored.py`       | ✅ Ready |

### Telegram Bot Handlers

| Original                                                    | Refactored                                                             | Status  |
| ----------------------------------------------------------- | ---------------------------------------------------------------------- | ------- |
| `src/telegram_bot/handlers/scanner_handler.py`              | `src/telegram_bot/handlers/scanner_handler_refactored.py`              | ✅ Ready |
| `src/telegram_bot/handlers/target_handler.py`               | `src/telegram_bot/handlers/target_handler_refactored.py`               | ✅ Ready |
| `src/telegram_bot/handlers/market_analysis_handler.py`      | `src/telegram_bot/handlers/market_analysis_handler_refactored.py`      | ✅ Ready |
| `src/telegram_bot/handlers/callbacks.py`                    | `src/telegram_bot/handlers/callbacks_refactored.py`                    | ✅ Ready |
| `src/telegram_bot/handlers/game_filter_handlers.py`         | `src/telegram_bot/handlers/game_filter_handlers_refactored.py`         | ✅ Ready |
| `src/telegram_bot/handlers/notification_filters_handler.py` | `src/telegram_bot/handlers/notification_filters_handler_refactored.py` | ✅ Ready |
| `src/telegram_bot/handlers/settings_handlers.py`            | `src/telegram_bot/handlers/settings_handlers_refactored.py`            | ✅ Ready |

### New Helper Modules (Phase 2)

| Module                                                    | Purpose                     | Status |
| --------------------------------------------------------- | --------------------------- | ------ |
| `src/dmarket/rare_pricing_analyzer.py`                    | Rare item pricing analysis  | ✅ New  |
| `src/dmarket/market_depth_analyzer.py`                    | Market depth analysis       | ✅ New  |
| `src/dmarket/direct_balance_requester.py`                 | Direct balance requests     | ✅ New  |
| `src/dmarket/trending_items_finder.py`                    | Find trending items         | ✅ New  |
| `src/dmarket/game_scanner.py`                             | Game-specific scanning      | ✅ New  |
| `src/dmarket/balance_checker.py`                          | Balance checking utilities  | ✅ New  |
| `src/dmarket/universal_balance_getter.py`                 | Universal balance getter    | ✅ New  |
| `src/dmarket/price_anomaly_detector.py`                   | Price anomaly detection     | ✅ New  |
| `src/dmarket/batch_scanner_optimizer.py`                  | Batch scanning optimization | ✅ New  |
| `src/utils/price_sanity_checker.py`                       | Price validation            | ✅ New  |
| `src/telegram_bot/commands/balance_command_refactored.py` | Balance command             | ✅ New  |

---

## Migration Strategy

### Phase 1: Preparation (30 minutes)

```bash
# 1. Create backup branch
git checkout -b backup-before-migration
git push origin backup-before-migration

# 2. Create migration branch
git checkout main
git checkout -b migration-refactored-modules

# 3. Run all tests to establish baseline
poetry run pytest tests/ -v --tb=short
```

### Phase 2: Module-by-Module Migration (2-3 hours)

#### Step 1: DMarket API Client (30 min)

```bash
# Backup original
mv src/dmarket/dmarket_api.py src/dmarket/dmarket_api_original.py

# Rename refactored
mv src/dmarket/dmarket_api_refactored.py src/dmarket/dmarket_api.py

# Run tests
poetry run pytest tests/unit/test_dmarket_api.py -v

# If tests pass, remove backup
rm src/dmarket/dmarket_api_original.py
```

#### Step 2: Arbitrage Scanner (30 min)

```bash
mv src/dmarket/arbitrage_scanner.py src/dmarket/arbitrage_scanner_original.py
mv src/dmarket/arbitrage_scanner_refactored.py src/dmarket/arbitrage_scanner.py

poetry run pytest tests/unit/test_arbitrage_scanner.py -v

# Verify with E2E test
poetry run pytest tests/e2e/test_arbitrage_flow.py -v
```

#### Step 3: Market Analysis (20 min)

```bash
mv src/dmarket/market_analysis.py src/dmarket/market_analysis_original.py
mv src/dmarket/market_analysis_refactored.py src/dmarket/market_analysis.py

poetry run pytest tests/unit/test_market_analysis.py -v
```

#### Step 4: Telegram Handlers (60 min)

```bash
# Scanner handler
mv src/telegram_bot/handlers/scanner_handler.py src/telegram_bot/handlers/scanner_handler_original.py
mv src/telegram_bot/handlers/scanner_handler_refactored.py src/telegram_bot/handlers/scanner_handler.py
poetry run pytest tests/unit/test_scanner_handler.py -v

# Target handler
mv src/telegram_bot/handlers/target_handler.py src/telegram_bot/handlers/target_handler_original.py
mv src/telegram_bot/handlers/target_handler_refactored.py src/telegram_bot/handlers/target_handler.py
poetry run pytest tests/unit/test_target_handler.py -v

# Callbacks
mv src/telegram_bot/handlers/callbacks.py src/telegram_bot/handlers/callbacks_original.py
mv src/telegram_bot/handlers/callbacks_refactored.py src/telegram_bot/handlers/callbacks.py
poetry run pytest tests/unit/test_callbacks.py -v

# Other handlers...
```

### Phase 3: Integration Testing (30 min)

```bash
# Run all tests
poetry run pytest tests/ -v --tb=short

# Run E2E tests
poetry run pytest tests/e2e/ -v

# Check coverage
poetry run pytest --cov=src --cov-report=term-missing
```

### Phase 4: Update Imports (20 min)

```bash
# Find all import statements that need updating
grep -r "from src.dmarket.dmarket_api_original" src/ tests/
grep -r "from src.dmarket.arbitrage_scanner_original" src/ tests/

# Update them to new locations
# (Most should automatically work if filenames match)
```

### Phase 5: Cleanup (10 min)

```bash
# Remove all *_original.py files
find src/ -name "*_original.py" -delete

# Remove all *_refactored.py files (now migrated)
find src/ -name "*_refactored.py" -delete

# Final test run
poetry run pytest tests/ -v
```

### Phase 6: Commit and Push

```bash
git add .
git commit -m "refactor: migrate to Phase 2 refactored modules

- Replaced original modules with refactored versions
- All tests passing (2348+ tests)
- Improved code readability (functions < 50 lines, nesting < 3)
- Added new helper modules for better separation of concerns

BREAKING CHANGE: Internal module structure changed, but API remains compatible
"

git push origin migration-refactored-modules

# Create PR for review
```

---

## Rollback Plan

If migration fails:

```bash
# 1. Return to backup branch
git checkout backup-before-migration

# 2. Verify everything works
poetry run pytest tests/ -v

# 3. If needed, force push to main (use with caution)
git push origin backup-before-migration:main --force
```

---

## Compatibility Notes

### API Compatibility
✅ All refactored modules maintain **100% API compatibility** with original versions
✅ Function signatures unchanged
✅ Return types unchanged
✅ Only internal implementation improved

### Breaking Changes
❌ **None** - this is a pure refactoring with no breaking changes

---

## Testing Checklist

- [ ] All unit tests pass (`poetry run pytest tests/unit/ -v`)
- [ ] All integration tests pass (`poetry run pytest tests/integration/ -v`)
- [ ] All E2E tests pass (`poetry run pytest tests/e2e/ -v`)
- [ ] Coverage remains >= 85% (`poetry run pytest --cov=src`)
- [ ] Ruff checks pass (`poetry run ruff check src/`)
- [ ] MyPy checks pass (`poetry run mypy src/`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)

---

## Estimated Timeline

| Phase               | Duration           | Complexity |
| ------------------- | ------------------ | ---------- |
| Preparation         | 30 min             | Low        |
| API Migration       | 30 min             | Medium     |
| Scanner Migration   | 30 min             | Medium     |
| Handlers Migration  | 60 min             | Medium     |
| Integration Testing | 30 min             | Medium     |
| Import Updates      | 20 min             | Low        |
| Cleanup             | 10 min             | Low        |
| **Total**           | **3 hours 30 min** | **Medium** |

---

## Questions?

If you encounter issues during migration:
1. Check test output for specific errors
2. Review `PHASE_2_REFACTORING_GUIDE.md` for patterns
3. Compare original and refactored side-by-side
4. Rollback if needed and investigate

---

**Happy Migrating! 🚀**

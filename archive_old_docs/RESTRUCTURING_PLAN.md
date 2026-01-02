# Repository Restructuring Plan

## Current Issues
1. Duplicate/overlapping functionality in different modules
2. Inconsistent directory structure
3. Mixed concerns in some directories

## Proposed Changes

### 1. Consolidate DMarket modules
- Move `src/dmarket/api/` content into main `src/dmarket/` if not used
- Organize scanner-related files into `src/dmarket/scanner/`
- Group arbitrage-related files into `src/dmarket/arbitrage/`
- Consolidate target management in `src/dmarket/targets/`

### 2. Organize Telegram bot structure
- Move all commands to `src/telegram_bot/commands/`
- Consolidate handlers in `src/telegram_bot/handlers/`
- Group notifications in `src/telegram_bot/notifications/`
- Organize keyboards in `src/telegram_bot/keyboards/`

### 3. Test structure improvements
- Mirror src/ structure in tests/
- Consolidate unit tests by module
- Keep integration, e2e, contracts, performance tests separate

### 4. Remove redundant files
- Identify and remove unused utility files
- Consolidate duplicate functionality

## Implementation Steps

### Step 1: DMarket Module Restructure
```
src/dmarket/
├── arbitrage/
│   ├── __init__.py
│   ├── scanner.py (from arbitrage_scanner.py)
│   ├── sales_analysis.py
│   ├── intramarket.py
│   └── hft_mode.py
├── scanner/
│   ├── __init__.py
│   ├── game_scanner.py
│   ├── batch_optimizer.py
│   └── smart_finder.py
├── targets/
│   ├── __init__.py
│   ├── manager.py (from targets.py)
│   └── auto_trader.py
├── analysis/
│   ├── __init__.py
│   ├── liquidity_analyzer.py
│   ├── market_analysis.py
│   ├── price_anomaly_detector.py
│   └── market_depth_analyzer.py
├── filters/
│   ├── __init__.py
│   ├── game_filters.py
│   ├── item_filters.py
│   └── advanced_filters.py
├── api/
│   ├── __init__.py
│   ├── client.py (from dmarket_api.py)
│   ├── validator.py
│   └── balance.py
└── models/
    ├── __init__.py
    └── schemas.py
```

### Step 2: Telegram Bot Restructure
```
src/telegram_bot/
├── commands/
│   ├── __init__.py
│   ├── arbitrage.py
│   ├── targets.py
│   ├── balance.py
│   ├── scanner.py
│   └── backtesting.py
├── handlers/
│   ├── __init__.py
│   ├── callbacks.py
│   ├── scanner.py
│   └── errors.py
├── notifications/
│   ├── __init__.py
│   ├── digest.py
│   ├── queue.py
│   ├── smart.py
│   └── handlers.py
├── keyboards/
│   ├── __init__.py
│   ├── main.py
│   └── inline.py
├── middleware/
│   ├── __init__.py
│   └── auth.py
└── core/
    ├── __init__.py
    ├── initialization.py
    ├── webhook.py
    └── health_check.py
```

### Step 3: Tests Restructure
- Mirror the new src/ structure
- Consolidate scattered test files
- Remove duplicate test fixtures

## Benefits
1. **Better organization**: Clear separation of concerns
2. **Easier navigation**: Logical grouping of related files
3. **Improved maintainability**: Easier to find and update code
4. **Better imports**: Clearer import paths
5. **Scalability**: Easier to add new features

## Backward Compatibility
- Update all imports across the codebase
- Update test imports
- Update documentation references
- Run full test suite to verify

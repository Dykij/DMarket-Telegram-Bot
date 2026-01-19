# Phase 2 Refactoring Plan

> **Status**: In Progress  
> **Started**: January 19, 2026  
> **Target Completion**: February 2026  
> **Last Updated**: January 19, 2026

---

## 🎯 Overview

This document outlines the refactoring plan for Phase 2 improvements following the guidelines
from `docs/refactoring_examples/README.md` and `.github/copilot-instructions.md`.

### Goals

1. **Reduce function length**: Max 50 lines per function
2. **Apply early returns**: Max 3 levels of nesting
3. **Improve testability**: Each function with single responsibility
4. **Maintain coverage**: Keep test coverage at 85%+

---

## 📊 Current Analysis

### Functions Exceeding Thresholds

| Threshold | Before | After | Change |
|-----------|--------|-------|--------|
| > 100 lines | 147 | 143 | -4 |
| > 50 lines | 639 | ~630 | -9 |

### Top 15 Priority Functions

| # | Function | File | Lines | Priority | Status |
|---|----------|------|-------|----------|--------|
| 1 | `button_callback_handler()` | `callbacks.py` | ~40 | 🔴 Critical | ✅ Refactored (was 950) |
| 2 | `initialize()` | `main.py` | 594 | 🔴 Critical | ⏳ Pending |
| 3 | `register_all_handlers()` | `register_all_handlers.py` | 455 | 🔴 Critical | ⏳ Pending |
| 4 | `check_balance_command()` | `balance_command.py` | 168 | 🔴 Critical | ✅ Refactored (was 331) |
| 5 | `_request()` | `dmarket_api.py` | 261 | 🟠 High | ✅ Refactored (was 330) |
| 6 | `ai_train_liquid_command()` | `ai_handler.py` | 137 | 🟠 High | ✅ Refactored (was 299) |
| 7 | `create_callback_router()` | `callback_registry.py` | ~25 | 🟠 High | ✅ Refactored (was 264) |
| 8 | `_request()` | `api/client.py` | 221 | 🟠 High | ✅ Refactored (was 262) |
| 9 | `_update_from_env()` | `config.py` | 108 | 🟠 High | ✅ Refactored (was 252) |
| 10 | `scan_game()` | `arbitrage_scanner.py` | <50 | 🟠 High | ✅ Refactored (was 216) |
| 11 | `market_analysis_callback()` | `market_analysis_handler.py` | 109 | 🟠 High | ✅ Refactored (was 252) |
| 12 | `handle_mode_selection_callback()` | `automatic_arbitrage_handler.py` | 240 | 🟠 High | ⏳ Pending |
| 13 | `train_from_real_data()` | `enhanced_predictor.py` | 225 | 🟠 High | ⏳ Pending |
| 14 | `hold_callback_handler()` | `intelligent_hold_handler.py` | 223 | 🟡 Medium | ⏳ Pending |
| 15 | `telegram_error_boundary()` | `telegram_error_handlers.py` | 222 | 🟡 Medium | ⏳ Pending |

---

## ✅ Completed Refactoring

### 1. `_request()` in `dmarket_api.py`

**Before**: 330 lines  
**After**: 261 lines  
**Reduction**: 21%

**Extracted Helper Methods**:
- `_prepare_sorted_params()` - Prepare and sort query parameters
- `_build_path_for_signature()` - Build path with query string for signing
- `_execute_single_http_request()` - Execute HTTP request with circuit breaker
- `_parse_json_response()` - Parse JSON from response
- `_calculate_retry_delay()` - Calculate retry delay based on error type
- `_parse_http_error_response()` - Parse error response body

### 2. `_request()` in `api/client.py`

**Before**: 262 lines  
**After**: 221 lines  
**Reduction**: 16%

**Extracted Helper Methods**:
- `_execute_single_http_request()` - Execute HTTP request
- `_parse_json_response()` - Parse JSON response
- `_calculate_retry_delay()` - Calculate retry delay
- `_parse_http_error_response()` - Parse HTTP error response

### 3. `scan_game()` in `arbitrage_scanner.py`

**Before**: 216 lines  
**After**: <50 lines  
**Reduction**: >75%

**Extracted Helper Methods**:
- `_get_profit_ranges()` - Get profit percentage range for scanning mode
- `_get_price_ranges()` - Get price range for scanning mode
- `_search_with_builtin_functions()` - Search using built-in arbitrage functions
- `_search_with_trader()` - Search using ArbitrageTrader
- `_apply_liquidity_filter()` - Apply liquidity filter to items
- `_enhance_with_steam()` - Enhance items with Steam price data

### 4. `_update_from_env()` in `config.py`

**Before**: 252 lines  
**After**: 108 lines  
**Reduction**: 57%

**Extracted Helper Methods**:
- `_get_env_int()` - Get integer from environment variable
- `_get_env_float()` - Get float from environment variable
- `_get_env_bool()` - Get boolean from environment variable
- `_get_env_list()` - Get list from comma-separated environment variable
- `_update_bot_from_env()` - Update bot configuration
- `_update_dmarket_from_env()` - Update DMarket configuration
- `_update_trading_from_env()` - Update trading configuration
- `_update_waxpeer_from_env()` - Update Waxpeer configuration

### 5. `check_balance_command()` in `balance_command.py`

**Before**: 331 lines  
**After**: 168 lines  
**Reduction**: 49%

**Extracted Helper Methods**:
- `_extract_user_info()` - Extract user and chat_id from message object
- `_get_message_type()` - Determine message type flags
- `_format_error_by_code()` - Format error message based on HTTP code
- `_format_balance_response()` - Format successful balance response
- `_send_message_response()` - Send response message to user

### 6. `create_callback_router()` in `callback_registry.py`

**Before**: 264 lines  
**After**: ~25 lines  
**Reduction**: 91%

**Extracted Helper Functions**:
- `_register_menu_handlers()` - Register main menu handlers
- `_register_arbitrage_handlers()` - Register arbitrage handlers
- `_register_help_and_noop_handlers()` - Register help and noop handlers
- `_register_settings_handlers()` - Register settings handlers
- `_register_alert_handlers()` - Register alert handlers
- `_register_arb_submenu_handlers()` - Register arb submenu handlers
- `_register_target_handlers()` - Register target handlers
- `_register_waxpeer_handlers()` - Register Waxpeer handlers
- `_register_float_arbitrage_handlers()` - Register float arb handlers
- `_register_advanced_orders_handlers()` - Register advanced order handlers
- `_register_doppler_and_pattern_handlers()` - Register doppler/pattern handlers
- `_register_strategy_handlers()` - Register strategy handlers
- `_register_other_features_handlers()` - Register other features
- `_register_auto_arb_handlers()` - Register auto arb handlers
- `_register_smart_arbitrage_handlers()` - Register smart arb handlers
- `_register_analysis_handlers()` - Register analysis handlers
- `_register_prefix_handlers()` - Register prefix handlers

### 7. `market_analysis_callback()` in `market_analysis_handler.py`

**Before**: 252 lines  
**After**: 109 lines  
**Reduction**: 57%

**Extracted Helper Functions**:
- `_create_analysis_keyboard()` - Create analysis options keyboard
- `_add_game_selection_rows()` - Add game selection rows to keyboard
- `_handle_game_selection()` - Handle game selection action
- `_run_price_changes_analysis()` - Run price changes analysis
- `_run_trending_analysis()` - Run trending items analysis
- `_run_volatility_analysis()` - Run volatility analysis
- `_run_undervalued_analysis()` - Run undervalued items analysis
- `_run_recommendations_analysis()` - Run investment recommendations

### 8. `button_callback_handler()` in `callbacks.py`

**Before**: 950 lines  
**After**: ~40 lines  
**Reduction**: 96%

**Approach**: Delegated to CallbackRouter (callback_registry.py) with fallback to legacy handler.

**Key Changes**:
- Replaced 83+ elif statements with CallbackRouter dispatch
- Extracted `_handle_legacy_callbacks()` for backward compatibility
- File reduced from 1256 to 491 lines (-61%)

### 9. `ai_train_liquid_command()` in `ai_handler.py`

**Before**: 299 lines  
**After**: 137 lines  
**Reduction**: 54%

**Extracted Helper Functions**:
- `_init_liquid_training_components()` - Initialize filters and API clients
- `_calculate_item_liquidity()` - Calculate liquidity score for an item
- `_save_liquid_data_to_csv()` - Save liquid items to CSV
- `_train_model_on_liquid_data()` - Train the price prediction model

---

## 📋 Refactoring Guidelines

### Step 1: Identify Long Functions

```bash
python scripts/find_long_functions.py --threshold 50
python scripts/find_long_functions.py --threshold 100 --path src/dmarket
```

### Step 2: Write Tests First

Before refactoring, ensure tests exist for:
- Current behavior
- Edge cases
- Error conditions

### Step 3: Extract Helper Functions

Apply these patterns:

#### Early Returns Pattern

```python
# ❌ BEFORE (nested)
if condition1:
    if condition2:
        if condition3:
            return result

# ✅ AFTER (early returns)
if not condition1:
    return None
if not condition2:
    return None
if not condition3:
    return None
return result
```

#### Single Responsibility

```python
# ❌ BEFORE (multiple responsibilities)
async def process_item(item):
    # validate
    # fetch data
    # calculate
    # save
    # notify
    ...

# ✅ AFTER (single responsibility)
async def process_item(item):
    if not await validate_item(item):
        return None
    data = await fetch_item_data(item)
    result = calculate_result(data)
    await save_result(result)
    await notify_user(result)
    return result
```

### Step 4: Verify

After each change:
```bash
# Run tests
python -m pytest tests/unit/ -v

# Check syntax
python -c "import ast; ast.parse(open('path/to/file.py').read())"

# Run linters
ruff check src/
mypy src/
```

---

## 🛠️ Tools

### Find Long Functions

```bash
# All functions > 50 lines in src/
python scripts/find_long_functions.py --threshold 50 --path src

# Specific directory
python scripts/find_long_functions.py --threshold 50 --path src/telegram_bot

# Fail if violations found (for CI)
python scripts/find_long_functions.py --threshold 100 --fail
```

### Generate TODO List

```bash
python scripts/generate_refactoring_todo.py --output TODO_REFACTORING.md
```

---

## 📈 Progress Tracking

### Metrics

| Metric | Before | Current | Target |
|--------|--------|---------|--------|
| Functions > 100 lines | 147 | 145 | 0 |
| Functions > 50 lines | 639 | 637 | < 50 |
| Average function length | ~80 lines | ~78 lines | < 30 lines |
| Test coverage | 85% | 85% | 90% |

### Sprint Plan

| Sprint | Focus Area | Functions | Est. Hours |
|--------|------------|-----------|------------|
| 1 (Current) | API Layer | `_request()` x2 | 4h | ✅
| 2 | Telegram Handlers | `button_callback_handler`, `callback_router` | 8h |
| 3 | Main Module | `initialize`, `register_all_handlers` | 6h |
| 4 | Commands | `check_balance_command`, `ai_train_liquid_command` | 4h |
| 5 | Config | `_update_from_env` | 3h |

---

## 📚 Resources

- **Refactoring Examples**: `docs/refactoring_examples/`
- **Copilot Instructions**: `.github/copilot-instructions.md` v5.0
- **Testing Guide**: `docs/TESTING_COMPLETE_GUIDE.md`
- **Find Long Functions**: `scripts/find_long_functions.py`
- **Generate TODO**: `scripts/generate_refactoring_todo.py`

---

## 📝 Notes

### Do's

- ✅ Write tests before refactoring
- ✅ Extract one function at a time
- ✅ Run tests after each change
- ✅ Keep helper functions < 50 lines
- ✅ Use descriptive function names
- ✅ Add docstrings to all functions

### Don'ts

- ❌ Refactor without tests
- ❌ Change multiple functions at once
- ❌ Create deeply nested helpers
- ❌ Break existing API contracts
- ❌ Remove comments without understanding

---

**Version**: 1.0  
**Maintainer**: @copilot  
**Part of**: Phase 2 Infrastructure Improvements

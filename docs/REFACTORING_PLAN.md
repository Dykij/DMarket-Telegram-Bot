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

| Threshold | Count | Status |
|-----------|-------|--------|
| > 100 lines | 147 | 🔴 Critical |
| > 50 lines | 639 | 🟠 Needs work |

### Top 15 Priority Functions

| # | Function | File | Lines | Priority | Status |
|---|----------|------|-------|----------|--------|
| 1 | `button_callback_handler()` | `callbacks.py` | 950 | 🔴 Critical | ⏳ Pending |
| 2 | `initialize()` | `main.py` | 594 | 🔴 Critical | ⏳ Pending |
| 3 | `register_all_handlers()` | `register_all_handlers.py` | 455 | 🔴 Critical | ⏳ Pending |
| 4 | `check_balance_command()` | `balance_command.py` | 331 | 🔴 Critical | ⏳ Pending |
| 5 | `_request()` | `dmarket_api.py` | 261 | 🟠 High | ✅ Refactored (was 330) |
| 6 | `ai_train_liquid_command()` | `ai_handler.py` | 299 | 🟠 High | ⏳ Pending |
| 7 | `create_callback_router()` | `callback_registry.py` | 264 | 🟠 High | ⏳ Pending |
| 8 | `_request()` | `api/client.py` | 221 | 🟠 High | ✅ Refactored (was 262) |
| 9 | `_update_from_env()` | `config.py` | 252 | 🟠 High | ⏳ Pending |
| 10 | `market_analysis_callback()` | `market_analysis_handler.py` | 252 | 🟠 High | ⏳ Pending |
| 11 | `handle_mode_selection_callback()` | `automatic_arbitrage_handler.py` | 240 | 🟠 High | ⏳ Pending |
| 12 | `train_from_real_data()` | `enhanced_predictor.py` | 225 | 🟠 High | ⏳ Pending |
| 13 | `hold_callback_handler()` | `intelligent_hold_handler.py` | 223 | 🟡 Medium | ⏳ Pending |
| 14 | `telegram_error_boundary()` | `telegram_error_handlers.py` | 222 | 🟡 Medium | ⏳ Pending |
| 15 | `auto_trade_scan_all()` | `main_keyboard.py` | 219 | 🟡 Medium | ⏳ Pending |

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

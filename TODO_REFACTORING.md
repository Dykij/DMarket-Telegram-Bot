# Phase 2 Refactoring TODO List

> **Generated**: 2026-01-01
> **Last Updated**: 2026-01-01 07:30 UTC
> **Status**: In Progress (1/15 complete)
> **Target**: Complete by February 11, 2026

---

## Overview

**Total Tasks**: 15
**Completed**: 1 ✅
**In Progress**: 0
**Remaining**: 14
**Estimated Hours**: 43.5h (45.5h - 2h saved)
**Average Complexity**: 7.7/10

### Progress

```
Critical:  [✅] 1/4 functions complete
High:      [ ] 11/116 functions
Medium:    [ ] 0/116 functions
Low:       [ ] 0/116 functions

Overall: █░░░░░░░░░░░░░░ 6.67% (1/15 tasks)
```

---

## Priority 1: Critical (MUST DO) 🔴

_Functions > 190 lines OR in critical modules_

### 1. `_request()` - 297 lines ✅ COMPLETE

- **File**: `src/dmarket/dmarket_api.py`
- **Lines**: 297 → 145 + 11 helpers
- **Complexity**: 10/10 → 4/10
- **Estimated Time**: 4.0h
- **Actual Time**: 2.0h (50% faster!)
- **Status**: ✅ **COMPLETE** (2026-01-01)

**Results**:
- ✅ 11 helper functions extracted (<50 lines each)
- ✅ Main function reduced to 145 lines (52% reduction)
- ✅ Nesting: 5 levels → 2 levels
- ✅ 29 unit tests created (all passing)
- ✅ Coverage: 56% (target: 85%+)
- ✅ Files created:
  - `src/dmarket/dmarket_api_refactored.py` (549 lines)
  - `tests/unit/test_dmarket_api_refactored.py` (29 tests)

**Commit**: `feat(refactor): extract 11 helpers from _request() (297→145 lines)`

### 2. `_request()` - 264 lines

- **File**: `src/dmarket/api/client.py`
- **Lines**: 264
- **Complexity**: 9/10
- **Estimated Time**: 4.0h
- **Status**: ⏳ Not Started

**Actions**:
- [ ] Write tests for current behavior
- [ ] Identify logical sections
- [ ] Extract helper functions (<50 lines each)
- [ ] Apply early returns pattern
- [ ] Run tests to verify
- [ ] Update documentation

### 3. `auto_trade_items()` - 199 lines

- **File**: `src/dmarket/arbitrage_scanner.py`
- **Lines**: 199
- **Complexity**: 9/10
- **Estimated Time**: 3.0h
- **Status**: ⏳ Not Started

**Actions**:
- [ ] Write tests for current behavior
- [ ] Identify logical sections
- [ ] Extract helper functions (<50 lines each)
- [ ] Apply early returns pattern
- [ ] Run tests to verify
- [ ] Update documentation

### 4. `find_mispriced_rare_items()` - 192 lines

- **File**: `src/dmarket/intramarket_arbitrage.py`
- **Lines**: 192
- **Complexity**: 8/10
- **Estimated Time**: 3.0h
- **Status**: ⏳ Not Started

**Actions**:
- [ ] Write tests for current behavior
- [ ] Identify logical sections
- [ ] Extract helper functions (<50 lines each)
- [ ] Apply early returns pattern
- [ ] Run tests to verify
- [ ] Update documentation

---

## Priority 2: High 🟠

_Functions 150-190 lines OR high-priority modules_

### 5. `analyze_market_depth()` - 191 lines

- **File**: `src/dmarket/market_analysis.py`
- **Complexity**: 8/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 6. `direct_balance_request()` - 186 lines

- **File**: `src/dmarket/dmarket_api.py`
- **Complexity**: 8/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 7. `find_trending_items()` - 184 lines

- **File**: `src/dmarket/intramarket_arbitrage.py`
- **Complexity**: 8/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 8. `scan_game()` - 175 lines

- **File**: `src/dmarket/arbitrage_scanner.py`
- **Complexity**: 7/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 9. `check_user_balance()` - 174 lines

- **File**: `src/dmarket/arbitrage_scanner.py`
- **Complexity**: 7/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 10. `get_balance()` - 170 lines

- **File**: `src/dmarket/dmarket_api.py`
- **Complexity**: 7/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 11. `find_price_anomalies()` - 170 lines

- **File**: `src/dmarket/intramarket_arbitrage.py`
- **Complexity**: 7/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 12. `_analyze_item()` - 169 lines

- **File**: `src/dmarket/arbitrage_scanner.py`
- **Complexity**: 7/10
- **Estimated**: 3.0h
- **Status**: ⏳ Not Started

### 13. `get_balance()` - 158 lines

- **File**: `src/dmarket/api/wallet.py`
- **Complexity**: 7/10
- **Estimated**: 2.5h
- **Status**: ⏳ Not Started

### 14. `get_rebalancing_recommendations()` - 154 lines

- **File**: `src/dmarket/portfolio_manager.py`
- **Complexity**: 7/10
- **Estimated**: 2.5h
- **Status**: ⏳ Not Started

### 15. `find_arbitrage_opportunities_advanced()` - 151 lines

- **File**: `src/dmarket/arbitrage/search.py`
- **Complexity**: 7/10
- **Estimated**: 2.5h
- **Status**: ⏳ Not Started

---

## Guidelines

### Before Refactoring

1. ✅ Write tests for existing behavior
2. ✅ Run tests to establish baseline
3. ✅ Understand function's purpose
4. ✅ Identify logical sections

### During Refactoring

1. ✅ Extract one section at a time
2. ✅ Name functions descriptively
3. ✅ Keep functions < 50 lines
4. ✅ Apply early returns
5. ✅ Add docstrings
6. ✅ Run tests after each change

### After Refactoring

1. ✅ Verify all tests pass
2. ✅ Check coverage maintained/improved
3. ✅ Run linters (ruff, mypy)
4. ✅ Update CHANGELOG.md
5. ✅ Mark task as complete

---

## Resources

- **Refactoring Guide**: `docs/PHASE_2_REFACTORING_GUIDE.md`
- **Examples**: `docs/refactoring_examples/`
- **Copilot Instructions**: `.github/copilot-instructions.md` v5.0
- **Find Long Functions**: `python scripts/find_long_functions.py --threshold 50`

---

**Next Update**: January 7, 2026
**Target Completion**: February 11, 2026
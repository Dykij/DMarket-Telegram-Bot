# Phase 2 Refactoring Guide

> **Status**: Infrastructure Ready | Refactoring In Progress
> **Version**: 1.0
> **Date**: January 1, 2026
> **Target Completion**: Q1 2026

---

## 🎯 Phase 2 Goals

### Primary Objectives

1. ✅ **E2E Test Infrastructure** - COMPLETED
2. ✅ **Code Readability Guidelines** - COMPLETED
3. ⏳ **Code Refactoring** - IN PROGRESS (30%)
4. ⏳ **Performance Optimization** - PENDING
5. ⏳ **Coverage Improvement** (85% → 90%) - PENDING

---

## 📊 Current Status

| Metric                   | Current | Target   | Progress |
| ------------------------ | ------- | -------- | -------- |
| **Test Coverage**        | 85%+    | 90%      | 🟡        |
| **E2E Tests**            | 4 files | Complete | ✅        |
| **Copilot Instructions** | v5.0    | v5.0     | ✅        |
| **Tests Count**          | 11,117  | -        | ✅        |
| **Refactored Modules**   | 0       | 50+      | 🔴        |

---

## 🔧 Refactoring Checklist

### 1. Code Complexity Reduction

#### High Priority Files (Deep Nesting Detected)

**Critical Modules** (16+ space indentation found):

- [ ] `src/dmarket/arbitrage_scanner.py`
- [ ] `src/dmarket/targets/manager.py`
- [ ] `src/utils/database.py`
- [ ] `src/telegram_bot/handlers/backtest_handler.py`
- [ ] `src/dmarket/dmarket_api.py`
- [ ] `src/dmarket/auto_seller.py`
- [ ] `src/portfolio/manager.py`

**Pattern to Refactor**:

```python
# ❌ BEFORE (nested conditions)
async def process_item(item):
    if item.price > 0:
        if item.suggested_price > 0:
            if item.profit_margin > 3:
                if await check_liquidity(item):
                    if not item.is_blacklisted:
                        return await execute_trade(item)
    return None

# ✅ AFTER (early returns - Phase 2 style)
async def process_item(item):
    """Process item with validation (Phase 2 refactored)."""
    if item.price <= 0:
        return None

    if item.suggested_price <= 0:
        return None

    if item.profit_margin <= 3:
        return None

    if not await check_liquidity(item):
        return None

    if item.is_blacklisted:
        return None

    return await execute_trade(item)
```

#### Function Length Violations

**Files with Functions > 50 Lines** (requires splitting):

To identify:

```bash
# Search for long functions
python scripts/find_long_functions.py --threshold 50
```

**Refactoring Strategy**:

1. Extract helper functions for each logical step
2. Use descriptive names (not `_helper1`, `_helper2`)
3. Each function should do ONE thing
4. Add docstrings to extracted functions

---

### 2. Performance Optimization

#### Profiling Required Before Optimization

**DO NOT optimize without profiling!**

```bash
# Step 1: Profile the application
pip install py-spy
py-spy record -o profile.svg -- python -m src.main

# Step 2: Identify bottlenecks
py-spy top -- python -m pytest tests/test_arbitrage_scanner.py

# Step 3: Optimize identified bottlenecks only
# Step 4: Re-profile to verify improvement
```

#### Known Performance Opportunities

**1. Arbitrage Scanner Batching**

Current:

```python
# Sequential processing
for item in items:
    result = await process_item(item)
```

Optimized:

```python
# Batch processing (Phase 2)
async def scan_items_batch(items: list[Item], batch_size: int = 100) -> list[Opportunity]:
    """Scan items in batches for better performance."""
    tasks = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        tasks.append(process_batch(batch))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    opportunities = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning("batch_error", error=str(result))
            continue
        opportunities.extend(result)

    return opportunities
```

**2. Enhanced Caching Strategy**

```python
# Current: Single-level cache
@cached(ttl=300)
async def get_market_items(game: str):
    ...

# Phase 2: Multi-level cache with context
@cached(ttl=300, key="market:items:{game}:{level}")
async def get_market_items_for_level(game: str, level: str):
    """Cache specific to game AND level."""
    ...

# Invalidation on updates
async def update_item_price(item_id: str, new_price: float):
    await save_price(item_id, new_price)
    # Invalidate related caches
    await cache.delete_pattern(f"market:items:*")
```

**3. Connection Pooling**

```python
# httpx client optimization
limits = httpx.Limits(
    max_keepalive_connections=20,
    max_connections=100,
    keepalive_expiry=30.0
)

client = httpx.AsyncClient(
    timeout=10.0,
    limits=limits,
    http2=True
)
```

---

### 3. Test Coverage Improvement

**Current Coverage**: 85%+
**Target**: 90%

#### Modules Below 85% Coverage

Run:

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

Then open `htmlcov/index.html` and identify:

- Red lines (not covered)
- Yellow branches (partially covered)

#### Priority Areas for New Tests

1. **E2E Flows** ✅ (Already added in Phase 2)
   - `tests/e2e/test_arbitrage_flow.py`
   - `tests/e2e/test_target_management_flow.py`

2. **Error Handling Paths** ⏳
   - API errors (rate limits, timeouts)
   - Database connection failures
   - Validation errors

3. **Edge Cases** ⏳
   - Empty lists
   - Null values
   - Extreme prices (very high/low)
   - Concurrent access

---

## 📝 Refactoring Process

### Step-by-Step Workflow

**For Each Module:**

1. **Analyze** 📊

   ```bash
   # Check complexity
   radon cc src/dmarket/arbitrage_scanner.py -a

   # Check maintainability
   radon mi src/dmarket/arbitrage_scanner.py
   ```

2. **Profile** (if performance-critical) ⚡

   ```bash
   py-spy record -o profile.svg -- python -m src.dmarket.arbitrage_scanner
   ```

3. **Write Tests First** 🧪
   - Add tests for current behavior
   - Ensure 100% coverage of function being refactored

4. **Refactor** ✨
   - Apply early returns
   - Extract helper functions
   - Reduce nesting
   - Improve naming

5. **Verify** ✅

   ```bash
   # Run tests
   pytest tests/ -v

   # Check coverage
   pytest --cov=src --cov-report=term-missing

   # Lint
   ruff check src/
   mypy src/
   ```

6. **Document** 📖
   - Update docstrings
   - Add inline comments for complex logic
   - Update CHANGELOG.md

---

## 🎨 Code Style Examples

### Early Returns Pattern

**❌ BAD: Deep Nesting**

```python
async def validate_and_process(data):
    if data is not None:
        if data.get("price"):
            if data["price"] > 0:
                if data.get("title"):
                    if len(data["title"]) > 3:
                        return await process(data)
    return {"error": "Invalid data"}
```

**✅ GOOD: Early Returns (Phase 2)**

```python
async def validate_and_process(data):
    """Validate and process data with early returns."""
    if data is None:
        return {"error": "Data is None"}

    if not data.get("price"):
        return {"error": "Price missing"}

    if data["price"] <= 0:
        return {"error": "Invalid price"}

    if not data.get("title"):
        return {"error": "Title missing"}

    if len(data["title"]) <= 3:
        return {"error": "Title too short"}

    return await process(data)
```

### Function Splitting

**❌ BAD: Long Function (100+ lines)**

```python
async def scan_and_trade(game: str, level: str):
    # 30 lines: validation
    # 40 lines: scanning
    # 30 lines: filtering
    # 20 lines: trading
    # 10 lines: notification
    pass  # 130 lines total!
```

**✅ GOOD: Split Functions (Phase 2)**

```python
async def scan_and_trade(game: str, level: str):
    """Scan market and execute trades (orchestrator)."""
    # Validation
    if not _is_valid_game(game):
        return {"error": "Invalid game"}

    # Scan
    opportunities = await _scan_market(game, level)
    if not opportunities:
        return {"message": "No opportunities found"}

    # Filter
    filtered = await _filter_opportunities(opportunities)

    # Trade
    results = await _execute_trades(filtered)

    # Notify
    await _send_notifications(results)

    return {"success": True, "results": results}

async def _scan_market(game: str, level: str) -> list[Opportunity]:
    """Scan market for opportunities."""
    # 20-30 lines of focused logic
    ...

async def _filter_opportunities(opps: list[Opportunity]) -> list[Opportunity]:
    """Filter opportunities by criteria."""
    # 15-20 lines of focused logic
    ...
```

### Descriptive Naming

**❌ BAD: Cryptic Names**

```python
async def proc_arb(g, l, min_p):
    opps = await scan(g, l)
    filt = [o for o in opps if o.p > min_p]
    return filt
```

**✅ GOOD: Clear Names (Phase 2)**

```python
async def process_arbitrage_opportunities(
    game: str,
    level: str,
    min_profit_margin: float
) -> list[ArbitrageOpportunity]:
    """Process arbitrage opportunities for game and level.

    Args:
        game: Game code (csgo, dota2, tf2, rust)
        level: Arbitrage level (boost, standard, medium, advanced, pro)
        min_profit_margin: Minimum profit % to include

    Returns:
        List of filtered arbitrage opportunities
    """
    opportunities = await scan_market(game, level)

    filtered_opportunities = [
        opp for opp in opportunities
        if opp.profit_margin > min_profit_margin
    ]

    return filtered_opportunities
```

---

## 🔍 Quality Metrics

### Before Phase 2

```
Average Function Length: 45 lines
Max Nesting Depth: 5 levels
Test Coverage: 85%
Cyclomatic Complexity: 8 (medium)
```

### After Phase 2 (Target)

```
Average Function Length: 30 lines ⬇️
Max Nesting Depth: 3 levels ⬇️
Test Coverage: 90% ⬆️
Cyclomatic Complexity: 5 (low) ⬇️
```

---

## 📅 Implementation Timeline

### Week 1-2 (January 1-14, 2026) ⏳ CURRENT

- [x] Setup E2E test infrastructure
- [x] Update Copilot instructions v5.0
- [x] Create refactoring guide (this document)
- [ ] Refactor 10 critical modules
- [ ] Add 50+ new tests

### Week 3-4 (January 15-28, 2026)

- [ ] Refactor remaining 40 modules
- [ ] Performance profiling and optimization
- [ ] Coverage improvement to 88%
- [ ] Documentation updates

### Week 5-6 (January 29 - February 11, 2026)

- [ ] Final coverage push to 90%
- [ ] Code review all changes
- [ ] Update all documentation
- [ ] Performance benchmarking

---

## 🚀 Quick Commands

```bash
# Run all tests
pytest tests/ -v

# Run only E2E tests
pytest tests/e2e/ -m e2e -v

# Exclude E2E for fast feedback
pytest -m "not e2e"

# Coverage check
pytest --cov=src --cov-report=term-missing --cov-report=html

# Find long functions
ruff check src/ --select C901  # McCabe complexity

# Profile specific module
py-spy top -- python -m pytest tests/test_arbitrage_scanner.py
```

---

## 📚 Resources

- **Copilot Instructions**: `.github/copilot-instructions.md` v5.0
- **Testing Guide**: `docs/testing_guide.md`
- **Code Quality Tools**: `docs/code_quality_tools_guide.md`
- **Roadmap**: `IMPROVEMENT_ROADMAP.md`

---

## ✅ Sign-Off Criteria

Phase 2 is complete when:

- ✅ All modules have max 3 nesting levels
- ✅ All functions are < 50 lines
- ✅ Test coverage >= 90%
- ✅ All E2E tests passing
- ✅ Performance benchmarks met
- ✅ Documentation updated

---

**Version**: 1.0
**Last Updated**: January 1, 2026
**Next Review**: January 15, 2026

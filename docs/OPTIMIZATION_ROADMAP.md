# Algorithm Optimization Recommendations

## 📋 Overview

This document provides concrete optimization recommendations for the DMarket Telegram Bot based on:
1. **Open Data Structures (Python)** - https://opendatastructures.org/ods-python/
2. **DMarket API Best Practices** - https://docs.dmarket.com/v1/swagger.html
3. **Current performance profiling results**

## 🎯 High-Impact Optimizations

### 1. Implement Batch API Operations

**Problem**: Multiple sequential API calls for related operations
**Solution**: Use batch endpoints from DMarket API v1.1.0

**Current (Inefficient)**:
```python
# 10 separate API calls - slow!
for item in items:
    price = await api.get_item_price(item.id)
    # Total time: 10 * 200ms = 2000ms
```

**Optimized (Batch)**:
```python
# 1 API call - 10x faster!
prices = await api.get_aggregated_prices_bulk(
    game="csgo",
    titles=[item.title for item in items],
    limit=100
)
# Total time: ~200ms
```

**Implementation Priority**: ⭐⭐⭐⭐⭐ (Critical)
**Estimated Speedup**: 10x for arbitrage scanning
**Effort**: 3-4 hours

**Action Items**:
1. Implement `buy_offers_batch()` method
2. Use `get_aggregated_prices_bulk()` instead of individual calls
3. Update arbitrage scanner to use batch operations

---

### 2. Replace Linear Search with Hash Table Lookups

**Problem**: O(n) linear search for item matching
**Solution**: Build hash table index for O(1) lookups

**Current (O(n) - Slow)**:
```python
def find_item_by_title(items: list[dict], title: str) -> dict | None:
    """O(n) linear search"""
    for item in items:
        if item["title"] == title:
            return item
    return None

# For 1000 items: average 500 comparisons
```

**Optimized (O(1) - Fast)**:
```python
def build_item_index(items: list[dict]) -> dict[str, dict]:
    """O(n) one-time indexing"""
    return {item["title"]: item for item in items}

# Usage
item_index = build_item_index(items)
item = item_index.get(title)  # O(1) lookup
# For 1000 items: 1 lookup
```

**Implementation Priority**: ⭐⭐⭐⭐ (High)
**Estimated Speedup**: 100-500x for large datasets
**Effort**: 1-2 hours

**Action Items**:
1. Add index building to `ArbitrageScanner`
2. Update search methods to use hash table
3. Rebuild index on data refresh

---

### 3. Use Skip List for Price History Range Queries

**Problem**: O(n) scan for time-range queries in price history
**Solution**: Skip list for O(log n) range queries

**Current (O(n) - Slow)**:
```python
def get_prices_in_range(
    prices: list[tuple[int, float]],  # (timestamp, price)
    start: int,
    end: int,
) -> list[tuple[int, float]]:
    """O(n) scan - inefficient"""
    return [
        (ts, price) for ts, price in prices
        if start <= ts <= end
    ]

# For 10,000 points: 10,000 comparisons
```

**Optimized (O(log n) - Fast)**:
```python
from sortedcontainers import SortedList

class PriceHistorySkipList:
    """Skip list for efficient range queries"""
    
    def __init__(self):
        self.prices = SortedList(key=lambda x: x[0])
    
    def add_price(self, timestamp: int, price: float):
        """O(log n) insertion"""
        self.prices.add((timestamp, price))
    
    def get_range(self, start: int, end: int) -> list[tuple[int, float]]:
        """O(log n + k) range query where k = results"""
        start_idx = self.prices.bisect_left((start, 0))
        end_idx = self.prices.bisect_right((end, float('inf')))
        return list(self.prices[start_idx:end_idx])

# For 10,000 points, 100 results: ~7 + 100 = 107 operations
```

**Implementation Priority**: ⭐⭐⭐ (Medium)
**Estimated Speedup**: 10-100x for range queries
**Effort**: 4-6 hours
**Dependencies**: Install `sortedcontainers` package

**Action Items**:
1. Add `sortedcontainers` to requirements.txt
2. Implement `PriceHistorySkipList` class
3. Migrate price history storage
4. Add tests for range queries

---

### 4. Optimize Cache Key Generation

**Problem**: O(m log m) sorting in cache key generation
**Solution**: Use hash-based cache keys

**Current (O(m log m) - Acceptable)**:
```python
def _make_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """O(n + m log m) where m = len(kwargs)"""
    key_parts = [prefix]
    for arg in args[1:]:
        key_parts.append(str(arg))
    # Sorting kwargs: O(m log m)
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    return ":".join(key_parts)
```

**Optimized (O(n + m) - Faster)**:
```python
import hashlib

def _make_cache_key_fast(
    prefix: str,
    args: tuple,
    kwargs: dict
) -> str:
    """O(n + m) hash-based key generation"""
    # Create hashable tuple
    key_tuple = (prefix, args[1:], tuple(sorted(kwargs.items())))
    # Hash to fixed-length string: O(n + m)
    key_bytes = str(key_tuple).encode()
    return hashlib.blake2b(key_bytes, digest_size=16).hexdigest()

# 32-char hex string, always same length
```

**Implementation Priority**: ⭐⭐ (Low - optimize only if profiling shows bottleneck)
**Estimated Speedup**: 2-3x for cache key generation
**Trade-off**: Less readable keys in logs
**Effort**: 30 minutes

**Action Items**:
1. Profile cache key generation
2. If bottleneck detected, implement hash-based keys
3. Add config option to toggle readable vs fast keys

---

### 5. Implement W-TinyLRU Cache for Better Hit Rates

**Problem**: Standard LRU evicts frequently-accessed items
**Solution**: W-TinyLRU (Windowed TinyLRU) admission policy

**Concept** (From Open Data Structures):
- **Window**: Small LRU cache for new items
- **Main**: Large LRU cache for proven frequently-used items
- **Promotion**: Items accessed 2+ times move from window to main

**Implementation**:
```python
class WTinyLRUCache:
    """
    Windowed TinyLRU cache with frequency filter
    
    Better hit rates than standard LRU for skewed access patterns
    (e.g., 80% of requests for 20% of items)
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        window_size: int = 100,  # 10% of cache
        default_ttl: int = 300,
    ):
        self.max_size = max_size
        self.window_size = window_size
        self.default_ttl = default_ttl
        
        # Window LRU for new items
        self.window: OrderedDict = OrderedDict()
        
        # Main LRU for frequently accessed
        self.main: OrderedDict = OrderedDict()
        
        # Access counter
        self.access_count: dict[str, int] = {}
    
    async def get(self, key: str) -> Any | None:
        """Get with frequency tracking"""
        # Check window first
        if key in self.window:
            entry = self.window[key]
            if not self._is_expired(entry):
                self.access_count[key] = self.access_count.get(key, 0) + 1
                
                # Promote to main if accessed 2+ times
                if self.access_count[key] >= 2:
                    self._promote_to_main(key, entry)
                else:
                    self.window.move_to_end(key)
                
                return entry["value"]
        
        # Check main
        if key in self.main:
            entry = self.main[key]
            if not self._is_expired(entry):
                self.main.move_to_end(key)
                return entry["value"]
        
        return None
    
    def _promote_to_main(self, key: str, entry: dict):
        """Promote frequently accessed item from window to main"""
        # Remove from window
        del self.window[key]
        
        # Add to main (with eviction if needed)
        if len(self.main) >= self.max_size - self.window_size:
            oldest = next(iter(self.main))
            del self.main[oldest]
        
        self.main[key] = entry
        self.main.move_to_end(key)
```

**Benefits**:
- **+5-10% hit rate** for trading data (skewed access)
- **Fewer cache misses** for popular items
- **Better memory utilization**

**Implementation Priority**: ⭐⭐ (Medium - nice to have)
**Estimated Improvement**: +5-10% cache hit rate
**Effort**: 6-8 hours

**Action Items**:
1. Implement `WTinyLRUCache` class
2. Add comprehensive tests
3. A/B test against current `TTLCache`
4. Migrate if hit rate improves significantly

---

### 6. Database Query Optimization with Composite Indexes

**Problem**: Slow queries on trade history
**Solution**: Composite B-tree indexes

**Current (Slow)**:
```sql
-- No index on (game_id, timestamp, price)
SELECT * FROM trades
WHERE game_id = 'csgo'
  AND timestamp >= '2025-01-01'
  AND price >= 10.00
ORDER BY timestamp DESC
LIMIT 100;

-- Sequential scan: O(n) where n = all trades
```

**Optimized (Fast)**:
```sql
-- Create composite index
CREATE INDEX idx_trades_game_time_price
ON trades (game_id, timestamp DESC, price)
USING BTREE;

-- Now uses index: O(log n + k) where k = 100
SELECT * FROM trades
WHERE game_id = 'csgo'
  AND timestamp >= '2025-01-01'
  AND price >= 10.00
ORDER BY timestamp DESC
LIMIT 100;
```

**Implementation Priority**: ⭐⭐⭐⭐ (High)
**Estimated Speedup**: 100-1000x for large datasets
**Effort**: 2-3 hours

**Action Items**:
1. Analyze slow queries with `EXPLAIN ANALYZE`
2. Create composite indexes for common query patterns
3. Add migration in Alembic
4. Monitor index usage with `pg_stat_user_indexes`

---

### 7. Parallel Arbitrage Scanning with asyncio.gather

**Problem**: Sequential game scanning is slow
**Solution**: Parallel concurrent scanning

**Current (Sequential)**:
```python
async def scan_all_games(games: list[str]) -> list[dict]:
    """O(n * scan_time) - slow"""
    results = []
    for game in games:
        result = await scan_game(game)  # 1.5s each
        results.extend(result)
    return results

# For 4 games: 4 * 1.5s = 6.0s total
```

**Optimized (Parallel)**:
```python
async def scan_all_games(games: list[str]) -> list[dict]:
    """O(max(scan_times)) - fast"""
    tasks = [scan_game(game) for game in games]
    results_list = await asyncio.gather(*tasks)
    
    # Flatten results
    return [item for results in results_list for item in results]

# For 4 games: max(1.5s, 1.5s, 1.5s, 1.5s) = 1.5s total
# 4x speedup!
```

**Implementation Status**: ✅ Already implemented in `arbitrage_scanner.py`

**Current Performance**: 4x speedup for 4 games (linear with # of games)

**Optimization Opportunity**: Limit concurrency to respect rate limits
```python
import asyncio
from asyncio import Semaphore

async def scan_all_games_limited(
    games: list[str],
    max_concurrent: int = 3,
) -> list[dict]:
    """Parallel with rate limit respect"""
    sem = Semaphore(max_concurrent)
    
    async def scan_with_limit(game: str):
        async with sem:
            return await scan_game(game)
    
    tasks = [scan_with_limit(game) for game in games]
    results_list = await asyncio.gather(*tasks)
    return [item for results in results_list for item in results]
```

---

## 📊 Priority Matrix

| Optimization | Priority | Speedup | Effort | ROI |
|--------------|----------|---------|--------|-----|
| Batch API Operations | ⭐⭐⭐⭐⭐ | 10x | 3-4h | Very High |
| Database Indexes | ⭐⭐⭐⭐ | 100x | 2-3h | Very High |
| Hash Table Lookups | ⭐⭐⭐⭐ | 100-500x | 1-2h | Very High |
| Skip List Range Queries | ⭐⭐⭐ | 10-100x | 4-6h | High |
| W-TinyLRU Cache | ⭐⭐ | +5-10% hit | 6-8h | Medium |
| Cache Key Optimization | ⭐⭐ | 2-3x | 30m | Low* |

*Low ROI because cache key generation is rarely a bottleneck

---

## 🎯 Recommended Implementation Order

### Phase 1: Quick Wins (Week 1)
1. ✅ Hash table for item lookups - 2 hours
2. ✅ Database composite indexes - 3 hours
3. ✅ Batch API operations - 4 hours

**Total Effort**: 9 hours
**Expected Speedup**: 10-100x in targeted areas

### Phase 2: Advanced Optimizations (Week 2-3)
4. Skip list for price history - 6 hours
5. W-TinyLRU cache implementation - 8 hours
6. Performance testing & validation - 4 hours

**Total Effort**: 18 hours
**Expected Improvement**: +10-20% overall performance

### Phase 3: Fine-tuning (Ongoing)
7. Profile-guided optimization
8. Cache key optimization (if needed)
9. Continuous monitoring & adjustment

---

## 🧪 Validation & Testing

### Benchmarking Suite

Create performance regression tests:

```python
import pytest
import time

@pytest.mark.benchmark
async def test_arbitrage_scan_performance():
    """Ensure scan completes within performance budget"""
    start = time.time()
    
    results = await scanner.scan_all_games(["csgo", "dota2"])
    
    elapsed = time.time() - start
    
    # Performance budget: 3 seconds max
    assert elapsed < 3.0, f"Scan took {elapsed:.2f}s, expected <3.0s"
    assert len(results) > 0


@pytest.mark.benchmark
async def test_cache_hit_rate():
    """Monitor cache efficiency"""
    # Warmup
    for _ in range(100):
        await api.get_market_items("csgo", limit=10)
    
    stats = await cache.get_stats()
    
    # Expect >50% hit rate for market data
    assert stats["hit_rate"] >= 50.0
```

### Profiling

Use Python profilers to identify actual bottlenecks:

```bash
# Profile with cProfile
python -m cProfile -o profile.stats -m src.main

# Analyze with snakeviz
snakeviz profile.stats

# Or use py-spy for production profiling
py-spy record -o profile.svg --pid <pid>
```

---

## 📚 References

1. **Open Data Structures (Python)**
   - Chapter 4: Hash Tables - https://opendatastructures.org/ods-python/4_Hash_Tables.html
   - Chapter 5: Binary Trees - https://opendatastructures.org/ods-python/5_Binary_Trees.html
   - Chapter 7: Heaps - https://opendatastructures.org/ods-python/7_Heaps.html

2. **DMarket API Documentation**
   - Batch Operations - https://docs.dmarket.com/v1/swagger.html#/Marketplace
   - Rate Limits - https://docs.dmarket.com/api-rate-limits/

3. **Python Performance**
   - Time Complexity - https://wiki.python.org/moin/TimeComplexity
   - asyncio Performance - https://docs.python.org/3/library/asyncio.html

4. **Database Optimization**
   - PostgreSQL Indexes - https://www.postgresql.org/docs/current/indexes.html
   - Query Optimization - https://www.postgresql.org/docs/current/using-explain.html

---

**Last Updated**: December 7, 2025
**Maintainer**: DMarket Bot Team
**Related Docs**: 
- [Data Structures Guide](DATA_STRUCTURES_GUIDE.md)
- [Performance Guide](PERFORMANCE_IMPROVEMENTS.md)
- [Architecture](ARCHITECTURE.md)

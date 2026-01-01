# Performance Optimization Guide

## Overview

This guide provides strategies and techniques for optimizing the performance of the DMarket Telegram Bot.

---

## Table of Contents

1. [Performance Metrics](#performance-metrics)
2. [Profiling Tools](#profiling-tools)
3. [Optimization Strategies](#optimization-strategies)
4. [Caching](#caching)
5. [Database Optimization](#database-optimization)
6. [API Optimization](#api-optimization)
7. [Memory Management](#memory-management)
8. [Monitoring](#monitoring)

---

## Performance Metrics

### Key Metrics to Track

| Metric              | Target | Critical Threshold |
| ------------------- | ------ | ------------------ |
| API Response Time   | <200ms | >500ms             |
| Database Query Time | <50ms  | >200ms             |
| Memory Usage (RSS)  | <500MB | >1GB               |
| Cache Hit Rate      | >80%   | <60%               |
| Error Rate          | <1%    | >5%                |

### Measurement Tools
```bash
# API response time
time curl -X GET https://api.dmarket.com/...

# Memory usage
ps aux | grep python

# Database query time
EXPLAIN ANALYZE SELECT ...
```

---

## Profiling Tools

### 1. py-spy (Recommended)

**Installation:**
```bash
pip install py-spy
```

**Usage:**
```bash
# Record profile
py-spy record -o profile.svg -- python -m src.main

# Live profiling
py-spy top -- python -m src.main

# Profile specific function
py-spy record -f speedscope -o profile.json -- python -m pytest tests/
```

### 2. cProfile

**Usage:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
await scanner.scan_level("standard", "csgo")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### 3. memory_profiler

**Installation:**
```bash
pip install memory_profiler
```

**Usage:**
```python
from memory_profiler import profile

@profile
async def scan_arbitrage():
    # Function to profile
    pass
```

---

## Optimization Strategies

### 1. Async/Await Optimization

**❌ Bad - Sequential**
```python
async def fetch_data():
    items1 = await api.get_items("csgo")
    items2 = await api.get_items("dota2")
    items3 = await api.get_items("rust")
    return items1 + items2 + items3
```

**✅ Good - Parallel**
```python
async def fetch_data():
    tasks = [
        api.get_items("csgo"),
        api.get_items("dota2"),
        api.get_items("rust")
    ]
    results = await asyncio.gather(*tasks)
    return sum(results, [])
```

### 2. Batch Processing

**❌ Bad - One by One**
```python
async def process_items(items):
    results = []
    for item in items:
        result = await process_single_item(item)
        results.append(result)
    return results
```

**✅ Good - Batches**
```python
async def process_items(items, batch_size=100):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(*[
            process_single_item(item) for item in batch
        ])
        results.extend(batch_results)
    return results
```

### 3. Early Returns

**❌ Bad - Nested**
```python
async def check_item(item):
    if item.price > 0:
        if item.suggested_price > 0:
            if item.profit_margin > 3:
                return await process(item)
    return None
```

**✅ Good - Early Returns**
```python
async def check_item(item):
    if item.price <= 0:
        return None
    if item.suggested_price <= 0:
        return None
    if item.profit_margin <= 3:
        return None
    return await process(item)
```

---

## Caching

### 1. Redis Caching

**Implementation:**
```python
from aiocache import cached

@cached(ttl=300, key="market:items:{game}")
async def get_market_items(game: str):
    """Cache market items for 5 minutes."""
    return await api.get_items(game)
```

### 2. In-Memory Cache (TTLCache)

**Implementation:**
```python
from cachetools import TTLCache
import time

cache = TTLCache(maxsize=1000, ttl=300)

async def get_balance(user_id: int):
    """Get balance with 5-minute cache."""
    cache_key = f"balance:{user_id}"

    if cache_key in cache:
        return cache[cache_key]

    balance = await api.get_balance()
    cache[cache_key] = balance
    return balance
```

### 3. Query Result Cache

**Implementation:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user_settings(user_id: int):
    """Cache user settings in memory."""
    # This should be called from async context
    pass
```

### Cache Invalidation

**Strategies:**
1. **Time-based** (TTL) - Expire after X seconds
2. **Event-based** - Invalidate on update
3. **Size-based** - LRU eviction

**Example:**
```python
async def update_balance(user_id: int, new_balance: float):
    """Update balance and invalidate cache."""
    await db.update_balance(user_id, new_balance)

    # Invalidate cache
    cache_key = f"balance:{user_id}"
    if cache_key in cache:
        del cache[cache_key]
```

---

## Database Optimization

### 1. Indexing

**Add indexes for frequent queries:**
```sql
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_targets_user_id ON targets(user_id);
CREATE INDEX idx_targets_game ON targets(game);
CREATE INDEX idx_targets_created_at ON targets(created_at);
```

### 2. Query Optimization

**❌ Bad - N+1 Problem**
```python
async def get_users_with_targets():
    users = await db.get_all_users()
    for user in users:
        user.targets = await db.get_targets(user.id)
    return users
```

**✅ Good - Eager Loading**
```python
async def get_users_with_targets():
    return await db.query(User).options(
        joinedload(User.targets)
    ).all()
```

### 3. Connection Pooling

**Configuration:**
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://...",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 4. Batch Inserts

**❌ Bad - One by One**
```python
for item in items:
    await db.insert(item)
```

**✅ Good - Batch Insert**
```python
await db.bulk_insert(items)
```

---

## API Optimization

### 1. Connection Pooling

**httpx Configuration:**
```python
limits = httpx.Limits(
    max_keepalive_connections=20,
    max_connections=100,
    keepalive_expiry=30.0
)

client = httpx.AsyncClient(
    timeout=10.0,
    limits=limits,
    http2=True  # Enable HTTP/2
)
```

### 2. Request Batching

**Combine multiple requests:**
```python
async def fetch_multiple_items(item_ids: list[str]):
    """Fetch multiple items in one request."""
    return await api.post("/batch", json={"ids": item_ids})
```

### 3. Rate Limiting

**Implement smart rate limiting:**
```python
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(max_rate=30, time_period=60)

async def api_call():
    async with rate_limiter:
        return await api.get("/endpoint")
```

---

## Memory Management

### 1. Generator Patterns

**❌ Bad - Load All**
```python
async def process_all_items():
    items = await api.get_all_items()  # Loads 10,000 items
    for item in items:
        await process(item)
```

**✅ Good - Generator**
```python
async def process_all_items():
    async for item in api.stream_items():  # Stream items
        await process(item)
```

### 2. Memory Profiling

**Track memory usage:**
```python
import tracemalloc

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

### 3. Garbage Collection

**Manual GC for long-running tasks:**
```python
import gc

async def long_running_task():
    for i in range(1000):
        await process_batch(i)

        if i % 100 == 0:
            gc.collect()  # Force garbage collection
```

---

## Monitoring

### 1. Prometheus Metrics

**Setup:**
```python
from prometheus_client import Counter, Histogram

api_requests = Counter('api_requests_total', 'Total API requests')
api_latency = Histogram('api_latency_seconds', 'API latency')

async def api_call():
    api_requests.inc()

    with api_latency.time():
        return await api.get("/endpoint")
```

### 2. Custom Metrics

**Track custom metrics:**
```python
from dataclasses import dataclass
import time

@dataclass
class PerformanceMetrics:
    api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0

metrics = PerformanceMetrics()

# Track metrics
metrics.api_calls += 1
metrics.cache_hits += 1
```

### 3. Logging Performance

**Add performance logs:**
```python
import structlog

logger = structlog.get_logger(__name__)

async def expensive_operation():
    start = time.perf_counter()

    result = await do_work()

    elapsed = time.perf_counter() - start
    logger.info(
        "operation_complete",
        operation="expensive_operation",
        elapsed_ms=elapsed * 1000
    )

    return result
```

---

## Benchmarking

### Before and After Comparison

**Run benchmark:**
```bash
# Before optimization
python scripts/profile_scanner.py

# After optimization
python scripts/profile_scanner.py

# Compare results
```

**Example Results:**
```
Before:
- Scan time: 5.2s
- Memory: 850 MB
- API calls: 50

After:
- Scan time: 1.8s (-65%)
- Memory: 320 MB (-62%)
- API calls: 15 (-70%)
```

---

## Optimization Checklist

### Before Optimization
- [ ] Profile code to find bottlenecks
- [ ] Measure current performance
- [ ] Set optimization goals

### During Optimization
- [ ] Focus on biggest bottlenecks first
- [ ] Make one change at a time
- [ ] Measure after each change
- [ ] Keep code readable

### After Optimization
- [ ] Verify performance improved
- [ ] Run all tests
- [ ] Update documentation
- [ ] Monitor in production

---

## Common Pitfalls

### ❌ Avoid
1. **Premature optimization** - Profile first!
2. **Over-caching** - Cache invalidation is hard
3. **Too much parallelism** - Can overwhelm systems
4. **Ignoring memory** - Can cause crashes
5. **No monitoring** - Can't improve what you don't measure

### ✅ Follow
1. **Measure first** - Use profiling tools
2. **Optimize hot paths** - Focus on what matters
3. **Keep it simple** - Readable code is maintainable
4. **Test thoroughly** - Don't break functionality
5. **Monitor continuously** - Track metrics over time

---

## Resources

### Tools
- [py-spy](https://github.com/benfred/py-spy)
- [memory_profiler](https://pypi.org/project/memory-profiler/)
- [locust](https://locust.io/) - Load testing

### Reading
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [asyncio Performance](https://docs.python.org/3/library/asyncio-dev.html)

---

**Last Updated**: January 1, 2026
**Version**: 1.0.0

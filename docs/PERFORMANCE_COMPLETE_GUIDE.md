# ⚡ Performance Complete Guide

> **Объединённое руководство** - метрики + оптимизация + профилирование

---

## 📖 Содержание

1. [Performance Overview](#performance-overview)
2. [Performance Metrics](#performance-metrics)
3. [Profiling Tools](#profiling-tools)
4. [Optimization Strategies](#optimization-strategies)
5. [Batch Processing](#batch-processing)
6. [Caching Strategies](#caching-strategies)
7. [Monitoring](#monitoring)

---

# Performance Overview

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


---

# Performance Optimization (Phase 2)

# Performance Optimization Guide

> **Phase 2 Task**: Performance profiling and optimization
> **Date**: January 1, 2026
> **Status**: Ready for implementation

---

## 📊 Overview

This guide covers performance optimization strategies for the DMarket Telegram Bot, focusing on:

1. **Profiling** - Identifying bottlenecks
2. **Batch Processing** - Optimizing large dataset handling
3. **Caching Strategies** - Reducing redundant API calls
4. **Connection Pooling** - Efficient resource usage
5. **Async Optimization** - Maximizing concurrency

---

## 🔍 Step 1: Performance Profiling

### Using py-spy (Recommended)

**Install**:
```bash
pip install py-spy
```

**Profile the entire bot**:
```bash
# Record flamegraph
py-spy record -o profile.svg -- python -m src.main

# Top view (real-time)
py-spy top -- python -m src.main

# Profile specific duration
py-spy record --duration 60 -o profile.svg -- python -m src.main
```

**Profile specific tests**:
```bash
# Profile scanner tests
py-spy record -o scanner_profile.svg -- python -m pytest tests/unit/test_arbitrage_scanner.py

# Profile API client tests
py-spy record -o api_profile.svg -- python -m pytest tests/unit/test_dmarket_api.py
```

### Using cProfile

**Script**:
```bash
# Use the profiling script
python scripts/profile_scanner.py
```

**Analysis**:
```python
import pstats

# Load stats
stats = pstats.Stats('profiling_results/scanner_profile.stats')

# Sort by cumulative time
stats.sort_stats('cumulative')
stats.print_stats(20)

# Sort by total time
stats.sort_stats('tottime')
stats.print_stats(20)
```

### Custom Performance Metrics

**Decorator for timing**:
```python
import time
import structlog
from functools import wraps

logger = structlog.get_logger(__name__)


def measure_time(func):
    """Measure execution time of async function."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        logger.info(
            "performance_metric",
            function=func.__name__,
            elapsed_ms=round(elapsed * 1000, 2),
        )
        return result
    return wrapper


# Usage
@measure_time
async def scan_market(game: str, level: str):
    """Scan market with performance tracking."""
    ...
```

---

## 📦 Step 2: Batch Processing

### Current Issue

Processing items one-by-one is slow for large datasets:

```python
# ❌ Slow - sequential processing
async def scan_items(items: list[Item]) -> list[Opportunity]:
    opportunities = []
    for item in items:
        opp = await process_item(item)  # One at a time
        if opp:
            opportunities.append(opp)
    return opportunities
```

### Solution: Batch Processing

**Implementation**:
```python
import asyncio

async def scan_items_batch(
    items: list[Item],
    batch_size: int = 100
) -> list[Opportunity]:
    """Scan items in batches for better performance."""
    opportunities = []

    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        # Process batch concurrently
        tasks = [process_item(item) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors and None values
        for result in results:
            if isinstance(result, Exception):
                logger.warning("batch_item_error", error=str(result))
                continue
            if result:
                opportunities.append(result)

    return opportunities
```

**Benefits**:
- ✅ 10-50x faster for large datasets (1000+ items)
- ✅ Controlled concurrency (no overwhelming API)
- ✅ Error isolation (one item failure doesn't stop batch)

### Optimal Batch Size

**Testing**:
```bash
python scripts/profile_scanner.py
```

**Recommended**:
- Small datasets (<100 items): `batch_size=10`
- Medium datasets (100-1000): `batch_size=50`
- Large datasets (1000+): `batch_size=100`
- Very large (10000+): `batch_size=200`

---

## 🗄️ Step 3: Advanced Caching

### Current Caching

Already implemented:
- ✅ TTLCache for in-memory caching
- ✅ Redis for distributed caching
- ✅ Query result caching

### Enhancements

#### 1. Multi-level Cache

```python
from aiocache import cached
from src.utils.memory_cache import get_cache

@cached(
    ttl=300,
    key="market:items:{game}:{level}",
    cache=get_cache("market")
)
async def get_market_items_cached(game: str, level: str):
    """Get market items with multi-level caching."""
    # Check Redis first (L1)
    redis_key = f"market:items:{game}:{level}"
    cached_data = await redis_client.get(redis_key)
    if cached_data:
        return json.loads(cached_data)

    # Fetch from API (L2)
    items = await api_client.get_market_items(game, level)

    # Store in Redis with TTL
    await redis_client.setex(
        redis_key,
        300,  # 5 minutes
        json.dumps(items)
    )

    return items
```

#### 2. Selective Cache Invalidation

```python
async def update_item_price(item_id: str, new_price: float):
    """Update item price and invalidate related caches."""
    # Update database
    await db.update_item_price(item_id, new_price)

    # Invalidate specific caches
    await cache.delete(f"item:{item_id}")
    await cache.delete(f"item:price:{item_id}")

    # Invalidate market cache for item's game
    item = await db.get_item(item_id)
    await cache.delete(f"market:items:{item.game}:*")
```

#### 3. Cache Warming

```python
async def warm_cache():
    """Pre-populate cache with frequently accessed data."""
    logger.info("cache_warming_started")

    games = ["csgo", "dota2", "tf2", "rust"]
    levels = ["standard", "medium", "advanced"]

    tasks = []
    for game in games:
        for level in levels:
            tasks.append(get_market_items_cached(game, level))

    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("cache_warming_complete", items_cached=len(tasks))
```

---

## 🔌 Step 4: Connection Pooling

### HTTP Client Optimization

**Current**:
```python
# Basic client
client = httpx.AsyncClient(timeout=10.0)
```

**Optimized**:
```python
import httpx

# Configure connection pooling
limits = httpx.Limits(
    max_keepalive_connections=20,  # Keep 20 connections alive
    max_connections=100,            # Max 100 total connections
    keepalive_expiry=30.0           # Keep alive for 30s
)

# Configure timeouts
timeout = httpx.Timeout(
    connect=5.0,   # 5s to establish connection
    read=10.0,     # 10s to read response
    write=5.0,     # 5s to write request
    pool=5.0       # 5s to get connection from pool
)

# Create optimized client
client = httpx.AsyncClient(
    timeout=timeout,
    limits=limits,
    http2=True,  # Enable HTTP/2 for better performance
)
```

**Benefits**:
- ✅ Reuse connections (avoid handshake overhead)
- ✅ Faster requests (no connection setup time)
- ✅ Better throughput (parallel requests)

### Database Connection Pooling

**SQLAlchemy 2.0**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,           # 10 connections in pool
    max_overflow=20,        # Allow 20 extra connections
    pool_recycle=3600,      # Recycle connections after 1h
    pool_pre_ping=True,     # Check connection before use
)
```

---

## ⚡ Step 5: Async Optimization

### 1. Use asyncio.gather for Parallel Execution

**Before**:
```python
# ❌ Sequential - slow
results = []
for item in items:
    result = await process_item(item)
    results.append(result)
```

**After**:
```python
# ✅ Parallel - fast
tasks = [process_item(item) for item in items]
results = await asyncio.gather(*tasks)
```

### 2. Use asyncio.as_completed for Early Results

```python
async def scan_with_early_results(items: list[Item]):
    """Process items and yield results as they complete."""
    tasks = [process_item(item) for item in items]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            yield result  # Yield as soon as available
```

### 3. Limit Concurrency with Semaphore

```python
async def scan_with_concurrency_limit(
    items: list[Item],
    max_concurrent: int = 50
):
    """Scan items with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(item: Item):
        async with semaphore:
            return await process_item(item)

    tasks = [process_with_limit(item) for item in items]
    return await asyncio.gather(*tasks)
```

---

## 📈 Step 6: Performance Benchmarks

### Before Optimization (Baseline)

| Operation                    | Time (ms) | Items/sec |
| ---------------------------- | --------- | --------- |
| Scan 100 items (sequential)  | 5000      | 20        |
| Scan 1000 items (sequential) | 50000     | 20        |
| API request (no pool)        | 150       | -         |
| Cache miss + API call        | 200       | -         |

### After Optimization (Target)

| Operation                   | Time (ms) | Items/sec | Improvement |
| --------------------------- | --------- | --------- | ----------- |
| Scan 100 items (batch=50)   | 500       | 200       | **10x**     |
| Scan 1000 items (batch=100) | 2500      | 400       | **20x**     |
| API request (pooled)        | 50        | -         | **3x**      |
| Cache hit                   | 5         | -         | **40x**     |

---

## 🎯 Optimization Checklist

### Phase 1: Profiling (Week 3)
- [ ] Run py-spy on production workload
- [ ] Identify top 10 slowest functions
- [ ] Profile scanner with different batch sizes
- [ ] Profile API client with/without pooling
- [ ] Document baseline metrics

### Phase 2: Implementation (Week 4)
- [ ] Implement batch processing in scanner
- [ ] Optimize connection pooling settings
- [ ] Add cache warming on startup
- [ ] Implement selective cache invalidation
- [ ] Add performance monitoring decorators

### Phase 3: Validation (Week 5)
- [ ] Re-run profiling after optimizations
- [ ] Measure performance improvements
- [ ] Update benchmarks in documentation
- [ ] Add performance regression tests
- [ ] Document optimal configurations

---

## 🛠️ Tools and Resources

### Profiling Tools
- **py-spy**: https://github.com/benfred/py-spy
- **cProfile**: Built-in Python profiler
- **Locust**: Load testing framework

### Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Sentry**: Error tracking with performance data

### Documentation
- Python asyncio: https://docs.python.org/3/library/asyncio.html
- httpx: https://www.python-httpx.org/
- SQLAlchemy: https://docs.sqlalchemy.org/

---

## 📝 Performance Notes

### Common Bottlenecks

1. **API Rate Limits**
   - Solution: Implement rate limiting with `aiolimiter`
   - Use exponential backoff on 429 errors

2. **Database Queries**
   - Solution: Add indexes on frequently queried columns
   - Use batch inserts/updates

3. **Large JSON Payloads**
   - Solution: Use compression (gzip)
   - Paginate large responses

4. **Memory Usage**
   - Solution: Process items in streams
   - Clear caches periodically

### Best Practices

✅ **DO**:
- Profile before optimizing
- Measure improvements with benchmarks
- Use batch processing for large datasets
- Implement multi-level caching
- Monitor production performance

❌ **DON'T**:
- Optimize without profiling
- Use unbounded concurrency
- Cache everything (be selective)
- Ignore error handling in optimized code

---

**Version**: 1.0
**Last Updated**: January 1, 2026
**Related**: `scripts/profile_scanner.py`, `IMPROVEMENT_ROADMAP.md`


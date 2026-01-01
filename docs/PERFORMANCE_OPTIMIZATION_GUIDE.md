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

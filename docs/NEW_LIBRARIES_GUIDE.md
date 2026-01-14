# New Libraries Integration Guide

This document describes the new libraries integrated into the DMarket Telegram Bot project to improve retry handling and HTTP caching.

## Overview

Two new libraries have been integrated:

| Library | Purpose | Version |
|---------|---------|---------|
| **stamina** | Production-grade retry with exponential backoff | 25.2.0+ |
| **hishel** | RFC 9111-compliant HTTP caching for httpx | 1.1.8+ |

## Stamina - Production-Grade Retries

### Why Stamina?

Stamina is built on top of `tenacity` but provides:

- **Safe defaults**: Forces explicit exception specification
- **Exponential backoff with jitter**: Built-in to prevent thundering herd
- **Prometheus metrics**: Out-of-the-box instrumentation
- **Structlog integration**: For structured logging
- **Testing support**: Easy to disable retries in tests

### Usage Examples

#### Decorator Usage

```python
from src.utils.stamina_retry import api_retry
import httpx

@api_retry(attempts=3, on=httpx.HTTPError)
async def fetch_market_data():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.dmarket.com/items")
        resp.raise_for_status()
        return resp.json()
```

#### Context Manager Usage

```python
from src.utils.stamina_retry import retry_async
import httpx

async def fetch_with_context():
    async for attempt in retry_async(on=httpx.HTTPError, attempts=3):
        with attempt:
            async with httpx.AsyncClient() as client:
                return (await client.get(url)).json()
```

#### Disabling Retries in Tests

```python
from src.utils.stamina_retry import disabled_retries, async_disabled_retries

# Sync context
with disabled_retries():
    # Retries are disabled here
    result = api_call()

# Async context
async with async_disabled_retries():
    result = await async_api_call()
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `attempts` | 3 | Maximum number of retry attempts |
| `timeout` | 45.0 | Total timeout in seconds |
| `on` | DEFAULT_API_EXCEPTIONS | Exception types to retry on |

### Default Exceptions

```python
DEFAULT_API_EXCEPTIONS = (
    httpx.HTTPError,
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
    NetworkError,
    RateLimitError,
    ConnectionError,
    TimeoutError,
    APIError,
)
```

## Hishel - HTTP Caching

### Why Hishel?

Hishel provides RFC 9111-compliant HTTP caching:

- **Standards compliance**: Follows RFC 9111 caching rules
- **Async support**: Works with httpx.AsyncClient
- **Multiple backends**: SQLite, filesystem, memory
- **Transparent caching**: Response includes cache info

### Usage Examples

#### Basic Usage

```python
from src.utils.http_cache import create_cached_client, CacheConfig

config = CacheConfig(ttl=300)  # 5 minutes

async with create_cached_client(config) as client:
    # First request - from origin
    response = await client.get("https://api.dmarket.com/items")
    print(f"From cache: {client.is_from_cache(response)}")  # False

    # Second request - from cache
    response = await client.get("https://api.dmarket.com/items")
    print(f"From cache: {client.is_from_cache(response)}")  # True
```

#### Global Client (Singleton)

```python
from src.utils.http_cache import get_cached_client, close_cached_client

# Get or create global client
client = await get_cached_client()
response = await client.get(url)

# Clean up when done
await close_cached_client()
```

### Configuration Options

```python
@dataclass
class CacheConfig:
    ttl: int = 300  # 5 minutes
    always_cache: bool = False
    storage_type: CacheStorageType = CacheStorageType.MEMORY
    cache_dir: Path = Path(".cache/http")
    max_size: int = 100 * 1024 * 1024  # 100 MB
    cacheable_methods: tuple[str, ...] = ("GET", "HEAD")
    cacheable_status_codes: tuple[int, ...] = (200, 203, 300, 301, 308)
```

### Storage Types

| Type | Description | Best For |
|------|-------------|----------|
| `SQLITE` | Persistent SQLite database | Production |
| `FILESYSTEM` | File-based storage | Multi-process |
| `MEMORY` | In-memory (not for async) | Testing |

### Cache Statistics

```python
async with CachedHTTPClient(config) as client:
    # Make requests...

    # Get statistics
    print(f"Total requests: {client.stats.total_requests}")
    print(f"Cache hits: {client.stats.hits}")
    print(f"Cache misses: {client.stats.misses}")
    print(f"Hit rate: {client.stats.hit_rate}%")

    # Reset statistics
    client.reset_stats()
```

## Integration with Existing Code

### DMarket API Client

The new libraries can be integrated into the existing DMarket API client:

```python
from src.utils.stamina_retry import api_retry
from src.utils.http_cache import CachedHTTPClient, CacheConfig

class DMarketAPI:
    def __init__(self):
        self.cache_config = CacheConfig(ttl=60)  # 1 minute cache

    async def __aenter__(self):
        self._client = CachedHTTPClient(self.cache_config)
        await self._client.__aenter__()
        return self

    @api_retry(attempts=3)
    async def get_market_items(self, game: str = "csgo"):
        response = await self._client.get(
            f"https://api.dmarket.com/market/items?game={game}"
        )
        return response.json()
```

### Arbitrage Scanner

```python
from src.utils.stamina_retry import api_retry, retry_async

class ArbitrageScanner:
    @api_retry(attempts=5, timeout=60.0)
    async def scan_market(self, game: str, level: str):
        # Automatic retries with exponential backoff
        return await self.api.get_market_items(game, level)

    async def scan_with_progress(self, items: list):
        results = []
        async for attempt in retry_async(attempts=3):
            with attempt:
                # Process items with retry
                results = await self._process_batch(items)
        return results
```

## Testing

### Running Tests

```bash
# Test stamina retry module
pytest tests/utils/test_stamina_retry.py -v

# Test HTTP cache module
pytest tests/utils/test_http_cache.py -v

# Run both
pytest tests/utils/test_stamina_retry.py tests/utils/test_http_cache.py -v
```

### Mocking in Tests

```python
from src.utils.stamina_retry import disabled_retries

def test_api_call_without_retries():
    with disabled_retries():
        # API calls will fail immediately without retry
        with pytest.raises(httpx.HTTPError):
            await failing_api_call()
```

## Fallback Behavior

Both modules are designed with graceful degradation:

- **Stamina not installed**: Falls back to `tenacity`-based retry
- **Hishel not installed**: Falls back to regular `httpx.AsyncClient`

```python
from src.utils.stamina_retry import STAMINA_AVAILABLE
from src.utils.http_cache import HISHEL_AVAILABLE

if STAMINA_AVAILABLE:
    print("Using stamina for retries")
else:
    print("Using tenacity fallback")

if HISHEL_AVAILABLE:
    print("HTTP caching enabled")
else:
    print("HTTP caching disabled")
```

## Best Practices

### 1. Always Specify Exceptions

```python
# ✅ Good - explicit exception
@api_retry(on=httpx.HTTPError)
async def fetch():
    ...

# ❌ Bad - too broad
@api_retry(on=Exception)
async def fetch():
    ...
```

### 2. Use Appropriate TTL

```python
# Short TTL for frequently changing data
price_cache = CacheConfig(ttl=30)  # 30 seconds

# Longer TTL for stable data
metadata_cache = CacheConfig(ttl=3600)  # 1 hour
```

### 3. Disable Retries in Tests

```python
@pytest.fixture
def no_retries():
    with disabled_retries():
        yield
```

### 4. Monitor Cache Hit Rate

```python
if client.stats.hit_rate < 50:
    logger.warning("Low cache hit rate, consider increasing TTL")
```

## References

- [Stamina Documentation](https://stamina.hynek.me/)
- [Hishel Documentation](https://hishel.com/)
- [RFC 9111 - HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)
- [httpx Documentation](https://www.python-httpx.org/)

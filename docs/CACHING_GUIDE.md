# Caching and Performance Guide

**Last updated: January 2026**
**Status**: ✅ Production Ready

---

## 📋 Overview

This guide covers the caching infrastructure in DMarket Telegram Bot.

See ERROR_HANDLING_GUIDE.md for retry and error handling.

---

## 🗄️ Available Caches

### 1. In-Memory Cache (TTLCache)
- **Module**: `src/utils/memory_cache.py`
- **Use for**: Single instance, hot data, temporary results
- **Features**: TTL, LRU eviction, auto-cleanup

### 2. Redis Cache (RedisCache) 
- **Module**: `src/utils/redis_cache.py`
- **Use for**: Multi-instance, distributed, shared data
- **Features**: TTL, fallback to memory, atomic operations

### 3. HTTP Response Cache (Hishel) 🆕
- **Module**: `src/utils/http_cache.py`
- **Use for**: Caching HTTP API responses
- **Features**: RFC 9111-compliant, SQLite storage, automatic TTL

```python
from src.utils.http_cache import CachedHTTPClient, CacheConfig

config = CacheConfig(ttl=300)  # 5 minutes

async with CachedHTTPClient(config) as client:
    response = await client.get("https://api.dmarket.com/items")
    is_cached = client.is_from_cache(response)
```

---

## 📚 Documentation

For detailed usage, see the inline documentation in:
- `src/utils/memory_cache.py`
- `src/utils/redis_cache.py`
- `src/utils/http_cache.py` 🆕
- Test examples in `tests/utils/test_redis_cache.py`
- Test examples in `tests/utils/test_http_cache.py` 🆕

---

## 🆕 Enhanced API Integration

The new `enhanced_api` module provides integration helpers:

```python
from src.utils.enhanced_api import (
    EnhancedAPIConfig,
    create_enhanced_http_client,
    get_api_enhancement_status,
)

# Check available enhancements
status = get_api_enhancement_status()
print(f"HTTP caching available: {status['hishel']['available']}")

# Create enhanced client
client = await create_enhanced_http_client(
    enable_caching=True,
    cache_ttl=300,
)
```

---

**Version**: 2.0.0
**Last Review**: January 14, 2026

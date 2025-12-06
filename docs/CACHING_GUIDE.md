# Caching and Performance Guide

**Last updated**: December 4, 2025  
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

---

## 📚 Documentation

For detailed usage, see the inline documentation in:
- `src/utils/memory_cache.py`
- `src/utils/redis_cache.py`
- Test examples in `tests/utils/test_redis_cache.py`

---

**Version**: 1.0  
**Last Review**: December 4, 2025

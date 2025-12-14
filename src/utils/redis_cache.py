"""Redis-based distributed cache for DMarket Bot.

This module provides a Redis-backed cache implementation for distributed
caching across multiple bot instances, with TTL support and async operations.
"""

import logging
import pickle
from typing import Any, cast


try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None  # type: ignore[assignment]

from src.utils.memory_cache import TTLCache


logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based distributed cache with TTL support.

    Features:
    - Distributed caching across multiple instances
    - TTL (Time To Live) support
    - Async operations
    - Automatic fallback to in-memory cache if Redis unavailable
    - Pickle serialization for complex objects
    """

    def __init__(
        self,
        redis_url: str | None = None,
        default_ttl: int = 300,
        fallback_to_memory: bool = True,
        max_memory_size: int = 1000,
    ):
        """Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (redis://localhost:6379/0)
            default_ttl: Default TTL in seconds (default: 300 = 5 minutes)
            fallback_to_memory: Use in-memory cache if Redis unavailable
            max_memory_size: Max size for fallback memory cache
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: aioredis.Redis[bytes] | None = None
        self._connected = False

        # Fallback to in-memory cache
        self._fallback_enabled = fallback_to_memory
        self._memory_cache: TTLCache | None = None
        if fallback_to_memory:
            self._memory_cache = TTLCache(
                max_size=max_memory_size,
                default_ttl=default_ttl,
            )

        # Statistics
        self._hits = 0
        self._misses = 0
        self._errors = 0

    async def connect(self) -> bool:
        """Connect to Redis server.

        Returns:
            True if connected successfully, False otherwise
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available. Install with: pip install redis[hiredis]")
            if self._fallback_enabled:
                logger.info("Falling back to in-memory cache")
                return False
            raise RuntimeError("Redis not available and fallback disabled")

        if not self.redis_url:
            logger.warning("Redis URL not configured. Using in-memory cache")
            return False

        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding ourselves
            )

            # Test connection
            await self._redis.ping()

            self._connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False

            if not self._fallback_enabled:
                raise

            logger.info("Falling back to in-memory cache")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")

        if self._memory_cache:
            await self._memory_cache.stop_cleanup()

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Try Redis first
        if self._connected and self._redis:
            try:
                value = await self._redis.get(key)
                if value is not None:
                    self._hits += 1
                    return pickle.loads(value)
                self._misses += 1
                return None
            except Exception as e:
                logger.error(f"Redis get error for key {key}: {e}")
                self._errors += 1
                # Fall through to memory cache

        # Fallback to memory cache
        if self._memory_cache:
            value = await self._memory_cache.get(key)
            if value is not None:
                self._hits += 1
            else:
                self._misses += 1
            return value

        self._misses += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = use default)

        Returns:
            True if successful, False otherwise
        """
        ttl = ttl or self.default_ttl

        # Try Redis first
        if self._connected and self._redis:
            try:
                serialized = pickle.dumps(value)
                await self._redis.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error for key {key}: {e}")
                self._errors += 1
                # Fall through to memory cache

        # Fallback to memory cache
        if self._memory_cache:
            await self._memory_cache.set(key, value, ttl)
            return True

        return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        success = False

        # Delete from Redis
        if self._connected and self._redis:
            try:
                result = await self._redis.delete(key)
                success = result > 0
            except Exception as e:
                logger.error(f"Redis delete error for key {key}: {e}")
                self._errors += 1

        # Delete from memory cache
        if self._memory_cache:
            await self._memory_cache.delete(key)
            success = True

        return success

    async def clear(self, pattern: str | None = None) -> int:
        """Clear cache entries.

        Args:
            pattern: Pattern to match keys (e.g., "market:*")
                    If None, clears all keys

        Returns:
            Number of keys deleted
        """
        count = 0

        # Clear from Redis
        if self._connected and self._redis:
            try:
                if pattern:
                    keys = await self._redis.keys(pattern)
                    if keys:
                        count = await self._redis.delete(*keys)
                else:
                    await self._redis.flushdb()
                    count = 1  # Indicate success
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
                self._errors += 1

        # Clear from memory cache
        if self._memory_cache:
            if pattern:
                # Memory cache doesn't support patterns, clear all
                await self._memory_cache.clear()
            else:
                await self._memory_cache.clear()

        return count

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        # Check Redis
        if self._connected and self._redis:
            try:
                return bool(await self._redis.exists(key))
            except Exception as e:
                logger.error(f"Redis exists error for key {key}: {e}")
                self._errors += 1

        # Check memory cache
        if self._memory_cache:
            value = await self._memory_cache.get(key)
            return value is not None

        return False

    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl: int | None = None,
    ) -> int:
        """Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by
            ttl: TTL in seconds (None = use default)

        Returns:
            New value after increment
        """
        ttl = ttl or self.default_ttl

        # Use Redis if available (atomic increment)
        if self._connected and self._redis:
            try:
                pipeline = self._redis.pipeline()
                pipeline.incrby(key, amount)
                pipeline.expire(key, ttl)
                results = await pipeline.execute()
                return cast("int", results[0])
            except Exception as e:
                logger.error(f"Redis increment error for key {key}: {e}")
                self._errors += 1

        # Fallback to memory cache (non-atomic)
        if self._memory_cache:
            current = await self._memory_cache.get(key) or 0
            new_value = current + amount
            await self._memory_cache.set(key, new_value, ttl)
            return new_value

        return amount

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        stats: dict[str, Any] = {
            "connected": self._connected,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "fallback_enabled": self._fallback_enabled,
        }

        # Add memory cache stats if available
        if self._memory_cache:
            stats["memory_cache"] = await self._memory_cache.get_stats()

        return stats

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on cache.

        Returns:
            Health check results
        """
        health: dict[str, Any] = {
            "redis_connected": False,
            "redis_ping": False,
            "memory_cache_available": self._memory_cache is not None,
        }

        if self._connected and self._redis:
            try:
                pong = await self._redis.ping()
                health["redis_connected"] = True
                health["redis_ping"] = pong
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                health["error"] = str(e)

        return health


# Global cache instance (initialized in main.py)
_global_cache: RedisCache | None = None


def get_cache() -> RedisCache:
    """Get global cache instance.

    Returns:
        Global RedisCache instance

    Raises:
        RuntimeError: If cache not initialized
    """
    if _global_cache is None:
        raise RuntimeError("Cache not initialized. Call init_cache() first in main.py")
    return _global_cache


async def init_cache(
    redis_url: str | None = None,
    default_ttl: int = 300,
) -> RedisCache:
    """Initialize global cache instance.

    Args:
        redis_url: Redis connection URL
        default_ttl: Default TTL in seconds

    Returns:
        Initialized RedisCache instance
    """
    global _global_cache

    _global_cache = RedisCache(
        redis_url=redis_url,
        default_ttl=default_ttl,
        fallback_to_memory=True,
    )

    await _global_cache.connect()

    logger.info("Global cache initialized")

    return _global_cache


async def close_cache() -> None:
    """Close global cache instance."""
    global _global_cache

    if _global_cache:
        await _global_cache.disconnect()
        _global_cache = None
        logger.info("Global cache closed")

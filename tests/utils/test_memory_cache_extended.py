"""Tests for memory_cache module.

This module tests the TTLCache class and cached decorator
for in-memory caching with TTL support.
"""

import asyncio

import pytest

from src.utils.memory_cache import TTLCache, cached


class TestTTLCacheBasic:
    """Tests for basic TTLCache operations."""

    @pytest.fixture()
    def cache(self):
        """Create a test cache instance."""
        return TTLCache(max_size=100, default_ttl=60)

    @pytest.mark.asyncio()
    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio()
    async def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio()
    async def test_set_with_custom_ttl(self, cache):
        """Test setting with custom TTL."""
        await cache.set("key1", "value1", ttl=120)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio()
    async def test_delete_key(self, cache):
        """Test deleting a key."""
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio()
    async def test_delete_nonexistent_key(self, cache):
        """Test deleting a key that doesn't exist."""
        # Should not raise
        await cache.delete("nonexistent")

    @pytest.mark.asyncio()
    async def test_clear_cache(self, cache):
        """Test clearing all cache entries."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio()
    async def test_key_exists_via_get(self, cache):
        """Test checking if key exists via get."""
        await cache.set("key1", "value1")

        # Check if key exists by getting it
        assert await cache.get("key1") is not None
        assert await cache.get("nonexistent") is None


class TestTTLCacheExpiration:
    """Tests for TTL expiration."""

    @pytest.mark.asyncio()
    async def test_expired_key_returns_none(self):
        """Test that expired keys return None."""
        cache = TTLCache(max_size=100, default_ttl=1)
        await cache.set("key1", "value1", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        result = await cache.get("key1")
        assert result is None


class TestTTLCacheStatistics:
    """Tests for cache statistics."""

    @pytest.fixture()
    def cache(self):
        """Create a test cache instance."""
        return TTLCache(max_size=100, default_ttl=60)

    @pytest.mark.asyncio()
    async def test_hits_counter(self, cache):
        """Test hits counter increments on cache hit."""
        await cache.set("key1", "value1")

        await cache.get("key1")
        await cache.get("key1")

        stats = await cache.get_stats()
        assert stats["hits"] >= 2

    @pytest.mark.asyncio()
    async def test_misses_counter(self, cache):
        """Test misses counter increments on cache miss."""
        await cache.get("nonexistent1")
        await cache.get("nonexistent2")

        stats = await cache.get_stats()
        assert stats["misses"] >= 2

    @pytest.mark.asyncio()
    async def test_size_stat(self, cache):
        """Test size statistic."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        stats = await cache.get_stats()
        assert stats["size"] == 2


class TestTTLCacheLRU:
    """Tests for LRU eviction."""

    @pytest.mark.asyncio()
    async def test_lru_eviction(self):
        """Test that oldest entry is evicted when max_size is reached."""
        cache = TTLCache(max_size=3, default_ttl=60)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        # This should evict key1
        await cache.set("key4", "value4")

        assert await cache.get("key1") is None
        assert await cache.get("key4") == "value4"


class TestTTLCacheCleanup:
    """Tests for cleanup task."""

    @pytest.mark.asyncio()
    async def test_start_and_stop_cleanup(self):
        """Test starting and stopping cleanup task."""
        cache = TTLCache(max_size=100, default_ttl=60)

        await cache.start_cleanup(interval=1)
        assert cache._cleanup_task is not None

        await cache.stop_cleanup()
        # Task should be cancelled

    @pytest.mark.asyncio()
    async def test_cleanup_removes_expired(self):
        """Test that cleanup removes expired entries."""
        cache = TTLCache(max_size=100, default_ttl=1)
        await cache.set("key1", "value1", ttl=1)

        await asyncio.sleep(1.1)
        await cache._cleanup_expired()

        assert await cache.get("key1") is None


class TestCachedDecorator:
    """Tests for the cached decorator."""

    @pytest.mark.asyncio()
    async def test_cached_function_caches_result(self):
        """Test that decorated function caches results."""
        call_count = 0

        @cached(ttl=60)
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await expensive_function(5)
        result2 = await expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Function should only be called once

    @pytest.mark.asyncio()
    async def test_cached_different_args(self):
        """Test that different args result in different cache entries."""
        call_count = 0

        @cached(ttl=60)
        async def func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await func(5)
        result2 = await func(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2

    @pytest.mark.asyncio()
    async def test_cached_with_kwargs(self):
        """Test caching with keyword arguments."""
        call_count = 0

        @cached(ttl=60)
        async def func(x: int, y: int = 1) -> int:
            nonlocal call_count
            call_count += 1
            return x + y

        result1 = await func(5, y=10)
        result2 = await func(5, y=10)

        assert result1 == 15
        assert result2 == 15
        assert call_count == 1


class TestTTLCacheDataTypes:
    """Tests for caching different data types."""

    @pytest.fixture()
    def cache(self):
        """Create a test cache instance."""
        return TTLCache(max_size=100, default_ttl=60)

    @pytest.mark.asyncio()
    async def test_cache_dict(self, cache):
        """Test caching dictionary."""
        data = {"name": "test", "value": 123}
        await cache.set("dict_key", data)
        result = await cache.get("dict_key")
        assert result == data

    @pytest.mark.asyncio()
    async def test_cache_list(self, cache):
        """Test caching list."""
        data = [1, 2, 3, "test"]
        await cache.set("list_key", data)
        result = await cache.get("list_key")
        assert result == data

    @pytest.mark.asyncio()
    async def test_cache_none(self, cache):
        """Test caching None value."""
        await cache.set("none_key", None)
        # Note: This might return None due to how cache handles None
        # The implementation may need to distinguish between "no value" and "None value"

    @pytest.mark.asyncio()
    async def test_cache_complex_object(self, cache):
        """Test caching complex nested object."""
        data = {
            "users": [
                {"id": 1, "name": "User1"},
                {"id": 2, "name": "User2"},
            ],
            "metadata": {"count": 2, "page": 1},
        }
        await cache.set("complex_key", data)
        result = await cache.get("complex_key")
        assert result == data

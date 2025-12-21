"""Comprehensive tests for scanner/cache.py module.

This module provides tests for:
- ScannerCache class initialization and configuration
- Cache get/set operations with TTL
- Cache eviction and invalidation
- Cache statistics tracking
- Cache key generation
- Edge cases and error handling

Coverage target: 80%+ (from 25.76%)
"""

import time
from typing import Any
from unittest.mock import patch

import pytest

from src.dmarket.scanner.cache import ScannerCache, generate_cache_key


class TestScannerCacheInit:
    """Tests for ScannerCache initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        cache = ScannerCache()

        assert cache.ttl == 300
        assert cache._max_size == 1000
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._evictions == 0
        assert len(cache._cache) == 0

    def test_init_with_custom_ttl(self):
        """Test initialization with custom TTL."""
        cache = ScannerCache(ttl=600)

        assert cache.ttl == 600

    def test_init_with_custom_max_size(self):
        """Test initialization with custom max size."""
        cache = ScannerCache(max_size=500)

        assert cache._max_size == 500

    def test_init_with_zero_ttl(self):
        """Test initialization with zero TTL."""
        cache = ScannerCache(ttl=0)

        assert cache.ttl == 0

    def test_init_with_small_max_size(self):
        """Test initialization with small max size."""
        cache = ScannerCache(max_size=1)

        assert cache._max_size == 1


class TestScannerCacheTTLProperty:
    """Tests for TTL property getter and setter."""

    def test_ttl_getter(self):
        """Test TTL property getter."""
        cache = ScannerCache(ttl=120)

        assert cache.ttl == 120

    def test_ttl_setter_valid_value(self):
        """Test TTL setter with valid value."""
        cache = ScannerCache()
        cache.ttl = 600

        assert cache.ttl == 600

    def test_ttl_setter_zero(self):
        """Test TTL setter with zero value."""
        cache = ScannerCache()
        cache.ttl = 0

        assert cache.ttl == 0

    def test_ttl_setter_negative_raises_error(self):
        """Test TTL setter raises error for negative value."""
        cache = ScannerCache()

        with pytest.raises(ValueError, match="TTL must be non-negative"):
            cache.ttl = -1


class TestScannerCacheMakeKey:
    """Tests for _make_key method."""

    def test_make_key_string_input(self):
        """Test _make_key with string input."""
        cache = ScannerCache()

        result = cache._make_key("test_key")

        assert result == "test_key"

    def test_make_key_tuple_input(self):
        """Test _make_key with tuple input."""
        cache = ScannerCache()

        result = cache._make_key(("game", "level", 123))

        assert result == "game_level_123"

    def test_make_key_single_element_tuple(self):
        """Test _make_key with single element tuple."""
        cache = ScannerCache()

        result = cache._make_key(("single",))

        assert result == "single"

    def test_make_key_empty_tuple(self):
        """Test _make_key with empty tuple."""
        cache = ScannerCache()

        result = cache._make_key(())

        assert result == ""

    def test_make_key_mixed_types_tuple(self):
        """Test _make_key with mixed types in tuple."""
        cache = ScannerCache()

        result = cache._make_key(("game", 123, 45.67, True))

        assert result == "game_123_45.67_True"


class TestScannerCacheGet:
    """Tests for get method."""

    def test_get_non_existent_key(self):
        """Test get returns None for non-existent key."""
        cache = ScannerCache()

        result = cache.get("non_existent")

        assert result is None
        assert cache._misses == 1

    def test_get_existing_key(self):
        """Test get returns cached value for existing key."""
        cache = ScannerCache(ttl=300)
        items = [{"id": 1, "name": "item1"}]
        cache.set("test_key", items)

        result = cache.get("test_key")

        assert result == items
        assert cache._hits == 1

    def test_get_expired_key(self):
        """Test get returns None for expired key."""
        cache = ScannerCache(ttl=0)  # Immediate expiration
        items = [{"id": 1}]
        cache.set("test_key", items)

        # Small delay to ensure expiration
        time.sleep(0.01)
        result = cache.get("test_key")

        assert result is None
        assert cache._misses == 1
        assert cache._evictions == 1

    def test_get_with_tuple_key(self):
        """Test get with tuple key."""
        cache = ScannerCache(ttl=300)
        items = [{"id": 2}]
        cache.set(("game", "level"), items)

        result = cache.get(("game", "level"))

        assert result == items

    def test_get_updates_statistics(self):
        """Test get correctly updates hit/miss statistics."""
        cache = ScannerCache(ttl=300)
        cache.set("key1", [{"id": 1}])

        # Hit
        cache.get("key1")
        assert cache._hits == 1
        assert cache._misses == 0

        # Miss
        cache.get("non_existent")
        assert cache._hits == 1
        assert cache._misses == 1


class TestScannerCacheSet:
    """Tests for set method."""

    def test_set_basic(self):
        """Test basic set operation."""
        cache = ScannerCache()
        items = [{"id": 1, "name": "test"}]

        cache.set("test_key", items)

        assert "test_key" in cache._cache
        assert cache._cache["test_key"][0] == items

    def test_set_overwrites_existing(self):
        """Test set overwrites existing entry."""
        cache = ScannerCache()
        items1 = [{"id": 1}]
        items2 = [{"id": 2}]

        cache.set("test_key", items1)
        cache.set("test_key", items2)

        result = cache.get("test_key")
        assert result == items2

    def test_set_with_tuple_key(self):
        """Test set with tuple key."""
        cache = ScannerCache()
        items = [{"id": 3}]

        cache.set(("game", "level", "filter"), items)

        result = cache.get(("game", "level", "filter"))
        assert result == items

    def test_set_triggers_eviction_when_full(self):
        """Test set triggers eviction when cache is full."""
        cache = ScannerCache(max_size=2)
        cache.set("key1", [{"id": 1}])
        cache.set("key2", [{"id": 2}])

        # This should trigger eviction
        cache.set("key3", [{"id": 3}])

        assert len(cache._cache) == 2
        assert cache._evictions >= 1

    def test_set_empty_items_list(self):
        """Test set with empty items list."""
        cache = ScannerCache()

        cache.set("empty_key", [])

        result = cache.get("empty_key")
        assert result == []

    def test_set_large_items_list(self):
        """Test set with large items list."""
        cache = ScannerCache()
        items = [{"id": i, "data": "x" * 100} for i in range(100)]

        cache.set("large_key", items)

        result = cache.get("large_key")
        assert len(result) == 100


class TestScannerCacheEvictOldest:
    """Tests for _evict_oldest method."""

    def test_evict_oldest_removes_oldest_entry(self):
        """Test _evict_oldest removes the oldest entry."""
        cache = ScannerCache()

        # Add entries with slight time differences
        cache._cache["key1"] = ([{"id": 1}], 100.0)
        cache._cache["key2"] = ([{"id": 2}], 200.0)
        cache._cache["key3"] = ([{"id": 3}], 150.0)

        cache._evict_oldest()

        assert "key1" not in cache._cache
        assert "key2" in cache._cache
        assert "key3" in cache._cache
        assert cache._evictions == 1

    def test_evict_oldest_empty_cache(self):
        """Test _evict_oldest does nothing on empty cache."""
        cache = ScannerCache()

        # Should not raise
        cache._evict_oldest()

        assert cache._evictions == 0


class TestScannerCacheClear:
    """Tests for clear method."""

    def test_clear_empties_cache(self):
        """Test clear removes all entries."""
        cache = ScannerCache()
        cache.set("key1", [{"id": 1}])
        cache.set("key2", [{"id": 2}])

        cache.clear()

        assert len(cache._cache) == 0

    def test_clear_empty_cache(self):
        """Test clear on empty cache."""
        cache = ScannerCache()

        # Should not raise
        cache.clear()

        assert len(cache._cache) == 0


class TestScannerCacheInvalidate:
    """Tests for invalidate method."""

    def test_invalidate_all_with_none_pattern(self):
        """Test invalidate with None pattern clears all."""
        cache = ScannerCache()
        cache.set("key1", [{"id": 1}])
        cache.set("key2", [{"id": 2}])

        count = cache.invalidate(None)

        assert count == 2
        assert len(cache._cache) == 0

    def test_invalidate_with_pattern(self):
        """Test invalidate with pattern removes matching entries."""
        cache = ScannerCache()
        cache.set("game_csgo_boost", [{"id": 1}])
        cache.set("game_csgo_standard", [{"id": 2}])
        cache.set("game_dota_boost", [{"id": 3}])

        count = cache.invalidate("csgo")

        assert count == 2
        assert "game_csgo_boost" not in cache._cache
        assert "game_csgo_standard" not in cache._cache
        assert "game_dota_boost" in cache._cache

    def test_invalidate_no_matches(self):
        """Test invalidate with pattern that matches nothing."""
        cache = ScannerCache()
        cache.set("key1", [{"id": 1}])
        cache.set("key2", [{"id": 2}])

        count = cache.invalidate("nonexistent")

        assert count == 0
        assert len(cache._cache) == 2

    def test_invalidate_updates_eviction_count(self):
        """Test invalidate updates eviction statistics."""
        cache = ScannerCache()
        cache.set("match_1", [{"id": 1}])
        cache.set("match_2", [{"id": 2}])

        cache.invalidate("match")

        assert cache._evictions == 2


class TestScannerCacheGetStatistics:
    """Tests for get_statistics method."""

    def test_get_statistics_initial(self):
        """Test get_statistics returns initial values."""
        cache = ScannerCache(ttl=300, max_size=1000)

        stats = cache.get_statistics()

        assert stats["size"] == 0
        assert stats["max_size"] == 1000
        assert stats["ttl"] == 300
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0

    def test_get_statistics_after_operations(self):
        """Test get_statistics after cache operations."""
        cache = ScannerCache(ttl=300)
        cache.set("key1", [{"id": 1}])
        cache.set("key2", [{"id": 2}])

        # Generate hits and misses
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.get_statistics()

        assert stats["size"] == 2
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        # hit_rate = 2 / (2 + 1) * 100 = 66.67
        assert stats["hit_rate"] == 66.67

    def test_get_statistics_hit_rate_calculation(self):
        """Test hit rate calculation."""
        cache = ScannerCache()
        cache.set("key1", [{"id": 1}])

        # 3 hits, 1 miss = 75% hit rate
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_statistics()

        assert stats["hit_rate"] == 75.0


class TestScannerCacheLen:
    """Tests for __len__ method."""

    def test_len_empty_cache(self):
        """Test len returns 0 for empty cache."""
        cache = ScannerCache()

        assert len(cache) == 0

    def test_len_with_items(self):
        """Test len returns correct count."""
        cache = ScannerCache()
        cache.set("key1", [{"id": 1}])
        cache.set("key2", [{"id": 2}])
        cache.set("key3", [{"id": 3}])

        assert len(cache) == 3


class TestScannerCacheContains:
    """Tests for __contains__ method."""

    def test_contains_existing_key(self):
        """Test __contains__ returns True for existing key."""
        cache = ScannerCache(ttl=300)
        cache.set("existing", [{"id": 1}])

        assert "existing" in cache

    def test_contains_non_existing_key(self):
        """Test __contains__ returns False for non-existing key."""
        cache = ScannerCache()

        assert "nonexistent" not in cache

    def test_contains_expired_key(self):
        """Test __contains__ returns False for expired key."""
        cache = ScannerCache(ttl=0)
        cache.set("expired", [{"id": 1}])

        time.sleep(0.01)

        assert "expired" not in cache

    def test_contains_with_tuple_key(self):
        """Test __contains__ with tuple key."""
        cache = ScannerCache(ttl=300)
        cache.set(("game", "level"), [{"id": 1}])

        assert ("game", "level") in cache


class TestGenerateCacheKey:
    """Tests for generate_cache_key function."""

    def test_generate_cache_key_basic(self):
        """Test basic cache key generation."""
        result = generate_cache_key("boost", "csgo")

        assert result == "scanner:boost:csgo"

    def test_generate_cache_key_with_extra(self):
        """Test cache key generation with extra params."""
        result = generate_cache_key(
            "standard",
            "dota2",
            extra={"min_profit": 5, "max_price": 100},
        )

        # Extra params should be sorted alphabetically
        assert "scanner:standard:dota2" in result
        assert "max_price=100" in result
        assert "min_profit=5" in result

    def test_generate_cache_key_no_extra(self):
        """Test cache key generation without extra params."""
        result = generate_cache_key("medium", "rust", extra=None)

        assert result == "scanner:medium:rust"

    def test_generate_cache_key_empty_extra(self):
        """Test cache key generation with empty extra dict."""
        result = generate_cache_key("advanced", "tf2", extra={})

        assert result == "scanner:advanced:tf2"

    def test_generate_cache_key_sorted_extra(self):
        """Test that extra params are sorted alphabetically."""
        result = generate_cache_key(
            "pro",
            "csgo",
            extra={"z_param": 1, "a_param": 2, "m_param": 3},
        )

        # Should be sorted: a_param, m_param, z_param
        assert "a_param=2" in result
        parts = result.split(":")
        # The extra params part should have sorted order
        extra_parts = [p for p in parts if "=" in p]
        assert extra_parts == ["a_param=2", "m_param=3", "z_param=1"]


class TestScannerCacheEdgeCases:
    """Edge case tests for ScannerCache."""

    def test_cache_with_special_characters_in_key(self):
        """Test cache with special characters in key."""
        cache = ScannerCache(ttl=300)
        items = [{"id": 1}]

        cache.set("key:with:colons", items)
        result = cache.get("key:with:colons")

        assert result == items

    def test_cache_with_unicode_in_items(self):
        """Test cache with unicode characters in items."""
        cache = ScannerCache(ttl=300)
        items = [{"name": "АК-47 | Редлайн", "price": 100}]

        cache.set("unicode_key", items)
        result = cache.get("unicode_key")

        assert result == items
        assert result[0]["name"] == "АК-47 | Редлайн"

    def test_cache_concurrent_access_simulation(self):
        """Test cache behavior with rapid sequential access."""
        cache = ScannerCache(ttl=300)

        # Simulate rapid access
        for i in range(100):
            cache.set(f"key_{i}", [{"id": i}])

        for i in range(100):
            result = cache.get(f"key_{i}")
            assert result == [{"id": i}]

        assert cache._hits == 100
        assert cache._misses == 0

    def test_cache_eviction_order(self):
        """Test that oldest entries are evicted first."""
        cache = ScannerCache(max_size=3)

        # Insert with controlled timestamps
        cache._cache["first"] = ([{"id": 1}], 100.0)
        cache._cache["second"] = ([{"id": 2}], 200.0)
        cache._cache["third"] = ([{"id": 3}], 300.0)

        # This should evict "first" (oldest)
        cache.set("fourth", [{"id": 4}])

        assert "first" not in cache._cache
        assert "second" in cache._cache
        assert "third" in cache._cache
        assert "fourth" in cache._cache

    def test_cache_get_after_ttl_change(self):
        """Test cache behavior when TTL is changed after set."""
        cache = ScannerCache(ttl=300)
        cache.set("test_key", [{"id": 1}])

        # Change TTL to 0
        cache.ttl = 0

        # Entry should now be expired
        time.sleep(0.01)
        result = cache.get("test_key")

        assert result is None

    def test_cache_statistics_reset_not_supported(self):
        """Test that statistics are not reset by clear."""
        cache = ScannerCache()
        cache.set("key1", [{"id": 1}])
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        cache.clear()

        stats = cache.get_statistics()
        # Statistics should persist after clear
        assert stats["hits"] == 1
        assert stats["misses"] == 1

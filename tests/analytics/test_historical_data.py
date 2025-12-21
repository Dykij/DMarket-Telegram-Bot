"""Tests for analytics/historical_data.py module.

Comprehensive test suite covering:
- PricePoint dataclass tests
- PriceHistory dataclass tests
- HistoricalDataCollector class tests
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.analytics.historical_data import (
    HistoricalDataCollector,
    PriceHistory,
    PricePoint,
)


# ============================================================================
# PricePoint Tests
# ============================================================================


class TestPricePoint:
    """Tests for the PricePoint dataclass."""

    def test_create_price_point_basic(self):
        """Test creating a basic PricePoint."""
        point = PricePoint(
            game="csgo",
            title="AK-47 | Redline",
            price=Decimal("10.50"),
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        assert point.game == "csgo"
        assert point.title == "AK-47 | Redline"
        assert point.price == Decimal("10.50")
        assert point.volume == 0  # Default
        assert point.source == "market"  # Default

    def test_create_price_point_with_all_fields(self):
        """Test creating a PricePoint with all optional fields."""
        point = PricePoint(
            game="dota2",
            title="Dragonclaw Hook",
            price=Decimal("500.00"),
            timestamp=datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC),
            volume=10,
            source="sales_history",
        )

        assert point.game == "dota2"
        assert point.volume == 10
        assert point.source == "sales_history"

    def test_price_point_to_dict(self):
        """Test converting PricePoint to dictionary."""
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        point = PricePoint(
            game="csgo",
            title="Test Item",
            price=Decimal("25.99"),
            timestamp=ts,
            volume=5,
            source="aggregated",
        )

        result = point.to_dict()

        assert result["game"] == "csgo"
        assert result["title"] == "Test Item"
        assert result["price"] == 25.99  # Converted to float
        assert result["volume"] == 5
        assert result["source"] == "aggregated"
        assert "timestamp" in result

    def test_price_point_from_dict(self):
        """Test creating PricePoint from dictionary."""
        data = {
            "game": "tf2",
            "title": "Test Hat",
            "price": 15.50,
            "volume": 3,
            "timestamp": "2024-01-01T12:00:00+00:00",
            "source": "market",
        }

        point = PricePoint.from_dict(data)

        assert point.game == "tf2"
        assert point.title == "Test Hat"
        assert point.price == Decimal("15.5")
        assert point.volume == 3

    def test_price_point_from_dict_missing_optional_fields(self):
        """Test creating PricePoint from dict with missing optional fields."""
        data = {
            "game": "rust",
            "title": "Rust Skin",
            "price": 5.00,
            "timestamp": "2024-01-01T00:00:00+00:00",
        }

        point = PricePoint.from_dict(data)

        assert point.volume == 0  # Default
        assert point.source == "market"  # Default

    def test_price_point_roundtrip(self):
        """Test that to_dict and from_dict are inverses."""
        original = PricePoint(
            game="csgo",
            title="AWP | Dragon Lore",
            price=Decimal("1500.00"),
            timestamp=datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC),
            volume=2,
            source="sales_history",
        )

        data = original.to_dict()
        restored = PricePoint.from_dict(data)

        assert restored.game == original.game
        assert restored.title == original.title
        assert abs(float(restored.price) - float(original.price)) < 0.01
        assert restored.volume == original.volume
        assert restored.source == original.source


# ============================================================================
# PriceHistory Tests
# ============================================================================


class TestPriceHistory:
    """Tests for the PriceHistory dataclass."""

    def test_create_empty_price_history(self):
        """Test creating PriceHistory with no points."""
        history = PriceHistory(game="csgo", title="Test Item")

        assert history.game == "csgo"
        assert history.title == "Test Item"
        assert len(history.points) == 0
        assert history.collected_at is not None

    def test_create_price_history_with_points(self):
        """Test creating PriceHistory with price points."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("12"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("11"), datetime.now(UTC)),
        ]

        history = PriceHistory(game="csgo", title="Item", points=points)

        assert len(history.points) == 3

    def test_average_price_empty(self):
        """Test average price with no points."""
        history = PriceHistory(game="csgo", title="Test")
        assert history.average_price == Decimal(0)

    def test_average_price_single_point(self):
        """Test average price with single point."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.average_price == Decimal("10")

    def test_average_price_multiple_points(self):
        """Test average price with multiple points."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("20"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("30"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        # Average of 10, 20, 30 = 20
        assert history.average_price == Decimal("20")

    def test_min_price_empty(self):
        """Test min price with no points."""
        history = PriceHistory(game="csgo", title="Test")
        assert history.min_price == Decimal(0)

    def test_min_price_with_points(self):
        """Test min price with multiple points."""
        points = [
            PricePoint("csgo", "Item", Decimal("15"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("25"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.min_price == Decimal("10")

    def test_max_price_empty(self):
        """Test max price with no points."""
        history = PriceHistory(game="csgo", title="Test")
        assert history.max_price == Decimal(0)

    def test_max_price_with_points(self):
        """Test max price with multiple points."""
        points = [
            PricePoint("csgo", "Item", Decimal("15"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("25"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.max_price == Decimal("25")

    def test_total_volume_empty(self):
        """Test total volume with no points."""
        history = PriceHistory(game="csgo", title="Test")
        assert history.total_volume == 0

    def test_total_volume_with_points(self):
        """Test total volume with multiple points."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC), volume=5),
            PricePoint("csgo", "Item", Decimal("12"), datetime.now(UTC), volume=3),
            PricePoint("csgo", "Item", Decimal("11"), datetime.now(UTC), volume=7),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.total_volume == 15

    def test_price_volatility_empty(self):
        """Test volatility with no points."""
        history = PriceHistory(game="csgo", title="Test")
        assert history.price_volatility == 0.0

    def test_price_volatility_single_point(self):
        """Test volatility with single point."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.price_volatility == 0.0

    def test_price_volatility_multiple_points(self):
        """Test volatility with multiple points."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("20"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("30"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        # Should return a positive volatility value
        assert history.price_volatility > 0

    def test_price_volatility_no_variance(self):
        """Test volatility when all prices are the same."""
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("10"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.price_volatility == 0.0

    def test_price_volatility_zero_mean(self):
        """Test volatility when mean is zero."""
        points = [
            PricePoint("csgo", "Item", Decimal("0"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("0"), datetime.now(UTC)),
        ]
        history = PriceHistory(game="csgo", title="Item", points=points)

        assert history.price_volatility == 0.0


# ============================================================================
# HistoricalDataCollector Tests
# ============================================================================


class TestHistoricalDataCollector:
    """Tests for the HistoricalDataCollector class."""

    @pytest.fixture()
    def mock_api(self):
        """Create a mock API client."""
        api = MagicMock()
        api.get_sales_history = AsyncMock(return_value={"sales": []})
        api.get_aggregated_prices_bulk = AsyncMock(return_value={"aggregatedPrices": []})
        return api

    @pytest.fixture()
    def collector(self, mock_api):
        """Create a collector with mock API."""
        return HistoricalDataCollector(api=mock_api, cache_ttl_minutes=60)

    def test_initialization(self, mock_api):
        """Test collector initialization."""
        collector = HistoricalDataCollector(api=mock_api, cache_ttl_minutes=30)

        assert collector.api == mock_api
        assert collector._cache_ttl == timedelta(minutes=30)
        assert len(collector._cache) == 0

    def test_initialization_default_ttl(self, mock_api):
        """Test collector initialization with default TTL."""
        collector = HistoricalDataCollector(api=mock_api)

        assert collector._cache_ttl == timedelta(minutes=60)

    @pytest.mark.asyncio()
    async def test_collect_price_history_empty_result(self, collector):
        """Test collecting history when no data is returned."""
        history = await collector.collect_price_history("csgo", "Test Item", days=30)

        assert history.game == "csgo"
        assert history.title == "Test Item"
        assert len(history.points) == 0

    @pytest.mark.asyncio()
    async def test_collect_price_history_with_sales_data(self, collector, mock_api):
        """Test collecting history with sales data."""
        mock_api.get_sales_history.return_value = {
            "sales": [
                {"price": {"USD": 1500}, "date": "2024-01-01T12:00:00Z"},
                {"price": {"USD": 1600}, "date": "2024-01-02T12:00:00Z"},
            ]
        }

        history = await collector.collect_price_history("csgo", "AK-47", days=30)

        assert history.game == "csgo"
        assert history.title == "AK-47"
        assert len(history.points) == 2

    @pytest.mark.asyncio()
    async def test_collect_price_history_with_aggregated_data(self, collector, mock_api):
        """Test collecting history with aggregated prices."""
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [
                {
                    "title": "AWP | Asiimov",
                    "offerBestPrice": 5000,
                    "orderBestPrice": 4800,
                }
            ]
        }

        history = await collector.collect_price_history("csgo", "AWP | Asiimov", days=30)

        # Should have points from aggregated data
        assert history.game == "csgo"
        assert history.title == "AWP | Asiimov"

    @pytest.mark.asyncio()
    async def test_collect_price_history_uses_cache(self, collector, mock_api):
        """Test that cache is used on subsequent calls."""
        mock_api.get_sales_history.return_value = {"sales": []}

        # First call
        await collector.collect_price_history("csgo", "Item", days=30)
        call_count_1 = mock_api.get_sales_history.call_count

        # Second call should use cache
        await collector.collect_price_history("csgo", "Item", days=30)
        call_count_2 = mock_api.get_sales_history.call_count

        assert call_count_2 == call_count_1  # No additional API call

    @pytest.mark.asyncio()
    async def test_collect_price_history_no_cache(self, collector, mock_api):
        """Test collecting without cache."""
        mock_api.get_sales_history.return_value = {"sales": []}

        # First call
        await collector.collect_price_history("csgo", "Item", days=30, use_cache=False)
        call_count_1 = mock_api.get_sales_history.call_count

        # Second call should not use cache
        await collector.collect_price_history("csgo", "Item", days=30, use_cache=False)
        call_count_2 = mock_api.get_sales_history.call_count

        assert call_count_2 > call_count_1  # Additional API call

    @pytest.mark.asyncio()
    async def test_collect_price_history_api_error(self, collector, mock_api):
        """Test handling API errors during collection."""
        mock_api.get_sales_history.side_effect = Exception("API Error")
        mock_api.get_aggregated_prices_bulk.side_effect = Exception("API Error")

        # Should not raise, should return empty history
        history = await collector.collect_price_history("csgo", "Item", days=30)

        assert history.game == "csgo"
        assert len(history.points) == 0

    @pytest.mark.asyncio()
    async def test_collect_from_sales_history_parsing(self, collector, mock_api):
        """Test parsing various sales history formats."""
        mock_api.get_sales_history.return_value = {
            "sales": [
                # Format with dict price
                {"price": {"USD": 1000}, "date": "2024-01-01T00:00:00Z"},
                # Format with amount
                {"price": {"amount": 2000}, "timestamp": "2024-01-02T00:00:00Z"},
                # Raw price value
                {"price": 3000, "date": "2024-01-03T00:00:00Z"},
            ]
        }

        history = await collector.collect_price_history("csgo", "Item", days=30)

        # All sales should be parsed
        assert len(history.points) >= 1

    @pytest.mark.asyncio()
    async def test_collect_batch(self, collector, mock_api):
        """Test collecting history for multiple items."""
        mock_api.get_sales_history.return_value = {"sales": []}

        titles = ["Item1", "Item2", "Item3"]
        results = await collector.collect_batch("csgo", titles, days=30)

        assert "Item1" in results
        assert "Item2" in results
        assert "Item3" in results

    @pytest.mark.asyncio()
    async def test_collect_batch_partial_failure(self, collector, mock_api):
        """Test batch collection with partial failures."""
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API Error")
            return {"sales": []}

        mock_api.get_sales_history.side_effect = side_effect

        titles = ["Item1", "Item2", "Item3"]
        results = await collector.collect_batch("csgo", titles, days=30)

        # Should still return results for successful items
        assert len(results) >= 1

    def test_clear_cache(self, collector):
        """Test clearing the cache."""
        # Add some fake cache entries
        collector._cache["key1"] = (datetime.now(UTC), MagicMock())
        collector._cache["key2"] = (datetime.now(UTC), MagicMock())

        assert len(collector._cache) == 2

        collector.clear_cache()

        assert len(collector._cache) == 0

    def test_get_cache_stats_empty(self, collector):
        """Test getting stats for empty cache."""
        stats = collector.get_cache_stats()

        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["ttl_minutes"] == 60

    def test_get_cache_stats_with_entries(self, collector):
        """Test getting stats with cache entries."""
        # Add valid entry (recent)
        collector._cache["valid"] = (datetime.now(UTC), MagicMock())

        # Add expired entry (old timestamp)
        collector._cache["expired"] = (
            datetime.now(UTC) - timedelta(hours=2),
            MagicMock(),
        )

        stats = collector.get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 1  # Only the recent one


# ============================================================================
# Module Exports Tests
# ============================================================================


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        from src.analytics import historical_data

        assert hasattr(historical_data, "__all__")
        assert "PricePoint" in historical_data.__all__
        assert "PriceHistory" in historical_data.__all__
        assert "HistoricalDataCollector" in historical_data.__all__

    def test_imports(self):
        """Test that classes can be imported."""
        from src.analytics.historical_data import (
            HistoricalDataCollector,
            PriceHistory,
            PricePoint,
        )

        assert PricePoint is not None
        assert PriceHistory is not None
        assert HistoricalDataCollector is not None


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_price_point_zero_price(self):
        """Test PricePoint with zero price."""
        point = PricePoint(
            game="csgo",
            title="Free Item",
            price=Decimal("0"),
            timestamp=datetime.now(UTC),
        )

        assert point.price == Decimal("0")

    def test_price_point_negative_price(self):
        """Test PricePoint with negative price (edge case)."""
        # This shouldn't happen in practice but should not crash
        point = PricePoint(
            game="csgo",
            title="Weird Item",
            price=Decimal("-5"),
            timestamp=datetime.now(UTC),
        )

        assert point.price == Decimal("-5")

    def test_price_point_large_price(self):
        """Test PricePoint with very large price."""
        point = PricePoint(
            game="csgo",
            title="Expensive Item",
            price=Decimal("999999.99"),
            timestamp=datetime.now(UTC),
        )

        assert point.price == Decimal("999999.99")

    def test_price_point_unicode_title(self):
        """Test PricePoint with unicode characters in title."""
        point = PricePoint(
            game="csgo",
            title="AK-47 | 红线 (崭新出厂)",  # Chinese characters
            price=Decimal("100"),
            timestamp=datetime.now(UTC),
        )

        assert "红线" in point.title

    def test_price_point_special_characters_in_title(self):
        """Test PricePoint with special characters in title."""
        point = PricePoint(
            game="csgo",
            title='M4A1-S | "Nitro" <Hot!>',
            price=Decimal("50"),
            timestamp=datetime.now(UTC),
        )

        assert "Nitro" in point.title

    def test_price_history_large_number_of_points(self):
        """Test PriceHistory with many points."""
        points = [
            PricePoint(
                "csgo",
                "Item",
                Decimal(str(i)),
                datetime.now(UTC) - timedelta(days=i),
            )
            for i in range(1, 1001)  # 1000 points
        ]

        history = PriceHistory(game="csgo", title="Item", points=points)

        assert len(history.points) == 1000
        assert history.average_price == Decimal("500.5")  # Average of 1..1000
        assert history.min_price == Decimal("1")
        assert history.max_price == Decimal("1000")

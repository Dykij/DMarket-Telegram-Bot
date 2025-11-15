"""Comprehensive tests for sales_history.py module.

Tests cover:
- Item sales history retrieval
- Price anomaly detection
- Price trend calculation
- Market trend overview
- Cache management
- Statistical calculations
- Compatibility functions (get_sales_history, analyze_sales_history, etc.)
"""

import asyncio
import contextlib
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.dmarket_api import DMarketAPI
from src.dmarket.sales_history import (
    CACHE_TTL,
    SALES_CACHE_DIR,
    _calculate_median,
    _calculate_std_dev,
    _extract_price_from_item,
    _get_cache_file_path,
    _load_from_cache,
    _save_to_cache,
    analyze_sales_history,
    calculate_price_trend,
    detect_price_anomalies,
    execute_api_request,
    get_arbitrage_opportunities_with_sales_history,
    get_item_sales_history,
    get_market_trend_overview,
    get_sales_history,
)


# ==================== Fixtures ====================


@pytest.fixture()
def mock_dmarket_api():
    """Create a mocked DMarket API client."""
    api = MagicMock(spec=DMarketAPI)
    api.get_item_price_history = AsyncMock()
    api.get_market_items = AsyncMock()
    api.request = AsyncMock()
    api._close_client = AsyncMock()
    return api


@pytest.fixture()
def sample_sales_data():
    """Sample sales data for testing."""
    base_timestamp = int(time.time()) - 7 * 24 * 3600  # 7 days ago

    return [
        {"price": 1000, "date": base_timestamp + i * 3600}  # $10.00 in cents
        for i in range(24)
    ]


@pytest.fixture()
def sample_sales_with_anomalies():
    """Sample sales data with price anomalies."""
    base_timestamp = int(time.time()) - 24 * 3600  # 1 day ago

    return [
        {"price": 1000, "date": base_timestamp},  # $10.00 - normal
        {"price": 1050, "date": base_timestamp + 3600},  # $10.50 - normal
        {"price": 1500, "date": base_timestamp + 7200},  # $15.00 - anomaly +50%
        {"price": 1020, "date": base_timestamp + 10800},  # $10.20 - normal
        {"price": 500, "date": base_timestamp + 14400},  # $5.00 - anomaly -50%
        {"price": 1000, "date": base_timestamp + 18000},  # $10.00 - normal
    ]


@pytest.fixture()
def sample_trending_sales():
    """Sample sales data showing clear trend."""
    base_timestamp = int(time.time()) - 7 * 24 * 3600  # 7 days ago

    # Prices gradually increasing from $10 to $15 (50% increase)
    return [
        {"price": 1000 + i * 20, "date": base_timestamp + i * 3600}  # Gradual increase
        for i in range(25)
    ]


@pytest.fixture()
def sample_market_items():
    """Sample market items data."""
    return {
        "items": [
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": 1250},  # $12.50
                "salesPrice": 1200,  # $12.00 last sale
                "imageUrl": "https://example.com/ak47.png",
            },
            {
                "title": "AWP | Asiimov (Field-Tested)",
                "price": {"USD": 5000},  # $50.00
                "salesPrice": 4800,  # $48.00 last sale
                "imageUrl": "https://example.com/awp.png",
            },
            {
                "title": "Glock-18 | Fade (Factory New)",
                "price": {"USD": 30000},  # $300.00
                "salesPrice": 29500,  # $295.00 last sale
                "imageUrl": "https://example.com/glock.png",
            },
        ],
        "total": 3,
    }


@pytest.fixture()
def cleanup_cache():
    """Cleanup cache files after tests."""
    yield
    # Cleanup test cache files
    for cache_file in SALES_CACHE_DIR.glob("*.json"):
        with contextlib.suppress(Exception):
            cache_file.unlink()


# ==================== Tests: get_item_sales_history ====================


class TestGetItemSalesHistory:
    """Tests for get_item_sales_history function."""

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_success(self, mock_dmarket_api, sample_sales_data):
        """Test successful retrieval of item sales history."""
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_data

        result = await get_item_sales_history(
            item_name="AK-47 | Redline (Field-Tested)",
            game="csgo",
            period="24h",
            use_cache=False,
            dmarket_api=mock_dmarket_api,
        )

        assert len(result) == 24
        assert all("price" in sale for sale in result)
        assert all("timestamp" in sale for sale in result)
        assert all("market_hash_name" in sale for sale in result)
        # Verify prices are converted from cents to USD
        assert result[0]["price"] == 10.00
        # Verify sorted by timestamp descending
        assert result[0]["timestamp"] >= result[-1]["timestamp"]

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_no_data(self, mock_dmarket_api):
        """Test handling when no sales data is available."""
        mock_dmarket_api.get_item_price_history.return_value = []

        result = await get_item_sales_history(
            item_name="Non-existent Item",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_invalid_period(self, mock_dmarket_api, sample_sales_data):
        """Test that invalid period defaults to 24h."""
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_data

        result = await get_item_sales_history(
            item_name="Test Item",
            game="csgo",
            period="invalid_period",
            use_cache=False,
            dmarket_api=mock_dmarket_api,
        )

        # Should still work with default period
        assert len(result) > 0

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_with_cache(
        self, mock_dmarket_api, sample_sales_data, cleanup_cache
    ):
        """Test caching mechanism for sales history."""
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_data

        item_name = "Test Item Cache"
        game = "csgo"
        period = "24h"

        # First call - should fetch from API and cache
        result1 = await get_item_sales_history(
            item_name=item_name,
            game=game,
            period=period,
            use_cache=True,
            dmarket_api=mock_dmarket_api,
        )

        # Second call - should load from cache
        result2 = await get_item_sales_history(
            item_name=item_name,
            game=game,
            period=period,
            use_cache=True,
            dmarket_api=mock_dmarket_api,
        )

        assert result1 == result2
        # API should be called only once (first time)
        assert mock_dmarket_api.get_item_price_history.call_count == 1

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_skip_invalid_records(self, mock_dmarket_api):
        """Test that records without required fields are skipped."""
        invalid_data = [
            {"price": 1000},  # Missing date
            {"date": 1234567890},  # Missing price
            {"price": 1000, "date": 1234567890},  # Valid
            {},  # Missing both
        ]
        mock_dmarket_api.get_item_price_history.return_value = invalid_data

        result = await get_item_sales_history(
            item_name="Test Item",
            game="csgo",
            use_cache=False,
            dmarket_api=mock_dmarket_api,
        )

        # Only 1 valid record should remain
        assert len(result) == 1

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_api_error(self, mock_dmarket_api):
        """Test handling of API errors."""
        mock_dmarket_api.get_item_price_history.side_effect = Exception("API Error")

        result = await get_item_sales_history(
            item_name="Test Item",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_create_own_client(self, sample_sales_data):
        """Test that function creates its own API client if not provided."""
        with patch("src.dmarket.sales_history.DMarketAPI") as mock_api_class:
            mock_instance = MagicMock()
            mock_instance.get_item_price_history = AsyncMock(return_value=sample_sales_data)
            mock_instance._close_client = AsyncMock()
            mock_api_class.return_value = mock_instance

            result = await get_item_sales_history(
                item_name="Test Item",
                game="csgo",
                dmarket_api=None,  # No API provided
                use_cache=False,
            )

            # Should create API client
            mock_api_class.assert_called_once()
            # Should close client after use
            mock_instance._close_client.assert_called_once()
            assert len(result) > 0


# ==================== Tests: detect_price_anomalies ====================


class TestDetectPriceAnomalies:
    """Tests for detect_price_anomalies function."""

    @pytest.mark.asyncio()
    async def test_detect_price_anomalies_with_anomalies(
        self, mock_dmarket_api, sample_sales_with_anomalies
    ):
        """Test detection of price anomalies."""
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_with_anomalies

        result = await detect_price_anomalies(
            item_name="Test Item",
            game="csgo",
            period="24h",
            threshold_percent=20.0,
            dmarket_api=mock_dmarket_api,
        )

        assert "anomalies" in result
        assert len(result["anomalies"]) == 2  # Two anomalies (high and low)
        assert result["num_sales"] == 6
        assert result["min_price"] == 5.00
        assert result["max_price"] == 15.00

        # Check anomaly details
        anomaly_high = next(a for a in result["anomalies"] if a["is_high"])
        anomaly_low = next(a for a in result["anomalies"] if not a["is_high"])

        assert anomaly_high["price"] == 15.00
        assert anomaly_low["price"] == 5.00
        assert "deviation_percent" in anomaly_high
        assert "date" in anomaly_high

    @pytest.mark.asyncio()
    async def test_detect_price_anomalies_no_anomalies(
        self, mock_dmarket_api, sample_sales_data, cleanup_cache
    ):
        """Test when there are no significant anomalies."""
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_data

        result = await detect_price_anomalies(
            item_name="Test Item No Anomalies Unique",
            game="csgo",
            period="24h",
            threshold_percent=50.0,  # Very high threshold
            dmarket_api=mock_dmarket_api,
        )

        assert result["anomalies"] == []
        assert result["num_sales"] == 24

    @pytest.mark.asyncio()
    async def test_detect_price_anomalies_no_sales_data(self, mock_dmarket_api):
        """Test anomaly detection with no sales data."""
        mock_dmarket_api.get_item_price_history.return_value = []

        result = await detect_price_anomalies(
            item_name="Test Item",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["anomalies"] == []
        assert result["average_price"] == 0
        assert result["median_price"] == 0
        assert result["num_sales"] == 0

    @pytest.mark.asyncio()
    async def test_detect_price_anomalies_statistics(self, mock_dmarket_api, sample_sales_data):
        """Test that statistics are calculated correctly."""
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_data

        result = await detect_price_anomalies(
            item_name="Test Item",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        # All prices are $10.00
        assert result["average_price"] == 10.00
        assert result["median_price"] == 10.00
        assert result["min_price"] == 10.00
        assert result["max_price"] == 10.00


# ==================== Tests: calculate_price_trend ====================


class TestCalculatePriceTrend:
    """Tests for calculate_price_trend function."""

    @pytest.mark.asyncio()
    async def test_calculate_price_trend_upward(self, mock_dmarket_api, cleanup_cache):
        """Test detection of upward price trend."""
        # Strong upward trend: $10 -> $20 (+100%)
        base_timestamp = int(time.time()) - 7 * 24 * 3600
        upward_sales = [
            {"price": 1000 + i * 40, "date": base_timestamp + i * 3600} for i in range(25)
        ]
        mock_dmarket_api.get_item_price_history.return_value = upward_sales

        result = await calculate_price_trend(
            item_name="Test Item Upward Unique",
            game="csgo",
            period="7d",
            dmarket_api=mock_dmarket_api,
        )

        assert result["trend"] == "up"
        assert result["change_percent"] > 5
        assert result["start_price"] < result["end_price"]
        assert result["volatility"] > 0
        assert result["num_sales"] == 25
        assert result["period"] == "7d"

    @pytest.mark.asyncio()
    async def test_calculate_price_trend_downward(self, mock_dmarket_api, cleanup_cache):
        """Test detection of downward price trend."""
        # Strong downward trend: $15 -> $8 (-47%)
        base_timestamp = int(time.time()) - 7 * 24 * 3600
        decreasing_sales = [
            {"price": 1500 - i * 30, "date": base_timestamp + i * 3600} for i in range(24)
        ]
        mock_dmarket_api.get_item_price_history.return_value = decreasing_sales

        result = await calculate_price_trend(
            item_name="Test Item Downward Unique",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["trend"] == "down"
        assert result["change_percent"] < -5
        assert result["start_price"] > result["end_price"]

    @pytest.mark.asyncio()
    async def test_calculate_price_trend_stable(self, mock_dmarket_api):
        """Test detection of stable price trend."""
        # Prices fluctuate slightly around $10 (±2%)
        base_timestamp = int(time.time()) - 7 * 24 * 3600
        stable_sales = [
            {
                "price": 1000 + (i % 3) * 10,  # Small variations
                "date": base_timestamp + i * 3600,
            }
            for i in range(25)
        ]
        mock_dmarket_api.get_item_price_history.return_value = stable_sales

        result = await calculate_price_trend(
            item_name="Test Item",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["trend"] == "stable"
        assert abs(result["change_percent"]) < 5

    @pytest.mark.asyncio()
    async def test_calculate_price_trend_insufficient_data(self, mock_dmarket_api, cleanup_cache):
        """Test trend calculation with insufficient data."""
        # Only 1 sale
        mock_dmarket_api.get_item_price_history.return_value = [
            {"price": 1000, "date": int(time.time())}
        ]

        result = await calculate_price_trend(
            item_name="Test Item Insufficient Unique",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["trend"] == "unknown"
        assert result["change_percent"] == 0

    @pytest.mark.asyncio()
    async def test_calculate_price_trend_no_data(self, mock_dmarket_api, cleanup_cache):
        """Test trend calculation with no data."""
        mock_dmarket_api.get_item_price_history.return_value = []

        result = await calculate_price_trend(
            item_name="Test Item No Data Unique",
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["trend"] == "unknown"
        assert result["start_price"] == 0
        assert result["end_price"] == 0


# ==================== Tests: get_market_trend_overview ====================


class TestGetMarketTrendOverview:
    """Tests for get_market_trend_overview function."""

    @pytest.mark.asyncio()
    async def test_get_market_trend_overview_success(self, mock_dmarket_api, sample_market_items):
        """Test successful market trend overview retrieval."""
        mock_dmarket_api.get_market_items.return_value = sample_market_items

        # Mock trend calculation for each item
        async def mock_trend(item_name, game, period, dmarket_api):
            if "AK-47" in item_name:
                return {
                    "trend": "up",
                    "change_percent": 10.0,
                    "start_price": 11.0,
                    "end_price": 12.1,
                    "volatility": 0.5,
                    "num_sales": 20,
                    "period": "7d",
                }
            if "AWP" in item_name:
                return {
                    "trend": "down",
                    "change_percent": -8.0,
                    "start_price": 52.0,
                    "end_price": 47.84,
                    "volatility": 1.2,
                    "num_sales": 15,
                    "period": "7d",
                }
            return {
                "trend": "stable",
                "change_percent": 2.0,
                "start_price": 290.0,
                "end_price": 295.8,
                "volatility": 5.0,
                "num_sales": 5,
                "period": "7d",
            }

        with patch(
            "src.dmarket.sales_history.calculate_price_trend",
            side_effect=mock_trend,
        ):
            result = await get_market_trend_overview(
                game="csgo",
                item_count=3,
                min_price=1.0,
                max_price=500.0,
                period="7d",
                dmarket_api=mock_dmarket_api,
            )

        assert "market_trend" in result
        assert "avg_change_percent" in result
        assert len(result["up_trending_items"]) > 0
        assert len(result["down_trending_items"]) > 0
        assert len(result["stable_items"]) > 0
        assert result["game"] == "csgo"
        assert result["period"] == "7d"

    @pytest.mark.asyncio()
    async def test_get_market_trend_overview_no_items(self, mock_dmarket_api):
        """Test market overview when no items are found."""
        # Return None to simulate no items (triggers unknown trend)
        mock_dmarket_api.get_market_items.return_value = None

        result = await get_market_trend_overview(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["market_trend"] == "unknown"
        assert result["avg_change_percent"] == 0
        assert result["up_trending_items"] == []
        assert result["down_trending_items"] == []
        assert result["stable_items"] == []

    @pytest.mark.asyncio()
    async def test_get_market_trend_overview_api_error(self, mock_dmarket_api):
        """Test handling of API errors during market overview."""
        mock_dmarket_api.get_market_items.side_effect = Exception("API Error")

        result = await get_market_trend_overview(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["market_trend"] == "unknown"
        assert result["up_trending_items"] == []

    @pytest.mark.asyncio()
    async def test_get_market_trend_overview_determines_overall_trend(
        self, mock_dmarket_api, sample_market_items
    ):
        """Test that overall market trend is determined correctly."""
        mock_dmarket_api.get_market_items.return_value = sample_market_items

        # All items trending up
        async def all_up_trend(item_name, game, period, dmarket_api):
            return {
                "trend": "up",
                "change_percent": 15.0,
                "start_price": 10.0,
                "end_price": 11.5,
                "volatility": 0.5,
                "num_sales": 20,
                "period": "7d",
            }

        with patch(
            "src.dmarket.sales_history.calculate_price_trend",
            side_effect=all_up_trend,
        ):
            result = await get_market_trend_overview(
                game="csgo",
                dmarket_api=mock_dmarket_api,
            )

        # Average change should be high and positive
        assert result["market_trend"] in ["up", "stable"]
        assert result["avg_change_percent"] > 3


# ==================== Tests: Helper Functions ====================


class TestHelperFunctions:
    """Tests for private helper functions."""

    def test_extract_price_from_item_with_sales_price(self):
        """Test price extraction from item with salesPrice."""
        item = {"salesPrice": 1250, "price": {"USD": 1300}}
        price = _extract_price_from_item(item)
        assert price == 12.50  # Uses salesPrice

    def test_extract_price_from_item_without_sales_price(self):
        """Test price extraction from item without salesPrice."""
        item = {"price": {"USD": 1300}}
        price = _extract_price_from_item(item)
        assert price == 13.00  # Uses price.USD

    def test_extract_price_from_item_no_price_data(self):
        """Test price extraction when no price data available."""
        item = {}
        price = _extract_price_from_item(item)
        assert price == 0

    def test_calculate_median_odd_count(self):
        """Test median calculation with odd number of elements."""
        numbers = [1, 3, 5, 7, 9]
        median = _calculate_median(numbers)
        assert median == 5

    def test_calculate_median_even_count(self):
        """Test median calculation with even number of elements."""
        numbers = [1, 2, 3, 4]
        median = _calculate_median(numbers)
        assert median == 2.5

    def test_calculate_median_empty_list(self):
        """Test median calculation with empty list."""
        median = _calculate_median([])
        assert median == 0

    def test_calculate_median_single_element(self):
        """Test median calculation with single element."""
        median = _calculate_median([42])
        assert median == 42

    def test_calculate_std_dev_normal(self):
        """Test standard deviation calculation."""
        numbers = [2, 4, 4, 4, 5, 5, 7, 9]
        std_dev = _calculate_std_dev(numbers)
        assert std_dev > 0
        assert 1.9 < std_dev < 2.2  # Approximate expected value

    def test_calculate_std_dev_empty_list(self):
        """Test standard deviation with empty list."""
        std_dev = _calculate_std_dev([])
        assert std_dev == 0

    def test_calculate_std_dev_single_element(self):
        """Test standard deviation with single element."""
        std_dev = _calculate_std_dev([42])
        assert std_dev == 0

    def test_calculate_std_dev_identical_values(self):
        """Test standard deviation when all values are identical."""
        numbers = [5, 5, 5, 5, 5]
        std_dev = _calculate_std_dev(numbers)
        assert std_dev == 0


# ==================== Tests: Cache Management ====================


class TestCacheManagement:
    """Tests for cache management functions."""

    def test_get_cache_file_path(self):
        """Test cache file path generation."""
        path = _get_cache_file_path("AK-47 | Redline (FT)", "csgo", "24h")
        assert path.parent == SALES_CACHE_DIR
        assert "csgo" in path.name
        assert "24h" in path.name
        assert path.suffix == ".json"

    def test_get_cache_file_path_special_characters(self):
        """Test cache file path with special characters in item name."""
        path = _get_cache_file_path("Item/with\\special:chars*?", "csgo", "7d")
        # Special chars should be replaced with underscores
        assert "/" not in path.name
        assert "\\" not in path.name
        assert ":" not in path.name
        assert "*" not in path.name

    def test_save_and_load_cache(self, cleanup_cache):
        """Test saving and loading cache."""
        item_name = "Test Cache Item"
        game = "csgo"
        period = "24h"
        data = [
            {"price": 10.0, "timestamp": 1234567890, "market_hash_name": item_name},
            {"price": 11.0, "timestamp": 1234567900, "market_hash_name": item_name},
        ]

        # Save to cache
        _save_to_cache(item_name, game, period, data)

        # Load from cache
        loaded_data = _load_from_cache(item_name, game, period)

        assert loaded_data == data

    def test_load_cache_expired(self, cleanup_cache):
        """Test that expired cache returns empty list."""
        item_name = "Expired Cache Item"
        game = "csgo"
        period = "1h"
        data = [{"price": 10.0, "timestamp": 1234567890}]

        # Save to cache
        _save_to_cache(item_name, game, period, data)

        # Modify file timestamp to make it expired
        cache_file = _get_cache_file_path(item_name, game, period)
        old_time = time.time() - CACHE_TTL[period] - 100
        cache_file.touch()
        # Set modified time to old time
        import os

        os.utime(cache_file, (old_time, old_time))

        # Load should return empty (cache expired)
        loaded_data = _load_from_cache(item_name, game, period)
        assert loaded_data == []

    def test_load_cache_nonexistent(self):
        """Test loading cache for non-existent item."""
        loaded_data = _load_from_cache("Nonexistent Item", "csgo", "24h")
        assert loaded_data == []


# ==================== Tests: Compatibility Functions ====================


class TestCompatibilityFunctions:
    """Tests for compatibility functions (get_sales_history, analyze_sales_history)."""

    @pytest.mark.asyncio()
    async def test_get_sales_history_success(self, mock_dmarket_api):
        """Test get_sales_history compatibility function."""
        mock_response = {
            "LastSales": [
                {"price": {"USD": 1000}, "date": 1234567890},
                {"price": {"USD": 1100}, "date": 1234567900},
            ],
            "Total": 2,
        }
        mock_dmarket_api.request.return_value = mock_response

        result = await get_sales_history(
            items=["Test Item 1", "Test Item 2"],
            api_client=mock_dmarket_api,
        )

        assert "LastSales" in result
        assert "Total" in result
        assert result["Total"] == 2
        assert len(result["LastSales"]) == 2

    @pytest.mark.asyncio()
    async def test_get_sales_history_empty_items(self, mock_dmarket_api):
        """Test get_sales_history with empty items list."""
        result = await get_sales_history(items=[], api_client=mock_dmarket_api)

        assert result["LastSales"] == []
        assert result["Total"] == 0

    @pytest.mark.asyncio()
    async def test_get_sales_history_api_error(self, mock_dmarket_api):
        """Test get_sales_history handling API errors."""
        mock_dmarket_api.request.side_effect = Exception("API Error")

        result = await get_sales_history(
            items=["Test Item"],
            api_client=mock_dmarket_api,
        )

        assert "Error" in result
        assert result["LastSales"] == []

    @pytest.mark.asyncio()
    async def test_get_sales_history_batch_processing(self, mock_dmarket_api):
        """Test that get_sales_history processes items in batches."""
        # Create 75 items (should be split into 2 batches of 50 and 25)
        items = [f"Item {i}" for i in range(75)]

        mock_response = {"LastSales": [{"price": {"USD": 1000}, "date": 1234567890}]}
        mock_dmarket_api.request.return_value = mock_response

        result = await get_sales_history(items=items, api_client=mock_dmarket_api)

        # Should call API twice (2 batches)
        assert mock_dmarket_api.request.call_count == 2

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_success(self, mock_dmarket_api):
        """Test analyze_sales_history compatibility function."""
        mock_sales_response = {
            "LastSales": [
                {"price": {"USD": 1000}, "date": int(time.time()) - 86400 * i} for i in range(10)
            ],
            "Total": 10,
        }
        mock_dmarket_api.request.return_value = mock_sales_response

        result = await analyze_sales_history(
            item_name="Test Item",
            days=7,
            api_client=mock_dmarket_api,
        )

        assert result["item_name"] == "Test Item"
        assert result["has_data"] is True
        assert result["total_sales"] == 10
        assert "recent_sales" in result
        assert "average_price" in result
        assert "sales_per_day" in result
        assert "price_trend" in result

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_no_data(self, mock_dmarket_api):
        """Test analyze_sales_history with no sales data."""
        mock_dmarket_api.request.return_value = {"LastSales": [], "Total": 0}

        result = await analyze_sales_history(
            item_name="Test Item",
            api_client=mock_dmarket_api,
        )

        assert result["has_data"] is False
        assert result["total_sales"] == 0
        assert result["sales_per_day"] == 0.0

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_price_trend_up(self, mock_dmarket_api):
        """Test price trend detection in analyze_sales_history (upward)."""
        # Prices increasing from 1000 to 1200 (20% increase)
        mock_sales_response = {
            "LastSales": [
                {
                    "price": {"USD": 1000 + i * 20},
                    "date": int(time.time()) - 86400 * (10 - i),
                }
                for i in range(10)
            ],
            "Total": 10,
        }
        mock_dmarket_api.request.return_value = mock_sales_response

        result = await analyze_sales_history(
            item_name="Test Item",
            days=7,
            api_client=mock_dmarket_api,
        )

        assert result["price_trend"] == "up"

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_price_trend_down(self, mock_dmarket_api):
        """Test price trend detection in analyze_sales_history (downward)."""
        # Prices decreasing from 1200 to 1000 (-16.7%)
        mock_sales_response = {
            "LastSales": [
                {
                    "price": {"USD": 1200 - i * 20},
                    "date": int(time.time()) - 86400 * (10 - i),
                }
                for i in range(10)
            ],
            "Total": 10,
        }
        mock_dmarket_api.request.return_value = mock_sales_response

        result = await analyze_sales_history(
            item_name="Test Item",
            days=7,
            api_client=mock_dmarket_api,
        )

        assert result["price_trend"] == "down"

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_api_error(self, mock_dmarket_api):
        """Test analyze_sales_history handling API errors."""
        mock_dmarket_api.request.side_effect = Exception("API Error")

        result = await analyze_sales_history(
            item_name="Test Item",
            api_client=mock_dmarket_api,
        )

        assert "error" in result
        assert result["has_data"] is False

    @pytest.mark.asyncio()
    async def test_execute_api_request_success(self, mock_dmarket_api):
        """Test execute_api_request compatibility function."""
        mock_response = {"data": "test"}
        mock_dmarket_api.request.return_value = mock_response

        result = await execute_api_request(
            endpoint="/test-endpoint",
            params={"key": "value"},
            api_client=mock_dmarket_api,
        )

        assert result == mock_response
        mock_dmarket_api.request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_execute_api_request_error(self, mock_dmarket_api):
        """Test execute_api_request handling errors."""
        mock_dmarket_api.request.side_effect = Exception("Request failed")

        result = await execute_api_request(
            endpoint="/test-endpoint",
            api_client=mock_dmarket_api,
        )

        assert "Error" in result

    @pytest.mark.skip(reason="find_arbitrage_items in different module")
    @pytest.mark.asyncio()
    async def test_get_arbitrage_opportunities_with_sales_history_success(self, mock_dmarket_api):
        """Test get_arbitrage_opportunities_with_sales_history filtering."""
        # Mock arbitrage items
        mock_arbitrage_items = [
            {"market_hash_name": "Item 1", "profit": 5.0},
            {"market_hash_name": "Item 2", "profit": 10.0},
            {"market_hash_name": "Item 3", "profit": 3.0},
        ]

        # Mock sales analysis
        async def mock_analyze(item_name, api_client):
            if item_name == "Item 1":
                return {
                    "has_data": True,
                    "sales_per_day": 5.0,  # Above min threshold
                    "price_trend": "up",
                }
            if item_name == "Item 2":
                return {
                    "has_data": True,
                    "sales_per_day": 0.5,  # Below min threshold
                    "price_trend": "up",
                }
            return {"has_data": False}

        with (
            patch(
                "src.dmarket.arbitrage.find_arbitrage_items",
                return_value=mock_arbitrage_items,
            ),
            patch(
                "src.dmarket.sales_history.analyze_sales_history",
                side_effect=mock_analyze,
            ),
        ):
            result = await get_arbitrage_opportunities_with_sales_history(
                min_sales_per_day=1.0,
                price_trend_filter="up",
                api_client=mock_dmarket_api,
            )

        # Only Item 1 should pass filters (has data, sales >= 1.0, trend = up)
        assert len(result) == 1
        assert result[0]["market_hash_name"] == "Item 1"
        assert "sales_analysis" in result[0]

    @pytest.mark.skip(reason="find_arbitrage_items in different module")
    @pytest.mark.asyncio()
    async def test_get_arbitrage_opportunities_with_sales_history_api_error(self, mock_dmarket_api):
        """Test get_arbitrage_opportunities_with_sales_history handling errors."""
        with patch(
            "src.dmarket.arbitrage.find_arbitrage_items",
            side_effect=Exception("API Error"),
        ):
            result = await get_arbitrage_opportunities_with_sales_history(
                api_client=mock_dmarket_api,
            )

        assert result == []


# ==================== Integration Tests ====================


class TestSalesHistoryIntegration:
    """Integration tests for sales history module."""

    @pytest.mark.asyncio()
    async def test_full_workflow_item_analysis(self, mock_dmarket_api, sample_sales_with_anomalies):
        """Test full workflow: get history -> detect anomalies -> calculate trend."""
        item_name = "Integration Test Item"
        mock_dmarket_api.get_item_price_history.return_value = sample_sales_with_anomalies

        # 1. Get sales history
        history = await get_item_sales_history(
            item_name=item_name,
            game="csgo",
            use_cache=False,
            dmarket_api=mock_dmarket_api,
        )
        assert len(history) == 6

        # 2. Detect anomalies
        anomalies = await detect_price_anomalies(
            item_name=item_name,
            game="csgo",
            threshold_percent=20.0,
            dmarket_api=mock_dmarket_api,
        )
        assert len(anomalies["anomalies"]) == 2

        # 3. Calculate trend
        trend = await calculate_price_trend(
            item_name=item_name,
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )
        assert trend["trend"] in ["up", "down", "stable"]

    @pytest.mark.asyncio()
    async def test_concurrent_sales_history_requests(self, mock_dmarket_api):
        """Test concurrent requests for multiple items."""
        items = ["Item 1", "Item 2", "Item 3"]
        mock_dmarket_api.get_item_price_history.return_value = [
            {"price": 1000, "date": int(time.time())}
        ]

        # Fetch history for multiple items concurrently
        tasks = [
            get_item_sales_history(
                item_name=item,
                game="csgo",
                use_cache=False,
                dmarket_api=mock_dmarket_api,
            )
            for item in items
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(len(r) > 0 for r in results)

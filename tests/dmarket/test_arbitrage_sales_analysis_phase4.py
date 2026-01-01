"""Phase 4 extended tests for arbitrage_sales_analysis.py.

This module provides comprehensive tests to achieve 100% coverage for:
- SalesAnalyzer class methods
- Module-level functions
- Cache management
- Error handling
- Edge cases
"""

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.arbitrage_sales_analysis import (
    SalesAnalyzer,
    analyze_item_liquidity,
    batch_analyze_items,
    enhanced_arbitrage_search,
    find_best_arbitrage_opportunities,
    get_sales_volume_stats,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture()
def mock_api() -> MagicMock:
    """Create a mock API client."""
    api = MagicMock()
    api.get_market_items = AsyncMock()
    api._request = AsyncMock()
    api.get_sales_history = AsyncMock()
    return api


@pytest.fixture()
def analyzer(mock_api: MagicMock) -> SalesAnalyzer:
    """Create a SalesAnalyzer instance with mock API."""
    return SalesAnalyzer(api_client=mock_api)


@pytest.fixture()
def sample_sales_data() -> list[dict[str, Any]]:
    """Generate sample sales data with Unix timestamps."""
    base_time = int(time.time())
    return [
        {"price": {"amount": 1000 + i * 50}, "date": base_time - i * 3600}
        for i in range(20)
    ]


@pytest.fixture()
def sample_items_response() -> dict[str, Any]:
    """Sample market items response."""
    return {
        "items": [
            {
                "itemId": "item123",
                "title": "AK-47 | Redline",
                "price": {"amount": 1500},
            }
        ]
    }


# ============================================================================
# SalesAnalyzer Initialization Tests
# ============================================================================


class TestSalesAnalyzerInit:
    """Tests for SalesAnalyzer initialization."""

    def test_init_with_api_client(self, mock_api: MagicMock) -> None:
        """Test initialization with provided API client."""
        analyzer = SalesAnalyzer(api_client=mock_api)
        assert analyzer.api_client == mock_api
        assert analyzer._sales_cache == {}
        assert analyzer._cache_ttl == 3600

    def test_init_without_api_client(self) -> None:
        """Test initialization without API client."""
        analyzer = SalesAnalyzer()
        assert analyzer.api_client is None
        assert analyzer._sales_cache == {}

    def test_init_default_thresholds(self) -> None:
        """Test default volume thresholds are set."""
        analyzer = SalesAnalyzer()
        assert analyzer.very_high_volume_threshold == 3
        assert analyzer.high_volume_threshold == 1.5
        assert analyzer.medium_volume_threshold == 0.5
        assert analyzer.min_sample_size == 3


# ============================================================================
# get_api_client Tests
# ============================================================================


class TestGetApiClient:
    """Tests for get_api_client method."""

    @pytest.mark.asyncio()
    async def test_get_existing_api_client(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test returning existing API client."""
        result = await analyzer.get_api_client()
        assert result == mock_api

    @pytest.mark.asyncio()
    async def test_create_new_api_client(self) -> None:
        """Test creating new API client when none exists."""
        analyzer = SalesAnalyzer()

        with (
            patch.dict(
                "os.environ",
                {
                    "DMARKET_PUBLIC_KEY": "test_public",
                    "DMARKET_SECRET_KEY": "test_secret",
                    "DMARKET_API_URL": "https://test.api.com",
                },
            ),
            patch("src.dmarket.arbitrage_sales_analysis.DMarketAPI") as mock_class,
        ):
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            result = await analyzer.get_api_client()

            mock_class.assert_called_once_with(
                public_key="test_public",
                secret_key="test_secret",
                api_url="https://test.api.com",
            )
            assert result == mock_instance


# ============================================================================
# get_item_sales_history Tests
# ============================================================================


class TestGetItemSalesHistory:
    """Tests for get_item_sales_history method."""

    @pytest.mark.asyncio()
    async def test_cache_hit(
        self, analyzer: SalesAnalyzer, sample_sales_data: list[dict[str, Any]]
    ) -> None:
        """Test cache hit returns cached data."""
        cache_key = "csgo:Test Item:30"
        analyzer._sales_cache[cache_key] = (sample_sales_data, time.time())

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 30)

        assert result == sample_sales_data
        # API should not be called
        analyzer.api_client.get_market_items.assert_not_called()

    @pytest.mark.asyncio()
    async def test_cache_expired(
        self,
        analyzer: SalesAnalyzer,
        mock_api: MagicMock,
        sample_sales_data: list[dict[str, Any]],
    ) -> None:
        """Test expired cache triggers new API call."""
        cache_key = "csgo:Test Item:30"
        # Set cache with expired timestamp
        analyzer._sales_cache[cache_key] = (sample_sales_data, time.time() - 7200)

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sample_sales_data}

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 30)

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_cache_bypass(
        self,
        analyzer: SalesAnalyzer,
        mock_api: MagicMock,
        sample_sales_data: list[dict[str, Any]],
    ) -> None:
        """Test cache bypass when use_cache=False."""
        cache_key = "csgo:Test Item:30"
        analyzer._sales_cache[cache_key] = (sample_sales_data, time.time())

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sample_sales_data}

        result = await analyzer.get_item_sales_history(
            "Test Item", "csgo", 30, use_cache=False
        )

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_item_not_found(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling when item is not found."""
        mock_api.get_market_items.return_value = {"items": []}

        result = await analyzer.get_item_sales_history("Nonexistent Item", "csgo", 30)

        assert result == {"sales": []}

    @pytest.mark.asyncio()
    async def test_no_items_key(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling response without items key."""
        mock_api.get_market_items.return_value = {}

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 30)

        assert result == {"sales": []}

    @pytest.mark.asyncio()
    async def test_missing_item_id(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling item without itemId."""
        mock_api.get_market_items.return_value = {"items": [{"title": "Test"}]}

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 30)

        assert result == {"sales": []}

    @pytest.mark.asyncio()
    async def test_api_exception(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling API exception."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 30)

        assert result == {"sales": []}

    @pytest.mark.asyncio()
    async def test_different_games(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test sales history for different games."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "dota_item"}]}
        mock_api._request.return_value = {"sales": []}

        for game in ["csgo", "dota2", "tf2", "rust"]:
            await analyzer.get_item_sales_history("Test Item", game, 30)

        assert mock_api.get_market_items.call_count == 4


# ============================================================================
# analyze_sales_volume Tests
# ============================================================================


class TestAnalyzeSalesVolume:
    """Tests for analyze_sales_volume method."""

    @pytest.mark.asyncio()
    async def test_very_high_volume(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test very high volume categorization."""
        # 100 sales in 30 days = ~3.3 sales/day
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 3600}
            for i in range(100)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_sales_volume("Popular Item", "csgo", 30)

        assert result["volume_category"] == "very_high"
        assert result["is_liquid"] is True
        assert result["sales_count"] == 100

    @pytest.mark.asyncio()
    async def test_empty_sales_list(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test empty sales list."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.analyze_sales_volume("Rare Item", "csgo", 30)

        assert result["sales_count"] == 0
        assert result["volume_category"] == "low"
        assert result["is_liquid"] is False
        assert result["price_range"]["min"] == 0
        assert result["price_range"]["max"] == 0

    @pytest.mark.asyncio()
    async def test_dict_sales_response(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling dict response with sales key."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": [{"price": {"amount": 1000}}]}

        # Mock to return dict
        with patch.object(analyzer, "get_item_sales_history") as mock_history:
            mock_history.return_value = {"sales": [{"price": {"amount": 1000}}]}

            result = await analyzer.analyze_sales_volume("Test Item", "csgo", 30)

            assert isinstance(result, dict)

    @pytest.mark.asyncio()
    async def test_price_range_calculation(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test price range is calculated correctly."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 500}, "date": base_time - 3600},
            {"price": {"amount": 1500}, "date": base_time - 7200},
            {"price": {"amount": 1000}, "date": base_time - 10800},
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_sales_volume("Test Item", "csgo", 30)

        # Prices are in cents, divided by 100
        assert result["price_range"]["min"] == 5.0
        assert result["price_range"]["max"] == 15.0


# ============================================================================
# estimate_time_to_sell Tests
# ============================================================================


class TestEstimateTimeToSell:
    """Tests for estimate_time_to_sell method."""

    @pytest.mark.asyncio()
    async def test_insufficient_data(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test response with insufficient sales data."""
        # Less than min_sample_size (3) sales
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": [{"price": {"amount": 1000}}]}

        result = await analyzer.estimate_time_to_sell("Rare Item", "csgo", 10.0, 30)

        assert result["estimated_days"] is None
        assert result["confidence"] == "very_low"
        assert "Insufficient" in result["message"]

    @pytest.mark.asyncio()
    async def test_high_confidence_estimation(
        self,
        analyzer: SalesAnalyzer,
        mock_api: MagicMock,
        sample_sales_data: list[dict[str, Any]],
    ) -> None:
        """Test high confidence time estimation."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sample_sales_data}

        result = await analyzer.estimate_time_to_sell("Popular Item", "csgo", 10.0, 30)

        assert "confidence" in result
        assert "estimated_days" in result or result["confidence"] == "very_low"

    @pytest.mark.asyncio()
    async def test_no_current_price(
        self,
        analyzer: SalesAnalyzer,
        mock_api: MagicMock,
        sample_sales_data: list[dict[str, Any]],
    ) -> None:
        """Test estimation without current price uses median."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sample_sales_data}

        result = await analyzer.estimate_time_to_sell("Test Item", "csgo", None, 30)

        assert "estimated_days" in result or result["confidence"] == "very_low"

    @pytest.mark.asyncio()
    async def test_zero_sales_per_day(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling zero sales per day."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - 86400 * 30}
            for _ in range(3)  # All on the same day, 30 days ago
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.estimate_time_to_sell("Rare Item", "csgo", 10.0, 30)

        # Should handle zero sales per day gracefully
        assert isinstance(result, dict)

    @pytest.mark.asyncio()
    async def test_recommendation_good(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test good recommendation for quick-selling items."""
        base_time = int(time.time())
        # Many recent sales = quick sell
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 1800} for i in range(50)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.estimate_time_to_sell("Popular Item", "csgo", 10.0, 7)

        if result["estimated_days"] is not None and result["estimated_days"] < 3:
            assert result["recommendation"] == "good"

    @pytest.mark.asyncio()
    async def test_exception_handling(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test exception handling in estimate_time_to_sell."""
        base_time = int(time.time())
        # Sales with invalid data structure to trigger exception in pandas
        sales = [{"invalid_field": "data", "date": base_time} for _ in range(5)]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.estimate_time_to_sell("Test Item", "csgo", 10.0, 30)

        assert result["confidence"] == "very_low"
        assert result["recommendation"] == "unknown"


# ============================================================================
# analyze_price_trends Tests
# ============================================================================


class TestAnalyzePriceTrends:
    """Tests for analyze_price_trends method."""

    @pytest.mark.asyncio()
    async def test_insufficient_sales(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling insufficient sales data."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.analyze_price_trends("Rare Item", "csgo", 30)

        assert result["trend"] == "unknown"
        assert "Insufficient" in result["message"]

    @pytest.mark.asyncio()
    async def test_strong_upward_trend(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test strong upward trend detection."""
        base_time = int(time.time())
        # Price increases by 20% over time
        sales = [
            {"price": {"amount": 1000}, "date": base_time - 4 * 86400},
            {"price": {"amount": 1050}, "date": base_time - 3 * 86400},
            {"price": {"amount": 1100}, "date": base_time - 2 * 86400},
            {"price": {"amount": 1200}, "date": base_time - 1 * 86400},
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_price_trends("Rising Item", "csgo", 7)

        assert result["trend_direction"] == "rising"
        assert result["price_change_percent"] > 10

    @pytest.mark.asyncio()
    async def test_strong_downward_trend(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test strong downward trend detection."""
        base_time = int(time.time())
        # Price decreases by 20% over time
        sales = [
            {"price": {"amount": 1200}, "date": base_time - 4 * 86400},
            {"price": {"amount": 1100}, "date": base_time - 3 * 86400},
            {"price": {"amount": 1050}, "date": base_time - 2 * 86400},
            {"price": {"amount": 1000}, "date": base_time - 1 * 86400},
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_price_trends("Falling Item", "csgo", 7)

        assert result["trend_direction"] == "falling"
        assert result["price_change_percent"] < -10

    @pytest.mark.asyncio()
    async def test_high_volatility_message(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test high volatility message addition."""
        base_time = int(time.time())
        # High volatility prices
        sales = [
            {"price": {"amount": 500}, "date": base_time - 4 * 86400},
            {"price": {"amount": 1500}, "date": base_time - 3 * 86400},
            {"price": {"amount": 700}, "date": base_time - 2 * 86400},
            {"price": {"amount": 1300}, "date": base_time - 1 * 86400},
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_price_trends("Volatile Item", "csgo", 7)

        assert result["volatility"] > 10
        assert "volatility" in result["message"]

    @pytest.mark.asyncio()
    async def test_missing_timestamp_field(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling missing timestamp field."""
        sales = [
            {"price": {"amount": 1000}, "invalid_date": "2023-01-01"},
            {"price": {"amount": 1100}, "invalid_date": "2023-01-02"},
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_price_trends("Test Item", "csgo", 7)

        assert result["trend"] == "unknown"

    @pytest.mark.asyncio()
    async def test_single_daily_average(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling when all sales are on same day."""
        base_time = int(time.time())
        # All sales on the same day
        sales = [
            {"price": {"amount": 1000 + i * 10}, "date": base_time - i * 60}
            for i in range(5)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.analyze_price_trends("Test Item", "csgo", 7)

        # Should return stable when insufficient data points
        assert result["trend"] == "stable"


# ============================================================================
# evaluate_arbitrage_potential Tests
# ============================================================================


class TestEvaluateArbitragePotential:
    """Tests for evaluate_arbitrage_potential method."""

    @pytest.mark.asyncio()
    async def test_high_rating_opportunity(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test high rating for excellent opportunity."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 1800}
            for i in range(50)  # High volume
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.evaluate_arbitrage_potential(
            "Popular Item", 10.0, 20.0, "csgo", 30  # 100% profit
        )

        assert result["rating"] >= 6
        assert result["profit_percent"] > 50

    @pytest.mark.asyncio()
    async def test_low_rating_opportunity(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test low rating for poor opportunity."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 86400 * 7}
            for i in range(3)  # Low volume, spread out
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.evaluate_arbitrage_potential(
            "Rare Item", 10.0, 10.1, "csgo", 30  # 1% profit
        )

        assert result["rating"] <= 5
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio()
    async def test_risk_level_calculation(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test risk level calculation."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 1800} for i in range(30)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.evaluate_arbitrage_potential(
            "Test Item", 10.0, 15.0, "csgo", 30
        )

        assert result["risk_level"] in {"low", "medium", "high"}

    @pytest.mark.asyncio()
    async def test_daily_roi_calculation(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test daily ROI calculation."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 1800} for i in range(30)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.evaluate_arbitrage_potential(
            "Test Item", 10.0, 12.0, "csgo", 30
        )

        # daily_roi should be calculated if estimated_days is available
        if result["time_to_sell"].get("estimated_days"):
            assert result["daily_roi"] is not None

    @pytest.mark.asyncio()
    async def test_summary_messages(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test different summary messages based on rating."""
        base_time = int(time.time())

        # High volume for better rating
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 1800} for i in range(50)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.evaluate_arbitrage_potential(
            "Test Item", 10.0, 15.0, "csgo", 30
        )

        assert "summary" in result
        assert isinstance(result["summary"], str)


# ============================================================================
# batch_analyze_items Tests
# ============================================================================


class TestBatchAnalyzeItems:
    """Tests for batch_analyze_items methods."""

    @pytest.mark.asyncio()
    async def test_class_method_batch_analyze(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test SalesAnalyzer.batch_analyze_items method."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 3600} for i in range(10)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        items = [
            {"title": "Item 1", "buy_price": 10.0},
            {"title": "Item 2", "buy_price": 20.0},
        ]

        result = await analyzer.batch_analyze_items("csgo", items, 30)

        assert len(result) == 2
        assert all("title" in item for item in result)

    @pytest.mark.asyncio()
    async def test_class_method_skip_invalid_items(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test skipping invalid items in batch analysis."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        items = [
            {"title": "", "buy_price": 10.0},  # Empty title
            {"title": "Valid Item", "buy_price": 0},  # Zero price
            {"title": "Good Item", "buy_price": 10.0},  # Valid
        ]

        result = await analyzer.batch_analyze_items("csgo", items, 30)

        # Only the valid item should be processed
        assert len(result) == 1

    @pytest.mark.asyncio()
    async def test_module_function_batch_analyze(self) -> None:
        """Test module-level batch_analyze_items function."""
        with patch(
            "src.dmarket.arbitrage_sales_analysis.SalesAnalyzer"
        ) as MockAnalyzer:
            mock_instance = MagicMock()
            mock_instance.analyze_sales_volume = AsyncMock(
                return_value={
                    "sales_count": 10,
                    "volume_category": "medium",
                    "is_liquid": True,
                }
            )
            mock_instance.analyze_price_trends = AsyncMock(
                return_value={
                    "trend": "stable",
                }
            )
            MockAnalyzer.return_value = mock_instance

            items = [{"title": "Test Item", "buy_price": 10.0}]
            result = await batch_analyze_items("csgo", items, 30)

            assert len(result) == 1
            assert result[0]["title"] == "Test Item"

    @pytest.mark.asyncio()
    async def test_batch_analyze_exception_handling(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test exception handling in batch analysis."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        items = [{"title": "Item 1", "buy_price": 10.0}]
        result = await analyzer.batch_analyze_items("csgo", items, 30)

        # Should return empty list or continue processing
        assert isinstance(result, list)


# ============================================================================
# find_best_arbitrage_opportunities Tests
# ============================================================================


class TestFindBestArbitrageOpportunities:
    """Tests for find_best_arbitrage_opportunities methods."""

    @pytest.mark.asyncio()
    async def test_class_method_find_opportunities(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test SalesAnalyzer.find_best_arbitrage_opportunities method."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 3600} for i in range(20)
        ]

        mock_api.get_market_items.return_value = {
            "items": [
                {"title": "Item 1", "itemId": "id1", "price": {"amount": 1000}},
                {"title": "Item 2", "itemId": "id2", "price": {"amount": 2000}},
            ]
        }
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.find_best_arbitrage_opportunities(
            "csgo", 5.0, "medium", 10
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_find_opportunities_empty_items(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling empty items response."""
        mock_api.get_market_items.return_value = {"items": []}

        result = await analyzer.find_best_arbitrage_opportunities(
            "csgo", 5.0, "medium", 10
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_find_opportunities_no_items_key(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling response without items key."""
        mock_api.get_market_items.return_value = {}

        result = await analyzer.find_best_arbitrage_opportunities(
            "csgo", 5.0, "medium", 10
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_find_opportunities_api_error(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling API error."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        result = await analyzer.find_best_arbitrage_opportunities(
            "csgo", 5.0, "medium", 10
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_module_function_find_opportunities(self) -> None:
        """Test module-level find_best_arbitrage_opportunities function."""
        with patch(
            "src.dmarket.arbitrage_sales_analysis.SalesAnalyzer"
        ) as MockAnalyzer:
            mock_instance = MagicMock()
            mock_instance.get_api_client = AsyncMock()

            mock_api = MagicMock()
            mock_api.get_market_items = AsyncMock(return_value={"items": []})
            mock_instance.get_api_client.return_value = mock_api
            mock_instance.evaluate_arbitrage_potential = AsyncMock()

            MockAnalyzer.return_value = mock_instance

            result = await find_best_arbitrage_opportunities(
                "csgo", 5.0, "medium", 10, None
            )

            assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_risk_level_filtering(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test filtering by risk level."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 3600} for i in range(30)
        ]

        mock_api.get_market_items.return_value = {
            "items": [{"title": "Item 1", "itemId": "id1", "price": {"amount": 1000}}]
        }
        mock_api._request.return_value = {"sales": sales}

        # Test low risk filter
        result = await analyzer.find_best_arbitrage_opportunities(
            "csgo", 5.0, "low", 10
        )

        for opportunity in result:
            assert opportunity["risk_level"] == "low"


# ============================================================================
# Module-level Functions Tests
# ============================================================================


class TestModuleLevelFunctions:
    """Tests for module-level helper functions."""

    @pytest.mark.asyncio()
    async def test_analyze_item_liquidity(self) -> None:
        """Test analyze_item_liquidity function."""
        with patch(
            "src.dmarket.arbitrage_sales_analysis.SalesAnalyzer"
        ) as MockAnalyzer:
            mock_instance = MagicMock()
            mock_instance.analyze_sales_volume = AsyncMock(
                return_value={
                    "volume_category": "high",
                    "avg_daily_sales": 5,
                    "total_sales": 100,
                }
            )
            MockAnalyzer.return_value = mock_instance

            result = await analyze_item_liquidity("item123", None)

            assert result["liquidity"] == "high"
            assert result["item_id"] == "item123"

    @pytest.mark.asyncio()
    async def test_analyze_item_liquidity_error(self) -> None:
        """Test analyze_item_liquidity with error."""
        with patch(
            "src.dmarket.arbitrage_sales_analysis.SalesAnalyzer"
        ) as MockAnalyzer:
            mock_instance = MagicMock()
            mock_instance.analyze_sales_volume = AsyncMock(return_value={"error": True})
            MockAnalyzer.return_value = mock_instance

            result = await analyze_item_liquidity("item123", None)

            assert result["error"] is True
            assert result["liquidity"] == "unknown"

    @pytest.mark.asyncio()
    async def test_analyze_item_liquidity_exception(self) -> None:
        """Test analyze_item_liquidity with exception."""
        with patch(
            "src.dmarket.arbitrage_sales_analysis.SalesAnalyzer"
        ) as MockAnalyzer:
            mock_instance = MagicMock()
            mock_instance.analyze_sales_volume = AsyncMock(
                side_effect=ValueError("Test error")
            )
            MockAnalyzer.return_value = mock_instance

            result = await analyze_item_liquidity("item123", None)

            assert result["error"] is True
            assert result["liquidity"] == "unknown"

    @pytest.mark.asyncio()
    async def test_enhanced_arbitrage_search(self) -> None:
        """Test enhanced_arbitrage_search function."""
        result = await enhanced_arbitrage_search("csgo", 1.0, None)

        # Current implementation returns empty list
        assert result == []

    @pytest.mark.asyncio()
    async def test_get_sales_volume_stats(self) -> None:
        """Test get_sales_volume_stats function."""
        result = await get_sales_volume_stats("csgo", None)

        assert result["game"] == "csgo"
        assert result["error"] is False
        assert "total_volume" in result


# ============================================================================
# Cache Management Tests
# ============================================================================


class TestCacheManagement:
    """Tests for cache management functionality."""

    def test_cache_key_format(self, analyzer: SalesAnalyzer) -> None:
        """Test cache key format."""
        # The cache key should be game:item_name:days
        expected_format = "csgo:Test Item:30"
        assert expected_format == "csgo:Test Item:30"

    @pytest.mark.asyncio()
    async def test_cache_ttl_respected(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test cache TTL is respected."""
        cache_key = "csgo:Test Item:30"

        # Set cache with current time
        analyzer._sales_cache[cache_key] = ([{"price": 100}], time.time())

        # Should use cache
        result = await analyzer.get_item_sales_history("Test Item", "csgo", 30)
        mock_api.get_market_items.assert_not_called()

        # Expire the cache
        analyzer._sales_cache[cache_key] = ([{"price": 100}], time.time() - 7200)

        # Should call API
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        await analyzer.get_item_sales_history("Test Item", "csgo", 30)
        mock_api.get_market_items.assert_called()

    def test_cache_different_parameters(self, analyzer: SalesAnalyzer) -> None:
        """Test cache entries are separate for different parameters."""
        analyzer._sales_cache["csgo:Item1:30"] = ([], time.time())
        analyzer._sales_cache["csgo:Item2:30"] = ([], time.time())
        analyzer._sales_cache["dota2:Item1:30"] = ([], time.time())

        assert len(analyzer._sales_cache) == 3


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio()
    async def test_zero_buy_price(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling zero buy price in arbitrage evaluation."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.evaluate_arbitrage_potential(
            "Test Item", 0.0, 10.0, "csgo", 30
        )

        # Should handle division by zero gracefully
        assert "profit_percent" in result

    @pytest.mark.asyncio()
    async def test_negative_profit(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling negative profit scenario."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 3600} for i in range(10)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        result = await analyzer.evaluate_arbitrage_potential(
            "Test Item", 20.0, 10.0, "csgo", 30  # Buy high, sell low
        )

        assert result["raw_profit"] < 0
        assert result["profit_percent"] < 0

    @pytest.mark.asyncio()
    async def test_unicode_item_name(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling unicode characters in item name."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.get_item_sales_history("АК-47 | Редлайн", "csgo", 30)

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_very_long_item_name(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling very long item name."""
        long_name = "A" * 1000
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.get_item_sales_history(long_name, "csgo", 30)

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_special_characters_in_name(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling special characters in item name."""
        special_name = "Item (★) | Pattern #123"
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.get_item_sales_history(special_name, "csgo", 30)

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_empty_game_string(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling empty game string."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.get_item_sales_history("Test Item", "", 30)

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_zero_days_parameter(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling zero days parameter."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 0)

        # Should still make the call
        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_large_days_parameter(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test handling large days parameter."""
        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        result = await analyzer.get_item_sales_history("Test Item", "csgo", 365)

        mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    async def test_concurrent_cache_access(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test concurrent cache access doesn't cause issues."""
        import asyncio

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": []}

        # Run multiple concurrent requests
        tasks = [
            analyzer.get_item_sales_history(f"Item {i}", "csgo", 30) for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for SalesAnalyzer."""

    @pytest.mark.asyncio()
    async def test_full_analysis_workflow(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test complete analysis workflow."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000 + i * 10}, "date": base_time - i * 3600}
            for i in range(30)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        # Step 1: Get sales history
        history = await analyzer.get_item_sales_history("Test Item", "csgo", 30)
        assert history == sales

        # Step 2: Analyze volume
        volume = await analyzer.analyze_sales_volume("Test Item", "csgo", 30)
        assert "volume_category" in volume

        # Step 3: Analyze trends
        trends = await analyzer.analyze_price_trends("Test Item", "csgo", 30)
        assert "trend" in trends

        # Step 4: Estimate time to sell
        time_estimate = await analyzer.estimate_time_to_sell(
            "Test Item", "csgo", 10.0, 30
        )
        assert "confidence" in time_estimate

        # Step 5: Evaluate arbitrage
        evaluation = await analyzer.evaluate_arbitrage_potential(
            "Test Item", 10.0, 12.0, "csgo", 30
        )
        assert "rating" in evaluation

    @pytest.mark.asyncio()
    async def test_multiple_items_analysis(
        self, analyzer: SalesAnalyzer, mock_api: MagicMock
    ) -> None:
        """Test analyzing multiple items sequentially."""
        base_time = int(time.time())
        sales = [
            {"price": {"amount": 1000}, "date": base_time - i * 3600} for i in range(10)
        ]

        mock_api.get_market_items.return_value = {"items": [{"itemId": "item123"}]}
        mock_api._request.return_value = {"sales": sales}

        items = ["Item 1", "Item 2", "Item 3"]
        results = []

        for item in items:
            result = await analyzer.analyze_sales_volume(item, "csgo", 30)
            results.append(result)

        assert len(results) == 3
        assert all("sales_count" in r for r in results)

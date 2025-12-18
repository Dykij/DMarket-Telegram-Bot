"""Extended tests for sales_history module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time
from pathlib import Path

from src.dmarket.sales_history import (
    SALES_HISTORY_TYPES,
    CACHE_TTL,
    get_item_sales_history,
    detect_price_anomalies,
    calculate_price_trend,
    get_market_trend_overview,
    _extract_price_from_item,
    _calculate_median,
    _calculate_std_dev,
    _get_cache_file_path,
    get_sales_history,
    analyze_sales_history,
    execute_api_request,
    get_arbitrage_opportunities_with_sales_history,
)


class TestSalesHistoryConstants:
    """Tests for sales_history constants."""

    def test_sales_history_types(self):
        """Test SALES_HISTORY_TYPES constant."""
        assert "last_day" in SALES_HISTORY_TYPES
        assert "last_week" in SALES_HISTORY_TYPES
        assert "last_month" in SALES_HISTORY_TYPES
        assert "last_hour" in SALES_HISTORY_TYPES
        assert "last_12_hours" in SALES_HISTORY_TYPES
        assert SALES_HISTORY_TYPES["last_day"] == "24h"
        assert SALES_HISTORY_TYPES["last_week"] == "7d"

    def test_cache_ttl(self):
        """Test CACHE_TTL constant."""
        assert "1h" in CACHE_TTL
        assert "12h" in CACHE_TTL
        assert "24h" in CACHE_TTL
        assert "7d" in CACHE_TTL
        assert "30d" in CACHE_TTL
        assert CACHE_TTL["1h"] == 15 * 60  # 15 minutes
        assert CACHE_TTL["24h"] == 60 * 60  # 1 hour


class TestMathFunctions:
    """Tests for math helper functions."""

    def test_calculate_median_empty(self):
        """Test median with empty list."""
        result = _calculate_median([])
        assert result == 0

    def test_calculate_median_single(self):
        """Test median with single element."""
        result = _calculate_median([5.0])
        assert result == 5.0

    def test_calculate_median_odd_count(self):
        """Test median with odd number of elements."""
        result = _calculate_median([1.0, 3.0, 5.0])
        assert result == 3.0

    def test_calculate_median_even_count(self):
        """Test median with even number of elements."""
        result = _calculate_median([1.0, 2.0, 3.0, 4.0])
        assert result == 2.5

    def test_calculate_median_unsorted(self):
        """Test median with unsorted list."""
        result = _calculate_median([5.0, 1.0, 3.0])
        assert result == 3.0

    def test_calculate_std_dev_empty(self):
        """Test standard deviation with empty list."""
        result = _calculate_std_dev([])
        assert result == 0

    def test_calculate_std_dev_single(self):
        """Test standard deviation with single element."""
        result = _calculate_std_dev([5.0])
        assert result == 0

    def test_calculate_std_dev_same_values(self):
        """Test standard deviation with same values."""
        result = _calculate_std_dev([5.0, 5.0, 5.0])
        assert result == 0

    def test_calculate_std_dev_normal(self):
        """Test standard deviation with normal values."""
        result = _calculate_std_dev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
        assert result > 0


class TestExtractPriceFromItem:
    """Tests for _extract_price_from_item function."""

    def test_extract_sales_price(self):
        """Test extracting price from salesPrice field."""
        item = {"salesPrice": 1000}  # $10
        result = _extract_price_from_item(item)
        assert result == 10.0

    def test_extract_price_usd(self):
        """Test extracting price from price.USD field."""
        item = {"price": {"USD": 1500}}  # $15
        result = _extract_price_from_item(item)
        assert result == 15.0

    def test_extract_price_missing(self):
        """Test extracting price when both fields missing."""
        item = {"title": "Test Item"}
        result = _extract_price_from_item(item)
        assert result == 0

    def test_extract_price_invalid(self):
        """Test extracting price with invalid data."""
        item = {"price": "invalid"}
        result = _extract_price_from_item(item)
        assert result == 0


class TestGetCacheFilePath:
    """Tests for _get_cache_file_path function."""

    def test_cache_file_path_normal(self):
        """Test normal cache file path."""
        path = _get_cache_file_path("AK-47 | Redline", "csgo", "24h")
        assert isinstance(path, Path)
        assert "csgo" in str(path)
        assert "24h" in str(path)

    def test_cache_file_path_special_chars(self):
        """Test cache file path with special characters."""
        path = _get_cache_file_path("Item (FT) | Special★", "csgo", "7d")
        assert isinstance(path, Path)
        # Special chars should be replaced with underscores
        assert "★" not in str(path)


class TestGetItemSalesHistory:
    """Tests for get_item_sales_history function."""

    @pytest.mark.asyncio
    async def test_get_sales_history_cached(self):
        """Test getting cached sales history."""
        with patch("src.dmarket.sales_history._load_from_cache") as mock_cache:
            mock_cache.return_value = [{"price": 10.0, "timestamp": 123456}]
            
            result = await get_item_sales_history(
                item_name="Test Item",
                game="csgo",
                period="24h",
                use_cache=True
            )
            
            assert len(result) == 1
            assert result[0]["price"] == 10.0

    @pytest.mark.asyncio
    async def test_get_sales_history_invalid_period(self):
        """Test with invalid period defaults to 24h."""
        with patch("src.dmarket.sales_history._load_from_cache") as mock_cache:
            mock_cache.return_value = []
            
            mock_api = AsyncMock()
            mock_api.get_item_price_history = AsyncMock(return_value=[])
            
            await get_item_sales_history(
                item_name="Test Item",
                game="csgo",
                period="invalid",  # Invalid period
                use_cache=True,
                dmarket_api=mock_api
            )
            # Should not raise error, defaults to 24h


class TestDetectPriceAnomalies:
    """Tests for detect_price_anomalies function."""

    @pytest.mark.asyncio
    async def test_detect_anomalies_no_history(self):
        """Test anomaly detection with no sales history."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = []
            
            result = await detect_price_anomalies("Test Item", "csgo")
            
            assert result["anomalies"] == []
            assert result["average_price"] == 0
            assert result["num_sales"] == 0

    @pytest.mark.asyncio
    async def test_detect_anomalies_normal_prices(self):
        """Test anomaly detection with normal prices."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 10.5, "timestamp": 200},
            {"price": 9.5, "timestamp": 300}
        ]
        
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales
            
            result = await detect_price_anomalies(
                "Test Item", "csgo", threshold_percent=20.0
            )
            
            assert len(result["anomalies"]) == 0
            assert result["num_sales"] == 3

    @pytest.mark.asyncio
    async def test_detect_anomalies_with_outlier(self):
        """Test anomaly detection with outlier price."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 10.0, "timestamp": 200},
            {"price": 50.0, "timestamp": 300}  # Outlier
        ]
        
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales
            
            result = await detect_price_anomalies(
                "Test Item", "csgo", threshold_percent=20.0
            )
            
            assert len(result["anomalies"]) > 0
            assert result["anomalies"][0]["is_high"] is True


class TestCalculatePriceTrend:
    """Tests for calculate_price_trend function."""

    @pytest.mark.asyncio
    async def test_price_trend_insufficient_data(self):
        """Test price trend with insufficient data."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = [{"price": 10.0, "timestamp": 100}]
            
            result = await calculate_price_trend("Test Item", "csgo")
            
            assert result["trend"] == "unknown"
            assert result["change_percent"] == 0

    @pytest.mark.asyncio
    async def test_price_trend_stable(self):
        """Test stable price trend."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 10.2, "timestamp": 200},
            {"price": 10.1, "timestamp": 300}
        ]
        
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales
            
            result = await calculate_price_trend("Test Item", "csgo")
            
            assert result["trend"] == "stable"

    @pytest.mark.asyncio
    async def test_price_trend_up(self):
        """Test upward price trend."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 12.0, "timestamp": 200},
            {"price": 15.0, "timestamp": 300}
        ]
        
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales
            
            result = await calculate_price_trend("Test Item", "csgo")
            
            assert result["trend"] == "up"
            assert result["change_percent"] > 0

    @pytest.mark.asyncio
    async def test_price_trend_down(self):
        """Test downward price trend."""
        sales = [
            {"price": 15.0, "timestamp": 100},
            {"price": 12.0, "timestamp": 200},
            {"price": 10.0, "timestamp": 300}
        ]
        
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales
            
            result = await calculate_price_trend("Test Item", "csgo")
            
            assert result["trend"] == "down"
            assert result["change_percent"] < 0


class TestGetSalesHistory:
    """Tests for get_sales_history compatibility function."""

    @pytest.mark.asyncio
    async def test_get_sales_history_empty_items(self):
        """Test with empty items list."""
        result = await get_sales_history([])
        
        assert result["LastSales"] == []
        assert result["Total"] == 0

    @pytest.mark.asyncio
    async def test_get_sales_history_with_api_client(self):
        """Test with API client."""
        mock_api = AsyncMock()
        mock_api.request = AsyncMock(return_value={
            "LastSales": [{"price": {"USD": 1000}}]
        })
        
        result = await get_sales_history(["Test Item"], api_client=mock_api)
        
        assert "LastSales" in result
        mock_api.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sales_history_api_error(self):
        """Test with API error response."""
        mock_api = AsyncMock()
        mock_api.request = AsyncMock(return_value={"Error": "API Error"})
        
        result = await get_sales_history(["Test Item"], api_client=mock_api)
        
        assert "Error" in result


class TestAnalyzeSalesHistory:
    """Tests for analyze_sales_history compatibility function."""

    @pytest.mark.asyncio
    async def test_analyze_no_data(self):
        """Test analysis with no data."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {"LastSales": [], "Total": 0}
            
            result = await analyze_sales_history("Test Item")
            
            assert result["item_name"] == "Test Item"
            assert result["has_data"] is False
            assert result["total_sales"] == 0

    @pytest.mark.asyncio
    async def test_analyze_with_sales(self):
        """Test analysis with sales data."""
        sales = [
            {"price": {"USD": 1000}, "date": 100},
            {"price": {"USD": 1100}, "date": 200}
        ]
        
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {"LastSales": sales, "Total": 2}
            
            result = await analyze_sales_history("Test Item", days=7)
            
            assert result["item_name"] == "Test Item"
            assert result["has_data"] is True
            assert result["total_sales"] == 2

    @pytest.mark.asyncio
    async def test_analyze_price_trend_up(self):
        """Test analysis detects upward price trend."""
        sales = [
            {"price": {"USD": 1000}, "date": 100},
            {"price": {"USD": 1500}, "date": 200}  # 50% increase
        ]
        
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {"LastSales": sales, "Total": 2}
            
            result = await analyze_sales_history("Test Item")
            
            assert result["price_trend"] == "up"

    @pytest.mark.asyncio
    async def test_analyze_api_error(self):
        """Test analysis with API error."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {"Error": "API Error", "LastSales": [], "Total": 0}
            
            result = await analyze_sales_history("Test Item")
            
            assert result["has_data"] is False
            assert "error" in result


class TestExecuteApiRequest:
    """Tests for execute_api_request compatibility function."""

    @pytest.mark.asyncio
    async def test_execute_request_with_client(self):
        """Test execute request with API client."""
        mock_api = AsyncMock()
        mock_api.request = AsyncMock(return_value={"data": "test"})
        
        result = await execute_api_request(
            endpoint="/test",
            params={"key": "value"},
            api_client=mock_api
        )
        
        assert result["data"] == "test"
        mock_api.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_request_exception(self):
        """Test execute request with exception."""
        mock_api = AsyncMock()
        mock_api.request = AsyncMock(side_effect=Exception("Test Error"))
        
        result = await execute_api_request("/test", api_client=mock_api)
        
        assert "Error" in result


class TestGetArbitrageOpportunitiesWithSalesHistory:
    """Tests for get_arbitrage_opportunities_with_sales_history function."""

    @pytest.mark.asyncio
    async def test_get_opportunities_filtered(self):
        """Test getting filtered arbitrage opportunities."""
        arbitrage_items = [
            {"market_hash_name": "Item1", "profit": 5.0},
            {"market_hash_name": "Item2", "profit": 10.0}
        ]
        
        analysis = {
            "has_data": True,
            "sales_per_day": 2.0,
            "price_trend": "stable"
        }
        
        with patch("src.dmarket.sales_history.find_arbitrage_items") as mock_arb:
            mock_arb.return_value = arbitrage_items
            
            with patch("src.dmarket.sales_history.analyze_sales_history") as mock_analyze:
                mock_analyze.return_value = analysis
                
                result = await get_arbitrage_opportunities_with_sales_history(
                    min_sales_per_day=1.0
                )
                
                # Both items should pass the filter
                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_opportunities_price_trend_filter(self):
        """Test filtering by price trend."""
        arbitrage_items = [
            {"market_hash_name": "Item1", "profit": 5.0}
        ]
        
        analysis = {
            "has_data": True,
            "sales_per_day": 2.0,
            "price_trend": "down"  # Not matching filter
        }
        
        with patch("src.dmarket.sales_history.find_arbitrage_items") as mock_arb:
            mock_arb.return_value = arbitrage_items
            
            with patch("src.dmarket.sales_history.analyze_sales_history") as mock_analyze:
                mock_analyze.return_value = analysis
                
                result = await get_arbitrage_opportunities_with_sales_history(
                    min_sales_per_day=1.0,
                    price_trend_filter="up"  # Filter for upward trend
                )
                
                assert len(result) == 0

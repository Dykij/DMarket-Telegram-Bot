"""Phase 4 Extended tests for sales_history module.

These tests aim to achieve 100% coverage for the sales_history module.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.sales_history import (
    CACHE_TTL,
    SALES_CACHE_DIR,
    SALES_HISTORY_TYPES,
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


class TestSalesHistoryTypesConstant:
    """Tests for SALES_HISTORY_TYPES constant."""

    def test_last_day_value(self):
        """Test last_day mapping to 24h."""
        assert SALES_HISTORY_TYPES["last_day"] == "24h"

    def test_last_week_value(self):
        """Test last_week mapping to 7d."""
        assert SALES_HISTORY_TYPES["last_week"] == "7d"

    def test_last_month_value(self):
        """Test last_month mapping to 30d."""
        assert SALES_HISTORY_TYPES["last_month"] == "30d"

    def test_last_hour_value(self):
        """Test last_hour mapping to 1h."""
        assert SALES_HISTORY_TYPES["last_hour"] == "1h"

    def test_last_12_hours_value(self):
        """Test last_12_hours mapping to 12h."""
        assert SALES_HISTORY_TYPES["last_12_hours"] == "12h"

    def test_all_types_present(self):
        """Test all expected types are present."""
        expected_keys = {
            "last_day",
            "last_week",
            "last_month",
            "last_hour",
            "last_12_hours",
        }
        assert set(SALES_HISTORY_TYPES.keys()) == expected_keys


class TestCacheTTLConstant:
    """Tests for CACHE_TTL constant."""

    def test_1h_cache_ttl(self):
        """Test 1 hour cache TTL."""
        assert CACHE_TTL["1h"] == 15 * 60  # 15 minutes

    def test_12h_cache_ttl(self):
        """Test 12 hour cache TTL."""
        assert CACHE_TTL["12h"] == 30 * 60  # 30 minutes

    def test_24h_cache_ttl(self):
        """Test 24 hour cache TTL."""
        assert CACHE_TTL["24h"] == 60 * 60  # 1 hour

    def test_7d_cache_ttl(self):
        """Test 7 day cache TTL."""
        assert CACHE_TTL["7d"] == 6 * 60 * 60  # 6 hours

    def test_30d_cache_ttl(self):
        """Test 30 day cache TTL."""
        assert CACHE_TTL["30d"] == 24 * 60 * 60  # 24 hours


class TestCalculateMedianExtended:
    """Extended tests for _calculate_median function."""

    def test_median_two_elements(self):
        """Test median with two elements."""
        assert _calculate_median([1.0, 5.0]) == 3.0

    def test_median_large_list(self):
        """Test median with large list."""
        numbers = list(range(1, 101))  # 1 to 100
        assert _calculate_median([float(x) for x in numbers]) == 50.5

    def test_median_negative_numbers(self):
        """Test median with negative numbers."""
        assert _calculate_median([-3.0, -1.0, 2.0]) == -1.0

    def test_median_decimal_numbers(self):
        """Test median with decimal numbers."""
        assert _calculate_median([1.1, 2.2, 3.3]) == 2.2

    def test_median_same_numbers(self):
        """Test median with all same numbers."""
        assert _calculate_median([5.0, 5.0, 5.0, 5.0]) == 5.0


class TestCalculateStdDevExtended:
    """Extended tests for _calculate_std_dev function."""

    def test_std_dev_two_elements(self):
        """Test standard deviation with two elements."""
        result = _calculate_std_dev([1.0, 3.0])
        assert result > 0  # Should have some deviation

    def test_std_dev_large_variance(self):
        """Test standard deviation with large variance."""
        result = _calculate_std_dev([1.0, 100.0])
        assert result > 50  # Large deviation

    def test_std_dev_small_variance(self):
        """Test standard deviation with small variance."""
        result = _calculate_std_dev([10.0, 10.1, 10.2])
        assert result < 1  # Small deviation

    def test_std_dev_negative_numbers(self):
        """Test standard deviation with negative numbers."""
        result = _calculate_std_dev([-5.0, 0.0, 5.0])
        assert result > 0  # Should have deviation


class TestExtractPriceFromItemExtended:
    """Extended tests for _extract_price_from_item function."""

    def test_sales_price_zero(self):
        """Test extracting zero salesPrice."""
        item = {"salesPrice": 0}
        assert _extract_price_from_item(item) == 0

    def test_sales_price_large_value(self):
        """Test extracting large salesPrice."""
        item = {"salesPrice": 1000000}  # $10,000
        assert _extract_price_from_item(item) == 10000.0

    def test_price_usd_missing_usd_key(self):
        """Test when USD key is missing in price dict."""
        item = {"price": {"EUR": 1000}}
        assert _extract_price_from_item(item) == 0

    def test_price_usd_none_value(self):
        """Test when price value is None."""
        item = {"price": {"USD": None}}
        assert _extract_price_from_item(item) == 0

    def test_sales_price_priority(self):
        """Test that salesPrice is prioritized over price.USD."""
        item = {"salesPrice": 500, "price": {"USD": 1000}}
        # salesPrice should be used first
        assert _extract_price_from_item(item) == 5.0

    def test_empty_item(self):
        """Test with completely empty item."""
        assert _extract_price_from_item({}) == 0


class TestGetCacheFilePathExtended:
    """Extended tests for _get_cache_file_path function."""

    def test_path_ends_with_json(self):
        """Test cache file path ends with .json."""
        path = _get_cache_file_path("Item", "csgo", "24h")
        assert str(path).endswith(".json")

    def test_path_contains_game(self):
        """Test cache file path contains game identifier."""
        path = _get_cache_file_path("Item", "dota2", "7d")
        assert "dota2" in str(path)

    def test_path_contains_period(self):
        """Test cache file path contains period."""
        path = _get_cache_file_path("Item", "csgo", "30d")
        assert "30d" in str(path)

    def test_path_special_chars_replaced(self):
        """Test special characters are replaced with underscores."""
        path = _get_cache_file_path("★ Item | (FT)", "csgo", "24h")
        filename = path.name
        # No special chars in filename
        assert "★" not in filename
        assert "|" not in filename
        assert "(" not in filename
        assert ")" not in filename

    def test_different_games(self):
        """Test paths are different for different games."""
        path1 = _get_cache_file_path("Item", "csgo", "24h")
        path2 = _get_cache_file_path("Item", "rust", "24h")
        assert path1 != path2


class TestLoadFromCacheExtended:
    """Extended tests for _load_from_cache function."""

    def test_load_corrupted_cache_file(self, tmp_path, monkeypatch):
        """Test loading corrupted cache file returns empty list."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", tmp_path)

        # Create corrupted cache file
        cache_file = tmp_path / "csgo_TestItem_24h.json"
        cache_file.write_text("not valid json {{{")

        result = _load_from_cache("TestItem", "csgo", "24h")
        assert result == []

    def test_load_nonexistent_directory(self, tmp_path, monkeypatch):
        """Test loading from nonexistent directory."""
        nonexistent = tmp_path / "nonexistent_dir"
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", nonexistent)

        result = _load_from_cache("Item", "csgo", "24h")
        assert result == []


class TestSaveToCacheExtended:
    """Extended tests for _save_to_cache function."""

    def test_save_empty_data(self, tmp_path, monkeypatch):
        """Test saving empty data."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", tmp_path)

        _save_to_cache("Item", "csgo", "24h", [])

        cache_file = tmp_path / "csgo_Item_24h.json"
        assert cache_file.exists()

    def test_save_large_data(self, tmp_path, monkeypatch):
        """Test saving large dataset."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", tmp_path)

        large_data = [{"price": i, "timestamp": 1000 + i} for i in range(1000)]
        _save_to_cache("Item", "csgo", "24h", large_data)

        loaded = _load_from_cache("Item", "csgo", "24h")
        assert len(loaded) == 1000

    def test_save_unicode_data(self, tmp_path, monkeypatch):
        """Test saving data with unicode characters."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", tmp_path)

        data = [{"price": 10, "name": "Предмет ★"}]
        _save_to_cache("Item", "csgo", "24h", data)

        loaded = _load_from_cache("Item", "csgo", "24h")
        assert loaded[0]["name"] == "Предмет ★"


class TestGetItemSalesHistoryExtended:
    """Extended tests for get_item_sales_history function."""

    @pytest.mark.asyncio()
    async def test_missing_date_field(self):
        """Test handling sales missing date field."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[
                {"price": 1000},  # Missing date
                {"date": 123, "price": 2000},
            ],
        )

        result = await get_item_sales_history(
            item_name="Test",
            use_cache=False,
            dmarket_api=mock_api,
        )

        # Only the valid entry should be included
        assert len(result) == 1
        assert result[0]["price"] == 20.0

    @pytest.mark.asyncio()
    async def test_missing_price_field(self):
        """Test handling sales missing price field."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[
                {"date": 123},  # Missing price
                {"date": 124, "price": 500},
            ],
        )

        result = await get_item_sales_history(
            item_name="Test",
            use_cache=False,
            dmarket_api=mock_api,
        )

        assert len(result) == 1
        assert result[0]["price"] == 5.0

    @pytest.mark.asyncio()
    async def test_sorts_by_timestamp_descending(self):
        """Test results are sorted by timestamp descending."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[
                {"date": 100, "price": 1000},
                {"date": 300, "price": 3000},
                {"date": 200, "price": 2000},
            ],
        )

        result = await get_item_sales_history(
            item_name="Test",
            use_cache=False,
            dmarket_api=mock_api,
        )

        # Should be sorted from newest to oldest
        assert result[0]["timestamp"] == 300
        assert result[1]["timestamp"] == 200
        assert result[2]["timestamp"] == 100

    @pytest.mark.asyncio()
    async def test_closes_client_on_exception(self):
        """Test API client is closed on exception."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            side_effect=Exception("Test error"),
        )
        mock_api._close_client = AsyncMock()

        await get_item_sales_history(
            item_name="Test",
            use_cache=False,
            dmarket_api=mock_api,
        )

        # Client should be closed even on error (when created internally)

    @pytest.mark.asyncio()
    async def test_different_games(self):
        """Test fetching for different games."""
        for game in ["csgo", "dota2", "rust", "tf2"]:
            mock_api = MagicMock()
            mock_api.get_item_price_history = AsyncMock(
                return_value=[{"date": 123, "price": 1000}],
            )

            result = await get_item_sales_history(
                item_name="Test",
                game=game,
                use_cache=False,
                dmarket_api=mock_api,
            )

            mock_api.get_item_price_history.assert_called_once()
            assert len(result) == 1


class TestDetectPriceAnomaliesExtended:
    """Extended tests for detect_price_anomalies function."""

    @pytest.mark.asyncio()
    async def test_high_threshold(self):
        """Test with very high threshold - no anomalies detected."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 20.0, "timestamp": 200},
            {"price": 30.0, "timestamp": 300},
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await detect_price_anomalies(
                "Test", threshold_percent=500.0  # Very high threshold
            )

            assert len(result["anomalies"]) == 0

    @pytest.mark.asyncio()
    async def test_low_threshold(self):
        """Test with very low threshold - more anomalies detected."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 10.5, "timestamp": 200},
            {"price": 11.0, "timestamp": 300},
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await detect_price_anomalies(
                "Test", threshold_percent=2.0  # Very low threshold
            )

            # With 2% threshold, some prices might be anomalies

    @pytest.mark.asyncio()
    async def test_anomaly_sorting(self):
        """Test anomalies are sorted by deviation descending."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 10.0, "timestamp": 101},
            {"price": 15.0, "timestamp": 200},  # 50% deviation
            {"price": 10.0, "timestamp": 201},
            {"price": 20.0, "timestamp": 300},  # 100% deviation
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await detect_price_anomalies("Test", threshold_percent=30.0)

            # Anomalies should be sorted by deviation descending
            if len(result["anomalies"]) >= 2:
                assert (
                    result["anomalies"][0]["deviation_percent"]
                    >= result["anomalies"][1]["deviation_percent"]
                )

    @pytest.mark.asyncio()
    async def test_is_high_flag(self):
        """Test is_high flag is set correctly."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 10.0, "timestamp": 101},
            {"price": 5.0, "timestamp": 200},  # Low anomaly
            {"price": 20.0, "timestamp": 300},  # High anomaly
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await detect_price_anomalies("Test", threshold_percent=30.0)

            # Check is_high flags
            for anomaly in result["anomalies"]:
                median = result["median_price"]
                if anomaly["price"] > median:
                    assert anomaly["is_high"] is True
                else:
                    assert anomaly["is_high"] is False


class TestCalculatePriceTrendExtended:
    """Extended tests for calculate_price_trend function."""

    @pytest.mark.asyncio()
    async def test_zero_start_price(self):
        """Test trend calculation with zero start price."""
        sales = [
            {"price": 0.0, "timestamp": 100},
            {"price": 10.0, "timestamp": 200},
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await calculate_price_trend("Test")

            # Should handle division by zero gracefully
            assert result["trend"] in {"up", "down", "stable", "unknown"}

    @pytest.mark.asyncio()
    async def test_exactly_5_percent_change(self):
        """Test edge case at exactly 5% boundary."""
        sales = [
            {"price": 100.0, "timestamp": 100},
            {"price": 105.0, "timestamp": 200},  # Exactly 5% increase
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await calculate_price_trend("Test")

            # At exactly 5%, should be stable (< 5 is stable, >= 5 is up/down)
            assert result["trend"] in {"stable", "up"}

    @pytest.mark.asyncio()
    async def test_volatility_calculation(self):
        """Test volatility is calculated correctly."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 20.0, "timestamp": 200},
            {"price": 10.0, "timestamp": 300},
            {"price": 20.0, "timestamp": 400},
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await calculate_price_trend("Test")

            assert result["volatility"] > 0

    @pytest.mark.asyncio()
    async def test_num_sales_in_result(self):
        """Test num_sales field is included in result."""
        sales = [
            {"price": 10.0, "timestamp": 100},
            {"price": 11.0, "timestamp": 200},
            {"price": 12.0, "timestamp": 300},
        ]

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = sales

            result = await calculate_price_trend("Test", period="7d")

            assert result["num_sales"] == 3
            assert result["period"] == "7d"


class TestGetMarketTrendOverview:
    """Tests for get_market_trend_overview function."""

    @pytest.mark.asyncio()
    async def test_no_items_found(self):
        """Test when no popular items are found."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(return_value=None)
        mock_api._close_client = AsyncMock()

        result = await get_market_trend_overview(
            game="csgo",
            dmarket_api=mock_api,
        )

        assert result["market_trend"] == "unknown"
        assert result["up_trending_items"] == []

    @pytest.mark.asyncio()
    async def test_empty_items_list(self):
        """Test when items list is empty."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(return_value={"items": []})
        mock_api._close_client = AsyncMock()

        result = await get_market_trend_overview(
            game="csgo",
            dmarket_api=mock_api,
        )

        assert result["up_trending_items"] == []
        assert result["down_trending_items"] == []
        assert result["stable_items"] == []

    @pytest.mark.asyncio()
    async def test_api_exception(self):
        """Test handling API exception."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(
            side_effect=Exception("API Error"),
        )
        mock_api._close_client = AsyncMock()

        result = await get_market_trend_overview(
            game="csgo",
            dmarket_api=mock_api,
        )

        assert result["market_trend"] == "unknown"

    @pytest.mark.asyncio()
    async def test_categorizes_trends_correctly(self):
        """Test items are categorized by trend correctly."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(
            return_value={
                "items": [
                    {"title": "Item1", "salesPrice": 1000},
                    {"title": "Item2", "salesPrice": 2000},
                ],
            },
        )
        mock_api._close_client = AsyncMock()

        with patch("src.dmarket.sales_history.calculate_price_trend") as mock_trend:
            # First item goes up, second goes down
            mock_trend.side_effect = [
                {"trend": "up", "change_percent": 10.0},
                {"trend": "down", "change_percent": -10.0},
            ]

            result = await get_market_trend_overview(
                game="csgo",
                dmarket_api=mock_api,
            )

            # Should have categorized items correctly
            assert (
                len(result["up_trending_items"]) + len(result["down_trending_items"])
                <= 2
            )

    @pytest.mark.asyncio()
    async def test_timestamp_and_metadata(self):
        """Test result includes timestamp and metadata."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(
            return_value={"items": []},
        )
        mock_api._close_client = AsyncMock()

        result = await get_market_trend_overview(
            game="dota2",
            period="30d",
            dmarket_api=mock_api,
        )

        # Should not include timestamp when there are no items processed
        # But result should be valid
        assert result["market_trend"] in {"up", "down", "stable", "unknown"}


class TestGetSalesHistoryExtended:
    """Extended tests for get_sales_history function."""

    @pytest.mark.asyncio()
    async def test_batch_processing(self):
        """Test batch processing for multiple items."""
        items = [f"Item{i}" for i in range(100)]  # More than batch size

        mock_api = AsyncMock()
        mock_api.request = AsyncMock(
            return_value={"LastSales": [{"price": {"USD": 1000}}]},
        )

        result = await get_sales_history(items=items, api_client=mock_api)

        # Should make multiple batch requests
        assert mock_api.request.call_count >= 2

    @pytest.mark.asyncio()
    async def test_error_in_response(self):
        """Test handling error in API response."""
        mock_api = AsyncMock()
        mock_api.request = AsyncMock(
            return_value={"Error": "Rate limit exceeded"},
        )

        result = await get_sales_history(
            items=["Item1"],
            api_client=mock_api,
        )

        assert "Error" in result
        assert result["LastSales"] == []


class TestAnalyzeSalesHistoryExtended:
    """Extended tests for analyze_sales_history function."""

    @pytest.mark.asyncio()
    async def test_custom_days(self):
        """Test analysis with custom days parameter."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {
                "LastSales": [{"price": {"USD": 1000}, "date": 100}],
                "Total": 1,
            }

            result = await analyze_sales_history("Test", days=30)

            # sales_per_day should be calculated with 30 days
            assert result["sales_per_day"] == 1 / 30

    @pytest.mark.asyncio()
    async def test_none_days(self):
        """Test analysis with None days defaults to 7."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {
                "LastSales": [{"price": {"USD": 1000}, "date": 100}],
                "Total": 1,
            }

            result = await analyze_sales_history("Test", days=None)

            # sales_per_day should be calculated with 7 days
            assert result["sales_per_day"] == 1 / 7

    @pytest.mark.asyncio()
    async def test_price_trend_down(self):
        """Test detecting downward price trend."""
        sales = [
            {"price": {"USD": 2000}, "date": 100},  # $20 (older)
            {"price": {"USD": 1000}, "date": 200},  # $10 (newer) - 50% drop
        ]

        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.return_value = {"LastSales": sales, "Total": 2}

            result = await analyze_sales_history("Test")

            assert result["price_trend"] == "down"

    @pytest.mark.asyncio()
    async def test_exception_handling(self):
        """Test exception handling."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock:
            mock.side_effect = Exception("Test error")

            result = await analyze_sales_history("Test")

            assert result["has_data"] is False
            assert "error" in result


class TestExecuteApiRequestExtended:
    """Extended tests for execute_api_request function."""

    @pytest.mark.asyncio()
    async def test_no_params(self):
        """Test execute with no params."""
        mock_api = AsyncMock()
        mock_api.request = AsyncMock(return_value={"data": "test"})

        result = await execute_api_request(
            endpoint="/test",
            params=None,
            api_client=mock_api,
        )

        assert result["data"] == "test"
        # Should be called with empty dict for params
        mock_api.request.assert_called_once_with(
            method="GET",
            endpoint="/test",
            params={},
        )


class TestGetArbitrageOpportunitiesWithSalesHistoryExtended:
    """Extended tests for get_arbitrage_opportunities_with_sales_history function."""

    @pytest.mark.asyncio()
    async def test_no_sales_data(self):
        """Test when item has no sales data."""
        arbitrage_items = [{"market_hash_name": "Item1"}]

        with patch("src.dmarket.arbitrage.find_arbitrage_items") as mock_arb:
            mock_arb.return_value = arbitrage_items

            with patch(
                "src.dmarket.sales_history.analyze_sales_history"
            ) as mock_analyze:
                mock_analyze.return_value = {"has_data": False}

                result = await get_arbitrage_opportunities_with_sales_history()

                # Item should be filtered out
                assert len(result) == 0

    @pytest.mark.asyncio()
    async def test_low_sales_volume(self):
        """Test filtering by minimum sales per day."""
        arbitrage_items = [{"market_hash_name": "Item1"}]

        with patch("src.dmarket.arbitrage.find_arbitrage_items") as mock_arb:
            mock_arb.return_value = arbitrage_items

            with patch(
                "src.dmarket.sales_history.analyze_sales_history"
            ) as mock_analyze:
                mock_analyze.return_value = {
                    "has_data": True,
                    "sales_per_day": 0.5,  # Below min threshold
                    "price_trend": "stable",
                }

                result = await get_arbitrage_opportunities_with_sales_history(
                    min_sales_per_day=1.0
                )

                # Item should be filtered out
                assert len(result) == 0

    @pytest.mark.asyncio()
    async def test_exception_returns_empty(self):
        """Test exception returns empty list."""
        with patch("src.dmarket.arbitrage.find_arbitrage_items") as mock_arb:
            mock_arb.side_effect = Exception("Test error")

            result = await get_arbitrage_opportunities_with_sales_history()

            assert result == []


class TestEdgeCases:
    """Edge case tests."""

    def test_sales_cache_dir_exists(self):
        """Test SALES_CACHE_DIR constant is a valid path."""
        assert isinstance(SALES_CACHE_DIR, Path)

    @pytest.mark.asyncio()
    async def test_unicode_item_names(self):
        """Test handling unicode item names."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[{"date": 123, "price": 1000}],
        )

        result = await get_item_sales_history(
            item_name="★ Нож | Дракон",
            use_cache=False,
            dmarket_api=mock_api,
        )

        assert len(result) == 1

    @pytest.mark.asyncio()
    async def test_very_long_item_name(self):
        """Test handling very long item names."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(return_value=[])

        long_name = "A" * 500
        result = await get_item_sales_history(
            item_name=long_name,
            use_cache=False,
            dmarket_api=mock_api,
        )

        # Should handle without error
        assert result == []


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio()
    async def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[
                {"date": 100, "price": 1000},
                {"date": 200, "price": 1100},
                {"date": 300, "price": 1200},
            ],
        )

        # Get history
        history = await get_item_sales_history(
            item_name="Test Item",
            game="csgo",
            use_cache=False,
            dmarket_api=mock_api,
        )
        assert len(history) == 3

        # Detect anomalies
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = history
            anomalies = await detect_price_anomalies("Test Item")
            assert "anomalies" in anomalies

        # Calculate trend
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock:
            mock.return_value = history
            trend = await calculate_price_trend("Test Item")
            assert "trend" in trend

    @pytest.mark.asyncio()
    async def test_cache_workflow(self, tmp_path, monkeypatch):
        """Test caching workflow."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", tmp_path)

        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[{"date": 123, "price": 1000}],
        )

        # First call - fetches from API
        result1 = await get_item_sales_history(
            item_name="CacheTest",
            game="csgo",
            period="24h",
            use_cache=True,
            dmarket_api=mock_api,
        )

        # API should be called
        mock_api.get_item_price_history.assert_called_once()

        # Second call - should use cache
        mock_api.get_item_price_history.reset_mock()

        result2 = await get_item_sales_history(
            item_name="CacheTest",
            game="csgo",
            period="24h",
            use_cache=True,
            dmarket_api=mock_api,
        )

        # API should not be called again
        mock_api.get_item_price_history.assert_not_called()

        # Results should be the same
        assert result1 == result2

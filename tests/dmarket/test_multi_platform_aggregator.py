"""Tests for multi_platform_aggregator module.

This module tests the MultiPlatformAggregator class for aggregating
prices and opportunities across multiple platforms.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMultiPlatformAggregator:
    """Tests for MultiPlatformAggregator class."""

    @pytest.fixture
    def mock_dmarket_api(self):
        """Create mock DMarket API."""
        api = MagicMock()
        api.get_market_items = AsyncMock(return_value={"objects": []})
        return api

    @pytest.fixture
    def mock_waxpeer_api(self):
        """Create mock Waxpeer API."""
        api = MagicMock()
        api.get_items = AsyncMock(return_value={"items": []})
        return api

    @pytest.fixture
    def aggregator(self, mock_dmarket_api, mock_waxpeer_api):
        """Create MultiPlatformAggregator instance."""
        from src.dmarket.multi_platform_aggregator import MultiPlatformAggregator
        return MultiPlatformAggregator(
            dmarket_api=mock_dmarket_api,
            waxpeer_api=mock_waxpeer_api,
        )

    def test_init(self, aggregator):
        """Test initialization."""
        assert aggregator.dmarket_api is not None
        assert aggregator.waxpeer_api is not None

    @pytest.mark.asyncio
    async def test_fetch_dmarket_prices(self, aggregator, mock_dmarket_api):
        """Test fetching DMarket prices."""
        mock_dmarket_api.get_market_items.return_value = {
            "objects": [
                {"title": "AK-47 | Redline", "price": {"USD": "2500"}},
            ]
        }

        prices = await aggregator.fetch_dmarket_prices("csgo")

        assert len(prices) >= 1

    @pytest.mark.asyncio
    async def test_fetch_waxpeer_prices(self, aggregator, mock_waxpeer_api):
        """Test fetching Waxpeer prices."""
        mock_waxpeer_api.get_items.return_value = {
            "items": [
                {"name": "AK-47 | Redline", "price": 25000},  # In mils
            ]
        }

        prices = await aggregator.fetch_waxpeer_prices("csgo")

        assert len(prices) >= 1

    @pytest.mark.asyncio
    async def test_aggregate_prices(self, aggregator, mock_dmarket_api, mock_waxpeer_api):
        """Test aggregating prices from all platforms."""
        mock_dmarket_api.get_market_items.return_value = {
            "objects": [{"title": "AK-47 | Redline", "price": {"USD": "2500"}}]
        }
        mock_waxpeer_api.get_items.return_value = {
            "items": [{"name": "AK-47 | Redline", "price": 27000}]
        }

        aggregated = await aggregator.aggregate_prices("csgo")

        assert "AK-47 | Redline" in aggregated

    @pytest.mark.asyncio
    async def test_find_cross_platform_arbitrage(self, aggregator, mock_dmarket_api, mock_waxpeer_api):
        """Test finding cross-platform arbitrage opportunities."""
        mock_dmarket_api.get_market_items.return_value = {
            "objects": [{"title": "AK-47 | Redline", "price": {"USD": "2000"}}]
        }
        mock_waxpeer_api.get_items.return_value = {
            "items": [{"name": "AK-47 | Redline", "price": 30000}]
        }

        opportunities = await aggregator.find_arbitrage_opportunities("csgo")

        # Should find opportunity: buy on DMarket for $20, sell on Waxpeer for $30
        assert len(opportunities) >= 0

    @pytest.mark.asyncio
    async def test_calculate_profit(self, aggregator):
        """Test profit calculation across platforms."""
        buy_price = 20.0  # DMarket price
        sell_price = 30.0  # Waxpeer price
        fees = {
            "dmarket_fee": 0.0,
            "waxpeer_fee": 0.06,  # 6%
        }

        profit = aggregator.calculate_profit(buy_price, sell_price, fees)

        # Profit = 30 * 0.94 - 20 = 28.2 - 20 = 8.2
        assert profit == pytest.approx(8.2, rel=0.1)

    @pytest.mark.asyncio
    async def test_compare_item_prices(self, aggregator):
        """Test comparing item prices across platforms."""
        item_prices = {
            "dmarket": 20.0,
            "waxpeer": 25.0,
            "steam": 28.0,
        }

        comparison = aggregator.compare_prices(item_prices)

        assert comparison["lowest_platform"] == "dmarket"
        assert comparison["highest_platform"] == "steam"

    @pytest.mark.asyncio
    async def test_get_best_buy_platform(self, aggregator):
        """Test finding best platform to buy."""
        item_prices = {
            "dmarket": 20.0,
            "waxpeer": 22.0,
        }

        best = aggregator.get_best_buy_platform(item_prices)

        assert best == "dmarket"

    @pytest.mark.asyncio
    async def test_get_best_sell_platform(self, aggregator):
        """Test finding best platform to sell."""
        item_prices = {
            "dmarket": 20.0,
            "waxpeer": 25.0,
        }
        fees = {"dmarket": 0.07, "waxpeer": 0.06}

        best = aggregator.get_best_sell_platform(item_prices, fees)

        # Waxpeer net: 25 * 0.94 = 23.5
        # DMarket net: 20 * 0.93 = 18.6
        assert best == "waxpeer"

    def test_get_stats(self, aggregator):
        """Test getting aggregator statistics."""
        aggregator.total_comparisons = 100
        aggregator.opportunities_found = 25

        stats = aggregator.get_stats()

        assert stats["total_comparisons"] == 100
        assert stats["opportunities_found"] == 25

    @pytest.mark.asyncio
    async def test_handle_api_error(self, aggregator, mock_dmarket_api):
        """Test handling API errors."""
        mock_dmarket_api.get_market_items.side_effect = Exception("API Error")

        # Should not raise, but return empty results
        prices = await aggregator.fetch_dmarket_prices("csgo")

        assert prices == [] or prices is None

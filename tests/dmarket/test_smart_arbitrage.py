"""Tests for smart_arbitrage module.

This module tests the SmartArbitrageEngine class for intelligent
arbitrage opportunity detection and execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.dmarket.smart_arbitrage import SmartArbitrageEngine, SmartLimits, SmartOpportunity


class TestSmartArbitrageEngine:
    """Tests for SmartArbitrageEngine class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_balance = AsyncMock(return_value={"balance": 100.0})
        api.get_market_items = AsyncMock(return_value={"objects": []})
        api.__aenter__ = AsyncMock(return_value=api)
        api.__aexit__ = AsyncMock(return_value=None)
        return api

    @pytest.fixture
    def smart_arb(self, mock_api):
        """Create SmartArbitrageEngine instance."""
        return SmartArbitrageEngine(api_client=mock_api)

    def test_init(self, smart_arb, mock_api):
        """Test SmartArbitrageEngine initialization."""
        assert smart_arb.api == mock_api
        assert smart_arb.is_running is False

    def test_check_balance_safety(self, smart_arb):
        """Test balance safety check."""
        result, message = smart_arb.check_balance_safety()
        assert isinstance(result, bool)
        assert isinstance(message, str)

    @pytest.mark.asyncio
    async def test_scan_opportunities(self, smart_arb, mock_api):
        """Test scanning for opportunities."""
        mock_api.get_market_items = AsyncMock(return_value={
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                }
            ]
        })

        opportunities = await smart_arb.scan_opportunities(game="csgo")
        assert isinstance(opportunities, list)

    @pytest.mark.asyncio
    async def test_scan_empty_market(self, smart_arb, mock_api):
        """Test scanning empty market."""
        mock_api.get_market_items = AsyncMock(return_value={"objects": []})

        opportunities = await smart_arb.scan_opportunities(game="csgo")
        assert opportunities == []

    @pytest.mark.asyncio
    async def test_calculate_roi(self, smart_arb):
        """Test ROI calculation."""
        roi = smart_arb._calculate_roi(buy_price=10.0, sell_price=12.0)
        # ROI = (12 * 0.93 - 10) / 10 * 100 = 11.6%
        assert roi > 0
        assert roi < 100

    @pytest.mark.asyncio
    async def test_calculate_roi_zero_buy_price(self, smart_arb):
        """Test ROI with zero buy price."""
        roi = smart_arb._calculate_roi(buy_price=0.0, sell_price=12.0)
        assert roi == 0  # Should handle division by zero

    @pytest.mark.asyncio
    async def test_filter_opportunities(self, smart_arb):
        """Test filtering opportunities by criteria."""
        opportunities = [
            {"profit_percent": 15.0, "price": 10.0},
            {"profit_percent": 5.0, "price": 5.0},
            {"profit_percent": 20.0, "price": 100.0},
        ]

        filtered = smart_arb._filter_opportunities(
            opportunities,
            min_profit=10.0,
            max_price=50.0,
        )

        assert len(filtered) == 1
        assert filtered[0]["profit_percent"] == 15.0

    @pytest.mark.asyncio
    async def test_start_stop(self, smart_arb):
        """Test starting and stopping."""
        assert smart_arb.is_running is False

        await smart_arb.start()
        assert smart_arb.is_running is True

        await smart_arb.stop()
        assert smart_arb.is_running is False

    @pytest.mark.asyncio
    async def test_get_status(self, smart_arb):
        """Test getting status info."""
        status = smart_arb.get_status()

        assert isinstance(status, dict)
        assert "is_running" in status
        assert "opportunities_found" in status or "status" in status

    @pytest.mark.asyncio
    async def test_execute_opportunity(self, smart_arb, mock_api):
        """Test executing an opportunity."""
        opportunity = {
            "itemId": "item123",
            "name": "Test Item",
            "buy_price": 10.0,
            "sell_price": 12.0,
            "profit": 1.76,
        }

        mock_api.purchase_item = AsyncMock(return_value={"success": True})

        result = await smart_arb.execute_opportunity(opportunity)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_validate_opportunity(self, smart_arb):
        """Test opportunity validation."""
        valid_opp = {
            "itemId": "item123",
            "buy_price": 10.0,
            "sell_price": 12.0,
            "profit_percent": 15.0,
        }

        invalid_opp = {
            "itemId": "item123",
            "buy_price": 10.0,
            "sell_price": 10.5,
            "profit_percent": 2.0,  # Too low profit
        }

        assert smart_arb._validate_opportunity(valid_opp, min_profit=10.0) is True
        assert smart_arb._validate_opportunity(invalid_opp, min_profit=10.0) is False

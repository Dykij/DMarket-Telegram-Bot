"""Tests for smart_bidder module.

This module tests the SmartBidder class for intelligent
bidding on items.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSmartBidder:
    """Tests for SmartBidder class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_balance = AsyncMock(return_value={"balance": 100.0})
        api.create_bid = AsyncMock(return_value={"success": True, "bidId": "bid123"})
        api.cancel_bid = AsyncMock(return_value={"success": True})
        api.get_my_bids = AsyncMock(return_value={"objects": []})
        return api

    @pytest.fixture
    def bidder(self, mock_api):
        """Create SmartBidder instance."""
        from src.dmarket.smart_bidder import SmartBidder
        return SmartBidder(api_client=mock_api)

    def test_init(self, bidder, mock_api):
        """Test initialization."""
        assert bidder.api == mock_api

    @pytest.mark.asyncio
    async def test_place_bid(self, bidder, mock_api):
        """Test placing a bid."""
        result = await bidder.place_bid(
            item_title="AK-47 | Redline",
            price=25.0,
        )

        assert result["success"] is True
        mock_api.create_bid.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_bid(self, bidder, mock_api):
        """Test canceling a bid."""
        result = await bidder.cancel_bid("bid123")

        assert result is True
        mock_api.cancel_bid.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_bids(self, bidder, mock_api):
        """Test getting active bids."""
        mock_api.get_my_bids.return_value = {
            "objects": [
                {"bidId": "bid1", "title": "AK-47", "price": 20.0},
                {"bidId": "bid2", "title": "M4A4", "price": 30.0},
            ]
        }

        bids = await bidder.get_active_bids()

        assert len(bids) == 2

    @pytest.mark.asyncio
    async def test_calculate_optimal_bid(self, bidder):
        """Test calculating optimal bid price."""
        item_data = {
            "suggestedPrice": {"USD": "3000"},
            "recent_sales": [{"price": 28.0}, {"price": 29.0}, {"price": 27.0}],
        }

        optimal = bidder.calculate_optimal_bid(item_data, target_discount=0.15)

        # Should be ~15% below suggested price
        assert optimal < 30.0
        assert optimal > 20.0

    @pytest.mark.asyncio
    async def test_bid_below_balance(self, bidder, mock_api):
        """Test bid validation against balance."""
        mock_api.get_balance.return_value = {"balance": 10.0}

        result = await bidder.place_bid(
            item_title="Expensive Item",
            price=500.0,  # More than balance
        )

        assert result["success"] is False
        assert "balance" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_update_bid(self, bidder, mock_api):
        """Test updating existing bid."""
        mock_api.update_bid = AsyncMock(return_value={"success": True})

        result = await bidder.update_bid("bid123", new_price=30.0)

        assert result is True
        mock_api.update_bid.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_outbid(self, bidder, mock_api):
        """Test auto-outbidding competitor."""
        current_highest = 25.0

        new_bid = bidder.calculate_outbid_price(current_highest, max_price=35.0)

        assert new_bid > current_highest
        assert new_bid <= 35.0

    @pytest.mark.asyncio
    async def test_bid_strategy_aggressive(self, bidder):
        """Test aggressive bidding strategy."""
        bidder.set_strategy("aggressive")

        # Aggressive strategy should bid closer to market price
        bid = bidder.calculate_optimal_bid(
            {"suggestedPrice": {"USD": "3000"}},
            target_discount=0.10,
        )

        assert bid >= 27.0  # At most 10% below

    @pytest.mark.asyncio
    async def test_bid_strategy_conservative(self, bidder):
        """Test conservative bidding strategy."""
        bidder.set_strategy("conservative")

        # Conservative strategy should bid lower
        bid = bidder.calculate_optimal_bid(
            {"suggestedPrice": {"USD": "3000"}},
            target_discount=0.25,
        )

        assert bid <= 22.5  # At least 25% below

    def test_get_stats(self, bidder):
        """Test getting bidding statistics."""
        bidder.total_bids = 50
        bidder.successful_bids = 10
        bidder.total_spent = 250.0

        stats = bidder.get_stats()

        assert stats["total_bids"] == 50
        assert stats["successful_bids"] == 10
        assert stats["success_rate"] == 0.2

    @pytest.mark.asyncio
    async def test_cancel_all_bids(self, bidder, mock_api):
        """Test canceling all bids."""
        mock_api.get_my_bids.return_value = {
            "objects": [
                {"bidId": "bid1"},
                {"bidId": "bid2"},
            ]
        }

        count = await bidder.cancel_all_bids()

        assert count == 2
        assert mock_api.cancel_bid.call_count == 2

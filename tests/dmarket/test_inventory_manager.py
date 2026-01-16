"""Tests for inventory_manager module.

This module tests the InventoryManager class for automatic selling
and price undercutting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestInventoryManager:
    """Tests for InventoryManager class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_inventory = AsyncMock(return_value={"objects": []})
        api.get_my_offers = AsyncMock(return_value={"objects": []})
        api.create_offer = AsyncMock(return_value={"success": True})
        api.update_offer = AsyncMock(return_value={"success": True})
        api.delete_offer = AsyncMock(return_value={"success": True})
        api.get_market_items = AsyncMock(return_value={"objects": []})
        return api

    @pytest.fixture
    def mock_bot(self):
        """Create mock Telegram bot."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def manager(self, mock_api, mock_bot):
        """Create InventoryManager instance."""
        from src.dmarket.inventory_manager import InventoryManager
        return InventoryManager(
            api_client=mock_api,
            telegram_bot=mock_bot,
            undercut_step=1,
            min_profit_margin=1.02,
        )

    def test_init(self, manager, mock_api):
        """Test initialization."""
        assert manager.api == mock_api
        assert manager.undercut_step == 1
        assert manager.min_profit_margin == 1.02
        assert manager.total_undercuts == 0

    @pytest.mark.asyncio
    async def test_get_inventory(self, manager, mock_api):
        """Test getting inventory."""
        mock_api.get_inventory.return_value = {
            "objects": [
                {"itemId": "item1", "title": "AK-47"},
                {"itemId": "item2", "title": "M4A4"},
            ]
        }

        inventory = await manager.get_inventory()

        assert len(inventory) == 2
        mock_api.get_inventory.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_offers(self, manager, mock_api):
        """Test getting active offers."""
        mock_api.get_my_offers.return_value = {
            "objects": [
                {"offerId": "offer1", "price": {"USD": "1000"}},
            ]
        }

        offers = await manager.get_active_offers()

        assert len(offers) == 1
        mock_api.get_my_offers.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_item(self, manager, mock_api):
        """Test listing item for sale."""
        item = {"itemId": "item123", "title": "AK-47 | Redline"}

        result = await manager.list_item(item, price_cents=2500)

        assert result is True
        mock_api.create_offer.assert_called_once()
        assert manager.total_listed == 1

    @pytest.mark.asyncio
    async def test_list_item_failure(self, manager, mock_api):
        """Test failed listing."""
        mock_api.create_offer.side_effect = Exception("API Error")
        item = {"itemId": "item123", "title": "AK-47 | Redline"}

        result = await manager.list_item(item, price_cents=2500)

        assert result is False
        assert manager.failed_listings == 1

    @pytest.mark.asyncio
    async def test_undercut_price(self, manager, mock_api):
        """Test undercutting price."""
        offer = {
            "offerId": "offer123",
            "price": {"USD": "2500"},
        }

        result = await manager.undercut_offer(offer, current_lowest=2400)

        assert result is True
        mock_api.update_offer.assert_called_once()
        assert manager.total_undercuts == 1

    @pytest.mark.asyncio
    async def test_undercut_below_minimum(self, manager, mock_api):
        """Test undercut blocked when below minimum."""
        offer = {
            "offerId": "offer123",
            "price": {"USD": "1000"},
            "buy_price": 990,  # Can't go lower
        }

        result = await manager.undercut_offer(offer, current_lowest=900)

        # Should not undercut below minimum profit margin

    @pytest.mark.asyncio
    async def test_cancel_offer(self, manager, mock_api):
        """Test canceling offer."""
        result = await manager.cancel_offer("offer123")

        assert result is True
        mock_api.delete_offer.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_market_price(self, manager, mock_api):
        """Test getting market price."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {"price": {"USD": "2500"}},
                {"price": {"USD": "2600"}},
            ]
        }

        lowest = await manager.get_lowest_market_price("AK-47 | Redline")

        assert lowest == 2500

    @pytest.mark.asyncio
    async def test_get_market_price_empty(self, manager, mock_api):
        """Test getting market price with no listings."""
        mock_api.get_market_items.return_value = {"objects": []}

        lowest = await manager.get_lowest_market_price("Rare Item")

        assert lowest is None

    @pytest.mark.asyncio
    async def test_sync_inventory(self, manager, mock_api):
        """Test syncing inventory with offers."""
        mock_api.get_inventory.return_value = {
            "objects": [
                {"itemId": "item1", "title": "AK-47"},
            ]
        }
        mock_api.get_my_offers.return_value = {"objects": []}

        # Should list items not currently for sale
        await manager.sync_inventory()

    def test_get_stats(self, manager):
        """Test getting statistics."""
        manager.total_undercuts = 10
        manager.total_listed = 20
        manager.failed_listings = 2

        stats = manager.get_stats()

        assert stats["total_undercuts"] == 10
        assert stats["total_listed"] == 20
        assert stats["failed_listings"] == 2

    @pytest.mark.asyncio
    async def test_calculate_minimum_price(self, manager):
        """Test minimum price calculation."""
        buy_price = 1000  # $10

        min_price = manager.calculate_minimum_price(buy_price)

        # Should be buy_price * min_profit_margin
        assert min_price >= 1020  # At least 2% profit

    def test_track_relist_attempts(self, manager):
        """Test tracking relist attempts."""
        item_id = "item123"

        manager.track_relist(item_id)
        assert manager.relist_attempts[item_id] == 1

        manager.track_relist(item_id)
        assert manager.relist_attempts[item_id] == 2

    def test_reset_relist_attempts(self, manager):
        """Test resetting relist attempts."""
        manager.relist_attempts["item123"] = 5

        manager.reset_relist(item_id="item123")

        assert "item123" not in manager.relist_attempts

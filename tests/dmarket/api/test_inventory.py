"""Unit tests for DMarket API inventory operations module.

This module contains tests for src/dmarket/api/inventory.py covering:
- Getting user inventory
- Listing inventory items
- Deposit operations
- Withdrawal operations
- Inventory synchronization

Target: 20+ tests to achieve 70%+ coverage of inventory.py
"""

from unittest.mock import AsyncMock

import pytest


# Test fixtures


@pytest.fixture()
def mock_request():
    """Fixture providing a mocked _request method."""
    return AsyncMock()


@pytest.fixture()
def inventory_mixin(mock_request):
    """Fixture providing an InventoryOperationsMixin instance with mocked dependencies."""
    from src.dmarket.api.inventory import InventoryOperationsMixin

    class TestInventoryClient(InventoryOperationsMixin):
        """Test client with mixin."""

        ENDPOINT_USER_INVENTORY = "/marketplace-api/v1/user-inventory"
        ENDPOINT_DEPOSIT_ASSETS = "/marketplace-api/v1/deposit-assets"
        ENDPOINT_DEPOSIT_STATUS = "/marketplace-api/v1/deposit-status"
        ENDPOINT_WITHDRAW_ASSETS = "/marketplace-api/v1/withdraw-assets"
        ENDPOINT_INVENTORY_SYNC = "/marketplace-api/v1/user-inventory/sync"

        def __init__(self) -> None:
            self._request = mock_request

    return TestInventoryClient()


# TestGetUserInventory


class TestGetUserInventory:
    """Tests for get_user_inventory method."""

    @pytest.mark.asyncio()
    async def test_get_user_inventory_default(self, inventory_mixin, mock_request):
        """Test get_user_inventory with default parameters."""
        # Arrange
        mock_request.return_value = {
            "objects": [
                {"assetId": "1", "title": "Item 1", "price": {"USD": "1000"}},
            ],
            "total": "1",
        }

        # Act
        result = await inventory_mixin.get_user_inventory()

        # Assert
        assert result is not None
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[1]["params"]["gameId"] == "csgo"
        assert call_args[1]["params"]["limit"] == 100
        assert call_args[1]["params"]["offset"] == 0

    @pytest.mark.asyncio()
    async def test_get_user_inventory_with_game(self, inventory_mixin, mock_request):
        """Test get_user_inventory with specific game."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await inventory_mixin.get_user_inventory(game="dota2")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["gameId"] == "dota2"

    @pytest.mark.asyncio()
    async def test_get_user_inventory_with_pagination(self, inventory_mixin, mock_request):
        """Test get_user_inventory with pagination parameters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await inventory_mixin.get_user_inventory(limit=50, offset=100)

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["limit"] == 50
        assert call_args[1]["params"]["offset"] == 100


# TestListUserInventory


class TestListUserInventory:
    """Tests for list_user_inventory method."""

    @pytest.mark.asyncio()
    async def test_list_user_inventory_default(self, inventory_mixin, mock_request):
        """Test list_user_inventory with default parameters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await inventory_mixin.list_user_inventory()

        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[1]["params"]["GameID"] == "a8db"

    @pytest.mark.asyncio()
    async def test_list_user_inventory_with_game_id(self, inventory_mixin, mock_request):
        """Test list_user_inventory with specific game ID."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await inventory_mixin.list_user_inventory(game_id="custom_game_id")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["GameID"] == "custom_game_id"

    @pytest.mark.asyncio()
    async def test_list_user_inventory_with_pagination(self, inventory_mixin, mock_request):
        """Test list_user_inventory with pagination."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await inventory_mixin.list_user_inventory(limit=25, offset=50)

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["Limit"] == "25"
        assert call_args[1]["params"]["Offset"] == "50"


# TestDepositAssets


class TestDepositAssets:
    """Tests for deposit_assets method."""

    @pytest.mark.asyncio()
    async def test_deposit_assets_single(self, inventory_mixin, mock_request):
        """Test deposit_assets with single asset."""
        # Arrange
        mock_request.return_value = {"DepositID": "deposit_123"}
        asset_ids = ["asset_1"]

        # Act
        result = await inventory_mixin.deposit_assets(asset_ids=asset_ids)

        # Assert
        assert result is not None
        assert result.get("DepositID") == "deposit_123"
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_deposit_assets_multiple(self, inventory_mixin, mock_request):
        """Test deposit_assets with multiple assets."""
        # Arrange
        mock_request.return_value = {"DepositID": "deposit_456"}
        asset_ids = ["asset_1", "asset_2", "asset_3"]

        # Act
        result = await inventory_mixin.deposit_assets(asset_ids=asset_ids)

        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        data = call_args[1].get("data", {})
        assert len(data.get("AssetID", [])) == 3

    @pytest.mark.asyncio()
    async def test_deposit_assets_empty_list(self, inventory_mixin, mock_request):
        """Test deposit_assets with empty list."""
        # Arrange
        mock_request.return_value = {"error": True, "message": "No assets provided"}

        # Act
        result = await inventory_mixin.deposit_assets(asset_ids=[])

        # Assert
        mock_request.assert_called_once()


# TestGetDepositStatus


class TestGetDepositStatus:
    """Tests for get_deposit_status method."""

    @pytest.mark.asyncio()
    async def test_get_deposit_status(self, inventory_mixin, mock_request):
        """Test get_deposit_status."""
        # Arrange
        mock_request.return_value = {"status": "completed", "depositId": "deposit_123"}
        deposit_id = "deposit_123"

        # Act
        result = await inventory_mixin.get_deposit_status(deposit_id=deposit_id)

        # Assert
        assert result is not None
        mock_request.assert_called_once()


# TestWithdrawAssets


class TestWithdrawAssets:
    """Tests for withdraw_assets method."""

    @pytest.mark.asyncio()
    async def test_withdraw_assets(self, inventory_mixin, mock_request):
        """Test withdraw_assets."""
        # Arrange
        mock_request.return_value = {"WithdrawID": "withdraw_123"}
        asset_ids = ["asset_1", "asset_2"]

        # Act
        result = await inventory_mixin.withdraw_assets(asset_ids=asset_ids)

        # Assert
        assert result is not None
        mock_request.assert_called_once()


# TestSyncInventory


class TestSyncInventory:
    """Tests for sync_inventory method."""

    @pytest.mark.asyncio()
    async def test_sync_inventory(self, inventory_mixin, mock_request):
        """Test sync_inventory."""
        # Arrange
        mock_request.return_value = {"success": True, "synced": 10}

        # Act
        result = await inventory_mixin.sync_inventory()

        # Assert
        assert result is not None
        mock_request.assert_called_once()


# TestInventoryEdgeCases


class TestInventoryEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_get_inventory_empty_response(self, inventory_mixin, mock_request):
        """Test handling of empty inventory response."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await inventory_mixin.get_user_inventory()

        # Assert
        assert result["objects"] == []

    @pytest.mark.asyncio()
    async def test_get_inventory_error_response(self, inventory_mixin, mock_request):
        """Test handling of error response."""
        # Arrange
        mock_request.return_value = {"error": True, "message": "Server error"}

        # Act
        result = await inventory_mixin.get_user_inventory()

        # Assert
        assert result.get("error") is True

    @pytest.mark.asyncio()
    async def test_get_inventory_with_all_games(self, inventory_mixin, mock_request):
        """Test getting inventory for different games."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}
        games = ["csgo", "dota2", "tf2", "rust"]

        # Act & Assert
        for game in games:
            result = await inventory_mixin.get_user_inventory(game=game)
            assert result is not None

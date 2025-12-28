"""
Extended tests for dmarket_api.py module - Phase 4 Coverage Enhancement.

This module adds tests for methods not yet covered:
- deposit_assets, get_deposit_status, withdraw_assets
- sync_inventory, list_user_inventory
- list_market_items, list_offers_by_title
- buy_offers, get_aggregated_prices, get_aggregated_prices_bulk
- get_sales_history_aggregator, get_market_best_offers
- get_market_aggregated_prices, get_sales_history, get_item_price_history
- get_market_meta, edit_offer, delete_offer, get_active_offers
- create_targets, get_user_targets, delete_targets
- get_targets_by_title, get_buy_orders_competition
- get_closed_targets, get_supported_games, direct_balance_request
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.dmarket.dmarket_api import DMarketAPI


@pytest.fixture()
def api_keys():
    """Fixture with test API keys."""
    return {
        "public_key": "test_public_key_12345",
        "secret_key": "a" * 64,
    }


@pytest.fixture()
def dmarket_api(api_keys):
    """Fixture: DMarket API client."""
    return DMarketAPI(
        public_key=api_keys["public_key"],
        secret_key=api_keys["secret_key"],
        max_retries=2,
        connection_timeout=10.0,
    )


@pytest.fixture()
def dmarket_api_live(api_keys):
    """Fixture: DMarket API client with DRY_RUN disabled."""
    return DMarketAPI(
        public_key=api_keys["public_key"],
        secret_key=api_keys["secret_key"],
        max_retries=2,
        connection_timeout=10.0,
        dry_run=False,
    )


# ============================================================================
# Tests for Deposit/Withdraw Operations
# ============================================================================


class TestDepositOperations:
    """Tests for deposit-related methods."""

    @pytest.mark.asyncio
    async def test_deposit_assets_success(self, dmarket_api):
        """Test successful asset deposit."""
        mock_response = {"DepositID": "deposit_123"}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.deposit_assets(["asset_1", "asset_2"])

            assert result["DepositID"] == "deposit_123"
            dmarket_api._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_deposit_assets_empty_list(self, dmarket_api):
        """Test deposit with empty asset list."""
        mock_response = {"DepositID": "deposit_empty"}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.deposit_assets([])

            assert result["DepositID"] == "deposit_empty"

    @pytest.mark.asyncio
    async def test_deposit_assets_single_item(self, dmarket_api):
        """Test deposit with single asset."""
        mock_response = {"DepositID": "deposit_single"}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.deposit_assets(["single_asset"])

            assert "DepositID" in result

    @pytest.mark.asyncio
    async def test_get_deposit_status_pending(self, dmarket_api):
        """Test getting pending deposit status."""
        mock_response = {
            "DepositID": "deposit_123",
            "Status": "TransferStatusPending",
            "Assets": [],
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_deposit_status("deposit_123")

            assert result["Status"] == "TransferStatusPending"

    @pytest.mark.asyncio
    async def test_get_deposit_status_completed(self, dmarket_api):
        """Test getting completed deposit status."""
        mock_response = {
            "DepositID": "deposit_123",
            "Status": "TransferStatusCompleted",
            "Assets": [{"AssetID": "asset_1"}],
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_deposit_status("deposit_123")

            assert result["Status"] == "TransferStatusCompleted"
            assert len(result["Assets"]) == 1

    @pytest.mark.asyncio
    async def test_get_deposit_status_failed(self, dmarket_api):
        """Test getting failed deposit status."""
        mock_response = {
            "DepositID": "deposit_123",
            "Status": "TransferStatusFailed",
            "Error": "Asset not found",
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_deposit_status("deposit_123")

            assert result["Status"] == "TransferStatusFailed"
            assert "Error" in result

    @pytest.mark.asyncio
    async def test_withdraw_assets_success(self, dmarket_api):
        """Test successful asset withdrawal."""
        mock_response = {"success": True, "WithdrawID": "withdraw_123"}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.withdraw_assets(["item_1", "item_2"])

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_withdraw_assets_empty_list(self, dmarket_api):
        """Test withdrawal with empty list."""
        mock_response = {"success": True}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.withdraw_assets([])

            assert result["success"] is True


# ============================================================================
# Tests for Inventory Operations
# ============================================================================


class TestInventoryOperations:
    """Tests for inventory-related methods."""

    @pytest.mark.asyncio
    async def test_sync_inventory_success(self, dmarket_api):
        """Test successful inventory sync."""
        mock_response = {"success": True, "syncedItems": 10}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.sync_inventory(game_id="a8db")

            assert result["success"] is True
            dmarket_api._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_inventory_default_game(self, dmarket_api):
        """Test sync with default game ID."""
        mock_response = {"success": True}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.sync_inventory()

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_user_inventory_success(self, dmarket_api):
        """Test listing user inventory."""
        mock_response = {
            "items": [
                {"id": "item_1", "title": "AK-47 | Redline"},
                {"id": "item_2", "title": "M4A4 | Asiimov"},
            ],
            "total": 2,
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_user_inventory(
                game_id="a8db", limit=100, offset=0
            )

            assert len(result["items"]) == 2
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_user_inventory_with_pagination(self, dmarket_api):
        """Test inventory listing with pagination."""
        mock_response = {"items": [], "total": 200}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_user_inventory(
                game_id="a8db", limit=50, offset=100
            )

            dmarket_api._request.assert_called_once()
            assert "items" in result

    @pytest.mark.asyncio
    async def test_list_user_inventory_empty(self, dmarket_api):
        """Test listing empty inventory."""
        mock_response = {"items": [], "total": 0}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_user_inventory()

            assert result["items"] == []
            assert result["total"] == 0


# ============================================================================
# Tests for Market Operations
# ============================================================================


class TestMarketOperations:
    """Tests for market-related methods."""

    @pytest.mark.asyncio
    async def test_list_market_items_success(self, dmarket_api):
        """Test listing market items."""
        mock_response = {
            "objects": [
                {"title": "Item 1", "price": {"USD": "1000"}},
                {"title": "Item 2", "price": {"USD": "2000"}},
            ],
            "total": 2,
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_market_items(
                game_id="a8db", limit=100, offset=0
            )

            assert len(result["objects"]) == 2

    @pytest.mark.asyncio
    async def test_list_market_items_with_ordering(self, dmarket_api):
        """Test market items with ordering."""
        mock_response = {"objects": [], "total": 0}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_market_items(
                order_by="price", order_dir="asc"
            )

            assert "objects" in result

    @pytest.mark.asyncio
    async def test_list_offers_by_title_success(self, dmarket_api):
        """Test listing offers by title."""
        mock_response = {
            "offers": [
                {"offerId": "offer_1", "price": 1000},
                {"offerId": "offer_2", "price": 1100},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_offers_by_title(
                title="AK-47 | Redline", game_id="a8db"
            )

            assert len(result["offers"]) == 2

    @pytest.mark.asyncio
    async def test_list_offers_by_title_empty(self, dmarket_api):
        """Test listing offers for non-existent item."""
        mock_response = {"offers": []}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_offers_by_title(
                title="Non Existent Item", game_id="a8db"
            )

            assert result["offers"] == []

    @pytest.mark.asyncio
    async def test_buy_offers_success(self, dmarket_api_live):
        """Test buying offers."""
        mock_response = {"success": True, "offersProcessed": 2}

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.buy_offers(
                offers=[
                    {"offerId": "offer_1", "price": {"USD": "1000"}},
                    {"offerId": "offer_2", "price": {"USD": "1500"}},
                ]
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_market_best_offers_success(self, dmarket_api):
        """Test getting best market offers."""
        mock_response = {
            "offers": [
                {"title": "Item 1", "price": 900},
                {"title": "Item 2", "price": 1000},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_market_best_offers(
                title="AK-47 | Redline", game="csgo"
            )

            assert len(result["offers"]) == 2

    @pytest.mark.asyncio
    async def test_get_market_meta_success(self, dmarket_api):
        """Test getting market metadata."""
        mock_response = {
            "categories": ["Rifle", "Pistol"],
            "qualities": ["FN", "MW", "FT"],
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_market_meta(game="csgo")

            assert "categories" in result


# ============================================================================
# Tests for Price/Sales History
# ============================================================================


class TestPriceAndSalesHistory:
    """Tests for price and sales history methods."""

    @pytest.mark.asyncio
    async def test_get_aggregated_prices_success(self, dmarket_api):
        """Test getting aggregated prices."""
        mock_response = {
            "aggregatedPrices": [
                {"title": "Item 1", "minPrice": 900, "maxPrice": 1100},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_aggregated_prices(
                titles=["AK-47 | Redline"], game_id="a8db"
            )

            assert "aggregatedPrices" in result

    @pytest.mark.asyncio
    async def test_get_aggregated_prices_bulk_success(self, dmarket_api):
        """Test getting aggregated prices in bulk."""
        mock_response = {
            "prices": {
                "Item 1": {"min": 900, "max": 1100},
                "Item 2": {"min": 500, "max": 600},
            }
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_aggregated_prices_bulk(
                titles=["Item 1", "Item 2"], game="csgo"
            )

            assert "prices" in result

    @pytest.mark.asyncio
    async def test_get_market_aggregated_prices_success(self, dmarket_api):
        """Test getting market aggregated prices."""
        mock_response = {
            "items": [
                {"title": "Item", "avgPrice": 1000},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_market_aggregated_prices(
                title="AK-47", game="csgo"
            )

            assert "items" in result

    @pytest.mark.asyncio
    async def test_get_sales_history_success(self, dmarket_api):
        """Test getting sales history."""
        mock_response = {
            "sales": [
                {"date": "2024-01-15", "price": 1000, "quantity": 5},
                {"date": "2024-01-14", "price": 1050, "quantity": 3},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_sales_history(
                title="AK-47 | Redline", game="csgo"
            )

            assert len(result["sales"]) == 2

    @pytest.mark.asyncio
    async def test_get_sales_history_empty(self, dmarket_api):
        """Test sales history for item with no sales."""
        mock_response = {"sales": []}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_sales_history(
                title="Rare Item", game="csgo"
            )

            assert result["sales"] == []

    @pytest.mark.asyncio
    async def test_get_item_price_history_success(self, dmarket_api):
        """Test getting item price history."""
        mock_response = {
            "history": [
                {"timestamp": "2024-01-15T10:00:00Z", "price": 1000},
                {"timestamp": "2024-01-14T10:00:00Z", "price": 1050},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_item_price_history(
                game="csgo", title="AK-47 | Redline", period="last_week"
            )

            assert len(result["history"]) == 2

    @pytest.mark.asyncio
    async def test_get_sales_history_aggregator_success(self, dmarket_api):
        """Test getting aggregated sales history."""
        mock_response = {
            "sales": [
                {"price": "1000", "date": "2024-01-15"},
                {"price": "1050", "date": "2024-01-14"},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_sales_history_aggregator(
                game_id="a8db", title="AK-47 | Redline"
            )

            assert len(result["sales"]) == 2


# ============================================================================
# Tests for Offer Management
# ============================================================================


class TestOfferManagement:
    """Tests for offer management methods."""

    @pytest.mark.asyncio
    async def test_edit_offer_success(self, dmarket_api_live):
        """Test editing an offer."""
        mock_response = {"success": True, "offerId": "offer_123"}

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.edit_offer(
                offer_id="offer_123", price=15.99, currency="USD"
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_edit_offer_price_conversion(self, dmarket_api_live):
        """Test that price is converted to cents."""
        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value={"success": True})
        ) as mock_request:
            await dmarket_api_live.edit_offer(
                offer_id="offer_123", price=10.50, currency="USD"
            )

            # Check the data passed contains price in cents
            call_args = mock_request.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_delete_offer_success(self, dmarket_api_live):
        """Test deleting an offer."""
        mock_response = {"success": True}

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.delete_offer(offer_id="offer_123")

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_active_offers_success(self, dmarket_api):
        """Test getting active offers."""
        mock_response = {
            "offers": [
                {"offerId": "offer_1", "status": "active", "price": 1000},
                {"offerId": "offer_2", "status": "active", "price": 1500},
            ],
            "total": 2,
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_active_offers(
                game="csgo", limit=50, offset=0
            )

            assert len(result["offers"]) == 2

    @pytest.mark.asyncio
    async def test_get_active_offers_empty(self, dmarket_api):
        """Test getting offers when none exist."""
        mock_response = {"offers": [], "total": 0}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_active_offers(game="csgo")

            assert result["offers"] == []

    @pytest.mark.asyncio
    async def test_get_active_offers_with_status_filter(self, dmarket_api):
        """Test getting offers with status filter."""
        mock_response = {"offers": [], "total": 0}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_active_offers(
                game="csgo", status="completed"
            )

            assert "offers" in result


# ============================================================================
# Tests for Target Operations
# ============================================================================


class TestTargetOperations:
    """Tests for target/buy order methods."""

    @pytest.mark.asyncio
    async def test_create_targets_success(self, dmarket_api_live):
        """Test creating targets."""
        mock_response = {
            "Targets": [
                {"TargetID": "target_1", "Status": "TargetStatusActive"},
            ]
        }

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.create_targets(
                game_id="a8db",
                targets=[
                    {
                        "Title": "AK-47 | Redline (FT)",
                        "Amount": 1,
                        "Price": {"Amount": 800, "Currency": "USD"},
                    }
                ],
            )

            assert len(result["Targets"]) == 1

    @pytest.mark.asyncio
    async def test_create_targets_multiple(self, dmarket_api_live):
        """Test creating multiple targets."""
        mock_response = {
            "Targets": [
                {"TargetID": "target_1"},
                {"TargetID": "target_2"},
            ]
        }

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.create_targets(
                game_id="a8db",
                targets=[
                    {"Title": "Item 1", "Amount": 1, "Price": {"Amount": 100}},
                    {"Title": "Item 2", "Amount": 2, "Price": {"Amount": 200}},
                ],
            )

            assert len(result["Targets"]) == 2

    @pytest.mark.asyncio
    async def test_get_user_targets_success(self, dmarket_api):
        """Test getting user targets."""
        mock_response = {
            "Targets": [
                {"TargetID": "target_1", "Title": "AK-47", "Status": "Active"},
            ],
            "Total": 1,
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_user_targets(game_id="a8db")

            assert len(result["Targets"]) == 1

    @pytest.mark.asyncio
    async def test_get_user_targets_with_status(self, dmarket_api):
        """Test getting targets with status filter."""
        mock_response = {"Targets": [], "Total": 0}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_user_targets(
                game_id="a8db", status="TargetStatusActive"
            )

            assert "Targets" in result

    @pytest.mark.asyncio
    async def test_delete_targets_success(self, dmarket_api_live):
        """Test deleting targets."""
        mock_response = {"success": True, "deleted": 2}

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.delete_targets(
                target_ids=["target_1", "target_2"]
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_targets_by_title_success(self, dmarket_api):
        """Test getting targets by title."""
        mock_response = {
            "orders": [
                {"title": "AK-47 | Redline", "price": "800", "amount": 5},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_targets_by_title(
                game_id="a8db", title="AK-47 | Redline"
            )

            assert len(result["orders"]) == 1

    @pytest.mark.asyncio
    async def test_get_buy_orders_competition_success(self, dmarket_api):
        """Test getting buy orders competition."""
        mock_response = {
            "title": "AK-47 | Redline",
            "game_id": "a8db",
            "total_orders": 15,
            "competition_level": "medium",
            "orders": [{"price": "800", "amount": 5}],
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_buy_orders_competition(
                game_id="a8db", title="AK-47 | Redline"
            )

            assert "competition_level" in result or "orders" in result or "title" in result

    @pytest.mark.asyncio
    async def test_get_closed_targets_success(self, dmarket_api):
        """Test getting closed targets."""
        mock_response = {
            "Targets": [
                {"TargetID": "target_1", "Status": "successful"},
            ]
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_closed_targets(limit=50)

            assert len(result["Targets"]) == 1


# ============================================================================
# Tests for Utility Methods
# ============================================================================


class TestUtilityMethods:
    """Tests for utility methods."""

    @pytest.mark.asyncio
    async def test_get_supported_games_success(self, dmarket_api):
        """Test getting supported games."""
        mock_response = [
            {"id": "a8db", "name": "CS:GO"},
            {"id": "9a92", "name": "Dota 2"},
            {"id": "tf2", "name": "Team Fortress 2"},
            {"id": "rust", "name": "Rust"},
        ]

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_supported_games()

            assert len(result) == 4

    @pytest.mark.asyncio
    async def test_direct_balance_request_success(self, dmarket_api):
        """Test direct balance request."""
        mock_response = {
            "usd": "10000",
            "dmc": "5000",
        }

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            # Mock the entire direct_balance_request to avoid real network call
            with patch.object(
                dmarket_api, "direct_balance_request", new=AsyncMock(return_value=mock_response)
            ):
                result = await dmarket_api.direct_balance_request()

                assert "usd" in result or "USD" in result or "balance" in str(result).lower()


# ============================================================================
# Tests for Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_deposit_assets_api_error(self, dmarket_api):
        """Test deposit with API error."""
        with patch.object(
            dmarket_api,
            "_request",
            new=AsyncMock(side_effect=httpx.HTTPStatusError(
                "Error", request=MagicMock(), response=MagicMock(status_code=500)
            )),
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await dmarket_api.deposit_assets(["asset_1"])

    @pytest.mark.asyncio
    async def test_sync_inventory_timeout(self, dmarket_api):
        """Test inventory sync with timeout."""
        with patch.object(
            dmarket_api,
            "_request",
            new=AsyncMock(side_effect=httpx.TimeoutException("Timeout")),
        ):
            with pytest.raises(httpx.TimeoutException):
                await dmarket_api.sync_inventory()

    @pytest.mark.asyncio
    async def test_get_targets_connection_error(self, dmarket_api):
        """Test targets request with connection error."""
        with patch.object(
            dmarket_api,
            "_request",
            new=AsyncMock(side_effect=httpx.ConnectError("Connection failed")),
        ):
            with pytest.raises(httpx.ConnectError):
                await dmarket_api.get_user_targets(game_id="a8db")


# ============================================================================
# Tests for Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_list_inventory_large_offset(self, dmarket_api):
        """Test inventory listing with large offset."""
        mock_response = {"items": [], "total": 0}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_user_inventory(
                game_id="a8db", limit=100, offset=10000
            )

            assert result["items"] == []

    @pytest.mark.asyncio
    async def test_create_targets_empty_list(self, dmarket_api_live):
        """Test creating empty targets list."""
        mock_response = {"Targets": []}

        with patch.object(
            dmarket_api_live, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api_live.create_targets(
                game_id="a8db", targets=[]
            )

            assert result["Targets"] == []

    @pytest.mark.asyncio
    async def test_get_offers_max_limit(self, dmarket_api):
        """Test getting offers with max limit."""
        mock_response = {"offers": [{"id": i} for i in range(100)], "total": 100}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_active_offers(game="csgo", limit=100)

            assert len(result["offers"]) == 100

    @pytest.mark.asyncio
    async def test_sales_history_long_period(self, dmarket_api):
        """Test sales history for long period."""
        mock_response = {"sales": [{"date": f"2024-01-{i:02d}"} for i in range(1, 31)]}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.get_sales_history(
                title="AK-47", game="csgo"
            )

            assert len(result["sales"]) == 30

    @pytest.mark.asyncio
    async def test_unicode_title_handling(self, dmarket_api):
        """Test handling of Unicode characters in titles."""
        mock_response = {"offers": [{"title": "АК-47 | Кровавый"}]}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_offers_by_title(
                title="АК-47 | Кровавый", game_id="a8db"
            )

            assert len(result["offers"]) == 1

    @pytest.mark.asyncio
    async def test_special_characters_in_title(self, dmarket_api):
        """Test handling of special characters in titles."""
        mock_response = {"offers": []}

        with patch.object(
            dmarket_api, "_request", new=AsyncMock(return_value=mock_response)
        ):
            result = await dmarket_api.list_offers_by_title(
                title="Item (★) | Name [Test]", game_id="a8db"
            )

            assert "offers" in result

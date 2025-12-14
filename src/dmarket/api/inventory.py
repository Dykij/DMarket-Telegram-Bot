"""DMarket API inventory operations.

This module provides inventory-related API operations including:
- Getting user inventory
- Listing inventory items
- Deposit and withdrawal operations
- Inventory synchronization
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class InventoryOperationsMixin:
    """Mixin class providing inventory-related API operations.

    This mixin is designed to be used with DMarketAPIClient or DMarketAPI
    which provides the _request method and endpoint constants.
    """

    # Type hints for mixin compatibility
    _request: Any
    ENDPOINT_USER_INVENTORY: str
    ENDPOINT_DEPOSIT_ASSETS: str
    ENDPOINT_DEPOSIT_STATUS: str
    ENDPOINT_WITHDRAW_ASSETS: str
    ENDPOINT_INVENTORY_SYNC: str

    async def get_user_inventory(
        self,
        game: str = "csgo",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get user inventory items.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            limit: Number of items to retrieve
            offset: Offset for pagination

        Returns:
            User inventory items as dict
        """
        params = {
            "gameId": game,
            "limit": limit,
            "offset": offset,
        }
        return await self._request(
            "GET",
            self.ENDPOINT_USER_INVENTORY,
            params=params,
        )

    async def list_user_inventory(
        self,
        game_id: str = "a8db",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get user inventory according to DMarket API.

        Args:
            game_id: Game ID (a8db for CS:GO)
            limit: Number of results
            offset: Offset for pagination

        Returns:
            List of inventory items
        """
        params = {
            "GameID": game_id,
            "Limit": str(limit),
            "Offset": str(offset),
        }
        return await self._request(
            "GET",
            "/marketplace-api/v1/user-inventory",
            params=params,
        )

    async def deposit_assets(
        self,
        asset_ids: list[str],
    ) -> dict[str, Any]:
        """Deposit assets from Steam to DMarket (API v1.1.0).

        Args:
            asset_ids: List of asset IDs to deposit

        Returns:
            Deposit ID

        Response format:
            {"DepositID": "string"}

        Example:
            >>> result = await api.deposit_assets(["asset_id_1", "asset_id_2"])
            >>> deposit_id = result["DepositID"]
            >>> # Then check status:
            >>> status = await api.get_deposit_status(deposit_id)
        """
        data = {"AssetID": asset_ids}
        return await self._request(
            "POST",
            self.ENDPOINT_DEPOSIT_ASSETS,
            data=data,
        )

    async def get_deposit_status(
        self,
        deposit_id: str,
    ) -> dict[str, Any]:
        """Get deposit status (API v1.1.0).

        Args:
            deposit_id: Deposit ID

        Returns:
            Deposit status

        Response format:
            {
                "DepositID": "string",
                "Status": "TransferStatusPending | TransferStatusCompleted | TransferStatusFailed",
                "Assets": [...],
                "Error": "string" (if any)
            }

        Example:
            >>> status = await api.get_deposit_status("deposit_123")
            >>> if status["Status"] == "TransferStatusCompleted":
            ...     print("Deposit completed!")
        """
        path = f"{self.ENDPOINT_DEPOSIT_STATUS}/{deposit_id}"
        return await self._request("GET", path)

    async def withdraw_assets(
        self,
        asset_ids: list[str],
    ) -> dict[str, Any]:
        """Withdraw assets from DMarket to Steam (API v1.1.0).

        Args:
            asset_ids: List of asset IDs to withdraw

        Returns:
            Withdrawal operation result

        Example:
            >>> result = await api.withdraw_assets(["item_id_1", "item_id_2"])
        """
        data = {"AssetIDs": asset_ids}
        return await self._request(
            "POST",
            self.ENDPOINT_WITHDRAW_ASSETS,
            data=data,
        )

    async def sync_inventory(
        self,
        game_id: str = "a8db",
    ) -> dict[str, Any]:
        """Synchronize inventory with external platforms (API v1.1.0).

        Args:
            game_id: Game ID to sync

        Returns:
            Synchronization result

        Example:
            >>> result = await api.sync_inventory(game_id="a8db")
            >>> if result.get("success"):
            ...     print("Inventory synchronized")
        """
        data = {"GameID": game_id}
        return await self._request(
            "POST",
            self.ENDPOINT_INVENTORY_SYNC,
            data=data,
        )

    async def get_all_user_inventory(
        self,
        game: str = "csgo",
        max_items: int = 1000,
    ) -> list[dict[str, Any]]:
        """Get all user inventory items using pagination.

        Args:
            game: Game name
            max_items: Maximum number of items to retrieve

        Returns:
            List of all inventory items
        """
        all_items: list[dict[str, Any]] = []
        limit = 100
        offset = 0
        total_fetched = 0

        while total_fetched < max_items:
            response = await self.get_user_inventory(
                game=game,
                limit=limit,
                offset=offset,
            )

            items = response.get("objects", []) or response.get("items", [])
            if not items:
                break

            all_items.extend(items)
            total_fetched += len(items)
            offset += limit

            if len(items) < limit:
                break

        return all_items[:max_items]

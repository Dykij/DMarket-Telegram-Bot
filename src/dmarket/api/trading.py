"""DMarket API trading operations.

This module provides trading-related API operations including:
- Buying items
- Selling items
- Creating and managing offers
- Editing and deleting offers
"""

import logging
from typing import Any

from src.utils.sentry_breadcrumbs import add_trading_breadcrumb


logger = logging.getLogger(__name__)


class TradingOperationsMixin:
    """Mixin class providing trading-related API operations.

    This mixin is designed to be used with DMarketAPIClient or DMarketAPI
    which provides the _request method and endpoint constants.
    """

    # Type hints for mixin compatibility
    _request: Any
    clear_cache_for_endpoint: Any
    dry_run: bool
    ENDPOINT_PURCHASE: str
    ENDPOINT_SELL: str
    ENDPOINT_OFFER_EDIT: str
    ENDPOINT_OFFER_DELETE: str
    ENDPOINT_USER_INVENTORY: str
    ENDPOINT_USER_OFFERS: str
    ENDPOINT_BALANCE: str
    ENDPOINT_BALANCE_LEGACY: str
    ENDPOINT_ACCOUNT_OFFERS: str

    async def buy_item(
        self,
        item_id: str,
        price: float,
        game: str = "csgo",
        item_name: str | None = None,
        sell_price: float | None = None,
        profit: float | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        """Buy an item with specified ID and price.

        Args:
            item_id: Item ID to buy
            price: Price in USD (will be converted to cents)
            game: Game code (csgo, dota2, tf2, rust)
            item_name: Item name (for logging)
            sell_price: Expected sell price (for logging)
            profit: Expected profit (for logging)
            source: Intent source (arbitrage_scanner, manual, etc.)

        Returns:
            Purchase operation result
        """
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger(__name__)

        profit_usd = profit or (sell_price - price if sell_price else None)
        profit_percent = (
            (profit_usd / price * 100) if profit_usd and price > 0 else None
        )

        add_trading_breadcrumb(
            action="buy_item_intent",
            game=game,
            item_id=item_id,
            price=price,
            item_name=item_name,
            sell_price=sell_price,
            profit=profit_usd,
            profit_percent=profit_percent,
            dry_run=self.dry_run,
        )

        bot_logger.log_buy_intent(
            item_name=item_name or item_id,
            price_usd=price,
            sell_price_usd=sell_price,
            profit_usd=profit_usd,
            profit_percent=profit_percent,
            source=source,
            dry_run=self.dry_run,
            game=game,
            item_id=item_id,
        )

        price_cents = int(price * 100)

        data = {
            "itemId": item_id,
            "price": {
                "amount": price_cents,
                "currency": "USD",
            },
            "gameType": game,
        }

        if self.dry_run:
            mode_label = "[DRY-RUN]"
            logger.info(
                f"{mode_label} 🔵 SIMULATED BUY: item_id={item_id}, price=${price:.2f}, game={game}"
            )
            result = {
                "success": True,
                "dry_run": True,
                "operation": "buy",
                "item_id": item_id,
                "price_usd": price,
                "game": game,
                "message": "Simulated purchase (DRY_RUN mode)",
            }
            bot_logger.log_trade_result(
                operation="buy",
                success=True,
                item_name=item_name or item_id,
                price_usd=price,
                dry_run=True,
            )
            return result

        mode_label = "[LIVE]"
        logger.warning(
            f"{mode_label} 🔴 REAL BUY: item_id={item_id}, price=${price:.2f}, game={game}"
        )

        try:
            result = await self._request(
                "POST",
                self.ENDPOINT_PURCHASE,
                data=data,
            )

            bot_logger.log_trade_result(
                operation="buy",
                success=True,
                item_name=item_name or item_id,
                price_usd=price,
                dry_run=False,
            )

            await self.clear_cache_for_endpoint(self.ENDPOINT_USER_INVENTORY)
            await self.clear_cache_for_endpoint(self.ENDPOINT_BALANCE)
            await self.clear_cache_for_endpoint(self.ENDPOINT_BALANCE_LEGACY)

            return result

        except Exception as e:
            bot_logger.log_trade_result(
                operation="buy",
                success=False,
                item_name=item_name or item_id,
                price_usd=price,
                error_message=str(e),
                dry_run=False,
            )
            raise

    async def sell_item(
        self,
        item_id: str,
        price: float,
        game: str = "csgo",
        item_name: str | None = None,
        buy_price: float | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        """List an item for sale.

        Args:
            item_id: Item ID to sell
            price: Price in USD (will be converted to cents)
            game: Game code (csgo, dota2, tf2, rust)
            item_name: Item name (for logging)
            buy_price: Purchase price (for profit calculation)
            source: Intent source (auto_sell, manual, etc.)

        Returns:
            Sale operation result
        """
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger(__name__)

        profit_usd = price - buy_price if buy_price else None
        profit_percent = (
            (profit_usd / buy_price * 100) if profit_usd and buy_price else None
        )

        bot_logger.log_sell_intent(
            item_name=item_name or item_id,
            price_usd=price,
            buy_price_usd=buy_price,
            profit_usd=profit_usd,
            profit_percent=profit_percent,
            source=source,
            dry_run=self.dry_run,
            game=game,
            item_id=item_id,
        )

        price_cents = int(price * 100)

        data = {
            "itemId": item_id,
            "price": {
                "amount": price_cents,
                "currency": "USD",
            },
        }

        if self.dry_run:
            mode_label = "[DRY-RUN]"
            logger.info(
                f"{mode_label} 🔵 SIMULATED SELL: item_id={item_id}, "
                f"price=${price:.2f}, game={game}"
            )
            result = {
                "success": True,
                "dry_run": True,
                "operation": "sell",
                "item_id": item_id,
                "price_usd": price,
                "game": game,
                "message": "Simulated sale (DRY_RUN mode)",
            }
            bot_logger.log_trade_result(
                operation="sell",
                success=True,
                item_name=item_name or item_id,
                price_usd=price,
                dry_run=True,
            )
            return result

        mode_label = "[LIVE]"
        logger.warning(
            f"{mode_label} 🔴 REAL SELL: item_id={item_id}, price=${price:.2f}, game={game}"
        )

        try:
            result = await self._request(
                "POST",
                self.ENDPOINT_SELL,
                data=data,
            )

            bot_logger.log_trade_result(
                operation="sell",
                success=True,
                item_name=item_name or item_id,
                price_usd=price,
                dry_run=False,
            )

            await self.clear_cache_for_endpoint(self.ENDPOINT_USER_INVENTORY)
            await self.clear_cache_for_endpoint(self.ENDPOINT_USER_OFFERS)

            return result

        except Exception as e:
            bot_logger.log_trade_result(
                operation="sell",
                success=False,
                item_name=item_name or item_id,
                price_usd=price,
                error_message=str(e),
                dry_run=False,
            )
            raise

    async def buy_offers(
        self,
        offer_ids: list[str],
        prices: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Buy multiple offers according to DMarket API v1.1.0.

        Args:
            offer_ids: List of offer IDs to buy
            prices: List of prices for each offer
                Format: [{"Amount": 100, "Currency": "USD"}, ...]

        Returns:
            Purchase result
        """
        offers = [
            {"OfferID": offer_id, "Price": price}
            for offer_id, price in zip(offer_ids, prices, strict=False)
        ]

        data = {"Offers": offers}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/buy",
            data=data,
        )

    async def create_offers(
        self,
        assets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create sell offers according to DMarket API.

        Args:
            assets: List of assets to sell
                Format: [{"AssetID": "...", "Price": {"Amount": 100, "Currency": "USD"}}]

        Returns:
            Created offers result
        """
        data = {"Assets": assets}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/create",
            data=data,
        )

    async def update_offer_prices(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Update offer prices according to DMarket API.

        Args:
            offers: List of offers with new prices
                Format: [{"OfferID": "...", "Price": {"Amount": 100, "Currency": "USD"}}]

        Returns:
            Update result
        """
        data = {"Offers": offers}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/edit",
            data=data,
        )

    async def remove_offers(
        self,
        offer_ids: list[str],
    ) -> dict[str, Any]:
        """Remove offers from sale according to DMarket API.

        Args:
            offer_ids: List of offer IDs to remove

        Returns:
            Removal result
        """
        data = {"Offers": [{"OfferID": oid} for oid in offer_ids]}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/delete",
            data=data,
        )

    async def edit_offer(
        self,
        offer_id: str,
        new_price: float,
    ) -> dict[str, Any]:
        """Edit offer price.

        Args:
            offer_id: Offer ID
            new_price: New price in USD

        Returns:
            Edit result
        """
        price_cents = int(new_price * 100)

        data = {
            "offer_id": offer_id,
            "price": {
                "amount": price_cents,
                "currency": "USD",
            },
        }

        result = await self._request(
            "POST",
            self.ENDPOINT_OFFER_EDIT,
            data=data,
        )

        await self.clear_cache_for_endpoint(self.ENDPOINT_USER_OFFERS)

        return result

    async def delete_offer(
        self,
        offer_id: str,
    ) -> dict[str, Any]:
        """Delete an offer.

        Args:
            offer_id: Offer ID

        Returns:
            Deletion result
        """
        data = {"offer_id": offer_id}

        result = await self._request(
            "POST",
            self.ENDPOINT_OFFER_DELETE,
            data=data,
        )

        await self.clear_cache_for_endpoint(self.ENDPOINT_USER_OFFERS)
        await self.clear_cache_for_endpoint(self.ENDPOINT_USER_INVENTORY)

        return result

    async def get_active_offers(
        self,
        game: str = "csgo",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get user's active trading offers.

        Args:
            game: Game name
            limit: Number of offers to retrieve
            offset: Offset for pagination

        Returns:
            Active offers as dict
        """
        params = {
            "gameId": game,
            "limit": limit,
            "offset": offset,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_ACCOUNT_OFFERS,
            params=params,
        )

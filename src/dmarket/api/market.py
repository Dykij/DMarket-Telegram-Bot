"""DMarket API market operations.

This module provides market-related API operations including:
- Searching and listing market items
- Getting aggregated prices
- Getting best offers
- Market metadata
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


class MarketOperationsMixin:
    """Mixin class providing market-related API operations.

    This mixin is designed to be used with DMarketAPIClient or DMarketAPI
    which provides the _request method and endpoint constants.
    """

    # Type hints for mixin compatibility
    _request: Any
    clear_cache_for_endpoint: Any
    ENDPOINT_MARKET_ITEMS: str
    ENDPOINT_MARKET_PRICE_AGGREGATED: str
    ENDPOINT_MARKET_META: str
    ENDPOINT_MARKET_BEST_OFFERS: str
    ENDPOINT_MARKET_SEARCH: str
    ENDPOINT_AGGREGATED_PRICES_POST: str
    ENDPOINT_LAST_SALES: str

    async def get_market_items(
        self,
        game: str = "csgo",
        limit: int = 100,
        offset: int = 0,
        currency: str = "USD",
        price_from: float | None = None,
        price_to: float | None = None,
        title: str | None = None,
        sort: str = "price",
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Get items from the marketplace.

        Response is automatically validated through MarketItemsResponse schema.
        If validation fails, a CRITICAL error is logged and Telegram notification sent.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            limit: Number of items to retrieve
            offset: Offset for pagination
            currency: Price currency (USD, EUR etc)
            price_from: Minimum price filter
            price_to: Maximum price filter
            title: Filter by item title
            sort: Sort options (price, price_desc, date, popularity)
            force_refresh: Force refresh cache

        Returns:
            Items as dict with 'objects' key containing list of items
        """
        params = {
            "gameId": game,
            "limit": limit,
            "offset": offset,
            "currency": currency,
        }

        if price_from is not None:
            params["priceFrom"] = str(int(price_from * 100))  # Price in cents

        if price_to is not None:
            params["priceTo"] = str(int(price_to * 100))  # Price in cents

        if title:
            params["title"] = title

        if sort:
            params["orderBy"] = sort

        logger.debug(
            f"Requesting market items: game={game}, limit={limit}, "
            f"price_from={price_from}, price_to={price_to}"
        )

        try:
            response = await self._request(
                "GET",
                self.ENDPOINT_MARKET_ITEMS,
                params=params,
                force_refresh=force_refresh,
            )

            if response and isinstance(response, dict):
                if "objects" in response:
                    items_count = len(response.get("objects", []))
                    logger.info(f"✅ Retrieved {items_count} items for game {game}")
                elif "items" in response:
                    items_count = len(response.get("items", []))
                    logger.info(
                        f"✅ Retrieved {items_count} items for game {game} (via 'items' field)"
                    )
                else:
                    logger.warning(
                        f"⚠️ API response missing 'objects' or 'items'. "
                        f"Available keys: {list(response.keys())}"
                    )

            return response

        except Exception as e:
            logger.exception(f"❌ Error retrieving items: {e}")
            return {"objects": [], "total": {"items": 0, "offers": 0}}

    async def get_all_market_items(
        self,
        game: str = "csgo",
        max_items: int = 1000,
        currency: str = "USD",
        price_from: float | None = None,
        price_to: float | None = None,
        title: str | None = None,
        sort: str = "price",
    ) -> list[dict[str, Any]]:
        """Get all items from the marketplace using pagination.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            max_items: Maximum number of items to retrieve
            currency: Price currency (USD, EUR etc)
            price_from: Minimum price filter
            price_to: Maximum price filter
            title: Filter by item title
            sort: Sort options (price, price_desc, date, popularity)

        Returns:
            List of all items as dict
        """
        all_items: list[dict[str, Any]] = []
        limit = 100
        offset = 0
        total_fetched = 0

        while total_fetched < max_items:
            response = await self.get_market_items(
                game=game,
                limit=limit,
                offset=offset,
                currency=currency,
                price_from=price_from,
                price_to=price_to,
                title=title,
                sort=sort,
            )

            items = response.get("objects", [])
            if not items:
                break

            all_items.extend(items)
            total_fetched += len(items)
            offset += limit

            if len(items) < limit:
                break

        return all_items[:max_items]

    async def list_market_items(  # noqa: PLR0917
        self,
        game_id: str = "a8db",
        limit: int = 100,
        offset: int = 0,
        order_by: str = "price",
        order_dir: str = "asc",
        title: str | None = None,
        price_from: int | None = None,
        price_to: int | None = None,
        tree_filters: str | None = None,
        types: list[str] | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List market items using marketplace API v1.1.0.

        Args:
            game_id: Game ID (default: a8db for CS:GO)
            limit: Number of items per page
            offset: Offset for pagination
            order_by: Sort field (price, title, discount, etc.)
            order_dir: Sort direction (asc, desc)
            title: Filter by item title
            price_from: Minimum price in cents
            price_to: Maximum price in cents
            tree_filters: Tree filters (JSON string)
            types: Item types filter
            cursor: Cursor for pagination

        Returns:
            Market items response
        """
        params: dict[str, Any] = {
            "gameId": game_id,
            "limit": limit,
            "offset": offset,
            "orderBy": order_by,
            "orderDir": order_dir,
        }

        if title:
            params["title"] = title
        if price_from is not None:
            params["priceFrom"] = price_from
        if price_to is not None:
            params["priceTo"] = price_to
        if tree_filters:
            params["treeFilters"] = tree_filters
        if types:
            params["types"] = ",".join(types)
        if cursor:
            params["cursor"] = cursor

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_ITEMS,
            params=params,
        )

    async def get_market_best_offers(
        self,
        game: str = "csgo",
        limit: int = 100,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Get best offers from the market.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            limit: Number of items to retrieve
            currency: Price currency (USD, EUR etc)

        Returns:
            Best offers as dict
        """
        params = {
            "gameId": game,
            "limit": limit,
            "currency": currency,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_BEST_OFFERS,
            params=params,
        )

    async def get_market_aggregated_prices(
        self,
        game: str = "csgo",
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Get aggregated prices for all items in a game.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            currency: Price currency (USD, EUR etc)

        Returns:
            Aggregated prices as dict
        """
        params = {
            "gameId": game,
            "currency": currency,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_PRICE_AGGREGATED,
            params=params,
        )

    async def get_aggregated_prices(
        self,
        titles: list[str],
        game_id: str = "a8db",
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Get aggregated prices for specific items by title.

        Uses POST endpoint for bulk queries (API v1.1.0).

        Args:
            titles: List of item titles
            game_id: Game ID
            currency: Price currency

        Returns:
            Aggregated prices response
        """
        data = {
            "Titles": titles,
        }

        params = {
            "gameId": game_id,
            "currency": currency,
        }

        return await self._request(
            "POST",
            self.ENDPOINT_AGGREGATED_PRICES_POST,
            data=data,
            params=params,
        )

    async def get_aggregated_prices_bulk(
        self,
        titles: list[str],
        game_id: str = "a8db",
        currency: str = "USD",
        chunk_size: int = 100,
    ) -> dict[str, Any]:
        """Get aggregated prices for multiple items in bulk.

        Handles large lists by splitting into chunks.

        Args:
            titles: List of item titles
            game_id: Game ID
            currency: Price currency
            chunk_size: Maximum items per request

        Returns:
            Combined aggregated prices response
        """
        if not titles:
            return {"objects": []}

        all_prices: list[dict[str, Any]] = []

        for i in range(0, len(titles), chunk_size):
            chunk = titles[i : i + chunk_size]
            response = await self.get_aggregated_prices(
                titles=chunk,
                game_id=game_id,
                currency=currency,
            )

            if isinstance(response, dict) and "objects" in response:
                all_prices.extend(response["objects"])
            elif isinstance(response, list):
                all_prices.extend(response)

        return {"objects": all_prices}

    async def get_market_meta(
        self,
        game: str = "csgo",
    ) -> dict[str, Any]:
        """Get market metadata (categories, types, etc.).

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)

        Returns:
            Market metadata as dict
        """
        params = {"gameId": game}

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_META,
            params=params,
        )

    async def get_sales_history_aggregator(
        self,
        title: str,
        game_id: str = "a8db",
        currency: str = "USD",
        limit: int = 100,
        period: str = "1M",
    ) -> dict[str, Any]:
        """Get sales history via trade aggregator API.

        Args:
            title: Item title
            game_id: Game ID
            currency: Price currency
            limit: Number of sales to retrieve
            period: Time period (1D, 1W, 1M, 3M, 6M, 1Y)

        Returns:
            Sales history response
        """
        params = {
            "title": title,
            "gameId": game_id,
            "currency": currency,
            "limit": limit,
            "period": period,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_LAST_SALES,
            params=params,
        )

    async def get_suggested_price(
        self,
        item_name: str,
        game: str = "csgo",
    ) -> float | None:
        """Get suggested price for an item.

        Args:
            item_name: Item name
            game: Game name

        Returns:
            Suggested price as float or None if not found
        """
        response = await self.get_market_items(
            game=game,
            title=item_name,
            limit=1,
        )

        items = response.get("items", []) or response.get("objects", [])
        if not items:
            return None

        item = items[0]
        suggested_price = item.get("suggestedPrice")

        if suggested_price:
            try:
                return float(suggested_price) / 100
            except (ValueError, TypeError):
                try:
                    amount = suggested_price.get("amount", 0)
                    return float(amount) / 100
                except (AttributeError, ValueError, TypeError):
                    return None

        return None

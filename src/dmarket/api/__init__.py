"""DMarket API client package.

This package provides a modular DMarket API client split into:
- client: Base HTTP client with authentication
- endpoints: API endpoint constants and utilities
- auth: Signature generation (Ed25519/HMAC)
- cache: Request caching
- market: Market operations (get items, prices, best offers)
- inventory: User inventory operations (deposit, withdraw, sync)
- trading: Buy/sell operations (buy, sell, offers)
- wallet: Balance and wallet operations
- targets_api: Target (buy order) operations

The main DMarketAPI class in dmarket_api.py uses these modules
internally while maintaining backward compatibility.

Example:
    from src.dmarket.api import DMarketAPIClient, Endpoints

    # Use endpoint utilities
    game_id = Endpoints.get_game_id("csgo")  # => "a8db"
    url = Endpoints.build_url(Endpoints.MARKET_ITEMS, query_params={"gameId": game_id})

    # Use API client
    async with DMarketAPIClient(public_key, secret_key) as api:
        balance = await api.get_balance()
        items = await api.get_market_items(game="csgo")

Mixins for extending functionality:
    from src.dmarket.api import MarketOperationsMixin, WalletOperationsMixin
"""

from src.dmarket.api.client import DMarketAPIClient
from src.dmarket.api.endpoints import (
    EndpointCategory,
    EndpointInfo,
    Endpoints,
    HttpMethod,
)
from src.dmarket.api.inventory import InventoryOperationsMixin
from src.dmarket.api.market import MarketOperationsMixin
from src.dmarket.api.targets_api import TargetsOperationsMixin
from src.dmarket.api.trading import TradingOperationsMixin
from src.dmarket.api.wallet import WalletOperationsMixin


__all__ = [
    "DMarketAPIClient",
    "EndpointCategory",
    "EndpointInfo",
    "Endpoints",
    "HttpMethod",
    "InventoryOperationsMixin",
    "MarketOperationsMixin",
    "TargetsOperationsMixin",
    "TradingOperationsMixin",
    "WalletOperationsMixin",
]

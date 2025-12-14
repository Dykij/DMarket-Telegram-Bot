"""DMarket API client package.

This package provides a modular DMarket API client split into:
- client: Base HTTP client with authentication
- endpoints: API endpoint constants
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
    from src.dmarket.api import DMarketAPIClient

    async with DMarketAPIClient(public_key, secret_key) as api:
        balance = await api.get_balance()
        items = await api.get_market_items(game="csgo")

Mixins for extending functionality:
    from src.dmarket.api import MarketOperationsMixin, WalletOperationsMixin
"""

from src.dmarket.api.client import DMarketAPIClient
from src.dmarket.api.endpoints import Endpoints
from src.dmarket.api.inventory import InventoryOperationsMixin
from src.dmarket.api.market import MarketOperationsMixin
from src.dmarket.api.targets_api import TargetsOperationsMixin
from src.dmarket.api.trading import TradingOperationsMixin
from src.dmarket.api.wallet import WalletOperationsMixin


__all__ = [
    "DMarketAPIClient",
    "Endpoints",
    "InventoryOperationsMixin",
    "MarketOperationsMixin",
    "TargetsOperationsMixin",
    "TradingOperationsMixin",
    "WalletOperationsMixin",
]

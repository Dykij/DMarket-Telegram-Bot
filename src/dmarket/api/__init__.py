"""DMarket API client package.

This package provides a modular DMarket API client split into:
- client: Base HTTP client with authentication
- endpoints: API endpoint constants
- cache: Request caching
- market: Market operations
- inventory: User inventory operations
- trading: Buy/sell operations
- wallet: Balance and wallet operations
- targets: Target (buy order) operations

Example:
    from src.dmarket.api import DMarketAPIClient

    async with DMarketAPIClient(public_key, secret_key) as api:
        balance = await api.get_balance()
        items = await api.get_market_items(game="csgo")
"""

from src.dmarket.api.client import DMarketAPIClient
from src.dmarket.api.endpoints import Endpoints

__all__ = [
    "DMarketAPIClient",
    "Endpoints",
]

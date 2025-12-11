"""DMarket API endpoints constants.

This module contains all API endpoint constants for DMarket API.
Organized by category: account, market, user, operations, analytics.
"""


class Endpoints:
    """DMarket API endpoint constants.

    Organized by category:
    - BASE_URL: Base API URL
    - Account: Balance, details, offers
    - Market: Items, search, prices
    - User: Inventory, offers, targets
    - Operations: Buy, sell, edit, delete
    - Analytics: Sales history, price history
    - V1.1.0: New endpoints added in 2024/2025
    """

    # Base URL
    BASE_URL = "https://api.dmarket.com"

    # Account endpoints
    BALANCE = "/account/v1/balance"
    BALANCE_LEGACY = "/api/v1/account/balance"
    ACCOUNT_DETAILS = "/api/v1/account/details"
    ACCOUNT_OFFERS = "/api/v1/account/offers"

    # Market endpoints
    MARKET_ITEMS = "/exchange/v1/market/items"
    MARKET_PRICE_AGGREGATED = "/exchange/v1/market/aggregated-prices"
    MARKET_META = "/exchange/v1/market/meta"
    MARKET_BEST_OFFERS = "/exchange/v1/market/best-offers"
    MARKET_SEARCH = "/exchange/v1/market/search"

    # User endpoints
    USER_INVENTORY = "/exchange/v1/user/inventory"
    USER_OFFERS = "/exchange/v1/user/offers"
    USER_TARGETS = "/exchange/v1/target-lists"

    # Operations endpoints
    PURCHASE = "/exchange/v1/market/items/buy"
    SELL = "/exchange/v1/user/inventory/sell"
    OFFER_EDIT = "/exchange/v1/user/offers/edit"
    OFFER_DELETE = "/exchange/v1/user/offers/delete"

    # Analytics endpoints
    SALES_HISTORY = "/account/v1/sales-history"
    ITEM_PRICE_HISTORY = "/exchange/v1/market/price-history"
    LAST_SALES = "/trade-aggregator/v1/last-sales"

    # V1.1.0 endpoints (2024/2025)
    AGGREGATED_PRICES_POST = "/marketplace-api/v1/aggregated-prices"
    TARGETS_BY_TITLE = "/marketplace-api/v1/targets-by-title"
    DEPOSIT_ASSETS = "/marketplace-api/v1/deposit-assets"
    DEPOSIT_STATUS = "/marketplace-api/v1/deposit-status"
    WITHDRAW_ASSETS = "/exchange/v1/withdraw-assets"
    INVENTORY_SYNC = "/marketplace-api/v1/user-inventory/sync"
    GAMES_LIST = "/game/v1/games"

    # HTTP error codes
    ERROR_CODES = {
        400: "Bad request or invalid parameters",
        401: "Invalid authentication",
        403: "Access denied",
        404: "Resource not found",
        429: "Rate limit exceeded",
        500: "Internal server error",
        502: "Bad Gateway",
        503: "Service unavailable",
        504: "Gateway timeout",
    }

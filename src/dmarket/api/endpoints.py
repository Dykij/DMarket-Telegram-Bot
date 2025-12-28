"""DMarket API endpoints constants.

This module contains all API endpoint constants for DMarket API.
Organized by category: account, market, user, operations, analytics.

Documentation: https://docs.dmarket.com/v1/swagger.html
Last updated: December 28, 2025
"""


class Endpoints:
    """DMarket API endpoint constants.

    Organized by category:
    - BASE_URL: Base API URL
    - Account: Balance, details, offers, user profile
    - Market: Items, search, prices, best offers
    - User: Inventory, offers, targets
    - Operations: Buy, sell, edit, delete
    - Analytics: Sales history, price history, last sales
    - V1.1.0: New endpoints (aggregated prices, targets-by-title, deposits, withdrawals)

    Note: Prices in API responses are in CENTS (divide by 100 for USD).
    """

    # Base URL
    BASE_URL = "https://api.dmarket.com"

    # Account endpoints
    BALANCE = "/account/v1/balance"
    BALANCE_LEGACY = "/api/v1/account/balance"
    ACCOUNT_DETAILS = "/api/v1/account/details"
    ACCOUNT_OFFERS = "/api/v1/account/offers"
    USER_PROFILE = "/account/v1/user"  # Get user profile

    # Market endpoints
    MARKET_ITEMS = "/exchange/v1/market/items"
    MARKET_PRICE_AGGREGATED = "/exchange/v1/market/aggregated-prices"
    MARKET_META = "/exchange/v1/market/meta"
    MARKET_BEST_OFFERS = "/exchange/v1/market/best-offers"
    MARKET_SEARCH = "/exchange/v1/market/search"
    OFFERS_BY_TITLE = "/exchange/v1/offers-by-title"  # Get offers by item title

    # User endpoints
    USER_INVENTORY = "/exchange/v1/user/inventory"
    USER_OFFERS = "/exchange/v1/user/offers"
    USER_TARGETS = "/exchange/v1/target-lists"

    # Operations endpoints
    PURCHASE = "/exchange/v1/market/items/buy"
    OFFERS_BUY = "/exchange/v1/offers-buy"  # PATCH - buy offers
    SELL = "/exchange/v1/user/inventory/sell"
    OFFER_EDIT = "/exchange/v1/user/offers/edit"
    OFFER_DELETE = "/exchange/v1/user/offers/delete"
    OFFERS_DELETE = "/exchange/v1/offers"  # DELETE - remove offers

    # Analytics endpoints
    SALES_HISTORY = "/account/v1/sales-history"
    ITEM_PRICE_HISTORY = "/exchange/v1/market/price-history"
    LAST_SALES = "/trade-aggregator/v1/last-sales"

    # V1.1.0 endpoints (2024/2025) - Marketplace API
    AGGREGATED_PRICES_POST = "/marketplace-api/v1/aggregated-prices"  # POST - recommended
    AGGREGATED_PRICES_DEPRECATED = "/price-aggregator/v1/aggregated-prices"  # DEPRECATED
    TARGETS_BY_TITLE = "/marketplace-api/v1/targets-by-title"  # GET /{game_id}/{title}
    USER_TARGETS_CREATE = "/marketplace-api/v1/user-targets/create"  # POST
    USER_TARGETS_LIST = "/marketplace-api/v1/user-targets"  # GET
    USER_TARGETS_DELETE = "/marketplace-api/v1/user-targets/delete"  # POST
    USER_TARGETS_CLOSED = "/marketplace-api/v1/user-targets/closed"  # GET - with new statuses
    USER_OFFERS_CREATE = "/marketplace-api/v1/user-offers/create"  # POST
    USER_OFFERS_EDIT = "/marketplace-api/v1/user-offers/edit"  # POST
    USER_OFFERS_CLOSED = "/marketplace-api/v1/user-offers/closed"  # GET - with new statuses
    USER_INVENTORY_V2 = "/marketplace-api/v1/user-inventory"  # GET - with cursor pagination

    # Deposit/Withdraw endpoints (V1.1.0)
    DEPOSIT_ASSETS = "/marketplace-api/v1/deposit-assets"  # POST
    DEPOSIT_STATUS = "/marketplace-api/v1/deposit-status"  # GET /{DepositID}
    WITHDRAW_ASSETS = "/exchange/v1/withdraw-assets"  # POST
    INVENTORY_SYNC = "/marketplace-api/v1/user-inventory/sync"  # POST

    # Game endpoints
    GAMES_LIST = "/game/v1/games"  # GET - list all supported games

    # Game IDs (for reference)
    GAME_CSGO = "a8db"  # CS:GO / CS2
    GAME_DOTA2 = "9a92"  # Dota 2
    GAME_TF2 = "tf2"  # Team Fortress 2
    GAME_RUST = "rust"  # Rust

    # HTTP error codes with descriptions
    ERROR_CODES = {
        400: "Bad request or invalid parameters",
        401: "Invalid authentication - check API keys",
        403: "Access denied - insufficient permissions",
        404: "Resource not found",
        429: "Rate limit exceeded - use Retry-After header",
        500: "Internal server error",
        502: "Bad Gateway",
        503: "Service unavailable",
        504: "Gateway timeout",
    }

    # Target/Offer status values (V1.1.0)
    TARGET_STATUS_ACTIVE = "TargetStatusActive"
    TARGET_STATUS_INACTIVE = "TargetStatusInactive"
    OFFER_STATUS_ACTIVE = "OfferStatusActive"
    OFFER_STATUS_SOLD = "OfferStatusSold"
    OFFER_STATUS_INACTIVE = "OfferStatusInactive"

    # Closed target/offer status values (V1.1.0 - new)
    CLOSED_STATUS_SUCCESSFUL = "successful"
    CLOSED_STATUS_REVERTED = "reverted"  # New in v1.1.0
    CLOSED_STATUS_TRADE_PROTECTED = "trade_protected"  # New in v1.1.0

    # Transfer status values (V1.1.0)
    TRANSFER_STATUS_PENDING = "TransferStatusPending"
    TRANSFER_STATUS_COMPLETED = "TransferStatusCompleted"
    TRANSFER_STATUS_FAILED = "TransferStatusFailed"

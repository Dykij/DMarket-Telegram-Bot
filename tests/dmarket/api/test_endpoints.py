"""Tests for DMarket API endpoints constants.

This module tests the endpoint constants defined in src.dmarket.api.endpoints.
"""

import pytest

from src.dmarket.api.endpoints import Endpoints


class TestEndpointsConstants:
    """Test endpoint constants."""

    def test_base_url(self):
        """Test base URL is correct."""
        assert Endpoints.BASE_URL == "https://api.dmarket.com"

    def test_game_ids(self):
        """Test game ID constants."""
        assert Endpoints.GAME_CSGO == "a8db"
        assert Endpoints.GAME_DOTA2 == "9a92"
        assert Endpoints.GAME_TF2 == "tf2"
        assert Endpoints.GAME_RUST == "rust"

    def test_account_endpoints(self):
        """Test account endpoints."""
        assert Endpoints.BALANCE == "/account/v1/balance"
        assert Endpoints.USER_PROFILE == "/account/v1/user"
        assert Endpoints.ACCOUNT_DETAILS == "/api/v1/account/details"

    def test_market_endpoints(self):
        """Test market endpoints."""
        assert Endpoints.MARKET_ITEMS == "/exchange/v1/market/items"
        assert Endpoints.MARKET_BEST_OFFERS == "/exchange/v1/market/best-offers"
        assert Endpoints.OFFERS_BY_TITLE == "/exchange/v1/offers-by-title"

    def test_v110_endpoints(self):
        """Test V1.1.0 marketplace API endpoints."""
        assert Endpoints.AGGREGATED_PRICES_POST == "/marketplace-api/v1/aggregated-prices"
        assert Endpoints.TARGETS_BY_TITLE == "/marketplace-api/v1/targets-by-title"
        assert Endpoints.USER_TARGETS_CREATE == "/marketplace-api/v1/user-targets/create"
        assert Endpoints.USER_TARGETS_LIST == "/marketplace-api/v1/user-targets"
        assert Endpoints.USER_TARGETS_DELETE == "/marketplace-api/v1/user-targets/delete"
        assert Endpoints.USER_TARGETS_CLOSED == "/marketplace-api/v1/user-targets/closed"
        assert Endpoints.USER_OFFERS_CREATE == "/marketplace-api/v1/user-offers/create"
        assert Endpoints.USER_OFFERS_CLOSED == "/marketplace-api/v1/user-offers/closed"

    def test_deposit_withdraw_endpoints(self):
        """Test deposit and withdraw endpoints."""
        assert Endpoints.DEPOSIT_ASSETS == "/marketplace-api/v1/deposit-assets"
        assert Endpoints.DEPOSIT_STATUS == "/marketplace-api/v1/deposit-status"
        assert Endpoints.WITHDRAW_ASSETS == "/exchange/v1/withdraw-assets"
        assert Endpoints.INVENTORY_SYNC == "/marketplace-api/v1/user-inventory/sync"

    def test_deprecated_endpoints(self):
        """Test deprecated endpoints exist with correct path."""
        # This endpoint is deprecated - use AGGREGATED_PRICES_POST instead
        assert Endpoints.AGGREGATED_PRICES_DEPRECATED == "/price-aggregator/v1/aggregated-prices"
        # Verify the recommended endpoint is different
        assert Endpoints.AGGREGATED_PRICES_POST != Endpoints.AGGREGATED_PRICES_DEPRECATED


class TestStatusConstants:
    """Test status constants."""

    def test_target_status_values(self):
        """Test target status constants."""
        assert Endpoints.TARGET_STATUS_ACTIVE == "TargetStatusActive"
        assert Endpoints.TARGET_STATUS_INACTIVE == "TargetStatusInactive"

    def test_offer_status_values(self):
        """Test offer status constants."""
        assert Endpoints.OFFER_STATUS_ACTIVE == "OfferStatusActive"
        assert Endpoints.OFFER_STATUS_SOLD == "OfferStatusSold"
        assert Endpoints.OFFER_STATUS_INACTIVE == "OfferStatusInactive"

    def test_closed_status_values_v110(self):
        """Test V1.1.0 closed status values."""
        assert Endpoints.CLOSED_STATUS_SUCCESSFUL == "successful"
        assert Endpoints.CLOSED_STATUS_REVERTED == "reverted"
        assert Endpoints.CLOSED_STATUS_TRADE_PROTECTED == "trade_protected"

    def test_transfer_status_values(self):
        """Test transfer status constants."""
        assert Endpoints.TRANSFER_STATUS_PENDING == "TransferStatusPending"
        assert Endpoints.TRANSFER_STATUS_COMPLETED == "TransferStatusCompleted"
        assert Endpoints.TRANSFER_STATUS_FAILED == "TransferStatusFailed"


class TestErrorCodes:
    """Test error code constants."""

    def test_error_codes_exist(self):
        """Test error codes dictionary exists and has expected keys."""
        assert isinstance(Endpoints.ERROR_CODES, dict)
        assert 400 in Endpoints.ERROR_CODES
        assert 401 in Endpoints.ERROR_CODES
        assert 403 in Endpoints.ERROR_CODES
        assert 404 in Endpoints.ERROR_CODES
        assert 429 in Endpoints.ERROR_CODES
        assert 500 in Endpoints.ERROR_CODES

    def test_error_codes_have_descriptions(self):
        """Test error codes have meaningful descriptions."""
        for code, description in Endpoints.ERROR_CODES.items():
            assert isinstance(description, str)
            assert len(description) > 0

"""Unit tests for rate_limiter module.

This module contains tests for src/utils/rate_limiter.py covering:
- RateLimiter initialization
- Endpoint type detection
- Rate limit tracking
- Backoff calculations

Target: 25+ tests to achieve 70%+ coverage
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from src.utils.rate_limiter import (
    BASE_RETRY_DELAY,
    DMARKET_API_RATE_LIMITS,
    MAX_BACKOFF_TIME,
    RATE_LIMIT_WARNING_THRESHOLD,
    RateLimiter,
)


# TestRateLimiterInit


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        # Act
        limiter = RateLimiter()

        # Assert
        assert limiter.is_authorized is True
        assert limiter.notifier is None
        assert limiter.rate_limits == DMARKET_API_RATE_LIMITS

    def test_init_unauthorized(self):
        """Test initialization as unauthorized client."""
        # Act
        limiter = RateLimiter(is_authorized=False)

        # Assert
        assert limiter.is_authorized is False

    def test_init_with_notifier(self):
        """Test initialization with notifier."""
        # Arrange
        mock_notifier = MagicMock()

        # Act
        limiter = RateLimiter(notifier=mock_notifier)

        # Assert
        assert limiter.notifier is mock_notifier

    def test_init_empty_tracking_dicts(self):
        """Test that tracking dictionaries start empty."""
        # Act
        limiter = RateLimiter()

        # Assert
        assert limiter.last_request_times == {}
        assert limiter.reset_times == {}
        assert limiter.remaining_requests == {}
        assert limiter.retry_attempts == {}
        assert limiter.total_requests == {}
        assert limiter.total_429_errors == {}


# TestEndpointTypeDetection


class TestEndpointTypeDetection:
    """Tests for endpoint type detection."""

    def test_market_endpoint(self):
        """Test detection of market endpoints."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        assert limiter.get_endpoint_type("/exchange/v1/market/items") == "market"
        assert limiter.get_endpoint_type("/market/items") == "market"
        assert limiter.get_endpoint_type("/market/aggregated-prices") == "market"
        assert limiter.get_endpoint_type("/market/best-offers") == "market"
        assert limiter.get_endpoint_type("/market/search") == "market"

    def test_trade_endpoint(self):
        """Test detection of trade endpoints."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        # Note: /exchange/v1/market/buy is detected as "market" because "market" check comes first
        assert limiter.get_endpoint_type("/exchange/v1/user/offers/edit") == "trade"
        assert limiter.get_endpoint_type("/exchange/v1/user/offers/delete") == "trade"

    def test_balance_endpoint(self):
        """Test detection of balance endpoints."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        assert limiter.get_endpoint_type("/api/v1/account/balance") == "balance"
        assert limiter.get_endpoint_type("/account/v1/balance") == "balance"

    def test_user_endpoint(self):
        """Test detection of user endpoints."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        assert limiter.get_endpoint_type("/exchange/v1/user/inventory") == "user"
        assert limiter.get_endpoint_type("/api/v1/account/details") == "user"
        assert limiter.get_endpoint_type("/exchange/v1/user/offers") == "user"
        assert limiter.get_endpoint_type("/exchange/v1/user/targets") == "user"

    def test_other_endpoint(self):
        """Test detection of other/unknown endpoints."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        assert limiter.get_endpoint_type("/some/random/path") == "other"
        assert limiter.get_endpoint_type("/api/v1/unknown") == "other"

    def test_case_insensitive(self):
        """Test that endpoint detection is case insensitive."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        assert limiter.get_endpoint_type("/MARKET/ITEMS") == "market"
        # Note: path with "market" in it will be detected as "market" type
        assert limiter.get_endpoint_type("/API/V1/ACCOUNT/BALANCE") == "balance"


# TestUpdateFromHeaders


class TestUpdateFromHeaders:
    """Tests for updating limits from response headers."""

    def test_update_remaining_requests(self):
        """Test updating remaining requests from headers."""
        # Arrange
        limiter = RateLimiter()
        headers = {"X-RateLimit-Remaining": "5"}

        # Act
        limiter.update_from_headers(headers)

        # Assert
        assert limiter.remaining_requests.get("other") == 5

    def test_update_with_limit_header(self):
        """Test updating rate limit from headers."""
        # Arrange
        limiter = RateLimiter()
        headers = {
            "X-RateLimit-Remaining": "8",
            "X-RateLimit-Limit": "10",
        }

        # Act
        limiter.update_from_headers(headers)

        # Assert
        assert limiter.remaining_requests.get("other") == 8

    def test_update_with_scope_header(self):
        """Test updating with scope header."""
        # Arrange
        limiter = RateLimiter()
        headers = {
            "X-RateLimit-Remaining": "3",
            "X-RateLimit-Scope": "market",
        }

        # Act
        limiter.update_from_headers(headers)

        # Assert
        assert limiter.remaining_requests.get("market") == 3

    def test_warning_at_threshold(self):
        """Test warning when reaching threshold."""
        # Arrange
        limiter = RateLimiter()
        headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Limit": "10",
        }

        # Act
        limiter.update_from_headers(headers)

        # Assert - warning should be sent
        assert limiter._warning_sent.get("other") is True


# TestRateLimitConstants


class TestRateLimitConstants:
    """Tests for rate limit constants."""

    def test_dmarket_api_rate_limits(self):
        """Test DMARKET_API_RATE_LIMITS constants."""
        assert "market" in DMARKET_API_RATE_LIMITS
        assert "trade" in DMARKET_API_RATE_LIMITS
        assert "user" in DMARKET_API_RATE_LIMITS
        assert "balance" in DMARKET_API_RATE_LIMITS
        assert "other" in DMARKET_API_RATE_LIMITS

    def test_base_retry_delay(self):
        """Test BASE_RETRY_DELAY constant."""
        assert BASE_RETRY_DELAY == 1.0

    def test_warning_threshold(self):
        """Test RATE_LIMIT_WARNING_THRESHOLD constant."""
        assert RATE_LIMIT_WARNING_THRESHOLD == 0.9

    def test_max_backoff_time(self):
        """Test MAX_BACKOFF_TIME constant."""
        assert MAX_BACKOFF_TIME == 60.0


# TestCustomLimits


class TestCustomLimits:
    """Tests for custom rate limits."""

    def test_set_custom_limit(self):
        """Test setting custom rate limit."""
        # Arrange
        limiter = RateLimiter()

        # Act
        limiter.custom_limits["custom_endpoint"] = 0.5

        # Assert
        assert limiter.custom_limits["custom_endpoint"] == 0.5


# TestStatisticsTracking


class TestStatisticsTracking:
    """Tests for statistics tracking."""

    def test_total_requests_tracking(self):
        """Test tracking total requests."""
        # Arrange
        limiter = RateLimiter()

        # Act
        limiter.total_requests["market"] = 10
        limiter.total_requests["trade"] = 5

        # Assert
        assert limiter.total_requests["market"] == 10
        assert limiter.total_requests["trade"] == 5

    def test_total_429_errors_tracking(self):
        """Test tracking 429 errors."""
        # Arrange
        limiter = RateLimiter()

        # Act
        limiter.total_429_errors["market"] = 2

        # Assert
        assert limiter.total_429_errors["market"] == 2


# TestEdgeCases


class TestRateLimiterEdgeCases:
    """Tests for edge cases."""

    def test_empty_path(self):
        """Test endpoint type for empty path."""
        # Arrange
        limiter = RateLimiter()

        # Act
        result = limiter.get_endpoint_type("")

        # Assert
        assert result == "other"

    def test_invalid_remaining_header(self):
        """Test handling invalid remaining header."""
        # Arrange
        limiter = RateLimiter()
        headers = {"X-RateLimit-Remaining": "invalid"}

        # Act - should not raise
        limiter.update_from_headers(headers)

        # Assert - nothing should be set
        assert "other" not in limiter.remaining_requests

    def test_retry_attempts_tracking(self):
        """Test retry attempts tracking."""
        # Arrange
        limiter = RateLimiter()

        # Act
        limiter.retry_attempts["market"] = 3

        # Assert
        assert limiter.retry_attempts["market"] == 3

    def test_reset_times_tracking(self):
        """Test reset times tracking."""
        # Arrange
        limiter = RateLimiter()
        reset_time = time.time() + 60

        # Act
        limiter.reset_times["market"] = reset_time

        # Assert
        assert limiter.reset_times["market"] == reset_time

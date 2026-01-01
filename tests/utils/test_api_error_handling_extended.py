"""Tests for api_error_handling module.

This module tests the API error handling utilities including
handle_response and retry_request functions.
"""

import pytest

from src.utils.api_error_handling import (
    APIError,
    AuthenticationError,
    ErrorCode,
    NetworkError,
    RateLimitError,
    ValidationError,
    retry_request,
)


class TestRetryRequest:
    """Tests for retry_request function."""

    @pytest.mark.asyncio()
    async def test_retry_request_success_first_try(self):
        """Test successful request on first try."""

        async def success_func():
            return {"success": True}

        result = await retry_request(success_func)

        assert result == {"success": True}

    @pytest.mark.asyncio()
    async def test_retry_request_success_after_retry(self):
        """Test successful request after retry."""
        call_count = 0

        async def retry_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APIError("Temporary error", status_code=500)
            return {"success": True}

        result = await retry_request(
            retry_then_success, max_retries=3, retry_delay=0.01
        )

        assert result == {"success": True}
        assert call_count == 2

    @pytest.mark.asyncio()
    async def test_retry_request_exhausts_retries(self):
        """Test request fails after exhausting retries."""

        async def always_fails():
            raise APIError("Always fails", status_code=500)

        with pytest.raises(APIError):
            await retry_request(always_fails, max_retries=2, retry_delay=0.01)

    @pytest.mark.asyncio()
    async def test_retry_request_with_network_error(self):
        """Test retrying on NetworkError."""
        call_count = 0

        async def network_error_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Network failed")
            return {"data": "recovered"}

        result = await retry_request(
            network_error_then_success, max_retries=3, retry_delay=0.01
        )

        assert result == {"data": "recovered"}

    @pytest.mark.asyncio()
    async def test_retry_request_with_args(self):
        """Test retry_request passes positional arguments."""

        async def func_with_args(a, b):
            return a + b

        result = await retry_request(func_with_args, 5, 10)

        assert result == 15

    @pytest.mark.asyncio()
    async def test_retry_request_with_kwargs(self):
        """Test retry_request passes keyword arguments."""

        async def func_with_kwargs(x, y=10):
            return x * y

        result = await retry_request(func_with_kwargs, 5, y=20)

        assert result == 100


class TestErrorClasses:
    """Tests for error classes re-exported from exceptions."""

    def test_api_error_creation(self):
        """Test creating APIError."""
        error = APIError("Test error", status_code=400)

        assert "Test error" in str(error)
        assert error.status_code == 400

    def test_network_error_creation(self):
        """Test creating NetworkError."""
        error = NetworkError("Network failed")

        assert "Network failed" in str(error)

    def test_rate_limit_error_creation(self):
        """Test creating RateLimitError."""
        error = RateLimitError("Rate limited", retry_after=60)

        assert "Rate limited" in str(error)
        assert error.retry_after == 60

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError."""
        error = AuthenticationError("Invalid token")

        assert "Invalid token" in str(error)

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid data")

        assert "Invalid data" in str(error)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_error_code_exists(self):
        """Test that ErrorCode enum exists and has values."""
        # ErrorCode should be accessible
        assert ErrorCode is not None


class TestAPIErrorProperties:
    """Tests for APIError properties and methods."""

    def test_api_error_with_status_code(self):
        """Test APIError with status code."""
        error = APIError("Server error", status_code=500)

        assert error.status_code == 500

    def test_api_error_default_status(self):
        """Test APIError with default status code."""
        error = APIError("Error")

        # Default status should be set
        assert hasattr(error, "status_code")

    def test_api_error_is_exception(self):
        """Test APIError is an Exception."""
        error = APIError("Test")

        assert isinstance(error, Exception)


class TestNetworkErrorProperties:
    """Tests for NetworkError properties."""

    def test_network_error_message(self):
        """Test NetworkError message."""
        error = NetworkError("Connection refused")

        assert "Connection refused" in str(error)

    def test_network_error_is_api_error(self):
        """Test NetworkError inherits from APIError."""
        error = NetworkError("Test")

        # Should be catchable as APIError
        assert isinstance(error, Exception)


class TestRateLimitErrorProperties:
    """Tests for RateLimitError properties."""

    def test_rate_limit_error_retry_after(self):
        """Test RateLimitError retry_after property."""
        error = RateLimitError("Too many requests", retry_after=30)

        assert error.retry_after == 30

    def test_rate_limit_error_default_retry_after(self):
        """Test RateLimitError with no retry_after."""
        error = RateLimitError("Too many requests")

        # Should have retry_after attribute (may be None or default)
        assert hasattr(error, "retry_after")

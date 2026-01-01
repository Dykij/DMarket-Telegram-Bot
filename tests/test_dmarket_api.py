"""Unit tests for refactored DMarket API _request() method - Phase 2.

These tests verify the behavior of the refactored helper functions
extracted from the original 297-line _request() method.

Test Coverage:
- Cache key preparation
- Cache retrieval
- Request body preparation
- HTTP request execution
- JSON parsing
- Retry delay calculation
- Error data building
- HTTP status error handling
- Network error handling
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.dmarket.dmarket_api_refactored import (
    _build_error_data,
    _calculate_retry_delay,
    _execute_http_request,
    _handle_http_status_error,
    _handle_network_error,
    _parse_response_json,
    _prepare_cache_key,
    _prepare_request_body,
    _should_return_error_data,
    _try_get_cached,
)


class TestPrepareCacheKey:
    """Tests for _prepare_cache_key function."""

    def test_prepare_cache_key_for_get_request(self):
        """Test cache key generation for GET requests."""
        # Arrange
        method = "GET"
        path = "/market/items"
        params = {"game": "csgo", "limit": 100}
        data = {}

        def get_cache_key_fn(m, p, prm, d):
            return f"{m}:{p}:{prm!s}"

        # Act
        result = _prepare_cache_key(method, path, params, data, get_cache_key_fn)

        # Assert
        assert result == "GET:/market/items:{'game': 'csgo', 'limit': 100}"

    def test_prepare_cache_key_for_post_request_returns_empty(self):
        """Test that POST requests don't generate cache keys."""
        # Arrange
        method = "POST"
        path = "/market/buy"
        params = {}
        data = {"item_id": "123"}

        def get_cache_key_fn(m, p, prm, d):
            return f"{m}:{p}"

        # Act
        result = _prepare_cache_key(method, path, params, data, get_cache_key_fn)

        # Assert
        assert result == ""


class TestTryGetCached:
    """Tests for _try_get_cached function."""

    def test_try_get_cached_returns_data_when_found(self):
        """Test cache retrieval when data exists."""
        # Arrange
        cache_key = "test_key"
        is_cacheable = True
        cached_data = {"result": "cached"}

        def get_from_cache_fn(key):
            return cached_data
        path = "/test"

        # Act
        result = _try_get_cached(cache_key, is_cacheable, get_from_cache_fn, path)

        # Assert
        assert result == cached_data

    def test_try_get_cached_returns_none_when_not_cacheable(self):
        """Test that non-cacheable requests return None."""
        # Arrange
        cache_key = "test_key"
        is_cacheable = False

        def get_from_cache_fn(key):
            return {"data": "should_not_return"}
        path = "/test"

        # Act
        result = _try_get_cached(cache_key, is_cacheable, get_from_cache_fn, path)

        # Assert
        assert result is None

    def test_try_get_cached_returns_none_when_cache_miss(self):
        """Test cache miss returns None."""
        # Arrange
        cache_key = "missing_key"
        is_cacheable = True

        def get_from_cache_fn(key):
            return None
        path = "/test"

        # Act
        result = _try_get_cached(cache_key, is_cacheable, get_from_cache_fn, path)

        # Assert
        assert result is None


class TestPrepareRequestBody:
    """Tests for _prepare_request_body function."""

    def test_prepare_request_body_for_post(self):
        """Test JSON body preparation for POST requests."""
        # Arrange
        method = "POST"
        data = {"item_id": "123", "price": 1000}

        # Act
        result = _prepare_request_body(method, data)

        # Assert
        assert "item_id" in result
        assert "123" in result
        assert "1000" in result

    def test_prepare_request_body_for_get_returns_empty(self):
        """Test GET requests don't prepare body."""
        # Arrange
        method = "GET"
        data = {"some": "data"}

        # Act
        result = _prepare_request_body(method, data)

        # Assert
        assert result == ""

    def test_prepare_request_body_with_empty_data(self):
        """Test empty data returns empty string."""
        # Arrange
        method = "POST"
        data = {}

        # Act
        result = _prepare_request_body(method, data)

        # Assert
        assert result == ""


class TestExecuteHttpRequest:
    """Tests for _execute_http_request function."""

    @pytest.mark.asyncio()
    async def test_execute_http_request_get(self):
        """Test GET request execution."""
        # Arrange
        method = "GET"
        url = "https://api.dmarket.com/market/items"
        client = AsyncMock(spec=httpx.AsyncClient)
        headers = {"X-Api-Key": "test"}
        params = {"game": "csgo"}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200

        with patch(
            "src.dmarket.dmarket_api_refactored.call_with_circuit_breaker",
            return_value=mock_response,
        ):
            # Act
            result = await _execute_http_request(method, url, client, headers, params)

            # Assert
            assert result == mock_response

    @pytest.mark.asyncio()
    async def test_execute_http_request_post(self):
        """Test POST request execution."""
        # Arrange
        method = "POST"
        url = "https://api.dmarket.com/market/buy"
        client = AsyncMock(spec=httpx.AsyncClient)
        headers = {"X-Api-Key": "test"}
        data = {"item_id": "123"}

        mock_response = MagicMock(spec=httpx.Response)

        with patch(
            "src.dmarket.dmarket_api_refactored.call_with_circuit_breaker",
            return_value=mock_response,
        ):
            # Act
            result = await _execute_http_request(method, url, client, headers, data=data)

            # Assert
            assert result == mock_response

    @pytest.mark.asyncio()
    async def test_execute_http_request_unsupported_method_raises_error(self):
        """Test unsupported HTTP method raises ValueError."""
        # Arrange
        method = "PATCH"
        url = "https://api.dmarket.com/test"
        client = AsyncMock()
        headers = {}

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported HTTP method"):
            await _execute_http_request(method, url, client, headers)


class TestParseResponseJson:
    """Tests for _parse_response_json function."""

    def test_parse_response_json_success(self):
        """Test successful JSON parsing."""
        # Arrange
        response = MagicMock(spec=httpx.Response)
        response.json.return_value = {"result": "success"}
        response.status_code = 200

        # Act
        result = _parse_response_json(response)

        # Assert
        assert result == {"result": "success"}

    def test_parse_response_json_fallback_on_error(self):
        """Test fallback to text when JSON parsing fails."""
        # Arrange
        response = MagicMock(spec=httpx.Response)
        response.json.side_effect = ValueError("Invalid JSON")
        response.text = "Invalid response"
        response.status_code = 500

        # Act
        result = _parse_response_json(response)

        # Assert
        assert result == {"text": "Invalid response", "status_code": 500}


class TestCalculateRetryDelay:
    """Tests for _calculate_retry_delay function."""

    def test_calculate_retry_delay_for_rate_limit_with_header(self):
        """Test delay calculation with Retry-After header."""
        # Arrange
        status_code = 429
        retry_headers = {"Retry-After": "60"}
        current_delay = 2.0
        retries = 1

        # Act
        result = _calculate_retry_delay(status_code, retry_headers, current_delay, retries)

        # Assert
        assert result == 60.0

    def test_calculate_retry_delay_for_rate_limit_exponential_backoff(self):
        """Test exponential backoff for rate limit without header."""
        # Arrange
        status_code = 429
        retry_headers = {}
        current_delay = 2.0
        retries = 2

        # Act
        result = _calculate_retry_delay(status_code, retry_headers, current_delay, retries)

        # Assert
        assert result == 4.0  # current_delay * 2

    def test_calculate_retry_delay_for_rate_limit_max_30_seconds(self):
        """Test max delay cap of 30 seconds."""
        # Arrange
        status_code = 429
        retry_headers = {}
        current_delay = 20.0
        retries = 3

        # Act
        result = _calculate_retry_delay(status_code, retry_headers, current_delay, retries)

        # Assert
        assert result == 30.0  # capped at 30

    def test_calculate_retry_delay_for_other_errors(self):
        """Test linear backoff for non-rate-limit errors."""
        # Arrange
        status_code = 500
        retry_headers = {}
        current_delay = 2.0
        retries = 3

        # Act
        result = _calculate_retry_delay(status_code, retry_headers, current_delay, retries)

        # Assert
        assert result == 2.5  # 1.0 + 3 * 0.5


class TestBuildErrorData:
    """Tests for _build_error_data function."""

    def test_build_error_data_with_json_response(self):
        """Test error data building from JSON response."""
        # Arrange
        response = MagicMock(spec=httpx.Response)
        response.json.return_value = {"message": "Item not found", "code": "ITEM_NOT_FOUND"}
        response.text = ""
        status_code = 404
        error_description = "Resource not found"

        # Act
        result = _build_error_data(response, status_code, error_description)

        # Assert
        assert result == {
            "error": True,
            "code": "ITEM_NOT_FOUND",
            "message": "Item not found",
            "status": 404,
            "description": "Resource not found",
        }

    def test_build_error_data_fallback_to_text(self):
        """Test error data building when JSON parsing fails."""
        # Arrange
        response = MagicMock(spec=httpx.Response)
        response.json = MagicMock(side_effect=Exception("JSON decode error"))
        response.text = "Server error"
        status_code = 500
        error_description = "Internal server error"

        # Act
        result = _build_error_data(response, status_code, error_description)

        # Assert
        assert result["message"] == "Server error"
        assert result["code"] == 500


class TestShouldReturnErrorData:
    """Tests for _should_return_error_data function."""

    def test_should_return_error_data_for_400(self):
        """Test 400 status returns error data."""
        assert _should_return_error_data(400) is True

    def test_should_return_error_data_for_404(self):
        """Test 404 status returns error data."""
        assert _should_return_error_data(404) is True

    def test_should_return_error_data_for_500_is_false(self):
        """Test 500 status raises exception."""
        assert _should_return_error_data(500) is False


class TestHandleHttpStatusError:
    """Tests for _handle_http_status_error function."""

    @pytest.mark.asyncio()
    async def test_handle_http_status_error_retryable(self):
        """Test handling of retryable HTTP errors."""
        # Arrange
        response = MagicMock(spec=httpx.Response)
        response.status_code = 429
        response.text = "Rate limit"
        response.headers = {"Retry-After": "10"}

        error = httpx.HTTPStatusError("Rate limit", request=MagicMock(), response=response)

        # Act
        should_retry, new_delay, exception = await _handle_http_status_error(
            error, "GET", "/market/items", 0, 3, time.time(), {429, 500}, {429: "Rate limit"}, 1.0
        )

        # Assert
        assert should_retry is True
        assert new_delay == 10.0
        assert exception is None

    @pytest.mark.asyncio()
    async def test_handle_http_status_error_non_retryable(self):
        """Test handling of non-retryable HTTP errors."""
        # Arrange
        response = MagicMock(spec=httpx.Response)
        response.status_code = 403
        response.text = "Forbidden"
        response.headers = {}
        response.json.return_value = {"message": "Access denied"}

        error = httpx.HTTPStatusError("Forbidden", request=MagicMock(), response=response)

        # Act
        should_retry, _new_delay, exception = await _handle_http_status_error(
            error, "GET", "/market/items", 0, 3, time.time(), {429, 500}, {403: "Forbidden"}, 1.0
        )

        # Assert
        assert should_retry is False
        assert exception is not None
        assert "Access denied" in str(exception)


class TestHandleNetworkError:
    """Tests for _handle_network_error function."""

    @pytest.mark.asyncio()
    async def test_handle_network_error(self):
        """Test handling of network errors."""
        # Arrange
        error = httpx.ConnectError("Connection failed")

        # Act
        should_retry, new_delay = await _handle_network_error(error, "GET", "/market/items", 1, 2.0)

        # Assert
        assert should_retry is True
        assert new_delay == 3.0  # 2.0 * 1.5

    @pytest.mark.asyncio()
    async def test_handle_network_error_max_delay(self):
        """Test max delay cap for network errors."""
        # Arrange
        error = httpx.ReadError("Read timeout")

        # Act
        should_retry, new_delay = await _handle_network_error(error, "GET", "/market/items", 5, 8.0)

        # Assert
        assert should_retry is True
        assert new_delay == 10.0  # capped at 10


# ============================================================================
# Integration Test for _request_refactored
# ============================================================================


class TestRequestRefactoredIntegration:
    """Integration tests for the complete refactored _request function."""

    @pytest.mark.asyncio()
    async def test_request_refactored_success_flow(self):
        """Test successful request flow end-to-end."""
        # This would require mocking DMarketAPI instance
        # Placeholder for future implementation

    @pytest.mark.asyncio()
    async def test_request_refactored_cache_hit(self):
        """Test cache hit returns cached data."""
        # Placeholder for future implementation

    @pytest.mark.asyncio()
    async def test_request_refactored_retry_on_rate_limit(self):
        """Test retry logic for rate limit errors."""
        # Placeholder for future implementation

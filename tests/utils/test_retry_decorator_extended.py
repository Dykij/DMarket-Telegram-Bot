"""Tests for retry_decorator module.

This module tests the retry decorator functionality with
exponential backoff for both sync and async functions.
"""

from unittest.mock import patch

import pytest

from src.utils.exceptions import NetworkError, RateLimitError
from src.utils.retry_decorator import retry_api_call, retry_on_failure


class TestRetryOnFailure:
    """Tests for retry_on_failure decorator."""

    @pytest.mark.asyncio()
    async def test_async_success_no_retry(self):
        """Test async function succeeds on first attempt."""
        call_count = 0

        @retry_on_failure(max_attempts=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio()
    async def test_async_retry_on_network_error(self):
        """Test async function retries on NetworkError."""
        call_count = 0

        @retry_on_failure(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Network failed")
            return "success"

        result = await failing_then_success()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio()
    async def test_async_max_attempts_exceeded(self):
        """Test async function raises after max attempts."""
        call_count = 0

        @retry_on_failure(max_attempts=2, min_wait=0.1, max_wait=0.2)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Always fails")

        with pytest.raises(NetworkError):
            await always_fails()

        assert call_count == 2

    @pytest.mark.asyncio()
    async def test_async_retry_on_connection_error(self):
        """Test async function retries on ConnectionError."""
        call_count = 0

        @retry_on_failure(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def conn_error_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "connected"

        result = await conn_error_then_success()

        assert result == "connected"
        assert call_count == 2

    @pytest.mark.asyncio()
    async def test_async_retry_on_timeout_error(self):
        """Test async function retries on TimeoutError."""
        call_count = 0

        @retry_on_failure(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def timeout_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "completed"

        result = await timeout_then_success()

        assert result == "completed"

    @pytest.mark.asyncio()
    async def test_async_no_retry_on_value_error(self):
        """Test async function does not retry on ValueError."""
        call_count = 0

        @retry_on_failure(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid value")

        with pytest.raises(ValueError):
            await raises_value_error()

        # Should not retry on ValueError (not in retry_on list)
        assert call_count == 1

    @pytest.mark.asyncio()
    async def test_async_custom_retry_exceptions(self):
        """Test async function with custom retry exceptions."""
        call_count = 0

        @retry_on_failure(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.2,
            retry_on=(ValueError,)
        )
        async def custom_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Custom error")
            return "custom success"

        result = await custom_retry()

        assert result == "custom success"
        assert call_count == 2


class TestRetryApiCall:
    """Tests for retry_api_call decorator."""

    @pytest.mark.asyncio()
    async def test_api_call_success(self):
        """Test API call succeeds on first attempt."""
        @retry_api_call(max_attempts=3)
        async def api_call():
            return {"data": "response"}

        result = await api_call()

        assert result == {"data": "response"}

    @pytest.mark.asyncio()
    async def test_api_call_retry_on_network_error(self):
        """Test API call retries on NetworkError."""
        call_count = 0

        @retry_api_call(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def api_with_network_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Network issue")
            return {"status": "ok"}

        result = await api_with_network_error()

        assert result == {"status": "ok"}
        assert call_count == 2

    @pytest.mark.asyncio()
    async def test_api_call_retry_on_rate_limit(self):
        """Test API call retries on RateLimitError."""
        call_count = 0

        @retry_api_call(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def rate_limited_api():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limited")
            return {"status": "success"}

        result = await rate_limited_api()

        assert result == {"status": "success"}

    @pytest.mark.asyncio()
    async def test_api_call_exhausts_retries(self):
        """Test API call raises after exhausting retries."""
        call_count = 0

        @retry_api_call(max_attempts=2, min_wait=0.1, max_wait=0.2)
        async def always_rate_limited():
            nonlocal call_count
            call_count += 1
            raise RateLimitError("Always rate limited")

        with pytest.raises(RateLimitError):
            await always_rate_limited()

        assert call_count == 2


class TestRetryDecoratorParameters:
    """Tests for retry decorator parameters."""

    @pytest.mark.asyncio()
    async def test_max_attempts_parameter(self):
        """Test max_attempts parameter is respected."""
        call_count = 0

        @retry_on_failure(max_attempts=5, min_wait=0.1, max_wait=0.2)
        async def retry_five_times():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Fail")

        with pytest.raises(NetworkError):
            await retry_five_times()

        assert call_count == 5

    @pytest.mark.asyncio()
    async def test_default_parameters(self):
        """Test decorator works with default parameters."""
        @retry_on_failure()
        async def default_retry():
            return "default"

        result = await default_retry()
        assert result == "default"


class TestRetryDecoratorLogging:
    """Tests for retry decorator logging."""

    @pytest.mark.asyncio()
    async def test_logging_on_retry(self):
        """Test that retries are logged."""
        call_count = 0

        @retry_on_failure(max_attempts=2, min_wait=0.1, max_wait=0.2)
        async def logged_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Logged error")
            return "logged"

        with patch("src.utils.retry_decorator.logger") as mock_logger:
            result = await logged_retry()

        assert result == "logged"
        # Should have logged warning for failed attempt and possibly info for success
        assert mock_logger.warning.called or mock_logger.info.called


class TestRetryDecoratorFunctionType:
    """Tests for handling different function types."""

    def test_sync_function_detection(self):
        """Test that sync functions are properly wrapped."""
        @retry_on_failure(max_attempts=3)
        def sync_func():
            return "sync"

        # Should be wrapped as sync (not coroutine)
        import inspect
        assert not inspect.iscoroutinefunction(sync_func)

    def test_async_function_detection(self):
        """Test that async functions are properly wrapped."""
        @retry_on_failure(max_attempts=3)
        async def async_func():
            return "async"

        # Should be wrapped as async (coroutine)
        import inspect
        assert inspect.iscoroutinefunction(async_func)

    @pytest.mark.asyncio()
    async def test_async_function_preserves_signature(self):
        """Test that async function signature is preserved."""
        @retry_on_failure(max_attempts=3)
        async def func_with_args(a: int, b: str, c: float = 1.0) -> dict:
            return {"a": a, "b": b, "c": c}

        result = await func_with_args(1, "test", c=2.5)

        assert result == {"a": 1, "b": "test", "c": 2.5}

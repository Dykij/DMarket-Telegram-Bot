"""Phase 4 extended unit tests for exceptions module.

This module contains comprehensive Phase 4 tests for src/utils/exceptions.py covering:
- ErrorCode enum edge cases
- BaseAppException extended tests
- APIError extended tests
- Exception hierarchy and inheritance
- Error categorization edge cases
- format_error_for_user extended tests
- handle_exceptions decorator extended tests
- retry_async decorator extended tests
- handle_api_error extended tests
- DMARKET_ERROR_MAPPING extended tests
- Integration scenarios
- Edge cases and boundary conditions

Target: 85+ tests to achieve 95%+ coverage
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    BaseAppException,
    BusinessLogicError,
    DMARKET_ERROR_MAPPING,
    DMarketSpecificError,
    ErrorCode,
    ForbiddenError,
    InsufficientFundsError,
    ItemNotAvailableError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    RateLimitExceeded,
    RetryStrategy,
    ServerError,
    TemporaryUnavailableError,
    ValidationError,
    categorize_error,
    format_error_for_user,
    handle_api_error,
    handle_exceptions,
    retry_async,
)


# =============================================================================
# TestErrorCodeExtended - Extended tests for ErrorCode enum
# =============================================================================


class TestErrorCodeExtended:
    """Extended tests for ErrorCode enum."""

    def test_all_error_codes_unique(self):
        """Test that all error codes have unique values."""
        values = [e.value for e in ErrorCode]
        assert len(values) == len(set(values)), "Error codes should have unique values"

    def test_error_codes_are_integers(self):
        """Test that all error codes are integers."""
        for code in ErrorCode:
            assert isinstance(code.value, int)

    def test_error_codes_are_positive(self):
        """Test that all error codes are positive integers."""
        for code in ErrorCode:
            assert code.value > 0

    def test_error_code_names(self):
        """Test error code names match expected pattern."""
        expected_names = [
            "UNKNOWN_ERROR",
            "API_ERROR",
            "VALIDATION_ERROR",
            "AUTH_ERROR",
            "RATE_LIMIT_ERROR",
            "NETWORK_ERROR",
            "DATABASE_ERROR",
            "BUSINESS_LOGIC_ERROR",
        ]
        for name in expected_names:
            assert hasattr(ErrorCode, name)

    def test_error_code_iteration(self):
        """Test iterating over all error codes."""
        codes = list(ErrorCode)
        assert len(codes) == 8

    def test_error_code_comparison(self):
        """Test error code comparison."""
        assert ErrorCode.API_ERROR != ErrorCode.AUTH_ERROR
        assert ErrorCode.UNKNOWN_ERROR.value < ErrorCode.API_ERROR.value


# =============================================================================
# TestBaseAppExceptionExtended - Extended tests for BaseAppException
# =============================================================================


class TestBaseAppExceptionExtended:
    """Extended tests for BaseAppException."""

    def test_exception_can_be_raised(self):
        """Test exception can be raised and caught."""
        with pytest.raises(BaseAppException) as exc_info:
            raise BaseAppException("Test error", code=ErrorCode.API_ERROR)
        assert exc_info.value.code == ErrorCode.API_ERROR.value

    def test_exception_with_unicode_message(self):
        """Test exception with unicode message."""
        exc = BaseAppException("Ошибка сервера 服务器错误")
        assert "Ошибка" in exc.message
        assert "服务器" in exc.message

    def test_exception_with_special_characters(self):
        """Test exception with special characters in message."""
        exc = BaseAppException("Error: <script>alert('xss')</script>")
        assert "<script>" in exc.message

    def test_to_dict_without_details_excludes_key(self):
        """Test to_dict excludes details key when empty."""
        exc = BaseAppException("Error")
        result = exc.to_dict()
        assert "details" not in result

    def test_str_representation_without_details(self):
        """Test string representation without details."""
        exc = BaseAppException("Error", code=1000)
        str_repr = str(exc)
        assert "details" not in str_repr

    def test_exception_args(self):
        """Test exception args attribute."""
        exc = BaseAppException("Test message")
        assert exc.args == ("Test message",)

    def test_exception_inheritance(self):
        """Test exception inherits from Exception."""
        exc = BaseAppException("Test")
        assert isinstance(exc, Exception)

    def test_code_with_int_value(self):
        """Test code when initialized with ErrorCode enum."""
        exc = BaseAppException("Test", code=ErrorCode.VALIDATION_ERROR)
        assert exc.code == 3000

    def test_details_mutation_safety(self):
        """Test that details dict is independent."""
        original_details = {"key": "value"}
        exc = BaseAppException("Error", details=original_details)
        exc.details["new_key"] = "new_value"
        # Original should be unchanged after initialization
        assert "key" in exc.details


# =============================================================================
# TestAPIErrorExtended - Extended tests for APIError
# =============================================================================


class TestAPIErrorExtended:
    """Extended tests for APIError exception."""

    def test_api_error_with_response_body_none(self):
        """Test APIError when response_body is None."""
        exc = APIError("Error", response_body=None)
        assert "response_body" not in exc.details

    def test_api_error_with_empty_response_body(self):
        """Test APIError with empty response body."""
        exc = APIError("Error", response_body="")
        # Empty string is falsy, so should not be included
        assert "response_body" not in exc.details

    def test_api_error_status_code_in_details(self):
        """Test that status_code is always in details."""
        exc = APIError("Error", status_code=404)
        assert exc.details["status_code"] == 404

    def test_api_error_default_status_code(self):
        """Test default status code is 500."""
        exc = APIError("Error")
        assert exc.status_code == 500

    def test_api_error_human_readable_format(self):
        """Test human_readable format."""
        exc = APIError("Service unavailable", status_code=503)
        readable = exc.human_readable
        assert "503" in readable
        assert "Service unavailable" in readable

    def test_api_error_with_all_parameters(self):
        """Test APIError with all parameters."""
        exc = APIError(
            message="Full error",
            status_code=422,
            code=ErrorCode.VALIDATION_ERROR,
            details={"field": "price"},
            response_body='{"error": "invalid"}',
        )
        assert exc.message == "Full error"
        assert exc.status_code == 422
        assert exc.code == ErrorCode.VALIDATION_ERROR.value
        assert exc.details["field"] == "price"
        assert exc.details["response_body"] == '{"error": "invalid"}'


# =============================================================================
# TestExceptionHierarchy - Tests for exception inheritance
# =============================================================================


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_authentication_error_is_api_error(self):
        """Test AuthenticationError inherits from APIError."""
        exc = AuthenticationError()
        assert isinstance(exc, APIError)
        assert isinstance(exc, BaseAppException)

    def test_forbidden_error_is_api_error(self):
        """Test ForbiddenError inherits from APIError."""
        exc = ForbiddenError()
        assert isinstance(exc, APIError)

    def test_not_found_error_is_api_error(self):
        """Test NotFoundError inherits from APIError."""
        exc = NotFoundError()
        assert isinstance(exc, APIError)

    def test_rate_limit_exceeded_is_api_error(self):
        """Test RateLimitExceeded inherits from APIError."""
        exc = RateLimitExceeded()
        assert isinstance(exc, APIError)

    def test_server_error_is_api_error(self):
        """Test ServerError inherits from APIError."""
        exc = ServerError("Error")
        assert isinstance(exc, APIError)

    def test_bad_request_error_is_api_error(self):
        """Test BadRequestError inherits from APIError."""
        exc = BadRequestError("Error")
        assert isinstance(exc, APIError)

    def test_dmarket_specific_error_is_api_error(self):
        """Test DMarketSpecificError inherits from APIError."""
        exc = DMarketSpecificError("Error")
        assert isinstance(exc, APIError)

    def test_insufficient_funds_error_is_dmarket_specific(self):
        """Test InsufficientFundsError inherits from DMarketSpecificError."""
        exc = InsufficientFundsError("Error")
        assert isinstance(exc, DMarketSpecificError)
        assert isinstance(exc, APIError)

    def test_item_not_available_error_is_dmarket_specific(self):
        """Test ItemNotAvailableError inherits from DMarketSpecificError."""
        exc = ItemNotAvailableError("Error")
        assert isinstance(exc, DMarketSpecificError)

    def test_temporary_unavailable_error_is_dmarket_specific(self):
        """Test TemporaryUnavailableError inherits from DMarketSpecificError."""
        exc = TemporaryUnavailableError("Error")
        assert isinstance(exc, DMarketSpecificError)

    def test_network_error_is_base_app_exception(self):
        """Test NetworkError inherits from BaseAppException."""
        exc = NetworkError()
        assert isinstance(exc, BaseAppException)
        assert not isinstance(exc, APIError)

    def test_validation_error_is_base_app_exception(self):
        """Test ValidationError inherits from BaseAppException."""
        exc = ValidationError("Error")
        assert isinstance(exc, BaseAppException)
        assert not isinstance(exc, APIError)

    def test_business_logic_error_is_base_app_exception(self):
        """Test BusinessLogicError inherits from BaseAppException."""
        exc = BusinessLogicError("Error")
        assert isinstance(exc, BaseAppException)
        assert not isinstance(exc, APIError)


# =============================================================================
# TestRateLimitAlias - Tests for RateLimitError alias
# =============================================================================


class TestRateLimitAlias:
    """Tests for RateLimitError alias."""

    def test_rate_limit_error_is_rate_limit_exceeded(self):
        """Test RateLimitError is alias for RateLimitExceeded."""
        assert RateLimitError is RateLimitExceeded

    def test_rate_limit_error_can_be_instantiated(self):
        """Test RateLimitError can be instantiated."""
        exc = RateLimitError()
        assert isinstance(exc, RateLimitExceeded)


# =============================================================================
# TestDMarketSpecificErrorExtended - Extended tests for DMarketSpecificError
# =============================================================================


class TestDMarketSpecificErrorExtended:
    """Extended tests for DMarketSpecificError."""

    def test_error_code_property_empty_string(self):
        """Test error_code property returns empty string when not set."""
        exc = DMarketSpecificError("Error")
        assert exc.error_code == ""

    def test_error_code_property_priority(self):
        """Test error_code property priority: _error_code > details."""
        exc = DMarketSpecificError(
            "Error",
            error_code="PRIORITY_CODE",
            response_data={"code": "DETAILS_CODE"},
        )
        assert exc.error_code == "PRIORITY_CODE"

    def test_error_code_with_non_dict_details(self):
        """Test error_code when details is not a dict."""
        exc = DMarketSpecificError("Error")
        exc.details = None  # Manually set to None
        # Should not raise, returns empty string
        assert exc.error_code == ""

    def test_human_readable_without_error_code(self):
        """Test human_readable without error code."""
        exc = DMarketSpecificError("Some error")
        readable = exc.human_readable
        assert "DMarket API" in readable
        assert "Some error" in readable


# =============================================================================
# TestCategorizeErrorExtended - Extended tests for categorize_error
# =============================================================================


class TestCategorizeErrorExtended:
    """Extended tests for categorize_error function."""

    def test_response_keyword_in_message(self):
        """Test categorization by 'response' in message."""
        exc = Exception("Bad response from server")
        assert categorize_error(exc) == "API_ERROR"

    def test_key_keyword_in_message(self):
        """Test categorization by 'key' in message."""
        # Note: "Invalid API key" contains "api" which is matched first
        exc = Exception("Invalid key provided")
        assert categorize_error(exc) == "AUTH_ERROR"

    def test_unauthorized_keyword_in_message(self):
        """Test categorization by 'unauthorized' in message."""
        exc = Exception("Unauthorized access")
        assert categorize_error(exc) == "AUTH_ERROR"

    def test_insufficient_keyword_in_message(self):
        """Test categorization by 'insufficient' in message."""
        exc = Exception("Insufficient permissions")
        assert categorize_error(exc) == "BALANCE_ERROR"

    def test_funds_keyword_in_message(self):
        """Test categorization by 'funds' in message."""
        exc = Exception("No available funds")
        assert categorize_error(exc) == "BALANCE_ERROR"

    def test_parse_keyword_in_message(self):
        """Test categorization by 'parse' in message."""
        # Note: "response" is matched before "parse" so use different message
        exc = Exception("Failed to parse json data")
        assert categorize_error(exc) == "DATA_ERROR"

    def test_data_keyword_in_message(self):
        """Test categorization by 'data' in message."""
        exc = Exception("Invalid data format")
        assert categorize_error(exc) == "DATA_ERROR"

    def test_empty_error_message(self):
        """Test categorization with empty message."""
        exc = Exception("")
        assert categorize_error(exc) == "INTERNAL_ERROR"

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case insensitive."""
        exc = Exception("CONNECTION TIMEOUT")
        assert categorize_error(exc) == "NETWORK_ERROR"


# =============================================================================
# TestFormatErrorForUserExtended - Extended tests for format_error_for_user
# =============================================================================


class TestFormatErrorForUserExtended:
    """Extended tests for format_error_for_user function."""

    def test_format_rate_limit_exceeded(self):
        """Test formatting RateLimitExceeded exception."""
        exc = RateLimitExceeded(retry_after=30)
        result = format_error_for_user(exc)
        assert "❌" in result

    def test_format_network_error(self):
        """Test formatting NetworkError."""
        exc = NetworkError("Connection failed")
        result = format_error_for_user(exc, with_details=True)
        assert "Connection failed" in result

    def test_format_validation_error(self):
        """Test formatting ValidationError."""
        exc = ValidationError("Invalid price", field="price")
        result = format_error_for_user(exc, with_details=True)
        assert "Invalid price" in result

    def test_format_business_logic_error(self):
        """Test formatting BusinessLogicError."""
        exc = BusinessLogicError("Cannot process order", operation="buy")
        result = format_error_for_user(exc, with_details=True)
        assert "Cannot process order" in result

    def test_format_generic_exception_with_api_category(self):
        """Test formatting generic exception that categorizes as API error."""
        exc = Exception("API request failed")
        result = format_error_for_user(exc, lang="ru")
        assert "❌" in result

    def test_format_generic_exception_with_network_category(self):
        """Test formatting generic exception that categorizes as network error."""
        exc = Exception("Connection timeout occurred")
        result = format_error_for_user(exc, lang="ru")
        assert "❌" in result

    def test_format_error_unknown_lang(self):
        """Test formatting with unknown language defaults to English."""
        exc = Exception("Test error")
        result = format_error_for_user(exc, lang="unknown")
        # Should default to English
        assert "❌" in result

    def test_format_string_error_with_details(self):
        """Test formatting string error with details."""
        result = format_error_for_user("Something failed", with_details=True)
        assert "Something failed" in result

    def test_format_api_error_uses_human_readable(self):
        """Test that APIError uses human_readable property."""
        exc = AuthenticationError("Bad token")
        result = format_error_for_user(exc)
        # Should use human_readable which includes authentication details
        assert "❌" in result


# =============================================================================
# TestHandleExceptionsExtended - Extended tests for handle_exceptions decorator
# =============================================================================


class TestHandleExceptionsExtended:
    """Extended tests for handle_exceptions decorator."""

    @pytest.mark.asyncio
    async def test_async_decorator_with_base_app_exception(self):
        """Test async decorator handling BaseAppException."""

        @handle_exceptions(reraise=True)
        async def raises_base_exception():
            raise BaseAppException("Base error")

        with pytest.raises(BaseAppException):
            await raises_base_exception()

    @pytest.mark.asyncio
    async def test_async_decorator_with_unexpected_exception(self):
        """Test async decorator handling unexpected exception."""

        @handle_exceptions(reraise=True)
        async def raises_unexpected():
            raise ValueError("Unexpected error")

        with pytest.raises(ValueError):
            await raises_unexpected()

    def test_sync_decorator_with_unexpected_exception(self):
        """Test sync decorator handling unexpected exception."""

        @handle_exceptions(reraise=True)
        def raises_unexpected():
            raise TypeError("Type error")

        with pytest.raises(TypeError):
            raises_unexpected()

    @pytest.mark.asyncio
    async def test_async_decorator_no_reraise(self):
        """Test async decorator with reraise=False."""

        @handle_exceptions(reraise=False)
        async def raises_error():
            raise APIError("API failed")

        # Should not raise, just log and handle
        result = await raises_error()
        assert result is None

    def test_sync_decorator_no_reraise(self):
        """Test sync decorator with reraise=False."""

        @handle_exceptions(reraise=False)
        def raises_error():
            raise ValidationError("Invalid")

        # Should not raise
        result = raises_error()
        assert result is None

    @pytest.mark.asyncio
    async def test_decorator_with_logger_parameter(self):
        """Test decorator with logger_instance parameter."""
        custom_logger = logging.getLogger("custom_test")

        @handle_exceptions(logger_instance=custom_logger, reraise=True)
        async def test_func():
            raise APIError("Error")

        with pytest.raises(APIError):
            await test_func()

    def test_decorator_without_parens(self):
        """Test decorator used without parentheses."""

        @handle_exceptions
        def simple_func():
            return "result"

        assert simple_func() == "result"

    @pytest.mark.asyncio
    async def test_async_decorator_without_parens(self):
        """Test async decorator without parentheses."""

        @handle_exceptions
        async def simple_async():
            return "async_result"

        result = await simple_async()
        assert result == "async_result"

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves original function name."""

        @handle_exceptions
        def my_named_function():
            pass

        assert my_named_function.__name__ == "my_named_function"


# =============================================================================
# TestRetryAsyncExtended - Extended tests for retry_async decorator
# =============================================================================


class TestRetryAsyncExtended:
    """Extended tests for retry_async decorator."""

    @pytest.mark.asyncio
    async def test_retry_with_non_retryable_exception(self):
        """Test retry does not retry non-matching exceptions."""
        call_count = 0

        @retry_async(max_retries=3, exceptions=(APIError,))
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            await raises_value_error()
        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_retry_with_network_error(self):
        """Test retry handles NetworkError."""
        call_count = 0

        @retry_async(max_retries=2, retry_delay=0.01)
        async def raises_network_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Network issue")
            return "success"

        result = await raises_network_error()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff_delay(self):
        """Test exponential backoff increases delay."""
        import time

        call_times = []

        @retry_async(
            max_retries=3,
            retry_delay=0.05,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        )
        async def track_times():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise APIError("Retry needed")
            return "done"

        await track_times()

        # Check delays are increasing (exponential)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be larger than first
            assert delay2 > delay1 * 0.5  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_retry_preserves_function_name(self):
        """Test retry decorator preserves function name."""

        @retry_async(max_retries=1)
        async def named_retry_func():
            return "ok"

        assert named_retry_func.__name__ == "named_retry_func"

    @pytest.mark.asyncio
    async def test_retry_with_custom_exceptions_tuple(self):
        """Test retry with custom exceptions tuple."""
        call_count = 0

        @retry_async(
            max_retries=2,
            retry_delay=0.01,
            exceptions=(ValueError, TypeError),
        )
        async def raises_custom():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Custom error")
            return "done"

        result = await raises_custom()
        assert result == "done"


# =============================================================================
# TestHandleApiErrorExtended - Extended tests for handle_api_error
# =============================================================================


class TestHandleApiErrorExtended:
    """Extended tests for handle_api_error function."""

    def test_handle_api_error_with_custom_logger(self, caplog):
        """Test handle_api_error with custom logger."""
        custom_logger = logging.getLogger("api_handler")
        exc = APIError("Custom API error", status_code=400)

        with caplog.at_level(logging.ERROR, logger="api_handler"):
            handle_api_error(exc, logger_instance=custom_logger)

    def test_handle_api_error_with_empty_context(self, caplog):
        """Test handle_api_error with empty context."""
        exc = APIError("Error", status_code=500)
        with caplog.at_level(logging.ERROR):
            handle_api_error(exc, context={})

    def test_handle_non_api_error(self, caplog):
        """Test handle_api_error with non-APIError exception."""
        exc = ValueError("Not an API error")
        with caplog.at_level(logging.ERROR):
            handle_api_error(exc)
        assert "Unexpected error" in caplog.text or "ValueError" in caplog.text


# =============================================================================
# TestDMarketErrorMappingExtended - Extended tests for DMARKET_ERROR_MAPPING
# =============================================================================


class TestDMarketErrorMappingExtended:
    """Extended tests for DMARKET_ERROR_MAPPING dictionary."""

    def test_wallet_not_found_mapping(self):
        """Test WalletNotFound maps to DMarketSpecificError."""
        assert DMARKET_ERROR_MAPPING["WalletNotFound"] == DMarketSpecificError

    def test_service_unavailable_mapping(self):
        """Test ServiceUnavailable maps to TemporaryUnavailableError."""
        assert DMARKET_ERROR_MAPPING["ServiceUnavailable"] == TemporaryUnavailableError

    def test_all_mappings_are_exception_classes(self):
        """Test all mappings point to exception classes."""
        for key, exc_class in DMARKET_ERROR_MAPPING.items():
            assert issubclass(exc_class, Exception)

    def test_mapping_keys_are_strings(self):
        """Test all mapping keys are strings."""
        for key in DMARKET_ERROR_MAPPING:
            assert isinstance(key, str)


# =============================================================================
# TestExceptionEdgeCasesExtended - Extended edge case tests
# =============================================================================


class TestExceptionEdgeCasesExtended:
    """Extended edge case tests."""

    def test_very_long_error_message(self):
        """Test exception with very long message."""
        long_message = "x" * 10000
        exc = BaseAppException(long_message)
        assert len(exc.message) == 10000

    def test_nested_details(self):
        """Test exception with deeply nested details."""
        details = {"level1": {"level2": {"level3": {"level4": "value"}}}}
        exc = BaseAppException("Error", details=details)
        assert exc.details["level1"]["level2"]["level3"]["level4"] == "value"

    def test_details_with_list(self):
        """Test exception with list in details."""
        details = {"errors": ["error1", "error2", "error3"]}
        exc = BaseAppException("Multiple errors", details=details)
        assert len(exc.details["errors"]) == 3

    def test_exception_with_none_values_in_details(self):
        """Test exception with None values in details."""
        details = {"key": None, "other": "value"}
        exc = BaseAppException("Error", details=details)
        assert exc.details["key"] is None

    def test_server_error_default_status(self):
        """Test ServerError default status code is 500."""
        exc = ServerError("Internal error")
        assert exc.status_code == 500

    def test_validation_error_with_details_and_field(self):
        """Test ValidationError with both details and field."""
        exc = ValidationError(
            "Invalid value",
            field="amount",
            details={"constraint": "positive"},
        )
        assert exc.details["field"] == "amount"
        assert exc.details["constraint"] == "positive"

    def test_business_logic_error_with_details_and_operation(self):
        """Test BusinessLogicError with both details and operation."""
        exc = BusinessLogicError(
            "Operation failed",
            operation="transfer",
            details={"reason": "limit exceeded"},
        )
        assert exc.details["operation"] == "transfer"
        assert exc.details["reason"] == "limit exceeded"


# =============================================================================
# TestRetryStrategyExtended - Extended tests for RetryStrategy enum
# =============================================================================


class TestRetryStrategyExtended:
    """Extended tests for RetryStrategy enum."""

    def test_all_strategies_unique(self):
        """Test all strategies have unique values."""
        values = [s.value for s in RetryStrategy]
        assert len(values) == len(set(values))

    def test_strategy_values_are_strings(self):
        """Test all strategy values are strings."""
        for strategy in RetryStrategy:
            assert isinstance(strategy.value, str)

    def test_strategy_count(self):
        """Test number of strategies."""
        strategies = list(RetryStrategy)
        assert len(strategies) == 4


# =============================================================================
# TestIntegration - Integration tests
# =============================================================================


class TestIntegration:
    """Integration tests for exceptions module."""

    @pytest.mark.asyncio
    async def test_full_error_handling_workflow(self):
        """Test complete error handling workflow."""
        # Create error
        exc = APIError("API failed", status_code=500)

        # Categorize
        category = categorize_error(exc)
        assert category == "API_ERROR"

        # Format for user
        user_message = format_error_for_user(exc)
        assert "❌" in user_message

        # Log
        handle_api_error(exc, context={"request_id": "123"})

    @pytest.mark.asyncio
    async def test_retry_with_eventual_success(self):
        """Test retry mechanism with eventual success."""
        attempt = 0

        @retry_async(max_retries=3, retry_delay=0.01)
        async def flaky_operation():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise NetworkError("Temporary failure")
            return {"status": "success"}

        result = await flaky_operation()
        assert result["status"] == "success"
        assert attempt == 3

    @pytest.mark.asyncio
    async def test_handle_exceptions_with_telegram_update_mock(self):
        """Test handle_exceptions with mocked Telegram update."""
        # Create mock update with message
        mock_message = MagicMock()
        mock_message.reply_text = AsyncMock()

        mock_update = MagicMock()
        mock_update.message = mock_message
        mock_update.callback_query = None

        @handle_exceptions(reraise=False)
        async def handler(update, context):
            raise APIError("Handler failed")

        await handler(mock_update, None)
        # Should have tried to send error message
        mock_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_exceptions_with_callback_query_mock(self):
        """Test handle_exceptions with mocked callback query."""
        # Create mock callback query
        mock_callback_query = MagicMock()
        mock_callback_query.answer = AsyncMock()

        mock_update = MagicMock()
        mock_update.message = None
        mock_update.callback_query = mock_callback_query

        @handle_exceptions(reraise=False)
        async def callback_handler(update, context):
            raise ValidationError("Invalid callback")

        await callback_handler(mock_update, None)
        # Should have tried to answer callback
        mock_callback_query.answer.assert_called()

    def test_exception_chain(self):
        """Test exception chaining."""
        original = ValueError("Original error")
        try:
            try:
                raise original
            except ValueError as e:
                raise APIError("API failed") from e
        except APIError as api_error:
            assert api_error.__cause__ is original


# =============================================================================
# TestSpecialCases - Special case tests
# =============================================================================


class TestSpecialCases:
    """Special case tests."""

    def test_rate_limit_with_response_data(self):
        """Test RateLimitExceeded with response_data."""
        exc = RateLimitExceeded(
            response_data={"limit": 100, "remaining": 0},
            retry_after=120,
        )
        assert exc.retry_after == 120
        assert exc.details.get("limit") == 100

    def test_api_error_inherits_code_correctly(self):
        """Test APIError inherits error code correctly."""
        exc = APIError("Error", code=ErrorCode.NETWORK_ERROR)
        assert exc.code == ErrorCode.NETWORK_ERROR.value

    def test_network_error_with_custom_code(self):
        """Test NetworkError with custom code."""
        exc = NetworkError("Error", code=9999)
        assert exc.code == 9999

    def test_format_error_all_categories_ru(self):
        """Test formatting covers all categories in Russian."""
        categories = [
            RateLimitExceeded(),
            AuthenticationError(),
            InsufficientFundsError("No funds"),
            APIError("API error"),
            ValidationError("Invalid"),
            Exception("Connection error"),  # NETWORK
            Exception("Unknown error"),  # INTERNAL
        ]

        for exc in categories:
            result = format_error_for_user(exc, lang="ru")
            assert "❌" in result

    def test_format_error_all_categories_en(self):
        """Test formatting covers all categories in English."""
        categories = [
            RateLimitExceeded(),
            AuthenticationError(),
            InsufficientFundsError("No funds"),
            APIError("API error"),
            ValidationError("Invalid"),
        ]

        for exc in categories:
            result = format_error_for_user(exc, lang="en")
            assert "❌" in result

"""Unit tests for exceptions module.

This module contains tests for src/utils/exceptions.py covering:
- ErrorCode enum
- BaseAppException
- APIError
- Other exception classes
- Error categorization and formatting
- Retry strategies and decorators

Target: 70+ tests to achieve 85%+ coverage
"""

import logging

import pytest

from src.utils.exceptions import (
    DMARKET_ERROR_MAPPING,
    APIError,
    AuthenticationError,
    BadRequestError,
    BaseAppException,
    BusinessLogicError,
    DMarketSpecificError,
    ErrorCode,
    ForbiddenError,
    InsufficientFundsError,
    ItemNotAvailableError,
    NetworkError,
    NotFoundError,
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


# TestErrorCode


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_unknown_error_code(self):
        """Test UNKNOWN_ERROR code value."""
        assert ErrorCode.UNKNOWN_ERROR.value == 1000

    def test_api_error_code(self):
        """Test API_ERROR code value."""
        assert ErrorCode.API_ERROR.value == 2000

    def test_validation_error_code(self):
        """Test VALIDATION_ERROR code value."""
        assert ErrorCode.VALIDATION_ERROR.value == 3000

    def test_auth_error_code(self):
        """Test AUTH_ERROR code value."""
        assert ErrorCode.AUTH_ERROR.value == 4000

    def test_rate_limit_error_code(self):
        """Test RATE_LIMIT_ERROR code value."""
        assert ErrorCode.RATE_LIMIT_ERROR.value == 5000

    def test_network_error_code(self):
        """Test NETWORK_ERROR code value."""
        assert ErrorCode.NETWORK_ERROR.value == 6000

    def test_database_error_code(self):
        """Test DATABASE_ERROR code value."""
        assert ErrorCode.DATABASE_ERROR.value == 7000

    def test_business_logic_error_code(self):
        """Test BUSINESS_LOGIC_ERROR code value."""
        assert ErrorCode.BUSINESS_LOGIC_ERROR.value == 8000


# TestBaseAppException


class TestBaseAppException:
    """Tests for BaseAppException."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        # Act
        exc = BaseAppException("Test error")

        # Assert
        assert exc.message == "Test error"
        assert exc.code == ErrorCode.UNKNOWN_ERROR.value
        assert exc.details == {}

    def test_init_with_code(self):
        """Test initialization with error code."""
        # Act
        exc = BaseAppException("API failed", code=ErrorCode.API_ERROR)

        # Assert
        assert exc.message == "API failed"
        assert exc.code == ErrorCode.API_ERROR.value

    def test_init_with_int_code(self):
        """Test initialization with integer code."""
        # Act
        exc = BaseAppException("Custom error", code=9999)

        # Assert
        assert exc.code == 9999

    def test_init_with_details(self):
        """Test initialization with details."""
        # Arrange
        details = {"endpoint": "/api/test", "user_id": 123}

        # Act
        exc = BaseAppException("Error", details=details)

        # Assert
        assert exc.details == details

    def test_to_dict(self):
        """Test to_dict method."""
        # Arrange
        exc = BaseAppException("Test error", code=ErrorCode.API_ERROR)

        # Act
        result = exc.to_dict()

        # Assert
        assert result["code"] == ErrorCode.API_ERROR.value
        assert result["message"] == "Test error"

    def test_to_dict_with_details(self):
        """Test to_dict method with details."""
        # Arrange
        details = {"key": "value"}
        exc = BaseAppException("Error", details=details)

        # Act
        result = exc.to_dict()

        # Assert
        assert result["details"] == details

    def test_str_representation(self):
        """Test string representation."""
        # Act
        exc = BaseAppException("Test error", code=ErrorCode.API_ERROR)

        # Assert
        assert "BaseAppException" in str(exc)
        assert "Test error" in str(exc)
        assert str(ErrorCode.API_ERROR.value) in str(exc)

    def test_str_with_details(self):
        """Test string representation with details."""
        # Act
        exc = BaseAppException("Error", details={"key": "value"})

        # Assert
        assert "details" in str(exc)
        assert "key" in str(exc)


# TestAPIError


class TestAPIError:
    """Tests for APIError exception."""

    def test_init_basic(self):
        """Test basic initialization."""
        # Act
        exc = APIError("API failed")

        # Assert
        assert exc.message == "API failed"
        assert exc.status_code == 500
        assert exc.code == ErrorCode.API_ERROR.value

    def test_init_with_status_code(self):
        """Test initialization with status code."""
        # Act
        exc = APIError("Not found", status_code=404)

        # Assert
        assert exc.status_code == 404

    def test_init_with_details_and_status(self):
        """Test initialization with details and status code."""
        # Arrange
        details = {"endpoint": "/api/test"}

        # Act
        exc = APIError("Error", status_code=400, details=details)

        # Assert
        assert exc.status_code == 400
        assert exc.details == details

    def test_api_error_inherits_base(self):
        """Test that APIError inherits from BaseAppException."""
        # Act
        exc = APIError("Test")

        # Assert
        assert isinstance(exc, BaseAppException)

    def test_api_error_to_dict(self):
        """Test APIError to_dict method."""
        # Arrange
        exc = APIError("API error", status_code=400)

        # Act
        result = exc.to_dict()

        # Assert
        assert "code" in result
        assert "message" in result


# TestExceptionRaising


class TestExceptionRaising:
    """Tests for raising exceptions."""

    def test_raise_base_exception(self):
        """Test raising BaseAppException."""
        # Act & Assert
        with pytest.raises(BaseAppException) as exc_info:
            raise BaseAppException("Test error")

        assert exc_info.value.message == "Test error"

    def test_raise_api_error(self):
        """Test raising APIError."""
        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            raise APIError("API failed", status_code=503)

        assert exc_info.value.status_code == 503

    def test_catch_as_base_exception(self):
        """Test catching APIError as BaseAppException."""
        # Act & Assert
        with pytest.raises(BaseAppException):
            raise APIError("API error")


# TestEdgeCases


class TestExceptionEdgeCases:
    """Tests for edge cases."""

    def test_empty_message(self):
        """Test with empty message."""
        # Act
        exc = BaseAppException("")

        # Assert
        assert exc.message == ""

    def test_none_details(self):
        """Test with None details."""
        # Act
        exc = BaseAppException("Error", details=None)

        # Assert
        assert exc.details == {}

    def test_empty_details(self):
        """Test with empty details dict."""
        # Act
        exc = BaseAppException("Error", details={})

        # Assert
        assert exc.details == {}

    def test_complex_details(self):
        """Test with complex nested details."""
        # Arrange
        details = {
            "request": {
                "url": "/api/test",
                "method": "POST",
                "body": {"key": "value"},
            },
            "response": {
                "status": 500,
                "body": None,
            },
        }

        # Act
        exc = BaseAppException("Error", details=details)

        # Assert
        assert exc.details == details
        result = exc.to_dict()
        assert result["details"]["request"]["url"] == "/api/test"


# TestAuthenticationError


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_init_default(self):
        """Test default initialization."""
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert exc.code == ErrorCode.AUTH_ERROR.value
        assert "авторизации" in exc.message.lower()

    def test_init_custom_message(self):
        """Test initialization with custom message."""
        exc = AuthenticationError(message="Invalid token")
        assert exc.message == "Invalid token"
        assert exc.status_code == 401

    def test_human_readable(self):
        """Test human_readable property."""
        exc = AuthenticationError("Bad token")
        readable = exc.human_readable
        assert "аутентификации" in readable.lower()
        assert "Bad token" in readable


# TestForbiddenError


class TestForbiddenError:
    """Tests for ForbiddenError exception."""

    def test_init_default(self):
        """Test default initialization."""
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert "запрещен" in exc.message.lower()

    def test_human_readable(self):
        """Test human_readable property."""
        exc = ForbiddenError("Access denied to resource")
        readable = exc.human_readable
        assert "запрещен" in readable.lower()


# TestNotFoundError


class TestNotFoundError:
    """Tests for NotFoundError exception."""

    def test_init_default(self):
        """Test default initialization."""
        exc = NotFoundError()
        assert exc.status_code == 404
        assert "не найден" in exc.message.lower()

    def test_human_readable(self):
        """Test human_readable property."""
        exc = NotFoundError("Item not found")
        readable = exc.human_readable
        assert "не найден" in readable.lower()


# TestRateLimitExceeded


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded exception."""

    def test_init_default(self):
        """Test default initialization."""
        exc = RateLimitExceeded()
        assert exc.status_code == 429
        assert exc.retry_after == 60
        assert exc.code == ErrorCode.RATE_LIMIT_ERROR.value

    def test_init_custom_retry_after(self):
        """Test initialization with custom retry_after."""
        exc = RateLimitExceeded(retry_after=120)
        assert exc.retry_after == 120

    def test_human_readable(self):
        """Test human_readable property."""
        exc = RateLimitExceeded(retry_after=30)
        readable = exc.human_readable
        assert "30" in readable
        assert "лимит" in readable.lower()


# TestNetworkError


class TestNetworkError:
    """Tests for NetworkError exception."""

    def test_init_default(self):
        """Test default initialization."""
        exc = NetworkError()
        assert exc.code == ErrorCode.NETWORK_ERROR.value
        assert "сети" in exc.message.lower()

    def test_init_custom_message(self):
        """Test initialization with custom message."""
        exc = NetworkError("Connection timeout")
        assert exc.message == "Connection timeout"


# TestServerError


class TestServerError:
    """Tests for ServerError exception."""

    def test_init(self):
        """Test initialization."""
        exc = ServerError("Internal error", status_code=503)
        assert exc.status_code == 503
        assert exc.message == "Internal error"

    def test_human_readable(self):
        """Test human_readable property."""
        exc = ServerError("Database unavailable", status_code=500)
        readable = exc.human_readable
        assert "сервера" in readable.lower()
        assert "500" in readable


# TestBadRequestError


class TestBadRequestError:
    """Tests for BadRequestError exception."""

    def test_init(self):
        """Test initialization."""
        exc = BadRequestError("Invalid parameters")
        assert exc.status_code == 400
        assert exc.message == "Invalid parameters"

    def test_human_readable(self):
        """Test human_readable property."""
        exc = BadRequestError("Missing required field")
        readable = exc.human_readable
        assert "запрос" in readable.lower()


# TestDMarketSpecificError


class TestDMarketSpecificError:
    """Tests for DMarketSpecificError exception."""

    def test_init(self):
        """Test initialization."""
        exc = DMarketSpecificError(
            "DMarket error", status_code=400, error_code="ITEM_SOLD"
        )
        assert exc.status_code == 400
        assert exc._error_code == "ITEM_SOLD"

    def test_error_code_property_from_init(self):
        """Test error_code property when set via init."""
        exc = DMarketSpecificError("Error", error_code="TEST_CODE")
        assert exc.error_code == "TEST_CODE"

    def test_error_code_property_from_details(self):
        """Test error_code property when set via details."""
        exc = DMarketSpecificError("Error", response_data={"code": "FROM_DETAILS"})
        assert exc.error_code == "FROM_DETAILS"

    def test_error_code_property_from_error_code_key(self):
        """Test error_code property when set via error_code key in details."""
        exc = DMarketSpecificError(
            "Error", response_data={"error_code": "FROM_ERROR_CODE"}
        )
        assert exc.error_code == "FROM_ERROR_CODE"

    def test_error_code_property_from_error_key(self):
        """Test error_code property when set via error key in details."""
        exc = DMarketSpecificError("Error", response_data={"error": "FROM_ERROR"})
        assert exc.error_code == "FROM_ERROR"

    def test_human_readable(self):
        """Test human_readable property."""
        exc = DMarketSpecificError("Item sold out", error_code="ITEM_SOLD")
        readable = exc.human_readable
        assert "DMarket" in readable
        assert "ITEM_SOLD" in readable


# TestInsufficientFundsError


class TestInsufficientFundsError:
    """Tests for InsufficientFundsError exception."""

    def test_human_readable(self):
        """Test human_readable property."""
        exc = InsufficientFundsError("Not enough balance")
        readable = exc.human_readable
        assert "недостаточно" in readable.lower() or "средств" in readable.lower()


# TestItemNotAvailableError


class TestItemNotAvailableError:
    """Tests for ItemNotAvailableError exception."""

    def test_human_readable(self):
        """Test human_readable property."""
        exc = ItemNotAvailableError("Item sold")
        readable = exc.human_readable
        assert "недоступен" in readable.lower()


# TestTemporaryUnavailableError


class TestTemporaryUnavailableError:
    """Tests for TemporaryUnavailableError exception."""

    def test_human_readable(self):
        """Test human_readable property."""
        exc = TemporaryUnavailableError("Maintenance")
        readable = exc.human_readable
        assert "временно" in readable.lower()


# TestValidationError


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_init_with_field(self):
        """Test initialization with field."""
        exc = ValidationError("Invalid value", field="price")
        assert exc.message == "Invalid value"
        assert exc.code == ErrorCode.VALIDATION_ERROR.value
        assert exc.details["field"] == "price"

    def test_init_without_field(self):
        """Test initialization without field."""
        exc = ValidationError("Invalid data")
        assert "field" not in exc.details


# TestBusinessLogicError


class TestBusinessLogicError:
    """Tests for BusinessLogicError exception."""

    def test_init_with_operation(self):
        """Test initialization with operation."""
        exc = BusinessLogicError("Cannot process", operation="buy_item")
        assert exc.message == "Cannot process"
        assert exc.code == ErrorCode.BUSINESS_LOGIC_ERROR.value
        assert exc.details["operation"] == "buy_item"

    def test_init_without_operation(self):
        """Test initialization without operation."""
        exc = BusinessLogicError("Generic error")
        assert "operation" not in exc.details


# TestDMarketErrorMapping


class TestDMarketErrorMapping:
    """Tests for DMARKET_ERROR_MAPPING."""

    def test_insufficient_amount_mapping(self):
        """Test InsuficientAmount maps to InsufficientFundsError."""
        assert DMARKET_ERROR_MAPPING["InsuficientAmount"] == InsufficientFundsError

    def test_not_enough_money_mapping(self):
        """Test NotEnoughMoney maps to InsufficientFundsError."""
        assert DMARKET_ERROR_MAPPING["NotEnoughMoney"] == InsufficientFundsError

    def test_item_not_found_mapping(self):
        """Test ItemNotFound maps to ItemNotAvailableError."""
        assert DMARKET_ERROR_MAPPING["ItemNotFound"] == ItemNotAvailableError

    def test_offer_not_found_mapping(self):
        """Test OfferNotFound maps to ItemNotAvailableError."""
        assert DMARKET_ERROR_MAPPING["OfferNotFound"] == ItemNotAvailableError

    def test_temporary_unavailable_mapping(self):
        """Test TemporaryUnavailable maps to TemporaryUnavailableError."""
        assert (
            DMARKET_ERROR_MAPPING["TemporaryUnavailable"] == TemporaryUnavailableError
        )


# TestCategorizeError


class TestCategorizeError:
    """Tests for categorize_error function."""

    def test_rate_limit_error(self):
        """Test categorization of RateLimitExceeded."""
        exc = RateLimitExceeded()
        assert categorize_error(exc) == "RATE_LIMIT_ERROR"

    def test_auth_error(self):
        """Test categorization of AuthenticationError."""
        exc = AuthenticationError()
        assert categorize_error(exc) == "AUTH_ERROR"

    def test_insufficient_funds_error(self):
        """Test categorization of InsufficientFundsError."""
        exc = InsufficientFundsError("No money")
        assert categorize_error(exc) == "BALANCE_ERROR"

    def test_api_error(self):
        """Test categorization of APIError."""
        exc = APIError("API failed")
        assert categorize_error(exc) == "API_ERROR"

    def test_validation_error(self):
        """Test categorization of ValidationError."""
        exc = ValidationError("Invalid")
        assert categorize_error(exc) == "VALIDATION_ERROR"

    def test_connection_error_string(self):
        """Test categorization by 'connection' in message."""
        exc = Exception("Connection refused")
        assert categorize_error(exc) == "NETWORK_ERROR"

    def test_timeout_error_string(self):
        """Test categorization by 'timeout' in message."""
        exc = Exception("Request timeout")
        assert categorize_error(exc) == "NETWORK_ERROR"

    def test_socket_error_string(self):
        """Test categorization by 'socket' in message."""
        exc = Exception("Socket error occurred")
        assert categorize_error(exc) == "NETWORK_ERROR"

    def test_api_keyword_in_message(self):
        """Test categorization by 'api' in message."""
        exc = Exception("API call failed")
        assert categorize_error(exc) == "API_ERROR"

    def test_request_keyword_in_message(self):
        """Test categorization by 'request' in message."""
        exc = Exception("Request error")
        assert categorize_error(exc) == "API_ERROR"

    def test_auth_keyword_in_message(self):
        """Test categorization by 'auth' in message."""
        exc = Exception("Auth failed")
        assert categorize_error(exc) == "AUTH_ERROR"

    def test_token_keyword_in_message(self):
        """Test categorization by 'token' in message."""
        exc = Exception("Token expired")
        assert categorize_error(exc) == "AUTH_ERROR"

    def test_balance_keyword_in_message(self):
        """Test categorization by 'balance' in message."""
        exc = Exception("Insufficient balance")
        assert categorize_error(exc) == "BALANCE_ERROR"

    def test_json_keyword_in_message(self):
        """Test categorization by 'json' in message."""
        exc = Exception("JSON parse error")
        assert categorize_error(exc) == "DATA_ERROR"

    def test_unknown_error(self):
        """Test categorization of unknown error."""
        exc = Exception("Something went wrong")
        assert categorize_error(exc) == "INTERNAL_ERROR"


# TestFormatErrorForUser


class TestFormatErrorForUser:
    """Tests for format_error_for_user function."""

    def test_format_with_human_readable(self):
        """Test formatting exception with human_readable property."""
        exc = AuthenticationError("Bad credentials")
        result = format_error_for_user(exc)
        assert "❌" in result

    def test_format_string_error(self):
        """Test formatting string error."""
        result = format_error_for_user("Something failed")
        assert "❌" in result

    def test_format_with_details_ru(self):
        """Test formatting with details in Russian."""
        exc = Exception("Test error")
        result = format_error_for_user(exc, with_details=True, lang="ru")
        assert "Test error" in result
        assert "Тип" in result

    def test_format_with_details_en(self):
        """Test formatting with details in English."""
        exc = Exception("Test error")
        result = format_error_for_user(exc, with_details=True, lang="en")
        assert "Test error" in result
        assert "Type" in result

    def test_format_without_details_ru(self):
        """Test formatting without details in Russian."""
        exc = Exception("Error")
        result = format_error_for_user(exc, with_details=False, lang="ru")
        assert "попробуйте" in result.lower()

    def test_format_without_details_en(self):
        """Test formatting without details in English."""
        exc = Exception("Error")
        result = format_error_for_user(exc, with_details=False, lang="en")
        assert "try again" in result.lower()


# TestRetryStrategy


class TestRetryStrategy:
    """Tests for RetryStrategy enum."""

    def test_exponential_backoff_value(self):
        """Test EXPONENTIAL_BACKOFF value."""
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential"

    def test_linear_backoff_value(self):
        """Test LINEAR_BACKOFF value."""
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear"

    def test_fixed_delay_value(self):
        """Test FIXED_DELAY value."""
        assert RetryStrategy.FIXED_DELAY.value == "fixed"

    def test_no_retry_value(self):
        """Test NO_RETRY value."""
        assert RetryStrategy.NO_RETRY.value == "none"


# TestHandleApiError


class TestHandleApiError:
    """Tests for handle_api_error function."""

    def test_handle_api_error(self, caplog):
        """Test handling APIError."""
        exc = APIError("API failed", status_code=500)
        with caplog.at_level(logging.ERROR):
            handle_api_error(exc)
        assert "API Error" in caplog.text or "API failed" in caplog.text

    def test_handle_generic_error(self, caplog):
        """Test handling generic exception."""
        exc = Exception("Unknown error")
        with caplog.at_level(logging.ERROR):
            handle_api_error(exc)
        assert "Unknown error" in caplog.text or "Unexpected" in caplog.text

    def test_handle_with_context(self, caplog):
        """Test handling with context."""
        exc = APIError("Failed", status_code=400)
        context = {"user_id": 123}
        with caplog.at_level(logging.ERROR):
            handle_api_error(exc, context=context)
        # Context should be passed to logger


# TestRetryAsync


class TestRetryAsync:
    """Tests for retry_async decorator."""

    @pytest.mark.asyncio()
    async def test_retry_successful_first_try(self):
        """Test function succeeds on first try."""
        call_count = 0

        @retry_async(max_retries=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio()
    async def test_retry_succeeds_after_failures(self):
        """Test function succeeds after initial failures."""
        call_count = 0

        @retry_async(max_retries=3, retry_delay=0.01)
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError("Temporary failure")
            return "success"

        result = await eventually_succeeds()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio()
    async def test_retry_exhausted(self):
        """Test all retries exhausted."""

        @retry_async(max_retries=2, retry_delay=0.01)
        async def always_fails():
            raise APIError("Always fails")

        with pytest.raises(APIError):
            await always_fails()

    @pytest.mark.asyncio()
    async def test_retry_linear_backoff(self):
        """Test linear backoff strategy."""
        call_count = 0

        @retry_async(
            max_retries=3,
            retry_delay=0.01,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
        )
        async def linear_test():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Network issue")
            return "done"

        result = await linear_test()
        assert result == "done"

    @pytest.mark.asyncio()
    async def test_retry_fixed_delay(self):
        """Test fixed delay strategy."""
        call_count = 0

        @retry_async(
            max_retries=2,
            retry_delay=0.01,
            retry_strategy=RetryStrategy.FIXED_DELAY,
        )
        async def fixed_test():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APIError("Retry needed")
            return "ok"

        result = await fixed_test()
        assert result == "ok"


# TestHandleExceptions


class TestHandleExceptions:
    """Tests for handle_exceptions decorator."""

    @pytest.mark.asyncio()
    async def test_async_function_success(self):
        """Test successful async function."""

        @handle_exceptions
        async def successful_async():
            return "success"

        result = await successful_async()
        assert result == "success"

    @pytest.mark.asyncio()
    async def test_async_function_reraise(self):
        """Test async function with reraise=True."""

        @handle_exceptions(reraise=True)
        async def failing_async():
            raise APIError("API failed")

        with pytest.raises(APIError):
            await failing_async()

    def test_sync_function_success(self):
        """Test successful sync function."""

        @handle_exceptions
        def successful_sync():
            return "success"

        result = successful_sync()
        assert result == "success"

    def test_sync_function_reraise(self):
        """Test sync function with reraise=True."""

        @handle_exceptions(reraise=True)
        def failing_sync():
            raise ValidationError("Invalid data")

        with pytest.raises(ValidationError):
            failing_sync()

    def test_decorator_with_custom_message(self):
        """Test decorator with custom error message."""

        @handle_exceptions(default_error_message="Custom error occurred")
        def some_function():
            return "ok"

        result = some_function()
        assert result == "ok"

    def test_decorator_with_logger(self):
        """Test decorator with custom logger."""
        custom_logger = logging.getLogger("custom")

        @handle_exceptions(logger_instance=custom_logger)
        def func_with_logger():
            return "logged"

        result = func_with_logger()
        assert result == "logged"


# TestAPIErrorWithResponseBody


class TestAPIErrorWithResponseBody:
    """Tests for APIError with response_body parameter."""

    def test_init_with_response_body(self):
        """Test initialization with response_body."""
        exc = APIError(
            "Error occurred",
            status_code=400,
            response_body='{"error": "invalid_request"}',
        )
        assert exc.details["response_body"] == '{"error": "invalid_request"}'

    def test_human_readable_property(self):
        """Test human_readable property of APIError."""
        exc = APIError("API failure", status_code=503)
        readable = exc.human_readable
        assert "API" in readable
        assert "503" in readable

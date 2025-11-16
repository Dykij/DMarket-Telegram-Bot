"""Tests for exceptions module."""

import pytest
from src.utils.exceptions import (
    ErrorCode,
    BaseAppException,
    APIError,
    ValidationError,
    AuthenticationError,
    RateLimitExceeded,
    NetworkError,
    BusinessLogicError,
    DMarketSpecificError,
    InsufficientFundsError,
    ItemNotAvailableError,
    categorize_error,
    format_error_for_user,
)


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_error_codes_exist(self):
        """Test that all error codes are defined."""
        assert ErrorCode.UNKNOWN_ERROR.value == 1000
        assert ErrorCode.API_ERROR.value == 2000
        assert ErrorCode.VALIDATION_ERROR.value == 3000
        assert ErrorCode.AUTH_ERROR.value == 4000
        assert ErrorCode.RATE_LIMIT_ERROR.value == 5000
        assert ErrorCode.NETWORK_ERROR.value == 6000
        assert ErrorCode.DATABASE_ERROR.value == 7000
        assert ErrorCode.BUSINESS_LOGIC_ERROR.value == 8000


class TestBaseAppException:
    """Test BaseAppException class."""

    def test_basic_exception(self):
        """Test creating a basic exception."""
        exc = BaseAppException("Test error")
        
        assert exc.message == "Test error"
        assert exc.code == ErrorCode.UNKNOWN_ERROR.value
        assert exc.details == {}

    def test_exception_with_code(self):
        """Test exception with specific error code."""
        exc = BaseAppException("Test error", code=ErrorCode.API_ERROR)
        
        assert exc.code == ErrorCode.API_ERROR.value

    def test_exception_with_int_code(self):
        """Test exception with integer code."""
        exc = BaseAppException("Test error", code=9999)
        
        assert exc.code == 9999

    def test_exception_with_details(self):
        """Test exception with details."""
        details = {"key": "value", "count": 42}
        exc = BaseAppException("Test error", details=details)
        
        assert exc.details == details

    def test_to_dict(self):
        """Test converting exception to dict."""
        exc = BaseAppException("Test error", code=ErrorCode.API_ERROR)
        
        result = exc.to_dict()
        
        assert result["code"] == ErrorCode.API_ERROR.value
        assert result["message"] == "Test error"

    def test_to_dict_with_details(self):
        """Test converting exception with details to dict."""
        details = {"user_id": 123, "action": "login"}
        exc = BaseAppException("Auth failed", details=details)
        
        result = exc.to_dict()
        
        assert result["details"] == details

    def test_str_representation(self):
        """Test string representation."""
        exc = BaseAppException("Test error", code=ErrorCode.API_ERROR)
        
        str_repr = str(exc)
        
        assert "BaseAppException" in str_repr
        assert "2000" in str_repr
        assert "Test error" in str_repr


class TestAPIError:
    """Test APIError class."""

    def test_api_error_creation(self):
        """Test creating API error."""
        err = APIError("API failed", status_code=404)
        
        assert err.message == "API failed"
        assert err.status_code == 404
        assert err.code == ErrorCode.API_ERROR.value

    def test_api_error_with_response_body(self):
        """Test API error with response body."""
        err = APIError("API failed", response_body='{"error": "not found"}')
        
        assert err.response_body == '{"error": "not found"}'

    def test_api_error_to_dict(self):
        """Test API error to_dict."""
        err = APIError("API failed", status_code=500)
        
        result = err.to_dict()
        
        assert result["code"] == ErrorCode.API_ERROR.value
        assert result["message"] == "API failed"
        assert result["status_code"] == 500


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        err = ValidationError("Invalid input")
        
        assert err.message == "Invalid input"
        assert err.code == ErrorCode.VALIDATION_ERROR.value

    def test_validation_error_with_field(self):
        """Test validation error with field."""
        err = ValidationError("Invalid", field_name="email")
        
        assert err.field_name == "email"

    def test_validation_error_to_dict(self):
        """Test validation error to_dict."""
        err = ValidationError("Invalid", field_name="price")
        
        result = err.to_dict()
        
        assert result["code"] == ErrorCode.VALIDATION_ERROR.value
        assert result["field_name"] == "price"


class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_auth_error_creation(self):
        """Test creating auth error."""
        err = AuthenticationError("Unauthorized")
        
        assert err.message == "Unauthorized"
        assert err.code == ErrorCode.AUTH_ERROR.value


class TestRateLimitExceeded:
    """Test RateLimitExceeded class."""

    def test_rate_limit_error_creation(self):
        """Test creating rate limit error."""
        err = RateLimitExceeded("Too many requests", retry_after=60)
        
        assert err.message == "Too many requests"
        assert err.retry_after == 60
        assert err.code == ErrorCode.RATE_LIMIT_ERROR.value

    def test_rate_limit_error_to_dict(self):
        """Test rate limit error to_dict."""
        err = RateLimitExceeded("Rate limited", retry_after=120)
        
        result = err.to_dict()
        
        assert result["retry_after"] == 120


class TestNetworkError:
    """Test NetworkError class."""

    def test_network_error_creation(self):
        """Test creating network error."""
        err = NetworkError("Connection failed")
        
        assert err.message == "Connection failed"
        assert err.code == ErrorCode.NETWORK_ERROR.value


class TestBusinessLogicError:
    """Test BusinessLogicError class."""

    def test_business_logic_error_creation(self):
        """Test creating business logic error."""
        err = BusinessLogicError("Insufficient funds")
        
        assert err.message == "Insufficient funds"
        assert err.code == ErrorCode.BUSINESS_LOGIC_ERROR.value


class TestDMarketSpecificErrors:
    """Test DMarket-specific exception classes."""

    def test_dmarket_specific_error(self):
        """Test DMarketSpecificError."""
        err = DMarketSpecificError("DMarket error")
        
        assert err.message == "DMarket error"
        assert isinstance(err, APIError)

    def test_insufficient_funds_error(self):
        """Test InsufficientFundsError."""
        err = InsufficientFundsError("Not enough balance")
        
        assert err.message == "Not enough balance"
        assert isinstance(err, DMarketSpecificError)

    def test_item_not_available_error(self):
        """Test ItemNotAvailableError."""
        err = ItemNotAvailableError("Item sold out")
        
        assert err.message == "Item sold out"
        assert isinstance(err, DMarketSpecificError)


class TestCategorizeError:
    """Test categorize_error function."""

    def test_categorize_api_error(self):
        """Test categorizing API error."""
        err = APIError("API failed")
        
        category = categorize_error(err)
        
        assert "API" in category or "api" in category

    def test_categorize_validation_error(self):
        """Test categorizing validation error."""
        err = ValidationError("Invalid")
        
        category = categorize_error(err)
        
        assert "validation" in category.lower() or "Validation" in category

    def test_categorize_generic_exception(self):
        """Test categorizing generic exception."""
        err = ValueError("Some error")
        
        category = categorize_error(err)
        
        assert category is not None


class TestFormatErrorForUser:
    """Test format_error_for_user function."""

    def test_format_api_error(self):
        """Test formatting API error for user."""
        err = APIError("API failed", status_code=500)
        
        formatted = format_error_for_user(err)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_validation_error(self):
        """Test formatting validation error for user."""
        err = ValidationError("Invalid input", field_name="email")
        
        formatted = format_error_for_user(err)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_generic_error(self):
        """Test formatting generic error for user."""
        err = Exception("Unknown error")
        
        formatted = format_error_for_user(err)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0

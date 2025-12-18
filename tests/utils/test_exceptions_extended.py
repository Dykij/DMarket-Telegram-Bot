"""Unit tests for exceptions module.

This module contains tests for src/utils/exceptions.py covering:
- ErrorCode enum
- BaseAppException
- APIError
- Other exception classes

Target: 25+ tests to achieve 70%+ coverage
"""

import pytest

from src.utils.exceptions import (
    APIError,
    BaseAppException,
    ErrorCode,
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

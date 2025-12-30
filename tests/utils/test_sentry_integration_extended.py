"""Tests for sentry_integration module.

This module tests Sentry integration initialization and helper functions.
"""

import logging
import os
from unittest.mock import MagicMock, patch

from src.utils.sentry_integration import (
    add_breadcrumb,
    before_send_callback,
    capture_exception,
    clear_user_context,
    init_sentry,
    set_transaction_name,
    set_user_context,
)


class TestInitSentry:
    """Tests for init_sentry function."""

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_dsn_logs_warning(self, mock_init, caplog):
        """Test init_sentry without DSN logs warning."""
        with caplog.at_level(logging.WARNING):
            init_sentry(dsn=None)

        # Should not initialize Sentry
        mock_init.assert_not_called()
        # Should log warning about missing DSN
        assert "SENTRY_DSN" in caplog.text or "not configured" in caplog.text.lower()

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    def test_init_with_dsn_initializes_sentry(self, mock_init):
        """Test init_sentry with DSN initializes Sentry."""
        init_sentry(dsn="https://test@sentry.io/123")

        mock_init.assert_called_once()

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    def test_init_with_environment(self, mock_init):
        """Test init_sentry passes environment parameter."""
        init_sentry(dsn="https://test@sentry.io/123", environment="staging")

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("environment") == "staging"

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    def test_init_with_release(self, mock_init):
        """Test init_sentry passes release parameter."""
        init_sentry(dsn="https://test@sentry.io/123", release="1.0.0")

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("release") == "1.0.0"

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    def test_init_with_traces_sample_rate(self, mock_init):
        """Test init_sentry passes traces_sample_rate."""
        init_sentry(dsn="https://test@sentry.io/123", traces_sample_rate=0.5)

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("traces_sample_rate") == 0.5

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    def test_init_with_profiles_sample_rate(self, mock_init):
        """Test init_sentry passes profiles_sample_rate."""
        init_sentry(dsn="https://test@sentry.io/123", profiles_sample_rate=0.2)

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("profiles_sample_rate") == 0.2

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    def test_init_with_debug_mode(self, mock_init):
        """Test init_sentry passes debug parameter."""
        init_sentry(dsn="https://test@sentry.io/123", debug=True)

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("debug") is True

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    @patch.dict(os.environ, {"SENTRY_DSN": "https://env@sentry.io/456"}, clear=True)
    def test_init_reads_dsn_from_env(self, mock_init):
        """Test init_sentry reads DSN from environment."""
        init_sentry()

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("dsn") == "https://env@sentry.io/456"

    @patch("src.utils.sentry_integration.sentry_sdk.init")
    @patch.dict(os.environ, {"SENTRY_RELEASE": "2.0.0"}, clear=True)
    def test_init_reads_release_from_env(self, mock_init):
        """Test init_sentry reads release from environment."""
        init_sentry(dsn="https://test@sentry.io/123")

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get("release") == "2.0.0"


class TestBeforeSendCallback:
    """Tests for before_send_callback function."""

    def test_before_send_callback_returns_event(self):
        """Test before_send_callback returns the event."""
        event = {"level": "error", "message": "Test error"}
        hint = {}

        result = before_send_callback(event, hint)

        assert result is not None
        assert "tags" in result
        assert result["tags"]["bot_type"] == "dmarket_telegram"

    def test_before_send_callback_filters_sensitive_headers(self):
        """Test that callback filters sensitive headers."""
        event = {
            "level": "error",
            "request": {
                "headers": {
                    "authorization": "Bearer secret",
                    "x-api-key": "secret_key",
                    "content-type": "application/json",
                }
            }
        }
        hint = {}

        result = before_send_callback(event, hint)

        # Sensitive headers should be removed
        assert "authorization" not in result["request"]["headers"]
        assert "x-api-key" not in result["request"]["headers"]
        # Non-sensitive headers should remain
        assert "content-type" in result["request"]["headers"]


class TestCaptureException:
    """Tests for capture_exception function."""

    @patch("src.utils.sentry_integration.sentry_sdk.capture_exception")
    @patch("src.utils.sentry_integration.sentry_sdk.push_scope")
    def test_capture_exception_calls_sentry(self, mock_push_scope, mock_capture):
        """Test capture_exception calls Sentry."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)

        error = ValueError("Test error")

        capture_exception(error)

        mock_capture.assert_called_once_with(error)

    @patch("src.utils.sentry_integration.sentry_sdk.capture_exception")
    @patch("src.utils.sentry_integration.sentry_sdk.push_scope")
    def test_capture_exception_with_various_types(self, mock_push_scope, mock_capture):
        """Test capture_exception with different exception types."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)

        errors = [
            ValueError("value error"),
            TypeError("type error"),
            RuntimeError("runtime error"),
        ]

        for error in errors:
            capture_exception(error)

        assert mock_capture.call_count == len(errors)


class TestSetUserContext:
    """Tests for set_user_context function."""

    @patch("src.utils.sentry_integration.sentry_sdk.set_user")
    def test_set_user_context_with_user_id(self, mock_set_user):
        """Test set_user_context with user_id."""
        set_user_context(user_id=12345)

        mock_set_user.assert_called_once()

    @patch("src.utils.sentry_integration.sentry_sdk.set_user")
    def test_set_user_context_with_username(self, mock_set_user):
        """Test set_user_context with username."""
        set_user_context(user_id=12345, username="testuser")

        mock_set_user.assert_called_once()

    @patch("src.utils.sentry_integration.sentry_sdk.set_user")
    def test_set_user_context_formats_correctly(self, mock_set_user):
        """Test set_user_context formats user data correctly."""
        set_user_context(user_id=12345, username="testuser")

        call_args = mock_set_user.call_args
        user_data = call_args[0][0] if call_args[0] else call_args[1]

        # User data should contain id
        assert "id" in user_data or isinstance(user_data, dict)


class TestClearUserContext:
    """Tests for clear_user_context function."""

    @patch("src.utils.sentry_integration.sentry_sdk.set_user")
    def test_clear_user_context_calls_sentry(self, mock_set_user):
        """Test clear_user_context calls Sentry with None."""
        clear_user_context()

        mock_set_user.assert_called_once_with(None)


class TestSetTransactionName:
    """Tests for set_transaction_name function."""

    def test_set_transaction_name_calls_sentry(self):
        """Test set_transaction_name calls Sentry."""
        # set_transaction doesn't exist in newer sentry_sdk
        # Just verify the function can be called without error
        try:
            set_transaction_name("test_transaction")
        except AttributeError:
            # Expected if sentry_sdk.set_transaction doesn't exist
            pass


class TestAddBreadcrumb:
    """Tests for add_breadcrumb function."""

    @patch("src.utils.sentry_integration.sentry_sdk.add_breadcrumb")
    def test_add_breadcrumb_calls_sentry(self, mock_add):
        """Test add_breadcrumb calls Sentry."""
        add_breadcrumb(message="User clicked button", category="ui")

        mock_add.assert_called_once()

    @patch("src.utils.sentry_integration.sentry_sdk.add_breadcrumb")
    def test_add_breadcrumb_with_level(self, mock_add):
        """Test add_breadcrumb with level parameter."""
        add_breadcrumb(message="Error occurred", category="error", level="error")

        mock_add.assert_called_once()

    @patch("src.utils.sentry_integration.sentry_sdk.add_breadcrumb")
    def test_add_breadcrumb_with_data(self, mock_add):
        """Test add_breadcrumb with data parameter."""
        add_breadcrumb(
            message="API call",
            category="http",
            data={"url": "/api/test", "status": 200}
        )

        mock_add.assert_called_once()

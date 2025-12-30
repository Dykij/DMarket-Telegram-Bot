"""Comprehensive tests for sentry_breadcrumbs module.

Tests for all breadcrumb functions and context management.
"""

from __future__ import annotations

from unittest.mock import patch


class TestAddTradingBreadcrumb:
    """Tests for add_trading_breadcrumb function."""

    def test_add_trading_breadcrumb_with_all_params(self) -> None:
        """Test adding breadcrumb with all parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

            add_trading_breadcrumb(
                action="scanning_market",
                game="csgo",
                level="standard",
                user_id=123456789,
                balance=100.50,
                item_count=50,
            )

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["category"] == "trading"
            assert "scanning_market" in call_kwargs["message"]
            assert call_kwargs["level"] == "info"
            assert call_kwargs["data"]["game"] == "csgo"
            assert call_kwargs["data"]["level"] == "standard"
            assert call_kwargs["data"]["user_id"] == 123456789
            assert call_kwargs["data"]["balance"] == "$100.50"
            assert call_kwargs["data"]["item_count"] == 50

    def test_add_trading_breadcrumb_minimal_params(self) -> None:
        """Test adding breadcrumb with minimal parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

            add_trading_breadcrumb(action="start_scan")

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert "start_scan" in call_kwargs["message"]

    def test_add_trading_breadcrumb_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

            add_trading_breadcrumb(action="scan")

            mock_sentry.add_breadcrumb.assert_not_called()

    def test_add_trading_breadcrumb_with_extra_data(self) -> None:
        """Test adding breadcrumb with extra data."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

            add_trading_breadcrumb(
                action="buy_item",
                game="csgo",
                custom_field="custom_value",
                item_name="AK-47",
            )

            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["data"]["custom_field"] == "custom_value"
            assert call_kwargs["data"]["item_name"] == "AK-47"


class TestAddApiBreadcrumb:
    """Tests for add_api_breadcrumb function."""

    def test_add_api_breadcrumb_with_all_params(self) -> None:
        """Test adding API breadcrumb with all parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_api_breadcrumb

            add_api_breadcrumb(
                endpoint="/marketplace-api/v1/items",
                method="GET",
                status_code=200,
                response_time_ms=250.5,
                game="csgo",
            )

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["category"] == "http"
            assert "GET" in call_kwargs["message"]
            assert "/marketplace-api/v1/items" in call_kwargs["message"]
            assert call_kwargs["data"]["status_code"] == 200
            assert call_kwargs["data"]["response_time_ms"] == "250.50"

    def test_add_api_breadcrumb_minimal_params(self) -> None:
        """Test adding API breadcrumb with minimal parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_api_breadcrumb

            add_api_breadcrumb(endpoint="/api/test")

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["data"]["endpoint"] == "/api/test"
            assert call_kwargs["data"]["method"] == "GET"

    def test_add_api_breadcrumb_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import add_api_breadcrumb

            add_api_breadcrumb(endpoint="/api/test")

            mock_sentry.add_breadcrumb.assert_not_called()

    def test_add_api_breadcrumb_post_method(self) -> None:
        """Test adding API breadcrumb with POST method."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_api_breadcrumb

            add_api_breadcrumb(
                endpoint="/api/buy",
                method="POST",
                status_code=201,
            )

            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert "POST" in call_kwargs["message"]
            assert call_kwargs["data"]["status_code"] == 201


class TestAddCommandBreadcrumb:
    """Tests for add_command_breadcrumb function."""

    def test_add_command_breadcrumb_with_all_params(self) -> None:
        """Test adding command breadcrumb with all parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_command_breadcrumb

            add_command_breadcrumb(
                command="scan",
                user_id=123456789,
                username="john_doe",
                chat_id=-1001234567890,
                game="csgo",
                level="standard",
            )

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["category"] == "telegram"
            assert "/scan" in call_kwargs["message"]
            assert call_kwargs["data"]["user_id"] == 123456789
            assert call_kwargs["data"]["username"] == "john_doe"
            assert call_kwargs["data"]["chat_id"] == -1001234567890

    def test_add_command_breadcrumb_minimal_params(self) -> None:
        """Test adding command breadcrumb with minimal parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_command_breadcrumb

            add_command_breadcrumb(command="start", user_id=123)

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert "/start" in call_kwargs["message"]
            assert call_kwargs["data"]["user_id"] == 123

    def test_add_command_breadcrumb_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import add_command_breadcrumb

            add_command_breadcrumb(command="start", user_id=123)

            mock_sentry.add_breadcrumb.assert_not_called()


class TestAddDatabaseBreadcrumb:
    """Tests for add_database_breadcrumb function."""

    def test_add_database_breadcrumb_with_all_params(self) -> None:
        """Test adding database breadcrumb with all parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_database_breadcrumb

            add_database_breadcrumb(
                operation="insert",
                table="market_data",
                record_id=42,
                affected_rows=100,
                batch_size=100,
            )

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["category"] == "database"
            assert "insert" in call_kwargs["message"]
            assert call_kwargs["data"]["operation"] == "insert"
            assert call_kwargs["data"]["table"] == "market_data"
            assert call_kwargs["data"]["record_id"] == 42
            assert call_kwargs["data"]["affected_rows"] == 100

    def test_add_database_breadcrumb_select(self) -> None:
        """Test adding database breadcrumb for select operation."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_database_breadcrumb

            add_database_breadcrumb(operation="select", table="users")

            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert "select" in call_kwargs["message"]

    def test_add_database_breadcrumb_minimal(self) -> None:
        """Test adding database breadcrumb with minimal parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_database_breadcrumb

            add_database_breadcrumb(operation="delete")

            mock_sentry.add_breadcrumb.assert_called_once()

    def test_add_database_breadcrumb_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import add_database_breadcrumb

            add_database_breadcrumb(operation="insert")

            mock_sentry.add_breadcrumb.assert_not_called()


class TestAddErrorBreadcrumb:
    """Tests for add_error_breadcrumb function."""

    def test_add_error_breadcrumb_default_severity(self) -> None:
        """Test adding error breadcrumb with default severity."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_error_breadcrumb

            add_error_breadcrumb(
                error_type="ValueError",
                error_message="Invalid input",
            )

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["category"] == "error"
            assert "ValueError" in call_kwargs["message"]
            assert call_kwargs["level"] == "error"

    def test_add_error_breadcrumb_warning_severity(self) -> None:
        """Test adding error breadcrumb with warning severity."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_error_breadcrumb

            add_error_breadcrumb(
                error_type="RateLimitError",
                error_message="Too many requests",
                severity="warning",
                retry_after=60,
            )

            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["level"] == "warning"
            assert call_kwargs["data"]["retry_after"] == 60

    def test_add_error_breadcrumb_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import add_error_breadcrumb

            add_error_breadcrumb(error_type="Error", error_message="Test")

            mock_sentry.add_breadcrumb.assert_not_called()


class TestAddCustomBreadcrumb:
    """Tests for add_custom_breadcrumb function."""

    def test_add_custom_breadcrumb(self) -> None:
        """Test adding custom breadcrumb."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_custom_breadcrumb

            add_custom_breadcrumb(
                category="cache",
                message="Cache hit",
                level="debug",
                cache_key="market_items_csgo",
                ttl=300,
            )

            mock_sentry.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["category"] == "cache"
            assert call_kwargs["message"] == "Cache hit"
            assert call_kwargs["level"] == "debug"

    def test_add_custom_breadcrumb_default_level(self) -> None:
        """Test adding custom breadcrumb with default level."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import add_custom_breadcrumb

            add_custom_breadcrumb(category="test", message="Test message")

            call_kwargs = mock_sentry.add_breadcrumb.call_args.kwargs
            assert call_kwargs["level"] == "info"

    def test_add_custom_breadcrumb_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import add_custom_breadcrumb

            add_custom_breadcrumb(category="test", message="Test")

            mock_sentry.add_breadcrumb.assert_not_called()


class TestSetUserContext:
    """Tests for set_user_context function."""

    def test_set_user_context_with_all_params(self) -> None:
        """Test setting user context with all parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import set_user_context

            set_user_context(
                user_id=123456789,
                username="john_doe",
                subscription="premium",
                balance=100.50,
            )

            mock_sentry.set_user.assert_called_once()
            call_args = mock_sentry.set_user.call_args[0][0]
            assert call_args["id"] == "123456789"
            assert call_args["username"] == "john_doe"
            assert call_args["subscription"] == "premium"
            assert call_args["balance"] == 100.50

    def test_set_user_context_minimal(self) -> None:
        """Test setting user context with minimal parameters."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import set_user_context

            set_user_context(user_id=123)

            mock_sentry.set_user.assert_called_once()
            call_args = mock_sentry.set_user.call_args[0][0]
            assert call_args["id"] == "123"

    def test_set_user_context_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import set_user_context

            set_user_context(user_id=123)

            mock_sentry.set_user.assert_not_called()


class TestSetContextTag:
    """Tests for set_context_tag function."""

    def test_set_context_tag_string_value(self) -> None:
        """Test setting context tag with string value."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import set_context_tag

            set_context_tag("game", "csgo")

            mock_sentry.set_tag.assert_called_once_with("game", "csgo")

    def test_set_context_tag_float_value(self) -> None:
        """Test setting context tag with float value."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import set_context_tag

            set_context_tag("balance", 100.50)

            mock_sentry.set_tag.assert_called_once_with("balance", 100.50)

    def test_set_context_tag_bool_value(self) -> None:
        """Test setting context tag with bool value."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import set_context_tag

            set_context_tag("premium", True)

            mock_sentry.set_tag.assert_called_once_with("premium", True)

    def test_set_context_tag_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import set_context_tag

            set_context_tag("key", "value")

            mock_sentry.set_tag.assert_not_called()


class TestClearBreadcrumbs:
    """Tests for clear_breadcrumbs function."""

    def test_clear_breadcrumbs(self) -> None:
        """Test clearing breadcrumbs."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import clear_breadcrumbs

            clear_breadcrumbs()

            mock_sentry.push_scope.assert_called_once()

    def test_clear_breadcrumbs_sentry_not_initialized(self) -> None:
        """Test that nothing happens when Sentry is not initialized."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False

            from src.utils.sentry_breadcrumbs import clear_breadcrumbs

            clear_breadcrumbs()

            mock_sentry.push_scope.assert_not_called()


class TestIntegration:
    """Integration tests for sentry_breadcrumbs module."""

    def test_multiple_breadcrumbs_in_sequence(self) -> None:
        """Test adding multiple breadcrumbs in sequence."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import (
                add_api_breadcrumb,
                add_command_breadcrumb,
                add_trading_breadcrumb,
            )

            # Simulate a user flow
            add_command_breadcrumb(command="scan", user_id=123)
            add_api_breadcrumb(endpoint="/api/items", status_code=200)
            add_trading_breadcrumb(action="found_opportunity", game="csgo")

            assert mock_sentry.add_breadcrumb.call_count == 3

    def test_user_context_and_tags(self) -> None:
        """Test setting user context and tags together."""
        with patch("src.utils.sentry_breadcrumbs.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True

            from src.utils.sentry_breadcrumbs import set_context_tag, set_user_context

            set_user_context(user_id=123, username="test_user")
            set_context_tag("game", "csgo")
            set_context_tag("level", "standard")

            mock_sentry.set_user.assert_called_once()
            assert mock_sentry.set_tag.call_count == 2

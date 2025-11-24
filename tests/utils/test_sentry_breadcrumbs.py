"""
Unit tests для модуля sentry_breadcrumbs.

Проверяет корректность добавления breadcrumbs в Sentry.
"""

from unittest.mock import MagicMock, patch

from src.utils.sentry_breadcrumbs import (
    add_api_breadcrumb,
    add_command_breadcrumb,
    add_custom_breadcrumb,
    add_database_breadcrumb,
    add_error_breadcrumb,
    add_trading_breadcrumb,
    set_context_tag,
    set_user_context,
)


class TestTradingBreadcrumbs:
    """Тесты для trading breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_trading_breadcrumb_minimal(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест минимального trading breadcrumb."""
        add_trading_breadcrumb(
            action="test_action",
            game="csgo",
        )

        mock_add_breadcrumb.assert_called_once()
        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["category"] == "default"
        assert call_args["message"] == "Trading: test_action"
        assert call_args["level"] == "info"
        assert call_args["data"]["action"] == "test_action"
        assert call_args["data"]["game"] == "csgo"

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_trading_breadcrumb_full(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест полного trading breadcrumb со всеми параметрами."""
        add_trading_breadcrumb(
            action="arbitrage_scan_started",
            game="csgo",
            level="standard",
            user_id=123456,
            balance=100.50,
            max_items=100,
            price_from=300,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["data"]["level"] == "standard"
        assert call_args["data"]["user_id"] == 123456
        assert call_args["data"]["balance"] == 100.50
        assert call_args["data"]["max_items"] == 100
        assert call_args["data"]["price_from"] == 300


class TestAPIBreadcrumbs:
    """Тесты для API breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_api_breadcrumb_success(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест API breadcrumb для успешного запроса."""
        add_api_breadcrumb(
            endpoint="/marketplace-api/v1/items",
            method="GET",
            status_code=200,
            response_time_ms=450.5,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["category"] == "http"
        assert call_args["message"] == "API: GET /marketplace-api/v1/items"
        assert call_args["data"]["endpoint"] == "/marketplace-api/v1/items"
        assert call_args["data"]["method"] == "GET"
        assert call_args["data"]["status_code"] == 200
        assert call_args["data"]["response_time_ms"] == 450.5

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_api_breadcrumb_error(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест API breadcrumb для ошибки."""
        add_api_breadcrumb(
            endpoint="/account/v1/balance",
            method="GET",
            status_code=429,
            error="rate_limit",
            retry_attempt=2,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["data"]["status_code"] == 429
        assert call_args["data"]["error"] == "rate_limit"
        assert call_args["data"]["retry_attempt"] == 2


class TestCommandBreadcrumbs:
    """Тесты для command breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_command_breadcrumb_basic(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест базового command breadcrumb."""
        add_command_breadcrumb(
            command="/start",
            user_id=123456,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["category"] == "navigation"
        assert call_args["message"] == "Command: /start"
        assert call_args["data"]["command"] == "/start"
        assert call_args["data"]["user_id"] == 123456

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_command_breadcrumb_full(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест command breadcrumb со всеми параметрами."""
        add_command_breadcrumb(
            command="/arbitrage",
            user_id=123456,
            username="john_doe",
            chat_id=987654,
            game="csgo",
            level="standard",
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["data"]["username"] == "john_doe"
        assert call_args["data"]["chat_id"] == 987654
        assert call_args["data"]["game"] == "csgo"
        assert call_args["data"]["level"] == "standard"


class TestDatabaseBreadcrumbs:
    """Тесты для database breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_database_breadcrumb_insert(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест database breadcrumb для INSERT."""
        add_database_breadcrumb(
            operation="INSERT",
            table="users",
            record_id="uuid-123",
            affected_rows=1,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["category"] == "query"
        assert call_args["message"] == "Database: INSERT users"
        assert call_args["data"]["operation"] == "INSERT"
        assert call_args["data"]["table"] == "users"
        assert call_args["data"]["record_id"] == "uuid-123"
        assert call_args["data"]["affected_rows"] == 1

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_database_breadcrumb_update(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест database breadcrumb для UPDATE."""
        add_database_breadcrumb(
            operation="UPDATE",
            table="market_data",
            affected_rows=15,
            query_time_ms=23.5,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["data"]["affected_rows"] == 15
        assert call_args["data"]["query_time_ms"] == 23.5


class TestErrorBreadcrumbs:
    """Тесты для error breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_error_breadcrumb_warning(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест error breadcrumb с уровнем warning."""
        add_error_breadcrumb(
            error_type="ValidationError",
            error_message="Invalid price",
            severity="warning",
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["category"] == "error"
        assert call_args["message"] == "Error: ValidationError - Invalid price"
        assert call_args["level"] == "warning"
        assert call_args["data"]["error_type"] == "ValidationError"
        assert call_args["data"]["error_message"] == "Invalid price"

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_error_breadcrumb_critical(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест error breadcrumb с уровнем critical."""
        add_error_breadcrumb(
            error_type="SystemError",
            error_message="Bot shutdown",
            severity="critical",
            consecutive_errors=5,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["level"] == "critical"
        assert call_args["data"]["consecutive_errors"] == 5


class TestCustomBreadcrumbs:
    """Тесты для custom breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    def test_add_custom_breadcrumb(self, mock_add_breadcrumb: MagicMock) -> None:
        """Тест custom breadcrumb."""
        add_custom_breadcrumb(
            category="cache",
            message="Cache miss",
            level="info",
            key="test_key",
            ttl=300,
        )

        call_args = mock_add_breadcrumb.call_args[1]

        assert call_args["category"] == "cache"
        assert call_args["message"] == "Cache miss"
        assert call_args["level"] == "info"
        assert call_args["data"]["key"] == "test_key"
        assert call_args["data"]["ttl"] == 300


class TestContextFunctions:
    """Тесты для функций установки контекста."""

    @patch("sentry_sdk.set_user")
    def test_set_user_context_basic(self, mock_set_user: MagicMock) -> None:
        """Тест установки user context."""
        set_user_context(
            user_id=123456,
            username="john_doe",
        )

        mock_set_user.assert_called_once_with({
            "id": 123456,
            "username": "john_doe",
        })

    @patch("sentry_sdk.set_user")
    def test_set_user_context_full(self, mock_set_user: MagicMock) -> None:
        """Тест установки user context со всеми параметрами."""
        set_user_context(
            user_id=123456,
            username="john_doe",
            language="ru",
            is_admin=True,
        )

        call_args = mock_set_user.call_args[0][0]

        assert call_args["id"] == 123456
        assert call_args["username"] == "john_doe"
        assert call_args["language"] == "ru"
        assert call_args["is_admin"] is True

    @patch("sentry_sdk.set_tag")
    def test_set_context_tag(self, mock_set_tag: MagicMock) -> None:
        """Тест установки context tag."""
        set_context_tag("environment", "production")

        mock_set_tag.assert_called_once_with("environment", "production")


class TestBreadcrumbIntegration:
    """Интеграционные тесты для breadcrumbs."""

    @patch("sentry_sdk.add_breadcrumb")
    @patch("sentry_sdk.set_user")
    def test_full_breadcrumb_trail(
        self,
        mock_set_user: MagicMock,
        mock_add_breadcrumb: MagicMock,
    ) -> None:
        """Тест полного trail breadcrumbs."""
        # 1. Установить user context
        set_user_context(user_id=123456, username="test_user")

        # 2. Command breadcrumb
        add_command_breadcrumb(command="/arbitrage", user_id=123456)

        # 3. Trading breadcrumb
        add_trading_breadcrumb(
            action="arbitrage_scan_started",
            game="csgo",
            level="standard",
        )

        # 4. API breadcrumb
        add_api_breadcrumb(
            endpoint="/marketplace-api/v1/items",
            method="GET",
            status_code=200,
            response_time_ms=450,
        )

        # 5. Error breadcrumb
        add_error_breadcrumb(
            error_type="RateLimitError",
            error_message="Too many requests",
            severity="error",
        )

        # Проверить, что все функции были вызваны
        assert mock_set_user.call_count == 1
        assert mock_add_breadcrumb.call_count == 4

        # Проверить последний breadcrumb (ошибка)
        last_call = mock_add_breadcrumb.call_args_list[-1][1]
        assert last_call["category"] == "error"
        assert last_call["data"]["error_type"] == "RateLimitError"

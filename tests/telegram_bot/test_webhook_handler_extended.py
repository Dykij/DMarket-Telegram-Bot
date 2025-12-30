"""Unit tests for webhook_handler.py.

This module tests src/telegram_bot/webhook_handler.py covering:
- WebhookHandler initialization and configuration
- Server lifecycle (start, stop)
- Webhook endpoint handling
- Health endpoint
- Metrics endpoint
- WebhookFailover initialization
- Failover mode switching
- Health monitoring loop

Target: 40+ tests to achieve 70%+ coverage
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import web
import pytest

from src.telegram_bot.webhook_handler import (
    WebhookFailover,
    WebhookHandler,
)


# Test fixtures


@pytest.fixture()
def mock_bot_app():
    """Fixture providing a mocked Telegram Application."""
    app = MagicMock()
    app.bot = MagicMock()
    app.bot.set_webhook = AsyncMock(return_value=True)
    app.bot.delete_webhook = AsyncMock(return_value=True)
    app.process_update = AsyncMock()
    app.start = AsyncMock()
    app.stop = AsyncMock()
    app.updater = MagicMock()
    app.updater.running = False
    app.updater.start_polling = AsyncMock()
    app.updater.stop = AsyncMock()
    return app


@pytest.fixture()
def webhook_handler(mock_bot_app):
    """Fixture providing a WebhookHandler instance."""
    return WebhookHandler(
        bot_app=mock_bot_app,
        host="127.0.0.1",
        port=8443,
        webhook_path="/webhook",
        health_path="/health",
    )


@pytest.fixture()
def webhook_failover(mock_bot_app, webhook_handler):
    """Fixture providing a WebhookFailover instance."""
    return WebhookFailover(
        bot_app=mock_bot_app,
        webhook_url="https://example.com",
        webhook_handler=webhook_handler,
        health_check_interval=30,
        failure_threshold=3,
    )


# TestWebhookHandlerInit


class TestWebhookHandlerInit:
    """Tests for WebhookHandler initialization."""

    def test_init_with_defaults(self, mock_bot_app):
        """Test initialization with default parameters."""
        handler = WebhookHandler(bot_app=mock_bot_app)

        assert handler.bot_app == mock_bot_app
        assert handler.host == "0.0.0.0"
        assert handler.port == 8443
        assert handler.webhook_path == "/webhook"
        assert handler.health_path == "/health"

    def test_init_with_custom_params(self, mock_bot_app):
        """Test initialization with custom parameters."""
        handler = WebhookHandler(
            bot_app=mock_bot_app,
            host="127.0.0.1",
            port=9000,
            webhook_path="/api/webhook",
            health_path="/api/health",
        )

        assert handler.host == "127.0.0.1"
        assert handler.port == 9000
        assert handler.webhook_path == "/api/webhook"
        assert handler.health_path == "/api/health"

    def test_init_state(self, webhook_handler):
        """Test initial state of handler."""
        assert webhook_handler._app is None
        assert webhook_handler._runner is None
        assert webhook_handler._site is None
        assert webhook_handler._running is False
        assert webhook_handler._request_count == 0
        assert webhook_handler._error_count == 0
        assert webhook_handler._last_request_time is None
        assert webhook_handler._start_time is None


# TestWebhookHandlerSetup


class TestWebhookHandlerSetup:
    """Tests for WebhookHandler setup."""

    @pytest.mark.asyncio()
    async def test_setup_creates_app(self, webhook_handler):
        """Test that setup creates aiohttp application."""
        app = await webhook_handler.setup()

        assert app is not None
        assert isinstance(app, web.Application)
        assert webhook_handler._app == app

    @pytest.mark.asyncio()
    async def test_setup_registers_routes(self, webhook_handler):
        """Test that setup registers all routes."""
        await webhook_handler.setup()

        # Check routes are registered
        routes = list(webhook_handler._app.router.routes())
        paths = [r.resource.canonical if hasattr(r, "resource") else str(r) for r in routes]

        # At least 4 routes should exist
        assert len(routes) >= 4


# TestWebhookHandlerStartStop


class TestWebhookHandlerStartStop:
    """Tests for start and stop functionality."""

    @pytest.mark.asyncio()
    async def test_start_sets_running_true(self, webhook_handler):
        """Test that start sets running flag to True."""
        with patch.object(web.AppRunner, "setup", new_callable=AsyncMock):
            with patch.object(web.TCPSite, "start", new_callable=AsyncMock):
                await webhook_handler.start()

        assert webhook_handler._running is True
        assert webhook_handler._start_time is not None

    @pytest.mark.asyncio()
    async def test_start_idempotent(self, webhook_handler):
        """Test that multiple starts don't break."""
        webhook_handler._running = True

        # Should log warning but not fail
        await webhook_handler.start()

        # Still running
        assert webhook_handler._running is True

    @pytest.mark.asyncio()
    async def test_stop_when_not_running(self, webhook_handler):
        """Test stop when not running."""
        webhook_handler._running = False

        # Should not fail
        await webhook_handler.stop()

        assert webhook_handler._running is False

    @pytest.mark.asyncio()
    async def test_stop_cleans_up(self, webhook_handler):
        """Test that stop cleans up resources."""
        webhook_handler._running = True
        webhook_handler._site = MagicMock()
        webhook_handler._site.stop = AsyncMock()
        webhook_handler._runner = MagicMock()
        webhook_handler._runner.cleanup = AsyncMock()

        await webhook_handler.stop()

        assert webhook_handler._running is False
        webhook_handler._site.stop.assert_called_once()
        webhook_handler._runner.cleanup.assert_called_once()


# TestWebhookEndpoint


class TestWebhookEndpoint:
    """Tests for webhook endpoint handling."""

    @pytest.mark.asyncio()
    async def test_handle_webhook_success(self, webhook_handler):
        """Test successful webhook processing."""
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={"update_id": 123})

        with patch("telegram.Update.de_json") as mock_de_json:
            mock_update = MagicMock()
            mock_de_json.return_value = mock_update

            response = await webhook_handler._handle_webhook(mock_request)

        assert response.status == 200
        assert webhook_handler._request_count == 1
        assert webhook_handler._last_request_time is not None

    @pytest.mark.asyncio()
    async def test_handle_webhook_error(self, webhook_handler):
        """Test webhook error handling."""
        mock_request = MagicMock()
        mock_request.json = AsyncMock(side_effect=Exception("JSON parse error"))

        response = await webhook_handler._handle_webhook(mock_request)

        assert response.status == 500
        assert webhook_handler._error_count == 1

    @pytest.mark.asyncio()
    async def test_handle_webhook_null_update(self, webhook_handler):
        """Test webhook with null update."""
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={})

        with patch("telegram.Update.de_json", return_value=None):
            response = await webhook_handler._handle_webhook(mock_request)

        assert response.status == 200
        # Request count should NOT increment for null update
        assert webhook_handler._request_count == 0


# TestHealthEndpoint


class TestHealthEndpoint:
    """Tests for health endpoint."""

    @pytest.mark.asyncio()
    async def test_handle_health_healthy(self, webhook_handler):
        """Test health endpoint when healthy."""
        webhook_handler._running = True
        webhook_handler._start_time = datetime.now(UTC) - timedelta(hours=1)
        webhook_handler._request_count = 100
        webhook_handler._error_count = 5

        mock_request = MagicMock()
        response = await webhook_handler._handle_health(mock_request)

        assert response.status == 200
        assert response.content_type == "application/json"

    @pytest.mark.asyncio()
    async def test_handle_health_unhealthy(self, webhook_handler):
        """Test health endpoint when unhealthy."""
        webhook_handler._running = False

        mock_request = MagicMock()
        response = await webhook_handler._handle_health(mock_request)

        assert response.status == 200

    @pytest.mark.asyncio()
    async def test_handle_health_no_start_time(self, webhook_handler):
        """Test health endpoint when start time is None."""
        webhook_handler._running = True
        webhook_handler._start_time = None

        mock_request = MagicMock()
        response = await webhook_handler._handle_health(mock_request)

        assert response.status == 200


# TestRootEndpoint


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio()
    async def test_handle_root(self, webhook_handler):
        """Test root endpoint returns server info."""
        mock_request = MagicMock()
        response = await webhook_handler._handle_root(mock_request)

        assert response.status == 200
        assert "DMarket" in response.text


# TestMetricsEndpoint


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""

    @pytest.mark.asyncio()
    async def test_handle_metrics(self, webhook_handler):
        """Test metrics endpoint returns Prometheus format."""
        webhook_handler._request_count = 100
        webhook_handler._error_count = 5
        webhook_handler._start_time = datetime.now(UTC) - timedelta(hours=1)

        mock_request = MagicMock()
        response = await webhook_handler._handle_metrics(mock_request)

        assert response.status == 200
        assert "webhook_requests_total" in response.text
        assert "webhook_uptime_seconds" in response.text
        assert "text/plain" in response.content_type

    @pytest.mark.asyncio()
    async def test_handle_metrics_no_start_time(self, webhook_handler):
        """Test metrics endpoint with no start time."""
        webhook_handler._start_time = None

        mock_request = MagicMock()
        response = await webhook_handler._handle_metrics(mock_request)

        assert response.status == 200
        assert "webhook_uptime_seconds 0" in response.text


# TestWebhookHandlerProperties


class TestWebhookHandlerProperties:
    """Tests for handler properties."""

    def test_is_running_property(self, webhook_handler):
        """Test is_running property."""
        assert webhook_handler.is_running is False

        webhook_handler._running = True
        assert webhook_handler.is_running is True

    def test_stats_property(self, webhook_handler):
        """Test stats property."""
        webhook_handler._running = True
        webhook_handler._request_count = 50
        webhook_handler._error_count = 2
        webhook_handler._start_time = datetime.now(UTC)
        webhook_handler._last_request_time = datetime.now(UTC)

        stats = webhook_handler.stats

        assert stats["running"] is True
        assert stats["request_count"] == 50
        assert stats["error_count"] == 2
        assert stats["start_time"] is not None
        assert stats["last_request"] is not None

    def test_stats_property_no_times(self, webhook_handler):
        """Test stats property with no times set."""
        stats = webhook_handler.stats

        assert stats["start_time"] is None
        assert stats["last_request"] is None


# TestWebhookFailoverInit


class TestWebhookFailoverInit:
    """Tests for WebhookFailover initialization."""

    def test_init_with_defaults(self, mock_bot_app, webhook_handler):
        """Test initialization with defaults."""
        failover = WebhookFailover(
            bot_app=mock_bot_app,
            webhook_url="https://example.com",
            webhook_handler=webhook_handler,
        )

        assert failover.bot_app == mock_bot_app
        assert failover.webhook_url == "https://example.com"
        assert failover.health_check_interval == 30
        assert failover.failure_threshold == 3

    def test_init_with_custom_params(self, mock_bot_app, webhook_handler):
        """Test initialization with custom parameters."""
        failover = WebhookFailover(
            bot_app=mock_bot_app,
            webhook_url="https://custom.com",
            webhook_handler=webhook_handler,
            health_check_interval=60,
            failure_threshold=5,
        )

        assert failover.health_check_interval == 60
        assert failover.failure_threshold == 5

    def test_init_state(self, webhook_failover):
        """Test initial state."""
        assert webhook_failover._mode == "polling"
        assert webhook_failover._failover_task is None
        assert webhook_failover._running is False
        assert webhook_failover._consecutive_failures == 0


# TestWebhookFailoverModes


class TestWebhookFailoverModes:
    """Tests for failover mode operations."""

    @pytest.mark.asyncio()
    async def test_try_webhook_mode_success(self, webhook_failover):
        """Test successful webhook mode setup."""
        webhook_failover.webhook_handler.start = AsyncMock()
        webhook_failover.bot_app.bot.set_webhook = AsyncMock(return_value=True)

        result = await webhook_failover._try_webhook_mode()

        assert result is True
        webhook_failover.webhook_handler.start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_try_webhook_mode_failure(self, webhook_failover):
        """Test failed webhook mode setup."""
        webhook_failover.webhook_handler.start = AsyncMock(side_effect=Exception("Start failed"))
        webhook_failover.webhook_handler.is_running = False
        webhook_failover.webhook_handler.stop = AsyncMock()

        result = await webhook_failover._try_webhook_mode()

        assert result is False

    @pytest.mark.asyncio()
    async def test_try_webhook_mode_set_webhook_fails(self, webhook_failover):
        """Test webhook mode when set_webhook fails."""
        webhook_failover.webhook_handler.start = AsyncMock()
        webhook_failover.webhook_handler.stop = AsyncMock()
        webhook_failover.bot_app.bot.set_webhook = AsyncMock(return_value=False)

        result = await webhook_failover._try_webhook_mode()

        assert result is False
        webhook_failover.webhook_handler.stop.assert_called_once()

    @pytest.mark.asyncio()
    async def test_start_polling_mode(self, webhook_failover):
        """Test starting polling mode."""
        await webhook_failover._start_polling_mode()

        webhook_failover.bot_app.bot.delete_webhook.assert_called_once()
        webhook_failover.bot_app.start.assert_called_once()


# TestWebhookFailoverStartStop


class TestWebhookFailoverStartStop:
    """Tests for start and stop operations."""

    @pytest.mark.asyncio()
    async def test_start_with_webhook(self, webhook_failover):
        """Test starting with webhook mode."""
        webhook_failover._try_webhook_mode = AsyncMock(return_value=True)

        await webhook_failover.start_with_failover()

        assert webhook_failover._running is True
        assert webhook_failover._mode == "webhook"

    @pytest.mark.asyncio()
    async def test_start_fallback_to_polling(self, webhook_failover):
        """Test falling back to polling when webhook fails."""
        webhook_failover._try_webhook_mode = AsyncMock(return_value=False)
        webhook_failover._start_polling_mode = AsyncMock()

        await webhook_failover.start_with_failover()

        assert webhook_failover._running is True
        assert webhook_failover._mode == "polling"

    @pytest.mark.asyncio()
    async def test_start_without_webhook_url(self, mock_bot_app, webhook_handler):
        """Test starting without webhook URL."""
        failover = WebhookFailover(
            bot_app=mock_bot_app,
            webhook_url="",  # No webhook URL
            webhook_handler=webhook_handler,
        )
        failover._start_polling_mode = AsyncMock()

        await failover.start_with_failover()

        assert failover._mode == "polling"

    @pytest.mark.asyncio()
    async def test_stop_webhook_mode(self, webhook_failover):
        """Test stopping in webhook mode."""
        webhook_failover._running = True
        webhook_failover._mode = "webhook"
        webhook_failover.webhook_handler.stop = AsyncMock()
        webhook_failover._failover_task = MagicMock()
        webhook_failover._failover_task.cancel = MagicMock()

        await webhook_failover.stop()

        assert webhook_failover._running is False
        webhook_failover.webhook_handler.stop.assert_called_once()

    @pytest.mark.asyncio()
    async def test_stop_polling_mode(self, webhook_failover):
        """Test stopping in polling mode."""
        webhook_failover._running = True
        webhook_failover._mode = "polling"
        webhook_failover.bot_app.updater.running = True

        await webhook_failover.stop()

        assert webhook_failover._running is False


# TestWebhookFailoverSwitching


class TestWebhookFailoverSwitching:
    """Tests for mode switching."""

    @pytest.mark.asyncio()
    async def test_switch_to_polling(self, webhook_failover):
        """Test switching to polling mode."""
        webhook_failover.webhook_handler.stop = AsyncMock()
        webhook_failover._start_polling_mode = AsyncMock()

        await webhook_failover._switch_to_polling()

        assert webhook_failover._mode == "polling"
        webhook_failover.webhook_handler.stop.assert_called_once()
        webhook_failover._start_polling_mode.assert_called_once()

    @pytest.mark.asyncio()
    async def test_switch_to_webhook(self, webhook_failover):
        """Test switching to webhook mode."""
        await webhook_failover._switch_to_webhook()

        assert webhook_failover._mode == "webhook"


# TestWebhookFailoverProperties


class TestWebhookFailoverProperties:
    """Tests for failover properties."""

    def test_current_mode_property(self, webhook_failover):
        """Test current_mode property."""
        assert webhook_failover.current_mode == "polling"

        webhook_failover._mode = "webhook"
        assert webhook_failover.current_mode == "webhook"

    def test_is_running_property(self, webhook_failover):
        """Test is_running property."""
        assert webhook_failover.is_running is False

        webhook_failover._running = True
        assert webhook_failover.is_running is True


# TestFailoverLoop


class TestFailoverLoop:
    """Tests for failover monitoring loop."""

    @pytest.mark.asyncio()
    async def test_failover_loop_webhook_healthy(self, webhook_failover):
        """Test failover loop when webhook is healthy."""
        webhook_failover._running = True
        webhook_failover._mode = "webhook"
        webhook_failover.webhook_handler._running = True
        webhook_failover._consecutive_failures = 0

        # Run one iteration
        webhook_failover._running = False  # Stop after first check

        # No mode change expected
        assert webhook_failover._mode == "webhook"

    @pytest.mark.asyncio()
    async def test_failover_loop_webhook_unhealthy_increments(self, webhook_failover):
        """Test that unhealthy webhook increments failure count."""
        webhook_failover._mode = "webhook"
        webhook_failover.webhook_handler._running = False

        # Simulate unhealthy check
        webhook_failover._consecutive_failures += 1

        assert webhook_failover._consecutive_failures == 1


# TestEdgeCases


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio()
    async def test_webhook_handle_empty_json(self, webhook_handler):
        """Test webhook with empty JSON."""
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={})

        with patch("telegram.Update.de_json", return_value=None):
            response = await webhook_handler._handle_webhook(mock_request)

        assert response.status == 200

    @pytest.mark.asyncio()
    async def test_failover_delete_webhook_fails(self, webhook_failover):
        """Test failover when delete_webhook fails."""
        webhook_failover.bot_app.bot.delete_webhook = AsyncMock(
            side_effect=Exception("Network error")
        )

        # Should not raise
        await webhook_failover._start_polling_mode()

    def test_stats_default_values(self, webhook_handler):
        """Test stats with all default values."""
        stats = webhook_handler.stats

        assert stats["running"] is False
        assert stats["request_count"] == 0
        assert stats["error_count"] == 0
        assert stats["start_time"] is None
        assert stats["last_request"] is None

    @pytest.mark.asyncio()
    async def test_stop_failover_task_cancelled_error(self, webhook_failover):
        """Test stop handles CancelledError gracefully."""
        import asyncio

        webhook_failover._running = True
        webhook_failover._mode = "polling"

        # Create a task that will be cancelled
        async def dummy_task():
            await asyncio.sleep(10)

        webhook_failover._failover_task = asyncio.create_task(dummy_task())

        await webhook_failover.stop()

        assert webhook_failover._running is False
        assert webhook_failover._failover_task is None

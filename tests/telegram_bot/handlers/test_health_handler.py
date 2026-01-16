"""Tests for health_handler module.

This module tests the HealthHandler class for system health
monitoring via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestHealthHandler:
    """Tests for HealthHandler class."""

    @pytest.fixture
    def mock_health_monitor(self):
        """Create mock health monitor."""
        monitor = MagicMock()
        monitor.check_health = AsyncMock(return_value={
            "status": "healthy",
            "components": {
                "api": "ok",
                "database": "ok",
                "cache": "ok",
            }
        })
        monitor.get_metrics = AsyncMock(return_value={
            "cpu": 25.0,
            "memory": 512,
            "requests": 1000,
        })
        return monitor

    @pytest.fixture
    def handler(self, mock_health_monitor):
        """Create HealthHandler instance."""
        from src.telegram_bot.handlers.health_handler import HealthHandler
        return HealthHandler(health_monitor=mock_health_monitor)

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = MagicMock()
        context.user_data = {}
        context.bot_data = {}
        return context

    @pytest.mark.asyncio
    async def test_health_command(self, handler, mock_update, mock_context):
        """Test /health command."""
        await handler.health_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing health menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health(self, handler, mock_update, mock_context, mock_health_monitor):
        """Test checking system health."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "health_check"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.check_health(mock_update, mock_context)

        mock_health_monitor.check_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_metrics(self, handler, mock_update, mock_context, mock_health_monitor):
        """Test getting system metrics."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "health_metrics"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_metrics(mock_update, mock_context)

        mock_health_monitor.get_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_api_health(self, handler, mock_update, mock_context, mock_health_monitor):
        """Test checking API health."""
        mock_health_monitor.check_api = AsyncMock(return_value={"status": "ok", "latency": 50})

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "health_api"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.check_api(mock_update, mock_context)

        mock_health_monitor.check_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_health(self, handler, mock_update, mock_context, mock_health_monitor):
        """Test checking database health."""
        mock_health_monitor.check_database = AsyncMock(return_value={"status": "ok", "connections": 5})

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "health_database"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.check_database(mock_update, mock_context)

        mock_health_monitor.check_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_unhealthy_status(self, handler, mock_update, mock_context, mock_health_monitor):
        """Test unhealthy status display."""
        mock_health_monitor.check_health.return_value = {
            "status": "unhealthy",
            "components": {
                "api": "ok",
                "database": "error",
                "cache": "ok",
            },
            "errors": ["Database connection failed"]
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "health_check"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.check_health(mock_update, mock_context)

        # Should show error status

    @pytest.mark.asyncio
    async def test_show_logs(self, handler, mock_update, mock_context, mock_health_monitor):
        """Test showing recent logs."""
        mock_health_monitor.get_recent_logs = AsyncMock(return_value=[
            {"level": "INFO", "message": "System started"},
            {"level": "WARNING", "message": "High memory usage"},
        ])

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "health_logs"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_logs(mock_update, mock_context)

        mock_health_monitor.get_recent_logs.assert_called_once()

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

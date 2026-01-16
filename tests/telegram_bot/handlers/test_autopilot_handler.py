"""Tests for autopilot_handler module.

This module tests the AutopilotHandler class for automated
trading management via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestAutopilotHandler:
    """Tests for AutopilotHandler class."""

    @pytest.fixture
    def mock_autopilot(self):
        """Create mock autopilot manager."""
        autopilot = MagicMock()
        autopilot.start = AsyncMock()
        autopilot.stop = AsyncMock()
        autopilot.get_status = MagicMock(return_value={"is_running": False})
        autopilot.get_stats = AsyncMock(return_value={"trades": 0, "profit": 0.0})
        autopilot.set_config = MagicMock()
        return autopilot

    @pytest.fixture
    def handler(self, mock_autopilot):
        """Create AutopilotHandler instance."""
        from src.telegram_bot.handlers.autopilot_handler import AutopilotHandler
        return AutopilotHandler(autopilot=mock_autopilot)

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
    async def test_autopilot_command(self, handler, mock_update, mock_context):
        """Test /autopilot command."""
        await handler.autopilot_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing autopilot menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_autopilot(self, handler, mock_update, mock_context, mock_autopilot):
        """Test starting autopilot."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_start"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.start_autopilot(mock_update, mock_context)

        mock_autopilot.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_autopilot(self, handler, mock_update, mock_context, mock_autopilot):
        """Test stopping autopilot."""
        mock_autopilot.get_status.return_value = {"is_running": True}

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_stop"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.stop_autopilot(mock_update, mock_context)

        mock_autopilot.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status(self, handler, mock_update, mock_context, mock_autopilot):
        """Test getting autopilot status."""
        mock_autopilot.get_status.return_value = {
            "is_running": True,
            "mode": "aggressive",
            "uptime": "2h 30m",
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_status"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_status(mock_update, mock_context)

        mock_autopilot.get_status.assert_called()

    @pytest.mark.asyncio
    async def test_get_stats(self, handler, mock_update, mock_context, mock_autopilot):
        """Test getting autopilot stats."""
        mock_autopilot.get_stats.return_value = {
            "trades": 25,
            "profit": 150.0,
            "success_rate": 0.85,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_stats"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_stats(mock_update, mock_context)

        mock_autopilot.get_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_settings(self, handler, mock_update, mock_context):
        """Test showing settings."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_settings"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_settings(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_set_mode(self, handler, mock_update, mock_context, mock_autopilot):
        """Test setting autopilot mode."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_mode_aggressive"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.set_mode(mock_update, mock_context)

        mock_autopilot.set_config.assert_called()

    @pytest.mark.asyncio
    async def test_set_budget(self, handler, mock_update, mock_context):
        """Test setting budget."""
        mock_update.message.text = "100"
        mock_context.user_data["awaiting"] = "budget"

        await handler.handle_input(mock_update, mock_context)

        assert mock_context.user_data.get("budget") == 100

    @pytest.mark.asyncio
    async def test_autopilot_already_running(self, handler, mock_update, mock_context, mock_autopilot):
        """Test starting when already running."""
        mock_autopilot.get_status.return_value = {"is_running": True}

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "autopilot_start"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.start_autopilot(mock_update, mock_context)

        # Should handle gracefully

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

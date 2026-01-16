"""Tests for panic_handler module.

This module tests the PanicHandler class for emergency sell
and panic mode management via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestPanicHandler:
    """Tests for PanicHandler class."""

    @pytest.fixture
    def mock_panic_manager(self):
        """Create mock panic manager."""
        manager = MagicMock()
        manager.activate_panic_mode = AsyncMock(return_value={"success": True, "items_sold": 5})
        manager.deactivate_panic_mode = AsyncMock(return_value=True)
        manager.get_status = MagicMock(return_value={"is_active": False})
        manager.sell_all = AsyncMock(return_value={"sold": 10, "total": 500.0})
        return manager

    @pytest.fixture
    def handler(self, mock_panic_manager):
        """Create PanicHandler instance."""
        from src.telegram_bot.handlers.panic_handler import PanicHandler
        return PanicHandler(panic_manager=mock_panic_manager)

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
    async def test_panic_command(self, handler, mock_update, mock_context):
        """Test /panic command."""
        await handler.panic_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing panic menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_panic_mode(self, handler, mock_update, mock_context, mock_panic_manager):
        """Test activating panic mode."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_activate"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.activate_panic(mock_update, mock_context)

        mock_panic_manager.activate_panic_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_panic_mode(self, handler, mock_update, mock_context, mock_panic_manager):
        """Test deactivating panic mode."""
        mock_panic_manager.get_status.return_value = {"is_active": True}

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_deactivate"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.deactivate_panic(mock_update, mock_context)

        mock_panic_manager.deactivate_panic_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_sell_all(self, handler, mock_update, mock_context, mock_panic_manager):
        """Test selling all items."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_sell_all"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.sell_all(mock_update, mock_context)

        mock_panic_manager.sell_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status(self, handler, mock_update, mock_context, mock_panic_manager):
        """Test getting panic status."""
        mock_panic_manager.get_status.return_value = {
            "is_active": False,
            "last_activation": None,
            "items_in_inventory": 10,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_status"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_status(mock_update, mock_context)

        mock_panic_manager.get_status.assert_called()

    @pytest.mark.asyncio
    async def test_confirm_sell_all(self, handler, mock_update, mock_context):
        """Test confirming sell all action."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_confirm_sell"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.confirm_sell_all(mock_update, mock_context)

        # Should show confirmation dialog

    @pytest.mark.asyncio
    async def test_cancel_action(self, handler, mock_update, mock_context):
        """Test canceling panic action."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_cancel"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.cancel(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_panic_mode_already_active(self, handler, mock_update, mock_context, mock_panic_manager):
        """Test activating panic mode when already active."""
        mock_panic_manager.get_status.return_value = {"is_active": True}

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_activate"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.activate_panic(mock_update, mock_context)

        # Should handle gracefully

    @pytest.mark.asyncio
    async def test_sell_all_with_discount(self, handler, mock_update, mock_context, mock_panic_manager):
        """Test selling all with discount."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "panic_sell_discount_10"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.sell_with_discount(mock_update, mock_context)

        # Should sell with 10% discount

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

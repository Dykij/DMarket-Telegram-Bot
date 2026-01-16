"""Tests for intelligent_hold_handler module.

This module tests the IntelligentHoldHandler class for managing
intelligent item holding strategies via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestIntelligentHoldHandler:
    """Tests for IntelligentHoldHandler class."""

    @pytest.fixture
    def mock_hold_manager(self):
        """Create mock hold manager."""
        manager = MagicMock()
        manager.analyze_item = AsyncMock(return_value={
            "recommendation": "hold",
            "expected_profit": 15.0,
            "hold_duration": "7 days",
        })
        manager.get_holdings = AsyncMock(return_value=[])
        manager.set_hold = AsyncMock(return_value=True)
        manager.release_hold = AsyncMock(return_value=True)
        return manager

    @pytest.fixture
    def handler(self, mock_hold_manager):
        """Create IntelligentHoldHandler instance."""
        from src.telegram_bot.handlers.intelligent_hold_handler import IntelligentHoldHandler
        return IntelligentHoldHandler(hold_manager=mock_hold_manager)

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
    async def test_hold_command(self, handler, mock_update, mock_context):
        """Test /hold command."""
        await handler.hold_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing hold menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_item(self, handler, mock_update, mock_context, mock_hold_manager):
        """Test analyzing item for hold."""
        mock_update.message.text = "/analyze AK-47 | Redline"

        await handler.analyze_item(mock_update, mock_context)

        mock_hold_manager.analyze_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_holdings(self, handler, mock_update, mock_context, mock_hold_manager):
        """Test showing current holdings."""
        mock_hold_manager.get_holdings.return_value = [
            {"item": "AK-47", "hold_since": "2026-01-01", "expected_profit": 10.0},
            {"item": "M4A4", "hold_since": "2026-01-05", "expected_profit": 15.0},
        ]

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "hold_list"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_holdings(mock_update, mock_context)

        mock_hold_manager.get_holdings.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_hold(self, handler, mock_update, mock_context, mock_hold_manager):
        """Test setting item on hold."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "hold_set_item123"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.set_hold(mock_update, mock_context)

        mock_hold_manager.set_hold.assert_called_once()

    @pytest.mark.asyncio
    async def test_release_hold(self, handler, mock_update, mock_context, mock_hold_manager):
        """Test releasing item from hold."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "hold_release_item123"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.release_hold(mock_update, mock_context)

        mock_hold_manager.release_hold.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recommendations(self, handler, mock_update, mock_context, mock_hold_manager):
        """Test getting hold recommendations."""
        mock_hold_manager.get_recommendations = AsyncMock(return_value=[
            {"item": "AK-47", "recommendation": "buy_and_hold", "confidence": 0.85},
        ])

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "hold_recommendations"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_recommendations(mock_update, mock_context)

        mock_hold_manager.get_recommendations.assert_called_once()

    @pytest.mark.asyncio
    async def test_configure_settings(self, handler, mock_update, mock_context):
        """Test configuring hold settings."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "hold_settings"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_settings(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_empty_holdings(self, handler, mock_update, mock_context, mock_hold_manager):
        """Test showing empty holdings."""
        mock_hold_manager.get_holdings.return_value = []

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "hold_list"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_holdings(mock_update, mock_context)

        # Should show "no holdings" message

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

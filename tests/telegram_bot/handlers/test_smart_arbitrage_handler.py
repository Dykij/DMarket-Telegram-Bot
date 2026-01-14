"""Tests for smart_arbitrage_handler module.

This module tests the SmartArbitrageHandler class for intelligent
arbitrage operations via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestSmartArbitrageHandler:
    """Tests for SmartArbitrageHandler class."""

    @pytest.fixture
    def mock_smart_arbitrage(self):
        """Create mock smart arbitrage engine."""
        engine = MagicMock()
        engine.scan_opportunities = AsyncMock(return_value=[])
        engine.execute_opportunity = AsyncMock(return_value={"success": True})
        engine.get_status = MagicMock(return_value={"is_running": False})
        engine.start = AsyncMock()
        engine.stop = AsyncMock()
        return engine

    @pytest.fixture
    def handler(self, mock_smart_arbitrage):
        """Create SmartArbitrageHandler instance."""
        from src.telegram_bot.handlers.smart_arbitrage_handler import SmartArbitrageHandler
        return SmartArbitrageHandler(smart_arbitrage=mock_smart_arbitrage)

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
    async def test_smart_arbitrage_command(self, handler, mock_update, mock_context):
        """Test /smart_arbitrage command."""
        await handler.smart_arbitrage_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing smart arbitrage menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_smart_arbitrage(self, handler, mock_update, mock_context, mock_smart_arbitrage):
        """Test starting smart arbitrage."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_start"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.start_arbitrage(mock_update, mock_context)

        mock_smart_arbitrage.start.assert_called_once()
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_smart_arbitrage(self, handler, mock_update, mock_context, mock_smart_arbitrage):
        """Test stopping smart arbitrage."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_stop"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.stop_arbitrage(mock_update, mock_context)

        mock_smart_arbitrage.stop.assert_called_once()
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_opportunities(self, handler, mock_update, mock_context, mock_smart_arbitrage):
        """Test scanning for opportunities."""
        mock_smart_arbitrage.scan_opportunities.return_value = [
            {"name": "Item 1", "profit": 10.0, "profit_percent": 15.0},
            {"name": "Item 2", "profit": 8.0, "profit_percent": 12.0},
        ]

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_scan"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.scan_opportunities(mock_update, mock_context)

        mock_smart_arbitrage.scan_opportunities.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_no_opportunities(self, handler, mock_update, mock_context, mock_smart_arbitrage):
        """Test scanning with no opportunities found."""
        mock_smart_arbitrage.scan_opportunities.return_value = []

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_scan"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.scan_opportunities(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_get_status(self, handler, mock_update, mock_context, mock_smart_arbitrage):
        """Test getting status."""
        mock_smart_arbitrage.get_status.return_value = {
            "is_running": True,
            "opportunities_found": 5,
            "trades_executed": 2,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_status"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_status(mock_update, mock_context)

        mock_smart_arbitrage.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_configure_settings(self, handler, mock_update, mock_context):
        """Test opening settings menu."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_settings"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_settings(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_set_min_profit(self, handler, mock_update, mock_context):
        """Test setting minimum profit."""
        mock_update.message.text = "15"
        mock_context.user_data["awaiting"] = "min_profit"

        await handler.handle_setting_input(mock_update, mock_context)

        assert mock_context.user_data.get("min_profit") == 15

    @pytest.mark.asyncio
    async def test_execute_opportunity(self, handler, mock_update, mock_context, mock_smart_arbitrage):
        """Test executing an opportunity."""
        mock_smart_arbitrage.execute_opportunity.return_value = {
            "success": True,
            "profit": 5.0,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "smart_arb_execute_123"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        mock_context.user_data["opportunities"] = {
            "123": {"name": "Test Item", "profit": 5.0}
        }

        await handler.execute_opportunity(mock_update, mock_context)

        mock_smart_arbitrage.execute_opportunity.assert_called_once()

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

"""Tests for websocket_handler module.

This module tests the WebSocketHandler class for managing
real-time WebSocket connections via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestWebSocketHandler:
    """Tests for WebSocketHandler class."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket client."""
        ws = MagicMock()
        ws.connect = AsyncMock()
        ws.disconnect = AsyncMock()
        ws.subscribe = AsyncMock()
        ws.unsubscribe = AsyncMock()
        ws.is_connected = False
        ws.get_status = MagicMock(return_value={"is_connected": False})
        return ws

    @pytest.fixture
    def handler(self, mock_websocket):
        """Create WebSocketHandler instance."""
        from src.telegram_bot.handlers.websocket_handler import WebSocketHandler
        return WebSocketHandler(websocket_client=mock_websocket)

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
    async def test_websocket_command(self, handler, mock_update, mock_context):
        """Test /websocket command."""
        await handler.websocket_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing WebSocket menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect(self, handler, mock_update, mock_context, mock_websocket):
        """Test connecting to WebSocket."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_connect"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.connect(mock_update, mock_context)

        mock_websocket.connect.assert_called_once()
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, handler, mock_update, mock_context, mock_websocket):
        """Test disconnecting from WebSocket."""
        mock_websocket.is_connected = True

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_disconnect"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.disconnect(mock_update, mock_context)

        mock_websocket.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_channel(self, handler, mock_update, mock_context, mock_websocket):
        """Test subscribing to channel."""
        mock_websocket.is_connected = True

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_subscribe_prices"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.subscribe(mock_update, mock_context)

        mock_websocket.subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_channel(self, handler, mock_update, mock_context, mock_websocket):
        """Test unsubscribing from channel."""
        mock_websocket.is_connected = True

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_unsubscribe_prices"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.unsubscribe(mock_update, mock_context)

        mock_websocket.unsubscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status(self, handler, mock_update, mock_context, mock_websocket):
        """Test getting status."""
        mock_websocket.get_status.return_value = {
            "is_connected": True,
            "subscriptions": ["prices", "trades"],
            "messages_received": 100,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_status"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_status(mock_update, mock_context)

        mock_websocket.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_subscriptions(self, handler, mock_update, mock_context, mock_websocket):
        """Test showing current subscriptions."""
        mock_websocket.subscriptions = ["prices", "trades", "alerts"]

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_subscriptions"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_subscriptions(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_connect_not_connected_yet(self, handler, mock_update, mock_context, mock_websocket):
        """Test connect when already connected."""
        mock_websocket.is_connected = True

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_connect"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.connect(mock_update, mock_context)

        # Should show already connected message

    @pytest.mark.asyncio
    async def test_handle_connection_error(self, handler, mock_update, mock_context, mock_websocket):
        """Test handling connection error."""
        mock_websocket.connect.side_effect = Exception("Connection failed")

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "ws_connect"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.connect(mock_update, mock_context)

        # Should handle error gracefully

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

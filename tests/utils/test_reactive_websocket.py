"""Tests for reactive_websocket module.

This module tests the ReactiveWebSocket class for real-time
market data streaming.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.utils.reactive_websocket import ReactiveWebSocket


class TestReactiveWebSocket:
    """Tests for ReactiveWebSocket class."""

    @pytest.fixture
    def websocket(self):
        """Create ReactiveWebSocket instance."""
        return ReactiveWebSocket(url="wss://test.example.com/ws")

    def test_init(self, websocket):
        """Test initialization."""
        assert websocket.url == "wss://test.example.com/ws"
        assert websocket.is_connected is False

    def test_init_with_options(self):
        """Test initialization with options."""
        ws = ReactiveWebSocket(
            url="wss://test.example.com/ws",
            reconnect_interval=5.0,
            max_reconnects=10,
        )

        assert ws.reconnect_interval == 5.0
        assert ws.max_reconnects == 10

    @pytest.mark.asyncio
    async def test_connect(self, websocket):
        """Test connecting to WebSocket."""
        with patch("src.utils.reactive_websocket.websockets") as mock_ws:
            mock_connection = MagicMock()
            mock_ws.connect = AsyncMock(return_value=mock_connection)

            await websocket.connect()

            assert websocket.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self, websocket):
        """Test disconnecting from WebSocket."""
        websocket.is_connected = True
        websocket.connection = MagicMock()
        websocket.connection.close = AsyncMock()

        await websocket.disconnect()

        assert websocket.is_connected is False

    @pytest.mark.asyncio
    async def test_subscribe(self, websocket):
        """Test subscribing to channel."""
        websocket.is_connected = True
        websocket.connection = MagicMock()
        websocket.connection.send = AsyncMock()

        await websocket.subscribe("price_updates")

        websocket.connection.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe(self, websocket):
        """Test unsubscribing from channel."""
        websocket.is_connected = True
        websocket.connection = MagicMock()
        websocket.connection.send = AsyncMock()

        await websocket.unsubscribe("price_updates")

        websocket.connection.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message(self, websocket):
        """Test sending message."""
        websocket.is_connected = True
        websocket.connection = MagicMock()
        websocket.connection.send = AsyncMock()

        await websocket.send({"type": "ping"})

        websocket.connection.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_message(self, websocket):
        """Test receiving message."""
        websocket.is_connected = True
        websocket.connection = MagicMock()
        websocket.connection.recv = AsyncMock(return_value='{"type": "price_update", "price": 10.0}')

        message = await websocket.receive()

        assert message["type"] == "price_update"
        assert message["price"] == 10.0

    @pytest.mark.asyncio
    async def test_reconnect(self, websocket):
        """Test reconnection logic."""
        websocket.reconnect_count = 0

        with patch.object(websocket, "connect", new_callable=AsyncMock):
            await websocket.reconnect()

            websocket.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_max_reconnects_exceeded(self, websocket):
        """Test max reconnects exceeded."""
        websocket.reconnect_count = websocket.max_reconnects + 1

        with pytest.raises(ConnectionError):
            await websocket.reconnect()

    def test_add_handler(self, websocket):
        """Test adding message handler."""
        handler = AsyncMock()

        websocket.add_handler("price_update", handler)

        assert "price_update" in websocket.handlers

    def test_remove_handler(self, websocket):
        """Test removing message handler."""
        handler = AsyncMock()
        websocket.handlers["price_update"] = handler

        websocket.remove_handler("price_update")

        assert "price_update" not in websocket.handlers

    @pytest.mark.asyncio
    async def test_handle_message(self, websocket):
        """Test handling incoming message."""
        handler = AsyncMock()
        websocket.handlers["price_update"] = handler

        message = {"type": "price_update", "price": 10.0}
        await websocket._handle_message(message)

        handler.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_heartbeat(self, websocket):
        """Test heartbeat mechanism."""
        websocket.is_connected = True
        websocket.connection = MagicMock()
        websocket.connection.ping = AsyncMock()

        await websocket._send_heartbeat()

        websocket.connection.ping.assert_called_once()

    def test_get_status(self, websocket):
        """Test getting status."""
        status = websocket.get_status()

        assert isinstance(status, dict)
        assert "is_connected" in status
        assert "url" in status

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        with patch("src.utils.reactive_websocket.websockets") as mock_ws:
            mock_connection = MagicMock()
            mock_connection.close = AsyncMock()
            mock_ws.connect = AsyncMock(return_value=mock_connection)

            async with ReactiveWebSocket("wss://test.example.com/ws") as ws:
                assert ws.is_connected is True

            assert ws.is_connected is False

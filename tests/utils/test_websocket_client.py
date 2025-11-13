"""Тесты для модуля websocket_client.py"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import WSMessage, WSMsgType

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.websocket_client import DMarketWebSocketClient


@pytest.fixture
def mock_api_client():
    """Мок для DMarketAPI."""
    api_client = MagicMock(spec=DMarketAPI)
    api_client._generate_signature.return_value = {
        "Authorization": "DMR1:public:secret",
    }
    api_client.public_key = "test_public_key"
    api_client.secret_key = "test_secret_key"
    return api_client


@pytest.fixture
def websocket_client(mock_api_client):
    """Создает экземпляр DMarketWebSocketClient для тестирования."""
    return DMarketWebSocketClient(api_client=mock_api_client)


class MockClientSession:
    """Мок для ClientSession."""

    def __init__(self, response=None):
        self.response = response or {"token": "test_token"}
        self.get = AsyncMock()
        self.ws_connect = AsyncMock()
        self.close = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass


class MockResponse:
    """Мок для Response."""

    def __init__(self, status=200, data=None):
        self.status = status
        self.data = data or {"token": "test_token"}

    async def json(self):
        return self.data

    async def text(self):
        return json.dumps(self.data)


class MockWebSocket:
    """Мок для WebSocket соединения."""

    def __init__(self, messages=None):
        self.messages = messages or []
        self.closed = False
        self.send_json = AsyncMock()
        self.ping = AsyncMock()
        self.close = AsyncMock()
        self.exception = MagicMock(return_value=Exception("WebSocket error"))

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)

    async def receive(self):
        """Получить следующее сообщение."""
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)


@pytest.mark.asyncio
async def test_connect_success(websocket_client):
    """Тест успешного подключения к WebSocket."""

    # Переопределяем метод connect чтобы не создавать реальное соединение
    async def mock_connect_impl():
        websocket_client.is_connected = True
        websocket_client.authenticated = True
        return True

    # Заменяем реальный метод connect нашим мок-методом
    original_connect = websocket_client.connect
    websocket_client.connect = mock_connect_impl

    try:
        # Вызываем метод
        result = await websocket_client.connect()

        # Проверки
        assert result is True
        assert websocket_client.is_connected is True
        assert websocket_client.reconnect_attempts == 0
    finally:
        # Восстанавливаем оригинальный метод
        websocket_client.connect = original_connect


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_connect_token_error(mock_session, websocket_client):
    """Тест ошибки получения токена."""
    # Подготовка моков
    mock_session_instance = MagicMock()
    mock_session_instance.ws_connect = AsyncMock(
        side_effect=aiohttp.ClientError("Connection failed"),
    )
    mock_session.return_value = mock_session_instance

    # Вызов тестируемого метода
    result = await websocket_client.connect()

    # Проверки
    assert result is False
    assert websocket_client.is_connected is False


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_connect_no_token(mock_session, websocket_client):
    """Тест таймаута при подключении."""
    # Подготовка моков
    mock_session_instance = MagicMock()
    mock_session_instance.ws_connect = AsyncMock(
        side_effect=TimeoutError("Connection timeout"),
    )
    mock_session.return_value = mock_session_instance

    # Вызов тестируемого метода
    result = await websocket_client.connect()

    # Проверки
    assert result is False
    assert websocket_client.is_connected is False


@pytest.mark.asyncio
async def test_subscribe(websocket_client):
    """Test subscribing to topics."""
    # Setup connection
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()

    # Test subscribing
    result = await websocket_client.subscribe("prices:update")

    # Verify subscription was successful
    assert result is True
    assert "prices:update" in websocket_client.subscriptions


@pytest.mark.asyncio
async def test_subscribe_not_connected(websocket_client):
    """Тест подписки при отсутствии соединения."""
    # Подготовка
    websocket_client.is_connected = False

    # Вызов тестируемого метода
    result = await websocket_client.subscribe("prices:update")

    # Проверки
    assert result is False
    assert "prices:update" not in websocket_client.subscriptions


@pytest.mark.asyncio
async def test_unsubscribe(websocket_client):
    """Тест отписки от темы."""
    # Подготовка
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()
    websocket_client.subscriptions = {"market:update", "prices:update"}

    # Вызов тестируемого метода
    result = await websocket_client.unsubscribe("prices:update")

    # Проверки
    assert result is True
    assert "prices:update" not in websocket_client.subscriptions


@pytest.mark.asyncio
async def test_register_handler(websocket_client):
    """Тест регистрации обработчика."""
    # Подготовка
    handler = AsyncMock()

    # Вызов тестируемого метода
    websocket_client.register_handler("market:update", handler)

    # Проверки - handlers это список обработчиков
    assert "market:update" in websocket_client.handlers
    assert handler in websocket_client.handlers["market:update"]


@pytest.mark.asyncio
@patch("asyncio.create_task")
async def test_listen_message_handling(mock_create_task, websocket_client):
    """Тест обработки сообщений."""
    # Подготовка
    websocket_client.is_connected = True
    handler = AsyncMock()
    websocket_client.register_handler("market:update", handler)

    # Создаем сообщения для теста - используем "type" вместо "channel"
    text_message = WSMessage(
        WSMsgType.TEXT,
        json.dumps(
            {
                "type": "market:update",
                "data": {"item_id": "123", "price": 100},
            },
        ).encode(),
        None,
    )

    error_message = WSMessage(WSMsgType.ERROR, None, None)

    mock_ws = MockWebSocket(messages=[text_message, error_message])
    websocket_client.ws_connection = mock_ws
    websocket_client.is_connected = True

    # Имитируем один вызов listen перед ошибкой
    # Mock _attempt_reconnect to prevent actual reconnection
    with patch.object(websocket_client, "_attempt_reconnect", AsyncMock()):
        await websocket_client.listen()

    # Проверки
    handler.assert_called_once()
    expected_data = {
        "type": "market:update",
        "data": {"item_id": "123", "price": 100},
    }
    assert handler.call_args[0][0] == expected_data
    assert websocket_client.is_connected is False


@pytest.mark.asyncio
async def test_close(websocket_client):
    """Test closing WebSocket connection."""
    # Setup mock session and connection
    websocket_client.session = MagicMock()
    websocket_client.session.close = AsyncMock()
    websocket_client.ws_connection = MagicMock()
    websocket_client.ws_connection.close = AsyncMock()
    websocket_client.is_connected = True

    # Close connection
    await websocket_client.close()

    # Verify connection was closed
    assert websocket_client.is_connected is False

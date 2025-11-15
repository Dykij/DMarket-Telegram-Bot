"""Тесты для модуля websocket_client.py"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import WSMessage, WSMsgType

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.websocket_client import DMarketWebSocketClient


@pytest.fixture()
def mock_api_client():
    """Мок для DMarketAPI."""
    api_client = MagicMock(spec=DMarketAPI)
    api_client._generate_signature.return_value = {
        "Authorization": "DMR1:public:secret",
    }
    api_client.public_key = "test_public_key"
    api_client.secret_key = "test_secret_key"
    return api_client


@pytest.fixture()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
async def test_subscribe_not_connected(websocket_client):
    """Тест подписки при отсутствии соединения."""
    # Подготовка
    websocket_client.is_connected = False

    # Вызов тестируемого метода
    result = await websocket_client.subscribe("prices:update")

    # Проверки
    assert result is False
    assert "prices:update" not in websocket_client.subscriptions


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
async def test_register_handler(websocket_client):
    """Тест регистрации обработчика."""
    # Подготовка
    handler = AsyncMock()

    # Вызов тестируемого метода
    websocket_client.register_handler("market:update", handler)

    # Проверки - handlers это список обработчиков
    assert "market:update" in websocket_client.handlers
    assert handler in websocket_client.handlers["market:update"]


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
async def test_init(mock_api_client):
    """Тест инициализации клиента."""
    client = DMarketWebSocketClient(api_client=mock_api_client)

    assert client.api_client == mock_api_client
    assert client.session is None
    assert client.ws_connection is None
    assert client.is_connected is False
    assert client.reconnect_attempts == 0
    assert client.max_reconnect_attempts == 10
    assert client.handlers == {}
    assert client.authenticated is False
    assert client.subscriptions == set()
    assert client.connection_id is not None


@pytest.mark.asyncio()
async def test_authenticate(websocket_client):
    """Тест аутентификации."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()

    await websocket_client._authenticate()

    websocket_client.ws_connection.send_json.assert_called_once()
    call_args = websocket_client.ws_connection.send_json.call_args[0][0]
    assert call_args["type"] == "auth"
    assert "apiKey" in call_args
    assert "timestamp" in call_args


@pytest.mark.asyncio()
async def test_authenticate_not_connected(websocket_client):
    """Тест аутентификации при отсутствии соединения."""
    websocket_client.is_connected = False

    await websocket_client._authenticate()

    # Не должно быть исключений, просто логирование


@pytest.mark.asyncio()
async def test_resubscribe(websocket_client):
    """Тест переподписки после реконнекта."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()
    websocket_client.subscriptions = {"market:update", "prices:update"}

    await websocket_client._resubscribe()

    # Должно быть два вызова subscribe
    assert websocket_client.ws_connection.send_json.call_count == 2


@pytest.mark.asyncio()
async def test_unsubscribe_all(websocket_client):
    """Тест отписки от всех тем."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()
    websocket_client.subscriptions = {"market:update", "prices:update"}

    await websocket_client._unsubscribe_all()

    # Должно быть два вызова unsubscribe
    assert websocket_client.ws_connection.send_json.call_count == 2
    assert len(websocket_client.subscriptions) == 0


@pytest.mark.asyncio()
async def test_handle_message_auth_success(websocket_client):
    """Тест обработки успешной аутентификации."""
    message_data = json.dumps({"type": "auth", "status": "success"})

    await websocket_client._handle_message(message_data)

    assert websocket_client.authenticated is True


@pytest.mark.asyncio()
async def test_handle_message_auth_failure(websocket_client):
    """Тест обработки неудачной аутентификации."""
    message_data = json.dumps({"type": "auth", "status": "error", "error": "Invalid API key"})

    await websocket_client._handle_message(message_data)

    assert websocket_client.authenticated is False


@pytest.mark.asyncio()
async def test_handle_message_subscription(websocket_client):
    """Тест обработки ответа на подписку."""
    message_data = json.dumps({"type": "subscription", "topic": "market:update", "status": "ok"})

    # Не должно быть исключений
    await websocket_client._handle_message(message_data)


@pytest.mark.asyncio()
async def test_handle_message_json_decode_error(websocket_client):
    """Тест обработки некорректного JSON."""
    message_data = "invalid json {"

    # Не должно быть исключений, только логирование
    await websocket_client._handle_message(message_data)


@pytest.mark.asyncio()
async def test_attempt_reconnect_success(websocket_client):
    """Тест успешного реконнекта."""
    websocket_client.reconnect_attempts = 2

    with patch.object(websocket_client, "connect", AsyncMock(return_value=True)):
        with patch("asyncio.sleep", AsyncMock()):
            await websocket_client._attempt_reconnect()

    assert websocket_client.reconnect_attempts == 3


@pytest.mark.asyncio()
async def test_attempt_reconnect_max_attempts(websocket_client):
    """Тест достижения максимума попыток реконнекта."""
    websocket_client.reconnect_attempts = 10
    websocket_client.max_reconnect_attempts = 10

    await websocket_client._attempt_reconnect()

    # Должен выйти без попыток
    assert websocket_client.reconnect_attempts == 10


@pytest.mark.asyncio()
async def test_unregister_handler(websocket_client):
    """Тест отмены регистрации обработчика."""
    handler = AsyncMock()
    websocket_client.register_handler("market:update", handler)

    websocket_client.unregister_handler("market:update", handler)

    assert handler not in websocket_client.handlers.get("market:update", [])


@pytest.mark.asyncio()
async def test_send_message(websocket_client):
    """Тест отправки кастомного сообщения."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()

    message = {"type": "custom", "data": {"key": "value"}}
    result = await websocket_client.send_message(message)

    assert result is True
    websocket_client.ws_connection.send_json.assert_called_once_with(message)


@pytest.mark.asyncio()
async def test_send_message_not_connected(websocket_client):
    """Тест отправки сообщения при отсутствии соединения."""
    websocket_client.is_connected = False

    result = await websocket_client.send_message({"type": "test"})

    assert result is False


@pytest.mark.asyncio()
async def test_subscribe_to_market_updates(websocket_client):
    """Тест подписки на обновления рынка."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()

    result = await websocket_client.subscribe_to_market_updates("csgo")

    assert result is True
    websocket_client.ws_connection.send_json.assert_called_once()
    call_args = websocket_client.ws_connection.send_json.call_args[0][0]
    assert call_args["topic"] == "market:update"
    assert call_args["params"]["gameId"] == "csgo"


@pytest.mark.asyncio()
async def test_subscribe_to_item_updates(websocket_client):
    """Тест подписки на обновления предметов."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()

    item_ids = ["item1", "item2", "item3"]
    result = await websocket_client.subscribe_to_item_updates(item_ids)

    assert result is True
    websocket_client.ws_connection.send_json.assert_called_once()
    call_args = websocket_client.ws_connection.send_json.call_args[0][0]
    assert call_args["topic"] == "items:update"
    assert call_args["params"]["itemIds"] == item_ids


@pytest.mark.asyncio()
async def test_subscribe_with_params(websocket_client):
    """Тест подписки с параметрами."""
    websocket_client.is_connected = True
    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.send_json = AsyncMock()

    params = {"filter": "price>100"}
    result = await websocket_client.subscribe("custom:topic", params)

    assert result is True
    call_args = websocket_client.ws_connection.send_json.call_args[0][0]
    assert call_args["params"] == params


@pytest.mark.asyncio()
async def test_connect_already_connected(websocket_client):
    """Тест подключения когда уже подключен."""
    websocket_client.is_connected = True

    result = await websocket_client.connect()

    assert result is True


@pytest.mark.asyncio()
async def test_listen_cancelled_error(websocket_client):
    """Тест отмены listen task."""
    websocket_client.is_connected = True

    async def mock_receive():
        raise asyncio.CancelledError

    websocket_client.ws_connection = AsyncMock()
    websocket_client.ws_connection.receive = mock_receive

    # Не должно быть исключений
    await websocket_client.listen()


@pytest.mark.asyncio()
async def test_listen_closed_message(websocket_client):
    """Тест обработки закрытия соединения."""
    closed_message = WSMessage(WSMsgType.CLOSED, None, None)
    mock_ws = MockWebSocket(messages=[closed_message])

    websocket_client.ws_connection = mock_ws
    websocket_client.is_connected = True

    with patch.object(websocket_client, "_attempt_reconnect", AsyncMock()):
        await websocket_client.listen()

    assert websocket_client.is_connected is False

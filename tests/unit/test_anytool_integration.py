"""
Тесты для модуля anytool_integration.

Проверяет функциональность интеграции с AnyTool через MCP.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.anytool_integration import (
    AnyToolClient,
    AnyToolConfig,
    get_anytool_client,
    initialize_anytool,
)


@pytest.fixture()
def mock_api_client():
    """Фикстура для мокированного API клиента."""
    client = AsyncMock(spec=DMarketAPI)
    client.get_balance = AsyncMock(return_value={"usd": "10000", "dmc": "5000"})
    client.get_market_items = AsyncMock(
        return_value={
            "objects": [
                {"title": "Test Item", "price": {"USD": "1000"}},
            ]
        }
    )
    client.get_item_by_id = AsyncMock(return_value={"title": "Test Item", "price": {"USD": "1000"}})
    return client


@pytest.fixture()
def anytool_config():
    """Фикстура для конфигурации AnyTool."""
    return AnyToolConfig(
        mcp_server_path="src.mcp_server.dmarket_mcp:main",
        timeout=30,
        max_retries=3,
        enabled=True,
    )


@pytest.fixture()
def anytool_client(mock_api_client, anytool_config):
    """Фикстура для AnyTool клиента."""
    return AnyToolClient(config=anytool_config, api_client=mock_api_client)


class TestAnyToolConfig:
    """Тесты для конфигурации AnyTool."""

    def test_default_config_values(self):
        """Тест значений по умолчанию."""
        config = AnyToolConfig()
        assert config.mcp_server_path == "src.mcp_server.dmarket_mcp:main"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.enabled is True

    def test_custom_config_values(self):
        """Тест пользовательских значений конфигурации."""
        config = AnyToolConfig(
            mcp_server_path="custom.path:main",
            timeout=60,
            max_retries=5,
            enabled=False,
        )
        assert config.mcp_server_path == "custom.path:main"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.enabled is False


class TestAnyToolClient:
    """Тесты для AnyTool клиента."""

    def test_client_initialization_with_config(self, anytool_config, mock_api_client):
        """Тест инициализации с конфигурацией."""
        client = AnyToolClient(config=anytool_config, api_client=mock_api_client)
        assert client.config == anytool_config
        assert client.api_client == mock_api_client

    def test_client_initialization_without_config(self):
        """Тест инициализации без конфигурации."""
        with patch("src.utils.anytool_integration.DMarketAPI") as mock_api:
            client = AnyToolClient()
            assert isinstance(client.config, AnyToolConfig)
            mock_api.assert_called_once()

    def test_register_callback(self, anytool_client):
        """Тест регистрации callback."""

        def test_callback(data):
            pass

        anytool_client.register_callback("test_event", test_callback)
        assert "test_event" in anytool_client._callbacks
        assert test_callback in anytool_client._callbacks["test_event"]

    @pytest.mark.asyncio()
    async def test_trigger_callbacks_with_sync_callback(self, anytool_client):
        """Тест запуска синхронных callbacks."""
        callback_called = False

        def test_callback(data):
            nonlocal callback_called
            callback_called = True
            assert data == {"test": "data"}

        anytool_client.register_callback("test_event", test_callback)
        await anytool_client._trigger_callbacks("test_event", {"test": "data"})
        assert callback_called

    @pytest.mark.asyncio()
    async def test_trigger_callbacks_with_async_callback(self, anytool_client):
        """Тест запуска асинхронных callbacks."""
        callback_called = False

        async def test_callback(data):
            nonlocal callback_called
            callback_called = True
            assert data == {"test": "data"}

        anytool_client.register_callback("test_event", test_callback)
        await anytool_client._trigger_callbacks("test_event", {"test": "data"})
        assert callback_called

    @pytest.mark.asyncio()
    async def test_call_tool_when_disabled(self, anytool_client):
        """Тест вызова инструмента когда интеграция отключена."""
        anytool_client.config.enabled = False

        with pytest.raises(ValueError, match="AnyTool integration is disabled"):
            await anytool_client.call_tool("get_balance", {})

    @pytest.mark.asyncio()
    async def test_call_tool_get_balance(self, anytool_client, mock_api_client):
        """Тест вызова get_balance через AnyTool."""
        result = await anytool_client.call_tool("get_balance", {})

        assert result["success"] is True
        assert "balance" in result
        mock_api_client.get_balance.assert_called_once()

    @pytest.mark.asyncio()
    async def test_call_tool_get_market_items(self, anytool_client, mock_api_client):
        """Тест вызова get_market_items через AnyTool."""
        result = await anytool_client.call_tool(
            "get_market_items",
            {
                "game": "csgo",
                "limit": 10,
                "price_from": 100,
                "price_to": 1000,
            },
        )

        assert result["success"] is True
        assert "items" in result
        mock_api_client.get_market_items.assert_called_once_with(
            game="csgo",
            limit=10,
            price_from=100,
            price_to=1000,
        )

    @pytest.mark.asyncio()
    async def test_call_tool_scan_arbitrage(self, anytool_client):
        """Тест вызова scan_arbitrage через AnyTool."""
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner_class:
            mock_scanner = AsyncMock()
            mock_scanner.scan_level = AsyncMock(
                return_value=[
                    {"item": "Test", "profit": 1.5},
                    {"item": "Test2", "profit": 0.3},
                ]
            )
            mock_scanner_class.return_value = mock_scanner

            result = await anytool_client.call_tool(
                "scan_arbitrage",
                {
                    "game": "csgo",
                    "level": "standard",
                    "min_profit": 1.0,
                },
            )

            assert result["success"] is True
            assert len(result["opportunities"]) == 1
            assert result["opportunities"][0]["profit"] == 1.5

    @pytest.mark.asyncio()
    async def test_call_tool_get_item_details(self, anytool_client, mock_api_client):
        """Тест вызова get_item_details через AnyTool."""
        result = await anytool_client.call_tool(
            "get_item_details",
            {"item_id": "test_item_123"},
        )

        assert result["success"] is True
        assert "item" in result
        mock_api_client.get_item_by_id.assert_called_once_with("test_item_123")

    @pytest.mark.asyncio()
    async def test_call_tool_create_target(self, anytool_client):
        """Тест вызова create_target через AnyTool."""
        with patch("src.dmarket.targets.TargetManager") as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.create_target = AsyncMock(return_value={"target_id": "test_target_123"})
            mock_tm_class.return_value = mock_tm

            result = await anytool_client.call_tool(
                "create_target",
                {
                    "game": "csgo",
                    "title": "AK-47 | Redline",
                    "price": 10.5,
                    "amount": 2,
                },
            )

            assert result["success"] is True
            assert "target" in result
            mock_tm.create_target.assert_called_once_with(
                game="csgo",
                title="AK-47 | Redline",
                price=10.5,
                amount=2,
            )

    @pytest.mark.asyncio()
    async def test_call_tool_get_targets(self, anytool_client):
        """Тест вызова get_targets через AnyTool."""
        with patch("src.dmarket.targets.TargetManager") as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.get_all_targets = AsyncMock(
                return_value=[
                    {"id": "1", "title": "Target 1"},
                    {"id": "2", "title": "Target 2"},
                ]
            )
            mock_tm_class.return_value = mock_tm

            result = await anytool_client.call_tool("get_targets", {})

            assert result["success"] is True
            assert len(result["targets"]) == 2

    @pytest.mark.asyncio()
    async def test_call_tool_unknown_tool(self, anytool_client):
        """Тест вызова неизвестного инструмента."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await anytool_client.call_tool("unknown_tool", {})

    @pytest.mark.asyncio()
    async def test_get_available_tools(self, anytool_client):
        """Тест получения списка доступных инструментов."""
        tools = await anytool_client.get_available_tools()

        assert len(tools) == 6
        tool_names = [tool["name"] for tool in tools]
        assert "get_balance" in tool_names
        assert "get_market_items" in tool_names
        assert "scan_arbitrage" in tool_names

    def test_export_config(self, anytool_client, tmp_path):
        """Тест экспорта конфигурации."""
        config_path = tmp_path / "config_mcp.json"

        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket_public_key = "test_public_key"
            mock_settings.dmarket_secret_key = "test_secret_key"

            anytool_client.export_config(config_path)

        assert config_path.exists()

        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "dmarket-bot" in config["mcpServers"]
        assert config["mcpServers"]["dmarket-bot"]["command"] == "python"


class TestGlobalClient:
    """Тесты для глобального клиента."""

    def test_get_anytool_client_returns_singleton(self):
        """Тест получения singleton экземпляра."""
        client1 = get_anytool_client()
        client2 = get_anytool_client()
        assert client1 is client2

    @pytest.mark.asyncio()
    async def test_initialize_anytool(self, tmp_path):
        """Тест инициализации AnyTool."""
        config_path = tmp_path / "config_mcp.json"

        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket_public_key = "test_key"
            mock_settings.dmarket_secret_key = "test_secret"

            client = await initialize_anytool(config_path)

        assert isinstance(client, AnyToolClient)
        assert config_path.exists()

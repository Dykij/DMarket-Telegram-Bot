"""Unit tests for src/utils/anytool_integration.py.

Tests for AnyTool MCP integration including:
- AnyToolConfig model
- AnyToolClient class
- Tool execution methods
- Callback registration
- Configuration export
- Global client management
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAnyToolConfig:
    """Tests for AnyToolConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        from src.utils.anytool_integration import AnyToolConfig

        config = AnyToolConfig()
        assert config.mcp_server_path == "src.mcp_server.dmarket_mcp:main"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.enabled is True

    def test_custom_values(self):
        """Test custom configuration values."""
        from src.utils.anytool_integration import AnyToolConfig

        config = AnyToolConfig(
            mcp_server_path="custom.path:run",
            timeout=60,
            max_retries=5,
            enabled=False,
        )
        assert config.mcp_server_path == "custom.path:run"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.enabled is False

    def test_partial_custom_values(self):
        """Test configuration with partial custom values."""
        from src.utils.anytool_integration import AnyToolConfig

        config = AnyToolConfig(timeout=120)
        assert config.timeout == 120
        # Other values should be default
        assert config.mcp_server_path == "src.mcp_server.dmarket_mcp:main"


class TestAnyToolClientInit:
    """Tests for AnyToolClient initialization."""

    def test_init_with_defaults(self):
        """Test client initialization with default values."""
        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket.public_key = "test_public"
            mock_settings.dmarket.secret_key = "test_secret"

            from src.utils.anytool_integration import AnyToolClient

            client = AnyToolClient()
            assert client.config is not None
            assert client.api_client is not None
            assert client._callbacks == {}

    def test_init_with_custom_config(self):
        """Test client initialization with custom config."""
        from src.utils.anytool_integration import AnyToolClient, AnyToolConfig

        config = AnyToolConfig(timeout=120, enabled=False)
        mock_api = MagicMock()

        client = AnyToolClient(config=config, api_client=mock_api)
        assert client.config.timeout == 120
        assert client.config.enabled is False
        assert client.api_client is mock_api

    def test_init_with_custom_api_client(self):
        """Test client initialization with custom API client."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)
        assert client.api_client is mock_api


class TestCallbackRegistration:
    """Tests for callback registration."""

    def test_register_callback(self):
        """Test registering a callback for an event."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback = MagicMock()
        client.register_callback("tool_called", callback)

        assert "tool_called" in client._callbacks
        assert callback in client._callbacks["tool_called"]

    def test_register_multiple_callbacks_same_event(self):
        """Test registering multiple callbacks for the same event."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback1 = MagicMock()
        callback2 = MagicMock()

        client.register_callback("tool_called", callback1)
        client.register_callback("tool_called", callback2)

        assert len(client._callbacks["tool_called"]) == 2

    def test_register_callbacks_different_events(self):
        """Test registering callbacks for different events."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback1 = MagicMock()
        callback2 = MagicMock()

        client.register_callback("event1", callback1)
        client.register_callback("event2", callback2)

        assert "event1" in client._callbacks
        assert "event2" in client._callbacks


class TestTriggerCallbacks:
    """Tests for _trigger_callbacks method."""

    @pytest.mark.asyncio
    async def test_trigger_sync_callback(self):
        """Test triggering a synchronous callback."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback = MagicMock()
        client.register_callback("test_event", callback)

        await client._trigger_callbacks("test_event", {"data": "test"})

        callback.assert_called_once_with({"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_async_callback(self):
        """Test triggering an asynchronous callback."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback = AsyncMock()
        client.register_callback("test_event", callback)

        await client._trigger_callbacks("test_event", {"data": "test"})

        callback.assert_called_once_with({"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_handles_callback_error(self):
        """Test that callback errors are handled gracefully."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        failing_callback = MagicMock(side_effect=Exception("Callback error"))
        client.register_callback("test_event", failing_callback)

        # Should not raise exception
        await client._trigger_callbacks("test_event", {"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_event(self):
        """Test triggering callbacks for an event with no callbacks."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        # Should not raise exception
        await client._trigger_callbacks("nonexistent_event", {"data": "test"})


class TestCallTool:
    """Tests for call_tool method."""

    @pytest.mark.asyncio
    async def test_call_tool_when_disabled(self):
        """Test that call_tool raises when integration is disabled."""
        from src.utils.anytool_integration import AnyToolClient, AnyToolConfig

        config = AnyToolConfig(enabled=False)
        mock_api = MagicMock()
        client = AnyToolClient(config=config, api_client=mock_api)

        with pytest.raises(ValueError, match="AnyTool integration is disabled"):
            await client.call_tool("get_balance", {})

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_balance = AsyncMock(return_value={"usd": "1000", "dmc": "500"})

        client = AnyToolClient(api_client=mock_api)

        result = await client.call_tool("get_balance", {})

        assert result["success"] is True
        assert result["balance"] == {"usd": "1000", "dmc": "500"}

    @pytest.mark.asyncio
    async def test_call_tool_triggers_callback(self):
        """Test that call_tool triggers callbacks."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_balance = AsyncMock(return_value={"usd": "1000"})

        client = AnyToolClient(api_client=mock_api)

        callback = MagicMock()
        client.register_callback("tool_called", callback)

        await client.call_tool("get_balance", {})

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["tool"] == "get_balance"

    @pytest.mark.asyncio
    async def test_call_tool_raises_on_error(self):
        """Test that call_tool raises on execution error."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_balance = AsyncMock(side_effect=Exception("API error"))

        client = AnyToolClient(api_client=mock_api)

        with pytest.raises(Exception, match="API error"):
            await client.call_tool("get_balance", {})


class TestExecuteTool:
    """Tests for _execute_tool method."""

    @pytest.mark.asyncio
    async def test_execute_get_balance(self):
        """Test executing get_balance tool."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_balance = AsyncMock(return_value={"usd": "1000", "dmc": "500"})

        client = AnyToolClient(api_client=mock_api)

        result = await client._execute_tool("get_balance", {})

        assert result["success"] is True
        assert result["balance"]["usd"] == "1000"

    @pytest.mark.asyncio
    async def test_execute_get_market_items(self):
        """Test executing get_market_items tool."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(
            return_value={"objects": [{"name": "Item1"}, {"name": "Item2"}]}
        )

        client = AnyToolClient(api_client=mock_api)

        result = await client._execute_tool(
            "get_market_items",
            {"game": "csgo", "limit": 10},
        )

        assert result["success"] is True
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_execute_scan_arbitrage(self):
        """Test executing scan_arbitrage tool."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()

        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as MockScanner:
            mock_scanner = AsyncMock()
            mock_scanner.scan_level = AsyncMock(
                return_value=[
                    {"item": "Item1", "profit": 1.5},
                    {"item": "Item2", "profit": 0.3},
                ]
            )
            MockScanner.return_value = mock_scanner

            client = AnyToolClient(api_client=mock_api)

            result = await client._execute_tool(
                "scan_arbitrage",
                {"game": "csgo", "level": "standard", "min_profit": 0.5},
            )

            assert result["success"] is True
            # Should filter out items with profit < 0.5
            assert len(result["opportunities"]) == 1
            assert result["opportunities"][0]["profit"] == 1.5

    @pytest.mark.asyncio
    async def test_execute_get_item_details(self):
        """Test executing get_item_details tool."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_item_by_id = AsyncMock(return_value={"id": "123", "name": "Test Item"})

        client = AnyToolClient(api_client=mock_api)

        result = await client._execute_tool(
            "get_item_details",
            {"item_id": "123"},
        )

        assert result["success"] is True
        assert result["item"]["id"] == "123"

    @pytest.mark.asyncio
    async def test_execute_create_target(self):
        """Test executing create_target tool."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()

        with patch("src.dmarket.targets.TargetManager") as MockTargetManager:
            mock_tm = AsyncMock()
            mock_tm.create_target = AsyncMock(return_value={"id": "target_123"})
            MockTargetManager.return_value = mock_tm

            client = AnyToolClient(api_client=mock_api)

            result = await client._execute_tool(
                "create_target",
                {"game": "csgo", "title": "Test Item", "price": 10.0, "amount": 1},
            )

            assert result["success"] is True
            assert result["target"]["id"] == "target_123"

    @pytest.mark.asyncio
    async def test_execute_get_targets(self):
        """Test executing get_targets tool."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()

        with patch("src.dmarket.targets.TargetManager") as MockTargetManager:
            mock_tm = AsyncMock()
            mock_tm.get_all_targets = AsyncMock(
                return_value=[{"id": "target_1"}, {"id": "target_2"}]
            )
            MockTargetManager.return_value = mock_tm

            client = AnyToolClient(api_client=mock_api)

            result = await client._execute_tool("get_targets", {})

            assert result["success"] is True
            assert len(result["targets"]) == 2

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing an unknown tool raises error."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        client = AnyToolClient(api_client=mock_api)

        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            await client._execute_tool("unknown_tool", {})


class TestGetAvailableTools:
    """Tests for get_available_tools method."""

    @pytest.mark.asyncio
    async def test_returns_list_of_tools(self):
        """Test that get_available_tools returns a list."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        tools = await client.get_available_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_tools_have_required_fields(self):
        """Test that all tools have required fields."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        tools = await client.get_available_tools()

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

    @pytest.mark.asyncio
    async def test_contains_expected_tools(self):
        """Test that expected tools are in the list."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        tools = await client.get_available_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = [
            "get_balance",
            "get_market_items",
            "scan_arbitrage",
            "get_item_details",
            "create_target",
            "get_targets",
        ]

        for expected in expected_tools:
            assert expected in tool_names


class TestExportConfig:
    """Tests for export_config method."""

    def test_export_creates_file(self, tmp_path):
        """Test that export_config creates a config file."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        config_path = tmp_path / "config.json"

        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket_public_key = "test_public"
            mock_settings.dmarket_secret_key = "test_secret"

            client.export_config(config_path)

        assert config_path.exists()

    def test_export_creates_parent_dirs(self, tmp_path):
        """Test that export_config creates parent directories."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        config_path = tmp_path / "nested" / "dir" / "config.json"

        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket_public_key = "test_public"
            mock_settings.dmarket_secret_key = "test_secret"

            client.export_config(config_path)

        assert config_path.exists()

    def test_export_contains_mcp_servers(self, tmp_path):
        """Test that exported config contains mcpServers section."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        config_path = tmp_path / "config.json"

        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket_public_key = "test_public"
            mock_settings.dmarket_secret_key = "test_secret"

            client.export_config(config_path)

        with open(config_path) as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "dmarket-bot" in config["mcpServers"]


class TestGlobalClientManagement:
    """Tests for global client management functions."""

    def test_get_anytool_client_returns_singleton(self):
        """Test that get_anytool_client returns a singleton."""
        with patch("src.utils.anytool_integration._anytool_client", None):
            with patch("src.utils.anytool_integration.settings") as mock_settings:
                mock_settings.dmarket.public_key = "test_public"
                mock_settings.dmarket.secret_key = "test_secret"

                from src.utils.anytool_integration import get_anytool_client

                # Reset the global
                import src.utils.anytool_integration

                src.utils.anytool_integration._anytool_client = None

                client1 = get_anytool_client()
                client2 = get_anytool_client()

                assert client1 is client2

    @pytest.mark.asyncio
    async def test_initialize_anytool_returns_client(self):
        """Test that initialize_anytool returns a client."""
        with patch("src.utils.anytool_integration._anytool_client", None):
            with patch("src.utils.anytool_integration.settings") as mock_settings:
                mock_settings.dmarket.public_key = "test_public"
                mock_settings.dmarket.secret_key = "test_secret"

                from src.utils.anytool_integration import initialize_anytool

                # Reset the global
                import src.utils.anytool_integration

                src.utils.anytool_integration._anytool_client = None

                client = await initialize_anytool()

                assert client is not None

    @pytest.mark.asyncio
    async def test_initialize_anytool_exports_config(self, tmp_path):
        """Test that initialize_anytool exports config when path is provided."""
        with patch("src.utils.anytool_integration._anytool_client", None):
            with patch("src.utils.anytool_integration.settings") as mock_settings:
                mock_settings.dmarket.public_key = "test_public"
                mock_settings.dmarket.secret_key = "test_secret"
                mock_settings.dmarket_public_key = "test_public"
                mock_settings.dmarket_secret_key = "test_secret"

                from src.utils.anytool_integration import initialize_anytool

                # Reset the global
                import src.utils.anytool_integration

                src.utils.anytool_integration._anytool_client = None

                config_path = tmp_path / "config.json"
                await initialize_anytool(config_path=config_path)

                assert config_path.exists()


class TestToolArgumentHandling:
    """Tests for tool argument handling."""

    @pytest.mark.asyncio
    async def test_get_market_items_with_optional_args(self):
        """Test get_market_items with optional arguments."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={"objects": []})

        client = AnyToolClient(api_client=mock_api)

        await client._execute_tool(
            "get_market_items",
            {
                "game": "csgo",
                "limit": 20,
                "price_from": 100,
                "price_to": 500,
            },
        )

        mock_api.get_market_items.assert_called_once_with(
            game="csgo",
            limit=20,
            price_from=100,
            price_to=500,
        )

    @pytest.mark.asyncio
    async def test_get_market_items_with_defaults(self):
        """Test get_market_items uses default limit."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={"objects": []})

        client = AnyToolClient(api_client=mock_api)

        await client._execute_tool(
            "get_market_items",
            {"game": "csgo"},
        )

        mock_api.get_market_items.assert_called_once_with(
            game="csgo",
            limit=10,  # default
            price_from=None,
            price_to=None,
        )

    @pytest.mark.asyncio
    async def test_scan_arbitrage_with_default_level(self):
        """Test scan_arbitrage uses default level."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()

        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as MockScanner:
            mock_scanner = AsyncMock()
            mock_scanner.scan_level = AsyncMock(return_value=[])
            MockScanner.return_value = mock_scanner

            client = AnyToolClient(api_client=mock_api)

            await client._execute_tool(
                "scan_arbitrage",
                {"game": "csgo"},
            )

            mock_scanner.scan_level.assert_called_once_with(
                level="standard",
                game="csgo",
            )

    @pytest.mark.asyncio
    async def test_create_target_with_default_amount(self):
        """Test create_target uses default amount."""
        from src.utils.anytool_integration import AnyToolClient

        mock_api = AsyncMock()

        with patch("src.dmarket.targets.TargetManager") as MockTargetManager:
            mock_tm = AsyncMock()
            mock_tm.create_target = AsyncMock(return_value={"id": "target_123"})
            MockTargetManager.return_value = mock_tm

            client = AnyToolClient(api_client=mock_api)

            await client._execute_tool(
                "create_target",
                {"game": "csgo", "title": "Test", "price": 10.0},
            )

            mock_tm.create_target.assert_called_once_with(
                game="csgo",
                title="Test",
                price=10.0,
                amount=1,  # default
            )

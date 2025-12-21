"""
Comprehensive tests for AnyTool integration module.

Tests the AnyToolConfig, AnyToolClient, and related functions.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.anytool_integration import (
    AnyToolClient,
    AnyToolConfig,
    get_anytool_client,
    initialize_anytool,
)


# ============================================================================
# AnyToolConfig Tests
# ============================================================================


class TestAnyToolConfig:
    """Tests for AnyToolConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = AnyToolConfig()

        assert config.mcp_server_path == "src.mcp_server.dmarket_mcp:main"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.enabled is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
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

    def test_partial_custom_config(self) -> None:
        """Test partial custom configuration."""
        config = AnyToolConfig(timeout=120)

        assert config.timeout == 120
        assert config.max_retries == 3  # default
        assert config.enabled is True  # default


# ============================================================================
# AnyToolClient Tests - Initialization
# ============================================================================


class TestAnyToolClientInit:
    """Tests for AnyToolClient initialization."""

    @patch("src.utils.anytool_integration.settings")
    @patch("src.utils.anytool_integration.DMarketAPI")
    def test_init_default(self, mock_api_cls: MagicMock, mock_settings: MagicMock) -> None:
        """Test default initialization."""
        mock_settings.dmarket.public_key = "test_public"
        mock_settings.dmarket.secret_key = "test_secret"
        mock_api_cls.return_value = MagicMock()

        client = AnyToolClient()

        assert client.config is not None
        assert client.api_client is not None
        assert client._callbacks == {}

    def test_init_with_custom_config(self) -> None:
        """Test initialization with custom config."""
        config = AnyToolConfig(timeout=60, enabled=False)
        mock_api = MagicMock()

        client = AnyToolClient(config=config, api_client=mock_api)

        assert client.config.timeout == 60
        assert client.config.enabled is False
        assert client.api_client is mock_api

    def test_init_with_api_client(self) -> None:
        """Test initialization with custom API client."""
        mock_api = MagicMock()

        client = AnyToolClient(api_client=mock_api)

        assert client.api_client is mock_api


# ============================================================================
# AnyToolClient Tests - Callbacks
# ============================================================================


class TestAnyToolClientCallbacks:
    """Tests for AnyToolClient callback functionality."""

    def test_register_callback(self) -> None:
        """Test registering a callback."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback = MagicMock()
        client.register_callback("test_event", callback)

        assert "test_event" in client._callbacks
        assert callback in client._callbacks["test_event"]

    def test_register_multiple_callbacks(self) -> None:
        """Test registering multiple callbacks for same event."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback1 = MagicMock()
        callback2 = MagicMock()
        client.register_callback("test_event", callback1)
        client.register_callback("test_event", callback2)

        assert len(client._callbacks["test_event"]) == 2
        assert callback1 in client._callbacks["test_event"]
        assert callback2 in client._callbacks["test_event"]

    def test_register_callbacks_different_events(self) -> None:
        """Test registering callbacks for different events."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback1 = MagicMock()
        callback2 = MagicMock()
        client.register_callback("event1", callback1)
        client.register_callback("event2", callback2)

        assert "event1" in client._callbacks
        assert "event2" in client._callbacks
        assert callback1 in client._callbacks["event1"]
        assert callback2 in client._callbacks["event2"]

    @pytest.mark.asyncio
    async def test_trigger_sync_callback(self) -> None:
        """Test triggering sync callback."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        callback = MagicMock()
        client.register_callback("test_event", callback)

        await client._trigger_callbacks("test_event", {"data": "test"})

        callback.assert_called_once_with({"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_async_callback(self) -> None:
        """Test triggering async callback."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        async_callback = AsyncMock()
        client.register_callback("test_event", async_callback)

        await client._trigger_callbacks("test_event", {"data": "test"})

        async_callback.assert_called_once_with({"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_callback_handles_errors(self) -> None:
        """Test callback error handling."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        def failing_callback(data: Any) -> None:
            raise ValueError("Test error")

        client.register_callback("test_event", failing_callback)

        # Should not raise
        await client._trigger_callbacks("test_event", {"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_callbacks_no_event(self) -> None:
        """Test triggering callbacks for non-existent event."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        # Should not raise
        await client._trigger_callbacks("non_existent", {"data": "test"})


# ============================================================================
# AnyToolClient Tests - Tool Calls
# ============================================================================


class TestAnyToolClientToolCalls:
    """Tests for AnyToolClient tool call functionality."""

    @pytest.mark.asyncio
    async def test_call_tool_disabled(self) -> None:
        """Test calling tool when disabled."""
        config = AnyToolConfig(enabled=False)
        mock_api = MagicMock()
        client = AnyToolClient(config=config, api_client=mock_api)

        with pytest.raises(ValueError, match="AnyTool integration is disabled"):
            await client.call_tool("get_balance", {})

    @pytest.mark.asyncio
    async def test_call_tool_get_balance(self) -> None:
        """Test calling get_balance tool."""
        mock_api = AsyncMock()
        mock_api.get_balance.return_value = {"usd": "1000", "dmc": "500"}
        client = AnyToolClient(api_client=mock_api)

        result = await client.call_tool("get_balance", {})

        assert result["success"] is True
        assert result["balance"] == {"usd": "1000", "dmc": "500"}
        mock_api.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_get_market_items(self) -> None:
        """Test calling get_market_items tool."""
        mock_api = AsyncMock()
        mock_api.get_market_items.return_value = {
            "objects": [{"title": "Test Item", "price": {"USD": "1000"}}]
        }
        client = AnyToolClient(api_client=mock_api)

        result = await client.call_tool(
            "get_market_items",
            {"game": "csgo", "limit": 5},
        )

        assert result["success"] is True
        assert len(result["items"]) == 1
        mock_api.get_market_items.assert_called_once_with(
            game="csgo",
            limit=5,
            price_from=None,
            price_to=None,
        )

    @pytest.mark.asyncio
    async def test_call_tool_get_market_items_with_price_range(self) -> None:
        """Test calling get_market_items with price range."""
        mock_api = AsyncMock()
        mock_api.get_market_items.return_value = {"objects": []}
        client = AnyToolClient(api_client=mock_api)

        await client.call_tool(
            "get_market_items",
            {"game": "dota2", "price_from": 100, "price_to": 500},
        )

        mock_api.get_market_items.assert_called_once_with(
            game="dota2",
            limit=10,
            price_from=100,
            price_to=500,
        )

    @pytest.mark.asyncio
    async def test_call_tool_scan_arbitrage(self) -> None:
        """Test calling scan_arbitrage tool."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner_cls:
            mock_scanner = AsyncMock()
            mock_scanner.scan_level.return_value = [
                {"profit": 1.0, "item": "Test"},
                {"profit": 0.3, "item": "Low Profit"},
            ]
            mock_scanner_cls.return_value = mock_scanner

            result = await client.call_tool(
                "scan_arbitrage",
                {"game": "csgo", "min_profit": 0.5},
            )

            assert result["success"] is True
            assert len(result["opportunities"]) == 1
            assert result["opportunities"][0]["profit"] == 1.0

    @pytest.mark.asyncio
    async def test_call_tool_get_item_details(self) -> None:
        """Test calling get_item_details tool."""
        mock_api = AsyncMock()
        mock_api.get_item_by_id.return_value = {"title": "Test Item", "price": 10.0}
        client = AnyToolClient(api_client=mock_api)

        result = await client.call_tool("get_item_details", {"item_id": "test123"})

        assert result["success"] is True
        assert result["item"]["title"] == "Test Item"
        mock_api.get_item_by_id.assert_called_once_with("test123")

    @pytest.mark.asyncio
    async def test_call_tool_create_target(self) -> None:
        """Test calling create_target tool."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        with patch("src.dmarket.targets.TargetManager") as mock_target_mgr_cls:
            mock_target_mgr = AsyncMock()
            mock_target_mgr.create_target.return_value = {"target_id": "t123"}
            mock_target_mgr_cls.return_value = mock_target_mgr

            result = await client.call_tool(
                "create_target",
                {"game": "csgo", "title": "AK-47", "price": 25.0},
            )

            assert result["success"] is True
            assert result["target"]["target_id"] == "t123"

    @pytest.mark.asyncio
    async def test_call_tool_get_targets(self) -> None:
        """Test calling get_targets tool."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        with patch("src.dmarket.targets.TargetManager") as mock_target_mgr_cls:
            mock_target_mgr = AsyncMock()
            mock_target_mgr.get_all_targets.return_value = [{"target_id": "t1"}, {"target_id": "t2"}]
            mock_target_mgr_cls.return_value = mock_target_mgr

            result = await client.call_tool("get_targets", {})

            assert result["success"] is True
            assert len(result["targets"]) == 2

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self) -> None:
        """Test calling unknown tool."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        with pytest.raises(ValueError, match="Unknown tool"):
            await client.call_tool("unknown_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_triggers_callback(self) -> None:
        """Test that tool call triggers callback."""
        mock_api = AsyncMock()
        mock_api.get_balance.return_value = {"usd": "1000"}
        client = AnyToolClient(api_client=mock_api)

        callback = MagicMock()
        client.register_callback("tool_called", callback)

        await client.call_tool("get_balance", {})

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["tool"] == "get_balance"


# ============================================================================
# AnyToolClient Tests - Available Tools
# ============================================================================


class TestAnyToolClientAvailableTools:
    """Tests for AnyToolClient available tools functionality."""

    @pytest.mark.asyncio
    async def test_get_available_tools(self) -> None:
        """Test getting available tools list."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        tools = await client.get_available_tools()

        assert len(tools) == 6
        tool_names = [t["name"] for t in tools]
        assert "get_balance" in tool_names
        assert "get_market_items" in tool_names
        assert "scan_arbitrage" in tool_names
        assert "get_item_details" in tool_names
        assert "create_target" in tool_names
        assert "get_targets" in tool_names

    @pytest.mark.asyncio
    async def test_available_tools_have_descriptions(self) -> None:
        """Test that all tools have descriptions."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        tools = await client.get_available_tools()

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert len(tool["description"]) > 0


# ============================================================================
# AnyToolClient Tests - Export Config
# ============================================================================


class TestAnyToolClientExportConfig:
    """Tests for AnyToolClient config export functionality."""

    @patch("src.utils.anytool_integration.settings")
    def test_export_config(self, mock_settings: MagicMock, tmp_path: Path) -> None:
        """Test exporting configuration to file."""
        mock_settings.dmarket_public_key = "test_public"
        mock_settings.dmarket_secret_key = "test_secret"

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        config_path = tmp_path / "config" / "anytool.json"
        client.export_config(config_path)

        assert config_path.exists()

        with open(config_path) as f:
            config_data = json.load(f)

        assert "mcpServers" in config_data
        assert "dmarket-bot" in config_data["mcpServers"]

    @patch("src.utils.anytool_integration.settings")
    def test_export_config_creates_directory(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        """Test that export_config creates parent directories."""
        mock_settings.dmarket_public_key = "test_public"
        mock_settings.dmarket_secret_key = "test_secret"

        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        config_path = tmp_path / "deep" / "nested" / "config.json"
        client.export_config(config_path)

        assert config_path.exists()


# ============================================================================
# Module Functions Tests
# ============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    @patch("src.utils.anytool_integration._anytool_client", None)
    @patch("src.utils.anytool_integration.settings")
    @patch("src.utils.anytool_integration.DMarketAPI")
    def test_get_anytool_client_creates_singleton(
        self, mock_api_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that get_anytool_client creates a singleton."""
        mock_settings.dmarket.public_key = "test"
        mock_settings.dmarket.secret_key = "test"
        mock_api_cls.return_value = MagicMock()

        client1 = get_anytool_client()
        client2 = get_anytool_client()

        assert client1 is client2

    @pytest.mark.asyncio
    @patch("src.utils.anytool_integration.get_anytool_client")
    async def test_initialize_anytool(self, mock_get_client: MagicMock) -> None:
        """Test initialize_anytool function."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await initialize_anytool()

        assert result is mock_client
        mock_get_client.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.utils.anytool_integration.get_anytool_client")
    async def test_initialize_anytool_with_config_path(
        self, mock_get_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test initialize_anytool with config path."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config_path = tmp_path / "config.json"
        await initialize_anytool(config_path)

        mock_client.export_config.assert_called_once_with(config_path)


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_call_tool_api_error(self) -> None:
        """Test handling API errors in tool calls."""
        mock_api = AsyncMock()
        mock_api.get_balance.side_effect = Exception("API Error")
        client = AnyToolClient(api_client=mock_api)

        with pytest.raises(Exception, match="API Error"):
            await client.call_tool("get_balance", {})

    @pytest.mark.asyncio
    async def test_scan_arbitrage_filters_low_profit(self) -> None:
        """Test that scan_arbitrage filters low profit items."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner_cls:
            mock_scanner = AsyncMock()
            mock_scanner.scan_level.return_value = [
                {"profit": 2.0},
                {"profit": 0.1},
                {"profit": 1.5},
            ]
            mock_scanner_cls.return_value = mock_scanner

            result = await client.call_tool(
                "scan_arbitrage",
                {"game": "csgo", "min_profit": 1.0},
            )

            assert len(result["opportunities"]) == 2

    def test_config_path_as_string(self, tmp_path: Path) -> None:
        """Test export_config with string path."""
        mock_api = MagicMock()
        client = AnyToolClient(api_client=mock_api)

        with patch("src.utils.anytool_integration.settings") as mock_settings:
            mock_settings.dmarket_public_key = "test"
            mock_settings.dmarket_secret_key = "test"

            config_path = str(tmp_path / "config.json")
            client.export_config(config_path)

            assert Path(config_path).exists()

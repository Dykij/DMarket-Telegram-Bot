"""Tests for DMarket MCP Server.

This module contains tests for the MCP Server integration with DMarket API.
"""

import pytest

from src.mcp_server.dmarket_mcp import (
    create_dmarket_mcp_server,
    DMarketMCPServer,
    Tool,
    ToolCategory,
    TextContent,
    ToolResult,
)


class TestDMarketMCPServer:
    """Tests for DMarketMCPServer class."""

    def test_create_server_with_defaults(self) -> None:
        """Test creating server with default parameters."""
        server = create_dmarket_mcp_server()

        assert isinstance(server, DMarketMCPServer)
        assert server.dry_run is True
        assert len(server._tools) > 0

    def test_create_server_with_custom_dry_run(self) -> None:
        """Test creating server with custom dry_run setting."""
        server = create_dmarket_mcp_server(dry_run=False)

        assert server.dry_run is False

    def test_server_registers_all_tools(self) -> None:
        """Test that server registers all expected tools."""
        server = create_dmarket_mcp_server()

        expected_tools = [
            "get_balance",
            "get_user_profile",
            "get_market_items",
            "get_market_best_offers",
            "create_target",
            "get_user_targets",
            "delete_targets",
            "scan_arbitrage",
            "analyze_liquidity",
            "get_sales_history",
            "get_buy_orders_competition",
            "buy_item",
            "sell_item",
        ]

        for tool_name in expected_tools:
            assert tool_name in server._tools, f"Missing tool: {tool_name}"

    def test_tool_categories(self) -> None:
        """Test that tools are categorized correctly."""
        server = create_dmarket_mcp_server()

        # Check account tools
        assert server._tools["get_balance"].category == ToolCategory.ACCOUNT
        assert server._tools["get_user_profile"].category == ToolCategory.ACCOUNT

        # Check market tools
        assert server._tools["get_market_items"].category == ToolCategory.MARKET

        # Check trading tools
        assert server._tools["buy_item"].category == ToolCategory.TRADING
        assert server._tools["sell_item"].category == ToolCategory.TRADING

        # Check targets tools
        assert server._tools["create_target"].category == ToolCategory.TARGETS

        # Check analysis tools
        assert server._tools["scan_arbitrage"].category == ToolCategory.ANALYSIS


class TestToolSchema:
    """Tests for Tool input schema definitions."""

    def test_get_market_items_schema(self) -> None:
        """Test get_market_items tool schema."""
        server = create_dmarket_mcp_server()
        tool = server._tools["get_market_items"]

        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "game" in schema["properties"]
        assert "price_from" in schema["properties"]
        assert "price_to" in schema["properties"]
        assert "title" in schema["properties"]
        assert "limit" in schema["properties"]

    def test_create_target_schema(self) -> None:
        """Test create_target tool schema with required fields."""
        server = create_dmarket_mcp_server()
        tool = server._tools["create_target"]

        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "game" in schema["required"]
        assert "title" in schema["required"]
        assert "price" in schema["required"]

    def test_buy_item_schema(self) -> None:
        """Test buy_item tool schema with required fields."""
        server = create_dmarket_mcp_server()
        tool = server._tools["buy_item"]

        schema = tool.input_schema
        assert "item_id" in schema["required"]
        assert "price" in schema["required"]


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating successful tool result."""
        result = ToolResult(
            success=True,
            content=[TextContent(text="Test result")],
        )

        assert result.success is True
        assert len(result.content) == 1
        assert result.content[0].text == "Test result"
        assert result.error is None

    def test_error_result(self) -> None:
        """Test creating error tool result."""
        result = ToolResult(
            success=False,
            content=[TextContent(text="Error occurred")],
            error="Test error message",
        )

        assert result.success is False
        assert result.error == "Test error message"

    def test_result_to_dict(self) -> None:
        """Test converting tool result to dictionary."""
        result = ToolResult(
            success=True,
            content=[TextContent(text="Test")],
        )

        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert len(result_dict["content"]) == 1
        assert result_dict["content"][0]["type"] == "text"


class TestToolToDict:
    """Tests for Tool.to_dict method."""

    def test_tool_to_dict(self) -> None:
        """Test converting tool to dictionary for MCP protocol."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            category=ToolCategory.MARKET,
        )

        tool_dict = tool.to_dict()

        assert tool_dict["name"] == "test_tool"
        assert tool_dict["description"] == "A test tool"
        assert "inputSchema" in tool_dict


@pytest.mark.asyncio
class TestListTools:
    """Tests for list_tools method."""

    async def test_list_tools_returns_all_tools(self) -> None:
        """Test that list_tools returns all registered tools."""
        server = create_dmarket_mcp_server()

        tools = await server.list_tools()

        assert len(tools) == len(server._tools)
        for tool_dict in tools:
            assert "name" in tool_dict
            assert "description" in tool_dict
            assert "inputSchema" in tool_dict


@pytest.mark.asyncio
class TestCallTool:
    """Tests for call_tool method."""

    async def test_call_unknown_tool_returns_error(self) -> None:
        """Test calling unknown tool returns error."""
        server = create_dmarket_mcp_server()

        result = await server.call_tool("unknown_tool", {})

        assert result.success is False
        assert "unknown" in result.error.lower()

"""MCP Server package for DMarket Trading API.

This package provides MCP (Model Context Protocol) server implementations
for integrating DMarket API with AI agents like AnyTool and GitHub Copilot.

The MCP protocol allows AI agents to use DMarket API methods as tools,
enabling natural language interactions with the trading platform.

Example:
    # Start MCP server
    python -m src.mcp_server.dmarket_mcp

    # Or use via AnyTool
    from anytool import AnyTool
    async with AnyTool() as tool:
        result = await tool.execute("Get my DMarket balance")

Note:
    This integration follows DMarket ToS compliance - only API calls
    are allowed, no GUI/web automation.

Modules:
    dmarket_mcp: Main MCP server for DMarket Trading API
"""

from src.mcp_server.dmarket_mcp import (
    create_dmarket_mcp_server,
    DMarketMCPServer,
)

__all__ = [
    "create_dmarket_mcp_server",
    "DMarketMCPServer",
]

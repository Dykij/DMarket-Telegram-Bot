"""MCP Server для DMarket Trading API.

Этот модуль предоставляет MCP (Model Context Protocol) сервер для интеграции
DMarket API с AI агентами (AnyTool, GitHub Copilot и другими).

MCP протокол позволяет AI агентам использовать методы DMarket API как инструменты,
обеспечивая естественное языковое взаимодействие с торговой платформой.

Пример использования:
    # Запуск MCP сервера
    python -m src.mcp_server.dmarket_mcp

    # Или через AnyTool
    from anytool import AnyTool
    async with AnyTool() as tool:
        result = await tool.execute("Получи мой баланс на DMarket")

Важно:
    Эта интеграция соответствует ToS DMarket - разрешены только API вызовы,
    GUI/web автоматизация запрещена.

Documentation: https://docs.dmarket.com/v1/swagger.html
MCP Protocol: https://modelcontextprotocol.io/
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog


# Configure logging
logger = structlog.get_logger(__name__)


class ToolCategory(str, Enum):
    """Categories of MCP tools."""

    ACCOUNT = "account"
    MARKET = "market"
    TRADING = "trading"
    ANALYSIS = "analysis"
    TARGETS = "targets"


@dataclass
class Tool:
    """MCP Tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]
    category: ToolCategory = ToolCategory.MARKET

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary for MCP protocol."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class TextContent:
    """MCP Text content response."""

    type: str = "text"
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"type": self.type, "text": self.text}


@dataclass
class ToolResult:
    """Result of tool execution."""

    success: bool
    content: list[TextContent]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "content": [c.to_dict() for c in self.content],
            "error": self.error,
        }


class DMarketMCPServer:
    """MCP Server для DMarket Trading API.

    Предоставляет инструменты для AI агентов для взаимодействия с DMarket API.

    Поддерживаемые операции:
    - Получение баланса аккаунта
    - Поиск предметов на маркетплейсе
    - Создание таргетов (buy orders)
    - Сканирование арбитражных возможностей
    - Анализ ликвидности предметов
    - Получение истории продаж

    Attributes:
        api_client: DMarket API клиент
        tools: Словарь доступных инструментов
        dry_run: Режим симуляции (не выполнять реальные сделки)
    """

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        dry_run: bool = True,
    ) -> None:
        """Инициализация MCP сервера.

        Args:
            public_key: DMarket API public key (или из env DMARKET_PUBLIC_KEY)
            secret_key: DMarket API secret key (или из env DMARKET_SECRET_KEY)
            dry_run: Режим симуляции - если True, торговые операции симулируются

        """
        self.public_key = public_key or os.environ.get("DMARKET_PUBLIC_KEY", "")
        self.secret_key = secret_key or os.environ.get("DMARKET_SECRET_KEY", "")
        self.dry_run = dry_run
        self._api_client: Any = None
        self._tools: dict[str, Tool] = {}
        self._initialized = False

        # Register all tools
        self._register_tools()

        logger.info(
            "dmarket_mcp_server_initialized",
            dry_run=dry_run,
            tools_count=len(self._tools),
            has_credentials=bool(self.public_key and self.secret_key),
        )

    async def _get_api_client(self) -> Any:
        """Lazy initialization of DMarket API client."""
        if self._api_client is None:
            from src.dmarket.dmarket_api import DMarketAPI

            self._api_client = DMarketAPI(
                public_key=self.public_key,
                secret_key=self.secret_key,
                dry_run=self.dry_run,
            )
        return self._api_client

    def _register_tools(self) -> None:
        """Register all available MCP tools."""
        # Account tools
        self._tools["get_balance"] = Tool(
            name="get_balance",
            description="Получить текущий баланс аккаунта DMarket в USD",
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category=ToolCategory.ACCOUNT,
        )

        self._tools["get_user_profile"] = Tool(
            name="get_user_profile",
            description="Получить профиль пользователя DMarket",
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category=ToolCategory.ACCOUNT,
        )

        # Market tools
        self._tools["get_market_items"] = Tool(
            name="get_market_items",
            description="Получить предметы с маркетплейса DMarket с фильтрами по игре, цене и названию",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "description": "Идентификатор игры",
                        "default": "csgo",
                    },
                    "price_from": {
                        "type": "number",
                        "description": "Минимальная цена в USD (например, 1.50)",
                    },
                    "price_to": {
                        "type": "number",
                        "description": "Максимальная цена в USD (например, 100.00)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Поиск по названию предмета",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Количество результатов (макс 100)",
                        "default": 20,
                    },
                },
                "required": [],
            },
            category=ToolCategory.MARKET,
        )

        self._tools["get_market_best_offers"] = Tool(
            name="get_market_best_offers",
            description="Получить лучшие предложения на маркетплейсе для конкретного предмета",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "default": "csgo",
                    },
                    "title": {
                        "type": "string",
                        "description": "Название предмета",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                    },
                },
                "required": [],
            },
            category=ToolCategory.MARKET,
        )

        # Target tools
        self._tools["create_target"] = Tool(
            name="create_target",
            description="Создать таргет (buy order) на покупку предмета по указанной цене",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "description": "Идентификатор игры",
                    },
                    "title": {
                        "type": "string",
                        "description": "Точное название предмета",
                    },
                    "price": {
                        "type": "number",
                        "description": "Цена покупки в USD (например: 8.50 для $8.50). Будет автоматически конвертирована в центы для API.",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Количество предметов для покупки",
                        "default": 1,
                    },
                },
                "required": ["game", "title", "price"],
            },
            category=ToolCategory.TARGETS,
        )

        self._tools["get_user_targets"] = Tool(
            name="get_user_targets",
            description="Получить список активных таргетов (buy orders) пользователя",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "default": "csgo",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                    },
                },
                "required": [],
            },
            category=ToolCategory.TARGETS,
        )

        self._tools["delete_targets"] = Tool(
            name="delete_targets",
            description="Удалить таргеты (buy orders) по их ID",
            input_schema={
                "type": "object",
                "properties": {
                    "target_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Список ID таргетов для удаления",
                    },
                },
                "required": ["target_ids"],
            },
            category=ToolCategory.TARGETS,
        )

        # Analysis tools
        self._tools["scan_arbitrage"] = Tool(
            name="scan_arbitrage",
            description="Сканировать арбитражные возможности на DMarket для указанной игры и уровня",
            input_schema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "enum": ["boost", "standard", "medium", "advanced", "pro"],
                        "description": "Уровень арбитража (boost: $0.50-$3, standard: $3-$10, medium: $10-$30, advanced: $30-$100, pro: $100+)",
                        "default": "standard",
                    },
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "default": "csgo",
                    },
                    "min_profit_percent": {
                        "type": "number",
                        "description": "Минимальный процент прибыли",
                        "default": 5.0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество результатов",
                        "default": 10,
                    },
                },
                "required": [],
            },
            category=ToolCategory.ANALYSIS,
        )

        self._tools["analyze_liquidity"] = Tool(
            name="analyze_liquidity",
            description="Проанализировать ликвидность предмета (скорость продаж, объем торгов)",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Название предмета",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Период анализа в днях",
                        "default": 7,
                    },
                },
                "required": ["game", "title"],
            },
            category=ToolCategory.ANALYSIS,
        )

        self._tools["get_sales_history"] = Tool(
            name="get_sales_history",
            description="Получить историю продаж предмета за указанный период",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Название предмета",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Количество дней истории",
                        "default": 7,
                    },
                },
                "required": ["game", "title"],
            },
            category=ToolCategory.ANALYSIS,
        )

        self._tools["get_buy_orders_competition"] = Tool(
            name="get_buy_orders_competition",
            description="Оценить уровень конкуренции по buy orders для предмета",
            input_schema={
                "type": "object",
                "properties": {
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Название предмета",
                    },
                    "price_threshold": {
                        "type": "number",
                        "description": "Порог цены в USD для фильтрации ордеров",
                    },
                },
                "required": ["game", "title"],
            },
            category=ToolCategory.ANALYSIS,
        )

        # Trading tools
        self._tools["buy_item"] = Tool(
            name="buy_item",
            description="Купить предмет с маркетплейса (⚠️ РЕАЛЬНАЯ СДЕЛКА если dry_run=False)",
            input_schema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "ID предмета для покупки",
                    },
                    "price": {
                        "type": "number",
                        "description": "Цена покупки в USD",
                    },
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "default": "csgo",
                    },
                },
                "required": ["item_id", "price"],
            },
            category=ToolCategory.TRADING,
        )

        self._tools["sell_item"] = Tool(
            name="sell_item",
            description="Выставить предмет на продажу (⚠️ РЕАЛЬНАЯ СДЕЛКА если dry_run=False)",
            input_schema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "ID предмета для продажи",
                    },
                    "price": {
                        "type": "number",
                        "description": "Цена продажи в USD",
                    },
                    "game": {
                        "type": "string",
                        "enum": ["csgo", "dota2", "tf2", "rust"],
                        "default": "csgo",
                    },
                },
                "required": ["item_id", "price"],
            },
            category=ToolCategory.TRADING,
        )

    async def list_tools(self) -> list[dict[str, Any]]:
        """Получить список доступных инструментов.

        Returns:
            Список инструментов в формате MCP

        """
        return [tool.to_dict() for tool in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Вызвать инструмент по имени с аргументами.

        Args:
            name: Имя инструмента
            arguments: Аргументы для инструмента

        Returns:
            Результат выполнения инструмента

        """
        logger.info("mcp_tool_call", tool_name=name, arguments=arguments)

        if name not in self._tools:
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Unknown tool: {name}")],
                error=f"Tool '{name}' not found",
            )

        try:
            # Get API client
            api = await self._get_api_client()

            # Route to appropriate handler
            if name == "get_balance":
                result = await self._handle_get_balance(api)
            elif name == "get_user_profile":
                result = await self._handle_get_user_profile(api)
            elif name == "get_market_items":
                result = await self._handle_get_market_items(api, arguments)
            elif name == "get_market_best_offers":
                result = await self._handle_get_market_best_offers(api, arguments)
            elif name == "create_target":
                result = await self._handle_create_target(api, arguments)
            elif name == "get_user_targets":
                result = await self._handle_get_user_targets(api, arguments)
            elif name == "delete_targets":
                result = await self._handle_delete_targets(api, arguments)
            elif name == "scan_arbitrage":
                result = await self._handle_scan_arbitrage(api, arguments)
            elif name == "analyze_liquidity":
                result = await self._handle_analyze_liquidity(api, arguments)
            elif name == "get_sales_history":
                result = await self._handle_get_sales_history(api, arguments)
            elif name == "get_buy_orders_competition":
                result = await self._handle_get_buy_orders_competition(api, arguments)
            elif name == "buy_item":
                result = await self._handle_buy_item(api, arguments)
            elif name == "sell_item":
                result = await self._handle_sell_item(api, arguments)
            else:
                return ToolResult(
                    success=False,
                    content=[TextContent(text=f"Tool '{name}' not implemented")],
                    error="Not implemented",
                )

            logger.info("mcp_tool_success", tool_name=name)
            return result

        except Exception as e:
            logger.exception("mcp_tool_error", tool_name=name, error=str(e))
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error executing {name}: {str(e)}")],
                error=str(e),
            )

    # ==================== Tool Handlers ====================

    async def _handle_get_balance(self, api: Any) -> ToolResult:
        """Handle get_balance tool."""
        balance = await api.get_balance()

        if balance.get("error"):
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error: {balance.get('error_message', 'Unknown error')}")],
                error=balance.get("error_message"),
            )

        text = (
            f"💰 DMarket Balance:\n"
            f"  • Total: ${balance.get('balance', 0):.2f} USD\n"
            f"  • Available: ${balance.get('available_balance', 0):.2f} USD\n"
            f"  • Has Funds: {'Yes' if balance.get('has_funds') else 'No'}"
        )
        return ToolResult(
            success=True,
            content=[TextContent(text=text)],
        )

    async def _handle_get_user_profile(self, api: Any) -> ToolResult:
        """Handle get_user_profile tool."""
        profile = await api.get_user_profile()

        if profile.get("error"):
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error: {profile.get('message', 'Unknown error')}")],
                error=profile.get("message"),
            )

        text = f"👤 User Profile:\n{json.dumps(profile, indent=2, ensure_ascii=False)}"
        return ToolResult(
            success=True,
            content=[TextContent(text=text)],
        )

    async def _handle_get_market_items(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle get_market_items tool."""
        response = await api.get_market_items(
            game=args.get("game", "csgo"),
            price_from=args.get("price_from"),
            price_to=args.get("price_to"),
            title=args.get("title"),
            limit=args.get("limit", 20),
        )

        items = response.get("objects", [])
        if not items:
            return ToolResult(
                success=True,
                content=[TextContent(text="No items found matching criteria")],
            )

        # Format items for display
        lines = [f"🛒 Found {len(items)} items:"]
        for item in items[:10]:  # Limit to 10 for readability
            price = int(item.get("price", {}).get("USD", 0)) / 100
            title = item.get("title", "Unknown")
            lines.append(f"  • {title}: ${price:.2f}")

        if len(items) > 10:
            lines.append(f"  ... and {len(items) - 10} more")

        return ToolResult(
            success=True,
            content=[TextContent(text="\n".join(lines))],
        )

    async def _handle_get_market_best_offers(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle get_market_best_offers tool."""
        response = await api.get_market_best_offers(
            game=args.get("game", "csgo"),
            title=args.get("title"),
            limit=args.get("limit", 10),
        )

        text = f"📊 Best Offers:\n{json.dumps(response, indent=2, ensure_ascii=False)}"
        return ToolResult(
            success=True,
            content=[TextContent(text=text)],
        )

    async def _handle_create_target(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle create_target tool."""
        game = args["game"]
        title = args["title"]
        price = args["price"]
        amount = args.get("amount", 1)

        # Map game name to game ID
        game_ids = {
            "csgo": "a8db",
            "dota2": "9a92",
            "tf2": "tf2",
            "rust": "rust",
        }
        game_id = game_ids.get(game, game)

        # Create target via API
        targets = [
            {
                "Title": title,
                "Amount": amount,
                "Price": {"Amount": int(price * 100), "Currency": "USD"},
            }
        ]

        result = await api.create_targets(game_id=game_id, targets=targets)

        if result.get("error"):
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error: {result.get('message', 'Failed to create target')}")],
                error=result.get("message"),
            )

        text = (
            f"✅ Target Created:\n"
            f"  • Item: {title}\n"
            f"  • Price: ${price:.2f} USD\n"
            f"  • Amount: {amount}\n"
            f"  • Game: {game}"
        )
        return ToolResult(
            success=True,
            content=[TextContent(text=text)],
        )

    async def _handle_get_user_targets(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle get_user_targets tool."""
        game = args.get("game", "csgo")
        game_ids = {"csgo": "a8db", "dota2": "9a92", "tf2": "tf2", "rust": "rust"}
        game_id = game_ids.get(game, game)

        response = await api.get_user_targets(
            game_id=game_id,
            limit=args.get("limit", 50),
        )

        items = response.get("Items", [])
        if not items:
            return ToolResult(
                success=True,
                content=[TextContent(text="No active targets found")],
            )

        lines = [f"🎯 Active Targets ({len(items)}):"]
        for item in items[:10]:
            title = item.get("Title", "Unknown")
            price = int(item.get("Price", {}).get("Amount", 0)) / 100
            status = item.get("Status", "Unknown")
            lines.append(f"  • {title}: ${price:.2f} ({status})")

        if len(items) > 10:
            lines.append(f"  ... and {len(items) - 10} more")

        return ToolResult(
            success=True,
            content=[TextContent(text="\n".join(lines))],
        )

    async def _handle_delete_targets(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle delete_targets tool."""
        target_ids = args["target_ids"]

        result = await api.delete_targets(target_ids)

        if result.get("error"):
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error: {result.get('message', 'Failed to delete targets')}")],
                error=result.get("message"),
            )

        return ToolResult(
            success=True,
            content=[TextContent(text=f"✅ Deleted {len(target_ids)} targets")],
        )

    async def _handle_scan_arbitrage(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle scan_arbitrage tool."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(api_client=api)

        level = args.get("level", "standard")
        game = args.get("game", "csgo")
        min_profit = args.get("min_profit_percent", 5.0)
        limit = args.get("limit", 10)

        try:
            opportunities = await scanner.scan_game(
                game=game,
                mode=level,
                limit=limit,
            )

            if not opportunities:
                return ToolResult(
                    success=True,
                    content=[TextContent(text=f"No arbitrage opportunities found for {game} at {level} level")],
                )

            # Filter by min profit
            filtered = [
                op for op in opportunities
                if op.get("profit_percent", 0) >= min_profit
            ]

            lines = [f"💹 Arbitrage Opportunities ({len(filtered)}):"]
            for op in filtered[:limit]:
                title = op.get("title", "Unknown")
                profit = op.get("profit_percent", 0)
                buy_price = op.get("buy_price", 0)
                sell_price = op.get("sell_price", 0)
                lines.append(
                    f"  • {title}\n"
                    f"    Buy: ${buy_price:.2f} → Sell: ${sell_price:.2f}\n"
                    f"    Profit: {profit:.1f}%"
                )

            return ToolResult(
                success=True,
                content=[TextContent(text="\n".join(lines))],
            )

        except Exception as e:
            logger.exception("scan_arbitrage_error", error=str(e))
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error scanning arbitrage: {str(e)}")],
                error=str(e),
            )

    async def _handle_analyze_liquidity(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle analyze_liquidity tool."""
        from src.dmarket.liquidity_analyzer import LiquidityAnalyzer

        analyzer = LiquidityAnalyzer(api_client=api)

        game = args["game"]
        title = args["title"]
        days = args.get("days", 7)

        try:
            result = await analyzer.analyze_item_liquidity(
                game=game,
                title=title,
                days=days,
            )

            text = (
                f"📊 Liquidity Analysis for '{title}':\n"
                f"  • Sales Count (last {days}d): {result.get('sales_count', 0)}\n"
                f"  • Avg Daily Sales: {result.get('avg_daily_sales', 0):.1f}\n"
                f"  • Liquidity Score: {result.get('liquidity_score', 0):.1f}/100\n"
                f"  • Recommendation: {result.get('recommendation', 'N/A')}"
            )
            return ToolResult(
                success=True,
                content=[TextContent(text=text)],
            )

        except Exception as e:
            logger.exception("analyze_liquidity_error", error=str(e))
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error analyzing liquidity: {str(e)}")],
                error=str(e),
            )

    async def _handle_get_sales_history(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle get_sales_history tool."""
        game = args["game"]
        title = args["title"]
        days = args.get("days", 7)

        response = await api.get_sales_history(
            game=game,
            title=title,
            days=days,
        )

        sales = response.get("sales", [])
        if not sales:
            return ToolResult(
                success=True,
                content=[TextContent(text=f"No sales history found for '{title}'")],
            )

        lines = [f"📜 Sales History for '{title}' (last {days} days):"]
        for sale in sales[:10]:
            price = int(sale.get("price", 0)) / 100
            date = sale.get("date", "Unknown")
            lines.append(f"  • ${price:.2f} on {date}")

        if len(sales) > 10:
            lines.append(f"  ... and {len(sales) - 10} more sales")

        return ToolResult(
            success=True,
            content=[TextContent(text="\n".join(lines))],
        )

    async def _handle_get_buy_orders_competition(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle get_buy_orders_competition tool."""
        game = args["game"]
        title = args["title"]
        price_threshold = args.get("price_threshold")

        game_ids = {"csgo": "csgo", "dota2": "dota2", "tf2": "tf2", "rust": "rust"}
        game_id = game_ids.get(game, game)

        result = await api.get_buy_orders_competition(
            game_id=game_id,
            title=title,
            price_threshold=price_threshold,
        )

        text = (
            f"🏆 Competition Analysis for '{title}':\n"
            f"  • Total Orders: {result.get('total_orders', 0)}\n"
            f"  • Total Amount: {result.get('total_amount', 0)}\n"
            f"  • Competition Level: {result.get('competition_level', 'unknown')}\n"
            f"  • Best Price: ${result.get('best_price', 0):.2f}\n"
            f"  • Average Price: ${result.get('average_price', 0):.2f}"
        )
        return ToolResult(
            success=True,
            content=[TextContent(text=text)],
        )

    async def _handle_buy_item(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle buy_item tool."""
        item_id = args["item_id"]
        price = args["price"]
        game = args.get("game", "csgo")

        if self.dry_run:
            return ToolResult(
                success=True,
                content=[TextContent(
                    text=f"🔵 [DRY-RUN] Would buy item {item_id} for ${price:.2f}"
                )],
            )

        result = await api.buy_item(
            item_id=item_id,
            price=price,
            game=game,
        )

        if result.get("error"):
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error: {result.get('message', 'Purchase failed')}")],
                error=result.get("message"),
            )

        return ToolResult(
            success=True,
            content=[TextContent(text=f"✅ Purchased item {item_id} for ${price:.2f}")],
        )

    async def _handle_sell_item(
        self, api: Any, args: dict[str, Any]
    ) -> ToolResult:
        """Handle sell_item tool."""
        item_id = args["item_id"]
        price = args["price"]
        game = args.get("game", "csgo")

        if self.dry_run:
            return ToolResult(
                success=True,
                content=[TextContent(
                    text=f"🔵 [DRY-RUN] Would list item {item_id} for ${price:.2f}"
                )],
            )

        result = await api.sell_item(
            item_id=item_id,
            price=price,
            game=game,
        )

        if result.get("error"):
            return ToolResult(
                success=False,
                content=[TextContent(text=f"Error: {result.get('message', 'Listing failed')}")],
                error=result.get("message"),
            )

        return ToolResult(
            success=True,
            content=[TextContent(text=f"✅ Listed item {item_id} for ${price:.2f}")],
        )

    async def run(self) -> None:
        """Run MCP server using stdio transport."""
        logger.info("Starting DMarket MCP Server...")

        # Simple JSON-RPC over stdio
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})

                if method == "list_tools":
                    result = await self.list_tools()
                elif method == "call_tool":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    tool_result = await self.call_tool(tool_name, arguments)
                    result = tool_result.to_dict()
                else:
                    result = {"error": f"Unknown method: {method}"}

                response = json.dumps({"result": result})
                print(response, flush=True)

            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception("mcp_server_error", error=str(e))
                response = json.dumps({"error": str(e)})
                print(response, flush=True)


def create_dmarket_mcp_server(
    public_key: str | None = None,
    secret_key: str | None = None,
    dry_run: bool = True,
) -> DMarketMCPServer:
    """Factory function to create DMarket MCP Server.

    Args:
        public_key: DMarket API public key
        secret_key: DMarket API secret key
        dry_run: Enable dry-run mode (no real trades)

    Returns:
        Configured DMarketMCPServer instance

    """
    return DMarketMCPServer(
        public_key=public_key,
        secret_key=secret_key,
        dry_run=dry_run,
    )


async def main() -> None:
    """Main entry point for MCP server."""
    server = create_dmarket_mcp_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

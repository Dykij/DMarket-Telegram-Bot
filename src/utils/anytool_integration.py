"""
AnyTool Integration для DMarket Telegram Bot.

Модуль для интеграции с AnyTool через MCP (Model Context Protocol).
"""

import asyncio
from collections.abc import Callable
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
import structlog

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.config import settings


logger = structlog.get_logger(__name__)


class AnyToolConfig(BaseModel):
    """Конфигурация AnyTool."""

    mcp_server_path: str = Field(
        default="src.mcp_server.dmarket_mcp:main",
        description="Путь к MCP серверу",
    )
    timeout: int = Field(default=30, description="Таймаут запроса в секундах")
    max_retries: int = Field(default=3, description="Максимум попыток")
    enabled: bool = Field(default=True, description="Включена ли интеграция")


class AnyToolClient:
    """Клиент для работы с AnyTool через MCP."""

    def __init__(
        self,
        config: AnyToolConfig | None = None,
        api_client: DMarketAPI | None = None,
    ):
        """
        Инициализация AnyTool клиента.

        Args:
            config: Конфигурация AnyTool
            api_client: Клиент DMarket API
        """
        self.config = config or AnyToolConfig()
        self.api_client = api_client or DMarketAPI(
            public_key=settings.dmarket.public_key,
            secret_key=settings.dmarket.secret_key,
        )
        self._callbacks: dict[str, list[Callable]] = {}

    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Регистрация callback для события.

        Args:
            event: Название события
            callback: Функция callback
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
        logger.debug("callback_registered", event_name=event)

    async def _trigger_callbacks(self, event: str, data: Any) -> None:
        """Запуск callbacks для события."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(
                        "callback_error",
                        event_name=event,
                        error=str(e),
                        exc_info=True,
                    )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Вызов MCP инструмента.

        Args:
            tool_name: Название инструмента
            arguments: Аргументы для инструмента

        Returns:
            Результат выполнения

        Raises:
            ValueError: При ошибке вызова инструмента
        """
        if not self.config.enabled:
            raise ValueError("AnyTool integration is disabled")

        logger.info("anytool_call", tool=tool_name, arguments=arguments)

        try:
            # Прямой вызов через API клиент
            result = await self._execute_tool(tool_name, arguments)

            await self._trigger_callbacks(
                "tool_called",
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                },
            )

            return result

        except Exception as e:
            logger.error(
                "anytool_call_failed",
                tool=tool_name,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Выполнение инструмента."""
        if tool_name == "get_balance":
            balance = await self.api_client.get_balance()
            return {"success": True, "balance": balance}

        if tool_name == "get_market_items":
            items = await self.api_client.get_market_items(
                game=arguments["game"],
                limit=arguments.get("limit", 10),
                price_from=arguments.get("price_from"),
                price_to=arguments.get("price_to"),
            )
            return {
                "success": True,
                "items": items.get("objects", []),
            }

        if tool_name == "scan_arbitrage":
            from src.dmarket.arbitrage_scanner import ArbitrageScanner

            scanner = ArbitrageScanner(api_client=self.api_client)
            opportunities = await scanner.scan_level(
                level=arguments.get("level", "standard"),
                game=arguments["game"],
            )

            min_profit = arguments.get("min_profit", 0.5)
            filtered = [opp for opp in opportunities if opp.get("profit", 0) >= min_profit]

            return {
                "success": True,
                "opportunities": filtered,
            }

        if tool_name == "get_item_details":
            details = await self.api_client.get_item_by_id(arguments["item_id"])
            return {"success": True, "item": details}

        if tool_name == "create_target":
            from src.dmarket.targets import TargetManager

            target_manager = TargetManager(api_client=self.api_client)
            target = await target_manager.create_target(
                game=arguments["game"],
                title=arguments["title"],
                price=arguments["price"],
                amount=arguments.get("amount", 1),
            )
            return {"success": True, "target": target}

        if tool_name == "get_targets":
            from src.dmarket.targets import TargetManager

            target_manager = TargetManager(api_client=self.api_client)
            targets = await target_manager.get_all_targets()
            return {"success": True, "targets": targets}

        raise ValueError(f"Unknown tool: {tool_name}")

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Получить список доступных инструментов."""
        return [
            {
                "name": "get_balance",
                "description": "Получить баланс на DMarket",
                "parameters": {},
            },
            {
                "name": "get_market_items",
                "description": "Получить предметы рынка",
                "parameters": {
                    "game": "str (required)",
                    "limit": "int (optional, default: 10)",
                    "price_from": "int (optional)",
                    "price_to": "int (optional)",
                },
            },
            {
                "name": "scan_arbitrage",
                "description": "Сканировать арбитраж",
                "parameters": {
                    "game": "str (required)",
                    "level": "str (optional, default: standard)",
                    "min_profit": "float (optional, default: 0.5)",
                },
            },
            {
                "name": "get_item_details",
                "description": "Получить детали предмета",
                "parameters": {"item_id": "str (required)"},
            },
            {
                "name": "create_target",
                "description": "Создать buy order",
                "parameters": {
                    "game": "str (required)",
                    "title": "str (required)",
                    "price": "float (required)",
                    "amount": "int (optional, default: 1)",
                },
            },
            {
                "name": "get_targets",
                "description": "Получить активные таргеты",
                "parameters": {},
            },
        ]

    def export_config(self, path: str | Path) -> None:
        """
        Экспорт конфигурации в JSON файл.

        Args:
            path: Путь к файлу конфигурации
        """
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            "mcpServers": {
                "dmarket-bot": {
                    "command": "python",
                    "args": [
                        "-m",
                        self.config.mcp_server_path.replace(":", "."),
                    ],
                    "env": {
                        "DMARKET_PUBLIC_KEY": settings.dmarket_public_key,
                        "DMARKET_SECRET_KEY": settings.dmarket_secret_key,
                    },
                }
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info("anytool_config_exported", path=str(config_path))


# Глобальный клиент AnyTool
_anytool_client: AnyToolClient | None = None


def get_anytool_client() -> AnyToolClient:
    """Получить глобальный экземпляр AnyTool клиента."""
    global _anytool_client
    if _anytool_client is None:
        _anytool_client = AnyToolClient()
    return _anytool_client


async def initialize_anytool(config_path: str | Path | None = None) -> AnyToolClient:
    """
    Инициализация AnyTool интеграции.

    Args:
        config_path: Путь к файлу конфигурации (опционально)

    Returns:
        Инициализированный клиент AnyTool
    """
    client = get_anytool_client()

    if config_path:
        client.export_config(config_path)

    logger.info("anytool_initialized")
    return client

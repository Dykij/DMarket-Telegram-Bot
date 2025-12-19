"""AnyTool integration for DMarket Trading Bot.

This module provides safe integration with AnyTool - Universal Tool-Use Layer
for AI agents. It configures AnyTool to work ONLY with allowed backends
(MCP, Shell) while blocking prohibited ones (GUI, Web) per DMarket ToS.

Example usage:
    from src.utils.anytool_integration import (
        create_safe_anytool_config,
        execute_safe_task,
    )

    # Execute a task safely
    result = await execute_safe_task(
        "Найди арбитражные возможности для CS:GO с прибылью > 10%"
    )

Note:
    GUI and Web backends are BLOCKED to comply with DMarket Terms of Service.
    Only API calls via MCP and local shell operations are allowed.

Documentation:
    - AnyTool: https://github.com/HKUDS/AnyTool
    - DMarket ToS: https://dmarket.com/terms-of-use
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


# ==================== AnyTool Configuration ====================


@dataclass
class AnyToolConfig:
    """Safe configuration for AnyTool with DMarket ToS compliance.

    This configuration ONLY allows:
    - MCP backend (for API calls via Model Context Protocol)
    - Shell backend (for local operations like tests, scripts)
    - System backend (for local file operations)

    BLOCKED backends (violate DMarket ToS):
    - GUI backend (browser/desktop automation)
    - Web backend (web scraping, headless browsing)

    Attributes:
        llm_model: LLM model to use for task execution
        llm_enable_thinking: Enable chain-of-thought reasoning
        llm_timeout: Timeout for LLM calls in seconds
        backend_scope: List of allowed backends
        enable_recording: Enable task recording for audit
        recording_backends: Backends to record
        recording_log_dir: Directory for recording logs
        log_level: Logging level
        mcp_config_path: Path to MCP server configuration
        dry_run: Enable dry-run mode (no real trades)

    """

    # LLM Configuration
    llm_model: str = "anthropic/claude-sonnet-4-5"
    llm_enable_thinking: bool = False
    llm_timeout: float = 120.0

    # Backend Configuration - ONLY safe backends
    # ⚠️ IMPORTANT: "gui" and "web" are BLOCKED per DMarket ToS
    backend_scope: list[str] = field(
        default_factory=lambda: ["mcp", "shell", "system"]
    )

    # Recording for audit trail
    enable_recording: bool = True
    recording_backends: list[str] = field(
        default_factory=lambda: ["mcp", "shell"]
    )
    recording_log_dir: str = "./logs/anytool"

    # Logging
    log_level: str = "INFO"

    # MCP Configuration
    mcp_config_path: str = "./anytool/config/config_mcp.json"

    # Trading mode
    dry_run: bool = True

    def validate(self) -> bool:
        """Validate configuration for DMarket ToS compliance.

        Returns:
            True if configuration is safe, False otherwise

        Raises:
            ValueError: If prohibited backends are included

        """
        prohibited = {"gui", "web"}
        included_prohibited = set(self.backend_scope) & prohibited

        if included_prohibited:
            raise ValueError(
                f"⛔ BLOCKED: Backends {included_prohibited} are prohibited by DMarket ToS!\n"
                f"DMarket Terms of Service explicitly forbid:\n"
                f"  - GUI automation (robots, automated means)\n"
                f"  - Web scraping (spiders, scrapers)\n"
                f"  - Browser automation (headless browsing)\n"
                f"\n"
                f"Only API calls via official Trading API are allowed.\n"
                f"Allowed backends: mcp, shell, system"
            )

        logger.info(
            "anytool_config_validated",
            backends=self.backend_scope,
            dry_run=self.dry_run,
            recording_enabled=self.enable_recording,
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary

        """
        return {
            "llm": {
                "model": self.llm_model,
                "enable_thinking": self.llm_enable_thinking,
                "timeout": self.llm_timeout,
            },
            "backends": {
                "scope": self.backend_scope,
            },
            "recording": {
                "enabled": self.enable_recording,
                "backends": self.recording_backends,
                "log_dir": self.recording_log_dir,
            },
            "logging": {
                "level": self.log_level,
            },
            "mcp": {
                "config_path": self.mcp_config_path,
            },
            "trading": {
                "dry_run": self.dry_run,
            },
        }


def create_safe_anytool_config(
    dry_run: bool = True,
    log_level: str = "INFO",
    enable_recording: bool = True,
) -> AnyToolConfig:
    """Create a safe AnyTool configuration for DMarket integration.

    This function creates a configuration that is compliant with DMarket ToS
    by only enabling safe backends (MCP, Shell, System).

    Args:
        dry_run: Enable dry-run mode (no real trades)
        log_level: Logging level
        enable_recording: Enable task recording for audit

    Returns:
        Safe AnyToolConfig instance

    Example:
        config = create_safe_anytool_config(dry_run=True)
        # GUI and Web backends are automatically blocked

    """
    config = AnyToolConfig(
        # Only safe backends - GUI and Web are NOT included
        backend_scope=["mcp", "shell", "system"],
        dry_run=dry_run,
        log_level=log_level,
        enable_recording=enable_recording,
        recording_log_dir="./logs/anytool",
        mcp_config_path="./anytool/config/config_mcp.json",
    )

    # Validate to ensure no prohibited backends
    config.validate()

    return config


# ==================== AnyTool Integration ====================


class AnyToolIntegration:
    """Integration layer for AnyTool with DMarket Trading Bot.

    This class provides a safe wrapper around AnyTool that:
    1. Blocks prohibited backends (GUI, Web) per DMarket ToS
    2. Routes tasks to appropriate MCP servers
    3. Records all operations for audit
    4. Supports dry-run mode for testing

    Example:
        integration = AnyToolIntegration(dry_run=True)
        result = await integration.execute(
            "Получи баланс моего аккаунта DMarket"
        )

    """

    def __init__(
        self,
        config: AnyToolConfig | None = None,
        dry_run: bool = True,
    ) -> None:
        """Initialize AnyTool integration.

        Args:
            config: AnyTool configuration (creates safe default if None)
            dry_run: Enable dry-run mode

        """
        self.config = config or create_safe_anytool_config(dry_run=dry_run)
        self.dry_run = dry_run
        self._anytool_instance: Any = None
        self._is_available = False

        # Check if AnyTool is installed
        self._check_anytool_availability()

        logger.info(
            "anytool_integration_initialized",
            dry_run=dry_run,
            is_available=self._is_available,
        )

    def _check_anytool_availability(self) -> None:
        """Check if AnyTool package is available."""
        try:
            # Try to import AnyTool
            # Note: AnyTool may not be on PyPI, install from GitHub
            import importlib.util

            spec = importlib.util.find_spec("anytool")
            self._is_available = spec is not None

            if not self._is_available:
                logger.warning(
                    "anytool_not_installed",
                    message="AnyTool is not installed. Install from GitHub: "
                    "pip install git+https://github.com/HKUDS/AnyTool.git",
                )
        except ImportError:
            self._is_available = False
            logger.warning(
                "anytool_import_error",
                message="Could not import AnyTool. Using fallback MCP server.",
            )

    @property
    def is_available(self) -> bool:
        """Check if AnyTool is available.

        Returns:
            True if AnyTool is installed and available

        """
        return self._is_available

    async def execute(self, task: str) -> dict[str, Any]:
        """Execute a task through AnyTool safely.

        This method routes the task through AnyTool with safe configuration.
        If AnyTool is not available, falls back to direct MCP server calls.

        Args:
            task: Natural language task description

        Returns:
            Task execution result

        Example:
            result = await integration.execute(
                "Найди арбитражные возможности для CS:GO"
            )

        """
        logger.info("anytool_execute_task", task=task[:100])

        # Validate task doesn't request prohibited operations
        self._validate_task(task)

        if self._is_available:
            return await self._execute_with_anytool(task)
        else:
            return await self._execute_with_fallback(task)

    def _validate_task(self, task: str) -> None:
        """Validate task doesn't request prohibited operations.

        Args:
            task: Task description

        Raises:
            ValueError: If task requests prohibited operations

        """
        prohibited_keywords = [
            "browser",
            "selenium",
            "puppeteer",
            "headless",
            "scrape",
            "scraping",
            "web page",
            "screenshot",
            "click button",
            "fill form",
            "navigate to",
            "open website",
            "dmarket.com",  # Direct website access
        ]

        task_lower = task.lower()
        for keyword in prohibited_keywords:
            if keyword in task_lower:
                raise ValueError(
                    f"⛔ BLOCKED: Task contains prohibited operation '{keyword}'.\n"
                    f"DMarket ToS prohibits GUI/Web automation.\n"
                    f"Use DMarket Trading API via MCP server instead."
                )

    async def _execute_with_anytool(self, task: str) -> dict[str, Any]:
        """Execute task using AnyTool.

        Args:
            task: Task description

        Returns:
            Execution result

        """
        try:
            from anytool import AnyTool

            # Create AnyTool instance with safe config
            async with AnyTool(config=self.config.to_dict()) as tool_layer:
                result = await tool_layer.execute(task)
                return {
                    "success": True,
                    "result": result,
                    "method": "anytool",
                }

        except Exception as e:
            logger.exception("anytool_execution_error", error=str(e))
            # Fallback to direct MCP server
            return await self._execute_with_fallback(task)

    async def _execute_with_fallback(self, task: str) -> dict[str, Any]:
        """Execute task using fallback MCP server directly.

        This is used when AnyTool is not available.

        Args:
            task: Task description

        Returns:
            Execution result

        """
        logger.info("anytool_fallback_execution", task=task[:50])

        try:
            from src.mcp_server.dmarket_mcp import create_dmarket_mcp_server

            # Create MCP server
            server = create_dmarket_mcp_server(dry_run=self.dry_run)

            # Parse task to determine tool to call
            tool_name, arguments = self._parse_task(task)

            if tool_name:
                result = await server.call_tool(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content[0].text if result.content else "",
                    "error": result.error,
                    "method": "fallback_mcp",
                }
            else:
                return {
                    "success": False,
                    "error": "Could not parse task to MCP tool call",
                    "method": "fallback_mcp",
                }

        except Exception as e:
            logger.exception("fallback_execution_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "method": "fallback_mcp",
            }

    def _parse_task(self, task: str) -> tuple[str | None, dict[str, Any]]:
        """Parse natural language task to MCP tool call.

        This is a simple parser for common tasks. AnyTool provides
        more sophisticated parsing with LLM.

        Args:
            task: Task description

        Returns:
            Tuple of (tool_name, arguments)

        """
        task_lower = task.lower()

        # Balance queries
        if any(
            keyword in task_lower
            for keyword in ["баланс", "balance", "деньги", "money", "сколько"]
        ):
            return "get_balance", {}

        # Arbitrage queries
        if any(
            keyword in task_lower
            for keyword in ["арбитраж", "arbitrage", "прибыль", "profit"]
        ):
            game = "csgo"
            if "dota" in task_lower:
                game = "dota2"
            elif "rust" in task_lower:
                game = "rust"
            elif "tf2" in task_lower:
                game = "tf2"

            return "scan_arbitrage", {
                "game": game,
                "level": "standard",
                "min_profit_percent": 5.0,
            }

        # Target queries
        if any(
            keyword in task_lower
            for keyword in ["таргет", "target", "buy order", "заказ"]
        ):
            return "get_user_targets", {"game": "csgo"}

        # Market queries
        if any(
            keyword in task_lower
            for keyword in ["предмет", "item", "маркет", "market", "товар"]
        ):
            return "get_market_items", {"game": "csgo", "limit": 10}

        # Sales history
        if any(
            keyword in task_lower
            for keyword in ["история", "history", "продаж", "sales"]
        ):
            # Need item title for this
            return None, {}

        # Default - couldn't parse
        return None, {}

    async def close(self) -> None:
        """Close AnyTool integration and cleanup resources."""
        if self._anytool_instance is not None:
            try:
                await self._anytool_instance.close()
            except Exception as e:
                logger.exception("anytool_close_error", error=str(e))

        self._anytool_instance = None
        logger.info("anytool_integration_closed")


# ==================== Convenience Functions ====================


async def execute_safe_task(
    task: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute a task safely through AnyTool.

    This is a convenience function that creates an integration,
    executes the task, and closes the integration.

    Args:
        task: Natural language task description
        dry_run: Enable dry-run mode

    Returns:
        Task execution result

    Example:
        result = await execute_safe_task(
            "Получи мой баланс на DMarket",
            dry_run=True
        )

    """
    integration = AnyToolIntegration(dry_run=dry_run)

    try:
        return await integration.execute(task)
    finally:
        await integration.close()


def get_anytool_status() -> dict[str, Any]:
    """Get status of AnyTool integration.

    Returns:
        Status information including:
        - is_installed: Whether AnyTool package is installed
        - config_path: Path to MCP configuration
        - allowed_backends: List of allowed backends
        - blocked_backends: List of blocked backends

    """
    # Check if AnyTool is installed
    is_installed = False
    try:
        import importlib.util

        spec = importlib.util.find_spec("anytool")
        is_installed = spec is not None
    except ImportError:
        pass

    # Check config file
    config_path = Path("./anytool/config/config_mcp.json")
    config_exists = config_path.exists()

    return {
        "is_installed": is_installed,
        "install_command": "pip install git+https://github.com/HKUDS/AnyTool.git",
        "config_path": str(config_path),
        "config_exists": config_exists,
        "allowed_backends": ["mcp", "shell", "system"],
        "blocked_backends": ["gui", "web"],
        "dmarket_tos_compliant": True,
        "mcp_server_available": True,
    }


# ==================== Module Exports ====================

__all__ = [
    "AnyToolConfig",
    "AnyToolIntegration",
    "create_safe_anytool_config",
    "execute_safe_task",
    "get_anytool_status",
]

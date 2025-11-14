"""Enhanced DMarket Bot wrapper for main entry point compatibility.

This module provides a wrapper around the existing bot implementation
to integrate with the new main entry point and configuration system.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from src.dmarket.dmarket_api import DMarketAPI
from src.telegram_bot.initialization import initialize_bot_application
from src.utils.config import Config
from src.utils.database import DatabaseManager


if TYPE_CHECKING:
    from telegram.ext import Application


logger = logging.getLogger(__name__)


class DMarketBot:
    """Enhanced DMarket Bot wrapper."""

    def __init__(
        self,
        config: Config,
        dmarket_api: DMarketAPI,
        database: DatabaseManager | None = None,
    ) -> None:
        """Initialize bot wrapper.

        Args:
            config: Application configuration
            dmarket_api: DMarket API client
            database: Database manager (optional)

        """
        self.config = config
        self.dmarket_api = dmarket_api
        self.database = database
        self.application: Application | None = None

    async def initialize(self) -> None:
        """Initialize the bot application."""
        logger.info("Initializing DMarket Bot...")

        # Create the telegram application using initialization module
        self.application = await initialize_bot_application(
            token=self.config.bot.token,
            setup_persistence=True,
        )

        # Add DMarket API and database to bot_data for handlers to access
        self.application.bot_data["dmarket_api"] = self.dmarket_api
        if self.database:
            self.application.bot_data["database"] = self.database

        # Add config to bot_data
        self.application.bot_data["config"] = self.config

        # Register all bot handlers
        from src.telegram_bot.register_all_handlers import register_all_handlers

        register_all_handlers(self.application)

        logger.info("DMarket Bot initialized successfully")

    async def start(self) -> None:
        """Start the bot."""
        if not self.application:
            msg = "Bot not initialized. Call initialize() first."
            raise RuntimeError(msg)

        logger.info("Starting DMarket Bot...")

        # Use webhook if configured, otherwise use polling
        if self.config.bot.webhook_url:
            await self._start_webhook()
        else:
            await self._start_polling()

    async def stop(self) -> None:
        """Stop the bot."""
        if self.application:
            logger.info("Stopping DMarket Bot...")
            try:
                await self.application.stop()
                await self.application.shutdown()
            except RuntimeError as e:
                if "not running" not in str(e).lower():
                    raise
                logger.debug(f"Application was not running: {e}")
            logger.info("DMarket Bot stopped")

    async def _start_webhook(self) -> None:
        """Start bot with webhook."""
        logger.info(f"Starting webhook mode: {self.config.bot.webhook_url}")

        # Initialize and start the application
        await self.application.initialize()
        await self.application.start()

        # Set webhook
        await self.application.bot.set_webhook(
            url=self.config.bot.webhook_url,
            secret_token=self.config.bot.webhook_secret,
        )

        logger.info("Webhook mode started")

        # Keep running (in production this would be handled by web server)
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def _start_polling(self) -> None:
        """Start bot with polling."""
        logger.info("Starting polling mode...")

        # Initialize and start the application
        await self.application.initialize()
        await self.application.start()

        # Start polling
        await self.application.updater.start_polling(
            poll_interval=1.0,
            timeout=10,
            bootstrap_retries=-1,
        )

        logger.info("Polling mode started")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

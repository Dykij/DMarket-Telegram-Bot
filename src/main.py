"""Main entry point for DMarket Telegram Bot.

This module provides the main entry point for running the DMarket Telegram Bot,
including initialization, configuration loading, and graceful shutdown handling.
"""

import asyncio
import logging
import signal
import sys

from telegram.ext import Application as TelegramApplication
from telegram.ext import ApplicationBuilder

from src.dmarket.dmarket_api import DMarketAPI
from src.telegram_bot.register_all_handlers import register_all_handlers
from src.utils.config import Config
from src.utils.database import DatabaseManager
from src.utils.logging_utils import setup_logging


logger = logging.getLogger(__name__)


class Application:
    """Main application class for DMarket Bot."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize application.

        Args:
            config_path: Optional path to configuration file

        """
        self.config_path = config_path
        self.config: Config | None = None
        self.database: DatabaseManager | None = None
        self.dmarket_api: DMarketAPI | None = None
        self.bot: TelegramApplication | None = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize all application components."""
        try:
            # Load configuration
            logger.info("Loading configuration...")
            self.config = Config.load(self.config_path)
            self.config.validate()

            # Setup logging
            setup_logging(
                level=self.config.logging.level,
                log_file=self.config.logging.file,
                format_string=self.config.logging.format,
            )

            logger.info("Configuration loaded successfully")
            logger.info(f"Debug mode: {self.config.debug}")
            logger.info(f"Testing mode: {self.config.testing}")

            # Initialize database
            if not self.config.testing:
                logger.info("Initializing database...")
                self.database = DatabaseManager(
                    database_url=self.config.database.url,
                    echo=self.config.debug,
                )
                await self.database.init_database()
                logger.info("Database initialized successfully")

            # Initialize DMarket API
            logger.info("Initializing DMarket API...")
            self.dmarket_api = DMarketAPI(
                public_key=self.config.dmarket.public_key,
                secret_key=self.config.dmarket.secret_key,
                api_url=self.config.dmarket.api_url,
            )

            # Test API connection if not in testing mode
            if not self.config.testing and self.config.dmarket.public_key:
                try:
                    balance_result = await self.dmarket_api.get_balance()
                    if balance_result.get("error"):
                        logger.warning(
                            f"DMarket API test failed: {balance_result.get('error_message', 'Unknown error')}",
                        )
                    else:
                        logger.info(
                            f"DMarket API connected. Balance: ${balance_result.get('balance', 0):.2f}",
                        )
                except Exception as e:
                    logger.warning(f"DMarket API test failed: {e}")

            # Initialize Telegram Bot
            logger.info("Initializing Telegram Bot...")

            if not self.config.telegram.bot_token:
                raise ValueError("Telegram bot token is not configured")

            builder = ApplicationBuilder().token(
                self.config.telegram.bot_token,
            )
            self.bot = builder.build()

            # Store dependencies in bot_data
            self.bot.bot_data["config"] = self.config
            self.bot.bot_data["dmarket_api"] = self.dmarket_api
            self.bot.bot_data["database"] = self.database

            # Register handlers
            register_all_handlers(self.bot)

            # Initialize application
            await self.bot.initialize()

            logger.info("Telegram Bot initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize application: {e}")
            raise

    async def run(self) -> None:
        """Run the application."""
        try:
            await self.initialize()

            # Setup signal handlers
            self._setup_signal_handlers()

            logger.info("Starting DMarket Telegram Bot...")

            # Start the bot
            if self.bot:
                await self.bot.start()
                await self.bot.updater.start_polling()
                logger.info("Bot polling started")

            # Wait for shutdown signal
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await self._shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.exception(f"Application error: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logger.info("Shutting down application...")

        try:
            # Stop the bot
            if self.bot:
                logger.info("Stopping Telegram Bot...")
                if self.bot.updater.running:
                    await self.bot.updater.stop()
                if self.bot.running:
                    await self.bot.stop()
                await self.bot.shutdown()
                logger.info("Telegram Bot stopped")

            # Close DMarket API connections
            if self.dmarket_api:
                logger.info("Closing DMarket API connections...")
                await self.dmarket_api._close_client()
                logger.info("DMarket API connections closed")

            # Close database connections
            if self.database:
                logger.info("Closing database connections...")
                await self.database.close()
                logger.info("Database connections closed")

        except Exception as e:
            logger.exception(f"Error during shutdown: {e}")

        logger.info("Application shutdown complete")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(sig: int, frame: object) -> None:
            logger.info(f"Received signal {sig}")
            self._shutdown_event.set()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Windows doesn't have SIGQUIT
        if hasattr(signal, "SIGQUIT"):
            signal.signal(signal.SIGQUIT, signal_handler)


async def main() -> None:
    """Main entry point."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="DMarket Telegram Bot")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level",
    )

    args = parser.parse_args()

    # Setup basic logging first
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Override config with command line arguments
    if args.debug:
        import os

        os.environ["DEBUG"] = "true"
        os.environ["LOG_LEVEL"] = "DEBUG"

    # Create and run application
    app = Application(config_path=args.config)

    try:
        await app.run()
    except Exception as e:
        logger.critical(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure proper event loop policy on Windows
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Run the application
    asyncio.run(main())

"""Main entry point for DMarket Telegram Bot.

This module provides the main entry point for running the DMarket Telegram Bot,
including initialization, configuration loading, and graceful shutdown handling.
"""

import asyncio
import logging
import os
import signal
import sys

from telegram.ext import Application as TelegramApplication, ApplicationBuilder

from src.dmarket.dmarket_api import DMarketAPI
from src.telegram_bot.notifier import send_crash_notification, send_critical_shutdown_notification
from src.telegram_bot.register_all_handlers import register_all_handlers
from src.utils.config import Config
from src.utils.daily_report_scheduler import DailyReportScheduler
from src.utils.database import DatabaseManager
from src.utils.logging_utils import BotLogger, setup_logging
from src.utils.sentry_integration import init_sentry
from src.utils.state_manager import StateManager


logger = logging.getLogger(__name__)
bot_logger = BotLogger(__name__)


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
        self.state_manager: StateManager | None = None
        self.daily_report_scheduler: DailyReportScheduler | None = None
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

            # Initialize Sentry for production error monitoring
            if not self.config.testing:
                environment = "production" if not self.config.debug else "development"
                init_sentry(
                    dsn=os.getenv("SENTRY_DSN"),
                    environment=environment,
                    release=os.getenv("SENTRY_RELEASE", "1.0.0"),
                    traces_sample_rate=0.1,
                    profiles_sample_rate=0.1,
                    debug=self.config.debug,
                )
                logger.info(f"Sentry initialized for {environment} environment")

            # Initialize database
            if not self.config.testing:
                logger.info("Initializing database...")
                self.database = DatabaseManager(
                    database_url=self.config.database.url,
                    echo=self.config.debug,
                )
                await self.database.init_database()
                logger.info("Database initialized successfully")

                # Initialize StateManager
                session = self.database.get_async_session()
                self.state_manager = StateManager(
                    session=session,
                    max_consecutive_errors=5,
                )
                logger.info("StateManager initialized")

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

            if not self.config.bot.token:
                raise ValueError("Telegram bot token is not configured")

            builder = ApplicationBuilder().token(
                self.config.bot.token,
            )
            self.bot = builder.build()

            # Store dependencies in bot_data
            self.bot.bot_data["config"] = self.config
            self.bot.bot_data["dmarket_api"] = self.dmarket_api
            self.bot.bot_data["database"] = self.database
            self.bot.bot_data["state_manager"] = self.state_manager

            # Register critical shutdown callback
            if self.state_manager:
                self.state_manager.set_shutdown_callback(
                    self._handle_critical_shutdown,
                )

            # Register handlers
            register_all_handlers(self.bot)

            # Initialize application
            await self.bot.initialize()

            # Setup bot commands for UI autocomplete
            from src.telegram_bot.initialization import setup_bot_commands

            await setup_bot_commands(self.bot.bot)
            logger.info("Bot commands registered for autocomplete UI")

            logger.info("Telegram Bot initialized successfully")

            # Initialize Daily Report Scheduler
            if not self.config.testing and self.database and self.config.daily_report.enabled:
                logger.info("Initializing Daily Report Scheduler...")
                from datetime import time

                admin_users_raw = (
                    self.config.security.admin_users
                    if hasattr(self.config.security, "admin_users")
                    else []
                )

                if not admin_users_raw and hasattr(
                    self.config.security,
                    "allowed_users",
                ):
                    admin_users_raw = self.config.security.allowed_users

                # Convert to list[int] for DailyReportScheduler
                admin_users: list[int] = [int(uid) for uid in admin_users_raw if str(uid).isdigit()]

                report_time = time(
                    hour=self.config.daily_report.report_time_hour,
                    minute=self.config.daily_report.report_time_minute,
                )

                self.daily_report_scheduler = DailyReportScheduler(
                    database=self.database,
                    bot=self.bot.bot,
                    admin_users=admin_users,
                    report_time=report_time,
                    enabled=self.config.daily_report.enabled,
                )

                # Store scheduler in bot_data for command access
                self.bot.bot_data["daily_report_scheduler"] = self.daily_report_scheduler

                logger.info(
                    "Daily Report Scheduler initialized at %s",
                    report_time.strftime("%H:%M"),
                )

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

            # Start Daily Report Scheduler
            if self.daily_report_scheduler:
                await self.daily_report_scheduler.start()
                logger.info("Daily Report Scheduler started")

            # Start the bot
            if self.bot:
                await self.bot.start()
                if self.bot.updater is not None:
                    await self.bot.updater.start_polling()
                logger.info("Bot polling started")

            # Wait for shutdown signal
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await self._shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.exception(f"Application error: {e}")

            # Log crash with BotLogger
            import traceback as tb

            traceback_text = tb.format_exc()
            bot_logger.log_crash(
                error=e,
                traceback_text=traceback_text,
                context={"component": "main_application"},
            )

            # Send crash notification to admins
            await self._send_crash_notifications(
                error=e,
                traceback_text=traceback_text,
            )

            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logger.info("Shutting down application...")

        try:
            # Stop Daily Report Scheduler
            if self.daily_report_scheduler:
                logger.info("Stopping Daily Report Scheduler...")
                await self.daily_report_scheduler.stop()
                logger.info("Daily Report Scheduler stopped")

            # Stop the bot
            if self.bot:
                logger.info("Stopping Telegram Bot...")
                if self.bot.updater is not None and self.bot.updater.running:
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

    async def _handle_critical_shutdown(self, reason: str) -> None:
        """Handle critical shutdown event.

        Args:
            reason: Reason for critical shutdown

        """
        logger.critical(f"CRITICAL SHUTDOWN TRIGGERED: {reason}")

        # Отправить уведомления всем администраторам
        if self.bot and self.config:
            # Получить список администраторов
            admin_users = []
            if hasattr(self.config.security, "admin_users"):
                admin_users = self.config.security.admin_users

            if not admin_users and hasattr(
                self.config.security,
                "allowed_users",
            ):
                # Если нет админов, отправить первому разрешенному
                admin_users = self.config.security.allowed_users[:1]

            # Получить количество ошибок
            consecutive_errors = self.state_manager.consecutive_errors if self.state_manager else 0

            # Отправить уведомления
            for user_id in admin_users:
                try:
                    await send_critical_shutdown_notification(
                        bot=self.bot.bot,
                        user_id=int(user_id),
                        reason=reason,
                        details={"consecutive_errors": consecutive_errors},
                    )
                    logger.info(
                        f"Critical shutdown notification sent to {user_id}",
                    )
                except Exception as e:
                    logger.exception(
                        f"Failed to send shutdown notification to {user_id}: {e}",
                    )

    async def _send_crash_notifications(
        self,
        error: Exception,
        traceback_text: str,
    ) -> None:
        """Send crash notifications to all administrators.

        Args:
            error: Exception that caused the crash
            traceback_text: Full traceback string

        """
        if not self.bot or not self.config:
            return

        # Получить список администраторов
        admin_users = []
        if hasattr(self.config.security, "admin_users"):
            admin_users = self.config.security.admin_users

        if not admin_users and hasattr(self.config.security, "allowed_users"):
            # Если нет админов, отправить первому разрешенному пользователю
            admin_users = self.config.security.allowed_users[:1]

        # Отправить уведомления
        for user_id in admin_users:
            try:
                await send_crash_notification(
                    bot=self.bot.bot,
                    user_id=int(user_id),
                    error_type=type(error).__name__,
                    error_message=str(error),
                    traceback_str=traceback_text,
                )
                logger.info(f"Crash notification sent to user {user_id}")
            except Exception as e:
                logger.exception(
                    f"Failed to send crash notification to {user_id}: {e}",
                )

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
    asyncio.run(main())
    asyncio.run(main())

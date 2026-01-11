"""Main entry point for DMarket Telegram Bot.

This module provides the main entry point for running the DMarket Telegram Bot,
including initialization, configuration loading, and graceful shutdown handling.

Integrated utils modules:
- env_validator: Environment validation on startup
- shutdown_handler: Graceful shutdown handling
- health_monitor: Service health monitoring
- feature_flags: Feature flags management
- discord_notifier: Discord webhook notifications
- prometheus_metrics: Prometheus metrics export
- rate_limit_decorator: Rate limiting for commands
- retry_decorator: Retry logic for API calls
- watchdog: Bot supervision and auto-restart
"""

import asyncio
import logging
import os
import signal
import sys

from telegram.ext import Application as TelegramApplication, ApplicationBuilder, PersistenceInput

from src.dmarket.dmarket_api import DMarketAPI
from src.dmarket.scanner_manager import ScannerManager
from src.telegram_bot.health_check import health_check_server
from src.telegram_bot.notifier import send_crash_notification, send_critical_shutdown_notification
from src.telegram_bot.register_all_handlers import register_all_handlers
from src.utils.config import Config
from src.utils.daily_report_scheduler import DailyReportScheduler
from src.utils.database import DatabaseManager
from src.utils.logging_utils import BotLogger, setup_logging
from src.utils.sentry_integration import init_sentry
from src.utils.state_manager import StateManager

# Optional utils imports - graceful degradation if not available
try:
    from src.utils.env_validator import validate_on_startup
except ImportError:
    validate_on_startup = None

try:
    from src.utils.shutdown_handler import shutdown_handler
except ImportError:
    shutdown_handler = None

try:
    from src.utils.health_monitor import HealthMonitor, HeartbeatConfig
except ImportError:
    HealthMonitor = None
    HeartbeatConfig = None

try:
    from src.utils.feature_flags import init_feature_flags
except ImportError:
    init_feature_flags = None

try:
    from src.utils.discord_notifier import create_discord_notifier_from_env
except ImportError:
    create_discord_notifier_from_env = None

try:
    from src.utils.prometheus_metrics import (
        app_info,
        set_bot_uptime,
        track_command,
    )
except ImportError:
    app_info = None
    set_bot_uptime = None
    track_command = None


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
        self.scanner_manager: ScannerManager | None = None
        self.inventory_manager = None
        self.websocket_manager = None
        self.health_check_monitor = None
        self.ai_scheduler = None  # AI Training Scheduler
        self._shutdown_event = asyncio.Event()
        self._scanner_task: asyncio.Task | None = None
        # New utils integrations
        self.health_monitor = None  # HealthMonitor from utils
        self.feature_flags = None  # FeatureFlagsManager
        self.discord_notifier = None  # DiscordNotifier
        self._start_time = None  # For uptime tracking

    async def initialize(self) -> None:
        """Initialize all application components."""
        try:
            # Track start time for uptime metrics
            import time
            self._start_time = time.time()

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

            # Initialize Prometheus app info (if available)
            if app_info and not self.config.testing:
                app_info.info({
                    "version": os.getenv("APP_VERSION", "1.0.0"),
                    "environment": "production" if not self.config.debug else "development",
                })
                logger.info("Prometheus metrics initialized")

            # Initialize Feature Flags (if available)
            if init_feature_flags and not self.config.testing:
                try:
                    self.feature_flags = init_feature_flags(
                        config_path="config/feature_flags.yaml",
                    )
                    logger.info("Feature flags manager initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize feature flags: {e}")

            # Initialize Discord Notifier (if available)
            if create_discord_notifier_from_env and not self.config.testing:
                try:
                    self.discord_notifier = create_discord_notifier_from_env()
                    if self.discord_notifier.enabled:
                        logger.info("Discord notifier initialized")
                    else:
                        logger.info("Discord notifier disabled (no webhook URL)")
                except Exception as e:
                    logger.warning(f"Failed to initialize Discord notifier: {e}")

            # Load whitelist from JSON file
            try:
                from src.dmarket.whitelist_config import load_whitelist_from_json

                whitelist_path = os.getenv("WHITELIST_PATH", "data/whitelist.json")
                if load_whitelist_from_json(whitelist_path):
                    logger.info(f"Whitelist loaded from {whitelist_path}")
                else:
                    logger.info("Using default whitelist (no JSON file found)")
            except Exception as e:
                logger.warning(f"Failed to load whitelist: {e}")

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
            logger.info(f"DRY_RUN mode: {self.config.dry_run}")
            self.dmarket_api = DMarketAPI(
                public_key=self.config.dmarket.public_key,
                secret_key=self.config.dmarket.secret_key,
                api_url=self.config.dmarket.api_url,
                dry_run=self.config.dry_run,  # Pass dry_run from config
            )

            # Test API connection if not in testing mode
            if not self.config.testing and self.config.dmarket.public_key:
                try:
                    balance_result = await self.dmarket_api.get_balance()
                    if balance_result.get("error"):
                        logger.warning(
                            "DMarket API test failed: "
                            f"{balance_result.get('error_message', 'Unknown error')}",
                        )
                    else:
                        balance_value = balance_result.get("balance", 0)
                        logger.info(
                            f"DMarket API connected. Balance: ${balance_value:.2f}",
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

            # Enable persistence (best practice) with store_data configuration
            if not self.config.testing:
                from telegram.ext import PicklePersistence

                persistence_path = "data/bot_persistence.pickle"
                os.makedirs("data", exist_ok=True)
                # CRITICAL: Exclude bot_data from persistence to avoid pickle errors
                # python-telegram-bot v20+ uses PersistenceInput instead of StoreData
                persistence = PicklePersistence(
                    filepath=persistence_path,
                    store_data=PersistenceInput(
                        bot_data=False,  # Don't persist bot_data (has non-picklable objects)
                        chat_data=True,
                        user_data=True,
                        callback_data=True,
                    ),
                )
                builder.persistence(persistence)
                logger.info(f"Persistence enabled (bot_data excluded): {persistence_path}")

            self.bot = builder.build()

            # Attach database to application for AutopilotOrchestrator (FIX)
            # Use direct attribute assignment (not bot_data) to avoid pickle issues
            self.bot.db = self.database
            logger.info("Database attached as application.db attribute")

            # Clear pending updates on start (best practice)
            if not self.config.testing:
                try:
                    logger.info("Clearing pending updates...")
                    updates = await self.bot.bot.get_updates(timeout=5)
                    if updates:
                        last_id = updates[-1].update_id
                        await self.bot.bot.get_updates(offset=last_id + 1, timeout=1)
                        logger.info(f"Cleared {len(updates)} pending updates")
                    else:
                        logger.info("No pending updates to clear")
                except Exception as e:
                    logger.warning(f"Failed to clear pending updates: {e}")

            # Store non-picklable dependencies as application attributes (not bot_data)
            # This prevents "cannot pickle 'module' object" errors on shutdown
            self.bot.dmarket_api = self.dmarket_api
            self.bot.database = self.database
            self.bot.state_manager = self.state_manager
            self.bot.bot_instance = self

            # Store only picklable config in bot_data for handlers
            self.bot.bot_data["config"] = self.config

            logger.info("Dependencies attached as application attributes (pickle-safe)")

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

                # Store scheduler as application attribute (pickle-safe)
                self.bot.daily_report_scheduler = self.daily_report_scheduler

                logger.info(
                    "Daily Report Scheduler initialized at %s",
                    report_time.strftime("%H:%M"),
                )

            # Initialize AI Training Scheduler (nightly training at 03:00 UTC)
            if not self.config.testing and self.dmarket_api:
                logger.info("Initializing AI Training Scheduler...")
                try:
                    from datetime import time as dt_time

                    from src.utils.ai_scheduler import AITrainingScheduler

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

                    admin_users_ai: list[int] = [
                        int(uid) for uid in admin_users_raw if str(uid).isdigit()
                    ]

                    self.ai_scheduler = AITrainingScheduler(
                        api_client=self.dmarket_api,
                        admin_users=admin_users_ai,
                        bot=self.bot.bot if self.bot else None,
                        training_time=dt_time(3, 0),  # 03:00 UTC nightly training
                        data_collection_interval=300,  # 5 minutes
                        enabled=True,
                    )

                    self.bot.ai_scheduler = self.ai_scheduler

                    logger.info(
                        "AI Training Scheduler initialized (training at 03:00 UTC)"
                    )

                except Exception as e:
                    logger.warning(f"Failed to initialize AI Training Scheduler: {e}")

            # Initialize Scanner Manager (Adaptive, Parallel, Cleanup)
            if not self.config.testing and self.dmarket_api:
                logger.info("Initializing Scanner Manager...")

                # Get scan configuration from config or use defaults
                enable_adaptive = getattr(self.config, "enable_adaptive_scan", True)
                enable_parallel = getattr(self.config, "enable_parallel_scan", True)
                enable_cleanup = getattr(self.config, "enable_target_cleanup", True)

                self.scanner_manager = ScannerManager(
                    api_client=self.dmarket_api,
                    config=self.config,
                    enable_adaptive=enable_adaptive,
                    enable_parallel=enable_parallel,
                    enable_cleanup=enable_cleanup,
                )

                # Store as application attribute (pickle-safe)
                self.bot.scanner_manager = self.scanner_manager

                logger.info(
                    f"Scanner Manager initialized: "
                    f"adaptive={enable_adaptive}, "
                    f"parallel={enable_parallel}, "
                    f"cleanup={enable_cleanup}"
                )

            # Initialize Inventory Manager for Direct Buy mode (NEW)
            if not self.config.testing and self.dmarket_api:
                logger.info("Initializing Inventory Manager (Direct Buy Mode)...")
                try:
                    from src.dmarket.inventory_manager import InventoryManager

                    # Get configuration from config object
                    undercut_step = int(
                        self.config.inventory.undercut_price * 100
                    )  # Convert to cents
                    min_profit_margin = self.config.inventory.min_margin_threshold
                    check_interval = int(os.getenv("INVENTORY_CHECK_INTERVAL", "1800"))
                    undercut_enabled = self.config.inventory.auto_sell

                    self.inventory_manager = InventoryManager(
                        api_client=self.dmarket_api,
                        telegram_bot=self.bot.bot,
                        undercut_step=undercut_step,
                        min_profit_margin=min_profit_margin,
                        check_interval=check_interval,
                    )

                    # Store as application attribute (pickle-safe)
                    self.bot.inventory_manager = self.inventory_manager

                    logger.info(
                        f"Inventory Manager initialized: "
                        f"undercut={'ON' if undercut_enabled else 'OFF'}, "
                        f"step=${undercut_step / 100:.2f}, "
                        f"margin={min_profit_margin:.2%}, "
                        f"interval={check_interval}s"
                    )

                except Exception as e:
                    logger.warning(f"Failed to initialize Inventory Manager: {e}")
                    # Not critical, continue without inventory management

            # Initialize Auto Steam Arbitrage Scanner (NEW - FIX)
            if not self.config.testing and self.dmarket_api:
                logger.info("Initializing Auto Steam Arbitrage Scanner...")
                try:
                    # Get admin chat ID from config
                    admin_users = getattr(self.config.security, "admin_users", [])
                    if not admin_users and hasattr(self.config.security, "allowed_users"):
                        admin_users = self.config.security.allowed_users

                    if admin_users:
                        admin_chat_id = int(admin_users[0])

                        from src.dmarket.auto_steam_arbitrage import AutoSteamArbitrageScanner

                        self.steam_arbitrage_scanner = AutoSteamArbitrageScanner(
                            dmarket_api=self.dmarket_api,
                            telegram_bot=self.bot.bot,
                            admin_chat_id=admin_chat_id,
                            scan_interval_minutes=10,  # Сканировать каждые 10 минут
                            min_roi_percent=5.0,  # Минимум 5% профита
                            max_items_per_scan=50,  # Максимум 50 предметов
                            game="csgo",  # По умолчанию CS:GO
                        )

                        # Store as application attribute (pickle-safe)
                        self.bot.steam_arbitrage_scanner = self.steam_arbitrage_scanner

                        logger.info("Auto Steam Arbitrage Scanner initialized")
                    else:
                        logger.warning("No admin users configured, Steam Scanner skipped")
                except Exception as e:
                    logger.warning(f"Failed to initialize Steam Arbitrage Scanner: {e}")

            # Initialize Autopilot Orchestrator
            logger.info("Initializing Autopilot Orchestrator...")
            try:
                from src.dmarket.auto_buyer import AutoBuyConfig, AutoBuyer
                from src.dmarket.auto_seller import AutoSeller
                from src.dmarket.autopilot_orchestrator import (
                    AutopilotConfig,
                    AutopilotOrchestrator,
                )

                # Initialize auto-buyer if not exists
                auto_buyer = getattr(self.bot, "auto_buyer", None)
                if not auto_buyer:
                    # Read AUTO_BUY_ENABLED from environment (default: False for safety)
                    auto_buy_enabled = os.getenv("AUTO_BUY_ENABLED", "false").lower() == "true"
                    min_discount = float(os.getenv("MIN_DISCOUNT", "30.0"))

                    auto_buy_config = AutoBuyConfig(
                        enabled=auto_buy_enabled,
                        dry_run=self.config.dry_run,
                        max_price_usd=self.config.trading.max_item_price,
                        min_discount_percent=min_discount,
                    )
                    auto_buyer = AutoBuyer(self.dmarket_api, auto_buy_config)
                    self.bot.auto_buyer = auto_buyer

                    if auto_buy_enabled:
                        logger.warning(
                            "AUTO_BUY is ENABLED! Bot will make REAL purchases "
                            f"(dry_run={self.config.dry_run})"
                        )

                # Initialize auto-seller if not exists
                auto_seller = getattr(self.bot, "auto_seller", None)
                if not auto_seller:
                    auto_seller = AutoSeller(
                        api=self.dmarket_api,
                    )
                    self.bot.auto_seller = auto_seller

                # Initialize Trading Persistence (NEW - survives restarts)
                from src.utils.trading_persistence import init_trading_persistence

                trading_persistence = init_trading_persistence(
                    database=self.database,
                    dmarket_api=self.dmarket_api,
                    telegram_bot=self.bot.bot if self.bot else None,
                    min_margin_percent=5.0,  # Minimum 5% margin to protect from losses
                    dmarket_fee_percent=7.0,  # DMarket fee
                )

                # Link persistence to auto-buyer
                auto_buyer.set_trading_persistence(trading_persistence)
                self.bot.trading_persistence = trading_persistence

                logger.info("Trading Persistence initialized - purchases will survive restarts")

                # Create orchestrator config
                orchestrator_config = AutopilotConfig(
                    games=self.config.trading.games,
                    min_discount_percent=30.0,
                    max_price_usd=self.config.trading.max_item_price,
                    min_balance_threshold_usd=10.0,
                )

                # Create orchestrator
                orchestrator = AutopilotOrchestrator(
                    scanner_manager=self.scanner_manager,
                    auto_buyer=auto_buyer,
                    auto_seller=auto_seller,
                    api_client=self.dmarket_api,
                    config=orchestrator_config,
                )

                self.bot.orchestrator = orchestrator

                logger.info("Autopilot Orchestrator initialized successfully")

            except Exception as e:
                logger.warning(f"Failed to initialize Autopilot Orchestrator: {e}")
                # Not critical, continue without autopilot

            # Initialize WebSocket Listener (if not in testing mode)
            if not self.config.testing and self.dmarket_api:
                logger.info("Initializing WebSocket Listener...")
                try:
                    from src.dmarket.websocket_listener import (
                        DMarketWebSocketListener,
                        WebSocketManager,
                    )

                    websocket_listener = DMarketWebSocketListener(
                        public_key=self.config.dmarket.public_key,
                        secret_key=self.config.dmarket.secret_key,
                    )

                    self.websocket_manager = WebSocketManager(websocket_listener)
                    self.bot.websocket_manager = self.websocket_manager

                    logger.info("WebSocket Listener initialized successfully")

                except Exception as e:
                    logger.warning(f"Failed to initialize WebSocket Listener: {e}")
                    # Not critical, continue without websocket

            # Initialize Health Check Monitor (if not in testing mode)
            if not self.config.testing and self.bot:
                logger.info("Initializing Health Check Monitor...")
                try:
                    from src.utils.health_check import HealthCheckMonitor

                    # Get first admin user for health pings
                    admin_users = (
                        self.config.security.admin_users
                        if hasattr(self.config.security, "admin_users")
                        else self.config.security.allowed_users
                    )

                    if admin_users:
                        first_admin = int(admin_users[0])

                        self.health_check_monitor = HealthCheckMonitor(
                            telegram_bot=self.bot.bot,
                            user_id=first_admin,
                            check_interval=900,  # 15 minutes
                            alert_on_failure=True,
                        )

                        # Register components for monitoring
                        if self.dmarket_api is not None:
                            self.health_check_monitor.register_api_client(self.dmarket_api)

                        if self.websocket_manager:
                            self.health_check_monitor.register_websocket(
                                self.websocket_manager.listener
                            )

                        self.bot.health_check_monitor = self.health_check_monitor

                        logger.info("Health Check Monitor initialized successfully")

                except Exception as e:
                    logger.warning(f"Failed to initialize Health Check Monitor: {e}")
                    # Not critical, continue without health check

            # Initialize HealthMonitor from utils (comprehensive service monitoring)
            if not self.config.testing and HealthMonitor:
                logger.info("Initializing HealthMonitor (service monitoring)...")
                try:
                    config = HeartbeatConfig(
                        interval_seconds=60,  # Check every minute
                        timeout_seconds=10,
                        failure_threshold=3,
                        recovery_threshold=2,
                    )

                    self.health_monitor = HealthMonitor(
                        database=self.database,
                        redis_cache=None,  # Will be set later if Redis is initialized
                        dmarket_api_url=self.config.dmarket.api_url,
                        telegram_bot_token=self.config.bot.token,
                        config=config,
                    )

                    # Register Discord alert callback if available
                    if self.discord_notifier and self.discord_notifier.enabled:
                        async def discord_health_alert(result):
                            """Send health alert to Discord."""
                            await self.discord_notifier.send_health_check(
                                status=result.status.value,
                                components={result.service: result.message},
                            )

                        self.health_monitor.register_alert_callback(discord_health_alert)

                    self.bot.health_monitor = self.health_monitor
                    logger.info("HealthMonitor initialized successfully")

                except Exception as e:
                    logger.warning(f"Failed to initialize HealthMonitor: {e}")

            # Store feature flags and discord notifier in bot
            if self.bot:
                if self.feature_flags:
                    self.bot.feature_flags = self.feature_flags
                if self.discord_notifier:
                    self.bot.discord_notifier = self.discord_notifier

        except Exception as e:
            logger.exception(f"Failed to initialize application: {e}")
            raise

    async def run(self) -> None:
        """Run the application."""
        try:
            await self.initialize()

            # Setup signal handlers
            self._setup_signal_handlers()

            # Start health check server (if enabled)
            if health_check_server:
                health_check_server.update_status("starting")
                await health_check_server.start()

            logger.info("Starting DMarket Telegram Bot...")

            # CRITICAL: Recover pending trades from database (NEW)
            # This ensures bot doesn't "forget" purchases after restart
            await self._recover_pending_trades()

            # Start Daily Report Scheduler
            if self.daily_report_scheduler:
                await self.daily_report_scheduler.start()
                logger.info("Daily Report Scheduler started")

            # Start AI Training Scheduler (nightly model training + data collection)
            if self.ai_scheduler:
                await self.ai_scheduler.start()
                logger.info("AI Training Scheduler started (nightly training at 03:00 UTC)")

            # Start Scanner Manager (background scanning)
            if self.scanner_manager and not self.config.testing:
                logger.info("Starting Scanner Manager background task...")

                # Configure which games to scan
                games_to_scan = getattr(
                    self.config, "arbitrage_games", ["csgo", "dota2", "rust", "tf2"]
                )
                arbitrage_level = getattr(self.config, "arbitrage_level", "medium")
                cleanup_interval = getattr(self.config, "cleanup_interval_hours", 6.0)

                self._scanner_task = asyncio.create_task(
                    self.scanner_manager.run_continuous(
                        games=games_to_scan,
                        level=arbitrage_level,
                        enable_cleanup=True,
                        cleanup_interval_hours=cleanup_interval,
                    )
                )

                logger.info(
                    f"Scanner Manager started: "
                    f"games={games_to_scan}, "
                    f"level={arbitrage_level}, "
                    f"cleanup_interval={cleanup_interval}h"
                )

            # Start Inventory Manager (Direct Buy - Undercutting)
            if (
                hasattr(self, "inventory_manager")
                and self.inventory_manager
                and not self.config.testing
            ):
                undercut_enabled = (
                    self.config.inventory.auto_sell
                    if self.config and hasattr(self.config, "inventory")
                    else False
                )
                if undercut_enabled:
                    logger.info("Starting Inventory Manager (Undercutting)...")
                    asyncio.create_task(self.inventory_manager.refresh_inventory_loop())
                    logger.info("Inventory Manager started - auto-repricing enabled")
                else:
                    logger.info("Inventory Manager initialized but undercutting is disabled")

            # Start WebSocket Listener
            if self.websocket_manager:
                logger.info("Starting WebSocket Listener...")
                await self.websocket_manager.start()
                logger.info("WebSocket Listener started - real-time updates enabled")

            # Start Health Check Monitor
            if self.health_check_monitor:
                logger.info("Starting Health Check Monitor...")
                asyncio.create_task(self.health_check_monitor.start())
                logger.info("Health Check Monitor started - 15min intervals")

            # Start HealthMonitor heartbeat (comprehensive service monitoring)
            if self.health_monitor:
                logger.info("Starting HealthMonitor heartbeat...")
                await self.health_monitor.start_heartbeat()
                logger.info("HealthMonitor heartbeat started - 60s intervals")

            # Start uptime tracking (if Prometheus metrics available)
            if set_bot_uptime and self._start_time:
                async def update_uptime():
                    """Update uptime metrics periodically."""
                    import time
                    while True:
                        try:
                            uptime = time.time() - self._start_time
                            set_bot_uptime(uptime)
                            await asyncio.sleep(60)  # Update every minute
                        except asyncio.CancelledError:
                            break
                        except Exception:
                            pass

                asyncio.create_task(update_uptime())
                logger.info("Uptime tracking started")

            # Start the bot (webhook or polling)
            if self.bot is not None:
                await self.bot.start()

                # Check if webhook mode is enabled (Roadmap Task #1)
                from src.telegram_bot.webhook import (
                    WebhookConfig,
                    should_use_polling,
                    start_webhook,
                )

                webhook_config = WebhookConfig.from_env()

                # Use webhook if configured and not explicitly disabled
                if webhook_config and not should_use_polling():
                    logger.info("🌐 Starting in WEBHOOK mode")
                    try:
                        # Start webhook (this blocks until shutdown)
                        await start_webhook(self.bot, webhook_config)
                        health_check_server.update_status("running")
                    except Exception as e:
                        logger.exception(f"Failed to start webhook, falling back to polling: {e}")
                        # Fallback to polling
                        if self.bot.updater is not None:
                            await self.bot.updater.start_polling()
                        logger.info("📡 Bot polling started (fallback)")
                        health_check_server.update_status("running")
                else:
                    # Use polling (default for development)
                    if self.bot.updater is not None:
                        await self.bot.updater.start_polling()
                    logger.info("📡 Bot polling started")
                    if health_check_server:
                        health_check_server.update_status("running")

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

    async def shutdown(self, timeout: float = 30.0) -> None:
        """Gracefully shutdown the application.

        Args:
            timeout: Maximum time to wait for graceful shutdown (seconds)

        Roadmap Task #4: Graceful Shutdown
        """
        logger.info("=" * 60)
        logger.info("🛑 Initiating graceful shutdown...")
        logger.info("=" * 60)
        if health_check_server:
            health_check_server.update_status("stopping")

        # Set shutdown flag for scanners
        if hasattr(self, "_is_shutting_down"):
            self._is_shutting_down = True

        start_time = asyncio.get_event_loop().time()

        try:
            # Step 0: Stop WebSocket and Health Check
            logger.info("Step 0/9: Stopping WebSocket and Health Check...")

            if self.health_check_monitor:
                try:
                    await asyncio.wait_for(
                        self.health_check_monitor.stop(),
                        timeout=5.0,
                    )
                    logger.info("✅ Health Check Monitor stopped")
                except TimeoutError:
                    logger.warning("⚠️ Health Check Monitor stop timeout")
                except Exception as e:
                    logger.exception(f"❌ Error stopping Health Check: {e}")

            if self.websocket_manager:
                try:
                    await asyncio.wait_for(
                        self.websocket_manager.stop(),
                        timeout=5.0,
                    )
                    logger.info("✅ WebSocket Listener stopped")
                except TimeoutError:
                    logger.warning("⚠️ WebSocket Listener stop timeout")
                except Exception as e:
                    logger.exception(f"❌ Error stopping WebSocket: {e}")

            # Stop HealthMonitor heartbeat
            if self.health_monitor:
                try:
                    await asyncio.wait_for(
                        self.health_monitor.stop_heartbeat(),
                        timeout=5.0,
                    )
                    logger.info("✅ HealthMonitor heartbeat stopped")
                except TimeoutError:
                    logger.warning("⚠️ HealthMonitor stop timeout")
                except Exception as e:
                    logger.exception(f"❌ Error stopping HealthMonitor: {e}")

            # Step 1: Stop Scanner Manager
            if self.scanner_manager:
                logger.info("Step 1/9: Stopping Scanner Manager...")
                try:
                    await asyncio.wait_for(
                        self.scanner_manager.stop(),
                        timeout=10.0,
                    )
                    if self._scanner_task:
                        self._scanner_task.cancel()
                        try:
                            await self._scanner_task
                        except asyncio.CancelledError:
                            pass
                    logger.info("✅ Scanner Manager stopped")
                except TimeoutError:
                    logger.warning("⚠️ Scanner Manager stop timeout")
                except Exception as e:
                    logger.exception(f"❌ Error stopping Scanner Manager: {e}")

            # Step 2: Stop accepting new updates
            logger.info("Step 2/9: Stopping new updates...")
            if self.bot is not None:
                try:
                    if self.bot.updater is not None and self.bot.updater.running:
                        await asyncio.wait_for(
                            self.bot.updater.stop(),
                            timeout=5.0,
                        )
                        logger.info("✅ Stopped accepting new updates")
                except TimeoutError:
                    logger.warning("⚠️  Timeout stopping updater, forcing...")

            # Step 2: Waiting for active tasks to complete (with timeout)
            logger.info("Step 3/9: Waiting for active tasks to complete...")
            active_tasks = [
                task
                for task in asyncio.all_tasks()
                if not task.done() and task != asyncio.current_task()
            ]

            if active_tasks:
                logger.info(f"  Found {len(active_tasks)} active tasks")
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*active_tasks, return_exceptions=True),
                        timeout=min(10.0, timeout - (asyncio.get_event_loop().time() - start_time)),
                    )
                    logger.info("✅ All tasks completed")
                except TimeoutError:
                    logger.warning(
                        f"⚠️  Timeout waiting for {len(active_tasks)} tasks, continuing..."
                    )
                    # Cancel remaining tasks
                    for task in active_tasks:
                        if not task.done():
                            task.cancel()

            # Step 3: Stop Daily Report Scheduler
            logger.info("Step 4/9: Stopping Daily Report Scheduler...")
            if self.daily_report_scheduler:
                try:
                    await asyncio.wait_for(
                        self.daily_report_scheduler.stop(),
                        timeout=5.0,
                    )
                    logger.info("✅ Daily Report Scheduler stopped")
                except TimeoutError:
                    logger.warning("⚠️  Timeout stopping scheduler")

            # Step 4a: Stop AI Training Scheduler
            if self.ai_scheduler:
                try:
                    await asyncio.wait_for(
                        self.ai_scheduler.stop(),
                        timeout=5.0,
                    )
                    logger.info("✅ AI Training Scheduler stopped")
                except TimeoutError:
                    logger.warning("⚠️  Timeout stopping AI scheduler")

            # Step 4: Stop Telegram Bot
            logger.info("Step 5/9: Stopping Telegram Bot...")
            if self.bot is not None:
                try:
                    if self.bot.running:
                        await asyncio.wait_for(
                            self.bot.stop(),
                            timeout=5.0,
                        )
                    await asyncio.wait_for(
                        self.bot.shutdown(),
                        timeout=5.0,
                    )
                    logger.info("✅ Telegram Bot stopped")
                except TimeoutError:
                    logger.warning("⚠️  Timeout stopping bot")
                except Exception as e:
                    logger.exception(f"❌ Error stopping bot: {e}")

            # Step 5: Close DMarket API connections
            logger.info("Step 6/9: Closing DMarket API connections...")
            if self.dmarket_api is not None:
                try:
                    await asyncio.wait_for(
                        self.dmarket_api._close_client(),
                        timeout=3.0,
                    )
                    logger.info("✅ DMarket API connections closed")
                except TimeoutError:
                    logger.warning("⚠️  Timeout closing API connections")
                except Exception as e:
                    logger.exception(f"❌ Error closing API: {e}")

            # Step 6: Close database connections
            logger.info("Step 7/9: Closing database connections...")
            if self.database:
                try:
                    await asyncio.wait_for(
                        self.database.close(),
                        timeout=5.0,
                    )
                    logger.info("✅ Database connections closed")
                except TimeoutError:
                    logger.warning("⚠️  Timeout closing database")
                except Exception as e:
                    logger.exception(f"❌ Error closing database: {e}")

            # Stop health check server (last)
            logger.info("Stopping health check server...")
            try:
                if health_check_server:
                    await health_check_server.stop()
                logger.info("✅ Health check server stopped")
            except Exception as e:
                logger.exception(f"❌ Error stopping health check: {e}")

            # Flush logs
            logger.info("Flushing logs...")
            for handler in logging.root.handlers:
                try:
                    handler.flush()
                except Exception:
                    pass

        except Exception as e:
            logger.exception(f"❌ Error during shutdown: {e}")

        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ Application shutdown complete in {elapsed:.2f}s")
        logger.info("=" * 60)

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

    async def _recover_pending_trades(self) -> None:
        """Recover pending trades from database after restart.

        This is CRITICAL for bot persistence. Without this, the bot would
        "forget" about purchased items after shutdown or restart.

        The recovery process:
        1. Reads pending trades from database
        2. Syncs with DMarket inventory (what's still there vs sold offline)
        3. Re-lists items that need to be sold
        4. Sends summary notification to admin
        """
        if not self.bot or self.config.testing:
            return

        trading_persistence = getattr(self.bot, "trading_persistence", None)
        if not trading_persistence:
            logger.debug("Trading persistence not available, skipping recovery")
            return

        try:
            logger.info("🔍 Recovering pending trades from database...")

            # Recover trades and sync with inventory
            results = await trading_persistence.recover_pending_trades()

            if not results:
                logger.info("✅ No pending trades to recover")
                return

            # Count actions
            to_list = sum(1 for r in results if r.get("action") == "list_for_sale")
            sold_offline = sum(1 for r in results if r.get("action") == "marked_sold")

            logger.info(
                f"📦 Recovery complete: {sold_offline} sold offline, {to_list} need listing"
            )

            # Auto-list items that need to be sold
            if to_list > 0 and self.inventory_manager:
                logger.info(f"📤 Scheduling {to_list} items for auto-listing...")
                # Inventory manager will pick them up in next cycle

        except Exception as e:
            logger.exception(f"Failed to recover pending trades: {e}")
            # Not critical, continue startup

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(sig: int, frame: object) -> None:
            _ = frame  # Unused but required by signal.signal protocol
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

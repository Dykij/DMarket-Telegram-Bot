"""Configuration management utilities for DMarket Bot.

This module provides utilities for loading and managing configuration
from various sources including environment variables, YAML files, and defaults.
"""

import contextlib
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Any

import yaml


# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "sqlite:///data/dmarket_bot.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class BotConfig:
    """Telegram bot configuration."""

    token: str = ""
    username: str = "dmarket_bot"
    webhook_url: str = ""
    webhook_secret: str = ""
    webhook_host: str = "127.0.0.1"  # По умолчанию localhost для безопасности
    webhook_port: int = 8443


@dataclass
class DMarketConfig:
    """DMarket API configuration."""

    api_url: str = "https://api.dmarket.com"
    public_key: str = ""
    secret_key: str = ""
    rate_limit: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""

    allowed_users: list[str | int] = field(default_factory=list)
    admin_users: list[str | int] = field(default_factory=list)


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = "logs/dmarket_bot.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotation: str = "1 week"
    retention: str = "1 month"


@dataclass
class TradingConfig:
    """Trading configuration."""

    max_item_price: float = 20.0
    min_profit_percent: float = 10.0
    games: list[str] = field(default_factory=lambda: ["csgo", "rust"])
    min_sales_last_month: int = 100
    max_inventory_items: int = 30

    # Universal percentage-based settings (new!)
    max_buy_percent: float = 0.25  # Max 25% of balance per item
    min_buy_percent: float = 0.005  # Min 0.5% of balance per item
    reserve_percent: float = 0.05  # Keep 5% as reserve
    max_stack_percent: float = 0.15  # Max 15% in same item type
    enable_smart_mode: bool = True  # Use dynamic limits based on balance


@dataclass
class FiltersConfig:
    """Item filtering configuration."""

    min_liquidity: int = 50
    max_items_in_stock: int = 5


@dataclass
class InventoryConfig:
    """Inventory management configuration."""

    auto_sell: bool = True
    undercut_price: float = 0.01
    min_margin_threshold: float = 1.02
    auto_repricing: bool = True  # Enable automatic price reduction
    repricing_interval_hours: int = 48  # Reduce price after this many hours
    max_price_cut_percent: float = 15.0  # Max price reduction percentage


@dataclass
class TradingSafetyConfig:
    """Trading safety configuration."""

    # Санитарная проверка цен
    max_price_multiplier: float = 1.5  # Максимум 50% выше средней цены
    price_history_days: int = 7  # Период анализа истории цен
    min_history_samples: int = 3  # Минимум сэмплов для расчета средней
    enable_price_sanity_check: bool = True  # Включить проверку цен


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    # Мониторинг rate limit
    warning_threshold: float = 0.9  # Порог для уведомлений (90%)
    enable_notifications: bool = True  # Включить уведомления

    # Exponential backoff
    base_retry_delay: float = 1.0  # Базовая задержка (секунды)
    max_backoff_time: float = 60.0  # Максимальное время backoff (секунды)
    max_retry_attempts: int = 5  # Максимум попыток повтора

    # Лимиты для разных эндпоинтов (запросов в секунду)
    market_limit: int = 2  # Рыночные запросы
    trade_limit: int = 1  # Торговые операции
    user_limit: int = 5  # Пользовательские данные
    balance_limit: int = 10  # Запросы баланса
    other_limit: int = 5  # Прочие запросы


@dataclass
class DailyReportConfig:
    """Daily report configuration."""

    enabled: bool = True  # Включить ежедневные отчёты
    report_time_hour: int = 9  # Час отправки отчёта (UTC)
    report_time_minute: int = 0  # Минута отправки отчёта
    include_days: int = 1  # Количество дней в отчёте


@dataclass
class WaxpeerConfig:
    """Waxpeer P2P integration configuration."""

    enabled: bool = False  # Включить интеграцию с Waxpeer
    api_key: str = ""  # API ключ Waxpeer

    # Настройки наценок
    markup: float = 10.0  # Наценка для обычных скинов (%)
    rare_markup: float = 25.0  # Наценка для редких скинов (%)
    ultra_markup: float = 40.0  # Наценка для JACKPOT скинов (%)
    min_profit: float = 5.0  # Минимальная прибыль для листинга (%)

    # Авто-репрайсинг
    reprice: bool = True  # Включить автоматический undercut
    reprice_interval: int = 30  # Интервал проверки цен (минуты)

    # Shadow Listing
    shadow: bool = True  # Умное ценообразование
    scarcity_threshold: int = 3  # Порог дефицита

    # Auto-Hold
    auto_hold: bool = True  # Не выставлять редкие предметы
    alert_on_rare: bool = True  # Уведомлять о редких находках


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""

    prometheus_host: str = "127.0.0.1"  # По умолчанию localhost для безопасности
    prometheus_port: int = 9090
    enabled: bool = True


@dataclass
class Config:
    """Main application configuration."""

    bot: BotConfig = field(default_factory=BotConfig)
    dmarket: DMarketConfig = field(default_factory=DMarketConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    filters: FiltersConfig = field(default_factory=FiltersConfig)
    inventory: InventoryConfig = field(default_factory=InventoryConfig)
    trading_safety: TradingSafetyConfig = field(default_factory=TradingSafetyConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    daily_report: DailyReportConfig = field(default_factory=DailyReportConfig)
    waxpeer: WaxpeerConfig = field(default_factory=WaxpeerConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    debug: bool = False
    testing: bool = False
    dry_run: bool = True  # По умолчанию True для защиты
    environment: str = "development"  # development, staging, production

    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":
        """Load configuration from file and environment variables.

        Args:
            config_path: Path to configuration file (YAML)

        Returns:
            Config: Loaded configuration

        """
        config = cls()

        # Load from YAML file if provided
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    yaml_config = yaml.safe_load(f)
                config._update_from_dict(yaml_config)
                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        # Override with environment variables
        config._update_from_env()

        return config

    def _update_from_dict(self, data: dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        if "bot" in data:
            bot_data = data["bot"]
            self.bot.token = bot_data.get("token", self.bot.token)
            self.bot.username = bot_data.get("username", self.bot.username)
            if "webhook" in bot_data:
                webhook = bot_data["webhook"]
                self.bot.webhook_url = webhook.get("url", self.bot.webhook_url)
                self.bot.webhook_secret = webhook.get("secret", self.bot.webhook_secret)

        if "dmarket" in data:
            dmarket_data = data["dmarket"]
            self.dmarket.api_url = dmarket_data.get("api_url", self.dmarket.api_url)
            self.dmarket.public_key = dmarket_data.get(
                "public_key",
                self.dmarket.public_key,
            )
            self.dmarket.secret_key = dmarket_data.get(
                "secret_key",
                self.dmarket.secret_key,
            )
            self.dmarket.rate_limit = dmarket_data.get(
                "rate_limit",
                self.dmarket.rate_limit,
            )

        if "database" in data:
            db_data = data["database"]
            self.database.url = db_data.get("url", self.database.url)
            self.database.echo = db_data.get("echo", self.database.echo)
            self.database.pool_size = db_data.get(
                "pool_size",
                self.database.pool_size,
            )
            self.database.max_overflow = db_data.get(
                "max_overflow",
                self.database.max_overflow,
            )

        if "security" in data:
            security_data = data["security"]
            allowed = security_data.get("allowed_users", "")
            if allowed:
                self.security.allowed_users = [u.strip() for u in allowed.split(",")]
            admin = security_data.get("admin_users", "")
            if admin:
                self.security.admin_users = [u.strip() for u in admin.split(",")]

        if "logging" in data:
            log_data = data["logging"]
            self.logging.level = log_data.get("level", self.logging.level)
            self.logging.file = log_data.get("file", self.logging.file)

        if "trading" in data:
            trading_data = data["trading"]
            self.trading.max_item_price = trading_data.get(
                "max_item_price", self.trading.max_item_price
            )
            self.trading.min_profit_percent = trading_data.get(
                "min_profit_percent", self.trading.min_profit_percent
            )
            self.trading.games = trading_data.get("games", self.trading.games)
            self.trading.min_sales_last_month = trading_data.get(
                "min_sales_last_month", self.trading.min_sales_last_month
            )
            self.trading.max_inventory_items = trading_data.get(
                "max_inventory_items", self.trading.max_inventory_items
            )

        if "filters" in data:
            filters_data = data["filters"]
            self.filters.min_liquidity = filters_data.get(
                "min_liquidity", self.filters.min_liquidity
            )
            self.filters.max_items_in_stock = filters_data.get(
                "max_items_in_stock", self.filters.max_items_in_stock
            )

        if "inventory" in data:
            inv_data = data["inventory"]
            self.inventory.auto_sell = inv_data.get("auto_sell", self.inventory.auto_sell)
            self.inventory.undercut_price = inv_data.get(
                "undercut_price", self.inventory.undercut_price
            )
            self.inventory.min_margin_threshold = inv_data.get(
                "min_margin_threshold", self.inventory.min_margin_threshold
            )

        if "trading_safety" in data:
            safety_data = data["trading_safety"]
            self.trading_safety.max_price_multiplier = safety_data.get(
                "max_price_multiplier",
                self.trading_safety.max_price_multiplier,
            )
            self.trading_safety.price_history_days = safety_data.get(
                "price_history_days",
                self.trading_safety.price_history_days,
            )
            self.trading_safety.min_history_samples = safety_data.get(
                "min_history_samples",
                self.trading_safety.min_history_samples,
            )
            self.trading_safety.enable_price_sanity_check = safety_data.get(
                "enable_price_sanity_check",
                self.trading_safety.enable_price_sanity_check,
            )

        if "daily_report" in data:
            report_data = data["daily_report"]
            self.daily_report.enabled = report_data.get(
                "enabled",
                self.daily_report.enabled,
            )
            self.daily_report.report_time_hour = report_data.get(
                "report_time_hour",
                self.daily_report.report_time_hour,
            )
            self.daily_report.report_time_minute = report_data.get(
                "report_time_minute",
                self.daily_report.report_time_minute,
            )
            self.daily_report.include_days = report_data.get(
                "include_days",
                self.daily_report.include_days,
            )

        if "rate_limit" in data:
            rl_data = data["rate_limit"]
            self.rate_limit.warning_threshold = rl_data.get(
                "warning_threshold",
                self.rate_limit.warning_threshold,
            )
            self.rate_limit.enable_notifications = rl_data.get(
                "enable_notifications",
                self.rate_limit.enable_notifications,
            )
            self.rate_limit.base_retry_delay = rl_data.get(
                "base_retry_delay",
                self.rate_limit.base_retry_delay,
            )
            self.rate_limit.max_backoff_time = rl_data.get(
                "max_backoff_time",
                self.rate_limit.max_backoff_time,
            )
            self.rate_limit.max_retry_attempts = rl_data.get(
                "max_retry_attempts",
                self.rate_limit.max_retry_attempts,
            )
            self.rate_limit.market_limit = rl_data.get(
                "market_limit",
                self.rate_limit.market_limit,
            )
            self.rate_limit.trade_limit = rl_data.get(
                "trade_limit",
                self.rate_limit.trade_limit,
            )
            self.rate_limit.user_limit = rl_data.get(
                "user_limit",
                self.rate_limit.user_limit,
            )
            self.rate_limit.balance_limit = rl_data.get(
                "balance_limit",
                self.rate_limit.balance_limit,
            )
            self.rate_limit.other_limit = rl_data.get(
                "other_limit",
                self.rate_limit.other_limit,
            )

    def _update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # Bot configuration
        self.bot.token = os.getenv("TELEGRAM_BOT_TOKEN", self.bot.token)
        self.bot.username = os.getenv("BOT_USERNAME", self.bot.username)
        self.bot.webhook_url = os.getenv("WEBHOOK_URL", self.bot.webhook_url)
        self.bot.webhook_secret = os.getenv("WEBHOOK_SECRET", self.bot.webhook_secret)
        self.bot.webhook_host = os.getenv("WEBHOOK_HOST", self.bot.webhook_host)
        webhook_port = os.getenv("WEBHOOK_PORT")
        if webhook_port:
            with contextlib.suppress(ValueError):
                self.bot.webhook_port = int(webhook_port)

        # Environment
        self.environment = os.getenv("ENVIRONMENT", self.environment)

        # Monitoring configuration
        self.monitoring.prometheus_host = os.getenv(
            "PROMETHEUS_HOST", self.monitoring.prometheus_host
        )
        prometheus_port = os.getenv("PROMETHEUS_PORT")
        if prometheus_port:
            with contextlib.suppress(ValueError):
                self.monitoring.prometheus_port = int(prometheus_port)

        monitoring_enabled = os.getenv("MONITORING_ENABLED")
        if monitoring_enabled:
            self.monitoring.enabled = monitoring_enabled.lower() == "true"

        # DMarket configuration
        self.dmarket.api_url = os.getenv("DMARKET_API_URL", self.dmarket.api_url)
        self.dmarket.public_key = os.getenv(
            "DMARKET_PUBLIC_KEY",
            self.dmarket.public_key,
        )
        self.dmarket.secret_key = os.getenv(
            "DMARKET_SECRET_KEY",
            self.dmarket.secret_key,
        )

        rate_limit = os.getenv("API_RATE_LIMIT")
        if rate_limit:
            with contextlib.suppress(ValueError):
                self.dmarket.rate_limit = int(rate_limit)

        # Database configuration
        self.database.url = os.getenv("DATABASE_URL", self.database.url)

        # Security configuration
        allowed_users = os.getenv("ALLOWED_USERS", "")
        if allowed_users:
            self.security.allowed_users = [u.strip() for u in allowed_users.split(",")]

        admin_users = os.getenv("ADMIN_USERS", "")
        if admin_users:
            self.security.admin_users = [u.strip() for u in admin_users.split(",")]

        # Logging configuration
        self.logging.level = os.getenv("LOG_LEVEL", self.logging.level)
        self.logging.file = os.getenv("LOG_FILE", self.logging.file)

        # Debug and testing flags
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.testing = os.getenv("TESTING", "false").lower() == "true"

        # Trading configuration
        max_item_price = os.getenv("MAX_ITEM_PRICE")
        if max_item_price:
            with contextlib.suppress(ValueError):
                self.trading.max_item_price = float(max_item_price)

        min_profit = os.getenv("MIN_PROFIT_PERCENT")
        if min_profit:
            with contextlib.suppress(ValueError):
                self.trading.min_profit_percent = float(min_profit)

        min_sales = os.getenv("MIN_SALES_LAST_MONTH")
        if min_sales:
            with contextlib.suppress(ValueError):
                self.trading.min_sales_last_month = int(min_sales)

        max_inv = os.getenv("MAX_INVENTORY_ITEMS")
        if max_inv:
            with contextlib.suppress(ValueError):
                self.trading.max_inventory_items = int(max_inv)

        # Universal percentage-based settings (new!)
        max_buy_pct = os.getenv("MAX_BUY_PERCENT")
        if max_buy_pct:
            with contextlib.suppress(ValueError):
                self.trading.max_buy_percent = float(max_buy_pct)

        min_buy_pct = os.getenv("MIN_BUY_PERCENT")
        if min_buy_pct:
            with contextlib.suppress(ValueError):
                self.trading.min_buy_percent = float(min_buy_pct)

        reserve_pct = os.getenv("RESERVE_PERCENT")
        if reserve_pct:
            with contextlib.suppress(ValueError):
                self.trading.reserve_percent = float(reserve_pct)

        max_stack_pct = os.getenv("MAX_STACK_PERCENT")
        if max_stack_pct:
            with contextlib.suppress(ValueError):
                self.trading.max_stack_percent = float(max_stack_pct)

        smart_mode = os.getenv("ENABLE_SMART_MODE", "true").lower()
        self.trading.enable_smart_mode = smart_mode == "true"

        # Filters configuration
        min_liquidity = os.getenv("MIN_LIQUIDITY_SCORE")
        if min_liquidity:
            with contextlib.suppress(ValueError):
                self.filters.min_liquidity = int(min_liquidity)

        # Inventory configuration
        undercut = os.getenv("PRICE_STEP")  # Using PRICE_STEP as alias for undercut_price
        if undercut:
            with contextlib.suppress(ValueError):
                self.inventory.undercut_price = float(undercut)

        min_margin = os.getenv("MIN_MARGIN_THRESHOLD")
        if min_margin:
            with contextlib.suppress(ValueError):
                self.inventory.min_margin_threshold = float(min_margin)

        auto_repricing = os.getenv("AUTO_REPRICING", "true").lower()
        self.inventory.auto_repricing = auto_repricing == "true"

        repricing_hours = os.getenv("REPRICING_INTERVAL_HOURS")
        if repricing_hours:
            with contextlib.suppress(ValueError):
                self.inventory.repricing_interval_hours = int(repricing_hours)

        max_price_cut = os.getenv("MAX_PRICE_CUT_PERCENT")
        if max_price_cut:
            with contextlib.suppress(ValueError):
                self.inventory.max_price_cut_percent = float(max_price_cut)

        # Trading safety mode - defaults to True for safety
        dry_run_env = os.getenv("DRY_RUN", "true").lower()
        self.dry_run = dry_run_env == "true"

        # Trading safety configuration
        max_price_mult = os.getenv("MAX_PRICE_MULTIPLIER")
        if max_price_mult:
            with contextlib.suppress(ValueError):
                self.trading_safety.max_price_multiplier = float(max_price_mult)

        price_hist_days = os.getenv("PRICE_HISTORY_DAYS")
        if price_hist_days:
            with contextlib.suppress(ValueError):
                self.trading_safety.price_history_days = int(price_hist_days)

        min_hist_samples = os.getenv("MIN_HISTORY_SAMPLES")
        if min_hist_samples:
            with contextlib.suppress(ValueError):
                self.trading_safety.min_history_samples = int(min_hist_samples)

        enable_sanity = os.getenv("ENABLE_PRICE_SANITY_CHECK", "true").lower()
        self.trading_safety.enable_price_sanity_check = enable_sanity == "true"

        # Daily report configuration
        daily_enabled = os.getenv("DAILY_REPORT_ENABLED", "true").lower()
        self.daily_report.enabled = daily_enabled == "true"

        report_hour = os.getenv("DAILY_REPORT_HOUR")
        if report_hour:
            with contextlib.suppress(ValueError):
                self.daily_report.report_time_hour = int(report_hour)

        report_minute = os.getenv("DAILY_REPORT_MINUTE")
        if report_minute:
            with contextlib.suppress(ValueError):
                self.daily_report.report_time_minute = int(report_minute)

        include_days = os.getenv("DAILY_REPORT_DAYS")
        if include_days:
            with contextlib.suppress(ValueError):
                self.daily_report.include_days = int(include_days)

        # Rate limit configuration
        warning_threshold = os.getenv("RATE_LIMIT_WARNING_THRESHOLD")
        if warning_threshold:
            with contextlib.suppress(ValueError):
                self.rate_limit.warning_threshold = float(warning_threshold)

        enable_rl_notif = os.getenv("RATE_LIMIT_NOTIFICATIONS", "true").lower()
        self.rate_limit.enable_notifications = enable_rl_notif == "true"

        base_delay = os.getenv("RATE_LIMIT_BASE_DELAY")
        if base_delay:
            with contextlib.suppress(ValueError):
                self.rate_limit.base_retry_delay = float(base_delay)

        max_backoff = os.getenv("RATE_LIMIT_MAX_BACKOFF")
        if max_backoff:
            with contextlib.suppress(ValueError):
                self.rate_limit.max_backoff_time = float(max_backoff)

        max_attempts = os.getenv("RATE_LIMIT_MAX_ATTEMPTS")
        if max_attempts:
            with contextlib.suppress(ValueError):
                self.rate_limit.max_retry_attempts = int(max_attempts)

        # Waxpeer configuration
        waxpeer_enabled = os.getenv("WAXPEER_ENABLED", "false").lower()
        self.waxpeer.enabled = waxpeer_enabled == "true"
        self.waxpeer.api_key = os.getenv("WAXPEER_API_KEY", self.waxpeer.api_key)

        waxpeer_markup = os.getenv("WAXPEER_MARKUP")
        if waxpeer_markup:
            with contextlib.suppress(ValueError):
                self.waxpeer.markup = float(waxpeer_markup)

        waxpeer_rare_markup = os.getenv("WAXPEER_RARE_MARKUP")
        if waxpeer_rare_markup:
            with contextlib.suppress(ValueError):
                self.waxpeer.rare_markup = float(waxpeer_rare_markup)

        waxpeer_ultra_markup = os.getenv("WAXPEER_ULTRA_MARKUP")
        if waxpeer_ultra_markup:
            with contextlib.suppress(ValueError):
                self.waxpeer.ultra_markup = float(waxpeer_ultra_markup)

        waxpeer_min_profit = os.getenv("WAXPEER_MIN_PROFIT")
        if waxpeer_min_profit:
            with contextlib.suppress(ValueError):
                self.waxpeer.min_profit = float(waxpeer_min_profit)

        waxpeer_reprice = os.getenv("WAXPEER_REPRICE", "true").lower()
        self.waxpeer.reprice = waxpeer_reprice == "true"

        waxpeer_reprice_interval = os.getenv("WAXPEER_REPRICE_INTERVAL")
        if waxpeer_reprice_interval:
            with contextlib.suppress(ValueError):
                self.waxpeer.reprice_interval = int(waxpeer_reprice_interval)

        waxpeer_shadow = os.getenv("WAXPEER_SHADOW", "true").lower()
        self.waxpeer.shadow = waxpeer_shadow == "true"

        waxpeer_scarcity = os.getenv("WAXPEER_SCARCITY")
        if waxpeer_scarcity:
            with contextlib.suppress(ValueError):
                self.waxpeer.scarcity_threshold = int(waxpeer_scarcity)

        waxpeer_auto_hold = os.getenv("WAXPEER_AUTO_HOLD", "true").lower()
        self.waxpeer.auto_hold = waxpeer_auto_hold == "true"

        waxpeer_alert = os.getenv("WAXPEER_ALERT", "true").lower()
        self.waxpeer.alert_on_rare = waxpeer_alert == "true"

    def validate(self) -> None:
        """Validate configuration and raise errors for required missing values."""
        errors = []

        # Validate Telegram Bot configuration
        if not self.bot.token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        elif not self.bot.token.startswith("bot") and ":" not in self.bot.token:
            errors.append(
                "TELEGRAM_BOT_TOKEN appears invalid "
                "(should be in format: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)"
            )

        # Validate DMarket API configuration (unless in testing mode)
        if not self.testing:
            if not self.dmarket.public_key:
                errors.append("DMARKET_PUBLIC_KEY is required (unless in testing mode)")
            elif len(self.dmarket.public_key) < 20:
                errors.append("DMARKET_PUBLIC_KEY appears too short")

            if not self.dmarket.secret_key:
                errors.append("DMARKET_SECRET_KEY is required (unless in testing mode)")
            elif len(self.dmarket.secret_key) < 20:
                errors.append("DMARKET_SECRET_KEY appears too short")

            # Validate API URL format
            if not self.dmarket.api_url.startswith(("http://", "https://")):
                errors.append(
                    "DMARKET_API_URL must start with http:// or https://, "
                    f"got: {self.dmarket.api_url}"
                )

            # Validate rate limit
            if self.dmarket.rate_limit <= 0:
                errors.append(
                    f"DMARKET rate_limit must be positive, got: {self.dmarket.rate_limit}"
                )

        # Validate database URL
        if not self.database.url:
            errors.append("DATABASE_URL is required")
        elif not self.database.url.startswith(("sqlite://", "postgresql://", "mysql://")):
            errors.append(
                "DATABASE_URL has unsupported scheme. "
                "Supported: sqlite://, postgresql://, mysql://. "
                f"Got: {self.database.url}"
            )

        # Validate logging level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of {valid_log_levels}, got: {self.logging.level}")

        # Validate security settings (convert user IDs)
        if self.security.allowed_users:
            try:
                self.security.allowed_users = [
                    int(uid) if isinstance(uid, str) and uid.isdigit() else uid
                    for uid in self.security.allowed_users
                ]
            except ValueError as e:
                errors.append(f"Invalid ALLOWED_USERS format: {e}")

        if self.security.admin_users:
            try:
                self.security.admin_users = [
                    int(uid) if isinstance(uid, str) and uid.isdigit() else uid
                    for uid in self.security.admin_users
                ]
            except ValueError as e:
                errors.append(f"Invalid ADMIN_USERS format: {e}")

        # Validate pool settings
        if self.database.pool_size <= 0:
            errors.append(f"Database pool_size must be positive, got: {self.database.pool_size}")

        if self.database.max_overflow < 0:
            errors.append(
                f"Database max_overflow must be non-negative, got: {self.database.max_overflow}"
            )

        # Log safety warnings
        if not self.dry_run and not self.testing:
            logger.warning(
                "⚠️  DRY_RUN=false - BOT WILL MAKE REAL TRADES! Make sure you understand the risks."
            )
        elif self.dry_run:
            logger.info("✅ DRY_RUN=true - Bot is in safe mode (no real trades will be made)")

        # Raise all errors at once
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {err}" for err in errors
            )
            raise ValueError(error_msg)


# Global settings instance
settings = Config.load()

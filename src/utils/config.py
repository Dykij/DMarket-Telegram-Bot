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
class TradingSafetyConfig:
    """Trading safety configuration."""

    # Санитарная проверка цен
    max_price_multiplier: float = 1.5  # Максимум 50% выше средней цены
    price_history_days: int = 7  # Период анализа истории цен
    min_history_samples: int = 3  # Минимум сэмплов для расчета средней
    enable_price_sanity_check: bool = True  # Включить проверку цен


@dataclass
class Config:
    """Main application configuration."""

    bot: BotConfig = field(default_factory=BotConfig)
    dmarket: DMarketConfig = field(default_factory=DMarketConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    trading_safety: TradingSafetyConfig = field(default_factory=TradingSafetyConfig)
    debug: bool = False
    testing: bool = False
    dry_run: bool = True  # По умолчанию True для защиты от случайных реальных сделок

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
                with open(config_path) as f:
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

    def _update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # Bot configuration
        self.bot.token = os.getenv("TELEGRAM_BOT_TOKEN", self.bot.token)
        self.bot.username = os.getenv("BOT_USERNAME", self.bot.username)
        self.bot.webhook_url = os.getenv("WEBHOOK_URL", self.bot.webhook_url)
        self.bot.webhook_secret = os.getenv("WEBHOOK_SECRET", self.bot.webhook_secret)

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

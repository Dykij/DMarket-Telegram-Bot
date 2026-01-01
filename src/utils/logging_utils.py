"""Enhanced logging utilities for DMarket Bot.

This module provides comprehensive logging configuration and utilities
for the DMarket Telegram Bot, including structured logging, file rotation,
and integration with monitoring systems, including Sentry error tracking.
"""

from datetime import datetime
import json
import logging
import logging.handlers
import os
from pathlib import Path
import sys
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import structlog


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Create colored level name
        colored_levelname = f"{color}{record.levelname}{reset}"

        # Replace levelname in format
        original_format = self._style._fmt
        colored_format = original_format.replace("%(levelname)s", colored_levelname)

        # Create temporary formatter with colored format
        temp_formatter = logging.Formatter(colored_format, self.datefmt)
        return temp_formatter.format(record)


def setup_sentry(
    environment: str = "production",
    traces_sample_rate: float = 0.5,
    send_default_pii: bool = False,
) -> None:
    """Setup Sentry error tracking with enhanced integrations.

    Args:
        environment: Environment name (development, production)
        traces_sample_rate: Sample rate for performance monitoring (0.0-1.0)
        send_default_pii: Whether to send personally identifiable information

    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger = logging.getLogger(__name__)
        logger.info("Sentry DSN not configured, error tracking disabled")
        return

    def filter_sensitive_data(event, hint):
        """Filter sensitive data from Sentry events."""
        _ = hint  # Unused but required by Sentry callback protocol
        # Remove API keys and tokens
        if "request" in event:
            headers = event["request"].get("headers", {})
            for key in list(headers.keys()):
                if any(
                    sensitive in key.lower()
                    for sensitive in ["api", "token", "key", "secret", "auth"]
                ):
                    headers[key] = "[Filtered]"

        # Remove sensitive context
        if "extra" in event:
            for key in list(event["extra"].keys()):
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "secret", "token", "key"]
                ):
                    event["extra"][key] = "[Filtered]"

        return event

    # Configure enhanced Sentry integrations
    integrations = [
        LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors and above as events
        ),
        AsyncioIntegration(),  # Async error tracking
        HttpxIntegration(),  # HTTP request breadcrumbs
    ]

    # Add SQLAlchemy integration if available
    try:
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        integrations.append(SqlalchemyIntegration())
    except ImportError:
        pass

    # Add Redis integration if available
    try:
        from sentry_sdk.integrations.redis import RedisIntegration

        integrations.append(RedisIntegration())
    except ImportError:
        pass

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        send_default_pii=send_default_pii,
        integrations=integrations,
        before_send=filter_sensitive_data,
        release=os.getenv("BOT_VERSION", "unknown"),
        attach_stacktrace=True,
        max_breadcrumbs=100,  # Increased for better context
        debug=False,
        # Performance monitoring
        enable_tracing=True,
        # Database query spans
        _experiments={  # type: ignore[typeddict-unknown-key]
            "profiles_sample_rate": 0.5 if environment == "production" else 1.0,
        },
    )

    logger = logging.getLogger(__name__)
    logger.info(
        f"Sentry initialized: env={environment}, sample_rate={traces_sample_rate}, "
        f"integrations={len(integrations)}"
    )


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    format_string: str | None = None,
    json_format: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_structlog: bool = True,
    enable_sentry: bool = True,
    sentry_environment: str = "production",
) -> None:
    """Setup comprehensive logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        format_string: Custom format string
        json_format: Use JSON format for file logging
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        enable_structlog: Enable structured logging with structlog
        enable_sentry: Enable Sentry error tracking
        sentry_environment: Sentry environment (development, production)

    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format
    if not format_string:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if sys.stdout.isatty():  # Only use colors if output is a terminal
        console_formatter = ColoredFormatter(format_string)
    else:
        console_formatter = logging.Formatter(format_string)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)

        file_formatter = (
            JSONFormatter() if json_format else logging.Formatter(format_string)
        )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Set root logger level
    root_logger.setLevel(numeric_level)

    # Configure structlog if enabled
    if enable_structlog:
        setup_structlog(json_format=json_format)

    # Configure Sentry if enabled
    if enable_sentry:
        setup_sentry(
            environment=sentry_environment,
            traces_sample_rate=0.1,
        )

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={level}, file={log_file}, "
        f"json={json_format}, sentry={enable_sentry}",
    )


def setup_structlog(json_format: bool = False) -> None:
    """Setup structured logging with structlog.

    Args:
        json_format: Use JSON output format

    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
            ],
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


class BotLogger:
    """Enhanced logger for bot operations with context."""

    def __init__(self, name: str) -> None:
        """Initialize bot logger.

        Args:
            name: Logger name

        """
        self.logger = structlog.get_logger(name)

    def log_command(
        self,
        user_id: int,
        command: str,
        success: bool = True,
        **kwargs: Any,
    ) -> None:
        """Log bot command execution.

        Args:
            user_id: Telegram user ID
            command: Command name
            success: Whether command succeeded
            **kwargs: Additional context

        """
        self.logger.info(
            "Bot command executed",
            user_id=user_id,
            command=command,
            success=success,
            **kwargs,
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int | None = None,
        response_time: float | None = None,
        error: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time: Response time in seconds
            error: Error message if any
            **kwargs: Additional context

        """
        level = "error" if error else "info"

        self.logger.log(
            level,
            "API call",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            error=error,
            **kwargs,
        )

    def log_market_data(
        self,
        game: str,
        items_count: int,
        total_value: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Log market data processing.

        Args:
            game: Game identifier
            items_count: Number of items processed
            total_value: Total value of items
            **kwargs: Additional context

        """
        self.logger.info(
            "Market data processed",
            game=game,
            items_count=items_count,
            total_value=total_value,
            **kwargs,
        )

    def log_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error with context.

        Args:
            error: Exception object
            context: Error context
            **kwargs: Additional context

        """
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(context or {}),
            **kwargs,
        }

        self.logger.error("Error occurred", **error_context)

    def log_buy_intent(
        self,
        item_name: str,
        price_usd: float,
        sell_price_usd: float | None = None,
        profit_usd: float | None = None,
        profit_percent: float | None = None,
        source: str = "unknown",
        dry_run: bool = True,
        user_id: int | None = None,
        game: str = "csgo",
        **kwargs: Any,
    ) -> None:
        """Log buy intent before purchase.

        Args:
            item_name: Item name
            price_usd: Buy price in USD
            sell_price_usd: Expected sell price in USD
            profit_usd: Expected profit in USD
            profit_percent: Expected profit percentage
            source: Source of the intent (arbitrage_scanner, manual, etc)
            dry_run: Whether this is a dry run
            user_id: Telegram user ID
            game: Game identifier
            **kwargs: Additional context

        """
        from datetime import UTC, datetime

        intent_data = {
            "intent_type": "BUY_INTENT",
            "item": item_name,
            "price_usd": price_usd,
            "sell_price_usd": sell_price_usd,
            "profit_usd": profit_usd,
            "profit_percent": profit_percent,
            "source": source,
            "dry_run": dry_run,
            "user_id": user_id,
            "game": game,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            **kwargs,
        }

        # Log with CRITICAL level to ensure visibility
        mode = "DRY-RUN" if dry_run else "LIVE"
        msg = f"[{mode}] 🔵 BUY_INTENT: {item_name} @ ${price_usd:.2f}"
        self.logger.info(msg, **intent_data)

    def log_sell_intent(
        self,
        item_name: str,
        price_usd: float,
        buy_price_usd: float | None = None,
        profit_usd: float | None = None,
        profit_percent: float | None = None,
        source: str = "unknown",
        dry_run: bool = True,
        user_id: int | None = None,
        game: str = "csgo",
        **kwargs: Any,
    ) -> None:
        """Log sell intent before selling.

        Args:
            item_name: Item name
            price_usd: Sell price in USD
            buy_price_usd: Original buy price in USD
            profit_usd: Actual profit in USD
            profit_percent: Actual profit percentage
            source: Source of the intent (auto_sell, manual, etc)
            dry_run: Whether this is a dry run
            user_id: Telegram user ID
            game: Game identifier
            **kwargs: Additional context

        """
        from datetime import UTC, datetime

        intent_data = {
            "intent_type": "SELL_INTENT",
            "item": item_name,
            "price_usd": price_usd,
            "buy_price_usd": buy_price_usd,
            "profit_usd": profit_usd,
            "profit_percent": profit_percent,
            "source": source,
            "dry_run": dry_run,
            "user_id": user_id,
            "game": game,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            **kwargs,
        }

        # Log with INFO level
        mode = "DRY-RUN" if dry_run else "LIVE"
        msg = f"[{mode}] 🟢 SELL_INTENT: {item_name} @ ${price_usd:.2f}"
        self.logger.info(msg, **intent_data)

    def log_trade_result(
        self,
        operation: str,
        success: bool,
        item_name: str,
        price_usd: float,
        error_message: str | None = None,
        dry_run: bool = True,
        **kwargs: Any,
    ) -> None:
        """Log trade result after operation.

        Args:
            operation: Operation type (buy/sell)
            success: Whether operation succeeded
            item_name: Item name
            price_usd: Price in USD
            error_message: Error message if failed
            dry_run: Whether this was a dry run
            **kwargs: Additional context

        """
        from datetime import UTC, datetime

        result_data = {
            "result_type": f"{operation.upper()}_RESULT",
            "success": success,
            "item": item_name,
            "price_usd": price_usd,
            "error": error_message,
            "dry_run": dry_run,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            **kwargs,
        }

        import logging

        level = logging.INFO if success else logging.ERROR
        emoji = "✅" if success else "❌"
        status = "SUCCESS" if success else "FAILED"
        mode = "DRY-RUN" if dry_run else "LIVE"
        msg = f"[{mode}] {emoji} {operation.upper()}_{status}: {item_name}"

        self.logger.log(level, msg, **result_data)

    def log_crash(
        self,
        error: Exception,
        traceback_text: str | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log critical crash with full context and traceback.

        Args:
            error: Exception object
            traceback_text: Full traceback string
            context: Additional context about the crash
            **kwargs: Additional context

        """
        from datetime import UTC, datetime

        crash_data = {
            "crash_type": "BOT_CRASH",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback_text,
            "context": context or {},
            "timestamp": datetime.now(tz=UTC).isoformat(),
            **kwargs,
        }

        self.logger.critical(
            f"💥 BOT CRASH: {type(error).__name__} - {error!s}",
            **crash_data,
        )

        # Также отправляем в Sentry если доступен
        if sentry_sdk.is_initialized():
            with sentry_sdk.push_scope() as scope:
                # Добавляем весь контекст в Sentry
                for key, value in crash_data.items():
                    if key != "traceback":  # traceback уже в exception
                        scope.set_context(key, value)

                # Отправляем исключение в Sentry
                sentry_sdk.capture_exception(error)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Configured logger instance

    """
    return logging.getLogger(name)

"""Enhanced logging utilities for DMarket Bot.

This module provides comprehensive logging configuration and utilities
for the DMarket Telegram Bot, including structured logging, file rotation,
and integration with monitoring systems.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

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
            if key not in [
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
            ]:
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


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    format_string: str | None = None,
    json_format: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_structlog: bool = True,
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

        file_formatter = JSONFormatter() if json_format else logging.Formatter(format_string)

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Set root logger level
    root_logger.setLevel(numeric_level)

    # Configure structlog if enabled
    if enable_structlog:
        setup_structlog(json_format=json_format)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={level}, file={log_file}, json={json_format}",
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


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Configured logger instance

    """
    return logging.getLogger(name)

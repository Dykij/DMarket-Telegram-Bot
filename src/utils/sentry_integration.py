"""Sentry integration for production error monitoring.

This module initializes and configures Sentry for tracking errors,
performance, and release versions in production.
"""

import logging
import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

logger = logging.getLogger(__name__)


def init_sentry(
    dsn: str | None = None,
    environment: str = "production",
    release: str | None = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    debug: bool = False,
) -> None:
    """Initialize Sentry SDK for error tracking.

    Args:
        dsn: Sentry DSN (Data Source Name). If None, reads from SENTRY_DSN env var
        environment: Environment name (production, staging, development)
        release: Release version. If None, reads from SENTRY_RELEASE env var
        traces_sample_rate: Percentage of transactions to sample (0.0 to 1.0)
        profiles_sample_rate: Percentage of profiles to sample (0.0 to 1.0)
        debug: Enable debug mode for Sentry

    Example:
        >>> init_sentry(
        >>>     dsn="https://xxx@sentry.io/xxx",
        >>>     environment="production",
        >>>     release="1.0.0",
        >>> )
    """
    # Get DSN from parameter or environment
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.warning(
            "Sentry DSN not configured. Error tracking disabled. "
            "Set SENTRY_DSN environment variable to enable."
        )
        return

    # Get release version
    sentry_release = release or os.getenv("SENTRY_RELEASE") or "unknown"

    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=sentry_release,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            debug=debug,
            integrations=[
                sentry_logging,
                AsyncioIntegration(),
                SqlalchemyIntegration(),
            ],
            # Ignore certain errors
            ignore_errors=[
                KeyboardInterrupt,
                SystemExit,
            ],
            # Set a custom before_send callback
            before_send=before_send_callback,
        )

        logger.info(
            "Sentry initialized successfully",
            extra={
                "environment": environment,
                "release": sentry_release,
                "traces_sample_rate": traces_sample_rate,
            },
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Sentry: {e}",
            extra={"error": str(e)},
            exc_info=True,
        )


def before_send_callback(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Filter and modify events before sending to Sentry.

    Args:
        event: Sentry event dictionary
        hint: Additional context about the event (unused but required by protocol)

    Returns:
        Modified event or None to discard the event
    """
    _ = hint  # Unused but required by Sentry callback protocol
    # Filter out sensitive data from event
    if "request" in event:
        if "headers" in event["request"]:
            # Remove sensitive headers
            sensitive_headers = {"authorization", "x-api-key", "cookie"}
            event["request"]["headers"] = {
                k: v
                for k, v in event["request"]["headers"].items()
                if k.lower() not in sensitive_headers
            }

    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["bot_type"] = "dmarket_telegram"

    return event


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb to Sentry for debugging context.

    Args:
        message: Breadcrumb message
        category: Category of the breadcrumb (e.g., 'api', 'user_action')
        level: Severity level (debug, info, warning, error, critical)
        data: Additional data to include

    Example:
        >>> add_breadcrumb(
        >>>     message="User started arbitrage scan",
        >>>     category="user_action",
        >>>     level="info",
        >>>     data={"user_id": 12345, "game": "csgo"}
        >>> )
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


def capture_exception(
    error: Exception,
    level: str = "error",
    tags: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> str | None:
    """Capture an exception and send to Sentry.

    Args:
        error: Exception to capture
        level: Severity level (debug, info, warning, error, critical)
        tags: Additional tags for the event
        extra: Additional context data

    Returns:
        Event ID from Sentry, or None if not sent

    Example:
        >>> try:
        >>>     risky_operation()
        >>> except Exception as e:
        >>>     capture_exception(
        >>>         e,
        >>>         tags={"operation": "market_scan"},
        >>>         extra={"item_count": 100}
        >>>     )
    """
    with sentry_sdk.push_scope() as scope:
        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Add extra context
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        # Set level
        scope.level = level

        # Capture exception
        event_id = sentry_sdk.capture_exception(error)

        logger.debug(
            f"Exception captured by Sentry: {event_id}",
            extra={"event_id": event_id, "error": str(error)},
        )

        return event_id


def set_user_context(
    user_id: int | None = None,
    username: str | None = None,
    email: str | None = None,
    **kwargs: Any,
) -> None:
    """Set user context for Sentry events.

    Args:
        user_id: User ID
        username: Username
        email: User email
        **kwargs: Additional user attributes

    Example:
        >>> set_user_context(
        >>>     user_id=12345,
        >>>     username="trader_pro",
        >>>     subscription="premium"
        >>> )
    """
    user_data: dict[str, Any] = {}

    if user_id is not None:
        user_data["id"] = user_id
    if username is not None:
        user_data["username"] = username
    if email is not None:
        user_data["email"] = email

    user_data.update(kwargs)

    sentry_sdk.set_user(user_data)


def clear_user_context() -> None:
    """Clear user context from Sentry."""
    sentry_sdk.set_user(None)


def set_transaction_name(name: str) -> None:
    """Set the transaction name for performance monitoring.

    Args:
        name: Transaction name (e.g., 'scan_arbitrage', 'buy_item')

    Example:
        >>> set_transaction_name("arbitrage_scan_csgo")
    """
    sentry_sdk.set_transaction(name)

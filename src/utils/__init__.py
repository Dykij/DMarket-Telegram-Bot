"""Utils module.

This module provides various utility functions and classes for the DMarket Bot:

- Environment validation
- Graceful shutdown handling
- Health monitoring
- Feature flags management
- Discord notifications
- Prometheus metrics
- Rate limiting
- Retry decorators
- Watchdog for bot supervision
"""

from typing import TYPE_CHECKING

from src.utils.config import Config
from src.utils.exceptions import (
    APIError,
    BaseAppException,
    NetworkError,
    RateLimitExceeded,
)


if TYPE_CHECKING:
    from src.utils.discord_notifier import (
        DiscordNotifier,
        NotificationLevel,
        create_discord_notifier_from_env,
    )
    from src.utils.env_validator import validate_on_startup, validate_required_env_vars
    from src.utils.feature_flags import (
        Feature,
        FeatureFlagsManager,
        get_feature_flags,
        init_feature_flags,
    )
    from src.utils.health_monitor import HealthCheckResult, HealthMonitor, ServiceStatus
    from src.utils.rate_limit_decorator import rate_limit
    from src.utils.retry_decorator import retry_api_call, retry_on_failure
    from src.utils.shutdown_handler import ShutdownHandler, shutdown_handler
    from src.utils.watchdog import Watchdog, WatchdogConfig


def __getattr__(name: str):  # noqa: C901, PLR0911, PLR0912
    """Lazy import to avoid import errors when dependencies are not installed."""
    # Environment validation
    if name == "validate_on_startup":
        from src.utils.env_validator import validate_on_startup
        return validate_on_startup
    if name == "validate_required_env_vars":
        from src.utils.env_validator import validate_required_env_vars
        return validate_required_env_vars

    # Shutdown handling
    if name == "ShutdownHandler":
        from src.utils.shutdown_handler import ShutdownHandler
        return ShutdownHandler
    if name == "shutdown_handler":
        from src.utils.shutdown_handler import shutdown_handler
        return shutdown_handler

    # Health monitoring
    if name == "HealthMonitor":
        from src.utils.health_monitor import HealthMonitor
        return HealthMonitor
    if name == "HealthCheckResult":
        from src.utils.health_monitor import HealthCheckResult
        return HealthCheckResult
    if name == "ServiceStatus":
        from src.utils.health_monitor import ServiceStatus
        return ServiceStatus

    # Feature flags
    if name == "Feature":
        from src.utils.feature_flags import Feature
        return Feature
    if name == "FeatureFlagsManager":
        from src.utils.feature_flags import FeatureFlagsManager
        return FeatureFlagsManager
    if name == "get_feature_flags":
        from src.utils.feature_flags import get_feature_flags
        return get_feature_flags
    if name == "init_feature_flags":
        from src.utils.feature_flags import init_feature_flags
        return init_feature_flags

    # Discord notifications
    if name == "DiscordNotifier":
        from src.utils.discord_notifier import DiscordNotifier
        return DiscordNotifier
    if name == "NotificationLevel":
        from src.utils.discord_notifier import NotificationLevel
        return NotificationLevel
    if name == "create_discord_notifier_from_env":
        from src.utils.discord_notifier import create_discord_notifier_from_env
        return create_discord_notifier_from_env

    # Rate limiting
    if name == "rate_limit":
        from src.utils.rate_limit_decorator import rate_limit
        return rate_limit

    # Retry decorators
    if name == "retry_api_call":
        from src.utils.retry_decorator import retry_api_call
        return retry_api_call
    if name == "retry_on_failure":
        from src.utils.retry_decorator import retry_on_failure
        return retry_on_failure

    # Watchdog
    if name == "Watchdog":
        from src.utils.watchdog import Watchdog
        return Watchdog
    if name == "WatchdogConfig":
        from src.utils.watchdog import WatchdogConfig
        return WatchdogConfig

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Exceptions
    "APIError",
    "BaseAppException",
    # Config
    "Config",
    # Discord notifications
    "DiscordNotifier",
    # Feature flags
    "Feature",
    "FeatureFlagsManager",
    # Health monitoring
    "HealthCheckResult",
    "HealthMonitor",
    "NetworkError",
    "NotificationLevel",
    "RateLimitExceeded",
    "ServiceStatus",
    # Shutdown handling
    "ShutdownHandler",
    # Watchdog
    "Watchdog",
    "WatchdogConfig",
    "create_discord_notifier_from_env",
    "get_feature_flags",
    "init_feature_flags",
    # Rate limiting
    "rate_limit",
    # Retry decorators
    "retry_api_call",
    "retry_on_failure",
    "shutdown_handler",
    # Environment validation
    "validate_on_startup",
    "validate_required_env_vars",
]

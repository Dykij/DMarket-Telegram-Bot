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

from src.utils.config import Config
from src.utils.exceptions import (
    APIError,
    BaseAppException,
    NetworkError,
    RateLimitExceeded,
)

# Optional imports - these may fail if dependencies are not installed
try:
    from src.utils.env_validator import validate_on_startup, validate_required_env_vars
except ImportError:
    validate_on_startup = None
    validate_required_env_vars = None

try:
    from src.utils.shutdown_handler import ShutdownHandler, shutdown_handler
except ImportError:
    ShutdownHandler = None
    shutdown_handler = None

try:
    from src.utils.health_monitor import HealthCheckResult, HealthMonitor, ServiceStatus
except ImportError:
    HealthMonitor = None
    HealthCheckResult = None
    ServiceStatus = None

try:
    from src.utils.feature_flags import (
        Feature,
        FeatureFlagsManager,
        get_feature_flags,
        init_feature_flags,
    )
except ImportError:
    Feature = None
    FeatureFlagsManager = None
    get_feature_flags = None
    init_feature_flags = None

try:
    from src.utils.discord_notifier import (
        DiscordNotifier,
        NotificationLevel,
        create_discord_notifier_from_env,
    )
except ImportError:
    DiscordNotifier = None
    NotificationLevel = None
    create_discord_notifier_from_env = None

try:
    from src.utils.rate_limit_decorator import rate_limit
except ImportError:
    rate_limit = None

try:
    from src.utils.retry_decorator import retry_api_call, retry_on_failure
except ImportError:
    retry_api_call = None
    retry_on_failure = None

try:
    from src.utils.watchdog import Watchdog, WatchdogConfig
except ImportError:
    Watchdog = None
    WatchdogConfig = None


__all__ = [
    # Config
    "Config",
    # Exceptions
    "APIError",
    "BaseAppException",
    "NetworkError",
    "RateLimitExceeded",
    # Environment validation
    "validate_on_startup",
    "validate_required_env_vars",
    # Shutdown handling
    "ShutdownHandler",
    "shutdown_handler",
    # Health monitoring
    "HealthCheckResult",
    "HealthMonitor",
    "ServiceStatus",
    # Feature flags
    "Feature",
    "FeatureFlagsManager",
    "get_feature_flags",
    "init_feature_flags",
    # Discord notifications
    "DiscordNotifier",
    "NotificationLevel",
    "create_discord_notifier_from_env",
    # Rate limiting
    "rate_limit",
    # Retry decorators
    "retry_api_call",
    "retry_on_failure",
    # Watchdog
    "Watchdog",
    "WatchdogConfig",
]

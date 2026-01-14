"""Utils module.

This module provides various utility functions and classes for the DMarket Bot:

- Environment validation
- Graceful shutdown handling
- Health monitoring
- Feature flags management
- Discord notifications
- Prometheus metrics
- Rate limiting
- Retry decorators (tenacity + stamina)
- HTTP caching (hishel)
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
    from src.utils.stamina_retry import (
        STAMINA_AVAILABLE,
        api_retry,
        async_disabled_retries,
        disabled_retries,
        retry_async,
        retry_sync,
    )
except ImportError:
    STAMINA_AVAILABLE = False
    api_retry = None
    async_disabled_retries = None
    disabled_retries = None
    retry_async = None
    retry_sync = None

try:
    from src.utils.http_cache import (
        HISHEL_AVAILABLE,
        CachedHTTPClient,
        CacheConfig,
        close_cached_client,
        create_cached_client,
        get_cached_client,
    )
except ImportError:
    HISHEL_AVAILABLE = False
    CachedHTTPClient = None
    CacheConfig = None
    close_cached_client = None
    create_cached_client = None
    get_cached_client = None

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
    # Retry decorators (tenacity)
    "retry_api_call",
    "retry_on_failure",
    # Retry decorators (stamina - production-grade)
    "STAMINA_AVAILABLE",
    "api_retry",
    "async_disabled_retries",
    "disabled_retries",
    "retry_async",
    "retry_sync",
    # HTTP caching (hishel)
    "HISHEL_AVAILABLE",
    "CachedHTTPClient",
    "CacheConfig",
    "close_cached_client",
    "create_cached_client",
    "get_cached_client",
    # Watchdog
    "Watchdog",
    "WatchdogConfig",
]

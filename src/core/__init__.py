"""Core application modules.

This package contains the core components of the DMarket Bot application,
split from the original monolithic main.py for better maintainability.

Modules:
    - app_config: Application configuration loading
    - app_initialization: Component initialization logic
    - app_lifecycle: Application lifecycle management (startup/shutdown)
    - app_signals: Signal handling for graceful shutdown
    - app_recovery: Pending trades recovery logic
"""


# Lazy imports to avoid circular dependencies and missing modules
def __getattr__(name: str):
    """Lazy import to avoid import errors when telegram is not installed."""
    if name == "Application":
        from src.core.application import Application

        return Application
    if name == "ApplicationLifecycle":
        from src.core.app_lifecycle import ApplicationLifecycle

        return ApplicationLifecycle
    if name == "SignalHandler":
        from src.core.app_signals import SignalHandler

        return SignalHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [  # noqa: F822
    "Application",
    "ApplicationLifecycle",
    "SignalHandler",
]

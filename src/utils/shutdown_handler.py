"""Graceful shutdown handler for production."""

import asyncio
import signal
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ShutdownHandler:
    """Handle graceful shutdown of the application."""

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.cleanup_tasks: list[Any] = []

    def register_cleanup(self, cleanup_func: Any) -> None:
        """Register cleanup function to run on shutdown.

        Args:
            cleanup_func: Async function to call during shutdown
        """
        self.cleanup_tasks.append(cleanup_func)

    async def graceful_shutdown(self) -> None:
        """Perform graceful shutdown."""
        logger.info("shutdown_initiated")

        # Run all cleanup tasks
        for cleanup_func in self.cleanup_tasks:
            try:
                await cleanup_func()
                logger.info("cleanup_task_completed", task=cleanup_func.__name__)
            except Exception as e:
                logger.error(
                    "cleanup_task_failed",
                    task=cleanup_func.__name__,
                    error=str(e),
                )

        logger.info("shutdown_complete")
        self.shutdown_event.set()

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame: Any) -> None:
            """Handle shutdown signals."""
            logger.info("shutdown_signal_received", signal=signum)
            asyncio.create_task(self.graceful_shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()


# Global shutdown handler
shutdown_handler = ShutdownHandler()

"""Webhook support for Telegram bot.

Enables scalable deployment with load balancers.
"""

import logging

from telegram import Update
from telegram.ext import Application

logger = logging.getLogger(__name__)


class WebhookConfig:
    """Webhook configuration."""

    def __init__(
        self,
        url: str,
        port: int = 8443,
        listen: str = "0.0.0.0",
        url_path: str = "telegram-webhook",
        cert_path: str | None = None,
        key_path: str | None = None,
    ):
        """Initialize webhook config.

        Args:
            url: Public URL for webhook (e.g., https://bot.example.com)
            port: Port to listen on (default: 8443)
            listen: Address to bind to (default: 0.0.0.0)
            url_path: URL path for webhook (default: telegram-webhook)
            cert_path: Path to SSL certificate (optional)
            key_path: Path to SSL private key (optional)
        """
        self.url = url.rstrip("/")
        self.port = port
        self.listen = listen
        self.url_path = url_path
        self.cert_path = cert_path
        self.key_path = key_path

    @property
    def webhook_url(self) -> str:
        """Get full webhook URL."""
        return f"{self.url}/{self.url_path}"

    @property
    def is_ssl(self) -> bool:
        """Check if SSL is configured."""
        return self.cert_path is not None and self.key_path is not None


async def setup_webhook(
    application: Application,
    config: WebhookConfig,
) -> None:
    """Setup webhook for bot.

    Args:
        application: Telegram application
        config: Webhook configuration
    """
    logger.info(f"Setting up webhook: {config.webhook_url}")

    try:
        # Set webhook
        await application.bot.set_webhook(
            url=config.webhook_url,
            certificate=open(config.cert_path, "rb") if config.cert_path else None,
            max_connections=100,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Clear pending updates
        )

        logger.info(f"✅ Webhook set successfully: {config.webhook_url}")
        logger.info(f"   Listening on: {config.listen}:{config.port}")
        logger.info(f"   SSL: {'enabled' if config.is_ssl else 'disabled'}")

    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        raise


async def start_webhook(
    application: Application,
    config: WebhookConfig,
) -> None:
    """Start webhook server.

    Args:
        application: Telegram application
        config: Webhook configuration
    """
    logger.info("Starting webhook server...")

    try:
        # Setup webhook
        await setup_webhook(application, config)

        # Start webhook server
        await application.run_webhook(
            listen=config.listen,
            port=config.port,
            url_path=config.url_path,
            cert=config.cert_path,
            key=config.key_path,
            webhook_url=config.webhook_url,
        )

        logger.info("Webhook server started successfully")

    except Exception as e:
        logger.error(f"Failed to start webhook server: {e}")
        raise


async def stop_webhook(application: Application) -> None:
    """Stop webhook and delete from Telegram.

    Args:
        application: Telegram application
    """
    logger.info("Stopping webhook...")

    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")


def is_webhook_mode(webhook_url: str | None) -> bool:
    """Check if webhook mode is enabled.

    Args:
        webhook_url: Webhook URL from config

    Returns:
        True if webhook mode is enabled
    """
    return webhook_url is not None and len(webhook_url.strip()) > 0

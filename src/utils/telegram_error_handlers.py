"""Error boundaries for Telegram bot handlers.

This module provides decorators and base handlers with comprehensive
error handling for Telegram bot commands and callbacks.
"""

from collections.abc import Callable
import functools
import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from src.utils.exceptions import APIError, AuthenticationError, RateLimitError, ValidationError
from src.utils.sentry_integration import add_breadcrumb, capture_exception, set_user_context


logger = logging.getLogger(__name__)


def telegram_error_boundary(
    user_friendly_message: str = "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
    log_context: bool = True,
) -> Callable:
    """Decorator for Telegram handlers with comprehensive error handling.

    This decorator:
    - Catches and logs all exceptions
    - Sends user-friendly error messages
    - Captures errors in Sentry
    - Logs request context (user_id, command, parameters)

    Args:
        user_friendly_message: Message to send to user on error
        log_context: Whether to log full context (user_id, command, etc.)

    Returns:
        Decorated handler function

    Example:
        >>> @telegram_error_boundary(
        >>>     user_friendly_message="❌ Не удалось выполнить команду"
        >>> )
        >>> async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        >>> # Handler logic
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            # Extract context information
            user_id = None
            username = None
            command = None
            message_text = None

            try:
                if update.effective_user:
                    user_id = update.effective_user.id
                    username = update.effective_user.username

                if update.message:
                    message_text = update.message.text
                    if message_text and message_text.startswith("/"):
                        command = message_text.split()[0]
                elif update.callback_query:
                    command = "callback_query"
                    if update.callback_query.data:
                        message_text = update.callback_query.data

                # Log request start
                if log_context:
                    logger.info(
                        f"Handler {func.__name__} started",
                        extra={
                            "handler": func.__name__,
                            "user_id": user_id,
                            "username": username,
                            "command": command,
                            "message_text": message_text,
                        },
                    )

                # Set Sentry user context
                if user_id:
                    set_user_context(user_id=user_id, username=username)

                # Add Sentry breadcrumb
                add_breadcrumb(
                    message=f"Executing handler: {func.__name__}",
                    category="handler",
                    level="info",
                    data={
                        "user_id": user_id,
                        "command": command,
                    },
                )

                # Execute handler
                result = await func(update, context, *args, **kwargs)

                # Log success
                if log_context:
                    logger.info(
                        f"Handler {func.__name__} completed successfully",
                        extra={
                            "handler": func.__name__,
                            "user_id": user_id,
                        },
                    )

                return result

            except ValidationError as e:
                # User input validation error
                logger.warning(
                    f"Validation error in {func.__name__}",
                    extra={
                        "handler": func.__name__,
                        "user_id": user_id,
                        "error": str(e),
                    },
                )
                error_message = f"❌ Ошибка валидации: {e}"
                if update.message:
                    await update.message.reply_text(error_message)
                elif update.callback_query:
                    await update.callback_query.answer(error_message, show_alert=True)

            except AuthenticationError as e:
                # Authentication/API key error
                logger.exception(
                    "Authentication error in %s",
                    func.__name__,
                    extra={
                        "handler": func.__name__,
                        "user_id": user_id,
                    },
                )
                error_message = "❌ Ошибка аутентификации. Проверьте API ключи в /settings"
                if update.message:
                    await update.message.reply_text(error_message)
                elif update.callback_query:
                    await update.callback_query.answer(error_message, show_alert=True)

                # Capture in Sentry
                capture_exception(
                    e,
                    level="error",
                    tags={"handler": func.__name__, "error_type": "authentication"},
                    extra={"user_id": user_id},
                )

            except RateLimitError as e:
                # Rate limit error
                logger.warning(
                    f"Rate limit error in {func.__name__}",
                    extra={
                        "handler": func.__name__,
                        "user_id": user_id,
                        "error": str(e),
                        "retry_after": getattr(e, "retry_after", None),
                    },
                )
                retry_after = getattr(e, "retry_after", 60)
                error_message = f"⏳ Превышен лимит запросов. Попробуйте через {retry_after} секунд"
                if update.message:
                    await update.message.reply_text(error_message)
                elif update.callback_query:
                    await update.callback_query.answer(error_message, show_alert=True)

            except APIError as e:
                # Generic API error
                logger.exception(
                    "API error in %s",
                    func.__name__,
                    extra={
                        "handler": func.__name__,
                        "user_id": user_id,
                        "status_code": getattr(e, "status_code", None),
                    },
                )
                error_message = "❌ Ошибка при обращении к API DMarket. Попробуйте позже"
                if update.message:
                    await update.message.reply_text(error_message)
                elif update.callback_query:
                    await update.callback_query.answer(error_message, show_alert=True)

                # Capture in Sentry
                capture_exception(
                    e,
                    level="error",
                    tags={"handler": func.__name__, "error_type": "api"},
                    extra={
                        "user_id": user_id,
                        "status_code": getattr(e, "status_code", None),
                    },
                )

            except Exception as e:
                # Unexpected error
                logger.exception(
                    f"Unexpected error in {func.__name__}",
                    extra={
                        "handler": func.__name__,
                        "user_id": user_id,
                        "command": command,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )

                # Send user-friendly message
                if update.message:
                    await update.message.reply_text(user_friendly_message)
                elif update.callback_query:
                    await update.callback_query.answer(user_friendly_message, show_alert=True)

                # Capture in Sentry
                capture_exception(
                    e,
                    level="error",
                    tags={
                        "handler": func.__name__,
                        "error_type": type(e).__name__,
                    },
                    extra={
                        "user_id": user_id,
                        "command": command,
                        "message_text": message_text,
                    },
                )

        return wrapper

    return decorator


class BaseHandler:
    """Base class for Telegram handlers with error handling.

    This class provides common functionality and error handling
    for all Telegram bot handlers.
    """

    def __init__(self, logger_name: str | None = None):
        """Initialize base handler.

        Args:
            logger_name: Name for the logger (defaults to class name)
        """
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)

    async def handle_error(
        self,
        update: Update,
        error: Exception,
        user_message: str = "❌ Произошла ошибка",
    ) -> None:
        """Handle error and notify user.

        Args:
            update: Telegram update object
            error: Exception that occurred
            user_message: Message to send to user
        """
        # Extract user info
        user_id = update.effective_user.id if update.effective_user else None

        # Log error
        self.logger.exception(
            "Error occurred: %s",
            error,
            extra={
                "user_id": user_id,
                "error_type": type(error).__name__,
            },
        )

        # Notify user
        if update.message:
            await update.message.reply_text(user_message)
        elif update.callback_query:
            await update.callback_query.answer(user_message, show_alert=True)

        # Capture in Sentry
        capture_exception(
            error,
            level="error",
            tags={"handler": self.__class__.__name__},
            extra={"user_id": user_id},
        )

    async def validate_user(self, update: Update) -> bool:
        """Validate that user exists and is authorized.

        Args:
            update: Telegram update object

        Returns:
            True if user is valid, False otherwise
        """
        if not update.effective_user:
            self.logger.warning("Update without effective_user")
            return False

        return True

    async def safe_reply(
        self,
        update: Update,
        text: str,
        **kwargs: Any,
    ) -> None:
        """Safely send reply to user, handling different update types.

        Args:
            update: Telegram update object
            text: Text to send
            **kwargs: Additional arguments for reply_text
        """
        try:
            if update.message:
                await update.message.reply_text(text, **kwargs)
            elif update.callback_query:
                await update.callback_query.message.reply_text(text, **kwargs)  # type: ignore[union-attr]
                await update.callback_query.answer()
        except Exception:
            self.logger.exception(
                "Failed to send reply",
                extra={"text": text},
            )

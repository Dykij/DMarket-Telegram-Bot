"""Resume command handler for resuming bot operations after pause.

This module provides the /resume command to manually resume bot operations
after they have been paused due to consecutive errors.
"""

from telegram import Update
from telegram.ext import ContextTypes

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def resume_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /resume command to resume bot operations.

    Args:
        update: Telegram update object
        context: Callback context

    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    # Получить state_manager из bot_data
    state_manager = context.bot_data.get("state_manager")

    if not state_manager:
        await update.message.reply_text(
            "❌ Система управления состоянием недоступна",
        )
        logger.error("state_manager not found in bot_data, user_id=%s", user_id)
        return

    # Проверить что бот на паузе
    if not state_manager.is_paused:
        await update.message.reply_text(
            "ℹ️ Бот не находится на паузе.\n"
            f"Текущее количество последовательных ошибок: "
            f"{state_manager.consecutive_errors}",
        )
        logger.info(
            "Resume attempt when bot not paused, user_id=%s, errors=%d",
            user_id,
            state_manager.consecutive_errors,
        )
        return

    # Проверить права администратора (опционально)
    config = context.bot_data.get("config")
    if config and hasattr(config.security, "admin_users"):
        admin_users = config.security.admin_users
        if admin_users and user_id not in admin_users:
            await update.message.reply_text(
                "⛔ Только администраторы могут возобновлять работу бота",
            )
            logger.warning("Unauthorized resume attempt, user_id=%s", user_id)
            return

    # Возобновить операции
    old_errors = state_manager.consecutive_errors
    state_manager.resume_operations()

    await update.message.reply_text(
        "✅ Работа бота возобновлена!\n\n"
        f"📊 Сброшено {old_errors} последовательных ошибок\n"
        "🔄 Операции восстановлены\n\n"
        "⚠️ Внимательно следите за логами и уведомлениями.",
    )

    logger.info(
        "Bot operations resumed by admin, user_id=%s, reset_errors=%d",
        user_id,
        old_errors,
    )

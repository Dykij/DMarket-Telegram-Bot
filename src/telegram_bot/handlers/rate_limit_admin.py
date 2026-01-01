"""
Admin команды для управления rate limiting.
"""

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from src.utils.user_rate_limiter import RateLimitConfig, UserRateLimiter


logger = structlog.get_logger(__name__)

# ID администраторов (должно быть в конфиге)
ADMIN_IDS = [123456789]  # Заменить на реальные ID


def is_admin(user_id: int) -> bool:
    """Проверить является ли пользователь администратором."""
    return user_id in ADMIN_IDS


async def rate_limit_stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Команда /ratelimit_stats - показать статистику лимитов.

    Usage: /ratelimit_stats [user_id]
    """
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам"
        )
        return

    rate_limiter: UserRateLimiter | None = getattr(
        context.bot_data, "user_rate_limiter", None
    )

    if not rate_limiter:
        await update.message.reply_text("❌ Rate limiter не настроен")
        return

    # Получить user_id из аргументов или использовать свой
    args = context.args
    user_id = int(args[0]) if args and args[0].isdigit() else update.effective_user.id

    try:
        stats = await rate_limiter.get_user_stats(user_id)

        # Форматировать статистику
        lines = [f"📊 **Статистика rate limits для пользователя {user_id}**\n"]

        for action, info in stats.items():
            remaining = info.get("remaining", 0)
            limit = info.get("limit", 0)
            usage_percent = ((limit - remaining) / limit * 100) if limit > 0 else 0

            emoji = "🟢" if usage_percent < 50 else "🟡" if usage_percent < 80 else "🔴"

            lines.append(
                f"{emoji} **{action}**: {limit - remaining}/{limit} ({usage_percent:.0f}%)"
            )

        message = "\n".join(lines)
        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.exception("rate_limit_stats_error", user_id=user_id)
        await update.message.reply_text(f"❌ Ошибка получения статистики: {e}")


async def rate_limit_reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Команда /ratelimit_reset - сбросить лимиты пользователя.

    Usage: /ratelimit_reset <user_id> [action]
    """
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам"
        )
        return

    rate_limiter: UserRateLimiter | None = getattr(
        context.bot_data, "user_rate_limiter", None
    )

    if not rate_limiter:
        await update.message.reply_text("❌ Rate limiter не настроен")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "⚠️ Использование: `/ratelimit_reset <user_id> [action]`",
            parse_mode="Markdown",
        )
        return

    user_id = int(args[0])
    action = args[1] if len(args) > 1 else None

    try:
        await rate_limiter.reset_user_limits(user_id, action)

        message = f"✅ Лимиты сброшены для пользователя {user_id}" + (
            f" (действие: {action})" if action else " (все действия)"
        )
        await update.message.reply_text(message)

    except Exception as e:
        logger.exception("rate_limit_reset_error", user_id=user_id)
        await update.message.reply_text(f"❌ Ошибка сброса лимитов: {e}")


async def rate_limit_whitelist_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Команда /ratelimit_whitelist - управление whitelist.

    Usage:
        /ratelimit_whitelist add <user_id>
        /ratelimit_whitelist remove <user_id>
        /ratelimit_whitelist check <user_id>
    """
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам"
        )
        return

    rate_limiter: UserRateLimiter | None = getattr(
        context.bot_data, "user_rate_limiter", None
    )

    if not rate_limiter:
        await update.message.reply_text("❌ Rate limiter не настроен")
        return

    args = context.args
    if len(args) < 2 or not args[1].isdigit():
        await update.message.reply_text(
            "⚠️ Использование:\n"
            "`/ratelimit_whitelist add <user_id>`\n"
            "`/ratelimit_whitelist remove <user_id>`\n"
            "`/ratelimit_whitelist check <user_id>`",
            parse_mode="Markdown",
        )
        return

    action = args[0].lower()
    user_id = int(args[1])

    try:
        if action == "add":
            await rate_limiter.add_whitelist(user_id)
            await update.message.reply_text(
                f"✅ Пользователь {user_id} добавлен в whitelist"
            )

        elif action == "remove":
            await rate_limiter.remove_whitelist(user_id)
            await update.message.reply_text(
                f"✅ Пользователь {user_id} удален из whitelist"
            )

        elif action == "check":
            is_whitelisted = await rate_limiter.is_whitelisted(user_id)
            status = "в whitelist" if is_whitelisted else "не в whitelist"
            await update.message.reply_text(f"ℹ️ Пользователь {user_id} {status}")

        else:
            await update.message.reply_text(
                "❌ Неизвестное действие. Используйте: add, remove, check"
            )

    except Exception as e:
        logger.exception("rate_limit_whitelist_error", user_id=user_id)
        await update.message.reply_text(f"❌ Ошибка управления whitelist: {e}")


async def rate_limit_config_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Команда /ratelimit_config - настройка лимитов.

    Usage: /ratelimit_config <action> <requests> <window>
    Example: /ratelimit_config scan 5 60
    """
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам"
        )
        return

    rate_limiter: UserRateLimiter | None = getattr(
        context.bot_data, "user_rate_limiter", None
    )

    if not rate_limiter:
        await update.message.reply_text("❌ Rate limiter не настроен")
        return

    args = context.args

    # Показать текущие лимиты
    if not args:
        lines = ["⚙️ **Текущие лимиты:**\n"]
        for action, config in rate_limiter.limits.items():
            lines.append(
                f"• **{action}**: {config.requests} запросов/{config.window} сек"
                + (f" (burst: {config.burst})" if config.burst else "")
            )

        message = "\n".join(lines)
        await update.message.reply_text(message, parse_mode="Markdown")
        return

    # Обновить лимит
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await update.message.reply_text(
            "⚠️ Использование: `/ratelimit_config <action> <requests> <window> [burst]`\n"
            "Пример: `/ratelimit_config scan 5 60`",
            parse_mode="Markdown",
        )
        return

    action = args[0]
    requests = int(args[1])
    window = int(args[2])
    burst = int(args[3]) if len(args) > 3 and args[3].isdigit() else None

    try:
        new_config = RateLimitConfig(requests=requests, window=window, burst=burst)
        rate_limiter.update_limit(action, new_config)

        message = (
            f"✅ Лимит обновлен:\n"
            f"**Действие**: {action}\n"
            f"**Лимит**: {requests} запросов/{window} сек"
        )
        if burst:
            message += f"\n**Burst**: {burst}"

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.exception("rate_limit_config_error", action=action)
        await update.message.reply_text(f"❌ Ошибка обновления лимита: {e}")

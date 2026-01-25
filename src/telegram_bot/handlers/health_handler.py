"""Health Check Handler - Telegram Commands for Health Monitoring.

Commands:
- /health status - Current health status
- /health summary - 24h health summary
- /health ping - Manual health ping

Created: January 2, 2026
"""

import structlog
from telegram import Update
from telegram.ext import ContextTypes


logger = structlog.get_logger(__name__)


async def health_status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Get current health status.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("health_status_command", user_id=user_id)

    health_monitor = context.bot_data.get("health_check_monitor")

    if not health_monitor:
        await update.message.reply_text(
            "❌ Health Check Monitor не инициализирован",
            parse_mode="HTML",
        )
        return

    # Force health check
    await health_monitor._perform_health_check()

    await update.message.reply_text(
        "✅ Health check выполнен, статус отправлен",
        parse_mode="HTML",
    )


async def health_summary_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Get 24h health summary.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("health_summary_command", user_id=user_id)

    health_monitor = context.bot_data.get("health_check_monitor")

    if not health_monitor:
        await update.message.reply_text(
            "❌ Health Check Monitor не инициализирован",
            parse_mode="HTML",
        )
        return

    summary = health_monitor.get_health_summary()

    if summary["total_checks"] == 0:
        await update.message.reply_text(
            "ℹ️ Недостаточно данных для отчета",
            parse_mode="HTML",
        )
        return

    message = (
        f"📊 <b>Health Summary (24h)</b>\n\n"
        f"<b>Проверки:</b>\n"
        f"• Всего: {summary['total_checks']}\n"
        f"• Успешных: {summary['healthy_checks']} "
        f"({summary['health_rate']:.1f}%)\n"
        f"• Проблемных: {summary['unhealthy_checks']}\n\n"
        f"<b>Система (среднее):</b>\n"
        f"• CPU: {summary['avg_cpu']:.1f}%\n"
        f"• Memory: {summary['avg_memory']:.1f}%\n\n"
        f"<b>Последняя проверка:</b>\n"
        f"{summary['last_check'].strftime('%Y-%m-%d %H:%M:%S') if summary['last_check'] else 'N/A'}"
    )

    await update.message.reply_text(message, parse_mode="HTML")


async def health_ping_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send manual health ping.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("health_ping_command", user_id=user_id)

    health_monitor = context.bot_data.get("health_check_monitor")

    if not health_monitor:
        await update.message.reply_text(
            "❌ Health Check Monitor не инициализирован",
            parse_mode="HTML",
        )
        return

    # Record activity
    health_monitor.record_activity()

    await update.message.reply_text(
        "💓 <b>Manual Health Ping</b>\n\n✅ Бот активен и работает",
        parse_mode="HTML",
    )


__all__ = [
    "health_ping_command",
    "health_status_command",
    "health_summary_command",
]

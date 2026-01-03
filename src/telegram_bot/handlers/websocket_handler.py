"""WebSocket Handler - Telegram Commands for WebSocket Control.

Commands:
- /websocket status - Check WebSocket status
- /websocket stats - WebSocket statistics
- /websocket restart - Restart WebSocket connection

Created: January 2, 2026
"""

import structlog
from telegram import Update
from telegram.ext import ContextTypes


logger = structlog.get_logger(__name__)


async def websocket_status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Check WebSocket connection status.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("websocket_status_command", user_id=user_id)

    websocket_manager = context.bot_data.get("websocket_manager")

    if not websocket_manager:
        await update.message.reply_text(
            "❌ WebSocket не инициализирован",
            parse_mode="HTML",
        )
        return

    listener = websocket_manager.listener
    stats = listener.get_stats()

    status_emoji = "🟢" if stats["is_running"] else "🔴"
    connection_emoji = "✅" if listener.ws else "❌"

    uptime_str = "N/A"
    if stats["uptime_seconds"]:
        hours = stats["uptime_seconds"] / 3600
        uptime_str = (
            f"{hours:.1f} часов" if hours >= 1 else f"{stats['uptime_seconds'] / 60:.0f} минут"
        )

    last_event_str = "Нет событий"
    if stats["last_event_time"]:
        from datetime import datetime

        minutes_ago = (datetime.now() - stats["last_event_time"]).total_seconds() / 60
        if minutes_ago < 1:
            last_event_str = "< 1 минуты назад"
        else:
            last_event_str = f"{minutes_ago:.0f} минут назад"

    message = (
        f"{status_emoji} <b>WebSocket Status</b>\n\n"
        f"<b>Подключение:</b> {connection_emoji} {'Активно' if listener.ws else 'Отключено'}\n"
        f"<b>Работает:</b> {'Да' if stats['is_running'] else 'Нет'}\n"
        f"<b>Uptime:</b> {uptime_str}\n\n"
        f"<b>События:</b>\n"
        f"• Получено: {stats['events_received']}\n"
        f"• Обработано: {stats['events_processed']}\n"
        f"• Ошибок: {stats['events_failed']}\n"
        f"• Переподключений: {stats['reconnects']}\n\n"
        f"<b>Последнее событие:</b> {last_event_str}"
    )

    await update.message.reply_text(message, parse_mode="HTML")


async def websocket_stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Get detailed WebSocket statistics.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("websocket_stats_command", user_id=user_id)

    websocket_manager = context.bot_data.get("websocket_manager")

    if not websocket_manager:
        await update.message.reply_text(
            "❌ WebSocket не инициализирован",
            parse_mode="HTML",
        )
        return

    listener = websocket_manager.listener
    stats = listener.get_stats()

    # Calculate success rate
    total_events = stats["events_received"]
    success_rate = 0.0
    if total_events > 0:
        success_rate = (stats["events_processed"] / total_events) * 100

    message = (
        f"📊 <b>WebSocket Statistics</b>\n\n"
        f"<b>События:</b>\n"
        f"• Всего получено: {stats['events_received']}\n"
        f"• Успешно обработано: {stats['events_processed']}\n"
        f"• Ошибок обработки: {stats['events_failed']}\n"
        f"• Success rate: {success_rate:.1f}%\n\n"
        f"<b>Соединение:</b>\n"
        f"• Переподключений: {stats['reconnects']}\n"
        f"• Uptime: {stats['uptime_seconds'] / 3600:.1f} часов\n\n"
        f"<b>Производительность:</b>\n"
        f"• События/минута: {stats['events_received'] / (stats['uptime_seconds'] / 60) if stats['uptime_seconds'] > 0 else 0:.1f}\n"
    )

    await update.message.reply_text(message, parse_mode="HTML")


async def websocket_restart_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Restart WebSocket connection.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("websocket_restart_command", user_id=user_id)

    websocket_manager = context.bot_data.get("websocket_manager")

    if not websocket_manager:
        await update.message.reply_text(
            "❌ WebSocket не инициализирован",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        "🔄 Перезапуск WebSocket соединения...",
        parse_mode="HTML",
    )

    try:
        # Stop and restart
        await websocket_manager.stop()
        await websocket_manager.start()

        # Wait for connection
        connected = await websocket_manager.wait_for_connection(timeout=10.0)

        if connected:
            await update.message.reply_text(
                "✅ WebSocket успешно перезапущен",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                "⚠️ WebSocket перезапущен, но соединение не установлено",
                parse_mode="HTML",
            )

    except Exception as e:
        logger.exception("websocket_restart_failed", error=str(e))
        await update.message.reply_text(
            f"❌ Ошибка перезапуска: {e}",
            parse_mode="HTML",
        )


__all__ = [
    "websocket_restart_command",
    "websocket_stats_command",
    "websocket_status_command",
]

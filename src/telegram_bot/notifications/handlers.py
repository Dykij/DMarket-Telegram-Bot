"""Telegram command and callback handlers for notifications.

This module contains all handlers for notification-related commands and callbacks:
- create_alert_command: /alert command to create new alerts
- list_alerts_command: /alerts command to view alerts
- remove_alert_command: /removealert command to delete alerts
- settings_command: /alertsettings command to configure notification settings
- handle_alert_callback: Callback for disable_alert: prefix
- handle_buy_cancel_callback: Callback for cancel_buy: prefix
- register_notification_handlers: Registers all handlers with Application
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from .alerts import (
    add_price_alert,
    get_user_alerts,
    remove_price_alert,
    update_user_settings,
)
from .checker import run_alerts_checker
from .constants import NOTIFICATION_TYPES
from .formatters import format_alert_message
from .storage import get_storage, load_user_alerts


if TYPE_CHECKING:
    from src.dmarket.dmarket_api import DMarketAPI

logger = logging.getLogger(__name__)


async def handle_buy_cancel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle callback query for canceling buy intent notification.

    Args:
        update: Telegram Update object
        context: Callback context

    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Extract item_id from callback_data (format: cancel_buy:item_id)
    callback_data = query.data
    if not callback_data or not callback_data.startswith("cancel_buy:"):
        return

    item_id = callback_data.replace("cancel_buy:", "")

    # Update message to show cancellation
    await query.edit_message_text(
        f"❌ Покупка отменена\n\nПредмет: `{item_id}`",
        parse_mode="Markdown",
    )

    logger.info(f"Покупка отменена пользователем: {item_id}")


async def handle_alert_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle callback query for disabling price alert.

    Args:
        update: Telegram Update object
        context: Callback context

    """
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()

    # Extract alert_id from callback_data (format: disable_alert:alert_id)
    callback_data = query.data
    if not callback_data or not callback_data.startswith("disable_alert:"):
        return

    alert_id = callback_data.replace("disable_alert:", "")
    user_id = update.effective_user.id

    # Remove the alert
    success = await remove_price_alert(user_id, alert_id)

    if success:
        await query.edit_message_text(
            "🔕 Оповещение отключено",
            parse_mode="Markdown",
        )
        logger.info(f"Оповещение {alert_id} отключено пользователем {user_id}")
    else:
        await query.edit_message_text(
            "❌ Не удалось отключить оповещение. Возможно, оно уже удалено.",
            parse_mode="Markdown",
        )


async def create_alert_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    api: DMarketAPI,
) -> None:
    """Handle /alert command to create a new price alert.

    Usage: /alert <item_id> <type> <threshold>
    Types: price_drop, price_rise, volume_increase, good_deal, trend_change

    Args:
        update: Telegram Update object
        context: Callback context
        api: DMarketAPI client instance

    """
    if not update.effective_user or not update.message:
        return

    # Validate arguments
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Используйте команду в формате:\n"
            "/alert <item_id> <тип> <порог>\n\n"
            "Типы оповещений:\n"
            "• price_drop - падение цены ниже порога\n"
            "• price_rise - рост цены выше порога\n"
            "• volume_increase - увеличение объема продаж\n"
            "• good_deal - хорошая сделка (% ниже рынка)\n"
            "• trend_change - изменение тренда",
        )
        return

    item_id = context.args[0]
    alert_type = context.args[1]
    try:
        threshold = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Порог должен быть числом")
        return

    # Validate alert type
    valid_types = [
        "price_drop",
        "price_rise",
        "volume_increase",
        "good_deal",
        "trend_change",
    ]
    if alert_type not in valid_types:
        await update.message.reply_text(
            f"Неизвестный тип оповещения: {alert_type}\nДоступные типы: {', '.join(valid_types)}",
        )
        return

    try:
        # Get item info from API
        item_data = await api._request(
            method="GET",
            path=f"/exchange/v1/offers/{item_id}",
            params={},
        )

        if not item_data:
            await update.message.reply_text(f"Предмет с ID {item_id} не найден")
            return

        title = item_data.get("title", "Неизвестный предмет")
        game = item_data.get("gameId", "csgo")

        # Create the alert
        alert = await add_price_alert(
            update.effective_user.id,
            item_id,
            title,
            game,
            alert_type,
            threshold,
        )

        # Format success message
        message = "✅ Оповещение создано!\n\n"
        message += format_alert_message(alert)

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Открыть на DMarket",
                    url=f"https://dmarket.com/ingame-items/item-list/csgo-skins?userOfferId={item_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔕 Отключить оповещение",
                    callback_data=f"disable_alert:{alert['id']}",
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.exception(f"Ошибка при создании оповещения: {e}")
        await update.message.reply_text(
            f"Произошла ошибка при создании оповещения: {e!s}",
        )


async def list_alerts_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /alerts command to list all active alerts.

    Args:
        update: Telegram Update object
        context: Callback context

    """
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id

    # Get user alerts
    alerts = await get_user_alerts(user_id)

    if not alerts:
        await update.message.reply_text("У вас нет активных оповещений")
        return

    # Format alerts list
    message = f"📋 *Ваши активные оповещения ({len(alerts)}):*\n\n"

    for i, alert in enumerate(alerts, 1):
        message += f"{i}. *{alert['title']}*\n"
        message += f"   Тип: {NOTIFICATION_TYPES.get(alert['type'], alert['type'])}\n"

        if alert["type"] in {"price_drop", "price_rise"}:
            message += f"   Порог: ${alert['threshold']:.2f}\n"
        elif alert["type"] == "volume_increase":
            message += f"   Порог: {int(alert['threshold'])}\n"
        elif alert["type"] in {"good_deal", "trend_change"}:
            message += f"   Порог: {alert['threshold']:.2f}%\n"

        message += "\n"

    # Add instructions
    message += "Чтобы удалить оповещение, используйте команду:\n"
    message += "/removealert <номер_оповещения>"

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


async def remove_alert_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /removealert command to remove an alert.

    Usage: /removealert <alert_number>

    Args:
        update: Telegram Update object
        context: Callback context

    """
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id

    # Check for alert number argument
    if not context.args:
        await update.message.reply_text(
            "Используйте команду в формате:\n"
            "/removealert <номер_оповещения>\n\n"
            "Чтобы увидеть список оповещений и их номера, используйте /alerts",
        )
        return

    try:
        # Convert alert number to index
        alert_num = int(context.args[0])

        # Get user alerts
        alerts = await get_user_alerts(user_id)

        if not alerts:
            await update.message.reply_text("У вас нет активных оповещений")
            return

        if alert_num < 1 or alert_num > len(alerts):
            await update.message.reply_text(
                f"Неверный номер оповещения. Доступны: 1-{len(alerts)}",
            )
            return

        # Get alert ID
        alert_id = alerts[alert_num - 1]["id"]
        title = alerts[alert_num - 1]["title"]

        # Remove the alert
        success = await remove_price_alert(user_id, alert_id)

        if success:
            await update.message.reply_text(f"Оповещение для {title} успешно удалено")
        else:
            await update.message.reply_text("Не удалось удалить оповещение")

    except ValueError:
        await update.message.reply_text("Номер оповещения должен быть числом")
    except Exception as e:
        logger.exception(f"Ошибка при удалении оповещения: {e}")
        await update.message.reply_text(f"Произошла ошибка: {e!s}")


async def settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /alertsettings command to configure notification settings.

    Usage: /alertsettings [key=value ...]
    Keys: enabled, language, min_interval, quiet_start, quiet_end, max_alerts

    Args:
        update: Telegram Update object
        context: Callback context

    """
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    user_id_str = str(user_id)

    # Get storage and ensure user exists
    storage = get_storage()
    user_alerts = storage._alerts

    if user_id_str not in user_alerts:
        user_alerts[user_id_str] = {
            "alerts": [],
            "settings": {
                "enabled": True,
                "language": "ru",
                "min_interval": 3600,
                "quiet_hours": {"start": 23, "end": 8},
                "max_alerts_per_day": 10,
            },
            "last_notification": 0,
            "daily_notifications": 0,
            "last_day": datetime.now().strftime("%Y-%m-%d"),
        }

    # Get current settings
    settings = user_alerts[user_id_str]["settings"]

    # Process arguments if provided
    if context.args:
        for arg in context.args:
            if "=" in arg:
                key, value = arg.split("=", 1)

                if key == "enabled":
                    settings["enabled"] = value.lower() == "true"
                elif key == "language":
                    settings["language"] = value
                elif key == "min_interval":
                    with contextlib.suppress(ValueError):
                        settings["min_interval"] = int(value)
                elif key == "quiet_start":
                    with contextlib.suppress(ValueError):
                        settings["quiet_hours"]["start"] = int(value)
                elif key == "quiet_end":
                    with contextlib.suppress(ValueError):
                        settings["quiet_hours"]["end"] = int(value)
                elif key == "max_alerts":
                    with contextlib.suppress(ValueError):
                        settings["max_alerts_per_day"] = int(value)

        # Save changes
        await update_user_settings(user_id, settings)

        await update.message.reply_text("Настройки оповещений обновлены")

    # Format current settings message
    enabled = "Включены" if settings["enabled"] else "Отключены"
    language = settings["language"]
    min_interval = settings["min_interval"] // 60  # convert to minutes
    quiet_start = settings["quiet_hours"]["start"]
    quiet_end = settings["quiet_hours"]["end"]
    max_alerts = settings["max_alerts_per_day"]

    message = "⚙️ *Настройки оповещений*\n\n"
    message += f"• Состояние: *{enabled}*\n"
    message += f"• Язык: *{language}*\n"
    message += f"• Минимальный интервал: *{min_interval} минут*\n"
    message += f"• Тихие часы: *{quiet_start}:00 - {quiet_end}:00*\n"
    message += f"• Макс. оповещений в день: *{max_alerts}*\n\n"

    message += "Чтобы изменить настройки, используйте команду с параметрами:\n"
    message += "/alertsettings enabled=true|false language=ru|en min_interval=минуты "
    message += "quiet_start=час quiet_end=час max_alerts=число\n\n"
    message += "Пример:\n"
    message += "/alertsettings enabled=true min_interval=30 quiet_start=22 quiet_end=9"

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


def register_notification_handlers(
    application: Application[Any, Any, Any, Any, Any, Any],
) -> None:
    """Register all notification command and callback handlers.

    This function should be called during bot initialization to register:
    - /alert command handler
    - /alerts command handler
    - /removealert command handler
    - /alertsettings command handler
    - disable_alert: callback handler
    - cancel_buy: callback handler
    - Starts the periodic alerts checker task

    Args:
        application: Telegram Application instance

    """
    # Load user alerts from storage
    load_user_alerts()

    # Add command handlers
    application.add_handler(
        CommandHandler(
            "alert",
            lambda update, context: create_alert_command(
                update,
                context,
                application.bot_data["dmarket_api"],
            ),
        ),
    )
    application.add_handler(CommandHandler("alerts", list_alerts_command))
    application.add_handler(CommandHandler("removealert", remove_alert_command))
    application.add_handler(CommandHandler("alertsettings", settings_command))

    # Add callback query handlers
    application.add_handler(
        CallbackQueryHandler(handle_alert_callback, pattern=r"^disable_alert:"),
    )
    application.add_handler(
        CallbackQueryHandler(handle_buy_cancel_callback, pattern=r"^cancel_buy:"),
    )

    # Start periodic alerts checker
    api = application.bot_data.get("dmarket_api")
    notification_queue = application.bot_data.get("notification_queue")

    if api:
        _ = asyncio.create_task(
            run_alerts_checker(
                bot=application.bot,
                api=api,
                check_interval=300,
            )
        )
        logger.info("Запущена периодическая проверка оповещений")
    else:
        logger.warning(
            "DMarket API не найден в bot_data, периодическая проверка оповещений не запущена"
        )

"""Notification sending functions for smart notifications."""

import logging
from datetime import datetime
from typing import Any

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from src.telegram_bot.notification_queue import NotificationQueue, Priority
from src.telegram_bot.smart_notifications.preferences import save_user_preferences
from src.telegram_bot.smart_notifications.throttling import record_notification
from src.telegram_bot.utils.formatters import (
    format_market_item,
    format_opportunities,
    split_long_message,
)

logger = logging.getLogger(__name__)


async def send_price_alert_notification(
    bot: Bot,
    user_id: int,
    alert: dict[str, Any],
    item_data: dict[str, Any],
    current_price: float,
    user_prefs: dict[str, Any],
    notification_queue: NotificationQueue | None = None,
) -> None:
    """Send a price alert notification to a user.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        alert: Alert data
        item_data: Item data from DMarket
        current_price: Current price of the item
        user_prefs: User preferences
        notification_queue: Notification queue instance
    """
    try:
        chat_id = user_prefs.get("chat_id", user_id)

        # Get alert conditions
        conditions = alert.get("conditions", {})
        target_price = conditions.get("price", 0)
        condition = conditions.get("condition", "below")

        # Format item details using the formatter
        item_formatted = format_market_item(item_data, show_details=True)

        # Build the notification text
        title = f"💰 <b>Уведомление о цене: {alert.get('item_name', 'Предмет')}</b>"
        alert_details = ""

        if condition == "below":
            alert_details = (
                f"📉 Цена упала до <b>${current_price:.2f}</b> (ниже ${target_price:.2f})"
            )
        elif condition == "above":
            alert_details = (
                f"📈 Цена поднялась до <b>${current_price:.2f}</b> (выше ${target_price:.2f})"
            )
        else:
            alert_details = (
                f"🔄 Текущая цена: <b>${current_price:.2f}</b> (целевая: ${target_price:.2f})"
            )

        # Create the message
        message = f"{title}\n\n{alert_details}\n\n{item_formatted}"

        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 Купить",
                    url=f"https://dmarket.com/ingame-items/item-list/{alert.get('game', 'csgo')}-skins?userOfferId={item_data.get('itemId', '')}",
                ),
                InlineKeyboardButton(
                    "🔕 Удалить оповещение",
                    callback_data=f"alert_delete:{alert.get('id', '')}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Аналитика цен",
                    callback_data=f"price_analytics:{item_data.get('itemId', '')}",
                ),
                InlineKeyboardButton(
                    "⏰ Новое оповещение",
                    callback_data=f"alert_create:{item_data.get('itemId', '')}",
                ),
            ],
        ]

        markup = InlineKeyboardMarkup(keyboard)

        # Ensure message isn't too long
        if len(message) > 4000:
            message = message[:3900] + "...\n\n(Сообщение было сокращено)"

        # Send the notification
        if notification_queue:
            await notification_queue.enqueue(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=False,
                priority=Priority.HIGH,
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=False,
            )

        logger.info(
            f"Sent price alert notification to user {user_id} for {alert.get('item_name')}"
        )

        # Update notification history
        await record_notification(user_id, "price_alert", alert.get("item_id"))

        # Update alert if one-time
        if alert.get("one_time", False):
            # Mark as inactive
            alert["active"] = False
            save_user_preferences()

    except Exception as e:  # noqa: BLE001
        logger.exception(f"Error sending price alert notification: {e}")


async def send_market_opportunity_notification(
    bot: Bot,
    user_id: int,
    opportunity: dict[str, Any],
    user_prefs: dict[str, Any],
    notification_queue: NotificationQueue | None = None,
) -> None:
    """Send a market opportunity notification to a user.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        opportunity: Market opportunity data
        user_prefs: User preferences
        notification_queue: Notification queue instance
    """
    try:
        chat_id = user_prefs.get("chat_id", user_id)
        notification_style = user_prefs.get("preferences", {}).get(
            "notification_style",
            "detailed",
        )

        # Extract opportunity details
        item_name = opportunity.get("item_name", "Unknown Item")
        game = opportunity.get("game", "csgo")
        score = opportunity.get("opportunity_score", 0)
        buy_price = opportunity.get("buy_price", 0)
        potential_profit = opportunity.get("potential_profit", 0)
        profit_percent = opportunity.get("profit_percent", 0)
        trend = opportunity.get("trend", "stable")

        # Format opportunity as an arbitrage opportunity for proper formatting
        formatted_opportunities = [
            {
                "item_name": item_name,
                "buy_price": buy_price,
                "sell_price": buy_price + potential_profit,
                "profit": potential_profit,
                "profit_percent": profit_percent,
                "game": game,
                "buy_item_id": opportunity.get("item_id", ""),
                "timestamp": datetime.now().isoformat(),
            },
        ]

        # Use the standardized formatter for opportunities
        if notification_style == "compact":
            # For compact style, use a simplified notification
            title = "🔍 <b>Рыночная возможность</b>"

            if score >= 80:
                title = "🔥 <b>ГОРЯЧАЯ ВОЗМОЖНОСТЬ!</b>"
            elif score >= 60:
                title = "⭐ <b>Хорошая возможность</b>"

            message = (
                f"{title}\n\n"
                f"<b>{item_name}</b>\n"
                f"💲 Цена: <b>${buy_price:.2f}</b>\n"
                f"📈 Потенциальная прибыль: <b>${potential_profit:.2f}</b> ({profit_percent:.1f}%)\n"
                f"📊 Рейтинг: <b>{score}/100</b>\n\n"
                f"🕒 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"
            )
        else:
            # For detailed style, use the standard formatter
            formatted_text = format_opportunities(formatted_opportunities, 0, 1)

            # Add a custom header
            header = (
                f"🔍 <b>Рыночная возможность обнаружена</b>\n\n"
                f"📊 Рейтинг: <b>{score}/100</b>\n"
                f"📈 Тренд: <b>{trend.upper()}</b>\n\n"
            )

            message = header + formatted_text

        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 Купить",
                    url=f"https://dmarket.com/ingame-items/item-list/{game}-skins?userOfferId={opportunity.get('item_id', '')}",
                ),
                InlineKeyboardButton(
                    "📊 Подробный анализ",
                    callback_data=f"analyze_opportunity:{opportunity.get('item_id', '')}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔔 Создать оповещение",
                    callback_data=f"create_alert:{opportunity.get('item_id', '')}",
                ),
                InlineKeyboardButton(
                    "🚫 Отключить уведомления",
                    callback_data="disable_notifications",
                ),
            ],
        ]

        markup = InlineKeyboardMarkup(keyboard)

        # Split message if needed
        messages = split_long_message(message)

        # Send the notification(s)
        for i, msg_part in enumerate(messages):
            # Send markup only with the last part
            reply_markup_part = markup if i == len(messages) - 1 else None

            if notification_queue:
                await notification_queue.enqueue(
                    chat_id=chat_id,
                    text=msg_part,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup_part,
                    disable_web_page_preview=True,
                    priority=Priority.NORMAL,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=msg_part,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup_part,
                    disable_web_page_preview=True,
                )

        logger.info(
            f"Sent market opportunity notification to user {user_id} for {item_name}"
        )

        # Update notification history
        await record_notification(
            user_id,
            "market_opportunity",
            opportunity.get("item_id"),
        )

    except Exception as e:  # noqa: BLE001
        logger.exception(f"Error sending market opportunity notification: {e}")


async def notify_user(
    bot: Bot,
    user_id: int,
    message: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    notification_queue: NotificationQueue | None = None,
) -> bool:
    """Send a notification to a user.

    Args:
        bot: Telegram Bot instance
        user_id: Telegram user ID
        message: Message text
        reply_markup: Optional reply markup
        notification_queue: Notification queue instance

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        if notification_queue:
            await notification_queue.enqueue(
                chat_id=user_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
                priority=Priority.HIGH,
            )
        else:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )
        return True
    except Exception as e:  # noqa: BLE001
        logger.exception(f"Error sending notification to user {user_id}: {e}")
        return False

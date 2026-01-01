"""Trading notification functions.

This module provides functions for sending trading-related notifications:
- Buy intent notifications
- Buy success/failure notifications
- Sell success notifications
- Critical shutdown notifications
- Crash notifications

Extracted from notifier.py during R-4 refactoring.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .alerts import can_send_notification, increment_notification_count
from .constants import NOTIFICATION_PRIORITIES


if TYPE_CHECKING:
    from telegram import Bot

__all__ = [
    "send_buy_failed_notification",
    "send_buy_intent_notification",
    "send_buy_success_notification",
    "send_crash_notification",
    "send_critical_shutdown_notification",
    "send_sell_success_notification",
]

logger = logging.getLogger(__name__)


async def send_buy_intent_notification(
    bot: Bot,
    user_id: int,
    item: dict[str, Any],
    reason: str = "",
    callback_data: str | None = None,
) -> bool:
    """Send notification about intent to buy an item.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        item: Item information dict
        reason: Reason for buy recommendation
        callback_data: Callback data for cancel button

    Returns:
        True if notification was sent

    """
    if not can_send_notification(user_id):
        logger.debug("Skipping buy intent notification for user %d", user_id)
        return False

    title = item.get("title", "Unknown Item")
    price = item.get("price", {}).get("USD", 0) / 100
    game = item.get("game", "csgo")

    message = (
        "🛒 <b>Рекомендация к покупке</b>\n\n"
        f"📦 <b>{title}</b>\n"
        f"💰 Цена: <b>${price:.2f}</b>\n"
        f"🎮 Игра: {game.upper()}\n"
    )

    if reason:
        message += f"\n📝 Причина: {reason}\n"

    keyboard = None
    if callback_data:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Купить",
                        callback_data=f"buy:{callback_data}",
                    ),
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=f"cancel_buy:{callback_data}",
                    ),
                ],
            ]
        )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        increment_notification_count(user_id)
        logger.info("Sent buy intent notification to user %d", user_id)
        return True
    except Exception:
        logger.exception("Failed to send buy intent to user %d", user_id)
        return False


async def send_buy_success_notification(
    bot: Bot,
    user_id: int,
    item: dict[str, Any],
    buy_price: float,
    order_id: str | None = None,
) -> bool:
    """Send notification about successful purchase.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        item: Purchased item information
        buy_price: Purchase price in USD
        order_id: DMarket order ID (optional)

    Returns:
        True if notification was sent

    """
    title = item.get("title", "Unknown Item")

    message = (
        "✅ <b>Покупка выполнена!</b>\n\n"
        f"📦 <b>{title}</b>\n"
        f"💰 Цена покупки: <b>${buy_price:.2f}</b>\n"
    )

    if order_id:
        message += f"📋 ID заказа: <code>{order_id}</code>\n"

    message += "\n💡 Предмет добавлен в инвентарь."

    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        increment_notification_count(user_id)
        logger.info("Sent buy success notification to user %d", user_id)
        return True
    except Exception:
        logger.exception("Failed to send buy success to user %d", user_id)
        return False


async def send_buy_failed_notification(
    bot: Bot,
    user_id: int,
    item: dict[str, Any],
    error: str,
) -> bool:
    """Send notification about failed purchase.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        item: Item that failed to purchase
        error: Error message

    Returns:
        True if notification was sent

    """
    title = item.get("title", "Unknown Item")
    price = item.get("price", {}).get("USD", 0) / 100

    message = f"❌ <b>Ошибка покупки</b>\n\n📦 <b>{title}</b>\n💰 Цена: ${price:.2f}\n\n⚠️ Ошибка: {error}"

    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        increment_notification_count(user_id)
        logger.info("Sent buy failed notification to user %d", user_id)
        return True
    except Exception:
        logger.exception("Failed to send buy failed to user %d", user_id)
        return False


async def send_sell_success_notification(
    bot: Bot,
    user_id: int,
    item: dict[str, Any],
    sell_price: float,
    buy_price: float | None = None,
    offer_id: str | None = None,
) -> bool:
    """Send notification about successful sale.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        item: Sold item information
        sell_price: Sale price in USD
        buy_price: Original buy price for profit calculation
        offer_id: DMarket offer ID (optional)

    Returns:
        True if notification was sent

    """
    title = item.get("title", "Unknown Item")

    message = (
        "💰 <b>Продажа выполнена!</b>\n\n"
        f"📦 <b>{title}</b>\n"
        f"💵 Цена продажи: <b>${sell_price:.2f}</b>\n"
    )

    if buy_price is not None:
        profit = sell_price - buy_price
        profit_pct = (profit / buy_price) * 100 if buy_price > 0 else 0
        profit_emoji = "📈" if profit > 0 else "📉"
        message += (
            f"\n{profit_emoji} Прибыль: <b>${profit:.2f}</b> ({profit_pct:+.1f}%)\n"
        )

    if offer_id:
        message += f"📋 ID предложения: <code>{offer_id}</code>\n"

    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        increment_notification_count(user_id)
        logger.info("Sent sell success notification to user %d", user_id)
        return True
    except Exception:
        logger.exception("Failed to send sell success to user %d", user_id)
        return False


async def send_critical_shutdown_notification(
    bot: Bot,
    user_id: int,
    reason: str,
    details: dict[str, Any] | None = None,
) -> bool:
    """Send critical shutdown notification.

    High priority notification that bypasses normal rate limits.

    Args:
        bot: Telegram bot instance
        user_id: User ID to notify
        reason: Shutdown reason
        details: Additional details dict

    Returns:
        True if notification was sent

    """
    priority = NOTIFICATION_PRIORITIES.get("critical", 100)

    message = f"🚨 <b>КРИТИЧЕСКОЕ ОТКЛЮЧЕНИЕ</b>\n\n⚠️ Причина: {reason}\n"

    if details:
        message += "\n📋 Детали:\n"
        for key, value in details.items():
            message += f"  • {key}: {value}\n"

    message += "\n⏰ Бот был остановлен для предотвращения потерь."

    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        logger.warning(
            "Sent critical shutdown notification to user %d (priority=%d)",
            user_id,
            priority,
        )
        return True
    except Exception:
        logger.exception("Failed to send critical shutdown to user %d", user_id)
        return False


async def send_crash_notification(
    bot: Bot,
    user_id: int,
    error_type: str,
    error_message: str,
    traceback_str: str | None = None,
) -> bool:
    """Send crash notification to admin.

    Args:
        bot: Telegram bot instance
        user_id: Admin user ID to notify
        error_type: Exception type name
        error_message: Error message
        traceback_str: Full traceback (optional)

    Returns:
        True if notification was sent

    """
    message = (
        "💥 <b>CRASH REPORT</b>\n\n"
        f"❌ Тип: <code>{error_type}</code>\n"
        f"📝 Сообщение: {error_message}\n"
    )

    if traceback_str:
        # Truncate long tracebacks
        max_tb_len = 1000
        if len(traceback_str) > max_tb_len:
            traceback_str = traceback_str[:max_tb_len] + "...[truncated]"
        message += f"\n📋 Traceback:\n<pre>{traceback_str}</pre>"

    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        logger.error(
            "Sent crash notification to admin %d: %s",
            user_id,
            error_type,
        )
        return True
    except Exception:
        logger.exception("Failed to send crash notification to %d", user_id)
        return False

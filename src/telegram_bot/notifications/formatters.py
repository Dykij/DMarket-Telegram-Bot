"""Notification message formatters.

This module provides formatting functions for notification messages:
- Alert message formatting
- Price formatting
- Item detail formatting

Extracted from notifier.py during R-4 refactoring.
"""

from __future__ import annotations

from typing import Any


__all__ = [
    "format_alert_message",
    "format_item_brief",
    "format_price",
    "format_profit",
]


def format_price(price_cents: float | None, currency: str = "USD") -> str:
    """Format price from cents to display string.

    Args:
        price_cents: Price in cents (or None)
        currency: Currency code (default USD)

    Returns:
        Formatted price string

    Examples:
        >>> format_price(1250)
        '$12.50'
        >>> format_price(None)
        'N/A'

    """
    if price_cents is None:
        return "N/A"
    price_usd = price_cents / 100
    if currency == "USD":
        return f"${price_usd:.2f}"
    return f"{price_usd:.2f} {currency}"


def format_profit(
    buy_price: float,
    sell_price: float,
    include_percent: bool = True,
) -> str:
    """Format profit for display.

    Args:
        buy_price: Buy price in USD
        sell_price: Sell price in USD
        include_percent: Include percentage

    Returns:
        Formatted profit string

    """
    profit = sell_price - buy_price
    emoji = "📈" if profit >= 0 else "📉"

    if include_percent and buy_price > 0:
        percent = (profit / buy_price) * 100
        return f"{emoji} ${profit:.2f} ({percent:+.1f}%)"
    return f"{emoji} ${profit:.2f}"


def format_item_brief(item: dict[str, Any]) -> str:
    """Format brief item information.

    Args:
        item: Item dictionary from API

    Returns:
        Brief formatted string

    """
    title = item.get("title", "Unknown")
    price = item.get("price", {}).get("USD", 0) / 100
    game = item.get("gameId", item.get("game", "csgo")).upper()

    return f"{title} | ${price:.2f} | {game}"


# Mapping of alert types to display names
NOTIFICATION_TYPES: dict[str, str] = {
    "price_drop": "Падение цены",
    "price_rise": "Рост цены",
    "price_above": "Цена выше порога",
    "volume_increase": "Рост объема торгов",
    "good_deal": "Выгодное предложение",
    "arbitrage": "Арбитражная возможность",
    "trend_change": "Изменение тренда",
    "buy_intent": "Намерение купить",
    "buy_success": "Покупка выполнена",
    "buy_failed": "Ошибка покупки",
    "sell_success": "Продажа выполнена",
    "sell_failed": "Ошибка продажи",
    "target_executed": "Таргет исполнен",
    "critical_shutdown": "Критическая остановка",
}


def format_alert_message(
    alert: dict[str, Any],
    current_price: float | None = None,
    triggered: bool = False,
) -> str:
    """Format alert notification message.

    Args:
        alert: Alert dictionary with item info
        current_price: Current item price in USD (optional)
        triggered: Whether alert was triggered

    Returns:
        Formatted HTML message

    """
    alert_type = alert.get("type", "price_drop")
    # Support both 'item_name' and 'title' for backward compatibility
    item_name = alert.get("item_name") or alert.get("title", "Unknown Item")
    # Support both 'target_price' and 'threshold' for backward compatibility
    target_price = alert.get("target_price") or alert.get("threshold", 0)
    game = alert.get("game", "csgo").upper()

    # Choose icon based on alert type
    type_icons = {
        "price_drop": "📉",
        "price_above": "📈",
        "good_deal": "💎",
        "target_executed": "🎯",
    }
    icon = type_icons.get(alert_type, "🔔")

    # Get display name for alert type
    alert_type_display = NOTIFICATION_TYPES.get(alert_type, alert_type)

    # Build message
    if triggered:
        header = f"{icon} <b>Алерт сработал!</b>"
    else:
        header = f"{icon} <b>Уведомление о цене</b>"

    message = f"{header}\n\n📦 <b>{item_name}</b>\n🎮 Игра: {game}\n"
    message += f"📊 Тип: {alert_type_display}\n"

    # Add price information
    if current_price is not None:
        message += f"💰 Текущая цена: <b>${current_price:.2f}</b>\n"

    if target_price > 0:
        message += f"🎯 Целевая цена: ${target_price:.2f}\n"

    # Add difference if both prices available
    if current_price is not None and target_price > 0:
        diff = current_price - target_price
        diff_pct = (diff / target_price) * 100 if target_price > 0 else 0

        if alert_type == "price_drop":
            if diff <= 0:
                message += f"\n✅ Цена достигла цели! ({diff_pct:+.1f}%)"
            else:
                message += f"\n📊 До цели: ${diff:.2f} ({diff_pct:.1f}%)"
        elif alert_type == "price_above":
            if diff >= 0:
                message += f"\n✅ Цена выше цели! ({diff_pct:+.1f}%)"

    return message


def format_alerts_list(alerts: list[dict[str, Any]]) -> str:
    """Format list of alerts for display.

    Args:
        alerts: List of alert dictionaries

    Returns:
        Formatted message with numbered alerts

    """
    if not alerts:
        return "📭 <b>У вас нет активных алертов</b>"

    message = f"🔔 <b>Ваши алерты</b> ({len(alerts)}):\n\n"

    for i, alert in enumerate(alerts, 1):
        item_name = alert.get("item_name", "Unknown")
        target_price = alert.get("target_price", 0)
        alert_type = alert.get("type", "price_drop")
        game = alert.get("game", "csgo").upper()

        type_label = {
            "price_drop": "📉 падение",
            "price_above": "📈 рост",
            "good_deal": "💎 выгодная сделка",
        }.get(alert_type, "🔔")

        message += f"<b>{i}.</b> {item_name}\n   {type_label} | ${target_price:.2f} | {game}\n\n"

    message += "💡 Используйте /remove_alert N для удаления"

    return message


def format_user_settings(settings: dict[str, Any]) -> str:
    """Format user notification settings for display.

    Args:
        settings: User settings dictionary

    Returns:
        Formatted settings message

    """
    enabled = settings.get("notifications_enabled", True)
    daily_limit = settings.get("daily_limit", 50)
    quiet_hours = settings.get("quiet_hours", {"enabled": False})
    min_profit = settings.get("min_profit_percent", 5.0)

    status = "✅ Включены" if enabled else "❌ Отключены"

    message = (
        "⚙️ <b>Настройки уведомлений</b>\n\n"
        f"📢 Статус: {status}\n"
        f"📊 Дневной лимит: {daily_limit} сообщений\n"
        f"💰 Мин. прибыль: {min_profit}%\n"
    )

    if quiet_hours.get("enabled"):
        start = quiet_hours.get("start", 23)
        end = quiet_hours.get("end", 7)
        message += f"🌙 Тихие часы: {start}:00 - {end}:00\n"
    else:
        message += "🌙 Тихие часы: отключены\n"

    return message

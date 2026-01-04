"""Клавиатуры алертов.

Содержит клавиатуры для управления ценовыми алертами
и уведомлениями.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.telegram_bot.keyboards.utils import CB_BACK, CB_CANCEL


def get_alert_keyboard() -> InlineKeyboardMarkup:
    """Создать главную клавиатуру алертов.

    Returns:
        InlineKeyboardMarkup с опциями алертов
    """
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Создать алерт", callback_data="alert_create"),
            InlineKeyboardButton(text="📋 Мои алерты", callback_data="alert_list"),
        ],
        [
            InlineKeyboardButton(text="🔔 Активные", callback_data="alert_active"),
            InlineKeyboardButton(text="📊 История", callback_data="alert_history"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="alert_settings"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=CB_BACK),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_alert_type_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора типа алерта.

    Returns:
        InlineKeyboardMarkup с типами алертов
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="📉 Цена ниже",
                callback_data="alert_type_below",
            ),
            InlineKeyboardButton(
                text="📈 Цена выше",
                callback_data="alert_type_above",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎯 Целевая цена",
                callback_data="alert_type_target",
            ),
            InlineKeyboardButton(
                text="📊 Изменение %",
                callback_data="alert_type_percent",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🆕 Новый предмет",
                callback_data="alert_type_new_item",
            ),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data=CB_CANCEL),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_alert_actions_keyboard(alert_id: str) -> InlineKeyboardMarkup:
    """Создать клавиатуру действий с алертом.

    Args:
        alert_id: ID алерта

    Returns:
        InlineKeyboardMarkup с действиями
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="✏️ Изменить",
                callback_data=f"alert_edit_{alert_id}",
            ),
            InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"alert_delete_{alert_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏸️ Приостановить",
                callback_data=f"alert_pause_{alert_id}",
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data=f"alert_stats_{alert_id}",
            ),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="alert_list"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_price_alerts_keyboard(
    alerts: list[dict],
    page: int = 1,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """Создать клавиатуру списка ценовых алертов.

    Args:
        alerts: Список алертов
        page: Текущая страница
        page_size: Количество алертов на странице

    Returns:
        InlineKeyboardMarkup со списком алертов и навигацией
    """
    total_pages = (len(alerts) + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_alerts = alerts[start_idx:end_idx]

    keyboard = []

    # Кнопки для каждого алерта
    for alert in page_alerts:
        alert_id = alert.get("id", "unknown")
        item_name = alert.get("item_name", "Unknown Item")[:25]
        price = alert.get("target_price", 0)
        alert_type = alert.get("type", "below")

        type_emoji = "📉" if alert_type == "below" else "📈"
        status_emoji = "🟢" if alert.get("active", True) else "🔴"

        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {type_emoji} {item_name} ${price:.2f}",
                callback_data=f"alert_view_{alert_id}",
            )
        ])

    # Навигация по страницам
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"alerts_page_{page - 1}"))
        nav_row.append(
            InlineKeyboardButton(
                text=f"📄 {page}/{total_pages}",
                callback_data="alerts_page_info",
            )
        )
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"alerts_page_{page + 1}"))
        keyboard.append(nav_row)

    # Основные действия
    keyboard.extend((
        [
            InlineKeyboardButton(text="➕ Создать", callback_data="alert_create"),
            InlineKeyboardButton(text="🗑️ Удалить все", callback_data="alert_delete_all"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=CB_BACK)],
    ))

    return InlineKeyboardMarkup(keyboard)


def get_alert_notification_settings_keyboard(
    settings: dict | None = None,
) -> InlineKeyboardMarkup:
    """Создать клавиатуру настроек уведомлений алертов.

    Args:
        settings: Текущие настройки уведомлений

    Returns:
        InlineKeyboardMarkup с настройками
    """
    if settings is None:
        settings = {}

    push_enabled = settings.get("push", True)
    telegram_enabled = settings.get("telegram", True)
    email_enabled = settings.get("email", False)
    sound_enabled = settings.get("sound", True)

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"📱 Push: {'✅' if push_enabled else '❌'}",
                callback_data="alert_setting_push",
            ),
            InlineKeyboardButton(
                text=f"💬 Telegram: {'✅' if telegram_enabled else '❌'}",
                callback_data="alert_setting_telegram",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"📧 Email: {'✅' if email_enabled else '❌'}",
                callback_data="alert_setting_email",
            ),
            InlineKeyboardButton(
                text=f"🔊 Звук: {'✅' if sound_enabled else '❌'}",
                callback_data="alert_setting_sound",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🕐 Время тишины",
                callback_data="alert_setting_quiet_hours",
            ),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="alerts"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

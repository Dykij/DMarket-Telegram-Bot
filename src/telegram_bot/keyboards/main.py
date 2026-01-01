"""Главные меню и основные клавиатуры.

Содержит клавиатуры главного меню, выбора игр
и постоянные reply клавиатуры.
"""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.dmarket.arbitrage import GAMES
from src.telegram_bot.keyboards.utils import CB_GAME_PREFIX, CB_HELP, CB_SETTINGS


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создать главную инлайн клавиатуру бота.

    Returns:
        InlineKeyboardMarkup с основными командами бота
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Арбитраж", callback_data="arbitrage"),
            InlineKeyboardButton(text="🎯 Таргеты", callback_data="targets"),
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="📦 Инвентарь", callback_data="inventory"),
        ],
        [
            InlineKeyboardButton(text="📈 Аналитика", callback_data="analytics"),
            InlineKeyboardButton(text="🔔 Оповещения", callback_data="alerts"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data=CB_SETTINGS),
            InlineKeyboardButton(text="❓ Помощь", callback_data=CB_HELP),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_permanent_reply_keyboard() -> ReplyKeyboardMarkup:
    """Создать постоянную reply клавиатуру.

    Returns:
        ReplyKeyboardMarkup с основными командами
    """
    keyboard = [
        [
            KeyboardButton(text="📊 Арбитраж"),
            KeyboardButton(text="🎯 Таргеты"),
        ],
        [
            KeyboardButton(text="💰 Баланс"),
            KeyboardButton(text="⚙️ Настройки"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def create_main_keyboard(*, include_all_buttons: bool = True) -> ReplyKeyboardMarkup:
    """Создать основную reply клавиатуру.

    Args:
        include_all_buttons: Включить все кнопки (по умолчанию True)

    Returns:
        ReplyKeyboardMarkup с основными командами
    """
    if include_all_buttons:
        keyboard = [
            [
                KeyboardButton(text="📊 Арбитраж"),
                KeyboardButton(text="🎯 Таргеты"),
                KeyboardButton(text="💰 Баланс"),
            ],
            [
                KeyboardButton(text="📦 Инвентарь"),
                KeyboardButton(text="📈 Аналитика"),
                KeyboardButton(text="🔔 Оповещения"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
                KeyboardButton(text="❓ Помощь"),
            ],
        ]
    else:
        keyboard = [
            [
                KeyboardButton(text="📊 Арбитраж"),
                KeyboardButton(text="💰 Баланс"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_games_keyboard(callback_prefix: str = CB_GAME_PREFIX) -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора игры.

    Args:
        callback_prefix: Префикс для callback_data (по умолчанию "game_")

    Returns:
        InlineKeyboardMarkup с кнопками игр
    """
    game_emojis = {
        "csgo": "🔫",
        "dota2": "⚔️",
        "tf2": "🎩",
        "rust": "🏠",
    }

    buttons = []
    row: list[InlineKeyboardButton] = []

    for game_id, game_name in GAMES.items():
        emoji = game_emojis.get(game_id, "🎮")
        button = InlineKeyboardButton(
            text=f"{emoji} {game_name}",
            callback_data=f"{callback_prefix}{game_id}",
        )
        row.append(button)

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # Кнопка отмены
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(buttons)

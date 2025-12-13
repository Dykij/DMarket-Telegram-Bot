"""Клавиатуры для арбитража.

Содержит клавиатуры для работы с арбитражным сканером,
автоматическим арбитражем и анализом рынка.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.dmarket.arbitrage import GAMES
from src.telegram_bot.keyboards.utils import CB_BACK, CB_GAME_PREFIX


def get_arbitrage_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру арбитражного меню.

    Returns:
        InlineKeyboardMarkup с опциями арбитража
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🔍 Сканировать", callback_data="arb_scan"),
            InlineKeyboardButton(text="🎮 Выбор игры", callback_data="arb_game"),
        ],
        [
            InlineKeyboardButton(text="📊 Уровни", callback_data="arb_levels"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="arb_settings"),
        ],
        [
            InlineKeyboardButton(text="🤖 Авто-арбитраж", callback_data="arb_auto"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=CB_BACK),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_modern_arbitrage_keyboard() -> InlineKeyboardMarkup:
    """Создать современную клавиатуру арбитража.

    Returns:
        InlineKeyboardMarkup с расширенными опциями
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Быстрый скан", callback_data="arb_quick"),
            InlineKeyboardButton(text="🔬 Глубокий скан", callback_data="arb_deep"),
        ],
        [
            InlineKeyboardButton(text="📈 Анализ рынка", callback_data="arb_market_analysis"),
        ],
        [
            InlineKeyboardButton(text="🎯 Создать таргет", callback_data="arb_target"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="arb_stats"),
        ],
        [
            InlineKeyboardButton(text="🔄 Сравнить площадки", callback_data="arb_compare"),
        ],
        [
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_auto_arbitrage_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру авто-арбитража.

    Returns:
        InlineKeyboardMarkup с настройками авто-арбитража
    """
    keyboard = [
        [
            InlineKeyboardButton(text="▶️ Запустить", callback_data="auto_arb_start"),
            InlineKeyboardButton(text="⏹️ Остановить", callback_data="auto_arb_stop"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="auto_arb_settings"),
            InlineKeyboardButton(text="📊 Статус", callback_data="auto_arb_status"),
        ],
        [
            InlineKeyboardButton(text="📜 История", callback_data="auto_arb_history"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="arbitrage"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_arbitrage_keyboard(
    *,
    include_auto: bool = True,
    include_analysis: bool = True,
) -> InlineKeyboardMarkup:
    """Создать клавиатуру арбитража с настраиваемыми опциями.

    Args:
        include_auto: Включить кнопку авто-арбитража
        include_analysis: Включить кнопку анализа

    Returns:
        InlineKeyboardMarkup с выбранными опциями
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🔍 Сканировать", callback_data="arb_scan"),
            InlineKeyboardButton(text="🎮 Игра", callback_data="arb_game"),
        ],
    ]

    if include_analysis:
        keyboard.append([
            InlineKeyboardButton(text="📈 Анализ", callback_data="arb_analysis"),
            InlineKeyboardButton(text="📊 Уровни", callback_data="arb_levels"),
        ])

    if include_auto:
        keyboard.append([InlineKeyboardButton(text="🤖 Авто", callback_data="arb_auto")])

    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data=CB_BACK)])

    return InlineKeyboardMarkup(keyboard)


def get_back_to_arbitrage_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру возврата к арбитражу.

    Returns:
        InlineKeyboardMarkup с кнопкой возврата
    """
    keyboard = [[InlineKeyboardButton(text="◀️ К арбитражу", callback_data="arbitrage")]]
    return InlineKeyboardMarkup(keyboard)


def get_marketplace_comparison_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру сравнения маркетплейсов.

    Returns:
        InlineKeyboardMarkup с опциями сравнения
    """
    keyboard = [
        [
            InlineKeyboardButton(text="DMarket ↔️ Steam", callback_data="cmp_steam"),
            InlineKeyboardButton(text="DMarket ↔️ Buff", callback_data="cmp_buff"),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="cmp_refresh"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="arbitrage"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_game_selection_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора игры для арбитража.

    Returns:
        InlineKeyboardMarkup с играми
    """
    game_emojis = {
        "csgo": "🔫 CS2",
        "dota2": "⚔️ Dota 2",
        "tf2": "🎩 TF2",
        "rust": "🏠 Rust",
    }

    buttons = []
    row: list[InlineKeyboardButton] = []

    for game_id in GAMES:
        label = game_emojis.get(game_id, f"🎮 {game_id}")
        button = InlineKeyboardButton(
            text=label,
            callback_data=f"{CB_GAME_PREFIX}{game_id}",
        )
        row.append(button)

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="arbitrage")])

    return InlineKeyboardMarkup(buttons)


def create_market_analysis_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру анализа рынка.

    Returns:
        InlineKeyboardMarkup с опциями анализа
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Тренды", callback_data="analysis_trends"),
            InlineKeyboardButton(text="💹 Волатильность", callback_data="analysis_vol"),
        ],
        [
            InlineKeyboardButton(text="🔥 Топ продаж", callback_data="analysis_top"),
            InlineKeyboardButton(text="📉 Падающие", callback_data="analysis_drop"),
        ],
        [
            InlineKeyboardButton(text="🎯 Рекомендации", callback_data="analysis_rec"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="arbitrage"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

"""Тесты для модуля keyboards, проверяющие создание различных клавиатур для Telegram-бота."""

from unittest.mock import patch

from telegram import InlineKeyboardMarkup

from src.telegram_bot.keyboards import (
    get_arbitrage_keyboard,
    get_auto_arbitrage_keyboard,
    get_back_to_arbitrage_keyboard,
    get_game_selection_keyboard,
)


def test_get_arbitrage_keyboard():
    """Проверяет создание клавиатуры для выбора режима арбитража."""
    keyboard = get_arbitrage_keyboard()

    # Проверяем, что возвращается правильный тип
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем количество строк в клавиатуре
    # (3 режима + авто-арбитраж + кнопка назад = 5 строк)
    assert len(keyboard.inline_keyboard) == 5

    # Проверяем наличие всех режимов
    all_buttons = [button for row in keyboard.inline_keyboard for button in row]
    callback_data = [button.callback_data for button in all_buttons]

    assert "arbitrage_boost" in callback_data
    assert "arbitrage_mid" in callback_data
    assert "arbitrage_pro" in callback_data
    assert "auto_arbitrage" in callback_data
    assert "back_to_menu" in callback_data

    # Проверяем последнюю кнопку (возврат в меню)
    last_row = keyboard.inline_keyboard[-1]
    assert len(last_row) == 1
    assert "Назад" in last_row[0].text
    assert last_row[0].callback_data == "back_to_menu"


def test_get_game_selection_keyboard():
    """Проверяет создание клавиатуры для выбора игры."""
    # Моделируем словарь игр для тестирования
    mock_games = {
        "csgo": "CS:GO",
        "dota2": "Dota 2",
        "rust": "Rust",
        "tf2": "Team Fortress 2",
    }

    with patch("src.telegram_bot.keyboards.GAMES", mock_games):
        keyboard = get_game_selection_keyboard()

    # Проверяем, что возвращается правильный тип
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем количество строк в клавиатуре
    # (4 игры + кнопка назад = 5 строк)
    assert len(keyboard.inline_keyboard) == 5

    # Проверяем, что все игры присутствуют
    all_buttons = [button for row in keyboard.inline_keyboard for button in row]

    # Исключая кнопку "Назад"
    game_buttons = [
        button for button in all_buttons if button.callback_data != "back_to_menu"
    ]
    assert len(game_buttons) == 4

    # Проверяем тексты кнопок и callback_data
    game_texts = [button.text for button in game_buttons]
    game_callbacks = [button.callback_data for button in game_buttons]

    # Проверяем callback_data (формат: game_selected:game_id)
    assert any(
        "csgo" in cb or "CS2" in text
        for cb, text in zip(game_callbacks, game_texts, strict=False)
    )
    assert any(
        "dota2" in cb or "Dota 2" in text
        for cb, text in zip(game_callbacks, game_texts, strict=False)
    )
    assert any(
        "rust" in cb or "Rust" in text
        for cb, text in zip(game_callbacks, game_texts, strict=False)
    )
    assert any(
        "tf2" in cb or "Fortress" in text
        for cb, text in zip(game_callbacks, game_texts, strict=False)
    )

    # Проверяем кнопку "Назад"
    back_button = next(
        button for button in all_buttons if button.callback_data == "back_to_menu"
    )
    assert "Назад" in back_button.text


def test_get_auto_arbitrage_keyboard():
    """Проверяет создание клавиатуры для автоматического арбитража."""
    keyboard = get_auto_arbitrage_keyboard()

    # Проверяем, что возвращается правильный тип
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем количество строк в клавиатуре
    # (3 режима + кнопка назад = 4 строки)
    assert len(keyboard.inline_keyboard) == 4

    # Проверяем наличие всех режимов
    all_buttons = [button for row in keyboard.inline_keyboard for button in row]
    callback_data = [button.callback_data for button in all_buttons]

    assert "auto_start:boost_low" in callback_data
    assert "auto_start:mid_medium" in callback_data
    assert "auto_start:pro_high" in callback_data
    assert "back_to_menu" in callback_data

    # Проверяем тексты кнопок
    button_texts = [button.text for button in all_buttons]
    assert any("Boost" in text and "прибыль" in text for text in button_texts)
    assert any("Medium" in text and "прибыль" in text for text in button_texts)
    assert any("Pro" in text and "прибыль" in text for text in button_texts)


def test_get_back_to_arbitrage_keyboard():
    """Проверяет создание клавиатуры с кнопкой возврата."""
    keyboard = get_back_to_arbitrage_keyboard()

    # Проверяем, что возвращается правильный тип
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем одну строку с одной кнопкой
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 1

    # Проверяем кнопку
    button = keyboard.inline_keyboard[0][0]
    assert "арбитраж" in button.text.lower()
    assert "назад" in button.text.lower() or "вернуть" in button.text.lower()
    assert button.callback_data == "arbitrage"

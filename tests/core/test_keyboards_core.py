"""Тесты для клавиатур Telegram бота.

Покрывают keyboards:
- Основное меню (УСТАРЕЛО - перемещено в simplified_menu_handler)
- Клавиатура настроек
- Клавиатура выбора игр (УСТАРЕЛО - перемещено в simplified_menu_handler)
- Константы callback_data
"""

import pytest
from telegram import InlineKeyboardMarkup

from src.telegram_bot.keyboards import (
    CB_BACK,
    CB_CANCEL,
    CB_GAME_PREFIX,
    CB_HELP,
    CB_NEXT_PAGE,
    CB_PREV_PAGE,
    CB_SETTINGS,
    get_back_to_settings_keyboard,
    get_settings_keyboard,
)

# REMOVED: get_games_keyboard, get_main_menu_keyboard moved to simplified_menu_handler


class TestKeyboardConstants:
    """Тесты констант для callback_data."""

    def test_callback_constants_exist(self):
        """Тест существования констант callback."""
        assert CB_CANCEL == "cancel"
        assert CB_BACK == "back"
        assert CB_NEXT_PAGE == "next_page"
        assert CB_PREV_PAGE == "prev_page"
        assert CB_GAME_PREFIX == "game_"
        assert CB_HELP == "help"
        assert CB_SETTINGS == "settings"


@pytest.mark.skip(reason="MainMenuKeyboard moved to simplified_menu_handler")
class TestMainMenuKeyboard:
    """Тесты основного меню (УСТАРЕЛО)."""

    def test_main_menu_keyboard_creation(self):
        """Тест создания основного меню."""

    def test_main_menu_has_balance_button(self):
        """Тест наличия кнопки баланса."""

    def test_main_menu_has_analytics_button(self):
        """Тест наличия кнопки аналитики."""

    def test_main_menu_has_arbitrage_button(self):
        """Тест наличия кнопки арбитража."""

        assert any("Арбитраж" in text for text in button_texts)


class TestSettingsKeyboard:
    """Тесты клавиатуры настроек."""

    def test_settings_keyboard_creation(self):
        """Тест создания клавиатуры настроек."""
        keyboard = get_settings_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0

    def test_settings_has_api_keys_button(self):
        """Тест наличия кнопки API ключей."""
        keyboard = get_settings_keyboard()

        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

        assert any("API" in text for text in button_texts)

    def test_settings_has_back_button(self):
        """Тест наличия кнопки назад."""
        keyboard = get_settings_keyboard()

        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

        assert any("Назад" in text for text in button_texts)


class TestBackToSettingsKeyboard:
    """Тесты клавиатуры возврата к настройкам."""

    def test_back_to_settings_keyboard_creation(self):
        """Тест создания клавиатуры возврата."""
        keyboard = get_back_to_settings_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1

    def test_back_to_settings_has_correct_text(self):
        """Тест текста кнопки возврата."""
        keyboard = get_back_to_settings_keyboard()

        button = keyboard.inline_keyboard[0][0]
        assert "Назад" in button.text or "настройкам" in button.text


@pytest.mark.skip(reason="GamesKeyboard moved to simplified_menu_handler")
class TestGamesKeyboard:
    """Тесты клавиатуры выбора игр (УСТАРЕЛО)."""

    def test_games_keyboard_creation(self):
        """Тест создания клавиатуры игр."""

    def test_games_keyboard_with_custom_prefix(self):
        """Тест создания клавиатуры с кастомным префиксом."""

    def test_games_keyboard_has_buttons(self):
        """Тест наличия кнопок в клавиатуре игр."""


@pytest.mark.skip(reason="Uses removed keyboards from main.py")
class TestKeyboardIntegration:
    """Интеграционные тесты клавиатур (УСТАРЕЛО)."""

    def test_all_keyboards_are_valid_telegram_objects(self):
        """Тест что все клавиатуры - валидные объекты Telegram."""
        pass

    def test_keyboards_have_callback_data(self):
        """Тест что у кнопок есть callback_data."""
        pass


class TestKeyboardStructure:
    """Тесты структуры клавиатур."""

    @pytest.mark.skip(reason="get_main_menu_keyboard removed")
    def test_main_menu_has_multiple_rows(self):
        """Тест что основное меню имеет несколько рядов."""
        pass

    def test_settings_keyboard_has_multiple_rows(self):
        """Тест что настройки имеют несколько рядов."""
        keyboard = get_settings_keyboard()

        assert len(keyboard.inline_keyboard) >= 2

    def test_back_keyboard_has_single_row(self):
        """Тест что клавиатура назад имеет один ряд."""
        keyboard = get_back_to_settings_keyboard()

        assert len(keyboard.inline_keyboard) == 1

"""Тесты для клавиатур Telegram бота.

Покрывают keyboards:
- Основное меню
- Клавиатура настроек
- Клавиатура выбора игр
- Константы callback_data
"""

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
    get_games_keyboard,
    get_main_menu_keyboard,
    get_settings_keyboard,
)


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


class TestMainMenuKeyboard:
    """Тесты основного меню."""

    def test_main_menu_keyboard_creation(self):
        """Тест создания основного меню."""
        keyboard = get_main_menu_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0

    def test_main_menu_has_balance_button(self):
        """Тест наличия кнопки баланса."""
        keyboard = get_main_menu_keyboard()

        # Проверяем что есть хотя бы одна строка с кнопками
        assert len(keyboard.inline_keyboard) > 0

        # Проверяем что кнопки есть
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

        # Должна быть кнопка с балансом
        assert any("Баланс" in text for text in button_texts)

    def test_main_menu_has_analytics_button(self):
        """Тест наличия кнопки аналитики."""
        keyboard = get_main_menu_keyboard()

        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

        assert any("Аналитика" in text for text in button_texts)

    def test_main_menu_has_arbitrage_button(self):
        """Тест наличия кнопки арбитража."""
        keyboard = get_main_menu_keyboard()

        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

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


class TestGamesKeyboard:
    """Тесты клавиатуры выбора игр."""

    def test_games_keyboard_creation(self):
        """Тест создания клавиатуры игр."""
        keyboard = get_games_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_games_keyboard_with_custom_prefix(self):
        """Тест создания клавиатуры с кастомным префиксом."""
        keyboard = get_games_keyboard(callback_prefix="custom")

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_games_keyboard_has_buttons(self):
        """Тест наличия кнопок в клавиатуре игр."""
        keyboard = get_games_keyboard()

        # Должно быть хотя бы несколько кнопок для игр
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(all_buttons) > 0


class TestKeyboardIntegration:
    """Интеграционные тесты клавиатур."""

    def test_all_keyboards_are_valid_telegram_objects(self):
        """Тест что все клавиатуры - валидные объекты Telegram."""
        keyboards = [
            get_main_menu_keyboard(),
            get_settings_keyboard(),
            get_back_to_settings_keyboard(),
            get_games_keyboard(),
        ]

        for keyboard in keyboards:
            assert isinstance(keyboard, InlineKeyboardMarkup)
            assert hasattr(keyboard, "inline_keyboard")

    def test_keyboards_have_callback_data(self):
        """Тест что у кнопок есть callback_data."""
        keyboard = get_main_menu_keyboard()

        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]

        for button in all_buttons:
            # У каждой кнопки должен быть callback_data
            assert hasattr(button, "callback_data")
            assert button.callback_data is not None


class TestKeyboardStructure:
    """Тесты структуры клавиатур."""

    def test_main_menu_has_multiple_rows(self):
        """Тест что основное меню имеет несколько рядов."""
        keyboard = get_main_menu_keyboard()

        # Должно быть больше одного ряда кнопок
        assert len(keyboard.inline_keyboard) >= 2

    def test_settings_keyboard_has_multiple_rows(self):
        """Тест что настройки имеют несколько рядов."""
        keyboard = get_settings_keyboard()

        assert len(keyboard.inline_keyboard) >= 2

    def test_back_keyboard_has_single_row(self):
        """Тест что клавиатура назад имеет один ряд."""
        keyboard = get_back_to_settings_keyboard()

        assert len(keyboard.inline_keyboard) == 1

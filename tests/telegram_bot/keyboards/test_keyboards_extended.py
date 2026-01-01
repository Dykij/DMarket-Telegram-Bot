"""Расширенные тесты для модулей клавиатур Telegram бота.

Этот модуль содержит тесты для:
- arbitrage.py - клавиатуры арбитража
- main.py - главные клавиатуры
- settings.py - клавиатуры настроек
- alerts.py - клавиатуры алертов
- filters.py - клавиатуры фильтров
- utils.py - утилиты клавиатур
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class TestArbitrageKeyboards:
    """Тесты для клавиатур арбитража."""

    def test_get_arbitrage_keyboard_returns_inline_markup(self):
        """Тест создания клавиатуры арбитражного меню."""
        from src.telegram_bot.keyboards.arbitrage import get_arbitrage_keyboard

        keyboard = get_arbitrage_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 4  # Минимум 4 ряда кнопок

    def test_get_arbitrage_keyboard_has_scan_button(self):
        """Тест наличия кнопки сканирования."""
        from src.telegram_bot.keyboards.arbitrage import get_arbitrage_keyboard

        keyboard = get_arbitrage_keyboard()

        # Проверяем, что есть кнопка сканирования
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        scan_button = next(
            (btn for btn in buttons_flat if btn.callback_data == "arb_scan"),
            None,
        )
        assert scan_button is not None
        assert "Сканировать" in scan_button.text

    def test_get_modern_arbitrage_keyboard_structure(self):
        """Тест структуры современной клавиатуры арбитража."""
        from src.telegram_bot.keyboards.arbitrage import get_modern_arbitrage_keyboard

        keyboard = get_modern_arbitrage_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        # Проверяем наличие кнопок быстрого и глубокого скана
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons_flat]
        assert "arb_quick" in callback_datas
        assert "arb_deep" in callback_datas

    def test_get_auto_arbitrage_keyboard_controls(self):
        """Тест кнопок управления авто-арбитражем."""
        from src.telegram_bot.keyboards.arbitrage import get_auto_arbitrage_keyboard

        keyboard = get_auto_arbitrage_keyboard()

        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons_flat]
        # Проверяем наличие кнопок запуска и остановки
        assert "auto_arb_start" in callback_datas
        assert "auto_arb_stop" in callback_datas
        assert "auto_arb_settings" in callback_datas

    def test_create_arbitrage_keyboard_with_options(self):
        """Тест создания клавиатуры с настраиваемыми опциями."""
        from src.telegram_bot.keyboards.arbitrage import create_arbitrage_keyboard

        # С полными опциями
        kb_full = create_arbitrage_keyboard(include_auto=True, include_analysis=True)
        buttons_full = [btn for row in kb_full.inline_keyboard for btn in row]
        callback_datas_full = [btn.callback_data for btn in buttons_full]
        assert "arb_auto" in callback_datas_full
        assert "arb_analysis" in callback_datas_full

        # Без авто-арбитража
        kb_no_auto = create_arbitrage_keyboard(
            include_auto=False, include_analysis=True
        )
        buttons_no_auto = [btn for row in kb_no_auto.inline_keyboard for btn in row]
        callback_datas_no_auto = [btn.callback_data for btn in buttons_no_auto]
        assert "arb_auto" not in callback_datas_no_auto

    def test_create_arbitrage_keyboard_without_analysis(self):
        """Тест создания клавиатуры без анализа."""
        from src.telegram_bot.keyboards.arbitrage import create_arbitrage_keyboard

        kb = create_arbitrage_keyboard(include_auto=True, include_analysis=False)
        buttons = [btn for row in kb.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons]
        assert "arb_analysis" not in callback_datas

    def test_get_back_to_arbitrage_keyboard(self):
        """Тест клавиатуры возврата к арбитражу."""
        from src.telegram_bot.keyboards.arbitrage import get_back_to_arbitrage_keyboard

        keyboard = get_back_to_arbitrage_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].callback_data == "arbitrage"

    def test_get_marketplace_comparison_keyboard(self):
        """Тест клавиатуры сравнения маркетплейсов."""
        from src.telegram_bot.keyboards.arbitrage import (
            get_marketplace_comparison_keyboard,
        )

        keyboard = get_marketplace_comparison_keyboard()

        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons_flat]
        assert "cmp_steam" in callback_datas
        assert "cmp_buff" in callback_datas
        assert "cmp_refresh" in callback_datas

    def test_get_game_selection_keyboard(self):
        """Тест клавиатуры выбора игры."""
        from src.telegram_bot.keyboards.arbitrage import get_game_selection_keyboard

        keyboard = get_game_selection_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        # Должна быть хотя бы одна игра
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        # Проверяем наличие кнопки назад
        back_button = next(
            (btn for btn in buttons_flat if btn.callback_data == "arbitrage"),
            None,
        )
        assert back_button is not None

    def test_create_market_analysis_keyboard(self):
        """Тест клавиатуры анализа рынка."""
        from src.telegram_bot.keyboards.arbitrage import create_market_analysis_keyboard

        keyboard = create_market_analysis_keyboard()

        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons_flat]
        assert "analysis_trends" in callback_datas
        assert "analysis_vol" in callback_datas
        assert "analysis_top" in callback_datas


class TestMainKeyboards:
    """Тесты для главных клавиатур."""

    def test_get_main_menu_keyboard(self):
        """Тест главного меню клавиатуры."""
        from src.telegram_bot.keyboards.main import get_main_menu_keyboard

        keyboard = get_main_menu_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        # Должны быть основные опции
        assert len(buttons_flat) >= 3

    def test_create_main_keyboard(self):
        """Тест создания главной клавиатуры."""
        from src.telegram_bot.keyboards.main import create_main_keyboard

        keyboard = create_main_keyboard()

        # Может быть InlineKeyboardMarkup или ReplyKeyboardMarkup
        assert keyboard is not None

    def test_get_games_keyboard(self):
        """Тест клавиатуры выбора игр."""
        from src.telegram_bot.keyboards.main import get_games_keyboard

        keyboard = get_games_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)


class TestSettingsKeyboards:
    """Тесты для клавиатур настроек."""

    def test_get_settings_keyboard(self):
        """Тест клавиатуры настроек."""
        from src.telegram_bot.keyboards.settings import get_settings_keyboard

        keyboard = get_settings_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_create_settings_keyboard(self):
        """Тест создания клавиатуры настроек."""
        from src.telegram_bot.keyboards.settings import create_settings_keyboard

        keyboard = create_settings_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_language_keyboard(self):
        """Тест клавиатуры выбора языка."""
        from src.telegram_bot.keyboards.settings import get_language_keyboard

        keyboard = get_language_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        # Должны быть языковые опции
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons_flat) >= 2

    def test_get_back_to_settings_keyboard(self):
        """Тест клавиатуры возврата к настройкам."""
        from src.telegram_bot.keyboards.settings import get_back_to_settings_keyboard

        keyboard = get_back_to_settings_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 1

    def test_create_confirm_keyboard(self):
        """Тест клавиатуры подтверждения."""
        from src.telegram_bot.keyboards.settings import create_confirm_keyboard

        keyboard = create_confirm_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons_flat]
        # Должны быть кнопки подтверждения и отмены
        assert any("confirm" in cd or "yes" in cd for cd in callback_datas)

    def test_get_risk_profile_keyboard(self):
        """Тест клавиатуры выбора профиля риска."""
        from src.telegram_bot.keyboards.settings import get_risk_profile_keyboard

        keyboard = get_risk_profile_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)


class TestAlertsKeyboards:
    """Тесты для клавиатур алертов."""

    def test_get_alert_keyboard(self):
        """Тест клавиатуры алертов."""
        from src.telegram_bot.keyboards.alerts import get_alert_keyboard

        keyboard = get_alert_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_alert_type_keyboard(self):
        """Тест клавиатуры выбора типа алерта."""
        from src.telegram_bot.keyboards.alerts import get_alert_type_keyboard

        keyboard = get_alert_type_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_alert_actions_keyboard(self):
        """Тест клавиатуры действий с алертом."""
        from src.telegram_bot.keyboards.alerts import get_alert_actions_keyboard

        keyboard = get_alert_actions_keyboard(alert_id="test_alert_123")

        assert isinstance(keyboard, InlineKeyboardMarkup)
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        # Должна быть кнопка с ID алерта
        assert any(
            "test_alert_123" in (btn.callback_data or "") for btn in buttons_flat
        )

    def test_create_price_alerts_keyboard(self):
        """Тест клавиатуры ценовых алертов."""
        from src.telegram_bot.keyboards.alerts import create_price_alerts_keyboard

        # Передаем пустой список алертов
        keyboard = create_price_alerts_keyboard(alerts=[])

        assert isinstance(keyboard, InlineKeyboardMarkup)


class TestFiltersKeyboards:
    """Тесты для клавиатур фильтров."""

    def test_get_filter_keyboard(self):
        """Тест клавиатуры фильтров."""
        from src.telegram_bot.keyboards.filters import get_filter_keyboard

        keyboard = get_filter_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_price_range_keyboard(self):
        """Тест клавиатуры выбора ценового диапазона."""
        from src.telegram_bot.keyboards.filters import get_price_range_keyboard

        keyboard = get_price_range_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_rarity_keyboard(self):
        """Тест клавиатуры выбора редкости."""
        from src.telegram_bot.keyboards.filters import get_rarity_keyboard

        keyboard = get_rarity_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_csgo_exterior_keyboard(self):
        """Тест клавиатуры выбора состояния CS:GO."""
        from src.telegram_bot.keyboards.filters import get_csgo_exterior_keyboard

        keyboard = get_csgo_exterior_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        # Должны быть опции состояния (FN, MW, FT, WW, BS)
        buttons_flat = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons_flat) >= 3

    def test_get_csgo_weapon_type_keyboard(self):
        """Тест клавиатуры выбора типа оружия CS:GO."""
        from src.telegram_bot.keyboards.filters import get_csgo_weapon_type_keyboard

        keyboard = get_csgo_weapon_type_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)


class TestKeyboardsUtils:
    """Тесты для утилит клавиатур."""

    def test_build_menu(self):
        """Тест построения меню из кнопок."""
        from src.telegram_bot.keyboards.utils import build_menu

        buttons = [
            InlineKeyboardButton(text="Btn1", callback_data="cb1"),
            InlineKeyboardButton(text="Btn2", callback_data="cb2"),
            InlineKeyboardButton(text="Btn3", callback_data="cb3"),
            InlineKeyboardButton(text="Btn4", callback_data="cb4"),
            InlineKeyboardButton(text="Btn5", callback_data="cb5"),
        ]

        # 2 кнопки в ряд
        menu = build_menu(buttons, n_cols=2)
        assert len(menu) == 3  # 2 + 2 + 1
        assert len(menu[0]) == 2
        assert len(menu[1]) == 2
        assert len(menu[2]) == 1

    def test_extract_callback_data_with_prefix(self):
        """Тест извлечения данных из callback с префиксом."""
        from src.telegram_bot.keyboards.utils import extract_callback_data

        # Callback с prefix
        result = extract_callback_data("game_csgo", prefix="game_")
        assert result == "csgo"

    def test_constants_defined(self):
        """Тест что константы определены."""
        from src.telegram_bot.keyboards.utils import (
            CB_BACK,
            CB_CANCEL,
            CB_GAME_PREFIX,
            CB_HELP,
            CB_NEXT_PAGE,
            CB_PREV_PAGE,
            CB_SETTINGS,
        )

        assert CB_BACK is not None
        assert CB_CANCEL is not None
        assert CB_GAME_PREFIX is not None
        assert CB_HELP is not None
        assert CB_NEXT_PAGE is not None
        assert CB_PREV_PAGE is not None
        assert CB_SETTINGS is not None

    def test_force_reply(self):
        """Тест force reply клавиатуры."""
        from src.telegram_bot.keyboards.utils import force_reply

        reply = force_reply()

        # Должен быть ForceReply объект
        assert reply is not None

    def test_remove_keyboard(self):
        """Тест удаления клавиатуры."""
        from src.telegram_bot.keyboards.utils import remove_keyboard

        markup = remove_keyboard()

        # Должен быть ReplyKeyboardRemove
        assert markup is not None


class TestWebAppKeyboards:
    """Тесты для WebApp клавиатур."""

    def test_get_webapp_keyboard_with_params(self):
        """Тест WebApp клавиатуры с параметрами."""
        from src.telegram_bot.keyboards.webapp import get_webapp_keyboard

        keyboard = get_webapp_keyboard(
            title="Test App", webapp_url="https://example.com"
        )

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_webapp_button(self):
        """Тест WebApp кнопки."""
        from src.telegram_bot.keyboards.webapp import get_webapp_button

        button = get_webapp_button(url="https://example.com", text="Open App")

        assert isinstance(button, InlineKeyboardButton)
        assert button.text == "Open App"

    def test_get_dmarket_webapp_keyboard(self):
        """Тест DMarket WebApp клавиатуры."""
        from src.telegram_bot.keyboards.webapp import get_dmarket_webapp_keyboard

        keyboard = get_dmarket_webapp_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_get_combined_web_app_keyboard_with_url(self):
        """Тест комбинированной WebApp клавиатуры с URL."""
        from src.telegram_bot.keyboards.webapp import get_combined_web_app_keyboard

        keyboard = get_combined_web_app_keyboard(webapp_url="https://example.com")

        assert isinstance(keyboard, InlineKeyboardMarkup)

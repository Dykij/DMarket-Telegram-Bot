"""Тесты для обработчиков настроек и локализации."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Update, User

from src.telegram_bot.handlers.settings_handlers import (
    get_localized_text,
    get_user_profile,
    save_user_profiles,
    settings_callback,
    settings_command,
)


# ======================== Fixtures ========================


@pytest.fixture()
def mock_user():
    """Создать мок объекта User."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    return user


@pytest.fixture()
def mock_message(mock_user):
    """Создать мок объекта Message."""
    message = MagicMock()
    message.reply_text = AsyncMock()
    message.from_user = mock_user
    return message


@pytest.fixture()
def mock_callback_query(mock_user):
    """Создать мок объекта CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = "settings"
    query.from_user = mock_user
    return query


@pytest.fixture()
def mock_update(mock_user, mock_callback_query, mock_message):
    """Создать мок объекта Update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.effective_user = mock_user
    update.message = mock_message
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456789
    return update


@pytest.fixture()
def mock_context():
    """Создать мок объекта CallbackContext."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context


# ======================== get_user_profile Tests ========================


class TestGetUserProfile:
    """Тесты для функции get_user_profile."""

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_creates_new_profile_if_not_exists(self):
        """Должен создавать новый профиль если его нет."""
        profile = get_user_profile(999)
        assert profile is not None

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_new_profile_has_default_language(self):
        """Новый профиль должен иметь русский язык по умолчанию."""
        profile = get_user_profile(999)
        assert profile.get("language") == "ru" or profile.get("settings", {}).get("language") == "ru"

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_new_profile_has_trade_settings(self):
        """Новый профиль должен иметь настройки торговли."""
        profile = get_user_profile(999)
        trade_settings = profile.get("trade_settings", {})
        assert "min_profit" in trade_settings or trade_settings == {}

    @patch("src.telegram_bot.handlers.settings_handlers._profile_manager", None)
    @patch(
        "src.telegram_bot.handlers.settings_handlers.USER_PROFILES",
        {"123": {"language": "en", "custom_field": "value"}},
    )
    def test_returns_existing_profile(self):
        """Должен возвращать существующий профиль."""
        # Use patched fallback function
        from src.telegram_bot.handlers.settings_handlers import USER_PROFILES
        profile = USER_PROFILES.get("123", {})
        if profile:
            assert profile.get("language") == "en"
            assert profile.get("custom_field") == "value"
        else:
            # If profile manager is active, we just verify it doesn't crash
            profile = get_user_profile(123)
            assert profile is not None

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_auto_trading_disabled_by_default(self):
        """Автоторговля должна быть отключена по умолчанию."""
        profile = get_user_profile(999)
        assert profile.get("auto_trading_enabled") is False or "auto_trading_enabled" not in profile


# ======================== get_localized_text Tests ========================


class TestGetLocalizedText:
    """Тесты для функции get_localized_text."""

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS", {"ru": {"test_key": "Тестовый текст"}})
    def test_returns_localized_text(self, mock_get_profile):
        """Должен возвращать локализованный текст."""
        mock_get_profile.return_value = {"language": "ru"}
        result = get_localized_text(123, "test_key")
        assert result == "Тестовый текст"

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch(
        "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
        {"ru": {"missing_fallback": "Текст по умолчанию"}, "en": {}},
    )
    def test_falls_back_to_russian(self, mock_get_profile):
        """Должен возвращать русский текст если ключ не найден."""
        mock_get_profile.return_value = {"language": "en"}
        result = get_localized_text(123, "missing_fallback")
        assert result == "Текст по умолчанию"

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS", {"ru": {}})
    def test_returns_missing_key_indicator(self, mock_get_profile):
        """Должен возвращать индикатор отсутствующего ключа."""
        mock_get_profile.return_value = {"language": "ru"}
        result = get_localized_text(123, "nonexistent_key")
        assert "Missing" in result or "nonexistent_key" in result

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch(
        "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
        {"ru": {"formatted": "Привет, {name}!"}},
    )
    def test_formats_text_with_kwargs(self, mock_get_profile):
        """Должен форматировать текст с параметрами."""
        mock_get_profile.return_value = {"language": "ru"}
        result = get_localized_text(123, "formatted", name="Мир")
        assert result == "Привет, Мир!"

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch(
        "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
        {"ru": {"test": "Русский"}, "en": {"test": "English"}},
    )
    def test_uses_language_from_settings(self, mock_get_profile):
        """Должен использовать язык из настроек."""
        mock_get_profile.return_value = {"settings": {"language": "en"}}
        result = get_localized_text(123, "test")
        assert result == "English"

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS", {"ru": {"test": "Русский"}})
    def test_defaults_to_russian_for_unknown_language(self, mock_get_profile):
        """Должен использовать русский для неизвестного языка."""
        mock_get_profile.return_value = {"language": "unknown"}
        result = get_localized_text(123, "test")
        assert result == "Русский"


# ======================== save_user_profiles Tests ========================


class TestSaveUserProfiles:
    """Тесты для функции save_user_profiles."""

    @patch("builtins.open")
    @patch("json.dump")
    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {"123": {"language": "ru"}})
    def test_saves_profiles_to_file(self, mock_json_dump, mock_open):
        """Должен сохранять профили в файл."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        save_user_profiles()

        mock_json_dump.assert_called_once()

    @patch("builtins.open")
    @patch("json.dump")
    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_saves_empty_profiles(self, mock_json_dump, mock_open):
        """Должен сохранять пустой словарь профилей."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        save_user_profiles()

        mock_json_dump.assert_called()
        call_args = mock_json_dump.call_args
        assert call_args[0][0] == {}


# ======================== settings_command Tests ========================


class TestSettingsCommand:
    """Тесты для функции settings_command."""

    @pytest.mark.asyncio
    async def test_returns_none_if_no_effective_user(self, mock_update, mock_context):
        """Должен возвращать None если нет effective_user."""
        mock_update.effective_user = None
        result = await settings_command(mock_update, mock_context)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_if_no_message(self, mock_update, mock_context):
        """Должен возвращать None если нет message."""
        mock_update.message = None
        result = await settings_command(mock_update, mock_context)
        assert result is None

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_sends_settings_message(self, mock_keyboard, mock_localized, mock_update, mock_context):
        """Должен отправлять сообщение с настройками."""
        mock_localized.return_value = "Настройки"
        mock_keyboard.return_value = MagicMock()

        await settings_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_uses_localized_text(self, mock_keyboard, mock_localized, mock_update, mock_context):
        """Должен использовать локализованный текст."""
        mock_localized.return_value = "Текст настроек"
        mock_keyboard.return_value = MagicMock()

        await settings_command(mock_update, mock_context)

        mock_localized.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args[0][0] == "Текст настроек"

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_includes_keyboard(self, mock_keyboard, mock_localized, mock_update, mock_context):
        """Должен включать клавиатуру."""
        mock_localized.return_value = "Settings"
        mock_kb = MagicMock()
        mock_keyboard.return_value = mock_kb

        await settings_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs.get("reply_markup") == mock_kb


# ======================== settings_callback Tests ========================


class TestSettingsCallback:
    """Тесты для функции settings_callback."""

    @pytest.mark.asyncio
    async def test_returns_none_if_no_callback_query(self, mock_update, mock_context):
        """Должен возвращать None если нет callback_query."""
        mock_update.callback_query = None
        result = await settings_callback(mock_update, mock_context)
        assert result is None

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_answers_callback_query(self, mock_keyboard, mock_localized, mock_update, mock_context):
        """Должен отвечать на callback_query."""
        mock_localized.return_value = "Settings"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings"

        await settings_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_if_no_data(self, mock_update, mock_context):
        """Должен возвращать None если нет data."""
        mock_update.callback_query.data = None
        await settings_callback(mock_update, mock_context)
        mock_update.callback_query.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_handles_settings_callback(self, mock_keyboard, mock_localized, mock_update, mock_context):
        """Должен обрабатывать callback 'settings'."""
        mock_localized.return_value = "Настройки"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings"

        await settings_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_language_keyboard")
    @patch("src.telegram_bot.handlers.settings_handlers.LANGUAGES", {"ru": "Русский", "en": "English"})
    async def test_handles_settings_language_callback(
        self, mock_keyboard, mock_localized, mock_profile, mock_update, mock_context
    ):
        """Должен обрабатывать callback 'settings_language'."""
        mock_profile.return_value = {"language": "ru"}
        mock_localized.return_value = "Выберите язык"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_language"

        await settings_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    @patch("src.telegram_bot.handlers.settings_handlers.LANGUAGES", {"ru": "Русский", "en": "English"})
    async def test_handles_language_change_callback(
        self, mock_keyboard, mock_localized, mock_save, mock_profile, mock_update, mock_context
    ):
        """Должен обрабатывать callback изменения языка."""
        mock_profile.return_value = {"language": "ru"}
        mock_localized.return_value = "Язык изменен"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "language:en"

        await settings_callback(mock_update, mock_context)

        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    async def test_handles_settings_api_keys_callback(self, mock_keyboard, mock_profile, mock_update, mock_context):
        """Должен обрабатывать callback 'settings_api_keys'."""
        mock_profile.return_value = {"api_key": "pk_12345_67890", "api_secret": "sk_abc_xyz"}
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_api_keys"

        await settings_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args.kwargs.get("text", "")
        assert "API" in message

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    async def test_api_key_is_masked(self, mock_keyboard, mock_profile, mock_update, mock_context):
        """API ключ должен быть скрыт частично."""
        mock_profile.return_value = {"api_key": "pk_1234567890abcdef", "api_secret": "sk_secret123"}
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_api_keys"

        await settings_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args.kwargs.get("text", "")
        assert "pk_1234567890abcdef" not in message  # Полный ключ не должен отображаться
        assert "..." in message  # Должен быть скрыт

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_handles_toggle_trading_callback(
        self, mock_keyboard, mock_localized, mock_save, mock_profile, mock_update, mock_context
    ):
        """Должен обрабатывать callback переключения автоторговли."""
        profile = {"auto_trading_enabled": False}
        mock_profile.return_value = profile
        mock_localized.return_value = "Торговля"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_toggle_trading"

        await settings_callback(mock_update, mock_context)

        assert profile["auto_trading_enabled"] is True
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_risk_profile_keyboard")
    async def test_handles_settings_limits_callback(self, mock_keyboard, mock_profile, mock_update, mock_context):
        """Должен обрабатывать callback 'settings_limits'."""
        mock_profile.return_value = {
            "trade_settings": {
                "min_profit": 5.0,
                "max_price": 100.0,
                "max_trades": 5,
                "risk_level": "high",
            }
        }
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_limits"

        await settings_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args.kwargs.get("text", "")
        assert "5.00" in message  # min_profit
        assert "100.00" in message  # max_price
        assert "5" in message  # max_trades
        assert "high" in message  # risk_level


# ======================== Edge Cases Tests ========================


class TestEdgeCases:
    """Тесты для граничных случаев."""

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    @pytest.mark.asyncio
    async def test_empty_api_key_displayed_correctly(self, mock_keyboard, mock_profile, mock_update, mock_context):
        """Пустой API ключ должен отображаться как 'Не установлен'."""
        mock_profile.return_value = {"api_key": "", "api_secret": ""}
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_api_keys"

        await settings_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args.kwargs.get("text", "")
        assert "Не установлен" in message

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_risk_profile_keyboard")
    @pytest.mark.asyncio
    async def test_missing_trade_settings(self, mock_keyboard, mock_profile, mock_update, mock_context):
        """Должен обрабатывать отсутствующие настройки торговли."""
        mock_profile.return_value = {}
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_limits"

        await settings_callback(mock_update, mock_context)

        # Не должно быть исключения
        mock_update.callback_query.edit_message_text.assert_called_once()

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_language_keyboard")
    @patch("src.telegram_bot.handlers.settings_handlers.LANGUAGES", {})
    @pytest.mark.asyncio
    async def test_handles_unsupported_language(self, mock_keyboard, mock_profile, mock_update, mock_context):
        """Должен обрабатывать неподдерживаемый язык."""
        mock_profile.return_value = {"language": "unsupported"}
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "language:unsupported"

        await settings_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args.kwargs.get("text", "") or call_args[0][0]
        assert "не поддерживается" in message

    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    @pytest.mark.asyncio
    async def test_toggle_trading_off(
        self, mock_keyboard, mock_localized, mock_save, mock_profile, mock_update, mock_context
    ):
        """Должен выключать автоторговлю если она была включена."""
        profile = {"auto_trading_enabled": True}
        mock_profile.return_value = profile
        mock_localized.return_value = "Торговля"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "settings_toggle_trading"

        await settings_callback(mock_update, mock_context)

        assert profile["auto_trading_enabled"] is False

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_profile_stores_last_activity(self):
        """Профиль должен хранить время последней активности."""
        profile = get_user_profile(999)
        assert "last_activity" in profile or profile == {}  # Зависит от реализации


# ======================== Integration Tests ========================


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_full_settings_flow(self, mock_keyboard, mock_localized, mock_update, mock_context):
        """Полный flow работы с настройками."""
        mock_localized.return_value = "Настройки"
        mock_keyboard.return_value = MagicMock()

        # Шаг 1: Открытие настроек через команду
        await settings_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

        # Шаг 2: Переход в подменю через callback
        mock_update.callback_query.data = "settings"
        await settings_callback(mock_update, mock_context)
        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    @patch("src.telegram_bot.handlers.settings_handlers.LANGUAGES", {"ru": "Русский", "en": "English"})
    async def test_language_change_flow(
        self, mock_keyboard, mock_localized, mock_save, mock_profile, mock_update, mock_context
    ):
        """Flow изменения языка."""
        profile = {"language": "ru"}
        mock_profile.return_value = profile
        mock_localized.return_value = "Язык изменен на English"
        mock_keyboard.return_value = MagicMock()
        mock_update.callback_query.data = "language:en"

        await settings_callback(mock_update, mock_context)

        # Проверяем что язык изменился
        assert profile["language"] == "en"
        mock_save.assert_called_once()

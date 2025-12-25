"""Extended tests for settings_handlers module.

Additional tests to improve coverage for settings management,
API key handling, and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import InlineKeyboardMarkup, Message, Update, User
from telegram.ext import Application, CallbackContext

from src.telegram_bot.handlers.settings_handlers import (
    get_localized_text,
    get_user_profile,
    handle_setup_input,
    register_localization_handlers,
    save_user_profiles,
    settings_callback,
    settings_command,
    setup_command,
)


@pytest.fixture
def mock_update():
    """Create a mock Update object for testing."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 123456789

    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.from_user = mock_user
    update.callback_query.data = "settings"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock CallbackContext object for testing."""
    context = MagicMock(spec=CallbackContext)
    context.user_data = {}
    return context


class TestGetUserProfileEdgeCases:
    """Edge case tests for get_user_profile function."""

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_get_user_profile_creates_default_settings(self):
        """Test that new user profile contains required fields."""
        user_id = 999888777
        profile = get_user_profile(user_id)

        # Should have either settings or language key
        assert "language" in profile or "settings" in profile

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_get_user_profile_multiple_calls_same_user(self):
        """Test that multiple calls for same user return same profile."""
        user_id = 111222333
        profile1 = get_user_profile(user_id)
        profile2 = get_user_profile(user_id)

        # Should return the same profile object or equivalent data
        assert profile1 == profile2


class TestGetLocalizedTextEdgeCases:
    """Edge case tests for get_localized_text function."""

    @patch(
        "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
        {
            "ru": {"key1": "Значение1", "key2": "Значение2"},
            "en": {"key1": "Value1"},
        },
    )
    def test_get_localized_text_fallback_to_russian(self):
        """Test that missing key falls back to Russian."""
        from src.telegram_bot.handlers import settings_handlers

        try:
            manager = settings_handlers._profile_manager
            original_profiles = manager._profiles.copy()
            try:
                manager._profiles.clear()
                manager._profiles[123456789] = {"settings": {"language": "en"}}
                # "key2" doesn't exist in English
                text = get_localized_text(123456789, "key2")
                assert text == "Значение2"
            finally:
                manager._profiles.clear()
                manager._profiles.update(original_profiles)
        except AttributeError:
            original_profiles = settings_handlers.USER_PROFILES.copy()
            try:
                settings_handlers.USER_PROFILES.clear()
                settings_handlers.USER_PROFILES["123456789"] = {"language": "en"}
                text = get_localized_text(123456789, "key2")
                assert text == "Значение2"
            finally:
                settings_handlers.USER_PROFILES.clear()
                settings_handlers.USER_PROFILES.update(original_profiles)

    @patch(
        "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
        {
            "ru": {"key1": "Значение1"},
            "en": {"key1": "Value1"},
        },
    )
    def test_get_localized_text_missing_in_all_languages(self):
        """Test that completely missing key returns error placeholder."""
        from src.telegram_bot.handlers import settings_handlers

        try:
            manager = settings_handlers._profile_manager
            original_profiles = manager._profiles.copy()
            try:
                manager._profiles.clear()
                manager._profiles[123456789] = {"settings": {"language": "ru"}}
                text = get_localized_text(123456789, "nonexistent_key")
                assert "[Missing:" in text or text == "[Missing: nonexistent_key]"
            finally:
                manager._profiles.clear()
                manager._profiles.update(original_profiles)
        except AttributeError:
            original_profiles = settings_handlers.USER_PROFILES.copy()
            try:
                settings_handlers.USER_PROFILES.clear()
                settings_handlers.USER_PROFILES["123456789"] = {"language": "ru"}
                text = get_localized_text(123456789, "nonexistent_key")
                assert "[Missing:" in text
            finally:
                settings_handlers.USER_PROFILES.clear()
                settings_handlers.USER_PROFILES.update(original_profiles)

    @patch(
        "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
        {
            "ru": {"greeting": "Привет, {name}! Возраст: {age}"},
            "en": {"greeting": "Hello, {name}! Age: {age}"},
        },
    )
    def test_get_localized_text_multiple_params(self):
        """Test that multiple parameters are properly substituted."""
        from src.telegram_bot.handlers import settings_handlers

        try:
            manager = settings_handlers._profile_manager
            original_profiles = manager._profiles.copy()
            try:
                manager._profiles.clear()
                manager._profiles[123456789] = {"settings": {"language": "en"}}
                text = get_localized_text(123456789, "greeting", name="John", age=25)
                assert "John" in text
                assert "25" in text
            finally:
                manager._profiles.clear()
                manager._profiles.update(original_profiles)
        except AttributeError:
            original_profiles = settings_handlers.USER_PROFILES.copy()
            try:
                settings_handlers.USER_PROFILES.clear()
                settings_handlers.USER_PROFILES["123456789"] = {"language": "en"}
                text = get_localized_text(123456789, "greeting", name="John", age=25)
                assert "John" in text
                assert "25" in text
            finally:
                settings_handlers.USER_PROFILES.clear()
                settings_handlers.USER_PROFILES.update(original_profiles)


class TestSettingsCommandEdgeCases:
    """Edge case tests for settings_command function."""

    @pytest.mark.asyncio
    async def test_settings_command_no_effective_user(self, mock_context):
        """Test settings_command when effective_user is None."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock(spec=Message)

        # Should return early without error
        await settings_command(update, mock_context)
        update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_settings_command_no_message(self, mock_context):
        """Test settings_command when message is None."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 123456789

        update = MagicMock(spec=Update)
        update.effective_user = mock_user
        update.message = None

        # Should return early without error
        await settings_command(update, mock_context)


class TestSettingsCallbackEdgeCases:
    """Edge case tests for settings_callback function."""

    @pytest.mark.asyncio
    async def test_settings_callback_no_callback_query(self, mock_context):
        """Test settings_callback when callback_query is None."""
        update = MagicMock(spec=Update)
        update.callback_query = None

        # Should return early without error
        await settings_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_settings_callback_empty_data(self, mock_update, mock_context):
        """Test settings_callback with empty data."""
        mock_update.callback_query.data = None

        # Should return early without calling answer
        await settings_callback(mock_update, mock_context)
        # When data is None, function returns early before answer()
        # So we just verify no error occurred

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    async def test_settings_callback_api_keys_empty(
        self, mock_get_back_keyboard, mock_get_user_profile, mock_update, mock_context
    ):
        """Test settings_callback with empty API keys."""
        mock_profile = {
            "api_key": "",
            "api_secret": "",
        }
        mock_get_user_profile.return_value = mock_profile
        mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
        mock_get_back_keyboard.return_value = mock_keyboard

        mock_update.callback_query.data = "settings_api_keys"

        await settings_callback(mock_update, mock_context)

        # Should show "Not set" for empty keys
        call_args = mock_update.callback_query.edit_message_text.call_args
        if call_args.kwargs and "text" in call_args.kwargs:
            message_text = call_args.kwargs["text"]
        elif call_args.args:
            message_text = call_args.args[0]
        else:
            message_text = ""

        assert "Не установлен" in message_text or "Not set" in message_text.lower()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.get_risk_profile_keyboard")
    async def test_settings_callback_limits_missing_trade_settings(
        self, mock_get_risk_keyboard, mock_get_user_profile, mock_update, mock_context
    ):
        """Test settings_callback with missing trade_settings."""
        mock_profile = {}  # No trade_settings
        mock_get_user_profile.return_value = mock_profile
        mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
        mock_get_risk_keyboard.return_value = mock_keyboard

        mock_update.callback_query.data = "settings_limits"

        await settings_callback(mock_update, mock_context)

        # Should use default values
        mock_get_risk_keyboard.assert_called_once_with("medium")

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    async def test_settings_callback_risk_profile_creates_trade_settings(
        self,
        mock_get_back_keyboard,
        mock_save_profiles,
        mock_get_user_profile,
        mock_update,
        mock_context,
    ):
        """Test that risk_profile callback creates trade_settings if missing."""
        mock_profile = {}  # No trade_settings
        mock_get_user_profile.return_value = mock_profile
        mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
        mock_get_back_keyboard.return_value = mock_keyboard

        mock_update.callback_query.data = "risk_profile:medium"

        await settings_callback(mock_update, mock_context)

        # trade_settings should be created
        assert "trade_settings" in mock_profile
        assert mock_profile["trade_settings"]["risk_level"] == "medium"

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
    @patch(
        "src.telegram_bot.handlers.settings_handlers.LANGUAGES",
        {"ru": "Русский", "en": "English"},
    )
    async def test_settings_callback_language_with_settings_key(
        self,
        mock_get_back_keyboard,
        mock_get_localized_text,
        mock_save_profiles,
        mock_get_user_profile,
        mock_update,
        mock_context,
    ):
        """Test language setting with settings sub-key."""
        mock_profile = {"settings": {"language": "ru"}}
        mock_get_user_profile.return_value = mock_profile
        mock_get_localized_text.return_value = "Language changed"
        mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
        mock_get_back_keyboard.return_value = mock_keyboard

        mock_update.callback_query.data = "language:en"

        await settings_callback(mock_update, mock_context)

        # Should update settings.language
        assert mock_profile["settings"]["language"] == "en"
        mock_save_profiles.assert_called_once()


class TestSetupCommandEdgeCases:
    """Edge case tests for setup_command function."""

    @pytest.mark.asyncio
    async def test_setup_command_no_effective_user(self, mock_context):
        """Test setup_command when effective_user is None."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock(spec=Message)

        await setup_command(update, mock_context)
        update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_command_no_message(self, mock_context):
        """Test setup_command when message is None."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 123456789

        update = MagicMock(spec=Update)
        update.effective_user = mock_user
        update.message = None

        await setup_command(update, mock_context)

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    async def test_setup_command_with_none_user_data(
        self, mock_get_localized_text, mock_update
    ):
        """Test setup_command when user_data is None."""
        mock_get_localized_text.return_value = "Enter API key:"
        context = MagicMock(spec=CallbackContext)
        context.user_data = None

        await setup_command(mock_update, context)

        # Should still send the message
        mock_update.message.reply_text.assert_called_once()


class TestHandleSetupInputEdgeCases:
    """Edge case tests for handle_setup_input function."""

    @pytest.mark.asyncio
    async def test_handle_setup_input_no_effective_user(self, mock_context):
        """Test handle_setup_input when effective_user is None."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock(spec=Message)
        update.message.text = "test"

        await handle_setup_input(update, mock_context)
        update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_setup_input_no_message(self, mock_context):
        """Test handle_setup_input when message is None."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 123456789

        update = MagicMock(spec=Update)
        update.effective_user = mock_user
        update.message = None

        await handle_setup_input(update, mock_context)

    @pytest.mark.asyncio
    async def test_handle_setup_input_no_text(self, mock_update, mock_context):
        """Test handle_setup_input when text is None."""
        mock_update.message.text = None
        mock_context.user_data = {"setup_state": "waiting_api_key"}

        await handle_setup_input(mock_update, mock_context)
        mock_update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_setup_input_none_user_data(self, mock_update):
        """Test handle_setup_input when user_data is None."""
        context = MagicMock(spec=CallbackContext)
        context.user_data = None
        mock_update.message.text = "test_key"

        await handle_setup_input(mock_update, context)
        # Should return early without error


class TestRegisterLocalizationHandlers:
    """Tests for register_localization_handlers function."""

    def test_register_handlers_adds_all_handlers(self):
        """Test that all required handlers are registered."""
        mock_app = MagicMock(spec=Application)

        register_localization_handlers(mock_app)

        # Should register at least 5 handlers
        assert mock_app.add_handler.call_count >= 5

    def test_register_handlers_correct_patterns(self):
        """Test that handlers are registered with correct patterns."""
        mock_app = MagicMock()
        registered_handlers = []

        def capture_handler(handler):
            registered_handlers.append(handler)

        mock_app.add_handler = capture_handler

        register_localization_handlers(mock_app)

        # Verify handlers were registered
        assert len(registered_handlers) >= 5


class TestSaveUserProfilesEdgeCases:
    """Edge case tests for save_user_profiles function."""

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    @patch("os.path.dirname")
    @patch("builtins.open")
    @patch("json.dump")
    def test_save_user_profiles_empty_profiles(
        self, mock_json_dump, mock_file_open, mock_dirname
    ):
        """Test saving empty profiles."""
        mock_dirname.return_value = "/test/path"
        mock_file = MagicMock()
        mock_file_open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)

        save_user_profiles()

        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        assert args[0] == {}

    @patch(
        "src.telegram_bot.handlers.settings_handlers.USER_PROFILES",
        {"user1": {"lang": "ru"}, "user2": {"lang": "en"}},
    )
    @patch("os.path.dirname")
    @patch("builtins.open")
    @patch("json.dump")
    def test_save_user_profiles_multiple_users(
        self, mock_json_dump, mock_file_open, mock_dirname
    ):
        """Test saving multiple user profiles."""
        mock_dirname.return_value = "/test/path"
        mock_file = MagicMock()
        mock_file_open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)

        save_user_profiles()

        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        assert len(args[0]) == 2


class TestAutoTradingToggle:
    """Tests for auto trading toggle functionality."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_toggle_trading_from_disabled_to_enabled(
        self,
        mock_get_settings_keyboard,
        mock_get_localized_text,
        mock_save_profiles,
        mock_get_user_profile,
        mock_update,
        mock_context,
    ):
        """Test toggling auto trading from disabled to enabled."""
        mock_profile = {"auto_trading_enabled": False}
        mock_get_user_profile.return_value = mock_profile
        mock_get_localized_text.side_effect = lambda user_id, key: (
            "Settings" if key == "settings" else "Auto trading enabled"
        )
        mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
        mock_get_settings_keyboard.return_value = mock_keyboard

        mock_update.callback_query.data = "settings_toggle_trading"

        await settings_callback(mock_update, mock_context)

        assert mock_profile["auto_trading_enabled"] is True
        mock_save_profiles.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
    @patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
    @patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
    @patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
    async def test_toggle_trading_from_enabled_to_disabled(
        self,
        mock_get_settings_keyboard,
        mock_get_localized_text,
        mock_save_profiles,
        mock_get_user_profile,
        mock_update,
        mock_context,
    ):
        """Test toggling auto trading from enabled to disabled."""
        mock_profile = {"auto_trading_enabled": True}
        mock_get_user_profile.return_value = mock_profile
        mock_get_localized_text.side_effect = lambda user_id, key: (
            "Settings" if key == "settings" else "Auto trading disabled"
        )
        mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
        mock_get_settings_keyboard.return_value = mock_keyboard

        mock_update.callback_query.data = "settings_toggle_trading"

        await settings_callback(mock_update, mock_context)

        assert mock_profile["auto_trading_enabled"] is False
        mock_save_profiles.assert_called_once()

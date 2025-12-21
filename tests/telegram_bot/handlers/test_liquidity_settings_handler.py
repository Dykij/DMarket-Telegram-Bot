"""Tests for liquidity_settings_handler module.

Tests cover:
- DEFAULT_LIQUIDITY_SETTINGS constant
- get_liquidity_settings function
- update_liquidity_settings function
- get_liquidity_settings_keyboard function
- liquidity_settings_command
- toggle_liquidity_filter
- reset_liquidity_settings
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestDefaultSettings:
    """Tests for DEFAULT_LIQUIDITY_SETTINGS constant."""

    def test_default_settings_structure(self):
        """Test DEFAULT_LIQUIDITY_SETTINGS has correct structure."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            DEFAULT_LIQUIDITY_SETTINGS,
        )

        assert "enabled" in DEFAULT_LIQUIDITY_SETTINGS
        assert "min_liquidity_score" in DEFAULT_LIQUIDITY_SETTINGS
        assert "min_sales_per_week" in DEFAULT_LIQUIDITY_SETTINGS
        assert "max_time_to_sell_days" in DEFAULT_LIQUIDITY_SETTINGS

    def test_default_settings_values(self):
        """Test DEFAULT_LIQUIDITY_SETTINGS has expected values."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            DEFAULT_LIQUIDITY_SETTINGS,
        )

        assert DEFAULT_LIQUIDITY_SETTINGS["enabled"] is True
        assert DEFAULT_LIQUIDITY_SETTINGS["min_liquidity_score"] == 60
        assert DEFAULT_LIQUIDITY_SETTINGS["min_sales_per_week"] == 5
        assert DEFAULT_LIQUIDITY_SETTINGS["max_time_to_sell_days"] == 7


class TestGetLiquiditySettings:
    """Tests for get_liquidity_settings function."""

    @patch("src.telegram_bot.handlers.liquidity_settings_handler.profile_manager")
    def test_get_settings_with_existing_profile(self, mock_profile_manager):
        """Test get_liquidity_settings with existing profile."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            get_liquidity_settings,
        )

        mock_profile_manager.get_profile.return_value = {
            "liquidity_settings": {
                "enabled": False,
                "min_liquidity_score": 80,
                "min_sales_per_week": 10,
                "max_time_to_sell_days": 3,
            }
        }

        settings = get_liquidity_settings(12345)

        assert settings["enabled"] is False
        assert settings["min_liquidity_score"] == 80
        mock_profile_manager.update_profile.assert_not_called()

    @patch("src.telegram_bot.handlers.liquidity_settings_handler.profile_manager")
    def test_get_settings_without_existing_profile(self, mock_profile_manager):
        """Test get_liquidity_settings creates default settings."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            get_liquidity_settings,
            DEFAULT_LIQUIDITY_SETTINGS,
        )

        mock_profile = {}
        mock_profile_manager.get_profile.return_value = mock_profile

        settings = get_liquidity_settings(12345)

        # Should create default settings
        assert "liquidity_settings" in mock_profile
        assert settings["enabled"] == DEFAULT_LIQUIDITY_SETTINGS["enabled"]
        mock_profile_manager.update_profile.assert_called_once()


class TestUpdateLiquiditySettings:
    """Tests for update_liquidity_settings function."""

    @patch("src.telegram_bot.handlers.liquidity_settings_handler.profile_manager")
    def test_update_settings_with_existing_profile(self, mock_profile_manager):
        """Test update_liquidity_settings with existing profile."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            update_liquidity_settings,
        )

        mock_profile_manager.get_profile.return_value = {
            "liquidity_settings": {
                "enabled": True,
                "min_liquidity_score": 60,
                "min_sales_per_week": 5,
                "max_time_to_sell_days": 7,
            }
        }

        update_liquidity_settings(12345, {"min_liquidity_score": 75})

        mock_profile_manager.update_profile.assert_called_once()
        call_args = mock_profile_manager.update_profile.call_args
        assert call_args[0][1]["liquidity_settings"]["min_liquidity_score"] == 75

    @patch("src.telegram_bot.handlers.liquidity_settings_handler.profile_manager")
    def test_update_settings_creates_default_if_missing(self, mock_profile_manager):
        """Test update_liquidity_settings creates default settings if missing."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            update_liquidity_settings,
        )

        mock_profile = {}
        mock_profile_manager.get_profile.return_value = mock_profile

        update_liquidity_settings(12345, {"enabled": False})

        # Should have created default settings first
        assert "liquidity_settings" in mock_profile
        mock_profile_manager.update_profile.assert_called_once()

    @patch("src.telegram_bot.handlers.liquidity_settings_handler.profile_manager")
    def test_update_multiple_settings(self, mock_profile_manager):
        """Test updating multiple settings at once."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            update_liquidity_settings,
        )

        mock_profile_manager.get_profile.return_value = {
            "liquidity_settings": {
                "enabled": True,
                "min_liquidity_score": 60,
                "min_sales_per_week": 5,
                "max_time_to_sell_days": 7,
            }
        }

        update_liquidity_settings(12345, {
            "min_liquidity_score": 80,
            "min_sales_per_week": 15,
        })

        call_args = mock_profile_manager.update_profile.call_args
        settings = call_args[0][1]["liquidity_settings"]
        assert settings["min_liquidity_score"] == 80
        assert settings["min_sales_per_week"] == 15


class TestGetLiquiditySettingsKeyboard:
    """Tests for get_liquidity_settings_keyboard function."""

    def test_keyboard_structure(self):
        """Test keyboard has correct structure."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            get_liquidity_settings_keyboard,
        )
        from telegram import InlineKeyboardMarkup

        keyboard = get_liquidity_settings_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 6  # At least 6 rows

    def test_keyboard_buttons(self):
        """Test keyboard has expected buttons."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            get_liquidity_settings_keyboard,
        )

        keyboard = get_liquidity_settings_keyboard()

        # Flatten to get all buttons
        all_buttons = []
        for row in keyboard.inline_keyboard:
            all_buttons.extend(row)

        # Check callback data
        callback_data_set = {btn.callback_data for btn in all_buttons}

        assert "liquidity_set_min_score" in callback_data_set
        assert "liquidity_set_min_sales" in callback_data_set
        assert "liquidity_set_max_time" in callback_data_set
        assert "liquidity_toggle" in callback_data_set
        assert "liquidity_reset" in callback_data_set
        assert "back_to_settings" in callback_data_set


class TestLiquiditySettingsCommand:
    """Tests for liquidity_settings_command function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    async def test_command_no_user(self, mock_get_settings):
        """Test command with no effective_user."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            liquidity_settings_command,
        )

        update = MagicMock()
        update.effective_user = None
        context = MagicMock()

        await liquidity_settings_command(update, context)

        mock_get_settings.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    async def test_command_no_message(self, mock_get_settings):
        """Test command with no message."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            liquidity_settings_command,
        )

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = None
        context = MagicMock()

        await liquidity_settings_command(update, context)

        mock_get_settings.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings_keyboard")
    async def test_command_enabled_filter(self, mock_keyboard, mock_get_settings):
        """Test command with enabled filter."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            liquidity_settings_command,
        )

        mock_get_settings.return_value = {
            "enabled": True,
            "min_liquidity_score": 60,
            "min_sales_per_week": 5,
            "max_time_to_sell_days": 7,
        }
        mock_keyboard.return_value = MagicMock()

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        context = MagicMock()

        await liquidity_settings_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        text = call_args[1].get("text", call_args[0][0])
        assert "✅" in text  # Enabled status
        assert "60" in text  # min_liquidity_score

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings_keyboard")
    async def test_command_disabled_filter(self, mock_keyboard, mock_get_settings):
        """Test command with disabled filter."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            liquidity_settings_command,
        )

        mock_get_settings.return_value = {
            "enabled": False,
            "min_liquidity_score": 60,
            "min_sales_per_week": 5,
            "max_time_to_sell_days": 7,
        }
        mock_keyboard.return_value = MagicMock()

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        context = MagicMock()

        await liquidity_settings_command(update, context)

        call_args = update.message.reply_text.call_args
        text = call_args[1].get("text", call_args[0][0])
        assert "❌" in text  # Disabled status


class TestToggleLiquidityFilter:
    """Tests for toggle_liquidity_filter function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    async def test_toggle_no_user(self, mock_update, mock_get):
        """Test toggle with no effective_user."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            toggle_liquidity_filter,
        )

        update = MagicMock()
        update.effective_user = None
        context = MagicMock()

        await toggle_liquidity_filter(update, context)

        mock_get.assert_not_called()
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    async def test_toggle_no_callback(self, mock_update, mock_get):
        """Test toggle with no callback_query."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            toggle_liquidity_filter,
        )

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.callback_query = None
        context = MagicMock()

        await toggle_liquidity_filter(update, context)

        mock_get.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    async def test_toggle_enable_to_disable(self, mock_update, mock_get):
        """Test toggle from enabled to disabled."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            toggle_liquidity_filter,
        )

        mock_get.return_value = {
            "enabled": True,
            "min_liquidity_score": 60,
            "min_sales_per_week": 5,
            "max_time_to_sell_days": 7,
        }

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.callback_query = AsyncMock()
        update.callback_query.message = AsyncMock()
        context = MagicMock()

        await toggle_liquidity_filter(update, context)

        mock_update.assert_called_once_with(12345, {"enabled": False})
        update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    async def test_toggle_disable_to_enable(self, mock_update, mock_get):
        """Test toggle from disabled to enabled."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            toggle_liquidity_filter,
        )

        mock_get.return_value = {
            "enabled": False,
            "min_liquidity_score": 60,
            "min_sales_per_week": 5,
            "max_time_to_sell_days": 7,
        }

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.callback_query = AsyncMock()
        update.callback_query.message = AsyncMock()
        context = MagicMock()

        await toggle_liquidity_filter(update, context)

        mock_update.assert_called_once_with(12345, {"enabled": True})


class TestResetLiquiditySettings:
    """Tests for reset_liquidity_settings function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    async def test_reset_no_user(self, mock_update):
        """Test reset with no effective_user."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            reset_liquidity_settings,
        )

        update = MagicMock()
        update.effective_user = None
        context = MagicMock()

        await reset_liquidity_settings(update, context)

        mock_update.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    async def test_reset_no_callback(self, mock_update):
        """Test reset with no callback_query."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            reset_liquidity_settings,
        )

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.callback_query = None
        context = MagicMock()

        await reset_liquidity_settings(update, context)

        mock_update.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings")
    @patch("src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings_keyboard")
    async def test_reset_to_defaults(self, mock_keyboard, mock_update):
        """Test reset applies default settings."""
        from src.telegram_bot.handlers.liquidity_settings_handler import (
            reset_liquidity_settings,
        )

        mock_keyboard.return_value = MagicMock()

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.callback_query = AsyncMock()
        update.callback_query.message = AsyncMock()
        context = MagicMock()

        await reset_liquidity_settings(update, context)

        # Check that update_liquidity_settings was called
        mock_update.assert_called_once()
        update.callback_query.answer.assert_called_once()


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_exist(self):
        """Test all expected exports exist."""
        from src.telegram_bot.handlers import liquidity_settings_handler

        # Functions
        assert hasattr(liquidity_settings_handler, "get_liquidity_settings")
        assert hasattr(liquidity_settings_handler, "update_liquidity_settings")
        assert hasattr(liquidity_settings_handler, "get_liquidity_settings_keyboard")
        assert hasattr(liquidity_settings_handler, "liquidity_settings_command")
        assert hasattr(liquidity_settings_handler, "toggle_liquidity_filter")
        assert hasattr(liquidity_settings_handler, "reset_liquidity_settings")

        # Constants
        assert hasattr(liquidity_settings_handler, "DEFAULT_LIQUIDITY_SETTINGS")

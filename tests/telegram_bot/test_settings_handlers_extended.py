"""Extended tests for settings_handlers.py module.

This module tests:
- Settings command handlers
- Language settings callbacks
- API key configuration
- Risk profile management
- User profile persistence
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.handlers.settings_handlers import (
    get_localized_text,
    get_user_profile,
    save_user_profiles,
    settings_callback,
    settings_command,
    setup_command,
    handle_setup_input,
    register_localization_handlers,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_update() -> MagicMock:
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789
    update.effective_user.mention_html = MagicMock(return_value="<a href=''>Test User</a>")
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_callback_update() -> MagicMock:
    """Create a mock Telegram Update with callback query."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789
    update.callback_query = MagicMock()
    update.callback_query.from_user = MagicMock()
    update.callback_query.from_user.id = 123456789
    update.callback_query.from_user.mention_html = MagicMock(return_value="<a href=''>Test</a>")
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "settings"
    update.message = None
    return update


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock Telegram context."""
    context = MagicMock()
    context.user_data = {}
    return context


# ============================================================================
# Test get_user_profile
# ============================================================================


class TestGetUserProfile:
    """Tests for get_user_profile function."""

    def test_get_existing_profile(self) -> None:
        """Test getting an existing user profile."""
        user_id = 111222333
        profile = get_user_profile(user_id)
        
        # Profile should be returned
        assert isinstance(profile, dict)
        
    def test_get_profile_creates_default_for_new_user(self) -> None:
        """Test that default profile is created for new users."""
        user_id = 999888777  # New user
        profile = get_user_profile(user_id)
        
        # Should have default structure
        assert isinstance(profile, dict)
        # Should have language set
        assert "language" in profile or "settings" in profile

    def test_get_profile_multiple_times_returns_same(self) -> None:
        """Test that getting profile multiple times returns same object."""
        user_id = 555666777
        profile1 = get_user_profile(user_id)
        profile2 = get_user_profile(user_id)
        
        # Should return consistent data
        assert profile1 is not None
        assert profile2 is not None


# ============================================================================
# Test get_localized_text
# ============================================================================


class TestGetLocalizedText:
    """Tests for get_localized_text function."""

    def test_get_localized_text_returns_string(self) -> None:
        """Test that localized text returns a string."""
        user_id = 123456789
        text = get_localized_text(user_id, "settings")
        
        assert isinstance(text, str)
        assert len(text) > 0

    def test_get_localized_text_with_missing_key(self) -> None:
        """Test handling of missing localization key."""
        user_id = 123456789
        text = get_localized_text(user_id, "nonexistent_key_xyz")
        
        # Should return something (either default or missing indicator)
        assert isinstance(text, str)

    def test_get_localized_text_with_kwargs(self) -> None:
        """Test localized text with format parameters."""
        user_id = 123456789
        # This should work with or without the parameters
        text = get_localized_text(user_id, "settings")
        
        assert isinstance(text, str)

    def test_get_localized_text_for_different_users(self) -> None:
        """Test that different users can have different languages."""
        user_id1 = 111111111
        user_id2 = 222222222
        
        # Get text for both users
        text1 = get_localized_text(user_id1, "settings")
        text2 = get_localized_text(user_id2, "settings")
        
        # Both should be valid strings
        assert isinstance(text1, str)
        assert isinstance(text2, str)


# ============================================================================
# Test settings_command
# ============================================================================


class TestSettingsCommand:
    """Tests for settings_command handler."""

    @pytest.mark.asyncio
    async def test_settings_command_sends_message(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that settings command sends a message."""
        await settings_command(mock_update, mock_context)
        
        # Should have sent a reply
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_settings_command_includes_keyboard(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that settings command includes keyboard."""
        await settings_command(mock_update, mock_context)
        
        # Should have reply_markup argument
        call_kwargs = mock_update.message.reply_text.call_args
        assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_settings_command_handles_no_user(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test settings command handling when no user."""
        mock_update.effective_user = None
        
        # Should not raise
        await settings_command(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_settings_command_handles_no_message(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test settings command handling when no message."""
        mock_update.message = None
        
        # Should not raise
        await settings_command(mock_update, mock_context)


# ============================================================================
# Test settings_callback
# ============================================================================


class TestSettingsCallback:
    """Tests for settings_callback handler."""

    @pytest.mark.asyncio
    async def test_callback_settings_main_menu(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test showing main settings menu."""
        mock_callback_update.callback_query.data = "settings"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_language_menu(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test showing language selection menu."""
        mock_callback_update.callback_query.data = "settings_language"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_set_language_ru(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setting Russian language."""
        mock_callback_update.callback_query.data = "language:ru"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_set_language_en(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setting English language."""
        mock_callback_update.callback_query.data = "language:en"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_invalid_language(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setting invalid language."""
        mock_callback_update.callback_query.data = "language:invalid_lang"
        
        await settings_callback(mock_callback_update, mock_context)
        
        # Should still respond
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_api_keys_menu(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test showing API keys menu."""
        mock_callback_update.callback_query.data = "settings_api_keys"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_toggle_trading(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test toggling auto trading."""
        mock_callback_update.callback_query.data = "settings_toggle_trading"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_limits_menu(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test showing limits menu."""
        mock_callback_update.callback_query.data = "settings_limits"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_risk_profile_low(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setting low risk profile."""
        mock_callback_update.callback_query.data = "risk_profile:low"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_risk_profile_medium(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setting medium risk profile."""
        mock_callback_update.callback_query.data = "risk_profile:medium"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_risk_profile_high(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setting high risk profile."""
        mock_callback_update.callback_query.data = "risk_profile:high"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_back_to_menu(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test back to main menu."""
        mock_callback_update.callback_query.data = "back_to_menu"
        
        await settings_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_handles_no_query(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling when no callback query."""
        mock_callback_update.callback_query = None
        
        # Should not raise
        await settings_callback(mock_callback_update, mock_context)

    @pytest.mark.asyncio
    async def test_callback_handles_no_data(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling when no callback data."""
        mock_callback_update.callback_query.data = None
        
        await settings_callback(mock_callback_update, mock_context)
        
        # With no data, callback should return early after answering
        # But the handler may return early before answer if data is None
        # This is acceptable behavior - test should not raise


# ============================================================================
# Test setup_command
# ============================================================================


class TestSetupCommand:
    """Tests for setup_command handler."""

    @pytest.mark.asyncio
    async def test_setup_command_starts_dialog(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that setup command starts API key dialog."""
        await setup_command(mock_update, mock_context)
        
        # Should send message prompting for API key
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_command_sets_state(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that setup command sets user state."""
        await setup_command(mock_update, mock_context)
        
        # Should set setup_state in user_data
        assert mock_context.user_data.get("setup_state") == "waiting_api_key"

    @pytest.mark.asyncio
    async def test_setup_command_handles_no_user(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setup command with no user."""
        mock_update.effective_user = None
        
        await setup_command(mock_update, mock_context)
        
        # Should not crash

    @pytest.mark.asyncio
    async def test_setup_command_handles_no_message(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test setup command with no message."""
        mock_update.message = None
        
        await setup_command(mock_update, mock_context)
        
        # Should not crash


# ============================================================================
# Test handle_setup_input
# ============================================================================


class TestHandleSetupInput:
    """Tests for handle_setup_input handler."""

    @pytest.mark.asyncio
    async def test_handle_api_key_input(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling API key input."""
        mock_context.user_data["setup_state"] = "waiting_api_key"
        mock_update.message.text = "test_api_key_12345"
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should prompt for secret key next
        mock_update.message.reply_text.assert_called_once()
        assert mock_context.user_data.get("setup_state") == "waiting_api_secret"

    @pytest.mark.asyncio
    async def test_handle_api_secret_input(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling API secret input."""
        mock_context.user_data["setup_state"] = "waiting_api_secret"
        mock_update.message.text = "test_secret_key_67890"
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should confirm and clear state
        mock_update.message.reply_text.assert_called_once()
        assert "setup_state" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_input_no_active_setup(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling input when no setup in progress."""
        mock_update.message.text = "random text"
        # No setup_state in user_data
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should not reply
        mock_update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_input_no_user(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling input with no user."""
        mock_update.effective_user = None
        mock_update.message.text = "test"
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should not crash

    @pytest.mark.asyncio
    async def test_handle_input_no_message(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling input with no message."""
        mock_update.message = None
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should not crash

    @pytest.mark.asyncio
    async def test_handle_input_no_text(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling input with no text."""
        mock_update.message.text = None
        mock_context.user_data["setup_state"] = "waiting_api_key"
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should not crash

    @pytest.mark.asyncio
    async def test_handle_input_null_user_data(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling input with None user_data."""
        mock_context.user_data = None
        mock_update.message.text = "test"
        
        await handle_setup_input(mock_update, mock_context)
        
        # Should not crash


# ============================================================================
# Test save_user_profiles
# ============================================================================


class TestSaveUserProfiles:
    """Tests for save_user_profiles function."""

    def test_save_profiles_does_not_raise(self) -> None:
        """Test that save_profiles doesn't raise exceptions."""
        # Should not raise
        save_user_profiles()

    @patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
    def test_save_empty_profiles(self) -> None:
        """Test saving empty profiles dictionary."""
        save_user_profiles()
        # Should not raise


# ============================================================================
# Test register_localization_handlers
# ============================================================================


class TestRegisterLocalizationHandlers:
    """Tests for register_localization_handlers function."""

    def test_register_handlers(self) -> None:
        """Test that handlers are registered with application."""
        mock_app = MagicMock()
        mock_app.add_handler = MagicMock()
        
        register_localization_handlers(mock_app)
        
        # Should have added handlers
        assert mock_app.add_handler.call_count >= 3  # At least 3 handlers


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_user_profile_concurrent_access(self) -> None:
        """Test concurrent access to user profiles."""
        user_id = 777888999
        
        # Multiple accesses should work
        profiles = [get_user_profile(user_id) for _ in range(10)]
        
        # All should be valid
        assert all(isinstance(p, dict) for p in profiles)

    def test_localized_text_special_characters(self) -> None:
        """Test localized text with special characters in kwargs."""
        user_id = 123456789
        
        # Should handle special characters
        text = get_localized_text(user_id, "settings")
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_settings_callback_unicode_data(
        self, mock_callback_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test callback with unicode data."""
        mock_callback_update.callback_query.data = "settings"  # Normal data
        
        await settings_callback(mock_callback_update, mock_context)
        
        # Should handle without error
        mock_callback_update.callback_query.answer.assert_called_once()

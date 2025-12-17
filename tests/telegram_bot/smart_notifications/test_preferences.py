"""Unit tests for smart_notifications/preferences module.

Tests for user preferences management.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.telegram_bot.smart_notifications.preferences import (
    get_active_alerts,
    get_user_preferences,
    get_user_prefs,
    load_user_preferences,
    register_user,
    save_user_preferences,
    update_user_preferences,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset module-level state before each test."""
    import src.telegram_bot.smart_notifications.preferences as prefs

    prefs._user_preferences = {}
    prefs._active_alerts = {}
    yield
    prefs._user_preferences = {}
    prefs._active_alerts = {}


# ============================================================================
# TESTS FOR get_user_preferences
# ============================================================================


class TestGetUserPreferences:
    """Tests for get_user_preferences function."""

    def test_empty_preferences(self):
        """Test getting empty preferences."""
        result = get_user_preferences()
        assert result == {}

    def test_returns_preferences_dict(self):
        """Test that function returns the preferences dict."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123": {"enabled": True}}

        result = get_user_preferences()

        assert result == {"123": {"enabled": True}}


# ============================================================================
# TESTS FOR get_active_alerts
# ============================================================================


class TestGetActiveAlerts:
    """Tests for get_active_alerts function."""

    def test_empty_alerts(self):
        """Test getting empty alerts."""
        result = get_active_alerts()
        assert result == {}

    def test_returns_alerts_dict(self):
        """Test that function returns the alerts dict."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {"123": [{"id": "alert1"}]}

        result = get_active_alerts()

        assert result == {"123": [{"id": "alert1"}]}


# ============================================================================
# TESTS FOR load_user_preferences
# ============================================================================


class TestLoadUserPreferences:
    """Tests for load_user_preferences function."""

    def test_file_not_exists(self):
        """Test loading when file doesn't exist."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE"
        ) as mock_file:
            mock_file.exists.return_value = False

            load_user_preferences()

            assert get_user_preferences() == {}
            assert get_active_alerts() == {}

    def test_successful_load(self):
        """Test successful loading of preferences."""
        test_data = {
            "user_preferences": {"123": {"enabled": True}},
            "active_alerts": {"123": [{"id": "alert1"}]},
        }

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE",
            mock_path,
        ):
            with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
                load_user_preferences()

        assert get_user_preferences() == {"123": {"enabled": True}}
        assert get_active_alerts() == {"123": [{"id": "alert1"}]}

    def test_json_decode_error(self):
        """Test handling of JSON decode error."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE",
            mock_path,
        ):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                load_user_preferences()

        assert get_user_preferences() == {}
        assert get_active_alerts() == {}

    def test_os_error(self):
        """Test handling of OS error."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE",
            mock_path,
        ):
            with patch("builtins.open", side_effect=OSError("File error")):
                load_user_preferences()

        assert get_user_preferences() == {}
        assert get_active_alerts() == {}


# ============================================================================
# TESTS FOR save_user_preferences
# ============================================================================


class TestSaveUserPreferences:
    """Tests for save_user_preferences function."""

    def test_creates_directory_if_not_exists(self):
        """Test that directory is created if it doesn't exist."""
        mock_data_dir = MagicMock()
        mock_data_dir.exists.return_value = False

        with patch(
            "src.telegram_bot.smart_notifications.preferences.DATA_DIR", mock_data_dir
        ):
            with patch("builtins.open", mock_open()):
                save_user_preferences()

        mock_data_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_successful_save(self):
        """Test successful saving of preferences."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123": {"enabled": True}}
        prefs._active_alerts = {"123": []}

        mock_data_dir = MagicMock()
        mock_data_dir.exists.return_value = True

        m = mock_open()

        with patch(
            "src.telegram_bot.smart_notifications.preferences.DATA_DIR", mock_data_dir
        ):
            with patch("builtins.open", m):
                save_user_preferences()

        # Verify file was written
        m.assert_called_once()

    def test_os_error_handling(self):
        """Test handling of OS error during save."""
        mock_data_dir = MagicMock()
        mock_data_dir.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.DATA_DIR", mock_data_dir
        ):
            with patch("builtins.open", side_effect=OSError("Write error")):
                # Should not raise
                save_user_preferences()


# ============================================================================
# TESTS FOR register_user
# ============================================================================


class TestRegisterUser:
    """Tests for register_user function."""

    @pytest.mark.asyncio()
    async def test_register_new_user(self):
        """Test registering a new user."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(123456)

        prefs = get_user_preferences()
        assert "123456" in prefs
        assert prefs["123456"]["chat_id"] == 123456

    @pytest.mark.asyncio()
    async def test_register_user_with_chat_id(self):
        """Test registering a user with custom chat ID."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(123456, chat_id=789012)

        prefs = get_user_preferences()
        assert prefs["123456"]["chat_id"] == 789012

    @pytest.mark.asyncio()
    async def test_register_existing_user_no_change(self):
        """Test that registering existing user doesn't change preferences."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {"enabled": False, "chat_id": 123456, "custom": "value"}
        }

        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(123456)

        # Original preferences should be unchanged
        assert prefs._user_preferences["123456"]["enabled"] is False
        assert prefs._user_preferences["123456"]["custom"] == "value"

    @pytest.mark.asyncio()
    async def test_register_adds_default_preferences(self):
        """Test that default preferences are added for new user."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(123456)

        prefs = get_user_preferences()
        assert "enabled" in prefs["123456"]
        assert "registered_at" in prefs["123456"]


# ============================================================================
# TESTS FOR update_user_preferences
# ============================================================================


class TestUpdateUserPreferences:
    """Tests for update_user_preferences function."""

    @pytest.mark.asyncio()
    async def test_update_simple_value(self):
        """Test updating a simple preference value."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {"enabled": True, "frequency": "normal"}
        }

        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(123456, {"frequency": "high"})

        assert prefs._user_preferences["123456"]["frequency"] == "high"

    @pytest.mark.asyncio()
    async def test_update_nested_dict(self):
        """Test updating a nested dictionary value."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": True, "price_alert": True},
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(
                123456, {"notifications": {"market_opportunity": False}}
            )

        # Should merge, not replace
        assert prefs._user_preferences["123456"]["notifications"]["market_opportunity"] is False
        assert prefs._user_preferences["123456"]["notifications"]["price_alert"] is True

    @pytest.mark.asyncio()
    async def test_update_registers_new_user(self):
        """Test that updating preferences for new user registers them first."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(123456, {"frequency": "low"})

        prefs = get_user_preferences()
        assert "123456" in prefs

    @pytest.mark.asyncio()
    async def test_update_unknown_key_ignored(self):
        """Test that updating with unknown key doesn't add it."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(123456, {"unknown_key": "value"})

        assert "unknown_key" not in prefs._user_preferences["123456"]


# ============================================================================
# TESTS FOR get_user_prefs
# ============================================================================


class TestGetUserPrefs:
    """Tests for get_user_prefs function."""

    def test_get_existing_user(self):
        """Test getting preferences for existing user."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True, "frequency": "normal"}}

        result = get_user_prefs(123456)

        assert result == {"enabled": True, "frequency": "normal"}

    def test_get_nonexistent_user(self):
        """Test getting preferences for nonexistent user."""
        result = get_user_prefs(123456)
        assert result == {}

    def test_get_user_returns_correct_type(self):
        """Test that function returns a dict."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        result = get_user_prefs(123456)

        assert isinstance(result, dict)

    def test_get_user_with_string_id(self):
        """Test that user_id is converted to string for lookup."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        # Pass int, should find string key
        result = get_user_prefs(123456)

        assert result == {"enabled": True}

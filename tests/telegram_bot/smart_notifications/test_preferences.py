"""Tests for smart_notifications/preferences.py module.

Covers:
- get_user_preferences function
- get_active_alerts function
- load_user_preferences function
- save_user_preferences function
- register_user function
- update_user_preferences function
- get_user_prefs function
"""

from datetime import datetime
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


class TestGetUserPreferences:
    """Tests for get_user_preferences function."""

    def test_get_user_preferences_returns_dict(self) -> None:
        """Test get_user_preferences returns a dictionary."""
        result = get_user_preferences()
        assert isinstance(result, dict)


class TestGetActiveAlerts:
    """Tests for get_active_alerts function."""

    def test_get_active_alerts_returns_dict(self) -> None:
        """Test get_active_alerts returns a dictionary."""
        result = get_active_alerts()
        assert isinstance(result, dict)


class TestLoadUserPreferences:
    """Tests for load_user_preferences function."""

    def test_load_preferences_file_not_exists(self) -> None:
        """Test loading preferences when file doesn't exist."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE"
        ) as mock_file:
            mock_file.exists.return_value = False

            # Should not raise error
            load_user_preferences()

    def test_load_preferences_valid_json(self) -> None:
        """Test loading valid JSON preferences."""
        test_data = {
            "user_preferences": {"123": {"enabled": True}},
            "active_alerts": {"123": []},
        }

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE",
            mock_path,
        ), patch(
            "builtins.open", mock_open(read_data=json.dumps(test_data))
        ):
            load_user_preferences()

    def test_load_preferences_invalid_json(self) -> None:
        """Test loading invalid JSON gracefully."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE",
            mock_path,
        ), patch(
            "builtins.open", mock_open(read_data="invalid json{")
        ):
            # Should not raise error, just log it
            load_user_preferences()

    def test_load_preferences_io_error(self) -> None:
        """Test handling IO error during load."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.SMART_ALERTS_FILE",
            mock_path,
        ), patch(
            "builtins.open", side_effect=OSError("File read error")
        ):
            # Should not raise error
            load_user_preferences()


class TestSaveUserPreferences:
    """Tests for save_user_preferences function."""

    def test_save_preferences_creates_directory(self) -> None:
        """Test that save creates directory if needed."""
        mock_data_dir = MagicMock(spec=Path)
        mock_data_dir.exists.return_value = False

        with patch(
            "src.telegram_bot.smart_notifications.preferences.DATA_DIR",
            mock_data_dir,
        ), patch(
            "builtins.open", mock_open()
        ):
            save_user_preferences()

            mock_data_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_save_preferences_writes_json(self) -> None:
        """Test that save writes valid JSON."""
        mock_data_dir = MagicMock(spec=Path)
        mock_data_dir.exists.return_value = True

        m = mock_open()
        with patch(
            "src.telegram_bot.smart_notifications.preferences.DATA_DIR",
            mock_data_dir,
        ), patch(
            "builtins.open", m
        ):
            save_user_preferences()

            m.assert_called()

    def test_save_preferences_handles_io_error(self) -> None:
        """Test handling IO error during save."""
        mock_data_dir = MagicMock(spec=Path)
        mock_data_dir.exists.return_value = True

        with patch(
            "src.telegram_bot.smart_notifications.preferences.DATA_DIR",
            mock_data_dir,
        ), patch(
            "builtins.open", side_effect=OSError("Write error")
        ):
            # Should not raise error
            save_user_preferences()


class TestRegisterUser:
    """Tests for register_user function."""

    @pytest.mark.asyncio
    async def test_register_new_user(self) -> None:
        """Test registering a new user."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ) as mock_save, patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences", {}
        ):
            await register_user(user_id=12345)

            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_with_chat_id(self) -> None:
        """Test registering user with specific chat_id."""
        user_prefs: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(user_id=111, chat_id=222)

            assert user_prefs["111"]["chat_id"] == 222

    @pytest.mark.asyncio
    async def test_register_user_default_chat_id(self) -> None:
        """Test registering user uses user_id as default chat_id."""
        user_prefs: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(user_id=333)

            assert user_prefs["333"]["chat_id"] == 333

    @pytest.mark.asyncio
    async def test_register_existing_user_does_nothing(self) -> None:
        """Test registering existing user doesn't modify preferences."""
        user_prefs = {"444": {"enabled": True, "custom_setting": "value"}}

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ) as mock_save:
            await register_user(user_id=444)

            # Should not save because user already exists
            mock_save.assert_not_called()
            # Custom setting should be preserved
            assert user_prefs["444"]["custom_setting"] == "value"

    @pytest.mark.asyncio
    async def test_register_user_includes_default_preferences(self) -> None:
        """Test that registered user has default preferences."""
        user_prefs: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await register_user(user_id=555)

            prefs = user_prefs["555"]
            assert "enabled" in prefs
            assert "registered_at" in prefs
            assert "chat_id" in prefs


class TestUpdateUserPreferences:
    """Tests for update_user_preferences function."""

    @pytest.mark.asyncio
    async def test_update_preferences_simple_value(self) -> None:
        """Test updating a simple preference value."""
        user_prefs = {
            "666": {
                "enabled": True,
                "frequency": "normal",
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(user_id=666, preferences={"frequency": "high"})

            assert user_prefs["666"]["frequency"] == "high"

    @pytest.mark.asyncio
    async def test_update_preferences_nested_dict(self) -> None:
        """Test updating nested dictionary preferences."""
        user_prefs = {
            "777": {
                "enabled": True,
                "quiet_hours": {"start": 23, "end": 8},
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(
                user_id=777,
                preferences={"quiet_hours": {"start": 22}},
            )

            # Should merge dictionaries
            assert user_prefs["777"]["quiet_hours"]["start"] == 22
            # Original value should be preserved
            assert user_prefs["777"]["quiet_hours"]["end"] == 8

    @pytest.mark.asyncio
    async def test_update_preferences_registers_new_user(self) -> None:
        """Test that update registers new user if needed."""
        # Simulate register_user adding user to preferences
        user_prefs: dict = {}

        async def fake_register(user_id: int) -> None:
            user_prefs[str(user_id)] = {"enabled": True, "frequency": "normal"}

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.register_user",
            side_effect=fake_register,
        ) as mock_register:
            await update_user_preferences(user_id=888, preferences={"enabled": False})

            mock_register.assert_called_once_with(888)

    @pytest.mark.asyncio
    async def test_update_preferences_ignores_unknown_keys(self) -> None:
        """Test that update ignores unknown preference keys."""
        user_prefs = {
            "999": {
                "enabled": True,
                "frequency": "normal",
            }
        }
        original_keys = set(user_prefs["999"].keys())

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            await update_user_preferences(
                user_id=999,
                preferences={"unknown_key": "value"},
            )

            # Should not add unknown key
            assert set(user_prefs["999"].keys()) == original_keys


class TestGetUserPrefs:
    """Tests for get_user_prefs function."""

    def test_get_user_prefs_existing_user(self) -> None:
        """Test getting preferences for existing user."""
        user_prefs = {
            "1000": {"enabled": True, "frequency": "high"}
        }

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ):
            result = get_user_prefs(user_id=1000)

            assert result["enabled"] is True
            assert result["frequency"] == "high"

    def test_get_user_prefs_nonexistent_user(self) -> None:
        """Test getting preferences for non-existent user."""
        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            {},
        ):
            result = get_user_prefs(user_id=9999)

            assert result == {}


class TestPreferencesIntegration:
    """Integration tests for preferences module."""

    @pytest.mark.asyncio
    async def test_register_and_update_flow(self) -> None:
        """Test complete register and update flow."""
        user_prefs: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.preferences._user_preferences",
            user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.preferences.save_user_preferences"
        ):
            # Register user
            await register_user(user_id=2000)
            assert "2000" in user_prefs

            # Update preferences
            await update_user_preferences(
                user_id=2000,
                preferences={"frequency": "low"},
            )
            assert user_prefs["2000"]["frequency"] == "low"

            # Get preferences
            prefs = get_user_prefs(user_id=2000)
            assert prefs["frequency"] == "low"

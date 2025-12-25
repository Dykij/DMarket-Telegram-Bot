"""Unit tests for smart_notifications/preferences module.

Tests for user preferences management including loading,
saving, and updating notification preferences.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import mock_open, patch

import pytest


# ============================================================================
# Tests for get_user_preferences
# ============================================================================


class TestGetUserPreferences:
    """Tests for get_user_preferences function."""

    def test_returns_user_preferences_dict(self) -> None:
        """Test that get_user_preferences returns the preferences dict."""
        from src.telegram_bot.smart_notifications import preferences

        # Set up test data
        original_prefs = preferences._user_preferences
        preferences._user_preferences = {"123": {"enabled": True}}

        try:
            result = preferences.get_user_preferences()
            assert result == {"123": {"enabled": True}}
        finally:
            preferences._user_preferences = original_prefs


# ============================================================================
# Tests for get_active_alerts
# ============================================================================


class TestGetActiveAlerts:
    """Tests for get_active_alerts function."""

    def test_returns_active_alerts_dict(self) -> None:
        """Test that get_active_alerts returns the alerts dict."""
        from src.telegram_bot.smart_notifications import preferences

        # Set up test data
        original_alerts = preferences._active_alerts
        preferences._active_alerts = {"123": [{"id": "alert_1"}]}

        try:
            result = preferences.get_active_alerts()
            assert result == {"123": [{"id": "alert_1"}]}
        finally:
            preferences._active_alerts = original_alerts


# ============================================================================
# Tests for load_user_preferences
# ============================================================================


class TestLoadUserPreferences:
    """Tests for load_user_preferences function."""

    def test_load_from_existing_file(self) -> None:
        """Test loading preferences from an existing file."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()
        original_alerts = preferences._active_alerts.copy()

        file_data = json.dumps(
            {
                "user_preferences": {"123": {"enabled": True}},
                "active_alerts": {"123": [{"id": "alert_1"}]},
            }
        )

        try:
            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=file_data)):
                    preferences.load_user_preferences()

            assert "123" in preferences._user_preferences
            assert "123" in preferences._active_alerts
        finally:
            preferences._user_preferences = original_prefs
            preferences._active_alerts = original_alerts

    def test_load_file_not_exists(self) -> None:
        """Test loading when file doesn't exist."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()
        original_alerts = preferences._active_alerts.copy()

        try:
            with patch.object(Path, "exists", return_value=False):
                preferences.load_user_preferences()

            # Should initialize to empty dicts
            assert preferences._user_preferences == {}
            assert preferences._active_alerts == {}
        finally:
            preferences._user_preferences = original_prefs
            preferences._active_alerts = original_alerts

    def test_load_handles_json_decode_error(self) -> None:
        """Test handling of invalid JSON file."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()
        original_alerts = preferences._active_alerts.copy()

        try:
            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="invalid json {")):
                    preferences.load_user_preferences()

            # Should reset to empty dicts
            assert preferences._user_preferences == {}
            assert preferences._active_alerts == {}
        finally:
            preferences._user_preferences = original_prefs
            preferences._active_alerts = original_alerts

    def test_load_handles_io_error(self) -> None:
        """Test handling of IO error during load."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()
        original_alerts = preferences._active_alerts.copy()

        try:
            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", side_effect=OSError("Read error")):
                    preferences.load_user_preferences()

            # Should reset to empty dicts
            assert preferences._user_preferences == {}
            assert preferences._active_alerts == {}
        finally:
            preferences._user_preferences = original_prefs
            preferences._active_alerts = original_alerts


# ============================================================================
# Tests for save_user_preferences
# ============================================================================


class TestSaveUserPreferences:
    """Tests for save_user_preferences function."""

    def test_save_creates_directory_if_needed(self) -> None:
        """Test that save creates data directory if it doesn't exist."""
        from src.telegram_bot.smart_notifications import preferences

        mock_file = mock_open()

        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "mkdir") as mock_mkdir:
                with patch("builtins.open", mock_file):
                    preferences.save_user_preferences()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_save_writes_json_file(self) -> None:
        """Test that save writes JSON to file."""
        from src.telegram_bot.smart_notifications import preferences

        mock_file = mock_open()

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_file):
                preferences.save_user_preferences()

        # Verify file was opened for writing
        mock_file.assert_called()

    def test_save_handles_io_error(self) -> None:
        """Test handling of IO error during save."""
        from src.telegram_bot.smart_notifications import preferences

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", side_effect=OSError("Write error")):
                # Should not raise
                preferences.save_user_preferences()


# ============================================================================
# Tests for register_user
# ============================================================================


class TestRegisterUser:
    """Tests for register_user function."""

    @pytest.mark.asyncio
    async def test_register_new_user(self) -> None:
        """Test registering a new user."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {}

            with patch.object(preferences, "save_user_preferences"):
                await preferences.register_user(user_id=123)

            assert "123" in preferences._user_preferences
            assert preferences._user_preferences["123"]["chat_id"] == 123
        finally:
            preferences._user_preferences = original_prefs

    @pytest.mark.asyncio
    async def test_register_with_chat_id(self) -> None:
        """Test registering a user with specific chat_id."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {}

            with patch.object(preferences, "save_user_preferences"):
                await preferences.register_user(user_id=123, chat_id=456)

            assert preferences._user_preferences["123"]["chat_id"] == 456
        finally:
            preferences._user_preferences = original_prefs

    @pytest.mark.asyncio
    async def test_register_existing_user_no_overwrite(self) -> None:
        """Test that registering existing user doesn't overwrite data."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {
                "123": {"enabled": True, "custom_setting": "value"}
            }

            with patch.object(preferences, "save_user_preferences"):
                await preferences.register_user(user_id=123)

            # Existing data should be preserved
            assert preferences._user_preferences["123"]["custom_setting"] == "value"
        finally:
            preferences._user_preferences = original_prefs


# ============================================================================
# Tests for update_user_preferences
# ============================================================================


class TestUpdateUserPreferences:
    """Tests for update_user_preferences function."""

    @pytest.mark.asyncio
    async def test_update_simple_preference(self) -> None:
        """Test updating a simple preference value."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {"123": {"enabled": True, "frequency": "normal"}}

            with patch.object(preferences, "save_user_preferences"):
                await preferences.update_user_preferences(
                    user_id=123,
                    preferences={"frequency": "high"},
                )

            assert preferences._user_preferences["123"]["frequency"] == "high"
        finally:
            preferences._user_preferences = original_prefs

    @pytest.mark.asyncio
    async def test_update_nested_preference(self) -> None:
        """Test updating a nested preference (dict merge)."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {
                "123": {
                    "notifications": {"price_alert": True, "market_opportunity": True}
                }
            }

            with patch.object(preferences, "save_user_preferences"):
                await preferences.update_user_preferences(
                    user_id=123,
                    preferences={"notifications": {"market_opportunity": False}},
                )

            # Should merge, not overwrite
            assert preferences._user_preferences["123"]["notifications"]["price_alert"] is True
            assert (
                preferences._user_preferences["123"]["notifications"]["market_opportunity"]
                is False
            )
        finally:
            preferences._user_preferences = original_prefs

    @pytest.mark.asyncio
    async def test_update_registers_new_user(self) -> None:
        """Test that updating unregistered user registers them first."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {}

            with patch.object(preferences, "save_user_preferences"):
                # Mock register_user to also add user to preferences
                async def mock_register(user_id, chat_id=None):
                    preferences._user_preferences[str(user_id)] = {"frequency": "normal"}

                with patch.object(preferences, "register_user", side_effect=mock_register) as mock_reg:
                    await preferences.update_user_preferences(
                        user_id=123,
                        preferences={"frequency": "low"},
                    )

            mock_reg.assert_called_once_with(123)
        finally:
            preferences._user_preferences = original_prefs


# ============================================================================
# Tests for get_user_prefs
# ============================================================================


class TestGetUserPrefs:
    """Tests for get_user_prefs function."""

    def test_get_existing_user_prefs(self) -> None:
        """Test getting preferences for existing user."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {"123": {"enabled": True, "frequency": "high"}}

            result = preferences.get_user_prefs(123)

            assert result == {"enabled": True, "frequency": "high"}
        finally:
            preferences._user_preferences = original_prefs

    def test_get_nonexistent_user_prefs(self) -> None:
        """Test getting preferences for non-existent user returns empty dict."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {}

            result = preferences.get_user_prefs(123)

            assert result == {}
        finally:
            preferences._user_preferences = original_prefs

    def test_get_user_prefs_by_int_id(self) -> None:
        """Test that integer user_id is converted to string for lookup."""
        from src.telegram_bot.smart_notifications import preferences

        # Save original values
        original_prefs = preferences._user_preferences.copy()

        try:
            preferences._user_preferences = {"123": {"enabled": True}}

            # Pass integer ID
            result = preferences.get_user_prefs(123)

            assert result == {"enabled": True}
        finally:
            preferences._user_preferences = original_prefs

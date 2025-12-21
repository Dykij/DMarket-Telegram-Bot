"""Comprehensive tests for notifications/storage module.

Tests AlertStorage class, singleton pattern, load/save operations,
user data management, and price cache functionality.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import time

from src.telegram_bot.notifications.storage import (
    AlertStorage,
    get_storage,
    load_user_alerts,
    save_user_alerts,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset AlertStorage singleton before each test."""
    AlertStorage._instance = None
    AlertStorage._initialized = False
    yield
    AlertStorage._instance = None
    AlertStorage._initialized = False


@pytest.fixture
def storage():
    """Create a fresh AlertStorage instance."""
    return AlertStorage()


@pytest.fixture
def sample_user_data():
    """Create sample user data."""
    return {
        "12345": {
            "alerts": [
                {"id": "alert_1", "item_name": "AK-47", "active": True},
                {"id": "alert_2", "item_name": "M4A4", "active": False},
            ],
            "settings": {"notifications": True, "language": "ru"},
            "last_notification": 1234567890,
            "daily_notifications": 5,
            "daily_reset": "2025-12-21",
        },
        "67890": {
            "alerts": [],
            "settings": {"notifications": False},
            "last_notification": 0,
            "daily_notifications": 0,
            "daily_reset": "2025-12-21",
        },
    }


# =============================================================================
# AlertStorage singleton tests
# =============================================================================


class TestAlertStorageSingleton:
    """Tests for AlertStorage singleton pattern."""

    def test_singleton_instance(self):
        """Test that AlertStorage returns the same instance."""
        storage1 = AlertStorage()
        storage2 = AlertStorage()
        assert storage1 is storage2

    def test_singleton_initialized_once(self):
        """Test that initialization only happens once."""
        storage1 = AlertStorage()
        storage1._user_alerts["test"] = {"data": "value"}

        storage2 = AlertStorage()
        # Second instance should have same data
        assert storage2._user_alerts.get("test") == {"data": "value"}

    def test_get_storage_returns_singleton(self):
        """Test get_storage returns the singleton instance."""
        storage1 = get_storage()
        storage2 = get_storage()
        assert storage1 is storage2


# =============================================================================
# AlertStorage initialization tests
# =============================================================================


class TestAlertStorageInitialization:
    """Tests for AlertStorage initialization."""

    def test_initial_state(self, storage):
        """Test initial state of storage."""
        assert storage._user_alerts == {}
        assert storage._current_prices_cache == {}
        assert storage._alerts_file == Path("data/user_alerts.json")
        assert storage._initialized is True

    def test_user_alerts_property(self, storage):
        """Test user_alerts property."""
        storage._user_alerts["test"] = {"data": "value"}
        assert storage.user_alerts == {"test": {"data": "value"}}

    def test_alerts_file_property(self, storage):
        """Test alerts_file property."""
        assert storage.alerts_file == Path("data/user_alerts.json")

    def test_prices_cache_property(self, storage):
        """Test prices_cache property."""
        storage._current_prices_cache["item"] = {"price": 10.0}
        assert storage.prices_cache == {"item": {"price": 10.0}}


# =============================================================================
# load_user_alerts tests
# =============================================================================


class TestLoadUserAlerts:
    """Tests for load_user_alerts functionality."""

    def test_load_alerts_from_file(self, storage, sample_user_data):
        """Test loading alerts from existing file."""
        mock_file_content = json.dumps(sample_user_data)

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", mock_open(read_data=mock_file_content)):
            storage.load_user_alerts()

        assert len(storage._user_alerts) == 2
        assert "12345" in storage._user_alerts
        assert "67890" in storage._user_alerts

    def test_load_alerts_file_not_exists(self, storage):
        """Test loading when file doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            storage.load_user_alerts()

        assert storage._user_alerts == {}

    def test_load_alerts_json_decode_error(self, storage):
        """Test handling of JSON decode error."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", mock_open(read_data="invalid json {")):
            storage.load_user_alerts()

        assert storage._user_alerts == {}

    def test_load_alerts_os_error(self, storage):
        """Test handling of OS error during file read."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", side_effect=OSError("Permission denied")):
            storage.load_user_alerts()

        assert storage._user_alerts == {}

    def test_load_alerts_preserves_dict_reference(self, storage, sample_user_data):
        """Test that load updates dict in place."""
        original_dict = storage._user_alerts
        mock_file_content = json.dumps(sample_user_data)

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", mock_open(read_data=mock_file_content)):
            storage.load_user_alerts()

        # Should be same dict object, just updated
        assert storage._user_alerts is original_dict

    def test_load_user_alerts_wrapper(self, sample_user_data):
        """Test load_user_alerts wrapper function."""
        mock_file_content = json.dumps(sample_user_data)

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", mock_open(read_data=mock_file_content)):
            load_user_alerts()

        storage = get_storage()
        assert len(storage._user_alerts) == 2


# =============================================================================
# save_user_alerts tests
# =============================================================================


class TestSaveUserAlerts:
    """Tests for save_user_alerts functionality."""

    def test_save_alerts_to_file(self, storage):
        """Test saving alerts to file."""
        storage._user_alerts["12345"] = {"alerts": [], "settings": {}}

        mock_file = mock_open()
        with patch.object(Path, "parent", new_callable=lambda: MagicMock()), \
             patch.object(Path, "open", mock_file):
            storage.save_user_alerts()

        mock_file.assert_called_once()

    def test_save_alerts_creates_directory(self, storage):
        """Test save creates parent directory if needed."""
        storage._user_alerts["12345"] = {"alerts": []}

        mock_mkdir = MagicMock()
        mock_parent = MagicMock()
        mock_parent.mkdir = mock_mkdir

        mock_file = mock_open()
        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_file):
            storage.save_user_alerts()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_save_alerts_os_error(self, storage):
        """Test handling of OS error during save."""
        storage._user_alerts["12345"] = {"alerts": []}

        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", side_effect=OSError("Permission denied")):
            # Should not raise
            storage.save_user_alerts()

    def test_save_user_alerts_wrapper(self):
        """Test save_user_alerts wrapper function."""
        storage = get_storage()
        storage._user_alerts["12345"] = {"alerts": []}

        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()
        mock_file = mock_open()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_file):
            save_user_alerts()


# =============================================================================
# get_user_data tests
# =============================================================================


class TestGetUserData:
    """Tests for get_user_data functionality."""

    def test_get_existing_user(self, storage):
        """Test getting data for existing user."""
        storage._user_alerts["12345"] = {
            "alerts": [{"id": "alert_1"}],
            "settings": {"notifications": True},
            "last_notification": 1234567890,
            "daily_notifications": 3,
            "daily_reset": time.strftime("%Y-%m-%d"),
        }

        user_data = storage.get_user_data(12345)
        assert user_data["alerts"] == [{"id": "alert_1"}]

    def test_get_new_user_creates_entry(self, storage):
        """Test getting data for new user creates entry."""
        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_open()):
            user_data = storage.get_user_data(99999)

        assert "99999" in storage._user_alerts
        assert user_data["alerts"] == []
        assert "settings" in user_data

    def test_get_user_data_resets_daily_counter(self, storage):
        """Test daily notification counter resets on new day."""
        storage._user_alerts["12345"] = {
            "alerts": [],
            "settings": {},
            "last_notification": 0,
            "daily_notifications": 100,
            "daily_reset": "2020-01-01",  # Old date
        }

        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_open()):
            user_data = storage.get_user_data(12345)

        assert user_data["daily_notifications"] == 0
        assert user_data["daily_reset"] == time.strftime("%Y-%m-%d")

    def test_get_user_data_preserves_daily_counter_same_day(self, storage):
        """Test daily counter preserved on same day."""
        today = time.strftime("%Y-%m-%d")
        storage._user_alerts["12345"] = {
            "alerts": [],
            "settings": {},
            "last_notification": 0,
            "daily_notifications": 50,
            "daily_reset": today,
        }

        user_data = storage.get_user_data(12345)
        assert user_data["daily_notifications"] == 50


class TestEnsureUserExists:
    """Tests for ensure_user_exists functionality."""

    def test_ensure_new_user(self, storage):
        """Test ensuring new user creates entry."""
        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_open()):
            storage.ensure_user_exists(12345)

        assert "12345" in storage._user_alerts

    def test_ensure_existing_user(self, storage):
        """Test ensuring existing user doesn't overwrite."""
        storage._user_alerts["12345"] = {
            "alerts": [{"id": "alert_1"}],
            "settings": {},
            "last_notification": 0,
            "daily_notifications": 0,
            "daily_reset": time.strftime("%Y-%m-%d"),
        }

        storage.ensure_user_exists(12345)
        assert storage._user_alerts["12345"]["alerts"] == [{"id": "alert_1"}]


# =============================================================================
# Price cache tests
# =============================================================================


class TestPriceCache:
    """Tests for price cache functionality."""

    def test_clear_price_cache(self, storage):
        """Test clearing price cache."""
        storage._current_prices_cache["item1"] = {"price": 10.0}
        storage._current_prices_cache["item2"] = {"price": 20.0}

        storage.clear_price_cache()

        assert storage._current_prices_cache == {}

    def test_clear_price_cache_preserves_reference(self, storage):
        """Test clearing cache preserves dict reference."""
        original_cache = storage._current_prices_cache
        storage._current_prices_cache["item1"] = {"price": 10.0}

        storage.clear_price_cache()

        assert storage._current_prices_cache is original_cache

    def test_get_cached_price_exists(self, storage):
        """Test getting existing cached price."""
        storage._current_prices_cache["item_123"] = {
            "price": 15.50,
            "timestamp": 1234567890,
        }

        result = storage.get_cached_price("item_123")
        assert result == {"price": 15.50, "timestamp": 1234567890}

    def test_get_cached_price_not_exists(self, storage):
        """Test getting non-existing cached price."""
        result = storage.get_cached_price("nonexistent_item")
        assert result is None

    def test_set_cached_price(self, storage):
        """Test setting cached price."""
        storage.set_cached_price("item_456", 25.00, 1234567890)

        assert storage._current_prices_cache["item_456"] == {
            "price": 25.00,
            "timestamp": 1234567890,
        }

    def test_set_cached_price_overwrites(self, storage):
        """Test setting cached price overwrites existing."""
        storage._current_prices_cache["item_789"] = {
            "price": 10.00,
            "timestamp": 1000000000,
        }

        storage.set_cached_price("item_789", 20.00, 2000000000)

        assert storage._current_prices_cache["item_789"] == {
            "price": 20.00,
            "timestamp": 2000000000,
        }


# =============================================================================
# Integration tests
# =============================================================================


class TestStorageIntegration:
    """Integration tests for storage module."""

    def test_full_workflow(self, storage):
        """Test complete workflow: create user, add data, save, load."""
        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        # Create user
        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_open()):
            user_data = storage.get_user_data(12345)
            user_data["alerts"].append({"id": "alert_1", "item": "AK-47"})
            storage.save_user_alerts()

        # Verify data exists
        assert "12345" in storage._user_alerts
        assert len(storage._user_alerts["12345"]["alerts"]) == 1

    def test_multiple_users(self, storage):
        """Test handling multiple users."""
        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_open()):
            # Create multiple users
            storage.get_user_data(11111)
            storage.get_user_data(22222)
            storage.get_user_data(33333)

        assert len(storage._user_alerts) == 3
        assert "11111" in storage._user_alerts
        assert "22222" in storage._user_alerts
        assert "33333" in storage._user_alerts

    def test_price_cache_workflow(self, storage):
        """Test price cache full workflow."""
        # Set prices
        storage.set_cached_price("item_1", 10.0, 1000)
        storage.set_cached_price("item_2", 20.0, 2000)

        # Get prices
        assert storage.get_cached_price("item_1")["price"] == 10.0
        assert storage.get_cached_price("item_2")["price"] == 20.0

        # Clear cache
        storage.clear_price_cache()
        assert storage.get_cached_price("item_1") is None
        assert storage.get_cached_price("item_2") is None


# =============================================================================
# Edge case tests
# =============================================================================


class TestEdgeCases:
    """Edge case tests for storage module."""

    def test_user_id_as_string(self, storage):
        """Test that user_id is converted to string."""
        mock_parent = MagicMock()
        mock_parent.mkdir = MagicMock()

        with patch.object(Path, "parent", mock_parent), \
             patch.object(Path, "open", mock_open()):
            storage.get_user_data(12345)

        # Key should be string, not int
        assert "12345" in storage._user_alerts
        assert 12345 not in storage._user_alerts

    def test_empty_alerts_file(self, storage):
        """Test loading empty alerts file."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", mock_open(read_data="{}")):
            storage.load_user_alerts()

        assert storage._user_alerts == {}

    def test_corrupted_user_data_recovery(self, storage):
        """Test recovery from partially corrupted data."""
        partial_data = {
            "12345": {
                "alerts": [],
                # Missing required fields
            },
        }
        mock_content = json.dumps(partial_data)

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "open", mock_open(read_data=mock_content)):
            storage.load_user_alerts()

        # Should still load what it can
        assert "12345" in storage._user_alerts

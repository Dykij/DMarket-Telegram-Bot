"""Tests for telegram_bot.notifications.alerts module.

This module tests alert management functions:
- add_price_alert
- remove_price_alert
- get_user_alerts
- update_user_settings
- get_user_settings
- reset_daily_counter
- increment_notification_count
- can_send_notification
"""

from __future__ import annotations

from datetime import datetime
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Test add_price_alert function
# =============================================================================

class TestAddPriceAlert:
    """Tests for add_price_alert function."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage."""
        storage = MagicMock()
        storage.get_user_data.return_value = {
            "alerts": [],
            "settings": {},
            "daily_notifications": 0,
        }
        return storage

    @pytest.mark.asyncio
    async def test_add_price_alert_creates_alert(self, mock_storage: MagicMock) -> None:
        """Test that add_price_alert creates an alert with correct data."""
        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import add_price_alert

            result = await add_price_alert(
                user_id=12345,
                item_id="item_abc123",
                title="AK-47 | Redline",
                game="csgo",
                alert_type="price_drop",
                threshold=15.50,
            )

            assert result["item_id"] == "item_abc123"
            assert result["title"] == "AK-47 | Redline"
            assert result["game"] == "csgo"
            assert result["type"] == "price_drop"
            assert result["threshold"] == 15.50
            assert result["active"] is True
            assert "id" in result
            assert "created_at" in result

    @pytest.mark.asyncio
    async def test_add_price_alert_generates_unique_id(
        self, mock_storage: MagicMock
    ) -> None:
        """Test that add_price_alert generates unique alert ID."""
        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import add_price_alert

            result = await add_price_alert(
                user_id=12345,
                item_id="item_abc",
                title="Test Item",
                game="csgo",
                alert_type="price_rise",
                threshold=25.00,
            )

            assert result["id"].startswith("alert_")
            assert "12345" in result["id"]

    @pytest.mark.asyncio
    async def test_add_price_alert_saves_to_storage(
        self, mock_storage: MagicMock
    ) -> None:
        """Test that add_price_alert saves the alert."""
        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import add_price_alert

            await add_price_alert(
                user_id=12345,
                item_id="item_xyz",
                title="Test",
                game="dota2",
                alert_type="volume_increase",
                threshold=100,
            )

            mock_storage.save_user_alerts.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_price_alert_various_types(
        self, mock_storage: MagicMock
    ) -> None:
        """Test add_price_alert with various alert types."""
        alert_types = [
            "price_drop",
            "price_rise",
            "price_below",
            "price_above",
            "volume_increase",
            "trend_change",
        ]

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import add_price_alert

            for alert_type in alert_types:
                mock_storage.get_user_data.return_value = {
                    "alerts": [],
                    "settings": {},
                }

                result = await add_price_alert(
                    user_id=12345,
                    item_id=f"item_{alert_type}",
                    title="Test",
                    game="csgo",
                    alert_type=alert_type,
                    threshold=10.0,
                )

                assert result["type"] == alert_type


# =============================================================================
# Test remove_price_alert function
# =============================================================================

class TestRemovePriceAlert:
    """Tests for remove_price_alert function."""

    @pytest.fixture
    def mock_storage_with_alerts(self) -> MagicMock:
        """Create mock storage with existing alerts."""
        storage = MagicMock()
        storage.get_user_data.return_value = {
            "alerts": [
                {"id": "alert_001", "title": "Alert 1", "active": True},
                {"id": "alert_002", "title": "Alert 2", "active": True},
            ],
            "settings": {},
        }
        return storage

    @pytest.mark.asyncio
    async def test_remove_existing_alert(
        self, mock_storage_with_alerts: MagicMock
    ) -> None:
        """Test removing an existing alert."""
        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage_with_alerts,
        ):
            from src.telegram_bot.notifications.alerts import remove_price_alert

            result = await remove_price_alert(user_id=12345, alert_id="alert_001")

            assert result is True
            mock_storage_with_alerts.save_user_alerts.assert_called()

    @pytest.mark.asyncio
    async def test_remove_non_existing_alert(
        self, mock_storage_with_alerts: MagicMock
    ) -> None:
        """Test removing a non-existing alert returns False."""
        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage_with_alerts,
        ):
            from src.telegram_bot.notifications.alerts import remove_price_alert

            result = await remove_price_alert(
                user_id=12345, alert_id="alert_non_existent"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_remove_alert_from_empty_list(self) -> None:
        """Test removing alert when no alerts exist."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "alerts": [],
            "settings": {},
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import remove_price_alert

            result = await remove_price_alert(user_id=12345, alert_id="any_id")

            assert result is False


# =============================================================================
# Test get_user_alerts function
# =============================================================================

class TestGetUserAlerts:
    """Tests for get_user_alerts function."""

    @pytest.mark.asyncio
    async def test_get_user_alerts_returns_active_only(self) -> None:
        """Test that get_user_alerts returns only active alerts."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "alerts": [
                {"id": "1", "title": "Active", "active": True},
                {"id": "2", "title": "Inactive", "active": False},
                {"id": "3", "title": "Active 2", "active": True},
            ],
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import get_user_alerts

            result = await get_user_alerts(user_id=12345)

            assert len(result) == 2
            assert all(alert["active"] for alert in result)

    @pytest.mark.asyncio
    async def test_get_user_alerts_empty_list(self) -> None:
        """Test get_user_alerts with no alerts."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {"alerts": []}

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import get_user_alerts

            result = await get_user_alerts(user_id=12345)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_user_alerts_missing_alerts_key(self) -> None:
        """Test get_user_alerts when alerts key is missing."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {"settings": {}}

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import get_user_alerts

            result = await get_user_alerts(user_id=12345)

            assert result == []


# =============================================================================
# Test update_user_settings function
# =============================================================================

class TestUpdateUserSettings:
    """Tests for update_user_settings function."""

    @pytest.mark.asyncio
    async def test_update_user_settings(self) -> None:
        """Test updating user settings."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "settings": {"enabled": True, "language": "ru"},
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import update_user_settings

            await update_user_settings(
                user_id=12345,
                settings={"language": "en", "min_interval": 600},
            )

            mock_storage.save_user_alerts.assert_called()


# =============================================================================
# Test get_user_settings function
# =============================================================================

class TestGetUserSettings:
    """Tests for get_user_settings function."""

    def test_get_user_settings_returns_existing(self) -> None:
        """Test get_user_settings returns existing settings."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "settings": {"enabled": True, "language": "en"},
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import get_user_settings

            result = get_user_settings(user_id=12345)

            assert result["enabled"] is True
            assert result["language"] == "en"

    def test_get_user_settings_returns_defaults(self) -> None:
        """Test get_user_settings returns defaults when settings missing."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {}

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import get_user_settings

            result = get_user_settings(user_id=12345)

            # Should return empty dict or defaults
            assert isinstance(result, dict)


# =============================================================================
# Test reset_daily_counter function
# =============================================================================

class TestResetDailyCounter:
    """Tests for reset_daily_counter function."""

    def test_reset_daily_counter_new_day(self) -> None:
        """Test reset_daily_counter resets on new day."""
        today = datetime.now().strftime("%Y-%m-%d")
        mock_storage = MagicMock()
        user_data: dict[str, Any] = {
            "last_day": "2020-01-01",
            "daily_notifications": 50,
        }
        mock_storage.get_user_data.return_value = user_data

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import reset_daily_counter

            reset_daily_counter(user_id=12345)

            assert user_data["last_day"] == today
            assert user_data["daily_notifications"] == 0
            mock_storage.save_user_alerts.assert_called()

    def test_reset_daily_counter_same_day(self) -> None:
        """Test reset_daily_counter does nothing on same day."""
        today = datetime.now().strftime("%Y-%m-%d")
        mock_storage = MagicMock()
        user_data: dict[str, Any] = {
            "last_day": today,
            "daily_notifications": 5,
        }
        mock_storage.get_user_data.return_value = user_data

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import reset_daily_counter

            reset_daily_counter(user_id=12345)

            # Should not reset
            assert user_data["daily_notifications"] == 5


# =============================================================================
# Test increment_notification_count function
# =============================================================================

class TestIncrementNotificationCount:
    """Tests for increment_notification_count function."""

    def test_increment_notification_count(self) -> None:
        """Test incrementing notification count."""
        mock_storage = MagicMock()
        user_data: dict[str, Any] = {
            "daily_notifications": 5,
            "last_notification": 0,
        }
        mock_storage.get_user_data.return_value = user_data

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import increment_notification_count

            increment_notification_count(user_id=12345)

            assert user_data["daily_notifications"] == 6
            assert user_data["last_notification"] > 0
            mock_storage.save_user_alerts.assert_called()

    def test_increment_from_zero(self) -> None:
        """Test incrementing from zero."""
        mock_storage = MagicMock()
        user_data: dict[str, Any] = {}
        mock_storage.get_user_data.return_value = user_data

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import increment_notification_count

            increment_notification_count(user_id=12345)

            assert user_data["daily_notifications"] == 1


# =============================================================================
# Test can_send_notification function
# =============================================================================

class TestCanSendNotification:
    """Tests for can_send_notification function."""

    def test_can_send_when_enabled(self) -> None:
        """Test can_send_notification returns True when all conditions met."""
        today = datetime.now().strftime("%Y-%m-%d")
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "settings": {
                "enabled": True,
                "max_alerts_per_day": 50,
                "quiet_hours": {"start": 23, "end": 7},
                "min_interval": 0,
            },
            "last_day": today,
            "daily_notifications": 5,
            "last_notification": 0,
        }

        with (
            patch(
                "src.telegram_bot.notifications.alerts.get_storage",
                return_value=mock_storage,
            ),
            patch(
                "src.telegram_bot.notifications.alerts.datetime",
            ) as mock_datetime,
        ):
            mock_datetime.now.return_value.strftime.return_value = today
            mock_datetime.now.return_value.hour = 12  # Midday, not quiet hours

            from src.telegram_bot.notifications.alerts import can_send_notification

            result = can_send_notification(user_id=12345)

            assert result is True

    def test_cannot_send_when_disabled(self) -> None:
        """Test can_send_notification returns False when disabled."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "settings": {"enabled": False},
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import can_send_notification

            result = can_send_notification(user_id=12345)

            assert result is False

    def test_cannot_send_daily_limit_reached(self) -> None:
        """Test can_send_notification returns False when daily limit reached."""
        today = datetime.now().strftime("%Y-%m-%d")
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = {
            "settings": {
                "enabled": True,
                "max_alerts_per_day": 10,
                "quiet_hours": {"start": 23, "end": 7},
            },
            "last_day": today,
            "daily_notifications": 10,  # Limit reached
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import can_send_notification

            result = can_send_notification(user_id=12345)

            assert result is False


# =============================================================================
# Integration tests
# =============================================================================

class TestAlertsIntegration:
    """Integration tests for alerts module."""

    @pytest.mark.asyncio
    async def test_add_and_get_alerts_flow(self) -> None:
        """Test complete flow: add alert, get alerts, remove alert."""
        mock_storage = MagicMock()
        user_alerts: list[dict[str, Any]] = []
        mock_storage.get_user_data.return_value = {
            "alerts": user_alerts,
            "settings": {},
        }

        with patch(
            "src.telegram_bot.notifications.alerts.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.alerts import (
                add_price_alert,
                get_user_alerts,
            )

            # Add alert
            alert = await add_price_alert(
                user_id=12345,
                item_id="item_test",
                title="Test Item",
                game="csgo",
                alert_type="price_drop",
                threshold=10.0,
            )

            # Get alerts
            alerts = await get_user_alerts(user_id=12345)

            assert len(alerts) == 1
            assert alerts[0]["id"] == alert["id"]

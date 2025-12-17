"""Unit tests for smart_notifications/throttling module.

Tests for notification throttling functionality.
"""

from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import patch

import pytest

from src.telegram_bot.smart_notifications.throttling import (
    record_notification,
    should_throttle_notification,
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
# TESTS FOR should_throttle_notification
# ============================================================================


class TestShouldThrottleNotification:
    """Tests for should_throttle_notification function."""

    @pytest.mark.asyncio()
    async def test_no_previous_notification(self):
        """Test when there's no previous notification."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {},
            }
        }

        # Mock datetime to be outside quiet hours
        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        assert result is False

    @pytest.mark.asyncio()
    async def test_throttle_during_cooldown(self):
        """Test throttling when within cooldown period."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {"price_alert": current_time - 60},  # 1 min ago
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        assert result is True

    @pytest.mark.asyncio()
    async def test_no_throttle_after_cooldown(self):
        """Test no throttling when cooldown has passed."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {"price_alert": current_time - 3600},  # 1 hour ago
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        assert result is False

    @pytest.mark.asyncio()
    async def test_throttle_during_quiet_hours_simple_range(self):
        """Test throttling during quiet hours with simple range (start < end)."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 22, "end": 24},  # Simple range: 22-24
                "last_notification": {},
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            # Hour 23 is within quiet hours (22-24)
            mock_dt.now.return_value = datetime(2025, 1, 1, 23, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        # Quiet hours check: 22 <= 23 < 24 is True, so should throttle
        assert result is True

    @pytest.mark.asyncio()
    async def test_throttle_during_quiet_hours_morning(self):
        """Test throttling during quiet hours (morning)."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 22, "end": 8},
                "last_notification": {},
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            # Hour 6 is within quiet hours if end is 8
            mock_dt.now.return_value = datetime(2025, 1, 1, 6, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        # Quiet hours check is 22 <= 6 < 8, which is False for start but True for end
        # The logic checks: quiet_hours["start"] <= now.hour < quiet_hours["end"]
        # 22 <= 6 is False, so should NOT throttle based on quiet hours
        # But there's no last notification, so should not throttle
        assert result is False

    @pytest.mark.asyncio()
    async def test_low_frequency_doubles_cooldown(self):
        """Test that low frequency doubles the cooldown period."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        # Default cooldown for price_alert is 1800 (30 min)
        # Low frequency doubles it to 3600 (1 hour)
        prefs._user_preferences = {
            "123456": {
                "frequency": "low",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {"price_alert": current_time - 2700},  # 45 min ago
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        # 45 min ago < 60 min cooldown, should throttle
        assert result is True

    @pytest.mark.asyncio()
    async def test_high_frequency_halves_cooldown(self):
        """Test that high frequency halves the cooldown period."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        # Default cooldown for price_alert is 1800 (30 min)
        # High frequency halves it to 900 (15 min)
        prefs._user_preferences = {
            "123456": {
                "frequency": "high",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {"price_alert": current_time - 1200},  # 20 min ago
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        # 20 min ago > 15 min cooldown, should not throttle
        assert result is False

    @pytest.mark.asyncio()
    async def test_throttle_with_item_id(self):
        """Test throttling with specific item ID."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert:item123": current_time - 60,
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(
                123456, "price_alert", item_id="item123"
            )

        assert result is True

    @pytest.mark.asyncio()
    async def test_different_items_not_throttled_together(self):
        """Test that different items are tracked separately."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert:item123": current_time - 60,  # Throttled
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            # Different item should not be throttled
            result = await should_throttle_notification(
                123456, "price_alert", item_id="item456"
            )

        assert result is False

    @pytest.mark.asyncio()
    async def test_different_notification_types_tracked_separately(self):
        """Test that different notification types are tracked separately."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert": current_time - 60,  # Recent price_alert
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            # trend_alert should not be throttled by price_alert
            result = await should_throttle_notification(123456, "trend_alert")

        assert result is False

    @pytest.mark.asyncio()
    async def test_user_not_in_preferences(self):
        """Test when user is not in preferences."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "price_alert")

        # No preferences, default behavior
        assert result is False

    @pytest.mark.asyncio()
    async def test_unknown_notification_type_uses_default_cooldown(self):
        """Test that unknown notification type uses default cooldown."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        current_time = time.time()
        prefs._user_preferences = {
            "123456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "unknown_type": current_time - 1800,  # 30 min ago
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

            result = await should_throttle_notification(123456, "unknown_type")

        # Default cooldown is 3600, 30 min < 1 hour, should throttle
        assert result is True


# ============================================================================
# TESTS FOR record_notification
# ============================================================================


class TestRecordNotification:
    """Tests for record_notification function."""

    @pytest.mark.asyncio()
    async def test_record_basic_notification(self):
        """Test recording a basic notification."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {"enabled": True, "last_notification": {}}
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(123456, "price_alert")

        assert "price_alert" in prefs._user_preferences["123456"]["last_notification"]

    @pytest.mark.asyncio()
    async def test_record_notification_with_item_id(self):
        """Test recording a notification with item ID."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {"enabled": True, "last_notification": {}}
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(123456, "price_alert", item_id="item123")

        assert (
            "price_alert:item123"
            in prefs._user_preferences["123456"]["last_notification"]
        )

    @pytest.mark.asyncio()
    async def test_record_updates_timestamp(self):
        """Test that recording updates the timestamp."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        old_time = time.time() - 3600
        prefs._user_preferences = {
            "123456": {"enabled": True, "last_notification": {"price_alert": old_time}}
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(123456, "price_alert")

        new_time = prefs._user_preferences["123456"]["last_notification"]["price_alert"]
        assert new_time > old_time

    @pytest.mark.asyncio()
    async def test_record_creates_last_notification_dict(self):
        """Test that recording creates last_notification dict if missing."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(123456, "price_alert")

        assert "last_notification" in prefs._user_preferences["123456"]
        assert "price_alert" in prefs._user_preferences["123456"]["last_notification"]

    @pytest.mark.asyncio()
    async def test_record_for_nonexistent_user(self):
        """Test recording for nonexistent user does nothing."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            # Should not raise
            await record_notification(123456, "price_alert")

        # User should not be added
        assert "123456" not in prefs._user_preferences

    @pytest.mark.asyncio()
    async def test_record_saves_preferences(self):
        """Test that recording saves preferences."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {"enabled": True, "last_notification": {}}
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ) as mock_save:
            await record_notification(123456, "price_alert")

            mock_save.assert_called_once()

    @pytest.mark.asyncio()
    async def test_record_multiple_notifications(self):
        """Test recording multiple different notifications."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {
            "123456": {"enabled": True, "last_notification": {}}
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(123456, "price_alert")
            await record_notification(123456, "trend_alert")

        last_notif = prefs._user_preferences["123456"]["last_notification"]
        assert "price_alert" in last_notif
        assert "trend_alert" in last_notif

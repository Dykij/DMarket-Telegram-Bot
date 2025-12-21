"""Tests for smart_notifications/throttling.py module.

Covers:
- should_throttle_notification function
- record_notification function
- Cooldown period calculations
- Quiet hours handling
- Frequency settings
"""

from datetime import datetime
import time
from unittest.mock import MagicMock, patch

import pytest

from src.telegram_bot.smart_notifications.throttling import (
    record_notification,
    should_throttle_notification,
)


class TestShouldThrottleNotification:
    """Tests for should_throttle_notification function."""

    @pytest.mark.asyncio
    async def test_throttle_within_cooldown(self) -> None:
        """Test throttling when within cooldown period."""
        user_prefs = {
            "123": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert": time.time() - 60,  # 1 minute ago
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)  # Noon, not quiet hours

            result = await should_throttle_notification(
                user_id=123,
                notification_type="price_alert",
            )

            # Should be throttled (1 minute < 30 minute cooldown)
            assert result is True

    @pytest.mark.asyncio
    async def test_no_throttle_after_cooldown(self) -> None:
        """Test no throttling after cooldown period."""
        user_prefs = {
            "456": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert": time.time() - 7200,  # 2 hours ago
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            result = await should_throttle_notification(
                user_id=456,
                notification_type="price_alert",
            )

            # Should not be throttled (2 hours > 30 minute cooldown)
            assert result is False

    @pytest.mark.asyncio
    async def test_throttle_during_quiet_hours(self) -> None:
        """Test throttling during quiet hours."""
        user_prefs = {
            "789": {
                "frequency": "normal",
                "quiet_hours": {"start": 0, "end": 8},  # Quiet hours from midnight to 8am
                "last_notification": {},
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            # Set time to quiet hours (2 AM is between 0 and 8)
            mock_now = MagicMock()
            mock_now.hour = 2
            mock_dt.now.return_value = mock_now

            result = await should_throttle_notification(
                user_id=789,
                notification_type="price_alert",
            )

            # Should be throttled during quiet hours
            assert result is True

    @pytest.mark.asyncio
    async def test_frequency_low_doubles_cooldown(self) -> None:
        """Test that low frequency doubles cooldown."""
        user_prefs = {
            "100": {
                "frequency": "low",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert": time.time() - 2400,  # 40 minutes ago
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            result = await should_throttle_notification(
                user_id=100,
                notification_type="price_alert",
            )

            # Low frequency: 30 min * 2 = 60 min cooldown
            # 40 min < 60 min, so should be throttled
            assert result is True

    @pytest.mark.asyncio
    async def test_frequency_high_halves_cooldown(self) -> None:
        """Test that high frequency halves cooldown."""
        user_prefs = {
            "200": {
                "frequency": "high",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert": time.time() - 1200,  # 20 minutes ago
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            result = await should_throttle_notification(
                user_id=200,
                notification_type="price_alert",
            )

            # High frequency: 30 min / 2 = 15 min cooldown
            # 20 min > 15 min, so should not be throttled
            assert result is False

    @pytest.mark.asyncio
    async def test_throttle_with_item_id(self) -> None:
        """Test throttling with specific item_id."""
        user_prefs = {
            "300": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert:item_123": time.time() - 60,  # 1 min ago for this item
                    "price_alert:item_456": time.time() - 7200,  # 2 hours ago for other
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            # Item 123 should be throttled
            result_123 = await should_throttle_notification(
                user_id=300,
                notification_type="price_alert",
                item_id="item_123",
            )
            assert result_123 is True

            # Item 456 should not be throttled
            result_456 = await should_throttle_notification(
                user_id=300,
                notification_type="price_alert",
                item_id="item_456",
            )
            assert result_456 is False

    @pytest.mark.asyncio
    async def test_new_user_no_throttle(self) -> None:
        """Test that new user without history is not throttled."""
        user_prefs: dict = {}  # No user data

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            result = await should_throttle_notification(
                user_id=999,
                notification_type="price_alert",
            )

            # New user with no history should not be throttled
            assert result is False

    @pytest.mark.asyncio
    async def test_different_notification_types_independent(self) -> None:
        """Test that different notification types have independent cooldowns."""
        user_prefs = {
            "400": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    "price_alert": time.time() - 60,  # 1 min ago
                    "trend_alert": time.time() - 10000,  # Long ago
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            # Price alert should be throttled
            price_result = await should_throttle_notification(
                user_id=400, notification_type="price_alert"
            )
            assert price_result is True

            # Trend alert should not be throttled
            trend_result = await should_throttle_notification(
                user_id=400, notification_type="trend_alert"
            )
            assert trend_result is False


class TestRecordNotification:
    """Tests for record_notification function."""

    @pytest.mark.asyncio
    async def test_record_notification_basic(self) -> None:
        """Test recording a basic notification."""
        user_prefs = {"500": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ) as mock_save:
            await record_notification(
                user_id=500,
                notification_type="price_alert",
            )

            # Should add last_notification entry
            assert "last_notification" in user_prefs["500"]
            assert "price_alert" in user_prefs["500"]["last_notification"]
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_notification_with_item_id(self) -> None:
        """Test recording notification with item_id."""
        user_prefs = {"600": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(
                user_id=600,
                notification_type="price_alert",
                item_id="item_789",
            )

            # Should use compound key
            assert "price_alert:item_789" in user_prefs["600"]["last_notification"]

    @pytest.mark.asyncio
    async def test_record_notification_unknown_user(self) -> None:
        """Test recording notification for unknown user does nothing."""
        user_prefs: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ) as mock_save:
            await record_notification(
                user_id=999,
                notification_type="price_alert",
            )

            # Should not save for unknown user
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_notification_updates_timestamp(self) -> None:
        """Test that recording updates timestamp."""
        old_time = time.time() - 3600  # 1 hour ago
        user_prefs = {
            "700": {
                "enabled": True,
                "last_notification": {"price_alert": old_time},
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ):
            await record_notification(user_id=700, notification_type="price_alert")

            new_time = user_prefs["700"]["last_notification"]["price_alert"]
            # New time should be more recent
            assert new_time > old_time


class TestThrottlingIntegration:
    """Integration tests for throttling module."""

    @pytest.mark.asyncio
    async def test_record_then_check_throttle(self) -> None:
        """Test recording notification then checking throttle."""
        user_prefs = {"800": {"frequency": "normal", "quiet_hours": {"start": 23, "end": 8}}}

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.save_user_preferences"
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            # First check - not throttled
            should_throttle_1 = await should_throttle_notification(
                user_id=800, notification_type="price_alert"
            )
            assert should_throttle_1 is False

            # Record notification
            await record_notification(user_id=800, notification_type="price_alert")

            # Second check - should be throttled
            should_throttle_2 = await should_throttle_notification(
                user_id=800, notification_type="price_alert"
            )
            assert should_throttle_2 is True


class TestCooldownConstants:
    """Tests for cooldown period handling."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "notification_type,expected_base_cooldown",
        [
            ("market_opportunity", 3600),  # 1 hour
            ("price_alert", 1800),  # 30 minutes
            ("trend_alert", 7200),  # 2 hours
            ("pattern_alert", 3600),  # 1 hour
            ("watchlist_update", 14400),  # 4 hours
            ("arbitrage_opportunity", 900),  # 15 minutes
            ("system_alert", 300),  # 5 minutes
        ],
    )
    async def test_cooldown_types(
        self, notification_type: str, expected_base_cooldown: int
    ) -> None:
        """Test different notification types have correct cooldowns."""
        # Just after cooldown should not be throttled
        user_prefs = {
            "900": {
                "frequency": "normal",
                "quiet_hours": {"start": 23, "end": 8},
                "last_notification": {
                    notification_type: time.time() - expected_base_cooldown - 60
                },
            }
        }

        with patch(
            "src.telegram_bot.smart_notifications.throttling.get_user_preferences",
            return_value=user_prefs,
        ), patch(
            "src.telegram_bot.smart_notifications.throttling.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)

            result = await should_throttle_notification(
                user_id=900, notification_type=notification_type
            )

            # Should not be throttled after cooldown + 1 min
            assert result is False

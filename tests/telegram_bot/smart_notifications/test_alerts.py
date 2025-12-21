"""Tests for smart_notifications/alerts.py module.

Covers:
- create_alert function
- deactivate_alert function
- get_user_alerts function
- Alert ID generation
- User registration flow
- Alert data structure
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from src.telegram_bot.smart_notifications.alerts import (
    create_alert,
    deactivate_alert,
    get_user_alerts,
)


class TestCreateAlert:
    """Tests for create_alert function."""

    @pytest.mark.asyncio
    async def test_create_alert_basic(self) -> None:
        """Test creating a basic alert."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ) as mock_register, patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ) as mock_save:
            mock_active.return_value = {}
            mock_prefs.return_value = {"123": {"enabled": True}}
            mock_register.return_value = None

            alert_id = await create_alert(
                user_id=123,
                alert_type="price_alert",
                item_id="item_123",
                item_name="Test Item",
                game="csgo",
            )

            assert alert_id is not None
            assert isinstance(alert_id, str)
            # UUID format check
            try:
                uuid.UUID(alert_id)
            except ValueError:
                pytest.fail("Alert ID is not a valid UUID")
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_alert_registers_new_user(self) -> None:
        """Test that create_alert registers new users."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ) as mock_register, patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            mock_active.return_value = {}
            mock_prefs.return_value = {}  # User not registered

            await create_alert(user_id=456, alert_type="price_alert")

            mock_register.assert_called_once_with(456)

    @pytest.mark.asyncio
    async def test_create_alert_with_conditions(self) -> None:
        """Test creating alert with conditions."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            active_alerts: dict = {}
            mock_active.return_value = active_alerts
            mock_prefs.return_value = {"789": {"enabled": True}}

            conditions = {"price": 100.0, "direction": "below"}
            await create_alert(
                user_id=789,
                alert_type="price_alert",
                item_id="item_001",
                conditions=conditions,
            )

            # Check alert was added with conditions
            assert "789" in active_alerts
            assert len(active_alerts["789"]) == 1
            alert = active_alerts["789"][0]
            assert alert["conditions"] == conditions

    @pytest.mark.asyncio
    async def test_create_alert_one_time(self) -> None:
        """Test creating one-time alert."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            active_alerts: dict = {}
            mock_active.return_value = active_alerts
            mock_prefs.return_value = {"100": {"enabled": True}}

            await create_alert(
                user_id=100,
                alert_type="trend_alert",
                one_time=True,
            )

            assert active_alerts["100"][0]["one_time"] is True

    @pytest.mark.asyncio
    async def test_create_alert_data_structure(self) -> None:
        """Test alert data structure contains all required fields."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            active_alerts: dict = {}
            mock_active.return_value = active_alerts
            mock_prefs.return_value = {"200": {"enabled": True}}

            await create_alert(
                user_id=200,
                alert_type="market_opportunity",
                item_id="item_200",
                item_name="Market Item",
                game="dota2",
                conditions={"min_profit": 10.0},
                one_time=False,
            )

            alert = active_alerts["200"][0]
            required_fields = [
                "id",
                "user_id",
                "type",
                "item_id",
                "item_name",
                "game",
                "conditions",
                "one_time",
                "created_at",
                "last_triggered",
                "trigger_count",
                "active",
            ]
            for field in required_fields:
                assert field in alert, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_create_alert_default_game(self) -> None:
        """Test alert uses default game 'csgo'."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            active_alerts: dict = {}
            mock_active.return_value = active_alerts
            mock_prefs.return_value = {"300": {"enabled": True}}

            await create_alert(user_id=300, alert_type="price_alert")

            assert active_alerts["300"][0]["game"] == "csgo"

    @pytest.mark.asyncio
    async def test_create_multiple_alerts_for_user(self) -> None:
        """Test creating multiple alerts for the same user."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences"
        ) as mock_prefs, patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            active_alerts: dict = {}
            mock_active.return_value = active_alerts
            mock_prefs.return_value = {"400": {"enabled": True}}

            await create_alert(user_id=400, alert_type="price_alert", item_id="item_1")
            await create_alert(user_id=400, alert_type="price_alert", item_id="item_2")
            await create_alert(user_id=400, alert_type="trend_alert", item_id="item_3")

            assert len(active_alerts["400"]) == 3


class TestDeactivateAlert:
    """Tests for deactivate_alert function."""

    @pytest.mark.asyncio
    async def test_deactivate_alert_success(self) -> None:
        """Test successfully deactivating an alert."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ) as mock_save:
            alert_id = "test-alert-123"
            mock_active.return_value = {
                "500": [
                    {"id": alert_id, "active": True, "type": "price_alert"},
                ]
            }

            result = await deactivate_alert(user_id=500, alert_id=alert_id)

            assert result is True
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_alert_user_not_found(self) -> None:
        """Test deactivating alert for non-existent user."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active:
            mock_active.return_value = {}

            result = await deactivate_alert(user_id=999, alert_id="any-id")

            assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_alert_not_found(self) -> None:
        """Test deactivating non-existent alert."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active:
            mock_active.return_value = {
                "600": [
                    {"id": "existing-alert", "active": True},
                ]
            }

            result = await deactivate_alert(user_id=600, alert_id="non-existent")

            assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_alert_sets_inactive(self) -> None:
        """Test that deactivate_alert sets active=False."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active, patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            alert_id = "alert-to-deactivate"
            alerts = {"700": [{"id": alert_id, "active": True}]}
            mock_active.return_value = alerts

            await deactivate_alert(user_id=700, alert_id=alert_id)

            assert alerts["700"][0]["active"] is False


class TestGetUserAlerts:
    """Tests for get_user_alerts function."""

    @pytest.mark.asyncio
    async def test_get_user_alerts_returns_active_only(self) -> None:
        """Test get_user_alerts returns only active alerts."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active:
            mock_active.return_value = {
                "800": [
                    {"id": "1", "active": True, "type": "price_alert"},
                    {"id": "2", "active": False, "type": "price_alert"},
                    {"id": "3", "active": True, "type": "trend_alert"},
                ]
            }

            alerts = await get_user_alerts(user_id=800)

            assert len(alerts) == 2
            assert all(a["active"] for a in alerts)

    @pytest.mark.asyncio
    async def test_get_user_alerts_user_not_found(self) -> None:
        """Test get_user_alerts returns empty list for unknown user."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active:
            mock_active.return_value = {}

            alerts = await get_user_alerts(user_id=999)

            assert alerts == []

    @pytest.mark.asyncio
    async def test_get_user_alerts_all_inactive(self) -> None:
        """Test get_user_alerts returns empty when all alerts inactive."""
        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts"
        ) as mock_active:
            mock_active.return_value = {
                "900": [
                    {"id": "1", "active": False},
                    {"id": "2", "active": False},
                ]
            }

            alerts = await get_user_alerts(user_id=900)

            assert alerts == []


class TestAlertIntegration:
    """Integration tests for alert functions."""

    @pytest.mark.asyncio
    async def test_create_and_deactivate_alert(self) -> None:
        """Test creating and then deactivating an alert."""
        active_alerts: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts",
            return_value=active_alerts,
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences",
            return_value={"1000": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            # Create alert
            alert_id = await create_alert(
                user_id=1000,
                alert_type="price_alert",
                item_name="Integration Test Item",
            )

            # Verify alert is active
            assert active_alerts["1000"][0]["active"] is True

            # Deactivate alert
            result = await deactivate_alert(user_id=1000, alert_id=alert_id)

            # Verify deactivation
            assert result is True
            assert active_alerts["1000"][0]["active"] is False

    @pytest.mark.asyncio
    async def test_create_and_get_alerts(self) -> None:
        """Test creating alerts and retrieving them."""
        active_alerts: dict = {}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.get_active_alerts",
            return_value=active_alerts,
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.get_user_preferences",
            return_value={"1100": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.register_user"
        ), patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            # Create multiple alerts
            await create_alert(user_id=1100, alert_type="price_alert", item_id="item_1")
            await create_alert(user_id=1100, alert_type="trend_alert", item_id="item_2")

            # Get alerts
            alerts = await get_user_alerts(user_id=1100)

            assert len(alerts) == 2

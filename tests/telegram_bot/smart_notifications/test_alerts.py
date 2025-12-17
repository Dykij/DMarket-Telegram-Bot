"""Unit tests for smart_notifications/alerts module.

Tests for alert management functionality.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.telegram_bot.smart_notifications.alerts import (
    create_alert,
    deactivate_alert,
    get_user_alerts,
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
# TESTS FOR create_alert
# ============================================================================


class TestCreateAlert:
    """Tests for create_alert function."""

    @pytest.mark.asyncio()
    async def test_create_basic_alert(self):
        """Test creating a basic alert."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            alert_id = await create_alert(
                user_id=123456,
                alert_type="price_alert",
                item_id="item123",
                item_name="Test Item",
                game="csgo",
            )

        assert alert_id is not None
        assert len(prefs._active_alerts["123456"]) == 1
        assert prefs._active_alerts["123456"][0]["type"] == "price_alert"

    @pytest.mark.asyncio()
    async def test_create_alert_with_conditions(self):
        """Test creating an alert with conditions."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        conditions = {"price": 10.0, "direction": "below"}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            alert_id = await create_alert(
                user_id=123456,
                alert_type="price_alert",
                item_id="item123",
                conditions=conditions,
            )

        alert = prefs._active_alerts["123456"][0]
        assert alert["conditions"] == conditions

    @pytest.mark.asyncio()
    async def test_create_one_time_alert(self):
        """Test creating a one-time alert."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            await create_alert(
                user_id=123456,
                alert_type="price_alert",
                one_time=True,
            )

        alert = prefs._active_alerts["123456"][0]
        assert alert["one_time"] is True

    @pytest.mark.asyncio()
    async def test_create_alert_registers_new_user(self):
        """Test that creating alert for new user registers them first."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            with patch(
                "src.telegram_bot.smart_notifications.alerts.register_user",
                new_callable=AsyncMock,
            ) as mock_register:
                await create_alert(
                    user_id=123456,
                    alert_type="price_alert",
                )

                mock_register.assert_called_once_with(123456)

    @pytest.mark.asyncio()
    async def test_create_multiple_alerts(self):
        """Test creating multiple alerts for same user."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            await create_alert(user_id=123456, alert_type="price_alert")
            await create_alert(user_id=123456, alert_type="trend_alert")

        assert len(prefs._active_alerts["123456"]) == 2

    @pytest.mark.asyncio()
    async def test_create_alert_returns_unique_id(self):
        """Test that each alert gets a unique ID."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            id1 = await create_alert(user_id=123456, alert_type="price_alert")
            id2 = await create_alert(user_id=123456, alert_type="price_alert")

        assert id1 != id2

    @pytest.mark.asyncio()
    async def test_create_alert_default_values(self):
        """Test alert is created with default values."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            await create_alert(user_id=123456, alert_type="price_alert")

        alert = prefs._active_alerts["123456"][0]
        assert alert["active"] is True
        assert alert["trigger_count"] == 0
        assert alert["last_triggered"] is None
        assert alert["game"] == "csgo"

    @pytest.mark.asyncio()
    async def test_create_alert_different_games(self):
        """Test creating alerts for different games."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._user_preferences = {"123456": {"enabled": True}}

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            await create_alert(user_id=123456, alert_type="price_alert", game="csgo")
            await create_alert(user_id=123456, alert_type="price_alert", game="dota2")

        alerts = prefs._active_alerts["123456"]
        games = [a["game"] for a in alerts]
        assert "csgo" in games
        assert "dota2" in games


# ============================================================================
# TESTS FOR deactivate_alert
# ============================================================================


class TestDeactivateAlert:
    """Tests for deactivate_alert function."""

    @pytest.mark.asyncio()
    async def test_deactivate_existing_alert(self):
        """Test deactivating an existing alert."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {
            "123456": [{"id": "alert1", "active": True}]
        }

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            result = await deactivate_alert(123456, "alert1")

        assert result is True
        assert prefs._active_alerts["123456"][0]["active"] is False

    @pytest.mark.asyncio()
    async def test_deactivate_nonexistent_alert(self):
        """Test deactivating a nonexistent alert."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {
            "123456": [{"id": "alert1", "active": True}]
        }

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            result = await deactivate_alert(123456, "nonexistent")

        assert result is False

    @pytest.mark.asyncio()
    async def test_deactivate_for_nonexistent_user(self):
        """Test deactivating alert for nonexistent user."""
        result = await deactivate_alert(123456, "alert1")
        assert result is False

    @pytest.mark.asyncio()
    async def test_deactivate_preserves_other_alerts(self):
        """Test that deactivating one alert preserves others."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {
            "123456": [
                {"id": "alert1", "active": True},
                {"id": "alert2", "active": True},
            ]
        }

        with patch(
            "src.telegram_bot.smart_notifications.alerts.save_user_preferences"
        ):
            await deactivate_alert(123456, "alert1")

        assert prefs._active_alerts["123456"][0]["active"] is False
        assert prefs._active_alerts["123456"][1]["active"] is True


# ============================================================================
# TESTS FOR get_user_alerts
# ============================================================================


class TestGetUserAlerts:
    """Tests for get_user_alerts function."""

    @pytest.mark.asyncio()
    async def test_get_alerts_for_existing_user(self):
        """Test getting alerts for existing user."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {
            "123456": [
                {"id": "alert1", "active": True, "type": "price_alert"},
                {"id": "alert2", "active": True, "type": "trend_alert"},
            ]
        }

        result = await get_user_alerts(123456)

        assert len(result) == 2

    @pytest.mark.asyncio()
    async def test_get_alerts_for_nonexistent_user(self):
        """Test getting alerts for nonexistent user."""
        result = await get_user_alerts(123456)
        assert result == []

    @pytest.mark.asyncio()
    async def test_get_alerts_filters_inactive(self):
        """Test that inactive alerts are filtered out."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {
            "123456": [
                {"id": "alert1", "active": True},
                {"id": "alert2", "active": False},
                {"id": "alert3", "active": True},
            ]
        }

        result = await get_user_alerts(123456)

        assert len(result) == 2
        assert all(a["active"] for a in result)

    @pytest.mark.asyncio()
    async def test_get_alerts_returns_list(self):
        """Test that function returns a list."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {"123456": []}

        result = await get_user_alerts(123456)

        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_get_alerts_all_inactive(self):
        """Test getting alerts when all are inactive."""
        import src.telegram_bot.smart_notifications.preferences as prefs

        prefs._active_alerts = {
            "123456": [
                {"id": "alert1", "active": False},
                {"id": "alert2", "active": False},
            ]
        }

        result = await get_user_alerts(123456)

        assert result == []

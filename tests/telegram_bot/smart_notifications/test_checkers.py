"""Unit tests for smart_notifications/checkers module.

Tests for notification checking functions that scan for
price alerts and market opportunities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api() -> AsyncMock:
    """Create a mock DMarketAPI client."""
    api = AsyncMock()
    api.get_market_items = AsyncMock(return_value={"objects": []})
    return api


@pytest.fixture
def mock_bot() -> MagicMock:
    """Create a mock Telegram Bot."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_notification_queue() -> MagicMock:
    """Create a mock NotificationQueue."""
    queue = MagicMock()
    queue.add = AsyncMock()
    return queue


@pytest.fixture
def sample_alert() -> dict[str, Any]:
    """Create a sample alert."""
    return {
        "id": "alert_1",
        "item_id": "item_123",
        "game": "csgo",
        "type": "price_alert",
        "active": True,
        "conditions": {
            "price": 10.0,
            "direction": "below",
        },
        "last_triggered": None,
        "trigger_count": 0,
        "one_time": False,
    }


@pytest.fixture
def sample_market_item() -> dict[str, Any]:
    """Create a sample market item."""
    return {
        "itemId": "item_123",
        "title": "AK-47 | Redline",
        "price": {"USD": "900"},  # $9.00 in cents
        "suggestedPrice": {"USD": "1100"},  # $11.00
        "extra": {
            "offersCount": 50,
            "ordersCount": 25,
        },
    }


@pytest.fixture
def sample_user_preferences() -> dict[str, Any]:
    """Create sample user preferences."""
    return {
        "enabled": True,
        "notifications": {
            "price_alert": True,
            "market_opportunity": True,
        },
        "games": {
            "csgo": True,
            "dota2": False,
            "tf2": False,
            "rust": False,
        },
    }


# ============================================================================
# Tests for check_price_alerts
# ============================================================================


class TestCheckPriceAlerts:
    """Tests for check_price_alerts function."""

    @pytest.mark.asyncio
    async def test_check_price_alerts_no_active_alerts(
        self, mock_api: AsyncMock, mock_bot: MagicMock
    ) -> None:
        """Test check_price_alerts with no active alerts."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={},
            ):
                await check_price_alerts(mock_api, mock_bot)

        # No API calls should be made
        mock_api.get_market_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_price_alerts_user_disabled(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
    ) -> None:
        """Test check_price_alerts with disabled user preferences."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [sample_alert]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": {"enabled": False}},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                ):
                    await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio
    async def test_check_price_alerts_alert_triggered_below(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_market_item: dict[str, Any],
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts when alert condition is met (below)."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        # Set threshold above current price so alert triggers
        sample_alert["conditions"]["price"] = 15.0  # $15
        sample_alert["conditions"]["direction"] = "below"

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [sample_alert]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={"item_123": sample_market_item},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=9.0,  # $9.00
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification"
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(mock_api, mock_bot)

                        # Notification should be sent
                        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_price_alerts_alert_not_triggered(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_market_item: dict[str, Any],
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts when alert condition is not met."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        # Set threshold below current price so alert doesn't trigger
        sample_alert["conditions"]["price"] = 5.0  # $5
        sample_alert["conditions"]["direction"] = "below"

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [sample_alert]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={"item_123": sample_market_item},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=9.0,  # $9.00 - above threshold
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification"
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(mock_api, mock_bot)

                        # Notification should not be sent
                        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_price_alerts_alert_triggered_above(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_market_item: dict[str, Any],
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts when alert condition is met (above)."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        # Set threshold below current price with direction "above"
        sample_alert["conditions"]["price"] = 5.0  # $5
        sample_alert["conditions"]["direction"] = "above"

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [sample_alert]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={"item_123": sample_market_item},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=9.0,  # $9.00 - above threshold
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification"
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(mock_api, mock_bot)

                        # Notification should be sent
                        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_price_alerts_one_time_deactivated(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_market_item: dict[str, Any],
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test that one-time alerts are deactivated after triggering."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        sample_alert["one_time"] = True
        sample_alert["conditions"]["price"] = 15.0
        sample_alert["conditions"]["direction"] = "below"

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [sample_alert]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={"item_123": sample_market_item},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=9.0,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification"
                        ):
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(mock_api, mock_bot)

        # Alert should be deactivated
        assert sample_alert["active"] is False

    @pytest.mark.asyncio
    async def test_check_price_alerts_handles_api_error(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts handles API errors gracefully."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts
        from src.utils.exceptions import APIError

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [sample_alert]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    side_effect=APIError("API Error"),
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                    ):
                        # Should not raise
                        await check_price_alerts(mock_api, mock_bot)


# ============================================================================
# Tests for check_market_opportunities
# ============================================================================


class TestCheckMarketOpportunities:
    """Tests for check_market_opportunities function."""

    @pytest.mark.asyncio
    async def test_check_market_opportunities_no_interested_users(
        self, mock_api: AsyncMock, mock_bot: MagicMock
    ) -> None:
        """Test check_market_opportunities with no interested users."""
        from src.telegram_bot.smart_notifications.checkers import (
            check_market_opportunities,
        )

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={},
        ):
            await check_market_opportunities(mock_api, mock_bot)

        # No market items should be fetched
        mock_api.get_market_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_market_opportunities_user_disabled(
        self, mock_api: AsyncMock, mock_bot: MagicMock
    ) -> None:
        """Test check_market_opportunities with disabled user."""
        from src.telegram_bot.smart_notifications.checkers import (
            check_market_opportunities,
        )

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"123": {"enabled": False}},
        ):
            await check_market_opportunities(mock_api, mock_bot)

        # No market items should be fetched
        mock_api.get_market_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_market_opportunities_no_market_items(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_market_opportunities with no market items."""
        from src.telegram_bot.smart_notifications.checkers import (
            check_market_opportunities,
        )

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"123": sample_user_preferences},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                return_value=[],
            ):
                await check_market_opportunities(mock_api, mock_bot)

    @pytest.mark.asyncio
    async def test_check_market_opportunities_with_opportunities(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_user_preferences: dict[str, Any],
        sample_market_item: dict[str, Any],
    ) -> None:
        """Test check_market_opportunities finds opportunities."""
        from src.telegram_bot.smart_notifications.checkers import (
            check_market_opportunities,
        )

        mock_opportunity = {
            "opportunity_score": 75,
            "type": "arbitrage",
            "item": sample_market_item,
        }

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"123": sample_user_preferences},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                return_value=[sample_market_item],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_price_history_for_items",
                    return_value={"item_123": [{"price": 900, "timestamp": 1000}]},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.analyze_market_opportunity",
                        return_value=mock_opportunity,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_market_opportunity_notification"
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.should_throttle_notification",
                                return_value=False,
                            ):
                                await check_market_opportunities(mock_api, mock_bot)


# ============================================================================
# Tests for Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_check_alerts_empty_item_id(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts with empty item_id."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        alert_with_empty_id = {
            "id": "alert_1",
            "item_id": "",
            "game": "csgo",
            "type": "price_alert",
            "active": True,
            "conditions": {"price": 10.0, "direction": "below"},
            "last_triggered": None,
            "trigger_count": 0,
        }

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [alert_with_empty_id]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                    ):
                        # Should not raise
                        await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio
    async def test_check_alerts_missing_conditions(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts with missing conditions."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        alert_without_conditions = {
            "id": "alert_1",
            "item_id": "item_123",
            "game": "csgo",
            "type": "price_alert",
            "active": True,
            "conditions": {},  # Empty conditions
            "last_triggered": None,
            "trigger_count": 0,
        }

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"123": [alert_without_conditions]},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={"123": sample_user_preferences},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={"item_123": {"price": {"USD": "900"}}},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=9.0,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                        ):
                            # Should not raise
                            await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio
    async def test_multiple_users_multiple_alerts(
        self,
        mock_api: AsyncMock,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_market_item: dict[str, Any],
        sample_user_preferences: dict[str, Any],
    ) -> None:
        """Test check_price_alerts with multiple users and alerts."""
        from src.telegram_bot.smart_notifications.checkers import check_price_alerts

        alert1 = sample_alert.copy()
        alert1["conditions"]["price"] = 15.0

        alert2 = sample_alert.copy()
        alert2["id"] = "alert_2"
        alert2["conditions"]["price"] = 15.0

        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "123": [alert1],
                "456": [alert2],
            },
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={
                    "123": sample_user_preferences,
                    "456": sample_user_preferences,
                },
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value={"item_123": sample_market_item},
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=9.0,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification"
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(mock_api, mock_bot)

                        # Both users should receive notifications
                        assert mock_send.call_count == 2

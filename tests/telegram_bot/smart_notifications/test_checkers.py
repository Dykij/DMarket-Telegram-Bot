"""Unit tests for smart notifications checkers.

This module tests src/telegram_bot/smart_notifications/checkers.py covering:
- check_price_alerts function
- check_market_opportunities function
- start_notification_checker function
- Alert filtering and notification logic

Target: 20+ tests to achieve 70%+ coverage
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Bot

from src.dmarket.dmarket_api import DMarketAPI
from src.telegram_bot.notification_queue import NotificationQueue
from src.utils.exceptions import APIError, NetworkError


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture()
def mock_api():
    """Fixture providing a mocked DMarketAPI."""
    api = MagicMock(spec=DMarketAPI)
    return api


@pytest.fixture()
def mock_bot():
    """Fixture providing a mocked Telegram Bot."""
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture()
def mock_notification_queue():
    """Fixture providing a mocked NotificationQueue."""
    queue = MagicMock(spec=NotificationQueue)
    queue.add_notification = AsyncMock()
    return queue


# ============================================================================
# TestCheckPriceAlerts
# ============================================================================


class TestCheckPriceAlerts:
    """Tests for check_price_alerts function."""

    @pytest.mark.asyncio()
    async def test_check_price_alerts_with_no_active_alerts(self, mock_api, mock_bot):
        """Test check_price_alerts with no active alerts."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ):
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            # Should complete without error
            await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_price_alerts_with_disabled_user(self, mock_api, mock_bot):
        """Test check_price_alerts skips disabled users."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "test_item",
                        "conditions": {"price": 10.0, "direction": "below"},
                    }
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": False}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
        ) as mock_get_market:
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            await check_price_alerts(mock_api, mock_bot)
            
            # Should not call market data fetch for disabled user
            mock_get_market.assert_not_called()

    @pytest.mark.asyncio()
    async def test_check_price_alerts_with_api_error(self, mock_api, mock_bot):
        """Test check_price_alerts handles API errors gracefully."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "test_item",
                        "conditions": {"price": 10.0, "direction": "below"},
                    }
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            side_effect=APIError("API Error"),
        ):
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            # Should not raise, handles error gracefully
            await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_price_alerts_filters_inactive_alerts(self, mock_api, mock_bot):
        """Test check_price_alerts filters out inactive alerts."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": False,  # Inactive
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "test_item",
                        "conditions": {"price": 10.0, "direction": "below"},
                    },
                    {
                        "active": True,
                        "type": "other_type",  # Not price_alert
                        "game": "csgo",
                        "item_id": "test_item2",
                        "conditions": {},
                    },
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
        ) as mock_get_market:
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            await check_price_alerts(mock_api, mock_bot)
            
            # Should not fetch market data since no active price alerts
            mock_get_market.assert_not_called()

    @pytest.mark.asyncio()
    async def test_check_price_alerts_triggers_below_threshold(self, mock_api, mock_bot):
        """Test check_price_alerts triggers alert when price below threshold."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "test_item",
                        "conditions": {"price": 10.0, "direction": "below"},
                        "last_triggered": None,
                        "trigger_count": 0,
                        "one_time": False,
                    }
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            new_callable=AsyncMock,
            return_value={
                "test_item": {"title": "Test Item", "price": {"USD": 500}},
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_item_price",
            return_value=5.0,  # Below threshold of 10.0
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification",
            new_callable=AsyncMock,
        ) as mock_send:
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            await check_price_alerts(mock_api, mock_bot)
            
            # Should send notification
            mock_send.assert_called_once()

    @pytest.mark.asyncio()
    async def test_check_price_alerts_triggers_above_threshold(self, mock_api, mock_bot):
        """Test check_price_alerts triggers alert when price above threshold."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "test_item",
                        "conditions": {"price": 10.0, "direction": "above"},
                        "last_triggered": None,
                        "trigger_count": 0,
                        "one_time": False,
                    }
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            new_callable=AsyncMock,
            return_value={
                "test_item": {"title": "Test Item", "price": {"USD": 1500}},
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_item_price",
            return_value=15.0,  # Above threshold of 10.0
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification",
            new_callable=AsyncMock,
        ) as mock_send:
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            await check_price_alerts(mock_api, mock_bot)
            
            # Should send notification
            mock_send.assert_called_once()

    @pytest.mark.asyncio()
    async def test_check_price_alerts_deactivates_one_time_alert(self, mock_api, mock_bot):
        """Test check_price_alerts deactivates one-time alerts after triggering."""
        alert_data = {
            "active": True,
            "type": "price_alert",
            "game": "csgo",
            "item_id": "test_item",
            "conditions": {"price": 10.0, "direction": "below"},
            "last_triggered": None,
            "trigger_count": 0,
            "one_time": True,  # One-time alert
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={"12345": [alert_data]},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            new_callable=AsyncMock,
            return_value={
                "test_item": {"title": "Test Item", "price": {"USD": 500}},
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_item_price",
            return_value=5.0,  # Below threshold
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification",
            new_callable=AsyncMock,
        ):
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            await check_price_alerts(mock_api, mock_bot)
            
            # Alert should be deactivated
            assert alert_data["active"] is False


# ============================================================================
# TestCheckMarketOpportunities
# ============================================================================


class TestCheckMarketOpportunities:
    """Tests for check_market_opportunities function."""

    @pytest.mark.asyncio()
    async def test_check_market_opportunities_no_interested_users(
        self, mock_api, mock_bot
    ):
        """Test check_market_opportunities with no interested users."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={},
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                check_market_opportunities,
            )
            
            # Should complete without error
            await check_market_opportunities(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_market_opportunities_with_disabled_users(
        self, mock_api, mock_bot
    ):
        """Test check_market_opportunities skips disabled users."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={
                "12345": {"enabled": False, "notifications": {"market_opportunity": True}}
            },
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                check_market_opportunities,
            )
            
            await check_market_opportunities(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_market_opportunities_api_error(self, mock_api, mock_bot):
        """Test check_market_opportunities handles API errors gracefully."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={
                "12345": {
                    "enabled": True,
                    "notifications": {"market_opportunity": True},
                    "games": {"csgo": True},
                }
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
            new_callable=AsyncMock,
            side_effect=APIError("API Error"),
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                check_market_opportunities,
            )
            
            # Should not raise, handles error gracefully
            await check_market_opportunities(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_market_opportunities_no_items_found(
        self, mock_api, mock_bot
    ):
        """Test check_market_opportunities when no market items found."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={
                "12345": {
                    "enabled": True,
                    "notifications": {"market_opportunity": True},
                    "games": {"csgo": True},
                }
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
            new_callable=AsyncMock,
            return_value=[],  # No items
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                check_market_opportunities,
            )
            
            await check_market_opportunities(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_market_opportunities_filters_low_scores(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test check_market_opportunities filters low score opportunities."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={
                "12345": {
                    "enabled": True,
                    "notifications": {"market_opportunity": True},
                    "games": {"csgo": True},
                    "preferences": {
                        "min_opportunity_score": 60,
                        "min_price": 1.0,
                        "max_price": 1000.0,
                    },
                }
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
            new_callable=AsyncMock,
            return_value=[{"itemId": "item1", "title": "Test"}],
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_price_history_for_items",
            new_callable=AsyncMock,
            return_value={"item1": [{"price": 10.0}]},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.analyze_market_opportunity",
            new_callable=AsyncMock,
            return_value={
                "item_id": "item1",
                "opportunity_score": 30,  # Below threshold of 60
                "current_price": 10.0,
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.send_market_opportunity_notification",
            new_callable=AsyncMock,
        ) as mock_send:
            from src.telegram_bot.smart_notifications.checkers import (
                check_market_opportunities,
            )
            
            await check_market_opportunities(mock_api, mock_bot, mock_notification_queue)
            
            # Should not send notification due to low score
            mock_send.assert_not_called()


# ============================================================================
# TestStartNotificationChecker
# ============================================================================


class TestStartNotificationChecker:
    """Tests for start_notification_checker function."""

    @pytest.mark.asyncio()
    async def test_start_notification_checker_loads_preferences(
        self, mock_api, mock_bot
    ):
        """Test start_notification_checker loads user preferences."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.load_user_preferences",
        ) as mock_load, patch(
            "src.telegram_bot.smart_notifications.checkers.check_price_alerts",
            new_callable=AsyncMock,
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_market_opportunities",
            new_callable=AsyncMock,
        ), patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
            side_effect=asyncio.CancelledError,  # Stop the loop
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                start_notification_checker,
            )
            
            with pytest.raises(asyncio.CancelledError):
                await start_notification_checker(mock_api, mock_bot, interval=1)
            
            mock_load.assert_called_once()

    @pytest.mark.asyncio()
    async def test_start_notification_checker_calls_checkers(
        self, mock_api, mock_bot
    ):
        """Test start_notification_checker calls both checkers."""
        call_count = {"price": 0, "market": 0}
        
        async def mock_check_price(*args, **kwargs):
            call_count["price"] += 1
        
        async def mock_check_market(*args, **kwargs):
            call_count["market"] += 1
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.load_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_price_alerts",
            new_callable=AsyncMock,
            side_effect=mock_check_price,
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_market_opportunities",
            new_callable=AsyncMock,
            side_effect=mock_check_market,
        ), patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
            side_effect=[None, asyncio.CancelledError],  # Run once then stop
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                start_notification_checker,
            )
            
            with pytest.raises(asyncio.CancelledError):
                await start_notification_checker(mock_api, mock_bot, interval=1)
            
            # Both checkers should be called
            assert call_count["price"] >= 1
            assert call_count["market"] >= 1

    @pytest.mark.asyncio()
    async def test_start_notification_checker_handles_errors(
        self, mock_api, mock_bot
    ):
        """Test start_notification_checker handles errors without crashing."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.load_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_price_alerts",
            new_callable=AsyncMock,
            side_effect=Exception("Test error"),
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_market_opportunities",
            new_callable=AsyncMock,
        ), patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
            side_effect=[None, asyncio.CancelledError],
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                start_notification_checker,
            )
            
            # Should not raise due to exception handling
            with pytest.raises(asyncio.CancelledError):
                await start_notification_checker(mock_api, mock_bot, interval=1)

    @pytest.mark.asyncio()
    async def test_start_notification_checker_uses_custom_interval(
        self, mock_api, mock_bot
    ):
        """Test start_notification_checker uses custom interval."""
        sleep_calls = []
        
        async def track_sleep(seconds):
            sleep_calls.append(seconds)
            if len(sleep_calls) >= 1:
                raise asyncio.CancelledError
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.load_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_price_alerts",
            new_callable=AsyncMock,
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.check_market_opportunities",
            new_callable=AsyncMock,
        ), patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
            side_effect=track_sleep,
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                start_notification_checker,
            )
            
            custom_interval = 600
            with pytest.raises(asyncio.CancelledError):
                await start_notification_checker(
                    mock_api, mock_bot, interval=custom_interval
                )
            
            assert custom_interval in sleep_calls


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_check_price_alerts_with_network_error(self, mock_api, mock_bot):
        """Test check_price_alerts handles NetworkError."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "test_item",
                        "conditions": {"price": 10.0, "direction": "below"},
                    }
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            side_effect=NetworkError("Network Error"),
        ):
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            # Should not raise
            await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_price_alerts_with_empty_item_ids(self, mock_api, mock_bot):
        """Test check_price_alerts handles alerts without item_id."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "",  # Empty item_id
                        "conditions": {"price": 10.0, "direction": "below"},
                    }
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            new_callable=AsyncMock,
            return_value={},
        ):
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            # Should not raise
            await check_price_alerts(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_market_opportunities_with_network_error(
        self, mock_api, mock_bot
    ):
        """Test check_market_opportunities handles NetworkError."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={
                "12345": {
                    "enabled": True,
                    "notifications": {"market_opportunity": True},
                    "games": {"csgo": True},
                }
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
            new_callable=AsyncMock,
            side_effect=NetworkError("Network Error"),
        ):
            from src.telegram_bot.smart_notifications.checkers import (
                check_market_opportunities,
            )
            
            # Should not raise
            await check_market_opportunities(mock_api, mock_bot)

    @pytest.mark.asyncio()
    async def test_check_price_alerts_groups_by_game(self, mock_api, mock_bot):
        """Test check_price_alerts groups alerts by game for efficiency."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={
                "12345": [
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "item1",
                        "conditions": {"price": 10.0, "direction": "below"},
                    },
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "csgo",
                        "item_id": "item2",
                        "conditions": {"price": 20.0, "direction": "above"},
                    },
                    {
                        "active": True,
                        "type": "price_alert",
                        "game": "dota2",
                        "item_id": "item3",
                        "conditions": {"price": 15.0, "direction": "below"},
                    },
                ]
            },
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={"12345": {"enabled": True}},
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.save_user_preferences",
        ), patch(
            "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
            new_callable=AsyncMock,
            return_value={},
        ) as mock_get_market:
            from src.telegram_bot.smart_notifications.checkers import check_price_alerts
            
            await check_price_alerts(mock_api, mock_bot)
            
            # Should be called twice - once for csgo, once for dota2
            assert mock_get_market.call_count == 2

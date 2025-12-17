"""Unit tests for smart_notifications/checkers module.

Tests for notification checking functionality.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.smart_notifications.checkers import (
    check_market_opportunities,
    check_price_alerts,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_api():
    """Create mock DMarket API."""
    api = AsyncMock()
    return api


@pytest.fixture
def mock_bot():
    """Create mock Telegram Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_notification_queue():
    """Create mock NotificationQueue."""
    queue = AsyncMock()
    queue.enqueue = AsyncMock()
    return queue


# ============================================================================
# TESTS FOR check_price_alerts
# ============================================================================


class TestCheckPriceAlerts:
    """Tests for check_price_alerts function."""

    @pytest.mark.asyncio()
    async def test_no_active_alerts(self, mock_api, mock_bot, mock_notification_queue):
        """Test when there are no active alerts."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value={},
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value={},
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                ):
                    await check_price_alerts(mock_api, mock_bot, mock_notification_queue)
                    
                    # Should complete without sending any notifications
                    mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_user_notifications_disabled(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test when user has notifications disabled."""
        alerts = {
            "123456": [
                {
                    "active": True,
                    "type": "price_alert",
                    "item_id": "item123",
                    "game": "csgo",
                    "conditions": {"price": 10.0, "direction": "below"},
                }
            ]
        }
        prefs = {
            "123456": {"enabled": False}
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value=alerts,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value=prefs,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                ):
                    await check_price_alerts(mock_api, mock_bot, mock_notification_queue)
                    
                    # Should skip disabled user
                    mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_alert_below_threshold_triggered(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test alert triggered when price drops below threshold."""
        alerts = {
            "123456": [
                {
                    "active": True,
                    "type": "price_alert",
                    "item_id": "item123",
                    "game": "csgo",
                    "conditions": {"price": 15.0, "direction": "below"},
                    "last_triggered": 0,
                    "trigger_count": 0,
                    "one_time": False,
                }
            ]
        }
        prefs = {
            "123456": {"enabled": True}
        }
        market_data = {
            "item123": {
                "itemId": "item123",
                "price": {"USD": "1000"},  # $10 - below $15 threshold
            }
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value=alerts,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value=prefs,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value=market_data,
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=10.0,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification",
                            new_callable=AsyncMock,
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(
                                    mock_api, mock_bot, mock_notification_queue
                                )
                                
                                mock_send.assert_called_once()

    @pytest.mark.asyncio()
    async def test_alert_above_threshold_triggered(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test alert triggered when price rises above threshold."""
        alerts = {
            "123456": [
                {
                    "active": True,
                    "type": "price_alert",
                    "item_id": "item123",
                    "game": "csgo",
                    "conditions": {"price": 8.0, "direction": "above"},
                    "last_triggered": 0,
                    "trigger_count": 0,
                    "one_time": False,
                }
            ]
        }
        prefs = {
            "123456": {"enabled": True}
        }
        market_data = {
            "item123": {
                "itemId": "item123",
                "price": {"USD": "1000"},  # $10 - above $8 threshold
            }
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value=alerts,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value=prefs,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value=market_data,
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=10.0,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification",
                            new_callable=AsyncMock,
                        ) as mock_send:
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(
                                    mock_api, mock_bot, mock_notification_queue
                                )
                                
                                mock_send.assert_called_once()

    @pytest.mark.asyncio()
    async def test_one_time_alert_deactivated(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test that one-time alerts are deactivated after triggering."""
        alerts = {
            "123456": [
                {
                    "active": True,
                    "type": "price_alert",
                    "item_id": "item123",
                    "game": "csgo",
                    "conditions": {"price": 15.0, "direction": "below"},
                    "last_triggered": 0,
                    "trigger_count": 0,
                    "one_time": True,
                }
            ]
        }
        prefs = {
            "123456": {"enabled": True}
        }
        market_data = {
            "item123": {
                "itemId": "item123",
                "price": {"USD": "1000"},
            }
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value=alerts,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value=prefs,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    return_value=market_data,
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.get_item_price",
                        return_value=10.0,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.send_price_alert_notification",
                            new_callable=AsyncMock,
                        ):
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                            ):
                                await check_price_alerts(
                                    mock_api, mock_bot, mock_notification_queue
                                )
                                
                                # Alert should be deactivated
                                assert alerts["123456"][0]["active"] is False

    @pytest.mark.asyncio()
    async def test_api_error_handling(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test handling of API errors."""
        from src.utils.exceptions import APIError
        
        alerts = {
            "123456": [
                {
                    "active": True,
                    "type": "price_alert",
                    "item_id": "item123",
                    "game": "csgo",
                    "conditions": {"price": 15.0, "direction": "below"},
                }
            ]
        }
        prefs = {
            "123456": {"enabled": True}
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_active_alerts",
            return_value=alerts,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
                return_value=prefs,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_market_data_for_items",
                    side_effect=APIError("Test error"),
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.save_user_preferences"
                    ):
                        # Should not raise, just log the error
                        await check_price_alerts(
                            mock_api, mock_bot, mock_notification_queue
                        )


# ============================================================================
# TESTS FOR check_market_opportunities
# ============================================================================


class TestCheckMarketOpportunities:
    """Tests for check_market_opportunities function."""

    @pytest.mark.asyncio()
    async def test_no_interested_users(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test when no users are interested in market opportunities."""
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value={},
        ):
            await check_market_opportunities(
                mock_api, mock_bot, mock_notification_queue
            )
            
            # Should complete without errors
            mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_user_disabled_market_notifications(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test when user has market opportunity notifications disabled."""
        prefs = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": False},
            }
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value=prefs,
        ):
            await check_market_opportunities(
                mock_api, mock_bot, mock_notification_queue
            )
            
            # Should not process since market_opportunity is disabled

    @pytest.mark.asyncio()
    async def test_no_market_items(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test when no market items are found."""
        prefs = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": True},
                "games": {"csgo": True},
            }
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value=prefs,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                return_value=[],
            ):
                await check_market_opportunities(
                    mock_api, mock_bot, mock_notification_queue
                )
                
                # Should complete without sending notifications

    @pytest.mark.asyncio()
    async def test_opportunity_found_and_notified(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test that opportunities are found and users are notified."""
        prefs = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": True},
                "games": {"csgo": True},
                "preferences": {
                    "min_opportunity_score": 50,
                    "min_price": 1.0,
                    "max_price": 100.0,
                },
            }
        }
        market_items = [
            {
                "itemId": "item123",
                "title": "Test Item",
                "price": {"USD": "1000"},
            }
        ]
        price_histories = {
            "item123": [{"price": 10.0, "timestamp": 1000}]
        }
        opportunity = {
            "item_id": "item123",
            "item_name": "Test Item",
            "opportunity_score": 75,
            "current_price": 10.0,
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value=prefs,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                return_value=market_items,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_price_history_for_items",
                    return_value=price_histories,
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.analyze_market_opportunity",
                        return_value=opportunity,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.should_throttle_notification",
                            return_value=False,
                        ):
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.send_market_opportunity_notification",
                                new_callable=AsyncMock,
                            ) as mock_send:
                                await check_market_opportunities(
                                    mock_api, mock_bot, mock_notification_queue
                                )
                                
                                mock_send.assert_called()

    @pytest.mark.asyncio()
    async def test_throttled_notification_not_sent(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test that throttled notifications are not sent."""
        prefs = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": True},
                "games": {"csgo": True},
                "preferences": {
                    "min_opportunity_score": 50,
                    "min_price": 1.0,
                    "max_price": 100.0,
                },
            }
        }
        market_items = [{"itemId": "item123", "title": "Test Item"}]
        price_histories = {"item123": []}
        opportunity = {
            "item_id": "item123",
            "opportunity_score": 75,
            "current_price": 10.0,
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value=prefs,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                return_value=market_items,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_price_history_for_items",
                    return_value=price_histories,
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.analyze_market_opportunity",
                        return_value=opportunity,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.should_throttle_notification",
                            return_value=True,  # Throttled
                        ):
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.send_market_opportunity_notification",
                                new_callable=AsyncMock,
                            ) as mock_send:
                                await check_market_opportunities(
                                    mock_api, mock_bot, mock_notification_queue
                                )
                                
                                mock_send.assert_not_called()

    @pytest.mark.asyncio()
    async def test_opportunity_below_min_score_filtered(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test that opportunities below min score are filtered out."""
        prefs = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": True},
                "games": {"csgo": True},
                "preferences": {
                    "min_opportunity_score": 80,  # High threshold
                    "min_price": 1.0,
                    "max_price": 100.0,
                },
            }
        }
        market_items = [{"itemId": "item123", "title": "Test Item"}]
        price_histories = {"item123": []}
        opportunity = {
            "item_id": "item123",
            "opportunity_score": 65,  # Below threshold
            "current_price": 10.0,
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value=prefs,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                return_value=market_items,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.checkers.get_price_history_for_items",
                    return_value=price_histories,
                ):
                    with patch(
                        "src.telegram_bot.smart_notifications.checkers.analyze_market_opportunity",
                        return_value=opportunity,
                    ):
                        with patch(
                            "src.telegram_bot.smart_notifications.checkers.should_throttle_notification",
                            return_value=False,
                        ):
                            with patch(
                                "src.telegram_bot.smart_notifications.checkers.send_market_opportunity_notification",
                                new_callable=AsyncMock,
                            ) as mock_send:
                                await check_market_opportunities(
                                    mock_api, mock_bot, mock_notification_queue
                                )
                                
                                # Should not be called due to score filter
                                mock_send.assert_not_called()

    @pytest.mark.asyncio()
    async def test_api_error_handling(
        self, mock_api, mock_bot, mock_notification_queue
    ):
        """Test handling of API errors."""
        from src.utils.exceptions import APIError
        
        prefs = {
            "123456": {
                "enabled": True,
                "notifications": {"market_opportunity": True},
                "games": {"csgo": True},
            }
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.checkers.get_user_preferences",
            return_value=prefs,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.checkers.get_market_items_for_game",
                side_effect=APIError("Test error"),
            ):
                # Should not raise
                await check_market_opportunities(
                    mock_api, mock_bot, mock_notification_queue
                )

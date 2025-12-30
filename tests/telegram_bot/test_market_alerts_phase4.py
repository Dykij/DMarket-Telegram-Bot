"""
Comprehensive Phase 4 tests for market_alerts.py module.

This module tests the MarketAlertsManager class which handles
market notifications for price changes, trending items, volatility,
and arbitrage opportunities.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.market_alerts import (
    MarketAlertsManager,
    get_alerts_manager,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def mock_bot():
    """Create a mock Telegram bot."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture()
def mock_dmarket_api():
    """Create a mock DMarket API client."""
    api = MagicMock()
    api.get_market_items = AsyncMock(return_value={"objects": []})
    api.get_balance = AsyncMock(return_value={"usd": "10000"})
    return api


@pytest.fixture()
def alerts_manager(mock_bot, mock_dmarket_api):
    """Create a MarketAlertsManager instance for testing."""
    return MarketAlertsManager(mock_bot, mock_dmarket_api)


# =============================================================================
# Test MarketAlertsManager Initialization
# =============================================================================


class TestMarketAlertsManagerInit:
    """Tests for MarketAlertsManager initialization."""

    def test_init_creates_instance(self, mock_bot, mock_dmarket_api):
        """Test that initialization creates a valid instance."""
        manager = MarketAlertsManager(mock_bot, mock_dmarket_api)

        assert manager.bot is mock_bot
        assert manager.dmarket_api is mock_dmarket_api
        assert manager.running is False
        assert manager.background_task is None

    def test_init_creates_subscribers_dict(self, alerts_manager):
        """Test that subscribers dictionary is initialized correctly."""
        assert "price_changes" in alerts_manager.subscribers
        assert "trending" in alerts_manager.subscribers
        assert "volatility" in alerts_manager.subscribers
        assert "arbitrage" in alerts_manager.subscribers

        for subscribers in alerts_manager.subscribers.values():
            assert isinstance(subscribers, set)
            assert len(subscribers) == 0

    def test_init_creates_active_alerts_dict(self, alerts_manager):
        """Test that active_alerts dictionary is initialized correctly."""
        assert "price_changes" in alerts_manager.active_alerts
        assert "trending" in alerts_manager.active_alerts
        assert "volatility" in alerts_manager.active_alerts
        assert "arbitrage" in alerts_manager.active_alerts

    def test_init_creates_alert_thresholds(self, alerts_manager):
        """Test that alert thresholds are initialized with default values."""
        assert alerts_manager.alert_thresholds["price_change_percent"] == 15.0
        assert alerts_manager.alert_thresholds["trending_popularity"] == 50.0
        assert alerts_manager.alert_thresholds["volatility_threshold"] == 25.0
        assert alerts_manager.alert_thresholds["arbitrage_profit_percent"] == 10.0

    def test_init_creates_last_check_times(self, alerts_manager):
        """Test that last check times are initialized to 0."""
        for check_time in alerts_manager.last_check_time.values():
            assert check_time == 0

    def test_init_creates_check_intervals(self, alerts_manager):
        """Test that check intervals are initialized with default values."""
        assert alerts_manager.check_intervals["price_changes"] == 3600  # 1 hour
        assert alerts_manager.check_intervals["trending"] == 7200  # 2 hours
        assert alerts_manager.check_intervals["volatility"] == 14400  # 4 hours
        assert alerts_manager.check_intervals["arbitrage"] == 1800  # 30 minutes

    def test_init_creates_sent_alerts_dict(self, alerts_manager):
        """Test that sent_alerts dictionary is initialized correctly."""
        for alert_type in alerts_manager.subscribers:
            assert alert_type in alerts_manager.sent_alerts
            assert isinstance(alerts_manager.sent_alerts[alert_type], dict)


# =============================================================================
# Test Subscribe/Unsubscribe Methods
# =============================================================================


class TestSubscriptionMethods:
    """Tests for subscription management methods."""

    def test_subscribe_adds_user(self, alerts_manager):
        """Test that subscribe adds user to subscribers."""
        result = alerts_manager.subscribe(12345, "price_changes")

        assert result is True
        assert 12345 in alerts_manager.subscribers["price_changes"]

    def test_subscribe_multiple_users(self, alerts_manager):
        """Test subscribing multiple users."""
        alerts_manager.subscribe(12345, "price_changes")
        alerts_manager.subscribe(67890, "price_changes")

        assert 12345 in alerts_manager.subscribers["price_changes"]
        assert 67890 in alerts_manager.subscribers["price_changes"]
        assert len(alerts_manager.subscribers["price_changes"]) == 2

    def test_subscribe_same_user_twice(self, alerts_manager):
        """Test subscribing same user twice (idempotent)."""
        alerts_manager.subscribe(12345, "price_changes")
        alerts_manager.subscribe(12345, "price_changes")

        assert len(alerts_manager.subscribers["price_changes"]) == 1

    def test_subscribe_unknown_type_returns_false(self, alerts_manager):
        """Test that subscribing to unknown type returns False."""
        result = alerts_manager.subscribe(12345, "unknown_type")

        assert result is False

    def test_subscribe_to_all_types(self, alerts_manager):
        """Test subscribing user to all alert types."""
        for alert_type in ["price_changes", "trending", "volatility", "arbitrage"]:
            result = alerts_manager.subscribe(12345, alert_type)
            assert result is True
            assert 12345 in alerts_manager.subscribers[alert_type]

    def test_unsubscribe_removes_user(self, alerts_manager):
        """Test that unsubscribe removes user from subscribers."""
        alerts_manager.subscribe(12345, "price_changes")
        result = alerts_manager.unsubscribe(12345, "price_changes")

        assert result is True
        assert 12345 not in alerts_manager.subscribers["price_changes"]

    def test_unsubscribe_nonexistent_user(self, alerts_manager):
        """Test unsubscribing a user that wasn't subscribed."""
        result = alerts_manager.unsubscribe(12345, "price_changes")

        assert result is False

    def test_unsubscribe_unknown_type_returns_false(self, alerts_manager):
        """Test that unsubscribing from unknown type returns False."""
        result = alerts_manager.unsubscribe(12345, "unknown_type")

        assert result is False

    def test_unsubscribe_all_removes_from_all_types(self, alerts_manager):
        """Test that unsubscribe_all removes user from all types."""
        for alert_type in alerts_manager.subscribers:
            alerts_manager.subscribe(12345, alert_type)

        result = alerts_manager.unsubscribe_all(12345)

        assert result is True
        for subscribers in alerts_manager.subscribers.values():
            assert 12345 not in subscribers

    def test_unsubscribe_all_returns_false_if_not_subscribed(self, alerts_manager):
        """Test that unsubscribe_all returns False if user wasn't subscribed."""
        result = alerts_manager.unsubscribe_all(12345)

        assert result is False


# =============================================================================
# Test Get User Subscriptions
# =============================================================================


class TestGetUserSubscriptions:
    """Tests for get_user_subscriptions method."""

    def test_get_user_subscriptions_empty(self, alerts_manager):
        """Test getting subscriptions for user with no subscriptions."""
        subscriptions = alerts_manager.get_user_subscriptions(12345)

        assert subscriptions == []

    def test_get_user_subscriptions_single(self, alerts_manager):
        """Test getting subscriptions for user with one subscription."""
        alerts_manager.subscribe(12345, "price_changes")
        subscriptions = alerts_manager.get_user_subscriptions(12345)

        assert subscriptions == ["price_changes"]

    def test_get_user_subscriptions_multiple(self, alerts_manager):
        """Test getting subscriptions for user with multiple subscriptions."""
        alerts_manager.subscribe(12345, "price_changes")
        alerts_manager.subscribe(12345, "trending")
        alerts_manager.subscribe(12345, "arbitrage")

        subscriptions = alerts_manager.get_user_subscriptions(12345)

        assert len(subscriptions) == 3
        assert "price_changes" in subscriptions
        assert "trending" in subscriptions
        assert "arbitrage" in subscriptions


# =============================================================================
# Test Get Subscription Count
# =============================================================================


class TestGetSubscriptionCount:
    """Tests for get_subscription_count method."""

    def test_get_subscription_count_empty(self, alerts_manager):
        """Test getting subscription count with no subscribers."""
        count = alerts_manager.get_subscription_count("price_changes")

        assert count == 0

    def test_get_subscription_count_single_type(self, alerts_manager):
        """Test getting subscription count for single type."""
        alerts_manager.subscribe(12345, "price_changes")
        alerts_manager.subscribe(67890, "price_changes")

        count = alerts_manager.get_subscription_count("price_changes")

        assert count == 2

    def test_get_subscription_count_unknown_type(self, alerts_manager):
        """Test getting subscription count for unknown type returns 0."""
        count = alerts_manager.get_subscription_count("unknown_type")

        assert count == 0

    def test_get_subscription_count_total_unique(self, alerts_manager):
        """Test getting total unique subscriber count."""
        alerts_manager.subscribe(12345, "price_changes")
        alerts_manager.subscribe(12345, "trending")  # Same user, different type
        alerts_manager.subscribe(67890, "price_changes")

        count = alerts_manager.get_subscription_count()  # No type = total unique

        assert count == 2  # Only 2 unique users


# =============================================================================
# Test Update Alert Threshold
# =============================================================================


class TestUpdateAlertThreshold:
    """Tests for update_alert_threshold method."""

    def test_update_threshold_price_changes(self, alerts_manager):
        """Test updating price_changes threshold."""
        result = alerts_manager.update_alert_threshold("price_changes", 20.0)

        assert result is True
        assert alerts_manager.alert_thresholds["price_change_percent"] == 20.0

    def test_update_threshold_trending(self, alerts_manager):
        """Test updating trending threshold."""
        result = alerts_manager.update_alert_threshold("trending", 75.0)

        assert result is True
        assert alerts_manager.alert_thresholds["trending_popularity"] == 75.0

    def test_update_threshold_volatility(self, alerts_manager):
        """Test updating volatility threshold."""
        result = alerts_manager.update_alert_threshold("volatility", 30.0)

        assert result is True
        assert alerts_manager.alert_thresholds["volatility_threshold"] == 30.0

    def test_update_threshold_arbitrage(self, alerts_manager):
        """Test updating arbitrage threshold."""
        result = alerts_manager.update_alert_threshold("arbitrage", 15.0)

        assert result is True
        assert alerts_manager.alert_thresholds["arbitrage_profit_percent"] == 15.0

    def test_update_threshold_unknown_type_returns_false(self, alerts_manager):
        """Test updating threshold for unknown type returns False."""
        result = alerts_manager.update_alert_threshold("unknown_type", 20.0)

        assert result is False

    def test_update_threshold_zero_value_returns_false(self, alerts_manager):
        """Test updating threshold with zero value returns False."""
        result = alerts_manager.update_alert_threshold("price_changes", 0)

        assert result is False
        assert alerts_manager.alert_thresholds["price_change_percent"] == 15.0  # Unchanged

    def test_update_threshold_negative_value_returns_false(self, alerts_manager):
        """Test updating threshold with negative value returns False."""
        result = alerts_manager.update_alert_threshold("price_changes", -5.0)

        assert result is False


# =============================================================================
# Test Update Check Interval
# =============================================================================


class TestUpdateCheckInterval:
    """Tests for update_check_interval method."""

    def test_update_interval_valid(self, alerts_manager):
        """Test updating check interval with valid value."""
        result = alerts_manager.update_check_interval("price_changes", 600)  # 10 minutes

        assert result is True
        assert alerts_manager.check_intervals["price_changes"] == 600

    def test_update_interval_unknown_type_returns_false(self, alerts_manager):
        """Test updating interval for unknown type returns False."""
        result = alerts_manager.update_check_interval("unknown_type", 600)

        assert result is False

    def test_update_interval_too_small_returns_false(self, alerts_manager):
        """Test updating interval with value less than 5 minutes returns False."""
        result = alerts_manager.update_check_interval("price_changes", 60)  # 1 minute

        assert result is False
        assert alerts_manager.check_intervals["price_changes"] == 3600  # Unchanged

    def test_update_interval_minimum_allowed(self, alerts_manager):
        """Test updating interval with minimum allowed value (300 seconds)."""
        result = alerts_manager.update_check_interval("price_changes", 300)

        assert result is True
        assert alerts_manager.check_intervals["price_changes"] == 300


# =============================================================================
# Test Clear Sent Alerts
# =============================================================================


class TestClearSentAlerts:
    """Tests for clear_sent_alerts method."""

    def test_clear_all_sent_alerts(self, alerts_manager):
        """Test clearing all sent alerts."""
        # Add some sent alerts
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1", "alert2"}
        alerts_manager.sent_alerts["trending"][67890] = {"alert3"}

        alerts_manager.clear_sent_alerts()

        for alert_type in alerts_manager.sent_alerts:
            assert len(alerts_manager.sent_alerts[alert_type]) == 0

    def test_clear_sent_alerts_for_type(self, alerts_manager):
        """Test clearing sent alerts for specific type."""
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1"}
        alerts_manager.sent_alerts["trending"][12345] = {"alert2"}

        alerts_manager.clear_sent_alerts(alert_type="price_changes")

        assert len(alerts_manager.sent_alerts["price_changes"]) == 0
        assert 12345 in alerts_manager.sent_alerts["trending"]

    def test_clear_sent_alerts_for_user(self, alerts_manager):
        """Test clearing sent alerts for specific user."""
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1"}
        alerts_manager.sent_alerts["price_changes"][67890] = {"alert2"}

        alerts_manager.clear_sent_alerts(user_id=12345)

        assert alerts_manager.sent_alerts["price_changes"].get(12345, set()) == set()
        assert alerts_manager.sent_alerts["price_changes"][67890] == {"alert2"}

    def test_clear_sent_alerts_for_type_and_user(self, alerts_manager):
        """Test clearing sent alerts for specific type and user."""
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1"}
        alerts_manager.sent_alerts["trending"][12345] = {"alert2"}

        alerts_manager.clear_sent_alerts(alert_type="price_changes", user_id=12345)

        assert alerts_manager.sent_alerts["price_changes"][12345] == set()
        assert alerts_manager.sent_alerts["trending"][12345] == {"alert2"}

    def test_clear_sent_alerts_unknown_type(self, alerts_manager):
        """Test clearing sent alerts for unknown type does nothing."""
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1"}

        alerts_manager.clear_sent_alerts(alert_type="unknown_type")

        assert alerts_manager.sent_alerts["price_changes"][12345] == {"alert1"}


# =============================================================================
# Test Clear Old Alerts
# =============================================================================


class TestClearOldAlerts:
    """Tests for clear_old_alerts method."""

    def test_clear_old_alerts_returns_count(self, alerts_manager):
        """Test that clear_old_alerts returns count of cleared alerts."""
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1", "alert2"}
        alerts_manager.sent_alerts["trending"][67890] = {"alert3"}

        count = alerts_manager.clear_old_alerts()

        assert count == 3

    def test_clear_old_alerts_clears_all(self, alerts_manager):
        """Test that clear_old_alerts clears all sent alerts."""
        alerts_manager.sent_alerts["price_changes"][12345] = {"alert1"}
        alerts_manager.sent_alerts["trending"][67890] = {"alert2"}

        alerts_manager.clear_old_alerts()

        for alert_type in alerts_manager.sent_alerts:
            for user_alerts in alerts_manager.sent_alerts[alert_type].values():
                assert len(user_alerts) == 0

    def test_clear_old_alerts_empty(self, alerts_manager):
        """Test clear_old_alerts with no alerts returns 0."""
        count = alerts_manager.clear_old_alerts()

        assert count == 0


# =============================================================================
# Test Monitoring Start/Stop
# =============================================================================


class TestMonitoring:
    """Tests for monitoring start/stop methods."""

    @pytest.mark.asyncio()
    async def test_start_monitoring_sets_running(self, alerts_manager):
        """Test that start_monitoring sets running flag."""
        await alerts_manager.start_monitoring()

        assert alerts_manager.running is True
        assert alerts_manager.background_task is not None

        # Cleanup
        await alerts_manager.stop_monitoring()

    @pytest.mark.asyncio()
    async def test_start_monitoring_when_already_running(self, alerts_manager):
        """Test that start_monitoring does nothing when already running."""
        alerts_manager.running = True

        await alerts_manager.start_monitoring()

        # Should still be running but background_task should be None
        # since we didn't actually start the task
        assert alerts_manager.background_task is None

    @pytest.mark.asyncio()
    async def test_stop_monitoring_sets_not_running(self, alerts_manager):
        """Test that stop_monitoring clears running flag."""
        await alerts_manager.start_monitoring()
        await alerts_manager.stop_monitoring()

        assert alerts_manager.running is False

    @pytest.mark.asyncio()
    async def test_stop_monitoring_when_not_running(self, alerts_manager):
        """Test that stop_monitoring does nothing when not running."""
        await alerts_manager.stop_monitoring()

        assert alerts_manager.running is False


# =============================================================================
# Test Check Methods
# =============================================================================


class TestCheckMethods:
    """Tests for check methods."""

    @pytest.mark.asyncio()
    async def test_check_price_changes_no_changes(self, alerts_manager):
        """Test _check_price_changes with no price changes."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_price_changes",
            new_callable=AsyncMock,
            return_value=[]
        ):
            await alerts_manager._check_price_changes()

            # Should complete without sending any messages
            alerts_manager.bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_check_price_changes_with_changes(self, alerts_manager):
        """Test _check_price_changes with price changes and subscribers."""
        alerts_manager.subscribe(12345, "price_changes")

        mock_changes = [
            {
                "market_hash_name": "Test Item",
                "change_percent": 20.0,
                "direction": "up",
                "current_price": 100.0,
                "old_price": 80.0,
                "change_amount": 20.0,
                "item_url": "https://dmarket.com/test"
            }
        ]

        with patch(
            "src.telegram_bot.market_alerts.analyze_price_changes",
            new_callable=AsyncMock,
            return_value=mock_changes
        ):
            await alerts_manager._check_price_changes()

            alerts_manager.bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_check_price_changes_handles_error(self, alerts_manager):
        """Test _check_price_changes handles errors gracefully."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_price_changes",
            new_callable=AsyncMock,
            side_effect=Exception("API Error")
        ):
            # Should not raise exception
            await alerts_manager._check_price_changes()

    @pytest.mark.asyncio()
    async def test_check_trending_no_items(self, alerts_manager):
        """Test _check_trending_items with no trending items."""
        with patch(
            "src.telegram_bot.market_alerts.find_trending_items",
            new_callable=AsyncMock,
            return_value=[]
        ):
            await alerts_manager._check_trending_items()

            alerts_manager.bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_check_trending_with_items(self, alerts_manager):
        """Test _check_trending_items with trending items and subscribers."""
        alerts_manager.subscribe(12345, "trending")

        mock_items = [
            {
                "market_hash_name": "Trending Item",
                "popularity_score": 75.0,
                "price": 50.0,
                "sales_volume": 100,
                "offers_count": 50,
                "item_url": "https://dmarket.com/test"
            }
        ]

        with patch(
            "src.telegram_bot.market_alerts.find_trending_items",
            new_callable=AsyncMock,
            return_value=mock_items
        ):
            await alerts_manager._check_trending_items()

            alerts_manager.bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_check_volatility_no_items(self, alerts_manager):
        """Test _check_volatility with no volatile items."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_market_volatility",
            new_callable=AsyncMock,
            return_value=[]
        ):
            await alerts_manager._check_volatility()

            alerts_manager.bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_check_volatility_with_items(self, alerts_manager):
        """Test _check_volatility with volatile items and subscribers."""
        alerts_manager.subscribe(12345, "volatility")

        mock_items = [
            {
                "market_hash_name": "Volatile Item",
                "volatility_score": 30.0,
                "current_price": 100.0
            }
        ]

        with patch(
            "src.telegram_bot.market_alerts.analyze_market_volatility",
            new_callable=AsyncMock,
            return_value=mock_items
        ):
            await alerts_manager._check_volatility()

            alerts_manager.bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_check_arbitrage_no_opportunities(self, alerts_manager):
        """Test _check_arbitrage with no opportunities."""
        with patch(
            "src.dmarket.arbitrage_scanner.ArbitrageScanner"
        ) as MockScanner:
            mock_scanner = MagicMock()
            mock_scanner.scan_level = AsyncMock(return_value=[])
            MockScanner.return_value = mock_scanner

            with patch("src.dmarket.dmarket_api.DMarketAPI"):
                await alerts_manager._check_arbitrage()

                alerts_manager.bot.send_message.assert_not_called()


# =============================================================================
# Test Monitor Market Loop
# =============================================================================


class TestMonitorMarketLoop:
    """Tests for _monitor_market method."""

    @pytest.mark.asyncio()
    async def test_monitor_market_no_subscribers(self, alerts_manager):
        """Test _monitor_market skips check when no subscribers."""
        alerts_manager.running = True
        call_count = 0

        # Mock the sleep to speed up the test
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Stop after 2 sleep calls
                alerts_manager.running = False
            await original_sleep(0.01)  # Short delay

        with patch("asyncio.sleep", mock_sleep):
            with patch.object(alerts_manager, "_check_price_changes", new_callable=AsyncMock) as mock_check:
                await alerts_manager._monitor_market()

                # Should not call check methods since no subscribers
                mock_check.assert_not_called()


# =============================================================================
# Test Get Alerts Manager
# =============================================================================


class TestGetAlertsManager:
    """Tests for get_alerts_manager function."""

    def test_get_alerts_manager_requires_bot(self):
        """Test that get_alerts_manager raises error without bot."""
        # Reset global manager
        import src.telegram_bot.market_alerts as module
        module._alerts_manager = None

        with pytest.raises(ValueError, match="требуется bot"):
            get_alerts_manager(bot=None, dmarket_api=MagicMock())

    def test_get_alerts_manager_creates_instance(self, mock_bot, mock_dmarket_api):
        """Test that get_alerts_manager creates new instance."""
        # Reset global manager
        import src.telegram_bot.market_alerts as module
        module._alerts_manager = None

        manager = get_alerts_manager(bot=mock_bot, dmarket_api=mock_dmarket_api)

        assert manager is not None
        assert isinstance(manager, MarketAlertsManager)

        # Reset for other tests
        module._alerts_manager = None

    def test_get_alerts_manager_returns_existing(self, mock_bot, mock_dmarket_api):
        """Test that get_alerts_manager returns existing instance."""
        import src.telegram_bot.market_alerts as module
        module._alerts_manager = None

        manager1 = get_alerts_manager(bot=mock_bot, dmarket_api=mock_dmarket_api)
        manager2 = get_alerts_manager()

        assert manager1 is manager2

        # Reset for other tests
        module._alerts_manager = None


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_subscribe_with_zero_user_id(self, alerts_manager):
        """Test subscribing with user_id of 0."""
        result = alerts_manager.subscribe(0, "price_changes")

        assert result is True
        assert 0 in alerts_manager.subscribers["price_changes"]

    def test_subscribe_with_large_user_id(self, alerts_manager):
        """Test subscribing with very large user_id."""
        large_id = 9999999999999999
        result = alerts_manager.subscribe(large_id, "price_changes")

        assert result is True
        assert large_id in alerts_manager.subscribers["price_changes"]

    def test_multiple_subscriptions_same_user(self, alerts_manager):
        """Test user subscribing to all available types."""
        user_id = 12345

        for alert_type in ["price_changes", "trending", "volatility", "arbitrage"]:
            alerts_manager.subscribe(user_id, alert_type)

        subscriptions = alerts_manager.get_user_subscriptions(user_id)
        assert len(subscriptions) == 4

    def test_update_threshold_boundary_value(self, alerts_manager):
        """Test updating threshold with very small positive value."""
        result = alerts_manager.update_alert_threshold("price_changes", 0.001)

        assert result is True
        assert alerts_manager.alert_thresholds["price_change_percent"] == 0.001

    def test_update_threshold_large_value(self, alerts_manager):
        """Test updating threshold with very large value."""
        result = alerts_manager.update_alert_threshold("price_changes", 1000.0)

        assert result is True
        assert alerts_manager.alert_thresholds["price_change_percent"] == 1000.0


# =============================================================================
# Test Integration Scenarios
# =============================================================================


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_full_subscription_workflow(self, alerts_manager):
        """Test complete subscription workflow."""
        user_id = 12345

        # Subscribe to multiple types
        alerts_manager.subscribe(user_id, "price_changes")
        alerts_manager.subscribe(user_id, "arbitrage")

        # Verify subscriptions
        subs = alerts_manager.get_user_subscriptions(user_id)
        assert len(subs) == 2

        # Unsubscribe from one
        alerts_manager.unsubscribe(user_id, "price_changes")
        subs = alerts_manager.get_user_subscriptions(user_id)
        assert len(subs) == 1
        assert "arbitrage" in subs

        # Unsubscribe all
        alerts_manager.unsubscribe_all(user_id)
        subs = alerts_manager.get_user_subscriptions(user_id)
        assert len(subs) == 0

    def test_threshold_and_interval_configuration(self, alerts_manager):
        """Test configuring thresholds and intervals."""
        # Update threshold
        alerts_manager.update_alert_threshold("price_changes", 25.0)
        assert alerts_manager.alert_thresholds["price_change_percent"] == 25.0

        # Update interval
        alerts_manager.update_check_interval("price_changes", 900)
        assert alerts_manager.check_intervals["price_changes"] == 900

    @pytest.mark.asyncio()
    async def test_monitoring_lifecycle(self, alerts_manager):
        """Test complete monitoring lifecycle."""
        # Start monitoring
        await alerts_manager.start_monitoring()
        assert alerts_manager.running is True

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Stop monitoring
        await alerts_manager.stop_monitoring()
        assert alerts_manager.running is False

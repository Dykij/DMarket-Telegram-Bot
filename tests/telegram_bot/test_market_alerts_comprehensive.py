"""Comprehensive tests for market_alerts.py MarketAlertsManager.

This module tests the MarketAlertsManager class including:
- Initialization and configuration
- Subscription management (subscribe, unsubscribe)
- Alert thresholds and check intervals
- Monitoring start/stop
- Notification sending logic
- Clear alerts functionality

Coverage target: 70%+
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.market_alerts import (
    MarketAlertsManager,
    get_alerts_manager,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    return bot


@pytest.fixture()
def mock_dmarket_api():
    """Create a mock DMarket API client."""
    api = AsyncMock()
    api.get_market_items = AsyncMock(return_value={"objects": []})
    return api


@pytest.fixture()
def alerts_manager(mock_bot, mock_dmarket_api):
    """Create a MarketAlertsManager instance for testing."""
    return MarketAlertsManager(bot=mock_bot, dmarket_api=mock_dmarket_api)


# ============================================================================
# Test: Initialization
# ============================================================================


class TestMarketAlertsManagerInit:
    """Tests for MarketAlertsManager initialization."""

    def test_init_creates_instance(self, mock_bot, mock_dmarket_api):
        """Test successful initialization with valid arguments."""
        manager = MarketAlertsManager(bot=mock_bot, dmarket_api=mock_dmarket_api)

        assert manager.bot is mock_bot
        assert manager.dmarket_api is mock_dmarket_api
        assert manager.running is False
        assert manager.background_task is None

    def test_init_sets_default_subscribers(self, alerts_manager):
        """Test that default subscriber sets are initialized."""
        assert "price_changes" in alerts_manager.subscribers
        assert "trending" in alerts_manager.subscribers
        assert "volatility" in alerts_manager.subscribers
        assert "arbitrage" in alerts_manager.subscribers
        assert all(isinstance(s, set) for s in alerts_manager.subscribers.values())

    def test_init_sets_default_alert_thresholds(self, alerts_manager):
        """Test that default alert thresholds are set."""
        assert alerts_manager.alert_thresholds["price_change_percent"] == 15.0
        assert alerts_manager.alert_thresholds["trending_popularity"] == 50.0
        assert alerts_manager.alert_thresholds["volatility_threshold"] == 25.0
        assert alerts_manager.alert_thresholds["arbitrage_profit_percent"] == 10.0

    def test_init_sets_default_check_intervals(self, alerts_manager):
        """Test that default check intervals are set."""
        assert alerts_manager.check_intervals["price_changes"] == 3600  # 1 hour
        assert alerts_manager.check_intervals["trending"] == 7200  # 2 hours
        assert alerts_manager.check_intervals["volatility"] == 14400  # 4 hours
        assert alerts_manager.check_intervals["arbitrage"] == 1800  # 30 minutes

    def test_init_sets_empty_active_alerts(self, alerts_manager):
        """Test that active alerts dict is initialized."""
        assert isinstance(alerts_manager.active_alerts, dict)
        assert "price_changes" in alerts_manager.active_alerts

    def test_init_sets_sent_alerts(self, alerts_manager):
        """Test that sent alerts tracking dict is initialized."""
        assert isinstance(alerts_manager.sent_alerts, dict)
        for alert_type in alerts_manager.subscribers:
            assert alert_type in alerts_manager.sent_alerts


# ============================================================================
# Test: Subscription Management
# ============================================================================


class TestSubscriptionManagement:
    """Tests for subscription management methods."""

    def test_subscribe_valid_alert_type(self, alerts_manager):
        """Test subscribing to a valid alert type."""
        user_id = 12345

        result = alerts_manager.subscribe(user_id, "price_changes")

        assert result is True
        assert user_id in alerts_manager.subscribers["price_changes"]

    def test_subscribe_invalid_alert_type(self, alerts_manager):
        """Test subscribing to an invalid alert type returns False."""
        user_id = 12345

        result = alerts_manager.subscribe(user_id, "invalid_type")

        assert result is False

    def test_subscribe_multiple_users(self, alerts_manager):
        """Test subscribing multiple users to same alert type."""
        user_ids = [111, 222, 333]

        for user_id in user_ids:
            alerts_manager.subscribe(user_id, "trending")

        for user_id in user_ids:
            assert user_id in alerts_manager.subscribers["trending"]

    def test_subscribe_user_to_multiple_types(self, alerts_manager):
        """Test subscribing same user to multiple alert types."""
        user_id = 12345

        alerts_manager.subscribe(user_id, "price_changes")
        alerts_manager.subscribe(user_id, "arbitrage")
        alerts_manager.subscribe(user_id, "volatility")

        assert user_id in alerts_manager.subscribers["price_changes"]
        assert user_id in alerts_manager.subscribers["arbitrage"]
        assert user_id in alerts_manager.subscribers["volatility"]

    def test_unsubscribe_valid_subscription(self, alerts_manager):
        """Test unsubscribing from a valid subscription."""
        user_id = 12345
        alerts_manager.subscribe(user_id, "price_changes")

        result = alerts_manager.unsubscribe(user_id, "price_changes")

        assert result is True
        assert user_id not in alerts_manager.subscribers["price_changes"]

    def test_unsubscribe_invalid_alert_type(self, alerts_manager):
        """Test unsubscribing from an invalid alert type."""
        result = alerts_manager.unsubscribe(12345, "invalid_type")

        assert result is False

    def test_unsubscribe_user_not_subscribed(self, alerts_manager):
        """Test unsubscribing a user that wasn't subscribed."""
        result = alerts_manager.unsubscribe(12345, "price_changes")

        assert result is False

    def test_unsubscribe_all(self, alerts_manager):
        """Test unsubscribing from all alert types."""
        user_id = 12345
        alerts_manager.subscribe(user_id, "price_changes")
        alerts_manager.subscribe(user_id, "trending")
        alerts_manager.subscribe(user_id, "arbitrage")

        result = alerts_manager.unsubscribe_all(user_id)

        assert result is True
        for subscribers in alerts_manager.subscribers.values():
            assert user_id not in subscribers

    def test_unsubscribe_all_user_not_subscribed(self, alerts_manager):
        """Test unsubscribe_all when user has no subscriptions."""
        result = alerts_manager.unsubscribe_all(99999)

        assert result is False

    def test_get_user_subscriptions(self, alerts_manager):
        """Test getting list of user's subscriptions."""
        user_id = 12345
        alerts_manager.subscribe(user_id, "price_changes")
        alerts_manager.subscribe(user_id, "volatility")

        subscriptions = alerts_manager.get_user_subscriptions(user_id)

        assert "price_changes" in subscriptions
        assert "volatility" in subscriptions
        assert "trending" not in subscriptions

    def test_get_user_subscriptions_empty(self, alerts_manager):
        """Test getting subscriptions for user with none."""
        subscriptions = alerts_manager.get_user_subscriptions(99999)

        assert subscriptions == []

    def test_get_subscription_count_specific_type(self, alerts_manager):
        """Test getting subscriber count for specific alert type."""
        alerts_manager.subscribe(111, "trending")
        alerts_manager.subscribe(222, "trending")
        alerts_manager.subscribe(333, "trending")

        count = alerts_manager.get_subscription_count("trending")

        assert count == 3

    def test_get_subscription_count_invalid_type(self, alerts_manager):
        """Test getting subscriber count for invalid type."""
        count = alerts_manager.get_subscription_count("invalid_type")

        assert count == 0

    def test_get_subscription_count_all_unique(self, alerts_manager):
        """Test getting total unique subscriber count."""
        alerts_manager.subscribe(111, "trending")
        alerts_manager.subscribe(111, "price_changes")  # Same user
        alerts_manager.subscribe(222, "trending")
        alerts_manager.subscribe(333, "arbitrage")

        count = alerts_manager.get_subscription_count()

        assert count == 3  # 3 unique users


# ============================================================================
# Test: Alert Threshold Management
# ============================================================================


class TestAlertThresholdManagement:
    """Tests for alert threshold update methods."""

    def test_update_alert_threshold_valid(self, alerts_manager):
        """Test updating a valid alert threshold."""
        result = alerts_manager.update_alert_threshold("price_changes", 20.0)

        assert result is True
        assert alerts_manager.alert_thresholds["price_change_percent"] == 20.0

    def test_update_alert_threshold_trending(self, alerts_manager):
        """Test updating trending popularity threshold."""
        result = alerts_manager.update_alert_threshold("trending", 75.0)

        assert result is True
        assert alerts_manager.alert_thresholds["trending_popularity"] == 75.0

    def test_update_alert_threshold_volatility(self, alerts_manager):
        """Test updating volatility threshold."""
        result = alerts_manager.update_alert_threshold("volatility", 30.0)

        assert result is True
        assert alerts_manager.alert_thresholds["volatility_threshold"] == 30.0

    def test_update_alert_threshold_arbitrage(self, alerts_manager):
        """Test updating arbitrage profit threshold."""
        result = alerts_manager.update_alert_threshold("arbitrage", 15.0)

        assert result is True
        assert alerts_manager.alert_thresholds["arbitrage_profit_percent"] == 15.0

    def test_update_alert_threshold_invalid_type(self, alerts_manager):
        """Test updating threshold for invalid type."""
        result = alerts_manager.update_alert_threshold("invalid_type", 10.0)

        assert result is False

    def test_update_alert_threshold_zero_value(self, alerts_manager):
        """Test updating threshold with zero value."""
        result = alerts_manager.update_alert_threshold("price_changes", 0)

        assert result is False

    def test_update_alert_threshold_negative_value(self, alerts_manager):
        """Test updating threshold with negative value."""
        result = alerts_manager.update_alert_threshold("price_changes", -5.0)

        assert result is False


# ============================================================================
# Test: Check Interval Management
# ============================================================================


class TestCheckIntervalManagement:
    """Tests for check interval update methods."""

    def test_update_check_interval_valid(self, alerts_manager):
        """Test updating a valid check interval."""
        result = alerts_manager.update_check_interval("price_changes", 7200)

        assert result is True
        assert alerts_manager.check_intervals["price_changes"] == 7200

    def test_update_check_interval_invalid_type(self, alerts_manager):
        """Test updating interval for invalid type."""
        result = alerts_manager.update_check_interval("invalid_type", 3600)

        assert result is False

    def test_update_check_interval_too_small(self, alerts_manager):
        """Test updating interval with too small value (< 5 min)."""
        result = alerts_manager.update_check_interval("price_changes", 60)

        assert result is False

    def test_update_check_interval_minimum_allowed(self, alerts_manager):
        """Test updating interval with minimum allowed value (5 min)."""
        result = alerts_manager.update_check_interval("price_changes", 300)

        assert result is True
        assert alerts_manager.check_intervals["price_changes"] == 300


# ============================================================================
# Test: Clear Alerts
# ============================================================================


class TestClearAlerts:
    """Tests for clearing sent alerts history."""

    def test_clear_sent_alerts_all(self, alerts_manager):
        """Test clearing all sent alerts."""
        # Setup sent alerts
        alerts_manager.sent_alerts["price_changes"][111] = {"alert1", "alert2"}
        alerts_manager.sent_alerts["trending"][222] = {"alert3"}

        alerts_manager.clear_sent_alerts()

        assert len(alerts_manager.sent_alerts["price_changes"]) == 0
        assert len(alerts_manager.sent_alerts["trending"]) == 0

    def test_clear_sent_alerts_specific_type(self, alerts_manager):
        """Test clearing alerts for specific type only."""
        alerts_manager.sent_alerts["price_changes"][111] = {"alert1"}
        alerts_manager.sent_alerts["trending"][111] = {"alert2"}

        alerts_manager.clear_sent_alerts(alert_type="price_changes")

        assert len(alerts_manager.sent_alerts["price_changes"]) == 0
        assert len(alerts_manager.sent_alerts["trending"][111]) == 1

    def test_clear_sent_alerts_specific_user(self, alerts_manager):
        """Test clearing alerts for specific user only."""
        alerts_manager.sent_alerts["price_changes"][111] = {"alert1"}
        alerts_manager.sent_alerts["price_changes"][222] = {"alert2"}
        alerts_manager.sent_alerts["trending"][111] = {"alert3"}

        alerts_manager.clear_sent_alerts(user_id=111)

        assert len(alerts_manager.sent_alerts["price_changes"][111]) == 0
        assert len(alerts_manager.sent_alerts["price_changes"][222]) == 1
        assert len(alerts_manager.sent_alerts["trending"][111]) == 0

    def test_clear_sent_alerts_specific_type_and_user(self, alerts_manager):
        """Test clearing alerts for specific type and user."""
        alerts_manager.sent_alerts["price_changes"][111] = {"alert1"}
        alerts_manager.sent_alerts["price_changes"][222] = {"alert2"}
        alerts_manager.sent_alerts["trending"][111] = {"alert3"}

        alerts_manager.clear_sent_alerts(alert_type="price_changes", user_id=111)

        assert len(alerts_manager.sent_alerts["price_changes"][111]) == 0
        assert len(alerts_manager.sent_alerts["price_changes"][222]) == 1
        assert len(alerts_manager.sent_alerts["trending"][111]) == 1

    def test_clear_sent_alerts_invalid_type(self, alerts_manager):
        """Test clearing alerts for invalid type does nothing."""
        alerts_manager.sent_alerts["price_changes"][111] = {"alert1"}

        alerts_manager.clear_sent_alerts(alert_type="invalid_type")

        # Original alerts should remain
        assert len(alerts_manager.sent_alerts["price_changes"][111]) == 1

    def test_clear_old_alerts(self, alerts_manager):
        """Test clearing old alerts returns count."""
        alerts_manager.sent_alerts["price_changes"][111] = {"a1", "a2", "a3"}
        alerts_manager.sent_alerts["trending"][222] = {"b1", "b2"}

        cleared = alerts_manager.clear_old_alerts(max_age_days=7)

        assert cleared == 5


# ============================================================================
# Test: Monitoring Start/Stop
# ============================================================================


class TestMonitoringControl:
    """Tests for monitoring start/stop functionality."""

    @pytest.mark.asyncio()
    async def test_start_monitoring(self, alerts_manager):
        """Test starting the monitoring process."""
        await alerts_manager.start_monitoring()

        assert alerts_manager.running is True
        assert alerts_manager.background_task is not None

        # Cleanup
        await alerts_manager.stop_monitoring()

    @pytest.mark.asyncio()
    async def test_start_monitoring_already_running(self, alerts_manager):
        """Test starting monitoring when already running logs warning."""
        await alerts_manager.start_monitoring()

        # Second start should not create new task
        original_task = alerts_manager.background_task
        await alerts_manager.start_monitoring()

        assert alerts_manager.background_task is original_task

        # Cleanup
        await alerts_manager.stop_monitoring()

    @pytest.mark.asyncio()
    async def test_stop_monitoring(self, alerts_manager):
        """Test stopping the monitoring process."""
        await alerts_manager.start_monitoring()
        await alerts_manager.stop_monitoring()

        assert alerts_manager.running is False

    @pytest.mark.asyncio()
    async def test_stop_monitoring_not_running(self, alerts_manager):
        """Test stopping monitoring when not running logs warning."""
        # Should not raise any exception
        await alerts_manager.stop_monitoring()

        assert alerts_manager.running is False


# ============================================================================
# Test: Price Changes Check
# ============================================================================


class TestPriceChangesCheck:
    """Tests for price changes notification checking."""

    @pytest.mark.asyncio()
    async def test_check_price_changes_no_changes(self, alerts_manager):
        """Test checking price changes when none found."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_price_changes",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = []

            await alerts_manager._check_price_changes()

            mock_analyze.assert_called_once()

    @pytest.mark.asyncio()
    async def test_check_price_changes_with_subscribers(self, alerts_manager, mock_bot):
        """Test checking price changes with subscribers."""
        alerts_manager.subscribe(12345, "price_changes")

        mock_changes = [
            {
                "market_hash_name": "AK-47 | Redline",
                "change_percent": 20.0,
                "direction": "up",
                "current_price": 50.0,
                "old_price": 40.0,
                "change_amount": 10.0,
                "item_url": "https://dmarket.com/item/123",
            }
        ]

        with patch(
            "src.telegram_bot.market_alerts.analyze_price_changes",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = mock_changes

            await alerts_manager._check_price_changes()

            mock_bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_check_price_changes_handles_api_error(self, alerts_manager):
        """Test that price changes check handles API errors gracefully."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_price_changes",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("API Error")

            # Should not raise
            await alerts_manager._check_price_changes()


# ============================================================================
# Test: Trending Items Check
# ============================================================================


class TestTrendingItemsCheck:
    """Tests for trending items notification checking."""

    @pytest.mark.asyncio()
    async def test_check_trending_items_no_items(self, alerts_manager):
        """Test checking trending items when none found."""
        with patch(
            "src.telegram_bot.market_alerts.find_trending_items",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.return_value = []

            await alerts_manager._check_trending_items()

            mock_find.assert_called_once()

    @pytest.mark.asyncio()
    async def test_check_trending_items_below_threshold(self, alerts_manager):
        """Test trending items below popularity threshold are filtered."""
        mock_items = [
            {
                "market_hash_name": "Item 1",
                "popularity_score": 30.0,  # Below default 50 threshold
                "price": 10.0,
                "sales_volume": 100,
                "item_url": "https://dmarket.com/item/1",
            }
        ]

        with patch(
            "src.telegram_bot.market_alerts.find_trending_items",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.return_value = mock_items

            await alerts_manager._check_trending_items()

            # No notifications should be sent
            alerts_manager.bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_check_trending_items_handles_error(self, alerts_manager):
        """Test that trending items check handles errors gracefully."""
        with patch(
            "src.telegram_bot.market_alerts.find_trending_items",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.side_effect = Exception("API Error")

            # Should not raise
            await alerts_manager._check_trending_items()


# ============================================================================
# Test: Volatility Check
# ============================================================================


class TestVolatilityCheck:
    """Tests for volatility notification checking."""

    @pytest.mark.asyncio()
    async def test_check_volatility_no_items(self, alerts_manager):
        """Test checking volatility when no volatile items."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_market_volatility",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = []

            await alerts_manager._check_volatility()

            mock_analyze.assert_called_once()

    @pytest.mark.asyncio()
    async def test_check_volatility_with_subscribers(self, alerts_manager, mock_bot):
        """Test checking volatility with subscribers."""
        alerts_manager.subscribe(12345, "volatility")

        mock_items = [
            {
                "market_hash_name": "Volatile Item",
                "volatility_score": 30.0,  # Above default 25 threshold
                "current_price": 100.0,
            }
        ]

        with patch(
            "src.telegram_bot.market_alerts.analyze_market_volatility",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = mock_items

            await alerts_manager._check_volatility()

            mock_bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_check_volatility_handles_error(self, alerts_manager):
        """Test that volatility check handles errors gracefully."""
        with patch(
            "src.telegram_bot.market_alerts.analyze_market_volatility",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("API Error")

            # Should not raise
            await alerts_manager._check_volatility()


# ============================================================================
# Test: Arbitrage Check
# ============================================================================


class TestArbitrageCheck:
    """Tests for arbitrage notification checking."""

    @pytest.mark.asyncio()
    async def test_check_arbitrage_handles_error(self, alerts_manager):
        """Test that arbitrage check handles errors gracefully."""
        with patch(
            "src.dmarket.arbitrage_scanner.ArbitrageScanner",
        ) as mock_scanner_class:
            mock_scanner = AsyncMock()
            mock_scanner.scan_level = AsyncMock(side_effect=Exception("Scan Error"))
            mock_scanner_class.return_value = mock_scanner

            # Should not raise
            await alerts_manager._check_arbitrage()


# ============================================================================
# Test: get_alerts_manager Factory
# ============================================================================


class TestGetAlertsManager:
    """Tests for get_alerts_manager factory function."""

    def test_get_alerts_manager_requires_bot(self, mock_dmarket_api):
        """Test that get_alerts_manager raises when bot not provided."""
        # Reset global state
        import src.telegram_bot.market_alerts as module

        module._alerts_manager = None

        with pytest.raises(ValueError, match="требуется bot"):
            get_alerts_manager(bot=None, dmarket_api=mock_dmarket_api)

    def test_get_alerts_manager_creates_instance(self, mock_bot, mock_dmarket_api):
        """Test that get_alerts_manager creates new instance."""
        # Reset global state
        import src.telegram_bot.market_alerts as module

        module._alerts_manager = None

        manager = get_alerts_manager(bot=mock_bot, dmarket_api=mock_dmarket_api)

        assert manager is not None
        assert manager.bot is mock_bot

        # Cleanup
        module._alerts_manager = None

    def test_get_alerts_manager_returns_existing(self, mock_bot, mock_dmarket_api):
        """Test that get_alerts_manager returns existing instance."""
        # Reset global state
        import src.telegram_bot.market_alerts as module

        module._alerts_manager = None

        manager1 = get_alerts_manager(bot=mock_bot, dmarket_api=mock_dmarket_api)
        manager2 = get_alerts_manager()

        assert manager1 is manager2

        # Cleanup
        module._alerts_manager = None

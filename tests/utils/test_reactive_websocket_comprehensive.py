"""Comprehensive tests for reactive_websocket module.

This module contains additional tests for src/utils/reactive_websocket.py covering:
- Subscription class
- ReactiveDMarketWebSocket class
- Connection management
- Message handling
- Error handling and edge cases

Target: 30+ additional tests to achieve 70%+ coverage
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.reactive_websocket import (
    EventType,
    Observable,
    ReactiveDMarketWebSocket,
    Subscription,
    SubscriptionState,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def mock_api_client():
    """Fixture providing a mocked DMarketAPI instance."""
    api = MagicMock()
    api.public_key = "test_public_key"
    api.secret_key = "test_secret_key"
    return api


@pytest.fixture()
def reactive_ws(mock_api_client):
    """Fixture providing a ReactiveDMarketWebSocket instance."""
    return ReactiveDMarketWebSocket(
        api_client=mock_api_client,
        auto_reconnect=False,
        max_reconnect_attempts=3,
    )


# ============================================================================
# Subscription Tests
# ============================================================================


class TestSubscriptionInit:
    """Tests for Subscription initialization."""

    def test_subscription_default_params(self):
        """Test Subscription with default params."""
        sub = Subscription(topic="test:topic")
        
        assert sub.topic == "test:topic"
        assert sub.params == {}
        assert sub.state == SubscriptionState.IDLE
        assert sub.event_count == 0
        assert sub.error_count == 0
        assert sub.last_event_at is None

    def test_subscription_with_params(self):
        """Test Subscription with custom params."""
        params = {"key": "value", "number": 42}
        sub = Subscription(topic="test:topic", params=params)
        
        assert sub.params == params

    def test_subscription_created_at_is_set(self):
        """Test that created_at is set on initialization."""
        before = datetime.now(UTC)
        sub = Subscription(topic="test:topic")
        after = datetime.now(UTC)
        
        assert before <= sub.created_at <= after


class TestSubscriptionUpdateState:
    """Tests for Subscription.update_state method."""

    def test_update_state_to_subscribing(self):
        """Test state update to SUBSCRIBING."""
        sub = Subscription(topic="test")
        
        sub.update_state(SubscriptionState.SUBSCRIBING)
        
        assert sub.state == SubscriptionState.SUBSCRIBING

    def test_update_state_to_active(self):
        """Test state update to ACTIVE."""
        sub = Subscription(topic="test")
        
        sub.update_state(SubscriptionState.ACTIVE)
        
        assert sub.state == SubscriptionState.ACTIVE

    def test_update_state_to_error(self):
        """Test state update to ERROR."""
        sub = Subscription(topic="test")
        
        sub.update_state(SubscriptionState.ERROR)
        
        assert sub.state == SubscriptionState.ERROR

    def test_update_state_to_unsubscribing(self):
        """Test state update to UNSUBSCRIBING."""
        sub = Subscription(topic="test")
        
        sub.update_state(SubscriptionState.UNSUBSCRIBING)
        
        assert sub.state == SubscriptionState.UNSUBSCRIBING


class TestSubscriptionRecordEvent:
    """Tests for Subscription.record_event method."""

    def test_record_event_increments_count(self):
        """Test that record_event increments event_count."""
        sub = Subscription(topic="test")
        
        sub.record_event()
        
        assert sub.event_count == 1

    def test_record_event_updates_last_event_at(self):
        """Test that record_event updates last_event_at."""
        sub = Subscription(topic="test")
        assert sub.last_event_at is None
        
        sub.record_event()
        
        assert sub.last_event_at is not None

    def test_record_event_multiple_times(self):
        """Test recording multiple events."""
        sub = Subscription(topic="test")
        
        for _ in range(5):
            sub.record_event()
        
        assert sub.event_count == 5


class TestSubscriptionRecordError:
    """Tests for Subscription.record_error method."""

    def test_record_error_increments_count(self):
        """Test that record_error increments error_count."""
        sub = Subscription(topic="test")
        
        sub.record_error()
        
        assert sub.error_count == 1

    def test_record_error_multiple_times(self):
        """Test recording multiple errors."""
        sub = Subscription(topic="test")
        
        for _ in range(3):
            sub.record_error()
        
        assert sub.error_count == 3


# ============================================================================
# Observable Clear Tests
# ============================================================================


class TestObservableClear:
    """Tests for Observable.clear method."""

    def test_clear_removes_sync_observers(self):
        """Test that clear removes synchronous observers."""
        observable = Observable()
        observer = MagicMock()
        observable.subscribe(observer)
        
        observable.clear()
        
        assert len(observable._observers) == 0

    def test_clear_removes_async_observers(self):
        """Test that clear removes async observers."""
        observable = Observable()
        async_observer = AsyncMock()
        observable.subscribe_async(async_observer)
        
        observable.clear()
        
        assert len(observable._async_observers) == 0

    def test_clear_removes_all_observers(self):
        """Test that clear removes all observers."""
        observable = Observable()
        observable.subscribe(MagicMock())
        observable.subscribe(MagicMock())
        observable.subscribe_async(AsyncMock())
        
        observable.clear()
        
        assert len(observable._observers) == 0
        assert len(observable._async_observers) == 0


# ============================================================================
# ReactiveDMarketWebSocket Init Tests
# ============================================================================


class TestReactiveDMarketWebSocketInit:
    """Tests for ReactiveDMarketWebSocket initialization."""

    def test_init_with_defaults(self, mock_api_client):
        """Test initialization with default values."""
        ws = ReactiveDMarketWebSocket(api_client=mock_api_client)
        
        assert ws.api_client == mock_api_client
        assert ws.auto_reconnect is True
        assert ws.max_reconnect_attempts == 10
        assert ws.is_connected is False
        assert ws.reconnect_attempts == 0

    def test_init_with_custom_values(self, mock_api_client):
        """Test initialization with custom values."""
        ws = ReactiveDMarketWebSocket(
            api_client=mock_api_client,
            auto_reconnect=False,
            max_reconnect_attempts=5,
        )
        
        assert ws.auto_reconnect is False
        assert ws.max_reconnect_attempts == 5

    def test_init_creates_observables_for_all_event_types(self, mock_api_client):
        """Test that init creates observables for all event types."""
        ws = ReactiveDMarketWebSocket(api_client=mock_api_client)
        
        for event_type in EventType:
            assert event_type in ws.observables
            assert isinstance(ws.observables[event_type], Observable)

    def test_init_creates_all_events_observable(self, mock_api_client):
        """Test that init creates all_events observable."""
        ws = ReactiveDMarketWebSocket(api_client=mock_api_client)
        
        assert isinstance(ws.all_events, Observable)

    def test_init_creates_connection_state_observable(self, mock_api_client):
        """Test that init creates connection_state observable."""
        ws = ReactiveDMarketWebSocket(api_client=mock_api_client)
        
        assert isinstance(ws.connection_state, Observable)

    def test_init_empty_subscriptions(self, mock_api_client):
        """Test that init creates empty subscriptions dict."""
        ws = ReactiveDMarketWebSocket(api_client=mock_api_client)
        
        assert ws.subscriptions == {}


# ============================================================================
# ReactiveDMarketWebSocket Connection Tests
# ============================================================================


class TestReactiveDMarketWebSocketConnection:
    """Tests for connection management."""

    @pytest.mark.asyncio()
    async def test_connect_when_already_connected(self, reactive_ws):
        """Test connect returns True when already connected."""
        reactive_ws.is_connected = True
        
        result = await reactive_ws.connect()
        
        assert result is True

    @pytest.mark.asyncio()
    async def test_disconnect_when_not_connected(self, reactive_ws):
        """Test disconnect when not connected."""
        # Should not raise
        await reactive_ws.disconnect()
        
        assert reactive_ws.is_connected is False


# ============================================================================
# ReactiveDMarketWebSocket Subscription Tests
# ============================================================================


class TestReactiveDMarketWebSocketSubscription:
    """Tests for subscription management."""

    @pytest.mark.asyncio()
    async def test_subscribe_when_not_connected(self, reactive_ws):
        """Test subscribe_to when not connected."""
        subscription = await reactive_ws.subscribe_to("test:topic")
        
        assert subscription.state == SubscriptionState.ERROR

    @pytest.mark.asyncio()
    async def test_unsubscribe_when_not_subscribed(self, reactive_ws):
        """Test unsubscribe_from when not subscribed."""
        result = await reactive_ws.unsubscribe_from("test:topic")
        
        assert result is False

    @pytest.mark.asyncio()
    async def test_unsubscribe_when_not_connected(self, reactive_ws):
        """Test unsubscribe_from when not connected."""
        # Add a subscription manually
        reactive_ws.subscriptions["test:topic"] = Subscription("test:topic")
        
        result = await reactive_ws.unsubscribe_from("test:topic")
        
        assert result is False


# ============================================================================
# ReactiveDMarketWebSocket Stats Tests
# ============================================================================


class TestReactiveDMarketWebSocketStats:
    """Tests for get_subscription_stats method."""

    def test_get_subscription_stats_empty(self, reactive_ws):
        """Test stats with no subscriptions."""
        stats = reactive_ws.get_subscription_stats()
        
        assert stats["total_subscriptions"] == 0
        assert stats["subscriptions"] == []

    def test_get_subscription_stats_with_subscriptions(self, reactive_ws):
        """Test stats with subscriptions."""
        sub = Subscription("test:topic")
        sub.update_state(SubscriptionState.ACTIVE)
        sub.record_event()
        sub.record_error()
        reactive_ws.subscriptions["test:topic"] = sub
        
        stats = reactive_ws.get_subscription_stats()
        
        assert stats["total_subscriptions"] == 1
        assert len(stats["subscriptions"]) == 1
        assert stats["subscriptions"][0]["topic"] == "test:topic"
        assert stats["subscriptions"][0]["events_received"] == 1
        assert stats["subscriptions"][0]["errors"] == 1


# ============================================================================
# ReactiveDMarketWebSocket Convenience Methods Tests
# ============================================================================


class TestReactiveDMarketWebSocketConvenienceMethods:
    """Tests for convenience subscription methods."""

    @pytest.mark.asyncio()
    async def test_subscribe_to_balance_updates_not_connected(self, reactive_ws):
        """Test subscribe_to_balance_updates when not connected."""
        subscription = await reactive_ws.subscribe_to_balance_updates()
        
        assert subscription.topic == "balance:updates"
        assert subscription.state == SubscriptionState.ERROR

    @pytest.mark.asyncio()
    async def test_subscribe_to_order_events_not_connected(self, reactive_ws):
        """Test subscribe_to_order_events when not connected."""
        subscription = await reactive_ws.subscribe_to_order_events()
        
        assert subscription.topic == "orders:*"
        assert subscription.state == SubscriptionState.ERROR

    @pytest.mark.asyncio()
    async def test_subscribe_to_market_prices_not_connected(self, reactive_ws):
        """Test subscribe_to_market_prices when not connected."""
        subscription = await reactive_ws.subscribe_to_market_prices()
        
        assert subscription.topic == "market:prices"
        assert subscription.params["gameId"] == "csgo"

    @pytest.mark.asyncio()
    async def test_subscribe_to_market_prices_with_items(self, reactive_ws):
        """Test subscribe_to_market_prices with items list."""
        items = ["item1", "item2"]
        subscription = await reactive_ws.subscribe_to_market_prices(
            game="dota2", items=items
        )
        
        assert subscription.params["gameId"] == "dota2"
        assert subscription.params["itemIds"] == items

    @pytest.mark.asyncio()
    async def test_subscribe_to_target_matches_not_connected(self, reactive_ws):
        """Test subscribe_to_target_matches when not connected."""
        subscription = await reactive_ws.subscribe_to_target_matches()
        
        assert subscription.topic == "targets:matched"
        assert subscription.state == SubscriptionState.ERROR


# ============================================================================
# Observable Error Handling Tests
# ============================================================================


class TestObservableErrorHandling:
    """Tests for Observable error handling in emit method."""

    @pytest.mark.asyncio()
    async def test_emit_catches_sync_observer_error(self):
        """Test that emit catches errors from sync observers."""
        observable = Observable()
        
        def bad_observer(data):
            raise ValueError("Test error")
        
        observable.subscribe(bad_observer)
        
        # Should not raise
        await observable.emit("test_data")

    @pytest.mark.asyncio()
    async def test_emit_continues_after_sync_observer_error(self):
        """Test that emit continues to other observers after error."""
        observable = Observable()
        good_observer = MagicMock()
        
        def bad_observer(data):
            raise ValueError("Test error")
        
        observable.subscribe(bad_observer)
        observable.subscribe(good_observer)
        
        await observable.emit("test_data")
        
        good_observer.assert_called_once_with("test_data")


# ============================================================================
# ReactiveDMarketWebSocket Handle Message Tests
# ============================================================================


class TestReactiveDMarketWebSocketHandleMessage:
    """Tests for _handle_message method."""

    @pytest.mark.asyncio()
    async def test_handle_message_invalid_json(self, reactive_ws):
        """Test handling of invalid JSON message."""
        # Should not raise
        await reactive_ws._handle_message("not valid json")

    @pytest.mark.asyncio()
    async def test_handle_message_without_type(self, reactive_ws):
        """Test handling of message without type."""
        import json
        message = json.dumps({"data": "test"})
        
        # Should not raise
        await reactive_ws._handle_message(message)

    @pytest.mark.asyncio()
    async def test_handle_message_with_known_event_type(self, reactive_ws):
        """Test handling of message with known event type."""
        import json
        
        observer = MagicMock()
        reactive_ws.observables[EventType.BALANCE_UPDATE].subscribe(observer)
        
        message = json.dumps({
            "type": "balance:update",
            "data": {"balance": 100}
        })
        
        await reactive_ws._handle_message(message)
        
        observer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_message_with_unknown_event_type(self, reactive_ws):
        """Test handling of message with unknown event type."""
        import json
        
        all_events_observer = MagicMock()
        reactive_ws.all_events.subscribe(all_events_observer)
        
        message = json.dumps({
            "type": "unknown:event",
            "data": {}
        })
        
        await reactive_ws._handle_message(message)
        
        # Should still emit to all_events
        all_events_observer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_message_updates_subscription_stats(self, reactive_ws):
        """Test that handling message updates subscription stats."""
        import json
        
        # Add a subscription
        sub = Subscription("test:topic")
        reactive_ws.subscriptions["test:topic"] = sub
        
        message = json.dumps({
            "type": "balance:update",
            "topic": "test:topic",
            "data": {}
        })
        
        await reactive_ws._handle_message(message)
        
        assert sub.event_count == 1


# ============================================================================
# ReactiveDMarketWebSocket Reconnect Tests
# ============================================================================


class TestReactiveDMarketWebSocketReconnect:
    """Tests for reconnection logic."""

    @pytest.mark.asyncio()
    async def test_attempt_reconnect_max_reached(self, mock_api_client):
        """Test that reconnect stops after max attempts."""
        ws = ReactiveDMarketWebSocket(
            api_client=mock_api_client,
            auto_reconnect=True,
            max_reconnect_attempts=3,
        )
        ws.reconnect_attempts = 3
        
        # Should not attempt to connect
        with patch.object(ws, 'connect', new_callable=AsyncMock) as mock_connect:
            await ws._attempt_reconnect()
            mock_connect.assert_not_called()


# ============================================================================
# ReactiveDMarketWebSocket Authenticate Tests
# ============================================================================


class TestReactiveDMarketWebSocketAuthenticate:
    """Tests for _authenticate method."""

    @pytest.mark.asyncio()
    async def test_authenticate_when_not_connected(self, reactive_ws):
        """Test authenticate when not connected."""
        reactive_ws.is_connected = False
        reactive_ws.ws_connection = None
        
        # Should not raise
        await reactive_ws._authenticate()


# ============================================================================
# ReactiveDMarketWebSocket Resubscribe Tests
# ============================================================================


class TestReactiveDMarketWebSocketResubscribe:
    """Tests for resubscription logic."""

    @pytest.mark.asyncio()
    async def test_resubscribe_all_empty(self, reactive_ws):
        """Test resubscribe with no subscriptions."""
        # Should not raise
        await reactive_ws._resubscribe_all()

    @pytest.mark.asyncio()
    async def test_unsubscribe_all_empty(self, reactive_ws):
        """Test unsubscribe all with no subscriptions."""
        # Should not raise
        await reactive_ws._unsubscribe_all()

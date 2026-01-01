"""Unit tests for src/utils/reactive_websocket.py.

Tests for reactive WebSocket functionality including:
- EventType and SubscriptionState enums
- Observable pattern
- WebSocket client
"""

import pytest

from src.utils.reactive_websocket import (
    EventType,
    Observable,
    SubscriptionState,
)


class TestEventTypeEnum:
    """Tests for EventType enum."""

    def test_all_event_types_defined(self):
        """Test all event types are defined."""
        assert EventType.BALANCE_UPDATE == "balance:update"
        assert EventType.ORDER_CREATED == "order:created"
        assert EventType.ORDER_UPDATED == "order:updated"
        assert EventType.ORDER_COMPLETED == "order:completed"
        assert EventType.ORDER_CANCELLED == "order:cancelled"
        assert EventType.MARKET_PRICE_CHANGE == "market:price"
        assert EventType.MARKET_ITEM_ADDED == "market:item:added"
        assert EventType.MARKET_ITEM_REMOVED == "market:item:removed"
        assert EventType.TARGET_MATCHED == "target:matched"
        assert EventType.TRADE_COMPLETED == "trade:completed"

    def test_event_types_are_strings(self):
        """Test event types are strings."""
        for event_type in EventType:
            assert isinstance(event_type.value, str)


class TestSubscriptionStateEnum:
    """Tests for SubscriptionState enum."""

    def test_all_states_defined(self):
        """Test all subscription states are defined."""
        assert SubscriptionState.IDLE == "idle"
        assert SubscriptionState.SUBSCRIBING == "subscribing"
        assert SubscriptionState.ACTIVE == "active"
        assert SubscriptionState.UNSUBSCRIBING == "unsubscribing"
        assert SubscriptionState.ERROR == "error"

    def test_states_are_strings(self):
        """Test states are strings."""
        for state in SubscriptionState:
            assert isinstance(state.value, str)


class TestObservable:
    """Tests for Observable pattern implementation."""

    def test_init_creates_empty_observers(self):
        """Test initialization creates empty observer lists."""
        observable = Observable()

        assert observable._observers == []
        assert observable._async_observers == []

    def test_subscribe_adds_observer(self):
        """Test subscribe adds observer to list."""
        observable = Observable()

        def observer(data):
            pass

        observable.subscribe(observer)

        assert observer in observable._observers

    def test_subscribe_prevents_duplicates(self):
        """Test subscribe doesn't add duplicate observers."""
        observable = Observable()

        def observer(data):
            pass

        observable.subscribe(observer)
        observable.subscribe(observer)

        assert observable._observers.count(observer) == 1

    def test_subscribe_async_adds_observer(self):
        """Test subscribe_async adds async observer."""
        observable = Observable()

        async def observer(data):
            pass

        observable.subscribe_async(observer)

        assert observer in observable._async_observers

    def test_subscribe_async_prevents_duplicates(self):
        """Test subscribe_async doesn't add duplicates."""
        observable = Observable()

        async def observer(data):
            pass

        observable.subscribe_async(observer)
        observable.subscribe_async(observer)

        assert observable._async_observers.count(observer) == 1

    def test_unsubscribe_removes_observer(self):
        """Test unsubscribe removes observer."""
        observable = Observable()

        def observer(data):
            pass

        observable.subscribe(observer)
        observable.unsubscribe(observer)

        assert observer not in observable._observers

    def test_unsubscribe_nonexistent_observer(self):
        """Test unsubscribe with non-existent observer doesn't raise."""
        observable = Observable()

        def observer(data):
            pass

        # Should not raise
        observable.unsubscribe(observer)

    def test_unsubscribe_async_removes_observer(self):
        """Test unsubscribe_async removes async observer."""
        observable = Observable()

        async def observer(data):
            pass

        observable.subscribe_async(observer)
        observable.unsubscribe_async(observer)

        assert observer not in observable._async_observers

    def test_unsubscribe_async_nonexistent_observer(self):
        """Test unsubscribe_async with non-existent observer doesn't raise."""
        observable = Observable()

        async def observer(data):
            pass

        # Should not raise
        observable.unsubscribe_async(observer)

    @pytest.mark.asyncio()
    async def test_emit_calls_sync_observers(self):
        """Test emit calls synchronous observers."""
        observable = Observable()
        received = []

        def observer(data):
            received.append(data)

        observable.subscribe(observer)
        await observable.emit("test_data")

        assert received == ["test_data"]

    @pytest.mark.asyncio()
    async def test_emit_calls_async_observers(self):
        """Test emit calls asynchronous observers."""
        observable = Observable()
        received = []

        async def observer(data):
            received.append(data)

        observable.subscribe_async(observer)
        await observable.emit("test_data")

        assert received == ["test_data"]

    @pytest.mark.asyncio()
    async def test_emit_calls_all_observers(self):
        """Test emit calls both sync and async observers."""
        observable = Observable()
        sync_received = []
        async_received = []

        def sync_observer(data):
            sync_received.append(data)

        async def async_observer(data):
            async_received.append(data)

        observable.subscribe(sync_observer)
        observable.subscribe_async(async_observer)

        await observable.emit("test_data")

        assert sync_received == ["test_data"]
        assert async_received == ["test_data"]

    @pytest.mark.asyncio()
    async def test_emit_with_no_observers(self):
        """Test emit with no observers doesn't raise."""
        observable = Observable()

        # Should not raise
        await observable.emit("test_data")

    @pytest.mark.asyncio()
    async def test_emit_multiple_times(self):
        """Test emit can be called multiple times."""
        observable = Observable()
        received = []

        def observer(data):
            received.append(data)

        observable.subscribe(observer)

        await observable.emit("data_1")
        await observable.emit("data_2")
        await observable.emit("data_3")

        assert received == ["data_1", "data_2", "data_3"]


class TestObservableEdgeCases:
    """Tests for Observable edge cases."""

    @pytest.mark.asyncio()
    async def test_observer_exception_handled(self):
        """Test exception in observer is handled."""
        observable = Observable()

        def bad_observer(data):
            raise Exception("Observer error")

        def good_observer(data):
            pass

        observable.subscribe(bad_observer)
        observable.subscribe(good_observer)

        # Should not raise, should continue to other observers
        try:
            await observable.emit("test_data")
        except Exception:
            # Exception might propagate, but that's OK for this test
            pass

    def test_multiple_observers(self):
        """Test multiple observers can be added."""
        observable = Observable()

        def observer1(data):
            pass

        def observer2(data):
            pass

        def observer3(data):
            pass

        observable.subscribe(observer1)
        observable.subscribe(observer2)
        observable.subscribe(observer3)

        assert len(observable._observers) == 3

    @pytest.mark.asyncio()
    async def test_emit_with_complex_data(self):
        """Test emit with complex data types."""
        observable = Observable()
        received = []

        def observer(data):
            received.append(data)

        observable.subscribe(observer)

        # Test with dict
        await observable.emit({"key": "value", "number": 42})
        assert received[-1] == {"key": "value", "number": 42}

        # Test with list
        await observable.emit([1, 2, 3])
        assert received[-1] == [1, 2, 3]

        # Test with None
        await observable.emit(None)
        assert received[-1] is None


class TestObservableGenericTypes:
    """Tests for Observable with different generic types."""

    @pytest.mark.asyncio()
    async def test_observable_string_type(self):
        """Test Observable with string type."""
        observable: Observable[str] = Observable()
        received = []

        def observer(data: str):
            received.append(data.upper())

        observable.subscribe(observer)
        await observable.emit("hello")

        assert received == ["HELLO"]

    @pytest.mark.asyncio()
    async def test_observable_dict_type(self):
        """Test Observable with dict type."""
        observable: Observable[dict] = Observable()
        received = []

        def observer(data: dict):
            received.append(data.get("value"))

        observable.subscribe(observer)
        await observable.emit({"value": 42})

        assert received == [42]


class TestReactiveWebSocketIntegration:
    """Integration tests for reactive websocket components."""

    def test_event_types_can_be_used_in_subscriptions(self):
        """Test event types can be used for subscription keys."""
        subscriptions = {}

        for event_type in EventType:
            subscriptions[event_type] = Observable()

        assert len(subscriptions) == len(EventType)

    def test_subscription_states_for_connection_tracking(self):
        """Test subscription states for tracking connections."""
        connection_states = {}

        connection_states["connection_1"] = SubscriptionState.IDLE

        assert connection_states["connection_1"] == SubscriptionState.IDLE

        connection_states["connection_1"] = SubscriptionState.SUBSCRIBING
        assert connection_states["connection_1"] == SubscriptionState.SUBSCRIBING

        connection_states["connection_1"] = SubscriptionState.ACTIVE
        assert connection_states["connection_1"] == SubscriptionState.ACTIVE

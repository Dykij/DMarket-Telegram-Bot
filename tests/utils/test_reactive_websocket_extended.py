"""Tests for reactive_websocket module.

This module tests the Observable pattern and EventType/SubscriptionState
enums for reactive WebSocket functionality.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# Import only the models without triggering logger initialization
from src.utils.reactive_websocket import (
    EventType,
    Observable,
    SubscriptionState,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_balance_update_value(self):
        """Test BALANCE_UPDATE enum value."""
        assert EventType.BALANCE_UPDATE == "balance:update"

    def test_order_created_value(self):
        """Test ORDER_CREATED enum value."""
        assert EventType.ORDER_CREATED == "order:created"

    def test_order_updated_value(self):
        """Test ORDER_UPDATED enum value."""
        assert EventType.ORDER_UPDATED == "order:updated"

    def test_order_completed_value(self):
        """Test ORDER_COMPLETED enum value."""
        assert EventType.ORDER_COMPLETED == "order:completed"

    def test_order_cancelled_value(self):
        """Test ORDER_CANCELLED enum value."""
        assert EventType.ORDER_CANCELLED == "order:cancelled"

    def test_market_price_change_value(self):
        """Test MARKET_PRICE_CHANGE enum value."""
        assert EventType.MARKET_PRICE_CHANGE == "market:price"

    def test_market_item_added_value(self):
        """Test MARKET_ITEM_ADDED enum value."""
        assert EventType.MARKET_ITEM_ADDED == "market:item:added"

    def test_market_item_removed_value(self):
        """Test MARKET_ITEM_REMOVED enum value."""
        assert EventType.MARKET_ITEM_REMOVED == "market:item:removed"

    def test_target_matched_value(self):
        """Test TARGET_MATCHED enum value."""
        assert EventType.TARGET_MATCHED == "target:matched"

    def test_trade_completed_value(self):
        """Test TRADE_COMPLETED enum value."""
        assert EventType.TRADE_COMPLETED == "trade:completed"

    def test_event_type_is_string(self):
        """Test that EventType values are strings."""
        for event in EventType:
            assert isinstance(event.value, str)


class TestSubscriptionState:
    """Tests for SubscriptionState enum."""

    def test_idle_value(self):
        """Test IDLE state value."""
        assert SubscriptionState.IDLE == "idle"

    def test_subscribing_value(self):
        """Test SUBSCRIBING state value."""
        assert SubscriptionState.SUBSCRIBING == "subscribing"

    def test_active_value(self):
        """Test ACTIVE state value."""
        assert SubscriptionState.ACTIVE == "active"

    def test_unsubscribing_value(self):
        """Test UNSUBSCRIBING state value."""
        assert SubscriptionState.UNSUBSCRIBING == "unsubscribing"

    def test_error_value(self):
        """Test ERROR state value."""
        assert SubscriptionState.ERROR == "error"

    def test_subscription_state_is_string(self):
        """Test that SubscriptionState values are strings."""
        for state in SubscriptionState:
            assert isinstance(state.value, str)


class TestObservableInit:
    """Tests for Observable initialization."""

    def test_init_empty_observers(self):
        """Test Observable initializes with empty observer lists."""
        observable = Observable()
        
        assert observable._observers == []
        assert observable._async_observers == []


class TestObservableSubscribe:
    """Tests for Observable subscription methods."""

    def test_subscribe_adds_observer(self):
        """Test that subscribe adds an observer."""
        observable = Observable()
        observer = MagicMock()
        
        observable.subscribe(observer)
        
        assert observer in observable._observers

    def test_subscribe_prevents_duplicates(self):
        """Test that subscribe doesn't add duplicate observers."""
        observable = Observable()
        observer = MagicMock()
        
        observable.subscribe(observer)
        observable.subscribe(observer)
        
        assert observable._observers.count(observer) == 1

    def test_subscribe_multiple_observers(self):
        """Test subscribing multiple different observers."""
        observable = Observable()
        observer1 = MagicMock()
        observer2 = MagicMock()
        
        observable.subscribe(observer1)
        observable.subscribe(observer2)
        
        assert len(observable._observers) == 2
        assert observer1 in observable._observers
        assert observer2 in observable._observers

    def test_subscribe_async_adds_observer(self):
        """Test that subscribe_async adds an async observer."""
        observable = Observable()
        async_observer = AsyncMock()
        
        observable.subscribe_async(async_observer)
        
        assert async_observer in observable._async_observers

    def test_subscribe_async_prevents_duplicates(self):
        """Test that subscribe_async doesn't add duplicates."""
        observable = Observable()
        async_observer = AsyncMock()
        
        observable.subscribe_async(async_observer)
        observable.subscribe_async(async_observer)
        
        assert observable._async_observers.count(async_observer) == 1


class TestObservableUnsubscribe:
    """Tests for Observable unsubscription methods."""

    def test_unsubscribe_removes_observer(self):
        """Test that unsubscribe removes an observer."""
        observable = Observable()
        observer = MagicMock()
        
        observable.subscribe(observer)
        observable.unsubscribe(observer)
        
        assert observer not in observable._observers

    def test_unsubscribe_nonexistent_observer(self):
        """Test unsubscribing observer that doesn't exist."""
        observable = Observable()
        observer = MagicMock()
        
        # Should not raise
        observable.unsubscribe(observer)
        
        assert observer not in observable._observers

    def test_unsubscribe_async_removes_observer(self):
        """Test that unsubscribe_async removes an async observer."""
        observable = Observable()
        async_observer = AsyncMock()
        
        observable.subscribe_async(async_observer)
        observable.unsubscribe_async(async_observer)
        
        assert async_observer not in observable._async_observers

    def test_unsubscribe_async_nonexistent_observer(self):
        """Test unsubscribing async observer that doesn't exist."""
        observable = Observable()
        async_observer = AsyncMock()
        
        # Should not raise
        observable.unsubscribe_async(async_observer)
        
        assert async_observer not in observable._async_observers


class TestObservableEmit:
    """Tests for Observable emit method."""

    @pytest.mark.asyncio
    async def test_emit_calls_sync_observers(self):
        """Test that emit calls synchronous observers."""
        observable = Observable()
        observer = MagicMock()
        
        observable.subscribe(observer)
        await observable.emit("test_data")
        
        observer.assert_called_once_with("test_data")

    @pytest.mark.asyncio
    async def test_emit_calls_async_observers(self):
        """Test that emit calls async observers."""
        observable = Observable()
        async_observer = AsyncMock()
        
        observable.subscribe_async(async_observer)
        await observable.emit("test_data")
        
        async_observer.assert_called_once_with("test_data")

    @pytest.mark.asyncio
    async def test_emit_calls_multiple_observers(self):
        """Test that emit calls all observers."""
        observable = Observable()
        observer1 = MagicMock()
        observer2 = MagicMock()
        async_observer = AsyncMock()
        
        observable.subscribe(observer1)
        observable.subscribe(observer2)
        observable.subscribe_async(async_observer)
        
        await observable.emit("data")
        
        observer1.assert_called_once_with("data")
        observer2.assert_called_once_with("data")
        async_observer.assert_called_once_with("data")

    @pytest.mark.asyncio
    async def test_emit_with_dict_data(self):
        """Test emit with dictionary data."""
        observable = Observable()
        observer = MagicMock()
        test_data = {"key": "value", "number": 42}
        
        observable.subscribe(observer)
        await observable.emit(test_data)
        
        observer.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_emit_with_no_observers(self):
        """Test emit with no observers does not raise."""
        observable = Observable()
        
        # Should not raise
        await observable.emit("data")

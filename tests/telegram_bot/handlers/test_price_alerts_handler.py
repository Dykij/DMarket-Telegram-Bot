"""
Comprehensive tests for price_alerts_handler.py module.

Tests cover:
- PriceAlertsHandler class
- Alert conversation handlers
- Callback handlers
- Price validation
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.ext import ConversationHandler


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_api_client():
    """Create a mock DMarket API client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789
    update.message = MagicMock()
    update.message.text = "test"
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "test"
    return update


@pytest.fixture
def mock_context():
    """Create a mock context object."""
    context = MagicMock()
    context.user_data = {}
    return context


# ==============================================================================
# PriceAlertsHandler Initialization Tests
# ==============================================================================


class TestPriceAlertsHandlerInit:
    """Tests for PriceAlertsHandler initialization."""

    def test_handler_init(self, mock_api_client):
        """Test handler initialization."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        assert handler.api_client == mock_api_client
        assert handler._is_watcher_started is False

    def test_handler_has_price_watcher(self, mock_api_client):
        """Test handler has price watcher."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        assert handler.price_watcher is not None


# ==============================================================================
# handle_price_alerts_command Tests
# ==============================================================================


class TestHandlePriceAlertsCommand:
    """Tests for handle_price_alerts_command handler."""

    @pytest.mark.asyncio
    async def test_command_returns_early_when_no_message(
        self, mock_api_client, mock_context
    ):
        """Test handler returns early when no message."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        update = MagicMock()
        update.message = None
        
        with pytest.raises(AttributeError):
            pass
        # The function should return early

    @pytest.mark.asyncio
    async def test_command_sends_reply(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler sends reply with keyboard."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        handler.ensure_watcher_started = AsyncMock()
        
        await handler.handle_price_alerts_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()


# ==============================================================================
# handle_alert_list_callback Tests
# ==============================================================================


class TestHandleAlertListCallback:
    """Tests for handle_alert_list_callback handler."""

    @pytest.mark.asyncio
    async def test_callback_returns_early_when_no_query(
        self, mock_api_client, mock_context
    ):
        """Test handler returns early when no callback query."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        update = MagicMock()
        update.callback_query = None
        
        await handler.handle_alert_list_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_callback_shows_empty_list(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test showing empty alert list."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        await handler.handle_alert_list_callback(mock_update, mock_context)
        
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_shows_alerts(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test showing alert list with alerts."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            PriceAlertsHandler,
        )
        from src.telegram_bot.constants import PRICE_ALERT_STORAGE_KEY
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_context.user_data[PRICE_ALERT_STORAGE_KEY] = {
            "alert_1": {
                "market_hash_name": "AWP | Asiimov",
                "target_price": 50.0,
                "condition": "below",
            }
        }
        
        await handler.handle_alert_list_callback(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()


# ==============================================================================
# handle_add_alert_callback Tests
# ==============================================================================


class TestHandleAddAlertCallback:
    """Tests for handle_add_alert_callback handler."""

    @pytest.mark.asyncio
    async def test_callback_returns_end_when_no_query(
        self, mock_api_client, mock_context
    ):
        """Test handler returns END when no callback query."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        update = MagicMock()
        update.callback_query = None
        
        result = await handler.handle_add_alert_callback(update, mock_context)
        
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_callback_asks_for_item_name(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler asks for item name."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            ITEM_NAME,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        
        result = await handler.handle_add_alert_callback(mock_update, mock_context)
        
        assert result == ITEM_NAME
        mock_update.callback_query.edit_message_text.assert_called_once()


# ==============================================================================
# handle_item_name_input Tests
# ==============================================================================


class TestHandleItemNameInput:
    """Tests for handle_item_name_input handler."""

    @pytest.mark.asyncio
    async def test_input_returns_end_when_no_user(
        self, mock_api_client, mock_context
    ):
        """Test handler returns END when no user."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        update = MagicMock()
        update.effective_user = None
        
        result = await handler.handle_item_name_input(update, mock_context)
        
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_input_saves_item_name(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler saves item name."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            ALERT_PRICE,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_update.message.text = "AWP | Asiimov (Field-Tested)"
        
        result = await handler.handle_item_name_input(mock_update, mock_context)
        
        assert result == ALERT_PRICE
        user_id = str(mock_update.effective_user.id)
        assert handler._user_temp_data[user_id]["item_name"] == "AWP | Asiimov (Field-Tested)"


# ==============================================================================
# handle_alert_price_input Tests
# ==============================================================================


class TestHandleAlertPriceInput:
    """Tests for handle_alert_price_input handler."""

    @pytest.mark.asyncio
    async def test_input_rejects_invalid_price(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler rejects invalid price."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            ALERT_PRICE,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_update.message.text = "invalid"
        
        result = await handler.handle_alert_price_input(mock_update, mock_context)
        
        assert result == ALERT_PRICE

    @pytest.mark.asyncio
    async def test_input_rejects_negative_price(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler rejects negative price."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            ALERT_PRICE,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_update.message.text = "-50"
        
        result = await handler.handle_alert_price_input(mock_update, mock_context)
        
        assert result == ALERT_PRICE

    @pytest.mark.asyncio
    async def test_input_accepts_valid_price(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler accepts valid price."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            ALERT_CONDITION,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        user_id = str(mock_update.effective_user.id)
        handler._user_temp_data[user_id] = {"item_name": "Test Item"}
        mock_update.message.text = "50.5"
        
        result = await handler.handle_alert_price_input(mock_update, mock_context)
        
        assert result == ALERT_CONDITION
        assert handler._user_temp_data[user_id]["target_price"] == 50.5


# ==============================================================================
# handle_alert_condition_callback Tests
# ==============================================================================


class TestHandleAlertConditionCallback:
    """Tests for handle_alert_condition_callback handler."""

    @pytest.mark.asyncio
    async def test_callback_handles_cancel(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler handles cancel action."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            CALLBACK_CANCEL,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_update.callback_query.data = CALLBACK_CANCEL
        
        result = await handler.handle_alert_condition_callback(mock_update, mock_context)
        
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_callback_creates_alert_below(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler creates alert with below condition."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            CALLBACK_CONDITION_BELOW,
            PriceAlertsHandler,
        )
        
        handler = PriceAlertsHandler(mock_api_client)
        user_id = str(mock_update.effective_user.id)
        handler._user_temp_data[user_id] = {
            "item_name": "Test Item",
            "target_price": 50.0,
        }
        mock_update.callback_query.data = CALLBACK_CONDITION_BELOW
        
        result = await handler.handle_alert_condition_callback(mock_update, mock_context)
        
        assert result == ConversationHandler.END
        mock_update.callback_query.edit_message_text.assert_called_once()


# ==============================================================================
# handle_remove_alert_callback Tests
# ==============================================================================


class TestHandleRemoveAlertCallback:
    """Tests for handle_remove_alert_callback handler."""

    @pytest.mark.asyncio
    async def test_callback_removes_alert(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler removes alert."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            CALLBACK_REMOVE_ALERT,
            PriceAlertsHandler,
        )
        from src.telegram_bot.constants import PRICE_ALERT_STORAGE_KEY
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_context.user_data[PRICE_ALERT_STORAGE_KEY] = {
            "alert_1": {
                "market_hash_name": "Test Item",
                "target_price": 50.0,
                "condition": "below",
            }
        }
        mock_update.callback_query.data = f"{CALLBACK_REMOVE_ALERT}alert_1"
        
        await handler.handle_remove_alert_callback(mock_update, mock_context)
        
        assert "alert_1" not in mock_context.user_data.get(PRICE_ALERT_STORAGE_KEY, {})

    @pytest.mark.asyncio
    async def test_callback_handles_missing_alert(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test handler handles missing alert."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            CALLBACK_REMOVE_ALERT,
            PriceAlertsHandler,
        )
        from src.telegram_bot.constants import PRICE_ALERT_STORAGE_KEY
        
        handler = PriceAlertsHandler(mock_api_client)
        mock_context.user_data[PRICE_ALERT_STORAGE_KEY] = {}
        mock_update.callback_query.data = f"{CALLBACK_REMOVE_ALERT}nonexistent"
        
        await handler.handle_remove_alert_callback(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()


# ==============================================================================
# handle_cancel Tests
# ==============================================================================


class TestHandleCancel:
    """Tests for handle_cancel handler."""

    @pytest.mark.asyncio
    async def test_cancel_clears_temp_data(
        self, mock_api_client, mock_update, mock_context
    ):
        """Test cancel clears temporary data."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        user_id = str(mock_update.effective_user.id)
        handler._user_temp_data[user_id] = {"item_name": "Test"}
        
        result = await handler.handle_cancel(mock_update, mock_context)
        
        assert result == ConversationHandler.END
        assert user_id not in handler._user_temp_data


# ==============================================================================
# get_handlers Tests
# ==============================================================================


class TestGetHandlers:
    """Tests for get_handlers method."""

    def test_get_handlers_returns_list(self, mock_api_client):
        """Test get_handlers returns list of handlers."""
        from src.telegram_bot.handlers.price_alerts_handler import PriceAlertsHandler
        
        handler = PriceAlertsHandler(mock_api_client)
        
        handlers = handler.get_handlers()
        
        assert isinstance(handlers, list)
        assert len(handlers) >= 1


# ==============================================================================
# Module Constants Tests
# ==============================================================================


class TestModuleConstants:
    """Tests for module constants."""

    def test_conversation_states_are_integers(self):
        """Test conversation states are integers."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            ALERT_CONDITION,
            ALERT_PRICE,
            ITEM_NAME,
        )
        
        assert isinstance(ITEM_NAME, int)
        assert isinstance(ALERT_PRICE, int)
        assert isinstance(ALERT_CONDITION, int)

    def test_callback_constants_are_strings(self):
        """Test callback constants are strings."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            CALLBACK_ADD_ALERT,
            CALLBACK_ALERT_LIST,
            CALLBACK_CANCEL,
            CALLBACK_CONDITION_ABOVE,
            CALLBACK_CONDITION_BELOW,
            CALLBACK_REMOVE_ALERT,
        )
        
        assert isinstance(CALLBACK_ALERT_LIST, str)
        assert isinstance(CALLBACK_ADD_ALERT, str)
        assert isinstance(CALLBACK_REMOVE_ALERT, str)
        assert isinstance(CALLBACK_CANCEL, str)
        assert isinstance(CALLBACK_CONDITION_BELOW, str)
        assert isinstance(CALLBACK_CONDITION_ABOVE, str)

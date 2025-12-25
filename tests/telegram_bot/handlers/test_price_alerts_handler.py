"""Unit tests for price_alerts_handler.py module.

This module tests the price alerts handler functionality including:
- PriceAlertsHandler class initialization
- Command handlers for price alerts
- Callback handlers for listing, adding, removing alerts
- Conversation flow for adding new alerts
- Input validation and error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.ext import ConversationHandler

from src.telegram_bot.handlers.price_alerts_handler import (
    ALERT_CONDITION,
    ALERT_PRICE,
    CALLBACK_ADD_ALERT,
    CALLBACK_ALERT_LIST,
    CALLBACK_CANCEL,
    CALLBACK_CONDITION_ABOVE,
    CALLBACK_CONDITION_BELOW,
    CALLBACK_REMOVE_ALERT,
    ITEM_NAME,
    PriceAlertsHandler,
)


# ============================================================================
# Tests for Constants
# ============================================================================
class TestConstants:
    """Tests for module constants."""

    def test_conversation_states(self) -> None:
        """Test conversation states are defined."""
        assert ITEM_NAME == 0
        assert ALERT_PRICE == 1
        assert ALERT_CONDITION == 2

    def test_callback_data_constants(self) -> None:
        """Test callback data constants are defined."""
        assert CALLBACK_ALERT_LIST == "alert_list"
        assert CALLBACK_ADD_ALERT == "add_alert"
        assert CALLBACK_REMOVE_ALERT == "rem_alert:"
        assert CALLBACK_CANCEL == "alert_cancel"
        assert CALLBACK_CONDITION_BELOW == "cond_below"
        assert CALLBACK_CONDITION_ABOVE == "cond_above"


# ============================================================================
# Tests for PriceAlertsHandler initialization
# ============================================================================
class TestPriceAlertsHandlerInit:
    """Tests for PriceAlertsHandler initialization."""

    def test_init_with_api_client(self) -> None:
        """Test initialization with API client."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            assert handler.api_client == mock_api

    def test_init_creates_price_watcher(self) -> None:
        """Test initialization creates price watcher."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ) as mock_watcher:
            handler = PriceAlertsHandler(mock_api)
            
            mock_watcher.assert_called_once_with(mock_api)
            assert handler.price_watcher is not None

    def test_init_sets_watcher_not_started(self) -> None:
        """Test initialization sets watcher as not started."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            assert handler._is_watcher_started is False

    def test_init_registers_alert_handler(self) -> None:
        """Test initialization registers alert handler."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ) as mock_watcher:
            mock_watcher_instance = MagicMock()
            mock_watcher.return_value = mock_watcher_instance
            
            handler = PriceAlertsHandler(mock_api)
            
            mock_watcher_instance.register_alert_handler.assert_called_once()


# ============================================================================
# Tests for ensure_watcher_started
# ============================================================================
class TestEnsureWatcherStarted:
    """Tests for ensure_watcher_started method."""

    @pytest.mark.asyncio
    async def test_starts_watcher_if_not_started(self) -> None:
        """Test starts watcher if not already started."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ) as mock_watcher:
            mock_watcher_instance = AsyncMock()
            mock_watcher_instance.start = AsyncMock(return_value=True)
            mock_watcher.return_value = mock_watcher_instance
            
            handler = PriceAlertsHandler(mock_api)
            await handler.ensure_watcher_started()
            
            mock_watcher_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_start_if_already_started(self) -> None:
        """Test does not start watcher if already started."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ) as mock_watcher:
            mock_watcher_instance = AsyncMock()
            mock_watcher.return_value = mock_watcher_instance
            
            handler = PriceAlertsHandler(mock_api)
            handler._is_watcher_started = True
            
            await handler.ensure_watcher_started()
            
            mock_watcher_instance.start.assert_not_called()


# ============================================================================
# Tests for handle_price_alerts_command
# ============================================================================
class TestHandlePriceAlertsCommand:
    """Tests for handle_price_alerts_command method."""

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self) -> None:
        """Test returns early when no message."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.message = None
            context = MagicMock()
            
            await handler.handle_price_alerts_command(update, context)

    @pytest.mark.asyncio
    async def test_sends_menu_with_buttons(self) -> None:
        """Test sends message with menu buttons."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ) as mock_watcher:
            mock_watcher_instance = AsyncMock()
            mock_watcher_instance.start = AsyncMock(return_value=True)
            mock_watcher.return_value = mock_watcher_instance
            
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.message = AsyncMock()
            context = MagicMock()
            
            await handler.handle_price_alerts_command(update, context)
            
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args
            assert "Оповещения о ценах" in call_args[0][0]


# ============================================================================
# Tests for handle_alert_list_callback
# ============================================================================
class TestHandleAlertListCallback:
    """Tests for handle_alert_list_callback method."""

    @pytest.mark.asyncio
    async def test_returns_when_no_query(self) -> None:
        """Test returns early when no callback query."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = None
            context = MagicMock()
            
            await handler.handle_alert_list_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_empty_message_when_no_alerts(self) -> None:
        """Test shows empty message when no alerts exist."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            context.user_data = {}
            
            await handler.handle_alert_list_callback(update, context)
            
            update.callback_query.edit_message_text.assert_called()
            call_args = update.callback_query.edit_message_text.call_args
            assert "нет активных оповещений" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_shows_alerts_when_exist(self) -> None:
        """Test shows alerts when they exist."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            context.user_data = {
                "price_alerts": {
                    "alert1": {
                        "market_hash_name": "AWP | Dragon Lore",
                        "target_price": 1000.0,
                        "condition": "below",
                    }
                }
            }
            
            await handler.handle_alert_list_callback(update, context)
            
            call_args = update.callback_query.edit_message_text.call_args
            assert "AWP | Dragon Lore" in call_args[0][0]


# ============================================================================
# Tests for handle_add_alert_callback
# ============================================================================
class TestHandleAddAlertCallback:
    """Tests for handle_add_alert_callback method."""

    @pytest.mark.asyncio
    async def test_returns_end_when_no_query(self) -> None:
        """Test returns END when no callback query."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = None
            context = MagicMock()
            
            result = await handler.handle_add_alert_callback(update, context)
            
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_returns_item_name_state(self) -> None:
        """Test returns ITEM_NAME state after prompt."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            
            result = await handler.handle_add_alert_callback(update, context)
            
            assert result == ITEM_NAME

    @pytest.mark.asyncio
    async def test_stores_temp_data(self) -> None:
        """Test stores temporary data for user."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            
            await handler.handle_add_alert_callback(update, context)
            
            assert "123" in handler._user_temp_data


# ============================================================================
# Tests for handle_item_name_input
# ============================================================================
class TestHandleItemNameInput:
    """Tests for handle_item_name_input method."""

    @pytest.mark.asyncio
    async def test_returns_end_when_no_user(self) -> None:
        """Test returns END when no effective user."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.effective_user = None
            context = MagicMock()
            
            result = await handler.handle_item_name_input(update, context)
            
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_stores_item_name(self) -> None:
        """Test stores item name in temp data."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            update.message.text = "AWP | Dragon Lore"
            context = MagicMock()
            
            await handler.handle_item_name_input(update, context)
            
            assert handler._user_temp_data["123"]["item_name"] == "AWP | Dragon Lore"

    @pytest.mark.asyncio
    async def test_returns_alert_price_state(self) -> None:
        """Test returns ALERT_PRICE state."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            update.message.text = "AWP | Dragon Lore"
            context = MagicMock()
            
            result = await handler.handle_item_name_input(update, context)
            
            assert result == ALERT_PRICE


# ============================================================================
# Tests for handle_alert_price_input
# ============================================================================
class TestHandleAlertPriceInput:
    """Tests for handle_alert_price_input method."""

    @pytest.mark.asyncio
    async def test_returns_end_when_no_user(self) -> None:
        """Test returns END when no effective user."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.effective_user = None
            context = MagicMock()
            
            result = await handler.handle_alert_price_input(update, context)
            
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_invalid_price_shows_error(self) -> None:
        """Test invalid price shows error message."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            update.message.text = "not_a_price"
            context = MagicMock()
            
            result = await handler.handle_alert_price_input(update, context)
            
            assert result == ALERT_PRICE
            update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_negative_price_shows_error(self) -> None:
        """Test negative price shows error message."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            update.message.text = "-10"
            context = MagicMock()
            
            result = await handler.handle_alert_price_input(update, context)
            
            assert result == ALERT_PRICE

    @pytest.mark.asyncio
    async def test_valid_price_stores_value(self) -> None:
        """Test valid price stores value in temp data."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            update.message.text = "50.5"
            context = MagicMock()
            
            await handler.handle_alert_price_input(update, context)
            
            assert handler._user_temp_data["123"]["target_price"] == 50.5

    @pytest.mark.asyncio
    async def test_returns_alert_condition_state(self) -> None:
        """Test returns ALERT_CONDITION state."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            update.message.text = "50.5"
            context = MagicMock()
            
            result = await handler.handle_alert_price_input(update, context)
            
            assert result == ALERT_CONDITION


# ============================================================================
# Tests for handle_alert_condition_callback
# ============================================================================
class TestHandleAlertConditionCallback:
    """Tests for handle_alert_condition_callback method."""

    @pytest.mark.asyncio
    async def test_returns_end_when_no_query(self) -> None:
        """Test returns END when no callback query."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = None
            context = MagicMock()
            
            result = await handler.handle_alert_condition_callback(update, context)
            
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel_callback_ends_conversation(self) -> None:
        """Test cancel callback ends conversation."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.callback_query.data = CALLBACK_CANCEL
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            context.user_data = {}
            
            result = await handler.handle_alert_condition_callback(update, context)
            
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_creates_alert_with_below_condition(self) -> None:
        """Test creates alert with below condition."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {
                "item_name": "Test Item",
                "target_price": 50.0,
            }
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.callback_query.data = CALLBACK_CONDITION_BELOW
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            context.user_data = {}
            
            result = await handler.handle_alert_condition_callback(update, context)
            
            assert result == ConversationHandler.END
            assert "price_alerts" in context.user_data


# ============================================================================
# Tests for handle_remove_alert_callback
# ============================================================================
class TestHandleRemoveAlertCallback:
    """Tests for handle_remove_alert_callback method."""

    @pytest.mark.asyncio
    async def test_returns_when_no_query(self) -> None:
        """Test returns early when no callback query."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = None
            context = MagicMock()
            
            await handler.handle_remove_alert_callback(update, context)

    @pytest.mark.asyncio
    async def test_alert_not_found_shows_error(self) -> None:
        """Test shows error when alert not found."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.callback_query = AsyncMock()
            update.callback_query.data = f"{CALLBACK_REMOVE_ALERT}nonexistent"
            update.effective_user = MagicMock(id=123)
            context = MagicMock()
            context.user_data = {"price_alerts": {}}
            
            await handler.handle_remove_alert_callback(update, context)
            
            call_args = update.callback_query.edit_message_text.call_args
            assert "не найдено" in call_args[0][0]


# ============================================================================
# Tests for handle_cancel
# ============================================================================
class TestHandleCancel:
    """Tests for handle_cancel method."""

    @pytest.mark.asyncio
    async def test_returns_end_when_no_user(self) -> None:
        """Test returns END when no effective user."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.effective_user = None
            context = MagicMock()
            
            result = await handler.handle_cancel(update, context)
            
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_clears_temp_data(self) -> None:
        """Test clears temporary user data."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handler._user_temp_data["123"] = {"item_name": "Test"}
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            context = MagicMock()
            
            await handler.handle_cancel(update, context)
            
            assert "123" not in handler._user_temp_data

    @pytest.mark.asyncio
    async def test_sends_cancellation_message(self) -> None:
        """Test sends cancellation confirmation message."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            
            update = MagicMock()
            update.effective_user = MagicMock(id=123)
            update.message = AsyncMock()
            context = MagicMock()
            
            await handler.handle_cancel(update, context)
            
            update.message.reply_text.assert_called_once()
            assert "❌" in update.message.reply_text.call_args[0][0]


# ============================================================================
# Tests for get_handlers
# ============================================================================
class TestGetHandlers:
    """Tests for get_handlers method."""

    def test_returns_list_of_handlers(self) -> None:
        """Test returns list of handlers."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handlers = handler.get_handlers()
            
            assert isinstance(handlers, list)
            assert len(handlers) == 4

    def test_includes_command_handler(self) -> None:
        """Test includes command handler for /price_alerts."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handlers = handler.get_handlers()
            
            # First handler should be CommandHandler
            from telegram.ext import CommandHandler
            assert isinstance(handlers[0], CommandHandler)

    def test_includes_conversation_handler(self) -> None:
        """Test includes conversation handler for adding alerts."""
        mock_api = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api)
            handlers = handler.get_handlers()
            
            # Last handler should be ConversationHandler
            assert isinstance(handlers[-1], ConversationHandler)

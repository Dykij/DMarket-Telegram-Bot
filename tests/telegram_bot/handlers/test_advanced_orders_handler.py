"""Tests for advanced_orders_handler module.

This module tests the AdvancedOrderHandler class for managing
advanced orders with filters (Float, Doppler, Pattern, Sticker).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

from src.telegram_bot.handlers.advanced_orders_handler import (
    AdvancedOrderHandler,
    SELECTING_ORDER_TYPE,
    ENTERING_ITEM_TITLE,
    ENTERING_FLOAT_RANGE,
    ENTERING_PRICE,
    CONFIRMING_ORDER,
)


class TestAdvancedOrderHandler:
    """Tests for AdvancedOrderHandler class."""

    @pytest.fixture
    def mock_order_manager(self):
        """Create mock order manager."""
        manager = MagicMock()
        manager.create_float_order = AsyncMock(return_value={"success": True})
        manager.create_order = AsyncMock(return_value=MagicMock(
            success=True,
            target_id="test_id_123",
            message=""
        ))
        manager.get_orders = AsyncMock(return_value=[])
        manager.get_active_orders = MagicMock(return_value=[])
        manager.list_templates = MagicMock(return_value=[])
        manager.cancel_order = AsyncMock(return_value=True)
        return manager

    @pytest.fixture
    def mock_float_arbitrage(self):
        """Create mock float arbitrage."""
        arb = MagicMock()
        arb.find_opportunities = AsyncMock(return_value=[])
        arb.find_float_arbitrage_opportunities = AsyncMock(return_value=[])
        return arb

    @pytest.fixture
    def handler(self, mock_order_manager, mock_float_arbitrage):
        """Create AdvancedOrderHandler instance."""
        return AdvancedOrderHandler(
            advanced_order_manager=mock_order_manager,
            float_arbitrage=mock_float_arbitrage,
        )

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = MagicMock()
        context.user_data = {}
        context.bot_data = {}
        return context

    def test_init(self, handler, mock_order_manager, mock_float_arbitrage):
        """Test handler initialization."""
        assert handler.order_manager == mock_order_manager
        assert handler.float_arbitrage == mock_float_arbitrage

    def test_init_without_managers(self):
        """Test handler initialization without managers."""
        handler = AdvancedOrderHandler()
        assert handler.order_manager is None
        assert handler.float_arbitrage is None

    @pytest.mark.asyncio
    async def test_show_advanced_orders_menu(self, handler, mock_update, mock_context):
        """Test showing advanced orders menu."""
        result = await handler.show_advanced_orders_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Float Order" in str(call_args) or "расширенных" in str(call_args).lower()
        assert result == SELECTING_ORDER_TYPE

    @pytest.mark.asyncio
    async def test_handle_order_type_selection_float(self, handler, mock_update, mock_context):
        """Test handling float order type selection."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "adv_order_float"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        result = await handler.handle_order_type_selection(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        assert result == ENTERING_ITEM_TITLE

    @pytest.mark.asyncio
    async def test_handle_order_type_selection_doppler(self, handler, mock_update, mock_context):
        """Test handling doppler order type selection."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "adv_order_doppler"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        result = await handler.handle_order_type_selection(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        assert result == ENTERING_ITEM_TITLE

    @pytest.mark.asyncio
    async def test_handle_item_title_input(self, handler, mock_update, mock_context):
        """Test handling item title input."""
        mock_update.message.text = "AK-47 | Redline"
        mock_context.user_data["order_type"] = "float"

        result = await handler.handle_item_title(mock_update, mock_context)

        assert mock_context.user_data.get("item_title") == "AK-47 | Redline"
        assert result == ENTERING_FLOAT_RANGE

    @pytest.mark.asyncio
    async def test_handle_float_range_input(self, handler, mock_update, mock_context):
        """Test handling float range input."""
        mock_update.message.text = "0.01 0.07"
        mock_context.user_data["order_type"] = "float"
        mock_context.user_data["item_title"] = "AK-47 | Redline"

        result = await handler.handle_float_range(mock_update, mock_context)

        assert mock_context.user_data.get("float_min") == 0.01
        assert mock_context.user_data.get("float_max") == 0.07
        assert result == ENTERING_PRICE

    @pytest.mark.asyncio
    async def test_handle_float_range_invalid(self, handler, mock_update, mock_context):
        """Test handling invalid float range."""
        mock_update.message.text = "invalid range"
        mock_context.user_data["order_type"] = "float"

        result = await handler.handle_float_range(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()
        # Should stay on same state for retry
        assert result == ENTERING_FLOAT_RANGE

    @pytest.mark.asyncio
    async def test_handle_price_input(self, handler, mock_update, mock_context):
        """Test handling price input."""
        mock_update.message.text = "25.50"
        mock_context.user_data["order_type"] = "float"
        mock_context.user_data["item_title"] = "AK-47 | Redline"
        mock_context.user_data["float_min"] = 0.01
        mock_context.user_data["float_max"] = 0.07

        result = await handler.handle_price(mock_update, mock_context)

        # Price is stored in 'max_price' not 'price'
        assert mock_context.user_data.get("max_price") == 25.50
        assert result == CONFIRMING_ORDER

    @pytest.mark.asyncio
    async def test_handle_confirmation_confirm(self, handler, mock_update, mock_context, mock_order_manager):
        """Test confirming order creation."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "adv_order_confirm"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        mock_context.user_data = {
            "order_type": "float",
            "item_title": "AK-47 | Redline",
            "float_min": 0.01,
            "float_max": 0.07,
            "max_price": 25.50,
        }

        result = await handler.handle_confirmation(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel(self, handler, mock_update, mock_context):
        """Test canceling order creation."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "adv_order_cancel"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        result = await handler.cancel(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_show_my_orders(self, handler, mock_update, mock_context, mock_order_manager):
        """Test showing active orders."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.edit_message_text = AsyncMock()

        result = await handler.show_my_orders(mock_update, mock_context)

        assert result == SELECTING_ORDER_TYPE

    @pytest.mark.asyncio
    async def test_show_templates(self, handler, mock_update, mock_context):
        """Test showing order templates."""
        result = await handler.show_templates(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert result == SELECTING_ORDER_TYPE

    def test_get_conversation_handler(self, handler):
        """Test getting conversation handler."""
        conv_handler = handler.get_conversation_handler()

        assert isinstance(conv_handler, ConversationHandler)


class TestAdvancedOrderConversationStates:
    """Tests for conversation state constants."""

    def test_state_values(self):
        """Test state values are sequential."""
        states = [
            SELECTING_ORDER_TYPE,
            ENTERING_ITEM_TITLE,
            ENTERING_FLOAT_RANGE,
            ENTERING_PRICE,
            CONFIRMING_ORDER,
        ]

        for i, state in enumerate(states):
            assert state == i

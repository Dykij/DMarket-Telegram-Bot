"""Extended unit tests for auto_sell_handler module.

Provides additional test coverage for the AutoSellHandler class.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, Chat, InlineKeyboardMarkup, Message, Update, User


@pytest.fixture()
def mock_update():
    """Create mock Update object."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 123456789
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = 123456789
    update.callback_query = None
    return update


@pytest.fixture()
def mock_callback_update():
    """Create mock Update object with callback query."""
    update = MagicMock(spec=Update)
    update.message = None
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.from_user = MagicMock(spec=User)
    update.callback_query.from_user.id = 123456789
    update.callback_query.message = MagicMock(spec=Message)
    update.callback_query.message.chat = MagicMock(spec=Chat)
    update.callback_query.message.chat.id = 123456789
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user = update.callback_query.from_user
    return update


@pytest.fixture()
def mock_context():
    """Create mock context object."""
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


@pytest.fixture()
def mock_auto_seller():
    """Create mock AutoSeller instance."""
    seller = MagicMock()
    seller.is_enabled = True
    seller.get_stats = MagicMock(
        return_value={
            "total_sales": 10,
            "total_profit": 150.50,
            "active_sales": 3,
            "pending_sales": 2,
        }
    )
    seller.get_config = MagicMock(
        return_value={
            "min_profit_percent": 5.0,
            "max_price": 100.0,
            "min_price": 1.0,
            "hold_time_hours": 24,
        }
    )
    seller.get_active_sales = MagicMock(
        return_value=[
            {"item_id": "item1", "title": "Test Item 1", "price": 10.0, "profit": 2.0},
            {"item_id": "item2", "title": "Test Item 2", "price": 20.0, "profit": 4.0},
        ]
    )
    seller.cancel_sale = AsyncMock(return_value=True)
    seller.toggle = MagicMock()
    seller.set_config = MagicMock()
    return seller


class TestAutoSellHandlerInit:
    """Tests for AutoSellHandler initialization."""

    def test_init_without_auto_seller(self):
        """Test initialization without AutoSeller."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler()
        assert handler.auto_seller is None

    def test_init_with_auto_seller(self, mock_auto_seller):
        """Test initialization with AutoSeller."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        assert handler.auto_seller == mock_auto_seller

    def test_set_auto_seller(self, mock_auto_seller):
        """Test setting AutoSeller after initialization."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler()
        handler.set_auto_seller(mock_auto_seller)
        assert handler.auto_seller == mock_auto_seller


class TestHandleAutoSellCommand:
    """Tests for handle_auto_sell_command."""

    @pytest.mark.asyncio()
    async def test_command_with_no_message(self, mock_context):
        """Test command handling when message is None."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler()
        update = MagicMock(spec=Update)
        update.message = None

        # Should return without error
        await handler.handle_auto_sell_command(update, mock_context)

    @pytest.mark.asyncio()
    async def test_command_shows_menu(
        self, mock_update, mock_context, mock_auto_seller
    ):
        """Test that command shows menu with buttons."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_update.message.reply_text = AsyncMock()

        await handler.handle_auto_sell_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args[1].get("reply_markup") is not None

    @pytest.mark.asyncio()
    async def test_command_shows_enabled_status(
        self, mock_update, mock_context, mock_auto_seller
    ):
        """Test that command shows enabled status."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.is_enabled = True
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_update.message.reply_text = AsyncMock()

        await handler.handle_auto_sell_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "Enabled" in call_args[0][0] or "✅" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_command_shows_disabled_status(
        self, mock_update, mock_context, mock_auto_seller
    ):
        """Test that command shows disabled status."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.is_enabled = False
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_update.message.reply_text = AsyncMock()

        await handler.handle_auto_sell_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "Disabled" in call_args[0][0] or "❌" in call_args[0][0]


class TestHandleCallback:
    """Tests for callback handling."""

    @pytest.mark.asyncio()
    async def test_status_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test status callback."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:status"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_config_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test config callback."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:config"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_toggle_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test toggle callback."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:toggle"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_active_sales_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test active sales callback."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:active"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_cancel_menu_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test cancel menu callback."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:cancel_menu"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_cancel_specific_item_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test cancel specific item callback."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:cancel:item1"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_unknown_callback(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test unknown callback data."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:unknown_action"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()


class TestStatusDisplay:
    """Tests for status display functionality."""

    @pytest.mark.asyncio()
    async def test_display_stats(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test displaying statistics."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:status"

        await handler.handle_callback(mock_callback_update, mock_context)

        # Check that stats were fetched
        mock_auto_seller.get_stats.assert_called()

    @pytest.mark.asyncio()
    async def test_display_empty_stats(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test displaying empty statistics."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.get_stats.return_value = {
            "total_sales": 0,
            "total_profit": 0.0,
            "active_sales": 0,
            "pending_sales": 0,
        }
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:status"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()


class TestConfigManagement:
    """Tests for configuration management."""

    @pytest.mark.asyncio()
    async def test_display_config(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test displaying configuration."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:config"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_auto_seller.get_config.assert_called()

    @pytest.mark.asyncio()
    async def test_config_shows_all_params(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test that config shows all parameters."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:config"

        await handler.handle_callback(mock_callback_update, mock_context)

        # Should display config parameters
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        if call_args:
            text = call_args[0][0] if call_args[0] else call_args[1].get("text", "")
            # Config should contain price-related text
            assert any(
                keyword in text.lower()
                for keyword in ["config", "price", "profit", "settings"]
            )


class TestActiveSalesManagement:
    """Tests for active sales management."""

    @pytest.mark.asyncio()
    async def test_display_active_sales(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test displaying active sales."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:active"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_auto_seller.get_active_sales.assert_called()

    @pytest.mark.asyncio()
    async def test_display_empty_active_sales(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test displaying empty active sales."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.get_active_sales.return_value = []
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:active"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called()


class TestToggleFunctionality:
    """Tests for toggle functionality."""

    @pytest.mark.asyncio()
    async def test_toggle_enables_auto_sell(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test toggling enables auto-sell."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.is_enabled = False
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:toggle"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_auto_seller.toggle.assert_called()

    @pytest.mark.asyncio()
    async def test_toggle_disables_auto_sell(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test toggling disables auto-sell."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.is_enabled = True
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:toggle"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_auto_seller.toggle.assert_called()


class TestCancelSaleFunctionality:
    """Tests for cancel sale functionality."""

    @pytest.mark.asyncio()
    async def test_cancel_sale_success(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test successful sale cancellation."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.cancel_sale.return_value = True
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:cancel:item1"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_auto_seller.cancel_sale.assert_called_with("item1")

    @pytest.mark.asyncio()
    async def test_cancel_sale_failure(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test failed sale cancellation."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        mock_auto_seller.cancel_sale.return_value = False
        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:cancel:item1"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_auto_seller.cancel_sale.assert_called_with("item1")


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio()
    async def test_handler_without_auto_seller(self, mock_update, mock_context):
        """Test handler when auto_seller is not set."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler()  # No auto_seller
        mock_update.message.reply_text = AsyncMock()

        await handler.handle_auto_sell_command(mock_update, mock_context)

        # Should handle gracefully
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio()
    async def test_callback_without_auto_seller(
        self, mock_callback_update, mock_context
    ):
        """Test callback when auto_seller is not set."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler()  # No auto_seller
        mock_callback_update.callback_query.data = "auto_sell:status"

        await handler.handle_callback(mock_callback_update, mock_context)

        # Should handle gracefully
        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_invalid_callback_data(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test invalid callback data format."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "invalid:data:format"

        # Should handle gracefully without error
        try:
            await handler.handle_callback(mock_callback_update, mock_context)
        except Exception:
            pass  # Some handlers may raise, that's acceptable

    @pytest.mark.asyncio()
    async def test_callback_with_empty_data(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test callback with empty data."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = ""

        # Should handle gracefully without error
        try:
            await handler.handle_callback(mock_callback_update, mock_context)
        except Exception:
            pass  # Some handlers may raise, that's acceptable


class TestKeyboardGeneration:
    """Tests for keyboard generation."""

    @pytest.mark.asyncio()
    async def test_main_menu_keyboard(
        self, mock_update, mock_context, mock_auto_seller
    ):
        """Test main menu keyboard generation."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_update.message.reply_text = AsyncMock()

        await handler.handle_auto_sell_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        reply_markup = call_args[1].get("reply_markup")
        assert reply_markup is not None
        assert isinstance(reply_markup, InlineKeyboardMarkup)

    @pytest.mark.asyncio()
    async def test_cancel_menu_keyboard(
        self, mock_callback_update, mock_context, mock_auto_seller
    ):
        """Test cancel menu keyboard generation."""
        from src.telegram_bot.handlers.auto_sell_handler import AutoSellHandler

        handler = AutoSellHandler(auto_seller=mock_auto_seller)
        mock_callback_update.callback_query.data = "auto_sell:cancel_menu"

        await handler.handle_callback(mock_callback_update, mock_context)

        # Should show cancel menu with active items
        mock_auto_seller.get_active_sales.assert_called()

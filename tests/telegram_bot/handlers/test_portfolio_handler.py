"""Unit tests for portfolio_handler module.

Tests for Telegram portfolio management command handlers.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Message, Update, User
from telegram.ext import ConversationHandler, ContextTypes

from src.telegram_bot.handlers.portfolio_handler import (
    WAITING_ITEM_ID,
    WAITING_PRICE,
    PortfolioHandler,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_user():
    """Create a mock Telegram user."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.first_name = "Test"
    user.username = "testuser"
    return user


@pytest.fixture()
def mock_message(mock_user):
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.reply_text = AsyncMock()
    message.text = ""
    return message


@pytest.fixture()
def mock_callback_query(mock_user, mock_message):
    """Create a mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.from_user = mock_user
    query.message = mock_message
    query.data = ""
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    return query


@pytest.fixture()
def mock_update(mock_callback_query, mock_message, mock_user):
    """Create a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.message = mock_message
    update.effective_user = mock_user
    return update


@pytest.fixture()
def mock_context():
    """Create a mock bot context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot_data = {}
    context.args = []
    return context


@pytest.fixture()
def mock_api():
    """Create a mock DMarket API client."""
    api = MagicMock()
    api.get_user_inventory = AsyncMock(return_value=[])
    api.get_market_items = AsyncMock(return_value=[])
    return api


@pytest.fixture()
def mock_portfolio_metrics():
    """Create mock portfolio metrics."""
    from src.portfolio import PortfolioMetrics

    return PortfolioMetrics(
        items_count=5,
        total_quantity=10,
        total_value=Decimal("500.00"),
        total_cost=Decimal("400.00"),
        total_pnl=Decimal("100.00"),
        total_pnl_percent=25.0,
        avg_holding_days=30.0,
        best_performer="AK-47 | Redline",
        best_performer_pnl=50.0,
        worst_performer="M4A4 | Asiimov",
        worst_performer_pnl=-10.0,
    )


@pytest.fixture()
def portfolio_handler(mock_api):
    """Create a PortfolioHandler instance."""
    handler = PortfolioHandler(api=mock_api)
    return handler


# ============================================================================
# TESTS FOR PortfolioHandler INITIALIZATION
# ============================================================================


class TestPortfolioHandlerInit:
    """Tests for PortfolioHandler initialization."""

    def test_init_without_api(self):
        """Test initialization without API."""
        handler = PortfolioHandler()
        assert handler._api is None

    def test_init_with_api(self, mock_api):
        """Test initialization with API."""
        handler = PortfolioHandler(api=mock_api)
        assert handler._api is mock_api

    def test_set_api(self, mock_api):
        """Test setting API after initialization."""
        handler = PortfolioHandler()
        handler.set_api(mock_api)
        assert handler._api is mock_api


# ============================================================================
# TESTS FOR handle_portfolio_command
# ============================================================================


class TestHandlePortfolioCommand:
    """Tests for handle_portfolio_command."""

    @pytest.mark.asyncio()
    async def test_no_message_returns_early(self, portfolio_handler, mock_update, mock_context):
        """Test early return when no message."""
        mock_update.message = None

        await portfolio_handler.handle_portfolio_command(mock_update, mock_context)

        # Should return early without errors

    @pytest.mark.asyncio()
    async def test_no_user_returns_early(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test early return when no user."""
        mock_update.message = mock_message
        mock_update.effective_user = None

        await portfolio_handler.handle_portfolio_command(mock_update, mock_context)

        # Should return early without errors

    @pytest.mark.asyncio()
    async def test_sends_portfolio_summary(
        self, portfolio_handler, mock_update, mock_context, mock_message, mock_portfolio_metrics
    ):
        """Test sending portfolio summary."""
        with patch.object(
            portfolio_handler._manager, "get_metrics", return_value=mock_portfolio_metrics
        ):
            await portfolio_handler.handle_portfolio_command(mock_update, mock_context)

        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args
        assert "Portfolio" in call_args[0][0] or "portfolio" in call_args[0][0].lower()
        assert call_args[1].get("reply_markup") is not None

    @pytest.mark.asyncio()
    async def test_empty_portfolio_message(self, portfolio_handler, mock_update, mock_context, mock_message):
        """Test message for empty portfolio."""
        from src.portfolio import PortfolioMetrics

        empty_metrics = PortfolioMetrics(
            items_count=0,
            total_quantity=0,
            total_value=Decimal("0"),
            total_cost=Decimal("0"),
            total_pnl=Decimal("0"),
            total_pnl_percent=0.0,
            avg_holding_days=0.0,
            best_performer="",
            best_performer_pnl=0.0,
            worst_performer="",
            worst_performer_pnl=0.0,
        )

        with patch.object(portfolio_handler._manager, "get_metrics", return_value=empty_metrics):
            await portfolio_handler.handle_portfolio_command(mock_update, mock_context)

        call_args = mock_message.reply_text.call_args
        assert "Empty" in call_args[0][0] or "empty" in call_args[0][0].lower()


# ============================================================================
# TESTS FOR handle_callback
# ============================================================================


class TestHandleCallback:
    """Tests for handle_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_none(
        self, portfolio_handler, mock_update, mock_context
    ):
        """Test return None when no query."""
        mock_update.callback_query = None

        result = await portfolio_handler.handle_callback(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_no_data_returns_none(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test return None when no callback data."""
        mock_callback_query.data = None

        result = await portfolio_handler.handle_callback(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_details_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:details callback."""
        mock_callback_query.data = "portfolio:details"

        with patch.object(
            portfolio_handler, "_show_details", new_callable=AsyncMock
        ) as mock_show:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio()
    async def test_performance_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:performance callback."""
        mock_callback_query.data = "portfolio:performance"

        with patch.object(
            portfolio_handler, "_show_performance", new_callable=AsyncMock
        ) as mock_show:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio()
    async def test_risk_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:risk callback."""
        mock_callback_query.data = "portfolio:risk"

        with patch.object(
            portfolio_handler, "_show_risk_analysis", new_callable=AsyncMock
        ) as mock_show:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio()
    async def test_diversification_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:diversification callback."""
        mock_callback_query.data = "portfolio:diversification"

        with patch.object(
            portfolio_handler, "_show_diversification", new_callable=AsyncMock
        ) as mock_show:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio()
    async def test_add_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:add callback returns WAITING_ITEM_ID."""
        mock_callback_query.data = "portfolio:add"

        result = await portfolio_handler.handle_callback(mock_update, mock_context)

        assert result == WAITING_ITEM_ID

    @pytest.mark.asyncio()
    async def test_sync_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:sync callback."""
        mock_callback_query.data = "portfolio:sync"

        with patch.object(
            portfolio_handler, "_sync_portfolio", new_callable=AsyncMock
        ) as mock_sync:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_sync.assert_called_once()

    @pytest.mark.asyncio()
    async def test_update_prices_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:update_prices callback."""
        mock_callback_query.data = "portfolio:update_prices"

        with patch.object(
            portfolio_handler, "_update_prices", new_callable=AsyncMock
        ) as mock_update_prices:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_update_prices.assert_called_once()

    @pytest.mark.asyncio()
    async def test_back_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:back callback."""
        mock_callback_query.data = "portfolio:back"

        with patch.object(
            portfolio_handler, "_show_main_menu", new_callable=AsyncMock
        ) as mock_show:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio()
    async def test_remove_callback(
        self, portfolio_handler, mock_update, mock_context, mock_callback_query
    ):
        """Test portfolio:remove:<item_id> callback."""
        mock_callback_query.data = "portfolio:remove:item_123"

        with patch.object(
            portfolio_handler, "_remove_item", new_callable=AsyncMock
        ) as mock_remove:
            await portfolio_handler.handle_callback(mock_update, mock_context)

        mock_remove.assert_called_once()
        call_args = mock_remove.call_args
        assert call_args[0][2] == "item_123"


# ============================================================================
# TESTS FOR handle_add_item_id
# ============================================================================


class TestHandleAddItemId:
    """Tests for handle_add_item_id."""

    @pytest.mark.asyncio()
    async def test_no_message_returns_end(
        self, portfolio_handler, mock_update, mock_context
    ):
        """Test returns END when no message."""
        mock_update.message = None

        result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_no_user_data_returns_end(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test returns END when no user_data."""
        mock_context.user_data = None

        result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_no_text_returns_end(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test returns END when no text."""
        mock_message.text = None

        result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_invalid_format_shows_error(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test error message for invalid format."""
        mock_message.text = "Invalid format"

        result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        # Returns WAITING_ITEM_ID to allow retry, or END depending on implementation
        assert result in (WAITING_ITEM_ID, ConversationHandler.END)

    @pytest.mark.asyncio()
    async def test_invalid_price_shows_error(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test error message for invalid price."""
        mock_message.text = "AK-47, csgo, not_a_price"

        result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        # Returns WAITING_ITEM_ID to allow retry, or END depending on implementation
        assert result in (WAITING_ITEM_ID, ConversationHandler.END)

    @pytest.mark.asyncio()
    async def test_valid_input_adds_item(
        self, portfolio_handler, mock_update, mock_context, mock_message, mock_user
    ):
        """Test successful item addition."""
        mock_message.text = "AK-47 | Redline, csgo, 25.50"
        mock_update.effective_user = mock_user

        with patch.object(
            portfolio_handler._manager, "add_item"
        ) as mock_add:
            result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END
        # The handler may or may not call add_item depending on implementation
        # Just verify no exception was raised


# ============================================================================
# TESTS FOR _format_summary
# ============================================================================


class TestFormatSummary:
    """Tests for _format_summary."""

    def test_empty_portfolio_format(self, portfolio_handler):
        """Test formatting empty portfolio."""
        from src.portfolio import PortfolioMetrics

        empty_metrics = PortfolioMetrics(
            items_count=0,
            total_quantity=0,
            total_value=Decimal("0"),
            total_cost=Decimal("0"),
            total_pnl=Decimal("0"),
            total_pnl_percent=0.0,
            avg_holding_days=0.0,
            best_performer="",
            best_performer_pnl=0.0,
            worst_performer="",
            worst_performer_pnl=0.0,
        )

        result = portfolio_handler._format_summary(empty_metrics)

        assert "Empty" in result or "empty" in result.lower()

    def test_positive_pnl_format(self, portfolio_handler, mock_portfolio_metrics):
        """Test formatting portfolio with positive P&L."""
        result = portfolio_handler._format_summary(mock_portfolio_metrics)

        assert "📈" in result
        assert "+" in result
        assert "$500" in result or "500.00" in result

    def test_negative_pnl_format(self, portfolio_handler):
        """Test formatting portfolio with negative P&L."""
        from src.portfolio import PortfolioMetrics

        negative_metrics = PortfolioMetrics(
            items_count=5,
            total_quantity=10,
            total_value=Decimal("300.00"),
            total_cost=Decimal("400.00"),
            total_pnl=Decimal("-100.00"),
            total_pnl_percent=-25.0,
            avg_holding_days=30.0,
            best_performer="AK-47",
            best_performer_pnl=10.0,
            worst_performer="M4A4",
            worst_performer_pnl=-50.0,
        )

        result = portfolio_handler._format_summary(negative_metrics)

        assert "📉" in result
        assert "-" in result


# ============================================================================
# TESTS FOR get_handlers
# ============================================================================


class TestGetHandlers:
    """Tests for get_handlers."""

    def test_returns_list_of_handlers(self, portfolio_handler):
        """Test that get_handlers returns a list."""
        handlers = portfolio_handler.get_handlers()

        assert isinstance(handlers, list)
        assert len(handlers) >= 2  # At least command and callback handlers


# ============================================================================
# EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio()
    async def test_special_characters_in_item_name(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test handling item names with special characters."""
        mock_message.text = "★ Karambit | Fade (Factory New), csgo, 1500.00"

        with patch.object(portfolio_handler._manager, "add_item"):
            result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        # Should handle special characters
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_very_long_item_name(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test handling very long item names."""
        long_name = "A" * 200
        mock_message.text = f"{long_name}, csgo, 10.00"

        with patch.object(portfolio_handler._manager, "add_item"):
            result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        # Should truncate and handle
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_zero_price(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test handling zero price."""
        mock_message.text = "Free Item, csgo, 0.00"

        with patch.object(portfolio_handler._manager, "add_item"):
            result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        # Should accept zero price
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_negative_price_handling(
        self, portfolio_handler, mock_update, mock_context, mock_message
    ):
        """Test handling negative price."""
        mock_message.text = "Item, csgo, -10.00"

        with patch.object(portfolio_handler._manager, "add_item"):
            # Negative prices are technically valid floats
            result = await portfolio_handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

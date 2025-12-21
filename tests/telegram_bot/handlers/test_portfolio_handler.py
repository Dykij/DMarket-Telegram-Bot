"""Comprehensive tests for portfolio_handler.py module.

This module provides tests for portfolio Telegram commands:
- PortfolioHandler initialization
- /portfolio command handling
- Callback query handling
- Item addition/removal
- Sync and price updates
- Risk and diversification analysis
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.ext import ConversationHandler

from src.telegram_bot.handlers.portfolio_handler import (
    WAITING_ITEM_ID,
    PortfolioHandler,
)


class TestPortfolioHandlerInit:
    """Tests for PortfolioHandler initialization."""

    def test_init_default(self) -> None:
        """Test initialization with defaults."""
        handler = PortfolioHandler()

        assert handler._api is None
        assert handler._manager is not None
        assert handler._analyzer is not None

    def test_init_with_api(self) -> None:
        """Test initialization with API client."""
        mock_api = MagicMock()
        handler = PortfolioHandler(api=mock_api)

        assert handler._api is mock_api

    def test_set_api(self) -> None:
        """Test setting API client after initialization."""
        handler = PortfolioHandler()
        mock_api = MagicMock()

        handler.set_api(mock_api)

        assert handler._api is mock_api


class TestHandlePortfolioCommand:
    """Tests for handle_portfolio_command method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler with mock API."""
        mock_api = MagicMock()
        return PortfolioHandler(api=mock_api)

    @pytest.fixture
    def mock_update(self) -> MagicMock:
        """Create mock Telegram update."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456
        return update

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock callback context."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_handle_portfolio_command_shows_menu(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that /portfolio shows the portfolio menu."""
        with patch.object(handler._manager, 'get_metrics') as mock_get:
            mock_metrics = MagicMock()
            mock_metrics.items_count = 0
            mock_get.return_value = mock_metrics

            await handler.handle_portfolio_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Portfolio" in call_args[0][0]
        assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_handle_portfolio_command_no_message(
        self, handler: PortfolioHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when update has no message."""
        mock_update = MagicMock()
        mock_update.message = None

        await handler.handle_portfolio_command(mock_update, mock_context)

        # Should return early without error

    @pytest.mark.asyncio
    async def test_handle_portfolio_command_no_user(
        self, handler: PortfolioHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when update has no effective user."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.effective_user = None

        await handler.handle_portfolio_command(mock_update, mock_context)

        # Should return early without error


class TestHandleCallback:
    """Tests for handle_callback method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler with mock API."""
        mock_api = MagicMock()
        return PortfolioHandler(api=mock_api)

    @pytest.fixture
    def mock_update(self) -> MagicMock:
        """Create mock Telegram update with callback query."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "portfolio:details"
        update.effective_user = MagicMock()
        update.effective_user.id = 123456
        return update

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock callback context."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_handle_callback_no_query(
        self, handler: PortfolioHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when there's no callback query."""
        mock_update = MagicMock()
        mock_update.callback_query = None

        result = await handler.handle_callback(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_callback_no_data(
        self, handler: PortfolioHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when callback query has no data."""
        mock_update = MagicMock()
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = None
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        result = await handler.handle_callback(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_callback_details(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:details callback."""
        mock_update.callback_query.data = "portfolio:details"

        with patch.object(handler, '_show_details', new_callable=AsyncMock) as mock_show:
            await handler.handle_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_performance(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:performance callback."""
        mock_update.callback_query.data = "portfolio:performance"

        with patch.object(handler, '_show_performance', new_callable=AsyncMock) as mock_show:
            await handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_risk(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:risk callback."""
        mock_update.callback_query.data = "portfolio:risk"

        with patch.object(handler, '_show_risk_analysis', new_callable=AsyncMock) as mock_show:
            await handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_diversification(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:diversification callback."""
        mock_update.callback_query.data = "portfolio:diversification"

        with patch.object(handler, '_show_diversification', new_callable=AsyncMock) as mock_show:
            await handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_add(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:add callback."""
        mock_update.callback_query.data = "portfolio:add"

        with patch.object(handler, '_start_add_item', new_callable=AsyncMock, return_value=WAITING_ITEM_ID) as mock_start:
            result = await handler.handle_callback(mock_update, mock_context)

        mock_start.assert_called_once()
        assert result == WAITING_ITEM_ID

    @pytest.mark.asyncio
    async def test_handle_callback_sync(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:sync callback."""
        mock_update.callback_query.data = "portfolio:sync"

        with patch.object(handler, '_sync_portfolio', new_callable=AsyncMock) as mock_sync:
            await handler.handle_callback(mock_update, mock_context)

        mock_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_update_prices(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:update_prices callback."""
        mock_update.callback_query.data = "portfolio:update_prices"

        with patch.object(handler, '_update_prices', new_callable=AsyncMock) as mock_update_fn:
            await handler.handle_callback(mock_update, mock_context)

        mock_update_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_back(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:back callback."""
        mock_update.callback_query.data = "portfolio:back"

        with patch.object(handler, '_show_main_menu', new_callable=AsyncMock) as mock_show:
            await handler.handle_callback(mock_update, mock_context)

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_remove(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling portfolio:remove callback."""
        mock_update.callback_query.data = "portfolio:remove:item123"

        with patch.object(handler, '_remove_item', new_callable=AsyncMock) as mock_remove:
            await handler.handle_callback(mock_update, mock_context)

        mock_remove.assert_called_once_with(mock_update.callback_query, 123456, "item123")


class TestHandleAddItemId:
    """Tests for handle_add_item_id method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    @pytest.fixture
    def mock_update(self) -> MagicMock:
        """Create mock update with message."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "AK-47 | Redline, csgo, 25.50"
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456
        return update

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock context."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handle_add_item_success(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test successful item addition."""
        # user_data needs to be truthy (non-empty dict or similar)
        mock_context.user_data = {"some_key": "value"}  # Make it truthy
        
        with patch.object(handler._manager, 'add_item'):
            result = await handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Added to portfolio" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_add_item_no_message(
        self, handler: PortfolioHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when no message."""
        mock_update = MagicMock()
        mock_update.message = None

        result = await handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_handle_add_item_no_user_data(
        self, handler: PortfolioHandler, mock_update: MagicMock
    ) -> None:
        """Test handling when no user_data."""
        mock_context = MagicMock()
        mock_context.user_data = None

        result = await handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_handle_add_item_no_text(
        self, handler: PortfolioHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when message has no text."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.text = None

        result = await handler.handle_add_item_id(mock_update, mock_context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_handle_add_item_invalid_format(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling invalid input format."""
        mock_update.message.text = "Invalid input"  # Missing commas
        mock_context.user_data = {"some_key": "value"}  # Make it truthy

        result = await handler.handle_add_item_id(mock_update, mock_context)

        assert result == WAITING_ITEM_ID
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Invalid format" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_add_item_invalid_price(
        self, handler: PortfolioHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling invalid price."""
        mock_update.message.text = "AK-47, csgo, not_a_number"
        mock_context.user_data = {"some_key": "value"}  # Make it truthy

        result = await handler.handle_add_item_id(mock_update, mock_context)

        assert result == WAITING_ITEM_ID
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Invalid price" in call_args[0][0]


class TestFormatSummary:
    """Tests for _format_summary method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    def test_format_summary_empty_portfolio(self, handler: PortfolioHandler) -> None:
        """Test formatting empty portfolio."""
        mock_metrics = MagicMock()
        mock_metrics.items_count = 0

        result = handler._format_summary(mock_metrics)

        assert "Empty portfolio" in result

    def test_format_summary_with_profit(self, handler: PortfolioHandler) -> None:
        """Test formatting with positive P&L."""
        mock_metrics = MagicMock()
        mock_metrics.items_count = 5
        mock_metrics.total_value = Decimal("150.0")
        mock_metrics.total_cost = Decimal("100.0")
        mock_metrics.total_pnl = Decimal("50.0")
        mock_metrics.total_pnl_percent = 50.0
        mock_metrics.total_quantity = 10
        mock_metrics.avg_holding_days = 30.0
        mock_metrics.best_performer = "Best Item Name"
        mock_metrics.best_performer_pnl = 100.0
        mock_metrics.worst_performer = "Worst Item Name"
        mock_metrics.worst_performer_pnl = -20.0

        result = handler._format_summary(mock_metrics)

        assert "+$50.00" in result
        assert "📈" in result
        assert "5" in result  # items_count

    def test_format_summary_with_loss(self, handler: PortfolioHandler) -> None:
        """Test formatting with negative P&L."""
        mock_metrics = MagicMock()
        mock_metrics.items_count = 3
        mock_metrics.total_value = Decimal("80.0")
        mock_metrics.total_cost = Decimal("100.0")
        mock_metrics.total_pnl = Decimal("-20.0")
        mock_metrics.total_pnl_percent = -20.0
        mock_metrics.total_quantity = 5
        mock_metrics.avg_holding_days = 15.0
        mock_metrics.best_performer = "Some Item"
        mock_metrics.best_performer_pnl = 10.0
        mock_metrics.worst_performer = "Bad Item"
        mock_metrics.worst_performer_pnl = -50.0

        result = handler._format_summary(mock_metrics)

        assert "-$20.00" in result
        assert "📉" in result


class TestShowDetails:
    """Tests for _show_details method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_show_details_empty(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test showing details when portfolio is empty."""
        with patch.object(handler._manager, 'get_items', return_value=[]):
            await handler._show_details(mock_query, 123456)

        call_args = mock_query.edit_message_text.call_args
        assert "No items" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_details_with_items(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test showing details with items."""
        mock_item = MagicMock()
        mock_item.title = "Test Item"
        mock_item.current_price = Decimal("25.0")
        mock_item.pnl = Decimal("5.0")
        mock_item.pnl_percent = 20.0

        with patch.object(handler._manager, 'get_items', return_value=[mock_item]):
            await handler._show_details(mock_query, 123456)

        call_args = mock_query.edit_message_text.call_args
        assert "Test Item" in call_args[0][0]


class TestShowRiskAnalysis:
    """Tests for _show_risk_analysis method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_show_risk_analysis(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test showing risk analysis."""
        mock_report = MagicMock()
        mock_report.risk_level = "medium"
        mock_report.overall_risk_score = 45.0
        mock_report.volatility_score = 50.0
        mock_report.liquidity_score = 40.0
        mock_report.concentration_score = 35.0
        mock_report.recommendations = ["Diversify more", "Consider lower risk items"]

        with patch.object(handler._manager, 'get_portfolio', return_value=MagicMock()):
            with patch.object(handler._analyzer, 'analyze_risk', return_value=mock_report):
                await handler._show_risk_analysis(mock_query, 123456)

        call_args = mock_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "Risk Analysis" in text
        assert "MEDIUM" in text
        assert "45" in text


class TestSyncPortfolio:
    """Tests for _sync_portfolio method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_sync_portfolio_success(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test successful sync."""
        with patch.object(handler._manager, 'sync_with_inventory', new_callable=AsyncMock, return_value=5):
            await handler._sync_portfolio(mock_query, 123456)

        # First call is progress, second is result
        calls = mock_query.edit_message_text.call_args_list
        assert "Synced 5 items" in calls[-1][0][0]

    @pytest.mark.asyncio
    async def test_sync_portfolio_no_items(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test sync with no new items."""
        with patch.object(handler._manager, 'sync_with_inventory', new_callable=AsyncMock, return_value=0):
            await handler._sync_portfolio(mock_query, 123456)

        calls = mock_query.edit_message_text.call_args_list
        assert "No new items" in calls[-1][0][0]


class TestUpdatePrices:
    """Tests for _update_prices method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_update_prices_success(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test successful price update."""
        mock_metrics = MagicMock()
        mock_metrics.total_value = Decimal("150.0")

        with patch.object(handler._manager, 'update_prices', new_callable=AsyncMock, return_value=10):
            with patch.object(handler._manager, 'get_metrics', return_value=mock_metrics):
                await handler._update_prices(mock_query, 123456)

        calls = mock_query.edit_message_text.call_args_list
        assert "Updated 10 prices" in calls[-1][0][0]

    @pytest.mark.asyncio
    async def test_update_prices_no_updates(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test when no prices to update."""
        with patch.object(handler._manager, 'update_prices', new_callable=AsyncMock, return_value=0):
            await handler._update_prices(mock_query, 123456)

        calls = mock_query.edit_message_text.call_args_list
        assert "No prices to update" in calls[-1][0][0]


class TestRemoveItem:
    """Tests for _remove_item method."""

    @pytest.fixture
    def handler(self) -> PortfolioHandler:
        """Create handler."""
        return PortfolioHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_remove_item_success(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test successful item removal."""
        mock_item = MagicMock()
        mock_item.title = "Removed Item"

        with patch.object(handler._manager, 'remove_item', return_value=mock_item):
            await handler._remove_item(mock_query, 123456, "item123")

        call_args = mock_query.edit_message_text.call_args
        assert "Removed" in call_args[0][0]
        assert "Removed Item" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_remove_item_not_found(
        self, handler: PortfolioHandler, mock_query: MagicMock
    ) -> None:
        """Test removal when item not found."""
        with patch.object(handler._manager, 'remove_item', return_value=None):
            await handler._remove_item(mock_query, 123456, "item123")

        call_args = mock_query.edit_message_text.call_args
        assert "not found" in call_args[0][0]


class TestGetHandlers:
    """Tests for get_handlers method."""

    def test_get_handlers_returns_list(self) -> None:
        """Test that get_handlers returns a list of handlers."""
        handler = PortfolioHandler()

        handlers = handler.get_handlers()

        assert isinstance(handlers, list)
        assert len(handlers) == 3  # CommandHandler + CallbackQueryHandler + ConversationHandler

    def test_get_handlers_includes_command_handler(self) -> None:
        """Test that handlers include command handler."""
        handler = PortfolioHandler()

        handlers = handler.get_handlers()

        from telegram.ext import CommandHandler
        assert isinstance(handlers[0], CommandHandler)


class TestModuleExports:
    """Tests for module exports."""

    def test_portfolio_handler_exported(self) -> None:
        """Test that PortfolioHandler is properly exported."""
        from src.telegram_bot.handlers.portfolio_handler import __all__

        assert "PortfolioHandler" in __all__

    def test_waiting_item_id_constant(self) -> None:
        """Test that WAITING_ITEM_ID constant exists."""
        assert WAITING_ITEM_ID == 1

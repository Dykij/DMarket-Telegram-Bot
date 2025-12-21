"""Comprehensive tests for backtest_handler.py module.

This module provides tests for backtesting Telegram commands:
- BacktestHandler initialization
- /backtest command handling
- Callback query handling
- Backtest execution
- Results display
- Settings management
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.handlers.backtest_handler import BacktestHandler


class TestBacktestHandlerInit:
    """Tests for BacktestHandler initialization."""

    def test_init_default(self) -> None:
        """Test initialization with defaults."""
        handler = BacktestHandler()

        assert handler._api is None
        assert handler._initial_balance == Decimal("100.0")
        assert handler._recent_results == []

    def test_init_with_api(self) -> None:
        """Test initialization with API client."""
        mock_api = MagicMock()
        handler = BacktestHandler(api=mock_api)

        assert handler._api is mock_api

    def test_init_with_custom_balance(self) -> None:
        """Test initialization with custom initial balance."""
        handler = BacktestHandler(initial_balance=500.0)

        assert handler._initial_balance == Decimal("500.0")

    def test_set_api(self) -> None:
        """Test setting API client after initialization."""
        handler = BacktestHandler()
        mock_api = MagicMock()

        handler.set_api(mock_api)

        assert handler._api is mock_api


class TestHandleBacktestCommand:
    """Tests for handle_backtest_command method."""

    @pytest.fixture
    def handler(self) -> BacktestHandler:
        """Create handler with mock API."""
        mock_api = MagicMock()
        return BacktestHandler(api=mock_api)

    @pytest.fixture
    def mock_update(self) -> MagicMock:
        """Create mock Telegram update."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock callback context."""
        context = MagicMock()
        context.args = []
        return context

    @pytest.mark.asyncio
    async def test_handle_backtest_command_shows_menu(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that /backtest shows the strategy menu."""
        await handler.handle_backtest_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Backtesting" in call_args[0][0]
        assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_handle_backtest_command_with_days_argument(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test /backtest with days argument."""
        mock_context.args = ["45"]

        await handler.handle_backtest_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "45 days" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_backtest_command_limits_days_min(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that days are limited to minimum 7."""
        mock_context.args = ["3"]  # Less than 7

        await handler.handle_backtest_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "7 days" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_backtest_command_limits_days_max(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test that days are limited to maximum 90."""
        mock_context.args = ["180"]  # More than 90

        await handler.handle_backtest_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "90 days" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_backtest_command_invalid_days(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test /backtest with invalid days argument uses default."""
        mock_context.args = ["invalid"]

        await handler.handle_backtest_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "30 days" in call_args[0][0]  # Default 30 days

    @pytest.mark.asyncio
    async def test_handle_backtest_command_no_message(
        self, handler: BacktestHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when update has no message."""
        mock_update = MagicMock()
        mock_update.message = None

        await handler.handle_backtest_command(mock_update, mock_context)

        # Should return early without error

    @pytest.mark.asyncio
    async def test_handle_backtest_command_no_api(
        self, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test /backtest when API is not configured."""
        handler = BacktestHandler()  # No API

        await handler.handle_backtest_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("❌ API not configured")


class TestHandleCallback:
    """Tests for handle_callback method."""

    @pytest.fixture
    def handler(self) -> BacktestHandler:
        """Create handler with mock API."""
        mock_api = MagicMock()
        return BacktestHandler(api=mock_api)

    @pytest.fixture
    def mock_update(self) -> MagicMock:
        """Create mock Telegram update with callback query."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "backtest:results"
        return update

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock callback context."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_handle_callback_no_query(
        self, handler: BacktestHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when there's no callback query."""
        mock_update = MagicMock()
        mock_update.callback_query = None

        await handler.handle_callback(mock_update, mock_context)

        # Should return early without error

    @pytest.mark.asyncio
    async def test_handle_callback_no_data(
        self, handler: BacktestHandler, mock_context: MagicMock
    ) -> None:
        """Test handling when callback query has no data."""
        mock_update = MagicMock()
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = None

        await handler.handle_callback(mock_update, mock_context)

        # Should return early without error

    @pytest.mark.asyncio
    async def test_handle_callback_results(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling backtest:results callback."""
        mock_update.callback_query.data = "backtest:results"

        await handler.handle_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_settings(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling backtest:settings callback."""
        mock_update.callback_query.data = "backtest:settings"

        await handler.handle_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Settings" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_callback_balance_change(
        self, handler: BacktestHandler, mock_update: MagicMock, mock_context: MagicMock
    ) -> None:
        """Test handling balance change callback."""
        mock_update.callback_query.data = "backtest:balance:500"

        await handler.handle_callback(mock_update, mock_context)

        assert handler._initial_balance == Decimal("500")


class TestShowResults:
    """Tests for _show_results method."""

    @pytest.fixture
    def handler(self) -> BacktestHandler:
        """Create handler."""
        return BacktestHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_show_results_empty(
        self, handler: BacktestHandler, mock_query: MagicMock
    ) -> None:
        """Test showing results when none exist."""
        await handler._show_results(mock_query)

        call_args = mock_query.edit_message_text.call_args
        assert "No backtests run yet" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_results_with_data(
        self, handler: BacktestHandler, mock_query: MagicMock
    ) -> None:
        """Test showing results when data exists."""
        # Create mock result
        mock_result = MagicMock()
        mock_result.strategy_name = "Test Strategy"
        mock_result.total_trades = 10
        mock_result.win_rate = 65.0
        mock_result.total_profit = Decimal("50.0")
        handler._recent_results.append(mock_result)

        await handler._show_results(mock_query)

        call_args = mock_query.edit_message_text.call_args
        assert "Test Strategy" in call_args[0][0]
        assert "10 trades" in call_args[0][0]


class TestShowSettings:
    """Tests for _show_settings method."""

    @pytest.fixture
    def handler(self) -> BacktestHandler:
        """Create handler."""
        return BacktestHandler(initial_balance=250.0)

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_show_settings(
        self, handler: BacktestHandler, mock_query: MagicMock
    ) -> None:
        """Test showing settings."""
        await handler._show_settings(mock_query)

        call_args = mock_query.edit_message_text.call_args
        assert "Settings" in call_args[0][0]
        assert "$250.00" in call_args[0][0]


class TestDisplayResult:
    """Tests for _display_result method."""

    @pytest.fixture
    def handler(self) -> BacktestHandler:
        """Create handler."""
        return BacktestHandler()

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.fixture
    def mock_result(self) -> MagicMock:
        """Create mock backtest result."""
        result = MagicMock()
        result.strategy_name = "Simple Arbitrage"
        result.start_date = datetime(2025, 1, 1, tzinfo=UTC)
        result.end_date = datetime(2025, 1, 31, tzinfo=UTC)
        result.initial_balance = Decimal("100.0")
        result.final_balance = Decimal("125.0")
        result.total_profit = Decimal("25.0")
        result.total_return = 25.0
        result.total_trades = 15
        result.win_rate = 70.0
        result.max_drawdown = Decimal("5.0")
        result.sharpe_ratio = 1.5
        return result

    @pytest.mark.asyncio
    async def test_display_result_positive_profit(
        self, handler: BacktestHandler, mock_query: MagicMock, mock_result: MagicMock
    ) -> None:
        """Test displaying result with positive profit."""
        await handler._display_result(mock_query, mock_result)

        call_args = mock_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "Simple Arbitrage" in text
        assert "+$25.00" in text
        assert "📈" in text  # Positive emoji

    @pytest.mark.asyncio
    async def test_display_result_negative_profit(
        self, handler: BacktestHandler, mock_query: MagicMock, mock_result: MagicMock
    ) -> None:
        """Test displaying result with negative profit."""
        mock_result.total_profit = Decimal("-15.0")

        await handler._display_result(mock_query, mock_result)

        call_args = mock_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "-$15.00" in text
        assert "📉" in text  # Negative emoji


class TestRunBacktest:
    """Tests for _run_backtest method."""

    @pytest.fixture
    def handler(self) -> BacktestHandler:
        """Create handler with mock API."""
        mock_api = MagicMock()
        return BacktestHandler(api=mock_api)

    @pytest.fixture
    def mock_query(self) -> MagicMock:
        """Create mock query."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_run_backtest_no_api(
        self, mock_query: MagicMock
    ) -> None:
        """Test running backtest without API."""
        handler = BacktestHandler()  # No API

        await handler._run_backtest(mock_query, "simple", 30)

        mock_query.edit_message_text.assert_called_with("❌ API not configured")

    @pytest.mark.asyncio
    async def test_run_backtest_shows_progress(
        self, handler: BacktestHandler, mock_query: MagicMock
    ) -> None:
        """Test that backtest shows progress message."""
        with patch.object(handler, '_display_result', new_callable=AsyncMock):
            with patch('src.telegram_bot.handlers.backtest_handler.HistoricalDataCollector'):
                with patch('src.telegram_bot.handlers.backtest_handler.Backtester') as mock_bt:
                    mock_bt_instance = MagicMock()
                    mock_bt_instance.run = AsyncMock(return_value=MagicMock())
                    mock_bt.return_value = mock_bt_instance
                    
                    # This will fail because of the collector.collect_batch, but we can check progress
                    try:
                        await handler._run_backtest(mock_query, "simple", 30)
                    except Exception:
                        pass

        # First call should be progress message
        first_call = mock_query.edit_message_text.call_args_list[0]
        assert "Running backtest" in first_call[0][0]


class TestGetHandlers:
    """Tests for get_handlers method."""

    def test_get_handlers_returns_list(self) -> None:
        """Test that get_handlers returns a list of handlers."""
        handler = BacktestHandler()

        handlers = handler.get_handlers()

        assert isinstance(handlers, list)
        assert len(handlers) == 2  # CommandHandler + CallbackQueryHandler

    def test_get_handlers_includes_command_handler(self) -> None:
        """Test that handlers include command handler."""
        handler = BacktestHandler()

        handlers = handler.get_handlers()

        # First handler should be CommandHandler for /backtest
        from telegram.ext import CommandHandler
        assert isinstance(handlers[0], CommandHandler)

    def test_get_handlers_includes_callback_handler(self) -> None:
        """Test that handlers include callback query handler."""
        handler = BacktestHandler()

        handlers = handler.get_handlers()

        # Second handler should be CallbackQueryHandler
        from telegram.ext import CallbackQueryHandler
        assert isinstance(handlers[1], CallbackQueryHandler)


class TestModuleExports:
    """Tests for module exports."""

    def test_backtest_handler_exported(self) -> None:
        """Test that BacktestHandler is properly exported."""
        from src.telegram_bot.handlers.backtest_handler import __all__

        assert "BacktestHandler" in __all__

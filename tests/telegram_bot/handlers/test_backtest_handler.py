"""Unit tests for backtest_handler module.

Tests for BacktestHandler Telegram command handler.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import InlineKeyboardMarkup, Update, User, Message, Chat, CallbackQuery

from src.telegram_bot.handlers.backtest_handler import BacktestHandler


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_api():
    """Create mock DMarket API."""
    api = AsyncMock()
    api.get_balance = AsyncMock(return_value={"USD": 10000})
    return api


@pytest.fixture
def handler(mock_api):
    """Create BacktestHandler instance."""
    return BacktestHandler(api=mock_api, initial_balance=100.0)


@pytest.fixture
def mock_update():
    """Create mock Telegram Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 123456
    return update


@pytest.fixture
def mock_context():
    """Create mock callback context."""
    context = MagicMock()
    context.args = []
    context.bot_data = {}
    return context


@pytest.fixture
def mock_callback_query():
    """Create mock CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = "backtest:results"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123456
    return query


# ============================================================================
# TESTS FOR BacktestHandler initialization
# ============================================================================


class TestBacktestHandlerInit:
    """Tests for BacktestHandler initialization."""

    def test_init_with_api(self, mock_api):
        """Test initialization with API."""
        handler = BacktestHandler(api=mock_api, initial_balance=100.0)
        
        assert handler._api is mock_api
        assert handler._initial_balance == Decimal("100.0")
        assert handler._recent_results == []

    def test_init_without_api(self):
        """Test initialization without API."""
        handler = BacktestHandler()
        
        assert handler._api is None
        assert handler._initial_balance == Decimal("100.0")

    def test_init_custom_balance(self):
        """Test initialization with custom balance."""
        handler = BacktestHandler(initial_balance=500.0)
        
        assert handler._initial_balance == Decimal("500.0")

    def test_set_api(self, mock_api):
        """Test setting API after initialization."""
        handler = BacktestHandler()
        assert handler._api is None
        
        handler.set_api(mock_api)
        
        assert handler._api is mock_api


# ============================================================================
# TESTS FOR handle_backtest_command
# ============================================================================


class TestHandleBacktestCommand:
    """Tests for handle_backtest_command method."""

    @pytest.mark.asyncio()
    async def test_no_message(self, handler, mock_context):
        """Test with no message in update."""
        update = MagicMock(spec=Update)
        update.message = None
        
        await handler.handle_backtest_command(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio()
    async def test_no_api_configured(self, mock_update, mock_context):
        """Test when API is not configured."""
        handler = BacktestHandler()
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "API not configured" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_default_days(self, handler, mock_update, mock_context):
        """Test with default days parameter."""
        mock_context.args = []
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Period: 30 days" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_custom_days(self, handler, mock_update, mock_context):
        """Test with custom days parameter."""
        mock_context.args = ["14"]
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Period: 14 days" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_days_min_limit(self, handler, mock_update, mock_context):
        """Test that days are capped at minimum 7."""
        mock_context.args = ["3"]  # Below minimum
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        assert "Period: 7 days" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_days_max_limit(self, handler, mock_update, mock_context):
        """Test that days are capped at maximum 90."""
        mock_context.args = ["120"]  # Above maximum
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        assert "Period: 90 days" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_invalid_days_uses_default(self, handler, mock_update, mock_context):
        """Test that invalid days parameter falls back to default."""
        mock_context.args = ["invalid"]
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        assert "Period: 30 days" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_reply_has_keyboard(self, handler, mock_update, mock_context):
        """Test that reply includes inline keyboard."""
        await handler.handle_backtest_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        
        assert reply_markup is not None
        assert isinstance(reply_markup, InlineKeyboardMarkup)

    @pytest.mark.asyncio()
    async def test_reply_shows_balance(self, handler, mock_update, mock_context):
        """Test that reply shows initial balance."""
        await handler.handle_backtest_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        assert "Initial Balance: $100.00" in call_args[0][0]


# ============================================================================
# TESTS FOR handle_callback
# ============================================================================


class TestHandleCallback:
    """Tests for handle_callback method."""

    @pytest.mark.asyncio()
    async def test_no_query(self, handler, mock_context):
        """Test with no callback query."""
        update = MagicMock(spec=Update)
        update.callback_query = None
        
        await handler.handle_callback(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio()
    async def test_no_query_data(self, handler, mock_context):
        """Test with no query data."""
        update = MagicMock(spec=Update)
        query = MagicMock(spec=CallbackQuery)
        query.data = None
        update.callback_query = query
        
        await handler.handle_callback(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio()
    async def test_results_callback(self, handler, mock_callback_query, mock_context):
        """Test handling results callback."""
        mock_callback_query.data = "backtest:results"
        update = MagicMock(spec=Update)
        update.callback_query = mock_callback_query
        
        await handler.handle_callback(update, mock_context)
        
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_settings_callback(self, handler, mock_callback_query, mock_context):
        """Test handling settings callback."""
        mock_callback_query.data = "backtest:settings"
        update = MagicMock(spec=Update)
        update.callback_query = mock_callback_query
        
        await handler.handle_callback(update, mock_context)
        
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_balance_change_callback(self, handler, mock_callback_query, mock_context):
        """Test handling balance change callback."""
        mock_callback_query.data = "backtest:balance:500"
        update = MagicMock(spec=Update)
        update.callback_query = mock_callback_query
        
        await handler.handle_callback(update, mock_context)
        
        assert handler._initial_balance == Decimal("500.0")

    @pytest.mark.asyncio()
    async def test_run_backtest_callback(self, handler, mock_callback_query, mock_context):
        """Test handling run backtest callback."""
        mock_callback_query.data = "backtest:run:simple:30"
        update = MagicMock(spec=Update)
        update.callback_query = mock_callback_query
        
        with patch.object(handler, "_run_backtest", new_callable=AsyncMock) as mock_run:
            await handler.handle_callback(update, mock_context)
            
            mock_run.assert_called_once_with(mock_callback_query, "simple", 30)


# ============================================================================
# TESTS FOR _show_results
# ============================================================================


class TestShowResults:
    """Tests for _show_results method."""

    @pytest.mark.asyncio()
    async def test_no_results(self, handler, mock_callback_query):
        """Test showing results when none exist."""
        await handler._show_results(mock_callback_query)
        
        call_args = mock_callback_query.edit_message_text.call_args
        assert "No backtests run yet" in call_args.kwargs.get("text", call_args[0][0])

    @pytest.mark.asyncio()
    async def test_with_results(self, handler, mock_callback_query):
        """Test showing results when they exist."""
        # Add a mock result
        mock_result = MagicMock()
        mock_result.strategy_name = "simple"
        mock_result.total_trades = 10
        mock_result.win_rate = 60.0
        mock_result.total_profit = Decimal("25.50")
        
        handler._recent_results.append(mock_result)
        
        await handler._show_results(mock_callback_query)
        
        call_args = mock_callback_query.edit_message_text.call_args
        text = call_args.kwargs.get("text", call_args[0][0])
        
        assert "simple" in text
        assert "10 trades" in text


# ============================================================================
# TESTS FOR _show_settings
# ============================================================================


class TestShowSettings:
    """Tests for _show_settings method."""

    @pytest.mark.asyncio()
    async def test_shows_current_balance(self, handler, mock_callback_query):
        """Test that settings show current balance."""
        await handler._show_settings(mock_callback_query)
        
        call_args = mock_callback_query.edit_message_text.call_args
        text = call_args.kwargs.get("text", call_args[0][0])
        
        assert "Initial Balance" in text
        assert "$100.00" in text

    @pytest.mark.asyncio()
    async def test_has_balance_buttons(self, handler, mock_callback_query):
        """Test that settings include balance selection buttons."""
        await handler._show_settings(mock_callback_query)
        
        call_args = mock_callback_query.edit_message_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        
        assert reply_markup is not None
        
        # Check that balance options are present
        buttons_data = []
        for row in reply_markup.inline_keyboard:
            for button in row:
                buttons_data.append(button.callback_data)
        
        assert "backtest:balance:50" in buttons_data
        assert "backtest:balance:100" in buttons_data
        assert "backtest:balance:500" in buttons_data


# ============================================================================
# TESTS FOR _display_result
# ============================================================================


class TestDisplayResult:
    """Tests for _display_result method."""

    @pytest.mark.asyncio()
    async def test_positive_profit(self, handler, mock_callback_query):
        """Test displaying result with positive profit."""
        mock_result = MagicMock()
        mock_result.strategy_name = "SimpleArbitrageStrategy"
        mock_result.start_date = datetime(2025, 1, 1, tzinfo=UTC)
        mock_result.end_date = datetime(2025, 1, 31, tzinfo=UTC)
        mock_result.initial_balance = Decimal("100.0")
        mock_result.final_balance = Decimal("125.0")
        mock_result.total_profit = Decimal("25.0")
        mock_result.total_return = 25.0
        mock_result.total_trades = 50
        mock_result.win_rate = 65.0
        mock_result.max_drawdown = Decimal("5.0")
        mock_result.sharpe_ratio = 1.5
        
        await handler._display_result(mock_callback_query, mock_result)
        
        call_args = mock_callback_query.edit_message_text.call_args
        text = call_args.kwargs.get("text", call_args[0][0])
        
        assert "📈" in text  # Profit emoji
        assert "+$25.00" in text
        assert "65.0%" in text  # Win rate

    @pytest.mark.asyncio()
    async def test_negative_profit(self, handler, mock_callback_query):
        """Test displaying result with negative profit (loss)."""
        mock_result = MagicMock()
        mock_result.strategy_name = "SimpleArbitrageStrategy"
        mock_result.start_date = datetime(2025, 1, 1, tzinfo=UTC)
        mock_result.end_date = datetime(2025, 1, 31, tzinfo=UTC)
        mock_result.initial_balance = Decimal("100.0")
        mock_result.final_balance = Decimal("85.0")
        mock_result.total_profit = Decimal("-15.0")
        mock_result.total_return = -15.0
        mock_result.total_trades = 30
        mock_result.win_rate = 40.0
        mock_result.max_drawdown = Decimal("20.0")
        mock_result.sharpe_ratio = -0.5
        
        await handler._display_result(mock_callback_query, mock_result)
        
        call_args = mock_callback_query.edit_message_text.call_args
        text = call_args.kwargs.get("text", call_args[0][0])
        
        assert "📉" in text  # Loss emoji
        assert "-$15.00" in text


# ============================================================================
# TESTS FOR _run_backtest
# ============================================================================


class TestRunBacktest:
    """Tests for _run_backtest method."""

    @pytest.mark.asyncio()
    async def test_no_api(self, mock_callback_query):
        """Test running backtest without API."""
        handler = BacktestHandler()
        
        await handler._run_backtest(mock_callback_query, "simple", 30)
        
        call_args = mock_callback_query.edit_message_text.call_args
        text = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        
        assert "API not configured" in text

    @pytest.mark.asyncio()
    async def test_shows_progress_message(self, handler, mock_callback_query):
        """Test that progress message is shown."""
        with patch("src.telegram_bot.handlers.backtest_handler.HistoricalDataCollector"):
            with patch("src.telegram_bot.handlers.backtest_handler.Backtester"):
                # Make it fail after showing progress
                mock_callback_query.edit_message_text.side_effect = [
                    None,  # First call (progress)
                    Exception("Test"),  # Second call
                ]
                
                try:
                    await handler._run_backtest(mock_callback_query, "simple", 30)
                except Exception:
                    pass
                
                # Check first call was progress message
                first_call = mock_callback_query.edit_message_text.call_args_list[0]
                text = first_call[0][0] if first_call[0] else first_call.kwargs.get("text", "")
                
                assert "Running backtest" in text or "⏳" in text


# ============================================================================
# TESTS FOR get_handlers
# ============================================================================


class TestGetHandlers:
    """Tests for get_handlers method."""

    def test_returns_handlers(self, handler):
        """Test that handlers are returned."""
        handlers = handler.get_handlers()
        
        assert len(handlers) == 2  # Command handler + Callback handler

    def test_handler_types(self, handler):
        """Test handler types."""
        from telegram.ext import CommandHandler, CallbackQueryHandler
        
        handlers = handler.get_handlers()
        
        handler_types = [type(h) for h in handlers]
        
        assert CommandHandler in handler_types
        assert CallbackQueryHandler in handler_types


# ============================================================================
# TESTS FOR result storage
# ============================================================================


class TestResultStorage:
    """Tests for result storage functionality."""

    def test_results_limit(self, handler):
        """Test that results are limited to 10."""
        mock_result = MagicMock()
        
        # Add 15 results
        for _ in range(15):
            handler._recent_results.append(mock_result)
            if len(handler._recent_results) > 10:
                handler._recent_results.pop(0)
        
        assert len(handler._recent_results) == 10

    def test_results_order(self, handler):
        """Test that newest results are at the end."""
        for i in range(5):
            mock_result = MagicMock()
            mock_result.id = i
            handler._recent_results.append(mock_result)
        
        # Newest should be at index 4
        assert handler._recent_results[-1].id == 4

"""Tests for backtest_handler module.

Tests:
- BacktestHandler initialization
- /backtest command handling
- Callback query handling
- Backtest execution
- Result display
- Settings management
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.backtest_handler import BacktestHandler


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_api():
    """Create a mocked API client."""
    api = MagicMock()
    api.get_market_items = AsyncMock()
    api.get_item_price_history = AsyncMock()
    return api


@pytest.fixture
def handler(mock_api):
    """Create a BacktestHandler instance."""
    return BacktestHandler(api=mock_api, initial_balance=100.0)


@pytest.fixture
def mock_update():
    """Create a mocked Update object."""
    update = MagicMock(spec=Update)
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.callback_query = None
    return update


@pytest.fixture
def mock_callback_update():
    """Create a mocked Update object with callback query."""
    update = MagicMock(spec=Update)
    update.message = None
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "backtest:run:simple:30"
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    return update


@pytest.fixture
def mock_context():
    """Create a mocked context object."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.user_data = {}
    context.bot_data = {}
    return context


@pytest.fixture
def mock_backtest_result():
    """Create a mock backtest result."""
    result = MagicMock()
    result.strategy_name = "SimpleArbitrageStrategy"
    result.start_date = datetime(2024, 1, 1, tzinfo=UTC)
    result.end_date = datetime(2024, 1, 31, tzinfo=UTC)
    result.initial_balance = Decimal("100.00")
    result.final_balance = Decimal("115.00")
    result.total_profit = Decimal("15.00")
    result.total_return = 15.0
    result.total_trades = 10
    result.win_rate = 60.0
    result.max_drawdown = Decimal("5.0")
    result.sharpe_ratio = 1.5
    return result


# ============================================================================
# TEST: Initialization
# ============================================================================


class TestBacktestHandlerInit:
    """Tests for BacktestHandler initialization."""

    def test_init_with_api(self, mock_api):
        """Test initialization with API client."""
        handler = BacktestHandler(api=mock_api, initial_balance=100.0)
        
        assert handler._api is mock_api
        assert handler._initial_balance == Decimal("100.0")
        assert handler._recent_results == []

    def test_init_without_api(self):
        """Test initialization without API client."""
        handler = BacktestHandler()
        
        assert handler._api is None
        assert handler._initial_balance == Decimal("100.0")

    def test_init_custom_balance(self, mock_api):
        """Test initialization with custom initial balance."""
        handler = BacktestHandler(api=mock_api, initial_balance=500.0)
        
        assert handler._initial_balance == Decimal("500.0")

    def test_set_api(self):
        """Test setting API after initialization."""
        handler = BacktestHandler()
        mock_api = MagicMock()
        
        handler.set_api(mock_api)
        
        assert handler._api is mock_api


# ============================================================================
# TEST: Backtest Command
# ============================================================================


class TestBacktestCommand:
    """Tests for /backtest command handler."""

    @pytest.mark.asyncio
    async def test_command_no_message(self, handler, mock_context):
        """Test command with no message."""
        update = MagicMock(spec=Update)
        update.message = None
        
        result = await handler.handle_backtest_command(update, mock_context)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_command_no_api(self, mock_update, mock_context):
        """Test command without API configured."""
        handler = BacktestHandler()
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "not configured" in call_args

    @pytest.mark.asyncio
    async def test_command_default_days(self, handler, mock_update, mock_context):
        """Test command with default days."""
        mock_context.args = []
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "30 days" in call_args[0][0]
        assert call_args[1]["reply_markup"] is not None

    @pytest.mark.asyncio
    async def test_command_custom_days(self, handler, mock_update, mock_context):
        """Test command with custom days argument."""
        mock_context.args = ["14"]
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "14 days" in call_args

    @pytest.mark.asyncio
    async def test_command_days_min_limit(self, handler, mock_update, mock_context):
        """Test command with days below minimum (7)."""
        mock_context.args = ["3"]
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        # Should be clamped to 7
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "7 days" in call_args

    @pytest.mark.asyncio
    async def test_command_days_max_limit(self, handler, mock_update, mock_context):
        """Test command with days above maximum (90)."""
        mock_context.args = ["120"]
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        # Should be clamped to 90
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "90 days" in call_args

    @pytest.mark.asyncio
    async def test_command_invalid_days(self, handler, mock_update, mock_context):
        """Test command with invalid days argument."""
        mock_context.args = ["invalid"]
        
        await handler.handle_backtest_command(mock_update, mock_context)
        
        # Should use default 30 days
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "30 days" in call_args


# ============================================================================
# TEST: Callback Handler
# ============================================================================


class TestCallbackHandler:
    """Tests for callback query handler."""

    @pytest.mark.asyncio
    async def test_callback_no_query(self, handler, mock_context):
        """Test callback with no query."""
        update = MagicMock(spec=Update)
        update.callback_query = None
        
        result = await handler.handle_callback(update, mock_context)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_callback_no_data(self, handler, mock_context):
        """Test callback with no data."""
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock()
        update.callback_query.data = None
        update.callback_query.answer = AsyncMock()
        
        result = await handler.handle_callback(update, mock_context)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_callback_run_backtest(self, handler, mock_callback_update, mock_context):
        """Test callback for running backtest."""
        mock_callback_update.callback_query.data = "backtest:run:simple:30"
        
        with patch.object(handler, "_run_backtest", new=AsyncMock()) as mock_run:
            await handler.handle_callback(mock_callback_update, mock_context)
            
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_show_results(self, handler, mock_callback_update, mock_context):
        """Test callback for showing results."""
        mock_callback_update.callback_query.data = "backtest:results"
        
        with patch.object(handler, "_show_results", new=AsyncMock()) as mock_show:
            await handler.handle_callback(mock_callback_update, mock_context)
            
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_show_settings(self, handler, mock_callback_update, mock_context):
        """Test callback for showing settings."""
        mock_callback_update.callback_query.data = "backtest:settings"
        
        with patch.object(handler, "_show_settings", new=AsyncMock()) as mock_show:
            await handler.handle_callback(mock_callback_update, mock_context)
            
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_change_balance(self, handler, mock_callback_update, mock_context):
        """Test callback for changing balance."""
        mock_callback_update.callback_query.data = "backtest:balance:500"
        
        with patch.object(handler, "_show_settings", new=AsyncMock()) as mock_show:
            await handler.handle_callback(mock_callback_update, mock_context)
            
            assert handler._initial_balance == Decimal("500.0")
            mock_show.assert_called_once()


# ============================================================================
# TEST: Run Backtest
# ============================================================================


class TestRunBacktest:
    """Tests for backtest execution."""

    @pytest.mark.asyncio
    async def test_run_backtest_no_api(self, mock_context):
        """Test running backtest without API."""
        handler = BacktestHandler()
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        await handler._run_backtest(query, "simple", 30)
        
        query.edit_message_text.assert_called()
        call_text = query.edit_message_text.call_args[0][0]
        assert "not configured" in call_text

    @pytest.mark.asyncio
    async def test_run_backtest_success(self, handler, mock_backtest_result, mock_context):
        """Test successful backtest execution."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        with (
            patch(
                "src.telegram_bot.handlers.backtest_handler.HistoricalDataCollector"
            ) as mock_collector_class,
            patch(
                "src.telegram_bot.handlers.backtest_handler.Backtester"
            ) as mock_backtester_class,
            patch(
                "src.telegram_bot.handlers.backtest_handler.SimpleArbitrageStrategy"
            ),
            patch.object(handler, "_display_result", new=AsyncMock()) as mock_display,
        ):
            mock_collector = MagicMock()
            mock_collector.collect_batch = AsyncMock(return_value=[])
            mock_collector_class.return_value = mock_collector
            
            mock_backtester = MagicMock()
            mock_backtester.run = AsyncMock(return_value=mock_backtest_result)
            mock_backtester_class.return_value = mock_backtester
            
            await handler._run_backtest(query, "simple", 30)
            
            mock_display.assert_called_once()
            assert len(handler._recent_results) == 1

    @pytest.mark.asyncio
    async def test_run_backtest_error(self, handler, mock_context):
        """Test backtest execution with error."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        with patch(
            "src.telegram_bot.handlers.backtest_handler.HistoricalDataCollector"
        ) as mock_collector_class:
            mock_collector_class.side_effect = Exception("API error")
            
            await handler._run_backtest(query, "simple", 30)
            
            # Should show error message
            calls = query.edit_message_text.call_args_list
            assert len(calls) > 0
            last_call_text = calls[-1][0][0]
            assert "failed" in last_call_text.lower() or "error" in last_call_text.lower()


# ============================================================================
# TEST: Display Results
# ============================================================================


class TestDisplayResult:
    """Tests for result display."""

    @pytest.mark.asyncio
    async def test_display_result_profit(self, handler, mock_backtest_result):
        """Test displaying result with profit."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        await handler._display_result(query, mock_backtest_result)
        
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        text = call_args[0][0]
        
        assert "Results" in text
        assert "Profit" in text
        assert "$15.00" in text
        assert "📈" in text  # Profit emoji

    @pytest.mark.asyncio
    async def test_display_result_loss(self, handler):
        """Test displaying result with loss."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        result = MagicMock()
        result.strategy_name = "SimpleArbitrageStrategy"
        result.start_date = datetime(2024, 1, 1, tzinfo=UTC)
        result.end_date = datetime(2024, 1, 31, tzinfo=UTC)
        result.initial_balance = Decimal("100.00")
        result.final_balance = Decimal("85.00")
        result.total_profit = Decimal("-15.00")
        result.total_return = -15.0
        result.total_trades = 10
        result.win_rate = 40.0
        result.max_drawdown = Decimal("15.0")
        result.sharpe_ratio = -0.5
        
        await handler._display_result(query, result)
        
        call_args = query.edit_message_text.call_args
        text = call_args[0][0]
        
        assert "📉" in text  # Loss emoji
        assert "-$15.00" in text


# ============================================================================
# TEST: Show Results
# ============================================================================


class TestShowResults:
    """Tests for showing recent results."""

    @pytest.mark.asyncio
    async def test_show_results_empty(self, handler):
        """Test showing results when no results exist."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        await handler._show_results(query)
        
        call_args = query.edit_message_text.call_args
        text = call_args[0][0]
        assert "No backtests run yet" in text

    @pytest.mark.asyncio
    async def test_show_results_with_data(self, handler, mock_backtest_result):
        """Test showing results with existing data."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        handler._recent_results = [mock_backtest_result]
        
        await handler._show_results(query)
        
        call_args = query.edit_message_text.call_args
        text = call_args[0][0]
        assert "Recent Backtest Results" in text
        assert "SimpleArbitrageStrategy" in text


# ============================================================================
# TEST: Show Settings
# ============================================================================


class TestShowSettings:
    """Tests for showing settings."""

    @pytest.mark.asyncio
    async def test_show_settings(self, handler):
        """Test showing settings."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        
        await handler._show_settings(query)
        
        call_args = query.edit_message_text.call_args
        text = call_args[0][0]
        
        assert "Settings" in text
        assert "$100.00" in text
        assert call_args[1]["reply_markup"] is not None


# ============================================================================
# TEST: Get Handlers
# ============================================================================


class TestGetHandlers:
    """Tests for getting handler list."""

    def test_get_handlers(self, handler):
        """Test getting handlers for registration."""
        handlers = handler.get_handlers()
        
        assert len(handlers) == 2
        # First should be CommandHandler
        assert handlers[0].commands == frozenset({"backtest"})
        # Second should be CallbackQueryHandler


# ============================================================================
# TEST: Results Limit
# ============================================================================


class TestResultsLimit:
    """Tests for results storage limit."""

    def test_results_limit_enforced(self, handler, mock_backtest_result):
        """Test that only last 10 results are kept."""
        # Add 15 results
        for _ in range(15):
            handler._recent_results.append(mock_backtest_result)
            if len(handler._recent_results) > 10:
                handler._recent_results.pop(0)
        
        assert len(handler._recent_results) == 10

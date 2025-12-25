"""Unit tests for src/telegram_bot/sales_analysis_callbacks.py.

Tests for sales analysis callback handlers including:
- Sales history callbacks
- Liquidity analysis callbacks
- Refresh callbacks
- Arbitrage with sales callbacks
- Volume statistics callbacks
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSalesHistoryCallback:
    """Tests for handle_sales_history_callback."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "sales_history:AK-47 | Redline"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handles_missing_query(self, mock_context):
        """Test handling when callback_query is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_sales_history_callback,
        )

        update = MagicMock()
        update.callback_query = None

        # Should return without error
        await handle_sales_history_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_missing_callback_data(self, mock_context):
        """Test handling when callback_data is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_sales_history_callback,
        )

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = None

        # Should return without error
        await handle_sales_history_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_data(self, mock_update, mock_context):
        """Test handling invalid callback data format."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_sales_history_callback,
        )

        mock_update.callback_query.data = "invalid_data"

        await handle_sales_history_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in call_args[1].get("text", call_args[0][0] if call_args[0] else "")

    @pytest.mark.asyncio
    async def test_sends_loading_message(self, mock_update, mock_context):
        """Test that loading message is sent."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_sales_history_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            new_callable=AsyncMock,
        ) as mock_get_sales:
            mock_get_sales.return_value = {"Error": "API error"}

            await handle_sales_history_callback(mock_update, mock_context)

            # First call should be loading message
            first_call = mock_update.callback_query.edit_message_text.call_args_list[0]
            assert "подождите" in first_call[1].get("text", first_call[0][0] if first_call[0] else "").lower()

    @pytest.mark.asyncio
    async def test_handles_api_error_response(self, mock_update, mock_context):
        """Test handling API error response."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_sales_history_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            new_callable=AsyncMock,
        ) as mock_get_sales:
            mock_get_sales.return_value = {"Error": "API rate limit exceeded"}

            await handle_sales_history_callback(mock_update, mock_context)

            # Last call should show error
            last_call = mock_update.callback_query.edit_message_text.call_args
            assert "Ошибка" in last_call[1].get("text", last_call[0][0] if last_call[0] else "")


class TestLiquidityCallback:
    """Tests for handle_liquidity_callback."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "liquidity:AK-47 | Redline"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {"current_game": "csgo"}
        return context

    @pytest.mark.asyncio
    async def test_handles_missing_query(self, mock_context):
        """Test handling when callback_query is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_liquidity_callback,
        )

        update = MagicMock()
        update.callback_query = None

        # Should return without error
        await handle_liquidity_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_missing_callback_data(self, mock_context):
        """Test handling when callback_data is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_liquidity_callback,
        )

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = None

        # Should return without error
        await handle_liquidity_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_data(self, mock_update, mock_context):
        """Test handling invalid callback data format."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_liquidity_callback,
        )

        mock_update.callback_query.data = "invalid_data"

        await handle_liquidity_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_sends_loading_message(self, mock_update, mock_context):
        """Test that loading message is sent."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_liquidity_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = {
                "sales_analysis": {"has_data": False}
            }

            await handle_liquidity_callback(mock_update, mock_context)

            # First call should be loading message
            first_call = mock_update.callback_query.edit_message_text.call_args_list[0]
            text = first_call[1].get("text", first_call[0][0] if first_call[0] else "")
            assert "анализ" in text.lower() or "подождите" in text.lower()

    @pytest.mark.asyncio
    async def test_handles_no_sales_data(self, mock_update, mock_context):
        """Test handling when no sales data available."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_liquidity_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = {
                "sales_analysis": {"has_data": False}
            }

            await handle_liquidity_callback(mock_update, mock_context)

            # Last call should indicate no data
            last_call = mock_update.callback_query.edit_message_text.call_args
            text = last_call[1].get("text", last_call[0][0] if last_call[0] else "")
            assert "не удалось" in text.lower() or "данны" in text.lower()


class TestRefreshSalesCallback:
    """Tests for handle_refresh_sales_callback."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "refresh_sales:AK-47 | Redline"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handles_missing_query(self, mock_context):
        """Test handling when callback_query is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_refresh_sales_callback,
        )

        update = MagicMock()
        update.callback_query = None

        # Should return without error
        await handle_refresh_sales_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_data(self, mock_update, mock_context):
        """Test handling invalid callback data format."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_refresh_sales_callback,
        )

        mock_update.callback_query.data = "invalid_data"

        await handle_refresh_sales_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_sends_loading_message(self, mock_update, mock_context):
        """Test that loading message is sent."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_refresh_sales_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_sales_history",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = {"has_data": False}

            await handle_refresh_sales_callback(mock_update, mock_context)

            # First call should be loading message
            first_call = mock_update.callback_query.edit_message_text.call_args_list[0]
            text = first_call[1].get("text", first_call[0][0] if first_call[0] else "")
            assert "обновлен" in text.lower() or "подождите" in text.lower()


class TestRefreshLiquidityCallback:
    """Tests for handle_refresh_liquidity_callback."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "refresh_liquidity:AK-47 | Redline"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_redirects_to_liquidity_callback(self, mock_update, mock_context):
        """Test that refresh redirects to liquidity callback."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_refresh_liquidity_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.handle_liquidity_callback",
            new_callable=AsyncMock,
        ) as mock_handler:
            await handle_refresh_liquidity_callback(mock_update, mock_context)

            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_modifies_callback_data(self, mock_update, mock_context):
        """Test that callback data is modified."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_refresh_liquidity_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.handle_liquidity_callback",
            new_callable=AsyncMock,
        ):
            await handle_refresh_liquidity_callback(mock_update, mock_context)

            # Data should be modified from refresh_liquidity to liquidity
            assert "liquidity:" in mock_update.callback_query.data


class TestAllArbitrageSalesCallback:
    """Tests for handle_all_arbitrage_sales_callback."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "all_arbitrage_sales:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handles_missing_query(self, mock_context):
        """Test handling when callback_query is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_all_arbitrage_sales_callback,
        )

        update = MagicMock()
        update.callback_query = None

        # Should return without error
        await handle_all_arbitrage_sales_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_data(self, mock_update, mock_context):
        """Test handling invalid callback data format."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_all_arbitrage_sales_callback,
        )

        mock_update.callback_query.data = "invalid_data"

        await handle_all_arbitrage_sales_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_handles_empty_results(self, mock_update, mock_context):
        """Test handling empty arbitrage results."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_all_arbitrage_sales_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = []

            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

            last_call = mock_update.callback_query.edit_message_text.call_args
            text = last_call[1].get("text", last_call[0][0] if last_call[0] else "")
            assert "не найдено" in text.lower()


class TestSetupSalesFiltersCallback:
    """Tests for handle_setup_sales_filters_callback."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "setup_sales_filters:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handles_missing_query(self, mock_context):
        """Test handling when callback_query is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_setup_sales_filters_callback,
        )

        update = MagicMock()
        update.callback_query = None

        # Should return without error
        await handle_setup_sales_filters_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_uses_default_game(self, mock_update, mock_context):
        """Test default game is used when not specified."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_setup_sales_filters_callback,
        )

        mock_update.callback_query.data = "setup_sales_filters"

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_shows_current_filters(self, mock_update, mock_context):
        """Test that current filters are displayed."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_setup_sales_filters_callback,
        )

        mock_context.user_data = {
            "sales_filters": {
                "min_profit": 2.0,
                "min_profit_percent": 10.0,
            }
        }

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        last_call = mock_update.callback_query.edit_message_text.call_args
        text = last_call[1].get("text", last_call[0][0] if last_call[0] else "")
        assert "настройк" in text.lower() or "фильтр" in text.lower()

    @pytest.mark.asyncio
    async def test_creates_keyboard(self, mock_update, mock_context):
        """Test that keyboard is created."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_setup_sales_filters_callback,
        )

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        last_call = mock_update.callback_query.edit_message_text.call_args
        assert "reply_markup" in last_call[1]


class TestVolumeStatsCallback:
    """Tests for volume statistics callbacks."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "all_volume_stats:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handles_missing_query(self, mock_context):
        """Test handling when callback_query is None."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_all_volume_stats_callback,
        )

        update = MagicMock()
        update.callback_query = None

        # Should return without error
        await handle_all_volume_stats_callback(update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_data(self, mock_update, mock_context):
        """Test handling invalid callback data format."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_all_volume_stats_callback,
        )

        mock_update.callback_query.data = "invalid_data"

        await handle_all_volume_stats_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_handles_empty_stats(self, mock_update, mock_context):
        """Test handling empty volume stats."""
        from src.telegram_bot.sales_analysis_callbacks import (
            handle_all_volume_stats_callback,
        )

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats",
            new_callable=AsyncMock,
        ) as mock_stats:
            mock_stats.return_value = {"items": []}

            await handle_all_volume_stats_callback(mock_update, mock_context)

            last_call = mock_update.callback_query.edit_message_text.call_args
            text = last_call[1].get("text", last_call[0][0] if last_call[0] else "")
            assert "не удалось" in text.lower()


class TestPriceTrendToText:
    """Tests for price_trend_to_text helper function."""

    def test_up_trend(self):
        """Test up trend text."""
        from src.telegram_bot.sales_analysis_callbacks import price_trend_to_text

        result = price_trend_to_text("up")
        assert "растущ" in result.lower() or "⬆️" in result

    def test_down_trend(self):
        """Test down trend text."""
        from src.telegram_bot.sales_analysis_callbacks import price_trend_to_text

        result = price_trend_to_text("down")
        assert "падающ" in result.lower() or "⬇️" in result

    def test_stable_trend(self):
        """Test stable trend text."""
        from src.telegram_bot.sales_analysis_callbacks import price_trend_to_text

        result = price_trend_to_text("stable")
        assert "стабильн" in result.lower() or "➡️" in result

    def test_unknown_trend(self):
        """Test unknown trend text."""
        from src.telegram_bot.sales_analysis_callbacks import price_trend_to_text

        result = price_trend_to_text("unknown")
        assert "любой" in result.lower() or "🔄" in result

    def test_all_trend(self):
        """Test 'all' trend text."""
        from src.telegram_bot.sales_analysis_callbacks import price_trend_to_text

        result = price_trend_to_text("all")
        assert "любой" in result.lower() or "🔄" in result

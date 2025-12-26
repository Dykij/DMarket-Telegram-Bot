"""Tests for sales_analysis_callbacks module.

This module provides comprehensive tests for sales analysis callback handlers
including sales history, liquidity analysis, and arbitrage with sales data.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime

from src.telegram_bot.sales_analysis_callbacks import (
    handle_sales_history_callback,
    handle_liquidity_callback,
    handle_refresh_sales_callback,
    handle_refresh_liquidity_callback,
    handle_all_arbitrage_sales_callback,
    handle_refresh_arbitrage_sales_callback,
    handle_setup_sales_filters_callback,
    handle_all_volume_stats_callback,
    handle_refresh_volume_stats_callback,
    price_trend_to_text,
)
from src.utils.exceptions import APIError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_update():
    """Creates a mock Telegram Update object."""
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = MagicMock()
    return update


@pytest.fixture
def mock_context():
    """Creates a mock Telegram Context object."""
    context = MagicMock()
    context.user_data = {}
    return context


# ============================================================================
# TESTS FOR handle_sales_history_callback
# ============================================================================


class TestSalesHistoryCallback:
    """Tests for handle_sales_history_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        # Should not raise
        await handle_sales_history_callback(update, context)

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query_data(self, mock_update, mock_context):
        """Test returns early if no callback data."""
        mock_update.callback_query.data = None
        
        # Should not raise
        await handle_sales_history_callback(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_format(self, mock_update, mock_context):
        """Test handles invalid callback data format."""
        mock_update.callback_query.data = "sales_history"  # Missing item name
        
        await handle_sales_history_callback(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in call_args.kwargs.get("text", call_args[0][0])

    @pytest.mark.asyncio
    async def test_successful_sales_history_request(self, mock_update, mock_context):
        """Test successful sales history request."""
        mock_update.callback_query.data = "sales_history:AK-47 | Redline"
        
        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "AK-47 | Redline",
                    "Sales": [
                        {"Timestamp": 1703001600, "Price": 25.50, "Currency": "USD", "OrderType": "Buy"},
                        {"Timestamp": 1703002600, "Price": 26.00, "Currency": "USD", "OrderType": "Sell"},
                    ]
                }
            ]
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data
            
            await handle_sales_history_callback(mock_update, mock_context)
            
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_api_error_response(self, mock_update, mock_context):
        """Test handles API error in response."""
        mock_update.callback_query.data = "sales_history:TestItem"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"Error": "API rate limit exceeded"}
            
            await handle_sales_history_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_handles_no_sales_data(self, mock_update, mock_context):
        """Test handles no sales data for item."""
        mock_update.callback_query.data = "sales_history:RareItem"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"LastSales": []}
            
            await handle_sales_history_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не удалось" in str(call_args)

    @pytest.mark.asyncio
    async def test_handles_api_exception(self, mock_update, mock_context):
        """Test handles APIError exception."""
        mock_update.callback_query.data = "sales_history:TestItem"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = APIError("Network error", status_code=500)
            
            await handle_sales_history_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_handles_general_exception(self, mock_update, mock_context):
        """Test handles general exception."""
        mock_update.callback_query.data = "sales_history:TestItem"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ValueError("Unexpected error")
            
            await handle_sales_history_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "ошибка" in str(call_args).lower()


# ============================================================================
# TESTS FOR handle_liquidity_callback
# ============================================================================


class TestLiquidityCallback:
    """Tests for handle_liquidity_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_liquidity_callback(update, context)

    @pytest.mark.asyncio
    async def test_handles_invalid_callback_format(self, mock_update, mock_context):
        """Test handles invalid callback data format."""
        mock_update.callback_query.data = "liquidity"  # Missing item name
        
        await handle_liquidity_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_successful_liquidity_analysis(self, mock_update, mock_context):
        """Test successful liquidity analysis."""
        mock_update.callback_query.data = "liquidity:TestItem"
        
        mock_analysis = {
            "liquidity_score": 5,
            "liquidity_category": "Высокая",
            "sales_analysis": {
                "has_data": True,
                "price_trend": "up",
                "sales_per_day": 10.5,
                "sales_volume": 150,
                "avg_price": 25.0,
            },
            "market_data": {
                "offers_count": 50,
                "lowest_price": 20.0,
                "highest_price": 30.0,
            }
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            await handle_liquidity_callback(mock_update, mock_context)
            
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_no_sales_data(self, mock_update, mock_context):
        """Test handles item with no sales data."""
        mock_update.callback_query.data = "liquidity:RareItem"
        
        mock_analysis = {
            "sales_analysis": {"has_data": False}
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            await handle_liquidity_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не удалось" in str(call_args)

    @pytest.mark.asyncio
    async def test_uses_game_from_context(self, mock_update, mock_context):
        """Test uses game from context user_data."""
        mock_update.callback_query.data = "liquidity:TestItem"
        mock_context.user_data = {"current_game": "dota2"}
        
        mock_analysis = {
            "liquidity_score": 3,
            "liquidity_category": "Средняя",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 1.0, "sales_volume": 10, "avg_price": 5.0},
            "market_data": {"offers_count": 5, "lowest_price": 4.0, "highest_price": 6.0}
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            await handle_liquidity_callback(mock_update, mock_context)
            
            # Game should be used (even if just stored)
            assert mock_context.user_data.get("current_game") == "dota2"

    @pytest.mark.asyncio
    async def test_high_liquidity_recommendation(self, mock_update, mock_context):
        """Test recommendation for high liquidity items."""
        mock_update.callback_query.data = "liquidity:TestItem"
        
        mock_analysis = {
            "liquidity_score": 6,
            "liquidity_category": "Высокая",
            "sales_analysis": {"has_data": True, "price_trend": "up", "sales_per_day": 20.0, "sales_volume": 300, "avg_price": 50.0},
            "market_data": {"offers_count": 100, "lowest_price": 45.0, "highest_price": 55.0}
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            await handle_liquidity_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            # High liquidity should have positive recommendation
            assert "подходит" in str(call_args).lower() or "Отлично" in str(call_args)


# ============================================================================
# TESTS FOR handle_refresh_sales_callback
# ============================================================================


class TestRefreshSalesCallback:
    """Tests for handle_refresh_sales_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_refresh_sales_callback(update, context)

    @pytest.mark.asyncio
    async def test_handles_invalid_format(self, mock_update, mock_context):
        """Test handles invalid callback format."""
        mock_update.callback_query.data = "refresh_sales"
        
        await handle_refresh_sales_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_successful_refresh(self, mock_update, mock_context):
        """Test successful sales refresh."""
        mock_update.callback_query.data = "refresh_sales:TestItem"
        
        mock_analysis = {
            "has_data": True,
            "avg_price": 25.0,
            "max_price": 30.0,
            "min_price": 20.0,
            "price_trend": "up",
            "sales_volume": 100,
            "sales_per_day": 7.0,
            "period_days": 14,
            "recent_sales": [
                {"date": "2024-01-15", "price": 25.0, "currency": "USD"}
            ]
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            await handle_refresh_sales_callback(mock_update, mock_context)
            
            mock_analyze.assert_called_once_with(item_name="TestItem", days=14)

    @pytest.mark.asyncio
    async def test_handles_no_data(self, mock_update, mock_context):
        """Test handles no data response."""
        mock_update.callback_query.data = "refresh_sales:TestItem"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"has_data": False}
            
            await handle_refresh_sales_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не удалось" in str(call_args)


# ============================================================================
# TESTS FOR handle_refresh_liquidity_callback
# ============================================================================


class TestRefreshLiquidityCallback:
    """Tests for handle_refresh_liquidity_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_refresh_liquidity_callback(update, context)

    @pytest.mark.asyncio
    async def test_redirects_to_liquidity_callback(self, mock_update, mock_context):
        """Test redirects to main liquidity handler."""
        mock_update.callback_query.data = "refresh_liquidity:TestItem"
        
        mock_analysis = {
            "liquidity_score": 5,
            "liquidity_category": "Высокая",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 5.0, "sales_volume": 50, "avg_price": 10.0},
            "market_data": {"offers_count": 20, "lowest_price": 8.0, "highest_price": 12.0}
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            await handle_refresh_liquidity_callback(mock_update, mock_context)
            
            # Should have modified the callback data
            assert mock_update.callback_query.data == "liquidity:TestItem"


# ============================================================================
# TESTS FOR handle_all_arbitrage_sales_callback
# ============================================================================


class TestAllArbitrageSalesCallback:
    """Tests for handle_all_arbitrage_sales_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_all_arbitrage_sales_callback(update, context)

    @pytest.mark.asyncio
    async def test_handles_invalid_format(self, mock_update, mock_context):
        """Test handles invalid callback format."""
        mock_update.callback_query.data = "all_arbitrage_sales"
        
        await handle_all_arbitrage_sales_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_successful_arbitrage_search(self, mock_update, mock_context):
        """Test successful arbitrage search with sales data."""
        mock_update.callback_query.data = "all_arbitrage_sales:csgo"
        
        mock_results = [
            {
                "market_hash_name": "AK-47 | Redline",
                "profit": 5.0,
                "profit_percent": 10.0,
                "buy_price": 50.0,
                "sell_price": 55.0,
                "sales_analysis": {"price_trend": "up", "sales_per_day": 15.0}
            }
        ]
        
        with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results
            
            await handle_all_arbitrage_sales_callback(mock_update, mock_context)
            
            mock_search.assert_called_once_with(game="csgo", min_profit=1.0)

    @pytest.mark.asyncio
    async def test_handles_no_results(self, mock_update, mock_context):
        """Test handles no arbitrage opportunities found."""
        mock_update.callback_query.data = "all_arbitrage_sales:csgo"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            await handle_all_arbitrage_sales_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не найдено" in str(call_args) or "арбитражных" in str(call_args)

    @pytest.mark.asyncio
    async def test_limits_displayed_results(self, mock_update, mock_context):
        """Test limits displayed results to 10."""
        mock_update.callback_query.data = "all_arbitrage_sales:csgo"
        
        # Create 15 results
        mock_results = [
            {
                "market_hash_name": f"Item {i}",
                "profit": 5.0 + i,
                "profit_percent": 10.0,
                "buy_price": 50.0,
                "sell_price": 55.0,
                "sales_analysis": {"price_trend": "stable", "sales_per_day": 5.0}
            }
            for i in range(15)
        ]
        
        with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results
            
            await handle_all_arbitrage_sales_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should show "10 из 15"
            assert "10" in str(call_args) and "15" in str(call_args)


# ============================================================================
# TESTS FOR handle_setup_sales_filters_callback
# ============================================================================


class TestSetupSalesFiltersCallback:
    """Tests for handle_setup_sales_filters_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_setup_sales_filters_callback(update, context)

    @pytest.mark.asyncio
    async def test_uses_default_game_if_not_provided(self, mock_update, mock_context):
        """Test uses default game if not in callback data."""
        mock_update.callback_query.data = "setup_sales_filters"
        
        await handle_setup_sales_filters_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        # Should default to csgo
        assert "csgo" in str(call_args).lower()

    @pytest.mark.asyncio
    async def test_displays_current_filter_settings(self, mock_update, mock_context):
        """Test displays current filter settings."""
        mock_update.callback_query.data = "setup_sales_filters:csgo"
        mock_context.user_data = {
            "sales_filters": {
                "min_profit": 2.0,
                "min_profit_percent": 10.0,
                "min_sales_per_day": 0.5,
                "price_trend": "up"
            }
        }
        
        await handle_setup_sales_filters_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        # Should display filter values
        assert "$2.00" in str(call_args)
        assert "10.0%" in str(call_args)

    @pytest.mark.asyncio
    async def test_creates_filter_keyboard(self, mock_update, mock_context):
        """Test creates filter configuration keyboard."""
        mock_update.callback_query.data = "setup_sales_filters:csgo"
        
        await handle_setup_sales_filters_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        # Should have reply_markup
        assert "reply_markup" in call_args.kwargs


# ============================================================================
# TESTS FOR handle_all_volume_stats_callback
# ============================================================================


class TestAllVolumeStatsCallback:
    """Tests for handle_all_volume_stats_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_all_volume_stats_callback(update, context)

    @pytest.mark.asyncio
    async def test_handles_invalid_format(self, mock_update, mock_context):
        """Test handles invalid callback format."""
        mock_update.callback_query.data = "all_volume_stats"
        
        await handle_all_volume_stats_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_successful_volume_stats(self, mock_update, mock_context):
        """Test successful volume stats retrieval."""
        mock_update.callback_query.data = "all_volume_stats:csgo"
        
        mock_stats = {
            "count": 50,
            "items": [
                {"item_name": "Item 1", "sales_per_day": 10.0, "avg_price": 25.0, "price_trend": "up"},
                {"item_name": "Item 2", "sales_per_day": 5.0, "avg_price": 15.0, "price_trend": "stable"}
            ],
            "summary": {
                "up_trend_count": 20,
                "down_trend_count": 10,
                "stable_trend_count": 20
            }
        }
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_stats
            
            await handle_all_volume_stats_callback(mock_update, mock_context)
            
            mock_get.assert_called_once_with(game="csgo")

    @pytest.mark.asyncio
    async def test_handles_no_items(self, mock_update, mock_context):
        """Test handles no items in stats."""
        mock_update.callback_query.data = "all_volume_stats:csgo"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"items": []}
            
            await handle_all_volume_stats_callback(mock_update, mock_context)
            
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не удалось" in str(call_args)


# ============================================================================
# TESTS FOR handle_refresh_volume_stats_callback
# ============================================================================


class TestRefreshVolumeStatsCallback:
    """Tests for handle_refresh_volume_stats_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_refresh_volume_stats_callback(update, context)

    @pytest.mark.asyncio
    async def test_handles_invalid_format(self, mock_update, mock_context):
        """Test handles invalid callback format."""
        mock_update.callback_query.data = "refresh_volume_stats"
        
        await handle_refresh_volume_stats_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_updates_context_and_delegates(self, mock_update, mock_context):
        """Test updates context and delegates to handler."""
        mock_update.callback_query.data = "refresh_volume_stats:dota2"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.handle_sales_volume_stats", new_callable=AsyncMock) as mock_handler:
            await handle_refresh_volume_stats_callback(mock_update, mock_context)
            
            # Should update context
            assert mock_context.user_data["current_game"] == "dota2"
            # Should delegate to handler
            mock_handler.assert_called_once()


# ============================================================================
# TESTS FOR price_trend_to_text
# ============================================================================


class TestPriceTrendToText:
    """Tests for price_trend_to_text helper function."""

    def test_up_trend(self):
        """Test up trend conversion."""
        result = price_trend_to_text("up")
        assert "Растущая" in result or "⬆️" in result

    def test_down_trend(self):
        """Test down trend conversion."""
        result = price_trend_to_text("down")
        assert "Падающая" in result or "⬇️" in result

    def test_stable_trend(self):
        """Test stable trend conversion."""
        result = price_trend_to_text("stable")
        assert "Стабильная" in result or "➡️" in result

    def test_unknown_trend(self):
        """Test unknown/all trend conversion."""
        result = price_trend_to_text("all")
        assert "Любой" in result or "🔄" in result

    def test_empty_trend(self):
        """Test empty trend string."""
        result = price_trend_to_text("")
        # Should return default/all
        assert "🔄" in result or "Любой" in result


# ============================================================================
# TESTS FOR handle_refresh_arbitrage_sales_callback
# ============================================================================


class TestRefreshArbitrageSalesCallback:
    """Tests for handle_refresh_arbitrage_sales_callback."""

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_refresh_arbitrage_sales_callback(update, context)

    @pytest.mark.asyncio
    async def test_handles_invalid_format(self, mock_update, mock_context):
        """Test handles invalid callback format."""
        mock_update.callback_query.data = "refresh_arbitrage_sales"
        
        await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio
    async def test_updates_context_and_delegates(self, mock_update, mock_context):
        """Test updates context and delegates to handler."""
        mock_update.callback_query.data = "refresh_arbitrage_sales:rust"
        
        with patch("src.telegram_bot.sales_analysis_callbacks.handle_arbitrage_with_sales", new_callable=AsyncMock) as mock_handler:
            await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)
            
            # Should update context
            assert mock_context.user_data["current_game"] == "rust"
            # Should delegate to handler
            mock_handler.assert_called_once()

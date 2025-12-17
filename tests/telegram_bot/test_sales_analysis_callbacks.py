"""Unit tests for sales_analysis_callbacks module.

Tests for callback handlers related to sales analysis, liquidity,
and volume statistics.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update, User

from src.telegram_bot.sales_analysis_callbacks import (
    handle_all_arbitrage_sales_callback,
    handle_all_volume_stats_callback,
    handle_liquidity_callback,
    handle_refresh_arbitrage_sales_callback,
    handle_refresh_liquidity_callback,
    handle_refresh_sales_callback,
    handle_refresh_volume_stats_callback,
    handle_sales_history_callback,
    handle_setup_sales_filters_callback,
    price_trend_to_text,
)
from src.utils.exceptions import APIError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_user():
    """Create a mock Telegram user."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    return user


@pytest.fixture()
def mock_message(mock_user):
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = mock_user
    message.chat_id = 123456789
    message.reply_text = AsyncMock()
    return message


@pytest.fixture()
def mock_callback_query(mock_user, mock_message):
    """Create a mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.id = "callback_query_123"
    query.from_user = mock_user
    query.message = mock_message
    query.data = ""
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    return query


@pytest.fixture()
def mock_update(mock_callback_query, mock_message):
    """Create a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.message = mock_message
    update.effective_user = mock_callback_query.from_user
    return update


@pytest.fixture()
def mock_context():
    """Create a mock bot context."""
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


# ============================================================================
# TESTS FOR price_trend_to_text HELPER
# ============================================================================


class TestPriceTrendToText:
    """Tests for price_trend_to_text helper function."""

    def test_up_trend(self):
        """Test up trend text."""
        result = price_trend_to_text("up")
        assert "⬆️" in result
        assert "Растущая" in result

    def test_down_trend(self):
        """Test down trend text."""
        result = price_trend_to_text("down")
        assert "⬇️" in result
        assert "Падающая" in result

    def test_stable_trend(self):
        """Test stable trend text."""
        result = price_trend_to_text("stable")
        assert "➡️" in result
        assert "Стабильная" in result

    def test_any_trend(self):
        """Test any/unknown trend text."""
        result = price_trend_to_text("all")
        assert "🔄" in result
        assert "Любой" in result

    def test_unknown_trend(self):
        """Test unknown trend defaults to 'any'."""
        result = price_trend_to_text("unknown_value")
        assert "🔄" in result


# ============================================================================
# TESTS FOR handle_sales_history_callback
# ============================================================================


class TestHandleSalesHistoryCallback:
    """Tests for handle_sales_history_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_sales_history_callback(mock_update, mock_context)

        # Should return early without errors

    @pytest.mark.asyncio()
    async def test_no_data_returns_early(self, mock_update, mock_context, mock_callback_query):
        """Test early return when no callback data."""
        mock_callback_query.data = None

        await handle_sales_history_callback(mock_update, mock_context)

        # Should return early without errors

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "sales_history"  # Missing item name

        await handle_sales_history_callback(mock_update, mock_context)

        mock_callback_query.edit_message_text.assert_called()
        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_successful_sales_history_request(self, mock_update, mock_context, mock_callback_query):
        """Test successful sales history request."""
        mock_callback_query.data = "sales_history:AK-47 | Redline"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "AK-47 | Redline",
                    "Sales": [
                        {
                            "Timestamp": 1700000000,
                            "Price": 15.50,
                            "Currency": "USD",
                            "OrderType": "Market",
                        }
                    ],
                }
            ]
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(return_value=mock_sales_data),
        ):
            await handle_sales_history_callback(mock_update, mock_context)

        # Should call edit_message_text at least twice (progress + result)
        assert mock_callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    async def test_sales_history_api_error(self, mock_update, mock_context, mock_callback_query):
        """Test API error handling."""
        mock_callback_query.data = "sales_history:Test Item"

        mock_sales_data = {"Error": "API unavailable"}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(return_value=mock_sales_data),
        ):
            await handle_sales_history_callback(mock_update, mock_context)

        # Should display error message
        call_args = mock_callback_query.edit_message_text.call_args
        assert "Ошибка" in call_args[0][0] or "Error" in str(call_args)

    @pytest.mark.asyncio()
    async def test_sales_history_no_data(self, mock_update, mock_context, mock_callback_query):
        """Test handling when no sales data found."""
        mock_callback_query.data = "sales_history:Unknown Item"

        mock_sales_data = {"LastSales": []}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(return_value=mock_sales_data),
        ):
            await handle_sales_history_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Не удалось" in call_args[0][0] or "⚠️" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_sales_history_exception_handling(self, mock_update, mock_context, mock_callback_query):
        """Test general exception handling."""
        mock_callback_query.data = "sales_history:Test Item"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(side_effect=Exception("Unexpected error")),
        ):
            await handle_sales_history_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "ошибка" in call_args[0][0].lower() or "❌" in call_args[0][0]


# ============================================================================
# TESTS FOR handle_liquidity_callback
# ============================================================================


class TestHandleLiquidityCallback:
    """Tests for handle_liquidity_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_liquidity_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "liquidity"  # Missing item name

        await handle_liquidity_callback(mock_update, mock_context)

        mock_callback_query.edit_message_text.assert_called()
        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_successful_liquidity_analysis(self, mock_update, mock_context, mock_callback_query):
        """Test successful liquidity analysis."""
        mock_callback_query.data = "liquidity:AK-47 | Redline"

        mock_analysis = {
            "sales_analysis": {
                "has_data": True,
                "price_trend": "up",
                "sales_per_day": 5.5,
                "sales_volume": 100,
                "avg_price": 15.00,
            },
            "liquidity_score": 6,
            "liquidity_category": "Высокая",
            "market_data": {
                "offers_count": 50,
                "lowest_price": 14.50,
                "highest_price": 18.00,
            },
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(return_value=mock_analysis),
        ), patch(
            "src.telegram_bot.sales_analysis_callbacks.get_liquidity_emoji",
            return_value="💧",
        ), patch(
            "src.telegram_bot.sales_analysis_callbacks.get_trend_emoji",
            return_value="📈",
        ):
            await handle_liquidity_callback(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    async def test_liquidity_no_data(self, mock_update, mock_context, mock_callback_query):
        """Test handling when no liquidity data found."""
        mock_callback_query.data = "liquidity:Unknown Item"

        mock_analysis = {
            "sales_analysis": {"has_data": False},
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(return_value=mock_analysis),
        ):
            await handle_liquidity_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Не удалось" in call_args[0][0] or "⚠️" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_liquidity_api_error(self, mock_update, mock_context, mock_callback_query):
        """Test API error handling."""
        mock_callback_query.data = "liquidity:Test Item"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(side_effect=APIError("API Error", status_code=500)),
        ):
            await handle_liquidity_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Ошибка" in call_args[0][0] or "❌" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_liquidity_uses_context_game(self, mock_update, mock_context, mock_callback_query):
        """Test that game is read from context."""
        mock_callback_query.data = "liquidity:Test Item"
        mock_context.user_data = {"current_game": "dota2"}

        mock_analysis = {
            "sales_analysis": {"has_data": False},
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(return_value=mock_analysis),
        ):
            await handle_liquidity_callback(mock_update, mock_context)

        # Should not crash with context game


# ============================================================================
# TESTS FOR handle_refresh_sales_callback
# ============================================================================


class TestHandleRefreshSalesCallback:
    """Tests for handle_refresh_sales_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_refresh_sales_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "refresh_sales"  # Missing item name

        await handle_refresh_sales_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_successful_refresh_sales(self, mock_update, mock_context, mock_callback_query):
        """Test successful sales analysis refresh."""
        mock_callback_query.data = "refresh_sales:AK-47 | Redline"

        mock_analysis = {
            "has_data": True,
            "avg_price": 15.00,
            "max_price": 18.00,
            "min_price": 12.00,
            "price_trend": "up",
            "sales_volume": 100,
            "sales_per_day": 5.5,
            "period_days": 14,
            "recent_sales": [
                {"date": "2024-01-01", "price": 15.50, "currency": "USD"},
            ],
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_sales_history",
            AsyncMock(return_value=mock_analysis),
        ), patch(
            "src.telegram_bot.sales_analysis_callbacks.get_trend_emoji",
            return_value="📈",
        ):
            await handle_refresh_sales_callback(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    async def test_refresh_sales_no_data(self, mock_update, mock_context, mock_callback_query):
        """Test handling when no sales data found."""
        mock_callback_query.data = "refresh_sales:Unknown Item"

        mock_analysis = {"has_data": False}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_sales_history",
            AsyncMock(return_value=mock_analysis),
        ):
            await handle_refresh_sales_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Не удалось" in call_args[0][0] or "⚠️" in call_args[0][0]


# ============================================================================
# TESTS FOR handle_refresh_liquidity_callback
# ============================================================================


class TestHandleRefreshLiquidityCallback:
    """Tests for handle_refresh_liquidity_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_refresh_liquidity_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_no_data_returns_early(self, mock_update, mock_context, mock_callback_query):
        """Test early return when no callback data."""
        mock_callback_query.data = None

        await handle_refresh_liquidity_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_refresh_liquidity_redirects_to_liquidity(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Test that refresh liquidity redirects to main liquidity handler."""
        mock_callback_query.data = "refresh_liquidity:Test Item"

        mock_analysis = {
            "sales_analysis": {"has_data": False},
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(return_value=mock_analysis),
        ):
            await handle_refresh_liquidity_callback(mock_update, mock_context)

        # Should have modified data to redirect
        assert mock_callback_query.data == "liquidity:Test Item"


# ============================================================================
# TESTS FOR handle_all_arbitrage_sales_callback
# ============================================================================


class TestHandleAllArbitrageSalesCallback:
    """Tests for handle_all_arbitrage_sales_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_all_arbitrage_sales_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "all_arbitrage_sales"  # Missing game

        await handle_all_arbitrage_sales_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_successful_arbitrage_search(self, mock_update, mock_context, mock_callback_query):
        """Test successful arbitrage search with sales data."""
        mock_callback_query.data = "all_arbitrage_sales:csgo"

        mock_results = [
            {
                "market_hash_name": "AK-47 | Redline",
                "profit": 5.00,
                "profit_percent": 10.0,
                "buy_price": 50.00,
                "sell_price": 55.00,
                "sales_analysis": {
                    "price_trend": "up",
                    "sales_per_day": 5.5,
                },
            }
        ]

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search",
            AsyncMock(return_value=mock_results),
        ), patch(
            "src.telegram_bot.sales_analysis_callbacks.get_trend_emoji",
            return_value="📈",
        ):
            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    async def test_no_arbitrage_opportunities(self, mock_update, mock_context, mock_callback_query):
        """Test handling when no opportunities found."""
        mock_callback_query.data = "all_arbitrage_sales:csgo"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search",
            AsyncMock(return_value=[]),
        ):
            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Не найдено" in call_args[0][0] or "⚠️" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_arbitrage_api_error(self, mock_update, mock_context, mock_callback_query):
        """Test API error handling."""
        mock_callback_query.data = "all_arbitrage_sales:csgo"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search",
            AsyncMock(side_effect=APIError("API Error", status_code=500)),
        ):
            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Ошибка" in call_args[0][0] or "❌" in call_args[0][0]


# ============================================================================
# TESTS FOR handle_refresh_arbitrage_sales_callback
# ============================================================================


class TestHandleRefreshArbitrageSalesCallback:
    """Tests for handle_refresh_arbitrage_sales_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "refresh_arbitrage_sales"  # Missing game

        await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_refresh_updates_context_game(self, mock_update, mock_context, mock_callback_query):
        """Test that refresh updates the game in context."""
        mock_callback_query.data = "refresh_arbitrage_sales:dota2"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.handle_arbitrage_with_sales",
            AsyncMock(),
        ):
            await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)

        assert mock_context.user_data.get("current_game") == "dota2"


# ============================================================================
# TESTS FOR handle_setup_sales_filters_callback
# ============================================================================


class TestHandleSetupSalesFiltersCallback:
    """Tests for handle_setup_sales_filters_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_setup_sales_filters_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_default_game_when_missing(self, mock_update, mock_context, mock_callback_query):
        """Test default game (csgo) when not provided."""
        mock_callback_query.data = "setup_sales_filters"  # No game specified

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        mock_callback_query.edit_message_text.assert_called()
        call_args = mock_callback_query.edit_message_text.call_args
        # Check either positional or keyword argument
        text = call_args[1].get("text") if call_args[1] else (call_args[0][0] if call_args[0] else "")
        assert "csgo" in text.lower() or "Настройка" in text

    @pytest.mark.asyncio()
    async def test_shows_current_filter_settings(self, mock_update, mock_context, mock_callback_query):
        """Test that current filter settings are displayed."""
        mock_callback_query.data = "setup_sales_filters:csgo"
        mock_context.user_data = {
            "sales_filters": {
                "min_profit": 2.0,
                "min_profit_percent": 10.0,
                "min_sales_per_day": 0.5,
                "price_trend": "up",
            }
        }

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "2.0" in str(call_args) or "Минимальная прибыль" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_creates_filter_keyboard(self, mock_update, mock_context, mock_callback_query):
        """Test that filter configuration keyboard is created."""
        mock_callback_query.data = "setup_sales_filters:csgo"

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        keyboard = call_args[1].get("reply_markup")
        assert keyboard is not None


# ============================================================================
# TESTS FOR handle_all_volume_stats_callback
# ============================================================================


class TestHandleAllVolumeStatsCallback:
    """Tests for handle_all_volume_stats_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_all_volume_stats_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "all_volume_stats"  # Missing game

        await handle_all_volume_stats_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_successful_volume_stats(self, mock_update, mock_context, mock_callback_query):
        """Test successful volume stats retrieval."""
        mock_callback_query.data = "all_volume_stats:csgo"

        mock_stats = {
            "count": 10,
            "items": [
                {
                    "item_name": "AK-47 | Redline",
                    "sales_per_day": 5.5,
                    "avg_price": 15.00,
                    "price_trend": "up",
                }
            ],
            "summary": {
                "up_trend_count": 5,
                "down_trend_count": 3,
                "stable_trend_count": 2,
            },
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats",
            AsyncMock(return_value=mock_stats),
        ), patch(
            "src.telegram_bot.sales_analysis_callbacks.get_trend_emoji",
            return_value="📈",
        ):
            await handle_all_volume_stats_callback(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    async def test_no_volume_stats(self, mock_update, mock_context, mock_callback_query):
        """Test handling when no stats found."""
        mock_callback_query.data = "all_volume_stats:csgo"

        mock_stats = {"items": []}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats",
            AsyncMock(return_value=mock_stats),
        ):
            await handle_all_volume_stats_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Не удалось" in call_args[0][0] or "⚠️" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_volume_stats_api_error(self, mock_update, mock_context, mock_callback_query):
        """Test API error handling."""
        mock_callback_query.data = "all_volume_stats:csgo"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats",
            AsyncMock(side_effect=APIError("API Error", status_code=500)),
        ):
            await handle_all_volume_stats_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "Ошибка" in call_args[0][0] or "❌" in call_args[0][0]


# ============================================================================
# TESTS FOR handle_refresh_volume_stats_callback
# ============================================================================


class TestHandleRefreshVolumeStatsCallback:
    """Tests for handle_refresh_volume_stats_callback."""

    @pytest.mark.asyncio()
    async def test_no_query_returns_early(self, mock_update, mock_context):
        """Test early return when no query."""
        mock_update.callback_query = None

        await handle_refresh_volume_stats_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_invalid_callback_data_format(self, mock_update, mock_context, mock_callback_query):
        """Test error handling for invalid callback data format."""
        mock_callback_query.data = "refresh_volume_stats"  # Missing game

        await handle_refresh_volume_stats_callback(mock_update, mock_context)

        call_args = mock_callback_query.edit_message_text.call_args
        assert "некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_refresh_updates_context_game(self, mock_update, mock_context, mock_callback_query):
        """Test that refresh updates the game in context."""
        mock_callback_query.data = "refresh_volume_stats:dota2"

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.handle_sales_volume_stats",
            AsyncMock(),
        ):
            await handle_refresh_volume_stats_callback(mock_update, mock_context)

        assert mock_context.user_data.get("current_game") == "dota2"


# ============================================================================
# EDGE CASES AND INTEGRATION TESTS
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and integration scenarios."""

    @pytest.mark.asyncio()
    async def test_special_characters_in_item_name(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Test handling item names with special characters."""
        mock_callback_query.data = "sales_history:AK-47 | Redline (Field-Tested)"

        mock_sales_data = {"LastSales": []}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(return_value=mock_sales_data),
        ):
            # Should not crash with special characters
            await handle_sales_history_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_unicode_in_item_name(self, mock_update, mock_context, mock_callback_query):
        """Test handling item names with unicode characters."""
        mock_callback_query.data = "liquidity:АК-47 | Красная линия"

        mock_analysis = {
            "sales_analysis": {"has_data": False},
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(return_value=mock_analysis),
        ):
            # Should not crash with unicode
            await handle_liquidity_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_empty_item_name(self, mock_update, mock_context, mock_callback_query):
        """Test handling empty item name."""
        mock_callback_query.data = "sales_history:"

        mock_sales_data = {"LastSales": []}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(return_value=mock_sales_data),
        ):
            # Should not crash with empty name
            await handle_sales_history_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_very_long_item_name(self, mock_update, mock_context, mock_callback_query):
        """Test handling very long item names."""
        long_name = "A" * 500
        mock_callback_query.data = f"liquidity:{long_name}"

        mock_analysis = {
            "sales_analysis": {"has_data": False},
        }

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity",
            AsyncMock(return_value=mock_analysis),
        ):
            # Should not crash with long name
            await handle_liquidity_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_context_without_user_data(self, mock_update, mock_callback_query):
        """Test handling context without user_data."""
        context = MagicMock()
        context.user_data = None  # No user_data

        mock_callback_query.data = "setup_sales_filters:csgo"

        # Should not crash without user_data
        await handle_setup_sales_filters_callback(mock_update, context)

    @pytest.mark.asyncio()
    async def test_multiple_colons_in_callback_data(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Test handling callback data with multiple colons."""
        mock_callback_query.data = "sales_history:Item:With:Colons"

        mock_sales_data = {"LastSales": []}

        with patch(
            "src.telegram_bot.sales_analysis_callbacks.get_sales_history",
            AsyncMock(return_value=mock_sales_data),
        ):
            # Should correctly parse with split(":", 1)
            await handle_sales_history_callback(mock_update, mock_context)

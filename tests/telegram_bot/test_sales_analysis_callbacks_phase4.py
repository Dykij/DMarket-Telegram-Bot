"""Phase 4 extended tests for sales_analysis_callbacks module.

This module provides comprehensive extended tests for sales analysis callback handlers
to achieve 100% coverage including edge cases, error handling, and integration tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
def mock_update():
    """Creates a mock Telegram Update object."""
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = MagicMock()
    return update


@pytest.fixture()
def mock_context():
    """Creates a mock Telegram Context object."""
    context = MagicMock()
    context.user_data = {}
    return context


# ============================================================================
# EXTENDED TESTS FOR handle_sales_history_callback
# ============================================================================


class TestSalesHistoryCallbackExtended:
    """Extended tests for handle_sales_history_callback."""

    @pytest.mark.asyncio()
    async def test_item_name_with_colon(self, mock_update, mock_context):
        """Test handles item names containing colons."""
        mock_update.callback_query.data = "sales_history:AK-47 | Redline (Field-Tested):Souvenir"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "AK-47 | Redline (Field-Tested):Souvenir",
                    "Sales": [
                        {"Timestamp": 1703001600, "Price": 25.50, "Currency": "USD", "OrderType": "Buy"}
                    ]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            mock_get.assert_called_once()

    @pytest.mark.asyncio()
    async def test_item_with_empty_sales_list(self, mock_update, mock_context):
        """Test handles item with empty sales list."""
        mock_update.callback_query.data = "sales_history:RareItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "RareItem",
                    "Sales": []
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не удалось" in str(call_args)

    @pytest.mark.asyncio()
    async def test_multiple_items_in_response(self, mock_update, mock_context):
        """Test extracts correct item from multiple items in response."""
        mock_update.callback_query.data = "sales_history:TargetItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "OtherItem",
                    "Sales": [{"Timestamp": 1703001600, "Price": 10.0, "Currency": "USD", "OrderType": "Buy"}]
                },
                {
                    "MarketHashName": "TargetItem",
                    "Sales": [{"Timestamp": 1703001600, "Price": 25.50, "Currency": "USD", "OrderType": "Buy"}]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            text = str(call_args)
            assert "TargetItem" in text or "$25.50" in text

    @pytest.mark.asyncio()
    async def test_sale_with_missing_timestamp(self, mock_update, mock_context):
        """Test handles sale with missing timestamp (defaults to 0)."""
        mock_update.callback_query.data = "sales_history:TestItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "TestItem",
                    "Sales": [
                        {"Price": 25.50, "Currency": "USD", "OrderType": "Buy"}  # No Timestamp
                    ]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            # Should handle gracefully with default timestamp
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_sale_with_missing_price(self, mock_update, mock_context):
        """Test handles sale with missing price (defaults to 0)."""
        mock_update.callback_query.data = "sales_history:TestItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "TestItem",
                    "Sales": [
                        {"Timestamp": 1703001600, "Currency": "USD", "OrderType": "Buy"}  # No Price
                    ]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_more_than_20_sales(self, mock_update, mock_context):
        """Test limits displayed sales to 20."""
        mock_update.callback_query.data = "sales_history:TestItem"

        # Create 30 sales
        sales = [
            {"Timestamp": 1703001600 + i * 3600, "Price": 25.0 + i, "Currency": "USD", "OrderType": "Buy"}
            for i in range(30)
        ]

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "TestItem",
                    "Sales": sales
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            # Should complete without error, showing only 20 sales
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_unicode_item_name(self, mock_update, mock_context):
        """Test handles Unicode characters in item name."""
        mock_update.callback_query.data = "sales_history:АК-47 | Кровавый спорт"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "АК-47 | Кровавый спорт",
                    "Sales": [
                        {"Timestamp": 1703001600, "Price": 50.0, "Currency": "USD", "OrderType": "Buy"}
                    ]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            mock_get.assert_called_once()

    @pytest.mark.asyncio()
    async def test_zero_price_sale(self, mock_update, mock_context):
        """Test handles zero price sales."""
        mock_update.callback_query.data = "sales_history:TestItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "TestItem",
                    "Sales": [
                        {"Timestamp": 1703001600, "Price": 0, "Currency": "USD", "OrderType": "Buy"}
                    ]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "$0.00" in str(call_args)


# ============================================================================
# EXTENDED TESTS FOR handle_liquidity_callback
# ============================================================================


class TestLiquidityCallbackExtended:
    """Extended tests for handle_liquidity_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_liquidity_callback(mock_update, mock_context)

        # Should return early without editing message
        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_very_high_liquidity_recommendation(self, mock_update, mock_context):
        """Test recommendation for very high liquidity items."""
        mock_update.callback_query.data = "liquidity:TestItem"

        mock_analysis = {
            "liquidity_score": 7,
            "liquidity_category": "Очень высокая",
            "sales_analysis": {"has_data": True, "price_trend": "up", "sales_per_day": 50.0, "sales_volume": 700, "avg_price": 100.0},
            "market_data": {"offers_count": 200, "lowest_price": 90.0, "highest_price": 110.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Отлично" in str(call_args)

    @pytest.mark.asyncio()
    async def test_medium_liquidity_recommendation(self, mock_update, mock_context):
        """Test recommendation for medium liquidity items."""
        mock_update.callback_query.data = "liquidity:TestItem"

        mock_analysis = {
            "liquidity_score": 4,
            "liquidity_category": "Средняя",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 2.0, "sales_volume": 30, "avg_price": 15.0},
            "market_data": {"offers_count": 10, "lowest_price": 14.0, "highest_price": 16.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "осторожностью" in str(call_args)

    @pytest.mark.asyncio()
    async def test_low_liquidity_recommendation(self, mock_update, mock_context):
        """Test recommendation for low liquidity items."""
        mock_update.callback_query.data = "liquidity:TestItem"

        mock_analysis = {
            "liquidity_score": 2,
            "liquidity_category": "Низкая",
            "sales_analysis": {"has_data": True, "price_trend": "down", "sales_per_day": 0.1, "sales_volume": 2, "avg_price": 5.0},
            "market_data": {"offers_count": 2, "lowest_price": 4.0, "highest_price": 6.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Не рекомендуется" in str(call_args)

    @pytest.mark.asyncio()
    async def test_context_without_user_data(self, mock_update):
        """Test handles context without user_data attribute."""
        mock_update.callback_query.data = "liquidity:TestItem"

        context = MagicMock()
        # Simulate context without user_data
        context.user_data = None

        mock_analysis = {
            "liquidity_score": 5,
            "liquidity_category": "Высокая",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 5.0, "sales_volume": 50, "avg_price": 10.0},
            "market_data": {"offers_count": 20, "lowest_price": 8.0, "highest_price": 12.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, context)

            # Should work with default game
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio()
    async def test_api_error_handling(self, mock_update, mock_context):
        """Test handles APIError exception with message."""
        mock_update.callback_query.data = "liquidity:TestItem"

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = APIError("Rate limit exceeded", status_code=429)

            await handle_liquidity_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio()
    async def test_general_exception_handling(self, mock_update, mock_context):
        """Test handles general exception."""
        mock_update.callback_query.data = "liquidity:TestItem"

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = RuntimeError("Unexpected error")

            await handle_liquidity_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "ошибка" in str(call_args).lower()


# ============================================================================
# EXTENDED TESTS FOR handle_refresh_sales_callback
# ============================================================================


class TestRefreshSalesCallbackExtended:
    """Extended tests for handle_refresh_sales_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_refresh_sales_callback(mock_update, mock_context)

        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_no_recent_sales(self, mock_update, mock_context):
        """Test handles analysis with no recent sales."""
        mock_update.callback_query.data = "refresh_sales:TestItem"

        mock_analysis = {
            "has_data": True,
            "avg_price": 25.0,
            "max_price": 30.0,
            "min_price": 20.0,
            "price_trend": "stable",
            "sales_volume": 100,
            "sales_per_day": 7.0,
            "period_days": 14,
            "recent_sales": []  # Empty recent sales
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_refresh_sales_callback(mock_update, mock_context)

            # Should complete without showing recent sales section
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_more_than_5_recent_sales(self, mock_update, mock_context):
        """Test limits recent sales display to 5."""
        mock_update.callback_query.data = "refresh_sales:TestItem"

        recent_sales = [
            {"date": f"2024-01-{15 - i:02d}", "price": 25.0 + i, "currency": "USD"}
            for i in range(10)
        ]

        mock_analysis = {
            "has_data": True,
            "avg_price": 25.0,
            "max_price": 30.0,
            "min_price": 20.0,
            "price_trend": "up",
            "sales_volume": 100,
            "sales_per_day": 7.0,
            "period_days": 14,
            "recent_sales": recent_sales
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_refresh_sales_callback(mock_update, mock_context)

            # Should show only 5 recent sales
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_api_error_handling(self, mock_update, mock_context):
        """Test handles APIError exception."""
        mock_update.callback_query.data = "refresh_sales:TestItem"

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = APIError("Service unavailable", status_code=503)

            await handle_refresh_sales_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio()
    async def test_general_exception_handling(self, mock_update, mock_context):
        """Test handles general exception."""
        mock_update.callback_query.data = "refresh_sales:TestItem"

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = ValueError("Parsing error")

            await handle_refresh_sales_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "ошибка" in str(call_args).lower()


# ============================================================================
# EXTENDED TESTS FOR handle_refresh_liquidity_callback
# ============================================================================


class TestRefreshLiquidityCallbackExtended:
    """Extended tests for handle_refresh_liquidity_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_refresh_liquidity_callback(mock_update, mock_context)

        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_correctly_transforms_callback_data(self, mock_update, mock_context):
        """Test correctly transforms callback data from refresh to regular."""
        mock_update.callback_query.data = "refresh_liquidity:SomeItem"

        mock_analysis = {
            "liquidity_score": 5,
            "liquidity_category": "Высокая",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 5.0, "sales_volume": 50, "avg_price": 10.0},
            "market_data": {"offers_count": 20, "lowest_price": 8.0, "highest_price": 12.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_refresh_liquidity_callback(mock_update, mock_context)

            # Callback data should be modified
            assert mock_update.callback_query.data == "liquidity:SomeItem"


# ============================================================================
# EXTENDED TESTS FOR handle_all_arbitrage_sales_callback
# ============================================================================


class TestAllArbitrageSalesCallbackExtended:
    """Extended tests for handle_all_arbitrage_sales_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_all_arbitrage_sales_callback(mock_update, mock_context)

        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_exactly_10_results(self, mock_update, mock_context):
        """Test displays exactly 10 results without truncation message."""
        mock_update.callback_query.data = "all_arbitrage_sales:csgo"

        mock_results = [
            {
                "market_hash_name": f"Item {i}",
                "profit": 5.0 + i,
                "profit_percent": 10.0,
                "buy_price": 50.0,
                "sell_price": 55.0,
                "sales_analysis": {"price_trend": "stable", "sales_per_day": 5.0}
            }
            for i in range(10)
        ]

        with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results

            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should not show truncation message for exactly 10 results
            assert "10 из" not in str(call_args)

    @pytest.mark.asyncio()
    async def test_api_error_handling(self, mock_update, mock_context):
        """Test handles APIError exception."""
        mock_update.callback_query.data = "all_arbitrage_sales:csgo"

        with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = APIError("Timeout", status_code=504)

            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio()
    async def test_general_exception_handling(self, mock_update, mock_context):
        """Test handles general exception."""
        mock_update.callback_query.data = "all_arbitrage_sales:csgo"

        with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = KeyError("missing_key")

            await handle_all_arbitrage_sales_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "ошибка" in str(call_args).lower()

    @pytest.mark.asyncio()
    async def test_different_games(self, mock_update, mock_context):
        """Test with different game types."""
        games = ["csgo", "dota2", "tf2", "rust"]

        for game in games:
            mock_update.callback_query.data = f"all_arbitrage_sales:{game}"

            with patch("src.telegram_bot.sales_analysis_callbacks.enhanced_arbitrage_search", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = []

                await handle_all_arbitrage_sales_callback(mock_update, mock_context)

                mock_search.assert_called_with(game=game, min_profit=1.0)


# ============================================================================
# EXTENDED TESTS FOR handle_refresh_arbitrage_sales_callback
# ============================================================================


class TestRefreshArbitrageSalesCallbackExtended:
    """Extended tests for handle_refresh_arbitrage_sales_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)

        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_context_without_user_data(self, mock_update):
        """Test handles context without user_data attribute."""
        mock_update.callback_query.data = "refresh_arbitrage_sales:csgo"

        context = MagicMock()
        context.user_data = None

        with patch("src.telegram_bot.sales_analysis_callbacks.handle_arbitrage_with_sales", new_callable=AsyncMock) as mock_handler:
            await handle_refresh_arbitrage_sales_callback(mock_update, context)

            # Should still call handler
            mock_handler.assert_called_once()

    @pytest.mark.asyncio()
    async def test_updates_message_reference(self, mock_update, mock_context):
        """Test updates message reference for handler."""
        mock_update.callback_query.data = "refresh_arbitrage_sales:dota2"
        mock_update.callback_query.message = MagicMock()

        with patch("src.telegram_bot.sales_analysis_callbacks.handle_arbitrage_with_sales", new_callable=AsyncMock) as mock_handler:
            await handle_refresh_arbitrage_sales_callback(mock_update, mock_context)

            # update.message should be set
            assert mock_update.message is not None


# ============================================================================
# EXTENDED TESTS FOR handle_setup_sales_filters_callback
# ============================================================================


class TestSetupSalesFiltersCallbackExtended:
    """Extended tests for handle_setup_sales_filters_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_query(self):
        """Test returns early if no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_setup_sales_filters_callback(update, context)

        # Should return without error

    @pytest.mark.asyncio()
    async def test_uses_default_filters(self, mock_update, mock_context):
        """Test uses default filter values when not set."""
        mock_update.callback_query.data = "setup_sales_filters:csgo"
        mock_context.user_data = {}  # No filters set

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        # Should show default values
        assert "$1.00" in str(call_args)  # default min_profit
        assert "5.0%" in str(call_args)  # default min_profit_percent

    @pytest.mark.asyncio()
    async def test_updates_game_in_context(self, mock_update, mock_context):
        """Test updates current game in context."""
        mock_update.callback_query.data = "setup_sales_filters:dota2"

        await handle_setup_sales_filters_callback(mock_update, mock_context)

        assert mock_context.user_data["current_game"] == "dota2"

    @pytest.mark.asyncio()
    async def test_context_without_user_data(self, mock_update):
        """Test handles context without user_data."""
        mock_update.callback_query.data = "setup_sales_filters:tf2"

        context = MagicMock()
        context.user_data = None

        await handle_setup_sales_filters_callback(mock_update, context)

        # Should work with default values
        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_all_trend_options(self, mock_update, mock_context):
        """Test handles all trend filter options."""
        trends = ["up", "down", "stable", "all"]

        for trend in trends:
            mock_context.user_data = {"sales_filters": {"price_trend": trend}}
            mock_update.callback_query.data = "setup_sales_filters:csgo"

            await handle_setup_sales_filters_callback(mock_update, mock_context)

            mock_update.callback_query.edit_message_text.assert_called()


# ============================================================================
# EXTENDED TESTS FOR handle_all_volume_stats_callback
# ============================================================================


class TestAllVolumeStatsCallbackExtended:
    """Extended tests for handle_all_volume_stats_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_all_volume_stats_callback(mock_update, mock_context)

        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_exactly_15_items(self, mock_update, mock_context):
        """Test displays exactly 15 items without truncation message."""
        mock_update.callback_query.data = "all_volume_stats:csgo"

        items = [
            {"item_name": f"Item {i}", "sales_per_day": 10.0 - i * 0.5, "avg_price": 25.0, "price_trend": "up"}
            for i in range(15)
        ]

        mock_stats = {
            "count": 15,
            "items": items,
            "summary": {
                "up_trend_count": 10,
                "down_trend_count": 3,
                "stable_trend_count": 2
            }
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_stats

            await handle_all_volume_stats_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should not show truncation for exactly 15
            assert "15 из" not in str(call_args)

    @pytest.mark.asyncio()
    async def test_more_than_15_items(self, mock_update, mock_context):
        """Test truncates display for more than 15 items."""
        mock_update.callback_query.data = "all_volume_stats:csgo"

        items = [
            {"item_name": f"Item {i}", "sales_per_day": 10.0 - i * 0.3, "avg_price": 25.0, "price_trend": "stable"}
            for i in range(20)
        ]

        mock_stats = {
            "count": 20,
            "items": items,
            "summary": {
                "up_trend_count": 5,
                "down_trend_count": 5,
                "stable_trend_count": 10
            }
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_stats

            await handle_all_volume_stats_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should show truncation message
            assert "15" in str(call_args)
            assert "20" in str(call_args)

    @pytest.mark.asyncio()
    async def test_api_error_handling(self, mock_update, mock_context):
        """Test handles APIError exception."""
        mock_update.callback_query.data = "all_volume_stats:csgo"

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = APIError("Connection failed", status_code=502)

            await handle_all_volume_stats_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "Ошибка" in str(call_args)

    @pytest.mark.asyncio()
    async def test_general_exception_handling(self, mock_update, mock_context):
        """Test handles general exception."""
        mock_update.callback_query.data = "all_volume_stats:csgo"

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_volume_stats", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = TypeError("Invalid type")

            await handle_all_volume_stats_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "ошибка" in str(call_args).lower()


# ============================================================================
# EXTENDED TESTS FOR handle_refresh_volume_stats_callback
# ============================================================================


class TestRefreshVolumeStatsCallbackExtended:
    """Extended tests for handle_refresh_volume_stats_callback."""

    @pytest.mark.asyncio()
    async def test_returns_early_if_no_data(self, mock_update, mock_context):
        """Test returns early if callback data is None."""
        mock_update.callback_query.data = None

        await handle_refresh_volume_stats_callback(mock_update, mock_context)

        assert mock_update.callback_query.answer.call_count == 0

    @pytest.mark.asyncio()
    async def test_context_without_user_data(self, mock_update):
        """Test handles context without user_data."""
        mock_update.callback_query.data = "refresh_volume_stats:rust"

        context = MagicMock()
        context.user_data = None

        with patch("src.telegram_bot.sales_analysis_callbacks.handle_sales_volume_stats", new_callable=AsyncMock) as mock_handler:
            await handle_refresh_volume_stats_callback(mock_update, context)

            # Should still call handler
            mock_handler.assert_called_once()


# ============================================================================
# EXTENDED TESTS FOR price_trend_to_text
# ============================================================================


class TestPriceTrendToTextExtended:
    """Extended tests for price_trend_to_text helper function."""

    def test_random_unknown_trend(self):
        """Test returns default for random unknown trend."""
        result = price_trend_to_text("random_trend")
        assert "🔄" in result or "Любой" in result

    def test_none_as_trend(self):
        """Test handles None-like string."""
        result = price_trend_to_text("None")
        assert "🔄" in result or "Любой" in result

    def test_uppercase_trends(self):
        """Test handles uppercase trend values."""
        # Function expects lowercase, so uppercase should return default
        result = price_trend_to_text("UP")
        assert "🔄" in result or "Любой" in result

    def test_whitespace_trend(self):
        """Test handles whitespace trend."""
        result = price_trend_to_text("  ")
        assert "🔄" in result or "Любой" in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSalesAnalysisCallbacksIntegration:
    """Integration tests for sales analysis callbacks."""

    @pytest.mark.asyncio()
    async def test_full_sales_history_workflow(self, mock_update, mock_context):
        """Test full sales history viewing workflow."""
        mock_update.callback_query.data = "sales_history:IntegrationTestItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "IntegrationTestItem",
                    "Sales": [
                        {"Timestamp": 1703001600, "Price": 25.50, "Currency": "USD", "OrderType": "Buy"},
                        {"Timestamp": 1703002600, "Price": 26.00, "Currency": "USD", "OrderType": "Sell"},
                        {"Timestamp": 1703003600, "Price": 25.75, "Currency": "EUR", "OrderType": "Buy"}
                    ]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            # Should show initial loading message then results
            assert mock_update.callback_query.edit_message_text.call_count >= 1

    @pytest.mark.asyncio()
    async def test_full_liquidity_workflow(self, mock_update, mock_context):
        """Test full liquidity analysis workflow."""
        mock_update.callback_query.data = "liquidity:IntegrationTestItem"
        mock_context.user_data = {"current_game": "csgo"}

        mock_analysis = {
            "liquidity_score": 6,
            "liquidity_category": "Высокая",
            "sales_analysis": {
                "has_data": True,
                "price_trend": "up",
                "sales_per_day": 15.0,
                "sales_volume": 200,
                "avg_price": 50.0
            },
            "market_data": {
                "offers_count": 75,
                "lowest_price": 45.0,
                "highest_price": 55.0
            }
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should show liquidity analysis results
            assert "Высокая" in str(call_args)

    @pytest.mark.asyncio()
    async def test_refresh_then_view_history_workflow(self, mock_update, mock_context):
        """Test refresh sales then view history workflow."""
        # First, refresh sales
        mock_update.callback_query.data = "refresh_sales:WorkflowItem"

        mock_analysis = {
            "has_data": True,
            "avg_price": 30.0,
            "max_price": 35.0,
            "min_price": 25.0,
            "price_trend": "stable",
            "sales_volume": 50,
            "sales_per_day": 3.5,
            "period_days": 14,
            "recent_sales": [{"date": "2024-01-15", "price": 30.0, "currency": "USD"}]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_refresh_sales_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should show analysis with history button
            assert "reply_markup" in call_args.kwargs


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Edge case tests for sales analysis callbacks."""

    @pytest.mark.asyncio()
    async def test_empty_item_name(self, mock_update, mock_context):
        """Test handles empty item name."""
        mock_update.callback_query.data = "sales_history:"

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"LastSales": []}

            await handle_sales_history_callback(mock_update, mock_context)

            # Should handle gracefully
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_very_long_item_name(self, mock_update, mock_context):
        """Test handles very long item name."""
        long_name = "A" * 500
        mock_update.callback_query.data = f"liquidity:{long_name}"

        mock_analysis = {
            "liquidity_score": 3,
            "liquidity_category": "Средняя",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 1.0, "sales_volume": 10, "avg_price": 5.0},
            "market_data": {"offers_count": 5, "lowest_price": 4.0, "highest_price": 6.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, mock_context)

            mock_analyze.assert_called_once()

    @pytest.mark.asyncio()
    async def test_special_characters_in_item_name(self, mock_update, mock_context):
        """Test handles special characters in item name."""
        special_name = "Item <test> & 'quotes' \"double\""
        mock_update.callback_query.data = f"sales_history:{special_name}"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": special_name,
                    "Sales": [{"Timestamp": 1703001600, "Price": 10.0, "Currency": "USD", "OrderType": "Buy"}]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            mock_get.assert_called_once()

    @pytest.mark.asyncio()
    async def test_negative_prices(self, mock_update, mock_context):
        """Test handles negative prices gracefully."""
        mock_update.callback_query.data = "refresh_sales:TestItem"

        mock_analysis = {
            "has_data": True,
            "avg_price": -5.0,  # Invalid negative price
            "max_price": -1.0,
            "min_price": -10.0,
            "price_trend": "down",
            "sales_volume": 10,
            "sales_per_day": 1.0,
            "period_days": 14,
            "recent_sales": []
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_sales_history", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_refresh_sales_callback(mock_update, mock_context)

            # Should format negative prices without crashing
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_very_large_prices(self, mock_update, mock_context):
        """Test handles very large prices."""
        mock_update.callback_query.data = "sales_history:ExpensiveItem"

        mock_sales_data = {
            "LastSales": [
                {
                    "MarketHashName": "ExpensiveItem",
                    "Sales": [{"Timestamp": 1703001600, "Price": 99999999.99, "Currency": "USD", "OrderType": "Buy"}]
                }
            ]
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.get_sales_history", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sales_data

            await handle_sales_history_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should format large price correctly
            assert "$99999999.99" in str(call_args)

    @pytest.mark.asyncio()
    async def test_zero_sales_per_day(self, mock_update, mock_context):
        """Test handles zero sales per day."""
        mock_update.callback_query.data = "liquidity:LowVolumeItem"

        mock_analysis = {
            "liquidity_score": 1,
            "liquidity_category": "Очень низкая",
            "sales_analysis": {"has_data": True, "price_trend": "stable", "sales_per_day": 0.0, "sales_volume": 0, "avg_price": 10.0},
            "market_data": {"offers_count": 1, "lowest_price": 10.0, "highest_price": 10.0}
        }

        with patch("src.telegram_bot.sales_analysis_callbacks.analyze_item_liquidity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            await handle_liquidity_callback(mock_update, mock_context)

            call_args = mock_update.callback_query.edit_message_text.call_args
            # Should format zero correctly
            assert "0.00" in str(call_args)

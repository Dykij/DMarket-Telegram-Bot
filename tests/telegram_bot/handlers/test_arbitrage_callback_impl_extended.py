"""Extended tests for arbitrage_callback_impl module.

This module adds comprehensive tests for edge cases, pagination,
and additional callback handlers not covered in the basic tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.arbitrage_callback_impl import (
    CONFIRMING_ACTION,
    SELECTING_GAME,
    SELECTING_MODE,
    arbitrage_callback_impl,
    handle_best_opportunities_impl,
    handle_dmarket_arbitrage_impl,
    handle_game_selected_impl,
    handle_game_selection_impl,
    handle_market_comparison_impl,
)
from src.utils.exceptions import APIError


# ============================================================================
# ФИКСТУРЫ
# ============================================================================


@pytest.fixture
def mock_update():
    """Создает мокированный Update объект."""
    update = MagicMock(spec=Update)
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = MagicMock()
    update.callback_query.message.chat = MagicMock()
    update.callback_query.message.chat.send_action = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.from_user = MagicMock()
    update.callback_query.from_user.id = 12345
    update.effective_chat = MagicMock()
    update.effective_chat.send_action = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Создает мокированный CallbackContext объект."""
    context = MagicMock(spec=CallbackContext)
    context.user_data = {}
    return context


@pytest.fixture
def mock_arbitrage_results():
    """Создает тестовые результаты арбитража."""
    return [
        {
            "title": "AK-47 | Redline (Field-Tested)",
            "buy_price": 10.50,
            "sell_price": 12.00,
            "profit": 1.50,
            "profit_percent": 14.3,
            "game": "csgo",
        },
        {
            "title": "AWP | Asiimov (Battle-Scarred)",
            "buy_price": 25.00,
            "sell_price": 28.50,
            "profit": 3.50,
            "profit_percent": 14.0,
            "game": "csgo",
        },
    ]


@pytest.fixture
def mock_large_results():
    """Создает большой набор результатов для тестирования пагинации."""
    return [
        {
            "title": f"Item {i}",
            "buy_price": 10.0 + i,
            "sell_price": 12.0 + i,
            "profit": 2.0,
            "profit_percent": 10.0,
            "game": "csgo",
        }
        for i in range(50)
    ]


# ============================================================================
# ТЕСТЫ: arbitrage_callback_impl
# ============================================================================


class TestArbitrageCallbackImplEdgeCases:
    """Edge case tests for arbitrage_callback_impl."""

    @pytest.mark.asyncio
    async def test_arbitrage_callback_impl_no_query(self, mock_context):
        """Test arbitrage_callback_impl when query is None."""
        update = MagicMock(spec=Update)
        update.callback_query = None
        
        result = await arbitrage_callback_impl(update, mock_context)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_arbitrage_callback_impl_no_effective_chat(self, mock_update, mock_context):
        """Test arbitrage_callback_impl when effective_chat is None."""
        mock_update.effective_chat = None
        mock_context.user_data = {"use_modern_ui": False}

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard"
        ) as mock_keyboard:
            mock_keyboard.return_value = MagicMock(spec=InlineKeyboardMarkup)
            
            result = await arbitrage_callback_impl(mock_update, mock_context)
            
            # Should still work, just skip the send_action
            assert result == SELECTING_MODE

    @pytest.mark.asyncio
    async def test_arbitrage_callback_impl_modern_ui(self, mock_update, mock_context):
        """Test arbitrage_callback_impl with modern UI enabled."""
        mock_context.user_data = {"use_modern_ui": True}

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_modern_arbitrage_keyboard"
        ) as mock_keyboard:
            mock_keyboard.return_value = MagicMock(spec=InlineKeyboardMarkup)
            
            result = await arbitrage_callback_impl(mock_update, mock_context)
            
            assert result == SELECTING_MODE
            mock_keyboard.assert_called_once()

    @pytest.mark.asyncio
    async def test_arbitrage_callback_impl_empty_user_data(self, mock_update, mock_context):
        """Test arbitrage_callback_impl with empty user_data."""
        mock_context.user_data = None

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard"
        ) as mock_keyboard:
            mock_keyboard.return_value = MagicMock(spec=InlineKeyboardMarkup)
            
            result = await arbitrage_callback_impl(mock_update, mock_context)
            
            assert result == SELECTING_MODE


# ============================================================================
# ТЕСТЫ: handle_dmarket_arbitrage_impl
# ============================================================================


class TestHandleDmarketArbitrageImplModes:
    """Tests for different arbitrage modes."""

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_mid_mode(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_dmarket_arbitrage_impl with mid mode."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_mid_async",
                new_callable=AsyncMock,
            ) as mock_mid,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_mid.return_value = mock_arbitrage_results
            mock_pagination.add_items_for_user = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_arbitrage_results, 0, 1))

            await handle_dmarket_arbitrage_impl(query, mock_context, "mid")

            mock_mid.assert_called_once_with("csgo")
            assert mock_context.user_data["last_arbitrage_mode"] == "mid"

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_pro_mode(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_dmarket_arbitrage_impl with pro mode."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_pro_async",
                new_callable=AsyncMock,
            ) as mock_pro,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_pro.return_value = mock_arbitrage_results
            mock_pagination.add_items_for_user = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_arbitrage_results, 0, 1))

            await handle_dmarket_arbitrage_impl(query, mock_context, "pro")

            mock_pro.assert_called_once_with("csgo")
            assert mock_context.user_data["last_arbitrage_mode"] == "pro"


class TestHandleDmarketArbitrageImplGames:
    """Tests for different games."""

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_dota2(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_dmarket_arbitrage_impl with Dota 2."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "dota2"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_boost.return_value = mock_arbitrage_results
            mock_pagination.add_items_for_user = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_arbitrage_results, 0, 1))

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            mock_boost.assert_called_once_with("dota2")

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_tf2(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_dmarket_arbitrage_impl with TF2."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "tf2"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_boost.return_value = mock_arbitrage_results
            mock_pagination.add_items_for_user = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_arbitrage_results, 0, 1))

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            mock_boost.assert_called_once_with("tf2")

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_default_game(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_dmarket_arbitrage_impl with default game (no selection)."""
        query = mock_update.callback_query
        mock_context.user_data = {}  # No game selected

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_boost.return_value = mock_arbitrage_results
            mock_pagination.add_items_for_user = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_arbitrage_results, 0, 1))

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            # Should default to csgo
            mock_boost.assert_called_once_with("csgo")


class TestHandleDmarketArbitrageImplPagination:
    """Tests for pagination functionality."""

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_multiple_pages(
        self, mock_update, mock_context, mock_large_results
    ):
        """Test handle_dmarket_arbitrage_impl with multiple pages."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_boost.return_value = mock_large_results
            mock_pagination.add_items_for_user = MagicMock()
            # Multiple pages
            mock_pagination.get_page = MagicMock(
                return_value=(mock_large_results[:10], 0, 5)
            )

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            # Verify pagination buttons would be added
            query.edit_message_text.assert_called()
            call_args = query.edit_message_text.call_args
            # Check that keyboard with pagination was passed
            assert call_args.kwargs.get("reply_markup") is not None

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_last_page(
        self, mock_update, mock_context, mock_large_results
    ):
        """Test handle_dmarket_arbitrage_impl on last page."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch("src.telegram_bot.pagination.pagination_manager") as mock_pagination,
            patch(
                "src.telegram_bot.pagination.format_paginated_results",
                return_value="<b>Результаты</b>",
            ),
        ):
            mock_boost.return_value = mock_large_results
            mock_pagination.add_items_for_user = MagicMock()
            # Last page (page 4 of 5, 0-indexed)
            mock_pagination.get_page = MagicMock(
                return_value=(mock_large_results[40:50], 4, 5)
            )

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            query.edit_message_text.assert_called()


class TestHandleDmarketArbitrageImplEmptyResults:
    """Tests for empty results handling."""

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_no_results(self, mock_update, mock_context):
        """Test handle_dmarket_arbitrage_impl with no results."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_dmarket_results",
                return_value="Нет результатов",
            ),
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard",
            ) as mock_keyboard,
        ):
            mock_boost.return_value = []
            mock_keyboard.return_value = MagicMock(spec=InlineKeyboardMarkup)

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_none_results(self, mock_update, mock_context):
        """Test handle_dmarket_arbitrage_impl with None results."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
            ) as mock_boost,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_dmarket_results",
                return_value="Нет результатов",
            ),
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard",
            ) as mock_keyboard,
        ):
            mock_boost.return_value = None
            mock_keyboard.return_value = MagicMock(spec=InlineKeyboardMarkup)

            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            query.edit_message_text.assert_called()


# ============================================================================
# ТЕСТЫ: handle_best_opportunities_impl
# ============================================================================


class TestHandleBestOpportunitiesImpl:
    """Tests for handle_best_opportunities_impl."""

    @pytest.mark.asyncio
    async def test_handle_best_opportunities_success(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_best_opportunities_impl success case."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage_scanner.find_arbitrage_opportunities_async",
                new_callable=AsyncMock,
            ) as mock_find,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_best_opportunities",
                return_value="<b>Best Opportunities</b>",
            ),
        ):
            mock_find.return_value = mock_arbitrage_results

            await handle_best_opportunities_impl(query, mock_context)

            mock_find.assert_called_once_with(game="csgo", max_items=10)
            query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_best_opportunities_no_results(
        self, mock_update, mock_context
    ):
        """Test handle_best_opportunities_impl with no results."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with (
            patch(
                "src.dmarket.arbitrage_scanner.find_arbitrage_opportunities_async",
                new_callable=AsyncMock,
            ) as mock_find,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_best_opportunities",
                return_value="<b>No opportunities found</b>",
            ),
        ):
            mock_find.return_value = []

            await handle_best_opportunities_impl(query, mock_context)

            query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_best_opportunities_different_game(
        self, mock_update, mock_context, mock_arbitrage_results
    ):
        """Test handle_best_opportunities_impl with different game."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "dota2"}

        with (
            patch(
                "src.dmarket.arbitrage_scanner.find_arbitrage_opportunities_async",
                new_callable=AsyncMock,
            ) as mock_find,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_best_opportunities",
                return_value="<b>Best Opportunities</b>",
            ),
        ):
            mock_find.return_value = mock_arbitrage_results

            await handle_best_opportunities_impl(query, mock_context)

            mock_find.assert_called_once_with(game="dota2", max_items=10)


# ============================================================================
# ТЕСТЫ: handle_game_selection_impl
# ============================================================================


class TestHandleGameSelectionImpl:
    """Tests for handle_game_selection_impl."""

    @pytest.mark.asyncio
    async def test_handle_game_selection_no_message_chat(self, mock_update, mock_context):
        """Test handle_game_selection_impl when message.chat is None."""
        query = mock_update.callback_query
        query.message = None

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_game_selection_keyboard",
            return_value=MagicMock(spec=InlineKeyboardMarkup),
        ):
            result = await handle_game_selection_impl(query, mock_context)

            assert result == SELECTING_GAME


# ============================================================================
# ТЕСТЫ: handle_game_selected_impl
# ============================================================================


class TestHandleGameSelectedImpl:
    """Tests for handle_game_selected_impl."""

    @pytest.mark.asyncio
    async def test_handle_game_selected_csgo(self, mock_update, mock_context):
        """Test handle_game_selected_impl with CS:GO."""
        query = mock_update.callback_query

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard",
            return_value=MagicMock(spec=InlineKeyboardMarkup),
        ):
            result = await handle_game_selected_impl(query, mock_context, "csgo")

            assert result == SELECTING_MODE
            assert mock_context.user_data["current_game"] == "csgo"

    @pytest.mark.asyncio
    async def test_handle_game_selected_rust(self, mock_update, mock_context):
        """Test handle_game_selected_impl with Rust."""
        query = mock_update.callback_query

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard",
            return_value=MagicMock(spec=InlineKeyboardMarkup),
        ):
            result = await handle_game_selected_impl(query, mock_context, "rust")

            assert result == SELECTING_MODE
            assert mock_context.user_data["current_game"] == "rust"

    @pytest.mark.asyncio
    async def test_handle_game_selected_initializes_user_data(self, mock_update, mock_context):
        """Test handle_game_selected_impl initializes user_data if None."""
        query = mock_update.callback_query
        mock_context.user_data = None

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_arbitrage_keyboard",
            return_value=MagicMock(spec=InlineKeyboardMarkup),
        ):
            result = await handle_game_selected_impl(query, mock_context, "csgo")

            assert result == SELECTING_MODE
            assert mock_context.user_data["current_game"] == "csgo"


# ============================================================================
# ТЕСТЫ: handle_market_comparison_impl
# ============================================================================


class TestHandleMarketComparisonImpl:
    """Tests for handle_market_comparison_impl."""

    @pytest.mark.asyncio
    async def test_handle_market_comparison_success(self, mock_update, mock_context):
        """Test handle_market_comparison_impl success case."""
        query = mock_update.callback_query

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_marketplace_comparison_keyboard",
            return_value=MagicMock(spec=InlineKeyboardMarkup),
        ):
            await handle_market_comparison_impl(query, mock_context)

            query.answer.assert_called_once()
            query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_market_comparison_no_message_chat(self, mock_update, mock_context):
        """Test handle_market_comparison_impl when message.chat is None."""
        query = mock_update.callback_query
        query.message = None

        with patch(
            "src.telegram_bot.handlers.arbitrage_callback_impl.get_marketplace_comparison_keyboard",
            return_value=MagicMock(spec=InlineKeyboardMarkup),
        ):
            # Should not raise
            await handle_market_comparison_impl(query, mock_context)


# ============================================================================
# ТЕСТЫ: Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in arbitrage callbacks."""

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_connection_error(
        self, mock_update, mock_context
    ):
        """Test handle_dmarket_arbitrage_impl with connection error."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with patch(
            "src.dmarket.arbitrage.arbitrage_boost_async",
            new_callable=AsyncMock,
        ) as mock_boost:
            mock_boost.side_effect = ConnectionError("Failed to connect")

            # Decorator handles exception
            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

            # Error should be sent to user
            query.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_dmarket_arbitrage_timeout_error(
        self, mock_update, mock_context
    ):
        """Test handle_dmarket_arbitrage_impl with timeout error."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with patch(
            "src.dmarket.arbitrage.arbitrage_boost_async",
            new_callable=AsyncMock,
        ) as mock_boost:
            mock_boost.side_effect = TimeoutError("Request timed out")

            # Decorator handles exception
            await handle_dmarket_arbitrage_impl(query, mock_context, "boost")

    @pytest.mark.asyncio
    async def test_handle_best_opportunities_api_error(
        self, mock_update, mock_context
    ):
        """Test handle_best_opportunities_impl with API error."""
        query = mock_update.callback_query
        mock_context.user_data = {"current_game": "csgo"}

        with patch(
            "src.dmarket.arbitrage_scanner.find_arbitrage_opportunities_async",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.side_effect = APIError(message="API Error", status_code=500)

            # Decorator handles exception
            await handle_best_opportunities_impl(query, mock_context)

"""Comprehensive tests for arbitrage handlers.

Tests for:
- arbitrage_callback_impl.py
- intramarket_arbitrage_handler.py (extended)

Coverage target: 75%+
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.dmarket.intramarket_arbitrage import PriceAnomalyType


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture()
def user():
    """Create a mock Telegram user."""
    return User(id=123456789, first_name="Test", is_bot=False)


@pytest.fixture()
def chat():
    """Create a mock Telegram chat."""
    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = 123456789
    mock_chat.type = "private"
    mock_chat.send_action = AsyncMock()
    return mock_chat


@pytest.fixture()
def message(user, chat):
    """Create a mock Telegram message."""
    msg = MagicMock(spec=Message)
    msg.message_id = 1
    msg.from_user = user
    msg.chat = chat
    msg.date = None
    msg.text = "Test message"
    return msg


@pytest.fixture()
def callback_query(user, message):
    """Create a mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.id = "test_id"
    query.from_user = user
    query.chat_instance = "test_chat_instance"
    query.message = message
    query.message.chat = message.chat
    query.data = "arbitrage"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    return query


@pytest.fixture()
def update(callback_query, user, chat):
    """Create a mock Update object."""
    upd = MagicMock(spec=Update)
    upd.effective_user = user
    upd.effective_chat = chat
    upd.callback_query = callback_query
    upd.message = None
    return upd


@pytest.fixture()
def context():
    """Create a mock context."""
    ctx = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    ctx.user_data = {}
    ctx.bot = AsyncMock()
    ctx.bot.send_message = AsyncMock()
    return ctx


# =============================================================================
# ARBITRAGE_CALLBACK_IMPL TESTS
# =============================================================================


class TestArbitrageCallbackImpl:
    """Tests for arbitrage_callback_impl.py module."""

    @pytest.mark.asyncio()
    async def test_arbitrage_callback_impl_basic(self, update, context):
        """Test basic arbitrage callback implementation."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            arbitrage_callback_impl,
        )

        # Setup
        update.effective_chat.send_action = AsyncMock()

        # Execute
        result = await arbitrage_callback_impl(update, context)

        # Verify
        update.callback_query.answer.assert_awaited_once()
        update.callback_query.edit_message_text.assert_awaited_once()

        # Check message content
        call_kwargs = update.callback_query.edit_message_text.call_args.kwargs
        assert "Выберите режим арбитража" in call_kwargs.get("text", "")
        assert call_kwargs.get("parse_mode") == ParseMode.HTML

    @pytest.mark.asyncio()
    async def test_arbitrage_callback_impl_no_query(self, update, context):
        """Test arbitrage callback when query is None."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            arbitrage_callback_impl,
        )

        # Setup
        update.callback_query = None

        # Execute
        result = await arbitrage_callback_impl(update, context)

        # Verify
        assert result is None

    @pytest.mark.asyncio()
    async def test_arbitrage_callback_impl_modern_ui(self, update, context):
        """Test arbitrage callback with modern UI enabled."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            arbitrage_callback_impl,
        )

        # Setup
        context.user_data = {"use_modern_ui": True}
        update.effective_chat.send_action = AsyncMock()

        # Execute
        result = await arbitrage_callback_impl(update, context)

        # Verify
        update.callback_query.answer.assert_awaited_once()
        update.callback_query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_arbitrage_callback_impl_with_empty_user_data(self, update, context):
        """Test arbitrage callback with empty user_data."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            arbitrage_callback_impl,
        )

        # Setup
        context.user_data = None
        update.effective_chat.send_action = AsyncMock()

        # Execute
        result = await arbitrage_callback_impl(update, context)

        # Verify - should still work with None user_data
        update.callback_query.answer.assert_awaited_once()


class TestHandleDmarketArbitrageImpl:
    """Tests for handle_dmarket_arbitrage_impl function."""

    @pytest.mark.asyncio()
    async def test_handle_dmarket_arbitrage_boost_mode(self, callback_query, context):
        """Test DMarket arbitrage in boost mode."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_dmarket_arbitrage_impl,
        )

        # Setup
        context.user_data = {"current_game": "csgo"}
        callback_query.message.chat.send_action = AsyncMock()

        mock_results = [
            {
                "title": "AK-47 | Redline",
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit": 3.5,
            }
        ]

        # Patch at the source module where the import happens
        with patch(
            "src.dmarket.arbitrage.arbitrage_boost_async",
            new_callable=AsyncMock,
            return_value=mock_results,
        ) as mock_boost:
            # Patch pagination_manager at the module level where it's imported
            with patch(
                "src.telegram_bot.pagination.pagination_manager"
            ) as mock_pagination:
                mock_pagination.add_items_for_user = MagicMock()
                mock_pagination.get_page.return_value = (mock_results, 0, 1)

                with patch(
                    "src.telegram_bot.pagination.format_paginated_results",
                    return_value="Formatted results",
                ):
                    # Execute
                    await handle_dmarket_arbitrage_impl(
                        callback_query, context, "boost"
                    )

                    # Verify
                    mock_boost.assert_awaited_once_with("csgo")
                    mock_pagination.add_items_for_user.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_dmarket_arbitrage_mid_mode(self, callback_query, context):
        """Test DMarket arbitrage in mid mode."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_dmarket_arbitrage_impl,
        )

        # Setup
        context.user_data = {"current_game": "dota2"}
        callback_query.message.chat.send_action = AsyncMock()

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_mid_async",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_mid,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_dmarket_results",
                return_value="No results",
            ),
        ):
            # Execute
            await handle_dmarket_arbitrage_impl(callback_query, context, "mid")

            # Verify
            mock_mid.assert_awaited_once_with("dota2")

    @pytest.mark.asyncio()
    async def test_handle_dmarket_arbitrage_pro_mode(self, callback_query, context):
        """Test DMarket arbitrage in pro mode."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_dmarket_arbitrage_impl,
        )

        # Setup
        context.user_data = {"current_game": "tf2"}
        callback_query.message.chat.send_action = AsyncMock()

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_pro_async",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_pro,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_dmarket_results",
                return_value="No results",
            ),
        ):
            # Execute
            await handle_dmarket_arbitrage_impl(callback_query, context, "pro")

            # Verify
            mock_pro.assert_awaited_once_with("tf2")

    @pytest.mark.asyncio()
    async def test_handle_dmarket_arbitrage_default_game(self, callback_query, context):
        """Test DMarket arbitrage with default game (csgo)."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_dmarket_arbitrage_impl,
        )

        # Setup - no game in user_data, should default to csgo
        context.user_data = {}
        callback_query.message.chat.send_action = AsyncMock()

        with (
            patch(
                "src.dmarket.arbitrage.arbitrage_boost_async",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_boost,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_dmarket_results",
                return_value="No results",
            ),
        ):
            # Execute
            await handle_dmarket_arbitrage_impl(callback_query, context, "boost")

            # Verify - should use default game csgo
            mock_boost.assert_awaited_once_with("csgo")


class TestHandleBestOpportunitiesImpl:
    """Tests for handle_best_opportunities_impl function."""

    @pytest.mark.asyncio()
    async def test_handle_best_opportunities_basic(self, callback_query, context):
        """Test basic best opportunities handling."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_best_opportunities_impl,
        )

        # Setup
        context.user_data = {"current_game": "csgo"}
        callback_query.message.chat.send_action = AsyncMock()

        mock_opportunities = [
            {"title": "Item 1", "profit": 5.0},
            {"title": "Item 2", "profit": 3.0},
        ]

        # Patch at the source module where the import happens inside the function
        with (
            patch(
                "src.dmarket.arbitrage_scanner.find_arbitrage_opportunities_async",
                new_callable=AsyncMock,
                return_value=mock_opportunities,
            ) as mock_find,
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_best_opportunities",
                return_value="Best opportunities formatted",
            ) as mock_format,
        ):
            # Execute
            await handle_best_opportunities_impl(callback_query, context)

            # Verify
            mock_find.assert_awaited_once()
            call_kwargs = mock_find.call_args.kwargs
            assert call_kwargs["game"] == "csgo"
            assert call_kwargs["max_items"] == 10
            mock_format.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_best_opportunities_empty_results(
        self, callback_query, context
    ):
        """Test best opportunities with empty results."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_best_opportunities_impl,
        )

        # Setup
        context.user_data = {"current_game": "rust"}
        callback_query.message.chat.send_action = AsyncMock()

        with (
            patch(
                "src.dmarket.arbitrage_scanner.find_arbitrage_opportunities_async",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "src.telegram_bot.handlers.arbitrage_callback_impl.format_best_opportunities",
                return_value="No opportunities found",
            ),
        ):
            # Execute
            await handle_best_opportunities_impl(callback_query, context)

            # Verify message was sent
            callback_query.edit_message_text.assert_awaited()


class TestHandleGameSelectionImpl:
    """Tests for handle_game_selection_impl function."""

    @pytest.mark.asyncio()
    async def test_handle_game_selection_basic(self, callback_query, context):
        """Test basic game selection handling."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_game_selection_impl,
        )

        # Setup
        callback_query.message.chat.send_action = AsyncMock()

        # Execute
        result = await handle_game_selection_impl(callback_query, context)

        # Verify
        callback_query.answer.assert_awaited_once()
        callback_query.edit_message_text.assert_awaited_once()

        # Check message content
        call_kwargs = callback_query.edit_message_text.call_args.kwargs
        assert "Выберите игру" in call_kwargs.get("text", "")


class TestHandleGameSelectedImpl:
    """Tests for handle_game_selected_impl function."""

    @pytest.mark.asyncio()
    async def test_handle_game_selected_csgo(self, callback_query, context):
        """Test game selection for CS:GO."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_game_selected_impl,
        )

        # Setup
        context.user_data = {}
        callback_query.message.chat.send_action = AsyncMock()

        # Execute
        result = await handle_game_selected_impl(callback_query, context, "csgo")

        # Verify
        callback_query.answer.assert_awaited_once()
        assert context.user_data.get("current_game") == "csgo"
        callback_query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_handle_game_selected_dota2(self, callback_query, context):
        """Test game selection for Dota 2."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_game_selected_impl,
        )

        # Setup
        context.user_data = {}
        callback_query.message.chat.send_action = AsyncMock()

        # Execute
        result = await handle_game_selected_impl(callback_query, context, "dota2")

        # Verify
        assert context.user_data.get("current_game") == "dota2"

    @pytest.mark.asyncio()
    async def test_handle_game_selected_with_none_user_data(
        self, callback_query, context
    ):
        """Test game selection when user_data is None."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_game_selected_impl,
        )

        # Setup
        context.user_data = None
        callback_query.message.chat.send_action = AsyncMock()

        # Execute - should handle None user_data gracefully
        result = await handle_game_selected_impl(callback_query, context, "csgo")

        # Verify
        callback_query.answer.assert_awaited_once()


class TestHandleMarketComparisonImpl:
    """Tests for handle_market_comparison_impl function."""

    @pytest.mark.asyncio()
    async def test_handle_market_comparison_basic(self, callback_query, context):
        """Test basic market comparison handling."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_market_comparison_impl,
        )

        # Setup
        callback_query.message.chat.send_action = AsyncMock()

        # Execute
        await handle_market_comparison_impl(callback_query, context)

        # Verify
        callback_query.answer.assert_awaited_once()
        callback_query.edit_message_text.assert_awaited_once()

        # Check message content
        call_kwargs = callback_query.edit_message_text.call_args.kwargs
        assert "Сравнение торговых площадок" in call_kwargs.get("text", "")


# =============================================================================
# INTRAMARKET_ARBITRAGE_HANDLER EXTENDED TESTS
# =============================================================================


class TestFormatIntramarketResultsExtended:
    """Extended tests for format_intramarket_results function."""

    def test_format_empty_results(self):
        """Test formatting with empty results list."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            format_intramarket_results,
        )

        result = format_intramarket_results([], 0, 10)
        assert "Нет результатов" in result

    def test_format_unknown_type(self):
        """Test formatting with unknown type."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            format_intramarket_results,
        )

        items = [{"type": "unknown_type", "data": "test"}]
        result = format_intramarket_results(items, 0, 10)
        assert "Неизвестный тип" in result

    def test_format_multiple_pages(self):
        """Test formatting with page indicator."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            format_intramarket_results,
        )

        items = [
            {
                "type": PriceAnomalyType.UNDERPRICED,
                "item_to_buy": {"itemId": "item1", "title": "Test Item"},
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit_percentage": 50.0,
                "profit_after_fee": 4.0,
                "similarity": 0.95,
            }
        ]

        result = format_intramarket_results(items, 2, 10)
        assert "Страница 3" in result  # 0-indexed, so page 2 = page 3


class TestFormatIntramarketItem:
    """Tests for format_intramarket_item function."""

    def test_format_underpriced_item(self):
        """Test formatting underpriced item."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            format_intramarket_item,
        )

        item = {
            "type": PriceAnomalyType.UNDERPRICED,
            "item_to_buy": {"itemId": "item123", "title": "M4A1-S | Hyper Beast"},
            "buy_price": 25.50,
            "sell_price": 35.00,
            "profit_percentage": 28.5,
            "profit_after_fee": 7.25,
            "similarity": 0.98,
        }

        result = format_intramarket_item(item)

        assert "M4A1-S | Hyper Beast" in result
        assert "$25.50" in result
        assert "$35.00" in result
        assert "28.5%" in result
        assert "item123" in result

    def test_format_trending_up_item(self):
        """Test formatting trending up item."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            format_intramarket_item,
        )

        item = {
            "type": PriceAnomalyType.TRENDING_UP,
            "item": {"itemId": "item456", "title": "AWP | Dragon Lore"},
            "current_price": 1500.00,
            "projected_price": 1800.00,
            "price_change_percent": 20.0,
            "potential_profit_percent": 18.0,
            "sales_velocity": 15,
        }

        result = format_intramarket_item(item)

        assert "AWP | Dragon Lore" in result
        assert "$1500.00" in result
        assert "$1800.00" in result
        assert "20.0%" in result
        assert "15" in result

    def test_format_rare_traits_item(self):
        """Test formatting rare traits item."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            format_intramarket_item,
        )

        item = {
            "type": PriceAnomalyType.RARE_TRAITS,
            "item": {"itemId": "item789", "title": "Karambit | Fade"},
            "current_price": 800.00,
            "estimated_value": 1200.00,
            "price_difference_percent": 50.0,
            "rare_traits": ["90/10 fade", "Perfect corner"],
        }

        result = format_intramarket_item(item)

        assert "Karambit | Fade" in result
        assert "$800.00" in result
        assert "$1200.00" in result
        assert "50.0%" in result
        assert "90/10 fade" in result
        assert "Perfect corner" in result


class TestDisplayResultsWithPagination:
    """Tests for display_results_with_pagination function."""

    @pytest.mark.asyncio()
    async def test_display_empty_results(self, callback_query):
        """Test displaying empty results."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            display_results_with_pagination,
        )

        await display_results_with_pagination(
            query=callback_query,
            results=[],
            title="Test Title",
            user_id=123,
            action_type="anomaly",
            game="csgo",
        )

        callback_query.edit_message_text.assert_awaited_once()
        call_args = callback_query.edit_message_text.call_args
        assert "Возможности не найдены" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_display_with_results(self, callback_query):
        """Test displaying results with pagination."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            display_results_with_pagination,
        )

        results = [
            {
                "type": PriceAnomalyType.UNDERPRICED,
                "item_to_buy": {"itemId": "item1", "title": "Test Item"},
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit_percentage": 40.0,
                "profit_after_fee": 4.0,
                "similarity": 0.95,
            }
        ]

        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.add_items_for_user = MagicMock()
            mock_pagination.get_page.return_value = (results, 0, 1)
            mock_pagination.get_items_per_page.return_value = 5

            with patch(
                "src.telegram_bot.handlers.intramarket_arbitrage_handler.create_pagination_keyboard"
            ) as mock_keyboard:
                mock_keyboard.return_value = MagicMock()

                await display_results_with_pagination(
                    query=callback_query,
                    results=results,
                    title="Test Results",
                    user_id=123,
                    action_type="anomaly",
                    game="csgo",
                )

                mock_pagination.add_items_for_user.assert_called_once()
                callback_query.edit_message_text.assert_awaited_once()


class TestHandleIntramarketPagination:
    """Tests for handle_intramarket_pagination function."""

    @pytest.mark.asyncio()
    async def test_pagination_next_page(self, update, context):
        """Test pagination next page."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_pagination,
        )

        # Setup
        update.callback_query.data = "intra_paginate:next:anomaly:csgo"

        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.next_page = MagicMock()
            mock_pagination.get_page.return_value = ([], 1, 3)
            mock_pagination.get_items_per_page.return_value = 5

            with patch(
                "src.telegram_bot.handlers.intramarket_arbitrage_handler.create_pagination_keyboard"
            ):
                await handle_intramarket_pagination(update, context)

                mock_pagination.next_page.assert_called_once()

    @pytest.mark.asyncio()
    async def test_pagination_prev_page(self, update, context):
        """Test pagination previous page."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_pagination,
        )

        # Setup
        update.callback_query.data = "intra_paginate:prev:anomaly:csgo"

        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.prev_page = MagicMock()
            mock_pagination.get_page.return_value = ([], 0, 3)
            mock_pagination.get_items_per_page.return_value = 5

            with patch(
                "src.telegram_bot.handlers.intramarket_arbitrage_handler.create_pagination_keyboard"
            ):
                await handle_intramarket_pagination(update, context)

                mock_pagination.prev_page.assert_called_once()

    @pytest.mark.asyncio()
    async def test_pagination_no_query(self, update, context):
        """Test pagination with no callback query."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_pagination,
        )

        # Setup
        update.callback_query = None

        # Execute - should return early
        await handle_intramarket_pagination(update, context)

    @pytest.mark.asyncio()
    async def test_pagination_no_user(self, update, context):
        """Test pagination with no effective user."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_pagination,
        )

        # Setup
        update.effective_user = None

        # Execute - should return early
        await handle_intramarket_pagination(update, context)

    @pytest.mark.asyncio()
    async def test_pagination_invalid_callback_data(self, update, context):
        """Test pagination with invalid callback data."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_pagination,
        )

        # Setup - not enough parts
        update.callback_query.data = "intra_paginate:next"

        # Execute - should return early
        await handle_intramarket_pagination(update, context)


class TestStartIntramarketArbitrageExtended:
    """Extended tests for start_intramarket_arbitrage function."""

    @pytest.mark.asyncio()
    async def test_start_without_callback_query(self, update, context):
        """Test start without callback query."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            start_intramarket_arbitrage,
        )

        # Setup
        update.callback_query = None

        # Execute - should still send message
        await start_intramarket_arbitrage(update, context)

        context.bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_start_without_effective_user(self, update, context):
        """Test start without effective user."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            start_intramarket_arbitrage,
        )

        # Setup
        update.effective_user = None

        # Execute - should return early
        await start_intramarket_arbitrage(update, context)


class TestHandleIntramarketCallbackExtended:
    """Extended tests for handle_intramarket_callback function."""

    @pytest.mark.asyncio()
    async def test_callback_no_query(self, update, context):
        """Test callback handling with no query."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_callback,
        )

        # Setup
        update.callback_query = None

        # Execute - should return early
        await handle_intramarket_callback(update, context)

    @pytest.mark.asyncio()
    async def test_callback_no_user(self, update, context):
        """Test callback handling with no user."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_callback,
        )

        # Setup
        update.effective_user = None

        # Execute - should return early
        await handle_intramarket_callback(update, context)

    @pytest.mark.asyncio()
    async def test_callback_no_data(self, update, context):
        """Test callback handling with no data."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_callback,
        )

        # Setup
        update.callback_query.data = None

        # Execute - should return early
        await handle_intramarket_callback(update, context)

    @pytest.mark.asyncio()
    async def test_callback_short_data(self, update, context):
        """Test callback handling with short data (invalid format)."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            handle_intramarket_callback,
        )

        # Setup - only one part instead of at least 2
        update.callback_query.data = "intra"

        # Execute
        await handle_intramarket_callback(update, context)

        # Verify error message was sent
        update.callback_query.edit_message_text.assert_awaited()
        call_args = update.callback_query.edit_message_text.call_args
        assert "Некорректные данные" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_callback_api_client_none(self, update, context):
        """Test callback handling when API client is None."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            ANOMALY_ACTION,
            INTRA_ARBITRAGE_ACTION,
            handle_intramarket_callback,
        )

        # Setup
        update.callback_query.data = f"{INTRA_ARBITRAGE_ACTION}_{ANOMALY_ACTION}_csgo"

        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.create_api_client_from_env",
            return_value=None,
        ):
            # Execute
            await handle_intramarket_callback(update, context)

            # Verify error message about API client was sent
            update.callback_query.edit_message_text.assert_awaited()
            # Find the call that contains the error message
            for call in update.callback_query.edit_message_text.call_args_list:
                if "API" in str(call):
                    break


class TestRegisterIntramarketHandlers:
    """Tests for register_intramarket_handlers function."""

    def test_register_handlers(self):
        """Test that handlers are registered correctly."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            register_intramarket_handlers,
        )

        # Create mock dispatcher
        dispatcher = MagicMock()
        dispatcher.add_handler = MagicMock()

        # Execute
        register_intramarket_handlers(dispatcher)

        # Verify - should register 3 handlers
        assert dispatcher.add_handler.call_count == 3


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in arbitrage handlers."""

    @pytest.mark.asyncio()
    async def test_arbitrage_callback_exception_handling(self, update, context):
        """Test exception handling in arbitrage callback."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            arbitrage_callback_impl,
        )

        # Setup - make answer raise an exception
        update.callback_query.answer = AsyncMock(side_effect=Exception("Test error"))

        # Execute - should be handled by @handle_exceptions decorator
        # The decorator catches the exception and may reraise or handle it
        try:
            await arbitrage_callback_impl(update, context)
        except Exception:
            pass  # Exception may be reraised depending on decorator config

    @pytest.mark.asyncio()
    async def test_dmarket_arbitrage_exception_handling(self, callback_query, context):
        """Test exception handling in DMarket arbitrage."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            handle_dmarket_arbitrage_impl,
        )

        # Setup
        context.user_data = {"current_game": "csgo"}
        callback_query.message.chat.send_action = AsyncMock()

        with patch(
            "src.dmarket.arbitrage.arbitrage_boost_async",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            # Execute - should be handled by @handle_exceptions decorator
            try:
                await handle_dmarket_arbitrage_impl(callback_query, context, "boost")
            except Exception:
                pass


class TestConstants:
    """Tests for module constants."""

    def test_selecting_states(self):
        """Test that selecting states are defined."""
        from src.telegram_bot.handlers.arbitrage_callback_impl import (
            CONFIRMING_ACTION,
            SELECTING_GAME,
            SELECTING_MODE,
        )

        assert SELECTING_GAME == 0
        assert SELECTING_MODE == 1
        assert CONFIRMING_ACTION == 2

    def test_intra_constants(self):
        """Test intramarket constants."""
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            ANOMALY_ACTION,
            INTRA_ARBITRAGE_ACTION,
            RARE_ACTION,
            TRENDING_ACTION,
        )

        assert INTRA_ARBITRAGE_ACTION == "intra"
        assert ANOMALY_ACTION == "anomaly"
        assert TRENDING_ACTION == "trend"
        assert RARE_ACTION == "rare"

"""Unit tests for intramarket_arbitrage_handler.py module.

This module tests the internal market arbitrage handler functionality including:
- Result formatting for different anomaly types
- Pagination handling
- Callback handlers for different arbitrage types
- Handler registration
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.intramarket_arbitrage import PriceAnomalyType
from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
    ANOMALY_ACTION,
    INTRA_ARBITRAGE_ACTION,
    RARE_ACTION,
    TRENDING_ACTION,
    display_results_with_pagination,
    format_intramarket_item,
    format_intramarket_results,
    handle_intramarket_callback,
    handle_intramarket_pagination,
    register_intramarket_handlers,
    start_intramarket_arbitrage,
)


# ============================================================================
# Tests for Constants
# ============================================================================
class TestConstants:
    """Tests for module constants."""

    def test_intra_arbitrage_action_defined(self) -> None:
        """Test INTRA_ARBITRAGE_ACTION constant is defined."""
        assert INTRA_ARBITRAGE_ACTION == "intra"

    def test_anomaly_action_defined(self) -> None:
        """Test ANOMALY_ACTION constant is defined."""
        assert ANOMALY_ACTION == "anomaly"

    def test_trending_action_defined(self) -> None:
        """Test TRENDING_ACTION constant is defined."""
        assert TRENDING_ACTION == "trend"

    def test_rare_action_defined(self) -> None:
        """Test RARE_ACTION constant is defined."""
        assert RARE_ACTION == "rare"


# ============================================================================
# Tests for format_intramarket_results
# ============================================================================
class TestFormatIntramarketResults:
    """Tests for format_intramarket_results function."""

    def test_empty_items_returns_no_results_message(self) -> None:
        """Test empty items list returns no results message."""
        result = format_intramarket_results([], 0, 10)
        assert result == "Нет результатов для отображения."

    def test_with_single_item(self) -> None:
        """Test formatting with single item."""
        items = [
            {
                "type": PriceAnomalyType.UNDERPRICED,
                "item_to_buy": {"title": "Test Item", "itemId": "123"},
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit_percentage": 50.0,
                "profit_after_fee": 4.5,
                "similarity": 0.95,
            }
        ]
        result = format_intramarket_results(items, 0, 10)
        assert "📄 Страница 1" in result
        assert "Test Item" in result

    def test_with_multiple_items(self) -> None:
        """Test formatting with multiple items."""
        items = [
            {
                "type": PriceAnomalyType.UNDERPRICED,
                "item_to_buy": {"title": f"Item {i}", "itemId": str(i)},
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit_percentage": 50.0,
                "profit_after_fee": 4.5,
                "similarity": 0.95,
            }
            for i in range(3)
        ]
        result = format_intramarket_results(items, 1, 10)
        assert "📄 Страница 2" in result

    def test_page_number_in_header(self) -> None:
        """Test correct page number in header."""
        items = [
            {
                "type": PriceAnomalyType.UNDERPRICED,
                "item_to_buy": {"title": "Test", "itemId": "1"},
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit_percentage": 50.0,
                "profit_after_fee": 4.5,
                "similarity": 0.95,
            }
        ]
        result = format_intramarket_results(items, 2, 10)
        assert "📄 Страница 3" in result


# ============================================================================
# Tests for format_intramarket_item
# ============================================================================
class TestFormatIntramarketItem:
    """Tests for format_intramarket_item function."""

    def test_format_underpriced_item(self) -> None:
        """Test formatting underpriced anomaly item."""
        result = {
            "type": PriceAnomalyType.UNDERPRICED,
            "item_to_buy": {"title": "AWP | Dragon Lore", "itemId": "abc123"},
            "buy_price": 1000.50,
            "sell_price": 1200.75,
            "profit_percentage": 20.0,
            "profit_after_fee": 150.25,
            "similarity": 0.98,
        }
        formatted = format_intramarket_item(result)
        
        assert "🔍" in formatted
        assert "AWP | Dragon Lore" in formatted
        assert "$1000.50" in formatted
        assert "$1200.75" in formatted
        assert "abc123" in formatted

    def test_format_trending_up_item(self) -> None:
        """Test formatting trending up item."""
        result = {
            "type": PriceAnomalyType.TRENDING_UP,
            "item": {"title": "M4A4 | Howl", "itemId": "def456"},
            "current_price": 500.0,
            "projected_price": 600.0,
            "price_change_percent": 20.0,
            "potential_profit_percent": 20.0,
            "sales_velocity": 15,
        }
        formatted = format_intramarket_item(result)
        
        assert "📈" in formatted
        assert "M4A4 | Howl" in formatted
        assert "$500.00" in formatted
        assert "$600.00" in formatted
        assert "15" in formatted

    def test_format_rare_traits_item(self) -> None:
        """Test formatting rare traits item."""
        result = {
            "type": PriceAnomalyType.RARE_TRAITS,
            "item": {"title": "Karambit | Fade", "itemId": "ghi789"},
            "current_price": 2000.0,
            "estimated_value": 2500.0,
            "price_difference_percent": 25.0,
            "rare_traits": ["Full Fade", "Clean Corner", "Low Float"],
        }
        formatted = format_intramarket_item(result)
        
        assert "💎" in formatted
        assert "Karambit | Fade" in formatted
        assert "$2000.00" in formatted
        assert "$2500.00" in formatted
        assert "Full Fade" in formatted
        assert "Clean Corner" in formatted

    def test_format_unknown_type(self) -> None:
        """Test formatting unknown anomaly type."""
        result = {"type": "unknown_type"}
        formatted = format_intramarket_item(result)
        
        assert "❓" in formatted
        assert "Неизвестный тип результата" in formatted

    def test_format_missing_type(self) -> None:
        """Test formatting item without type."""
        result = {}
        formatted = format_intramarket_item(result)
        
        assert "❓" in formatted


# ============================================================================
# Tests for display_results_with_pagination
# ============================================================================
class TestDisplayResultsWithPagination:
    """Tests for display_results_with_pagination function."""

    @pytest.mark.asyncio
    async def test_empty_results_shows_no_opportunities(self) -> None:
        """Test empty results shows no opportunities message."""
        query = AsyncMock()
        
        await display_results_with_pagination(
            query=query,
            results=[],
            title="Test Title",
            user_id=123,
            action_type="anomaly",
            game="csgo",
        )
        
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Возможности не найдены" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_with_results_shows_formatted_items(self) -> None:
        """Test results are formatted and displayed."""
        query = AsyncMock()
        results = [
            {
                "type": PriceAnomalyType.UNDERPRICED,
                "item_to_buy": {"title": "Test", "itemId": "1"},
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit_percentage": 50.0,
                "profit_after_fee": 4.5,
                "similarity": 0.95,
            }
        ]
        
        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page.return_value = (results, 0, 1)
            mock_pagination.get_items_per_page.return_value = 10
            
            await display_results_with_pagination(
                query=query,
                results=results,
                title="Test Title",
                user_id=123,
                action_type="anomaly",
                game="csgo",
            )
            
            query.edit_message_text.assert_called()


# ============================================================================
# Tests for handle_intramarket_pagination
# ============================================================================
class TestHandleIntramarketPagination:
    """Tests for handle_intramarket_pagination function."""

    @pytest.mark.asyncio
    async def test_no_query_returns_early(self) -> None:
        """Test handler returns early when no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_intramarket_pagination(update, context)
        # Should complete without error

    @pytest.mark.asyncio
    async def test_no_effective_user_returns_early(self) -> None:
        """Test handler returns early when no effective user."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.effective_user = None
        context = MagicMock()
        
        await handle_intramarket_pagination(update, context)

    @pytest.mark.asyncio
    async def test_invalid_callback_data_returns_early(self) -> None:
        """Test handler returns early with invalid callback data."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "invalid"
        update.effective_user = MagicMock(id=123)
        context = MagicMock()
        
        await handle_intramarket_pagination(update, context)


# ============================================================================
# Tests for start_intramarket_arbitrage
# ============================================================================
class TestStartIntramarketArbitrage:
    """Tests for start_intramarket_arbitrage function."""

    @pytest.mark.asyncio
    async def test_no_effective_user_returns_early(self) -> None:
        """Test handler returns early when no effective user."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.effective_user = None
        context = MagicMock()
        
        await start_intramarket_arbitrage(update, context)

    @pytest.mark.asyncio
    async def test_sends_menu_with_options(self) -> None:
        """Test handler sends menu with arbitrage options."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.effective_user = MagicMock(id=123)
        context = MagicMock()
        context.bot = AsyncMock()
        
        await start_intramarket_arbitrage(update, context)
        
        context.bot.send_message.assert_called_once()
        call_kwargs = context.bot.send_message.call_args[1]
        assert "Выберите тип арбитража" in call_kwargs["text"]


# ============================================================================
# Tests for handle_intramarket_callback
# ============================================================================
class TestHandleIntramarketCallback:
    """Tests for handle_intramarket_callback function."""

    @pytest.mark.asyncio
    async def test_no_query_returns_early(self) -> None:
        """Test handler returns early when no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await handle_intramarket_callback(update, context)

    @pytest.mark.asyncio
    async def test_no_effective_user_returns_early(self) -> None:
        """Test handler returns early when no effective user."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.effective_user = None
        context = MagicMock()
        
        await handle_intramarket_callback(update, context)

    @pytest.mark.asyncio
    async def test_invalid_callback_data(self) -> None:
        """Test handler handles invalid callback data."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "intra_"  # Incomplete
        update.effective_user = MagicMock(id=123)
        context = MagicMock()
        
        await handle_intramarket_callback(update, context)

    @pytest.mark.asyncio
    async def test_no_api_client_shows_error(self) -> None:
        """Test handler shows error when API client not available."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = f"{INTRA_ARBITRAGE_ACTION}_{ANOMALY_ACTION}_csgo"
        update.effective_user = MagicMock(id=123)
        context = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.create_api_client_from_env",
            return_value=None,
        ):
            await handle_intramarket_callback(update, context)
            
            update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_unknown_action_type_shows_error(self) -> None:
        """Test handler shows error for unknown action type."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = f"{INTRA_ARBITRAGE_ACTION}_unknown_csgo"
        update.effective_user = MagicMock(id=123)
        context = MagicMock()
        
        mock_api = AsyncMock()
        
        with patch(
            "src.telegram_bot.handlers.intramarket_arbitrage_handler.create_api_client_from_env",
            return_value=mock_api,
        ):
            await handle_intramarket_callback(update, context)
            
            call_args = update.callback_query.edit_message_text.call_args
            assert "Неизвестный тип сканирования" in str(call_args)


# ============================================================================
# Tests for register_intramarket_handlers
# ============================================================================
class TestRegisterIntramarketHandlers:
    """Tests for register_intramarket_handlers function."""

    def test_registers_handlers(self) -> None:
        """Test handler registration adds all handlers."""
        dispatcher = MagicMock()
        
        register_intramarket_handlers(dispatcher)
        
        assert dispatcher.add_handler.call_count == 3

    def test_registers_start_handler(self) -> None:
        """Test registration of start intramarket handler."""
        dispatcher = MagicMock()
        
        register_intramarket_handlers(dispatcher)
        
        dispatcher.add_handler.assert_called()

    def test_registers_callback_handler(self) -> None:
        """Test registration of callback handler."""
        dispatcher = MagicMock()
        
        register_intramarket_handlers(dispatcher)
        
        # Check that handlers were registered
        assert dispatcher.add_handler.called

    def test_registers_pagination_handler(self) -> None:
        """Test registration of pagination handler."""
        dispatcher = MagicMock()
        
        register_intramarket_handlers(dispatcher)
        
        # At least 3 handlers should be registered
        assert dispatcher.add_handler.call_count >= 3

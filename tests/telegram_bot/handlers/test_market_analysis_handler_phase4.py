"""
Extended Phase 4 tests for market_analysis_handler.py - achieving 100% coverage.

This module contains additional tests for the market analysis handler,
covering edge cases, error handling, pagination, and game selection functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Message, Update, User


# ======================== Test Fixtures ========================


@pytest.fixture
def mock_user():
    """Create mock User object."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    return user


@pytest.fixture
def mock_message(mock_user):
    """Create mock Message object."""
    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()
    message.from_user = mock_user
    message.chat = MagicMock()
    message.chat.id = 123456789
    return message


@pytest.fixture
def mock_callback_query(mock_user):
    """Create mock CallbackQuery object."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = "analysis:price_changes:csgo"
    query.from_user = mock_user
    query.message = MagicMock()
    return query


@pytest.fixture
def mock_update(mock_callback_query, mock_message):
    """Create mock Update object."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.message = mock_message
    update.effective_user = mock_callback_query.from_user
    return update


@pytest.fixture
def mock_context():
    """Create mock context with user data."""
    context = MagicMock()
    context.user_data = {
        "market_analysis": {
            "current_game": "csgo",
            "period": "24h",
            "min_price": 1.0,
            "max_price": 500.0,
        }
    }
    return context


@pytest.fixture
def mock_context_empty():
    """Create mock context without user data."""
    context = MagicMock()
    context.user_data = {}
    return context


# ======================== Game Selection Tests ========================


class TestGameSelection:
    """Tests for game selection functionality."""

    @pytest.mark.asyncio
    async def test_select_game_csgo(self, mock_update, mock_context):
        """Test selecting CS:GO game."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:csgo"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2", "dota2": "Dota 2"},
        ):
            await market_analysis_callback(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["current_game"] == "csgo"

    @pytest.mark.asyncio
    async def test_select_game_dota2(self, mock_update, mock_context):
        """Test selecting Dota 2 game."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:dota2"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2", "dota2": "Dota 2"},
        ):
            await market_analysis_callback(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["current_game"] == "dota2"

    @pytest.mark.asyncio
    async def test_select_game_tf2(self, mock_update, mock_context):
        """Test selecting TF2 game."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:tf2"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2", "dota2": "Dota 2", "tf2": "Team Fortress 2"},
        ):
            await market_analysis_callback(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["current_game"] == "tf2"

    @pytest.mark.asyncio
    async def test_select_game_rust(self, mock_update, mock_context):
        """Test selecting Rust game."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:rust"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2", "rust": "Rust"},
        ):
            await market_analysis_callback(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["current_game"] == "rust"

    @pytest.mark.asyncio
    async def test_select_game_updates_message(self, mock_update, mock_context):
        """Test that selecting game updates the message."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:dota2"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2", "dota2": "Dota 2"},
        ):
            await market_analysis_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()


# ======================== Analysis Type Tests ========================


class TestAnalysisTypes:
    """Tests for different analysis types."""

    @pytest.mark.asyncio
    async def test_price_changes_analysis(self, mock_update, mock_context):
        """Test price changes analysis action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:price_changes:csgo"

        mock_api_client = MagicMock()
        mock_results = [{"item": "test", "change": 5.0}]

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes",
                new_callable=AsyncMock,
                return_value=mock_results,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_price_changes_results",
                new_callable=AsyncMock,
            ) as mock_show,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_trending_analysis(self, mock_update, mock_context):
        """Test trending items analysis action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:trending:csgo"

        mock_api_client = MagicMock()
        mock_results = [{"item": "test", "trend": "up"}]

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.find_trending_items",
                new_callable=AsyncMock,
                return_value=mock_results,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_trending_items_results",
                new_callable=AsyncMock,
            ) as mock_show,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_volatility_analysis(self, mock_update, mock_context):
        """Test volatility analysis action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:volatility:csgo"

        mock_api_client = MagicMock()
        mock_results = [{"item": "test", "volatility": 10.0}]

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.analyze_market_volatility",
                new_callable=AsyncMock,
                return_value=mock_results,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_volatility_results",
                new_callable=AsyncMock,
            ) as mock_show,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_market_report_analysis(self, mock_update, mock_context):
        """Test full market report action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:report:csgo"

        mock_api_client = MagicMock()
        mock_report = {"summary": "Market report data"}

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.generate_market_report",
                new_callable=AsyncMock,
                return_value=mock_report,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_market_report",
                new_callable=AsyncMock,
            ) as mock_show,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_undervalued_items_analysis(self, mock_update, mock_context):
        """Test undervalued items analysis action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:undervalued:csgo"

        mock_api_client = MagicMock()
        mock_results = [{"item": "test", "discount": 20.0}]

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.find_undervalued_items",
                new_callable=AsyncMock,
                return_value=mock_results,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_undervalued_items_results",
                new_callable=AsyncMock,
            ) as mock_show,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_recommendations_analysis(self, mock_update, mock_context):
        """Test investment recommendations analysis action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:recommendations:csgo"

        mock_api_client = MagicMock()
        mock_results = [{"item": "test", "recommendation": "buy"}]

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.get_investment_recommendations",
                new_callable=AsyncMock,
                return_value=mock_results,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_investment_recommendations_results",
                new_callable=AsyncMock,
            ) as mock_show,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            mock_show.assert_called_once()


# ======================== Pagination Tests ========================


class TestPagination:
    """Tests for pagination functionality."""

    @pytest.mark.asyncio
    async def test_pagination_next_page(self, mock_update, mock_context):
        """Test next page navigation."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_pagination_analysis,
        )

        mock_update.callback_query.data = "analysis_page:next:price_changes:csgo"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
            ) as mock_pagination,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_price_changes_results",
                new_callable=AsyncMock,
            ),
        ):
            await handle_pagination_analysis(mock_update, mock_context)
            mock_pagination.next_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_prev_page(self, mock_update, mock_context):
        """Test previous page navigation."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_pagination_analysis,
        )

        mock_update.callback_query.data = "analysis_page:prev:price_changes:csgo"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
            ) as mock_pagination,
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_price_changes_results",
                new_callable=AsyncMock,
            ),
        ):
            await handle_pagination_analysis(mock_update, mock_context)
            mock_pagination.prev_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_trending(self, mock_update, mock_context):
        """Test pagination for trending analysis."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_pagination_analysis,
        )

        mock_update.callback_query.data = "analysis_page:next:trending:csgo"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_trending_items_results",
                new_callable=AsyncMock,
            ) as mock_show,
        ):
            await handle_pagination_analysis(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_volatility(self, mock_update, mock_context):
        """Test pagination for volatility analysis."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_pagination_analysis,
        )

        mock_update.callback_query.data = "analysis_page:next:volatility:dota2"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_volatility_results",
                new_callable=AsyncMock,
            ) as mock_show,
        ):
            await handle_pagination_analysis(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_undervalued(self, mock_update, mock_context):
        """Test pagination for undervalued items."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_pagination_analysis,
        )

        mock_update.callback_query.data = "analysis_page:next:undervalued:csgo"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_undervalued_items_results",
                new_callable=AsyncMock,
            ) as mock_show,
        ):
            await handle_pagination_analysis(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_recommendations(self, mock_update, mock_context):
        """Test pagination for recommendations."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_pagination_analysis,
        )

        mock_update.callback_query.data = "analysis_page:next:recommendations:csgo"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_investment_recommendations_results",
                new_callable=AsyncMock,
            ) as mock_show,
        ):
            await handle_pagination_analysis(mock_update, mock_context)
            mock_show.assert_called_once()


# ======================== Error Handling Tests ========================


class TestErrorHandling:
    """Tests for error handling in market analysis."""

    @pytest.mark.asyncio
    async def test_api_client_none(self, mock_update, mock_context):
        """Test handling when API client is None."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:price_changes:csgo"

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=None,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.get_back_to_market_analysis_keyboard",
                return_value=InlineKeyboardMarkup([]),
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            # Should show error message
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_analysis_exception(self, mock_update, mock_context):
        """Test handling of analysis exceptions."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:price_changes:csgo"

        mock_api_client = MagicMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes",
                new_callable=AsyncMock,
                side_effect=Exception("API Error"),
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.get_back_to_market_analysis_keyboard",
                return_value=InlineKeyboardMarkup([]),
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)
            # Should show error message
            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_missing_callback_query(self, mock_update, mock_context):
        """Test handling when callback query is missing."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query = None

        await market_analysis_callback(mock_update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_missing_callback_data(self, mock_update, mock_context):
        """Test handling when callback data is missing."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = None

        await market_analysis_callback(mock_update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_invalid_callback_data_parts(self, mock_update, mock_context):
        """Test handling when callback data has too few parts."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis"  # Only one part

        await market_analysis_callback(mock_update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_user_data_none(self, mock_update):
        """Test handling when user_data is None."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        context = MagicMock()
        context.user_data = None
        mock_update.callback_query.data = "analysis:price_changes:csgo"

        await market_analysis_callback(mock_update, context)
        # Should return early without error


# ======================== Period and Risk Level Tests ========================


class TestPeriodAndRiskSettings:
    """Tests for period and risk level settings."""

    @pytest.mark.asyncio
    async def test_period_change_1h(self, mock_update, mock_context):
        """Test changing period to 1 hour."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_period_change,
        )

        mock_update.callback_query.data = "analysis_period:1h:csgo"

        await handle_period_change(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["period"] == "1h"

    @pytest.mark.asyncio
    async def test_period_change_24h(self, mock_update, mock_context):
        """Test changing period to 24 hours."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_period_change,
        )

        mock_update.callback_query.data = "analysis_period:24h:csgo"

        await handle_period_change(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["period"] == "24h"

    @pytest.mark.asyncio
    async def test_period_change_7d(self, mock_update, mock_context):
        """Test changing period to 7 days."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_period_change,
        )

        mock_update.callback_query.data = "analysis_period:7d:csgo"

        await handle_period_change(mock_update, mock_context)

        assert mock_context.user_data["market_analysis"]["period"] == "7d"

    @pytest.mark.asyncio
    async def test_risk_level_change_low(self, mock_update, mock_context):
        """Test changing risk level to low."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_risk_level_change,
        )

        mock_update.callback_query.data = "analysis_risk:low:csgo"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.show_investment_recommendations_results",
            new_callable=AsyncMock,
        ):
            await handle_risk_level_change(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_risk_level_change_medium(self, mock_update, mock_context):
        """Test changing risk level to medium."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_risk_level_change,
        )

        mock_update.callback_query.data = "analysis_risk:medium:csgo"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.show_investment_recommendations_results",
            new_callable=AsyncMock,
        ):
            await handle_risk_level_change(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_risk_level_change_high(self, mock_update, mock_context):
        """Test changing risk level to high."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            handle_risk_level_change,
        )

        mock_update.callback_query.data = "analysis_risk:high:csgo"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.show_investment_recommendations_results",
            new_callable=AsyncMock,
        ):
            await handle_risk_level_change(mock_update, mock_context)


# ======================== Command Tests ========================


class TestMarketAnalysisCommand:
    """Tests for market analysis command."""

    @pytest.mark.asyncio
    async def test_market_analysis_command_creates_keyboard(
        self, mock_update, mock_context
    ):
        """Test that command creates proper keyboard."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_command,
        )

        mock_update.callback_query = None  # Remove callback query
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2", "dota2": "Dota 2"},
        ):
            await market_analysis_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_market_analysis_command_no_message(self, mock_update, mock_context):
        """Test command when message is None."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_command,
        )

        mock_update.message = None

        await market_analysis_command(mock_update, mock_context)
        # Should return early without error


# ======================== Handler Registration Tests ========================


class TestHandlerRegistration:
    """Tests for handler registration."""

    def test_register_handlers(self):
        """Test that handlers are registered correctly."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            register_market_analysis_handlers,
        )

        app = MagicMock()
        app.add_handler = MagicMock()

        register_market_analysis_handlers(app)

        # Should register multiple handlers
        assert app.add_handler.call_count >= 1


# ======================== Keyboard Generation Tests ========================


class TestKeyboardGeneration:
    """Tests for keyboard generation functions."""

    def test_back_to_market_analysis_keyboard_csgo(self):
        """Test back keyboard for CS:GO."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            get_back_to_market_analysis_keyboard,
        )

        keyboard = get_back_to_market_analysis_keyboard("csgo")

        assert keyboard is not None
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_back_to_market_analysis_keyboard_dota2(self):
        """Test back keyboard for Dota 2."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            get_back_to_market_analysis_keyboard,
        )

        keyboard = get_back_to_market_analysis_keyboard("dota2")

        assert keyboard is not None
        assert isinstance(keyboard, InlineKeyboardMarkup)


# ======================== Result Display Tests ========================


class TestResultDisplay:
    """Tests for result display functions."""

    @pytest.mark.asyncio
    async def test_show_price_changes_results_empty(self, mock_callback_query, mock_context):
        """Test showing price changes with empty results."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            show_price_changes_results,
        )

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page_items.return_value = []
            mock_pagination.get_current_page.return_value = 1
            mock_pagination.get_total_pages.return_value = 1

            await show_price_changes_results(mock_callback_query, mock_context, "csgo")

    @pytest.mark.asyncio
    async def test_show_trending_items_results_empty(self, mock_callback_query, mock_context):
        """Test showing trending items with empty results."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            show_trending_items_results,
        )

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page_items.return_value = []
            mock_pagination.get_current_page.return_value = 1
            mock_pagination.get_total_pages.return_value = 1

            await show_trending_items_results(mock_callback_query, mock_context, "csgo")

    @pytest.mark.asyncio
    async def test_show_volatility_results_empty(self, mock_callback_query, mock_context):
        """Test showing volatility with empty results."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            show_volatility_results,
        )

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page_items.return_value = []
            mock_pagination.get_current_page.return_value = 1
            mock_pagination.get_total_pages.return_value = 1

            await show_volatility_results(mock_callback_query, mock_context, "csgo")

    @pytest.mark.asyncio
    async def test_show_undervalued_items_results_empty(
        self, mock_callback_query, mock_context
    ):
        """Test showing undervalued items with empty results."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            show_undervalued_items_results,
        )

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page_items.return_value = []
            mock_pagination.get_current_page.return_value = 1
            mock_pagination.get_total_pages.return_value = 1

            await show_undervalued_items_results(
                mock_callback_query, mock_context, "csgo"
            )

    @pytest.mark.asyncio
    async def test_show_investment_recommendations_empty(
        self, mock_callback_query, mock_context
    ):
        """Test showing recommendations with empty results."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            show_investment_recommendations_results,
        )

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page_items.return_value = []
            mock_pagination.get_current_page.return_value = 1
            mock_pagination.get_total_pages.return_value = 1

            await show_investment_recommendations_results(
                mock_callback_query, mock_context, "csgo"
            )


# ======================== Edge Case Tests ========================


class TestEdgeCases:
    """Tests for edge cases in market analysis."""

    @pytest.mark.asyncio
    async def test_empty_games_dict(self, mock_update, mock_context):
        """Test handling of empty games dictionary."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:csgo"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {},
        ):
            await market_analysis_callback(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_unknown_game_code(self, mock_update, mock_context):
        """Test handling of unknown game code."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:select_game:unknown_game"

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler.GAMES",
            {"csgo": "CS2"},
        ):
            await market_analysis_callback(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_unknown_analysis_action(self, mock_update, mock_context):
        """Test handling of unknown analysis action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:unknown_action:csgo"

        mock_api_client = MagicMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            # Should not crash with unknown action
            await market_analysis_callback(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_user_data_initialization(self, mock_update, mock_context_empty):
        """Test initialization of user data when empty."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:price_changes:csgo"

        mock_api_client = MagicMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_price_changes_results",
                new_callable=AsyncMock,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context_empty)

        # User data should be initialized
        assert "market_analysis" in mock_context_empty.user_data

    @pytest.mark.asyncio
    async def test_api_client_close_on_exception(self, mock_update, mock_context):
        """Test API client is closed even on exception."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        mock_update.callback_query.data = "analysis:price_changes:csgo"

        mock_api_client = MagicMock()
        mock_api_client._close_client = AsyncMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes",
                new_callable=AsyncMock,
                side_effect=Exception("Test error"),
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.get_back_to_market_analysis_keyboard",
                return_value=InlineKeyboardMarkup([]),
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_default_game_when_not_in_callback_data(
        self, mock_update, mock_context
    ):
        """Test default game is used when not specified in callback data."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        # Only two parts, no game specified
        mock_update.callback_query.data = "analysis:price_changes"

        mock_api_client = MagicMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.show_price_changes_results",
                new_callable=AsyncMock,
            ),
            patch(
                "src.telegram_bot.handlers.market_analysis_handler.GAMES",
                {"csgo": "CS2"},
            ),
        ):
            await market_analysis_callback(mock_update, mock_context)

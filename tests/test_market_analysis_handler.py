import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Add project root to path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)


class TestMarketAnalysisHandler:
    """Tests for the Market Analysis Handler module."""

    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        # Create mock for update and context
        self.update = MagicMock()
        self.context = MagicMock()

        # Setup message mock for update
        self.update.message = MagicMock()
        self.update.message.reply_text = AsyncMock()

        # Setup callback query mock
        self.update.callback_query = MagicMock()
        self.update.callback_query.data = "analysis:price_changes:csgo"
        self.update.callback_query.from_user.id = 12345
        self.update.callback_query.edit_message_text = AsyncMock()
        self.update.callback_query.answer = AsyncMock()

        # Setup context.user_data
        self.context.user_data = {
            "market_analysis": {
                "current_game": "csgo",
                "period": "24h",
                "min_price": 1.0,
                "max_price": 500.0,
            },
        }

    @pytest.mark.asyncio()
    @patch(
        "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env"
    )
    @patch("src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes")
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_market_analysis_callback_price_changes(
        self,
        mock_pagination,
        mock_analyze,
        mock_api_client,
    ):
        """Test market_analysis_callback with price_changes action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        # Setup mocks
        mock_api_client.return_value = AsyncMock()
        test_results = [
            {
                "market_hash_name": "Test Item",
                "current_price": 10.0,
                "old_price": 8.0,
                "change_amount": 2.0,
                "change_percent": 25.0,
            },
        ]
        mock_analyze.return_value = test_results
        # Mock pagination manager methods
        mock_pagination.get_page.return_value = (test_results, 0, 1)

        # Call the function
        await market_analysis_callback(self.update, self.context)

        # Verify API client was created
        mock_api_client.assert_called_once()

        # Verify analyze_price_changes was called
        mock_analyze.assert_called_once()

        # Verify pagination was used
        assert mock_pagination.set_items.called

        # Verify edit_message_text was called at least twice (loading + results)
        assert self.update.callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    @patch(
        "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env"
    )
    @patch("src.telegram_bot.handlers.market_analysis_handler.find_undervalued_items")
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_market_analysis_callback_undervalued(
        self,
        mock_pagination,
        mock_find,
        mock_api_client,
    ):
        """Test market_analysis_callback with undervalued action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        # Change callback data
        self.update.callback_query.data = "analysis:undervalued:csgo"

        # Setup mocks
        mock_api_client.return_value = AsyncMock()
        test_results = [
            {
                "title": "Test Item",
                "current_price": 10.0,
                "avg_price": 15.0,
                "discount": 33.3,
                "trend": "stable",
                "volume": 100,
            },
        ]
        mock_find.return_value = test_results
        # Mock pagination manager methods
        mock_pagination.get_page.return_value = (test_results, 0, 1)

        # Call the function
        await market_analysis_callback(self.update, self.context)

        # Verify API client was created
        mock_api_client.assert_called_once()

        # Verify find_undervalued_items was called
        mock_find.assert_called_once()

        # Verify pagination was used
        assert mock_pagination.set_items.called

        # Verify edit_message_text was called at least twice (loading + results)
        assert self.update.callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    @patch(
        "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env"
    )
    @patch(
        "src.telegram_bot.handlers.market_analysis_handler.get_investment_recommendations",
    )
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_market_analysis_callback_recommendations(
        self,
        mock_pagination,
        mock_recommend,
        mock_api_client,
    ):
        """Test market_analysis_callback with recommendations action."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        # Change callback data
        self.update.callback_query.data = "analysis:recommendations:csgo"

        # Setup mocks
        mock_api_client.return_value = AsyncMock()
        test_results = [
            {
                "title": "Test Item",
                "current_price": 10.0,
                "discount": 15.0,
                "liquidity": "high",
                "investment_score": 85.0,
                "reason": "Good investment",
            },
        ]
        mock_recommend.return_value = test_results
        # Mock pagination manager methods
        mock_pagination.get_page.return_value = (test_results, 0, 1)

        # Call the function
        await market_analysis_callback(self.update, self.context)

        # Verify API client was created
        mock_api_client.assert_called_once()

        # Verify get_investment_recommendations was called
        mock_recommend.assert_called_once()

        # Verify pagination was used
        assert mock_pagination.set_items.called

        # Verify edit_message_text was called at least twice (loading + results)
        assert self.update.callback_query.edit_message_text.call_count >= 2

    @pytest.mark.asyncio()
    @patch(
        "src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env"
    )
    @patch("src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes")
    async def test_market_analysis_callback_error(self, mock_analyze, mock_api_client):
        """Test market_analysis_callback with an error."""
        from src.telegram_bot.handlers.market_analysis_handler import (
            market_analysis_callback,
        )

        # Setup API client and make analyze raise an exception
        mock_api_client.return_value = AsyncMock()
        mock_analyze.side_effect = Exception("Test error")

        # Call the function
        await market_analysis_callback(self.update, self.context)

        # Verify edit_message_text was called with error message
        call_args = self.update.callback_query.edit_message_text.call_args[0][0]
        assert "ошибка" in call_args.lower()

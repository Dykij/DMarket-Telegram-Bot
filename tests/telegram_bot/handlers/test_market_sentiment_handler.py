"""Tests for market_sentiment_handler module.

This module tests the MarketSentimentHandler class for market
sentiment analysis via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery


class TestMarketSentimentHandler:
    """Tests for MarketSentimentHandler class."""

    @pytest.fixture
    def mock_sentiment_analyzer(self):
        """Create mock sentiment analyzer."""
        analyzer = MagicMock()
        analyzer.analyze_sentiment = AsyncMock(return_value={
            "sentiment": "bullish",
            "score": 0.75,
            "confidence": 0.85,
        })
        analyzer.get_market_mood = AsyncMock(return_value="optimistic")
        return analyzer

    @pytest.fixture
    def handler(self, mock_sentiment_analyzer):
        """Create MarketSentimentHandler instance."""
        from src.telegram_bot.handlers.market_sentiment_handler import MarketSentimentHandler
        return MarketSentimentHandler(sentiment_analyzer=mock_sentiment_analyzer)

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = MagicMock()
        context.user_data = {}
        context.bot_data = {}
        return context

    @pytest.mark.asyncio
    async def test_sentiment_command(self, handler, mock_update, mock_context):
        """Test /sentiment command."""
        await handler.sentiment_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_menu(self, handler, mock_update, mock_context):
        """Test showing sentiment menu."""
        await handler.show_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_market(self, handler, mock_update, mock_context, mock_sentiment_analyzer):
        """Test analyzing market sentiment."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_analyze"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.analyze_market(mock_update, mock_context)

        mock_sentiment_analyzer.analyze_sentiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_game_specific(self, handler, mock_update, mock_context, mock_sentiment_analyzer):
        """Test analyzing game-specific sentiment."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_game_csgo"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.analyze_game(mock_update, mock_context)

        mock_sentiment_analyzer.analyze_sentiment.assert_called()

    @pytest.mark.asyncio
    async def test_get_market_mood(self, handler, mock_update, mock_context, mock_sentiment_analyzer):
        """Test getting overall market mood."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_mood"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.get_market_mood(mock_update, mock_context)

        mock_sentiment_analyzer.get_market_mood.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_trends(self, handler, mock_update, mock_context, mock_sentiment_analyzer):
        """Test showing market trends."""
        mock_sentiment_analyzer.get_trends = AsyncMock(return_value=[
            {"item": "AK-47", "trend": "up", "change": 5.0},
            {"item": "M4A4", "trend": "down", "change": -3.0},
        ])

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_trends"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.show_trends(mock_update, mock_context)

        mock_sentiment_analyzer.get_trends.assert_called_once()

    @pytest.mark.asyncio
    async def test_sentiment_alert(self, handler, mock_update, mock_context):
        """Test setting sentiment alert."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_alert_setup"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.setup_alert(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio
    async def test_bullish_sentiment(self, handler, mock_update, mock_context, mock_sentiment_analyzer):
        """Test bullish sentiment analysis."""
        mock_sentiment_analyzer.analyze_sentiment.return_value = {
            "sentiment": "bullish",
            "score": 0.85,
            "confidence": 0.90,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_analyze"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.analyze_market(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        # Should mention bullish or positive sentiment

    @pytest.mark.asyncio
    async def test_bearish_sentiment(self, handler, mock_update, mock_context, mock_sentiment_analyzer):
        """Test bearish sentiment analysis."""
        mock_sentiment_analyzer.analyze_sentiment.return_value = {
            "sentiment": "bearish",
            "score": 0.25,
            "confidence": 0.80,
        }

        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = "sentiment_analyze"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        await handler.analyze_market(mock_update, mock_context)

        # Should handle bearish sentiment

    def test_get_handlers(self, handler):
        """Test getting handlers."""
        handlers = handler.get_handlers()
        assert len(handlers) > 0

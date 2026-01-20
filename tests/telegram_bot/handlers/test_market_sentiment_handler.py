"""Tests for market_sentiment_handler module."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User

class TestMarketSentimentCommands:
    @pytest.fixture
    def mock_update(self):
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        context = MagicMock()
        context.user_data = {}
        context.bot_data = {"market_analyzer": None}
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_show_smart_menu(self, mock_update, mock_context):
        from src.telegram_bot.handlers.market_sentiment_handler import show_smart_menu
        await show_smart_menu(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

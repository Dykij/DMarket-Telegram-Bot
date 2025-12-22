"""Unit tests for src/telegram_bot/handlers/portfolio_handler.py.

Tests for portfolio handler including:
- PortfolioHandler initialization
- Portfolio command handling
- Callback query handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPortfolioHandlerInit:
    """Tests for PortfolioHandler initialization."""

    def test_init_without_api(self):
        """Test initialization without API."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()

        assert handler._api is None
        assert handler._manager is not None
        assert handler._analyzer is not None

    def test_init_with_api(self):
        """Test initialization with API."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        mock_api = MagicMock()
        handler = PortfolioHandler(api=mock_api)

        assert handler._api is mock_api

    def test_set_api(self):
        """Test setting API after initialization."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()
        mock_api = MagicMock()

        handler.set_api(mock_api)

        assert handler._api is mock_api


class TestPortfolioHandlerCommands:
    """Tests for portfolio command handlers."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock Update object."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio()
    async def test_handle_portfolio_command(self, mock_update, mock_context):
        """Test /portfolio command handler."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()

        await handler.handle_portfolio_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_portfolio_command_no_message(self, mock_context):
        """Test handler when message is None."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()
        update = MagicMock()
        update.message = None

        # Should not raise
        await handler.handle_portfolio_command(update, mock_context)

    @pytest.mark.asyncio()
    async def test_handle_portfolio_command_no_user(self, mock_context):
        """Test handler when effective_user is None."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()
        update = MagicMock()
        update.message = MagicMock()
        update.effective_user = None

        # Should not raise
        await handler.handle_portfolio_command(update, mock_context)


class TestPortfolioHandlerCallbacks:
    """Tests for portfolio callback handlers."""

    @pytest.fixture()
    def mock_callback_update(self):
        """Create mock Update with callback query."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "portfolio:details"
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock Context object."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio()
    async def test_handle_callback_details(self, mock_callback_update, mock_context):
        """Test portfolio details callback."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()
        mock_callback_update.callback_query.data = "portfolio:details"

        await handler.handle_callback(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_callback_no_query(self, mock_context):
        """Test callback handler when query is None."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()
        update = MagicMock()
        update.callback_query = None

        # Should not raise
        await handler.handle_callback(update, mock_context)

    @pytest.mark.asyncio()
    async def test_handle_callback_no_user(self, mock_callback_update, mock_context):
        """Test callback handler when effective_user is None."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        handler = PortfolioHandler()
        mock_callback_update.effective_user = None

        # Should not raise
        await handler.handle_callback(mock_callback_update, mock_context)


class TestPortfolioConversationStates:
    """Tests for portfolio conversation states."""

    def test_conversation_states_defined(self):
        """Test conversation states are defined."""
        from src.telegram_bot.handlers.portfolio_handler import (
            WAITING_ITEM_ID,
            WAITING_PRICE,
        )

        assert WAITING_ITEM_ID == 1
        assert WAITING_PRICE == 2


class TestPortfolioHandlerIntegration:
    """Integration tests for portfolio handler."""

    @pytest.fixture()
    def handler_with_mock_api(self):
        """Create handler with mocked API."""
        from src.telegram_bot.handlers.portfolio_handler import PortfolioHandler

        mock_api = MagicMock()
        mock_api.get_inventory = AsyncMock(return_value=[])
        mock_api.get_user_balance = AsyncMock(return_value={"balance": 100.0})

        handler = PortfolioHandler(api=mock_api)
        return handler

    @pytest.mark.asyncio()
    async def test_portfolio_with_api(self, handler_with_mock_api):
        """Test portfolio command with API configured."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        context = MagicMock()
        context.user_data = {}

        await handler_with_mock_api.handle_portfolio_command(update, context)

        update.message.reply_text.assert_called_once()

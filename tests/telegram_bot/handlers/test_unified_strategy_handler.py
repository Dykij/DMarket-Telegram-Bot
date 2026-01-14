"""Tests for unified_strategy_handler module.

This module tests the UnifiedStrategyHandler class for managing
unified trading strategies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery

from src.telegram_bot.handlers.unified_strategy_handler import (
    UnifiedStrategyHandler,
    SELECTING_STRATEGY,
    SELECTING_PRESET,
    SCANNING,
    CB_STRATEGY,
    CB_PRESET,
    CB_SCAN,
    CB_BACK,
)


class TestUnifiedStrategyHandler:
    """Tests for UnifiedStrategyHandler class."""

    @pytest.fixture
    def mock_strategy_manager(self):
        """Create mock strategy manager."""
        manager = MagicMock()
        manager.scan = AsyncMock(return_value=[])
        manager.get_available_strategies = MagicMock(return_value=[])
        return manager

    @pytest.fixture
    def handler(self, mock_strategy_manager):
        """Create UnifiedStrategyHandler instance."""
        return UnifiedStrategyHandler(strategy_manager=mock_strategy_manager)

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
        context.bot_data = {
            "dmarket_api": MagicMock(),
            "waxpeer_api": MagicMock(),
        }
        return context

    def test_init(self, handler, mock_strategy_manager):
        """Test handler initialization."""
        assert handler._manager == mock_strategy_manager

    def test_init_without_manager(self):
        """Test handler initialization without manager."""
        handler = UnifiedStrategyHandler()
        assert handler._manager is None

    @pytest.mark.asyncio
    async def test_strategies_command(self, handler, mock_update, mock_context):
        """Test /strategies command."""
        await handler.strategies_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "страте" in str(call_args).lower() or "strategy" in str(call_args).lower()

    @pytest.mark.asyncio
    async def test_show_strategy_menu(self, handler, mock_update, mock_context):
        """Test showing strategy menu."""
        result = await handler.show_strategy_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert result == SELECTING_STRATEGY

    @pytest.mark.asyncio
    async def test_handle_strategy_selection(self, handler, mock_update, mock_context):
        """Test handling strategy selection."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = f"{CB_STRATEGY}intramarket"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        result = await handler.handle_strategy_selection(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        assert result == SELECTING_PRESET

    @pytest.mark.asyncio
    async def test_handle_preset_selection(self, handler, mock_update, mock_context):
        """Test handling preset selection."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = f"{CB_PRESET}standard"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        mock_context.user_data["selected_strategy"] = "intramarket"

        result = await handler.handle_preset_selection(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_all_command(self, handler, mock_update, mock_context, mock_strategy_manager):
        """Test /scan_all command."""
        mock_strategy_manager.scan.return_value = [
            {"name": "Item 1", "profit": 10.0},
            {"name": "Item 2", "profit": 15.0},
        ]

        await handler.scan_all_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_best_deals_command(self, handler, mock_update, mock_context, mock_strategy_manager):
        """Test /best_deals command."""
        mock_strategy_manager.find_best_deals = AsyncMock(return_value=[
            {"name": "Best Item 1", "profit": 25.0},
            {"name": "Best Item 2", "profit": 20.0},
        ])

        await handler.best_deals_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_start_scan(self, handler, mock_update, mock_context, mock_strategy_manager):
        """Test starting a scan."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = f"{CB_SCAN}start"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        mock_context.user_data["selected_strategy"] = "intramarket"
        mock_context.user_data["selected_preset"] = "standard"

        await handler.start_scan(mock_update, mock_context)

        mock_strategy_manager.scan.assert_called()

    @pytest.mark.asyncio
    async def test_back_to_strategies(self, handler, mock_update, mock_context):
        """Test going back to strategies menu."""
        mock_update.callback_query = MagicMock(spec=CallbackQuery)
        mock_update.callback_query.data = CB_BACK
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        result = await handler.back_to_strategies(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        assert result == SELECTING_STRATEGY

    def test_get_manager_creates_new(self, mock_context):
        """Test _get_manager creates new manager when needed."""
        handler = UnifiedStrategyHandler()

        with patch("src.telegram_bot.handlers.unified_strategy_handler.create_strategy_manager") as mock_create:
            mock_create.return_value = MagicMock()
            manager = handler._get_manager(mock_context)

            assert manager is not None

    def test_get_manager_returns_existing(self, handler, mock_context, mock_strategy_manager):
        """Test _get_manager returns existing manager."""
        manager = handler._get_manager(mock_context)
        assert manager == mock_strategy_manager

    def test_get_handlers(self, handler):
        """Test getting conversation handlers."""
        handlers = handler.get_handlers()

        assert len(handlers) > 0


class TestUnifiedStrategyConstants:
    """Tests for constants."""

    def test_state_values(self):
        """Test state values."""
        assert SELECTING_STRATEGY == 0
        assert SELECTING_PRESET == 1
        assert SCANNING == 2

    def test_callback_prefixes(self):
        """Test callback data prefixes."""
        assert CB_STRATEGY == "strategy_"
        assert CB_PRESET == "preset_"
        assert CB_SCAN == "scan_"
        assert CB_BACK == "back_to_strategies"

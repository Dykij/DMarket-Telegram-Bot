"""Tests for autopilot_handler module.

This module tests the autopilot command handlers for automated
trading management via Telegram.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ContextTypes


class TestAutopilotCommand:
    """Tests for autopilot_command handler."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock autopilot orchestrator."""
        orchestrator = MagicMock()
        orchestrator.start = AsyncMock()
        orchestrator.stop = AsyncMock()
        orchestrator.is_active = MagicMock(return_value=False)
        orchestrator.get_stats = MagicMock(return_value={
            "uptime_minutes": 0,
            "purchases": 0,
            "sales": 0,
            "net_profit_usd": 0.0,
            "roi_percent": 0.0,
            "opportunities_found": 0,
            "opportunities_skipped": 0,
            "balance_checks": 0,
            "low_balance_warnings": 0,
            "failed_purchases": 0,
            "failed_sales": 0,
            "total_spent_usd": 0.0,
            "total_earned_usd": 0.0,
        })
        orchestrator.config = MagicMock()
        orchestrator.config.games = ["csgo"]
        orchestrator.config.min_discount_percent = 3.0
        orchestrator.config.max_price_usd = 100.0
        orchestrator.config.auto_sell_markup_percent = 5.0
        orchestrator.config.min_balance_threshold_usd = 10.0
        orchestrator.buyer = MagicMock()
        orchestrator.buyer.config = MagicMock()
        orchestrator.buyer.config.enabled = True
        orchestrator.seller = MagicMock()
        orchestrator.seller.enabled = True
        return orchestrator

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
    def mock_context(self, mock_orchestrator):
        """Create mock Context with orchestrator."""
        context = MagicMock()
        context.user_data = {}
        context.bot_data = {"orchestrator": mock_orchestrator}
        context.args = []
        context.bot = MagicMock()
        return context

    @pytest.mark.asyncio
    async def test_autopilot_command_starts_successfully(self, mock_update, mock_context, mock_orchestrator):
        """Test /autopilot command starts autopilot."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_command

        await autopilot_command(mock_update, mock_context)

        # Should call orchestrator.start
        mock_orchestrator.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_autopilot_command_already_running(self, mock_update, mock_context, mock_orchestrator):
        """Test /autopilot command when already running."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_command

        mock_orchestrator.is_active.return_value = True

        await autopilot_command(mock_update, mock_context)

        # Should not start again
        mock_orchestrator.start.assert_not_called()
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_autopilot_command_no_orchestrator(self, mock_update):
        """Test /autopilot command when orchestrator not initialized."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_command

        context = MagicMock()
        context.bot_data = {}  # No orchestrator
        context.args = []

        await autopilot_command(mock_update, context)

        # Should show error message
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "не инициализирован" in call_args

    @pytest.mark.asyncio
    async def test_autopilot_command_custom_settings(self, mock_update, mock_context):
        """Test /autopilot custom shows settings menu."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_command

        mock_context.args = ["custom"]

        await autopilot_command(mock_update, mock_context)

        # Should show settings menu
        mock_update.message.reply_text.assert_called()


class TestAutopilotStopCommand:
    """Tests for autopilot_stop_command handler."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        orchestrator = MagicMock()
        orchestrator.is_active = MagicMock(return_value=True)
        orchestrator.stop = AsyncMock()
        return orchestrator

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self, mock_orchestrator):
        """Create mock Context."""
        context = MagicMock()
        context.bot_data = {"orchestrator": mock_orchestrator}
        return context

    @pytest.mark.asyncio
    async def test_stop_autopilot(self, mock_update, mock_context, mock_orchestrator):
        """Test /autopilot_stop stops autopilot."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_stop_command

        await autopilot_stop_command(mock_update, mock_context)

        mock_orchestrator.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_autopilot_not_running(self, mock_update, mock_context, mock_orchestrator):
        """Test /autopilot_stop when not running."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_stop_command

        mock_orchestrator.is_active.return_value = False

        await autopilot_stop_command(mock_update, mock_context)

        mock_orchestrator.stop.assert_not_called()


class TestAutopilotStatusCommand:
    """Tests for autopilot_status_command handler."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        orchestrator = MagicMock()
        orchestrator.is_active = MagicMock(return_value=True)
        orchestrator.get_stats = MagicMock(return_value={
            "uptime_minutes": 30,
            "purchases": 5,
            "sales": 3,
            "net_profit_usd": 15.50,
        })
        orchestrator.buyer = MagicMock()
        orchestrator.buyer.config = MagicMock()
        orchestrator.buyer.config.enabled = True
        orchestrator.seller = MagicMock()
        orchestrator.seller.enabled = True
        return orchestrator

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self, mock_orchestrator):
        """Create mock Context."""
        context = MagicMock()
        context.bot_data = {"orchestrator": mock_orchestrator}
        return context

    @pytest.mark.asyncio
    async def test_status_when_active(self, mock_update, mock_context, mock_orchestrator):
        """Test /autopilot_status shows status when active."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_status_command

        await autopilot_status_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert "активен" in call_args[0][0].lower() or "активен" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_status_when_stopped(self, mock_update, mock_context, mock_orchestrator):
        """Test /autopilot_status shows stopped status."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_status_command

        mock_orchestrator.is_active.return_value = False

        await autopilot_status_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert "остановлен" in call_args[0][0].lower()


class TestAutopilotStatsCommand:
    """Tests for autopilot_stats_command handler."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator with stats."""
        orchestrator = MagicMock()
        orchestrator.get_stats = MagicMock(return_value={
            "uptime_minutes": 120,
            "purchases": 25,
            "failed_purchases": 5,
            "sales": 20,
            "failed_sales": 2,
            "net_profit_usd": 150.0,
            "roi_percent": 15.5,
            "total_spent_usd": 1000.0,
            "total_earned_usd": 1150.0,
            "opportunities_found": 100,
            "opportunities_skipped": 70,
            "balance_checks": 50,
            "low_balance_warnings": 3,
        })
        return orchestrator

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self, mock_orchestrator):
        """Create mock Context."""
        context = MagicMock()
        context.bot_data = {"orchestrator": mock_orchestrator}
        return context

    @pytest.mark.asyncio
    async def test_stats_display(self, mock_update, mock_context):
        """Test /autopilot_stats shows detailed statistics."""
        from src.telegram_bot.handlers.autopilot_handler import autopilot_stats_command

        await autopilot_stats_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "статистика" in call_args.lower()


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self):
        """Test that __all__ is defined with handlers."""
        from src.telegram_bot.handlers import autopilot_handler

        assert hasattr(autopilot_handler, "__all__")
        assert "autopilot_command" in autopilot_handler.__all__
        assert "autopilot_stop_command" in autopilot_handler.__all__
        assert "autopilot_status_command" in autopilot_handler.__all__
        assert "autopilot_stats_command" in autopilot_handler.__all__

    def test_can_import_handlers(self):
        """Test that handlers can be imported."""
        from src.telegram_bot.handlers.autopilot_handler import (
            autopilot_command,
            autopilot_stop_command,
            autopilot_status_command,
            autopilot_stats_command,
        )

        assert callable(autopilot_command)
        assert callable(autopilot_stop_command)
        assert callable(autopilot_status_command)
        assert callable(autopilot_stats_command)

"""
Comprehensive tests for dashboard_handler.py module.

Tests cover:
- ScannerDashboard class
- Dashboard keyboard generation
- Stats formatting
- Scanner control keyboard
- Dashboard handlers
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.message.reply_photo = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock context object."""
    context = MagicMock()
    return context


# ==============================================================================
# ScannerDashboard Tests
# ==============================================================================


class TestScannerDashboard:
    """Tests for ScannerDashboard class."""

    def test_dashboard_init(self):
        """Test dashboard initialization."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        
        assert dashboard.active_scans == {}
        assert dashboard.scan_history == []
        assert dashboard.max_history == 50

    def test_add_scan_result(self):
        """Test adding scan result to history."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        scan_data = {"level": "standard", "opportunities": []}
        
        dashboard.add_scan_result(123, scan_data)
        
        assert len(dashboard.scan_history) == 1
        assert dashboard.scan_history[0]["user_id"] == 123
        assert dashboard.scan_history[0]["data"] == scan_data

    def test_add_scan_result_inserts_at_beginning(self):
        """Test that new scans are inserted at the beginning."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        
        dashboard.add_scan_result(123, {"level": "first"})
        dashboard.add_scan_result(123, {"level": "second"})
        
        assert dashboard.scan_history[0]["data"]["level"] == "second"
        assert dashboard.scan_history[1]["data"]["level"] == "first"

    def test_add_scan_result_respects_max_history(self):
        """Test that history is limited to max_history."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        dashboard.max_history = 5
        
        for i in range(10):
            dashboard.add_scan_result(123, {"index": i})
        
        assert len(dashboard.scan_history) == 5

    def test_get_user_stats_empty_history(self):
        """Test getting stats with no history."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        
        stats = dashboard.get_user_stats(123)
        
        assert stats["total_scans"] == 0
        assert stats["total_opportunities"] == 0
        assert stats["avg_profit"] == 0.0
        assert stats["max_profit"] == 0.0
        assert stats["last_scan_time"] is None

    def test_get_user_stats_with_history(self):
        """Test getting stats with scan history."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(123, {
            "opportunities": [
                {"profit": 5.0},
                {"profit": 10.0},
            ]
        })
        dashboard.add_scan_result(123, {
            "opportunities": [
                {"profit": 3.0},
            ]
        })
        
        stats = dashboard.get_user_stats(123)
        
        assert stats["total_scans"] == 2
        assert stats["total_opportunities"] == 3
        assert stats["avg_profit"] == 6.0  # (5+10+3)/3
        assert stats["max_profit"] == 10.0
        assert stats["last_scan_time"] is not None

    def test_get_user_stats_filters_by_user(self):
        """Test that stats are filtered by user."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(123, {"opportunities": [{"profit": 5.0}]})
        dashboard.add_scan_result(456, {"opportunities": [{"profit": 10.0}]})
        
        stats_123 = dashboard.get_user_stats(123)
        stats_456 = dashboard.get_user_stats(456)
        
        assert stats_123["total_scans"] == 1
        assert stats_456["total_scans"] == 1

    def test_mark_scan_active(self):
        """Test marking a scan as active."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        
        dashboard.mark_scan_active(123, "scan_1", "standard", "csgo")
        
        assert 123 in dashboard.active_scans
        assert dashboard.active_scans[123]["scan_id"] == "scan_1"
        assert dashboard.active_scans[123]["level"] == "standard"
        assert dashboard.active_scans[123]["game"] == "csgo"
        assert dashboard.active_scans[123]["status"] == "running"

    def test_mark_scan_complete(self):
        """Test marking a scan as complete."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        dashboard.mark_scan_active(123, "scan_1", "standard", "csgo")
        
        dashboard.mark_scan_complete(123)
        
        assert dashboard.active_scans[123]["status"] == "completed"
        assert "completed_at" in dashboard.active_scans[123]

    def test_mark_scan_complete_nonexistent(self):
        """Test marking nonexistent scan as complete."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        
        # Should not raise error
        dashboard.mark_scan_complete(999)

    def test_get_active_scan(self):
        """Test getting active scan for user."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        dashboard.mark_scan_active(123, "scan_1", "standard", "csgo")
        
        scan = dashboard.get_active_scan(123)
        
        assert scan is not None
        assert scan["scan_id"] == "scan_1"

    def test_get_active_scan_returns_none(self):
        """Test getting active scan when none exists."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        
        dashboard = ScannerDashboard()
        
        scan = dashboard.get_active_scan(123)
        
        assert scan is None


# ==============================================================================
# Keyboard Generation Tests
# ==============================================================================


class TestKeyboardGeneration:
    """Tests for keyboard generation functions."""

    def test_get_dashboard_keyboard(self):
        """Test creating dashboard keyboard."""
        from src.telegram_bot.handlers.dashboard_handler import get_dashboard_keyboard
        
        keyboard = get_dashboard_keyboard()
        
        assert keyboard is not None
        assert hasattr(keyboard, "inline_keyboard")

    def test_get_scanner_control_keyboard_no_level(self):
        """Test scanner control keyboard without level."""
        from src.telegram_bot.handlers.dashboard_handler import (
            get_scanner_control_keyboard,
        )
        
        keyboard = get_scanner_control_keyboard()
        
        assert keyboard is not None
        # Should have level selection buttons

    def test_get_scanner_control_keyboard_with_level(self):
        """Test scanner control keyboard with level."""
        from src.telegram_bot.handlers.dashboard_handler import (
            get_scanner_control_keyboard,
        )
        
        keyboard = get_scanner_control_keyboard("standard")
        
        assert keyboard is not None
        # Should have action buttons for the level


# ==============================================================================
# Stats Formatting Tests
# ==============================================================================


class TestStatsFormatting:
    """Tests for stats formatting functions."""

    def test_format_stats_message_empty(self):
        """Test formatting empty stats."""
        from src.telegram_bot.handlers.dashboard_handler import format_stats_message
        
        stats = {
            "total_scans": 0,
            "total_opportunities": 0,
            "avg_profit": 0.0,
            "max_profit": 0.0,
            "last_scan_time": None,
        }
        
        message = format_stats_message(stats)
        
        assert "0" in message
        assert "Никогда" in message

    def test_format_stats_message_with_data(self):
        """Test formatting stats with data."""
        from src.telegram_bot.handlers.dashboard_handler import format_stats_message
        
        stats = {
            "total_scans": 10,
            "total_opportunities": 25,
            "avg_profit": 5.50,
            "max_profit": 15.00,
            "last_scan_time": datetime.now(),
        }
        
        message = format_stats_message(stats)
        
        assert "10" in message
        assert "25" in message
        assert "$5.50" in message
        assert "$15.00" in message

    def test_format_stats_message_recent_scan(self):
        """Test formatting with recent scan."""
        from src.telegram_bot.handlers.dashboard_handler import format_stats_message
        
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 1.0,
            "max_profit": 1.0,
            "last_scan_time": datetime.now() - timedelta(seconds=30),
        }
        
        message = format_stats_message(stats)
        
        assert "Только что" in message

    def test_format_stats_message_minutes_ago(self):
        """Test formatting with scan minutes ago."""
        from src.telegram_bot.handlers.dashboard_handler import format_stats_message
        
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 1.0,
            "max_profit": 1.0,
            "last_scan_time": datetime.now() - timedelta(minutes=30),
        }
        
        message = format_stats_message(stats)
        
        assert "мин. назад" in message

    def test_format_stats_message_hours_ago(self):
        """Test formatting with scan hours ago."""
        from src.telegram_bot.handlers.dashboard_handler import format_stats_message
        
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 1.0,
            "max_profit": 1.0,
            "last_scan_time": datetime.now() - timedelta(hours=5),
        }
        
        message = format_stats_message(stats)
        
        assert "ч. назад" in message

    def test_format_stats_message_days_ago(self):
        """Test formatting with scan days ago."""
        from src.telegram_bot.handlers.dashboard_handler import format_stats_message
        
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 1.0,
            "max_profit": 1.0,
            "last_scan_time": datetime.now() - timedelta(days=3),
        }
        
        message = format_stats_message(stats)
        
        assert "дн. назад" in message


# ==============================================================================
# Dashboard Handler Tests
# ==============================================================================


class TestShowDashboard:
    """Tests for show_dashboard handler."""

    @pytest.mark.asyncio
    async def test_show_dashboard_from_message(self, mock_update, mock_context):
        """Test showing dashboard from message."""
        from src.telegram_bot.handlers.dashboard_handler import show_dashboard
        
        mock_update.callback_query = None
        
        await show_dashboard(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_dashboard_from_callback(self, mock_update, mock_context):
        """Test showing dashboard from callback."""
        from src.telegram_bot.handlers.dashboard_handler import show_dashboard
        
        await show_dashboard(mock_update, mock_context)
        
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_dashboard_without_user(self, mock_context):
        """Test showing dashboard without effective user."""
        from src.telegram_bot.handlers.dashboard_handler import show_dashboard
        
        update = MagicMock()
        update.effective_user = None
        update.callback_query = None
        update.message = MagicMock()
        
        await show_dashboard(update, mock_context)


class TestShowStats:
    """Tests for show_stats handler."""

    @pytest.mark.asyncio
    async def test_show_stats(self, mock_update, mock_context):
        """Test showing stats."""
        from src.telegram_bot.handlers.dashboard_handler import show_stats
        
        await show_stats(mock_update, mock_context)
        
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_stats_without_query(self, mock_context):
        """Test showing stats without callback query."""
        from src.telegram_bot.handlers.dashboard_handler import show_stats
        
        update = MagicMock()
        update.callback_query = None
        
        await show_stats(update, mock_context)


class TestShowScannerMenu:
    """Tests for show_scanner_menu handler."""

    @pytest.mark.asyncio
    async def test_show_scanner_menu(self, mock_update, mock_context):
        """Test showing scanner menu."""
        from src.telegram_bot.handlers.dashboard_handler import show_scanner_menu
        
        await show_scanner_menu(mock_update, mock_context)
        
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()


class TestShowActiveScans:
    """Tests for show_active_scans handler."""

    @pytest.mark.asyncio
    async def test_show_active_scans_empty(self, mock_update, mock_context):
        """Test showing active scans when none exist."""
        from src.telegram_bot.handlers.dashboard_handler import show_active_scans
        
        await show_active_scans(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args[0][0]
        assert "Нет активных" in call_args


class TestShowHistory:
    """Tests for show_history handler."""

    @pytest.mark.asyncio
    async def test_show_history_empty(self, mock_update, mock_context):
        """Test showing history when empty."""
        from src.telegram_bot.handlers.dashboard_handler import show_history
        
        await show_history(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args[0][0]
        assert "пуста" in call_args


# ==============================================================================
# Register Handlers Tests
# ==============================================================================


class TestRegisterDashboardHandlers:
    """Tests for register_dashboard_handlers function."""

    def test_register_dashboard_handlers(self):
        """Test registering dashboard handlers."""
        from src.telegram_bot.handlers.dashboard_handler import (
            register_dashboard_handlers,
        )
        
        app = MagicMock()
        app.add_handler = MagicMock()
        
        register_dashboard_handlers(app)
        
        # Should add multiple handlers
        assert app.add_handler.call_count >= 1


# ==============================================================================
# Module Constants Tests
# ==============================================================================


class TestModuleConstants:
    """Tests for module constants."""

    def test_constants_are_strings(self):
        """Test that callback constants are strings."""
        from src.telegram_bot.handlers.dashboard_handler import (
            DASHBOARD_ACTION,
            DASHBOARD_ACTIVE_SCANS,
            DASHBOARD_CHARTS,
            DASHBOARD_HISTORY,
            DASHBOARD_REFRESH,
            DASHBOARD_SCANNER,
            DASHBOARD_STATS,
        )
        
        assert isinstance(DASHBOARD_ACTION, str)
        assert isinstance(DASHBOARD_STATS, str)
        assert isinstance(DASHBOARD_SCANNER, str)
        assert isinstance(DASHBOARD_ACTIVE_SCANS, str)
        assert isinstance(DASHBOARD_HISTORY, str)
        assert isinstance(DASHBOARD_REFRESH, str)
        assert isinstance(DASHBOARD_CHARTS, str)

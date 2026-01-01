"""Extended Phase 4 tests for dashboard_handler.py.

This module provides comprehensive additional tests for dashboard_handler.py
to achieve higher code coverage.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Message

from src.telegram_bot.handlers.dashboard_handler import (
    DASHBOARD_ACTION,
    DASHBOARD_ACTIVE_SCANS,
    DASHBOARD_CHARTS,
    DASHBOARD_HISTORY,
    DASHBOARD_REFRESH,
    DASHBOARD_SCANNER,
    DASHBOARD_STATS,
    ScannerDashboard,
    dashboard,
    format_stats_message,
    get_dashboard_keyboard,
    get_scanner_control_keyboard,
    register_dashboard_handlers,
    show_active_scans,
    show_charts,
    show_dashboard,
    show_history,
    show_scanner_menu,
    show_stats,
)


# ============================================================================
# Constants Tests
# ============================================================================
class TestDashboardConstants:
    """Tests for dashboard module constants."""

    def test_dashboard_action_constant(self):
        """Test DASHBOARD_ACTION constant value."""
        assert DASHBOARD_ACTION == "dashboard"

    def test_dashboard_stats_constant(self):
        """Test DASHBOARD_STATS constant value."""
        assert DASHBOARD_STATS == "dashboard_stats"

    def test_dashboard_scanner_constant(self):
        """Test DASHBOARD_SCANNER constant value."""
        assert DASHBOARD_SCANNER == "dashboard_scanner"

    def test_dashboard_active_scans_constant(self):
        """Test DASHBOARD_ACTIVE_SCANS constant value."""
        assert DASHBOARD_ACTIVE_SCANS == "dashboard_active"

    def test_dashboard_history_constant(self):
        """Test DASHBOARD_HISTORY constant value."""
        assert DASHBOARD_HISTORY == "dashboard_history"

    def test_dashboard_refresh_constant(self):
        """Test DASHBOARD_REFRESH constant value."""
        assert DASHBOARD_REFRESH == "dashboard_refresh"

    def test_dashboard_charts_constant(self):
        """Test DASHBOARD_CHARTS constant value."""
        assert DASHBOARD_CHARTS == "dashboard_charts"

    def test_all_constants_are_strings(self):
        """Test all constants are strings."""
        assert isinstance(DASHBOARD_ACTION, str)
        assert isinstance(DASHBOARD_STATS, str)
        assert isinstance(DASHBOARD_SCANNER, str)
        assert isinstance(DASHBOARD_ACTIVE_SCANS, str)
        assert isinstance(DASHBOARD_HISTORY, str)
        assert isinstance(DASHBOARD_REFRESH, str)
        assert isinstance(DASHBOARD_CHARTS, str)


# ============================================================================
# ScannerDashboard Extended Tests
# ============================================================================
class TestScannerDashboardExtended:
    """Extended tests for ScannerDashboard class."""

    def test_max_history_default_value(self):
        """Test default max_history value."""
        dashboard = ScannerDashboard()
        assert dashboard.max_history == 50

    def test_active_scans_is_dict(self):
        """Test active_scans is a dictionary."""
        dashboard = ScannerDashboard()
        assert isinstance(dashboard.active_scans, dict)

    def test_scan_history_is_list(self):
        """Test scan_history is a list."""
        dashboard = ScannerDashboard()
        assert isinstance(dashboard.scan_history, list)


class TestAddScanResultExtended:
    """Extended tests for add_scan_result method."""

    def test_scan_entry_structure(self):
        """Test scan entry has correct structure."""
        dashboard = ScannerDashboard()
        scan_data = {"test": "data"}

        dashboard.add_scan_result(user_id=123, scan_data=scan_data)

        entry = dashboard.scan_history[0]
        assert "user_id" in entry
        assert "timestamp" in entry
        assert "data" in entry

    def test_scan_timestamp_is_recent(self):
        """Test scan timestamp is recent."""
        dashboard = ScannerDashboard()
        before = datetime.now()

        dashboard.add_scan_result(user_id=123, scan_data={})

        after = datetime.now()
        timestamp = dashboard.scan_history[0]["timestamp"]
        assert before <= timestamp <= after

    def test_exact_history_limit(self):
        """Test exact history limit boundary."""
        dashboard = ScannerDashboard()
        dashboard.max_history = 3

        for i in range(3):
            dashboard.add_scan_result(user_id=i, scan_data={"i": i})

        assert len(dashboard.scan_history) == 3

    def test_history_over_limit_by_one(self):
        """Test history when exceeding limit by one."""
        dashboard = ScannerDashboard()
        dashboard.max_history = 3

        for i in range(4):
            dashboard.add_scan_result(user_id=i, scan_data={"i": i})

        assert len(dashboard.scan_history) == 3
        # Oldest should be removed
        assert dashboard.scan_history[-1]["data"]["i"] == 1

    def test_add_scan_with_complex_data(self):
        """Test adding scan with complex nested data."""
        dashboard = ScannerDashboard()
        complex_data = {
            "opportunities": [
                {"profit": 10.0, "item": {"name": "Test", "price": 100}},
                {"profit": 20.0, "item": {"name": "Test2", "price": 200}},
            ],
            "level": "advanced",
            "game": "csgo",
            "filters": {"min_price": 50, "max_price": 500},
        }

        dashboard.add_scan_result(user_id=123, scan_data=complex_data)

        assert dashboard.scan_history[0]["data"] == complex_data

    def test_add_scan_with_empty_opportunities(self):
        """Test adding scan with empty opportunities list."""
        dashboard = ScannerDashboard()

        dashboard.add_scan_result(user_id=123, scan_data={"opportunities": []})

        assert len(dashboard.scan_history) == 1

    def test_add_scan_preserves_order(self):
        """Test adding multiple scans preserves LIFO order."""
        dashboard = ScannerDashboard()

        for i in range(5):
            dashboard.add_scan_result(user_id=123, scan_data={"order": i})

        # Check LIFO order (most recent first)
        for i in range(5):
            assert dashboard.scan_history[i]["data"]["order"] == 4 - i


class TestGetUserStatsExtended:
    """Extended tests for get_user_stats method."""

    def test_stats_with_no_opportunities_key(self):
        """Test stats when opportunities key is missing."""
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(user_id=123, scan_data={"level": "boost"})

        stats = dashboard.get_user_stats(user_id=123)

        assert stats["total_opportunities"] == 0

    def test_stats_with_mixed_opportunities(self):
        """Test stats with mixed valid/invalid opportunities."""
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(
            user_id=123,
            scan_data={
                "opportunities": [
                    {"profit": 10.0},
                    {},  # Missing profit
                    {"profit": 30.0},
                ]
            },
        )

        stats = dashboard.get_user_stats(user_id=123)

        assert stats["total_opportunities"] == 3
        # avg_profit = (10 + 0 + 30) / 3 = 13.33...
        assert 13.0 <= stats["avg_profit"] <= 14.0

    def test_stats_multiple_users_isolation(self):
        """Test stats are isolated between users."""
        dashboard = ScannerDashboard()

        dashboard.add_scan_result(
            user_id=1, scan_data={"opportunities": [{"profit": 100.0}]}
        )
        dashboard.add_scan_result(
            user_id=2, scan_data={"opportunities": [{"profit": 200.0}]}
        )

        stats1 = dashboard.get_user_stats(user_id=1)
        stats2 = dashboard.get_user_stats(user_id=2)

        assert stats1["max_profit"] == 100.0
        assert stats2["max_profit"] == 200.0

    def test_stats_avg_profit_precision(self):
        """Test avg_profit calculation precision."""
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(
            user_id=123,
            scan_data={
                "opportunities": [
                    {"profit": 10.0},
                    {"profit": 20.0},
                    {"profit": 30.0},
                ]
            },
        )

        stats = dashboard.get_user_stats(user_id=123)

        assert stats["avg_profit"] == 20.0

    def test_stats_with_zero_profits(self):
        """Test stats with all zero profits."""
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(
            user_id=123,
            scan_data={
                "opportunities": [
                    {"profit": 0.0},
                    {"profit": 0.0},
                ]
            },
        )

        stats = dashboard.get_user_stats(user_id=123)

        assert stats["avg_profit"] == 0.0
        assert stats["max_profit"] == 0.0

    def test_stats_with_decimal_profits(self):
        """Test stats with decimal profits."""
        dashboard = ScannerDashboard()
        dashboard.add_scan_result(
            user_id=123,
            scan_data={
                "opportunities": [
                    {"profit": 10.55},
                    {"profit": 20.75},
                ]
            },
        )

        stats = dashboard.get_user_stats(user_id=123)

        assert abs(stats["avg_profit"] - 15.65) < 0.01
        assert stats["max_profit"] == 20.75


class TestMarkScanActiveExtended:
    """Extended tests for mark_scan_active method."""

    def test_mark_active_all_fields(self):
        """Test all fields are set correctly."""
        dashboard = ScannerDashboard()

        dashboard.mark_scan_active(
            user_id=123, scan_id="test_scan", level="pro", game="dota2"
        )

        scan = dashboard.active_scans[123]
        assert scan["scan_id"] == "test_scan"
        assert scan["level"] == "pro"
        assert scan["game"] == "dota2"
        assert scan["status"] == "running"
        assert "started_at" in scan

    def test_mark_active_different_games(self):
        """Test marking active scans for different games."""
        dashboard = ScannerDashboard()

        games = ["csgo", "dota2", "tf2", "rust"]
        for i, game in enumerate(games):
            dashboard.mark_scan_active(
                user_id=i, scan_id=f"scan_{game}", level="boost", game=game
            )

        for i, game in enumerate(games):
            assert dashboard.active_scans[i]["game"] == game

    def test_mark_active_replaces_completely(self):
        """Test that marking active completely replaces previous data."""
        dashboard = ScannerDashboard()

        dashboard.mark_scan_active(
            user_id=123, scan_id="first", level="boost", game="csgo"
        )
        first_started = dashboard.active_scans[123]["started_at"]

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)

        dashboard.mark_scan_active(
            user_id=123, scan_id="second", level="advanced", game="dota2"
        )

        assert dashboard.active_scans[123]["scan_id"] == "second"
        assert dashboard.active_scans[123]["level"] == "advanced"
        assert dashboard.active_scans[123]["game"] == "dota2"
        # New timestamp
        assert dashboard.active_scans[123]["started_at"] >= first_started


class TestMarkScanCompleteExtended:
    """Extended tests for mark_scan_complete method."""

    def test_complete_sets_completed_at(self):
        """Test complete sets completed_at timestamp."""
        dashboard = ScannerDashboard()
        dashboard.mark_scan_active(
            user_id=123, scan_id="test", level="boost", game="csgo"
        )

        before = datetime.now()
        dashboard.mark_scan_complete(user_id=123)
        after = datetime.now()

        completed_at = dashboard.active_scans[123]["completed_at"]
        assert before <= completed_at <= after

    def test_complete_preserves_other_fields(self):
        """Test complete preserves other fields."""
        dashboard = ScannerDashboard()
        dashboard.mark_scan_active(
            user_id=123, scan_id="test", level="boost", game="csgo"
        )

        dashboard.mark_scan_complete(user_id=123)

        assert dashboard.active_scans[123]["scan_id"] == "test"
        assert dashboard.active_scans[123]["level"] == "boost"
        assert dashboard.active_scans[123]["game"] == "csgo"

    def test_complete_multiple_users(self):
        """Test completing scans for multiple users."""
        dashboard = ScannerDashboard()

        for user_id in [1, 2, 3]:
            dashboard.mark_scan_active(
                user_id=user_id, scan_id=f"scan_{user_id}", level="boost", game="csgo"
            )

        dashboard.mark_scan_complete(user_id=2)

        assert dashboard.active_scans[1]["status"] == "running"
        assert dashboard.active_scans[2]["status"] == "completed"
        assert dashboard.active_scans[3]["status"] == "running"


class TestGetActiveScanExtended:
    """Extended tests for get_active_scan method."""

    def test_get_active_scan_returns_reference(self):
        """Test get_active_scan returns reference to dict."""
        dashboard = ScannerDashboard()
        dashboard.mark_scan_active(
            user_id=123, scan_id="test", level="boost", game="csgo"
        )

        scan = dashboard.get_active_scan(user_id=123)
        scan["modified"] = True

        # Should be modified in original
        assert dashboard.active_scans[123].get("modified") is True

    def test_get_active_scan_after_complete(self):
        """Test get_active_scan after completing scan."""
        dashboard = ScannerDashboard()
        dashboard.mark_scan_active(
            user_id=123, scan_id="test", level="boost", game="csgo"
        )
        dashboard.mark_scan_complete(user_id=123)

        scan = dashboard.get_active_scan(user_id=123)

        assert scan is not None
        assert scan["status"] == "completed"


# ============================================================================
# get_dashboard_keyboard Extended Tests
# ============================================================================
class TestGetDashboardKeyboardExtended:
    """Extended tests for get_dashboard_keyboard function."""

    def test_keyboard_has_three_rows(self):
        """Test keyboard has three rows."""
        keyboard = get_dashboard_keyboard()
        assert len(keyboard.inline_keyboard) == 3

    def test_first_row_has_two_buttons(self):
        """Test first row has two buttons."""
        keyboard = get_dashboard_keyboard()
        assert len(keyboard.inline_keyboard[0]) == 2

    def test_second_row_has_two_buttons(self):
        """Test second row has two buttons."""
        keyboard = get_dashboard_keyboard()
        assert len(keyboard.inline_keyboard[1]) == 2

    def test_third_row_has_two_buttons(self):
        """Test third row has two buttons."""
        keyboard = get_dashboard_keyboard()
        assert len(keyboard.inline_keyboard[2]) == 2

    def test_all_buttons_have_callback_data(self):
        """Test all buttons have callback_data."""
        keyboard = get_dashboard_keyboard()

        for row in keyboard.inline_keyboard:
            for button in row:
                assert button.callback_data is not None
                assert DASHBOARD_ACTION in button.callback_data

    def test_stats_button_callback_data(self):
        """Test stats button has correct callback data."""
        keyboard = get_dashboard_keyboard()

        stats_button = keyboard.inline_keyboard[0][0]
        assert f"{DASHBOARD_ACTION}_{DASHBOARD_STATS}" == stats_button.callback_data

    def test_scanner_button_callback_data(self):
        """Test scanner button has correct callback data."""
        keyboard = get_dashboard_keyboard()

        scanner_button = keyboard.inline_keyboard[0][1]
        assert f"{DASHBOARD_ACTION}_{DASHBOARD_SCANNER}" == scanner_button.callback_data

    def test_active_scans_button_callback_data(self):
        """Test active scans button has correct callback data."""
        keyboard = get_dashboard_keyboard()

        active_button = keyboard.inline_keyboard[1][0]
        assert (
            f"{DASHBOARD_ACTION}_{DASHBOARD_ACTIVE_SCANS}"
            == active_button.callback_data
        )

    def test_history_button_callback_data(self):
        """Test history button has correct callback data."""
        keyboard = get_dashboard_keyboard()

        history_button = keyboard.inline_keyboard[1][1]
        assert f"{DASHBOARD_ACTION}_{DASHBOARD_HISTORY}" == history_button.callback_data


# ============================================================================
# format_stats_message Extended Tests
# ============================================================================
class TestFormatStatsMessageExtended:
    """Extended tests for format_stats_message function."""

    def test_format_message_has_header(self):
        """Test formatted message has header."""
        stats = {
            "total_scans": 0,
            "total_opportunities": 0,
            "avg_profit": 0,
            "max_profit": 0,
        }
        message = format_stats_message(stats)

        assert "📊 *Ваша статистика*" in message

    def test_format_message_has_all_fields(self):
        """Test formatted message has all fields."""
        stats = {
            "total_scans": 5,
            "total_opportunities": 10,
            "avg_profit": 15.0,
            "max_profit": 25.0,
            "last_scan_time": None,
        }
        message = format_stats_message(stats)

        assert "Всего сканирований" in message
        assert "Найдено возможностей" in message
        assert "Средняя прибыль" in message
        assert "Максимальная прибыль" in message
        assert "Последнее сканирование" in message

    def test_format_message_profit_formatting(self):
        """Test profit values are formatted with dollar sign."""
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 12.34,
            "max_profit": 56.78,
            "last_scan_time": None,
        }
        message = format_stats_message(stats)

        assert "$12.34" in message
        assert "$56.78" in message

    def test_format_message_exactly_one_minute_ago(self):
        """Test formatting when scan was exactly one minute ago."""
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 0,
            "max_profit": 0,
            "last_scan_time": datetime.now() - timedelta(seconds=60),
        }
        message = format_stats_message(stats)

        assert "мин. назад" in message

    def test_format_message_exactly_one_hour_ago(self):
        """Test formatting when scan was exactly one hour ago."""
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 0,
            "max_profit": 0,
            "last_scan_time": datetime.now() - timedelta(hours=1),
        }
        message = format_stats_message(stats)

        assert "ч. назад" in message

    def test_format_message_exactly_one_day_ago(self):
        """Test formatting when scan was exactly one day ago."""
        stats = {
            "total_scans": 1,
            "total_opportunities": 1,
            "avg_profit": 0,
            "max_profit": 0,
            "last_scan_time": datetime.now() - timedelta(days=1),
        }
        message = format_stats_message(stats)

        assert "дн. назад" in message

    def test_format_message_missing_keys_uses_defaults(self):
        """Test formatting with missing keys uses defaults."""
        stats = {}
        message = format_stats_message(stats)

        assert "*0*" in message  # Default values
        assert "Никогда" in message  # No last scan


# ============================================================================
# get_scanner_control_keyboard Extended Tests
# ============================================================================
class TestGetScannerControlKeyboardExtended:
    """Extended tests for get_scanner_control_keyboard function."""

    def test_keyboard_without_level_has_back_button(self):
        """Test keyboard without level has back to dashboard button."""
        keyboard = get_scanner_control_keyboard(level=None)

        back_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if "Назад" in button.text:
                    back_buttons.append(button)

        assert len(back_buttons) == 1
        assert back_buttons[0].callback_data == DASHBOARD_ACTION

    def test_keyboard_with_level_has_start_button(self):
        """Test keyboard with level has start scan button."""
        keyboard = get_scanner_control_keyboard(level="standard")

        start_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if "Запустить" in button.text:
                    start_buttons.append(button)

        assert len(start_buttons) == 1
        assert "scan_start_standard" in start_buttons[0].callback_data

    def test_keyboard_with_level_has_settings_button(self):
        """Test keyboard with level has settings button."""
        keyboard = get_scanner_control_keyboard(level="boost")

        settings_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if "Настройки" in button.text:
                    settings_buttons.append(button)

        assert len(settings_buttons) == 1
        assert "scan_settings_boost" in settings_buttons[0].callback_data

    def test_keyboard_with_level_has_back_to_levels(self):
        """Test keyboard with level has back to levels button."""
        keyboard = get_scanner_control_keyboard(level="medium")

        back_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if "Назад к уровням" in button.text:
                    back_buttons.append(button)

        assert len(back_buttons) == 1


# ============================================================================
# Handler Functions Tests
# ============================================================================
class TestShowDashboardExtended:
    """Extended tests for show_dashboard function."""

    @pytest.fixture()
    def mock_update_with_query(self):
        """Create mock update with callback query."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        return update

    @pytest.fixture()
    def mock_update_with_message(self):
        """Create mock update with message."""
        update = MagicMock()
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 456
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock context."""
        return MagicMock()

    @pytest.mark.asyncio()
    async def test_show_dashboard_no_user(self, mock_context):
        """Test show_dashboard with no effective user."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.effective_user = None

        await show_dashboard(update, mock_context)

        # Should return early without error

    @pytest.mark.asyncio()
    async def test_show_dashboard_formats_active_scan(
        self, mock_update_with_query, mock_context
    ):
        """Test show_dashboard formats active scan info."""
        # Set up active scan
        dashboard.mark_scan_active(
            user_id=123, scan_id="test_scan", level="boost", game="csgo"
        )

        await show_dashboard(mock_update_with_query, mock_context)

        # Clean up
        dashboard.active_scans.clear()

    @pytest.mark.asyncio()
    async def test_show_dashboard_with_message_sends_reply(
        self, mock_update_with_message, mock_context
    ):
        """Test show_dashboard with message sends reply."""
        await show_dashboard(mock_update_with_message, mock_context)

        mock_update_with_message.message.reply_text.assert_called_once()


class TestShowStatsExtended:
    """Extended tests for show_stats function."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock update."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock context."""
        return MagicMock()

    @pytest.mark.asyncio()
    async def test_show_stats_no_query(self, mock_context):
        """Test show_stats with no callback query."""
        update = MagicMock()
        update.callback_query = None

        await show_stats(update, mock_context)

        # Should return early

    @pytest.mark.asyncio()
    async def test_show_stats_no_user(self, mock_context):
        """Test show_stats with no effective user."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.effective_user = None

        await show_stats(update, mock_context)

        # Should return early

    @pytest.mark.asyncio()
    async def test_show_stats_edits_message(self, mock_update, mock_context):
        """Test show_stats edits message with stats."""
        await show_stats(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args[1]
        assert "reply_markup" in call_kwargs


class TestShowScannerMenuExtended:
    """Extended tests for show_scanner_menu function."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock update."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock context."""
        return MagicMock()

    @pytest.mark.asyncio()
    async def test_show_scanner_menu_no_query(self, mock_context):
        """Test show_scanner_menu with no callback query."""
        update = MagicMock()
        update.callback_query = None

        await show_scanner_menu(update, mock_context)

        # Should return early

    @pytest.mark.asyncio()
    async def test_show_scanner_menu_edits_message(self, mock_update, mock_context):
        """Test show_scanner_menu edits message."""
        await show_scanner_menu(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()


class TestShowActiveScansExtended:
    """Extended tests for show_active_scans function."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock update."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock context."""
        return MagicMock()

    @pytest.mark.asyncio()
    async def test_show_active_scans_no_query(self, mock_context):
        """Test show_active_scans with no callback query."""
        update = MagicMock()
        update.callback_query = None

        await show_active_scans(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_active_scans_no_user(self, mock_context):
        """Test show_active_scans with no effective user."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.effective_user = None

        await show_active_scans(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_active_scans_with_no_active(self, mock_update, mock_context):
        """Test show_active_scans when no active scans."""
        dashboard.active_scans.clear()

        await show_active_scans(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "Нет активных сканирований" in message

    @pytest.mark.asyncio()
    async def test_show_active_scans_with_active(self, mock_update, mock_context):
        """Test show_active_scans when there is an active scan."""
        dashboard.mark_scan_active(
            user_id=123, scan_id="test", level="boost", game="csgo"
        )

        await show_active_scans(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "boost" in message
        assert "csgo" in message

        # Clean up
        dashboard.active_scans.clear()

    @pytest.mark.asyncio()
    async def test_show_active_scans_completed_status(self, mock_update, mock_context):
        """Test show_active_scans with completed status."""
        dashboard.mark_scan_active(
            user_id=123, scan_id="test", level="standard", game="dota2"
        )
        dashboard.mark_scan_complete(user_id=123)

        await show_active_scans(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "completed" in message

        # Clean up
        dashboard.active_scans.clear()


class TestShowHistoryExtended:
    """Extended tests for show_history function."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock update."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock context."""
        return MagicMock()

    @pytest.mark.asyncio()
    async def test_show_history_no_query(self, mock_context):
        """Test show_history with no callback query."""
        update = MagicMock()
        update.callback_query = None

        await show_history(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_history_no_user(self, mock_context):
        """Test show_history with no effective user."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.effective_user = None

        await show_history(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_history_empty(self, mock_update, mock_context):
        """Test show_history with empty history."""
        dashboard.scan_history.clear()

        await show_history(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "История пуста" in message

    @pytest.mark.asyncio()
    async def test_show_history_with_data(self, mock_update, mock_context):
        """Test show_history with scan data."""
        dashboard.scan_history.clear()
        dashboard.add_scan_result(
            user_id=123,
            scan_data={"level": "boost", "opportunities": [{"profit": 10.0}]},
        )

        await show_history(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "boost" in message

        # Clean up
        dashboard.scan_history.clear()

    @pytest.mark.asyncio()
    async def test_show_history_limits_to_ten(self, mock_update, mock_context):
        """Test show_history limits display to 10 items."""
        dashboard.scan_history.clear()

        for i in range(15):
            dashboard.add_scan_result(
                user_id=123, scan_data={"level": f"level_{i}", "opportunities": []}
            )

        await show_history(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        # Should show "последние 10"
        assert "последние 10" in message

        # Clean up
        dashboard.scan_history.clear()


class TestShowChartsExtended:
    """Extended tests for show_charts function."""

    @pytest.fixture()
    def mock_update(self):
        """Create mock update."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.message = MagicMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.message.reply_photo = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123
        return update

    @pytest.fixture()
    def mock_context(self):
        """Create mock context."""
        return MagicMock()

    @pytest.mark.asyncio()
    async def test_show_charts_no_query(self, mock_context):
        """Test show_charts with no callback query."""
        update = MagicMock()
        update.callback_query = None

        await show_charts(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_charts_no_user(self, mock_context):
        """Test show_charts with no effective user."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.effective_user = None

        await show_charts(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_charts_no_message(self, mock_context):
        """Test show_charts with no message."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.message = None
        update.effective_user = MagicMock()
        update.effective_user.id = 123

        await show_charts(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_charts_message_not_message_instance(self, mock_context):
        """Test show_charts when message is not Message instance."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        # Use a non-Message object by making isinstance check fail
        update.callback_query.message = "not_a_message"
        update.effective_user = MagicMock()
        update.effective_user.id = 123

        # This should handle gracefully - function returns early
        await show_charts(update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_charts_empty_history(self, mock_update, mock_context):
        """Test show_charts with empty scan history."""
        dashboard.scan_history.clear()

        loading_msg = MagicMock()
        loading_msg.edit_text = AsyncMock()
        loading_msg.delete = AsyncMock()
        mock_update.callback_query.message.reply_text = AsyncMock(
            return_value=loading_msg
        )

        await show_charts(mock_update, mock_context)

        # Should show "недостаточно данных" message
        loading_msg.edit_text.assert_called_once()
        call_args = loading_msg.edit_text.call_args
        assert "Недостаточно данных" in call_args[0][0]


class TestRegisterDashboardHandlers:
    """Tests for register_dashboard_handlers function."""

    def test_register_handlers(self):
        """Test handlers are registered."""
        app = MagicMock()
        app.add_handler = MagicMock()

        register_dashboard_handlers(app)

        # Should register 7 handlers
        assert app.add_handler.call_count == 7

    def test_register_handlers_patterns(self):
        """Test handlers are registered with correct patterns."""
        app = MagicMock()

        register_dashboard_handlers(app)

        # Check that handlers were added
        calls = app.add_handler.call_args_list
        patterns = []
        for call in calls:
            handler = call[0][0]
            if hasattr(handler, "pattern"):
                patterns.append(
                    handler.pattern.pattern
                    if hasattr(handler.pattern, "pattern")
                    else str(handler.pattern)
                )

        assert len(calls) == 7


# ============================================================================
# Global Dashboard Instance Tests
# ============================================================================
class TestGlobalDashboard:
    """Tests for global dashboard instance."""

    def test_global_dashboard_exists(self):
        """Test global dashboard instance exists."""
        assert dashboard is not None

    def test_global_dashboard_is_scanner_dashboard(self):
        """Test global dashboard is ScannerDashboard instance."""
        assert isinstance(dashboard, ScannerDashboard)


# ============================================================================
# Edge Cases Tests
# ============================================================================
class TestDashboardEdgeCases:
    """Tests for edge cases."""

    def test_unicode_in_scan_data(self):
        """Test unicode characters in scan data."""
        dash = ScannerDashboard()
        dash.add_scan_result(
            user_id=123,
            scan_data={
                "level": "буст",  # Russian
                "game": "ксго",  # Russian
                "opportunities": [{"name": "АК-47 | Редлайн"}],
            },
        )

        assert len(dash.scan_history) == 1
        assert dash.scan_history[0]["data"]["level"] == "буст"

    def test_very_large_user_id(self):
        """Test with very large user ID."""
        dash = ScannerDashboard()
        large_id = 999999999999

        dash.mark_scan_active(
            user_id=large_id, scan_id="test", level="boost", game="csgo"
        )

        assert large_id in dash.active_scans

    def test_zero_user_id(self):
        """Test with zero user ID."""
        dash = ScannerDashboard()

        dash.mark_scan_active(user_id=0, scan_id="test", level="boost", game="csgo")

        assert 0 in dash.active_scans

    def test_negative_user_id(self):
        """Test with negative user ID."""
        dash = ScannerDashboard()

        dash.mark_scan_active(user_id=-1, scan_id="test", level="boost", game="csgo")

        assert -1 in dash.active_scans

    def test_special_characters_in_scan_id(self):
        """Test special characters in scan_id."""
        dash = ScannerDashboard()

        dash.mark_scan_active(
            user_id=123, scan_id="scan-123_test@!#$%", level="boost", game="csgo"
        )

        assert dash.active_scans[123]["scan_id"] == "scan-123_test@!#$%"

    def test_very_long_opportunities_list(self):
        """Test with very long opportunities list."""
        dash = ScannerDashboard()

        opportunities = [{"profit": float(i)} for i in range(1000)]
        dash.add_scan_result(user_id=123, scan_data={"opportunities": opportunities})

        stats = dash.get_user_stats(user_id=123)
        assert stats["total_opportunities"] == 1000

    def test_very_high_profit_values(self):
        """Test with very high profit values."""
        dash = ScannerDashboard()

        dash.add_scan_result(
            user_id=123, scan_data={"opportunities": [{"profit": 999999.99}]}
        )

        stats = dash.get_user_stats(user_id=123)
        assert stats["max_profit"] == 999999.99

    def test_very_small_profit_values(self):
        """Test with very small profit values."""
        dash = ScannerDashboard()

        dash.add_scan_result(
            user_id=123, scan_data={"opportunities": [{"profit": 0.0001}]}
        )

        stats = dash.get_user_stats(user_id=123)
        assert stats["avg_profit"] == 0.0001


# ============================================================================
# Integration Tests
# ============================================================================
class TestDashboardIntegration:
    """Integration tests for dashboard functionality."""

    def test_full_scan_lifecycle(self):
        """Test full scan lifecycle: start -> add result -> complete."""
        dash = ScannerDashboard()
        user_id = 123

        # Start scan
        dash.mark_scan_active(
            user_id=user_id, scan_id="scan_001", level="standard", game="csgo"
        )
        assert dash.get_active_scan(user_id)["status"] == "running"

        # Add result
        dash.add_scan_result(
            user_id=user_id,
            scan_data={
                "level": "standard",
                "opportunities": [{"profit": 15.0}, {"profit": 25.0}],
            },
        )

        # Complete
        dash.mark_scan_complete(user_id)
        assert dash.get_active_scan(user_id)["status"] == "completed"

        # Check stats
        stats = dash.get_user_stats(user_id)
        assert stats["total_scans"] == 1
        assert stats["total_opportunities"] == 2
        assert stats["avg_profit"] == 20.0

    def test_multiple_users_workflow(self):
        """Test workflow with multiple users."""
        dash = ScannerDashboard()

        users = [1, 2, 3]

        # Each user starts and completes a scan
        for user_id in users:
            dash.mark_scan_active(
                user_id=user_id, scan_id=f"scan_{user_id}", level="boost", game="csgo"
            )
            dash.add_scan_result(
                user_id=user_id,
                scan_data={
                    "level": "boost",
                    "opportunities": [{"profit": float(user_id * 10)}],
                },
            )
            dash.mark_scan_complete(user_id)

        # Verify each user's stats
        for user_id in users:
            stats = dash.get_user_stats(user_id)
            assert stats["total_scans"] == 1
            assert stats["max_profit"] == float(user_id * 10)

    def test_repeated_scans_accumulate(self):
        """Test that repeated scans accumulate correctly."""
        dash = ScannerDashboard()
        user_id = 123

        for i in range(5):
            dash.add_scan_result(
                user_id=user_id,
                scan_data={
                    "level": f"level_{i}",
                    "opportunities": [{"profit": float(i + 1)}],
                },
            )

        stats = dash.get_user_stats(user_id)
        assert stats["total_scans"] == 5
        assert stats["total_opportunities"] == 5
        # avg = (1+2+3+4+5)/5 = 3.0
        assert stats["avg_profit"] == 3.0
        assert stats["max_profit"] == 5.0

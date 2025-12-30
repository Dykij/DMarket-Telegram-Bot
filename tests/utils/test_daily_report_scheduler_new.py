"""Unit tests for src/utils/daily_report_scheduler.py.

Tests for DailyReportScheduler including:
- Scheduler initialization
- Starting and stopping the scheduler
- Report generation and formatting
- Statistics collection
- Sending reports to admins
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.utils.daily_report_scheduler import DailyReportScheduler


class TestDailyReportSchedulerInit:
    """Tests for DailyReportScheduler initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        mock_database = MagicMock()
        mock_bot = MagicMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123456789],
        )

        assert scheduler.database is mock_database
        assert scheduler.bot is mock_bot
        assert scheduler.admin_users == [123456789]
        assert scheduler.report_time == time(9, 0)
        assert scheduler.enabled is True
        assert scheduler._is_running is False

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        mock_database = MagicMock()
        mock_bot = MagicMock()
        custom_time = time(18, 30)

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[111, 222, 333],
            report_time=custom_time,
            enabled=False,
        )

        assert scheduler.report_time == custom_time
        assert scheduler.enabled is False
        assert len(scheduler.admin_users) == 3


class TestDailyReportSchedulerStartStop:
    """Tests for starting and stopping the scheduler."""

    @pytest.mark.asyncio()
    async def test_start_when_disabled(self):
        """Test starting scheduler when disabled."""
        mock_database = MagicMock()
        mock_bot = MagicMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=False,
        )

        await scheduler.start()

        assert scheduler._is_running is False

    @pytest.mark.asyncio()
    async def test_start_when_enabled(self):
        """Test starting scheduler when enabled."""
        mock_database = MagicMock()
        mock_bot = MagicMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=True,
        )

        await scheduler.start()

        assert scheduler._is_running is True

        # Cleanup
        await scheduler.stop()

    @pytest.mark.asyncio()
    async def test_start_already_running(self):
        """Test starting scheduler that is already running."""
        mock_database = MagicMock()
        mock_bot = MagicMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=True,
        )

        await scheduler.start()
        assert scheduler._is_running is True

        # Start again should not fail
        await scheduler.start()
        assert scheduler._is_running is True

        # Cleanup
        await scheduler.stop()

    @pytest.mark.asyncio()
    async def test_stop_when_running(self):
        """Test stopping scheduler when running."""
        mock_database = MagicMock()
        mock_bot = MagicMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=True,
        )

        await scheduler.start()
        await scheduler.stop()

        assert scheduler._is_running is False

    @pytest.mark.asyncio()
    async def test_stop_when_not_running(self):
        """Test stopping scheduler that is not running."""
        mock_database = MagicMock()
        mock_bot = MagicMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=True,
        )

        # Should not fail
        await scheduler.stop()
        assert scheduler._is_running is False


class TestDailyReportSchedulerManualReport:
    """Tests for manual report generation."""

    @pytest.mark.asyncio()
    async def test_send_manual_report(self):
        """Test sending manual report."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(return_value={
            "total_trades": 10,
            "successful_trades": 8,
            "cancelled_trades": 1,
            "failed_trades": 1,
            "total_profit_usd": 50.0,
            "avg_profit_percent": 5.0,
        })
        mock_database.get_error_statistics = AsyncMock(return_value={
            "api_errors": {},
            "critical_errors": 0,
        })
        mock_database.get_scan_statistics = AsyncMock(return_value={
            "scans_performed": 100,
            "opportunities_found": 25,
        })

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123456789],
            enabled=True,
        )

        await scheduler.send_manual_report(days=1)

        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 123456789
        assert "Ежедневный отчёт" in call_args.kwargs["text"]


class TestDailyReportSchedulerGenerateReport:
    """Tests for report generation logic."""

    @pytest.mark.asyncio()
    async def test_generate_and_send_report_success(self):
        """Test successful report generation and sending."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(return_value={
            "total_trades": 5,
            "successful_trades": 4,
            "cancelled_trades": 1,
            "failed_trades": 0,
            "total_profit_usd": 25.0,
            "avg_profit_percent": 5.0,
        })
        mock_database.get_error_statistics = AsyncMock(return_value={})
        mock_database.get_scan_statistics = AsyncMock(return_value={
            "scans_performed": 50,
            "opportunities_found": 10,
        })

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[111, 222],
            enabled=True,
        )

        await scheduler._generate_and_send_report(days=1)

        # Should send to both admins
        assert mock_bot.send_message.call_count == 2

    @pytest.mark.asyncio()
    async def test_generate_report_with_no_trades(self):
        """Test report generation with no trades."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(return_value={
            "total_trades": 0,
            "successful_trades": 0,
            "cancelled_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
            "avg_profit_percent": 0.0,
        })
        mock_database.get_error_statistics = AsyncMock(return_value={})
        mock_database.get_scan_statistics = AsyncMock(return_value={})

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=True,
        )

        await scheduler._generate_and_send_report()

        mock_bot.send_message.assert_called_once()
        report_text = mock_bot.send_message.call_args.kwargs["text"]
        assert "Сделок: 0" in report_text

    @pytest.mark.asyncio()
    async def test_generate_report_with_errors(self):
        """Test report generation with API errors."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(return_value={})
        mock_database.get_error_statistics = AsyncMock(return_value={
            "api_errors": {
                "RateLimitError": 5,
                "TimeoutError": 2,
            },
            "critical_errors": 1,
        })
        mock_database.get_scan_statistics = AsyncMock(return_value={})

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[123],
            enabled=True,
        )

        await scheduler._generate_and_send_report()

        report_text = mock_bot.send_message.call_args.kwargs["text"]
        assert "Ошибки" in report_text
        assert "RateLimitError" in report_text
        assert "Критических: 1" in report_text

    @pytest.mark.asyncio()
    async def test_generate_report_send_failure(self):
        """Test handling send failure to some admins."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(return_value={})
        mock_database.get_error_statistics = AsyncMock(return_value={})
        mock_database.get_scan_statistics = AsyncMock(return_value={})

        mock_bot = MagicMock()
        # First call succeeds, second fails
        mock_bot.send_message = AsyncMock(
            side_effect=[None, Exception("Send failed")]
        )

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=mock_bot,
            admin_users=[111, 222],
            enabled=True,
        )

        # Should not raise
        await scheduler._generate_and_send_report()

        assert mock_bot.send_message.call_count == 2


class TestDailyReportSchedulerCollectStatistics:
    """Tests for statistics collection."""

    @pytest.mark.asyncio()
    async def test_collect_statistics_success(self):
        """Test successful statistics collection."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(return_value={
            "total_trades": 10,
            "successful_trades": 8,
        })
        mock_database.get_error_statistics = AsyncMock(return_value={
            "api_errors": {"Error1": 2},
            "critical_errors": 1,
        })
        mock_database.get_scan_statistics = AsyncMock(return_value={
            "scans_performed": 50,
            "opportunities_found": 10,
        })

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=MagicMock(),
            admin_users=[123],
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        stats = await scheduler._collect_statistics(start_date, end_date)

        assert stats["total_trades"] == 10
        assert stats["successful_trades"] == 8
        assert stats["api_errors"] == {"Error1": 2}
        assert stats["critical_errors"] == 1
        assert stats["scans_performed"] == 50

    @pytest.mark.asyncio()
    async def test_collect_statistics_with_db_error(self):
        """Test statistics collection when DB fails."""
        mock_database = MagicMock()
        mock_database.get_trade_statistics = AsyncMock(
            side_effect=RuntimeError("DB error")
        )
        mock_database.get_error_statistics = AsyncMock(return_value={})
        mock_database.get_scan_statistics = AsyncMock(return_value={})

        scheduler = DailyReportScheduler(
            database=mock_database,
            bot=MagicMock(),
            admin_users=[123],
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # Should not raise, returns default stats
        stats = await scheduler._collect_statistics(start_date, end_date)

        assert stats["total_trades"] == 0
        assert stats["api_errors"] == {}


class TestDailyReportSchedulerFormatReport:
    """Tests for report formatting."""

    def test_format_report_single_day(self):
        """Test formatting report for single day."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 10,
            "successful_trades": 8,
            "cancelled_trades": 1,
            "failed_trades": 1,
            "total_profit_usd": 50.0,
            "avg_profit_percent": 5.0,
            "scans_performed": 100,
            "opportunities_found": 20,
            "api_errors": {},
            "critical_errors": 0,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 15)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "📊 Ежедневный отчёт" in report
        assert "15.01.2024" in report
        assert "Сделок: 10" in report
        assert "Успешных: 8" in report
        assert "+50.00$" in report
        assert "✅ Ошибок не обнаружено" in report

    def test_format_report_date_range(self):
        """Test formatting report for date range."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 0,
            "total_profit_usd": 0.0,
            "avg_profit_percent": 0.0,
            "scans_performed": 0,
            "opportunities_found": 0,
            "api_errors": {},
            "critical_errors": 0,
        }

        start_date = datetime(2024, 1, 10)
        end_date = datetime(2024, 1, 15)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "10.01.2024 - 15.01.2024" in report

    def test_format_report_with_errors(self):
        """Test formatting report with errors."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 5,
            "successful_trades": 3,
            "cancelled_trades": 1,
            "failed_trades": 1,
            "total_profit_usd": -10.0,
            "avg_profit_percent": -2.0,
            "scans_performed": 50,
            "opportunities_found": 5,
            "api_errors": {
                "RateLimitError": 10,
                "ConnectionError": 3,
            },
            "critical_errors": 2,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 15)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "⚠️ Ошибки:" in report
        assert "RateLimitError: 10" in report
        assert "ConnectionError: 3" in report
        assert "🔴 Критических: 2" in report
        assert "-10.00$" in report

    def test_format_report_with_scans_only(self):
        """Test formatting report with scan data only."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 0,
            "total_profit_usd": 0.0,
            "avg_profit_percent": 0.0,
            "scans_performed": 200,
            "opportunities_found": 50,
            "api_errors": {},
            "critical_errors": 0,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 15)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "🔍 Сканирование:" in report
        assert "Сканов выполнено: 200" in report
        assert "Возможностей найдено: 50" in report

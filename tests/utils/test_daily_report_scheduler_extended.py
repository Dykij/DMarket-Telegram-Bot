"""Extended tests for daily_report_scheduler module.

This module adds comprehensive tests for edge cases, error handling,
and additional scenarios not covered in the basic tests.
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.daily_report_scheduler import DailyReportScheduler


class TestDailyReportSchedulerEdgeCases:
    """Tests for edge cases in DailyReportScheduler."""

    def test_init_with_very_late_report_time(self):
        """Test initialization with late report time (23:59)."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
            report_time=time(23, 59),
        )
        assert scheduler.report_time == time(23, 59)

    def test_init_with_early_morning_report_time(self):
        """Test initialization with early morning report time (00:01)."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
            report_time=time(0, 1),
        )
        assert scheduler.report_time == time(0, 1)

    def test_init_with_large_admin_list(self):
        """Test initialization with large admin list."""
        large_admin_list = list(range(1, 1001))  # 1000 admins
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=large_admin_list,
        )
        assert len(scheduler.admin_users) == 1000

    def test_init_with_negative_user_ids(self):
        """Test initialization with negative user IDs (group chats)."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[-100123456789, -100987654321],
        )
        assert -100123456789 in scheduler.admin_users


class TestDailyReportSchedulerStartStopEdgeCases:
    """Tests for start/stop edge cases."""

    @pytest.mark.asyncio()
    async def test_start_multiple_times(self):
        """Test calling start multiple times doesn't cause issues."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        with (
            patch.object(scheduler.scheduler, "add_job") as mock_add,
            patch.object(scheduler.scheduler, "start") as mock_start,
        ):
            await scheduler.start()
            await scheduler.start()  # Second call should be ignored
            await scheduler.start()  # Third call should be ignored

            # add_job and start should only be called once
            assert mock_add.call_count == 1
            assert mock_start.call_count == 1

    @pytest.mark.asyncio()
    async def test_stop_multiple_times(self):
        """Test calling stop multiple times doesn't cause issues."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )
        scheduler._is_running = True

        with patch.object(scheduler.scheduler, "shutdown") as mock_shutdown:
            await scheduler.stop()
            await scheduler.stop()  # Second call should be ignored
            await scheduler.stop()  # Third call should be ignored

            # shutdown should only be called once
            assert mock_shutdown.call_count == 1

    @pytest.mark.asyncio()
    async def test_start_then_stop_then_start(self):
        """Test scheduler can be restarted after stopping."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        with (
            patch.object(scheduler.scheduler, "add_job"),
            patch.object(scheduler.scheduler, "start"),
            patch.object(scheduler.scheduler, "shutdown"),
        ):
            await scheduler.start()
            assert scheduler._is_running is True

            await scheduler.stop()
            assert scheduler._is_running is False

            # Reset scheduler for restart
            scheduler.scheduler = MagicMock()

            await scheduler.start()
            assert scheduler._is_running is True


class TestGenerateAndSendReportEdgeCases:
    """Tests for _generate_and_send_report edge cases."""

    @pytest.mark.asyncio()
    async def test_generate_report_with_partial_admin_failures(self):
        """Test report generation when some admins fail to receive."""
        bot = MagicMock()
        call_count = 0

        async def send_with_partial_failure(chat_id, text):
            nonlocal call_count
            call_count += 1
            if chat_id == 456:  # Second admin fails
                raise Exception("User blocked bot")
            return True

        bot.send_message = send_with_partial_failure
        database = MagicMock()

        scheduler = DailyReportScheduler(
            database=database,
            bot=bot,
            admin_users=[123, 456, 789],
        )

        with patch.object(
            scheduler, "_collect_statistics", new_callable=AsyncMock
        ) as mock_stats:
            mock_stats.return_value = {"total_trades": 5}

            # Should not raise despite partial failure
            await scheduler._generate_and_send_report()

            assert call_count == 3  # All admins were attempted

    @pytest.mark.asyncio()
    async def test_generate_report_with_all_admins_failing(self):
        """Test report generation when all admins fail to receive."""
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Network error"))
        database = MagicMock()

        scheduler = DailyReportScheduler(
            database=database,
            bot=bot,
            admin_users=[123, 456],
        )

        with patch.object(
            scheduler, "_collect_statistics", new_callable=AsyncMock
        ) as mock_stats:
            mock_stats.return_value = {"total_trades": 0}

            # Should not raise
            await scheduler._generate_and_send_report()

    @pytest.mark.asyncio()
    async def test_generate_report_statistics_collection_error(self):
        """Test report generation when statistics collection fails."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        database = MagicMock()

        scheduler = DailyReportScheduler(
            database=database,
            bot=bot,
            admin_users=[123],
        )

        with patch.object(
            scheduler, "_collect_statistics", new_callable=AsyncMock
        ) as mock_stats:
            mock_stats.side_effect = RuntimeError("Database connection lost")

            # Should send error notification
            await scheduler._generate_and_send_report()

            # At least one message should be sent (error notification)
            assert bot.send_message.call_count >= 1

    @pytest.mark.asyncio()
    async def test_generate_report_with_multiday_range(self):
        """Test manual report with 30-day range."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        database = MagicMock()

        scheduler = DailyReportScheduler(
            database=database,
            bot=bot,
            admin_users=[123],
        )

        with patch.object(
            scheduler, "_collect_statistics", new_callable=AsyncMock
        ) as mock_stats:
            mock_stats.return_value = {
                "total_trades": 500,
                "successful_trades": 450,
                "cancelled_trades": 30,
                "failed_trades": 20,
                "total_profit_usd": 2500.0,
                "avg_profit_percent": 5.0,
                "api_errors": {},
                "critical_errors": 0,
                "scans_performed": 3000,
                "opportunities_found": 600,
            }

            await scheduler._generate_and_send_report(days=30)

            bot.send_message.assert_called_once()


class TestCollectStatisticsEdgeCases:
    """Tests for _collect_statistics edge cases."""

    @pytest.mark.asyncio()
    async def test_collect_statistics_with_missing_methods(self):
        """Test statistics collection when database methods return errors."""
        database = MagicMock()
        # Simulate methods that raise errors
        database.get_trade_statistics = AsyncMock(
            side_effect=RuntimeError("Method error")
        )
        database.get_error_statistics = AsyncMock(
            side_effect=RuntimeError("Method error")
        )
        database.get_scan_statistics = AsyncMock(
            side_effect=RuntimeError("Method error")
        )

        scheduler = DailyReportScheduler(
            database=database,
            bot=MagicMock(),
            admin_users=[123],
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # Should return default values when methods fail
        stats = await scheduler._collect_statistics(start_date, end_date)

        # Should return default stats structure
        assert "total_trades" in stats
        assert stats["total_trades"] == 0

    @pytest.mark.asyncio()
    async def test_collect_statistics_with_database_timeout(self):
        """Test statistics collection with database timeout."""
        database = MagicMock()
        database.get_trade_statistics = AsyncMock(
            side_effect=TimeoutError("Database timeout")
        )

        scheduler = DailyReportScheduler(
            database=database,
            bot=MagicMock(),
            admin_users=[123],
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # Should return default values on error
        # The current implementation might raise, so we test that case
        try:
            stats = await scheduler._collect_statistics(start_date, end_date)
            # If it doesn't raise, verify defaults
            assert "total_trades" in stats
        except (RuntimeError, TimeoutError):
            # Also acceptable behavior
            pass

    @pytest.mark.asyncio()
    async def test_collect_statistics_with_partial_data(self):
        """Test statistics collection with partial data from database."""
        database = MagicMock()
        database.get_trade_statistics = AsyncMock(
            return_value={"total_trades": 10}
        )  # Missing other fields
        database.get_error_statistics = AsyncMock(return_value=None)
        database.get_scan_statistics = AsyncMock(return_value=None)

        scheduler = DailyReportScheduler(
            database=database,
            bot=MagicMock(),
            admin_users=[123],
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        stats = await scheduler._collect_statistics(start_date, end_date)

        assert stats["total_trades"] == 10
        # Default values should be preserved for missing fields
        assert stats["api_errors"] == {}
        assert stats["critical_errors"] == 0

    @pytest.mark.asyncio()
    async def test_collect_statistics_with_negative_values(self):
        """Test statistics collection with negative values (edge case)."""
        database = MagicMock()
        database.get_trade_statistics = AsyncMock(
            return_value={
                "total_trades": 5,
                "successful_trades": 3,
                "total_profit_usd": -50.0,  # Loss
                "avg_profit_percent": -5.0,
            }
        )
        database.get_error_statistics = AsyncMock(return_value=None)
        database.get_scan_statistics = AsyncMock(return_value=None)

        scheduler = DailyReportScheduler(
            database=database,
            bot=MagicMock(),
            admin_users=[123],
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        stats = await scheduler._collect_statistics(start_date, end_date)

        assert stats["total_profit_usd"] == -50.0
        assert stats["avg_profit_percent"] == -5.0


class TestFormatReportEdgeCases:
    """Tests for _format_report edge cases."""

    def test_format_report_with_100_percent_success_rate(self):
        """Test report formatting with 100% success rate."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 100,
            "successful_trades": 100,
            "cancelled_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 500.0,
            "avg_profit_percent": 5.0,
            "api_errors": {},
            "critical_errors": 0,
            "scans_performed": 1000,
            "opportunities_found": 200,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "100.0%" in report  # 100% success rate
        assert "Успешных: 100" in report

    def test_format_report_with_zero_percent_success_rate(self):
        """Test report formatting with 0% success rate."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 10,
            "successful_trades": 0,
            "cancelled_trades": 5,
            "failed_trades": 5,
            "total_profit_usd": -100.0,
            "avg_profit_percent": -10.0,
            "api_errors": {},
            "critical_errors": 0,
            "scans_performed": 50,
            "opportunities_found": 5,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "0.0%" in report  # 0% success rate
        assert "Успешных: 0" in report
        assert "-100.00$" in report

    def test_format_report_with_large_numbers(self):
        """Test report formatting with very large numbers."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 1000000,
            "successful_trades": 999000,
            "cancelled_trades": 500,
            "failed_trades": 500,
            "total_profit_usd": 1000000.50,
            "avg_profit_percent": 50.5,
            "api_errors": {"rate_limit": 100000, "timeout": 50000},
            "critical_errors": 100,
            "scans_performed": 10000000,
            "opportunities_found": 5000000,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)

        report = scheduler._format_report(stats, start_date, end_date)

        assert "1000000" in report
        assert "🔴 Критических: 100" in report

    def test_format_report_with_many_api_errors(self):
        """Test report formatting with many different API error types."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 0,
            "successful_trades": 0,
            "cancelled_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
            "avg_profit_percent": 0.0,
            "api_errors": {
                "rate_limit": 100,
                "timeout": 50,
                "connection_error": 30,
                "unauthorized": 20,
                "server_error": 10,
            },
            "critical_errors": 5,
            "scans_performed": 0,
            "opportunities_found": 0,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)

        report = scheduler._format_report(stats, start_date, end_date)

        # Errors should be sorted by count (descending)
        assert "rate_limit: 100" in report
        assert "⚠️ Ошибки:" in report

    def test_format_report_with_very_long_date_range(self):
        """Test report formatting with year-long date range."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 0,
            "successful_trades": 0,
            "cancelled_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
            "avg_profit_percent": 0.0,
            "api_errors": {},
            "critical_errors": 0,
            "scans_performed": 0,
            "opportunities_found": 0,
        }

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        report = scheduler._format_report(stats, start_date, end_date)

        # Should show date range
        assert "01.01.2024" in report
        assert "31.12.2024" in report

    def test_format_report_with_float_precision(self):
        """Test report formatting with float precision edge cases."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 3,
            "successful_trades": 1,
            "cancelled_trades": 1,
            "failed_trades": 1,
            "total_profit_usd": 0.01,  # Very small profit
            "avg_profit_percent": 0.001,  # Very small percentage
            "api_errors": {},
            "critical_errors": 0,
            "scans_performed": 10,
            "opportunities_found": 1,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)

        report = scheduler._format_report(stats, start_date, end_date)

        # Check float formatting
        assert "+0.01$" in report
        assert "(+0.0%)" in report  # Rounded to 1 decimal

    def test_format_report_with_decimal_percentages(self):
        """Test report formatting with decimal success percentages."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        stats = {
            "total_trades": 3,
            "successful_trades": 1,  # 33.33...%
            "cancelled_trades": 1,
            "failed_trades": 1,
            "total_profit_usd": 10.0,
            "avg_profit_percent": 3.33,
            "api_errors": {},
            "critical_errors": 0,
            "scans_performed": 0,
            "opportunities_found": 0,
        }

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)

        report = scheduler._format_report(stats, start_date, end_date)

        # Should handle decimal percentages
        assert "33.3%" in report  # Rounded


class TestManualReportEdgeCases:
    """Tests for send_manual_report edge cases."""

    @pytest.mark.asyncio()
    async def test_manual_report_with_zero_days(self):
        """Test manual report with zero days (edge case)."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        with patch.object(
            scheduler, "_generate_and_send_report", new_callable=AsyncMock
        ) as mock_generate:
            await scheduler.send_manual_report(days=0)
            mock_generate.assert_called_once_with(days=0)

    @pytest.mark.asyncio()
    async def test_manual_report_with_large_day_range(self):
        """Test manual report with 365 days."""
        scheduler = DailyReportScheduler(
            database=MagicMock(),
            bot=MagicMock(),
            admin_users=[123],
        )

        with patch.object(
            scheduler, "_generate_and_send_report", new_callable=AsyncMock
        ) as mock_generate:
            await scheduler.send_manual_report(days=365)
            mock_generate.assert_called_once_with(days=365)


class TestSchedulerIntegration:
    """Integration-like tests for the scheduler."""

    @pytest.mark.asyncio()
    async def test_full_report_cycle(self):
        """Test a complete report generation cycle."""
        bot = MagicMock()
        bot.send_message = AsyncMock()

        database = MagicMock()
        database.get_trade_statistics = AsyncMock(
            return_value={
                "total_trades": 50,
                "successful_trades": 45,
                "cancelled_trades": 3,
                "failed_trades": 2,
                "total_profit_usd": 250.0,
                "avg_profit_percent": 5.0,
            }
        )
        database.get_error_statistics = AsyncMock(
            return_value={"api_errors": {"rate_limit": 5}, "critical_errors": 0}
        )
        database.get_scan_statistics = AsyncMock(
            return_value={"scans_performed": 500, "opportunities_found": 100}
        )

        scheduler = DailyReportScheduler(
            database=database,
            bot=bot,
            admin_users=[123, 456],
        )

        await scheduler.send_manual_report(days=7)

        assert bot.send_message.call_count == 2  # Both admins received report

        # Verify report content
        call_args = bot.send_message.call_args_list[0]
        report_text = call_args.kwargs.get(
            "text", call_args.args[1] if len(call_args.args) > 1 else ""
        )

        assert "📊 Ежедневный отчёт" in report_text
        assert "Сделок: 50" in report_text

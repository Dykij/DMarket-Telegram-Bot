"""Comprehensive tests for prometheus_exporter module.

Tests for MetricsCollector and measure_time decorator.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_record_command(self) -> None:
        """Test recording a command execution."""
        with patch("src.utils.prometheus_exporter.commands_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_command("scan", 123456789)

            mock_counter.labels.assert_called_once_with(
                command="scan",
                user_id="123456789",
            )
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_command_different_commands(self) -> None:
        """Test recording different commands."""
        with patch("src.utils.prometheus_exporter.commands_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_command("start", 1)
            MetricsCollector.record_command("balance", 2)
            MetricsCollector.record_command("targets", 3)

            assert mock_counter.labels.call_count == 3

    def test_record_api_request(self) -> None:
        """Test recording an API request."""
        with (
            patch("src.utils.prometheus_exporter.api_requests_total") as mock_counter,
            patch(
                "src.utils.prometheus_exporter.api_request_duration_seconds"
            ) as mock_histogram,
        ):
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_api_request(
                endpoint="/api/items",
                method="GET",
                status=200,
                duration=0.5,
            )

            mock_counter.labels.assert_called_once_with(
                endpoint="/api/items",
                method="GET",
                status="200",
            )
            mock_histogram.labels.assert_called_once_with(endpoint="/api/items")
            mock_histogram.labels.return_value.observe.assert_called_once_with(0.5)

    def test_record_api_request_error_status(self) -> None:
        """Test recording an API request with error status."""
        with (
            patch("src.utils.prometheus_exporter.api_requests_total") as mock_counter,
            patch(
                "src.utils.prometheus_exporter.api_request_duration_seconds"
            ) as mock_histogram,
        ):
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_api_request(
                endpoint="/api/buy",
                method="POST",
                status=500,
                duration=1.2,
            )

            mock_counter.labels.assert_called_once_with(
                endpoint="/api/buy",
                method="POST",
                status="500",
            )

    def test_record_error(self) -> None:
        """Test recording an error."""
        with patch("src.utils.prometheus_exporter.errors_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_error("ValueError", "arbitrage")

            mock_counter.labels.assert_called_once_with(
                error_type="ValueError",
                module="arbitrage",
            )
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_error_different_types(self) -> None:
        """Test recording different error types."""
        with patch("src.utils.prometheus_exporter.errors_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_error("APIError", "dmarket")
            MetricsCollector.record_error("RateLimitError", "api")
            MetricsCollector.record_error("TimeoutError", "network")

            assert mock_counter.labels.call_count == 3

    def test_record_arbitrage_scan(self) -> None:
        """Test recording an arbitrage scan."""
        with (
            patch("src.utils.prometheus_exporter.arbitrage_scans_total") as mock_scans,
            patch(
                "src.utils.prometheus_exporter.arbitrage_opportunities_found"
            ) as mock_found,
            patch(
                "src.utils.prometheus_exporter.arbitrage_scan_duration_seconds"
            ) as mock_duration,
        ):
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_arbitrage_scan(
                level="standard",
                game="csgo",
                duration=2.5,
                found=10,
            )

            mock_scans.labels.assert_called_once_with(level="standard", game="csgo")
            mock_scans.labels.return_value.inc.assert_called_once()

            mock_found.labels.assert_called_once_with(level="standard", game="csgo")
            mock_found.labels.return_value.inc.assert_called_once_with(10)

            mock_duration.labels.assert_called_once_with(level="standard", game="csgo")
            mock_duration.labels.return_value.observe.assert_called_once_with(2.5)

    def test_record_target_created(self) -> None:
        """Test recording target creation."""
        with patch("src.utils.prometheus_exporter.targets_created_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_target_created("csgo", 123)

            mock_counter.labels.assert_called_once_with(game="csgo", user_id="123")
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_target_hit(self) -> None:
        """Test recording target hit."""
        with patch("src.utils.prometheus_exporter.targets_hit_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_target_hit("dota2", 456)

            mock_counter.labels.assert_called_once_with(game="dota2", user_id="456")
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_trade_buy(self) -> None:
        """Test recording a buy trade."""
        with (
            patch("src.utils.prometheus_exporter.trades_total") as mock_trades,
            patch("src.utils.prometheus_exporter.trade_volume_usd") as mock_volume,
        ):
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_trade("buy", "csgo", 50.00)

            mock_trades.labels.assert_called_once_with(type="buy", game="csgo")
            mock_trades.labels.return_value.inc.assert_called_once()

            mock_volume.labels.assert_called_once_with(type="buy", game="csgo")
            mock_volume.labels.return_value.inc.assert_called_once_with(50.00)

    def test_record_trade_sell(self) -> None:
        """Test recording a sell trade."""
        with (
            patch("src.utils.prometheus_exporter.trades_total") as mock_trades,
            patch("src.utils.prometheus_exporter.trade_volume_usd") as mock_volume,
        ):
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.record_trade("sell", "tf2", 100.50)

            mock_trades.labels.assert_called_once_with(type="sell", game="tf2")
            mock_volume.labels.return_value.inc.assert_called_once_with(100.50)

    def test_update_active_users(self) -> None:
        """Test updating active users count."""
        with patch("src.utils.prometheus_exporter.active_users") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_active_users(150)

            mock_gauge.set.assert_called_once_with(150)

    def test_update_active_users_zero(self) -> None:
        """Test updating active users to zero."""
        with patch("src.utils.prometheus_exporter.active_users") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_active_users(0)

            mock_gauge.set.assert_called_once_with(0)

    def test_update_active_targets(self) -> None:
        """Test updating active targets count."""
        with patch("src.utils.prometheus_exporter.active_targets") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_active_targets("csgo", 25)

            mock_gauge.labels.assert_called_once_with(game="csgo")
            mock_gauge.labels.return_value.set.assert_called_once_with(25)

    def test_update_balance(self) -> None:
        """Test updating user balance."""
        with patch("src.utils.prometheus_exporter.balance_usd") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_balance(123, 500.75)

            mock_gauge.labels.assert_called_once_with(user_id="123")
            mock_gauge.labels.return_value.set.assert_called_once_with(500.75)

    def test_update_balance_zero(self) -> None:
        """Test updating balance to zero."""
        with patch("src.utils.prometheus_exporter.balance_usd") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_balance(456, 0.0)

            mock_gauge.labels.return_value.set.assert_called_once_with(0.0)

    def test_update_cache_size(self) -> None:
        """Test updating cache size."""
        with patch("src.utils.prometheus_exporter.cache_size") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_cache_size("market_items", 1000)

            mock_gauge.labels.assert_called_once_with(cache_type="market_items")
            mock_gauge.labels.return_value.set.assert_called_once_with(1000)

    def test_update_rate_limit(self) -> None:
        """Test updating rate limit remaining."""
        with patch("src.utils.prometheus_exporter.rate_limit_remaining") as mock_gauge:
            from src.utils.prometheus_exporter import MetricsCollector

            MetricsCollector.update_rate_limit(123, 25)

            mock_gauge.labels.assert_called_once_with(user_id="123")
            mock_gauge.labels.return_value.set.assert_called_once_with(25)

    def test_get_metrics(self) -> None:
        """Test getting metrics in Prometheus format."""
        with patch("src.utils.prometheus_exporter.generate_latest") as mock_generate:
            mock_generate.return_value = b"# HELP metric\n# TYPE metric gauge\nmetric 1.0"

            from src.utils.prometheus_exporter import MetricsCollector

            result = MetricsCollector.get_metrics()

            assert isinstance(result, bytes)
            mock_generate.assert_called_once()


class TestMeasureTimeDecorator:
    """Tests for measure_time decorator."""

    @pytest.mark.asyncio
    async def test_measure_time_basic(self) -> None:
        """Test measure_time decorator basic functionality."""
        mock_histogram = MagicMock()

        from src.utils.prometheus_exporter import measure_time

        @measure_time(mock_histogram)
        async def sample_function():
            await asyncio.sleep(0.01)
            return "result"

        result = await sample_function()

        assert result == "result"
        mock_histogram.observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_measure_time_with_labels(self) -> None:
        """Test measure_time decorator with labels."""
        mock_histogram = MagicMock()

        from src.utils.prometheus_exporter import measure_time

        labels = {"endpoint": "/api/test"}

        @measure_time(mock_histogram, labels)
        async def sample_function():
            return "result"

        result = await sample_function()

        assert result == "result"
        mock_histogram.labels.assert_called_once_with(**labels)
        mock_histogram.labels.return_value.observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_measure_time_with_exception(self) -> None:
        """Test measure_time decorator records time even on exception."""
        mock_histogram = MagicMock()

        from src.utils.prometheus_exporter import measure_time

        @measure_time(mock_histogram)
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_function()

        # Time should still be recorded
        mock_histogram.observe.assert_called_once()


class TestMetricDefinitions:
    """Tests for metric definitions."""

    def test_bot_info_exists(self) -> None:
        """Test that bot_info metric is defined."""
        from src.utils.prometheus_exporter import bot_info

        assert bot_info is not None

    def test_commands_total_exists(self) -> None:
        """Test that commands_total counter is defined."""
        from src.utils.prometheus_exporter import commands_total

        assert commands_total is not None

    def test_api_requests_total_exists(self) -> None:
        """Test that api_requests_total counter is defined."""
        from src.utils.prometheus_exporter import api_requests_total

        assert api_requests_total is not None

    def test_errors_total_exists(self) -> None:
        """Test that errors_total counter is defined."""
        from src.utils.prometheus_exporter import errors_total

        assert errors_total is not None

    def test_arbitrage_scans_total_exists(self) -> None:
        """Test that arbitrage_scans_total counter is defined."""
        from src.utils.prometheus_exporter import arbitrage_scans_total

        assert arbitrage_scans_total is not None

    def test_arbitrage_opportunities_found_exists(self) -> None:
        """Test that arbitrage_opportunities_found counter is defined."""
        from src.utils.prometheus_exporter import arbitrage_opportunities_found

        assert arbitrage_opportunities_found is not None

    def test_targets_created_total_exists(self) -> None:
        """Test that targets_created_total counter is defined."""
        from src.utils.prometheus_exporter import targets_created_total

        assert targets_created_total is not None

    def test_targets_hit_total_exists(self) -> None:
        """Test that targets_hit_total counter is defined."""
        from src.utils.prometheus_exporter import targets_hit_total

        assert targets_hit_total is not None

    def test_trades_total_exists(self) -> None:
        """Test that trades_total counter is defined."""
        from src.utils.prometheus_exporter import trades_total

        assert trades_total is not None

    def test_trade_volume_usd_exists(self) -> None:
        """Test that trade_volume_usd counter is defined."""
        from src.utils.prometheus_exporter import trade_volume_usd

        assert trade_volume_usd is not None

    def test_api_request_duration_seconds_exists(self) -> None:
        """Test that api_request_duration_seconds histogram is defined."""
        from src.utils.prometheus_exporter import api_request_duration_seconds

        assert api_request_duration_seconds is not None

    def test_arbitrage_scan_duration_seconds_exists(self) -> None:
        """Test that arbitrage_scan_duration_seconds histogram is defined."""
        from src.utils.prometheus_exporter import arbitrage_scan_duration_seconds

        assert arbitrage_scan_duration_seconds is not None

    def test_active_users_exists(self) -> None:
        """Test that active_users gauge is defined."""
        from src.utils.prometheus_exporter import active_users

        assert active_users is not None

    def test_active_targets_exists(self) -> None:
        """Test that active_targets gauge is defined."""
        from src.utils.prometheus_exporter import active_targets

        assert active_targets is not None

    def test_balance_usd_exists(self) -> None:
        """Test that balance_usd gauge is defined."""
        from src.utils.prometheus_exporter import balance_usd

        assert balance_usd is not None

    def test_cache_size_exists(self) -> None:
        """Test that cache_size gauge is defined."""
        from src.utils.prometheus_exporter import cache_size

        assert cache_size is not None

    def test_rate_limit_remaining_exists(self) -> None:
        """Test that rate_limit_remaining gauge is defined."""
        from src.utils.prometheus_exporter import rate_limit_remaining

        assert rate_limit_remaining is not None


class TestIntegration:
    """Integration tests for prometheus_exporter module."""

    def test_full_trading_flow_metrics(self) -> None:
        """Test recording metrics for a full trading flow."""
        with (
            patch("src.utils.prometheus_exporter.commands_total") as mock_commands,
            patch("src.utils.prometheus_exporter.api_requests_total") as mock_api,
            patch(
                "src.utils.prometheus_exporter.api_request_duration_seconds"
            ) as mock_api_duration,
            patch("src.utils.prometheus_exporter.trades_total") as mock_trades,
            patch("src.utils.prometheus_exporter.trade_volume_usd") as mock_volume,
        ):
            from src.utils.prometheus_exporter import MetricsCollector

            # User executes scan command
            MetricsCollector.record_command("scan", 123)

            # API request is made
            MetricsCollector.record_api_request("/api/items", "GET", 200, 0.5)

            # Trade is executed
            MetricsCollector.record_trade("buy", "csgo", 25.00)

            # Verify all metrics were recorded
            mock_commands.labels.assert_called_once()
            mock_api.labels.assert_called_once()
            mock_trades.labels.assert_called_once()
            mock_volume.labels.assert_called_once()

    def test_multiple_users_metrics(self) -> None:
        """Test recording metrics for multiple users."""
        with patch("src.utils.prometheus_exporter.commands_total") as mock_counter:
            from src.utils.prometheus_exporter import MetricsCollector

            # Multiple users execute commands
            MetricsCollector.record_command("scan", 1)
            MetricsCollector.record_command("scan", 2)
            MetricsCollector.record_command("balance", 1)

            assert mock_counter.labels.call_count == 3

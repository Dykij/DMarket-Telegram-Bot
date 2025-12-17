"""Unit tests for prometheus_metrics module.

Tests for Prometheus metrics, counters, gauges, histograms,
and utility functions.
"""

from unittest.mock import patch, MagicMock

import pytest

from src.utils.prometheus_metrics import (
    # Metrics
    bot_commands_total,
    bot_errors_total,
    bot_active_users,
    api_requests_total,
    api_request_duration,
    api_errors_total,
    db_connections_active,
    db_query_duration,
    db_errors_total,
    arbitrage_opportunities_found,
    arbitrage_opportunities_avg,
    arbitrage_profit_avg,
    targets_created_total,
    targets_executed_total,
    targets_active,
    total_profit_usd,
    transactions_total,
    transaction_amount_avg,
    app_info,
    app_uptime_seconds,
    # Utility functions
    track_command,
    track_api_request,
    track_db_query,
    track_arbitrage_scan,
    set_active_users,
    get_metrics,
    create_metrics_app,
    # Timer
    Timer,
)


class TestBotMetrics:
    """Tests for bot-related metrics."""

    def test_bot_commands_total_exists(self):
        """Test that bot_commands_total metric exists."""
        assert bot_commands_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "bot_commands" in bot_commands_total._name

    def test_bot_commands_total_has_labels(self):
        """Test that bot_commands_total has correct labels."""
        # Labels are 'command' and 'status'
        assert "command" in bot_commands_total._labelnames
        assert "status" in bot_commands_total._labelnames

    def test_bot_errors_total_exists(self):
        """Test that bot_errors_total metric exists."""
        assert bot_errors_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "bot_errors" in bot_errors_total._name

    def test_bot_errors_total_has_labels(self):
        """Test that bot_errors_total has error_type label."""
        assert "error_type" in bot_errors_total._labelnames

    def test_bot_active_users_exists(self):
        """Test that bot_active_users gauge exists."""
        assert bot_active_users is not None
        assert bot_active_users._name == "bot_active_users"


class TestAPIMetrics:
    """Tests for API-related metrics."""

    def test_api_requests_total_exists(self):
        """Test that api_requests_total metric exists."""
        assert api_requests_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "dmarket_api_requests" in api_requests_total._name

    def test_api_requests_total_has_labels(self):
        """Test that api_requests_total has correct labels."""
        assert "endpoint" in api_requests_total._labelnames
        assert "method" in api_requests_total._labelnames
        assert "status_code" in api_requests_total._labelnames

    def test_api_request_duration_exists(self):
        """Test that api_request_duration histogram exists."""
        assert api_request_duration is not None
        assert api_request_duration._name == "dmarket_api_request_duration_seconds"

    def test_api_request_duration_has_labels(self):
        """Test that api_request_duration has correct labels."""
        assert "endpoint" in api_request_duration._labelnames
        assert "method" in api_request_duration._labelnames

    def test_api_request_duration_has_buckets(self):
        """Test that api_request_duration has defined buckets."""
        # Buckets are defined in the histogram
        assert api_request_duration._upper_bounds is not None

    def test_api_errors_total_exists(self):
        """Test that api_errors_total metric exists."""
        assert api_errors_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "dmarket_api_errors" in api_errors_total._name


class TestDatabaseMetrics:
    """Tests for database-related metrics."""

    def test_db_connections_active_exists(self):
        """Test that db_connections_active gauge exists."""
        assert db_connections_active is not None
        assert db_connections_active._name == "db_connections_active"

    def test_db_query_duration_exists(self):
        """Test that db_query_duration histogram exists."""
        assert db_query_duration is not None
        assert db_query_duration._name == "db_query_duration_seconds"

    def test_db_query_duration_has_labels(self):
        """Test that db_query_duration has query_type label."""
        assert "query_type" in db_query_duration._labelnames

    def test_db_errors_total_exists(self):
        """Test that db_errors_total counter exists."""
        assert db_errors_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "db_errors" in db_errors_total._name


class TestArbitrageMetrics:
    """Tests for arbitrage-related metrics."""

    def test_arbitrage_opportunities_found_exists(self):
        """Test that arbitrage_opportunities_found counter exists."""
        assert arbitrage_opportunities_found is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "arbitrage_opportunities_found" in arbitrage_opportunities_found._name

    def test_arbitrage_opportunities_found_has_labels(self):
        """Test that arbitrage_opportunities_found has correct labels."""
        assert "game" in arbitrage_opportunities_found._labelnames
        assert "level" in arbitrage_opportunities_found._labelnames

    def test_arbitrage_opportunities_avg_exists(self):
        """Test that arbitrage_opportunities_avg gauge exists."""
        assert arbitrage_opportunities_avg is not None
        assert arbitrage_opportunities_avg._name == "arbitrage_opportunities_avg"

    def test_arbitrage_profit_avg_exists(self):
        """Test that arbitrage_profit_avg gauge exists."""
        assert arbitrage_profit_avg is not None
        assert arbitrage_profit_avg._name == "arbitrage_profit_avg_usd"


class TestTargetMetrics:
    """Tests for target-related metrics."""

    def test_targets_created_total_exists(self):
        """Test that targets_created_total counter exists."""
        assert targets_created_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "targets_created" in targets_created_total._name

    def test_targets_executed_total_exists(self):
        """Test that targets_executed_total counter exists."""
        assert targets_executed_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "targets_executed" in targets_executed_total._name

    def test_targets_active_exists(self):
        """Test that targets_active gauge exists."""
        assert targets_active is not None
        assert targets_active._name == "targets_active"

    def test_targets_have_game_label(self):
        """Test that target metrics have game label."""
        assert "game" in targets_created_total._labelnames
        assert "game" in targets_executed_total._labelnames
        assert "game" in targets_active._labelnames


class TestBusinessMetrics:
    """Tests for business-related metrics."""

    def test_total_profit_usd_exists(self):
        """Test that total_profit_usd gauge exists."""
        assert total_profit_usd is not None
        assert total_profit_usd._name == "total_profit_usd"

    def test_transactions_total_exists(self):
        """Test that transactions_total counter exists."""
        assert transactions_total is not None
        # Prometheus client strips "_total" suffix from Counter names
        assert "transactions" in transactions_total._name

    def test_transactions_total_has_labels(self):
        """Test that transactions_total has correct labels."""
        assert "type" in transactions_total._labelnames
        assert "status" in transactions_total._labelnames

    def test_transaction_amount_avg_exists(self):
        """Test that transaction_amount_avg gauge exists."""
        assert transaction_amount_avg is not None
        assert transaction_amount_avg._name == "transaction_amount_avg_usd"


class TestSystemMetrics:
    """Tests for system-related metrics."""

    def test_app_info_exists(self):
        """Test that app_info metric exists."""
        assert app_info is not None
        assert app_info._name == "app"

    def test_app_uptime_seconds_exists(self):
        """Test that app_uptime_seconds gauge exists."""
        assert app_uptime_seconds is not None
        assert app_uptime_seconds._name == "app_uptime_seconds"


class TestTrackCommand:
    """Tests for track_command utility function."""

    def test_track_command_success(self):
        """Test tracking successful command."""
        # Should not raise
        track_command("start", success=True)

    def test_track_command_failed(self):
        """Test tracking failed command."""
        # Should not raise
        track_command("arbitrage", success=False)

    def test_track_command_default_success(self):
        """Test that success defaults to True."""
        # Should not raise
        track_command("help")


class TestTrackApiRequest:
    """Tests for track_api_request utility function."""

    def test_track_api_request_basic(self):
        """Test tracking API request."""
        # Should not raise
        track_api_request(
            endpoint="/market/items",
            method="GET",
            status_code=200,
            duration=0.5,
        )

    def test_track_api_request_error(self):
        """Test tracking API request with error status."""
        # Should not raise
        track_api_request(
            endpoint="/market/buy",
            method="POST",
            status_code=500,
            duration=1.2,
        )

    def test_track_api_request_different_methods(self):
        """Test tracking API requests with different methods."""
        # Should not raise
        track_api_request("/items", "GET", 200, 0.1)
        track_api_request("/buy", "POST", 201, 0.2)
        track_api_request("/item/123", "DELETE", 204, 0.15)
        track_api_request("/settings", "PUT", 200, 0.3)


class TestTrackDbQuery:
    """Tests for track_db_query utility function."""

    def test_track_db_query_select(self):
        """Test tracking SELECT query."""
        # Should not raise
        track_db_query("SELECT", 0.005)

    def test_track_db_query_insert(self):
        """Test tracking INSERT query."""
        # Should not raise
        track_db_query("INSERT", 0.01)

    def test_track_db_query_update(self):
        """Test tracking UPDATE query."""
        # Should not raise
        track_db_query("UPDATE", 0.008)

    def test_track_db_query_delete(self):
        """Test tracking DELETE query."""
        # Should not raise
        track_db_query("DELETE", 0.003)


class TestTrackArbitrageScan:
    """Tests for track_arbitrage_scan utility function."""

    def test_track_arbitrage_scan_basic(self):
        """Test tracking arbitrage scan."""
        # Should not raise
        track_arbitrage_scan(
            game="csgo",
            level="standard",
            opportunities_count=10,
        )

    def test_track_arbitrage_scan_zero_opportunities(self):
        """Test tracking scan with no opportunities."""
        # Should not raise
        track_arbitrage_scan(
            game="dota2",
            level="advanced",
            opportunities_count=0,
        )

    def test_track_arbitrage_scan_different_games(self):
        """Test tracking scans for different games."""
        # Should not raise
        track_arbitrage_scan("csgo", "boost", 5)
        track_arbitrage_scan("dota2", "standard", 3)
        track_arbitrage_scan("tf2", "pro", 1)
        track_arbitrage_scan("rust", "medium", 8)


class TestSetActiveUsers:
    """Tests for set_active_users utility function."""

    def test_set_active_users_basic(self):
        """Test setting active users count."""
        # Should not raise
        set_active_users(100)

    def test_set_active_users_zero(self):
        """Test setting zero active users."""
        # Should not raise
        set_active_users(0)

    def test_set_active_users_large_number(self):
        """Test setting large number of active users."""
        # Should not raise
        set_active_users(10000)


class TestGetMetrics:
    """Tests for get_metrics utility function."""

    def test_get_metrics_returns_bytes(self):
        """Test that get_metrics returns bytes."""
        result = get_metrics()
        assert isinstance(result, bytes)

    def test_get_metrics_contains_metric_names(self):
        """Test that output contains some expected metric names."""
        result = get_metrics()
        decoded = result.decode("utf-8")

        # Should contain some of our defined metrics
        assert "bot_commands_total" in decoded or "dmarket_api" in decoded


class TestCreateMetricsApp:
    """Tests for create_metrics_app utility function."""

    def test_create_metrics_app_returns_app(self):
        """Test that create_metrics_app returns an ASGI app."""
        app = create_metrics_app()
        assert app is not None
        # ASGI apps are callable
        assert callable(app)


class TestTimer:
    """Tests for Timer context manager."""

    def test_timer_init(self):
        """Test Timer initialization."""
        timer = Timer()
        assert timer.start_time is None
        assert timer.elapsed is None

    def test_timer_context_manager(self):
        """Test Timer as context manager."""
        with Timer() as t:
            pass

        assert t.start_time is not None
        assert t.elapsed is not None
        assert t.elapsed >= 0

    def test_timer_measures_elapsed_time(self):
        """Test that Timer measures elapsed time."""
        import time

        with Timer() as t:
            time.sleep(0.01)  # Sleep 10ms

        # Should be at least 10ms
        assert t.elapsed >= 0.01

    def test_timer_returns_self(self):
        """Test that Timer __enter__ returns self."""
        timer = Timer()
        result = timer.__enter__()
        assert result is timer
        timer.__exit__(None, None, None)

    def test_timer_exit_returns_false(self):
        """Test that Timer __exit__ returns False."""
        timer = Timer()
        timer.__enter__()
        result = timer.__exit__(None, None, None)
        assert result is False

    def test_timer_does_not_suppress_exceptions(self):
        """Test that Timer does not suppress exceptions."""
        with pytest.raises(ValueError):
            with Timer() as t:
                raise ValueError("Test error")

        # Timer should still have recorded time
        assert t.elapsed is not None

    def test_timer_multiple_uses(self):
        """Test Timer can be used multiple times."""
        timer = Timer()

        with timer:
            pass
        first_elapsed = timer.elapsed

        with timer:
            pass
        second_elapsed = timer.elapsed

        # Both measurements should be valid
        assert first_elapsed >= 0
        assert second_elapsed >= 0


class TestMetricsLabels:
    """Tests for metric label combinations."""

    def test_bot_commands_total_label_values(self):
        """Test bot_commands_total with different label values."""
        # Test various command and status combinations
        bot_commands_total.labels(command="start", status="success")
        bot_commands_total.labels(command="arbitrage", status="failed")
        bot_commands_total.labels(command="help", status="success")

    def test_api_requests_total_label_values(self):
        """Test api_requests_total with different label values."""
        api_requests_total.labels(
            endpoint="/market/items",
            method="GET",
            status_code="200",
        )
        api_requests_total.labels(
            endpoint="/market/buy",
            method="POST",
            status_code="500",
        )

    def test_arbitrage_metrics_label_values(self):
        """Test arbitrage metrics with different label values."""
        arbitrage_opportunities_found.labels(game="csgo", level="boost")
        arbitrage_opportunities_found.labels(game="dota2", level="standard")
        arbitrage_opportunities_avg.labels(game="tf2")
        arbitrage_profit_avg.labels(game="rust")


class TestMetricTypes:
    """Tests for correct metric types."""

    def test_counters_are_counters(self):
        """Test that Counter metrics are correct type."""
        from prometheus_client import Counter

        assert isinstance(bot_commands_total, Counter)
        assert isinstance(bot_errors_total, Counter)
        assert isinstance(api_requests_total, Counter)
        assert isinstance(api_errors_total, Counter)
        assert isinstance(db_errors_total, Counter)
        assert isinstance(arbitrage_opportunities_found, Counter)
        assert isinstance(targets_created_total, Counter)
        assert isinstance(targets_executed_total, Counter)
        assert isinstance(transactions_total, Counter)

    def test_gauges_are_gauges(self):
        """Test that Gauge metrics are correct type."""
        from prometheus_client import Gauge

        assert isinstance(bot_active_users, Gauge)
        assert isinstance(db_connections_active, Gauge)
        assert isinstance(arbitrage_opportunities_avg, Gauge)
        assert isinstance(arbitrage_profit_avg, Gauge)
        assert isinstance(targets_active, Gauge)
        assert isinstance(total_profit_usd, Gauge)
        assert isinstance(transaction_amount_avg, Gauge)
        assert isinstance(app_uptime_seconds, Gauge)

    def test_histograms_are_histograms(self):
        """Test that Histogram metrics are correct type."""
        from prometheus_client import Histogram

        assert isinstance(api_request_duration, Histogram)
        assert isinstance(db_query_duration, Histogram)

    def test_info_is_info(self):
        """Test that Info metric is correct type."""
        from prometheus_client import Info

        assert isinstance(app_info, Info)

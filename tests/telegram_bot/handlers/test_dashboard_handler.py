"""Unit tests for src/telegram_bot/handlers/dashboard_handler.py.

Tests for ScannerDashboard including:
- Initialization
- Scan result management
- User statistics
- Dashboard display
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestScannerDashboardInit:
    """Tests for ScannerDashboard initialization."""

    def test_init_creates_empty_active_scans(self):
        """Test initialization creates empty active scans dict."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard

        dashboard = ScannerDashboard()

        assert dashboard.active_scans == {}

    def test_init_creates_empty_scan_history(self):
        """Test initialization creates empty scan history."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard

        dashboard = ScannerDashboard()

        assert dashboard.scan_history == []

    def test_init_sets_max_history(self):
        """Test initialization sets max history value."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard

        dashboard = ScannerDashboard()

        assert dashboard.max_history == 50


class TestScannerDashboardAddScanResult:
    """Tests for add_scan_result method."""

    @pytest.fixture()
    def dashboard(self):
        """Create ScannerDashboard instance."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        return ScannerDashboard()

    def test_add_scan_result_basic(self, dashboard):
        """Test adding a basic scan result."""
        user_id = 123456
        scan_data = {
            "level": "standard",
            "opportunities": [{"item": "test", "profit": 5.0}]
        }

        dashboard.add_scan_result(user_id, scan_data)

        assert len(dashboard.scan_history) == 1
        assert dashboard.scan_history[0]["user_id"] == user_id
        assert dashboard.scan_history[0]["data"] == scan_data

    def test_add_scan_result_has_timestamp(self, dashboard):
        """Test scan result has timestamp."""
        dashboard.add_scan_result(123456, {})

        assert "timestamp" in dashboard.scan_history[0]
        assert isinstance(dashboard.scan_history[0]["timestamp"], datetime)

    def test_add_scan_result_inserts_at_front(self, dashboard):
        """Test new results are inserted at front."""
        dashboard.add_scan_result(111, {"order": 1})
        dashboard.add_scan_result(222, {"order": 2})
        dashboard.add_scan_result(333, {"order": 3})

        assert dashboard.scan_history[0]["user_id"] == 333
        assert dashboard.scan_history[1]["user_id"] == 222
        assert dashboard.scan_history[2]["user_id"] == 111

    def test_add_scan_result_respects_max_history(self, dashboard):
        """Test max history limit is respected."""
        dashboard.max_history = 3

        for i in range(5):
            dashboard.add_scan_result(i, {"index": i})

        assert len(dashboard.scan_history) == 3
        # Most recent should be kept
        assert dashboard.scan_history[0]["user_id"] == 4
        assert dashboard.scan_history[1]["user_id"] == 3
        assert dashboard.scan_history[2]["user_id"] == 2


class TestScannerDashboardGetUserStats:
    """Tests for get_user_stats method."""

    @pytest.fixture()
    def dashboard(self):
        """Create ScannerDashboard instance."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        return ScannerDashboard()

    def test_get_user_stats_empty_history(self, dashboard):
        """Test stats for user with no history."""
        stats = dashboard.get_user_stats(123456)

        assert stats["total_scans"] == 0
        assert stats["total_opportunities"] == 0

    def test_get_user_stats_with_scans(self, dashboard):
        """Test stats for user with scan history."""
        user_id = 123456

        dashboard.add_scan_result(user_id, {
            "opportunities": [
                {"profit": 5.0},
                {"profit": 10.0}
            ]
        })
        dashboard.add_scan_result(user_id, {
            "opportunities": [
                {"profit": 15.0}
            ]
        })

        stats = dashboard.get_user_stats(user_id)

        assert stats["total_scans"] == 2
        assert stats["total_opportunities"] == 3

    def test_get_user_stats_calculates_avg_profit(self, dashboard):
        """Test average profit calculation."""
        user_id = 123456

        dashboard.add_scan_result(user_id, {
            "opportunities": [
                {"profit": 10.0},
                {"profit": 20.0},
                {"profit": 30.0}
            ]
        })

        stats = dashboard.get_user_stats(user_id)

        assert stats["avg_profit"] == 20.0  # (10 + 20 + 30) / 3

    def test_get_user_stats_calculates_max_profit(self, dashboard):
        """Test max profit calculation."""
        user_id = 123456

        dashboard.add_scan_result(user_id, {
            "opportunities": [
                {"profit": 5.0},
                {"profit": 25.0},
                {"profit": 15.0}
            ]
        })

        stats = dashboard.get_user_stats(user_id)

        assert stats["max_profit"] == 25.0

    def test_get_user_stats_last_scan_time(self, dashboard):
        """Test last scan time is tracked."""
        user_id = 123456

        dashboard.add_scan_result(user_id, {"opportunities": []})

        stats = dashboard.get_user_stats(user_id)

        assert stats["last_scan_time"] is not None
        assert isinstance(stats["last_scan_time"], datetime)

    def test_get_user_stats_filters_by_user(self, dashboard):
        """Test stats only include user's scans."""
        user_1 = 111
        user_2 = 222

        dashboard.add_scan_result(user_1, {
            "opportunities": [{"profit": 10.0}]
        })
        dashboard.add_scan_result(user_2, {
            "opportunities": [{"profit": 100.0}, {"profit": 200.0}]
        })

        stats_1 = dashboard.get_user_stats(user_1)
        stats_2 = dashboard.get_user_stats(user_2)

        assert stats_1["total_scans"] == 1
        assert stats_1["total_opportunities"] == 1
        assert stats_2["total_scans"] == 1
        assert stats_2["total_opportunities"] == 2


class TestDashboardConstants:
    """Tests for dashboard constants."""

    def test_dashboard_action_constants_defined(self):
        """Test dashboard action constants are defined."""
        from src.telegram_bot.handlers.dashboard_handler import (
            DASHBOARD_ACTION,
            DASHBOARD_STATS,
            DASHBOARD_SCANNER,
            DASHBOARD_ACTIVE_SCANS,
            DASHBOARD_HISTORY,
            DASHBOARD_REFRESH,
            DASHBOARD_CHARTS,
        )

        assert DASHBOARD_ACTION == "dashboard"
        assert DASHBOARD_STATS == "dashboard_stats"
        assert DASHBOARD_SCANNER == "dashboard_scanner"
        assert DASHBOARD_ACTIVE_SCANS == "dashboard_active"
        assert DASHBOARD_HISTORY == "dashboard_history"
        assert DASHBOARD_REFRESH == "dashboard_refresh"
        assert DASHBOARD_CHARTS == "dashboard_charts"


class TestScannerDashboardActiveScans:
    """Tests for active scans management."""

    @pytest.fixture()
    def dashboard(self):
        """Create ScannerDashboard instance."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        return ScannerDashboard()

    def test_add_active_scan(self, dashboard):
        """Test adding an active scan."""
        user_id = 123456
        scan_info = {
            "level": "standard",
            "start_time": datetime.now(),
            "status": "running"
        }

        dashboard.active_scans[user_id] = scan_info

        assert user_id in dashboard.active_scans
        assert dashboard.active_scans[user_id]["level"] == "standard"

    def test_remove_active_scan(self, dashboard):
        """Test removing an active scan."""
        user_id = 123456
        dashboard.active_scans[user_id] = {"level": "standard"}

        del dashboard.active_scans[user_id]

        assert user_id not in dashboard.active_scans

    def test_update_active_scan(self, dashboard):
        """Test updating an active scan."""
        user_id = 123456
        dashboard.active_scans[user_id] = {"status": "running"}

        dashboard.active_scans[user_id]["status"] = "completed"

        assert dashboard.active_scans[user_id]["status"] == "completed"


class TestScannerDashboardEdgeCases:
    """Tests for edge cases in ScannerDashboard."""

    @pytest.fixture()
    def dashboard(self):
        """Create ScannerDashboard instance."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard
        return ScannerDashboard()

    def test_empty_opportunities_list(self, dashboard):
        """Test handling empty opportunities list."""
        dashboard.add_scan_result(123456, {"opportunities": []})

        stats = dashboard.get_user_stats(123456)

        assert stats["total_opportunities"] == 0
        assert stats["avg_profit"] == 0.0
        assert stats["max_profit"] == 0.0

    def test_missing_opportunities_key(self, dashboard):
        """Test handling missing opportunities key."""
        dashboard.add_scan_result(123456, {})

        stats = dashboard.get_user_stats(123456)

        assert stats["total_opportunities"] == 0

    def test_opportunity_without_profit(self, dashboard):
        """Test handling opportunity without profit field."""
        dashboard.add_scan_result(123456, {
            "opportunities": [{"item": "test"}]
        })

        stats = dashboard.get_user_stats(123456)

        # Should use 0.0 as default profit
        assert stats["avg_profit"] == 0.0

    def test_negative_profit_values(self, dashboard):
        """Test handling negative profit values."""
        dashboard.add_scan_result(123456, {
            "opportunities": [
                {"profit": -5.0},
                {"profit": 10.0}
            ]
        })

        stats = dashboard.get_user_stats(123456)

        assert stats["avg_profit"] == 2.5  # (-5 + 10) / 2


class TestScannerDashboardIntegration:
    """Integration tests for ScannerDashboard."""

    def test_complete_scan_workflow(self):
        """Test complete scan workflow."""
        from src.telegram_bot.handlers.dashboard_handler import ScannerDashboard

        dashboard = ScannerDashboard()
        user_id = 123456

        # Start scan
        dashboard.active_scans[user_id] = {
            "level": "standard",
            "status": "running",
            "start_time": datetime.now()
        }

        # Verify active scan
        assert user_id in dashboard.active_scans

        # Complete scan with results
        scan_result = {
            "level": "standard",
            "opportunities": [
                {"item": "Item 1", "profit": 15.0},
                {"item": "Item 2", "profit": 25.0}
            ]
        }

        # Remove from active
        del dashboard.active_scans[user_id]

        # Add to history
        dashboard.add_scan_result(user_id, scan_result)

        # Verify
        assert user_id not in dashboard.active_scans
        assert len(dashboard.scan_history) == 1

        stats = dashboard.get_user_stats(user_id)
        assert stats["total_scans"] == 1
        assert stats["total_opportunities"] == 2
        assert stats["avg_profit"] == 20.0
        assert stats["max_profit"] == 25.0

"""Tests for pool_monitor module.

This module tests the PoolMonitor class for connection pool
monitoring and management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.pool_monitor import PoolMonitor


class TestPoolMonitor:
    """Tests for PoolMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create PoolMonitor instance."""
        return PoolMonitor()

    def test_init(self, monitor):
        """Test initialization."""
        assert monitor is not None

    def test_init_with_options(self):
        """Test initialization with options."""
        monitor = PoolMonitor(
            check_interval=30,
            max_connections=100,
        )

        assert monitor.check_interval == 30
        assert monitor.max_connections == 100

    def test_register_pool(self, monitor):
        """Test registering connection pool."""
        pool = MagicMock()
        pool.size = 10

        monitor.register_pool("database", pool)

        assert "database" in monitor.pools

    def test_unregister_pool(self, monitor):
        """Test unregistering connection pool."""
        pool = MagicMock()
        monitor.pools["database"] = pool

        monitor.unregister_pool("database")

        assert "database" not in monitor.pools

    def test_get_pool_status(self, monitor):
        """Test getting pool status."""
        pool = MagicMock()
        pool.size = 10
        pool.checkedout = 3
        pool.overflow = 0
        monitor.pools["database"] = pool

        status = monitor.get_pool_status("database")

        assert status["size"] == 10
        assert status["in_use"] == 3

    def test_get_all_status(self, monitor):
        """Test getting all pools status."""
        pool1 = MagicMock()
        pool1.size = 10
        pool2 = MagicMock()
        pool2.size = 5

        monitor.pools["db1"] = pool1
        monitor.pools["db2"] = pool2

        status = monitor.get_all_status()

        assert "db1" in status
        assert "db2" in status

    @pytest.mark.asyncio
    async def test_check_health(self, monitor):
        """Test health check."""
        pool = MagicMock()
        pool.size = 10
        pool.checkedout = 3
        monitor.pools["database"] = pool

        health = await monitor.check_health()

        assert health["healthy"] is True

    @pytest.mark.asyncio
    async def test_check_health_unhealthy(self, monitor):
        """Test unhealthy pool detection."""
        pool = MagicMock()
        pool.size = 10
        pool.checkedout = 10  # All connections in use
        pool.overflow = 5
        monitor.pools["database"] = pool

        health = await monitor.check_health()

        assert health["healthy"] is False or health["warnings"]

    def test_get_metrics(self, monitor):
        """Test getting metrics."""
        pool = MagicMock()
        pool.size = 10
        pool.checkedout = 3
        monitor.pools["database"] = pool

        metrics = monitor.get_metrics()

        assert "total_pools" in metrics
        assert "total_connections" in metrics

    @pytest.mark.asyncio
    async def test_cleanup_idle_connections(self, monitor):
        """Test cleaning up idle connections."""
        pool = MagicMock()
        pool.dispose = MagicMock()
        monitor.pools["database"] = pool

        await monitor.cleanup_idle_connections()

        # Should not raise

    def test_set_max_connections(self, monitor):
        """Test setting max connections."""
        monitor.set_max_connections(50)
        assert monitor.max_connections == 50

    def test_get_connection_stats(self, monitor):
        """Test getting connection statistics."""
        pool = MagicMock()
        pool.size = 10
        pool.checkedout = 3
        pool.checkedin = 7
        monitor.pools["database"] = pool

        stats = monitor.get_connection_stats("database")

        assert "total" in stats
        assert "in_use" in stats
        assert "available" in stats

    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """Test starting monitoring."""
        await monitor.start()
        assert monitor.is_running is True

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor):
        """Test stopping monitoring."""
        monitor.is_running = True
        await monitor.stop()
        assert monitor.is_running is False

    def test_add_alert_handler(self, monitor):
        """Test adding alert handler."""
        handler = MagicMock()

        monitor.add_alert_handler(handler)

        assert handler in monitor.alert_handlers

    @pytest.mark.asyncio
    async def test_trigger_alert(self, monitor):
        """Test triggering alert."""
        handler = AsyncMock()
        monitor.alert_handlers.append(handler)

        await monitor._trigger_alert("Pool exhausted", "database")

        handler.assert_called_once()

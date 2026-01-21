"""Tests for Skill Profiler module."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.utils.skill_profiler import (
    ProfileResult,
    SkillMetrics,
    SkillProfiler,
    get_profiler,
    profile_skill,
    reset_profiler,
)


@pytest.fixture
def profiler():
    """Create a fresh profiler instance."""
    reset_profiler()
    return SkillProfiler(enable_memory_tracking=False)


class TestSkillMetrics:
    """Test cases for SkillMetrics dataclass."""

    def test_metrics_initialization(self):
        """Test metrics default initialization."""
        metrics = SkillMetrics(skill_name="test_skill")

        assert metrics.skill_name == "test_skill"
        assert metrics.total_executions == 0
        assert metrics.latency_avg_ms == 0.0
        assert metrics.throughput_per_sec == 0.0

    def test_metrics_to_dict(self):
        """Test conversion to dictionary."""
        metrics = SkillMetrics(
            skill_name="test_skill",
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
            latency_avg_ms=25.5,
        )

        result = metrics.to_dict()

        assert result["skill_name"] == "test_skill"
        assert result["total_executions"] == 100
        assert result["success_rate"] == 95.0
        assert result["latency_avg_ms"] == 25.5


class TestSkillProfiler:
    """Test cases for SkillProfiler."""

    def test_profiler_initialization(self, profiler):
        """Test profiler initialization."""
        assert len(profiler.skills_metrics) == 0
        assert profiler.max_samples == 10000

    def test_record_execution(self, profiler):
        """Test recording execution manually."""
        result = profiler.record(
            skill_name="test_skill",
            latency_ms=50.0,
            success=True,
            items_count=10,
        )

        assert isinstance(result, ProfileResult)
        assert result.skill_name == "test_skill"
        assert result.success is True
        assert result.latency_ms == 50.0

        # Check metrics updated
        metrics = profiler.get_skill_metrics("test_skill")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["items_processed"] == 10

    def test_record_multiple_executions(self, profiler):
        """Test recording multiple executions updates stats."""
        profiler.record("skill", latency_ms=10.0, success=True)
        profiler.record("skill", latency_ms=20.0, success=True)
        profiler.record("skill", latency_ms=30.0, success=False)

        metrics = profiler.get_skill_metrics("skill")
        assert metrics["total_executions"] == 3
        assert metrics["successful_executions"] == 2
        assert metrics["failed_executions"] == 1
        assert metrics["latency_avg_ms"] == 20.0

    def test_context_manager_success(self, profiler):
        """Test synchronous context manager on success."""
        with profiler.profile("test_skill", "process", items_count=5):
            _ = sum(range(1000))  # Some work

        metrics = profiler.get_skill_metrics("test_skill")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["items_processed"] == 5
        assert metrics["latency_avg_ms"] > 0

    def test_context_manager_failure(self, profiler):
        """Test synchronous context manager on failure."""
        with pytest.raises(ValueError):
            with profiler.profile("test_skill"):
                raise ValueError("Test error")

        metrics = profiler.get_skill_metrics("test_skill")
        assert metrics["failed_executions"] == 1

    @pytest.mark.asyncio
    async def test_async_context_manager_success(self, profiler):
        """Test async context manager on success."""
        async with profiler.aprofile("async_skill", "analyze"):
            await asyncio.sleep(0.01)

        metrics = profiler.get_skill_metrics("async_skill")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["latency_avg_ms"] >= 10.0  # At least 10ms

    @pytest.mark.asyncio
    async def test_async_context_manager_failure(self, profiler):
        """Test async context manager on failure."""
        with pytest.raises(RuntimeError):
            async with profiler.aprofile("async_skill"):
                raise RuntimeError("Async error")

        metrics = profiler.get_skill_metrics("async_skill")
        assert metrics["failed_executions"] == 1


class TestLatencyPercentiles:
    """Test cases for latency percentile calculations."""

    def test_percentile_calculation(self, profiler):
        """Test latency percentiles are calculated correctly."""
        # Add 100 samples with known latencies
        for i in range(100):
            profiler.record("skill", latency_ms=float(i), success=True)

        metrics = profiler.get_skill_metrics("skill")

        # P50 should be around 50
        assert 45 <= metrics["latency_p50_ms"] <= 55
        # P95 should be around 95
        assert 90 <= metrics["latency_p95_ms"] <= 99
        # P99 should be around 99
        assert 95 <= metrics["latency_p99_ms"] <= 99

    def test_min_max_latency(self, profiler):
        """Test min/max latency tracking."""
        profiler.record("skill", latency_ms=10.0, success=True)
        profiler.record("skill", latency_ms=50.0, success=True)
        profiler.record("skill", latency_ms=100.0, success=True)

        metrics = profiler.get_skill_metrics("skill")
        assert metrics["latency_min_ms"] == 10.0
        assert metrics["latency_max_ms"] == 100.0


class TestThroughput:
    """Test cases for throughput calculation."""

    def test_throughput_calculation(self, profiler):
        """Test throughput is calculated correctly."""
        # 100 items in 100ms = 1000 items/sec
        profiler.record("skill", latency_ms=100.0, success=True, items_count=100)

        metrics = profiler.get_skill_metrics("skill")
        assert metrics["throughput_per_sec"] == 1000.0

    def test_throughput_multiple_executions(self, profiler):
        """Test throughput with multiple executions."""
        # 10 items in 100ms = 100/sec
        # 20 items in 200ms = 100/sec
        # Total: 30 items in 300ms = 100 items/sec
        profiler.record("skill", latency_ms=100.0, success=True, items_count=10)
        profiler.record("skill", latency_ms=200.0, success=True, items_count=20)

        metrics = profiler.get_skill_metrics("skill")
        assert metrics["throughput_per_sec"] == 100.0


class TestBottleneckDetection:
    """Test cases for bottleneck detection."""

    def test_high_latency_bottleneck(self, profiler):
        """Test detection of high latency bottleneck."""
        # Add slow executions
        for _ in range(10):
            profiler.record("slow_skill", latency_ms=200.0, success=True)

        bottlenecks = profiler.identify_bottlenecks(latency_threshold_ms=100.0)

        assert len(bottlenecks) >= 1
        assert any(b["skill_name"] == "slow_skill" for b in bottlenecks)
        assert any(b["issue"] == "high_latency" for b in bottlenecks)

    def test_high_failure_rate_bottleneck(self, profiler):
        """Test detection of high failure rate bottleneck."""
        # Add mostly failed executions
        for _ in range(5):
            profiler.record("failing_skill", latency_ms=10.0, success=True)
        for _ in range(10):
            profiler.record("failing_skill", latency_ms=10.0, success=False)

        bottlenecks = profiler.identify_bottlenecks()

        assert any(b["issue"] == "high_failure_rate" for b in bottlenecks)


class TestSummary:
    """Test cases for profiler summary."""

    def test_get_summary(self, profiler):
        """Test getting profiler summary."""
        profiler.record("skill1", latency_ms=10.0, success=True)
        profiler.record("skill2", latency_ms=20.0, success=True)
        profiler.record("skill2", latency_ms=30.0, success=False)

        summary = profiler.get_summary()

        assert summary["total_skills_profiled"] == 2
        assert summary["total_executions"] == 3
        assert summary["total_successes"] == 2
        assert "skill1" in summary["skills"]
        assert "skill2" in summary["skills"]

    def test_get_all_metrics(self, profiler):
        """Test getting metrics for all skills."""
        profiler.record("skill1", latency_ms=10.0, success=True)
        profiler.record("skill2", latency_ms=20.0, success=True)

        all_metrics = profiler.get_all_metrics()

        assert "skill1" in all_metrics
        assert "skill2" in all_metrics
        assert all_metrics["skill1"]["total_executions"] == 1


class TestResetMetrics:
    """Test cases for resetting metrics."""

    def test_reset_single_skill(self, profiler):
        """Test resetting metrics for a single skill."""
        profiler.record("skill1", latency_ms=10.0, success=True)
        profiler.record("skill2", latency_ms=20.0, success=True)

        profiler.reset_metrics("skill1")

        metrics1 = profiler.get_skill_metrics("skill1")
        metrics2 = profiler.get_skill_metrics("skill2")

        assert metrics1["total_executions"] == 0
        assert metrics2["total_executions"] == 1

    def test_reset_all_metrics(self, profiler):
        """Test resetting all metrics."""
        profiler.record("skill1", latency_ms=10.0, success=True)
        profiler.record("skill2", latency_ms=20.0, success=True)

        profiler.reset_metrics()

        assert len(profiler.skills_metrics) == 0


class TestProfileSkillDecorator:
    """Test cases for @profile_skill decorator."""

    @pytest.mark.asyncio
    async def test_async_function_decorator(self):
        """Test decorator on async function."""
        reset_profiler()

        @profile_skill("decorated_async_skill")
        async def async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await async_function()

        assert result == "async_result"

        profiler = get_profiler()
        metrics = profiler.get_skill_metrics("decorated_async_skill")
        assert metrics["total_executions"] == 1

    def test_sync_function_decorator(self):
        """Test decorator on sync function."""
        reset_profiler()

        @profile_skill("decorated_sync_skill")
        def sync_function():
            return "sync_result"

        result = sync_function()

        assert result == "sync_result"

        profiler = get_profiler()
        metrics = profiler.get_skill_metrics("decorated_sync_skill")
        assert metrics["total_executions"] == 1


class TestGlobalProfiler:
    """Test cases for global profiler instance."""

    def test_get_profiler_creates_singleton(self):
        """Test get_profiler returns singleton."""
        reset_profiler()

        p1 = get_profiler()
        p2 = get_profiler()

        assert p1 is p2

    def test_reset_profiler(self):
        """Test reset clears global instance."""
        p1 = get_profiler()
        p1.record("skill", latency_ms=10.0, success=True)

        reset_profiler()
        p2 = get_profiler()

        assert p1 is not p2
        assert len(p2.skills_metrics) == 0

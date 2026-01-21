"""Tests for Skill Orchestrator module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.utils.skill_orchestrator import (
    PipelineResult,
    PipelineStatus,
    SkillExecutionResult,
    SkillOrchestrator,
    get_orchestrator,
    reset_orchestrator,
)


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator instance."""
    reset_orchestrator()
    return SkillOrchestrator()


@pytest.fixture
def mock_sync_skill():
    """Create a mock synchronous skill."""
    skill = MagicMock()
    skill.process.return_value = {"result": "sync_processed"}
    skill.transform.return_value = "transformed"
    return skill


@pytest.fixture
def mock_async_skill():
    """Create a mock async skill."""
    skill = MagicMock()
    skill.analyze = AsyncMock(return_value={"analysis": "complete"})
    skill.predict = AsyncMock(return_value={"prediction": 0.95})
    return skill


class TestSkillOrchestrator:
    """Test cases for SkillOrchestrator."""

    def test_init_creates_empty_orchestrator(self, orchestrator):
        """Test initialization creates empty orchestrator."""
        assert len(orchestrator.skills) == 0
        assert len(orchestrator.pipelines) == 0
        assert orchestrator._metrics["total_executions"] == 0

    def test_register_skill(self, orchestrator, mock_sync_skill):
        """Test skill registration."""
        orchestrator.register_skill("test_skill", mock_sync_skill)

        assert "test_skill" in orchestrator.skills
        assert orchestrator.skills["test_skill"] == mock_sync_skill
        assert "test_skill" in orchestrator._metrics["skill_metrics"]

    def test_unregister_skill(self, orchestrator, mock_sync_skill):
        """Test skill unregistration."""
        orchestrator.register_skill("test_skill", mock_sync_skill)
        result = orchestrator.unregister_skill("test_skill")

        assert result is True
        assert "test_skill" not in orchestrator.skills

    def test_unregister_nonexistent_skill(self, orchestrator):
        """Test unregistering non-existent skill returns False."""
        result = orchestrator.unregister_skill("nonexistent")
        assert result is False

    def test_list_skills(self, orchestrator, mock_sync_skill, mock_async_skill):
        """Test listing registered skills."""
        orchestrator.register_skill("sync_skill", mock_sync_skill)
        orchestrator.register_skill("async_skill", mock_async_skill)

        skills = orchestrator.list_skills()
        assert "sync_skill" in skills
        assert "async_skill" in skills
        assert len(skills) == 2

    def test_register_pipeline(self, orchestrator):
        """Test pipeline registration."""
        steps = [
            {"skill": "skill1", "method": "process"},
            {"skill": "skill2", "method": "transform", "args": ["$prev"]},
        ]

        orchestrator.register_pipeline("test_pipeline", steps)

        assert "test_pipeline" in orchestrator.pipelines
        assert len(orchestrator.pipelines["test_pipeline"]) == 2


class TestSkillExecution:
    """Test cases for skill execution."""

    @pytest.mark.asyncio
    async def test_execute_sync_skill(self, orchestrator, mock_sync_skill):
        """Test executing a synchronous skill."""
        orchestrator.register_skill("sync_skill", mock_sync_skill)

        result = await orchestrator.execute_skill(
            skill_name="sync_skill",
            method_name="process",
            args=["input_data"],
        )

        assert isinstance(result, SkillExecutionResult)
        assert result.success is True
        assert result.result == {"result": "sync_processed"}
        assert result.skill_name == "sync_skill"
        mock_sync_skill.process.assert_called_once_with("input_data")

    @pytest.mark.asyncio
    async def test_execute_async_skill(self, orchestrator, mock_async_skill):
        """Test executing an asynchronous skill."""
        orchestrator.register_skill("async_skill", mock_async_skill)

        result = await orchestrator.execute_skill(
            skill_name="async_skill",
            method_name="analyze",
            args=["item_data"],
        )

        assert result.success is True
        assert result.result == {"analysis": "complete"}
        mock_async_skill.analyze.assert_called_once_with("item_data")

    @pytest.mark.asyncio
    async def test_execute_nonexistent_skill(self, orchestrator):
        """Test executing non-existent skill returns error."""
        result = await orchestrator.execute_skill(
            skill_name="nonexistent",
            method_name="process",
        )

        assert result.success is False
        assert "not registered" in result.error

    @pytest.mark.asyncio
    async def test_execute_nonexistent_method(self, orchestrator):
        """Test executing non-existent method returns error for real object."""
        # Use a real object without the method, not a MagicMock
        class RealSkill:
            def process(self):
                return "processed"

        orchestrator.register_skill("skill", RealSkill())

        result = await orchestrator.execute_skill(
            skill_name="skill",
            method_name="nonexistent_method",
        )

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execution_timeout(self, orchestrator):
        """Test execution timeout handling."""
        # Create a slow skill
        async def slow_method():
            await asyncio.sleep(5)
            return "done"

        slow_skill = MagicMock()
        slow_skill.slow = slow_method

        orchestrator.register_skill("slow_skill", slow_skill)

        result = await orchestrator.execute_skill(
            skill_name="slow_skill",
            method_name="slow",
            timeout_seconds=0.1,
        )

        assert result.success is False
        assert "timeout" in result.error.lower()


class TestPipelineExecution:
    """Test cases for pipeline execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_pipeline(
        self, orchestrator, mock_sync_skill, mock_async_skill
    ):
        """Test executing a simple pipeline."""
        orchestrator.register_skill("sync_skill", mock_sync_skill)
        orchestrator.register_skill("async_skill", mock_async_skill)

        pipeline = [
            {"skill": "sync_skill", "method": "process", "args": ["input"]},
            {"skill": "async_skill", "method": "analyze", "args": ["$prev"]},
        ]

        result = await orchestrator.execute_pipeline(pipeline)

        assert isinstance(result, PipelineResult)
        assert result.status == PipelineStatus.COMPLETED
        assert result.steps_executed == 2
        assert result.steps_total == 2
        assert len(result.step_results) == 2

    @pytest.mark.asyncio
    async def test_pipeline_context_passing(self, orchestrator, mock_sync_skill):
        """Test context passing in pipeline."""
        orchestrator.register_skill("skill", mock_sync_skill)

        pipeline = [
            {"skill": "skill", "method": "process", "args": ["$context.item_name"]},
        ]

        result = await orchestrator.execute_pipeline(
            pipeline,
            initial_context={"item_name": "AK-47"},
        )

        assert result.status == PipelineStatus.COMPLETED
        mock_sync_skill.process.assert_called_once_with("AK-47")

    @pytest.mark.asyncio
    async def test_pipeline_stops_on_failure(self, orchestrator, mock_sync_skill):
        """Test pipeline stops on failure when stop_on_failure=True."""
        mock_sync_skill.process.side_effect = ValueError("Test error")
        orchestrator.register_skill("skill", mock_sync_skill)

        pipeline = [
            {"skill": "skill", "method": "process"},
            {"skill": "skill", "method": "transform"},  # Should not execute
        ]

        result = await orchestrator.execute_pipeline(pipeline, stop_on_failure=True)

        assert result.status == PipelineStatus.FAILED
        assert result.steps_executed == 1
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_pipeline_continues_on_failure(self, orchestrator, mock_sync_skill):
        """Test pipeline continues when stop_on_failure=False."""
        mock_sync_skill.process.side_effect = ValueError("Test error")
        mock_sync_skill.transform.return_value = "transformed"
        orchestrator.register_skill("skill", mock_sync_skill)

        pipeline = [
            {"skill": "skill", "method": "process"},
            {"skill": "skill", "method": "transform"},
        ]

        result = await orchestrator.execute_pipeline(pipeline, stop_on_failure=False)

        assert result.status == PipelineStatus.PARTIALLY_FAILED
        assert result.steps_executed == 2

    @pytest.mark.asyncio
    async def test_execute_registered_pipeline(
        self, orchestrator, mock_sync_skill
    ):
        """Test executing a pre-registered pipeline by name."""
        orchestrator.register_skill("skill", mock_sync_skill)

        steps = [
            {"skill": "skill", "method": "process"},
        ]
        orchestrator.register_pipeline("my_pipeline", steps)

        result = await orchestrator.execute_pipeline("my_pipeline")

        assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_unknown_pipeline(self, orchestrator):
        """Test executing unknown pipeline returns error."""
        result = await orchestrator.execute_pipeline("unknown_pipeline")

        assert result.status == PipelineStatus.FAILED
        assert "not registered" in result.error


class TestParallelExecution:
    """Test cases for parallel skill execution."""

    @pytest.mark.asyncio
    async def test_execute_parallel_skills(
        self, orchestrator, mock_async_skill
    ):
        """Test executing multiple skills in parallel."""
        mock_async_skill.analyze = AsyncMock(return_value={"result": 1})
        mock_async_skill.predict = AsyncMock(return_value={"result": 2})
        orchestrator.register_skill("skill", mock_async_skill)

        skill_calls = [
            {"skill": "skill", "method": "analyze"},
            {"skill": "skill", "method": "predict"},
        ]

        results = await orchestrator.execute_parallel(skill_calls)

        assert len(results) == 2
        assert all(r.success for r in results)


class TestMetrics:
    """Test cases for metrics collection."""

    @pytest.mark.asyncio
    async def test_metrics_updated_on_execution(self, orchestrator, mock_sync_skill):
        """Test metrics are updated after execution."""
        orchestrator.register_skill("skill", mock_sync_skill)

        await orchestrator.execute_skill("skill", "process")
        await orchestrator.execute_skill("skill", "transform")

        metrics = orchestrator.get_metrics()
        assert metrics["total_executions"] == 2
        assert metrics["successful_executions"] == 2

        skill_metrics = orchestrator.get_skill_metrics("skill")
        assert skill_metrics["executions"] == 2

    @pytest.mark.asyncio
    async def test_metrics_track_failures(self, orchestrator, mock_sync_skill):
        """Test metrics track failed executions."""
        mock_sync_skill.process.side_effect = Exception("Error")
        orchestrator.register_skill("skill", mock_sync_skill)

        await orchestrator.execute_skill("skill", "process")

        metrics = orchestrator.get_metrics()
        assert metrics["failed_executions"] == 1

    def test_reset_metrics(self, orchestrator, mock_sync_skill):
        """Test resetting metrics."""
        orchestrator.register_skill("skill", mock_sync_skill)
        orchestrator._metrics["total_executions"] = 100

        orchestrator.reset_metrics()

        assert orchestrator._metrics["total_executions"] == 0


class TestGlobalOrchestrator:
    """Test cases for global orchestrator instance."""

    def test_get_orchestrator_creates_singleton(self):
        """Test get_orchestrator returns singleton."""
        reset_orchestrator()

        o1 = get_orchestrator()
        o2 = get_orchestrator()

        assert o1 is o2

    def test_reset_orchestrator(self):
        """Test reset clears global instance."""
        o1 = get_orchestrator()
        o1.register_skill("test", MagicMock())

        reset_orchestrator()
        o2 = get_orchestrator()

        assert o1 is not o2
        assert len(o2.skills) == 0

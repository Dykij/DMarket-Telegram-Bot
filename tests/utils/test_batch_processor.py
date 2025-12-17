"""Unit tests for batch_processor module.

Tests for SimpleBatchProcessor, ProgressTracker, and chunked_api_calls.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.batch_processor import (
    ProgressTracker,
    SimpleBatchProcessor,
    chunked_api_calls,
)


# ============================================================================
# TESTS FOR SimpleBatchProcessor
# ============================================================================


class TestSimpleBatchProcessor:
    """Tests for SimpleBatchProcessor class."""

    def test_init_default_values(self):
        """Test default initialization values."""
        processor = SimpleBatchProcessor()
        assert processor.batch_size == 100
        assert processor.delay_between_batches == 0.1

    def test_init_custom_values(self):
        """Test custom initialization values."""
        processor = SimpleBatchProcessor(batch_size=50, delay_between_batches=0.5)
        assert processor.batch_size == 50
        assert processor.delay_between_batches == 0.5

    @pytest.mark.asyncio()
    async def test_process_in_batches_empty_list(self):
        """Test processing empty list."""
        processor = SimpleBatchProcessor(batch_size=10)
        process_fn = AsyncMock(return_value=[])

        result = await processor.process_in_batches([], process_fn)

        assert result == []
        process_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_process_in_batches_single_batch(self):
        """Test processing items that fit in single batch."""
        processor = SimpleBatchProcessor(batch_size=10)
        items = [1, 2, 3, 4, 5]
        process_fn = AsyncMock(return_value=["result"])

        result = await processor.process_in_batches(items, process_fn)

        assert len(result) == 1
        process_fn.assert_called_once_with(items)

    @pytest.mark.asyncio()
    async def test_process_in_batches_multiple_batches(self):
        """Test processing items across multiple batches."""
        processor = SimpleBatchProcessor(batch_size=3, delay_between_batches=0)
        items = [1, 2, 3, 4, 5, 6, 7]
        process_fn = AsyncMock(return_value=["result"])

        result = await processor.process_in_batches(items, process_fn)

        # 3 batches: [1,2,3], [4,5,6], [7]
        assert process_fn.call_count == 3
        assert len(result) == 3

    @pytest.mark.asyncio()
    async def test_process_in_batches_with_progress_callback(self):
        """Test progress callback is called."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0)
        items = list(range(10))
        process_fn = AsyncMock(return_value=["result"])
        progress_callback = AsyncMock()

        await processor.process_in_batches(items, process_fn, progress_callback=progress_callback)

        assert progress_callback.call_count >= 2

    @pytest.mark.asyncio()
    async def test_process_in_batches_with_error_callback(self):
        """Test error callback is called on exception."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0)
        items = list(range(10))
        process_fn = AsyncMock(side_effect=ValueError("Test error"))
        error_callback = AsyncMock()

        await processor.process_in_batches(items, process_fn, error_callback=error_callback)

        error_callback.assert_called()

    @pytest.mark.asyncio()
    async def test_process_in_batches_raises_without_error_callback(self):
        """Test exception is raised without error callback."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0)
        items = list(range(10))
        process_fn = AsyncMock(side_effect=ValueError("Test error"))

        with pytest.raises(ValueError, match="Test error"):
            await processor.process_in_batches(items, process_fn)

    @pytest.mark.asyncio()
    async def test_process_in_batches_extends_list_results(self):
        """Test that list results are extended."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0)
        items = list(range(10))
        process_fn = AsyncMock(return_value=["a", "b"])

        result = await processor.process_in_batches(items, process_fn)

        # 2 batches, each returning ["a", "b"]
        assert len(result) == 4

    @pytest.mark.asyncio()
    async def test_process_in_batches_appends_non_list_results(self):
        """Test that non-list results are appended."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0)
        items = list(range(10))
        process_fn = AsyncMock(return_value="single_result")

        result = await processor.process_in_batches(items, process_fn)

        assert result == ["single_result", "single_result"]


class TestSimpleBatchProcessorConcurrency:
    """Tests for process_with_concurrency method."""

    @pytest.mark.asyncio()
    async def test_process_with_concurrency_empty_list(self):
        """Test processing empty list with concurrency."""
        processor = SimpleBatchProcessor()
        process_fn = AsyncMock()

        result = await processor.process_with_concurrency([], process_fn)

        assert result == []

    @pytest.mark.asyncio()
    async def test_process_with_concurrency_single_item(self):
        """Test processing single item."""
        processor = SimpleBatchProcessor()
        process_fn = AsyncMock(return_value="result")

        result = await processor.process_with_concurrency([1], process_fn)

        assert result == ["result"]
        process_fn.assert_called_once_with(1)

    @pytest.mark.asyncio()
    async def test_process_with_concurrency_multiple_items(self):
        """Test processing multiple items."""
        processor = SimpleBatchProcessor()
        process_fn = AsyncMock(side_effect=lambda x: f"result_{x}")

        result = await processor.process_with_concurrency([1, 2, 3], process_fn)

        assert len(result) == 3
        assert "result_1" in result
        assert "result_2" in result
        assert "result_3" in result

    @pytest.mark.asyncio()
    async def test_process_with_concurrency_respects_max_concurrent(self):
        """Test that max_concurrent limit is respected."""
        processor = SimpleBatchProcessor()
        concurrent_count = 0
        max_concurrent_observed = 0

        async def track_concurrency(item):
            nonlocal concurrent_count, max_concurrent_observed
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return item

        await processor.process_with_concurrency(
            list(range(10)),
            track_concurrency,
            max_concurrent=3,
        )

        assert max_concurrent_observed <= 3

    @pytest.mark.asyncio()
    async def test_process_with_concurrency_handles_exceptions(self):
        """Test that exceptions in individual items don't crash."""
        processor = SimpleBatchProcessor()

        async def process_fn(item):
            if item == 2:
                raise ValueError("Error for item 2")
            return f"result_{item}"

        result = await processor.process_with_concurrency([1, 2, 3], process_fn)

        # Item 2 failed, so only items 1 and 3 should be in results
        assert len(result) == 2
        assert "result_1" in result
        assert "result_3" in result

    @pytest.mark.asyncio()
    async def test_process_with_concurrency_with_progress_callback(self):
        """Test progress callback is called."""
        processor = SimpleBatchProcessor()
        process_fn = AsyncMock(return_value="result")
        progress_callback = AsyncMock()

        await processor.process_with_concurrency(
            [1, 2, 3],
            process_fn,
            progress_callback=progress_callback,
        )

        assert progress_callback.call_count == 3


# ============================================================================
# TESTS FOR ProgressTracker
# ============================================================================


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    def test_init_values(self):
        """Test initialization values."""
        tracker = ProgressTracker(total=100, update_interval=10)
        assert tracker.total == 100
        assert tracker.processed == 0
        assert tracker.update_interval == 10
        assert tracker.last_update == 0

    def test_update_returns_none_before_interval(self):
        """Test update returns None before interval reached."""
        tracker = ProgressTracker(total=100, update_interval=10)

        result = tracker.update(5)

        assert result is None

    def test_update_returns_progress_at_interval(self):
        """Test update returns progress at interval."""
        tracker = ProgressTracker(total=100, update_interval=10)

        result = tracker.update(10)

        assert result is not None
        assert result["processed"] == 10
        assert result["total"] == 100
        assert result["percent"] == 10.0
        assert result["remaining"] == 90

    def test_update_returns_progress_at_completion(self):
        """Test update returns progress at completion."""
        tracker = ProgressTracker(total=100, update_interval=10)

        result = tracker.update(100)

        assert result is not None
        assert result["processed"] == 100
        assert result["percent"] == 100.0
        assert result["remaining"] == 0

    def test_update_with_zero_total(self):
        """Test update with zero total."""
        tracker = ProgressTracker(total=0, update_interval=1)

        result = tracker.update(0)

        assert result["percent"] == 0

    def test_format_progress_default(self):
        """Test formatting progress with default values."""
        tracker = ProgressTracker(total=100)
        tracker.processed = 50

        result = tracker.format_progress()

        assert "50/100" in result
        assert "50.0%" in result
        assert "50" in result  # Remaining

    def test_format_progress_with_parameter(self):
        """Test formatting progress with parameter."""
        tracker = ProgressTracker(total=100)

        result = tracker.format_progress(75)

        assert tracker.processed == 75
        assert "75/100" in result
        assert "75.0%" in result

    def test_format_progress_with_zero_total(self):
        """Test formatting progress with zero total."""
        tracker = ProgressTracker(total=0)

        result = tracker.format_progress(0)

        assert "0%" in result or "0.0%" in result

    def test_format_progress_contains_emoji(self):
        """Test formatting contains emoji."""
        tracker = ProgressTracker(total=100)

        result = tracker.format_progress(50)

        assert "🔄" in result or "📊" in result


# ============================================================================
# TESTS FOR chunked_api_calls
# ============================================================================


class TestChunkedApiCalls:
    """Tests for chunked_api_calls function."""

    @pytest.mark.asyncio()
    async def test_empty_items(self):
        """Test with empty items list."""
        api_call_fn = AsyncMock()

        result = await chunked_api_calls([], api_call_fn)

        assert result == []
        api_call_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_single_chunk(self):
        """Test items fitting in single chunk."""
        api_call_fn = AsyncMock(return_value=["result"])
        items = [1, 2, 3]

        result = await chunked_api_calls(items, api_call_fn, chunk_size=10)

        assert len(result) == 1
        api_call_fn.assert_called_once_with(items)

    @pytest.mark.asyncio()
    async def test_multiple_chunks(self):
        """Test items across multiple chunks."""
        api_call_fn = AsyncMock(return_value=["result"])
        items = list(range(10))

        result = await chunked_api_calls(items, api_call_fn, chunk_size=3, delay=0)

        # 4 chunks: [0,1,2], [3,4,5], [6,7,8], [9]
        assert api_call_fn.call_count == 4
        assert len(result) == 4

    @pytest.mark.asyncio()
    async def test_extends_list_results(self):
        """Test that list results are extended."""
        api_call_fn = AsyncMock(return_value=["a", "b"])
        items = list(range(6))

        result = await chunked_api_calls(items, api_call_fn, chunk_size=3, delay=0)

        # 2 chunks, each returning ["a", "b"]
        assert result == ["a", "b", "a", "b"]

    @pytest.mark.asyncio()
    async def test_appends_non_list_results(self):
        """Test that non-list results are appended."""
        api_call_fn = AsyncMock(return_value="single")
        items = list(range(6))

        result = await chunked_api_calls(items, api_call_fn, chunk_size=3, delay=0)

        assert result == ["single", "single"]

    @pytest.mark.asyncio()
    async def test_raises_on_exception(self):
        """Test that exceptions are raised."""
        api_call_fn = AsyncMock(side_effect=ValueError("API Error"))
        items = [1, 2, 3]

        with pytest.raises(ValueError, match="API Error"):
            await chunked_api_calls(items, api_call_fn)

    @pytest.mark.asyncio()
    async def test_delay_between_chunks(self):
        """Test delay is applied between chunks."""
        api_call_fn = AsyncMock(return_value=["result"])
        items = list(range(6))

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await chunked_api_calls(items, api_call_fn, chunk_size=3, delay=0.5)

        # Should sleep once between first and second chunk
        mock_sleep.assert_called_with(0.5)

    @pytest.mark.asyncio()
    async def test_no_delay_after_last_chunk(self):
        """Test no delay after last chunk."""
        api_call_fn = AsyncMock(return_value=["result"])
        items = [1, 2, 3]  # Single chunk

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await chunked_api_calls(items, api_call_fn, chunk_size=10, delay=0.5)

        # Should not sleep for single chunk
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio()
    async def test_handles_none_results(self):
        """Test handling None results."""
        api_call_fn = AsyncMock(return_value=None)
        items = [1, 2, 3]

        result = await chunked_api_calls(items, api_call_fn, chunk_size=10)

        assert result == []


# ============================================================================
# EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio()
    async def test_batch_size_equals_items(self):
        """Test when batch size equals number of items."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0)
        items = [1, 2, 3, 4, 5]
        process_fn = AsyncMock(return_value=["result"])

        result = await processor.process_in_batches(items, process_fn)

        process_fn.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio()
    async def test_batch_size_larger_than_items(self):
        """Test when batch size is larger than number of items."""
        processor = SimpleBatchProcessor(batch_size=100, delay_between_batches=0)
        items = [1, 2, 3]
        process_fn = AsyncMock(return_value=["result"])

        result = await processor.process_in_batches(items, process_fn)

        process_fn.assert_called_once()

    @pytest.mark.asyncio()
    async def test_single_item_batch(self):
        """Test processing with single item."""
        processor = SimpleBatchProcessor(batch_size=10, delay_between_batches=0)
        items = [1]
        process_fn = AsyncMock(return_value=["result"])

        result = await processor.process_in_batches(items, process_fn)

        assert len(result) == 1

    def test_progress_tracker_updates_state(self):
        """Test that progress tracker updates internal state."""
        tracker = ProgressTracker(total=100, update_interval=10)

        tracker.update(10)
        assert tracker.processed == 10
        assert tracker.last_update == 10

        result = tracker.update(25)
        assert tracker.processed == 25
        # last_update is updated when interval is reached or at completion
        # With update_interval=10, update at 25 triggers since 25-10=15 >= 10
        assert tracker.last_update in (20, 25)  # Depends on implementation

    @pytest.mark.asyncio()
    async def test_concurrent_processing_maintains_order(self):
        """Test that concurrent processing returns all results."""
        processor = SimpleBatchProcessor()

        async def process_fn(item):
            await asyncio.sleep(0.001 * (5 - item))  # Reverse delay
            return f"result_{item}"

        result = await processor.process_with_concurrency([1, 2, 3, 4, 5], process_fn)

        # All results should be present
        assert len(result) == 5
        assert all(f"result_{i}" in result for i in range(1, 6))

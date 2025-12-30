"""Tests for batch_processor module.

This module tests the SimpleBatchProcessor class, ProgressTracker,
and chunked_api_calls function for memory-efficient batch processing
of large datasets.

Coverage Target: 80%+
Total Tests: 47 tests
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.batch_processor import (
    ProgressTracker,
    SimpleBatchProcessor,
    chunked_api_calls,
)


class TestSimpleBatchProcessorInit:
    """Tests for SimpleBatchProcessor initialization."""

    def test_init_default(self):
        """Test default initialization."""
        processor = SimpleBatchProcessor()

        assert processor.batch_size == 100
        assert processor.delay_between_batches == 0.1

    def test_init_custom_batch_size(self):
        """Test initialization with custom batch size."""
        processor = SimpleBatchProcessor(batch_size=50)

        assert processor.batch_size == 50

    def test_init_custom_delay(self):
        """Test initialization with custom delay."""
        processor = SimpleBatchProcessor(delay_between_batches=0.5)

        assert processor.delay_between_batches == 0.5

    def test_init_all_custom(self):
        """Test initialization with all custom parameters."""
        processor = SimpleBatchProcessor(batch_size=25, delay_between_batches=0.2)

        assert processor.batch_size == 25
        assert processor.delay_between_batches == 0.2


class TestSimpleBatchProcessorProcessing:
    """Tests for batch processing functionality."""

    @pytest.fixture()
    def processor(self):
        """Create a SimpleBatchProcessor instance."""
        return SimpleBatchProcessor(batch_size=3, delay_between_batches=0.01)

    @pytest.mark.asyncio()
    async def test_process_empty_list(self, processor):
        """Test processing empty list."""
        async def process_fn(batch):
            return batch

        results = await processor.process_in_batches([], process_fn)

        assert results == []

    @pytest.mark.asyncio()
    async def test_process_single_batch(self, processor):
        """Test processing items that fit in single batch."""
        items = [1, 2]

        async def process_fn(batch):
            return [x * 2 for x in batch]

        results = await processor.process_in_batches(items, process_fn)

        assert results == [2, 4]

    @pytest.mark.asyncio()
    async def test_process_multiple_batches(self, processor):
        """Test processing items across multiple batches."""
        items = [1, 2, 3, 4, 5, 6, 7]

        async def process_fn(batch):
            return [x * 2 for x in batch]

        results = await processor.process_in_batches(items, process_fn)

        assert results == [2, 4, 6, 8, 10, 12, 14]

    @pytest.mark.asyncio()
    async def test_process_with_progress_callback(self, processor):
        """Test processing with progress callback."""
        items = [1, 2, 3, 4, 5]
        progress_updates = []

        async def process_fn(batch):
            return batch

        async def progress_callback(processed, total):
            progress_updates.append((processed, total))

        await processor.process_in_batches(items, process_fn, progress_callback=progress_callback)

        # Should have progress updates
        assert len(progress_updates) > 0
        # Last update should show all items processed
        assert progress_updates[-1][0] == len(items)

    @pytest.mark.asyncio()
    async def test_process_with_error_callback(self, processor):
        """Test processing with error callback."""
        items = [1, 2, 3, 4, 5]
        errors = []

        async def process_fn(batch):
            if 3 in batch:
                raise ValueError("Error on batch with 3")
            return batch

        async def error_callback(error, failed_batch):
            errors.append((str(error), failed_batch))

        await processor.process_in_batches(items, process_fn, error_callback=error_callback)

        # Should have captured the error
        assert len(errors) > 0

    @pytest.mark.asyncio()
    async def test_process_returns_non_list_result(self, processor):
        """Test processing when function returns single value."""
        items = [1, 2, 3]

        async def process_fn(batch):
            return sum(batch)  # Returns int, not list

        results = await processor.process_in_batches(items, process_fn)

        # Single values should be appended
        assert 6 in results  # Sum of [1, 2, 3]

    @pytest.mark.asyncio()
    async def test_process_returns_none(self, processor):
        """Test processing when function returns None."""
        items = [1, 2, 3]

        async def process_fn(batch):
            return None

        results = await processor.process_in_batches(items, process_fn)

        # None results should not be added
        assert len(results) == 0


class TestSimpleBatchProcessorBatching:
    """Tests for batching logic."""

    @pytest.mark.asyncio()
    async def test_batch_size_respected(self):
        """Test that batch size is respected."""
        processor = SimpleBatchProcessor(batch_size=2, delay_between_batches=0.01)
        batch_sizes = []

        async def process_fn(batch):
            batch_sizes.append(len(batch))
            return batch

        items = [1, 2, 3, 4, 5]
        await processor.process_in_batches(items, process_fn)

        # All batches except possibly last should be batch_size
        assert all(size <= 2 for size in batch_sizes)
        assert batch_sizes == [2, 2, 1]  # 5 items in batches of 2

    @pytest.mark.asyncio()
    async def test_exact_batch_size_items(self):
        """Test processing exactly batch_size items."""
        processor = SimpleBatchProcessor(batch_size=3, delay_between_batches=0.01)

        async def process_fn(batch):
            return batch

        items = [1, 2, 3]
        results = await processor.process_in_batches(items, process_fn)

        assert results == [1, 2, 3]


class TestSimpleBatchProcessorConcurrency:
    """Tests for concurrency and delay behavior."""

    @pytest.mark.asyncio()
    async def test_delay_between_batches(self):
        """Test that delay is applied between batches."""
        processor = SimpleBatchProcessor(batch_size=2, delay_between_batches=0.1)

        import time
        start = time.time()

        async def process_fn(batch):
            return batch

        items = [1, 2, 3, 4]  # 2 batches
        await processor.process_in_batches(items, process_fn)

        elapsed = time.time() - start
        # Should have at least one delay of 0.1 seconds
        assert elapsed >= 0.1

    @pytest.mark.asyncio()
    async def test_no_delay_for_single_batch(self):
        """Test no delay when there's only one batch."""
        processor = SimpleBatchProcessor(batch_size=10, delay_between_batches=1.0)

        import time
        start = time.time()

        async def process_fn(batch):
            return batch

        items = [1, 2, 3]  # Fits in single batch
        await processor.process_in_batches(items, process_fn)

        elapsed = time.time() - start
        # Should complete quickly without delay
        assert elapsed < 0.5


# ============================================================================
# Test Class: ProcessWithConcurrency
# ============================================================================


class TestProcessWithConcurrency:
    """Tests for process_with_concurrency method."""

    @pytest.fixture()
    def processor(self):
        """Fixture providing a SimpleBatchProcessor instance."""
        return SimpleBatchProcessor(batch_size=10, delay_between_batches=0.01)

    @pytest.mark.asyncio()
    async def test_process_empty_list_concurrent(self, processor):
        """Test concurrent processing of empty list."""
        # Arrange
        items = []
        process_fn = AsyncMock(return_value="result")

        # Act
        results = await processor.process_with_concurrency(items, process_fn)

        # Assert
        assert results == []
        process_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_process_single_item_concurrent(self, processor):
        """Test concurrent processing of single item."""
        # Arrange
        items = [1]
        process_fn = AsyncMock(return_value=10)

        # Act
        results = await processor.process_with_concurrency(items, process_fn)

        # Assert
        assert results == [10]
        process_fn.assert_called_once_with(1)

    @pytest.mark.asyncio()
    async def test_process_multiple_items_concurrent(self, processor):
        """Test concurrent processing of multiple items."""
        # Arrange
        items = [1, 2, 3, 4, 5]
        process_fn = AsyncMock(side_effect=lambda x: x * 10)

        # Act
        results = await processor.process_with_concurrency(items, process_fn)

        # Assert
        assert sorted(results) == [10, 20, 30, 40, 50]
        assert process_fn.call_count == 5

    @pytest.mark.asyncio()
    async def test_process_with_limited_concurrency(self, processor):
        """Test that concurrency is limited by max_concurrent."""
        # Arrange
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        async def track_calls(x):
            await asyncio.sleep(0.01)
            return x * 10

        # Act
        results = await processor.process_with_concurrency(
            items, track_calls, max_concurrent=2
        )

        # Assert
        assert len(results) == 10
        # All items should be processed
        assert sorted(results) == [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    @pytest.mark.asyncio()
    async def test_process_concurrent_with_progress_callback(self, processor):
        """Test concurrent processing with progress callback."""
        # Arrange
        items = [1, 2, 3, 4, 5]
        process_fn = AsyncMock(side_effect=lambda x: x * 10)
        progress_callback = AsyncMock()

        # Act
        results = await processor.process_with_concurrency(
            items, process_fn, progress_callback=progress_callback
        )

        # Assert
        assert len(results) == 5
        assert progress_callback.call_count == 5

    @pytest.mark.asyncio()
    async def test_process_concurrent_filters_none_results(self, processor):
        """Test that None results are filtered out."""
        # Arrange
        items = [1, 2, 3, 4, 5]

        async def process_with_none(x):
            if x % 2 == 0:
                return None
            return x * 10

        # Act
        results = await processor.process_with_concurrency(items, process_with_none)

        # Assert
        # Only odd numbers should return results
        assert sorted(results) == [10, 30, 50]

    @pytest.mark.asyncio()
    async def test_process_concurrent_handles_exceptions(self, processor):
        """Test that exceptions are handled gracefully."""
        # Arrange
        items = [1, 2, 3, 4, 5]

        async def process_with_error(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 10

        # Act
        results = await processor.process_with_concurrency(items, process_with_error)

        # Assert
        # Item 3 should fail and return None (filtered out)
        assert 30 not in results
        assert len(results) == 4

    @pytest.mark.asyncio()
    async def test_process_concurrent_max_concurrent_one(self, processor):
        """Test with max_concurrent=1 (sequential processing)."""
        # Arrange
        items = [1, 2, 3]
        call_order = []

        async def track_order(x):
            call_order.append(x)
            return x * 10

        # Act
        results = await processor.process_with_concurrency(
            items, track_order, max_concurrent=1
        )

        # Assert
        assert len(results) == 3
        # With max_concurrent=1, order should be preserved
        assert call_order == [1, 2, 3]


# ============================================================================
# Test Class: ProgressTracker Initialization
# ============================================================================


class TestProgressTrackerInit:
    """Tests for ProgressTracker initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default update interval."""
        # Act
        tracker = ProgressTracker(total=100)

        # Assert
        assert tracker.total == 100
        assert tracker.processed == 0
        assert tracker.update_interval == 10
        assert tracker.last_update == 0

    def test_init_with_custom_interval(self):
        """Test initialization with custom update interval."""
        # Act
        tracker = ProgressTracker(total=500, update_interval=50)

        # Assert
        assert tracker.total == 500
        assert tracker.update_interval == 50

    def test_init_with_zero_total(self):
        """Test initialization with zero total items."""
        # Act
        tracker = ProgressTracker(total=0)

        # Assert
        assert tracker.total == 0


# ============================================================================
# Test Class: ProgressTracker Update
# ============================================================================


class TestProgressTrackerUpdate:
    """Tests for ProgressTracker update method."""

    def test_update_below_interval(self):
        """Test update when below update interval."""
        # Arrange
        tracker = ProgressTracker(total=100, update_interval=10)

        # Act
        result = tracker.update(5)

        # Assert
        assert result is None
        assert tracker.processed == 5

    def test_update_at_interval(self):
        """Test update when at update interval."""
        # Arrange
        tracker = ProgressTracker(total=100, update_interval=10)

        # Act
        result = tracker.update(10)

        # Assert
        assert result is not None
        assert result["processed"] == 10
        assert result["total"] == 100
        assert result["percent"] == 10.0
        assert result["remaining"] == 90

    def test_update_at_completion(self):
        """Test update when processing completes."""
        # Arrange
        tracker = ProgressTracker(total=100, update_interval=10)

        # Act
        result = tracker.update(100)

        # Assert
        assert result is not None
        assert result["processed"] == 100
        assert result["percent"] == 100.0
        assert result["remaining"] == 0

    def test_update_with_zero_total(self):
        """Test update with zero total (division by zero protection)."""
        # Arrange
        tracker = ProgressTracker(total=0)

        # Act
        result = tracker.update(0)

        # Assert
        assert result is not None
        assert result["percent"] == 0

    def test_update_multiple_intervals(self):
        """Test multiple updates through multiple intervals."""
        # Arrange
        tracker = ProgressTracker(total=100, update_interval=10)

        # Act & Assert
        assert tracker.update(5) is None   # Below interval
        assert tracker.update(10) is not None  # At interval
        assert tracker.update(15) is None  # Below next interval
        assert tracker.update(20) is not None  # At next interval

    def test_update_returns_correct_remaining(self):
        """Test that remaining items are calculated correctly."""
        # Arrange
        tracker = ProgressTracker(total=100, update_interval=10)

        # Act
        result = tracker.update(75)

        # Assert
        assert result is not None
        assert result["remaining"] == 25


# ============================================================================
# Test Class: ProgressTracker Format
# ============================================================================


class TestProgressTrackerFormat:
    """Tests for ProgressTracker format_progress method."""

    def test_format_progress_initial(self):
        """Test formatting at initial state."""
        # Arrange
        tracker = ProgressTracker(total=100)

        # Act
        result = tracker.format_progress(0)

        # Assert
        assert "0/100" in result
        assert "0.0%" in result

    def test_format_progress_partial(self):
        """Test formatting at partial completion."""
        # Arrange
        tracker = ProgressTracker(total=100)

        # Act
        result = tracker.format_progress(50)

        # Assert
        assert "50/100" in result
        assert "50.0%" in result

    def test_format_progress_complete(self):
        """Test formatting at completion."""
        # Arrange
        tracker = ProgressTracker(total=100)

        # Act
        result = tracker.format_progress(100)

        # Assert
        assert "100/100" in result
        assert "100.0%" in result

    def test_format_progress_uses_current_if_none(self):
        """Test that format_progress uses current value if none provided."""
        # Arrange
        tracker = ProgressTracker(total=100)
        tracker.processed = 42

        # Act
        result = tracker.format_progress()

        # Assert
        assert "42/100" in result

    def test_format_progress_with_zero_total(self):
        """Test formatting with zero total."""
        # Arrange
        tracker = ProgressTracker(total=0)

        # Act
        result = tracker.format_progress(0)

        # Assert
        assert "0/0" in result
        assert "0.0%" in result


# ============================================================================
# Test Class: chunked_api_calls
# ============================================================================


class TestChunkedApiCalls:
    """Tests for chunked_api_calls function."""

    @pytest.mark.asyncio()
    async def test_chunked_empty_list(self):
        """Test chunked API calls with empty list."""
        # Arrange
        items = []
        api_call_fn = AsyncMock(return_value=[])

        # Act
        results = await chunked_api_calls(items, api_call_fn)

        # Assert
        assert results == []
        api_call_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_chunked_single_chunk(self):
        """Test chunked API calls with single chunk."""
        # Arrange
        items = [1, 2, 3, 4, 5]
        api_call_fn = AsyncMock(return_value=[10, 20, 30, 40, 50])

        # Act
        results = await chunked_api_calls(items, api_call_fn, chunk_size=10)

        # Assert
        assert results == [10, 20, 30, 40, 50]
        api_call_fn.assert_called_once_with([1, 2, 3, 4, 5])

    @pytest.mark.asyncio()
    async def test_chunked_multiple_chunks(self):
        """Test chunked API calls with multiple chunks."""
        # Arrange
        items = [1, 2, 3, 4, 5, 6]
        api_call_fn = AsyncMock(side_effect=[
            [10, 20],
            [30, 40],
            [50, 60],
        ])

        # Act
        results = await chunked_api_calls(items, api_call_fn, chunk_size=2, delay=0.001)

        # Assert
        assert results == [10, 20, 30, 40, 50, 60]
        assert api_call_fn.call_count == 3

    @pytest.mark.asyncio()
    async def test_chunked_non_list_result(self):
        """Test chunked API calls with non-list result."""
        # Arrange
        items = [1, 2, 3]
        api_call_fn = AsyncMock(return_value={"status": "ok"})

        # Act
        results = await chunked_api_calls(items, api_call_fn, chunk_size=10)

        # Assert
        assert {"status": "ok"} in results

    @pytest.mark.asyncio()
    async def test_chunked_with_none_result(self):
        """Test chunked API calls when API returns None."""
        # Arrange
        items = [1, 2, 3]
        api_call_fn = AsyncMock(return_value=None)

        # Act
        results = await chunked_api_calls(items, api_call_fn, chunk_size=10)

        # Assert
        assert results == []

    @pytest.mark.asyncio()
    async def test_chunked_raises_on_error(self):
        """Test chunked API calls raises exception on API error."""
        # Arrange
        items = [1, 2, 3, 4]
        api_call_fn = AsyncMock(side_effect=[
            [10, 20],
            ValueError("API error"),
        ])

        # Act & Assert
        with pytest.raises(ValueError, match="API error"):
            await chunked_api_calls(items, api_call_fn, chunk_size=2, delay=0.001)

    @pytest.mark.asyncio()
    async def test_chunked_default_parameters(self):
        """Test chunked API calls with default parameters."""
        # Arrange
        items = list(range(100))
        api_call_fn = AsyncMock(return_value=list(range(50)))

        # Act - using default chunk_size=50 and delay=0.5
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            results = await chunked_api_calls(items, api_call_fn)

            # Assert
            assert api_call_fn.call_count == 2  # 100 items / 50 chunk_size
            # Should delay between chunks
            mock_sleep.assert_called()

    @pytest.mark.asyncio()
    async def test_chunked_exact_chunk_size(self):
        """Test chunked API calls with items exactly matching chunk size."""
        # Arrange
        items = [1, 2, 3, 4, 5]
        api_call_fn = AsyncMock(return_value=[10, 20, 30, 40, 50])

        # Act
        results = await chunked_api_calls(items, api_call_fn, chunk_size=5, delay=0.001)

        # Assert
        assert results == [10, 20, 30, 40, 50]
        api_call_fn.assert_called_once()  # Only one call needed


# ============================================================================
# Test Class: Integration Tests
# ============================================================================


class TestBatchProcessorIntegration:
    """Integration tests combining multiple features."""

    @pytest.mark.asyncio()
    async def test_full_batch_processing_workflow(self):
        """Test complete batch processing workflow."""
        # Arrange
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0.001)
        items = list(range(12))
        progress_updates = []

        async def process_batch(batch):
            return [x * 2 for x in batch]

        async def track_progress(processed, total):
            progress_updates.append((processed, total))

        # Act
        results = await processor.process_in_batches(
            items, process_batch, progress_callback=track_progress
        )

        # Assert
        assert len(results) == 12
        assert results == [x * 2 for x in range(12)]
        assert len(progress_updates) > 0

    @pytest.mark.asyncio()
    async def test_progress_tracker_with_batch_processor(self):
        """Test ProgressTracker integration with batch processor."""
        # Arrange
        processor = SimpleBatchProcessor(batch_size=10, delay_between_batches=0.001)
        tracker = ProgressTracker(total=25, update_interval=10)
        items = list(range(25))
        progress_results = []

        async def process_batch(batch):
            return batch

        async def track_progress(processed, total):
            result = tracker.update(processed)
            if result:
                progress_results.append(result)

        # Act
        await processor.process_in_batches(
            items, process_batch, progress_callback=track_progress
        )

        # Assert
        assert len(progress_results) >= 2  # At least at 10, 20, and 25

"""Unit tests for src/utils/batch_processor.py.

Tests for batch processing functionality including:
- SimpleBatchProcessor initialization
- Process in batches
- Progress callbacks
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.utils.batch_processor import SimpleBatchProcessor


class TestSimpleBatchProcessorInit:
    """Tests for SimpleBatchProcessor initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        processor = SimpleBatchProcessor()

        assert processor.batch_size == 100
        assert processor.delay_between_batches == 0.1

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        processor = SimpleBatchProcessor(batch_size=50, delay_between_batches=0.5)

        assert processor.batch_size == 50
        assert processor.delay_between_batches == 0.5

    def test_init_edge_cases(self):
        """Test initialization with edge case values."""
        # Small batch size
        processor = SimpleBatchProcessor(batch_size=1, delay_between_batches=0.0)
        assert processor.batch_size == 1
        assert processor.delay_between_batches == 0.0

        # Large batch size
        processor = SimpleBatchProcessor(batch_size=10000, delay_between_batches=5.0)
        assert processor.batch_size == 10000
        assert processor.delay_between_batches == 5.0


class TestProcessInBatches:
    """Tests for process_in_batches method."""

    @pytest.fixture()
    def processor(self):
        """Create SimpleBatchProcessor instance."""
        return SimpleBatchProcessor(batch_size=3, delay_between_batches=0.0)

    @pytest.mark.asyncio()
    async def test_process_empty_list(self, processor):
        """Test processing empty list."""
        process_fn = AsyncMock(return_value=[])

        results = await processor.process_in_batches([], process_fn)

        assert results == []
        process_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_process_single_item(self, processor):
        """Test processing single item."""
        process_fn = AsyncMock(return_value=["result_1"])

        results = await processor.process_in_batches([1], process_fn)

        assert results == ["result_1"]
        process_fn.assert_called_once_with([1])

    @pytest.mark.asyncio()
    async def test_process_multiple_batches(self, processor):
        """Test processing items across multiple batches."""
        items = [1, 2, 3, 4, 5, 6, 7]

        # Return items as processed
        async def process_fn(batch):
            return [f"processed_{x}" for x in batch]

        results = await processor.process_in_batches(items, process_fn)

        # 3 batches: [1,2,3], [4,5,6], [7]
        assert len(results) == 7
        assert results[0] == "processed_1"
        assert results[6] == "processed_7"

    @pytest.mark.asyncio()
    async def test_process_with_non_list_result(self, processor):
        """Test processing when process_fn returns non-list."""
        items = [1, 2, 3]
        process_fn = AsyncMock(return_value="single_result")

        results = await processor.process_in_batches(items, process_fn)

        assert "single_result" in results

    @pytest.mark.asyncio()
    async def test_process_with_none_result(self, processor):
        """Test processing when process_fn returns None."""
        items = [1, 2, 3]
        process_fn = AsyncMock(return_value=None)

        results = await processor.process_in_batches(items, process_fn)

        assert results == []

    @pytest.mark.asyncio()
    async def test_progress_callback_called(self, processor):
        """Test progress callback is called for each batch."""
        items = [1, 2, 3, 4, 5]
        process_fn = AsyncMock(return_value=[])
        progress_callback = AsyncMock()

        await processor.process_in_batches(
            items, process_fn, progress_callback=progress_callback
        )

        # Should be called twice: after batch [1,2,3] and after batch [4,5]
        assert progress_callback.call_count == 2

    @pytest.mark.asyncio()
    async def test_progress_callback_arguments(self, processor):
        """Test progress callback receives correct arguments."""
        items = [1, 2, 3, 4]
        process_fn = AsyncMock(return_value=[])
        progress_callback = AsyncMock()

        await processor.process_in_batches(
            items, process_fn, progress_callback=progress_callback
        )

        # First call after processing [1,2,3]: (3, 4)
        # Second call after processing [4]: (4, 4)
        calls = progress_callback.call_args_list
        assert calls[0][0] == (3, 4)  # First batch
        assert calls[1][0] == (4, 4)  # Second batch

    @pytest.mark.asyncio()
    async def test_error_callback_on_exception(self, processor):
        """Test error callback is called when exception occurs."""
        items = [1, 2, 3]
        error = Exception("Processing error")
        process_fn = AsyncMock(side_effect=error)
        error_callback = AsyncMock()

        await processor.process_in_batches(
            items, process_fn, error_callback=error_callback
        )

        error_callback.assert_called_once()
        call_args = error_callback.call_args[0]
        assert isinstance(call_args[0], Exception)
        assert call_args[1] == [1, 2, 3]  # The failed batch

    @pytest.mark.asyncio()
    async def test_continues_after_error(self, processor):
        """Test processing continues after error in one batch."""
        items = [1, 2, 3, 4, 5, 6]

        call_count = [0]

        async def process_fn(batch):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First batch error")
            return [f"processed_{x}" for x in batch]

        error_callback = AsyncMock()

        results = await processor.process_in_batches(
            items, process_fn, error_callback=error_callback
        )

        # First batch fails, second batch succeeds
        assert len(results) == 3  # Only second batch results
        error_callback.assert_called_once()


class TestBatchProcessorEdgeCases:
    """Tests for edge cases in batch processor."""

    @pytest.mark.asyncio()
    async def test_batch_size_equals_items_count(self):
        """Test when batch size equals items count."""
        processor = SimpleBatchProcessor(batch_size=5)
        items = [1, 2, 3, 4, 5]
        process_fn = AsyncMock(return_value=["result"])

        await processor.process_in_batches(items, process_fn)

        process_fn.assert_called_once_with(items)

    @pytest.mark.asyncio()
    async def test_batch_size_larger_than_items(self):
        """Test when batch size is larger than items count."""
        processor = SimpleBatchProcessor(batch_size=100)
        items = [1, 2, 3]
        process_fn = AsyncMock(return_value=["result"])

        await processor.process_in_batches(items, process_fn)

        process_fn.assert_called_once_with(items)

    @pytest.mark.asyncio()
    async def test_batch_size_one(self):
        """Test with batch size of 1."""
        processor = SimpleBatchProcessor(batch_size=1, delay_between_batches=0.0)
        items = [1, 2, 3]

        async def process_fn(batch):
            return [f"processed_{batch[0]}"]

        results = await processor.process_in_batches(items, process_fn)

        assert len(results) == 3
        assert results[0] == "processed_1"
        assert results[2] == "processed_3"

    @pytest.mark.asyncio()
    async def test_with_different_data_types(self):
        """Test processing different data types."""
        processor = SimpleBatchProcessor(batch_size=2)

        # Test with dicts
        items = [{"id": 1}, {"id": 2}, {"id": 3}]

        async def process_fn(batch):
            return [item["id"] * 2 for item in batch]

        results = await processor.process_in_batches(items, process_fn)

        assert results == [2, 4, 6]

    @pytest.mark.asyncio()
    async def test_no_callbacks_provided(self):
        """Test processing without callbacks."""
        processor = SimpleBatchProcessor(batch_size=2, delay_between_batches=0.0)
        items = [1, 2, 3]
        process_fn = AsyncMock(return_value=["result"])

        # Should not raise
        results = await processor.process_in_batches(items, process_fn)

        assert len(results) > 0


class TestBatchProcessorIntegration:
    """Integration tests for batch processor."""

    @pytest.mark.asyncio()
    async def test_full_processing_workflow(self):
        """Test complete processing workflow."""
        processor = SimpleBatchProcessor(batch_size=2, delay_between_batches=0.0)
        items = [1, 2, 3, 4, 5]
        processed_batches = []
        progress_updates = []

        async def process_fn(batch):
            processed_batches.append(batch)
            return [x * 2 for x in batch]

        async def progress_callback(processed, total):
            progress_updates.append((processed, total))

        results = await processor.process_in_batches(
            items, process_fn, progress_callback=progress_callback
        )

        # Verify batches were processed correctly
        assert processed_batches == [[1, 2], [3, 4], [5]]

        # Verify results
        assert results == [2, 4, 6, 8, 10]

        # Verify progress updates
        assert len(progress_updates) == 3
        assert progress_updates[0] == (2, 5)
        assert progress_updates[1] == (4, 5)
        assert progress_updates[2] == (5, 5)

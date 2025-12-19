"""Tests for batch_processor module.

This module tests the SimpleBatchProcessor class for
memory-efficient batch processing of large datasets.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.utils.batch_processor import SimpleBatchProcessor


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

    @pytest.fixture
    def processor(self):
        """Create a SimpleBatchProcessor instance."""
        return SimpleBatchProcessor(batch_size=3, delay_between_batches=0.01)

    @pytest.mark.asyncio
    async def test_process_empty_list(self, processor):
        """Test processing empty list."""
        async def process_fn(batch):
            return batch
        
        results = await processor.process_in_batches([], process_fn)
        
        assert results == []

    @pytest.mark.asyncio
    async def test_process_single_batch(self, processor):
        """Test processing items that fit in single batch."""
        items = [1, 2]
        
        async def process_fn(batch):
            return [x * 2 for x in batch]
        
        results = await processor.process_in_batches(items, process_fn)
        
        assert results == [2, 4]

    @pytest.mark.asyncio
    async def test_process_multiple_batches(self, processor):
        """Test processing items across multiple batches."""
        items = [1, 2, 3, 4, 5, 6, 7]
        
        async def process_fn(batch):
            return [x * 2 for x in batch]
        
        results = await processor.process_in_batches(items, process_fn)
        
        assert results == [2, 4, 6, 8, 10, 12, 14]

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_process_returns_non_list_result(self, processor):
        """Test processing when function returns single value."""
        items = [1, 2, 3]
        
        async def process_fn(batch):
            return sum(batch)  # Returns int, not list
        
        results = await processor.process_in_batches(items, process_fn)
        
        # Single values should be appended
        assert 6 in results  # Sum of [1, 2, 3]

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

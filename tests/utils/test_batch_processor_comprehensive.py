"""Additional unit tests for batch processor module.

This module contains additional tests for src/utils/batch_processor.py covering:
- ProgressTracker class
- chunked_api_calls function
- process_with_concurrency method
- Edge cases and error handling

Target: 20+ additional tests to achieve 80%+ coverage
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.batch_processor import (
    ProgressTracker,
    SimpleBatchProcessor,
    chunked_api_calls,
)


# ============================================================================
# ProgressTracker Tests
# ============================================================================


class TestProgressTrackerInit:
    """Tests for ProgressTracker initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        tracker = ProgressTracker(total=100)
        
        assert tracker.total == 100
        assert tracker.processed == 0
        assert tracker.update_interval == 10
        assert tracker.last_update == 0

    def test_init_with_custom_interval(self):
        """Test initialization with custom update interval."""
        tracker = ProgressTracker(total=500, update_interval=50)
        
        assert tracker.total == 500
        assert tracker.update_interval == 50


class TestProgressTrackerUpdate:
    """Tests for ProgressTracker update method."""

    def test_update_below_interval(self):
        """Test update when below interval - returns None."""
        tracker = ProgressTracker(total=100, update_interval=10)
        
        result = tracker.update(5)
        
        assert result is None
        assert tracker.processed == 5

    def test_update_at_interval(self):
        """Test update when at interval - returns progress info."""
        tracker = ProgressTracker(total=100, update_interval=10)
        
        result = tracker.update(10)
        
        assert result is not None
        assert result["processed"] == 10
        assert result["total"] == 100
        assert result["percent"] == 10.0
        assert result["remaining"] == 90

    def test_update_above_interval(self):
        """Test update when above interval."""
        tracker = ProgressTracker(total=100, update_interval=10)
        
        result = tracker.update(15)
        
        assert result is not None
        assert result["processed"] == 15
        assert result["percent"] == 15.0

    def test_update_at_completion(self):
        """Test update at completion always returns progress."""
        tracker = ProgressTracker(total=100, update_interval=10)
        tracker.update(5)  # Should return None
        
        result = tracker.update(100)  # Should return progress at completion
        
        assert result is not None
        assert result["processed"] == 100
        assert result["percent"] == 100.0
        assert result["remaining"] == 0

    def test_update_with_zero_total(self):
        """Test update with zero total items."""
        tracker = ProgressTracker(total=0, update_interval=10)
        
        result = tracker.update(0)
        
        assert result is not None
        assert result["percent"] == 0

    def test_multiple_updates(self):
        """Test multiple progressive updates."""
        tracker = ProgressTracker(total=100, update_interval=10)
        
        results = []
        for i in [5, 10, 15, 20, 25]:
            result = tracker.update(i)
            results.append(result)
        
        # Only updates at 10, 20 intervals should return values
        assert results[0] is None  # 5
        assert results[1] is not None  # 10
        assert results[2] is None  # 15
        assert results[3] is not None  # 20
        assert results[4] is None  # 25


class TestProgressTrackerFormatProgress:
    """Tests for ProgressTracker format_progress method."""

    def test_format_progress_default(self):
        """Test format_progress with current processed count."""
        tracker = ProgressTracker(total=100)
        tracker.processed = 25
        
        result = tracker.format_progress()
        
        assert "25/100" in result
        assert "25.0%" in result
        assert "75" in result  # remaining

    def test_format_progress_with_value(self):
        """Test format_progress with explicit value."""
        tracker = ProgressTracker(total=100)
        
        result = tracker.format_progress(processed=50)
        
        assert "50/100" in result
        assert "50.0%" in result
        assert tracker.processed == 50  # Should update processed

    def test_format_progress_at_zero(self):
        """Test format_progress at zero progress."""
        tracker = ProgressTracker(total=100)
        
        result = tracker.format_progress(processed=0)
        
        assert "0/100" in result
        assert "0.0%" in result
        assert "100" in result  # remaining

    def test_format_progress_at_completion(self):
        """Test format_progress at completion."""
        tracker = ProgressTracker(total=100)
        
        result = tracker.format_progress(processed=100)
        
        assert "100/100" in result
        assert "100.0%" in result
        assert "0" in result  # remaining

    def test_format_progress_with_zero_total(self):
        """Test format_progress with zero total."""
        tracker = ProgressTracker(total=0)
        
        result = tracker.format_progress(processed=0)
        
        assert "0/0" in result
        assert "0.0%" in result


# ============================================================================
# chunked_api_calls Tests
# ============================================================================


class TestChunkedApiCalls:
    """Tests for chunked_api_calls function."""

    @pytest.mark.asyncio()
    async def test_empty_items(self):
        """Test with empty items list."""
        api_call_fn = AsyncMock(return_value=[])
        
        result = await chunked_api_calls([], api_call_fn)
        
        assert result == []
        api_call_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_single_chunk(self):
        """Test with items fitting in single chunk."""
        items = [1, 2, 3]
        api_call_fn = AsyncMock(return_value=["a", "b", "c"])
        
        result = await chunked_api_calls(items, api_call_fn, chunk_size=10)
        
        assert result == ["a", "b", "c"]
        api_call_fn.assert_called_once_with([1, 2, 3])

    @pytest.mark.asyncio()
    async def test_multiple_chunks(self):
        """Test with items requiring multiple chunks."""
        items = [1, 2, 3, 4, 5]
        api_call_fn = AsyncMock(side_effect=[["a", "b"], ["c", "d"], ["e"]])
        
        result = await chunked_api_calls(items, api_call_fn, chunk_size=2, delay=0.001)
        
        assert result == ["a", "b", "c", "d", "e"]
        assert api_call_fn.call_count == 3

    @pytest.mark.asyncio()
    async def test_chunk_with_non_list_result(self):
        """Test when API returns non-list result."""
        items = [1, 2]
        api_call_fn = AsyncMock(return_value={"status": "ok"})
        
        result = await chunked_api_calls(items, api_call_fn, chunk_size=10)
        
        assert result == [{"status": "ok"}]

    @pytest.mark.asyncio()
    async def test_chunk_with_none_result(self):
        """Test when API returns None."""
        items = [1, 2]
        api_call_fn = AsyncMock(return_value=None)
        
        result = await chunked_api_calls(items, api_call_fn, chunk_size=10)
        
        assert result == []

    @pytest.mark.asyncio()
    async def test_chunk_api_error_propagates(self):
        """Test that API errors propagate."""
        items = [1, 2, 3, 4]
        api_call_fn = AsyncMock(side_effect=[["a", "b"], ValueError("API Error")])
        
        with pytest.raises(ValueError, match="API Error"):
            await chunked_api_calls(items, api_call_fn, chunk_size=2, delay=0.001)

    @pytest.mark.asyncio()
    async def test_chunk_with_custom_delay(self):
        """Test that delay is applied between chunks."""
        items = [1, 2, 3, 4]
        api_call_fn = AsyncMock(side_effect=[["a", "b"], ["c", "d"]])
        
        with patch("src.utils.batch_processor.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await chunked_api_calls(items, api_call_fn, chunk_size=2, delay=0.5)
            
            # Sleep should be called once (between first and second chunk)
            mock_sleep.assert_called_once_with(0.5)


# ============================================================================
# process_with_concurrency Tests
# ============================================================================


class TestProcessWithConcurrency:
    """Tests for process_with_concurrency method."""

    @pytest.fixture()
    def processor(self):
        """Fixture providing a SimpleBatchProcessor instance."""
        return SimpleBatchProcessor(batch_size=10, delay_between_batches=0.01)

    @pytest.mark.asyncio()
    async def test_empty_items(self, processor):
        """Test with empty items list."""
        process_fn = AsyncMock(return_value="result")
        
        result = await processor.process_with_concurrency([], process_fn)
        
        assert result == []
        process_fn.assert_not_called()

    @pytest.mark.asyncio()
    async def test_single_item(self, processor):
        """Test with single item."""
        process_fn = AsyncMock(return_value="result")
        
        result = await processor.process_with_concurrency([1], process_fn)
        
        assert result == ["result"]
        process_fn.assert_called_once_with(1)

    @pytest.mark.asyncio()
    async def test_multiple_items(self, processor):
        """Test with multiple items."""
        process_fn = AsyncMock(side_effect=lambda x: x * 10)
        
        result = await processor.process_with_concurrency([1, 2, 3], process_fn, max_concurrent=5)
        
        assert sorted(result) == [10, 20, 30]
        assert process_fn.call_count == 3

    @pytest.mark.asyncio()
    async def test_respects_concurrency_limit(self, processor):
        """Test that concurrency limit is respected."""
        concurrent_count = 0
        max_concurrent_seen = 0
        
        async def track_concurrency(item):
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            await asyncio.sleep(0.01)  # Simulate some work
            concurrent_count -= 1
            return item * 10
        
        result = await processor.process_with_concurrency(
            list(range(10)), track_concurrency, max_concurrent=3
        )
        
        assert len(result) == 10
        assert max_concurrent_seen <= 3

    @pytest.mark.asyncio()
    async def test_with_progress_callback(self, processor):
        """Test with progress callback."""
        progress_callback = AsyncMock()
        process_fn = AsyncMock(return_value="result")
        
        await processor.process_with_concurrency(
            [1, 2, 3], process_fn, progress_callback=progress_callback
        )
        
        assert progress_callback.call_count == 3

    @pytest.mark.asyncio()
    async def test_handles_item_errors(self, processor):
        """Test that errors in processing items are handled."""
        async def sometimes_fails(item):
            if item == 2:
                raise ValueError("Item 2 failed")
            return item * 10
        
        result = await processor.process_with_concurrency(
            [1, 2, 3], sometimes_fails, max_concurrent=1
        )
        
        # Should have results for items 1 and 3
        assert len(result) == 2
        assert 10 in result
        assert 30 in result

    @pytest.mark.asyncio()
    async def test_filters_none_results(self, processor):
        """Test that None results are filtered out."""
        async def return_none_sometimes(item):
            if item == 2:
                return None
            return item * 10
        
        result = await processor.process_with_concurrency(
            [1, 2, 3], return_none_sometimes
        )
        
        assert len(result) == 2
        assert 10 in result
        assert 30 in result


# ============================================================================
# Integration Tests
# ============================================================================


class TestBatchProcessorIntegration:
    """Integration tests for batch processor."""

    @pytest.mark.asyncio()
    async def test_process_and_track_progress(self):
        """Test processing with progress tracking."""
        processor = SimpleBatchProcessor(batch_size=5, delay_between_batches=0.001)
        tracker = ProgressTracker(total=20, update_interval=5)
        
        progress_updates = []
        
        async def progress_callback(processed, total):
            info = tracker.update(processed)
            if info:
                progress_updates.append(info)
        
        async def process_fn(batch):
            return [x * 2 for x in batch]
        
        results = await processor.process_in_batches(
            list(range(20)), process_fn, progress_callback=progress_callback
        )
        
        assert len(results) == 20
        assert len(progress_updates) >= 2  # At least at 5, 10, 15, 20

    @pytest.mark.asyncio()
    async def test_concurrent_processing_with_chunked_api(self):
        """Test combining concurrent processing with chunked API calls."""
        processor = SimpleBatchProcessor(batch_size=10, delay_between_batches=0.001)
        
        async def fetch_item_details(item):
            # Simulate API call
            await asyncio.sleep(0.001)
            return {"id": item, "name": f"Item {item}"}
        
        results = await processor.process_with_concurrency(
            list(range(10)), fetch_item_details, max_concurrent=3
        )
        
        assert len(results) == 10
        assert all(isinstance(r, dict) for r in results)
        assert all("id" in r and "name" in r for r in results)

"""Extended unit tests for notification_queue.py.

This module provides comprehensive tests for the NotificationQueue class covering:
- Queue initialization and configuration
- Message enqueueing with various priorities
- Rate limiting (global and per-chat)
- Worker start/stop lifecycle
- Error handling (RetryAfter, NetworkError, TimedOut)
- Timestamp cleanup
- Edge cases

Target: 35+ tests to achieve 80%+ coverage
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import NetworkError, RetryAfter, TimedOut

from src.telegram_bot.notification_queue import (
    NotificationMessage,
    NotificationQueue,
    Priority,
)


# Test fixtures


@pytest.fixture()
def mock_bot():
    """Fixture providing a mocked Telegram Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture()
def notification_queue(mock_bot):
    """Fixture providing a NotificationQueue instance."""
    return NotificationQueue(
        bot=mock_bot,
        global_rate_limit=0.01,  # Fast for testing
        chat_rate_limit=0.01,    # Fast for testing
    )


# TestPriorityEnum


class TestPriorityEnum:
    """Tests for Priority enum."""

    def test_high_priority_value(self):
        """Test HIGH priority has value 0."""
        assert Priority.HIGH == 0

    def test_normal_priority_value(self):
        """Test NORMAL priority has value 1."""
        assert Priority.NORMAL == 1

    def test_low_priority_value(self):
        """Test LOW priority has value 2."""
        assert Priority.LOW == 2

    def test_priority_comparison(self):
        """Test priority comparison (lower value = higher priority)."""
        assert Priority.HIGH < Priority.NORMAL < Priority.LOW


# TestNotificationMessage


class TestNotificationMessage:
    """Tests for NotificationMessage dataclass."""

    def test_message_creation_minimal(self):
        """Test creating message with minimal parameters."""
        msg = NotificationMessage(chat_id=123, text="Hello")

        assert msg.chat_id == 123
        assert msg.text == "Hello"
        assert msg.parse_mode is None
        assert msg.reply_markup is None
        assert msg.disable_web_page_preview is False
        assert msg.priority == Priority.NORMAL

    def test_message_creation_full(self):
        """Test creating message with all parameters."""
        reply_markup = MagicMock()
        msg = NotificationMessage(
            chat_id=456,
            text="Test",
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            priority=Priority.HIGH,
        )

        assert msg.chat_id == 456
        assert msg.text == "Test"
        assert msg.parse_mode == "HTML"
        assert msg.reply_markup == reply_markup
        assert msg.disable_web_page_preview is True
        assert msg.priority == Priority.HIGH


# TestNotificationQueueInit


class TestNotificationQueueInit:
    """Tests for NotificationQueue initialization."""

    def test_init_with_defaults(self, mock_bot):
        """Test initialization with default parameters."""
        queue = NotificationQueue(bot=mock_bot)

        assert queue.bot == mock_bot
        assert queue.is_running is False
        assert queue.worker_task is None
        assert queue.global_rate_limit == 1.0 / 30.0
        assert queue.chat_rate_limit == 1.0

    def test_init_with_custom_rates(self, mock_bot):
        """Test initialization with custom rate limits."""
        queue = NotificationQueue(
            bot=mock_bot,
            global_rate_limit=0.05,
            chat_rate_limit=0.5,
        )

        assert queue.global_rate_limit == 0.05
        assert queue.chat_rate_limit == 0.5

    def test_init_state(self, notification_queue):
        """Test initial state."""
        assert notification_queue.last_global_send_time == 0.0
        assert notification_queue.last_chat_send_time == {}


# TestQueueStartStop


class TestQueueStartStop:
    """Tests for start and stop functionality."""

    @pytest.mark.asyncio()
    async def test_start_creates_worker(self, notification_queue):
        """Test that start creates worker task."""
        await notification_queue.start()

        assert notification_queue.is_running is True
        assert notification_queue.worker_task is not None

        await notification_queue.stop()

    @pytest.mark.asyncio()
    async def test_start_idempotent(self, notification_queue):
        """Test that multiple starts don't create multiple workers."""
        await notification_queue.start()
        first_task = notification_queue.worker_task

        await notification_queue.start()
        second_task = notification_queue.worker_task

        assert first_task is second_task

        await notification_queue.stop()

    @pytest.mark.asyncio()
    async def test_stop_sets_running_false(self, notification_queue):
        """Test that stop sets is_running to False."""
        await notification_queue.start()
        await notification_queue.stop()

        assert notification_queue.is_running is False

    @pytest.mark.asyncio()
    async def test_stop_cancels_worker(self, notification_queue):
        """Test that stop cancels worker task."""
        await notification_queue.start()
        task = notification_queue.worker_task

        await notification_queue.stop()

        assert task.cancelled() or task.done()


# TestEnqueue


class TestEnqueue:
    """Tests for enqueue functionality."""

    @pytest.mark.asyncio()
    async def test_enqueue_adds_to_queue(self, notification_queue):
        """Test that enqueue adds message to queue."""
        await notification_queue.enqueue(
            chat_id=123,
            text="Test message",
        )

        assert notification_queue.queue.qsize() == 1

    @pytest.mark.asyncio()
    async def test_enqueue_with_priority(self, notification_queue):
        """Test enqueueing with specific priority."""
        await notification_queue.enqueue(
            chat_id=123,
            text="High priority",
            priority=Priority.HIGH,
        )

        priority, _, _, msg = await notification_queue.queue.get()
        assert priority == Priority.HIGH
        assert msg.priority == Priority.HIGH

    @pytest.mark.asyncio()
    async def test_enqueue_with_all_options(self, notification_queue):
        """Test enqueueing with all options."""
        reply_markup = MagicMock()

        await notification_queue.enqueue(
            chat_id=456,
            text="Full options",
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            priority=Priority.LOW,
        )

        _, _, _, msg = await notification_queue.queue.get()
        assert msg.chat_id == 456
        assert msg.text == "Full options"
        assert msg.parse_mode == "Markdown"
        assert msg.reply_markup == reply_markup
        assert msg.disable_web_page_preview is True

    @pytest.mark.asyncio()
    async def test_enqueue_multiple_messages(self, notification_queue):
        """Test enqueueing multiple messages."""
        for i in range(5):
            await notification_queue.enqueue(chat_id=100 + i, text=f"Message {i}")

        assert notification_queue.queue.qsize() == 5


# TestPriorityOrdering


class TestPriorityOrdering:
    """Tests for priority-based ordering."""

    @pytest.mark.asyncio()
    async def test_high_priority_first(self, notification_queue):
        """Test that HIGH priority messages come first."""
        await notification_queue.enqueue(chat_id=1, text="Low", priority=Priority.LOW)
        await notification_queue.enqueue(chat_id=2, text="High", priority=Priority.HIGH)

        p1, _, _, msg1 = await notification_queue.queue.get()
        assert p1 == Priority.HIGH
        assert msg1.text == "High"

    @pytest.mark.asyncio()
    async def test_fifo_within_same_priority(self, notification_queue):
        """Test FIFO ordering within same priority."""
        await notification_queue.enqueue(chat_id=1, text="First", priority=Priority.NORMAL)
        await notification_queue.enqueue(chat_id=2, text="Second", priority=Priority.NORMAL)
        await notification_queue.enqueue(chat_id=3, text="Third", priority=Priority.NORMAL)

        _, _, _, msg1 = await notification_queue.queue.get()
        _, _, _, msg2 = await notification_queue.queue.get()
        _, _, _, msg3 = await notification_queue.queue.get()

        assert msg1.text == "First"
        assert msg2.text == "Second"
        assert msg3.text == "Third"


# TestRateLimiting


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio()
    async def test_global_rate_limit_wait(self, notification_queue, mock_bot):
        """Test waiting for global rate limit."""
        notification_queue.global_rate_limit = 0.1
        notification_queue.last_global_send_time = time.time()

        start = time.time()
        await notification_queue._wait_for_rate_limits(123)
        elapsed = time.time() - start

        # Should have waited close to 0.1 seconds
        assert elapsed >= 0.09

    @pytest.mark.asyncio()
    async def test_chat_rate_limit_wait(self, notification_queue, mock_bot):
        """Test waiting for per-chat rate limit."""
        notification_queue.chat_rate_limit = 0.1
        notification_queue.last_chat_send_time[123] = time.time()

        start = time.time()
        await notification_queue._wait_for_rate_limits(123)
        elapsed = time.time() - start

        # Should have waited close to 0.1 seconds
        assert elapsed >= 0.09

    @pytest.mark.asyncio()
    async def test_no_wait_when_limit_passed(self, notification_queue):
        """Test no waiting when enough time has passed."""
        notification_queue.last_global_send_time = time.time() - 10
        notification_queue.last_chat_send_time[123] = time.time() - 10

        start = time.time()
        await notification_queue._wait_for_rate_limits(123)
        elapsed = time.time() - start

        # Should not have waited
        assert elapsed < 0.05


# TestSendMessage


class TestSendMessage:
    """Tests for _send_message functionality."""

    @pytest.mark.asyncio()
    async def test_send_message_success(self, notification_queue, mock_bot):
        """Test successful message sending."""
        msg = NotificationMessage(chat_id=123, text="Test")

        await notification_queue._send_message(msg)

        mock_bot.send_message.assert_called_once_with(
            chat_id=123,
            text="Test",
            parse_mode=None,
            reply_markup=None,
            disable_web_page_preview=False,
        )

    @pytest.mark.asyncio()
    async def test_send_message_updates_timestamps(self, notification_queue, mock_bot):
        """Test that sending updates timestamps."""
        msg = NotificationMessage(chat_id=456, text="Test")

        await notification_queue._send_message(msg)

        assert notification_queue.last_global_send_time > 0
        assert notification_queue.last_chat_send_time[456] > 0

    @pytest.mark.asyncio()
    async def test_send_message_retry_after(self, notification_queue, mock_bot):
        """Test handling of RetryAfter error."""
        msg = NotificationMessage(chat_id=123, text="Test")
        mock_bot.send_message.side_effect = [RetryAfter(0.01), None]

        await notification_queue._send_message(msg)

        # Message should be re-queued
        assert notification_queue.queue.qsize() == 1

    @pytest.mark.asyncio()
    async def test_send_message_network_error(self, notification_queue, mock_bot):
        """Test handling of NetworkError."""
        msg = NotificationMessage(chat_id=123, text="Test", priority=Priority.NORMAL)
        mock_bot.send_message.side_effect = [NetworkError("Connection reset"), None]

        await notification_queue._send_message(msg)

        # Message should be re-queued with same priority
        assert notification_queue.queue.qsize() == 1

    @pytest.mark.asyncio()
    async def test_send_message_timed_out(self, notification_queue, mock_bot):
        """Test handling of TimedOut error."""
        msg = NotificationMessage(chat_id=123, text="Test")
        mock_bot.send_message.side_effect = [TimedOut(), None]

        await notification_queue._send_message(msg)

        # Message should be re-queued
        assert notification_queue.queue.qsize() == 1

    @pytest.mark.asyncio()
    async def test_send_message_other_error(self, notification_queue, mock_bot):
        """Test handling of other errors (no retry)."""
        msg = NotificationMessage(chat_id=123, text="Test")
        mock_bot.send_message.side_effect = RuntimeError("User blocked bot")

        await notification_queue._send_message(msg)

        # Message should NOT be re-queued
        assert notification_queue.queue.qsize() == 0


# TestTimestampCleanup


class TestTimestampCleanup:
    """Tests for timestamp cleanup functionality."""

    def test_cleanup_removes_old_timestamps(self, notification_queue):
        """Test that old timestamps are removed."""
        now = time.time()

        # Add old and new timestamps
        notification_queue.last_chat_send_time = {
            1: now - 120,  # Old (2 min ago)
            2: now - 90,   # Old (1.5 min ago)
            3: now - 30,   # Recent (30 sec ago)
            4: now - 5,    # Recent (5 sec ago)
        }

        notification_queue._cleanup_timestamps()

        # Old ones should be removed
        assert 1 not in notification_queue.last_chat_send_time
        assert 2 not in notification_queue.last_chat_send_time
        # Recent ones should remain
        assert 3 in notification_queue.last_chat_send_time
        assert 4 in notification_queue.last_chat_send_time

    def test_cleanup_empty_dict(self, notification_queue):
        """Test cleanup on empty dict."""
        notification_queue.last_chat_send_time = {}

        # Should not fail
        notification_queue._cleanup_timestamps()

        assert notification_queue.last_chat_send_time == {}

    @pytest.mark.asyncio()
    async def test_cleanup_triggered_on_send(self, notification_queue, mock_bot):
        """Test that cleanup is triggered when dict exceeds 1000 entries."""
        # Add more than 1000 old entries
        now = time.time()
        notification_queue.last_chat_send_time = dict.fromkeys(range(1001), now - 120)

        msg = NotificationMessage(chat_id=9999, text="Test")
        await notification_queue._send_message(msg)

        # Old entries should be cleaned up
        assert len(notification_queue.last_chat_send_time) < 1001


# TestWorker


class TestWorker:
    """Tests for worker functionality."""

    @pytest.mark.asyncio()
    async def test_worker_processes_queue(self, notification_queue, mock_bot):
        """Test that worker processes messages from queue."""
        await notification_queue.start()

        await notification_queue.enqueue(chat_id=123, text="Test 1")
        await notification_queue.enqueue(chat_id=456, text="Test 2")

        await asyncio.sleep(0.1)  # Allow processing

        await notification_queue.stop()

        assert mock_bot.send_message.call_count == 2

    @pytest.mark.asyncio()
    async def test_worker_handles_cancel(self, notification_queue):
        """Test that worker handles cancellation."""
        await notification_queue.start()

        # Stop immediately
        await notification_queue.stop()

        assert notification_queue.is_running is False


# TestIntegration


class TestIntegration:
    """Integration tests for NotificationQueue."""

    @pytest.mark.asyncio()
    async def test_full_workflow(self, mock_bot):
        """Test complete workflow: init, start, enqueue, send, stop."""
        queue = NotificationQueue(
            bot=mock_bot,
            global_rate_limit=0.001,
            chat_rate_limit=0.001,
        )

        await queue.start()

        # Enqueue messages with different priorities
        await queue.enqueue(chat_id=1, text="Low", priority=Priority.LOW)
        await queue.enqueue(chat_id=2, text="High", priority=Priority.HIGH)
        await queue.enqueue(chat_id=3, text="Normal", priority=Priority.NORMAL)

        # Wait for processing
        await asyncio.sleep(0.2)

        await queue.stop()

        # All messages should have been sent
        assert mock_bot.send_message.call_count == 3

        # Verify order (high first, then normal, then low)
        calls = mock_bot.send_message.call_args_list
        assert calls[0].kwargs["text"] == "High"
        assert calls[1].kwargs["text"] == "Normal"
        assert calls[2].kwargs["text"] == "Low"


# TestEdgeCases


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio()
    async def test_enqueue_before_start(self, notification_queue):
        """Test enqueueing before worker is started."""
        # Should not fail
        await notification_queue.enqueue(chat_id=123, text="Test")

        assert notification_queue.queue.qsize() == 1

    @pytest.mark.asyncio()
    async def test_stop_without_start(self, notification_queue):
        """Test stopping without starting."""
        # Should not fail
        await notification_queue.stop()

        assert notification_queue.is_running is False

    @pytest.mark.asyncio()
    async def test_empty_text_message(self, notification_queue, mock_bot):
        """Test sending message with empty text."""
        msg = NotificationMessage(chat_id=123, text="")

        await notification_queue._send_message(msg)

        mock_bot.send_message.assert_called_once()
        assert mock_bot.send_message.call_args.kwargs["text"] == ""

    @pytest.mark.asyncio()
    async def test_large_queue(self, notification_queue, mock_bot):
        """Test handling large number of messages."""
        for i in range(100):
            await notification_queue.enqueue(chat_id=i, text=f"Message {i}")

        assert notification_queue.queue.qsize() == 100

"""E2E test for notification flow.

Tests complete notification delivery from trigger to user.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.telegram_bot.notification_queue import NotificationQueue
from src.telegram_bot.notifier import Notifier


@pytest.fixture()
async def notification_system():
    """Fixture for notification system."""
    queue = NotificationQueue()
    notifier = Notifier(queue=queue)
    return queue, notifier


@pytest.mark.e2e()
@pytest.mark.asyncio()
async def test_notification_delivery_flow(notification_system):
    """Test complete notification flow from opportunity to delivery."""
    queue, notifier = notification_system

    # Arrange: Mock telegram bot
    mock_bot = AsyncMock()
    notifier.bot = mock_bot

    # Arrange: Create arbitrage opportunity
    opportunity = {
        "item_title": "AK-47 | Redline (FT)",
        "buy_price": 10.00,
        "sell_price": 15.00,
        "profit": 3.95,
        "profit_margin": 26.3,
        "game": "csgo",
    }

    # Act: Add notification to queue
    await queue.add({"type": "arbitrage_opportunity", "user_id": 123456789, "data": opportunity})

    # Act: Process queue
    await notifier.process_queue()

    # Assert: Notification was sent
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args.kwargs["chat_id"] == 123456789
    assert "AK-47 | Redline" in call_args.kwargs["text"]


@pytest.mark.e2e()
@pytest.mark.asyncio()
async def test_batch_notification_flow(notification_system):
    """Test batch notifications are delivered correctly."""
    queue, notifier = notification_system

    # Arrange: Mock telegram bot
    mock_bot = AsyncMock()
    notifier.bot = mock_bot

    # Act: Add multiple notifications
    for i in range(5):
        await queue.add({
            "type": "price_alert",
            "user_id": 123456789,
            "data": {"item": f"Item {i}", "price": 10 + i},
        })

    # Act: Process all
    await notifier.process_queue()

    # Assert: All sent
    assert mock_bot.send_message.call_count == 5


@pytest.mark.e2e()
@pytest.mark.asyncio()
async def test_notification_retry_on_failure(notification_system):
    """Test notification retry mechanism on failure."""
    queue, notifier = notification_system

    # Arrange: Mock bot that fails first time
    mock_bot = AsyncMock()
    mock_bot.send_message.side_effect = [
        Exception("Network error"),
        None,  # Success on retry
    ]
    notifier.bot = mock_bot

    # Act: Add notification
    await queue.add({"type": "test", "user_id": 123456789, "data": {"message": "test"}})

    # Act: Process with retry
    await notifier.process_queue()
    await asyncio.sleep(0.1)  # Wait for retry
    await notifier.process_queue()

    # Assert: Retried and succeeded
    assert mock_bot.send_message.call_count == 2


@pytest.mark.e2e()
@pytest.mark.asyncio()
async def test_notification_filtering_flow(notification_system):
    """Test notification filters are applied correctly."""
    queue, notifier = notification_system

    # Arrange: Mock bot and user settings
    mock_bot = AsyncMock()
    notifier.bot = mock_bot

    # Arrange: User has filter for min profit
    user_filter = {"min_profit_margin": 10.0}

    # Act: Add notifications with different profits
    await queue.add({
        "type": "arbitrage_opportunity",
        "user_id": 123456789,
        "data": {"profit_margin": 5.0},  # Below threshold
        "filters": user_filter,
    })

    await queue.add({
        "type": "arbitrage_opportunity",
        "user_id": 123456789,
        "data": {"profit_margin": 15.0},  # Above threshold
        "filters": user_filter,
    })

    # Act: Process
    await notifier.process_queue()

    # Assert: Only one notification sent (above threshold)
    assert mock_bot.send_message.call_count == 1

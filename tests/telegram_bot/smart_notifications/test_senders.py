"""Unit tests for smart_notifications/senders module.

Tests for notification sending functions including price alerts,
market opportunities, and generic user notifications.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_bot() -> MagicMock:
    """Create a mock Telegram Bot."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_notification_queue() -> MagicMock:
    """Create a mock NotificationQueue."""
    queue = MagicMock()
    queue.enqueue = AsyncMock()
    return queue


@pytest.fixture
def sample_alert() -> dict[str, Any]:
    """Create a sample alert."""
    return {
        "id": "alert_123",
        "item_id": "item_123",
        "item_name": "AK-47 | Redline",
        "game": "csgo",
        "active": True,
        "one_time": False,
        "conditions": {
            "price": 10.0,
            "condition": "below",
        },
    }


@pytest.fixture
def sample_item_data() -> dict[str, Any]:
    """Create sample item data from DMarket."""
    return {
        "itemId": "item_123",
        "title": "AK-47 | Redline",
        "price": {"USD": "900"},
        "suggestedPrice": {"USD": "1100"},
        "extra": {
            "offersCount": 50,
            "ordersCount": 25,
        },
    }


@pytest.fixture
def sample_user_prefs() -> dict[str, Any]:
    """Create sample user preferences."""
    return {
        "chat_id": 123456789,
        "enabled": True,
        "preferences": {
            "notification_style": "detailed",
        },
    }


@pytest.fixture
def sample_opportunity() -> dict[str, Any]:
    """Create sample market opportunity."""
    return {
        "item_id": "item_123",
        "item_name": "AK-47 | Redline",
        "game": "csgo",
        "opportunity_score": 75,
        "buy_price": 9.0,
        "potential_profit": 2.0,
        "profit_percent": 22.0,
        "trend": "bullish",
    }


# ============================================================================
# Tests for send_price_alert_notification
# ============================================================================


class TestSendPriceAlertNotification:
    """Tests for send_price_alert_notification function."""

    @pytest.mark.asyncio
    async def test_send_price_alert_direct_bot(
        self,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_item_data: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test sending price alert directly via bot."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification"
            ):
                await send_price_alert_notification(
                    bot=mock_bot,
                    user_id=123,
                    alert=sample_alert,
                    item_data=sample_item_data,
                    current_price=9.0,
                    user_prefs=sample_user_prefs,
                )

        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_price_alert_via_queue(
        self,
        mock_bot: MagicMock,
        mock_notification_queue: MagicMock,
        sample_alert: dict[str, Any],
        sample_item_data: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test sending price alert via notification queue."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification"
            ):
                await send_price_alert_notification(
                    bot=mock_bot,
                    user_id=123,
                    alert=sample_alert,
                    item_data=sample_item_data,
                    current_price=9.0,
                    user_prefs=sample_user_prefs,
                    notification_queue=mock_notification_queue,
                )

        mock_notification_queue.enqueue.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_price_alert_below_condition(
        self,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_item_data: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test price alert message for 'below' condition."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )

        sample_alert["conditions"]["condition"] = "below"

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification"
            ):
                await send_price_alert_notification(
                    bot=mock_bot,
                    user_id=123,
                    alert=sample_alert,
                    item_data=sample_item_data,
                    current_price=9.0,
                    user_prefs=sample_user_prefs,
                )

        call_args = mock_bot.send_message.call_args
        message = call_args.kwargs.get("text", "")
        assert "упала" in message.lower() or "$9.00" in message

    @pytest.mark.asyncio
    async def test_send_price_alert_above_condition(
        self,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_item_data: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test price alert message for 'above' condition."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )

        sample_alert["conditions"]["condition"] = "above"

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification"
            ):
                await send_price_alert_notification(
                    bot=mock_bot,
                    user_id=123,
                    alert=sample_alert,
                    item_data=sample_item_data,
                    current_price=15.0,
                    user_prefs=sample_user_prefs,
                )

        call_args = mock_bot.send_message.call_args
        message = call_args.kwargs.get("text", "")
        assert "поднялась" in message.lower() or "$15.00" in message

    @pytest.mark.asyncio
    async def test_send_price_alert_one_time_deactivates(
        self,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_item_data: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test that one-time alert is deactivated after sending."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )

        sample_alert["one_time"] = True

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification"
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.save_user_preferences"
                ):
                    await send_price_alert_notification(
                        bot=mock_bot,
                        user_id=123,
                        alert=sample_alert,
                        item_data=sample_item_data,
                        current_price=9.0,
                        user_prefs=sample_user_prefs,
                    )

        assert sample_alert["active"] is False

    @pytest.mark.asyncio
    async def test_send_price_alert_handles_exception(
        self,
        mock_bot: MagicMock,
        sample_alert: dict[str, Any],
        sample_item_data: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test that exceptions are handled gracefully."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )

        mock_bot.send_message.side_effect = Exception("Send failed")

        # Should not raise
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=123,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=9.0,
                user_prefs=sample_user_prefs,
            )


# ============================================================================
# Tests for send_market_opportunity_notification
# ============================================================================


class TestSendMarketOpportunityNotification:
    """Tests for send_market_opportunity_notification function."""

    @pytest.mark.asyncio
    async def test_send_market_opportunity_direct_bot(
        self,
        mock_bot: MagicMock,
        sample_opportunity: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test sending market opportunity directly via bot."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted opportunity",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Single message"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification"
                ):
                    await send_market_opportunity_notification(
                        bot=mock_bot,
                        user_id=123,
                        opportunity=sample_opportunity,
                        user_prefs=sample_user_prefs,
                    )

        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_market_opportunity_via_queue(
        self,
        mock_bot: MagicMock,
        mock_notification_queue: MagicMock,
        sample_opportunity: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test sending market opportunity via notification queue."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted opportunity",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Single message"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification"
                ):
                    await send_market_opportunity_notification(
                        bot=mock_bot,
                        user_id=123,
                        opportunity=sample_opportunity,
                        user_prefs=sample_user_prefs,
                        notification_queue=mock_notification_queue,
                    )

        mock_notification_queue.enqueue.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_market_opportunity_compact_style(
        self,
        mock_bot: MagicMock,
        sample_opportunity: dict[str, Any],
    ) -> None:
        """Test sending market opportunity with compact style."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )

        user_prefs = {
            "chat_id": 123,
            "preferences": {"notification_style": "compact"},
        }

        with patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Single message"],
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification"
            ):
                await send_market_opportunity_notification(
                    bot=mock_bot,
                    user_id=123,
                    opportunity=sample_opportunity,
                    user_prefs=user_prefs,
                )

        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_market_opportunity_high_score_title(
        self,
        mock_bot: MagicMock,
        sample_opportunity: dict[str, Any],
    ) -> None:
        """Test that high score opportunities get special title."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )

        sample_opportunity["opportunity_score"] = 85  # High score
        user_prefs = {
            "chat_id": 123,
            "preferences": {"notification_style": "compact"},
        }

        with patch(
            "src.telegram_bot.smart_notifications.senders.record_notification"
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=123,
                opportunity=sample_opportunity,
                user_prefs=user_prefs,
            )

        call_args = mock_bot.send_message.call_args
        message = call_args.kwargs.get("text", "")
        # The message should contain "ГОРЯЧАЯ" for high score
        assert "ГОРЯЧАЯ ВОЗМОЖНОСТЬ" in message or sample_opportunity["item_name"] in message

    @pytest.mark.asyncio
    async def test_send_market_opportunity_handles_exception(
        self,
        mock_bot: MagicMock,
        sample_opportunity: dict[str, Any],
        sample_user_prefs: dict[str, Any],
    ) -> None:
        """Test that exceptions are handled gracefully."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )

        mock_bot.send_message.side_effect = Exception("Send failed")

        # Should not raise
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Single message"],
            ):
                await send_market_opportunity_notification(
                    bot=mock_bot,
                    user_id=123,
                    opportunity=sample_opportunity,
                    user_prefs=sample_user_prefs,
                )


# ============================================================================
# Tests for notify_user
# ============================================================================


class TestNotifyUser:
    """Tests for notify_user function."""

    @pytest.mark.asyncio
    async def test_notify_user_direct_bot_success(self, mock_bot: MagicMock) -> None:
        """Test successful notification via bot."""
        from src.telegram_bot.smart_notifications.senders import notify_user

        result = await notify_user(
            bot=mock_bot,
            user_id=123,
            message="Test message",
        )

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_user_via_queue_success(
        self,
        mock_bot: MagicMock,
        mock_notification_queue: MagicMock,
    ) -> None:
        """Test successful notification via queue."""
        from src.telegram_bot.smart_notifications.senders import notify_user

        result = await notify_user(
            bot=mock_bot,
            user_id=123,
            message="Test message",
            notification_queue=mock_notification_queue,
        )

        assert result is True
        mock_notification_queue.enqueue.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_user_with_markup(self, mock_bot: MagicMock) -> None:
        """Test notification with reply markup."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        from src.telegram_bot.smart_notifications.senders import notify_user

        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Test", callback_data="test")]])

        result = await notify_user(
            bot=mock_bot,
            user_id=123,
            message="Test message",
            reply_markup=markup,
        )

        assert result is True
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs.get("reply_markup") is markup

    @pytest.mark.asyncio
    async def test_notify_user_failure(self, mock_bot: MagicMock) -> None:
        """Test notification failure returns False."""
        from src.telegram_bot.smart_notifications.senders import notify_user

        mock_bot.send_message.side_effect = Exception("Send failed")

        result = await notify_user(
            bot=mock_bot,
            user_id=123,
            message="Test message",
        )

        assert result is False

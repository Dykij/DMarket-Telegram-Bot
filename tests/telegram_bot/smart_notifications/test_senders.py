"""Comprehensive tests for smart_notifications/senders module.

Tests send_price_alert_notification, send_market_opportunity_notification,
and notify_user functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.telegram_bot.smart_notifications.senders import (
    send_price_alert_notification,
    send_market_opportunity_notification,
    notify_user,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_notification_queue():
    """Create a mock notification queue."""
    queue = AsyncMock()
    queue.enqueue = AsyncMock()
    return queue


@pytest.fixture
def sample_alert():
    """Create a sample alert dictionary."""
    return {
        "id": "alert_123",
        "item_name": "AK-47 | Redline",
        "item_id": "item_456",
        "game": "csgo",
        "conditions": {
            "price": 15.00,
            "condition": "below",
        },
        "one_time": False,
    }


@pytest.fixture
def sample_item_data():
    """Create sample item data."""
    return {
        "itemId": "item_456",
        "title": "AK-47 | Redline (Field-Tested)",
        "price": {"USD": "1450"},
        "suggestedPrice": {"USD": "1500"},
        "image": "https://example.com/image.png",
        "game": "csgo",
    }


@pytest.fixture
def sample_user_prefs():
    """Create sample user preferences."""
    return {
        "chat_id": 12345678,
        "preferences": {
            "notification_style": "detailed",
            "language": "ru",
        },
    }


@pytest.fixture
def sample_opportunity():
    """Create a sample market opportunity."""
    return {
        "item_name": "AK-47 | Redline",
        "item_id": "item_456",
        "game": "csgo",
        "opportunity_score": 75,
        "buy_price": 14.50,
        "potential_profit": 2.50,
        "profit_percent": 17.24,
        "trend": "uptrend",
    }


# =============================================================================
# send_price_alert_notification tests
# =============================================================================


class TestSendPriceAlertNotification:
    """Tests for send_price_alert_notification function."""

    @pytest.mark.asyncio
    async def test_send_alert_below_condition(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test sending alert with 'below' condition."""
        sample_alert["conditions"]["condition"] = "below"
        current_price = 14.00

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=current_price,
                user_prefs=sample_user_prefs,
            )

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 12345678
        assert "📉" in call_kwargs["text"]  # Price fell indicator
        assert "$14.00" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_alert_above_condition(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test sending alert with 'above' condition."""
        sample_alert["conditions"]["condition"] = "above"
        current_price = 16.00

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=current_price,
                user_prefs=sample_user_prefs,
            )

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert "📈" in call_kwargs["text"]  # Price rose indicator

    @pytest.mark.asyncio
    async def test_send_alert_other_condition(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test sending alert with other condition types."""
        sample_alert["conditions"]["condition"] = "equals"
        current_price = 15.00

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=current_price,
                user_prefs=sample_user_prefs,
            )

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert "🔄" in call_kwargs["text"]  # General indicator

    @pytest.mark.asyncio
    async def test_send_alert_with_notification_queue(
        self,
        mock_bot,
        mock_notification_queue,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test sending alert through notification queue."""
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=14.00,
                user_prefs=sample_user_prefs,
                notification_queue=mock_notification_queue,
            )

        mock_notification_queue.enqueue.assert_called_once()
        # Bot should NOT be called directly when queue is used
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_alert_one_time(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test one-time alert is deactivated after sending."""
        sample_alert["one_time"] = True
        sample_alert["active"] = True

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ), patch(
            "src.telegram_bot.smart_notifications.senders.save_user_preferences",
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=14.00,
                user_prefs=sample_user_prefs,
            )

        assert sample_alert["active"] is False

    @pytest.mark.asyncio
    async def test_send_alert_uses_chat_id_from_prefs(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test alert uses chat_id from preferences."""
        sample_user_prefs["chat_id"] = 99999999

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=14.00,
                user_prefs=sample_user_prefs,
            )

        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 99999999

    @pytest.mark.asyncio
    async def test_send_alert_fallback_to_user_id(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
    ):
        """Test alert falls back to user_id when chat_id not in prefs."""
        user_prefs_no_chat = {"preferences": {}}

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item: AK-47",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=14.00,
                user_prefs=user_prefs_no_chat,
            )

        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 12345678

    @pytest.mark.asyncio
    async def test_send_alert_truncates_long_message(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test alert message is truncated if too long."""
        # Create a very long formatted item
        long_item = "A" * 5000

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value=long_item,
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=14.00,
                user_prefs=sample_user_prefs,
            )

        call_kwargs = mock_bot.send_message.call_args.kwargs
        # Message should be truncated
        assert len(call_kwargs["text"]) <= 4096

    @pytest.mark.asyncio
    async def test_send_alert_handles_exception(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test alert gracefully handles exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Item",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            # Should not raise
            await send_price_alert_notification(
                bot=mock_bot,
                user_id=12345678,
                alert=sample_alert,
                item_data=sample_item_data,
                current_price=14.00,
                user_prefs=sample_user_prefs,
            )


# =============================================================================
# send_market_opportunity_notification tests
# =============================================================================


class TestSendMarketOpportunityNotification:
    """Tests for send_market_opportunity_notification function."""

    @pytest.mark.asyncio
    async def test_send_opportunity_detailed_style(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test sending opportunity with detailed notification style."""
        sample_user_prefs["preferences"]["notification_style"] = "detailed"

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted opportunities",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Formatted opportunities"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
            )

        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_opportunity_compact_style(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test sending opportunity with compact notification style."""
        sample_user_prefs["preferences"]["notification_style"] = "compact"

        with patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Compact notification"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
            )

        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_opportunity_high_score(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test hot opportunity with high score."""
        sample_opportunity["opportunity_score"] = 85
        sample_user_prefs["preferences"]["notification_style"] = "compact"

        with patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Hot notification"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
            )

        call_kwargs = mock_bot.send_message.call_args.kwargs
        # Should contain hot opportunity indicator
        assert mock_bot.send_message.called

    @pytest.mark.asyncio
    async def test_send_opportunity_medium_score(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test good opportunity with medium score."""
        sample_opportunity["opportunity_score"] = 65
        sample_user_prefs["preferences"]["notification_style"] = "compact"

        with patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Good notification"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
            )

        assert mock_bot.send_message.called

    @pytest.mark.asyncio
    async def test_send_opportunity_with_queue(
        self,
        mock_bot,
        mock_notification_queue,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test sending opportunity through notification queue."""
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Formatted"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
                notification_queue=mock_notification_queue,
            )

        mock_notification_queue.enqueue.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_opportunity_multiple_messages(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test sending opportunity that requires multiple messages."""
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Long formatted text",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Part 1", "Part 2", "Part 3"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
            )

        # Should have sent 3 messages
        assert mock_bot.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_send_opportunity_handles_exception(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test opportunity notification gracefully handles exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted",
        ), patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            return_value=["Formatted"],
        ), patch(
            "src.telegram_bot.smart_notifications.senders.record_notification",
            new_callable=AsyncMock,
        ):
            # Should not raise
            await send_market_opportunity_notification(
                bot=mock_bot,
                user_id=12345678,
                opportunity=sample_opportunity,
                user_prefs=sample_user_prefs,
            )


# =============================================================================
# notify_user tests
# =============================================================================


class TestNotifyUser:
    """Tests for notify_user function."""

    @pytest.mark.asyncio
    async def test_notify_user_success(self, mock_bot):
        """Test successful user notification."""
        result = await notify_user(
            bot=mock_bot,
            user_id=12345678,
            message="Test message",
        )

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_user_with_markup(self, mock_bot):
        """Test notification with reply markup."""
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Button", callback_data="test")]
        ])

        result = await notify_user(
            bot=mock_bot,
            user_id=12345678,
            message="Test message",
            reply_markup=markup,
        )

        assert result is True
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["reply_markup"] == markup

    @pytest.mark.asyncio
    async def test_notify_user_with_queue(self, mock_bot, mock_notification_queue):
        """Test notification through queue."""
        result = await notify_user(
            bot=mock_bot,
            user_id=12345678,
            message="Test message",
            notification_queue=mock_notification_queue,
        )

        assert result is True
        mock_notification_queue.enqueue.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_user_failure(self, mock_bot):
        """Test notification failure returns False."""
        mock_bot.send_message.side_effect = Exception("Network error")

        result = await notify_user(
            bot=mock_bot,
            user_id=12345678,
            message="Test message",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_notify_user_uses_markdown(self, mock_bot):
        """Test notification uses Markdown parse mode."""
        await notify_user(
            bot=mock_bot,
            user_id=12345678,
            message="*Bold* _italic_",
        )

        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["parse_mode"] is not None

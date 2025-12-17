"""Unit tests for smart_notifications/senders module.

Tests for notification sending functionality.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_bot():
    """Create mock Telegram Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_notification_queue():
    """Create mock NotificationQueue."""
    queue = AsyncMock()
    queue.enqueue = AsyncMock()
    return queue


@pytest.fixture
def sample_alert():
    """Create sample alert data."""
    return {
        "id": "alert123",
        "item_id": "item123",
        "item_name": "AK-47 | Redline",
        "game": "csgo",
        "conditions": {
            "price": 15.0,
            "condition": "below",
        },
        "one_time": False,
        "active": True,
    }


@pytest.fixture
def sample_item_data():
    """Create sample item data."""
    return {
        "itemId": "item123",
        "title": "AK-47 | Redline",
        "price": {"USD": "1000"},
        "game": "csgo",
    }


@pytest.fixture
def sample_user_prefs():
    """Create sample user preferences."""
    return {
        "chat_id": 123456,
        "enabled": True,
        "preferences": {
            "notification_style": "detailed",
        },
    }


@pytest.fixture
def sample_opportunity():
    """Create sample market opportunity."""
    return {
        "item_id": "item123",
        "item_name": "AK-47 | Redline",
        "game": "csgo",
        "opportunity_score": 75,
        "buy_price": 10.0,
        "potential_profit": 3.0,
        "profit_percent": 30.0,
        "trend": "bullish",
    }


# ============================================================================
# TESTS FOR send_price_alert_notification
# ============================================================================


class TestSendPriceAlertNotification:
    """Tests for send_price_alert_notification function."""

    @pytest.mark.asyncio()
    async def test_sends_notification_with_queue(
        self,
        mock_bot,
        mock_notification_queue,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test that notification is sent via queue when available."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    mock_notification_queue,
                )
                
                mock_notification_queue.enqueue.assert_called_once()
                mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_sends_notification_without_queue(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test that notification is sent directly when no queue."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,  # No queue
                )
                
                mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio()
    async def test_uses_chat_id_from_prefs(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test that chat_id from preferences is used."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        sample_user_prefs["chat_id"] = 999999
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,
                )
                
                call_args = mock_bot.send_message.call_args
                assert call_args.kwargs["chat_id"] == 999999

    @pytest.mark.asyncio()
    async def test_below_condition_message(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test message for 'below' price condition."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        sample_alert["conditions"]["condition"] = "below"
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,
                )
                
                call_args = mock_bot.send_message.call_args
                text = call_args.kwargs["text"]
                assert "📉" in text or "упала" in text.lower()

    @pytest.mark.asyncio()
    async def test_above_condition_message(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test message for 'above' price condition."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        sample_alert["conditions"]["condition"] = "above"
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,
                )
                
                call_args = mock_bot.send_message.call_args
                text = call_args.kwargs["text"]
                assert "📈" in text or "поднялась" in text.lower()

    @pytest.mark.asyncio()
    async def test_one_time_alert_deactivated(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test that one-time alert is deactivated after sending."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        sample_alert["one_time"] = True
        sample_alert["active"] = True
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.save_user_preferences"
                ):
                    await send_price_alert_notification(
                        mock_bot,
                        123456,
                        sample_alert,
                        sample_item_data,
                        10.0,
                        sample_user_prefs,
                        None,
                    )
                    
                    assert sample_alert["active"] is False

    @pytest.mark.asyncio()
    async def test_records_notification(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test that notification is recorded."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ) as mock_record:
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,
                )
                
                mock_record.assert_called_once_with(
                    123456, "price_alert", sample_alert.get("item_id")
                )

    @pytest.mark.asyncio()
    async def test_long_message_truncated(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test that very long messages are truncated."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        # Create a very long formatted item string
        long_item = "X" * 5000
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value=long_item,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,
                )
                
                call_args = mock_bot.send_message.call_args
                text = call_args.kwargs["text"]
                assert len(text) <= 4096  # Telegram limit

    @pytest.mark.asyncio()
    async def test_error_handling(
        self,
        mock_bot,
        sample_alert,
        sample_item_data,
        sample_user_prefs,
    ):
        """Test error handling during notification sending."""
        from src.telegram_bot.smart_notifications.senders import (
            send_price_alert_notification,
        )
        
        mock_bot.send_message.side_effect = Exception("Test error")
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_market_item",
            return_value="Formatted item",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                # Should not raise
                await send_price_alert_notification(
                    mock_bot,
                    123456,
                    sample_alert,
                    sample_item_data,
                    10.0,
                    sample_user_prefs,
                    None,
                )


# ============================================================================
# TESTS FOR send_market_opportunity_notification
# ============================================================================


class TestSendMarketOpportunityNotification:
    """Tests for send_market_opportunity_notification function."""

    @pytest.mark.asyncio()
    async def test_sends_notification_with_queue(
        self,
        mock_bot,
        mock_notification_queue,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test that notification is sent via queue when available."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted opportunities",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Message part"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification",
                    new_callable=AsyncMock,
                ):
                    await send_market_opportunity_notification(
                        mock_bot,
                        123456,
                        sample_opportunity,
                        sample_user_prefs,
                        mock_notification_queue,
                    )
                    
                    mock_notification_queue.enqueue.assert_called()
                    mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_sends_notification_without_queue(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test that notification is sent directly when no queue."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted opportunities",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Message part"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification",
                    new_callable=AsyncMock,
                ):
                    await send_market_opportunity_notification(
                        mock_bot,
                        123456,
                        sample_opportunity,
                        sample_user_prefs,
                        None,
                    )
                    
                    mock_bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_compact_style(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test compact notification style."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        sample_user_prefs["preferences"]["notification_style"] = "compact"
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            side_effect=lambda x: [x],  # Return original text wrapped in list
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_market_opportunity_notification(
                    mock_bot,
                    123456,
                    sample_opportunity,
                    sample_user_prefs,
                    None,
                )
                
                call_args = mock_bot.send_message.call_args
                text = call_args.kwargs["text"]
                
                # Compact style should include price info - check for any price format
                assert "10" in text or "$" in text or "Цена" in text

    @pytest.mark.asyncio()
    async def test_high_score_hot_opportunity(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test that high score opportunities are marked as hot."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        sample_opportunity["opportunity_score"] = 85
        sample_user_prefs["preferences"]["notification_style"] = "compact"
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.split_long_message",
            side_effect=lambda x: [x],  # Return original text wrapped in list
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.record_notification",
                new_callable=AsyncMock,
            ):
                await send_market_opportunity_notification(
                    mock_bot,
                    123456,
                    sample_opportunity,
                    sample_user_prefs,
                    None,
                )
                
                call_args = mock_bot.send_message.call_args
                text = call_args.kwargs["text"]
                
                # High score should trigger special formatting
                assert "🔥" in text or "ГОРЯЧАЯ" in text or "85" in text

    @pytest.mark.asyncio()
    async def test_detailed_style(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test detailed notification style."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        sample_user_prefs["preferences"]["notification_style"] = "detailed"
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Detailed formatted",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Message"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification",
                    new_callable=AsyncMock,
                ):
                    await send_market_opportunity_notification(
                        mock_bot,
                        123456,
                        sample_opportunity,
                        sample_user_prefs,
                        None,
                    )
                    
                    # Should use format_opportunities for detailed style
                    mock_bot.send_message.assert_called()

    @pytest.mark.asyncio()
    async def test_records_notification(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test that notification is recorded."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Message"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification",
                    new_callable=AsyncMock,
                ) as mock_record:
                    await send_market_opportunity_notification(
                        mock_bot,
                        123456,
                        sample_opportunity,
                        sample_user_prefs,
                        None,
                    )
                    
                    mock_record.assert_called_once_with(
                        123456,
                        "market_opportunity",
                        sample_opportunity.get("item_id"),
                    )

    @pytest.mark.asyncio()
    async def test_error_handling(
        self,
        mock_bot,
        sample_opportunity,
        sample_user_prefs,
    ):
        """Test error handling during notification sending."""
        from src.telegram_bot.smart_notifications.senders import (
            send_market_opportunity_notification,
        )
        
        mock_bot.send_message.side_effect = Exception("Test error")
        
        with patch(
            "src.telegram_bot.smart_notifications.senders.format_opportunities",
            return_value="Formatted",
        ):
            with patch(
                "src.telegram_bot.smart_notifications.senders.split_long_message",
                return_value=["Message"],
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.senders.record_notification",
                    new_callable=AsyncMock,
                ):
                    # Should not raise
                    await send_market_opportunity_notification(
                        mock_bot,
                        123456,
                        sample_opportunity,
                        sample_user_prefs,
                        None,
                    )


# ============================================================================
# TESTS FOR notify_user
# ============================================================================


class TestNotifyUser:
    """Tests for notify_user function."""

    @pytest.mark.asyncio()
    async def test_sends_via_queue(self, mock_bot, mock_notification_queue):
        """Test sending via notification queue."""
        from src.telegram_bot.smart_notifications.senders import notify_user
        
        result = await notify_user(
            mock_bot,
            123456,
            "Test message",
            notification_queue=mock_notification_queue,
        )
        
        assert result is True
        mock_notification_queue.enqueue.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_sends_directly(self, mock_bot):
        """Test sending directly without queue."""
        from src.telegram_bot.smart_notifications.senders import notify_user
        
        result = await notify_user(
            mock_bot,
            123456,
            "Test message",
        )
        
        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio()
    async def test_with_reply_markup(self, mock_bot):
        """Test sending with reply markup."""
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        from src.telegram_bot.smart_notifications.senders import notify_user
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Test", callback_data="test")]
        ])
        
        result = await notify_user(
            mock_bot,
            123456,
            "Test message",
            reply_markup=markup,
        )
        
        assert result is True
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["reply_markup"] == markup

    @pytest.mark.asyncio()
    async def test_returns_false_on_error(self, mock_bot):
        """Test that False is returned on error."""
        from src.telegram_bot.smart_notifications.senders import notify_user
        
        mock_bot.send_message.side_effect = Exception("Test error")
        
        result = await notify_user(
            mock_bot,
            123456,
            "Test message",
        )
        
        assert result is False

    @pytest.mark.asyncio()
    async def test_uses_markdown_parse_mode(self, mock_bot):
        """Test that Markdown parse mode is used."""
        from src.telegram_bot.smart_notifications.senders import notify_user
        
        await notify_user(
            mock_bot,
            123456,
            "Test message",
        )
        
        call_args = mock_bot.send_message.call_args
        from telegram.constants import ParseMode
        assert call_args.kwargs["parse_mode"] == ParseMode.MARKDOWN

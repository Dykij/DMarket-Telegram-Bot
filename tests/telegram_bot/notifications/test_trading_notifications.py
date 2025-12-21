"""Comprehensive tests for telegram_bot.notifications.trading module.

This module tests all trading notification functions:
- send_buy_intent_notification
- send_buy_success_notification
- send_buy_failed_notification
- send_sell_success_notification
- send_critical_shutdown_notification
- send_crash_notification

Coverage target: 85%+
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_bot() -> AsyncMock:
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    return bot


@pytest.fixture
def sample_item() -> dict[str, Any]:
    """Sample item data for tests."""
    return {
        "title": "AK-47 | Redline (Field-Tested)",
        "price": {"USD": 1500},  # $15.00 in cents
        "game": "csgo",
        "itemId": "item_12345",
    }


@pytest.fixture
def sample_item_minimal() -> dict[str, Any]:
    """Minimal item data (missing fields)."""
    return {}


@pytest.fixture
def sample_item_dota() -> dict[str, Any]:
    """Sample Dota 2 item."""
    return {
        "title": "Dragonclaw Hook",
        "price": {"USD": 50000},  # $500.00
        "game": "dota2",
    }


# ============================================================================
# send_buy_intent_notification Tests
# ============================================================================


class TestSendBuyIntentNotification:
    """Tests for send_buy_intent_notification function."""

    @pytest.mark.asyncio
    async def test_sends_notification_successfully(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test successful buy intent notification."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                reason="Good profit margin",
            )

            assert result is True
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_item_title_in_message(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that item title is included in the message."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "AK-47 | Redline" in message_text

    @pytest.mark.asyncio
    async def test_includes_price_in_message(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that price is correctly formatted in the message."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$15.00" in message_text

    @pytest.mark.asyncio
    async def test_includes_game_in_message(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that game is included in the message."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "CSGO" in message_text

    @pytest.mark.asyncio
    async def test_includes_reason_when_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that reason is included when provided."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                reason="High liquidity item",
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "High liquidity item" in message_text

    @pytest.mark.asyncio
    async def test_adds_keyboard_when_callback_data_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that inline keyboard is added when callback_data is provided."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                callback_data="item_12345",
            )

            call_args = mock_bot.send_message.call_args
            keyboard = call_args.kwargs.get("reply_markup")
            assert keyboard is not None
            assert isinstance(keyboard, InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_no_keyboard_when_callback_data_not_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that no keyboard is added when callback_data is None."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            call_args = mock_bot.send_message.call_args
            keyboard = call_args.kwargs.get("reply_markup")
            assert keyboard is None

    @pytest.mark.asyncio
    async def test_returns_false_when_notification_blocked(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that False is returned when notification is blocked."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=False,
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            assert result is False
            mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_send_message_exception(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test graceful handling of send_message exceptions."""
        mock_bot.send_message.side_effect = Exception("Telegram API error")

        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_handles_missing_item_title(
        self, mock_bot: AsyncMock, sample_item_minimal: dict[str, Any]
    ) -> None:
        """Test handling of item without title."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item_minimal,
            )

            assert result is True
            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "Unknown Item" in message_text

    @pytest.mark.asyncio
    async def test_handles_missing_price(
        self, mock_bot: AsyncMock, sample_item_minimal: dict[str, Any]
    ) -> None:
        """Test handling of item without price."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item_minimal,
            )

            assert result is True
            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$0.00" in message_text

    @pytest.mark.asyncio
    async def test_uses_html_parse_mode(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that HTML parse mode is used."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
            )

            call_args = mock_bot.send_message.call_args
            assert call_args.kwargs["parse_mode"] == "HTML"


# ============================================================================
# send_buy_success_notification Tests
# ============================================================================


class TestSendBuySuccessNotification:
    """Tests for send_buy_success_notification function."""

    @pytest.mark.asyncio
    async def test_sends_notification_successfully(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test successful buy success notification."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            result = await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                buy_price=15.00,
            )

            assert result is True
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_item_title(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that item title is included in message."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                buy_price=15.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "AK-47 | Redline" in message_text

    @pytest.mark.asyncio
    async def test_includes_buy_price(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that buy price is included in message."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                buy_price=15.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$15.00" in message_text

    @pytest.mark.asyncio
    async def test_includes_order_id_when_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that order ID is included when provided."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                buy_price=15.00,
                order_id="order_abc123",
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "order_abc123" in message_text

    @pytest.mark.asyncio
    async def test_no_order_id_when_not_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test message without order ID."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                buy_price=15.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "ID заказа" not in message_text

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test graceful handling of exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        from src.telegram_bot.notifications.trading import (
            send_buy_success_notification,
        )

        result = await send_buy_success_notification(
            bot=mock_bot,
            user_id=123456,
            item=sample_item,
            buy_price=15.00,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_handles_missing_title(
        self, mock_bot: AsyncMock, sample_item_minimal: dict[str, Any]
    ) -> None:
        """Test handling of item without title."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            result = await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item_minimal,
                buy_price=10.00,
            )

            assert result is True
            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "Unknown Item" in message_text


# ============================================================================
# send_buy_failed_notification Tests
# ============================================================================


class TestSendBuyFailedNotification:
    """Tests for send_buy_failed_notification function."""

    @pytest.mark.asyncio
    async def test_sends_notification_successfully(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test successful buy failed notification."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_failed_notification,
            )

            result = await send_buy_failed_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                error="Insufficient balance",
            )

            assert result is True
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_error_message(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that error message is included."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_failed_notification,
            )

            await send_buy_failed_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                error="Item already sold",
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "Item already sold" in message_text

    @pytest.mark.asyncio
    async def test_includes_item_title(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that item title is included."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_failed_notification,
            )

            await send_buy_failed_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                error="Error",
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "AK-47 | Redline" in message_text

    @pytest.mark.asyncio
    async def test_includes_price(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that price is included."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_failed_notification,
            )

            await send_buy_failed_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                error="Error",
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$15.00" in message_text

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test graceful handling of exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        from src.telegram_bot.notifications.trading import (
            send_buy_failed_notification,
        )

        result = await send_buy_failed_notification(
            bot=mock_bot,
            user_id=123456,
            item=sample_item,
            error="Error",
        )

        assert result is False


# ============================================================================
# send_sell_success_notification Tests
# ============================================================================


class TestSendSellSuccessNotification:
    """Tests for send_sell_success_notification function."""

    @pytest.mark.asyncio
    async def test_sends_notification_successfully(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test successful sell notification."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            result = await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
            )

            assert result is True
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_sell_price(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that sell price is included."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$20.00" in message_text

    @pytest.mark.asyncio
    async def test_shows_profit_when_buy_price_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that profit is calculated when buy_price is provided."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
                buy_price=15.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$5.00" in message_text  # Profit
            assert "📈" in message_text  # Positive profit emoji

    @pytest.mark.asyncio
    async def test_shows_loss_with_correct_emoji(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that loss is shown with correct emoji."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=10.00,
                buy_price=15.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "📉" in message_text  # Negative profit emoji

    @pytest.mark.asyncio
    async def test_shows_profit_percentage(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that profit percentage is shown."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
                buy_price=10.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "+100.0%" in message_text

    @pytest.mark.asyncio
    async def test_no_profit_when_buy_price_not_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that no profit is shown when buy_price is None."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "Прибыль" not in message_text

    @pytest.mark.asyncio
    async def test_includes_offer_id_when_provided(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test that offer ID is included when provided."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
                offer_id="offer_xyz789",
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "offer_xyz789" in message_text

    @pytest.mark.asyncio
    async def test_handles_zero_buy_price(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test handling of zero buy price (division by zero protection)."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_sell_success_notification,
            )

            result = await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
                buy_price=0,
            )

            assert result is True
            # Should not crash with division by zero

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test graceful handling of exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        from src.telegram_bot.notifications.trading import (
            send_sell_success_notification,
        )

        result = await send_sell_success_notification(
            bot=mock_bot,
            user_id=123456,
            item=sample_item,
            sell_price=20.00,
        )

        assert result is False


# ============================================================================
# send_critical_shutdown_notification Tests
# ============================================================================


class TestSendCriticalShutdownNotification:
    """Tests for send_critical_shutdown_notification function."""

    @pytest.mark.asyncio
    async def test_sends_notification_successfully(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test successful critical shutdown notification."""
        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        result = await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="API rate limit exceeded",
        )

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_reason(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that reason is included in message."""
        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="Memory overflow detected",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "Memory overflow detected" in message_text

    @pytest.mark.asyncio
    async def test_includes_critical_header(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that critical header is in message."""
        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="Error",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "КРИТИЧЕСКОЕ ОТКЛЮЧЕНИЕ" in message_text

    @pytest.mark.asyncio
    async def test_includes_details_when_provided(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that details are included when provided."""
        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="API error",
            details={
                "error_code": 500,
                "endpoint": "/market/items",
                "retry_count": 3,
            },
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "error_code" in message_text
        assert "500" in message_text
        assert "endpoint" in message_text

    @pytest.mark.asyncio
    async def test_no_details_section_when_not_provided(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that details section is not present when not provided."""
        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="Generic error",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "Детали" not in message_text

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test graceful handling of exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        result = await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="Error",
        )

        assert result is False


# ============================================================================
# send_crash_notification Tests
# ============================================================================


class TestSendCrashNotification:
    """Tests for send_crash_notification function."""

    @pytest.mark.asyncio
    async def test_sends_notification_successfully(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test successful crash notification."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        result = await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="ValueError",
            error_message="Invalid price format",
        )

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_error_type(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that error type is included."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="KeyError",
            error_message="Missing key",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "KeyError" in message_text

    @pytest.mark.asyncio
    async def test_includes_error_message(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that error message is included."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="Exception",
            error_message="Unexpected error occurred",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "Unexpected error occurred" in message_text

    @pytest.mark.asyncio
    async def test_includes_crash_header(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that CRASH REPORT header is present."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="Exception",
            error_message="Error",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "CRASH REPORT" in message_text

    @pytest.mark.asyncio
    async def test_includes_traceback_when_provided(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that traceback is included when provided."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        traceback = """Traceback (most recent call last):
  File "main.py", line 10, in <module>
    raise ValueError("test")
ValueError: test"""

        await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="ValueError",
            error_message="test",
            traceback_str=traceback,
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "Traceback" in message_text

    @pytest.mark.asyncio
    async def test_truncates_long_traceback(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that long tracebacks are truncated."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        # Create a very long traceback
        long_traceback = "A" * 2000

        await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="Exception",
            error_message="Error",
            traceback_str=long_traceback,
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "[truncated]" in message_text

    @pytest.mark.asyncio
    async def test_no_traceback_section_when_not_provided(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test that traceback section is not present when not provided."""
        from src.telegram_bot.notifications.trading import send_crash_notification

        await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="Exception",
            error_message="Error",
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "Traceback" not in message_text

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test graceful handling of exceptions."""
        mock_bot.send_message.side_effect = Exception("Network error")

        from src.telegram_bot.notifications.trading import send_crash_notification

        result = await send_crash_notification(
            bot=mock_bot,
            user_id=123456,
            error_type="Exception",
            error_message="Error",
        )

        assert result is False


# ============================================================================
# Integration Tests
# ============================================================================


class TestTradingNotificationsIntegration:
    """Integration tests for trading notifications."""

    @pytest.mark.asyncio
    async def test_full_trading_cycle_notifications(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test sending notifications for a full trading cycle."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
                send_buy_success_notification,
                send_sell_success_notification,
            )

            # 1. Intent to buy
            result1 = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                reason="Good deal",
                callback_data="item_123",
            )
            assert result1 is True

            # 2. Buy success
            result2 = await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                buy_price=15.00,
                order_id="order_123",
            )
            assert result2 is True

            # 3. Sell success
            result3 = await send_sell_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                sell_price=20.00,
                buy_price=15.00,
                offer_id="offer_456",
            )
            assert result3 is True

            # Verify all notifications were sent
            assert mock_bot.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_failed_buy_cycle(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test notifications for a failed buy attempt."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
                send_buy_failed_notification,
            )

            # 1. Intent to buy
            result1 = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                reason="Looks profitable",
            )
            assert result1 is True

            # 2. Buy failed
            result2 = await send_buy_failed_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                error="Item was already sold",
            )
            assert result2 is True

            assert mock_bot.send_message.call_count == 2


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestTradingNotificationsEdgeCases:
    """Edge case tests for trading notifications."""

    @pytest.mark.asyncio
    async def test_very_high_price_formatting(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test formatting of very high prices."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            high_price_item = {
                "title": "Dragon Lore",
                "price": {"USD": 10000000},  # $100,000
                "game": "csgo",
            }

            await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=high_price_item,
                buy_price=100000.00,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$100000.00" in message_text

    @pytest.mark.asyncio
    async def test_very_low_price_formatting(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test formatting of very low prices."""
        with patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_success_notification,
            )

            low_price_item = {
                "title": "Cheap Item",
                "price": {"USD": 1},  # $0.01
                "game": "csgo",
            }

            await send_buy_success_notification(
                bot=mock_bot,
                user_id=123456,
                item=low_price_item,
                buy_price=0.01,
            )

            call_args = mock_bot.send_message.call_args
            message_text = call_args.kwargs["text"]
            assert "$0.01" in message_text

    @pytest.mark.asyncio
    async def test_special_characters_in_item_title(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test handling of special characters in item title."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            special_item = {
                "title": "<script>alert('xss')</script> | Item™",
                "price": {"USD": 1000},
                "game": "csgo",
            }

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=special_item,
            )

            assert result is True
            # Message should be sent (HTML escaping handled by Telegram)

    @pytest.mark.asyncio
    async def test_unicode_in_reason(
        self, mock_bot: AsyncMock, sample_item: dict[str, Any]
    ) -> None:
        """Test handling of unicode characters in reason."""
        with patch(
            "src.telegram_bot.notifications.trading.can_send_notification",
            return_value=True,
        ), patch(
            "src.telegram_bot.notifications.trading.increment_notification_count"
        ):
            from src.telegram_bot.notifications.trading import (
                send_buy_intent_notification,
            )

            result = await send_buy_intent_notification(
                bot=mock_bot,
                user_id=123456,
                item=sample_item,
                reason="Хорошая сделка 🔥 Профит гарантирован! 💰",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_empty_details_dict(
        self, mock_bot: AsyncMock
    ) -> None:
        """Test handling of empty details dict.
        
        Empty dict is falsy in Python, so no details section should be added.
        """
        from src.telegram_bot.notifications.trading import (
            send_critical_shutdown_notification,
        )

        await send_critical_shutdown_notification(
            bot=mock_bot,
            user_id=123456,
            reason="Test",
            details={},
        )

        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        # Empty dict is falsy, so details section should NOT be added
        assert "Детали" not in message_text

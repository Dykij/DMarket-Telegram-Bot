"""Tests for smart_notifications/handlers.py module.

Covers:
- handle_notification_callback function
- register_notification_handlers function
- disable_alert callback
- track_item callback
- Alert creation and management
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ParseMode


class TestHandleNotificationCallback:
    """Tests for handle_notification_callback function."""

    @pytest.mark.asyncio
    async def test_handle_callback_no_query(self) -> None:
        """Test handling callback with no query."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        update.callback_query = None
        context = MagicMock()

        # Should return without error
        await handle_notification_callback(update, context)

    @pytest.mark.asyncio
    async def test_handle_callback_no_data(self) -> None:
        """Test handling callback with no data."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock()
        update.callback_query.data = None
        context = MagicMock()

        # Should return without error
        await handle_notification_callback(update, context)

    @pytest.mark.asyncio
    async def test_disable_alert_success(self) -> None:
        """Test disabling alert successfully."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "disable_alert:alert-123"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original message"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()

        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            new_callable=AsyncMock,
            return_value=True,
        ):
            await handle_notification_callback(update, context)

            query.answer.assert_called_once()
            query.edit_message_text.assert_called_once()
            call_kwargs = query.edit_message_text.call_args
            assert "✅ Alert has been disabled" in call_kwargs.kwargs.get(
                "text", call_kwargs.args[0] if call_kwargs.args else ""
            )

    @pytest.mark.asyncio
    async def test_disable_alert_failure(self) -> None:
        """Test disabling alert when it fails."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "disable_alert:nonexistent"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original message"
        query.answer = AsyncMock()
        query.edit_message_reply_markup = AsyncMock()
        update.callback_query = query

        context = MagicMock()

        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            new_callable=AsyncMock,
            return_value=False,
        ):
            await handle_notification_callback(update, context)

            query.answer.assert_called_once()
            query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)

    @pytest.mark.asyncio
    async def test_track_item_no_api(self) -> None:
        """Test tracking item when API is not available."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "track_item:item_123:csgo"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original message"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.bot_data = {}  # No API

        await handle_notification_callback(update, context)

        query.edit_message_text.assert_called_once()
        call_kwargs = query.edit_message_text.call_args
        text = call_kwargs.kwargs.get("text", call_kwargs.args[0] if call_kwargs.args else "")
        assert "API not available" in text

    @pytest.mark.asyncio
    async def test_track_item_item_not_found(self) -> None:
        """Test tracking item when item is not found."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "track_item:nonexistent:csgo"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original message"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        mock_api = MagicMock()
        context = MagicMock()
        context.bot_data = {"dmarket_api": mock_api}

        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            new_callable=AsyncMock,
            return_value=None,  # Item not found
        ):
            await handle_notification_callback(update, context)

            call_kwargs = query.edit_message_text.call_args
            text = call_kwargs.kwargs.get("text", call_kwargs.args[0] if call_kwargs.args else "")
            assert "Item not found" in text

    @pytest.mark.asyncio
    async def test_track_item_success(self) -> None:
        """Test tracking item successfully."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "track_item:item_abc:csgo"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original message"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        mock_api = MagicMock()
        context = MagicMock()
        context.bot_data = {"dmarket_api": mock_api}

        mock_item_data = {
            "title": "Test Item",
            "price": {"amount": 1000},  # $10.00
        }

        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            new_callable=AsyncMock,
            return_value=mock_item_data,
        ), patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_price",
            return_value=10.0,
        ), patch(
            "src.telegram_bot.smart_notifications.handlers.create_alert",
            new_callable=AsyncMock,
        ) as mock_create_alert:
            await handle_notification_callback(update, context)

            # Should create two alerts (below and above)
            assert mock_create_alert.call_count == 2
            
            # Check edit message was called with success
            call_kwargs = query.edit_message_text.call_args
            text = call_kwargs.kwargs.get("text", call_kwargs.args[0] if call_kwargs.args else "")
            assert "Alerts created" in text

    @pytest.mark.asyncio
    async def test_track_item_default_game(self) -> None:
        """Test tracking item uses default game when not specified."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "track_item:item_xyz"  # No game specified
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        mock_api = MagicMock()
        context = MagicMock()
        context.bot_data = {"dmarket_api": mock_api}

        mock_item_data = {"title": "Item", "price": {"amount": 500}}

        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            new_callable=AsyncMock,
            return_value=mock_item_data,
        ) as mock_get_item, patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_price",
            return_value=5.0,
        ), patch(
            "src.telegram_bot.smart_notifications.handlers.create_alert",
            new_callable=AsyncMock,
        ):
            await handle_notification_callback(update, context)

            # Should use "csgo" as default game
            mock_get_item.assert_called_once_with(mock_api, "item_xyz", "csgo")

    @pytest.mark.asyncio
    async def test_track_item_error_handling(self) -> None:
        """Test error handling during item tracking."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "track_item:item_err:csgo"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.text = "Original"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        mock_api = MagicMock()
        context = MagicMock()
        context.bot_data = {"dmarket_api": mock_api}

        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            await handle_notification_callback(update, context)

            call_kwargs = query.edit_message_text.call_args
            text = call_kwargs.kwargs.get("text", call_kwargs.args[0] if call_kwargs.args else "")
            assert "Error creating alert" in text

    @pytest.mark.asyncio
    async def test_handle_callback_answers_query(self) -> None:
        """Test that callback always answers the query."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "disable_alert:test"
        query.from_user = MagicMock(id=1)
        query.message = MagicMock()
        query.message.text = "msg"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()

        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            new_callable=AsyncMock,
            return_value=True,
        ):
            await handle_notification_callback(update, context)

            query.answer.assert_called_once()


class TestRegisterNotificationHandlers:
    """Tests for register_notification_handlers function."""

    def test_register_handlers_adds_callback_handler(self) -> None:
        """Test that register adds callback query handler."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )

        app = MagicMock()
        app.bot_data = {}  # No API

        register_notification_handlers(app)

        app.add_handler.assert_called_once()

    def test_register_handlers_starts_checker_with_api(self) -> None:
        """Test that register starts checker when API is available."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )

        mock_api = MagicMock()
        mock_bot = MagicMock()
        mock_queue = MagicMock()

        app = MagicMock()
        app.bot_data = {
            "dmarket_api": mock_api,
            "notification_queue": mock_queue,
        }
        app.bot = mock_bot

        with patch(
            "src.telegram_bot.smart_notifications.handlers.asyncio.create_task"
        ) as mock_create_task:
            mock_create_task.return_value = MagicMock(get_name=MagicMock(return_value="test"))

            register_notification_handlers(app)

            mock_create_task.assert_called_once()

    def test_register_handlers_no_checker_without_api(self) -> None:
        """Test that register doesn't start checker without API."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )

        app = MagicMock()
        app.bot_data = {}  # No API

        with patch(
            "src.telegram_bot.smart_notifications.handlers.asyncio.create_task"
        ) as mock_create_task:
            register_notification_handlers(app)

            # Should not create task without API
            mock_create_task.assert_not_called()


class TestMessageTextHandling:
    """Tests for message text handling in callbacks."""

    @pytest.mark.asyncio
    async def test_handle_callback_no_message(self) -> None:
        """Test handling when message is None."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "disable_alert:test"
        query.from_user = MagicMock(id=1)
        query.message = None  # No message
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()

        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            new_callable=AsyncMock,
            return_value=True,
        ):
            # Should handle gracefully
            await handle_notification_callback(update, context)

    @pytest.mark.asyncio
    async def test_handle_callback_no_message_text(self) -> None:
        """Test handling when message.text is None."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )

        update = MagicMock(spec=Update)
        query = MagicMock()
        query.data = "disable_alert:test"
        query.from_user = MagicMock(id=1)
        query.message = MagicMock()
        query.message.text = None  # No text
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()

        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            new_callable=AsyncMock,
            return_value=True,
        ):
            # Should handle gracefully
            await handle_notification_callback(update, context)
            query.edit_message_text.assert_called_once()

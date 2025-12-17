"""Unit tests for smart_notifications/handlers module.

Tests for notification callback handlers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Update, User


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_callback_query():
    """Create mock CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()
    query.data = "disable_alert:alert123"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123456
    query.message = MagicMock()
    query.message.text = "Test message"
    return query


@pytest.fixture
def mock_update(mock_callback_query):
    """Create mock Update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    return update


@pytest.fixture
def mock_context():
    """Create mock callback context."""
    context = MagicMock()
    context.bot_data = {}
    return context


# ============================================================================
# TESTS FOR handle_notification_callback
# ============================================================================


class TestHandleNotificationCallback:
    """Tests for handle_notification_callback function."""

    @pytest.mark.asyncio()
    async def test_no_callback_query(self, mock_context):
        """Test when there is no callback query."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        update = MagicMock(spec=Update)
        update.callback_query = None
        
        await handle_notification_callback(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio()
    async def test_no_query_data(self, mock_context):
        """Test when callback query has no data."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        update = MagicMock(spec=Update)
        query = MagicMock(spec=CallbackQuery)
        query.data = None
        update.callback_query = query
        
        await handle_notification_callback(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio()
    async def test_disable_alert_success(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test successful alert disabling."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "disable_alert:alert123"
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            return_value=True,
        ):
            await handle_notification_callback(mock_update, mock_context)
            
            mock_callback_query.answer.assert_called_once()
            mock_callback_query.edit_message_text.assert_called_once()
            
            # Check that success message was shown
            call_args = mock_callback_query.edit_message_text.call_args
            text = call_args.kwargs.get("text", call_args[0][0] if call_args[0] else "")
            assert "✅" in text or "disabled" in text.lower()

    @pytest.mark.asyncio()
    async def test_disable_alert_failure(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test failed alert disabling."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "disable_alert:alert123"
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.deactivate_alert",
            return_value=False,
        ):
            await handle_notification_callback(mock_update, mock_context)
            
            mock_callback_query.answer.assert_called_once()
            # Should remove reply markup
            mock_callback_query.edit_message_reply_markup.assert_called_once_with(
                reply_markup=None
            )

    @pytest.mark.asyncio()
    async def test_track_item_no_api(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test tracking item when API is not available."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123:csgo"
        mock_context.bot_data = {}  # No API
        
        await handle_notification_callback(mock_update, mock_context)
        
        mock_callback_query.answer.assert_called_once()
        
        # Check error message
        call_args = mock_callback_query.edit_message_text.call_args
        text = call_args.kwargs.get("text", call_args[0][0] if call_args[0] else "")
        assert "❌" in text or "not available" in text.lower()

    @pytest.mark.asyncio()
    async def test_track_item_not_found(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test tracking item when item is not found."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123:csgo"
        mock_api = AsyncMock()
        mock_context.bot_data = {"dmarket_api": mock_api}
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            return_value=None,
        ):
            await handle_notification_callback(mock_update, mock_context)
            
            # Check error message
            call_args = mock_callback_query.edit_message_text.call_args
            text = call_args.kwargs.get("text", call_args[0][0] if call_args[0] else "")
            assert "❌" in text or "not found" in text.lower()

    @pytest.mark.asyncio()
    async def test_track_item_success(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test successful item tracking."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123:csgo"
        mock_api = AsyncMock()
        mock_context.bot_data = {"dmarket_api": mock_api}
        
        item_data = {
            "itemId": "item123",
            "title": "Test Item",
            "price": {"USD": "1000"},
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            return_value=item_data,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.handlers.get_item_price",
                return_value=10.0,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.handlers.create_alert",
                    new_callable=AsyncMock,
                ) as mock_create:
                    await handle_notification_callback(mock_update, mock_context)
                    
                    # Should create two alerts (above and below)
                    assert mock_create.call_count == 2

    @pytest.mark.asyncio()
    async def test_track_item_creates_below_alert(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test that tracking creates a 'below price' alert."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123:csgo"
        mock_api = AsyncMock()
        mock_context.bot_data = {"dmarket_api": mock_api}
        
        item_data = {
            "itemId": "item123",
            "title": "Test Item",
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            return_value=item_data,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.handlers.get_item_price",
                return_value=10.0,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.handlers.create_alert",
                    new_callable=AsyncMock,
                ) as mock_create:
                    await handle_notification_callback(mock_update, mock_context)
                    
                    # Check first call (below alert)
                    calls = mock_create.call_args_list
                    below_call = calls[0]
                    
                    assert below_call.kwargs["conditions"]["direction"] == "below"
                    assert below_call.kwargs["conditions"]["price"] == 9.0  # 10% below

    @pytest.mark.asyncio()
    async def test_track_item_creates_above_alert(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test that tracking creates an 'above price' alert."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123:csgo"
        mock_api = AsyncMock()
        mock_context.bot_data = {"dmarket_api": mock_api}
        
        item_data = {
            "itemId": "item123",
            "title": "Test Item",
        }
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            return_value=item_data,
        ):
            with patch(
                "src.telegram_bot.smart_notifications.handlers.get_item_price",
                return_value=10.0,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.handlers.create_alert",
                    new_callable=AsyncMock,
                ) as mock_create:
                    await handle_notification_callback(mock_update, mock_context)
                    
                    # Check second call (above alert)
                    calls = mock_create.call_args_list
                    above_call = calls[1]
                    
                    assert above_call.kwargs["conditions"]["direction"] == "above"
                    assert above_call.kwargs["conditions"]["price"] == 11.0  # 10% above

    @pytest.mark.asyncio()
    async def test_track_item_default_game(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test that default game is csgo when not specified."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123"  # No game specified
        mock_api = AsyncMock()
        mock_context.bot_data = {"dmarket_api": mock_api}
        
        item_data = {"itemId": "item123", "title": "Test Item"}
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            return_value=item_data,
        ) as mock_get:
            with patch(
                "src.telegram_bot.smart_notifications.handlers.get_item_price",
                return_value=10.0,
            ):
                with patch(
                    "src.telegram_bot.smart_notifications.handlers.create_alert",
                    new_callable=AsyncMock,
                ):
                    await handle_notification_callback(mock_update, mock_context)
                    
                    # Check that csgo was used as default
                    mock_get.assert_called_once()
                    call_args = mock_get.call_args
                    assert call_args[0][2] == "csgo"  # Third positional arg

    @pytest.mark.asyncio()
    async def test_track_item_error_handling(
        self, mock_update, mock_callback_query, mock_context
    ):
        """Test error handling during item tracking."""
        from src.telegram_bot.smart_notifications.handlers import (
            handle_notification_callback,
        )
        
        mock_callback_query.data = "track_item:item123:csgo"
        mock_api = AsyncMock()
        mock_context.bot_data = {"dmarket_api": mock_api}
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.get_item_by_id",
            side_effect=Exception("Test error"),
        ):
            await handle_notification_callback(mock_update, mock_context)
            
            # Check error message
            call_args = mock_callback_query.edit_message_text.call_args
            text = call_args.kwargs.get("text", call_args[0][0] if call_args[0] else "")
            assert "❌" in text or "error" in text.lower()


# ============================================================================
# TESTS FOR register_notification_handlers
# ============================================================================


class TestRegisterNotificationHandlers:
    """Tests for register_notification_handlers function."""

    def test_registers_callback_handler(self):
        """Test that callback handler is registered."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )
        
        application = MagicMock()
        application.add_handler = MagicMock()
        application.bot_data = {}
        application.bot = MagicMock()
        
        register_notification_handlers(application)
        
        application.add_handler.assert_called()

    def test_starts_notification_checker_with_api(self):
        """Test that notification checker is started when API is available."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )
        
        application = MagicMock()
        application.add_handler = MagicMock()
        mock_api = AsyncMock()
        application.bot_data = {"dmarket_api": mock_api}
        application.bot = MagicMock()
        
        with patch("asyncio.create_task") as mock_create_task:
            register_notification_handlers(application)
            
            mock_create_task.assert_called_once()

    def test_logs_error_without_api(self):
        """Test that error is logged when API is not available."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )
        
        application = MagicMock()
        application.add_handler = MagicMock()
        application.bot_data = {}  # No API
        application.bot = MagicMock()
        
        with patch(
            "src.telegram_bot.smart_notifications.handlers.logger"
        ) as mock_logger:
            register_notification_handlers(application)
            
            mock_logger.error.assert_called()

    def test_callback_pattern(self):
        """Test that callback handler has correct pattern."""
        from src.telegram_bot.smart_notifications.handlers import (
            register_notification_handlers,
        )
        from telegram.ext import CallbackQueryHandler
        
        application = MagicMock()
        application.bot_data = {}
        application.bot = MagicMock()
        
        handlers_added = []
        application.add_handler = lambda h: handlers_added.append(h)
        
        register_notification_handlers(application)
        
        # Find the callback handler
        callback_handlers = [
            h for h in handlers_added if isinstance(h, CallbackQueryHandler)
        ]
        
        assert len(callback_handlers) == 1

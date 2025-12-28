"""Extended unit tests for price_alerts_handler module.

Provides additional test coverage for price alerts functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, Chat, User, CallbackQuery, InlineKeyboardMarkup


@pytest.fixture
def mock_update():
    """Create mock Update object."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 123456789
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = 123456789
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    update.effective_user = update.message.from_user
    return update


@pytest.fixture
def mock_callback_update():
    """Create mock Update with callback query."""
    update = MagicMock(spec=Update)
    update.message = None
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.from_user = MagicMock(spec=User)
    update.callback_query.from_user.id = 123456789
    update.callback_query.message = MagicMock(spec=Message)
    update.callback_query.message.chat = MagicMock(spec=Chat)
    update.callback_query.message.chat.id = 123456789
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user = update.callback_query.from_user
    return update


@pytest.fixture
def mock_context():
    """Create mock context."""
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


class TestPriceAlertTypes:
    """Tests for different price alert types."""

    @pytest.mark.asyncio
    async def test_price_drop_alert(self, mock_update, mock_context):
        """Test creating price drop alert."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "drop", "10"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert1", "type": "drop"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_price_rise_alert(self, mock_update, mock_context):
        """Test creating price rise alert."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "rise", "20"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert2", "type": "rise"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_price_threshold_alert(self, mock_update, mock_context):
        """Test creating price threshold alert."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "threshold", "50"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert3", "type": "threshold"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()


class TestAlertManagement:
    """Tests for alert management functions."""

    @pytest.mark.asyncio
    async def test_list_alerts_empty(self, mock_update, mock_context):
        """Test listing alerts when none exist."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_list_alerts_command,
        )
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.get_user_alerts") as mock_get:
            mock_get.return_value = []
            await handle_list_alerts_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]
        assert "no" in text.lower() or "пусто" in text.lower() or "empty" in text.lower() or "нет" in text.lower()

    @pytest.mark.asyncio
    async def test_list_alerts_with_data(self, mock_update, mock_context):
        """Test listing alerts with data."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_list_alerts_command,
        )
        
        mock_alerts = [
            {"id": "alert1", "item": "Item 1", "type": "drop", "threshold": 10},
            {"id": "alert2", "item": "Item 2", "type": "rise", "threshold": 20},
        ]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.get_user_alerts") as mock_get:
            mock_get.return_value = mock_alerts
            await handle_list_alerts_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_delete_alert_success(self, mock_update, mock_context):
        """Test successful alert deletion."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_delete_alert_command,
        )
        
        mock_context.args = ["alert1"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.delete_alert") as mock_delete:
            mock_delete.return_value = True
            await handle_delete_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_delete_alert_not_found(self, mock_update, mock_context):
        """Test deleting non-existent alert."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_delete_alert_command,
        )
        
        mock_context.args = ["nonexistent"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.delete_alert") as mock_delete:
            mock_delete.return_value = False
            await handle_delete_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()


class TestAlertCallbacks:
    """Tests for alert callback handlers."""

    @pytest.mark.asyncio
    async def test_view_alert_callback(self, mock_callback_update, mock_context):
        """Test view alert callback."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_alert_callback,
        )
        
        mock_callback_update.callback_query.data = "alert:view:alert1"
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.get_alert_by_id") as mock_get:
            mock_get.return_value = {
                "id": "alert1",
                "item": "Test Item",
                "type": "drop",
                "threshold": 10,
            }
            await handle_alert_callback(mock_callback_update, mock_context)
            
        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_delete_alert_callback(self, mock_callback_update, mock_context):
        """Test delete alert callback."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_alert_callback,
        )
        
        mock_callback_update.callback_query.data = "alert:delete:alert1"
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.delete_alert") as mock_delete:
            mock_delete.return_value = True
            await handle_alert_callback(mock_callback_update, mock_context)
            
        mock_callback_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_toggle_alert_callback(self, mock_callback_update, mock_context):
        """Test toggle alert callback."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_alert_callback,
        )
        
        mock_callback_update.callback_query.data = "alert:toggle:alert1"
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.toggle_alert") as mock_toggle:
            mock_toggle.return_value = True
            await handle_alert_callback(mock_callback_update, mock_context)
            
        mock_callback_update.callback_query.answer.assert_called()


class TestAlertValidation:
    """Tests for alert validation."""

    @pytest.mark.asyncio
    async def test_create_alert_invalid_item(self, mock_update, mock_context):
        """Test creating alert with invalid item."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["", "drop", "10"]
        
        await handle_create_alert_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_create_alert_invalid_type(self, mock_update, mock_context):
        """Test creating alert with invalid type."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "invalid_type", "10"]
        
        await handle_create_alert_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_create_alert_invalid_threshold(self, mock_update, mock_context):
        """Test creating alert with invalid threshold."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "drop", "-10"]
        
        await handle_create_alert_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_create_alert_missing_args(self, mock_update, mock_context):
        """Test creating alert with missing arguments."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = []
        
        await handle_create_alert_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()


class TestAlertNotifications:
    """Tests for alert notifications."""

    @pytest.mark.asyncio
    async def test_send_alert_notification(self):
        """Test sending alert notification."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            send_price_alert_notification,
        )
        
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        alert = {
            "id": "alert1",
            "user_id": 123456789,
            "item": "Test Item",
            "type": "drop",
            "current_price": 8.0,
            "previous_price": 10.0,
        }
        
        await send_price_alert_notification(mock_bot, alert)
        
        mock_bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_send_alert_notification_rise(self):
        """Test sending alert notification for price rise."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            send_price_alert_notification,
        )
        
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        alert = {
            "id": "alert2",
            "user_id": 123456789,
            "item": "Test Item",
            "type": "rise",
            "current_price": 12.0,
            "previous_price": 10.0,
        }
        
        await send_price_alert_notification(mock_bot, alert)
        
        mock_bot.send_message.assert_called()


class TestAlertMenu:
    """Tests for alert menu functionality."""

    @pytest.mark.asyncio
    async def test_show_alert_menu(self, mock_update, mock_context):
        """Test showing alert menu."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_alerts_command,
        )
        
        await handle_alerts_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert call_args[1].get("reply_markup") is not None

    @pytest.mark.asyncio
    async def test_alert_menu_buttons(self, mock_update, mock_context):
        """Test alert menu has correct buttons."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_alerts_command,
        )
        
        await handle_alerts_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        reply_markup = call_args[1].get("reply_markup")
        assert isinstance(reply_markup, InlineKeyboardMarkup)


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_no_message_in_update(self, mock_context):
        """Test handling update with no message."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_alerts_command,
        )
        
        update = MagicMock(spec=Update)
        update.message = None
        
        # Should not raise error
        result = await handle_alerts_command(update, mock_context)
        assert result is None

    @pytest.mark.asyncio
    async def test_alert_with_special_characters(self, mock_update, mock_context):
        """Test alert with special characters in item name."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item_with_<special>&chars", "drop", "10"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert1"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_alert_with_unicode(self, mock_update, mock_context):
        """Test alert with unicode characters."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["предмет_тест", "drop", "10"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert1"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_very_large_threshold(self, mock_update, mock_context):
        """Test alert with very large threshold."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "drop", "999999999"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert1"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_decimal_threshold(self, mock_update, mock_context):
        """Test alert with decimal threshold."""
        from src.telegram_bot.handlers.price_alerts_handler import (
            handle_create_alert_command,
        )
        
        mock_context.args = ["item123", "drop", "10.5"]
        
        with patch("src.telegram_bot.handlers.price_alerts_handler.create_price_alert") as mock_create:
            mock_create.return_value = {"id": "alert1"}
            await handle_create_alert_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called()

"""Unit tests for notification digest handler.

This module tests src/telegram_bot/handlers/notification_digest_handler.py covering:
- Digest menu display
- Digest toggle functionality  
- Frequency settings
- Grouping mode settings
- Minimum items configuration
- Settings reset

Target: 40+ tests to achieve 70%+ coverage
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.notification_digest_handler import (
    DigestFrequency,
    GroupingMode,
    NotificationItem,
    digest_command,
    reset_digest_settings,
    set_frequency,
    set_grouping_mode,
    set_min_items,
    show_digest_menu,
    show_frequency_menu,
    show_grouping_menu,
    show_min_items_menu,
    toggle_digest,
)


# Test fixtures


@pytest.fixture()
def mock_update():
    """Fixture providing a mocked Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(id=123456789, username="test_user")
    update.effective_chat = MagicMock(id=123456789)
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "digest_menu"
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Fixture providing a mocked Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


# TestShowDigestMenu


class TestShowDigestMenu:
    """Tests for show_digest_menu function."""

    @pytest.mark.asyncio()
    async def test_show_menu_creates_keyboard(self, mock_update, mock_context):
        """Test that menu creates inline keyboard."""
        # Arrange
        mock_context.user_data = {"digest_enabled": False}

        # Act
        await show_digest_menu(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio()
    async def test_show_menu_displays_current_settings(self, mock_update, mock_context):
        """Test that menu shows current digest settings."""
        # Arrange
        mock_context.user_data = {
            "digest_enabled": True,
            "digest_frequency": DigestFrequency.DAILY.value,
            "digest_grouping": GroupingMode.BY_TYPE.value,
        }

        # Act
        await show_digest_menu(mock_update, mock_context)

        # Assert
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        assert "Enabled" in message_text or "включен" in message_text.lower()


# TestToggleDigest


class TestToggleDigest:
    """Tests for toggle_digest function."""

    @pytest.mark.asyncio()
    async def test_toggle_enables_digest(self, mock_update, mock_context):
        """Test toggling digest from disabled to enabled."""
        # Arrange
        mock_context.user_data = {"digest_enabled": False}

        # Act
        await toggle_digest(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_enabled") is True

    @pytest.mark.asyncio()
    async def test_toggle_disables_digest(self, mock_update, mock_context):
        """Test toggling digest from enabled to disabled."""
        # Arrange
        mock_context.user_data = {"digest_enabled": True}

        # Act
        await toggle_digest(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_enabled") is False


# TestFrequencySettings


class TestFrequencySettings:
    """Tests for frequency settings functions."""

    @pytest.mark.asyncio()
    async def test_show_frequency_menu(self, mock_update, mock_context):
        """Test showing frequency selection menu."""
        # Act
        await show_frequency_menu(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_set_frequency_hourly(self, mock_update, mock_context):
        """Test setting hourly frequency."""
        # Arrange
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.HOURLY.value}"

        # Act
        await set_frequency(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_frequency") == DigestFrequency.HOURLY.value

    @pytest.mark.asyncio()
    async def test_set_frequency_daily(self, mock_update, mock_context):
        """Test setting daily frequency."""
        # Arrange
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.DAILY.value}"

        # Act
        await set_frequency(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_frequency") == DigestFrequency.DAILY.value

    @pytest.mark.asyncio()
    async def test_set_frequency_weekly(self, mock_update, mock_context):
        """Test setting weekly frequency."""
        # Arrange
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.WEEKLY.value}"

        # Act
        await set_frequency(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_frequency") == DigestFrequency.WEEKLY.value


# TestGroupingMode


class TestGroupingMode:
    """Tests for grouping mode functions."""

    @pytest.mark.asyncio()
    async def test_show_grouping_menu(self, mock_update, mock_context):
        """Test showing grouping mode menu."""
        # Act
        await show_grouping_menu(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_set_grouping_by_type(self, mock_update, mock_context):
        """Test setting grouping by type."""
        # Arrange
        mock_update.callback_query.data = f"digest_set_group_{GroupingMode.BY_TYPE.value}"

        # Act
        await set_grouping_mode(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_grouping") == GroupingMode.BY_TYPE.value

    @pytest.mark.asyncio()
    async def test_set_grouping_by_game(self, mock_update, mock_context):
        """Test setting grouping by game."""
        # Arrange
        mock_update.callback_query.data = f"digest_set_group_{GroupingMode.BY_GAME.value}"

        # Act
        await set_grouping_mode(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_grouping") == GroupingMode.BY_GAME.value


# TestMinItemsConfiguration


class TestMinItemsConfiguration:
    """Tests for minimum items configuration."""

    @pytest.mark.asyncio()
    async def test_show_min_items_menu(self, mock_update, mock_context):
        """Test showing minimum items menu."""
        # Act
        await show_min_items_menu(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_set_min_items_3(self, mock_update, mock_context):
        """Test setting minimum items to 3."""
        # Arrange
        mock_update.callback_query.data = "digest_set_min_3"

        # Act
        await set_min_items(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_min_items") == 3

    @pytest.mark.asyncio()
    async def test_set_min_items_5(self, mock_update, mock_context):
        """Test setting minimum items to 5."""
        # Arrange
        mock_update.callback_query.data = "digest_set_min_5"

        # Act
        await set_min_items(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_min_items") == 5

    @pytest.mark.asyncio()
    async def test_set_min_items_10(self, mock_update, mock_context):
        """Test setting minimum items to 10."""
        # Arrange
        mock_update.callback_query.data = "digest_set_min_10"

        # Act
        await set_min_items(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_min_items") == 10


# TestResetSettings


class TestResetSettings:
    """Tests for reset settings functionality."""

    @pytest.mark.asyncio()
    async def test_reset_restores_defaults(self, mock_update, mock_context):
        """Test that reset restores default settings."""
        # Arrange
        mock_context.user_data = {
            "digest_enabled": True,
            "digest_frequency": DigestFrequency.WEEKLY.value,
            "digest_grouping": GroupingMode.BY_GAME.value,
            "digest_min_items": 10,
        }

        # Act
        await reset_digest_settings(mock_update, mock_context)

        # Assert
        assert mock_context.user_data.get("digest_enabled") is False
        assert mock_context.user_data.get("digest_frequency") == DigestFrequency.DISABLED.value


# TestDigestCommand


class TestDigestCommand:
    """Tests for digest command handler."""

    @pytest.mark.asyncio()
    async def test_digest_command_sends_menu(self, mock_update, mock_context):
        """Test that /digest command shows menu."""
        # Act
        await digest_command(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "reply_markup" in call_args.kwargs


# TestNotificationItem


class TestNotificationItem:
    """Tests for NotificationItem dataclass."""

    def test_notification_item_creation(self):
        """Test creating NotificationItem."""
        # Arrange & Act
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test Item",
            message="Test message",
            timestamp=datetime.now(),
            priority=2,
        )

        # Assert
        assert item.user_id == 123
        assert item.notification_type == "arbitrage"
        assert item.game == "csgo"
        assert item.priority == 2

    def test_notification_item_default_priority(self):
        """Test default priority value."""
        # Arrange & Act
        item = NotificationItem(
            user_id=123,
            notification_type="price_drop",
            game="dota2",
            title="Item",
            message="Message",
            timestamp=datetime.now(),
        )

        # Assert
        assert item.priority == 1

    def test_notification_item_with_data(self):
        """Test NotificationItem with additional data."""
        # Arrange & Act
        item = NotificationItem(
            user_id=123,
            notification_type="target",
            game="csgo",
            title="AK-47",
            message="Target reached",
            timestamp=datetime.now(),
            data={"price": 15.50, "target_id": "tgt_123"},
        )

        # Assert
        assert item.data["price"] == 15.50
        assert item.data["target_id"] == "tgt_123"

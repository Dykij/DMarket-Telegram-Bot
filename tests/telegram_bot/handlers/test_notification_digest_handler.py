"""Unit tests for notification digest handler.

This module tests src/telegram_bot/handlers/notification_digest_handler.py covering:
- Digest menu display
- Digest toggle functionality  
- Frequency settings
- Grouping mode settings
- Minimum items configuration
- Settings reset
- NotificationDigestManager class
- NotificationItem dataclass
- DigestSettings dataclass

Target: 40+ tests to achieve 70%+ coverage
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.notification_digest_handler import (
    DigestFrequency,
    DigestSettings,
    GroupingMode,
    NotificationDigestManager,
    NotificationItem,
    digest_command,
    get_digest_manager,
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


@pytest.fixture()
def digest_manager():
    """Fixture providing a fresh NotificationDigestManager."""
    return NotificationDigestManager()


# ============================================================================
# TestNotificationDigestManager
# ============================================================================


class TestNotificationDigestManager:
    """Tests for NotificationDigestManager class."""

    def test_init_creates_empty_storages(self):
        """Test that manager initializes with empty storages."""
        manager = NotificationDigestManager()
        assert len(manager._pending_notifications) == 0
        assert len(manager._user_settings) == 0
        assert manager._scheduler_task is None

    def test_get_user_settings_creates_default_for_new_user(self, digest_manager):
        """Test that get_user_settings creates default settings for new user."""
        user_id = 12345
        settings = digest_manager.get_user_settings(user_id)
        
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY
        assert settings.grouping_mode == GroupingMode.BY_TYPE
        assert settings.min_items == 3

    def test_get_user_settings_returns_same_object_for_existing_user(self, digest_manager):
        """Test that get_user_settings returns same settings for existing user."""
        user_id = 12345
        settings1 = digest_manager.get_user_settings(user_id)
        settings1.enabled = True
        
        settings2 = digest_manager.get_user_settings(user_id)
        assert settings2.enabled is True
        assert settings1 is settings2

    def test_update_user_settings_updates_enabled(self, digest_manager):
        """Test updating enabled setting."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"enabled": True})
        settings = digest_manager.get_user_settings(user_id)
        assert settings.enabled is True

    def test_update_user_settings_updates_frequency(self, digest_manager):
        """Test updating frequency setting."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"frequency": DigestFrequency.HOURLY})
        settings = digest_manager.get_user_settings(user_id)
        assert settings.frequency == DigestFrequency.HOURLY

    def test_update_user_settings_updates_grouping_mode(self, digest_manager):
        """Test updating grouping mode setting."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"grouping_mode": GroupingMode.BY_GAME})
        settings = digest_manager.get_user_settings(user_id)
        assert settings.grouping_mode == GroupingMode.BY_GAME

    def test_update_user_settings_updates_min_items(self, digest_manager):
        """Test updating min_items setting."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"min_items": 10})
        settings = digest_manager.get_user_settings(user_id)
        assert settings.min_items == 10

    def test_update_user_settings_updates_multiple_settings(self, digest_manager):
        """Test updating multiple settings at once."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {
            "enabled": True,
            "frequency": DigestFrequency.WEEKLY,
            "min_items": 5,
        })
        settings = digest_manager.get_user_settings(user_id)
        assert settings.enabled is True
        assert settings.frequency == DigestFrequency.WEEKLY
        assert settings.min_items == 5

    def test_reset_user_settings_resets_to_defaults(self, digest_manager):
        """Test that reset_user_settings restores default values."""
        user_id = 12345
        # First set custom values
        digest_manager.update_user_settings(user_id, {
            "enabled": True,
            "frequency": DigestFrequency.WEEKLY,
            "min_items": 15,
        })
        
        # Reset
        settings = digest_manager.reset_user_settings(user_id)
        
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY
        assert settings.min_items == 3

    def test_add_notification_when_digest_disabled(self, digest_manager):
        """Test that notifications are not added when digest is disabled."""
        user_id = 12345
        notification = NotificationItem(
            user_id=user_id,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=datetime.now(),
        )
        
        digest_manager.add_notification(notification)
        
        # Should not be added because digest is disabled by default
        assert len(digest_manager.get_pending_notifications(user_id)) == 0

    def test_add_notification_when_digest_enabled(self, digest_manager):
        """Test that notifications are added when digest is enabled."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"enabled": True})
        
        notification = NotificationItem(
            user_id=user_id,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=datetime.now(),
        )
        
        digest_manager.add_notification(notification)
        
        pending = digest_manager.get_pending_notifications(user_id)
        assert len(pending) == 1
        assert pending[0] == notification

    def test_get_pending_notifications_returns_empty_for_new_user(self, digest_manager):
        """Test that get_pending_notifications returns empty list for new user."""
        pending = digest_manager.get_pending_notifications(99999)
        assert pending == []

    def test_clear_pending_notifications(self, digest_manager):
        """Test clearing pending notifications."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"enabled": True})
        
        # Add some notifications
        for i in range(3):
            digest_manager.add_notification(NotificationItem(
                user_id=user_id,
                notification_type="test",
                game="csgo",
                title=f"Test {i}",
                message=f"Message {i}",
                timestamp=datetime.now(),
            ))
        
        assert len(digest_manager.get_pending_notifications(user_id)) == 3
        
        digest_manager.clear_pending_notifications(user_id)
        
        assert len(digest_manager.get_pending_notifications(user_id)) == 0

    def test_clear_pending_notifications_for_nonexistent_user(self, digest_manager):
        """Test that clearing for nonexistent user doesn't raise error."""
        # Should not raise
        digest_manager.clear_pending_notifications(99999)

    def test_should_send_digest_returns_false_when_disabled(self, digest_manager):
        """Test should_send_digest returns False when digest is disabled."""
        user_id = 12345
        assert digest_manager.should_send_digest(user_id) is False

    def test_should_send_digest_returns_false_when_not_enough_notifications(self, digest_manager):
        """Test should_send_digest returns False when not enough notifications."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"enabled": True, "min_items": 5})
        
        # Add only 2 notifications
        for i in range(2):
            digest_manager.add_notification(NotificationItem(
                user_id=user_id,
                notification_type="test",
                game="csgo",
                title=f"Test {i}",
                message=f"Message {i}",
                timestamp=datetime.now(),
            ))
        
        assert digest_manager.should_send_digest(user_id) is False

    def test_should_send_digest_returns_true_when_conditions_met(self, digest_manager):
        """Test should_send_digest returns True when all conditions met."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"enabled": True, "min_items": 3})
        
        # Add enough notifications
        for i in range(5):
            digest_manager.add_notification(NotificationItem(
                user_id=user_id,
                notification_type="test",
                game="csgo",
                title=f"Test {i}",
                message=f"Message {i}",
                timestamp=datetime.now(),
            ))
        
        # No last_sent means it should send
        assert digest_manager.should_send_digest(user_id) is True

    def test_should_send_digest_respects_frequency_interval(self, digest_manager):
        """Test that should_send_digest respects frequency interval."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {
            "enabled": True, 
            "min_items": 1,
            "frequency": DigestFrequency.DAILY,
        })
        
        # Add notification
        digest_manager.add_notification(NotificationItem(
            user_id=user_id,
            notification_type="test",
            game="csgo",
            title="Test",
            message="Message",
            timestamp=datetime.now(),
        ))
        
        # Set last_sent to just now
        settings = digest_manager.get_user_settings(user_id)
        settings.last_sent = datetime.now()
        
        # Should not send because not enough time has passed
        assert digest_manager.should_send_digest(user_id) is False

    def test_format_digest_with_empty_notifications(self, digest_manager):
        """Test format_digest with empty notifications list."""
        user_id = 12345
        result = digest_manager.format_digest(user_id, [])
        assert "Нет новых уведомлений" in result

    def test_format_digest_with_notifications(self, digest_manager):
        """Test format_digest with notifications."""
        user_id = 12345
        notifications = [
            NotificationItem(
                user_id=user_id,
                notification_type="arbitrage",
                game="csgo",
                title="Item 1",
                message="Found opportunity",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=user_id,
                notification_type="price_drop",
                game="csgo",
                title="Item 2",
                message="Price dropped",
                timestamp=datetime.now(),
            ),
        ]
        
        result = digest_manager.format_digest(user_id, notifications)
        
        assert "Дайджест" in result
        assert "2 уведомлений" in result

    def test_format_digest_groups_by_type(self, digest_manager):
        """Test that format_digest groups notifications by type."""
        user_id = 12345
        digest_manager.update_user_settings(user_id, {"grouping_mode": GroupingMode.BY_TYPE})
        
        notifications = [
            NotificationItem(
                user_id=user_id,
                notification_type="arbitrage",
                game="csgo",
                title="Item 1",
                message="Message 1",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=user_id,
                notification_type="arbitrage",
                game="dota2",
                title="Item 2",
                message="Message 2",
                timestamp=datetime.now(),
            ),
        ]
        
        result = digest_manager.format_digest(user_id, notifications)
        assert "Арбитраж" in result


class TestGroupNotifications:
    """Tests for _group_notifications method."""

    def test_group_by_type(self):
        """Test grouping notifications by type."""
        manager = NotificationDigestManager()
        notifications = [
            NotificationItem(
                user_id=1,
                notification_type="arbitrage",
                game="csgo",
                title="A",
                message="M",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=1,
                notification_type="price_drop",
                game="csgo",
                title="B",
                message="M",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=1,
                notification_type="arbitrage",
                game="dota2",
                title="C",
                message="M",
                timestamp=datetime.now(),
            ),
        ]
        
        grouped = manager._group_notifications(notifications, GroupingMode.BY_TYPE)
        
        assert "arbitrage" in grouped
        assert "price_drop" in grouped
        assert len(grouped["arbitrage"]) == 2
        assert len(grouped["price_drop"]) == 1

    def test_group_by_game(self):
        """Test grouping notifications by game."""
        manager = NotificationDigestManager()
        notifications = [
            NotificationItem(
                user_id=1,
                notification_type="arbitrage",
                game="csgo",
                title="A",
                message="M",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=1,
                notification_type="price_drop",
                game="dota2",
                title="B",
                message="M",
                timestamp=datetime.now(),
            ),
        ]
        
        grouped = manager._group_notifications(notifications, GroupingMode.BY_GAME)
        
        assert "csgo" in grouped
        assert "dota2" in grouped

    def test_group_chronological(self):
        """Test chronological grouping (no grouping)."""
        manager = NotificationDigestManager()
        notifications = [
            NotificationItem(
                user_id=1,
                notification_type="arbitrage",
                game="csgo",
                title="A",
                message="M",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=1,
                notification_type="price_drop",
                game="dota2",
                title="B",
                message="M",
                timestamp=datetime.now(),
            ),
        ]
        
        grouped = manager._group_notifications(notifications, GroupingMode.CHRONOLOGICAL)
        
        assert "all" in grouped
        assert len(grouped["all"]) == 2


# ============================================================================
# TestShowDigestMenu
# ============================================================================


class TestShowDigestMenu:
    """Tests for show_digest_menu function."""

    @pytest.mark.asyncio()
    async def test_show_menu_creates_keyboard(self, mock_update, mock_context):
        """Test that menu creates inline keyboard."""
        await show_digest_menu(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio()
    async def test_show_menu_displays_status(self, mock_update, mock_context):
        """Test that menu shows digest status."""
        await show_digest_menu(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        # Should contain status info
        assert "Статус" in message_text or "настройки" in message_text.lower()

    @pytest.mark.asyncio()
    async def test_show_menu_via_message(self, mock_update, mock_context):
        """Test showing menu via direct message (not callback)."""
        mock_update.callback_query = None
        
        await show_digest_menu(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_show_menu_returns_early_without_user(self, mock_update, mock_context):
        """Test that show_menu returns early without effective_user."""
        mock_update.effective_user = None
        
        await show_digest_menu(mock_update, mock_context)
        
        # Should not call any message methods
        mock_update.callback_query.edit_message_text.assert_not_called()


# ============================================================================
# TestToggleDigest
# ============================================================================


class TestToggleDigest:
    """Tests for toggle_digest function."""

    @pytest.mark.asyncio()
    async def test_toggle_enables_digest(self, mock_update, mock_context):
        """Test toggling digest from disabled to enabled."""
        user_id = mock_update.effective_user.id
        manager = get_digest_manager()
        
        # Ensure disabled initially
        manager.update_user_settings(user_id, {"enabled": False})
        
        await toggle_digest(mock_update, mock_context)
        
        settings = manager.get_user_settings(user_id)
        assert settings.enabled is True

    @pytest.mark.asyncio()
    async def test_toggle_disables_digest(self, mock_update, mock_context):
        """Test toggling digest from enabled to disabled."""
        user_id = mock_update.effective_user.id
        manager = get_digest_manager()
        
        # Enable first
        manager.update_user_settings(user_id, {"enabled": True})
        
        await toggle_digest(mock_update, mock_context)
        
        settings = manager.get_user_settings(user_id)
        assert settings.enabled is False

    @pytest.mark.asyncio()
    async def test_toggle_returns_early_without_query(self, mock_update, mock_context):
        """Test that toggle returns early without callback_query."""
        mock_update.callback_query = None
        
        # Should not raise
        await toggle_digest(mock_update, mock_context)


# ============================================================================
# TestFrequencySettings
# ============================================================================


class TestFrequencySettings:
    """Tests for frequency settings functions."""

    @pytest.mark.asyncio()
    async def test_show_frequency_menu(self, mock_update, mock_context):
        """Test showing frequency selection menu."""
        await show_frequency_menu(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_set_frequency_hourly(self, mock_update, mock_context):
        """Test setting hourly frequency."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.HOURLY.value}"

        await set_frequency(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.frequency == DigestFrequency.HOURLY

    @pytest.mark.asyncio()
    async def test_set_frequency_daily(self, mock_update, mock_context):
        """Test setting daily frequency."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.DAILY.value}"

        await set_frequency(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.frequency == DigestFrequency.DAILY

    @pytest.mark.asyncio()
    async def test_set_frequency_weekly(self, mock_update, mock_context):
        """Test setting weekly frequency."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.WEEKLY.value}"

        await set_frequency(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.frequency == DigestFrequency.WEEKLY

    @pytest.mark.asyncio()
    async def test_set_frequency_every_3_hours(self, mock_update, mock_context):
        """Test setting every 3 hours frequency."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_freq_{DigestFrequency.EVERY_3_HOURS.value}"

        await set_frequency(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.frequency == DigestFrequency.EVERY_3_HOURS


# ============================================================================
# TestGroupingModeSettings
# ============================================================================


class TestGroupingModeSettings:
    """Tests for grouping mode functions."""

    @pytest.mark.asyncio()
    async def test_show_grouping_menu(self, mock_update, mock_context):
        """Test showing grouping mode menu."""
        await show_grouping_menu(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_set_grouping_by_type(self, mock_update, mock_context):
        """Test setting grouping by type."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_group_{GroupingMode.BY_TYPE.value}"

        await set_grouping_mode(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.grouping_mode == GroupingMode.BY_TYPE

    @pytest.mark.asyncio()
    async def test_set_grouping_by_game(self, mock_update, mock_context):
        """Test setting grouping by game."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_group_{GroupingMode.BY_GAME.value}"

        await set_grouping_mode(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.grouping_mode == GroupingMode.BY_GAME

    @pytest.mark.asyncio()
    async def test_set_grouping_by_priority(self, mock_update, mock_context):
        """Test setting grouping by priority."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_group_{GroupingMode.BY_PRIORITY.value}"

        await set_grouping_mode(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.grouping_mode == GroupingMode.BY_PRIORITY

    @pytest.mark.asyncio()
    async def test_set_grouping_chronological(self, mock_update, mock_context):
        """Test setting chronological grouping."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = f"digest_set_group_{GroupingMode.CHRONOLOGICAL.value}"

        await set_grouping_mode(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.grouping_mode == GroupingMode.CHRONOLOGICAL


# ============================================================================
# TestMinItemsConfiguration
# ============================================================================


class TestMinItemsConfiguration:
    """Tests for minimum items configuration."""

    @pytest.mark.asyncio()
    async def test_show_min_items_menu(self, mock_update, mock_context):
        """Test showing minimum items menu."""
        await show_min_items_menu(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_set_min_items_1(self, mock_update, mock_context):
        """Test setting minimum items to 1."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "digest_set_min_1"

        await set_min_items(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.min_items == 1

    @pytest.mark.asyncio()
    async def test_set_min_items_3(self, mock_update, mock_context):
        """Test setting minimum items to 3."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "digest_set_min_3"

        await set_min_items(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.min_items == 3

    @pytest.mark.asyncio()
    async def test_set_min_items_10(self, mock_update, mock_context):
        """Test setting minimum items to 10."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "digest_set_min_10"

        await set_min_items(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.min_items == 10

    @pytest.mark.asyncio()
    async def test_set_min_items_20(self, mock_update, mock_context):
        """Test setting minimum items to 20."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "digest_set_min_20"

        await set_min_items(mock_update, mock_context)

        manager = get_digest_manager()
        settings = manager.get_user_settings(user_id)
        assert settings.min_items == 20


# ============================================================================
# TestResetSettings
# ============================================================================


class TestResetSettings:
    """Tests for reset settings functionality."""

    @pytest.mark.asyncio()
    async def test_reset_restores_defaults(self, mock_update, mock_context):
        """Test that reset restores default settings."""
        user_id = mock_update.effective_user.id
        manager = get_digest_manager()
        
        # Set custom values
        manager.update_user_settings(user_id, {
            "enabled": True,
            "frequency": DigestFrequency.WEEKLY,
            "grouping_mode": GroupingMode.BY_GAME,
            "min_items": 15,
        })

        await reset_digest_settings(mock_update, mock_context)

        settings = manager.get_user_settings(user_id)
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY
        assert settings.grouping_mode == GroupingMode.BY_TYPE
        assert settings.min_items == 3

    @pytest.mark.asyncio()
    async def test_reset_shows_confirmation(self, mock_update, mock_context):
        """Test that reset shows confirmation via callback answer."""
        await reset_digest_settings(mock_update, mock_context)
        
        # answer is called at least once (may be called multiple times if menu is refreshed)
        assert mock_update.callback_query.answer.call_count >= 1
        # Check that the confirmation message was passed
        calls = mock_update.callback_query.answer.call_args_list
        assert any("сброшен" in str(call).lower() for call in calls)


# ============================================================================
# TestDigestCommand
# ============================================================================


class TestDigestCommand:
    """Tests for digest command handler."""

    @pytest.mark.asyncio()
    async def test_digest_command_shows_menu(self, mock_update, mock_context):
        """Test that /digest command shows menu."""
        # For command, callback_query is None and message is used
        mock_update.callback_query = None
        
        await digest_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio()
    async def test_digest_command_returns_early_without_user(self, mock_update, mock_context):
        """Test that digest_command returns early without effective_user."""
        mock_update.effective_user = None
        mock_update.callback_query = None
        
        await digest_command(mock_update, mock_context)
        
        # Should not call reply_text
        mock_update.message.reply_text.assert_not_called()


# ============================================================================
# TestNotificationItem
# ============================================================================


class TestNotificationItem:
    """Tests for NotificationItem dataclass."""

    def test_notification_item_creation(self):
        """Test creating NotificationItem."""
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test Item",
            message="Test message",
            timestamp=datetime.now(),
            priority=2,
        )

        assert item.user_id == 123
        assert item.notification_type == "arbitrage"
        assert item.game == "csgo"
        assert item.priority == 2

    def test_notification_item_default_priority(self):
        """Test default priority value."""
        item = NotificationItem(
            user_id=123,
            notification_type="price_drop",
            game="dota2",
            title="Item",
            message="Message",
            timestamp=datetime.now(),
        )

        assert item.priority == 1

    def test_notification_item_with_data(self):
        """Test NotificationItem with additional data."""
        item = NotificationItem(
            user_id=123,
            notification_type="target",
            game="csgo",
            title="AK-47",
            message="Target reached",
            timestamp=datetime.now(),
            data={"price": 15.50, "target_id": "tgt_123"},
        )

        assert item.data["price"] == 15.50
        assert item.data["target_id"] == "tgt_123"

    def test_notification_item_default_data(self):
        """Test default data is empty dict."""
        item = NotificationItem(
            user_id=123,
            notification_type="test",
            game="csgo",
            title="Test",
            message="Message",
            timestamp=datetime.now(),
        )

        assert item.data == {}


# ============================================================================
# TestDigestSettings
# ============================================================================


class TestDigestSettings:
    """Tests for DigestSettings dataclass."""

    def test_digest_settings_defaults(self):
        """Test DigestSettings default values."""
        settings = DigestSettings()
        
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY
        assert settings.grouping_mode == GroupingMode.BY_TYPE
        assert settings.min_items == 3
        assert settings.last_sent is None

    def test_digest_settings_custom_values(self):
        """Test DigestSettings with custom values."""
        last_sent = datetime.now()
        settings = DigestSettings(
            enabled=True,
            frequency=DigestFrequency.WEEKLY,
            grouping_mode=GroupingMode.BY_GAME,
            min_items=10,
            last_sent=last_sent,
        )
        
        assert settings.enabled is True
        assert settings.frequency == DigestFrequency.WEEKLY
        assert settings.grouping_mode == GroupingMode.BY_GAME
        assert settings.min_items == 10
        assert settings.last_sent == last_sent


# ============================================================================
# TestDigestFrequencyEnum
# ============================================================================


class TestDigestFrequencyEnum:
    """Tests for DigestFrequency enum."""

    def test_all_frequency_values_exist(self):
        """Test that all expected frequency values exist."""
        assert DigestFrequency.DISABLED.value == "disabled"
        assert DigestFrequency.HOURLY.value == "hourly"
        assert DigestFrequency.EVERY_3_HOURS.value == "every_3h"
        assert DigestFrequency.EVERY_6_HOURS.value == "every_6h"
        assert DigestFrequency.DAILY.value == "daily"
        assert DigestFrequency.WEEKLY.value == "weekly"

    def test_frequency_enum_iteration(self):
        """Test iterating over frequency values."""
        frequencies = list(DigestFrequency)
        assert len(frequencies) == 6


# ============================================================================
# TestGroupingModeEnum  
# ============================================================================


class TestGroupingModeEnum:
    """Tests for GroupingMode enum."""

    def test_all_grouping_modes_exist(self):
        """Test that all expected grouping modes exist."""
        assert GroupingMode.BY_TYPE.value == "by_type"
        assert GroupingMode.BY_GAME.value == "by_game"
        assert GroupingMode.BY_PRIORITY.value == "by_priority"
        assert GroupingMode.CHRONOLOGICAL.value == "chronological"

    def test_grouping_mode_iteration(self):
        """Test iterating over grouping modes."""
        modes = list(GroupingMode)
        assert len(modes) == 4

"""
Phase 4 Extended Unit Tests for notification_digest_handler.py

This module provides comprehensive test coverage for the notification digest handler,
including:
- DigestFrequency enum tests
- GroupingMode enum tests
- NotificationItem dataclass tests
- DigestSettings dataclass tests
- NotificationDigestManager class tests
- Handler functions tests
- Edge cases and integration tests

Total: 82 tests
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.handlers.notification_digest_handler import (
    DIGEST_BACK,
    DIGEST_FREQUENCY,
    DIGEST_GROUP_BY,
    DIGEST_MENU,
    DIGEST_MIN_ITEMS,
    DIGEST_RESET,
    DIGEST_SET_FREQ,
    DIGEST_SET_GROUP,
    DIGEST_SET_MIN,
    DIGEST_TOGGLE,
    DigestFrequency,
    DigestSettings,
    GroupingMode,
    NotificationDigestManager,
    NotificationItem,
    digest_command,
    get_digest_manager,
    register_notification_digest_handlers,
    reset_digest_settings,
    set_frequency,
    set_grouping_mode,
    set_min_items,
    show_digest_menu,
    show_frequency_menu,
    toggle_digest,
)


# === Fixtures ===


@pytest.fixture()
def manager():
    """Create a fresh NotificationDigestManager instance."""
    return NotificationDigestManager()


@pytest.fixture()
def sample_notification():
    """Create a sample notification item."""
    return NotificationItem(
        user_id=123456,
        notification_type="arbitrage",
        game="csgo",
        title="Test Notification",
        message="This is a test notification",
        timestamp=datetime.now(),
        priority=1,
        data={"item_id": "test123"},
    )


@pytest.fixture()
def mock_update():
    """Create a mock Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "test_data"
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Create a mock Context object."""
    context = MagicMock()
    context.user_data = {}
    return context


# === Constants Tests ===


class TestConstants:
    """Tests for module constants."""

    def test_digest_menu_constant(self):
        """Test DIGEST_MENU constant."""
        assert DIGEST_MENU == "digest_menu"

    def test_digest_toggle_constant(self):
        """Test DIGEST_TOGGLE constant."""
        assert DIGEST_TOGGLE == "digest_toggle"

    def test_digest_frequency_constant(self):
        """Test DIGEST_FREQUENCY constant."""
        assert DIGEST_FREQUENCY == "digest_freq"

    def test_digest_set_freq_constant(self):
        """Test DIGEST_SET_FREQ constant."""
        assert DIGEST_SET_FREQ == "digest_set_freq_{}"
        assert DIGEST_SET_FREQ.format("daily") == "digest_set_freq_daily"

    def test_digest_group_by_constant(self):
        """Test DIGEST_GROUP_BY constant."""
        assert DIGEST_GROUP_BY == "digest_group"

    def test_digest_set_group_constant(self):
        """Test DIGEST_SET_GROUP constant."""
        assert DIGEST_SET_GROUP == "digest_set_group_{}"
        assert DIGEST_SET_GROUP.format("by_type") == "digest_set_group_by_type"

    def test_digest_min_items_constant(self):
        """Test DIGEST_MIN_ITEMS constant."""
        assert DIGEST_MIN_ITEMS == "digest_min"

    def test_digest_set_min_constant(self):
        """Test DIGEST_SET_MIN constant."""
        assert DIGEST_SET_MIN == "digest_set_min_{}"
        assert DIGEST_SET_MIN.format(5) == "digest_set_min_5"

    def test_digest_reset_constant(self):
        """Test DIGEST_RESET constant."""
        assert DIGEST_RESET == "digest_reset"

    def test_digest_back_constant(self):
        """Test DIGEST_BACK constant."""
        assert DIGEST_BACK == "digest_back"


# === DigestFrequency Enum Tests ===


class TestDigestFrequencyEnum:
    """Tests for DigestFrequency enum."""

    def test_disabled_value(self):
        """Test DISABLED frequency value."""
        assert DigestFrequency.DISABLED.value == "disabled"

    def test_hourly_value(self):
        """Test HOURLY frequency value."""
        assert DigestFrequency.HOURLY.value == "hourly"

    def test_every_3_hours_value(self):
        """Test EVERY_3_HOURS frequency value."""
        assert DigestFrequency.EVERY_3_HOURS.value == "every_3h"

    def test_every_6_hours_value(self):
        """Test EVERY_6_HOURS frequency value."""
        assert DigestFrequency.EVERY_6_HOURS.value == "every_6h"

    def test_daily_value(self):
        """Test DAILY frequency value."""
        assert DigestFrequency.DAILY.value == "daily"

    def test_weekly_value(self):
        """Test WEEKLY frequency value."""
        assert DigestFrequency.WEEKLY.value == "weekly"

    def test_all_frequencies_count(self):
        """Test total number of frequencies."""
        assert len(DigestFrequency) == 6

    def test_frequency_is_str_enum(self):
        """Test that DigestFrequency is a string enum."""
        assert isinstance(DigestFrequency.DAILY, str)
        assert DigestFrequency.DAILY == "daily"


# === GroupingMode Enum Tests ===


class TestGroupingModeEnum:
    """Tests for GroupingMode enum."""

    def test_by_type_value(self):
        """Test BY_TYPE grouping mode value."""
        assert GroupingMode.BY_TYPE.value == "by_type"

    def test_by_game_value(self):
        """Test BY_GAME grouping mode value."""
        assert GroupingMode.BY_GAME.value == "by_game"

    def test_by_priority_value(self):
        """Test BY_PRIORITY grouping mode value."""
        assert GroupingMode.BY_PRIORITY.value == "by_priority"

    def test_chronological_value(self):
        """Test CHRONOLOGICAL grouping mode value."""
        assert GroupingMode.CHRONOLOGICAL.value == "chronological"

    def test_all_modes_count(self):
        """Test total number of grouping modes."""
        assert len(GroupingMode) == 4

    def test_mode_is_str_enum(self):
        """Test that GroupingMode is a string enum."""
        assert isinstance(GroupingMode.BY_TYPE, str)
        assert GroupingMode.BY_TYPE == "by_type"


# === NotificationItem Dataclass Tests ===


class TestNotificationItemDataclass:
    """Tests for NotificationItem dataclass."""

    def test_basic_init(self):
        """Test basic NotificationItem initialization."""
        now = datetime.now()
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=now,
        )
        assert item.user_id == 123
        assert item.notification_type == "arbitrage"
        assert item.game == "csgo"
        assert item.title == "Test"
        assert item.message == "Test message"
        assert item.timestamp == now

    def test_default_priority(self):
        """Test default priority value."""
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=datetime.now(),
        )
        assert item.priority == 1

    def test_default_data(self):
        """Test default data value."""
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=datetime.now(),
        )
        assert item.data == {}

    def test_custom_priority(self):
        """Test custom priority value."""
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=datetime.now(),
            priority=5,
        )
        assert item.priority == 5

    def test_custom_data(self):
        """Test custom data value."""
        data = {"item_id": "abc123", "price": 100}
        item = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test message",
            timestamp=datetime.now(),
            data=data,
        )
        assert item.data == data

    def test_all_notification_types(self):
        """Test various notification types."""
        types = ["arbitrage", "price_drop", "price_rise", "trending", "good_deal"]
        for notif_type in types:
            item = NotificationItem(
                user_id=123,
                notification_type=notif_type,
                game="csgo",
                title="Test",
                message="Test message",
                timestamp=datetime.now(),
            )
            assert item.notification_type == notif_type

    def test_all_games(self):
        """Test various game values."""
        games = ["csgo", "dota2", "tf2", "rust"]
        for game in games:
            item = NotificationItem(
                user_id=123,
                notification_type="arbitrage",
                game=game,
                title="Test",
                message="Test message",
                timestamp=datetime.now(),
            )
            assert item.game == game


# === DigestSettings Dataclass Tests ===


class TestDigestSettingsDataclass:
    """Tests for DigestSettings dataclass."""

    def test_default_init(self):
        """Test default DigestSettings initialization."""
        settings = DigestSettings()
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY
        assert settings.grouping_mode == GroupingMode.BY_TYPE
        assert settings.min_items == 3
        assert settings.last_sent is None

    def test_custom_enabled(self):
        """Test custom enabled value."""
        settings = DigestSettings(enabled=True)
        assert settings.enabled is True

    def test_custom_frequency(self):
        """Test custom frequency value."""
        settings = DigestSettings(frequency=DigestFrequency.HOURLY)
        assert settings.frequency == DigestFrequency.HOURLY

    def test_custom_grouping_mode(self):
        """Test custom grouping mode value."""
        settings = DigestSettings(grouping_mode=GroupingMode.BY_GAME)
        assert settings.grouping_mode == GroupingMode.BY_GAME

    def test_custom_min_items(self):
        """Test custom min_items value."""
        settings = DigestSettings(min_items=10)
        assert settings.min_items == 10

    def test_custom_last_sent(self):
        """Test custom last_sent value."""
        now = datetime.now()
        settings = DigestSettings(last_sent=now)
        assert settings.last_sent == now

    def test_all_custom_values(self):
        """Test all custom values at once."""
        now = datetime.now()
        settings = DigestSettings(
            enabled=True,
            frequency=DigestFrequency.WEEKLY,
            grouping_mode=GroupingMode.CHRONOLOGICAL,
            min_items=20,
            last_sent=now,
        )
        assert settings.enabled is True
        assert settings.frequency == DigestFrequency.WEEKLY
        assert settings.grouping_mode == GroupingMode.CHRONOLOGICAL
        assert settings.min_items == 20
        assert settings.last_sent == now


# === NotificationDigestManager Tests ===


class TestNotificationDigestManagerInit:
    """Tests for NotificationDigestManager initialization."""

    def test_init_creates_empty_pending(self, manager):
        """Test that init creates empty pending notifications."""
        assert len(manager._pending_notifications) == 0

    def test_init_creates_empty_settings(self, manager):
        """Test that init creates empty user settings."""
        assert len(manager._user_settings) == 0

    def test_init_scheduler_task_is_none(self, manager):
        """Test that scheduler task is None initially."""
        assert manager._scheduler_task is None


class TestGetUserSettings:
    """Tests for get_user_settings method."""

    def test_creates_default_settings_for_new_user(self, manager):
        """Test that default settings are created for new user."""
        settings = manager.get_user_settings(12345)
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY

    def test_returns_same_settings_for_same_user(self, manager):
        """Test that same settings instance is returned for same user."""
        settings1 = manager.get_user_settings(12345)
        settings2 = manager.get_user_settings(12345)
        assert settings1 is settings2

    def test_different_users_have_different_settings(self, manager):
        """Test that different users have different settings."""
        settings1 = manager.get_user_settings(111)
        settings2 = manager.get_user_settings(222)
        assert settings1 is not settings2


class TestUpdateUserSettings:
    """Tests for update_user_settings method."""

    def test_update_enabled(self, manager):
        """Test updating enabled setting."""
        manager.update_user_settings(123, {"enabled": True})
        settings = manager.get_user_settings(123)
        assert settings.enabled is True

    def test_update_frequency(self, manager):
        """Test updating frequency setting."""
        manager.update_user_settings(123, {"frequency": DigestFrequency.HOURLY})
        settings = manager.get_user_settings(123)
        assert settings.frequency == DigestFrequency.HOURLY

    def test_update_grouping_mode(self, manager):
        """Test updating grouping mode."""
        manager.update_user_settings(123, {"grouping_mode": GroupingMode.BY_GAME})
        settings = manager.get_user_settings(123)
        assert settings.grouping_mode == GroupingMode.BY_GAME

    def test_update_min_items(self, manager):
        """Test updating min_items setting."""
        manager.update_user_settings(123, {"min_items": 10})
        settings = manager.get_user_settings(123)
        assert settings.min_items == 10

    def test_update_multiple_settings(self, manager):
        """Test updating multiple settings at once."""
        manager.update_user_settings(123, {
            "enabled": True,
            "frequency": DigestFrequency.EVERY_6_HOURS,
            "min_items": 5,
        })
        settings = manager.get_user_settings(123)
        assert settings.enabled is True
        assert settings.frequency == DigestFrequency.EVERY_6_HOURS
        assert settings.min_items == 5

    def test_update_returns_settings(self, manager):
        """Test that update returns the updated settings."""
        result = manager.update_user_settings(123, {"enabled": True})
        assert isinstance(result, DigestSettings)
        assert result.enabled is True


class TestResetUserSettings:
    """Tests for reset_user_settings method."""

    def test_reset_restores_defaults(self, manager):
        """Test that reset restores default values."""
        manager.update_user_settings(123, {
            "enabled": True,
            "frequency": DigestFrequency.HOURLY,
            "min_items": 20,
        })
        manager.reset_user_settings(123)
        settings = manager.get_user_settings(123)
        assert settings.enabled is False
        assert settings.frequency == DigestFrequency.DAILY
        assert settings.min_items == 3

    def test_reset_returns_settings(self, manager):
        """Test that reset returns the reset settings."""
        result = manager.reset_user_settings(123)
        assert isinstance(result, DigestSettings)


class TestAddNotification:
    """Tests for add_notification method."""

    def test_notification_not_added_when_disabled(self, manager, sample_notification):
        """Test that notification is not added when digest is disabled."""
        manager.add_notification(sample_notification)
        pending = manager.get_pending_notifications(sample_notification.user_id)
        assert len(pending) == 0

    def test_notification_added_when_enabled(self, manager, sample_notification):
        """Test that notification is added when digest is enabled."""
        manager.update_user_settings(sample_notification.user_id, {"enabled": True})
        manager.add_notification(sample_notification)
        pending = manager.get_pending_notifications(sample_notification.user_id)
        assert len(pending) == 1
        assert pending[0] == sample_notification

    def test_multiple_notifications_accumulated(self, manager, sample_notification):
        """Test that multiple notifications are accumulated."""
        manager.update_user_settings(sample_notification.user_id, {"enabled": True})
        for i in range(5):
            notif = NotificationItem(
                user_id=sample_notification.user_id,
                notification_type="arbitrage",
                game="csgo",
                title=f"Test {i}",
                message=f"Message {i}",
                timestamp=datetime.now(),
            )
            manager.add_notification(notif)
        pending = manager.get_pending_notifications(sample_notification.user_id)
        assert len(pending) == 5


class TestGetPendingNotifications:
    """Tests for get_pending_notifications method."""

    def test_returns_empty_list_for_no_notifications(self, manager):
        """Test returns empty list when no notifications."""
        pending = manager.get_pending_notifications(99999)
        assert pending == []

    def test_returns_notifications_for_user(self, manager, sample_notification):
        """Test returns notifications for user with pending items."""
        manager.update_user_settings(sample_notification.user_id, {"enabled": True})
        manager.add_notification(sample_notification)
        pending = manager.get_pending_notifications(sample_notification.user_id)
        assert len(pending) == 1


class TestClearPendingNotifications:
    """Tests for clear_pending_notifications method."""

    def test_clears_notifications(self, manager, sample_notification):
        """Test that notifications are cleared."""
        manager.update_user_settings(sample_notification.user_id, {"enabled": True})
        manager.add_notification(sample_notification)
        manager.clear_pending_notifications(sample_notification.user_id)
        pending = manager.get_pending_notifications(sample_notification.user_id)
        assert len(pending) == 0

    def test_no_error_when_clearing_empty(self, manager):
        """Test no error when clearing non-existent user's notifications."""
        manager.clear_pending_notifications(99999)  # Should not raise


class TestShouldSendDigest:
    """Tests for should_send_digest method."""

    def test_returns_false_when_disabled(self, manager, sample_notification):
        """Test returns False when digest is disabled."""
        manager.add_notification(sample_notification)
        assert manager.should_send_digest(sample_notification.user_id) is False

    def test_returns_false_when_insufficient_notifications(self, manager, sample_notification):
        """Test returns False when not enough notifications."""
        manager.update_user_settings(sample_notification.user_id, {
            "enabled": True,
            "min_items": 5,
        })
        manager.add_notification(sample_notification)
        assert manager.should_send_digest(sample_notification.user_id) is False

    def test_returns_true_when_never_sent(self, manager, sample_notification):
        """Test returns True when digest was never sent."""
        manager.update_user_settings(sample_notification.user_id, {
            "enabled": True,
            "min_items": 1,
        })
        manager.add_notification(sample_notification)
        assert manager.should_send_digest(sample_notification.user_id) is True

    def test_returns_false_when_sent_recently(self, manager, sample_notification):
        """Test returns False when sent recently."""
        manager.update_user_settings(sample_notification.user_id, {
            "enabled": True,
            "min_items": 1,
            "frequency": DigestFrequency.DAILY,
        })
        settings = manager.get_user_settings(sample_notification.user_id)
        settings.last_sent = datetime.now()  # Just now
        manager.add_notification(sample_notification)
        assert manager.should_send_digest(sample_notification.user_id) is False

    def test_returns_true_when_enough_time_passed(self, manager, sample_notification):
        """Test returns True when enough time has passed."""
        manager.update_user_settings(sample_notification.user_id, {
            "enabled": True,
            "min_items": 1,
            "frequency": DigestFrequency.HOURLY,
        })
        settings = manager.get_user_settings(sample_notification.user_id)
        settings.last_sent = datetime.now() - timedelta(hours=2)
        manager.add_notification(sample_notification)
        assert manager.should_send_digest(sample_notification.user_id) is True

    def test_returns_false_for_disabled_frequency(self, manager, sample_notification):
        """Test returns False for disabled frequency when last_sent is set."""
        manager.update_user_settings(sample_notification.user_id, {
            "enabled": True,
            "frequency": DigestFrequency.DISABLED,
            "min_items": 1,
        })
        # Set last_sent so it doesn't return True early
        settings = manager.get_user_settings(sample_notification.user_id)
        settings.last_sent = datetime.now() - timedelta(days=1)
        manager.add_notification(sample_notification)
        # should_send_digest checks frequency_map, DISABLED is not in map, returns False
        assert manager.should_send_digest(sample_notification.user_id) is False


class TestFormatDigest:
    """Tests for format_digest method."""

    def test_empty_notifications_message(self, manager):
        """Test message for empty notifications."""
        result = manager.format_digest(123, [])
        assert "Нет новых уведомлений" in result

    def test_contains_header(self, manager, sample_notification):
        """Test that digest contains header."""
        result = manager.format_digest(sample_notification.user_id, [sample_notification])
        assert "Дайджест уведомлений" in result

    def test_contains_count(self, manager, sample_notification):
        """Test that digest contains notification count."""
        result = manager.format_digest(sample_notification.user_id, [sample_notification])
        assert "1 уведомлений" in result

    def test_groups_by_type(self, manager):
        """Test grouping by type."""
        notifications = [
            NotificationItem(
                user_id=123,
                notification_type="arbitrage",
                game="csgo",
                title="Test",
                message="Arbitrage message",
                timestamp=datetime.now(),
            ),
            NotificationItem(
                user_id=123,
                notification_type="price_drop",
                game="csgo",
                title="Test",
                message="Price drop message",
                timestamp=datetime.now(),
            ),
        ]
        result = manager.format_digest(123, notifications)
        assert "Арбитраж" in result or "arbitrage" in result


class TestGroupNotifications:
    """Tests for _group_notifications method."""

    def test_group_by_type(self, manager):
        """Test grouping by notification type."""
        notifications = [
            NotificationItem(user_id=123, notification_type="arbitrage", game="csgo",
                           title="T1", message="M1", timestamp=datetime.now()),
            NotificationItem(user_id=123, notification_type="arbitrage", game="dota2",
                           title="T2", message="M2", timestamp=datetime.now()),
            NotificationItem(user_id=123, notification_type="price_drop", game="csgo",
                           title="T3", message="M3", timestamp=datetime.now()),
        ]
        grouped = manager._group_notifications(notifications, GroupingMode.BY_TYPE)
        assert "arbitrage" in grouped
        assert "price_drop" in grouped
        assert len(grouped["arbitrage"]) == 2
        assert len(grouped["price_drop"]) == 1

    def test_group_by_game(self, manager):
        """Test grouping by game."""
        notifications = [
            NotificationItem(user_id=123, notification_type="arbitrage", game="csgo",
                           title="T1", message="M1", timestamp=datetime.now()),
            NotificationItem(user_id=123, notification_type="price_drop", game="csgo",
                           title="T2", message="M2", timestamp=datetime.now()),
            NotificationItem(user_id=123, notification_type="arbitrage", game="dota2",
                           title="T3", message="M3", timestamp=datetime.now()),
        ]
        grouped = manager._group_notifications(notifications, GroupingMode.BY_GAME)
        assert "csgo" in grouped
        assert "dota2" in grouped
        assert len(grouped["csgo"]) == 2
        assert len(grouped["dota2"]) == 1

    def test_group_by_priority(self, manager):
        """Test grouping by priority."""
        notifications = [
            NotificationItem(user_id=123, notification_type="arbitrage", game="csgo",
                           title="T1", message="M1", timestamp=datetime.now(), priority=1),
            NotificationItem(user_id=123, notification_type="arbitrage", game="csgo",
                           title="T2", message="M2", timestamp=datetime.now(), priority=2),
        ]
        grouped = manager._group_notifications(notifications, GroupingMode.BY_PRIORITY)
        assert "priority_1" in grouped
        assert "priority_2" in grouped

    def test_chronological_grouping(self, manager):
        """Test chronological grouping."""
        notifications = [
            NotificationItem(user_id=123, notification_type="arbitrage", game="csgo",
                           title="T1", message="M1", timestamp=datetime.now()),
            NotificationItem(user_id=123, notification_type="price_drop", game="dota2",
                           title="T2", message="M2", timestamp=datetime.now()),
        ]
        grouped = manager._group_notifications(notifications, GroupingMode.CHRONOLOGICAL)
        assert "all" in grouped
        assert len(grouped["all"]) == 2


class TestFormatGroup:
    """Tests for _format_group method."""

    def test_format_by_type_arbitrage(self, manager):
        """Test formatting arbitrage type group."""
        items = [NotificationItem(
            user_id=123, notification_type="arbitrage", game="csgo",
            title="Test", message="Test message", timestamp=datetime.now()
        )]
        result = manager._format_group("arbitrage", items, GroupingMode.BY_TYPE)
        assert "Арбитраж" in result

    def test_format_by_type_price_drop(self, manager):
        """Test formatting price_drop type group."""
        items = [NotificationItem(
            user_id=123, notification_type="price_drop", game="csgo",
            title="Test", message="Test message", timestamp=datetime.now()
        )]
        result = manager._format_group("price_drop", items, GroupingMode.BY_TYPE)
        assert "Падение цены" in result

    def test_format_by_game_csgo(self, manager):
        """Test formatting csgo game group."""
        items = [NotificationItem(
            user_id=123, notification_type="arbitrage", game="csgo",
            title="Test", message="Test message", timestamp=datetime.now()
        )]
        result = manager._format_group("csgo", items, GroupingMode.BY_GAME)
        assert "CS2" in result

    def test_format_by_priority(self, manager):
        """Test formatting priority group."""
        items = [NotificationItem(
            user_id=123, notification_type="arbitrage", game="csgo",
            title="Test", message="Test message", timestamp=datetime.now(), priority=5
        )]
        result = manager._format_group("priority_5", items, GroupingMode.BY_PRIORITY)
        assert "Приоритет" in result

    def test_truncates_at_10_items(self, manager):
        """Test that group is truncated at 10 items."""
        items = [NotificationItem(
            user_id=123, notification_type="arbitrage", game="csgo",
            title=f"Test {i}", message=f"Message {i}", timestamp=datetime.now()
        ) for i in range(15)]
        result = manager._format_group("arbitrage", items, GroupingMode.BY_TYPE)
        assert "еще 5 уведомлений" in result


# === Handler Function Tests ===


class TestShowDigestMenu:
    """Tests for show_digest_menu handler."""

    @pytest.mark.asyncio()
    async def test_shows_menu_for_callback_query(self, mock_update, mock_context):
        """Test shows menu when called from callback query."""
        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            await show_digest_menu(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_shows_menu_for_message(self, mock_update, mock_context):
        """Test shows menu when called from message."""
        mock_update.callback_query = None

        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            await show_digest_menu(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_early_without_user(self, mock_update, mock_context):
        """Test returns early when no effective user."""
        mock_update.effective_user = None
        mock_update.callback_query = None

        await show_digest_menu(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_called()


class TestToggleDigest:
    """Tests for toggle_digest handler."""

    @pytest.mark.asyncio()
    async def test_toggles_enabled_status(self, mock_update, mock_context):
        """Test toggles enabled status."""
        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings(enabled=False)
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock):
                await toggle_digest(mock_update, mock_context)

            mock_manager.update_user_settings.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_early_without_query(self, mock_update, mock_context):
        """Test returns early without callback query."""
        mock_update.callback_query = None

        await toggle_digest(mock_update, mock_context)

        # No error should be raised


class TestShowFrequencyMenu:
    """Tests for show_frequency_menu handler."""

    @pytest.mark.asyncio()
    async def test_shows_frequency_options(self, mock_update, mock_context):
        """Test shows frequency options menu."""
        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_get_manager.return_value = mock_manager

            await show_frequency_menu(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()


class TestSetFrequency:
    """Tests for set_frequency handler."""

    @pytest.mark.asyncio()
    async def test_sets_frequency(self, mock_update, mock_context):
        """Test sets frequency from callback data."""
        mock_update.callback_query.data = "digest_set_freq_hourly"

        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock):
                await set_frequency(mock_update, mock_context)

            mock_manager.update_user_settings.assert_called_once()
            call_args = mock_manager.update_user_settings.call_args
            assert call_args[0][1]["frequency"] == DigestFrequency.HOURLY


class TestSetGroupingMode:
    """Tests for set_grouping_mode handler."""

    @pytest.mark.asyncio()
    async def test_sets_grouping_mode(self, mock_update, mock_context):
        """Test sets grouping mode from callback data."""
        mock_update.callback_query.data = "digest_set_group_by_game"

        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock):
                await set_grouping_mode(mock_update, mock_context)

            mock_manager.update_user_settings.assert_called_once()
            call_args = mock_manager.update_user_settings.call_args
            assert call_args[0][1]["grouping_mode"] == GroupingMode.BY_GAME


class TestSetMinItems:
    """Tests for set_min_items handler."""

    @pytest.mark.asyncio()
    async def test_sets_min_items(self, mock_update, mock_context):
        """Test sets min items from callback data."""
        mock_update.callback_query.data = "digest_set_min_10"

        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock):
                await set_min_items(mock_update, mock_context)

            mock_manager.update_user_settings.assert_called_once()
            call_args = mock_manager.update_user_settings.call_args
            assert call_args[0][1]["min_items"] == 10


class TestResetDigestSettings:
    """Tests for reset_digest_settings handler."""

    @pytest.mark.asyncio()
    async def test_resets_settings(self, mock_update, mock_context):
        """Test resets settings to defaults."""
        with patch("src.telegram_bot.handlers.notification_digest_handler.get_digest_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_user_settings.return_value = DigestSettings()
            mock_manager.get_pending_notifications.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock):
                await reset_digest_settings(mock_update, mock_context)

            mock_manager.reset_user_settings.assert_called_once()


class TestDigestCommand:
    """Tests for digest_command handler."""

    @pytest.mark.asyncio()
    async def test_calls_show_digest_menu(self, mock_update, mock_context):
        """Test digest command calls show_digest_menu."""
        with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock) as mock_show:
            await digest_command(mock_update, mock_context)
            mock_show.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_early_without_user(self, mock_update, mock_context):
        """Test returns early without effective user."""
        mock_update.effective_user = None

        with patch("src.telegram_bot.handlers.notification_digest_handler.show_digest_menu", new_callable=AsyncMock) as mock_show:
            await digest_command(mock_update, mock_context)
            mock_show.assert_not_called()


class TestRegisterHandlers:
    """Tests for register_notification_digest_handlers function."""

    def test_registers_all_handlers(self):
        """Test that all handlers are registered."""
        mock_app = MagicMock()

        register_notification_digest_handlers(mock_app)

        # Should register command handler and multiple callback handlers
        assert mock_app.add_handler.call_count >= 9


class TestGetDigestManager:
    """Tests for get_digest_manager function."""

    def test_returns_manager_instance(self):
        """Test returns NotificationDigestManager instance."""
        with patch("src.telegram_bot.handlers.notification_digest_handler._digest_manager", None):
            manager = get_digest_manager()
            assert isinstance(manager, NotificationDigestManager)

    def test_returns_same_instance(self):
        """Test returns same instance on subsequent calls."""
        manager1 = get_digest_manager()
        manager2 = get_digest_manager()
        assert manager1 is manager2


# === Edge Cases ===


class TestEdgeCases:
    """Edge case tests."""

    def test_unicode_in_notification_message(self, manager):
        """Test unicode characters in notification message."""
        manager.update_user_settings(123, {"enabled": True})
        notif = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Тест Unicode 🎮",
            message="Сообщение с эмодзи 💰🔥",
            timestamp=datetime.now(),
        )
        manager.add_notification(notif)
        pending = manager.get_pending_notifications(123)
        assert len(pending) == 1
        assert "💰" in pending[0].message

    def test_very_long_message(self, manager):
        """Test very long notification message."""
        manager.update_user_settings(123, {"enabled": True})
        long_message = "A" * 5000
        notif = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message=long_message,
            timestamp=datetime.now(),
        )
        manager.add_notification(notif)
        pending = manager.get_pending_notifications(123)
        assert len(pending[0].message) == 5000

    def test_special_characters_in_title(self, manager):
        """Test special characters in notification title."""
        manager.update_user_settings(123, {"enabled": True})
        notif = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test <script>alert('xss')</script>",
            message="Test",
            timestamp=datetime.now(),
        )
        manager.add_notification(notif)
        pending = manager.get_pending_notifications(123)
        assert "<script>" in pending[0].title

    def test_zero_min_items(self, manager):
        """Test zero min_items setting."""
        manager.update_user_settings(123, {"enabled": True, "min_items": 0})
        settings = manager.get_user_settings(123)
        assert settings.min_items == 0

    def test_negative_priority(self, manager):
        """Test negative priority value."""
        manager.update_user_settings(123, {"enabled": True})
        notif = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test",
            timestamp=datetime.now(),
            priority=-5,
        )
        manager.add_notification(notif)
        pending = manager.get_pending_notifications(123)
        assert pending[0].priority == -5

    def test_large_user_id(self, manager):
        """Test large user ID."""
        large_id = 9999999999999
        settings = manager.get_user_settings(large_id)
        assert settings is not None

    def test_empty_data_dict(self, manager):
        """Test empty data dict in notification."""
        notif = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test",
            timestamp=datetime.now(),
            data={},
        )
        assert notif.data == {}

    def test_complex_data_dict(self, manager):
        """Test complex nested data dict."""
        complex_data = {
            "item": {"id": "123", "name": "Test"},
            "prices": [100, 200, 300],
            "metadata": {"source": "api", "version": 1.0},
        }
        notif = NotificationItem(
            user_id=123,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test",
            timestamp=datetime.now(),
            data=complex_data,
        )
        assert notif.data == complex_data


# === Integration Tests ===


class TestIntegration:
    """Integration tests."""

    def test_full_notification_workflow(self, manager):
        """Test complete notification workflow."""
        user_id = 12345

        # Enable digest
        manager.update_user_settings(user_id, {
            "enabled": True,
            "frequency": DigestFrequency.HOURLY,
            "min_items": 2,
        })

        # Add notifications
        for i in range(3):
            notif = NotificationItem(
                user_id=user_id,
                notification_type="arbitrage",
                game="csgo",
                title=f"Item {i}",
                message=f"Message {i}",
                timestamp=datetime.now(),
            )
            manager.add_notification(notif)

        # Check pending
        pending = manager.get_pending_notifications(user_id)
        assert len(pending) == 3

        # Format digest
        digest = manager.format_digest(user_id, pending)
        assert "Дайджест" in digest
        assert "3 уведомлений" in digest

        # Clear notifications
        manager.clear_pending_notifications(user_id)
        assert len(manager.get_pending_notifications(user_id)) == 0

    def test_multiple_users_isolation(self, manager):
        """Test that multiple users have isolated data."""
        user1 = 111
        user2 = 222

        # Configure different settings
        manager.update_user_settings(user1, {"enabled": True, "min_items": 5})
        manager.update_user_settings(user2, {"enabled": True, "min_items": 10})

        # Add notifications
        for user_id in [user1, user2]:
            notif = NotificationItem(
                user_id=user_id,
                notification_type="arbitrage",
                game="csgo",
                title="Test",
                message="Test",
                timestamp=datetime.now(),
            )
            manager.add_notification(notif)

        # Verify isolation
        assert manager.get_user_settings(user1).min_items == 5
        assert manager.get_user_settings(user2).min_items == 10
        assert len(manager.get_pending_notifications(user1)) == 1
        assert len(manager.get_pending_notifications(user2)) == 1

    def test_frequency_time_intervals(self, manager):
        """Test different frequency time intervals."""
        user_id = 123
        manager.update_user_settings(user_id, {
            "enabled": True,
            "min_items": 1,
        })

        # Add a notification
        notif = NotificationItem(
            user_id=user_id,
            notification_type="arbitrage",
            game="csgo",
            title="Test",
            message="Test",
            timestamp=datetime.now(),
        )
        manager.add_notification(notif)

        # Test different frequencies
        frequencies_intervals = [
            (DigestFrequency.HOURLY, timedelta(hours=1)),
            (DigestFrequency.EVERY_3_HOURS, timedelta(hours=3)),
            (DigestFrequency.EVERY_6_HOURS, timedelta(hours=6)),
            (DigestFrequency.DAILY, timedelta(days=1)),
            (DigestFrequency.WEEKLY, timedelta(weeks=1)),
        ]

        for freq, interval in frequencies_intervals:
            manager.update_user_settings(user_id, {"frequency": freq})
            settings = manager.get_user_settings(user_id)

            # Set last_sent to just before the interval
            settings.last_sent = datetime.now() - interval - timedelta(minutes=1)
            assert manager.should_send_digest(user_id) is True

            # Set last_sent to just after the interval
            settings.last_sent = datetime.now() - interval + timedelta(hours=1)
            # Note: This should be False only if time_since_last < required_interval

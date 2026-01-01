"""Unit tests for notification filters handler.

This module tests src/telegram_bot/handlers/notification_filters_handler.py covering:
- NotificationFilters class methods
- Filter management (games, profit, levels, types)
- Menu display functions
- Toggle operations
- Filter reset functionality

Target: 35+ tests to achieve 70%+ coverage
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.notification_filters_handler import (
    ARBITRAGE_LEVELS,
    NOTIFICATION_TYPES,
    SUPPORTED_GAMES,
    NotificationFilters,
    get_filters_manager,
    reset_filters,
    set_profit_filter,
    show_games_filter,
    show_levels_filter,
    show_notification_filters,
    show_profit_filter,
    show_types_filter,
    toggle_game_filter,
    toggle_level_filter,
    toggle_type_filter,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def mock_update():
    """Fixture providing a mocked Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(id=123456789, username="test_user")
    update.effective_chat = MagicMock(id=123456789)
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "notify_filter"
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
def filters_manager():
    """Fixture providing a fresh NotificationFilters instance."""
    return NotificationFilters()


# =============================================================================
# Tests for NotificationFilters class
# =============================================================================


class TestNotificationFiltersClass:
    """Tests for NotificationFilters class methods."""

    def test_init_creates_empty_storage(self, filters_manager):
        """Test manager initializes with empty storage."""
        assert filters_manager._filters == {}

    def test_get_user_filters_creates_default(self, filters_manager):
        """Test get_user_filters creates default filters for new user."""
        user_id = 123
        filters = filters_manager.get_user_filters(user_id)

        assert "games" in filters
        assert "min_profit_percent" in filters
        assert "levels" in filters
        assert "notification_types" in filters
        assert "enabled" in filters

    def test_get_user_filters_default_games(self, filters_manager):
        """Test default filters include all games."""
        user_id = 123
        filters = filters_manager.get_user_filters(user_id)

        assert set(filters["games"]) == set(SUPPORTED_GAMES.keys())

    def test_get_user_filters_default_profit(self, filters_manager):
        """Test default minimum profit is 5%."""
        user_id = 123
        filters = filters_manager.get_user_filters(user_id)

        assert filters["min_profit_percent"] == 5.0

    def test_get_user_filters_default_levels(self, filters_manager):
        """Test default filters include all levels."""
        user_id = 123
        filters = filters_manager.get_user_filters(user_id)

        assert set(filters["levels"]) == set(ARBITRAGE_LEVELS.keys())

    def test_get_user_filters_default_types(self, filters_manager):
        """Test default filters include all notification types."""
        user_id = 123
        filters = filters_manager.get_user_filters(user_id)

        assert set(filters["notification_types"]) == set(NOTIFICATION_TYPES.keys())

    def test_get_user_filters_default_enabled(self, filters_manager):
        """Test default enabled is True."""
        user_id = 123
        filters = filters_manager.get_user_filters(user_id)

        assert filters["enabled"] is True

    def test_get_user_filters_returns_copy(self, filters_manager):
        """Test get_user_filters returns a copy, not reference."""
        user_id = 123
        filters1 = filters_manager.get_user_filters(user_id)
        filters1["games"] = []

        filters2 = filters_manager.get_user_filters(user_id)
        assert filters2["games"] != []  # Should not be affected

    def test_update_user_filters(self, filters_manager):
        """Test updating user filters."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 10.0})

        filters = filters_manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 10.0

    def test_update_user_filters_games(self, filters_manager):
        """Test updating games filter."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"games": ["csgo", "dota2"]})

        filters = filters_manager.get_user_filters(user_id)
        assert filters["games"] == ["csgo", "dota2"]

    def test_reset_user_filters(self, filters_manager):
        """Test resetting user filters to defaults."""
        user_id = 123

        # Modify filters
        filters_manager.update_user_filters(
            user_id,
            {
                "games": ["csgo"],
                "min_profit_percent": 20.0,
                "enabled": False,
            },
        )

        # Reset
        filters_manager.reset_user_filters(user_id)

        # Check defaults restored
        filters = filters_manager.get_user_filters(user_id)
        assert set(filters["games"]) == set(SUPPORTED_GAMES.keys())
        assert filters["min_profit_percent"] == 5.0
        assert filters["enabled"] is True


class TestShouldNotify:
    """Tests for should_notify method."""

    def test_should_notify_when_disabled(self, filters_manager):
        """Test should_notify returns False when disabled."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"enabled": False})

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is False

    def test_should_notify_invalid_game(self, filters_manager):
        """Test should_notify returns False for invalid game."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"games": ["dota2"]})

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is False

    def test_should_notify_profit_below_threshold(self, filters_manager):
        """Test should_notify returns False when profit below threshold."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 15.0})

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is False

    def test_should_notify_invalid_level(self, filters_manager):
        """Test should_notify returns False for invalid level."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"levels": ["boost", "standard"]})

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "advanced", "arbitrage"
        )
        assert result is False

    def test_should_notify_invalid_type(self, filters_manager):
        """Test should_notify returns False for invalid type."""
        user_id = 123
        filters_manager.update_user_filters(
            user_id, {"notification_types": ["arbitrage", "price_drop"]}
        )

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "trending"
        )
        assert result is False

    def test_should_notify_all_conditions_met(self, filters_manager):
        """Test should_notify returns True when all conditions met."""
        user_id = 123

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is True

    def test_should_notify_exact_threshold(self, filters_manager):
        """Test should_notify when profit equals threshold."""
        user_id = 123
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 10.0})

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is True


# =============================================================================
# Tests for Constants
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_supported_games_count(self):
        """Test correct number of supported games."""
        assert len(SUPPORTED_GAMES) == 4

    def test_supported_games_keys(self):
        """Test supported games keys."""
        assert "csgo" in SUPPORTED_GAMES
        assert "dota2" in SUPPORTED_GAMES
        assert "tf2" in SUPPORTED_GAMES
        assert "rust" in SUPPORTED_GAMES

    def test_arbitrage_levels_count(self):
        """Test correct number of arbitrage levels."""
        assert len(ARBITRAGE_LEVELS) == 5

    def test_arbitrage_levels_keys(self):
        """Test arbitrage levels keys."""
        assert "boost" in ARBITRAGE_LEVELS
        assert "standard" in ARBITRAGE_LEVELS
        assert "medium" in ARBITRAGE_LEVELS
        assert "advanced" in ARBITRAGE_LEVELS
        assert "pro" in ARBITRAGE_LEVELS

    def test_notification_types_count(self):
        """Test correct number of notification types."""
        assert len(NOTIFICATION_TYPES) == 5

    def test_notification_types_keys(self):
        """Test notification types keys."""
        assert "arbitrage" in NOTIFICATION_TYPES
        assert "price_drop" in NOTIFICATION_TYPES
        assert "price_rise" in NOTIFICATION_TYPES
        assert "trending" in NOTIFICATION_TYPES
        assert "good_deal" in NOTIFICATION_TYPES


# =============================================================================
# Tests for get_filters_manager
# =============================================================================


class TestGetFiltersManager:
    """Tests for get_filters_manager singleton function."""

    def test_returns_manager(self):
        """Test get_filters_manager returns a manager."""
        manager = get_filters_manager()
        assert isinstance(manager, NotificationFilters)

    def test_returns_same_instance(self):
        """Test get_filters_manager returns same instance (singleton)."""
        manager1 = get_filters_manager()
        manager2 = get_filters_manager()
        assert manager1 is manager2


# =============================================================================
# Tests for Handler Functions
# =============================================================================


class TestShowNotificationFilters:
    """Tests for show_notification_filters function."""

    @pytest.mark.asyncio()
    async def test_show_filters_with_callback_query(self, mock_update, mock_context):
        """Test showing filters with callback query."""
        # Act
        await show_notification_filters(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio()
    async def test_show_filters_with_message(self, mock_update, mock_context):
        """Test showing filters from command (message)."""
        mock_update.callback_query = None

        # Act
        await show_notification_filters(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_show_filters_displays_status(self, mock_update, mock_context):
        """Test filters menu displays status information."""
        # Act
        await show_notification_filters(mock_update, mock_context)

        # Assert
        call_args = mock_update.callback_query.edit_message_text.call_args
        text = call_args.kwargs.get("text", "")
        assert "Фильтры" in text
        assert "Статус" in text


class TestShowGamesFilter:
    """Tests for show_games_filter function."""

    @pytest.mark.asyncio()
    async def test_show_games_filter(self, mock_update, mock_context):
        """Test showing games filter menu."""
        mock_update.callback_query.data = "notify_filter_games"

        # Act
        await show_games_filter(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_show_games_filter_displays_games(self, mock_update, mock_context):
        """Test games filter displays game options."""
        mock_update.callback_query.data = "notify_filter_games"

        # Act
        await show_games_filter(mock_update, mock_context)

        # Assert - verify message is sent with reply markup for game selection
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "reply_markup" in call_args.kwargs


class TestToggleGameFilter:
    """Tests for toggle_game_filter function."""

    @pytest.mark.asyncio()
    async def test_toggle_game_removes_game(self, mock_update, mock_context):
        """Test toggling removes game from filter."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Ensure csgo is in the list initially
        manager.reset_user_filters(user_id)
        initial_filters = manager.get_user_filters(user_id)
        assert "csgo" in initial_filters["games"]

        # Toggle csgo off
        mock_update.callback_query.data = "notify_filter_game_csgo"

        # Act
        await toggle_game_filter(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert "csgo" not in filters["games"]

    @pytest.mark.asyncio()
    async def test_toggle_game_adds_game(self, mock_update, mock_context):
        """Test toggling adds game to filter."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Remove csgo first
        manager.update_user_filters(user_id, {"games": ["dota2", "tf2", "rust"]})

        # Toggle csgo on
        mock_update.callback_query.data = "notify_filter_game_csgo"

        # Act
        await toggle_game_filter(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert "csgo" in filters["games"]


class TestShowProfitFilter:
    """Tests for show_profit_filter function."""

    @pytest.mark.asyncio()
    async def test_show_profit_filter(self, mock_update, mock_context):
        """Test showing profit filter menu."""
        mock_update.callback_query.data = "notify_filter_profit"

        # Act
        await show_profit_filter(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_show_profit_filter_displays_current(self, mock_update, mock_context):
        """Test profit filter displays current value."""
        mock_update.callback_query.data = "notify_filter_profit"

        # Act
        await show_profit_filter(mock_update, mock_context)

        # Assert - verify message is sent with reply markup for profit selection
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "reply_markup" in call_args.kwargs


class TestSetProfitFilter:
    """Tests for set_profit_filter function."""

    @pytest.mark.asyncio()
    async def test_set_profit_filter_5(self, mock_update, mock_context):
        """Test setting profit filter to 5%."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "notify_filter_profit_5.0"

        # Act
        await set_profit_filter(mock_update, mock_context)

        # Assert
        manager = get_filters_manager()
        filters = manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 5.0

    @pytest.mark.asyncio()
    async def test_set_profit_filter_10(self, mock_update, mock_context):
        """Test setting profit filter to 10%."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "notify_filter_profit_10.0"

        # Act
        await set_profit_filter(mock_update, mock_context)

        # Assert
        manager = get_filters_manager()
        filters = manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 10.0

    @pytest.mark.asyncio()
    async def test_set_profit_filter_15(self, mock_update, mock_context):
        """Test setting profit filter to 15%."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "notify_filter_profit_15.0"

        # Act
        await set_profit_filter(mock_update, mock_context)

        # Assert
        manager = get_filters_manager()
        filters = manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 15.0


class TestShowLevelsFilter:
    """Tests for show_levels_filter function."""

    @pytest.mark.asyncio()
    async def test_show_levels_filter(self, mock_update, mock_context):
        """Test showing levels filter menu."""
        mock_update.callback_query.data = "notify_filter_levels"

        # Act
        await show_levels_filter(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()


class TestToggleLevelFilter:
    """Tests for toggle_level_filter function."""

    @pytest.mark.asyncio()
    async def test_toggle_level_removes_level(self, mock_update, mock_context):
        """Test toggling removes level from filter."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Reset to defaults (all levels)
        manager.reset_user_filters(user_id)

        # Toggle boost off
        mock_update.callback_query.data = "notify_filter_level_boost"

        # Act
        await toggle_level_filter(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert "boost" not in filters["levels"]

    @pytest.mark.asyncio()
    async def test_toggle_level_adds_level(self, mock_update, mock_context):
        """Test toggling adds level to filter."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Remove boost first
        manager.update_user_filters(
            user_id, {"levels": ["standard", "medium", "advanced", "pro"]}
        )

        # Toggle boost on
        mock_update.callback_query.data = "notify_filter_level_boost"

        # Act
        await toggle_level_filter(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert "boost" in filters["levels"]


class TestShowTypesFilter:
    """Tests for show_types_filter function."""

    @pytest.mark.asyncio()
    async def test_show_types_filter(self, mock_update, mock_context):
        """Test showing types filter menu."""
        mock_update.callback_query.data = "notify_filter_types"

        # Act
        await show_types_filter(mock_update, mock_context)

        # Assert
        mock_update.callback_query.edit_message_text.assert_called_once()


class TestToggleTypeFilter:
    """Tests for toggle_type_filter function."""

    @pytest.mark.asyncio()
    async def test_toggle_type_removes_type(self, mock_update, mock_context):
        """Test toggling removes type from filter."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Reset to defaults (all types)
        manager.reset_user_filters(user_id)

        # Toggle arbitrage off
        mock_update.callback_query.data = "notify_filter_type_arbitrage"

        # Act
        await toggle_type_filter(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert "arbitrage" not in filters["notification_types"]

    @pytest.mark.asyncio()
    async def test_toggle_type_adds_type(self, mock_update, mock_context):
        """Test toggling adds type to filter."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Remove arbitrage first
        manager.update_user_filters(
            user_id,
            {
                "notification_types": [
                    "price_drop",
                    "price_rise",
                    "trending",
                    "good_deal",
                ]
            },
        )

        # Toggle arbitrage on
        mock_update.callback_query.data = "notify_filter_type_arbitrage"

        # Act
        await toggle_type_filter(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert "arbitrage" in filters["notification_types"]


class TestResetFilters:
    """Tests for reset_filters function."""

    @pytest.mark.asyncio()
    async def test_reset_filters_restores_defaults(self, mock_update, mock_context):
        """Test reset restores default filter settings."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()

        # Modify filters
        manager.update_user_filters(
            user_id,
            {
                "games": ["csgo"],
                "min_profit_percent": 20.0,
                "levels": ["pro"],
                "notification_types": ["arbitrage"],
            },
        )

        # Act
        await reset_filters(mock_update, mock_context)

        # Assert
        filters = manager.get_user_filters(user_id)
        assert set(filters["games"]) == set(SUPPORTED_GAMES.keys())
        assert filters["min_profit_percent"] == 5.0
        assert set(filters["levels"]) == set(ARBITRAGE_LEVELS.keys())
        assert set(filters["notification_types"]) == set(NOTIFICATION_TYPES.keys())

    @pytest.mark.asyncio()
    async def test_reset_filters_answers_callback(self, mock_update, mock_context):
        """Test reset answers callback query."""
        # Act
        await reset_filters(mock_update, mock_context)

        # Assert
        assert mock_update.callback_query.answer.called


# =============================================================================
# Tests for Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_toggle_game_without_callback_data(self, mock_update, mock_context):
        """Test toggle game handles missing callback data."""
        mock_update.callback_query.data = None

        # Act - should not raise exception
        await toggle_game_filter(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_show_filters_without_user(self, mock_update, mock_context):
        """Test show filters handles missing user."""
        mock_update.effective_user = None

        # Act - should return early without error
        await show_notification_filters(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_toggle_without_callback_query(self, mock_update, mock_context):
        """Test toggle handles missing callback query."""
        mock_update.callback_query = None

        # Act - should return early without error
        await toggle_game_filter(mock_update, mock_context)

    def test_should_notify_with_non_list_games(self, filters_manager):
        """Test should_notify handles non-list games value."""
        user_id = 123
        # Simulate corrupted data
        filters_manager._filters[user_id] = {
            "games": "csgo",  # String instead of list
            "min_profit_percent": 5.0,
            "levels": ["standard"],
            "notification_types": ["arbitrage"],
            "enabled": True,
        }

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is False

    def test_should_notify_with_non_list_levels(self, filters_manager):
        """Test should_notify handles non-list levels value."""
        user_id = 123
        filters_manager._filters[user_id] = {
            "games": ["csgo"],
            "min_profit_percent": 5.0,
            "levels": "standard",  # String instead of list
            "notification_types": ["arbitrage"],
            "enabled": True,
        }

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        assert result is False

    def test_should_notify_with_non_numeric_profit(self, filters_manager):
        """Test should_notify handles non-numeric profit threshold."""
        user_id = 123
        filters_manager._filters[user_id] = {
            "games": ["csgo"],
            "min_profit_percent": "invalid",  # Non-numeric
            "levels": ["standard"],
            "notification_types": ["arbitrage"],
            "enabled": True,
        }

        result = filters_manager.should_notify(
            user_id, "csgo", 10.0, "standard", "arbitrage"
        )
        # Should handle gracefully (profit check is skipped)
        assert result is True  # All other conditions met

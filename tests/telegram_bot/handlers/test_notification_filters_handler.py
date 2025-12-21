"""Unit tests for notification filters handler.

This module tests src/telegram_bot/handlers/notification_filters_handler.py covering:
- NotificationFilters class functionality
- Filter menu display
- Game filter toggling
- Profit threshold settings
- Level filter toggling
- Notification type filter toggling
- Filter reset functionality
- should_notify logic

Target: 35+ tests to achieve 70%+ coverage
"""

from unittest.mock import AsyncMock, MagicMock, patch

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


# ============================================================================
# Test fixtures
# ============================================================================


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
    """Fixture providing a fresh NotificationFilters manager."""
    return NotificationFilters()


# ============================================================================
# TestNotificationFilters
# ============================================================================


class TestNotificationFilters:
    """Tests for NotificationFilters class."""

    def test_init_creates_empty_filters(self):
        """Test that manager initializes with empty filters."""
        manager = NotificationFilters()
        assert len(manager._filters) == 0

    def test_get_user_filters_creates_default_for_new_user(self, filters_manager):
        """Test that get_user_filters creates default filters for new user."""
        user_id = 12345
        filters = filters_manager.get_user_filters(user_id)
        
        assert filters["enabled"] is True
        assert "games" in filters
        assert "levels" in filters
        assert "notification_types" in filters
        assert "min_profit_percent" in filters

    def test_get_user_filters_includes_all_games_by_default(self, filters_manager):
        """Test that default filters include all games."""
        user_id = 12345
        filters = filters_manager.get_user_filters(user_id)
        
        assert set(filters["games"]) == set(SUPPORTED_GAMES.keys())

    def test_get_user_filters_includes_all_levels_by_default(self, filters_manager):
        """Test that default filters include all arbitrage levels."""
        user_id = 12345
        filters = filters_manager.get_user_filters(user_id)
        
        assert set(filters["levels"]) == set(ARBITRAGE_LEVELS.keys())

    def test_get_user_filters_includes_all_notification_types_by_default(self, filters_manager):
        """Test that default filters include all notification types."""
        user_id = 12345
        filters = filters_manager.get_user_filters(user_id)
        
        assert set(filters["notification_types"]) == set(NOTIFICATION_TYPES.keys())

    def test_get_user_filters_returns_copy(self, filters_manager):
        """Test that get_user_filters returns a copy, not original."""
        user_id = 12345
        filters1 = filters_manager.get_user_filters(user_id)
        filters1["min_profit_percent"] = 99.0  # Modify the copy
        
        filters2 = filters_manager.get_user_filters(user_id)
        assert filters2["min_profit_percent"] == 5.0  # Original unchanged

    def test_update_user_filters_updates_existing(self, filters_manager):
        """Test that update_user_filters updates existing filters."""
        user_id = 12345
        filters_manager.get_user_filters(user_id)  # Create defaults
        
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 10.0})
        
        filters = filters_manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 10.0

    def test_update_user_filters_creates_new_if_not_exists(self, filters_manager):
        """Test that update_user_filters creates filters if not existing."""
        user_id = 99999
        
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 15.0})
        
        filters = filters_manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 15.0

    def test_reset_user_filters_restores_defaults(self, filters_manager):
        """Test that reset_user_filters restores default values."""
        user_id = 12345
        
        # Set custom values
        filters_manager.update_user_filters(user_id, {
            "games": ["csgo"],
            "min_profit_percent": 20.0,
            "enabled": False,
        })
        
        # Reset
        filters_manager.reset_user_filters(user_id)
        
        filters = filters_manager.get_user_filters(user_id)
        assert filters["enabled"] is True
        assert filters["min_profit_percent"] == 5.0
        assert set(filters["games"]) == set(SUPPORTED_GAMES.keys())


# ============================================================================
# TestShouldNotify
# ============================================================================


class TestShouldNotify:
    """Tests for should_notify method."""

    def test_should_notify_returns_false_when_disabled(self, filters_manager):
        """Test that should_notify returns False when filters are disabled."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"enabled": False})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,
            level="standard",
            notification_type="arbitrage",
        )
        
        assert result is False

    def test_should_notify_returns_false_when_game_not_in_filter(self, filters_manager):
        """Test that should_notify returns False when game not in filter."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"games": ["dota2", "tf2"]})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",  # Not in filter
            profit_percent=10.0,
            level="standard",
            notification_type="arbitrage",
        )
        
        assert result is False

    def test_should_notify_returns_false_when_profit_below_threshold(self, filters_manager):
        """Test that should_notify returns False when profit below threshold."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 15.0})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,  # Below threshold
            level="standard",
            notification_type="arbitrage",
        )
        
        assert result is False

    def test_should_notify_returns_false_when_level_not_in_filter(self, filters_manager):
        """Test that should_notify returns False when level not in filter."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"levels": ["boost", "standard"]})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,
            level="pro",  # Not in filter
            notification_type="arbitrage",
        )
        
        assert result is False

    def test_should_notify_returns_false_when_type_not_in_filter(self, filters_manager):
        """Test that should_notify returns False when notification type not in filter."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"notification_types": ["price_drop"]})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,
            level="standard",
            notification_type="arbitrage",  # Not in filter
        )
        
        assert result is False

    def test_should_notify_returns_true_when_all_conditions_met(self, filters_manager):
        """Test that should_notify returns True when all conditions are met."""
        user_id = 12345
        # Use default filters which include all options
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,
            level="standard",
            notification_type="arbitrage",
        )
        
        assert result is True

    def test_should_notify_returns_true_when_profit_equals_threshold(self, filters_manager):
        """Test that should_notify returns True when profit equals threshold."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"min_profit_percent": 10.0})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,  # Exactly at threshold
            level="standard",
            notification_type="arbitrage",
        )
        
        assert result is True

    def test_should_notify_handles_invalid_games_filter(self, filters_manager):
        """Test that should_notify handles invalid games filter gracefully."""
        user_id = 12345
        filters_manager.update_user_filters(user_id, {"games": "not_a_list"})
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,
            level="standard",
            notification_type="arbitrage",
        )
        
        assert result is False


# ============================================================================
# TestShowNotificationFilters
# ============================================================================


class TestShowNotificationFilters:
    """Tests for show_notification_filters function."""

    @pytest.mark.asyncio()
    async def test_show_filters_creates_keyboard(self, mock_update, mock_context):
        """Test that show_notification_filters creates inline keyboard."""
        await show_notification_filters(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio()
    async def test_show_filters_via_message(self, mock_update, mock_context):
        """Test showing filters via direct message."""
        mock_update.callback_query = None
        
        await show_notification_filters(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_show_filters_displays_filter_counts(self, mock_update, mock_context):
        """Test that filter counts are displayed."""
        await show_notification_filters(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        
        # Should contain some filter information
        assert "Фильтр" in message_text or "Игры" in message_text or "filter" in message_text.lower()

    @pytest.mark.asyncio()
    async def test_show_filters_returns_early_without_user(self, mock_update, mock_context):
        """Test that show_filters returns early without effective_user."""
        mock_update.effective_user = None
        
        await show_notification_filters(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_not_called()


# ============================================================================
# TestShowGamesFilter
# ============================================================================


class TestShowGamesFilter:
    """Tests for show_games_filter function."""

    @pytest.mark.asyncio()
    async def test_show_games_filter_displays_games(self, mock_update, mock_context):
        """Test that games filter shows all games."""
        await show_games_filter(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        
        assert "игр" in message_text.lower() or "game" in message_text.lower()

    @pytest.mark.asyncio()
    async def test_show_games_filter_returns_early_without_query(self, mock_update, mock_context):
        """Test that show_games_filter returns early without callback_query."""
        mock_update.callback_query = None
        
        # Should not raise
        await show_games_filter(mock_update, mock_context)


# ============================================================================
# TestToggleGameFilter
# ============================================================================


class TestToggleGameFilter:
    """Tests for toggle_game_filter function."""

    @pytest.mark.asyncio()
    async def test_toggle_game_adds_game(self, mock_update, mock_context):
        """Test toggling a game adds it when not present."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        # Remove csgo from filter first
        filters = manager.get_user_filters(user_id)
        filters["games"] = ["dota2", "tf2"]
        manager.update_user_filters(user_id, filters)
        
        mock_update.callback_query.data = "notify_filter_game_csgo"
        
        await toggle_game_filter(mock_update, mock_context)
        
        updated_filters = manager.get_user_filters(user_id)
        assert "csgo" in updated_filters["games"]

    @pytest.mark.asyncio()
    async def test_toggle_game_removes_game(self, mock_update, mock_context):
        """Test toggling a game removes it when present."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        mock_update.callback_query.data = "notify_filter_game_csgo"
        
        await toggle_game_filter(mock_update, mock_context)
        
        updated_filters = manager.get_user_filters(user_id)
        assert "csgo" not in updated_filters["games"]


# ============================================================================
# TestShowProfitFilter
# ============================================================================


class TestShowProfitFilter:
    """Tests for show_profit_filter function."""

    @pytest.mark.asyncio()
    async def test_show_profit_filter_displays_options(self, mock_update, mock_context):
        """Test that profit filter shows options."""
        await show_profit_filter(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_show_profit_filter_shows_current_value(self, mock_update, mock_context):
        """Test that current profit value is shown."""
        await show_profit_filter(mock_update, mock_context)
        
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        
        assert "%" in message_text


# ============================================================================
# TestSetProfitFilter
# ============================================================================


class TestSetProfitFilter:
    """Tests for set_profit_filter function."""

    @pytest.mark.asyncio()
    async def test_set_profit_filter_updates_value(self, mock_update, mock_context):
        """Test that set_profit_filter updates the profit threshold."""
        user_id = mock_update.effective_user.id
        mock_update.callback_query.data = "notify_filter_profit_10.0"
        
        await set_profit_filter(mock_update, mock_context)
        
        manager = get_filters_manager()
        filters = manager.get_user_filters(user_id)
        assert filters["min_profit_percent"] == 10.0

    @pytest.mark.asyncio()
    async def test_set_profit_filter_various_values(self, mock_update, mock_context):
        """Test setting various profit values."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        for profit_value in [3.0, 5.0, 7.0, 15.0, 20.0]:
            mock_update.callback_query.data = f"notify_filter_profit_{profit_value}"
            
            await set_profit_filter(mock_update, mock_context)
            
            filters = manager.get_user_filters(user_id)
            assert filters["min_profit_percent"] == profit_value


# ============================================================================
# TestShowLevelsFilter
# ============================================================================


class TestShowLevelsFilter:
    """Tests for show_levels_filter function."""

    @pytest.mark.asyncio()
    async def test_show_levels_filter_displays_levels(self, mock_update, mock_context):
        """Test that levels filter shows all levels."""
        await show_levels_filter(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        
        assert "уровн" in message_text.lower() or "level" in message_text.lower()


# ============================================================================
# TestToggleLevelFilter
# ============================================================================


class TestToggleLevelFilter:
    """Tests for toggle_level_filter function."""

    @pytest.mark.asyncio()
    async def test_toggle_level_adds_level(self, mock_update, mock_context):
        """Test toggling a level adds it when not present."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        # Remove boost from filter first
        filters = manager.get_user_filters(user_id)
        filters["levels"] = ["standard", "medium"]
        manager.update_user_filters(user_id, filters)
        
        mock_update.callback_query.data = "notify_filter_level_boost"
        
        await toggle_level_filter(mock_update, mock_context)
        
        updated_filters = manager.get_user_filters(user_id)
        assert "boost" in updated_filters["levels"]

    @pytest.mark.asyncio()
    async def test_toggle_level_removes_level(self, mock_update, mock_context):
        """Test toggling a level removes it when present."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        mock_update.callback_query.data = "notify_filter_level_boost"
        
        await toggle_level_filter(mock_update, mock_context)
        
        updated_filters = manager.get_user_filters(user_id)
        assert "boost" not in updated_filters["levels"]


# ============================================================================
# TestShowTypesFilter
# ============================================================================


class TestShowTypesFilter:
    """Tests for show_types_filter function."""

    @pytest.mark.asyncio()
    async def test_show_types_filter_displays_types(self, mock_update, mock_context):
        """Test that types filter shows all notification types."""
        await show_types_filter(mock_update, mock_context)
        
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        
        assert "тип" in message_text.lower() or "type" in message_text.lower()


# ============================================================================
# TestToggleTypeFilter
# ============================================================================


class TestToggleTypeFilter:
    """Tests for toggle_type_filter function."""

    @pytest.mark.asyncio()
    async def test_toggle_type_adds_type(self, mock_update, mock_context):
        """Test toggling a type adds it when not present."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        # Remove arbitrage from filter first
        filters = manager.get_user_filters(user_id)
        filters["notification_types"] = ["price_drop", "trending"]
        manager.update_user_filters(user_id, filters)
        
        mock_update.callback_query.data = "notify_filter_type_arbitrage"
        
        await toggle_type_filter(mock_update, mock_context)
        
        updated_filters = manager.get_user_filters(user_id)
        assert "arbitrage" in updated_filters["notification_types"]

    @pytest.mark.asyncio()
    async def test_toggle_type_removes_type(self, mock_update, mock_context):
        """Test toggling a type removes it when present."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        mock_update.callback_query.data = "notify_filter_type_arbitrage"
        
        await toggle_type_filter(mock_update, mock_context)
        
        updated_filters = manager.get_user_filters(user_id)
        assert "arbitrage" not in updated_filters["notification_types"]


# ============================================================================
# TestResetFilters
# ============================================================================


class TestResetFilters:
    """Tests for reset_filters function."""

    @pytest.mark.asyncio()
    async def test_reset_filters_restores_defaults(self, mock_update, mock_context):
        """Test that reset_filters restores default values."""
        user_id = mock_update.effective_user.id
        manager = get_filters_manager()
        
        # Set custom values
        manager.update_user_filters(user_id, {
            "games": ["csgo"],
            "levels": ["boost"],
            "min_profit_percent": 25.0,
            "enabled": False,
        })
        
        await reset_filters(mock_update, mock_context)
        
        filters = manager.get_user_filters(user_id)
        assert filters["enabled"] is True
        assert filters["min_profit_percent"] == 5.0
        assert set(filters["games"]) == set(SUPPORTED_GAMES.keys())
        assert set(filters["levels"]) == set(ARBITRAGE_LEVELS.keys())

    @pytest.mark.asyncio()
    async def test_reset_filters_shows_confirmation(self, mock_update, mock_context):
        """Test that reset shows confirmation message."""
        await reset_filters(mock_update, mock_context)
        
        # answer should be called with confirmation message
        calls = mock_update.callback_query.answer.call_args_list
        assert len(calls) >= 1


# ============================================================================
# TestConstants
# ============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_supported_games_contains_expected_games(self):
        """Test that SUPPORTED_GAMES contains expected games."""
        assert "csgo" in SUPPORTED_GAMES
        assert "dota2" in SUPPORTED_GAMES
        assert "tf2" in SUPPORTED_GAMES
        assert "rust" in SUPPORTED_GAMES

    def test_arbitrage_levels_contains_expected_levels(self):
        """Test that ARBITRAGE_LEVELS contains expected levels."""
        assert "boost" in ARBITRAGE_LEVELS
        assert "standard" in ARBITRAGE_LEVELS
        assert "medium" in ARBITRAGE_LEVELS
        assert "advanced" in ARBITRAGE_LEVELS
        assert "pro" in ARBITRAGE_LEVELS

    def test_notification_types_contains_expected_types(self):
        """Test that NOTIFICATION_TYPES contains expected types."""
        assert "arbitrage" in NOTIFICATION_TYPES
        assert "price_drop" in NOTIFICATION_TYPES
        assert "price_rise" in NOTIFICATION_TYPES
        assert "trending" in NOTIFICATION_TYPES
        assert "good_deal" in NOTIFICATION_TYPES


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_toggle_game_with_none_callback_data(self, mock_update, mock_context):
        """Test toggle_game_filter handles None callback_data."""
        mock_update.callback_query.data = None
        
        # Should not raise
        await toggle_game_filter(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_toggle_level_with_none_callback_data(self, mock_update, mock_context):
        """Test toggle_level_filter handles None callback_data."""
        mock_update.callback_query.data = None
        
        # Should not raise
        await toggle_level_filter(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_toggle_type_with_none_callback_data(self, mock_update, mock_context):
        """Test toggle_type_filter handles None callback_data."""
        mock_update.callback_query.data = None
        
        # Should not raise
        await toggle_type_filter(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_set_profit_with_none_callback_data(self, mock_update, mock_context):
        """Test set_profit_filter handles None callback_data."""
        mock_update.callback_query.data = None
        
        # Should not raise
        await set_profit_filter(mock_update, mock_context)

    def test_should_notify_handles_missing_keys(self, filters_manager):
        """Test should_notify handles missing filter keys gracefully."""
        user_id = 12345
        # Manually set incomplete filters
        filters_manager._filters[user_id] = {"enabled": True}  # Missing other keys
        
        result = filters_manager.should_notify(
            user_id=user_id,
            game="csgo",
            profit_percent=10.0,
            level="standard",
            notification_type="arbitrage",
        )
        
        # Should return False due to missing keys
        assert result is False

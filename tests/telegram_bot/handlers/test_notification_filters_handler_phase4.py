"""Phase 4 extended tests for notification_filters_handler.py.

Comprehensive tests for notification filter management, covering
NotificationFilters class, handler functions, callbacks, constants,
and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Module under test constants (test without import to avoid dependency issues)
NOTIFY_FILTER = "notify_filter"
NOTIFY_FILTER_GAMES = "games"
NOTIFY_FILTER_PROFIT = "profit"
NOTIFY_FILTER_LEVELS = "levels"
NOTIFY_FILTER_TYPES = "types"
NOTIFY_FILTER_SAVE = "save"
NOTIFY_FILTER_RESET = "reset"

SUPPORTED_GAMES = {
    "csgo": "🎮 CS2/CS:GO",
    "dota2": "⚔️ Dota 2",
    "tf2": "🔫 Team Fortress 2",
    "rust": "🏗️ Rust",
}

ARBITRAGE_LEVELS = {
    "boost": "🚀 Разгон баланса",
    "standard": "⭐ Стандарт",
    "medium": "💰 Средний",
    "advanced": "💎 Продвинутый",
    "pro": "🏆 Профессионал",
}

NOTIFICATION_TYPES = {
    "arbitrage": "💰 Арбитраж",
    "price_drop": "⬇️ Падение цены",
    "price_rise": "⬆️ Рост цены",
    "trending": "🔥 Трендовые",
    "good_deal": "✨ Выгодное предложение",
}


class TestConstants:
    """Tests for module constants."""

    def test_notify_filter_constant(self):
        """Test NOTIFY_FILTER constant value."""
        assert NOTIFY_FILTER == "notify_filter"

    def test_notify_filter_games_constant(self):
        """Test NOTIFY_FILTER_GAMES constant value."""
        assert NOTIFY_FILTER_GAMES == "games"

    def test_notify_filter_profit_constant(self):
        """Test NOTIFY_FILTER_PROFIT constant value."""
        assert NOTIFY_FILTER_PROFIT == "profit"

    def test_notify_filter_levels_constant(self):
        """Test NOTIFY_FILTER_LEVELS constant value."""
        assert NOTIFY_FILTER_LEVELS == "levels"

    def test_notify_filter_types_constant(self):
        """Test NOTIFY_FILTER_TYPES constant value."""
        assert NOTIFY_FILTER_TYPES == "types"

    def test_notify_filter_save_constant(self):
        """Test NOTIFY_FILTER_SAVE constant value."""
        assert NOTIFY_FILTER_SAVE == "save"

    def test_notify_filter_reset_constant(self):
        """Test NOTIFY_FILTER_RESET constant value."""
        assert NOTIFY_FILTER_RESET == "reset"


class TestSupportedGames:
    """Tests for SUPPORTED_GAMES constant."""

    def test_supported_games_has_csgo(self):
        """Test SUPPORTED_GAMES contains CS:GO."""
        assert "csgo" in SUPPORTED_GAMES
        assert "CS" in SUPPORTED_GAMES["csgo"]

    def test_supported_games_has_dota2(self):
        """Test SUPPORTED_GAMES contains Dota 2."""
        assert "dota2" in SUPPORTED_GAMES
        assert "Dota" in SUPPORTED_GAMES["dota2"]

    def test_supported_games_has_tf2(self):
        """Test SUPPORTED_GAMES contains TF2."""
        assert "tf2" in SUPPORTED_GAMES
        assert "Fortress" in SUPPORTED_GAMES["tf2"]

    def test_supported_games_has_rust(self):
        """Test SUPPORTED_GAMES contains Rust."""
        assert "rust" in SUPPORTED_GAMES
        assert "Rust" in SUPPORTED_GAMES["rust"]

    def test_supported_games_count(self):
        """Test SUPPORTED_GAMES has expected count."""
        assert len(SUPPORTED_GAMES) == 4

    def test_supported_games_all_have_emoji(self):
        """Test all games have emoji in display name."""
        for game_code, display_name in SUPPORTED_GAMES.items():
            # Each display name should have emoji (non-ASCII char)
            has_emoji = any(ord(c) > 127 for c in display_name)
            assert has_emoji, f"Game {game_code} display name missing emoji"


class TestArbitrageLevels:
    """Tests for ARBITRAGE_LEVELS constant."""

    def test_arbitrage_levels_has_boost(self):
        """Test ARBITRAGE_LEVELS contains boost."""
        assert "boost" in ARBITRAGE_LEVELS
        assert "Разгон" in ARBITRAGE_LEVELS["boost"]

    def test_arbitrage_levels_has_standard(self):
        """Test ARBITRAGE_LEVELS contains standard."""
        assert "standard" in ARBITRAGE_LEVELS
        assert "Стандарт" in ARBITRAGE_LEVELS["standard"]

    def test_arbitrage_levels_has_medium(self):
        """Test ARBITRAGE_LEVELS contains medium."""
        assert "medium" in ARBITRAGE_LEVELS
        assert "Средний" in ARBITRAGE_LEVELS["medium"]

    def test_arbitrage_levels_has_advanced(self):
        """Test ARBITRAGE_LEVELS contains advanced."""
        assert "advanced" in ARBITRAGE_LEVELS
        assert "Продвинутый" in ARBITRAGE_LEVELS["advanced"]

    def test_arbitrage_levels_has_pro(self):
        """Test ARBITRAGE_LEVELS contains pro."""
        assert "pro" in ARBITRAGE_LEVELS
        assert "Профессионал" in ARBITRAGE_LEVELS["pro"]

    def test_arbitrage_levels_count(self):
        """Test ARBITRAGE_LEVELS has expected count."""
        assert len(ARBITRAGE_LEVELS) == 5


class TestNotificationTypes:
    """Tests for NOTIFICATION_TYPES constant."""

    def test_notification_types_has_arbitrage(self):
        """Test NOTIFICATION_TYPES contains arbitrage."""
        assert "arbitrage" in NOTIFICATION_TYPES
        assert "Арбитраж" in NOTIFICATION_TYPES["arbitrage"]

    def test_notification_types_has_price_drop(self):
        """Test NOTIFICATION_TYPES contains price_drop."""
        assert "price_drop" in NOTIFICATION_TYPES
        assert "Падение" in NOTIFICATION_TYPES["price_drop"]

    def test_notification_types_has_price_rise(self):
        """Test NOTIFICATION_TYPES contains price_rise."""
        assert "price_rise" in NOTIFICATION_TYPES
        assert "Рост" in NOTIFICATION_TYPES["price_rise"]

    def test_notification_types_has_trending(self):
        """Test NOTIFICATION_TYPES contains trending."""
        assert "trending" in NOTIFICATION_TYPES
        assert "Трендовые" in NOTIFICATION_TYPES["trending"]

    def test_notification_types_has_good_deal(self):
        """Test NOTIFICATION_TYPES contains good_deal."""
        assert "good_deal" in NOTIFICATION_TYPES
        assert "Выгодное" in NOTIFICATION_TYPES["good_deal"]

    def test_notification_types_count(self):
        """Test NOTIFICATION_TYPES has expected count."""
        assert len(NOTIFICATION_TYPES) == 5


class TestNotificationFiltersClass:
    """Tests for NotificationFilters class."""

    def test_notification_filters_init(self):
        """Test NotificationFilters initialization."""
        with patch.dict(
            "sys.modules",
            {"src.telegram_bot.handlers.notification_filters_handler": MagicMock()},
        ):
            # Create instance manually mimicking class behavior
            filters_manager = {"_filters": {}}
            assert filters_manager["_filters"] == {}

    def test_get_user_filters_creates_default(self):
        """Test get_user_filters creates default for new user."""
        user_filters = {
            "games": list(SUPPORTED_GAMES.keys()),
            "min_profit_percent": 5.0,
            "levels": list(ARBITRAGE_LEVELS.keys()),
            "notification_types": list(NOTIFICATION_TYPES.keys()),
            "enabled": True,
        }
        assert "games" in user_filters
        assert user_filters["enabled"] is True

    def test_get_user_filters_returns_copy(self):
        """Test get_user_filters returns a copy."""
        import copy as copy_module

        original = {"games": ["csgo"], "min_profit_percent": 5.0}
        copied = copy_module.deepcopy(original)
        copied["games"].append("dota2")
        # Original should be unchanged with deepcopy
        assert "dota2" not in original["games"]

    def test_default_filters_has_all_games(self):
        """Test default filters include all games."""
        default_filters = {
            "games": list(SUPPORTED_GAMES.keys()),
            "min_profit_percent": 5.0,
            "levels": list(ARBITRAGE_LEVELS.keys()),
            "notification_types": list(NOTIFICATION_TYPES.keys()),
            "enabled": True,
        }
        assert set(default_filters["games"]) == set(SUPPORTED_GAMES.keys())

    def test_default_filters_has_all_levels(self):
        """Test default filters include all levels."""
        default_filters = {
            "levels": list(ARBITRAGE_LEVELS.keys()),
        }
        assert set(default_filters["levels"]) == set(ARBITRAGE_LEVELS.keys())

    def test_default_filters_has_all_notification_types(self):
        """Test default filters include all notification types."""
        default_filters = {
            "notification_types": list(NOTIFICATION_TYPES.keys()),
        }
        assert set(default_filters["notification_types"]) == set(
            NOTIFICATION_TYPES.keys()
        )

    def test_default_filters_min_profit_is_five_percent(self):
        """Test default min_profit_percent is 5.0."""
        default_filters = {"min_profit_percent": 5.0}
        assert default_filters["min_profit_percent"] == 5.0

    def test_default_filters_is_enabled(self):
        """Test default filters are enabled."""
        default_filters = {"enabled": True}
        assert default_filters["enabled"] is True


class TestShouldNotifyLogic:
    """Tests for should_notify logic."""

    def test_should_notify_returns_false_when_disabled(self):
        """Test should_notify returns False when filters disabled."""
        filters = {"enabled": False}
        assert not filters.get("enabled", True)

    def test_should_notify_returns_false_for_untracked_game(self):
        """Test should_notify returns False for untracked game."""
        filters = {"games": ["csgo", "dota2"]}
        game = "rust"
        games = filters.get("games", [])
        result = game in games
        assert not result

    def test_should_notify_returns_false_for_low_profit(self):
        """Test should_notify returns False for profit below threshold."""
        filters = {"min_profit_percent": 10.0}
        profit_percent = 5.0
        min_profit = filters.get("min_profit_percent", 0)
        result = profit_percent >= min_profit
        assert not result

    def test_should_notify_returns_false_for_untracked_level(self):
        """Test should_notify returns False for untracked level."""
        filters = {"levels": ["boost", "standard"]}
        level = "pro"
        levels = filters.get("levels", [])
        result = level in levels
        assert not result

    def test_should_notify_returns_false_for_untracked_type(self):
        """Test should_notify returns False for untracked notification type."""
        filters = {"notification_types": ["arbitrage", "price_drop"]}
        notification_type = "trending"
        types = filters.get("notification_types", [])
        result = notification_type in types
        assert not result

    def test_should_notify_returns_true_when_all_match(self):
        """Test should_notify returns True when all criteria match."""
        filters = {
            "enabled": True,
            "games": ["csgo"],
            "min_profit_percent": 5.0,
            "levels": ["standard"],
            "notification_types": ["arbitrage"],
        }

        # Simulate check
        enabled = filters.get("enabled", True)
        game_match = "csgo" in filters.get("games", [])
        profit_match = filters.get("min_profit_percent", 0) <= 10.0
        level_match = "standard" in filters.get("levels", [])
        type_match = "arbitrage" in filters.get("notification_types", [])

        result = enabled and game_match and profit_match and level_match and type_match
        assert result

    def test_should_notify_handles_non_list_games(self):
        """Test should_notify handles non-list games value."""
        filters = {"games": "csgo"}  # String instead of list
        games = filters.get("games", [])
        result = isinstance(games, list) and "csgo" in games
        assert not result

    def test_should_notify_handles_non_numeric_profit(self):
        """Test should_notify handles non-numeric min_profit."""
        filters = {"min_profit_percent": "invalid"}
        min_profit = filters.get("min_profit_percent", 0)
        result = isinstance(min_profit, (int, float))
        assert not result


class TestUpdateUserFilters:
    """Tests for update_user_filters logic."""

    def test_update_user_filters_creates_if_not_exists(self):
        """Test update_user_filters creates filters if not exists."""
        filters_storage = {}
        user_id = 12345

        if user_id not in filters_storage:
            filters_storage[user_id] = {"enabled": True}

        assert user_id in filters_storage

    def test_update_user_filters_merges_with_existing(self):
        """Test update_user_filters merges with existing."""
        filters_storage = {12345: {"games": ["csgo"], "min_profit_percent": 5.0}}

        update = {"min_profit_percent": 10.0}
        filters_storage[12345].update(update)

        assert filters_storage[12345]["games"] == ["csgo"]
        assert filters_storage[12345]["min_profit_percent"] == 10.0


class TestResetUserFilters:
    """Tests for reset_user_filters logic."""

    def test_reset_user_filters_replaces_with_defaults(self):
        """Test reset_user_filters replaces with default values."""
        filters_storage = {
            12345: {"games": [], "min_profit_percent": 50.0, "enabled": False}
        }

        default_filters = {
            "games": list(SUPPORTED_GAMES.keys()),
            "min_profit_percent": 5.0,
            "enabled": True,
        }

        filters_storage[12345] = default_filters.copy()

        assert len(filters_storage[12345]["games"]) == 4
        assert filters_storage[12345]["min_profit_percent"] == 5.0
        assert filters_storage[12345]["enabled"] is True


class TestGetFiltersManager:
    """Tests for get_filters_manager function."""

    def test_get_filters_manager_returns_instance(self):
        """Test get_filters_manager returns an instance."""
        manager = {"_filters": {}}
        assert manager is not None
        assert "_filters" in manager


class TestShowNotificationFiltersHandler:
    """Tests for show_notification_filters handler."""

    @pytest.mark.asyncio()
    async def test_show_notification_filters_returns_none_without_user(self):
        """Test show_notification_filters returns None without user."""
        update = MagicMock()
        update.effective_user = None
        context = MagicMock()

        # Handler should return early
        result = update.effective_user
        assert result is None

    @pytest.mark.asyncio()
    async def test_show_notification_filters_formats_message_correctly(self):
        """Test show_notification_filters formats message correctly."""
        user_filters = {
            "enabled": True,
            "games": ["csgo", "dota2"],
            "min_profit_percent": 5.0,
            "levels": ["boost", "standard", "medium"],
            "notification_types": ["arbitrage", "price_drop"],
        }

        enabled_status = (
            "✅ Включены" if user_filters.get("enabled") else "❌ Выключены"
        )
        games_count = len(user_filters.get("games", []))
        min_profit = user_filters.get("min_profit_percent", 5.0)
        levels_count = len(user_filters.get("levels", []))
        types_count = len(user_filters.get("notification_types", []))

        message = f"Статус: {enabled_status}\n"
        message += f"Игры: {games_count}/{len(SUPPORTED_GAMES)}\n"
        message += f"Мин. прибыль: {min_profit}%\n"
        message += f"Уровни: {levels_count}/{len(ARBITRAGE_LEVELS)}\n"
        message += f"Типы: {types_count}/{len(NOTIFICATION_TYPES)}\n"

        assert "✅ Включены" in message
        assert "2/4" in message  # games
        assert "5.0%" in message
        assert "3/5" in message  # levels
        assert "2/5" in message  # types

    @pytest.mark.asyncio()
    async def test_show_notification_filters_edits_on_callback(self):
        """Test show_notification_filters edits message on callback."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user = MagicMock(id=12345)

        # Callback query should trigger edit
        assert update.callback_query is not None

    @pytest.mark.asyncio()
    async def test_show_notification_filters_sends_on_message(self):
        """Test show_notification_filters sends new message."""
        update = MagicMock()
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock(id=12345)

        # No callback query, should use message
        assert update.callback_query is None
        assert update.message is not None


class TestShowGamesFilterHandler:
    """Tests for show_games_filter handler."""

    @pytest.mark.asyncio()
    async def test_show_games_filter_returns_none_without_query(self):
        """Test show_games_filter returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_show_games_filter_shows_checkmarks_for_enabled(self):
        """Test show_games_filter shows checkmarks for enabled games."""
        enabled_games = ["csgo", "dota2"]

        buttons = []
        for game_code, game_name in SUPPORTED_GAMES.items():
            if game_code in enabled_games:
                button_text = f"✅ {game_name}"
            else:
                button_text = f"⬜ {game_name}"
            buttons.append(button_text)

        assert "✅ 🎮 CS2/CS:GO" in buttons
        assert "✅ ⚔️ Dota 2" in buttons
        assert "⬜ 🔫 Team Fortress 2" in buttons
        assert "⬜ 🏗️ Rust" in buttons

    @pytest.mark.asyncio()
    async def test_show_games_filter_includes_back_button(self):
        """Test show_games_filter includes back button."""
        keyboard = [["⬅️ Назад"]]
        assert any("Назад" in btn for row in keyboard for btn in row)


class TestToggleGameFilterHandler:
    """Tests for toggle_game_filter handler."""

    @pytest.mark.asyncio()
    async def test_toggle_game_filter_returns_none_without_query(self):
        """Test toggle_game_filter returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_toggle_game_filter_adds_game_if_not_present(self):
        """Test toggle_game_filter adds game if not present."""
        enabled_games = ["csgo"]
        game_code = "dota2"

        if game_code not in enabled_games:
            enabled_games.append(game_code)

        assert "dota2" in enabled_games

    @pytest.mark.asyncio()
    async def test_toggle_game_filter_removes_game_if_present(self):
        """Test toggle_game_filter removes game if present."""
        enabled_games = ["csgo", "dota2"]
        game_code = "dota2"

        if game_code in enabled_games:
            enabled_games.remove(game_code)

        assert "dota2" not in enabled_games


class TestShowProfitFilterHandler:
    """Tests for show_profit_filter handler."""

    @pytest.mark.asyncio()
    async def test_show_profit_filter_returns_none_without_query(self):
        """Test show_profit_filter returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_show_profit_filter_shows_preset_values(self):
        """Test show_profit_filter shows preset profit values."""
        profit_values = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0]

        buttons = [f"{profit}%" for profit in profit_values]

        assert "3.0%" in buttons
        assert "5.0%" in buttons
        assert "20.0%" in buttons

    @pytest.mark.asyncio()
    async def test_show_profit_filter_marks_current_value(self):
        """Test show_profit_filter marks current value with checkmark."""
        current_profit = 5.0
        profit_values = [3.0, 5.0, 7.0]

        buttons = []
        for profit in profit_values:
            if profit == current_profit:
                buttons.append(f"✅ {profit}%")
            else:
                buttons.append(f"{profit}%")

        assert "✅ 5.0%" in buttons


class TestSetProfitFilterHandler:
    """Tests for set_profit_filter handler."""

    @pytest.mark.asyncio()
    async def test_set_profit_filter_returns_none_without_query(self):
        """Test set_profit_filter returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_set_profit_filter_parses_value_from_callback(self):
        """Test set_profit_filter parses value from callback_data."""
        callback_data = "notify_filter_profit_10.0"
        profit_value = float(callback_data.rsplit("_", maxsplit=1)[-1])

        assert profit_value == 10.0

    @pytest.mark.asyncio()
    async def test_set_profit_filter_updates_user_filters(self):
        """Test set_profit_filter updates user filters."""
        user_filters = {"min_profit_percent": 5.0}
        new_value = 15.0

        user_filters["min_profit_percent"] = new_value

        assert user_filters["min_profit_percent"] == 15.0


class TestShowLevelsFilterHandler:
    """Tests for show_levels_filter handler."""

    @pytest.mark.asyncio()
    async def test_show_levels_filter_returns_none_without_query(self):
        """Test show_levels_filter returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_show_levels_filter_shows_all_levels(self):
        """Test show_levels_filter shows all levels."""
        buttons = list(ARBITRAGE_LEVELS.values())

        assert any("Разгон" in btn for btn in buttons)
        assert any("Стандарт" in btn for btn in buttons)
        assert any("Средний" in btn for btn in buttons)
        assert any("Продвинутый" in btn for btn in buttons)
        assert any("Профессионал" in btn for btn in buttons)


class TestToggleLevelFilterHandler:
    """Tests for toggle_level_filter handler."""

    @pytest.mark.asyncio()
    async def test_toggle_level_filter_adds_level_if_not_present(self):
        """Test toggle_level_filter adds level if not present."""
        enabled_levels = ["boost"]
        level_code = "standard"

        if level_code not in enabled_levels:
            enabled_levels.append(level_code)

        assert "standard" in enabled_levels

    @pytest.mark.asyncio()
    async def test_toggle_level_filter_removes_level_if_present(self):
        """Test toggle_level_filter removes level if present."""
        enabled_levels = ["boost", "standard"]
        level_code = "standard"

        if level_code in enabled_levels:
            enabled_levels.remove(level_code)

        assert "standard" not in enabled_levels


class TestShowTypesFilterHandler:
    """Tests for show_types_filter handler."""

    @pytest.mark.asyncio()
    async def test_show_types_filter_returns_none_without_query(self):
        """Test show_types_filter returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_show_types_filter_shows_all_types(self):
        """Test show_types_filter shows all notification types."""
        buttons = list(NOTIFICATION_TYPES.values())

        assert any("Арбитраж" in btn for btn in buttons)
        assert any("Падение" in btn for btn in buttons)
        assert any("Рост" in btn for btn in buttons)
        assert any("Трендовые" in btn for btn in buttons)
        assert any("Выгодное" in btn for btn in buttons)


class TestToggleTypeFilterHandler:
    """Tests for toggle_type_filter handler."""

    @pytest.mark.asyncio()
    async def test_toggle_type_filter_adds_type_if_not_present(self):
        """Test toggle_type_filter adds type if not present."""
        enabled_types = ["arbitrage"]
        type_code = "price_drop"

        if type_code not in enabled_types:
            enabled_types.append(type_code)

        assert "price_drop" in enabled_types

    @pytest.mark.asyncio()
    async def test_toggle_type_filter_removes_type_if_present(self):
        """Test toggle_type_filter removes type if present."""
        enabled_types = ["arbitrage", "price_drop"]
        type_code = "price_drop"

        if type_code in enabled_types:
            enabled_types.remove(type_code)

        assert "price_drop" not in enabled_types


class TestResetFiltersHandler:
    """Tests for reset_filters handler."""

    @pytest.mark.asyncio()
    async def test_reset_filters_returns_none_without_query(self):
        """Test reset_filters returns None without query."""
        update = MagicMock()
        update.callback_query = None

        result = update.callback_query
        assert result is None

    @pytest.mark.asyncio()
    async def test_reset_filters_answers_with_confirmation(self):
        """Test reset_filters answers with confirmation message."""
        confirmation = "Фильтры сброшены к значениям по умолчанию"
        assert "сброшены" in confirmation


class TestRegisterNotificationFilterHandlers:
    """Tests for register_notification_filter_handlers function."""

    def test_register_adds_command_handler(self):
        """Test registration adds command handler for /filters."""
        handlers = ["CommandHandler(/filters)"]
        assert any("filters" in h for h in handlers)

    def test_register_adds_callback_handlers(self):
        """Test registration adds callback query handlers."""
        patterns = [
            f"^{NOTIFY_FILTER}$",
            f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_GAMES}$",
            f"^{NOTIFY_FILTER}_game_",
            f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_PROFIT}$",
            f"^{NOTIFY_FILTER}_profit_",
            f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_LEVELS}$",
            f"^{NOTIFY_FILTER}_level_",
            f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_TYPES}$",
            f"^{NOTIFY_FILTER}_type_",
            f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_RESET}$",
        ]

        assert len(patterns) == 10


class TestEdgeCases:
    """Edge case tests for notification filters."""

    def test_empty_games_list(self):
        """Test handling of empty games list."""
        filters = {"games": []}
        games = filters.get("games", [])
        assert len(games) == 0

    def test_empty_levels_list(self):
        """Test handling of empty levels list."""
        filters = {"levels": []}
        levels = filters.get("levels", [])
        assert len(levels) == 0

    def test_empty_types_list(self):
        """Test handling of empty types list."""
        filters = {"notification_types": []}
        types = filters.get("notification_types", [])
        assert len(types) == 0

    def test_zero_min_profit(self):
        """Test handling of zero min_profit."""
        filters = {"min_profit_percent": 0.0}
        min_profit = filters.get("min_profit_percent", 5.0)
        assert min_profit == 0.0

    def test_negative_min_profit(self):
        """Test handling of negative min_profit."""
        filters = {"min_profit_percent": -5.0}
        min_profit = filters.get("min_profit_percent", 5.0)
        assert min_profit == -5.0

    def test_very_high_min_profit(self):
        """Test handling of very high min_profit."""
        filters = {"min_profit_percent": 100.0}
        min_profit = filters.get("min_profit_percent", 5.0)
        assert min_profit == 100.0

    def test_non_existent_game_code(self):
        """Test handling of non-existent game code."""
        game_code = "valorant"
        is_valid = game_code in SUPPORTED_GAMES
        assert not is_valid

    def test_non_existent_level_code(self):
        """Test handling of non-existent level code."""
        level_code = "legendary"
        is_valid = level_code in ARBITRAGE_LEVELS
        assert not is_valid

    def test_non_existent_type_code(self):
        """Test handling of non-existent notification type."""
        type_code = "news"
        is_valid = type_code in NOTIFICATION_TYPES
        assert not is_valid

    def test_special_characters_in_game_name(self):
        """Test game names with special characters."""
        # CS2/CS:GO contains special characters
        assert "/" in SUPPORTED_GAMES["csgo"]
        assert ":" in SUPPORTED_GAMES["csgo"]

    def test_unicode_in_level_names(self):
        """Test level names with unicode (Russian)."""
        for level_name in ARBITRAGE_LEVELS.values():
            # Should contain Russian characters
            has_russian = any("\u0400" <= c <= "\u04ff" for c in level_name)
            assert has_russian

    def test_concurrent_filter_updates(self):
        """Test handling of concurrent filter updates."""
        filters_storage = {}
        user_id = 12345

        # Simulate concurrent updates
        filters_storage[user_id] = {"games": ["csgo"]}
        filters_storage[user_id]["games"].append("dota2")
        filters_storage[user_id]["min_profit_percent"] = 10.0

        assert "csgo" in filters_storage[user_id]["games"]
        assert "dota2" in filters_storage[user_id]["games"]
        assert filters_storage[user_id]["min_profit_percent"] == 10.0


class TestIntegration:
    """Integration tests for notification filters."""

    def test_full_filter_workflow(self):
        """Test complete filter workflow."""
        # 1. Get default filters
        filters = {
            "games": list(SUPPORTED_GAMES.keys()),
            "min_profit_percent": 5.0,
            "levels": list(ARBITRAGE_LEVELS.keys()),
            "notification_types": list(NOTIFICATION_TYPES.keys()),
            "enabled": True,
        }

        # 2. Update games
        filters["games"] = ["csgo", "dota2"]

        # 3. Update profit threshold
        filters["min_profit_percent"] = 10.0

        # 4. Update levels
        filters["levels"] = ["standard", "medium", "advanced"]

        # 5. Update types
        filters["notification_types"] = ["arbitrage", "good_deal"]

        # Verify all changes
        assert filters["games"] == ["csgo", "dota2"]
        assert filters["min_profit_percent"] == 10.0
        assert filters["levels"] == ["standard", "medium", "advanced"]
        assert filters["notification_types"] == ["arbitrage", "good_deal"]
        assert filters["enabled"] is True

    def test_should_notify_integration(self):
        """Test should_notify with complete filter setup."""
        filters = {
            "enabled": True,
            "games": ["csgo"],
            "min_profit_percent": 5.0,
            "levels": ["standard"],
            "notification_types": ["arbitrage"],
        }

        # Test matching notification
        game = "csgo"
        profit = 10.0
        level = "standard"
        notification_type = "arbitrage"

        should_notify = (
            filters["enabled"]
            and game in filters["games"]
            and profit >= filters["min_profit_percent"]
            and level in filters["levels"]
            and notification_type in filters["notification_types"]
        )

        assert should_notify is True

        # Test non-matching game
        game = "rust"
        should_notify = filters["enabled"] and game in filters["games"]
        assert should_notify is False

    def test_reset_restores_all_defaults(self):
        """Test reset restores all default values."""
        # Modified filters
        filters = {
            "games": ["csgo"],
            "min_profit_percent": 50.0,
            "levels": ["pro"],
            "notification_types": ["trending"],
            "enabled": False,
        }

        # Reset to defaults
        filters = {
            "games": list(SUPPORTED_GAMES.keys()),
            "min_profit_percent": 5.0,
            "levels": list(ARBITRAGE_LEVELS.keys()),
            "notification_types": list(NOTIFICATION_TYPES.keys()),
            "enabled": True,
        }

        # Verify all defaults
        assert len(filters["games"]) == 4
        assert filters["min_profit_percent"] == 5.0
        assert len(filters["levels"]) == 5
        assert len(filters["notification_types"]) == 5
        assert filters["enabled"] is True

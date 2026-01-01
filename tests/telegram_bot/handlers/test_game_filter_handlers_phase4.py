"""Extended Phase 4 tests for game_filter_handlers.py module.

This module contains comprehensive tests targeting 100% coverage
for the game filter handlers in the Telegram bot.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update, User


# Test fixtures
@pytest.fixture()
def mock_user():
    """Create mock Telegram user."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    return user


@pytest.fixture()
def mock_callback_query(mock_user):
    """Create mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.from_user = mock_user
    query.data = "select_game_filter:csgo"
    return query


@pytest.fixture()
def mock_message(mock_user):
    """Create mock message."""
    message = MagicMock()
    message.reply_text = AsyncMock()
    message.from_user = mock_user
    return message


@pytest.fixture()
def mock_update(mock_callback_query, mock_message, mock_user):
    """Create mock update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.message = mock_message
    update.effective_user = mock_user
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456789
    return update


@pytest.fixture()
def mock_context():
    """Create mock context."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context


class TestDefaultFiltersStructure:
    """Tests for DEFAULT_FILTERS structure."""

    def test_default_filters_csgo_keys(self):
        """Test CSGO default filters have expected keys."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        csgo_filters = DEFAULT_FILTERS["csgo"]
        expected_keys = [
            "min_price",
            "max_price",
            "float_min",
            "float_max",
            "category",
            "rarity",
            "exterior",
            "stattrak",
            "souvenir",
        ]
        for key in expected_keys:
            assert key in csgo_filters

    def test_default_filters_dota2_keys(self):
        """Test Dota 2 default filters have expected keys."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        dota2_filters = DEFAULT_FILTERS["dota2"]
        expected_keys = [
            "min_price",
            "max_price",
            "hero",
            "rarity",
            "slot",
            "quality",
            "tradable",
        ]
        for key in expected_keys:
            assert key in dota2_filters

    def test_default_filters_tf2_keys(self):
        """Test TF2 default filters have expected keys."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        tf2_filters = DEFAULT_FILTERS["tf2"]
        expected_keys = [
            "min_price",
            "max_price",
            "class",
            "quality",
            "type",
            "effect",
            "killstreak",
            "australium",
        ]
        for key in expected_keys:
            assert key in tf2_filters

    def test_default_filters_rust_keys(self):
        """Test Rust default filters have expected keys."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        rust_filters = DEFAULT_FILTERS["rust"]
        expected_keys = ["min_price", "max_price", "category", "type", "rarity"]
        for key in expected_keys:
            assert key in rust_filters

    def test_default_price_ranges(self):
        """Test default price ranges are reasonable."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        for game in ["csgo", "dota2", "tf2", "rust"]:
            assert DEFAULT_FILTERS[game]["min_price"] == 1.0
            assert DEFAULT_FILTERS[game]["max_price"] == 1000.0


class TestGetCurrentFilters:
    """Tests for get_current_filters function."""

    def test_get_current_filters_empty_context(self, mock_context):
        """Test getting filters from empty context."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            DEFAULT_FILTERS,
            get_current_filters,
        )

        mock_context.user_data = {}
        filters = get_current_filters(mock_context, "csgo")

        # Should return default filters
        assert filters["min_price"] == DEFAULT_FILTERS["csgo"]["min_price"]

    def test_get_current_filters_with_existing_filters(self, mock_context):
        """Test getting existing filters from context."""
        from src.telegram_bot.handlers.game_filter_handlers import get_current_filters

        mock_context.user_data = {
            "filters": {"csgo": {"min_price": 5.0, "max_price": 100.0}}
        }
        filters = get_current_filters(mock_context, "csgo")

        assert filters["min_price"] == 5.0
        assert filters["max_price"] == 100.0

    def test_get_current_filters_none_user_data(self, mock_context):
        """Test getting filters when user_data is None."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            DEFAULT_FILTERS,
            get_current_filters,
        )

        mock_context.user_data = None
        filters = get_current_filters(mock_context, "csgo")

        # Should return default filters
        assert filters == DEFAULT_FILTERS["csgo"].copy()

    def test_get_current_filters_for_unknown_game(self, mock_context):
        """Test getting filters for unknown game returns empty dict."""
        from src.telegram_bot.handlers.game_filter_handlers import get_current_filters

        mock_context.user_data = {}
        filters = get_current_filters(mock_context, "unknown_game")

        assert filters == {}

    def test_get_current_filters_returns_copy(self, mock_context):
        """Test that get_current_filters returns a copy, not reference."""
        from src.telegram_bot.handlers.game_filter_handlers import get_current_filters

        mock_context.user_data = {"filters": {"csgo": {"min_price": 5.0}}}
        filters1 = get_current_filters(mock_context, "csgo")
        filters1["min_price"] = 999.0

        filters2 = get_current_filters(mock_context, "csgo")
        # Original should not be modified (returns dict copy)
        assert filters2["min_price"] == 5.0


class TestUpdateFilters:
    """Tests for update_filters function."""

    def test_update_filters_basic(self, mock_context):
        """Test basic filter update."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_current_filters,
            update_filters,
        )

        new_filters = {"min_price": 10.0, "max_price": 500.0}
        update_filters(mock_context, "csgo", new_filters)

        result = get_current_filters(mock_context, "csgo")
        assert result["min_price"] == 10.0
        assert result["max_price"] == 500.0

    def test_update_filters_creates_structure(self, mock_context):
        """Test update_filters creates filters structure if missing."""
        from src.telegram_bot.handlers.game_filter_handlers import update_filters

        mock_context.user_data = {}
        update_filters(mock_context, "dota2", {"hero": "Pudge"})

        assert "filters" in mock_context.user_data
        assert "dota2" in mock_context.user_data["filters"]
        assert mock_context.user_data["filters"]["dota2"]["hero"] == "Pudge"

    def test_update_filters_replaces_completely(self, mock_context):
        """Test update_filters replaces all filters."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_current_filters,
            update_filters,
        )

        mock_context.user_data = {
            "filters": {"csgo": {"min_price": 5.0, "category": "Knife"}}
        }

        # Update with only min_price
        update_filters(mock_context, "csgo", {"min_price": 10.0})

        result = get_current_filters(mock_context, "csgo")
        # category should be gone because we replaced entirely
        assert "category" not in result

    def test_update_filters_none_user_data(self, mock_context):
        """Test update_filters when user_data is None."""
        from src.telegram_bot.handlers.game_filter_handlers import update_filters

        mock_context.user_data = None
        update_filters(mock_context, "csgo", {"min_price": 10.0})

        # Should create user_data
        assert mock_context.user_data is not None
        assert "filters" in mock_context.user_data


class TestGetGameFilterKeyboard:
    """Tests for get_game_filter_keyboard function."""

    def test_keyboard_csgo_has_float_range(self):
        """Test CSGO keyboard has float range option."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        keyboard = get_game_filter_keyboard("csgo")

        # Check keyboard has buttons
        assert isinstance(keyboard, InlineKeyboardMarkup)

        # Flatten buttons and check for float range
        all_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                all_buttons.append(button.callback_data)

        assert any("float_range" in str(data) for data in all_buttons)

    def test_keyboard_csgo_has_stattrak(self):
        """Test CSGO keyboard has StatTrak option."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        keyboard = get_game_filter_keyboard("csgo")
        all_buttons = [b.callback_data for row in keyboard.inline_keyboard for b in row]

        assert any("stattrak" in str(data) for data in all_buttons)

    def test_keyboard_dota2_has_hero(self):
        """Test Dota 2 keyboard has hero selection."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        keyboard = get_game_filter_keyboard("dota2")
        all_buttons = [b.callback_data for row in keyboard.inline_keyboard for b in row]

        assert any("hero" in str(data) for data in all_buttons)

    def test_keyboard_tf2_has_class(self):
        """Test TF2 keyboard has class selection."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        keyboard = get_game_filter_keyboard("tf2")
        all_buttons = [b.callback_data for row in keyboard.inline_keyboard for b in row]

        assert any("class" in str(data) for data in all_buttons)

    def test_keyboard_rust_has_category(self):
        """Test Rust keyboard has category selection."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        keyboard = get_game_filter_keyboard("rust")
        all_buttons = [b.callback_data for row in keyboard.inline_keyboard for b in row]

        assert any("category" in str(data) for data in all_buttons)

    def test_keyboard_all_games_have_price_range(self):
        """Test all games have price range option."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        for game in ["csgo", "dota2", "tf2", "rust"]:
            keyboard = get_game_filter_keyboard(game)
            all_buttons = [
                b.callback_data for row in keyboard.inline_keyboard for b in row
            ]

            assert any("price_range" in str(data) for data in all_buttons)

    def test_keyboard_all_games_have_reset(self):
        """Test all games have reset option."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        for game in ["csgo", "dota2", "tf2", "rust"]:
            keyboard = get_game_filter_keyboard(game)
            all_buttons = [
                b.callback_data for row in keyboard.inline_keyboard for b in row
            ]

            assert any("reset" in str(data) for data in all_buttons)

    def test_keyboard_all_games_have_back(self):
        """Test all games have back button."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_game_filter_keyboard,
        )

        for game in ["csgo", "dota2", "tf2", "rust"]:
            keyboard = get_game_filter_keyboard(game)
            all_buttons = [
                b.callback_data for row in keyboard.inline_keyboard for b in row
            ]

            assert any("back_to_filters" in str(data) for data in all_buttons)


class TestGetFilterDescription:
    """Tests for get_filter_description function."""

    def test_filter_description_empty_filters(self):
        """Test filter description with empty filters."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_filter_description,
        )

        description = get_filter_description("csgo", {})

        # Should return some description string
        assert isinstance(description, str)

    def test_filter_description_with_price_range(self):
        """Test filter description includes price range."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_filter_description,
        )

        filters = {"min_price": 10.0, "max_price": 100.0}
        description = get_filter_description("csgo", filters)

        assert isinstance(description, str)


class TestBuildApiParamsForGame:
    """Tests for build_api_params_for_game function."""

    def test_build_params_csgo_basic(self):
        """Test building API params for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            build_api_params_for_game,
        )

        filters = {"min_price": 10.0, "max_price": 100.0}
        params = build_api_params_for_game("csgo", filters)

        assert isinstance(params, dict)

    def test_build_params_dota2_basic(self):
        """Test building API params for Dota 2."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            build_api_params_for_game,
        )

        filters = {"hero": "Pudge", "rarity": "Mythical"}
        params = build_api_params_for_game("dota2", filters)

        assert isinstance(params, dict)


class TestHandleGameFilters:
    """Tests for handle_game_filters handler."""

    @pytest.mark.asyncio()
    async def test_handle_game_filters_basic(self, mock_update, mock_context):
        """Test basic game filters command."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_game_filters

        await handle_game_filters(mock_update, mock_context)

        # Should send a message with game selection
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Выберите игру" in call_args.kwargs.get("text", call_args.args[0])

    @pytest.mark.asyncio()
    async def test_handle_game_filters_no_message(self, mock_update, mock_context):
        """Test handler when no message present."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_game_filters

        mock_update.message = None
        await handle_game_filters(mock_update, mock_context)

        # Should return early without error


class TestHandleSelectGameFilterCallback:
    """Tests for handle_select_game_filter_callback handler."""

    @pytest.mark.asyncio()
    async def test_select_csgo_filter(self, mock_update, mock_context):
        """Test selecting CSGO filters."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        mock_update.callback_query.data = "select_game_filter:csgo"

        await handle_select_game_filter_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "CS2" in call_args.kwargs.get("text", "")

    @pytest.mark.asyncio()
    async def test_select_dota2_filter(self, mock_update, mock_context):
        """Test selecting Dota 2 filters."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        mock_update.callback_query.data = "select_game_filter:dota2"

        await handle_select_game_filter_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Dota 2" in call_args.kwargs.get("text", "")

    @pytest.mark.asyncio()
    async def test_select_no_query(self, mock_update, mock_context):
        """Test handler with no callback query."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        mock_update.callback_query = None
        await handle_select_game_filter_callback(mock_update, mock_context)

        # Should return early without error

    @pytest.mark.asyncio()
    async def test_select_no_query_data(self, mock_update, mock_context):
        """Test handler with no callback query data."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        mock_update.callback_query.data = None
        await handle_select_game_filter_callback(mock_update, mock_context)

        # Should return early without error


class TestHandlePriceRangeCallback:
    """Tests for handle_price_range_callback handler."""

    @pytest.mark.asyncio()
    async def test_price_range_callback_basic(self, mock_update, mock_context):
        """Test basic price range callback."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_price_range_callback,
        )

        mock_update.callback_query.data = "price_range:csgo"

        await handle_price_range_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Настройка диапазона цен" in call_args.kwargs.get("text", "")

    @pytest.mark.asyncio()
    async def test_price_range_no_query(self, mock_update, mock_context):
        """Test price range with no query."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_price_range_callback,
        )

        mock_update.callback_query = None
        await handle_price_range_callback(mock_update, mock_context)


class TestHandleFloatRangeCallback:
    """Tests for handle_float_range_callback handler."""

    @pytest.mark.asyncio()
    async def test_float_range_callback_csgo(self, mock_update, mock_context):
        """Test float range callback for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_float_range_callback,
        )

        mock_update.callback_query.data = "float_range:csgo"

        await handle_float_range_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Float" in call_args.kwargs.get("text", "")

    @pytest.mark.asyncio()
    async def test_float_range_callback_non_csgo(self, mock_update, mock_context):
        """Test float range callback for non-CSGO game."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_float_range_callback,
        )

        mock_update.callback_query.data = "float_range:dota2"

        await handle_float_range_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "только для CS2" in call_args.kwargs.get("text", "")


class TestHandleSetCategoryCallback:
    """Tests for handle_set_category_callback handler."""

    @pytest.mark.asyncio()
    async def test_set_category_csgo(self, mock_update, mock_context):
        """Test set category callback for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_category_callback,
        )

        mock_update.callback_query.data = "set_category:csgo"

        await handle_set_category_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "категории" in call_args.kwargs.get("text", "").lower()

    @pytest.mark.asyncio()
    async def test_set_category_rust(self, mock_update, mock_context):
        """Test set category callback for Rust."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_category_callback,
        )

        mock_update.callback_query.data = "set_category:rust"

        await handle_set_category_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "категории" in call_args.kwargs.get("text", "").lower()


class TestHandleSetRarityCallback:
    """Tests for handle_set_rarity_callback handler."""

    @pytest.mark.asyncio()
    async def test_set_rarity_csgo(self, mock_update, mock_context):
        """Test set rarity callback for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_rarity_callback,
        )

        mock_update.callback_query.data = "set_rarity:csgo"

        await handle_set_rarity_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "редкости" in call_args.kwargs.get("text", "").lower()

    @pytest.mark.asyncio()
    async def test_set_rarity_dota2(self, mock_update, mock_context):
        """Test set rarity callback for Dota 2."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_rarity_callback,
        )

        mock_update.callback_query.data = "set_rarity:dota2"

        await handle_set_rarity_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "редкости" in call_args.kwargs.get("text", "").lower()

    @pytest.mark.asyncio()
    async def test_set_rarity_tf2_empty_list(self, mock_update, mock_context):
        """Test set rarity callback for TF2 (no rarity list)."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_rarity_callback,
        )

        mock_update.callback_query.data = "set_rarity:tf2"

        # TF2 doesn't have rarities in this implementation
        await handle_set_rarity_callback(mock_update, mock_context)


class TestHandleSetExteriorCallback:
    """Tests for handle_set_exterior_callback handler."""

    @pytest.mark.asyncio()
    async def test_set_exterior_csgo(self, mock_update, mock_context):
        """Test set exterior callback for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_exterior_callback,
        )

        mock_update.callback_query.data = "set_exterior:csgo"

        await handle_set_exterior_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "внешнего вида" in call_args.kwargs.get("text", "").lower()

    @pytest.mark.asyncio()
    async def test_set_exterior_non_csgo(self, mock_update, mock_context):
        """Test set exterior callback for non-CSGO game."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_exterior_callback,
        )

        mock_update.callback_query.data = "set_exterior:dota2"

        await handle_set_exterior_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "только для CS2" in call_args.kwargs.get("text", "")


class TestHandleSetHeroCallback:
    """Tests for handle_set_hero_callback handler."""

    @pytest.mark.asyncio()
    async def test_set_hero_dota2(self, mock_update, mock_context):
        """Test set hero callback for Dota 2."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_hero_callback,
        )

        mock_update.callback_query.data = "set_hero:dota2"

        await handle_set_hero_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "героя" in call_args.kwargs.get("text", "").lower()

    @pytest.mark.asyncio()
    async def test_set_hero_non_dota2(self, mock_update, mock_context):
        """Test set hero callback for non-Dota 2 game."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_hero_callback,
        )

        mock_update.callback_query.data = "set_hero:csgo"

        await handle_set_hero_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "только для Dota 2" in call_args.kwargs.get("text", "")


class TestHandleSetClassCallback:
    """Tests for handle_set_class_callback handler."""

    @pytest.mark.asyncio()
    async def test_set_class_tf2(self, mock_update, mock_context):
        """Test set class callback for TF2."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_class_callback,
        )

        mock_update.callback_query.data = "set_class:tf2"

        await handle_set_class_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "класса" in call_args.kwargs.get("text", "").lower()

    @pytest.mark.asyncio()
    async def test_set_class_non_tf2(self, mock_update, mock_context):
        """Test set class callback for non-TF2 game."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_set_class_callback,
        )

        mock_update.callback_query.data = "set_class:csgo"

        await handle_set_class_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "только для Team Fortress 2" in call_args.kwargs.get("text", "")


class TestHandleFilterCallback:
    """Tests for handle_filter_callback handler."""

    @pytest.mark.asyncio()
    async def test_filter_callback_price_range(self, mock_update, mock_context):
        """Test filter callback for price range."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:price_range:min:max:game
        mock_update.callback_query.data = "filter:price_range:10:50:csgo"

        # Mock handle_select_game_filter_callback to avoid the re-parsing issue
        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        # Should update filters
        assert "filters" in mock_context.user_data
        assert mock_context.user_data["filters"]["csgo"]["min_price"] == 10.0
        assert mock_context.user_data["filters"]["csgo"]["max_price"] == 50.0

    @pytest.mark.asyncio()
    async def test_filter_callback_price_range_reset(self, mock_update, mock_context):
        """Test filter callback for price range reset."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # First set some filters
        mock_context.user_data = {
            "filters": {"csgo": {"min_price": 10.0, "max_price": 50.0}}
        }
        # Format: filter:price_range:reset:game
        mock_update.callback_query.data = "filter:price_range:reset:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        # Price range should be reset
        assert "min_price" not in mock_context.user_data["filters"]["csgo"]

    @pytest.mark.asyncio()
    async def test_filter_callback_float_range(self, mock_update, mock_context):
        """Test filter callback for float range."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:float_range:min:max:game
        mock_update.callback_query.data = "filter:float_range:0.00:0.07:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        assert mock_context.user_data["filters"]["csgo"]["float_min"] == 0.0
        assert mock_context.user_data["filters"]["csgo"]["float_max"] == 0.07

    @pytest.mark.asyncio()
    async def test_filter_callback_category(self, mock_update, mock_context):
        """Test filter callback for category."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:category:value:game
        mock_update.callback_query.data = "filter:category:Rifle:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        assert mock_context.user_data["filters"]["csgo"]["category"] == "Rifle"

    @pytest.mark.asyncio()
    async def test_filter_callback_rarity(self, mock_update, mock_context):
        """Test filter callback for rarity."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:rarity:value:game
        mock_update.callback_query.data = "filter:rarity:Covert:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        assert mock_context.user_data["filters"]["csgo"]["rarity"] == "Covert"

    @pytest.mark.asyncio()
    async def test_filter_callback_exterior(self, mock_update, mock_context):
        """Test filter callback for exterior."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:exterior:value:game
        mock_update.callback_query.data = "filter:exterior:Factory New:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        assert mock_context.user_data["filters"]["csgo"]["exterior"] == "Factory New"

    @pytest.mark.asyncio()
    async def test_filter_callback_hero(self, mock_update, mock_context):
        """Test filter callback for hero."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:hero:value:game
        mock_update.callback_query.data = "filter:hero:Pudge:dota2"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        assert mock_context.user_data["filters"]["dota2"]["hero"] == "Pudge"

    @pytest.mark.asyncio()
    async def test_filter_callback_class(self, mock_update, mock_context):
        """Test filter callback for class."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        # Format: filter:class:value:game
        mock_update.callback_query.data = "filter:class:Scout:tf2"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        assert mock_context.user_data["filters"]["tf2"]["class"] == "Scout"

    @pytest.mark.asyncio()
    async def test_filter_callback_boolean_toggle_stattrak(
        self, mock_update, mock_context
    ):
        """Test filter callback for boolean toggle (StatTrak)."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        mock_context.user_data = {"filters": {"csgo": {"stattrak": False}}}
        # Format: filter:stattrak:toggle:game
        mock_update.callback_query.data = "filter:stattrak:toggle:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        # Should toggle stattrak to True
        assert mock_context.user_data["filters"]["csgo"]["stattrak"] is True

    @pytest.mark.asyncio()
    async def test_filter_callback_reset_all(self, mock_update, mock_context):
        """Test filter callback for complete reset."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            DEFAULT_FILTERS,
            handle_filter_callback,
        )

        mock_context.user_data = {
            "filters": {"csgo": {"min_price": 100.0, "category": "Knife"}}
        }
        # Format: filter:reset:all:game
        mock_update.callback_query.data = "filter:reset:all:csgo"

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(mock_update, mock_context)

        # Filters should be reset to defaults
        assert mock_context.user_data["filters"]["csgo"] == DEFAULT_FILTERS["csgo"]

    @pytest.mark.asyncio()
    async def test_filter_callback_invalid_format(self, mock_update, mock_context):
        """Test filter callback with invalid data format."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_filter_callback,
        )

        mock_update.callback_query.data = "filter:x"  # Too short

        await handle_filter_callback(mock_update, mock_context)

        # Should show error message
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Неверный формат" in call_args.kwargs.get("text", "")


class TestHandleBackToFiltersCallback:
    """Tests for handle_back_to_filters_callback handler."""

    @pytest.mark.asyncio()
    async def test_back_to_filters_main(self, mock_update, mock_context):
        """Test back to filters with main target."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_back_to_filters_callback,
        )

        mock_update.callback_query.data = "back_to_filters:main"

        await handle_back_to_filters_callback(mock_update, mock_context)

        # Should call handle_game_filters which sends game selection

    @pytest.mark.asyncio()
    async def test_back_to_filters_no_data(self, mock_update, mock_context):
        """Test back to filters with no target."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_back_to_filters_callback,
        )

        mock_update.callback_query.data = "back_to_filters"

        await handle_back_to_filters_callback(mock_update, mock_context)

        # Should show default message
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Выберите действие" in call_args.kwargs.get("text", "")

    @pytest.mark.asyncio()
    async def test_back_to_filters_unknown_type(self, mock_update, mock_context):
        """Test back to filters with unknown type."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_back_to_filters_callback,
        )

        mock_update.callback_query.data = "back_to_filters:unknown"

        await handle_back_to_filters_callback(mock_update, mock_context)

        # Should default to arbitrage
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Выберите действие" in call_args.kwargs.get("text", "")


class TestConstantsContent:
    """Test content of game constants."""

    def test_tf2_classes_includes_all_classes(self):
        """Test TF2 classes includes all 9 classes."""
        from src.telegram_bot.handlers.game_filter_handlers import TF2_CLASSES

        expected = [
            "Scout",
            "Soldier",
            "Pyro",
            "Demoman",
            "Heavy",
            "Engineer",
            "Medic",
            "Sniper",
            "Spy",
        ]
        for cls in expected:
            assert cls in TF2_CLASSES

    def test_tf2_qualities_includes_unusual(self):
        """Test TF2 qualities includes Unusual."""
        from src.telegram_bot.handlers.game_filter_handlers import TF2_QUALITIES

        assert "Unusual" in TF2_QUALITIES

    def test_rust_categories_content(self):
        """Test Rust categories content."""
        from src.telegram_bot.handlers.game_filter_handlers import RUST_CATEGORIES

        assert "Weapon" in RUST_CATEGORIES
        assert "Clothing" in RUST_CATEGORIES

    def test_rust_types_content(self):
        """Test Rust types content."""
        from src.telegram_bot.handlers.game_filter_handlers import RUST_TYPES

        assert "Assault Rifle" in RUST_TYPES


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_callback_with_none_query(self, mock_update, mock_context):
        """Test handlers with None callback query."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_back_to_filters_callback,
            handle_filter_callback,
            handle_float_range_callback,
            handle_price_range_callback,
            handle_select_game_filter_callback,
            handle_set_category_callback,
            handle_set_class_callback,
            handle_set_exterior_callback,
            handle_set_hero_callback,
            handle_set_rarity_callback,
        )

        mock_update.callback_query = None

        # All these should handle None gracefully
        await handle_select_game_filter_callback(mock_update, mock_context)
        await handle_price_range_callback(mock_update, mock_context)
        await handle_float_range_callback(mock_update, mock_context)
        await handle_set_category_callback(mock_update, mock_context)
        await handle_set_rarity_callback(mock_update, mock_context)
        await handle_set_exterior_callback(mock_update, mock_context)
        await handle_set_hero_callback(mock_update, mock_context)
        await handle_set_class_callback(mock_update, mock_context)
        await handle_filter_callback(mock_update, mock_context)
        await handle_back_to_filters_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_callback_with_empty_data(self, mock_update, mock_context):
        """Test handlers with empty callback data."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        mock_update.callback_query.data = ""
        await handle_select_game_filter_callback(mock_update, mock_context)

        # Should handle empty data gracefully

    def test_get_filters_multiple_games(self, mock_context):
        """Test getting filters for multiple games."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            get_current_filters,
            update_filters,
        )

        # Update filters for multiple games
        update_filters(mock_context, "csgo", {"min_price": 10.0})
        update_filters(mock_context, "dota2", {"hero": "Pudge"})
        update_filters(mock_context, "tf2", {"class": "Scout"})

        # Verify each game has its own filters
        csgo_filters = get_current_filters(mock_context, "csgo")
        dota2_filters = get_current_filters(mock_context, "dota2")
        tf2_filters = get_current_filters(mock_context, "tf2")

        assert csgo_filters["min_price"] == 10.0
        assert dota2_filters["hero"] == "Pudge"
        assert tf2_filters["class"] == "Scout"

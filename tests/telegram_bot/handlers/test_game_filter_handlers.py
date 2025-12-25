"""Unit tests for src/telegram_bot/handlers/game_filter_handlers.py.

Tests for game filter handlers including:
- Game filter constants (CS2, Dota 2, TF2, Rust)
- get_current_filters function
- update_filters function
- get_game_filter_keyboard function
- get_filter_description function
- build_api_params_for_game function
- Handler callbacks
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGameFilterConstants:
    """Tests for game filter constants."""

    def test_cs2_categories_defined(self):
        """Test CS2 categories are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import CS2_CATEGORIES

        expected_categories = ["Pistol", "SMG", "Rifle", "Knife", "Gloves", "Sticker"]
        for cat in expected_categories:
            assert cat in CS2_CATEGORIES

    def test_cs2_rarities_defined(self):
        """Test CS2 rarities are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import CS2_RARITIES

        expected_rarities = ["Consumer Grade", "Covert", "Contraband"]
        for rarity in expected_rarities:
            assert rarity in CS2_RARITIES

    def test_cs2_exteriors_defined(self):
        """Test CS2 exteriors are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import CS2_EXTERIORS

        expected_exteriors = [
            "Factory New",
            "Minimal Wear",
            "Field-Tested",
            "Well-Worn",
            "Battle-Scarred",
        ]
        assert CS2_EXTERIORS == expected_exteriors

    def test_dota2_heroes_defined(self):
        """Test Dota 2 heroes are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import DOTA2_HEROES

        expected_heroes = ["Axe", "Pudge", "Invoker"]
        for hero in expected_heroes:
            assert hero in DOTA2_HEROES

    def test_dota2_rarities_defined(self):
        """Test Dota 2 rarities are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import DOTA2_RARITIES

        expected_rarities = ["Common", "Immortal", "Arcana"]
        for rarity in expected_rarities:
            assert rarity in DOTA2_RARITIES

    def test_dota2_slots_defined(self):
        """Test Dota 2 slots are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import DOTA2_SLOTS

        expected_slots = ["Weapon", "Head", "Courier", "Ward"]
        for slot in expected_slots:
            assert slot in DOTA2_SLOTS

    def test_tf2_classes_defined(self):
        """Test TF2 classes are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import TF2_CLASSES

        expected_classes = ["Scout", "Soldier", "Spy", "All Classes"]
        for cls in expected_classes:
            assert cls in TF2_CLASSES

    def test_tf2_qualities_defined(self):
        """Test TF2 qualities are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import TF2_QUALITIES

        expected_qualities = ["Unique", "Strange", "Unusual"]
        for quality in expected_qualities:
            assert quality in TF2_QUALITIES

    def test_tf2_types_defined(self):
        """Test TF2 types are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import TF2_TYPES

        expected_types = ["Hat", "Weapon", "Cosmetic", "Key"]
        for typ in expected_types:
            assert typ in TF2_TYPES

    def test_rust_categories_defined(self):
        """Test Rust categories are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import RUST_CATEGORIES

        expected_categories = ["Weapon", "Clothing", "Tool"]
        for cat in expected_categories:
            assert cat in RUST_CATEGORIES

    def test_rust_types_defined(self):
        """Test Rust types are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import RUST_TYPES

        expected_types = ["Assault Rifle", "Pistol", "Jacket"]
        for typ in expected_types:
            assert typ in RUST_TYPES

    def test_rust_rarities_defined(self):
        """Test Rust rarities are defined."""
        from src.telegram_bot.handlers.game_filter_handlers import RUST_RARITIES

        expected_rarities = ["Common", "Rare", "Legendary"]
        for rarity in expected_rarities:
            assert rarity in RUST_RARITIES


class TestDefaultFilters:
    """Tests for DEFAULT_FILTERS constant."""

    def test_default_filters_for_csgo(self):
        """Test default filters for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        assert "csgo" in DEFAULT_FILTERS
        csgo_filters = DEFAULT_FILTERS["csgo"]
        assert csgo_filters["min_price"] == 1.0
        assert csgo_filters["max_price"] == 1000.0
        assert csgo_filters["float_min"] == 0.0
        assert csgo_filters["float_max"] == 1.0
        assert csgo_filters["stattrak"] is False
        assert csgo_filters["souvenir"] is False

    def test_default_filters_for_dota2(self):
        """Test default filters for Dota 2."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        assert "dota2" in DEFAULT_FILTERS
        dota2_filters = DEFAULT_FILTERS["dota2"]
        assert dota2_filters["min_price"] == 1.0
        assert dota2_filters["max_price"] == 1000.0
        assert dota2_filters["tradable"] is True

    def test_default_filters_for_tf2(self):
        """Test default filters for TF2."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        assert "tf2" in DEFAULT_FILTERS
        tf2_filters = DEFAULT_FILTERS["tf2"]
        assert tf2_filters["min_price"] == 1.0
        assert tf2_filters["max_price"] == 1000.0
        assert tf2_filters["australium"] is False

    def test_default_filters_for_rust(self):
        """Test default filters for Rust."""
        from src.telegram_bot.handlers.game_filter_handlers import DEFAULT_FILTERS

        assert "rust" in DEFAULT_FILTERS
        rust_filters = DEFAULT_FILTERS["rust"]
        assert rust_filters["min_price"] == 1.0
        assert rust_filters["max_price"] == 1000.0


class TestGetCurrentFilters:
    """Tests for get_current_filters function."""

    def test_returns_default_when_no_user_data(self):
        """Test returns default filters when no user data."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            DEFAULT_FILTERS,
            get_current_filters,
        )

        context = MagicMock()
        context.user_data = None

        result = get_current_filters(context, "csgo")
        assert result == DEFAULT_FILTERS["csgo"]

    def test_returns_default_when_no_filters(self):
        """Test returns default filters when filters not set."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            DEFAULT_FILTERS,
            get_current_filters,
        )

        context = MagicMock()
        context.user_data = {}

        result = get_current_filters(context, "csgo")
        assert result == DEFAULT_FILTERS["csgo"]

    def test_returns_user_filters(self):
        """Test returns user-set filters."""
        from src.telegram_bot.handlers.game_filter_handlers import get_current_filters

        context = MagicMock()
        context.user_data = {
            "filters": {
                "csgo": {"min_price": 10.0, "max_price": 500.0}
            }
        }

        result = get_current_filters(context, "csgo")
        assert result["min_price"] == 10.0
        assert result["max_price"] == 500.0

    def test_returns_default_for_unknown_game(self):
        """Test returns empty dict for unknown game."""
        from src.telegram_bot.handlers.game_filter_handlers import get_current_filters

        context = MagicMock()
        context.user_data = {}

        result = get_current_filters(context, "unknown_game")
        assert result == {}


class TestUpdateFilters:
    """Tests for update_filters function."""

    def test_creates_filters_dict(self):
        """Test creates filters dict when not exists."""
        from src.telegram_bot.handlers.game_filter_handlers import update_filters

        context = MagicMock()
        context.user_data = {}

        update_filters(context, "csgo", {"min_price": 10.0})

        assert "filters" in context.user_data
        assert context.user_data["filters"]["csgo"]["min_price"] == 10.0

    def test_updates_existing_filters(self):
        """Test updates existing filters."""
        from src.telegram_bot.handlers.game_filter_handlers import update_filters

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {"min_price": 5.0}}}

        update_filters(context, "csgo", {"min_price": 10.0, "max_price": 100.0})

        assert context.user_data["filters"]["csgo"]["min_price"] == 10.0
        assert context.user_data["filters"]["csgo"]["max_price"] == 100.0

    def test_handles_none_user_data(self):
        """Test handles None user_data."""
        from src.telegram_bot.handlers.game_filter_handlers import update_filters

        context = MagicMock()
        context.user_data = None

        # Should not raise
        update_filters(context, "csgo", {"min_price": 10.0})


class TestGetGameFilterKeyboard:
    """Tests for get_game_filter_keyboard function."""

    def test_returns_inline_keyboard(self):
        """Test returns InlineKeyboardMarkup."""
        from telegram import InlineKeyboardMarkup

        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("csgo")
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_csgo_keyboard_has_specific_buttons(self):
        """Test CSGO keyboard has game-specific buttons."""
        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("csgo")
        button_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_data.append(button.callback_data)

        assert any("float_range:csgo" in d for d in button_data if d)
        assert any("stattrak" in d for d in button_data if d)
        assert any("souvenir" in d for d in button_data if d)

    def test_dota2_keyboard_has_specific_buttons(self):
        """Test Dota 2 keyboard has game-specific buttons."""
        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("dota2")
        button_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_data.append(button.callback_data)

        assert any("set_hero:dota2" in d for d in button_data if d)
        assert any("set_slot:dota2" in d for d in button_data if d)

    def test_tf2_keyboard_has_specific_buttons(self):
        """Test TF2 keyboard has game-specific buttons."""
        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("tf2")
        button_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_data.append(button.callback_data)

        assert any("set_class:tf2" in d for d in button_data if d)
        assert any("australium" in d for d in button_data if d)

    def test_rust_keyboard_has_specific_buttons(self):
        """Test Rust keyboard has game-specific buttons."""
        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("rust")
        button_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_data.append(button.callback_data)

        assert any("set_category:rust" in d for d in button_data if d)
        assert any("set_type:rust" in d for d in button_data if d)

    def test_keyboard_has_reset_button(self):
        """Test keyboard has reset button."""
        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("csgo")
        button_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_data.append(button.callback_data)

        assert any("filter:reset:csgo" in d for d in button_data if d)

    def test_keyboard_has_back_button(self):
        """Test keyboard has back button."""
        from src.telegram_bot.handlers.game_filter_handlers import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("csgo")
        button_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_data.append(button.callback_data)

        assert any("back_to_filters:main" in d for d in button_data if d)


class TestGetFilterDescription:
    """Tests for get_filter_description function."""

    def test_returns_string(self):
        """Test returns a string."""
        from src.telegram_bot.handlers.game_filter_handlers import get_filter_description

        with patch("src.telegram_bot.handlers.game_filter_handlers.FilterFactory") as mock_factory:
            mock_filter = MagicMock()
            mock_filter.get_filter_description.return_value = "Test description"
            mock_factory.get_filter.return_value = mock_filter

            result = get_filter_description("csgo", {"min_price": 10.0})

            assert result == "Test description"

    def test_calls_filter_factory(self):
        """Test calls FilterFactory correctly."""
        from src.telegram_bot.handlers.game_filter_handlers import get_filter_description

        with patch("src.telegram_bot.handlers.game_filter_handlers.FilterFactory") as mock_factory:
            mock_filter = MagicMock()
            mock_filter.get_filter_description.return_value = ""
            mock_factory.get_filter.return_value = mock_filter

            get_filter_description("csgo", {"min_price": 10.0})

            mock_factory.get_filter.assert_called_once_with("csgo")
            mock_filter.get_filter_description.assert_called_once_with({"min_price": 10.0})


class TestBuildApiParamsForGame:
    """Tests for build_api_params_for_game function."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        from src.telegram_bot.handlers.game_filter_handlers import build_api_params_for_game

        with patch("src.telegram_bot.handlers.game_filter_handlers.FilterFactory") as mock_factory:
            mock_filter = MagicMock()
            mock_filter.build_api_params.return_value = {"param1": "value1"}
            mock_factory.get_filter.return_value = mock_filter

            result = build_api_params_for_game("csgo", {"min_price": 10.0})

            assert result == {"param1": "value1"}

    def test_calls_filter_factory(self):
        """Test calls FilterFactory correctly."""
        from src.telegram_bot.handlers.game_filter_handlers import build_api_params_for_game

        with patch("src.telegram_bot.handlers.game_filter_handlers.FilterFactory") as mock_factory:
            mock_filter = MagicMock()
            mock_filter.build_api_params.return_value = {}
            mock_factory.get_filter.return_value = mock_filter

            build_api_params_for_game("dota2", {"hero": "Axe"})

            mock_factory.get_filter.assert_called_once_with("dota2")
            mock_filter.build_api_params.assert_called_once_with({"hero": "Axe"})


class TestHandleGameFilters:
    """Tests for handle_game_filters handler."""

    @pytest.mark.asyncio
    async def test_sends_game_selection_message(self):
        """Test sends game selection message."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_game_filters

        update = MagicMock()
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        await handle_game_filters(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Выберите игру" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self):
        """Test returns early when no message."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_game_filters

        update = MagicMock()
        update.message = None

        context = MagicMock()

        # Should not raise
        await handle_game_filters(update, context)


class TestHandleSelectGameFilterCallback:
    """Tests for handle_select_game_filter_callback handler."""

    @pytest.mark.asyncio
    async def test_shows_filter_menu(self):
        """Test shows filter menu for selected game."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "select_game_filter:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        with patch("src.telegram_bot.handlers.game_filter_handlers.get_filter_description", return_value=""):
            await handle_select_game_filter_callback(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_when_no_query(self):
        """Test returns early when no callback query."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        update.callback_query = None

        context = MagicMock()

        # Should not raise
        await handle_select_game_filter_callback(update, context)


class TestHandlePriceRangeCallback:
    """Tests for handle_price_range_callback handler."""

    @pytest.mark.asyncio
    async def test_shows_price_range_options(self):
        """Test shows price range options."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_price_range_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "price_range:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        await handle_price_range_callback(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "Настройка диапазона цен" in call_args[1]["text"]


class TestHandleFloatRangeCallback:
    """Tests for handle_float_range_callback handler."""

    @pytest.mark.asyncio
    async def test_shows_float_range_for_csgo(self):
        """Test shows float range options for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_float_range_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "float_range:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        await handle_float_range_callback(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "Float" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_shows_error_for_non_csgo(self):
        """Test shows error message for non-CSGO games."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_float_range_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "float_range:dota2"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        await handle_float_range_callback(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "только для CS2" in call_args[1]["text"]


class TestHandleSetCategoryCallback:
    """Tests for handle_set_category_callback handler."""

    @pytest.mark.asyncio
    async def test_shows_categories_for_csgo(self):
        """Test shows category options for CSGO."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_set_category_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "set_category:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        await handle_set_category_callback(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "категории" in call_args[1]["text"]


class TestHandleSetRarityCallback:
    """Tests for handle_set_rarity_callback handler."""

    @pytest.mark.asyncio
    async def test_shows_rarities(self):
        """Test shows rarity options."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_set_rarity_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "set_rarity:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        await handle_set_rarity_callback(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "редкости" in call_args[1]["text"]


class TestHandleFilterCallback:
    """Tests for handle_filter_callback handler."""

    @pytest.mark.asyncio
    async def test_handles_price_range_filter(self):
        """Test handles price range filter update."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_filter_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "filter:price_range:10:50:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {}}}

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(update, context)

        # Filters should be updated
        assert context.user_data["filters"]["csgo"]["min_price"] == 10.0
        assert context.user_data["filters"]["csgo"]["max_price"] == 50.0

    @pytest.mark.asyncio
    async def test_handles_reset_filter(self):
        """Test handles reset filter."""
        from src.telegram_bot.handlers.game_filter_handlers import (
            DEFAULT_FILTERS,
            handle_filter_callback,
        )

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "filter:reset:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {"min_price": 100.0}}}

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(update, context)

        # Filters should be reset to defaults
        assert context.user_data["filters"]["csgo"] == DEFAULT_FILTERS["csgo"]

    @pytest.mark.asyncio
    async def test_handles_boolean_filter_toggle(self):
        """Test handles boolean filter toggle."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_filter_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "filter:stattrak:false:csgo"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {"stattrak": False}}}

        with patch(
            "src.telegram_bot.handlers.game_filter_handlers.handle_select_game_filter_callback",
            new_callable=AsyncMock,
        ):
            await handle_filter_callback(update, context)

        # StatTrak should be toggled to True
        assert context.user_data["filters"]["csgo"]["stattrak"] is True

    @pytest.mark.asyncio
    async def test_handles_invalid_data_format(self):
        """Test handles invalid callback data format."""
        from src.telegram_bot.handlers.game_filter_handlers import handle_filter_callback

        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.data = "filter:invalid"  # Missing parts
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        await handle_filter_callback(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "Неверный формат" in call_args[1]["text"]

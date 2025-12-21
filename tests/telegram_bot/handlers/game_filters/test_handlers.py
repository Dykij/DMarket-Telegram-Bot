"""Tests for game_filters handlers module.

This module tests handler functions for game filters:
- handle_game_filters
- handle_select_game_filter_callback
- handle_price_range_callback
- handle_float_range_callback
- handle_set_category_callback
- handle_set_rarity_callback
- handle_set_exterior_callback
- handle_set_hero_callback
- handle_set_slot_callback
- handle_set_class_callback
- handle_set_type_callback
- handle_set_quality_callback
- handle_filter_value_callback
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from telegram import Update, Message, CallbackQuery, User, Chat
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.game_filters.handlers import (
    handle_game_filters,
    handle_select_game_filter_callback,
    handle_price_range_callback,
    handle_float_range_callback,
    handle_set_category_callback,
    handle_set_rarity_callback,
    handle_set_exterior_callback,
    handle_set_hero_callback,
    handle_set_slot_callback,
    handle_set_class_callback,
    handle_set_type_callback,
    handle_set_quality_callback,
    handle_filter_value_callback,
)
from src.telegram_bot.handlers.game_filters.constants import DEFAULT_FILTERS


@pytest.fixture
def mock_update():
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_callback_update():
    """Create a mock Update object with callback_query."""
    update = MagicMock(spec=Update)
    update.message = None
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "select_game_filter:csgo"
    return update


@pytest.fixture
def mock_context():
    """Create a mock context object."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


class TestHandleGameFilters:
    """Tests for handle_game_filters function."""

    @pytest.mark.asyncio
    async def test_sends_game_selection_keyboard(self, mock_update, mock_context):
        """Test sends game selection keyboard."""
        await handle_game_filters(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Выберите игру" in call_args[0][0]
        assert call_args[1]["reply_markup"] is not None

    @pytest.mark.asyncio
    async def test_returns_early_if_no_message(self, mock_context):
        """Test returns early if no message."""
        update = MagicMock(spec=Update)
        update.message = None
        
        await handle_game_filters(update, mock_context)
        # Should not raise

    @pytest.mark.asyncio
    async def test_keyboard_has_all_games(self, mock_update, mock_context):
        """Test keyboard has all games."""
        await handle_game_filters(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args
        keyboard = call_args[1]["reply_markup"].inline_keyboard
        
        buttons = []
        for row in keyboard:
            for button in row:
                buttons.append(button.callback_data)
        
        assert any("csgo" in btn for btn in buttons)
        assert any("dota2" in btn for btn in buttons)
        assert any("tf2" in btn for btn in buttons)
        assert any("rust" in btn for btn in buttons)


class TestHandleSelectGameFilterCallback:
    """Tests for handle_select_game_filter_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_game_filters(
        self, mock_keyboard, mock_description, mock_get_filters, mock_callback_update, mock_context
    ):
        """Test shows game filters."""
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"]
        mock_description.return_value = "Test description"
        mock_keyboard.return_value = MagicMock()
        
        await handle_select_game_filter_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self, mock_context):
        """Test returns early if no query."""
        update = MagicMock(spec=Update)
        update.callback_query = None
        
        await handle_select_game_filter_callback(update, mock_context)
        # Should not raise

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query_data(self, mock_context):
        """Test returns early if no query data."""
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = None
        
        await handle_select_game_filter_callback(update, mock_context)
        # Should not raise

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_extracts_game_from_callback_data(
        self, mock_keyboard, mock_description, mock_get_filters, mock_context
    ):
        """Test extracts game from callback data."""
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "select_game_filter:dota2"
        
        mock_get_filters.return_value = DEFAULT_FILTERS["dota2"]
        mock_description.return_value = ""
        mock_keyboard.return_value = MagicMock()
        
        await handle_select_game_filter_callback(update, mock_context)
        
        mock_get_filters.assert_called_once_with(mock_context, "dota2")


class TestHandlePriceRangeCallback:
    """Tests for handle_price_range_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_price_range_options(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows price range options."""
        mock_callback_update.callback_query.data = "price_range:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"]
        
        await handle_price_range_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "диапазона цен" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_returns_early_if_no_query(self, mock_context):
        """Test returns early if no query."""
        update = MagicMock(spec=Update)
        update.callback_query = None
        
        await handle_price_range_callback(update, mock_context)
        # Should not raise


class TestHandleFloatRangeCallback:
    """Tests for handle_float_range_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_float_range_options_for_csgo(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows float range options for csgo."""
        mock_callback_update.callback_query.data = "float_range:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"]
        
        await handle_float_range_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_error_for_non_csgo(self, mock_keyboard, mock_callback_update, mock_context):
        """Test shows error message for non-csgo games."""
        mock_callback_update.callback_query.data = "float_range:dota2"
        mock_keyboard.return_value = MagicMock()
        
        await handle_float_range_callback(mock_callback_update, mock_context)
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "только для CS2" in call_args[1]["text"]


class TestHandleSetCategoryCallback:
    """Tests for handle_set_category_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_category_options_for_csgo(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows category options for csgo."""
        mock_callback_update.callback_query.data = "set_category:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"]
        
        await handle_set_category_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_category_options_for_rust(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows category options for rust."""
        mock_callback_update.callback_query.data = "set_category:rust"
        mock_get_filters.return_value = DEFAULT_FILTERS["rust"]
        
        await handle_set_category_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()


class TestHandleSetRarityCallback:
    """Tests for handle_set_rarity_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_rarity_options_for_csgo(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows rarity options for csgo."""
        mock_callback_update.callback_query.data = "set_rarity:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"]
        
        await handle_set_rarity_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_rarity_options_for_dota2(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows rarity options for dota2."""
        mock_callback_update.callback_query.data = "set_rarity:dota2"
        mock_get_filters.return_value = DEFAULT_FILTERS["dota2"]
        
        await handle_set_rarity_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()


class TestHandleSetExteriorCallback:
    """Tests for handle_set_exterior_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_exterior_options_for_csgo(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows exterior options for csgo."""
        mock_callback_update.callback_query.data = "set_exterior:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"]
        
        await handle_set_exterior_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_error_for_non_csgo(self, mock_keyboard, mock_callback_update, mock_context):
        """Test shows error for non-csgo games."""
        mock_callback_update.callback_query.data = "set_exterior:dota2"
        mock_keyboard.return_value = MagicMock()
        
        await handle_set_exterior_callback(mock_callback_update, mock_context)
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "только для CS2" in call_args[1]["text"]


class TestHandleSetHeroCallback:
    """Tests for handle_set_hero_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_hero_options_for_dota2(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows hero options for dota2."""
        mock_callback_update.callback_query.data = "set_hero:dota2"
        mock_get_filters.return_value = DEFAULT_FILTERS["dota2"]
        
        await handle_set_hero_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_error_for_non_dota2(self, mock_keyboard, mock_callback_update, mock_context):
        """Test shows error for non-dota2 games."""
        mock_callback_update.callback_query.data = "set_hero:csgo"
        mock_keyboard.return_value = MagicMock()
        
        await handle_set_hero_callback(mock_callback_update, mock_context)
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "только для Dota 2" in call_args[1]["text"]


class TestHandleSetSlotCallback:
    """Tests for handle_set_slot_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_slot_options_for_dota2(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows slot options for dota2."""
        mock_callback_update.callback_query.data = "set_slot:dota2"
        mock_get_filters.return_value = DEFAULT_FILTERS["dota2"]
        
        await handle_set_slot_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_error_for_non_dota2(self, mock_keyboard, mock_callback_update, mock_context):
        """Test shows error for non-dota2 games."""
        mock_callback_update.callback_query.data = "set_slot:csgo"
        mock_keyboard.return_value = MagicMock()
        
        await handle_set_slot_callback(mock_callback_update, mock_context)
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "только для Dota 2" in call_args[1]["text"]


class TestHandleSetClassCallback:
    """Tests for handle_set_class_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_class_options_for_tf2(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows class options for tf2."""
        mock_callback_update.callback_query.data = "set_class:tf2"
        mock_get_filters.return_value = DEFAULT_FILTERS["tf2"]
        
        await handle_set_class_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_error_for_non_tf2(self, mock_keyboard, mock_callback_update, mock_context):
        """Test shows error for non-tf2 games."""
        mock_callback_update.callback_query.data = "set_class:csgo"
        mock_keyboard.return_value = MagicMock()
        
        await handle_set_class_callback(mock_callback_update, mock_context)
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "только для Team Fortress 2" in call_args[1]["text"]


class TestHandleSetTypeCallback:
    """Tests for handle_set_type_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_type_options_for_tf2(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows type options for tf2."""
        mock_callback_update.callback_query.data = "set_type:tf2"
        mock_get_filters.return_value = DEFAULT_FILTERS["tf2"]
        
        await handle_set_type_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_type_options_for_rust(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows type options for rust."""
        mock_callback_update.callback_query.data = "set_type:rust"
        mock_get_filters.return_value = DEFAULT_FILTERS["rust"]
        
        await handle_set_type_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()


class TestHandleSetQualityCallback:
    """Tests for handle_set_quality_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    async def test_shows_quality_options_for_tf2(self, mock_get_filters, mock_callback_update, mock_context):
        """Test shows quality options for tf2."""
        mock_callback_update.callback_query.data = "set_quality:tf2"
        mock_get_filters.return_value = DEFAULT_FILTERS["tf2"]
        
        await handle_set_quality_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_shows_error_for_non_tf2(self, mock_keyboard, mock_callback_update, mock_context):
        """Test shows error for non-tf2 games."""
        mock_callback_update.callback_query.data = "set_quality:csgo"
        mock_keyboard.return_value = MagicMock()
        
        await handle_set_quality_callback(mock_callback_update, mock_context)
        
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "только для Team Fortress 2" in call_args[1]["text"]


class TestHandleFilterValueCallback:
    """Tests for handle_filter_value_callback function."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.update_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_handles_price_range_filter(
        self, mock_keyboard, mock_description, mock_update_filters, mock_get_filters, 
        mock_callback_update, mock_context
    ):
        """Test handles price range filter."""
        mock_callback_update.callback_query.data = "filter:price_range:10:50:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"].copy()
        mock_description.return_value = "Test"
        mock_keyboard.return_value = MagicMock()
        
        await handle_filter_value_callback(mock_callback_update, mock_context)
        
        mock_update_filters.assert_called_once()
        call_args = mock_update_filters.call_args
        assert call_args[0][1] == "csgo"
        assert call_args[0][2]["min_price"] == 10.0
        assert call_args[0][2]["max_price"] == 50.0

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.update_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_handles_price_range_reset(
        self, mock_keyboard, mock_description, mock_update_filters, mock_get_filters,
        mock_callback_update, mock_context
    ):
        """Test handles price range reset."""
        mock_callback_update.callback_query.data = "filter:price_range:reset:csgo"
        mock_get_filters.return_value = {"min_price": 10.0, "max_price": 50.0}
        mock_description.return_value = "Test"
        mock_keyboard.return_value = MagicMock()
        
        await handle_filter_value_callback(mock_callback_update, mock_context)
        
        mock_update_filters.assert_called_once()
        call_args = mock_update_filters.call_args
        assert call_args[0][2]["min_price"] == DEFAULT_FILTERS["csgo"]["min_price"]
        assert call_args[0][2]["max_price"] == DEFAULT_FILTERS["csgo"]["max_price"]

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.update_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_handles_category_filter(
        self, mock_keyboard, mock_description, mock_update_filters, mock_get_filters,
        mock_callback_update, mock_context
    ):
        """Test handles category filter."""
        mock_callback_update.callback_query.data = "filter:category:Rifle:csgo"
        mock_get_filters.return_value = DEFAULT_FILTERS["csgo"].copy()
        mock_description.return_value = "Test"
        mock_keyboard.return_value = MagicMock()
        
        await handle_filter_value_callback(mock_callback_update, mock_context)
        
        mock_update_filters.assert_called_once()
        call_args = mock_update_filters.call_args
        assert call_args[0][2]["category"] == "Rifle"

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.update_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_handles_boolean_toggle_stattrak(
        self, mock_keyboard, mock_description, mock_update_filters, mock_get_filters,
        mock_callback_update, mock_context
    ):
        """Test handles boolean toggle for stattrak."""
        mock_callback_update.callback_query.data = "filter:stattrak:toggle:csgo"
        mock_get_filters.return_value = {"stattrak": False}
        mock_description.return_value = "Test"
        mock_keyboard.return_value = MagicMock()
        
        await handle_filter_value_callback(mock_callback_update, mock_context)
        
        mock_update_filters.assert_called_once()
        call_args = mock_update_filters.call_args
        assert call_args[0][2]["stattrak"] == True

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_current_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.update_filters")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_filter_description")
    @patch("src.telegram_bot.handlers.game_filters.handlers.get_game_filter_keyboard")
    async def test_handles_reset_all_filters(
        self, mock_keyboard, mock_description, mock_update_filters, mock_get_filters,
        mock_callback_update, mock_context
    ):
        """Test handles reset all filters."""
        mock_callback_update.callback_query.data = "filter:reset:all:csgo"
        mock_get_filters.return_value = {"min_price": 100.0, "stattrak": True}
        mock_description.return_value = "Test"
        mock_keyboard.return_value = MagicMock()
        
        await handle_filter_value_callback(mock_callback_update, mock_context)
        
        mock_update_filters.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_if_short_callback_data(self, mock_callback_update, mock_context):
        """Test returns early if callback data is too short."""
        mock_callback_update.callback_query.data = "filter:a:b"  # Only 3 parts
        
        await handle_filter_value_callback(mock_callback_update, mock_context)
        
        mock_callback_update.callback_query.edit_message_text.assert_not_called()


class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_all_exports_are_importable(self):
        """Test that all exports are importable."""
        from src.telegram_bot.handlers.game_filters import handlers
        
        expected_exports = [
            "handle_game_filters",
            "handle_select_game_filter_callback",
            "handle_price_range_callback",
            "handle_float_range_callback",
            "handle_set_category_callback",
            "handle_set_rarity_callback",
            "handle_set_exterior_callback",
            "handle_set_hero_callback",
            "handle_set_slot_callback",
            "handle_set_class_callback",
            "handle_set_type_callback",
            "handle_set_quality_callback",
            "handle_filter_value_callback",
        ]
        
        for name in expected_exports:
            assert hasattr(handlers, name)

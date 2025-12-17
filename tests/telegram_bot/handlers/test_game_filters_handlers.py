"""Unit tests for game filter handlers module.

Tests for Telegram bot handlers that manage game filters:
- CS2/CSGO filters (category, rarity, exterior, float range)
- Dota 2 filters (hero, rarity, slot)
- TF2 filters (class, quality, type)
- Rust filters (category, type, rarity)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Message, Update

from src.telegram_bot.handlers.game_filters.handlers import (
    handle_filter_value_callback,
    handle_float_range_callback,
    handle_game_filters,
    handle_price_range_callback,
    handle_select_game_filter_callback,
    handle_set_category_callback,
    handle_set_class_callback,
    handle_set_exterior_callback,
    handle_set_hero_callback,
    handle_set_quality_callback,
    handle_set_rarity_callback,
    handle_set_slot_callback,
    handle_set_type_callback,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_update():
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456

    # Mock callback_query
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = ""

    # Mock message
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()

    return update


@pytest.fixture()
def mock_context():
    """Create a mock CallbackContext object."""
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


# ============================================================================
# TESTS FOR handle_game_filters COMMAND
# ============================================================================


class TestHandleGameFilters:
    """Tests for handle_game_filters command handler."""

    @pytest.mark.asyncio()
    async def test_handle_game_filters_sends_keyboard(self, mock_update, mock_context):
        """Test that game filters command sends keyboard."""
        await handle_game_filters(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_kwargs = mock_update.message.reply_text.call_args.kwargs
        assert "reply_markup" in call_kwargs
        assert isinstance(call_kwargs["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio()
    async def test_handle_game_filters_message_text(self, mock_update, mock_context):
        """Test that game filters command sends correct message text."""
        await handle_game_filters(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        message_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        assert "Выберите игру" in message_text

    @pytest.mark.asyncio()
    async def test_handle_game_filters_no_message(self, mock_update, mock_context):
        """Test handler when update has no message."""
        mock_update.message = None

        # Should not raise an error
        await handle_game_filters(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_select_game_filter_callback
# ============================================================================


class TestHandleSelectGameFilterCallback:
    """Tests for game selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_select_csgo(self, mock_update, mock_context):
        """Test selecting CS:GO game."""
        mock_update.callback_query.data = "select_game_filter:csgo"

        await handle_select_game_filter_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "CS2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_select_dota2(self, mock_update, mock_context):
        """Test selecting Dota 2 game."""
        mock_update.callback_query.data = "select_game_filter:dota2"

        await handle_select_game_filter_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Dota 2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_select_tf2(self, mock_update, mock_context):
        """Test selecting TF2 game."""
        mock_update.callback_query.data = "select_game_filter:tf2"

        await handle_select_game_filter_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Team Fortress 2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_select_rust(self, mock_update, mock_context):
        """Test selecting Rust game."""
        mock_update.callback_query.data = "select_game_filter:rust"

        await handle_select_game_filter_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Rust" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_select_default_game(self, mock_update, mock_context):
        """Test handler with missing game in data."""
        mock_update.callback_query.data = "select_game_filter"

        await handle_select_game_filter_callback(mock_update, mock_context)

        # Should default to csgo
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "CS2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_select_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        # Should not raise an error
        await handle_select_game_filter_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_handle_select_no_data(self, mock_update, mock_context):
        """Test handler when callback_query has no data."""
        mock_update.callback_query.data = None

        # Should not raise an error
        await handle_select_game_filter_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_price_range_callback
# ============================================================================


class TestHandlePriceRangeCallback:
    """Tests for price range callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_price_range_csgo(self, mock_update, mock_context):
        """Test price range selection for CS:GO."""
        mock_update.callback_query.data = "price_range:csgo"

        await handle_price_range_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Настройка диапазона цен" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_price_range_shows_current_values(self, mock_update, mock_context):
        """Test that current price range is shown."""
        mock_context.user_data["filters"] = {
            "csgo": {
                "min_price": 10.0,
                "max_price": 50.0,
            }
        }
        mock_update.callback_query.data = "price_range:csgo"

        await handle_price_range_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "$10.00" in call_kwargs["text"]
        assert "$50.00" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_price_range_keyboard_has_options(self, mock_update, mock_context):
        """Test that price range keyboard has options."""
        mock_update.callback_query.data = "price_range:csgo"

        await handle_price_range_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        keyboard = call_kwargs["reply_markup"]
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0

    @pytest.mark.asyncio()
    async def test_handle_price_range_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        # Should not raise an error
        await handle_price_range_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_float_range_callback
# ============================================================================


class TestHandleFloatRangeCallback:
    """Tests for float range callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_float_range_csgo(self, mock_update, mock_context):
        """Test float range selection for CS:GO."""
        mock_update.callback_query.data = "float_range:csgo"

        await handle_float_range_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Float" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_float_range_non_csgo_rejected(self, mock_update, mock_context):
        """Test float range is rejected for non-CS:GO games."""
        mock_update.callback_query.data = "float_range:dota2"

        await handle_float_range_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Float доступен только для CS2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_float_range_shows_current_values(self, mock_update, mock_context):
        """Test that current float range is shown."""
        mock_context.user_data["filters"] = {
            "csgo": {
                "float_min": 0.0,
                "float_max": 0.07,
            }
        }
        mock_update.callback_query.data = "float_range:csgo"

        await handle_float_range_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "0.00" in call_kwargs["text"]
        assert "0.07" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_float_range_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        # Should not raise an error
        await handle_float_range_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_category_callback
# ============================================================================


class TestHandleSetCategoryCallback:
    """Tests for category selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_category_csgo(self, mock_update, mock_context):
        """Test category selection for CS:GO."""
        mock_update.callback_query.data = "set_category:csgo"

        await handle_set_category_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор категории" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_category_rust(self, mock_update, mock_context):
        """Test category selection for Rust."""
        mock_update.callback_query.data = "set_category:rust"

        await handle_set_category_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор категории" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_category_has_keyboard(self, mock_update, mock_context):
        """Test that category selection has keyboard."""
        mock_update.callback_query.data = "set_category:csgo"

        await handle_set_category_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "reply_markup" in call_kwargs
        assert isinstance(call_kwargs["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio()
    async def test_handle_set_category_shows_current(self, mock_update, mock_context):
        """Test that current category is shown."""
        mock_context.user_data["filters"] = {
            "csgo": {"category": "Rifle"}
        }
        mock_update.callback_query.data = "set_category:csgo"

        await handle_set_category_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Rifle" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_category_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_category_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_rarity_callback
# ============================================================================


class TestHandleSetRarityCallback:
    """Tests for rarity selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_rarity_csgo(self, mock_update, mock_context):
        """Test rarity selection for CS:GO."""
        mock_update.callback_query.data = "set_rarity:csgo"

        await handle_set_rarity_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор редкости" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_rarity_dota2(self, mock_update, mock_context):
        """Test rarity selection for Dota 2."""
        mock_update.callback_query.data = "set_rarity:dota2"

        await handle_set_rarity_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор редкости" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_rarity_rust(self, mock_update, mock_context):
        """Test rarity selection for Rust."""
        mock_update.callback_query.data = "set_rarity:rust"

        await handle_set_rarity_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор редкости" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_rarity_unknown_game(self, mock_update, mock_context):
        """Test rarity selection for unknown game."""
        mock_update.callback_query.data = "set_rarity:unknown"

        await handle_set_rarity_callback(mock_update, mock_context)

        # Should still work but with empty rarities
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_set_rarity_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_rarity_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_exterior_callback
# ============================================================================


class TestHandleSetExteriorCallback:
    """Tests for exterior selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_exterior_csgo(self, mock_update, mock_context):
        """Test exterior selection for CS:GO."""
        mock_update.callback_query.data = "set_exterior:csgo"

        await handle_set_exterior_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор внешнего вида" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_exterior_non_csgo_rejected(self, mock_update, mock_context):
        """Test exterior selection is rejected for non-CS:GO games."""
        mock_update.callback_query.data = "set_exterior:dota2"

        await handle_set_exterior_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "внешнего вида доступен только для CS2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_exterior_shows_current(self, mock_update, mock_context):
        """Test that current exterior is shown."""
        mock_context.user_data["filters"] = {
            "csgo": {"exterior": "Factory New"}
        }
        mock_update.callback_query.data = "set_exterior:csgo"

        await handle_set_exterior_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Factory New" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_exterior_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_exterior_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_hero_callback
# ============================================================================


class TestHandleSetHeroCallback:
    """Tests for hero selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_hero_dota2(self, mock_update, mock_context):
        """Test hero selection for Dota 2."""
        mock_update.callback_query.data = "set_hero:dota2"

        await handle_set_hero_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор героя" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_hero_non_dota2_rejected(self, mock_update, mock_context):
        """Test hero selection is rejected for non-Dota 2 games."""
        mock_update.callback_query.data = "set_hero:csgo"

        await handle_set_hero_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "героя доступен только для Dota 2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_hero_shows_current(self, mock_update, mock_context):
        """Test that current hero is shown."""
        mock_context.user_data["filters"] = {
            "dota2": {"hero": "Pudge"}
        }
        mock_update.callback_query.data = "set_hero:dota2"

        await handle_set_hero_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Pudge" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_hero_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_hero_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_slot_callback
# ============================================================================


class TestHandleSetSlotCallback:
    """Tests for slot selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_slot_dota2(self, mock_update, mock_context):
        """Test slot selection for Dota 2."""
        mock_update.callback_query.data = "set_slot:dota2"

        await handle_set_slot_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор слота" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_slot_non_dota2_rejected(self, mock_update, mock_context):
        """Test slot selection is rejected for non-Dota 2 games."""
        mock_update.callback_query.data = "set_slot:csgo"

        await handle_set_slot_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "слота доступен только для Dota 2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_slot_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_slot_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_class_callback
# ============================================================================


class TestHandleSetClassCallback:
    """Tests for class selection callback handler (TF2)."""

    @pytest.mark.asyncio()
    async def test_handle_set_class_tf2(self, mock_update, mock_context):
        """Test class selection for TF2."""
        mock_update.callback_query.data = "set_class:tf2"

        await handle_set_class_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор класса" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_class_non_tf2_rejected(self, mock_update, mock_context):
        """Test class selection is rejected for non-TF2 games."""
        mock_update.callback_query.data = "set_class:csgo"

        await handle_set_class_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "класса доступен только для Team Fortress 2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_class_shows_current(self, mock_update, mock_context):
        """Test that current class is shown."""
        mock_context.user_data["filters"] = {
            "tf2": {"class": "Scout"}
        }
        mock_update.callback_query.data = "set_class:tf2"

        await handle_set_class_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Scout" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_class_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_class_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_type_callback
# ============================================================================


class TestHandleSetTypeCallback:
    """Tests for type selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_type_tf2(self, mock_update, mock_context):
        """Test type selection for TF2."""
        mock_update.callback_query.data = "set_type:tf2"

        await handle_set_type_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор типа" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_type_rust(self, mock_update, mock_context):
        """Test type selection for Rust."""
        mock_update.callback_query.data = "set_type:rust"

        await handle_set_type_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор типа" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_type_unknown_game(self, mock_update, mock_context):
        """Test type selection for unknown game."""
        mock_update.callback_query.data = "set_type:unknown"

        await handle_set_type_callback(mock_update, mock_context)

        # Should still work but with empty types
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_set_type_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_type_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_set_quality_callback
# ============================================================================


class TestHandleSetQualityCallback:
    """Tests for quality selection callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_set_quality_tf2(self, mock_update, mock_context):
        """Test quality selection for TF2."""
        mock_update.callback_query.data = "set_quality:tf2"

        await handle_set_quality_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "Выбор качества" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_quality_non_tf2_rejected(self, mock_update, mock_context):
        """Test quality selection is rejected for non-TF2 games."""
        mock_update.callback_query.data = "set_quality:csgo"

        await handle_set_quality_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert "качества доступен только для Team Fortress 2" in call_kwargs["text"]

    @pytest.mark.asyncio()
    async def test_handle_set_quality_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_set_quality_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR handle_filter_value_callback
# ============================================================================


class TestHandleFilterValueCallback:
    """Tests for filter value callback handler."""

    @pytest.mark.asyncio()
    async def test_handle_filter_value_price_range(self, mock_update, mock_context):
        """Test setting price range filter."""
        mock_update.callback_query.data = "filter:price_range:10:50:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("min_price") == 10.0
        assert filters.get("max_price") == 50.0

    @pytest.mark.asyncio()
    async def test_handle_filter_value_price_range_reset(self, mock_update, mock_context):
        """Test resetting price range filter."""
        mock_context.user_data["filters"] = {
            "csgo": {
                "min_price": 10.0,
                "max_price": 50.0,
            }
        }
        mock_update.callback_query.data = "filter:price_range:reset:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        # Should be reset to defaults
        assert filters.get("min_price") == 1.0
        assert filters.get("max_price") == 1000.0

    @pytest.mark.asyncio()
    async def test_handle_filter_value_float_range(self, mock_update, mock_context):
        """Test setting float range filter."""
        mock_update.callback_query.data = "filter:float_range:0.00:0.07:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("float_min") == 0.00
        assert filters.get("float_max") == 0.07

    @pytest.mark.asyncio()
    async def test_handle_filter_value_float_range_reset(self, mock_update, mock_context):
        """Test resetting float range filter."""
        mock_context.user_data["filters"] = {
            "csgo": {
                "float_min": 0.00,
                "float_max": 0.07,
            }
        }
        mock_update.callback_query.data = "filter:float_range:reset:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("float_min") == 0.0
        assert filters.get("float_max") == 1.0

    @pytest.mark.asyncio()
    async def test_handle_filter_value_category(self, mock_update, mock_context):
        """Test setting category filter."""
        mock_update.callback_query.data = "filter:category:Rifle:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("category") == "Rifle"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_category_reset(self, mock_update, mock_context):
        """Test resetting category filter."""
        mock_context.user_data["filters"] = {
            "csgo": {"category": "Rifle"}
        }
        mock_update.callback_query.data = "filter:category:reset:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("category") is None

    @pytest.mark.asyncio()
    async def test_handle_filter_value_rarity(self, mock_update, mock_context):
        """Test setting rarity filter."""
        mock_update.callback_query.data = "filter:rarity:Covert:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("rarity") == "Covert"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_exterior(self, mock_update, mock_context):
        """Test setting exterior filter."""
        mock_update.callback_query.data = "filter:exterior:Factory New:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("exterior") == "Factory New"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_hero(self, mock_update, mock_context):
        """Test setting hero filter."""
        mock_update.callback_query.data = "filter:hero:Pudge:dota2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("dota2", {})
        assert filters.get("hero") == "Pudge"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_slot(self, mock_update, mock_context):
        """Test setting slot filter."""
        mock_update.callback_query.data = "filter:slot:Weapon:dota2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("dota2", {})
        assert filters.get("slot") == "Weapon"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_class(self, mock_update, mock_context):
        """Test setting class filter."""
        mock_update.callback_query.data = "filter:class:Scout:tf2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("tf2", {})
        assert filters.get("class") == "Scout"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_type(self, mock_update, mock_context):
        """Test setting type filter."""
        mock_update.callback_query.data = "filter:type:Hat:tf2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("tf2", {})
        assert filters.get("type") == "Hat"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_quality(self, mock_update, mock_context):
        """Test setting quality filter."""
        mock_update.callback_query.data = "filter:quality:Strange:tf2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("tf2", {})
        assert filters.get("quality") == "Strange"

    @pytest.mark.asyncio()
    async def test_handle_filter_value_stattrak_toggle(self, mock_update, mock_context):
        """Test toggling StatTrak filter."""
        mock_context.user_data["filters"] = {
            "csgo": {"stattrak": False}
        }
        mock_update.callback_query.data = "filter:stattrak:toggle:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("stattrak") is True

    @pytest.mark.asyncio()
    async def test_handle_filter_value_souvenir_toggle(self, mock_update, mock_context):
        """Test toggling Souvenir filter."""
        mock_context.user_data["filters"] = {
            "csgo": {"souvenir": False}
        }
        mock_update.callback_query.data = "filter:souvenir:toggle:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        assert filters.get("souvenir") is True

    @pytest.mark.asyncio()
    async def test_handle_filter_value_tradable_toggle(self, mock_update, mock_context):
        """Test toggling tradable filter."""
        mock_context.user_data["filters"] = {
            "dota2": {"tradable": True}
        }
        mock_update.callback_query.data = "filter:tradable:toggle:dota2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("dota2", {})
        assert filters.get("tradable") is False

    @pytest.mark.asyncio()
    async def test_handle_filter_value_australium_toggle(self, mock_update, mock_context):
        """Test toggling Australium filter."""
        mock_context.user_data["filters"] = {
            "tf2": {"australium": False}
        }
        mock_update.callback_query.data = "filter:australium:toggle:tf2"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("tf2", {})
        assert filters.get("australium") is True

    @pytest.mark.asyncio()
    async def test_handle_filter_value_reset_all(self, mock_update, mock_context):
        """Test resetting all filters."""
        mock_context.user_data["filters"] = {
            "csgo": {
                "category": "Rifle",
                "rarity": "Covert",
                "min_price": 50.0,
            }
        }
        mock_update.callback_query.data = "filter:reset:all:csgo"

        await handle_filter_value_callback(mock_update, mock_context)

        filters = mock_context.user_data.get("filters", {}).get("csgo", {})
        # Should have default values
        assert filters.get("min_price") == 1.0

    @pytest.mark.asyncio()
    async def test_handle_filter_value_insufficient_data(self, mock_update, mock_context):
        """Test handler with insufficient data parts."""
        mock_update.callback_query.data = "filter:invalid"

        # Should not raise an error
        await handle_filter_value_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_handle_filter_value_no_query(self, mock_update, mock_context):
        """Test handler when callback_query is None."""
        mock_update.callback_query = None

        await handle_filter_value_callback(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_handle_filter_value_no_data(self, mock_update, mock_context):
        """Test handler when callback_query has no data."""
        mock_update.callback_query.data = None

        await handle_filter_value_callback(mock_update, mock_context)


# ============================================================================
# TESTS FOR __all__ EXPORTS
# ============================================================================


class TestModuleExports:
    """Tests for module exports."""

    def test_all_handlers_exported(self):
        """Test that all handlers are exported."""
        from src.telegram_bot.handlers.game_filters.handlers import __all__

        expected_exports = [
            "handle_filter_value_callback",
            "handle_float_range_callback",
            "handle_game_filters",
            "handle_price_range_callback",
            "handle_select_game_filter_callback",
            "handle_set_category_callback",
            "handle_set_class_callback",
            "handle_set_exterior_callback",
            "handle_set_hero_callback",
            "handle_set_quality_callback",
            "handle_set_rarity_callback",
            "handle_set_slot_callback",
            "handle_set_type_callback",
        ]

        for handler in expected_exports:
            assert handler in __all__

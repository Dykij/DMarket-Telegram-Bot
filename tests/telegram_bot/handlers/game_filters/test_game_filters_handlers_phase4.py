"""
Phase 4 unit tests for game_filters/handlers.py module.

This module contains extended tests for:
- handle_game_filters command
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
- Edge cases and integration tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHandleGameFilters:
    """Tests for handle_game_filters function."""

    @pytest.mark.asyncio
    async def test_no_message(self) -> None:
        """Test returns early when no message."""
        from src.telegram_bot.handlers.game_filters.handlers import handle_game_filters

        update = MagicMock()
        update.message = None
        context = MagicMock()

        await handle_game_filters(update, context)

        # Should not call any message methods
        assert update.message is None

    @pytest.mark.asyncio
    async def test_sends_game_selection_keyboard(self) -> None:
        """Test sends keyboard with game options."""
        from src.telegram_bot.handlers.game_filters.handlers import handle_game_filters

        update = MagicMock()
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        await handle_game_filters(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Выберите игру для настройки фильтров" in call_args[0][0]
        assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_keyboard_contains_all_games(self) -> None:
        """Test keyboard contains all game options."""
        from src.telegram_bot.handlers.game_filters.handlers import handle_game_filters

        update = MagicMock()
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        await handle_game_filters(update, context)

        call_args = update.message.reply_text.call_args
        reply_markup = call_args[1]["reply_markup"]

        # Collect all callback data
        callback_data = []
        for row in reply_markup.inline_keyboard:
            for button in row:
                callback_data.append(button.callback_data)

        assert "select_game_filter:csgo" in callback_data
        assert "select_game_filter:dota2" in callback_data
        assert "select_game_filter:tf2" in callback_data
        assert "select_game_filter:rust" in callback_data


class TestHandleSelectGameFilterCallback:
    """Tests for handle_select_game_filter_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_select_game_filter_callback(update, context)

    @pytest.mark.asyncio
    async def test_no_query_data(self) -> None:
        """Test returns early when no query data."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = None
        context = MagicMock()

        await handle_select_game_filter_callback(update, context)

    @pytest.mark.asyncio
    async def test_selects_csgo_game(self) -> None:
        """Test selects CSGO game."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "select_game_filter:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_select_game_filter_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "CS2" in call_args[1]["text"] or "CS" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_selects_dota2_game(self) -> None:
        """Test selects Dota 2 game."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "select_game_filter:dota2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_select_game_filter_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_selects_tf2_game(self) -> None:
        """Test selects TF2 game."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "select_game_filter:tf2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_select_game_filter_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_selects_rust_game(self) -> None:
        """Test selects Rust game."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "select_game_filter:rust"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_select_game_filter_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_default_game_when_missing(self) -> None:
        """Test defaults to csgo when game not specified."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "select_game_filter"  # No game specified
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_select_game_filter_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()


class TestHandlePriceRangeCallback:
    """Tests for handle_price_range_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_price_range_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_price_range_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_price_range_options(self) -> None:
        """Test shows price range options."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_price_range_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "price_range:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_price_range_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "цен" in call_args[1]["text"].lower()


class TestHandleFloatRangeCallback:
    """Tests for handle_float_range_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_float_range_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_float_range_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_float_range_for_csgo(self) -> None:
        """Test shows float range options for CSGO."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_float_range_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "float_range:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_float_range_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "float" in call_args[1]["text"].lower()

    @pytest.mark.asyncio
    async def test_rejects_float_for_non_csgo(self) -> None:
        """Test rejects float range for non-CSGO games."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_float_range_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "float_range:dota2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_float_range_callback(update, context)

        call_args = query.edit_message_text.call_args
        assert "только для cs2" in call_args[1]["text"].lower()


class TestHandleSetCategoryCallback:
    """Tests for handle_set_category_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_category_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_category_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_csgo_categories(self) -> None:
        """Test shows CSGO categories."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_category_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_category:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_category_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "категори" in call_args[1]["text"].lower()


class TestHandleSetRarityCallback:
    """Tests for handle_set_rarity_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_rarity_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_rarity_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_csgo_rarities(self) -> None:
        """Test shows CSGO rarities."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_rarity_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_rarity:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_rarity_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()


class TestHandleSetExteriorCallback:
    """Tests for handle_set_exterior_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_exterior_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_exterior_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_exterior_for_csgo(self) -> None:
        """Test shows exterior options for CSGO."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_exterior_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_exterior:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_exterior_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_exterior_for_non_csgo(self) -> None:
        """Test rejects exterior for non-CSGO games."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_exterior_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_exterior:dota2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_exterior_callback(update, context)

        call_args = query.edit_message_text.call_args
        assert "только для cs2" in call_args[1]["text"].lower()


class TestHandleSetHeroCallback:
    """Tests for handle_set_hero_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_hero_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_hero_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_heroes_for_dota2(self) -> None:
        """Test shows hero options for Dota 2."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_hero_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_hero:dota2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_hero_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_hero_for_non_dota2(self) -> None:
        """Test rejects hero for non-Dota 2 games."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_hero_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_hero:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_hero_callback(update, context)

        call_args = query.edit_message_text.call_args
        assert "только для dota 2" in call_args[1]["text"].lower()


class TestHandleSetSlotCallback:
    """Tests for handle_set_slot_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_slot_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_slot_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_slots_for_dota2(self) -> None:
        """Test shows slot options for Dota 2."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_slot_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_slot:dota2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_slot_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_slot_for_non_dota2(self) -> None:
        """Test rejects slot for non-Dota 2 games."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_slot_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_slot:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_slot_callback(update, context)

        call_args = query.edit_message_text.call_args
        assert "только для dota 2" in call_args[1]["text"].lower()


class TestHandleSetClassCallback:
    """Tests for handle_set_class_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_class_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_class_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_classes_for_tf2(self) -> None:
        """Test shows class options for TF2."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_class_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_class:tf2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_class_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_class_for_non_tf2(self) -> None:
        """Test rejects class for non-TF2 games."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_class_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_class:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_class_callback(update, context)

        call_args = query.edit_message_text.call_args
        assert "team fortress 2" in call_args[1]["text"].lower()


class TestHandleSetTypeCallback:
    """Tests for handle_set_type_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_type_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_type_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_types_for_tf2(self) -> None:
        """Test shows type options for TF2."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_type_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_type:tf2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_type_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_shows_types_for_rust(self) -> None:
        """Test shows type options for Rust."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_type_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_type:rust"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_type_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()


class TestHandleSetQualityCallback:
    """Tests for handle_set_quality_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_quality_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_set_quality_callback(update, context)

    @pytest.mark.asyncio
    async def test_shows_qualities_for_tf2(self) -> None:
        """Test shows quality options for TF2."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_quality_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_quality:tf2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_quality_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_quality_for_non_tf2(self) -> None:
        """Test rejects quality for non-TF2 games."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_set_quality_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "set_quality:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_set_quality_callback(update, context)

        call_args = query.edit_message_text.call_args
        assert "team fortress 2" in call_args[1]["text"].lower()


class TestHandleFilterValueCallback:
    """Tests for handle_filter_value_callback function."""

    @pytest.mark.asyncio
    async def test_no_query(self) -> None:
        """Test returns early when no query."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_filter_value_callback,
        )

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        await handle_filter_value_callback(update, context)

    @pytest.mark.asyncio
    async def test_insufficient_data(self) -> None:
        """Test returns early when insufficient data."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_filter_value_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "filter:rarity"  # Missing value and game
        query.answer = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_filter_value_callback(update, context)

    @pytest.mark.asyncio
    async def test_sets_price_range(self) -> None:
        """Test sets price range filter."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_filter_value_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "filter:price_range:10:50:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_filter_value_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        # Check filters were updated
        assert context.user_data.get("filters", {}).get("csgo", {}).get("min_price") == 10.0
        assert context.user_data.get("filters", {}).get("csgo", {}).get("max_price") == 50.0

    @pytest.mark.asyncio
    async def test_sets_category_filter(self) -> None:
        """Test sets category filter."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_filter_value_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "filter:category:Knife:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {}

        await handle_filter_value_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        assert context.user_data.get("filters", {}).get("csgo", {}).get("category") == "Knife"

    @pytest.mark.asyncio
    async def test_resets_category_filter(self) -> None:
        """Test resets category filter."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_filter_value_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "filter:category:reset:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {"category": "Knife"}}}

        await handle_filter_value_callback(update, context)

        assert context.user_data.get("filters", {}).get("csgo", {}).get("category") is None

    @pytest.mark.asyncio
    async def test_toggles_stattrak_filter(self) -> None:
        """Test toggles StatTrak filter."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_filter_value_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "filter:stattrak:toggle:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {"stattrak": False}}}

        await handle_filter_value_callback(update, context)

        assert context.user_data.get("filters", {}).get("csgo", {}).get("stattrak") is True


class TestEdgeCases:
    """Edge case tests for game_filters/handlers.py module."""

    @pytest.mark.asyncio
    async def test_empty_user_data(self) -> None:
        """Test handles empty user_data."""
        from src.telegram_bot.handlers.game_filters.handlers import (
            handle_select_game_filter_callback,
        )

        update = MagicMock()
        query = AsyncMock()
        query.data = "select_game_filter:csgo"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query

        context = MagicMock()
        context.user_data = None

        await handle_select_game_filter_callback(update, context)

        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()


class TestConstantsValidation:
    """Tests for constants validation in game_filters module."""

    def test_cs2_categories_exist(self) -> None:
        """Test CS2 categories are defined."""
        from src.telegram_bot.handlers.game_filters.constants import CS2_CATEGORIES

        assert len(CS2_CATEGORIES) > 0
        assert "Knife" in CS2_CATEGORIES
        assert "Rifle" in CS2_CATEGORIES

    def test_cs2_rarities_exist(self) -> None:
        """Test CS2 rarities are defined."""
        from src.telegram_bot.handlers.game_filters.constants import CS2_RARITIES

        assert len(CS2_RARITIES) > 0
        assert "Covert" in CS2_RARITIES

    def test_cs2_exteriors_exist(self) -> None:
        """Test CS2 exteriors are defined."""
        from src.telegram_bot.handlers.game_filters.constants import CS2_EXTERIORS

        assert len(CS2_EXTERIORS) == 5
        assert "Factory New" in CS2_EXTERIORS
        assert "Battle-Scarred" in CS2_EXTERIORS

    def test_dota2_heroes_exist(self) -> None:
        """Test Dota 2 heroes are defined."""
        from src.telegram_bot.handlers.game_filters.constants import DOTA2_HEROES

        assert len(DOTA2_HEROES) > 0
        assert "Axe" in DOTA2_HEROES

    def test_dota2_slots_exist(self) -> None:
        """Test Dota 2 slots are defined."""
        from src.telegram_bot.handlers.game_filters.constants import DOTA2_SLOTS

        assert len(DOTA2_SLOTS) > 0
        assert "Weapon" in DOTA2_SLOTS

    def test_tf2_classes_exist(self) -> None:
        """Test TF2 classes are defined."""
        from src.telegram_bot.handlers.game_filters.constants import TF2_CLASSES

        assert len(TF2_CLASSES) > 0
        assert "Scout" in TF2_CLASSES
        assert "Spy" in TF2_CLASSES

    def test_tf2_qualities_exist(self) -> None:
        """Test TF2 qualities are defined."""
        from src.telegram_bot.handlers.game_filters.constants import TF2_QUALITIES

        assert len(TF2_QUALITIES) > 0
        assert "Unusual" in TF2_QUALITIES

    def test_rust_categories_exist(self) -> None:
        """Test Rust categories are defined."""
        from src.telegram_bot.handlers.game_filters.constants import RUST_CATEGORIES

        assert len(RUST_CATEGORIES) > 0
        assert "Weapon" in RUST_CATEGORIES

    def test_default_filters_for_all_games(self) -> None:
        """Test default filters exist for all games."""
        from src.telegram_bot.handlers.game_filters.constants import DEFAULT_FILTERS

        assert "csgo" in DEFAULT_FILTERS
        assert "dota2" in DEFAULT_FILTERS
        assert "tf2" in DEFAULT_FILTERS
        assert "rust" in DEFAULT_FILTERS

    def test_game_names_exist(self) -> None:
        """Test game names are defined."""
        from src.telegram_bot.handlers.game_filters.constants import GAME_NAMES

        assert "csgo" in GAME_NAMES
        assert "dota2" in GAME_NAMES
        assert "tf2" in GAME_NAMES
        assert "rust" in GAME_NAMES


class TestUtilsFunctions:
    """Tests for utils functions in game_filters module."""

    def test_get_current_filters_empty_context(self) -> None:
        """Test get_current_filters with empty context."""
        from src.telegram_bot.handlers.game_filters.utils import get_current_filters

        context = MagicMock()
        context.user_data = None

        filters = get_current_filters(context, "csgo")

        assert isinstance(filters, dict)
        assert "min_price" in filters

    def test_get_current_filters_with_existing_filters(self) -> None:
        """Test get_current_filters with existing filters."""
        from src.telegram_bot.handlers.game_filters.utils import get_current_filters

        context = MagicMock()
        context.user_data = {"filters": {"csgo": {"min_price": 50.0}}}

        filters = get_current_filters(context, "csgo")

        assert filters.get("min_price") == 50.0

    def test_update_filters(self) -> None:
        """Test update_filters function."""
        from src.telegram_bot.handlers.game_filters.utils import update_filters

        context = MagicMock()
        context.user_data = {}

        update_filters(context, "csgo", {"min_price": 100.0})

        assert context.user_data.get("filters", {}).get("csgo", {}).get("min_price") == 100.0

    def test_get_game_filter_keyboard_csgo(self) -> None:
        """Test get_game_filter_keyboard for CSGO."""
        from src.telegram_bot.handlers.game_filters.utils import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("csgo")

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0

    def test_get_game_filter_keyboard_dota2(self) -> None:
        """Test get_game_filter_keyboard for Dota 2."""
        from src.telegram_bot.handlers.game_filters.utils import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("dota2")

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0

    def test_get_game_filter_keyboard_tf2(self) -> None:
        """Test get_game_filter_keyboard for TF2."""
        from src.telegram_bot.handlers.game_filters.utils import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("tf2")

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0

    def test_get_game_filter_keyboard_rust(self) -> None:
        """Test get_game_filter_keyboard for Rust."""
        from src.telegram_bot.handlers.game_filters.utils import get_game_filter_keyboard

        keyboard = get_game_filter_keyboard("rust")

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0

    def test_get_filter_description(self) -> None:
        """Test get_filter_description function."""
        from src.telegram_bot.handlers.game_filters.utils import get_filter_description

        filters = {"min_price": 10.0, "max_price": 100.0, "category": "Knife"}

        description = get_filter_description("csgo", filters)

        assert isinstance(description, str)

    def test_build_api_params_for_game(self) -> None:
        """Test build_api_params_for_game function."""
        from src.telegram_bot.handlers.game_filters.utils import build_api_params_for_game

        filters = {"min_price": 10.0, "max_price": 100.0}

        params = build_api_params_for_game("csgo", filters)

        assert isinstance(params, dict)

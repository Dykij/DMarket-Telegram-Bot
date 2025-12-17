"""Unit tests for game_filters utils module.

Tests for get_current_filters, update_filters, get_game_filter_keyboard,
get_filter_description, and build_api_params_for_game functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.telegram_bot.handlers.game_filters.utils import (
    get_current_filters,
    update_filters,
    get_game_filter_keyboard,
    get_filter_description,
    build_api_params_for_game,
)


class TestGetCurrentFilters:
    """Tests for get_current_filters function."""

    def test_get_filters_without_user_data(self):
        """Test getting filters when user_data is None."""
        mock_context = MagicMock()
        mock_context.user_data = None

        result = get_current_filters(mock_context, "csgo")

        assert isinstance(result, dict)

    def test_get_filters_with_empty_user_data(self):
        """Test getting filters when user_data is empty dict."""
        mock_context = MagicMock()
        mock_context.user_data = {}

        result = get_current_filters(mock_context, "csgo")

        assert isinstance(result, dict)

    def test_get_filters_with_no_game_filters(self):
        """Test getting filters when game filters not set."""
        mock_context = MagicMock()
        mock_context.user_data = {"filters": {}}

        result = get_current_filters(mock_context, "dota2")

        assert isinstance(result, dict)

    def test_get_filters_returns_game_filters(self):
        """Test getting existing game filters."""
        mock_context = MagicMock()
        mock_context.user_data = {
            "filters": {
                "csgo": {"price_min": 10, "price_max": 100},
            },
        }

        result = get_current_filters(mock_context, "csgo")

        assert result == {"price_min": 10, "price_max": 100}

    def test_get_filters_returns_copy(self):
        """Test that get_current_filters returns a copy."""
        mock_context = MagicMock()
        original_filters = {"price_min": 5}
        mock_context.user_data = {
            "filters": {
                "csgo": original_filters,
            },
        }

        result = get_current_filters(mock_context, "csgo")
        result["price_min"] = 999

        # Original should not be modified
        assert mock_context.user_data["filters"]["csgo"]["price_min"] == 5

    def test_get_filters_for_different_games(self):
        """Test getting filters for different games."""
        mock_context = MagicMock()
        mock_context.user_data = {
            "filters": {
                "csgo": {"category": "rifle"},
                "dota2": {"hero": "Pudge"},
                "tf2": {"class": "Scout"},
                "rust": {"type": "weapon"},
            },
        }

        csgo_result = get_current_filters(mock_context, "csgo")
        dota2_result = get_current_filters(mock_context, "dota2")
        tf2_result = get_current_filters(mock_context, "tf2")
        rust_result = get_current_filters(mock_context, "rust")

        assert csgo_result == {"category": "rifle"}
        assert dota2_result == {"hero": "Pudge"}
        assert tf2_result == {"class": "Scout"}
        assert rust_result == {"type": "weapon"}


class TestUpdateFilters:
    """Tests for update_filters function."""

    def test_update_filters_creates_user_data(self):
        """Test that update_filters creates user_data if needed."""
        mock_context = MagicMock()
        mock_context.user_data = None

        update_filters(mock_context, "csgo", {"price_min": 10})

        # Function should handle None user_data

    def test_update_filters_creates_filters_dict(self):
        """Test that update_filters creates filters dict if needed."""
        mock_context = MagicMock()
        mock_context.user_data = {}

        update_filters(mock_context, "csgo", {"price_min": 10})

        assert "filters" in mock_context.user_data
        assert mock_context.user_data["filters"]["csgo"] == {"price_min": 10}

    def test_update_filters_updates_existing(self):
        """Test updating existing filters."""
        mock_context = MagicMock()
        mock_context.user_data = {
            "filters": {
                "csgo": {"price_min": 5},
            },
        }

        update_filters(mock_context, "csgo", {"price_min": 10, "price_max": 100})

        assert mock_context.user_data["filters"]["csgo"] == {
            "price_min": 10,
            "price_max": 100,
        }

    def test_update_filters_preserves_other_games(self):
        """Test that updating one game doesn't affect others."""
        mock_context = MagicMock()
        mock_context.user_data = {
            "filters": {
                "csgo": {"price_min": 5},
                "dota2": {"hero": "Pudge"},
            },
        }

        update_filters(mock_context, "csgo", {"price_min": 100})

        assert mock_context.user_data["filters"]["dota2"] == {"hero": "Pudge"}

    def test_update_filters_for_new_game(self):
        """Test adding filters for a new game."""
        mock_context = MagicMock()
        mock_context.user_data = {
            "filters": {
                "csgo": {"price_min": 5},
            },
        }

        update_filters(mock_context, "rust", {"type": "weapon"})

        assert mock_context.user_data["filters"]["rust"] == {"type": "weapon"}
        assert mock_context.user_data["filters"]["csgo"] == {"price_min": 5}


class TestGetGameFilterKeyboard:
    """Tests for get_game_filter_keyboard function."""

    def test_keyboard_for_csgo(self):
        """Test keyboard generation for CS:GO."""
        result = get_game_filter_keyboard("csgo")

        # Should return InlineKeyboardMarkup
        assert result is not None
        assert hasattr(result, "inline_keyboard")

        # Convert to text for checking
        buttons_text = []
        for row in result.inline_keyboard:
            for btn in row:
                buttons_text.append(btn.text)

        # Should have CS:GO specific buttons
        assert "💰 Диапазон цен" in buttons_text
        assert "🔢 Диапазон Float" in buttons_text
        assert "🔫 Категория" in buttons_text
        assert "⭐ Редкость" in buttons_text
        assert "🧩 Внешний вид" in buttons_text

    def test_keyboard_for_dota2(self):
        """Test keyboard generation for Dota 2."""
        result = get_game_filter_keyboard("dota2")

        buttons_text = []
        for row in result.inline_keyboard:
            for btn in row:
                buttons_text.append(btn.text)

        # Should have Dota 2 specific buttons
        assert "💰 Диапазон цен" in buttons_text
        assert "🦸 Герой" in buttons_text
        assert "⭐ Редкость" in buttons_text
        assert "🧩 Слот" in buttons_text

    def test_keyboard_for_tf2(self):
        """Test keyboard generation for TF2."""
        result = get_game_filter_keyboard("tf2")

        buttons_text = []
        for row in result.inline_keyboard:
            for btn in row:
                buttons_text.append(btn.text)

        # Should have TF2 specific buttons
        assert "💰 Диапазон цен" in buttons_text
        assert "👤 Класс" in buttons_text
        assert "🔫 Тип" in buttons_text

    def test_keyboard_for_rust(self):
        """Test keyboard generation for Rust."""
        result = get_game_filter_keyboard("rust")

        buttons_text = []
        for row in result.inline_keyboard:
            for btn in row:
                buttons_text.append(btn.text)

        # Should have Rust specific buttons
        assert "💰 Диапазон цен" in buttons_text
        assert "🔫 Категория" in buttons_text
        assert "🧩 Тип" in buttons_text

    def test_keyboard_has_reset_button(self):
        """Test that all keyboards have reset button."""
        for game in ["csgo", "dota2", "tf2", "rust"]:
            result = get_game_filter_keyboard(game)

            buttons_text = []
            for row in result.inline_keyboard:
                for btn in row:
                    buttons_text.append(btn.text)

            assert "🔄 Сбросить фильтры" in buttons_text

    def test_keyboard_has_back_button(self):
        """Test that all keyboards have back button."""
        for game in ["csgo", "dota2", "tf2", "rust"]:
            result = get_game_filter_keyboard(game)

            buttons_text = []
            for row in result.inline_keyboard:
                for btn in row:
                    buttons_text.append(btn.text)

            assert "⬅️ Назад" in buttons_text

    def test_keyboard_callback_data_contains_game(self):
        """Test that callback data contains game identifier."""
        result = get_game_filter_keyboard("csgo")

        callback_data = []
        for row in result.inline_keyboard:
            for btn in row:
                callback_data.append(btn.callback_data)

        # At least one callback should contain the game
        assert any("csgo" in data for data in callback_data)


class TestGetFilterDescription:
    """Tests for get_filter_description function."""

    @patch("src.telegram_bot.handlers.game_filters.utils.FilterFactory")
    def test_get_filter_description_calls_factory(self, mock_factory):
        """Test that function calls FilterFactory."""
        mock_filter = MagicMock()
        mock_filter.get_filter_description.return_value = "Test description"
        mock_factory.get_filter.return_value = mock_filter

        filters = {"price_min": 10}
        result = get_filter_description("csgo", filters)

        mock_factory.get_filter.assert_called_once_with("csgo")
        mock_filter.get_filter_description.assert_called_once_with(filters)
        assert result == "Test description"

    @patch("src.telegram_bot.handlers.game_filters.utils.FilterFactory")
    def test_get_filter_description_empty_filters(self, mock_factory):
        """Test function with empty filters."""
        mock_filter = MagicMock()
        mock_filter.get_filter_description.return_value = ""
        mock_factory.get_filter.return_value = mock_filter

        result = get_filter_description("dota2", {})

        assert result == ""

    @patch("src.telegram_bot.handlers.game_filters.utils.FilterFactory")
    def test_get_filter_description_for_different_games(self, mock_factory):
        """Test function with different games."""
        mock_filter = MagicMock()
        mock_filter.get_filter_description.return_value = "Description"
        mock_factory.get_filter.return_value = mock_filter

        for game in ["csgo", "dota2", "tf2", "rust"]:
            get_filter_description(game, {})
            mock_factory.get_filter.assert_called_with(game)


class TestBuildApiParamsForGame:
    """Tests for build_api_params_for_game function."""

    @patch("src.telegram_bot.handlers.game_filters.utils.FilterFactory")
    def test_build_api_params_calls_factory(self, mock_factory):
        """Test that function calls FilterFactory."""
        mock_filter = MagicMock()
        mock_filter.build_api_params.return_value = {"param1": "value1"}
        mock_factory.get_filter.return_value = mock_filter

        filters = {"price_min": 10}
        result = build_api_params_for_game("csgo", filters)

        mock_factory.get_filter.assert_called_once_with("csgo")
        mock_filter.build_api_params.assert_called_once_with(filters)
        assert result == {"param1": "value1"}

    @patch("src.telegram_bot.handlers.game_filters.utils.FilterFactory")
    def test_build_api_params_empty_filters(self, mock_factory):
        """Test function with empty filters."""
        mock_filter = MagicMock()
        mock_filter.build_api_params.return_value = {}
        mock_factory.get_filter.return_value = mock_filter

        result = build_api_params_for_game("tf2", {})

        assert result == {}

    @patch("src.telegram_bot.handlers.game_filters.utils.FilterFactory")
    def test_build_api_params_for_different_games(self, mock_factory):
        """Test function with different games."""
        mock_filter = MagicMock()
        mock_filter.build_api_params.return_value = {}
        mock_factory.get_filter.return_value = mock_filter

        for game in ["csgo", "dota2", "tf2", "rust"]:
            build_api_params_for_game(game, {})
            mock_factory.get_filter.assert_called_with(game)


class TestKeyboardCallbackData:
    """Tests for keyboard callback data formatting."""

    def test_csgo_keyboard_callback_data_format(self):
        """Test CS:GO keyboard callback data format."""
        result = get_game_filter_keyboard("csgo")

        callback_data = []
        for row in result.inline_keyboard:
            for btn in row:
                callback_data.append(btn.callback_data)

        # Check specific callback data format
        assert "price_range:csgo" in callback_data
        assert "float_range:csgo" in callback_data
        assert "set_category:csgo" in callback_data
        assert "set_rarity:csgo" in callback_data
        assert "set_exterior:csgo" in callback_data

    def test_dota2_keyboard_callback_data_format(self):
        """Test Dota 2 keyboard callback data format."""
        result = get_game_filter_keyboard("dota2")

        callback_data = []
        for row in result.inline_keyboard:
            for btn in row:
                callback_data.append(btn.callback_data)

        assert "price_range:dota2" in callback_data
        assert "set_hero:dota2" in callback_data
        assert "set_rarity:dota2" in callback_data
        assert "set_slot:dota2" in callback_data

    def test_tf2_keyboard_callback_data_format(self):
        """Test TF2 keyboard callback data format."""
        result = get_game_filter_keyboard("tf2")

        callback_data = []
        for row in result.inline_keyboard:
            for btn in row:
                callback_data.append(btn.callback_data)

        assert "price_range:tf2" in callback_data
        assert "set_class:tf2" in callback_data
        assert "set_type:tf2" in callback_data

    def test_rust_keyboard_callback_data_format(self):
        """Test Rust keyboard callback data format."""
        result = get_game_filter_keyboard("rust")

        callback_data = []
        for row in result.inline_keyboard:
            for btn in row:
                callback_data.append(btn.callback_data)

        assert "price_range:rust" in callback_data
        assert "set_category:rust" in callback_data
        assert "set_type:rust" in callback_data
        assert "set_rarity:rust" in callback_data

    def test_reset_callback_data_format(self):
        """Test reset button callback data format."""
        for game in ["csgo", "dota2", "tf2", "rust"]:
            result = get_game_filter_keyboard(game)

            callback_data = []
            for row in result.inline_keyboard:
                for btn in row:
                    callback_data.append(btn.callback_data)

            assert f"filter:reset:{game}" in callback_data

    def test_back_callback_data_format(self):
        """Test back button callback data format."""
        result = get_game_filter_keyboard("csgo")

        callback_data = []
        for row in result.inline_keyboard:
            for btn in row:
                callback_data.append(btn.callback_data)

        assert "back_to_filters:main" in callback_data


class TestModuleExports:
    """Tests for module exports."""

    def test_all_functions_exported(self):
        """Test that all functions are in __all__."""
        from src.telegram_bot.handlers.game_filters import utils

        assert "get_current_filters" in utils.__all__
        assert "update_filters" in utils.__all__
        assert "get_game_filter_keyboard" in utils.__all__
        assert "get_filter_description" in utils.__all__
        assert "build_api_params_for_game" in utils.__all__

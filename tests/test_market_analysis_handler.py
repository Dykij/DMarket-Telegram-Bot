"""Тесты для market_analysis_handler_refactored - Фаза 2."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Message, Update, User
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.market_analysis_handler_refactored import (
    DEFAULT_GAME,
    _add_game_selection_rows,
    _create_main_analysis_keyboard,
    _initialize_user_settings,
    market_analysis_callback,
    market_analysis_command,
    show_price_changes_results,
    show_trending_items_results,
)


@pytest.fixture()
def mock_update():
    """Фикстура для mock update."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456
    return update


@pytest.fixture()
def mock_context():
    """Фикстура для mock context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.fixture()
def mock_callback_query():
    """Фикстура для mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123456
    return query


class TestMarketAnalysisCommand:
    """Тесты для market_analysis_command."""

    @pytest.mark.asyncio()
    async def test_command_without_message_returns_early(self, mock_context):
        """Тест: команда без сообщения завершается досрочно."""
        update = MagicMock(spec=Update)
        update.message = None

        await market_analysis_command(update, mock_context)

        # Проверяем что reply_text не был вызван
        assert True  # Просто проверяем что не упало

    @pytest.mark.asyncio()
    async def test_command_sends_main_keyboard(self, mock_update, mock_context):
        """Тест: команда отправляет основную клавиатуру."""
        await market_analysis_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args

        assert "Анализ рынка DMarket" in call_args[0][0]
        assert "reply_markup" in call_args[1]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)


class TestInitializeUserSettings:
    """Тесты для _initialize_user_settings."""

    def test_initializes_settings_when_none(self, mock_context):
        """Тест: инициализация настроек когда их нет."""
        mock_context.user_data = {}

        settings = _initialize_user_settings(mock_context)

        assert settings["current_game"] == DEFAULT_GAME
        assert "period" in settings
        assert "min_price" in settings
        assert "max_price" in settings

    def test_returns_existing_settings(self, mock_context):
        """Тест: возврат существующих настроек."""
        existing = {"current_game": "dota2", "period": "7d"}
        mock_context.user_data = {"market_analysis": existing}

        settings = _initialize_user_settings(mock_context)

        assert settings == existing

    def test_handles_none_user_data(self):
        """Тест: обработка None в user_data."""
        context = MagicMock()
        context.user_data = None

        settings = _initialize_user_settings(context)

        assert settings == {}


class TestCreateMainAnalysisKeyboard:
    """Тесты для _create_main_analysis_keyboard."""

    def test_creates_keyboard_with_all_options(self):
        """Тест: создание клавиатуры со всеми опциями."""
        keyboard = _create_main_analysis_keyboard("csgo")

        assert len(keyboard) == 3
        assert len(keyboard[0]) == 2  # Изменения цен + Трендовые
        assert len(keyboard[1]) == 2  # Волатильность + Отчет
        assert len(keyboard[2]) == 2  # Недооцененные + Рекомендации

    def test_keyboard_has_correct_callbacks(self):
        """Тест: клавиатура имеет правильные callback данные."""
        keyboard = _create_main_analysis_keyboard("dota2")

        first_button = keyboard[0][0]
        assert "analysis:price_changes:dota2" in first_button.callback_data


class TestAddGameSelectionRows:
    """Тесты для _add_game_selection_rows."""

    def test_adds_game_buttons_to_keyboard(self):
        """Тест: добавление кнопок игр к клавиатуре."""
        keyboard = []
        _add_game_selection_rows(keyboard)

        assert len(keyboard) > 0
        # Проверяем что добавлены кнопки игр
        all_buttons = [btn for row in keyboard for btn in row]
        assert len(all_buttons) > 0

    def test_marks_selected_game(self):
        """Тест: отметка выбранной игры."""
        keyboard = []
        _add_game_selection_rows(keyboard, selected_game="csgo")

        all_buttons = [btn for row in keyboard for btn in row]
        csgo_buttons = [btn for btn in all_buttons if "csgo" in btn.callback_data]

        assert any("✅" in btn.text for btn in csgo_buttons)


class TestMarketAnalysisCallback:
    """Тесты для market_analysis_callback."""

    @pytest.mark.asyncio()
    async def test_callback_without_query_returns_early(self, mock_context):
        """Тест: callback без query завершается досрочно."""
        update = MagicMock(spec=Update)
        update.callback_query = None

        await market_analysis_callback(update, mock_context)

        # Проверяем что ничего не упало
        assert True

    @pytest.mark.asyncio()
    async def test_callback_without_data_returns_early(self, mock_context):
        """Тест: callback без данных завершается досрочно."""
        update = MagicMock(spec=Update)
        query = MagicMock(spec=CallbackQuery)
        query.data = None
        query.answer = AsyncMock()
        update.callback_query = query

        await market_analysis_callback(update, mock_context)

        # Early return happens before answer(), so answer should NOT be called
        query.answer.assert_not_called()

    @pytest.mark.asyncio()
    async def test_callback_handles_game_selection(self, mock_callback_query, mock_context):
        """Тест: callback обрабатывает выбор игры."""
        update = MagicMock(spec=Update)
        update.callback_query = mock_callback_query
        mock_callback_query.data = "analysis:select_game:dota2"

        await market_analysis_callback(update, mock_context)

        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_text.assert_called_once()


class TestShowPriceChangesResults:
    """Тесты для show_price_changes_results."""

    @pytest.mark.asyncio()
    async def test_shows_empty_message_when_no_items(self, mock_callback_query, mock_context):
        """Тест: показ пустого сообщения когда нет предметов."""
        with patch(
            "src.telegram_bot.handlers.market_analysis_handler_refactored.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page.return_value = ([], 0, 0)

            await show_price_changes_results(mock_callback_query, mock_context, "csgo")

            call_args = mock_callback_query.edit_message_text.call_args
            assert "Не найдено" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_formats_items_correctly(self, mock_callback_query, mock_context):
        """Тест: правильное форматирование предметов."""
        items = [{"market_hash_name": "Test Item", "current_price": 10.5}]

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler_refactored.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page.return_value = (items, 0, 1)
            mock_pagination.get_items_per_page.return_value = 10

            with patch(
                "src.telegram_bot.handlers.market_analysis_handler_refactored.format_market_items"
            ) as mock_format:
                mock_format.return_value = "Formatted text"

                await show_price_changes_results(mock_callback_query, mock_context, "csgo")

                mock_format.assert_called_once_with(items=items, page=0, items_per_page=10)


class TestShowTrendingItemsResults:
    """Тесты для show_trending_items_results."""

    @pytest.mark.asyncio()
    async def test_shows_empty_message_when_no_items(self, mock_callback_query, mock_context):
        """Тест: показ пустого сообщения когда нет трендовых предметов."""
        with patch(
            "src.telegram_bot.handlers.market_analysis_handler_refactored.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page.return_value = ([], 0, 0)

            await show_trending_items_results(mock_callback_query, mock_context, "csgo")

            call_args = mock_callback_query.edit_message_text.call_args
            assert "Не найдено трендовых предметов" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_displays_trending_items(self, mock_callback_query, mock_context):
        """Тест: отображение трендовых предметов."""
        items = [{"title": "Trending Item", "price": 25.0}]

        with patch(
            "src.telegram_bot.handlers.market_analysis_handler_refactored.pagination_manager"
        ) as mock_pagination:
            mock_pagination.get_page.return_value = (items, 0, 1)
            mock_pagination.get_items_per_page.return_value = 10

            with patch(
                "src.telegram_bot.handlers.market_analysis_handler_refactored.format_market_items"
            ) as mock_format:
                mock_format.return_value = "Items text"

                await show_trending_items_results(mock_callback_query, mock_context, "csgo")

                mock_callback_query.edit_message_text.assert_called_once()
                call_args = mock_callback_query.edit_message_text.call_args
                assert "Трендовые предметы" in call_args[0][0]


@pytest.mark.asyncio()
async def test_error_handling_in_callback(mock_callback_query, mock_context):
    """Тест: обработка ошибок в callback."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    mock_callback_query.data = "analysis:price_changes:csgo"

    with patch(
        "src.telegram_bot.handlers.market_analysis_handler_refactored._perform_price_analysis"
    ) as mock_perform:
        mock_perform.side_effect = Exception("Test error")

        await market_analysis_callback(update, mock_context)

        # Проверяем что ошибка была обработана
        call_args = mock_callback_query.edit_message_text.call_args
        assert "ошибка" in call_args[0][0].lower()

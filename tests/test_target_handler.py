"""Тесты для refactored target_handler - Фаза 2."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Update, User
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.target_handler_refactored import (
    _create_targets_keyboard,
    _format_competition_analysis_text,
    _format_smart_targets_results,
    _get_popular_items_for_smart_targets,
    _get_targets_menu_text,
    handle_competition_analysis,
    handle_smart_targets,
    handle_target_callback,
    start_targets_menu,
)


@pytest.fixture()
def mock_update():
    """Фикстура для мокированного Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.callback_query = None
    return update


@pytest.fixture()
def mock_context():
    """Фикстура для мокированного Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    return context


@pytest.fixture()
def mock_callback_query():
    """Фикстура для мокированного CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = "target"
    return query


class TestHelperFunctions:
    """Тесты вспомогательных функций."""

    def test_create_targets_keyboard_returns_valid_structure(self):
        """Тест корректности структуры клавиатуры."""
        keyboard = _create_targets_keyboard()

        assert len(keyboard) == 6
        assert all(isinstance(row, list) for row in keyboard)
        assert all(len(row) == 1 for row in keyboard)

    def test_get_targets_menu_text_contains_key_info(self):
        """Тест наличия ключевой информации в тексте."""
        text = _get_targets_menu_text()

        assert "Таргеты" in text
        assert "Buy Orders" in text
        assert "API v1.1.0" in text
        assert "Умные таргеты" in text

    def test_get_popular_items_returns_list(self):
        """Тест получения списка популярных предметов."""
        items = _get_popular_items_for_smart_targets()

        assert isinstance(items, list)
        assert len(items) > 0
        assert all("title" in item for item in items)

    def test_format_smart_targets_results_with_empty_list(self):
        """Тест форматирования пустого списка результатов."""
        text = _format_smart_targets_results([])

        assert "Не удалось создать" in text

    def test_format_smart_targets_results_with_data(self):
        """Тест форматирования результатов с данными."""
        results = [
            {
                "Title": "Test Item",
                "Price": {"Amount": 1000},  # $10.00
            }
        ]

        text = _format_smart_targets_results(results)

        assert "успешно" in text
        assert "Test Item" in text
        assert "$10.00" in text

    def test_format_competition_analysis_text_with_none(self):
        """Тест форматирования анализа при None."""
        text = _format_competition_analysis_text(None, "Test Item")

        assert "Не удалось получить" in text


class TestStartTargetsMenu:
    """Тесты функции start_targets_menu."""

    @pytest.mark.asyncio()
    async def test_start_targets_menu_sends_new_message(
        self, mock_update, mock_context
    ):
        """Тест отправки нового сообщения."""
        await start_targets_menu(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 123456789
        assert "Таргеты" in call_args.kwargs["text"]

    @pytest.mark.asyncio()
    async def test_start_targets_menu_edits_existing_message(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест редактирования существующего сообщения."""
        mock_update.callback_query = mock_callback_query

        await start_targets_menu(mock_update, mock_context)

        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_start_targets_menu_handles_no_user(self, mock_update, mock_context):
        """Тест обработки отсутствия пользователя."""
        mock_update.effective_user = None

        await start_targets_menu(mock_update, mock_context)

        mock_context.bot.send_message.assert_not_called()


class TestHandleSmartTargets:
    """Тесты функции handle_smart_targets."""

    @pytest.mark.asyncio()
    async def test_handle_smart_targets_no_query_returns_early(
        self, mock_update, mock_context
    ):
        """Тест раннего возврата при отсутствии query."""
        mock_update.callback_query = None

        await handle_smart_targets(mock_update, mock_context)

        # Никакие методы не должны быть вызваны
        assert True

    @pytest.mark.asyncio()
    async def test_handle_smart_targets_no_api_client(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест обработки отсутствия API клиента."""
        mock_update.callback_query = mock_callback_query

        with patch(
            "src.telegram_bot.handlers.target_handler_refactored.create_api_client_from_env",
            return_value=None,
        ):
            await handle_smart_targets(mock_update, mock_context)

        # Должно быть два вызова edit_message_text
        assert mock_callback_query.edit_message_text.call_count == 2

    @pytest.mark.asyncio()
    async def test_handle_smart_targets_success(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест успешного создания умных таргетов."""
        mock_update.callback_query = mock_callback_query

        mock_api_client = AsyncMock()
        mock_target_manager = AsyncMock()
        mock_target_manager.create_smart_targets = AsyncMock(
            return_value=[{"Title": "Item 1", "Price": {"Amount": 1000}}]
        )

        with (
            patch(
                "src.telegram_bot.handlers.target_handler_refactored.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.target_handler_refactored.TargetManager",
                return_value=mock_target_manager,
            ),
        ):
            await handle_smart_targets(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count == 2


class TestHandleCompetitionAnalysis:
    """Тесты функции handle_competition_analysis."""

    @pytest.mark.asyncio()
    async def test_handle_competition_analysis_no_query(
        self, mock_update, mock_context
    ):
        """Тест раннего возврата при отсутствии query."""
        mock_update.callback_query = None

        await handle_competition_analysis(mock_update, mock_context)

        assert True

    @pytest.mark.asyncio()
    async def test_handle_competition_analysis_no_api_client(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест обработки отсутствия API клиента."""
        mock_update.callback_query = mock_callback_query

        with patch(
            "src.telegram_bot.handlers.target_handler_refactored.create_api_client_from_env",
            return_value=None,
        ):
            await handle_competition_analysis(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count == 2

    @pytest.mark.asyncio()
    async def test_handle_competition_analysis_success(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест успешного анализа конкуренции."""
        mock_update.callback_query = mock_callback_query

        mock_api_client = AsyncMock()
        mock_target_manager = AsyncMock()
        mock_target_manager.analyze_target_competition = AsyncMock(
            return_value={"total_orders": 10}
        )

        with (
            patch(
                "src.telegram_bot.handlers.target_handler_refactored.create_api_client_from_env",
                return_value=mock_api_client,
            ),
            patch(
                "src.telegram_bot.handlers.target_handler_refactored.TargetManager",
                return_value=mock_target_manager,
            ),
            patch(
                "src.telegram_bot.handlers.target_handler_refactored.format_target_competition_analysis",
                return_value="Analysis result",
            ),
        ):
            await handle_competition_analysis(mock_update, mock_context)

        assert mock_callback_query.edit_message_text.call_count == 2


class TestHandleTargetCallback:
    """Тесты функции handle_target_callback."""

    @pytest.mark.asyncio()
    async def test_handle_target_callback_no_query(self, mock_update, mock_context):
        """Тест раннего возврата при отсутствии query."""
        mock_update.callback_query = None

        await handle_target_callback(mock_update, mock_context)

        assert True

    @pytest.mark.asyncio()
    async def test_handle_target_callback_main_menu(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест вызова главного меню."""
        mock_callback_query.data = "target"
        mock_update.callback_query = mock_callback_query

        with patch(
            "src.telegram_bot.handlers.target_handler_refactored.start_targets_menu",
            new_callable=AsyncMock,
        ) as mock_start:
            await handle_target_callback(mock_update, mock_context)
            mock_start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_target_callback_smart_targets(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест вызова умных таргетов."""
        mock_callback_query.data = "target_target_smart"
        mock_update.callback_query = mock_callback_query

        with patch(
            "src.telegram_bot.handlers.target_handler_refactored.handle_smart_targets",
            new_callable=AsyncMock,
        ) as mock_smart:
            await handle_target_callback(mock_update, mock_context)
            mock_smart.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_target_callback_competition_analysis(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест вызова анализа конкуренции."""
        mock_callback_query.data = "target_target_competition"
        mock_update.callback_query = mock_callback_query

        with patch(
            "src.telegram_bot.handlers.target_handler_refactored.handle_competition_analysis",
            new_callable=AsyncMock,
        ) as mock_competition:
            await handle_target_callback(mock_update, mock_context)
            mock_competition.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handle_target_callback_unknown_action(
        self, mock_update, mock_context, mock_callback_query
    ):
        """Тест обработки неизвестного действия."""
        mock_callback_query.data = "target_unknown"
        mock_update.callback_query = mock_callback_query

        await handle_target_callback(mock_update, mock_context)

        mock_callback_query.answer.assert_called_once()

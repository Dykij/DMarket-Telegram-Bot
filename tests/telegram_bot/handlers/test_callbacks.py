"""Тесты для модуля callbacks.py.

Этот модуль содержит тесты функций, которые являются обертками для реальных обработчиков.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.callbacks import (
    arbitrage_callback_impl as arbitrage_callback,
)
from src.telegram_bot.handlers.callbacks import (
    handle_best_opportunities_impl as handle_best_opportunities,
)
from src.telegram_bot.handlers.callbacks import (
    handle_dmarket_arbitrage_impl as handle_dmarket_arbitrage,
)
from src.telegram_bot.handlers.callbacks import (
    handle_game_selected_impl as handle_game_selected,
)
from src.telegram_bot.handlers.callbacks import (
    handle_game_selection_impl as handle_game_selection,
)
from src.telegram_bot.handlers.callbacks import (
    show_arbitrage_opportunities,
)


@pytest.fixture()
def mock_update():
    """Создает мок объекта Update для тестирования."""
    update = MagicMock(spec=Update)
    update.callback_query = MagicMock()
    update.callback_query.data = "arbitrage"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    # Оборачиваем nested async методы
    update.callback_query.message.chat.send_action = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Создает мок объекта CallbackContext для тестирования."""
    context = MagicMock(spec=CallbackContext)
    context.user_data = {"current_game": "csgo"}
    return context


@pytest.mark.asyncio()
async def test_arbitrage_callback(mock_update, mock_context):
    """Тестирует, что arbitrage_callback вызывает edit_message_text."""
    # Вызываем тестируемую функцию (реальную, без моков)
    await arbitrage_callback(mock_update, mock_context)

    # Проверяем, что edit_message_text был вызван
    mock_update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.callbacks.setup_api_client")
@patch("src.telegram_bot.handlers.callbacks.find_arbitrage_opportunities_advanced")
async def test_handle_dmarket_arbitrage(
    mock_find_arb,
    mock_setup_api,
    mock_update,
    mock_context,
):
    """Тестирует handle_dmarket_arbitrage с реальной реализацией."""
    # Настраиваем тестовые данные
    mode = "boost"

    # Настраиваем моки
    mock_api = MagicMock()
    mock_setup_api.return_value = mock_api
    mock_find_arb.return_value = []

    # Вызываем тестируемую функцию
    await handle_dmarket_arbitrage(mock_update, mock_context, mode)

    # Проверяем, что edit_message_text был вызван
    mock_update.callback_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.callbacks.setup_api_client")
@patch("src.telegram_bot.handlers.callbacks.find_arbitrage_opportunities_advanced")
async def test_handle_best_opportunities(
    mock_find_arb,
    mock_setup_api,
    mock_update,
    mock_context,
):
    """Тестирует handle_best_opportunities с реальной реализацией."""
    # Настраиваем моки
    mock_api = MagicMock()
    mock_setup_api.return_value = mock_api
    mock_find_arb.return_value = []

    # Вызываем тестируемую функцию
    await handle_best_opportunities(mock_update, mock_context)

    # Проверяем, что edit_message_text был вызван
    mock_update.callback_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.callbacks.setup_api_client")
@patch("src.telegram_bot.handlers.callbacks.find_arbitrage_opportunities_advanced")
async def test_handle_dmarket_arbitrage_different_modes(
    mock_find_arb,
    mock_setup_api,
    mock_update,
    mock_context,
):
    """Тестирует handle_dmarket_arbitrage с разными режимами."""
    # Настраиваем моки
    mock_api = MagicMock()
    mock_setup_api.return_value = mock_api
    mock_find_arb.return_value = []

    # Настраиваем тестовые данные
    test_modes = ["boost", "mid", "pro"]

    # Тестируем с разными режимами
    for mode in test_modes:
        # Вызываем тестируемую функцию с разными режимами
        await handle_dmarket_arbitrage(mock_update, mock_context, mode)

        # Проверяем, что edit_message_text был вызван
        mock_update.callback_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
async def test_handle_game_selection(mock_update, mock_context):
    """Тестирует handle_game_selection."""
    # Вызываем тестируемую функцию
    await handle_game_selection(mock_update, mock_context)

    # Проверяем, что edit_message_text был вызван
    mock_update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.callbacks.setup_api_client")
@patch("src.telegram_bot.handlers.callbacks.find_arbitrage_opportunities_advanced")
async def test_handle_game_selected(
    mock_find_arb,
    mock_setup_api,
    mock_update,
    mock_context,
):
    """Тестирует handle_game_selected с выбором игры."""
    # Настраиваем моки
    mock_api = MagicMock()
    mock_setup_api.return_value = mock_api
    mock_find_arb.return_value = []

    # Вызываем тестируемую функцию с выбранной игрой
    await handle_game_selected(mock_update, mock_context, game="csgo")

    # Проверяем, что edit_message_text был вызван
    mock_update.callback_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.callbacks.format_opportunities")
async def test_show_arbitrage_opportunities(
    mock_format,
    mock_update,
    mock_context,
):
    """Тестирует show_arbitrage_opportunities."""
    # Настраиваем моки
    mock_format.return_value = "Test opportunities"
    mock_context.user_data = {"arbitrage_opportunities": []}

    # Создаем mock для query
    query = mock_update.callback_query

    # Вызываем тестируемую функцию
    await show_arbitrage_opportunities(query, mock_context, page=0)

    # Проверяем, что edit_message_text был вызван
    query.edit_message_text.assert_called()

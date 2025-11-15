"""Тесты для модуля scanner_handler.

Этот модуль тестирует обработчики для многоуровневого сканирования арбитража:
- Форматирование результатов сканирования
- Меню сканера
- Обработка сканирования по уровням
- Обработка обзора рынка
- Пагинация результатов
- Callback обработчики
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Update

from src.telegram_bot.handlers.scanner_handler import (
    ALL_LEVELS_ACTION,
    ARBITRAGE_LEVELS,
    BEST_OPPS_ACTION,
    GAMES,
    LEVEL_SCAN_ACTION,
    MARKET_OVERVIEW_ACTION,
    SCANNER_ACTION,
    format_scanner_item,
    format_scanner_results,
    handle_level_scan,
    handle_market_overview,
    handle_scanner_callback,
    handle_scanner_pagination,
    register_scanner_handlers,
    start_scanner_menu,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_update():
    """Создает мок Update объекта."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.from_user = MagicMock()
    update.callback_query.from_user.id = 123456
    update.callback_query.message = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Создает мок CallbackContext объекта."""
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


@pytest.fixture()
def sample_scanner_results():
    """Создает примерные результаты сканирования."""
    return [
        {
            "title": "Test Item 1",
            "buy_price": 100.0,
            "sell_price": 120.0,
            "profit": 20.0,
            "profit_percent": 20.0,
            "level": "1",
            "risk_level": "low",
            "item_id": "item123",
        },
        {
            "title": "Test Item 2",
            "buy_price": 200.0,
            "sell_price": 250.0,
            "profit": 50.0,
            "profit_percent": 25.0,
            "level": "2",
            "risk_level": "medium",
            "item_id": "item456",
        },
    ]


# ============================================================================
# ТЕСТЫ КОНСТАНТ
# ============================================================================


def test_constants_defined():
    """Тест наличия всех необходимых констант."""
    assert SCANNER_ACTION is not None
    assert LEVEL_SCAN_ACTION is not None
    assert ALL_LEVELS_ACTION is not None
    assert BEST_OPPS_ACTION is not None
    assert MARKET_OVERVIEW_ACTION is not None

    # Проверяем, что константы - строки
    assert isinstance(SCANNER_ACTION, str)
    assert isinstance(LEVEL_SCAN_ACTION, str)


def test_arbitrage_levels_imported():
    """Тест импорта уровней арбитража."""
    assert ARBITRAGE_LEVELS is not None
    assert isinstance(ARBITRAGE_LEVELS, dict)


def test_games_imported():
    """Тест импорта игр."""
    assert GAMES is not None
    assert isinstance(GAMES, dict)


# ============================================================================
# ТЕСТЫ ФОРМАТИРОВАНИЯ
# ============================================================================


def test_format_scanner_item(sample_scanner_results):
    """Тест форматирования одного элемента."""
    result = sample_scanner_results[0]
    formatted = format_scanner_item(result)

    # Проверяем, что форматирование содержит ключевые элементы
    assert isinstance(formatted, str)
    assert "Test Item 1" in formatted
    assert "100.00" in formatted
    assert "120.00" in formatted
    assert "20.0" in formatted


def test_format_scanner_results_empty():
    """Тест форматирования пустых результатов."""
    formatted = format_scanner_results([], 0, 10)

    assert isinstance(formatted, str)
    assert "Нет результатов" in formatted or "No results" in formatted.lower()


def test_format_scanner_results_with_items(sample_scanner_results):
    """Тест форматирования результатов с элементами."""
    formatted = format_scanner_results(sample_scanner_results, 0, 10)

    assert isinstance(formatted, str)
    assert "Test Item 1" in formatted
    assert "Test Item 2" in formatted
    assert "Страница" in formatted


# ============================================================================
# ТЕСТЫ МЕНЮ И ОБРАБОТЧИКОВ
# ============================================================================


@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@pytest.mark.asyncio()
async def test_start_scanner_menu(mock_api_client, mock_update, mock_context):
    """Тест запуска меню сканера."""
    # Настраиваем мок API клиента
    mock_api = AsyncMock()
    mock_api_client.return_value = mock_api

    # Вызываем меню
    await start_scanner_menu(mock_update, mock_context)

    # Проверяем, что callback был обработан
    mock_update.callback_query.answer.assert_called()


@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@pytest.mark.asyncio()
async def test_handle_level_scan_success(
    mock_api_client,
    mock_scanner,
    mock_update,
    mock_context,
    sample_scanner_results,
):
    """Тест успешного сканирования по уровню."""
    # Настраиваем моки
    mock_api = MagicMock()
    mock_api_client.return_value = mock_api

    mock_scanner_instance = MagicMock()
    mock_scanner_instance.scan_game = AsyncMock(return_value=sample_scanner_results)
    mock_scanner.return_value = mock_scanner_instance

    # Вызываем обработчик с правильными аргументами (используем boost для уровня)
    await handle_level_scan(mock_update, mock_context, "boost", "csgo")

    # Проверяем, что функция выполнилась без ошибок
    assert mock_api_client.called
    assert mock_update.callback_query.answer.called


@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@pytest.mark.asyncio()
async def test_handle_level_scan_no_results(
    mock_api_client,
    mock_scanner,
    mock_update,
    mock_context,
):
    """Тест сканирования когда нет результатов."""
    # Настраиваем моки
    mock_api = MagicMock()
    mock_api_client.return_value = mock_api

    mock_scanner_instance = MagicMock()
    mock_scanner_instance.scan_game = AsyncMock(return_value=[])
    mock_scanner.return_value = mock_scanner_instance

    # Вызываем обработчик с правильными аргументами
    await handle_level_scan(mock_update, mock_context, "pro", "dota2")

    # Проверяем, что функция выполнилась без ошибок
    assert mock_api_client.called
    assert mock_update.callback_query.answer.called


@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@pytest.mark.asyncio()
async def test_handle_market_overview(
    mock_api_client,
    mock_scanner,
    mock_update,
    mock_context,
    sample_scanner_results,
):
    """Тест обработчика обзора рынка."""
    # Настраиваем моки
    mock_api = AsyncMock()
    mock_api_client.return_value = mock_api

    mock_scanner_instance = AsyncMock()
    mock_scanner_instance.scan_game.return_value = sample_scanner_results
    mock_scanner.return_value = mock_scanner_instance

    # Настраиваем данные callback
    mock_update.callback_query.data = "market_overview:csgo"

    # Вызываем обработчик
    await handle_market_overview(mock_update, mock_context)

    # Проверяем обработку
    mock_update.callback_query.answer.assert_called()


@pytest.mark.asyncio()
async def test_handle_scanner_pagination(mock_update, mock_context):
    """Тест обработчика пагинации."""
    # Настраиваем данные callback
    mock_update.callback_query.data = "scanner_page:0"

    # Инициализируем user_data с результатами
    mock_context.user_data["scanner_results"] = [
        {"title": f"Item {i}", "item_id": f"id{i}"} for i in range(20)
    ]

    # Вызываем обработчик
    await handle_scanner_pagination(mock_update, mock_context)

    # Проверяем, что callback был обработан
    mock_update.callback_query.answer.assert_called()


@pytest.mark.asyncio()
async def test_handle_scanner_callback_invalid_action(mock_update, mock_context):
    """Тест обработки неизвестного действия."""
    # Настраиваем неизвестное действие
    mock_update.callback_query.data = "unknown_scanner_action"

    # Вызываем обработчик
    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем, что callback был обработан
    mock_update.callback_query.answer.assert_called()


def test_register_scanner_handlers():
    """Тест регистрации обработчиков сканера."""
    # Создаем мок dispatcher
    mock_dispatcher = MagicMock()
    mock_dispatcher.add_handler = MagicMock()

    # Вызываем регистрацию
    register_scanner_handlers(mock_dispatcher)

    # Проверяем, что обработчики были добавлены
    assert mock_dispatcher.add_handler.called
    assert mock_dispatcher.add_handler.call_count >= 1

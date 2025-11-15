"""Тесты для обработчика многоуровневого сканирования арбитража."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update, User

from src.telegram_bot.handlers.scanner_handler import (
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


# ======================== Fixtures ========================


@pytest.fixture()
def mock_user():
    """Создать мок объекта User."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    return user


@pytest.fixture()
def mock_callback_query(mock_user):
    """Создать мок объекта CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = SCANNER_ACTION
    query.from_user = mock_user
    return query


@pytest.fixture()
def mock_update(mock_user, mock_callback_query):
    """Создать мок объекта Update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.effective_user = mock_user
    return update


@pytest.fixture()
def mock_context():
    """Создать мок объекта CallbackContext."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context


@pytest.fixture()
def sample_arbitrage_result():
    """Создать пример результата арбитража."""
    return {
        "title": "AK-47 | Redline (Field-Tested)",
        "buy_price": 12.50,
        "sell_price": 15.00,
        "profit": 2.14,
        "profit_percent": 14.3,
        "level": "standard",
        "risk_level": "low",
        "item_id": "item_12345",
    }


@pytest.fixture()
def sample_arbitrage_results(sample_arbitrage_result):
    """Создать список результатов арбитража."""
    return [
        sample_arbitrage_result,
        {
            "title": "AWP | Asiimov (Battle-Scarred)",
            "buy_price": 25.00,
            "sell_price": 28.50,
            "profit": 2.51,
            "profit_percent": 8.8,
            "level": "medium",
            "risk_level": "medium",
            "item_id": "item_67890",
        },
    ]


# ======================== Тесты форматирования ========================


def test_format_scanner_item_contains_all_fields(sample_arbitrage_result):
    """Тест форматирования одного результата с полными данными."""
    result = format_scanner_item(sample_arbitrage_result)

    assert "AK-47 | Redline (Field-Tested)" in result
    assert "$12.50" in result
    assert "$15.00" in result
    assert "$2.14" in result
    assert "14.3%" in result
    assert "standard" in result
    assert "low" in result
    assert "item_12345" in result


def test_format_scanner_item_with_missing_fields():
    """Тест форматирования результата с отсутствующими полями."""
    incomplete_result = {
        "title": "Test Item",
    }
    result = format_scanner_item(incomplete_result)

    assert "Test Item" in result
    assert "$0.00" in result  # Default buy_price
    assert "0.0%" in result  # Default profit_percent


def test_format_scanner_item_with_empty_dict():
    """Тест форматирования пустого результата."""
    result = format_scanner_item({})

    assert "Неизвестный предмет" in result
    assert "$0.00" in result


def test_format_scanner_results_empty_list():
    """Тест форматирования пустого списка результатов."""
    result = format_scanner_results([], 0, 10)

    assert "Нет результатов для отображения" in result


def test_format_scanner_results_with_items(sample_arbitrage_results):
    """Тест форматирования списка результатов."""
    result = format_scanner_results(sample_arbitrage_results, 0, 10)

    assert "Страница 1" in result
    assert "AK-47 | Redline (Field-Tested)" in result
    assert "AWP | Asiimov (Battle-Scarred)" in result


def test_format_scanner_results_page_number():
    """Тест отображения номера страницы."""
    result = format_scanner_results([{"title": "Item"}], 2, 10)

    assert "Страница 3" in result  # current_page + 1


# ======================== Тесты start_scanner_menu ========================


@pytest.mark.asyncio()
async def test_start_scanner_menu_with_callback_query(mock_update, mock_context):
    """Тест отображения главного меню через callback query."""
    await start_scanner_menu(mock_update, mock_context)

    # Проверяем answer()
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем edit_message_text()
    mock_update.callback_query.edit_message_text.assert_called_once()
    call_args = mock_update.callback_query.edit_message_text.call_args

    # Проверяем текст
    text = call_args[0][0]
    assert "Многоуровневое сканирование" in text
    assert "Разгон" in text
    assert "Стандарт" in text
    assert "Средний" in text
    assert "Продвинутый" in text
    assert "Профессиональный" in text

    # Проверяем parse_mode
    assert call_args[1]["parse_mode"] == "Markdown"

    # Проверяем reply_markup
    assert "reply_markup" in call_args[1]
    assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)


@pytest.mark.asyncio()
async def test_start_scanner_menu_without_callback_query(mock_update, mock_context):
    """Тест отображения главного меню без callback query."""
    mock_update.callback_query = None

    await start_scanner_menu(mock_update, mock_context)

    # Проверяем send_message вместо edit
    mock_context.bot.send_message.assert_called_once()
    call_args = mock_context.bot.send_message.call_args

    assert call_args[1]["chat_id"] == 123456789
    assert "Многоуровневое сканирование" in call_args[1]["text"]


@pytest.mark.asyncio()
async def test_start_scanner_menu_has_all_level_buttons(mock_update, mock_context):
    """Тест наличия всех кнопок уровней в меню."""
    await start_scanner_menu(mock_update, mock_context)

    call_args = mock_update.callback_query.edit_message_text.call_args
    keyboard = call_args[1]["reply_markup"].inline_keyboard

    # Проверяем наличие кнопок для всех уровней
    button_texts = [btn.text for row in keyboard for btn in row]

    assert "🚀 Разгон баланса" in button_texts
    assert "⭐ Стандарт" in button_texts
    assert "💰 Средний" in button_texts
    assert "💎 Продвинутый" in button_texts
    assert "🏆 Профессиональный" in button_texts
    assert "🔍 Все уровни" in button_texts
    assert "⭐ Лучшие возможности" in button_texts
    assert "📊 Обзор рынка" in button_texts
    assert "⬅️ Назад" in button_texts


@pytest.mark.asyncio()
async def test_start_scanner_menu_button_callbacks(mock_update, mock_context):
    """Тест правильности callback_data для кнопок."""
    await start_scanner_menu(mock_update, mock_context)

    call_args = mock_update.callback_query.edit_message_text.call_args
    keyboard = call_args[1]["reply_markup"].inline_keyboard

    # Проверяем callback_data первой кнопки (Разгон)
    boost_button = keyboard[0][0]
    assert boost_button.callback_data == f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_boost"

    # Проверяем callback_data последней кнопки (Назад)
    back_button = keyboard[-1][0]
    assert back_button.callback_data == "arbitrage_menu"


# ======================== Тесты handle_level_scan ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
@patch("src.telegram_bot.handlers.scanner_handler.pagination_manager")
@patch("src.telegram_bot.handlers.scanner_handler.create_pagination_keyboard")
async def test_handle_level_scan_success(
    mock_keyboard,
    mock_pagination,
    mock_scanner_class,
    mock_api_client,
    mock_update,
    mock_context,
    sample_arbitrage_results,
):
    """Тест успешного сканирования уровня."""
    # Настраиваем моки
    mock_api_client.return_value = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.scan_level = AsyncMock(return_value=sample_arbitrage_results)
    mock_scanner_class.return_value = mock_scanner

    mock_pagination.add_items_for_user = MagicMock()
    mock_pagination.get_page.return_value = (sample_arbitrage_results, 0, 1)
    mock_pagination.get_items_per_page.return_value = 10

    mock_keyboard.return_value = InlineKeyboardMarkup([])

    # Вызываем функцию
    await handle_level_scan(mock_update, mock_context, "standard", "csgo")

    # Проверяем вызовы
    mock_update.callback_query.answer.assert_called_once()
    assert mock_update.callback_query.edit_message_text.call_count >= 2  # Начальное + результаты

    # Проверяем вызов scan_level
    mock_scanner.scan_level.assert_called_once_with(level="standard", game="csgo", max_results=50)

    # Проверяем добавление в пагинацию
    mock_pagination.add_items_for_user.assert_called_once_with(
        123456789,
        sample_arbitrage_results,
        "scanner_standard",
    )


@pytest.mark.asyncio()
async def test_handle_level_scan_no_callback_query(mock_update, mock_context):
    """Тест handle_level_scan без callback query."""
    mock_update.callback_query = None

    await handle_level_scan(mock_update, mock_context, "standard")

    # Функция должна завершиться без действий
    # Проверяем, что не было вызовов


@pytest.mark.asyncio()
async def test_handle_level_scan_invalid_level(mock_update, mock_context):
    """Тест handle_level_scan с неверным уровнем."""
    await handle_level_scan(mock_update, mock_context, "invalid_level")

    # Проверяем сообщение об ошибке
    mock_update.callback_query.edit_message_text.assert_called()
    call_args = mock_update.callback_query.edit_message_text.call_args
    assert "Неизвестный уровень" in call_args[0][0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
async def test_handle_level_scan_api_client_none(
    mock_api_client,
    mock_update,
    mock_context,
):
    """Тест handle_level_scan когда API клиент не создан."""
    mock_api_client.return_value = None

    await handle_level_scan(mock_update, mock_context, "standard")

    # Проверяем сообщение об ошибке
    calls = mock_update.callback_query.edit_message_text.call_args_list
    error_call = calls[-1]
    assert "Не удалось создать API клиент" in error_call[0][0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
async def test_handle_level_scan_no_results(
    mock_scanner_class,
    mock_api_client,
    mock_update,
    mock_context,
):
    """Тест handle_level_scan когда результаты не найдены."""
    mock_api_client.return_value = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.scan_level = AsyncMock(return_value=[])
    mock_scanner_class.return_value = mock_scanner

    await handle_level_scan(mock_update, mock_context, "standard")

    # Проверяем сообщение о пустых результатах
    calls = mock_update.callback_query.edit_message_text.call_args_list
    final_call = calls[-1]
    assert "Возможности не найдены" in final_call[0][0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
async def test_handle_level_scan_exception(
    mock_scanner_class,
    mock_api_client,
    mock_update,
    mock_context,
):
    """Тест обработки исключения в handle_level_scan."""
    mock_api_client.return_value = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.scan_level = AsyncMock(side_effect=Exception("API Error"))
    mock_scanner_class.return_value = mock_scanner

    await handle_level_scan(mock_update, mock_context, "standard")

    # Проверяем сообщение об ошибке
    calls = mock_update.callback_query.edit_message_text.call_args_list
    error_call = calls[-1]
    assert "Произошла ошибка" in error_call[0][0]


# ======================== Тесты handle_market_overview ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
async def test_handle_market_overview_success(
    mock_scanner_class,
    mock_api_client,
    mock_update,
    mock_context,
):
    """Тест успешного получения обзора рынка."""
    # Настраиваем моки
    mock_api_client.return_value = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.get_market_overview = AsyncMock(
        return_value={
            "total_opportunities": 42,
            "best_profit_percent": 15.5,
            "best_level": "standard",
            "results_by_level": {
                "boost": 10,
                "standard": 20,
                "medium": 12,
            },
        }
    )
    mock_scanner_class.return_value = mock_scanner

    await handle_market_overview(mock_update, mock_context, "csgo")

    # Проверяем вызовы
    mock_update.callback_query.answer.assert_called_once()
    mock_scanner.get_market_overview.assert_called_once_with(game="csgo")

    # Проверяем финальное сообщение
    calls = mock_update.callback_query.edit_message_text.call_args_list
    final_call = calls[-1]
    text = final_call[0][0]

    assert "Обзор рынка" in text
    assert "42" in text  # total_opportunities
    assert "15.5%" in text  # best_profit_percent


@pytest.mark.asyncio()
async def test_handle_market_overview_no_callback_query(mock_update, mock_context):
    """Тест handle_market_overview без callback query."""
    mock_update.callback_query = None

    await handle_market_overview(mock_update, mock_context)

    # Функция должна завершиться без действий


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
async def test_handle_market_overview_api_client_none(
    mock_api_client,
    mock_update,
    mock_context,
):
    """Тест handle_market_overview когда API клиент не создан."""
    mock_api_client.return_value = None

    await handle_market_overview(mock_update, mock_context)

    # Проверяем сообщение об ошибке
    calls = mock_update.callback_query.edit_message_text.call_args_list
    error_call = calls[-1]
    assert "Не удалось создать API клиент" in error_call[0][0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
async def test_handle_market_overview_exception(
    mock_scanner_class,
    mock_api_client,
    mock_update,
    mock_context,
):
    """Тест обработки исключения в handle_market_overview."""
    mock_api_client.return_value = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.get_market_overview = AsyncMock(side_effect=Exception("Scanner Error"))
    mock_scanner_class.return_value = mock_scanner

    await handle_market_overview(mock_update, mock_context)

    # Проверяем сообщение об ошибке
    calls = mock_update.callback_query.edit_message_text.call_args_list
    error_call = calls[-1]
    assert "Ошибка" in error_call[0][0]


# ======================== Тесты handle_scanner_pagination ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.pagination_manager")
@patch("src.telegram_bot.handlers.scanner_handler.create_pagination_keyboard")
async def test_handle_scanner_pagination_next(
    mock_keyboard,
    mock_pagination,
    mock_update,
    mock_context,
    sample_arbitrage_results,
):
    """Тест пагинации - следующая страница."""
    mock_update.callback_query.data = "scanner_paginate:next:standard_csgo_"

    mock_pagination.get_page.return_value = (sample_arbitrage_results, 1, 3)
    mock_pagination.get_items_per_page.return_value = 10
    mock_keyboard.return_value = InlineKeyboardMarkup([])

    await handle_scanner_pagination(mock_update, mock_context)

    # Проверяем вызов next_page
    mock_pagination.next_page.assert_called_once_with(123456789)
    mock_update.callback_query.answer.assert_called_once()
    mock_update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.pagination_manager")
@patch("src.telegram_bot.handlers.scanner_handler.create_pagination_keyboard")
async def test_handle_scanner_pagination_prev(
    mock_keyboard,
    mock_pagination,
    mock_update,
    mock_context,
    sample_arbitrage_results,
):
    """Тест пагинации - предыдущая страница."""
    mock_update.callback_query.data = "scanner_paginate:prev:standard_csgo_"

    mock_pagination.get_page.return_value = (sample_arbitrage_results, 0, 3)
    mock_pagination.get_items_per_page.return_value = 10
    mock_keyboard.return_value = InlineKeyboardMarkup([])

    await handle_scanner_pagination(mock_update, mock_context)

    # Проверяем вызов prev_page
    mock_pagination.prev_page.assert_called_once_with(123456789)


@pytest.mark.asyncio()
async def test_handle_scanner_pagination_no_callback_query(mock_update, mock_context):
    """Тест пагинации без callback query."""
    mock_update.callback_query = None

    await handle_scanner_pagination(mock_update, mock_context)

    # Функция должна завершиться без действий


@pytest.mark.asyncio()
async def test_handle_scanner_pagination_invalid_data(mock_update, mock_context):
    """Тест пагинации с некорректными данными."""
    mock_update.callback_query.data = "scanner_paginate:invalid"

    await handle_scanner_pagination(mock_update, mock_context)

    # Проверяем, что answer был вызван, но edit не был
    mock_update.callback_query.answer.assert_called_once()
    mock_update.callback_query.edit_message_text.assert_not_called()


# ======================== Тесты handle_scanner_callback ========================


@pytest.mark.asyncio()
async def test_handle_scanner_callback_main_menu(mock_update, mock_context):
    """Тест callback для главного меню сканера."""
    mock_update.callback_query.data = SCANNER_ACTION

    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем вызов start_scanner_menu
    mock_update.callback_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.handle_level_scan")
async def test_handle_scanner_callback_level_scan(
    mock_level_scan,
    mock_update,
    mock_context,
):
    """Тест callback для сканирования уровня."""
    mock_update.callback_query.data = f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_boost"
    mock_level_scan.return_value = AsyncMock()

    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем вызов handle_level_scan
    mock_level_scan.assert_called_once_with(mock_update, mock_context, "boost")


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.handle_market_overview")
async def test_handle_scanner_callback_market_overview(
    mock_overview,
    mock_update,
    mock_context,
):
    """Тест callback для обзора рынка."""
    mock_update.callback_query.data = f"{SCANNER_ACTION}_{MARKET_OVERVIEW_ACTION}"
    mock_overview.return_value = AsyncMock()

    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем вызов handle_market_overview
    mock_overview.assert_called_once_with(mock_update, mock_context)


@pytest.mark.asyncio()
async def test_handle_scanner_callback_unknown_action(mock_update, mock_context):
    """Тест callback для неизвестного действия."""
    mock_update.callback_query.data = f"{SCANNER_ACTION}_unknown_action"

    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer с сообщением
    mock_update.callback_query.answer.assert_called_once()
    call_args = mock_update.callback_query.answer.call_args
    assert "будет реализована" in call_args[0][0]


@pytest.mark.asyncio()
async def test_handle_scanner_callback_no_callback_query(mock_update, mock_context):
    """Тест handle_scanner_callback без callback query."""
    mock_update.callback_query = None

    await handle_scanner_callback(mock_update, mock_context)

    # Функция должна завершиться без действий


# ======================== Тесты register_scanner_handlers ========================


def test_register_scanner_handlers():
    """Тест регистрации обработчиков сканера."""
    mock_dispatcher = MagicMock()

    register_scanner_handlers(mock_dispatcher)

    # Проверяем, что add_handler был вызван дважды
    assert mock_dispatcher.add_handler.call_count == 2

    # Проверяем типы обработчиков
    from telegram.ext import CallbackQueryHandler

    for call in mock_dispatcher.add_handler.call_args_list:
        handler = call[0][0]
        assert isinstance(handler, CallbackQueryHandler)


# ======================== Интеграционные тесты ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.scanner_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.scanner_handler.ArbitrageScanner")
@patch("src.telegram_bot.handlers.scanner_handler.pagination_manager")
@patch("src.telegram_bot.handlers.scanner_handler.create_pagination_keyboard")
async def test_integration_full_scan_workflow(
    mock_keyboard,
    mock_pagination,
    mock_scanner_class,
    mock_api_client,
    mock_update,
    mock_context,
    sample_arbitrage_results,
):
    """Интеграционный тест: полный workflow сканирования."""
    # 1. Открываем главное меню
    mock_update.callback_query.data = SCANNER_ACTION
    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем, что меню открылось
    assert mock_update.callback_query.edit_message_text.called

    # 2. Выбираем уровень для сканирования
    mock_api_client.return_value = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.scan_level = AsyncMock(return_value=sample_arbitrage_results)
    mock_scanner_class.return_value = mock_scanner

    mock_pagination.add_items_for_user = MagicMock()
    mock_pagination.get_page.return_value = (sample_arbitrage_results, 0, 1)
    mock_pagination.get_items_per_page.return_value = 10
    mock_keyboard.return_value = InlineKeyboardMarkup([])

    mock_update.callback_query.data = f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_standard"
    await handle_scanner_callback(mock_update, mock_context)

    # Проверяем, что сканирование выполнено
    mock_scanner.scan_level.assert_called_once()

    # 3. Проверяем пагинацию
    mock_update.callback_query.data = "scanner_paginate:next:standard_csgo_"
    await handle_scanner_pagination(mock_update, mock_context)

    # Проверяем, что пагинация работает
    mock_pagination.next_page.assert_called_once()


@pytest.mark.asyncio()
async def test_integration_all_menu_buttons_work(mock_update, mock_context):
    """Интеграционный тест: все кнопки меню работают."""
    # Открываем меню
    mock_update.callback_query.data = SCANNER_ACTION
    await handle_scanner_callback(mock_update, mock_context)

    # Получаем клавиатуру
    call_args = mock_update.callback_query.edit_message_text.call_args
    keyboard = call_args[1]["reply_markup"].inline_keyboard

    # Проверяем, что все кнопки имеют корректные callback_data
    for row in keyboard:
        for button in row:
            assert button.callback_data is not None
            assert len(button.callback_data) > 0


# ======================== Тесты граничных случаев ========================


@pytest.mark.asyncio()
async def test_handle_level_scan_no_effective_user(mock_update, mock_context):
    """Тест handle_level_scan без effective_user."""
    mock_update.effective_user = None

    await handle_level_scan(mock_update, mock_context, "standard")

    # Проверяем, что функция завершилась без ошибок
    # edit_message_text не должен быть вызван после проверки user


@pytest.mark.asyncio()
async def test_handle_scanner_pagination_no_effective_user(mock_update, mock_context):
    """Тест пагинации без effective_user."""
    mock_update.effective_user = None
    mock_update.callback_query.data = "scanner_paginate:next:standard_csgo_"

    await handle_scanner_pagination(mock_update, mock_context)

    # Проверяем, что answer был вызван, но дальнейшая обработка не произошла
    mock_update.callback_query.answer.assert_called_once()


def test_format_scanner_results_large_page_number():
    """Тест форматирования с большим номером страницы."""
    result = format_scanner_results([{"title": "Item"}], 99, 10)

    assert "Страница 100" in result  # current_page + 1

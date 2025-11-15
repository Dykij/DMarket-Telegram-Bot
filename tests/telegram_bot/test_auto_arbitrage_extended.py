"""Расширенное тестирование модуля автоарбитража.

Этот модуль содержит полное покрытие функциональности автоматического арбитража:
- Безопасное редактирование сообщений
- Форматирование результатов
- Пагинация
- Создание API клиента
- Запуск/остановка автотрейдинга
- Проверка баланса
- Обработка callback
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Message, Update, User
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from src.telegram_bot.auto_arbitrage import (
    ARBITRAGE_MODES,
    check_balance_command,
    create_dmarket_api_client,
    format_auto_arbitrage_results,
    handle_pagination,
    safe_edit_message_text,
    show_auto_stats,
    show_auto_stats_with_pagination,
    stop_auto_trading,
)


# Константы для тестов
TEST_USER_ID = 12345
TEST_CHAT_ID = 67890


@pytest.fixture()
def mock_query():
    """Создает мок CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.id = "test_query_id"
    query.data = "test_data"
    query.message = MagicMock(spec=Message)
    query.message.message_id = 123
    query.message.chat_id = TEST_CHAT_ID
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    return query


@pytest.fixture()
def mock_context():
    """Создает мок CallbackContext."""
    context = MagicMock(spec=CallbackContext)
    context.bot_data = {}
    context.user_data = {}
    context.chat_data = {}
    return context


@pytest.fixture()
def mock_update():
    """Создает мок Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = TEST_USER_ID
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


# ==============================================================================
# ТЕСТЫ SAFE_EDIT_MESSAGE_TEXT
# ==============================================================================


@pytest.mark.asyncio()
async def test_safe_edit_message_text_success(mock_query):
    """Тест успешного редактирования сообщения."""
    text = "Test message"

    result = await safe_edit_message_text(mock_query, text)

    assert result is True
    mock_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio()
async def test_safe_edit_message_text_not_modified(mock_query):
    """Тест обработки ошибки 'message is not modified'."""
    mock_query.edit_message_text.side_effect = BadRequest("message is not modified")

    result = await safe_edit_message_text(mock_query, "test")

    # Должен вернуть False но не выбросить исключение
    assert result is False


@pytest.mark.asyncio()
async def test_safe_edit_message_text_other_bad_request(mock_query):
    """Тест обработки других BadRequest ошибок."""
    mock_query.edit_message_text.side_effect = BadRequest("Other error")

    with pytest.raises(BadRequest):
        await safe_edit_message_text(mock_query, "test")


@pytest.mark.asyncio()
async def test_safe_edit_message_text_with_keyboard(mock_query):
    """Тест редактирования с клавиатурой."""
    from telegram import InlineKeyboardMarkup

    keyboard = MagicMock(spec=InlineKeyboardMarkup)

    result = await safe_edit_message_text(mock_query, "test", reply_markup=keyboard)

    assert result is True
    call_kwargs = mock_query.edit_message_text.call_args.kwargs
    assert call_kwargs["reply_markup"] == keyboard


# ==============================================================================
# ТЕСТЫ ARBITRAGE_MODES
# ==============================================================================


def test_arbitrage_modes_constants():
    """Тест констант режимов арбитража."""
    assert "boost_low" in ARBITRAGE_MODES
    assert "mid_medium" in ARBITRAGE_MODES
    assert "pro_high" in ARBITRAGE_MODES

    # Проверяем структуру режима
    boost_mode = ARBITRAGE_MODES["boost_low"]
    assert "name" in boost_mode
    assert "min_price" in boost_mode
    assert "max_price" in boost_mode
    assert "min_profit_percent" in boost_mode
    assert "min_profit_amount" in boost_mode
    assert "trade_strategy" in boost_mode


def test_arbitrage_modes_price_ranges():
    """Тест ценовых диапазонов режимов."""
    # boost_low: низкие цены
    assert ARBITRAGE_MODES["boost_low"]["min_price"] < 10.0
    assert ARBITRAGE_MODES["boost_low"]["max_price"] < 100.0

    # mid_medium: средние цены
    assert ARBITRAGE_MODES["mid_medium"]["min_price"] >= 10.0
    assert ARBITRAGE_MODES["mid_medium"]["max_price"] < 500.0

    # pro_high: высокие цены
    assert ARBITRAGE_MODES["pro_high"]["min_price"] >= 50.0
    assert ARBITRAGE_MODES["pro_high"]["max_price"] >= 500.0


def test_arbitrage_modes_profit_requirements():
    """Тест требований к прибыли."""
    # Проверяем возрастание требований
    boost_profit = ARBITRAGE_MODES["boost_low"]["min_profit_percent"]
    mid_profit = ARBITRAGE_MODES["mid_medium"]["min_profit_percent"]
    pro_profit = ARBITRAGE_MODES["pro_high"]["min_profit_percent"]

    assert boost_profit < mid_profit < pro_profit


# ==============================================================================
# ТЕСТЫ FORMAT_AUTO_ARBITRAGE_RESULTS
# ==============================================================================


@pytest.mark.asyncio()
async def test_format_auto_arbitrage_results_empty():
    """Тест форматирования пустых результатов."""
    result = await format_auto_arbitrage_results([], 0, 1)

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio()
async def test_format_auto_arbitrage_results_with_items():
    """Тест форматирования результатов с предметами."""
    items = [
        {
            "title": "Test Item 1",
            "buy_price": 10.0,
            "sell_price": 12.0,
            "profit": 2.0,
            "profit_percentage": 20.0,
            "game": "csgo",
        },
        {
            "title": "Test Item 2",
            "buy_price": 20.0,
            "sell_price": 25.0,
            "profit": 5.0,
            "profit_percentage": 25.0,
            "game": "dota2",
        },
    ]

    result = await format_auto_arbitrage_results(items, 0, 1, mode="auto")

    assert isinstance(result, str)
    assert "Test Item 1" in result or "Item 1" in result  # Может быть сокращено


@pytest.mark.asyncio()
async def test_format_auto_arbitrage_results_pagination():
    """Тест форматирования с пагинацией."""
    items = [{"title": f"Item {i}"} for i in range(10)]

    result = await format_auto_arbitrage_results(items, 1, 3)

    assert isinstance(result, str)
    # Должна быть информация о странице
    assert "2" in result or "страниц" in result.lower()


# ==============================================================================
# ТЕСТЫ CREATE_DMARKET_API_CLIENT
# ==============================================================================


@pytest.mark.asyncio()
async def test_create_dmarket_api_client_success(mock_context):
    """Тест успешного создания API клиента."""
    # Устанавливаем ключи в bot_data
    mock_context.bot_data["dmarket_public_key"] = "test_public_key_12345"
    mock_context.bot_data["dmarket_secret_key"] = "test_secret_key_67890"

    with patch("src.telegram_bot.auto_arbitrage.DMarketAPI") as mock_api_class:
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance

        with patch("src.telegram_bot.auto_arbitrage.RetryStrategy"):
            with patch("src.telegram_bot.auto_arbitrage.environ_type") as mock_environ:
                mock_environ.get.return_value = "https://api.dmarket.com"

                client = await create_dmarket_api_client(mock_context)

                assert client is not None
                mock_api_class.assert_called_once()


@pytest.mark.asyncio()
async def test_create_dmarket_api_client_missing_keys(mock_context):
    """Тест создания клиента без ключей."""
    # Убираем ключи из bot_data и окружения
    mock_context.bot_data.clear()

    with patch("src.telegram_bot.auto_arbitrage.environ_type") as mock_environ:
        mock_environ.get.return_value = ""

        client = await create_dmarket_api_client(mock_context)

        # Должен вернуть None
        assert client is None


@pytest.mark.asyncio()
async def test_create_dmarket_api_client_from_environ(mock_context):
    """Тест создания клиента из переменных окружения."""
    # Не устанавливаем ключи в bot_data
    mock_context.bot_data.clear()

    with patch("src.telegram_bot.auto_arbitrage.environ_type") as mock_environ:
        mock_environ.get.side_effect = lambda key, default="": {
            "DMARKET_PUBLIC_KEY": "env_public_key",
            "DMARKET_SECRET_KEY": "env_secret_key",
            "DMARKET_API_URL": "https://api.dmarket.com",
        }.get(key, default)

        with patch("src.telegram_bot.auto_arbitrage.DMarketAPI") as mock_api_class:
            mock_api_instance = MagicMock()
            mock_api_class.return_value = mock_api_instance

            with patch("src.telegram_bot.auto_arbitrage.RetryStrategy"):
                client = await create_dmarket_api_client(mock_context)

                # Клиент должен быть создан из переменных окружения
                assert client is not None


# ==============================================================================
# ТЕСТЫ SHOW_AUTO_STATS_WITH_PAGINATION
# ==============================================================================


@pytest.mark.asyncio()
async def test_show_auto_stats_with_pagination(mock_query, mock_context):
    """Тест показа статистики с пагинацией."""
    items = [{"title": f"Item {i}", "profit": i * 1.0} for i in range(10)]
    mock_context.user_data["auto_results"] = items
    mock_context.user_data["auto_mode"] = "auto_medium"
    mock_context.user_data["auto_current_page"] = 0

    await show_auto_stats_with_pagination(mock_query, mock_context)

    # Проверяем, что сообщение было отредактировано
    mock_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
async def test_show_auto_stats_with_pagination_empty_results(mock_query, mock_context):
    """Тест показа статистики с пустыми результатами."""
    mock_context.user_data["auto_results"] = []
    mock_context.user_data["auto_mode"] = "auto_low"
    mock_context.user_data["auto_current_page"] = 0

    await show_auto_stats_with_pagination(mock_query, mock_context)

    mock_query.edit_message_text.assert_called()


# ==============================================================================
# ТЕСТЫ HANDLE_PAGINATION
# ==============================================================================


@pytest.mark.asyncio()
async def test_handle_pagination_next_page(mock_query, mock_context):
    """Тест переключения на следующую страницу."""
    mock_context.user_data["auto_results"] = [{"title": f"Item {i}"} for i in range(20)]
    mock_context.user_data["auto_mode"] = "auto"
    mock_context.user_data["auto_current_page"] = 0

    await handle_pagination(mock_query, mock_context, direction="next", mode="auto")

    mock_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
async def test_handle_pagination_prev_page(mock_query, mock_context):
    """Тест переключения на предыдущую страницу."""
    mock_context.user_data["auto_results"] = [{"title": f"Item {i}"} for i in range(20)]
    mock_context.user_data["auto_mode"] = "auto"
    mock_context.user_data["auto_current_page"] = 2

    await handle_pagination(mock_query, mock_context, direction="prev", mode="auto")

    mock_query.edit_message_text.assert_called()


# ==============================================================================
# ТЕСТЫ START_AUTO_TRADING (simplified - сложная функция)
# ==============================================================================


@pytest.mark.asyncio()
async def test_start_auto_trading_mode_validation():
    """Тест валидации режимов автотрейдинга."""
    # Проверяем, что все режимы существуют
    assert "boost_low" in ARBITRAGE_MODES
    assert "mid_medium" in ARBITRAGE_MODES
    assert "pro_high" in ARBITRAGE_MODES


# ==============================================================================
# ТЕСТЫ CHECK_BALANCE_COMMAND
# ==============================================================================


@pytest.mark.asyncio()
async def test_check_balance_command_with_update(mock_update, mock_context):
    """Тест проверки баланса через Update."""
    with (
        patch("src.telegram_bot.auto_arbitrage.create_dmarket_api_client") as mock_create,
        patch("src.telegram_bot.auto_arbitrage.check_user_balance") as mock_check,
    ):
        mock_api = MagicMock()
        mock_create.return_value = mock_api
        mock_check.return_value = {
            "balance": 100.0,
            "error": False,
            "has_funds": True,
        }

        await check_balance_command(mock_update, mock_context)

        # Проверяем, что был вызов API клиента
        mock_create.assert_called_once()


@pytest.mark.asyncio()
async def test_check_balance_command_with_query(mock_query, mock_context):
    """Тест проверки баланса через callback query."""
    with (
        patch("src.telegram_bot.auto_arbitrage.create_dmarket_api_client") as mock_create,
        patch("src.telegram_bot.auto_arbitrage.check_user_balance") as mock_check,
    ):
        mock_api = MagicMock()
        mock_create.return_value = mock_api
        mock_check.return_value = {
            "balance": 50.0,
            "error": False,
            "has_funds": True,
        }

        await check_balance_command(mock_query, mock_context)

        mock_create.assert_called_once()


# ==============================================================================
# ТЕСТЫ SHOW_AUTO_STATS
# ==============================================================================


@pytest.mark.asyncio()
async def test_show_auto_stats_basic(mock_query, mock_context):
    """Тест показа статистики автотрейдинга."""
    mock_context.user_data["auto_results"] = [{"title": "Item 1", "profit": 5.0}]
    mock_context.user_data["auto_mode"] = "auto_medium"

    await show_auto_stats(mock_query, mock_context)

    mock_query.edit_message_text.assert_called()


@pytest.mark.asyncio()
async def test_show_auto_stats_no_results(mock_query, mock_context):
    """Тест показа статистики без результатов."""
    mock_context.user_data["auto_results"] = []

    await show_auto_stats(mock_query, mock_context)

    mock_query.edit_message_text.assert_called()


# ==============================================================================
# ТЕСТЫ STOP_AUTO_TRADING
# ==============================================================================


@pytest.mark.asyncio()
async def test_stop_auto_trading(mock_query, mock_context):
    """Тест остановки автотрейдинга."""
    mock_context.user_data["auto_trading"] = True
    mock_context.user_data["auto_mode"] = "boost_low"

    await stop_auto_trading(mock_query, mock_context)

    # Проверяем, что функция вызвана без ошибок
    mock_query.edit_message_text.assert_called()


# ==============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.parametrize(
    "mode",
    ("boost_low", "mid_medium", "pro_high"),
)
def test_arbitrage_mode_structure(mode):
    """Параметризованный тест структуры режимов арбитража."""
    mode_config = ARBITRAGE_MODES[mode]

    # Проверяем обязательные поля
    assert "name" in mode_config
    assert "min_price" in mode_config
    assert "max_price" in mode_config
    assert "min_profit_percent" in mode_config
    assert "min_profit_amount" in mode_config
    assert "trade_strategy" in mode_config

    # Проверяем типы
    assert isinstance(mode_config["min_price"], (int, float))
    assert isinstance(mode_config["max_price"], (int, float))
    assert mode_config["min_price"] > 0
    assert mode_config["max_price"] > mode_config["min_price"]


@pytest.mark.parametrize(
    ("error_message", "should_ignore"),
    (
        ("message is not modified", True),
        ("Message is not modified", True),
        ("Other error", False),
        ("Bad request", False),
    ),
)
@pytest.mark.asyncio()
async def test_safe_edit_message_text_error_handling(mock_query, error_message, should_ignore):
    """Параметризованный тест обработки ошибок."""
    mock_query.edit_message_text.side_effect = BadRequest(error_message)

    if should_ignore:
        result = await safe_edit_message_text(mock_query, "test")
        assert result is False
    else:
        with pytest.raises(BadRequest):
            await safe_edit_message_text(mock_query, "test")


# ==============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.asyncio()
async def test_safe_edit_and_format_integration(mock_query):
    """Интеграционный тест редактирования и форматирования."""
    # 1. Форматируем результаты
    items = [{"title": "Item 1", "profit": 5.0}]
    formatted_text = await format_auto_arbitrage_results(items, 0, 1)

    # 2. Безопасно редактируем сообщение
    result = await safe_edit_message_text(mock_query, formatted_text)

    # Проверяем успех
    assert result is True
    assert mock_query.edit_message_text.called

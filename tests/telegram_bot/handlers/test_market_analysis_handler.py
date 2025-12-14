"""Тесты для обработчика анализа рынка."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update, User

from src.telegram_bot.handlers.market_analysis_handler import (
    get_back_to_market_analysis_keyboard,
    handle_pagination_analysis,
    handle_period_change,
    handle_risk_level_change,
    market_analysis_callback,
    market_analysis_command,
    register_market_analysis_handlers,
    show_investment_recommendations_results,
    show_market_report,
    show_price_changes_results,
    show_trending_items_results,
    show_undervalued_items_results,
    show_volatility_results,
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
def mock_message(mock_user):
    """Создать мок объекта Message."""
    message = MagicMock()
    message.reply_text = AsyncMock()
    message.from_user = mock_user
    return message


@pytest.fixture()
def mock_callback_query(mock_user):
    """Создать мок объекта CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = "analysis:price_changes:csgo"
    query.from_user = mock_user
    return query


@pytest.fixture()
def mock_update(mock_user, mock_callback_query, mock_message):
    """Создать мок объекта Update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.effective_user = mock_user
    update.message = mock_message
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456789
    return update


@pytest.fixture()
def mock_context():
    """Создать мок объекта CallbackContext."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    context.args = []
    return context


@pytest.fixture()
def sample_price_changes():
    """Создать пример данных изменения цен."""
    return [
        {
            "market_hash_name": "AK-47 | Redline (Field-Tested)",
            "current_price": 12.50,
            "price_change": 2.00,
            "change_percent": 19.0,
            "volume": 150,
            "liquidity": "high",
        },
        {
            "market_hash_name": "AWP | Asiimov (Battle-Scarred)",
            "current_price": 25.00,
            "price_change": -1.50,
            "change_percent": -5.7,
            "volume": 80,
            "liquidity": "medium",
        },
    ]


@pytest.fixture()
def sample_trending_items():
    """Создать пример трендовых предметов."""
    return [
        {
            "market_hash_name": "Butterfly Knife | Fade (Factory New)",
            "current_price": 850.00,
            "trend": "upward",
            "volume": 25,
            "sales_24h": 12,
        },
        {
            "market_hash_name": "M4A4 | Howl (Field-Tested)",
            "current_price": 1200.00,
            "trend": "stable",
            "volume": 10,
            "sales_24h": 5,
        },
    ]


@pytest.fixture()
def sample_volatility_data():
    """Создать пример данных волатильности."""
    return [
        {
            "market_hash_name": "Karambit | Doppler (Factory New)",
            "current_price": 950.00,
            "change_24h_percent": 5.2,
            "change_7d_percent": -3.1,
            "volatility_score": 25.5,
        },
        {
            "market_hash_name": "AK-47 | Fire Serpent (Minimal Wear)",
            "current_price": 450.00,
            "change_24h_percent": -2.1,
            "change_7d_percent": 8.3,
            "volatility_score": 15.2,
        },
    ]


@pytest.fixture()
def sample_market_report():
    """Создать пример рыночного отчета."""
    return {
        "game": "csgo",
        "market_summary": {
            "price_change_direction": "up",
            "market_volatility_level": "medium",
            "top_trending_categories": ["Knife", "Rifle", "Pistol"],
            "recommended_actions": [
                "Купить ножи - растущий тренд",
                "Продать AWP - высокая волатильность",
            ],
        },
        "price_changes": [
            {
                "market_hash_name": "Butterfly Knife | Fade (FN)",
                "change_percent": 12.5,
            },
        ],
        "trending_items": [
            {
                "market_hash_name": "AK-47 | Redline (FT)",
                "sales_volume": 150,
            },
        ],
    }


@pytest.fixture()
def sample_undervalued_items():
    """Создать пример недооцененных предметов."""
    return [
        {
            "title": "AWP | Dragon Lore (Minimal Wear)",
            "current_price": 3500.00,
            "avg_price": 4000.00,
            "discount": 12.5,
            "trend": "upward",
            "volume": 5,
        },
    ]


@pytest.fixture()
def sample_recommendations():
    """Создать пример инвестиционных рекомендаций."""
    return [
        {
            "title": "M4A1-S | Hot Rod (Factory New)",
            "current_price": 85.00,
            "discount": 15.0,
            "liquidity": "high",
            "investment_score": 8.5,
            "reason": "Высокая ликвидность, растущий тренд",
        },
    ]


# ======================== Тесты market_analysis_command ========================


@pytest.mark.asyncio()
async def test_market_analysis_command_success(mock_update, mock_context):
    """Тест успешного вызова команды анализа рынка."""
    await market_analysis_command(mock_update, mock_context)

    # Проверяем что сообщение отправлено
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args

    # Проверяем содержимое сообщения
    assert "Анализ рынка DMarket" in args[0]
    assert "reply_markup" in kwargs
    assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio()
async def test_market_analysis_command_creates_keyboard(mock_update, mock_context):
    """Тест создания клавиатуры для анализа рынка."""
    await market_analysis_command(mock_update, mock_context)

    _args, kwargs = mock_update.message.reply_text.call_args
    keyboard = kwargs["reply_markup"]

    # Проверяем наличие кнопок
    assert len(keyboard.inline_keyboard) > 0

    # Проверяем наличие основных кнопок анализа
    button_texts = [button.text for row in keyboard.inline_keyboard for button in row]

    assert any("Изменения цен" in text for text in button_texts)
    assert any("Трендовые предметы" in text for text in button_texts)
    assert any("Волатильность" in text for text in button_texts)


# ======================== Тесты market_analysis_callback ========================


@pytest.mark.asyncio()
async def test_market_analysis_callback_select_game(mock_update, mock_context):
    """Тест выбора игры через колбэк."""
    mock_update.callback_query.data = "analysis:select_game:dota2"

    await market_analysis_callback(mock_update, mock_context)

    # Проверяем обновление сообщения
    mock_update.callback_query.edit_message_text.assert_called_once()
    args, _kwargs = mock_update.callback_query.edit_message_text.call_args

    # Проверяем что игра обновлена в тексте
    assert "Dota 2" in args[0]


@pytest.mark.asyncio()
async def test_market_analysis_callback_initializes_user_data(mock_update, mock_context):
    """Тест инициализации данных пользователя."""
    mock_update.callback_query.data = "analysis:select_game:csgo"

    await market_analysis_callback(mock_update, mock_context)

    # Проверяем создание структуры данных
    assert "market_analysis" in mock_context.user_data
    assert "current_game" in mock_context.user_data["market_analysis"]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
@patch("src.telegram_bot.handlers.market_analysis_handler.analyze_price_changes")
async def test_market_analysis_callback_price_changes(
    mock_analyze, mock_api_client, mock_update, mock_context, sample_price_changes
):
    """Тест анализа изменений цен через колбэк."""
    mock_update.callback_query.data = "analysis:price_changes:csgo"
    mock_context.user_data["market_analysis"] = {
        "current_game": "csgo",
        "period": "24h",
    }

    # Настройка моков
    mock_api_client.return_value = MagicMock()
    mock_analyze.return_value = sample_price_changes

    await market_analysis_callback(mock_update, mock_context)

    # Проверяем что API клиент создан
    mock_api_client.assert_called_once()

    # Проверяем что анализ вызван
    mock_analyze.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
async def test_market_analysis_callback_api_error(mock_api_client, mock_update, mock_context):
    """Тест обработки ошибки API при колбэке."""
    mock_update.callback_query.data = "analysis:trending:csgo"
    mock_context.user_data["market_analysis"] = {"current_game": "csgo"}

    # Настройка мока для возврата None (ошибка API)
    mock_api_client.return_value = None

    await market_analysis_callback(mock_update, mock_context)

    # Проверяем сообщение об ошибке
    mock_update.callback_query.edit_message_text.assert_called()
    args = mock_update.callback_query.edit_message_text.call_args[0]
    assert "Не удалось создать API клиент" in args[0]


# ======================== Тесты show_* функций ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_show_price_changes_results_success(
    mock_pagination, mock_callback_query, mock_context, sample_price_changes
):
    """Тест отображения результатов изменения цен."""
    # Настройка пагинации
    mock_pagination.get_page.return_value = (sample_price_changes, 0, 1)
    mock_pagination.get_items_per_page.return_value = 5

    await show_price_changes_results(mock_callback_query, mock_context, "csgo")

    # Проверяем вызов редактирования сообщения
    mock_callback_query.edit_message_text.assert_called_once()
    args, kwargs = mock_callback_query.edit_message_text.call_args

    # Проверяем содержимое
    assert "Анализ изменений цен" in args[0]
    assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_show_price_changes_results_empty(mock_pagination, mock_callback_query, mock_context):
    """Тест отображения пустых результатов изменения цен."""
    # Настройка пагинации - пустой список
    mock_pagination.get_page.return_value = ([], 0, 0)

    await show_price_changes_results(mock_callback_query, mock_context, "csgo")

    # Проверяем сообщение о пустых результатах
    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Не найдено изменений цен" in args[0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_show_trending_items_results(
    mock_pagination, mock_callback_query, mock_context, sample_trending_items
):
    """Тест отображения трендовых предметов."""
    mock_pagination.get_page.return_value = (sample_trending_items, 0, 1)
    mock_pagination.get_items_per_page.return_value = 5

    await show_trending_items_results(mock_callback_query, mock_context, "csgo")

    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Трендовые предметы" in args[0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_show_volatility_results(
    mock_pagination, mock_callback_query, mock_context, sample_volatility_data
):
    """Тест отображения результатов волатильности."""
    mock_pagination.get_page.return_value = (sample_volatility_data, 0, 1)

    await show_volatility_results(mock_callback_query, mock_context, "csgo")

    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Анализ волатильности" in args[0]


@pytest.mark.asyncio()
async def test_show_market_report(mock_callback_query, mock_context, sample_market_report):
    """Тест отображения рыночного отчета."""
    await show_market_report(mock_callback_query, mock_context, sample_market_report)

    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Отчет о состоянии рынка" in args[0]
    assert "Растущий" in args[0]  # направление рынка


@pytest.mark.asyncio()
async def test_show_market_report_with_error(mock_callback_query, mock_context):
    """Тест отображения отчета с ошибкой."""
    error_report = {"error": "Test error message", "game": "csgo"}

    await show_market_report(mock_callback_query, mock_context, error_report)

    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Произошла ошибка" in args[0]
    assert "Test error message" in args[0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_show_undervalued_items_results(
    mock_pagination, mock_callback_query, mock_context, sample_undervalued_items
):
    """Тест отображения недооцененных предметов."""
    mock_pagination.get_page.return_value = (sample_undervalued_items, 0, 1)

    await show_undervalued_items_results(mock_callback_query, mock_context, "csgo")

    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Недооцененные предметы" in args[0]


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_show_investment_recommendations_results(
    mock_pagination, mock_callback_query, mock_context, sample_recommendations
):
    """Тест отображения инвестиционных рекомендаций."""
    mock_pagination.get_page.return_value = (sample_recommendations, 0, 1)

    await show_investment_recommendations_results(mock_callback_query, mock_context, "csgo")

    mock_callback_query.edit_message_text.assert_called_once()
    args = mock_callback_query.edit_message_text.call_args[0]
    assert "Инвестиционные рекомендации" in args[0]


# ======================== Тесты handle_pagination_analysis ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_handle_pagination_analysis_next_page(
    mock_pagination, mock_update, mock_context, sample_price_changes
):
    """Тест перехода на следующую страницу."""
    mock_update.callback_query.data = "analysis_page:next:price_changes:csgo"
    mock_pagination.get_page.return_value = (sample_price_changes, 1, 2)
    mock_pagination.get_items_per_page.return_value = 5

    await handle_pagination_analysis(mock_update, mock_context)

    # Проверяем вызов next_page
    mock_pagination.next_page.assert_called_once_with(123456789)


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
async def test_handle_pagination_analysis_prev_page(
    mock_pagination, mock_update, mock_context, sample_trending_items
):
    """Тест перехода на предыдущую страницу."""
    mock_update.callback_query.data = "analysis_page:prev:trending:csgo"
    mock_pagination.get_page.return_value = (sample_trending_items, 0, 2)
    mock_pagination.get_items_per_page.return_value = 5

    await handle_pagination_analysis(mock_update, mock_context)

    # Проверяем вызов prev_page
    mock_pagination.prev_page.assert_called_once_with(123456789)


# ======================== Тесты handle_period_change ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.market_analysis_callback")
async def test_handle_period_change(mock_callback_func, mock_update, mock_context):
    """Тест изменения периода анализа."""
    mock_update.callback_query.data = "period_change:7d:csgo"
    mock_update.callback_query.answer = AsyncMock()

    await handle_period_change(mock_update, mock_context)

    # Проверяем обновление периода
    assert mock_context.user_data["market_analysis"]["period"] == "7d"

    # Проверяем ответ пользователю (может быть вызван несколько раз)
    mock_update.callback_query.answer.assert_called()


# ======================== Тесты handle_risk_level_change ========================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.market_analysis_handler.market_analysis_callback")
async def test_handle_risk_level_change(mock_callback_func, mock_update, mock_context):
    """Тест изменения уровня риска."""
    mock_update.callback_query.data = "analysis_risk:high:csgo"
    mock_update.callback_query.answer = AsyncMock()

    await handle_risk_level_change(mock_update, mock_context)

    # Проверяем обновление уровня риска
    assert mock_context.user_data["market_analysis"]["risk_level"] == "high"

    # Проверяем ответ пользователю (может быть вызван несколько раз)
    mock_update.callback_query.answer.assert_called()

    # Сбрасываем query.data перед вторым вызовом
    # (handle_risk_level_change изменяет query.data на "analysis:recommendations:{game}")
    mock_update.callback_query.data = "analysis_risk:high:csgo"

    await handle_risk_level_change(mock_update, mock_context)

    # Проверяем обновление уровня риска
    assert mock_context.user_data["market_analysis"]["risk_level"] == "high"


# ======================== Тесты get_back_to_market_analysis_keyboard ========================


def test_get_back_to_market_analysis_keyboard():
    """Тест создания клавиатуры возврата."""
    keyboard = get_back_to_market_analysis_keyboard("csgo")

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 1
    assert "Назад к анализу рынка" in keyboard.inline_keyboard[0][0].text


# ======================== Тесты register_market_analysis_handlers ========================


def test_register_market_analysis_handlers():
    """Тест регистрации обработчиков."""
    mock_dispatcher = MagicMock()

    register_market_analysis_handlers(mock_dispatcher)

    # Проверяем что обработчики добавлены
    assert mock_dispatcher.add_handler.call_count >= 4

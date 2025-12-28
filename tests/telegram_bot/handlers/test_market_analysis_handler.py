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


# ======================== Helper functions for test data ========================


def create_undervalued_item(trend: str = "stable") -> list[dict]:
    """Create test data for undervalued item with specified trend."""
    return [{
        "title": "Test Item",
        "current_price": 100.0,
        "avg_price": 120.0,
        "discount": 16.7,
        "trend": trend,
        "volume": 50,
    }]


def create_recommendation_item(liquidity: str = "medium") -> list[dict]:
    """Create test data for recommendation item with specified liquidity."""
    return [{
        "title": "Test Item",
        "current_price": 100.0,
        "discount": 10.0,
        "liquidity": liquidity,
        "investment_score": 7.0,
        "reason": "Test reason",
    }]


def create_volatility_item(volatility_score: float = 15.0) -> list[dict]:
    """Create test data for volatility item with specified score."""
    return [{
        "market_hash_name": "Test Item",
        "current_price": 100.0,
        "change_24h_percent": 10.0,
        "change_7d_percent": 15.0,
        "volatility_score": volatility_score,
    }]


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


# ======================== Расширенные тесты (Phase 3) ========================


class TestMarketAnalysisCommandExtended:
    """Расширенные тесты для market_analysis_command."""

    @pytest.mark.asyncio()
    async def test_command_with_no_message(self, mock_context):
        """Тест возврата при отсутствии сообщения."""
        update = MagicMock(spec=Update)
        update.message = None

        result = await market_analysis_command(update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_command_keyboard_has_game_buttons(self, mock_update, mock_context):
        """Тест наличия кнопок выбора игр в клавиатуре."""
        await market_analysis_command(mock_update, mock_context)

        _, kwargs = mock_update.message.reply_text.call_args
        keyboard = kwargs["reply_markup"]

        # Собираем все callback_data
        callback_data_list = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        # Проверяем наличие select_game колбэков
        assert any("select_game" in data for data in callback_data_list)


class TestMarketAnalysisCallbackExtended:
    """Расширенные тесты для market_analysis_callback."""

    @pytest.mark.asyncio()
    async def test_callback_with_no_query(self, mock_context):
        """Тест возврата при отсутствии query."""
        update = MagicMock(spec=Update)
        update.callback_query = None

        result = await market_analysis_callback(update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_callback_with_no_data(self, mock_update, mock_context):
        """Тест возврата при отсутствии data."""
        mock_update.callback_query.data = None

        result = await market_analysis_callback(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_callback_with_short_data(self, mock_update, mock_context):
        """Тест возврата при коротких данных."""
        mock_update.callback_query.data = "analysis"

        result = await market_analysis_callback(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_callback_with_none_user_data(self, mock_update):
        """Тест возврата при None user_data."""
        context = MagicMock()
        context.user_data = None
        mock_update.callback_query.data = "analysis:price_changes:csgo"

        result = await market_analysis_callback(mock_update, context)

        assert result is None

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
    @patch("src.telegram_bot.handlers.market_analysis_handler.find_trending_items")
    async def test_callback_trending_action(
        self, mock_trending, mock_api_client, mock_update, mock_context
    ):
        """Тест вызова trending анализа."""
        mock_update.callback_query.data = "analysis:trending:csgo"
        mock_context.user_data["market_analysis"] = {
            "current_game": "csgo",
            "min_price": 1.0,
            "max_price": 500.0,
        }
        mock_api_client.return_value = MagicMock()
        mock_trending.return_value = []

        await market_analysis_callback(mock_update, mock_context)

        mock_trending.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
    @patch("src.telegram_bot.handlers.market_analysis_handler.analyze_market_volatility")
    async def test_callback_volatility_action(
        self, mock_volatility, mock_api_client, mock_update, mock_context
    ):
        """Тест вызова volatility анализа."""
        mock_update.callback_query.data = "analysis:volatility:csgo"
        mock_context.user_data["market_analysis"] = {
            "current_game": "csgo",
            "min_price": 1.0,
            "max_price": 500.0,
        }
        mock_api_client.return_value = MagicMock()
        mock_volatility.return_value = []

        await market_analysis_callback(mock_update, mock_context)

        mock_volatility.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
    @patch("src.telegram_bot.handlers.market_analysis_handler.generate_market_report")
    async def test_callback_report_action(
        self, mock_report, mock_api_client, mock_update, mock_context
    ):
        """Тест вызова report анализа."""
        mock_update.callback_query.data = "analysis:report:csgo"
        mock_context.user_data["market_analysis"] = {
            "current_game": "csgo",
        }
        mock_api_client.return_value = MagicMock()
        mock_report.return_value = {"game": "csgo", "market_summary": {}}

        await market_analysis_callback(mock_update, mock_context)

        mock_report.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
    @patch("src.telegram_bot.handlers.market_analysis_handler.find_undervalued_items")
    async def test_callback_undervalued_action(
        self, mock_undervalued, mock_api_client, mock_update, mock_context
    ):
        """Тест вызова undervalued анализа."""
        mock_update.callback_query.data = "analysis:undervalued:csgo"
        mock_context.user_data["market_analysis"] = {
            "current_game": "csgo",
            "min_price": 1.0,
            "max_price": 500.0,
        }
        mock_api_client.return_value = MagicMock()
        mock_undervalued.return_value = []

        await market_analysis_callback(mock_update, mock_context)

        mock_undervalued.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
    @patch("src.telegram_bot.handlers.market_analysis_handler.get_investment_recommendations")
    async def test_callback_recommendations_action(
        self, mock_recommendations, mock_api_client, mock_update, mock_context
    ):
        """Тест вызова recommendations анализа."""
        mock_update.callback_query.data = "analysis:recommendations:csgo"
        mock_context.user_data["market_analysis"] = {
            "current_game": "csgo",
            "max_price": 100.0,
        }
        mock_api_client.return_value = MagicMock()
        mock_recommendations.return_value = []

        await market_analysis_callback(mock_update, mock_context)

        mock_recommendations.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.create_api_client_from_env")
    async def test_callback_handles_exception(
        self, mock_api_client, mock_update, mock_context
    ):
        """Тест обработки исключения."""
        mock_update.callback_query.data = "analysis:price_changes:csgo"
        mock_context.user_data["market_analysis"] = {"current_game": "csgo"}
        mock_api_client.side_effect = Exception("Test error")

        await market_analysis_callback(mock_update, mock_context)

        mock_update.callback_query.edit_message_text.assert_called()
        args = mock_update.callback_query.edit_message_text.call_args[0]
        assert "ошибка" in args[0].lower()


class TestShowVolatilityResultsExtended:
    """Расширенные тесты для show_volatility_results."""

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_volatility_level_very_high(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест отображения очень высокой волатильности."""
        mock_pagination.get_page.return_value = (create_volatility_item(35.0), 0, 1)

        await show_volatility_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "Очень высокая" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_volatility_level_high(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест отображения высокой волатильности."""
        mock_pagination.get_page.return_value = (create_volatility_item(25.0), 0, 1)

        await show_volatility_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "Высокая" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_volatility_level_medium(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест отображения средней волатильности."""
        mock_pagination.get_page.return_value = (create_volatility_item(15.0), 0, 1)

        await show_volatility_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "Средняя" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_volatility_level_low(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест отображения низкой волатильности."""
        mock_pagination.get_page.return_value = (create_volatility_item(5.0), 0, 1)

        await show_volatility_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "Низкая" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_volatility_with_pagination_buttons(
        self, mock_pagination, mock_callback_query, mock_context, sample_volatility_data
    ):
        """Тест кнопок пагинации при наличии нескольких страниц."""
        mock_pagination.get_page.return_value = (sample_volatility_data, 0, 3)

        await show_volatility_results(mock_callback_query, mock_context, "csgo")

        _, kwargs = mock_callback_query.edit_message_text.call_args
        keyboard = kwargs["reply_markup"]

        # Должна быть кнопка "Вперед" на первой странице
        button_texts = [button.text for row in keyboard.inline_keyboard for button in row]
        assert any("Вперед" in text for text in button_texts)


class TestShowMarketReportExtended:
    """Расширенные тесты для show_market_report."""

    @pytest.mark.asyncio()
    async def test_market_direction_down(
        self, mock_callback_query, mock_context, sample_market_report
    ):
        """Тест отображения падающего направления рынка."""
        sample_market_report["market_summary"]["price_change_direction"] = "down"

        await show_market_report(mock_callback_query, mock_context, sample_market_report)

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "Падающий" in args[0]

    @pytest.mark.asyncio()
    async def test_market_direction_stable(
        self, mock_callback_query, mock_context, sample_market_report
    ):
        """Тест отображения стабильного направления рынка."""
        sample_market_report["market_summary"]["price_change_direction"] = "stable"

        await show_market_report(mock_callback_query, mock_context, sample_market_report)

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "Стабильный" in args[0]

    @pytest.mark.asyncio()
    async def test_market_volatility_levels(
        self, mock_callback_query, mock_context, sample_market_report
    ):
        """Тест отображения уровней волатильности рынка."""
        for level, expected in [("low", "Низкая"), ("medium", "Средняя"), ("high", "Высокая")]:
            # Create a copy to avoid modifying shared fixture
            report_copy = {
                "game": sample_market_report["game"],
                "market_summary": {
                    **sample_market_report["market_summary"],
                    "market_volatility_level": level,
                },
                "price_changes": sample_market_report.get("price_changes", []),
                "trending_items": sample_market_report.get("trending_items", []),
            }

            await show_market_report(mock_callback_query, mock_context, report_copy)

            args = mock_callback_query.edit_message_text.call_args[0]
            assert expected in args[0]


class TestShowUndervaluedItemsResultsExtended:
    """Расширенные тесты для show_undervalued_items_results."""

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_trend_icon_upward(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест иконки восходящего тренда."""
        mock_pagination.get_page.return_value = (create_undervalued_item("upward"), 0, 1)

        await show_undervalued_items_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "🔼" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_trend_icon_downward(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест иконки нисходящего тренда."""
        mock_pagination.get_page.return_value = (create_undervalued_item("downward"), 0, 1)

        await show_undervalued_items_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "🔽" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_trend_icon_stable(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест иконки стабильного тренда."""
        mock_pagination.get_page.return_value = (create_undervalued_item("stable"), 0, 1)

        await show_undervalued_items_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "➡️" in args[0]


class TestShowInvestmentRecommendationsResultsExtended:
    """Расширенные тесты для show_investment_recommendations_results."""

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_liquidity_icon_high(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест иконки высокой ликвидности."""
        mock_pagination.get_page.return_value = (create_recommendation_item("high"), 0, 1)

        await show_investment_recommendations_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "🟢" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_liquidity_icon_medium(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест иконки средней ликвидности."""
        mock_pagination.get_page.return_value = (create_recommendation_item("medium"), 0, 1)

        await show_investment_recommendations_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "🟡" in args[0]

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    async def test_liquidity_icon_low(
        self, mock_pagination, mock_callback_query, mock_context
    ):
        """Тест иконки низкой ликвидности."""
        mock_pagination.get_page.return_value = (create_recommendation_item("low"), 0, 1)

        await show_investment_recommendations_results(mock_callback_query, mock_context, "csgo")

        args = mock_callback_query.edit_message_text.call_args[0]
        assert "🔴" in args[0]


class TestHandlePeriodChangeExtended:
    """Расширенные тесты для handle_period_change."""

    @pytest.mark.asyncio()
    async def test_returns_early_with_no_query(self, mock_context):
        """Тест возврата при отсутствии query."""
        update = MagicMock(spec=Update)
        update.callback_query = None

        result = await handle_period_change(update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_no_data(self, mock_update, mock_context):
        """Тест возврата при отсутствии data."""
        mock_update.callback_query.data = None

        result = await handle_period_change(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_short_data(self, mock_update, mock_context):
        """Тест возврата при коротких данных."""
        mock_update.callback_query.data = "period_change"

        result = await handle_period_change(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_none_user_data(self, mock_update):
        """Тест возврата при None user_data."""
        context = MagicMock()
        context.user_data = None
        mock_update.callback_query.data = "period_change:24h:csgo"

        result = await handle_period_change(mock_update, context)

        assert result is None


class TestHandleRiskLevelChangeExtended:
    """Расширенные тесты для handle_risk_level_change."""

    @pytest.mark.asyncio()
    async def test_returns_early_with_no_query(self, mock_context):
        """Тест возврата при отсутствии query."""
        update = MagicMock(spec=Update)
        update.callback_query = None

        result = await handle_risk_level_change(update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_no_data(self, mock_update, mock_context):
        """Тест возврата при отсутствии data."""
        mock_update.callback_query.data = None

        result = await handle_risk_level_change(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_short_data(self, mock_update, mock_context):
        """Тест возврата при коротких данных."""
        mock_update.callback_query.data = "analysis_risk:low"

        result = await handle_risk_level_change(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_none_user_data(self, mock_update):
        """Тест возврата при None user_data."""
        context = MagicMock()
        context.user_data = None
        mock_update.callback_query.data = "analysis_risk:low:csgo"

        result = await handle_risk_level_change(mock_update, context)

        assert result is None


class TestHandlePaginationAnalysisExtended:
    """Расширенные тесты для handle_pagination_analysis."""

    @pytest.mark.asyncio()
    async def test_returns_early_with_no_query(self, mock_context):
        """Тест возврата при отсутствии query."""
        update = MagicMock(spec=Update)
        update.callback_query = None

        result = await handle_pagination_analysis(update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_no_data(self, mock_update, mock_context):
        """Тест возврата при отсутствии data."""
        mock_update.callback_query.data = None

        result = await handle_pagination_analysis(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_early_with_short_data(self, mock_update, mock_context):
        """Тест возврата при коротких данных."""
        mock_update.callback_query.data = "analysis_page:next"

        result = await handle_pagination_analysis(mock_update, mock_context)

        assert result is None

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    @patch("src.telegram_bot.handlers.market_analysis_handler.show_volatility_results")
    async def test_pagination_volatility_type(
        self, mock_show_results, mock_pagination, mock_update, mock_context
    ):
        """Тест пагинации для типа volatility."""
        mock_update.callback_query.data = "analysis_page:next:volatility:csgo"
        mock_show_results.return_value = None

        await handle_pagination_analysis(mock_update, mock_context)

        mock_pagination.next_page.assert_called_once()
        mock_show_results.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    @patch("src.telegram_bot.handlers.market_analysis_handler.show_undervalued_items_results")
    async def test_pagination_undervalued_type(
        self, mock_show_results, mock_pagination, mock_update, mock_context
    ):
        """Тест пагинации для типа undervalued."""
        mock_update.callback_query.data = "analysis_page:next:undervalued:csgo"
        mock_show_results.return_value = None

        await handle_pagination_analysis(mock_update, mock_context)

        mock_pagination.next_page.assert_called_once()
        mock_show_results.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.telegram_bot.handlers.market_analysis_handler.pagination_manager")
    @patch("src.telegram_bot.handlers.market_analysis_handler.show_investment_recommendations_results")
    async def test_pagination_recommendations_type(
        self, mock_show_results, mock_pagination, mock_update, mock_context
    ):
        """Тест пагинации для типа recommendations."""
        mock_update.callback_query.data = "analysis_page:prev:recommendations:csgo"
        mock_show_results.return_value = None

        await handle_pagination_analysis(mock_update, mock_context)

        mock_pagination.prev_page.assert_called_once()
        mock_show_results.assert_called_once()


class TestGetBackToMarketAnalysisKeyboardExtended:
    """Расширенные тесты для get_back_to_market_analysis_keyboard."""

    def test_keyboard_for_different_games(self):
        """Тест создания клавиатуры для разных игр."""
        games = ["csgo", "dota2", "tf2", "rust"]

        for game in games:
            keyboard = get_back_to_market_analysis_keyboard(game)
            assert game in keyboard.inline_keyboard[0][0].callback_data

    def test_keyboard_callback_data_format(self):
        """Тест формата callback_data."""
        keyboard = get_back_to_market_analysis_keyboard("csgo")
        callback_data = keyboard.inline_keyboard[0][0].callback_data

        assert callback_data.startswith("analysis:")
        assert "csgo" in callback_data


class TestRegisterMarketAnalysisHandlersExtended:
    """Расширенные тесты для register_market_analysis_handlers."""

    def test_registers_command_handler(self):
        """Тест регистрации CommandHandler."""
        mock_dispatcher = MagicMock()

        register_market_analysis_handlers(mock_dispatcher)

        # Проверяем что add_handler был вызван
        assert mock_dispatcher.add_handler.called

    def test_registers_callback_handlers(self):
        """Тест регистрации CallbackQueryHandler."""
        mock_dispatcher = MagicMock()

        register_market_analysis_handlers(mock_dispatcher)

        # Должно быть зарегистрировано минимум 5 обработчиков
        assert mock_dispatcher.add_handler.call_count >= 5

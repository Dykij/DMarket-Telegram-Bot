"""Тесты для обработчиков настроек фильтров ликвидности."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Message, Update, User
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.liquidity_settings_handler import (
    DEFAULT_LIQUIDITY_SETTINGS,
    cancel_liquidity_input,
    get_liquidity_settings,
    liquidity_settings_command,
    process_liquidity_value_input,
    reset_liquidity_settings,
    set_max_time_to_sell_prompt,
    set_min_liquidity_score_prompt,
    set_min_sales_per_week_prompt,
    toggle_liquidity_filter,
    update_liquidity_settings,
)


@pytest.fixture()
def mock_user():
    """Создает мок пользователя Telegram."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.first_name = "Test"
    user.username = "testuser"
    return user


@pytest.fixture()
def mock_message(mock_user):
    """Создает мок сообщения Telegram."""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat_id = 123456789
    message.reply_text = AsyncMock()
    return message


@pytest.fixture()
def mock_callback_query(mock_user, mock_message):
    """Создает мок callback query."""
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.from_user = mock_user
    callback_query.message = mock_message
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    return callback_query


@pytest.fixture()
def mock_update(mock_user, mock_message):
    """Создает мок Update для команды."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.message = mock_message
    update.callback_query = None
    return update


@pytest.fixture()
def mock_callback_update(mock_user, mock_callback_query):
    """Создает мок Update для callback."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.callback_query = mock_callback_query
    update.message = None
    return update


@pytest.fixture()
def mock_context():
    """Создает мок контекста."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.fixture(autouse=True)
def reset_profile_manager():
    """Сбрасывает профиль пользователя перед каждым тестом."""
    with patch(
        "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
    ) as mock_pm:
        mock_pm.get_profile.return_value = {
            "liquidity_settings": DEFAULT_LIQUIDITY_SETTINGS.copy()
        }
        mock_pm.update_profile = MagicMock()
        yield mock_pm


def test_get_liquidity_settings_default(reset_profile_manager):
    """Тест получения настроек по умолчанию."""
    # Мокаем отсутствие настроек
    reset_profile_manager.get_profile.return_value = {}

    settings = get_liquidity_settings(123456789)

    assert settings == DEFAULT_LIQUIDITY_SETTINGS
    reset_profile_manager.update_profile.assert_called_once()


def test_get_liquidity_settings_existing(reset_profile_manager):
    """Тест получения существующих настроек."""
    custom_settings = {
        "enabled": False,
        "min_liquidity_score": 70,
        "min_sales_per_week": 10,
        "max_time_to_sell_days": 5,
    }
    reset_profile_manager.get_profile.return_value = {
        "liquidity_settings": custom_settings
    }

    settings = get_liquidity_settings(123456789)

    assert settings == custom_settings
    reset_profile_manager.update_profile.assert_not_called()


def test_update_liquidity_settings(reset_profile_manager):
    """Тест обновления настроек."""
    reset_profile_manager.get_profile.return_value = {
        "liquidity_settings": DEFAULT_LIQUIDITY_SETTINGS.copy()
    }

    update_liquidity_settings(123456789, {"min_liquidity_score": 80})

    reset_profile_manager.update_profile.assert_called_once()
    call_args = reset_profile_manager.update_profile.call_args
    assert call_args[0][0] == 123456789
    assert call_args[0][1]["liquidity_settings"]["min_liquidity_score"] == 80


@pytest.mark.asyncio()
async def test_liquidity_settings_command(
    mock_update, mock_context, reset_profile_manager
):
    """Тест команды /liquidity_settings."""
    await liquidity_settings_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Настройки фильтров ликвидности" in call_args[0][0]
    assert call_args[1]["parse_mode"] == "HTML"


@pytest.mark.asyncio()
async def test_toggle_liquidity_filter(
    mock_callback_update, mock_context, reset_profile_manager
):
    """Тест переключения фильтра ликвидности."""
    await toggle_liquidity_filter(mock_callback_update, mock_context)

    mock_callback_update.callback_query.answer.assert_called_once()
    mock_callback_update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio()
async def test_reset_liquidity_settings(
    mock_callback_update, mock_context, reset_profile_manager
):
    """Тест сброса настроек на значения по умолчанию."""
    # Устанавливаем кастомные настройки
    reset_profile_manager.get_profile.return_value = {
        "liquidity_settings": {
            "enabled": False,
            "min_liquidity_score": 90,
            "min_sales_per_week": 20,
            "max_time_to_sell_days": 2,
        }
    }

    await reset_liquidity_settings(mock_callback_update, mock_context)

    mock_callback_update.callback_query.answer.assert_called_once()
    reset_profile_manager.update_profile.assert_called_once()


@pytest.mark.asyncio()
async def test_set_min_liquidity_score_prompt(mock_callback_update, mock_context):
    """Тест запроса минимального балла ликвидности."""
    await set_min_liquidity_score_prompt(mock_callback_update, mock_context)

    assert mock_context.user_data["awaiting_liquidity_score"] is True
    mock_callback_update.callback_query.answer.assert_called_once()
    mock_callback_update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio()
async def test_set_min_sales_per_week_prompt(mock_callback_update, mock_context):
    """Тест запроса минимальных продаж в неделю."""
    await set_min_sales_per_week_prompt(mock_callback_update, mock_context)

    assert mock_context.user_data["awaiting_sales_per_week"] is True
    mock_callback_update.callback_query.answer.assert_called_once()


@pytest.mark.asyncio()
async def test_set_max_time_to_sell_prompt(mock_callback_update, mock_context):
    """Тест запроса максимального времени продажи."""
    await set_max_time_to_sell_prompt(mock_callback_update, mock_context)

    assert mock_context.user_data["awaiting_time_to_sell"] is True
    mock_callback_update.callback_query.answer.assert_called_once()


@pytest.mark.asyncio()
async def test_process_liquidity_score_input_valid(
    mock_update,
    mock_context,
    reset_profile_manager,
):
    """Тест обработки корректного ввода балла ликвидности."""
    mock_context.user_data["awaiting_liquidity_score"] = True
    mock_update.message.text = "75"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "✅" in mock_update.message.reply_text.call_args[0][0]
    assert mock_context.user_data["awaiting_liquidity_score"] is False


@pytest.mark.asyncio()
async def test_process_liquidity_score_input_invalid_range(mock_update, mock_context):
    """Тест обработки некорректного балла (вне диапазона)."""
    mock_context.user_data["awaiting_liquidity_score"] = True
    mock_update.message.text = "150"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "❌" in mock_update.message.reply_text.call_args[0][0]
    assert mock_context.user_data["awaiting_liquidity_score"] is True


@pytest.mark.asyncio()
async def test_process_liquidity_score_input_invalid_type(mock_update, mock_context):
    """Тест обработки некорректного типа данных."""
    mock_context.user_data["awaiting_liquidity_score"] = True
    mock_update.message.text = "abc"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "❌" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio()
async def test_process_sales_per_week_input_valid(
    mock_update,
    mock_context,
    reset_profile_manager,
):
    """Тест обработки корректного ввода продаж в неделю."""
    mock_context.user_data["awaiting_sales_per_week"] = True
    mock_update.message.text = "10"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "✅" in mock_update.message.reply_text.call_args[0][0]
    assert mock_context.user_data["awaiting_sales_per_week"] is False


@pytest.mark.asyncio()
async def test_process_sales_per_week_input_negative(mock_update, mock_context):
    """Тест обработки отрицательного значения продаж."""
    mock_context.user_data["awaiting_sales_per_week"] = True
    mock_update.message.text = "-5"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "❌" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio()
async def test_process_time_to_sell_input_valid(
    mock_update,
    mock_context,
    reset_profile_manager,
):
    """Тест обработки корректного ввода времени продажи."""
    mock_context.user_data["awaiting_time_to_sell"] = True
    mock_update.message.text = "5"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "✅" in mock_update.message.reply_text.call_args[0][0]
    assert mock_context.user_data["awaiting_time_to_sell"] is False


@pytest.mark.asyncio()
async def test_process_time_to_sell_input_zero(mock_update, mock_context):
    """Тест обработки нулевого значения времени продажи."""
    mock_context.user_data["awaiting_time_to_sell"] = True
    mock_update.message.text = "0"

    await process_liquidity_value_input(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "❌" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio()
async def test_cancel_liquidity_input(mock_update, mock_context):
    """Тест отмены ввода настроек."""
    mock_context.user_data["awaiting_liquidity_score"] = True
    mock_context.user_data["awaiting_sales_per_week"] = True
    mock_context.user_data["awaiting_time_to_sell"] = True

    await cancel_liquidity_input(mock_update, mock_context)

    assert mock_context.user_data["awaiting_liquidity_score"] is False
    assert mock_context.user_data["awaiting_sales_per_week"] is False
    assert mock_context.user_data["awaiting_time_to_sell"] is False
    mock_update.message.reply_text.assert_called_once()
    assert "❌" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio()
async def test_liquidity_settings_command_without_message(mock_context):
    """Тест команды без сообщения."""
    update = MagicMock(spec=Update)
    update.effective_user = None
    update.message = None

    # Не должно вызывать исключение
    await liquidity_settings_command(update, mock_context)


@pytest.mark.asyncio()
async def test_toggle_liquidity_filter_without_callback(mock_context):
    """Тест переключения без callback query."""
    update = MagicMock(spec=Update)
    update.effective_user = None
    update.callback_query = None

    # Не должно вызывать исключение
    await toggle_liquidity_filter(update, mock_context)


@pytest.mark.asyncio()
async def test_process_liquidity_value_input_no_user_data(mock_update):
    """Тест обработки ввода без user_data."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = None

    # Не должно вызывать исключение
    await process_liquidity_value_input(mock_update, context)

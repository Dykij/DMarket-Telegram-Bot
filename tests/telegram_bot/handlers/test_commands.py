"""Тесты для обработчиков команд Telegram бота.

Этот модуль содержит тесты для всех обработчиков команд в handlers/commands.py,
включая /start, /help, /webapp, /markets, /status, /arbitrage и текстовые кнопки.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.commands import (
    arbitrage_command,
    dmarket_status_command,
    handle_text_buttons,
    help_command,
    markets_command,
    start_command,
    webapp_command,
)


# ============================================================================
# ФИКСТУРЫ
# ============================================================================


@pytest.fixture()
def mock_user():
    """Мок пользователя Telegram."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.first_name = "Test"
    user.username = "testuser"
    return user


@pytest.fixture()
def mock_chat():
    """Мок чата Telegram."""
    chat = MagicMock(spec=Chat)
    chat.id = 123456789
    chat.type = "private"
    chat.send_action = AsyncMock()
    return chat


@pytest.fixture()
def mock_message(mock_user, mock_chat):
    """Мок сообщения Telegram."""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.reply_text = AsyncMock()
    message.text = "/start"
    return message


@pytest.fixture()
def mock_update(mock_message, mock_chat):
    """Мок объекта Update от Telegram."""
    update = MagicMock(spec=Update)
    update.message = mock_message
    update.effective_user = mock_message.from_user
    update.effective_chat = mock_chat
    return update


@pytest.fixture()
def mock_context():
    """Мок контекста ContextTypes."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.chat_data = {}
    context.bot_data = {}
    return context


# ============================================================================
# ТЕСТЫ КОМАНДЫ /start
# ============================================================================


@pytest.mark.asyncio()
async def test_start_command_sends_welcome_message(mock_update, mock_context):
    """Тест: команда /start отправляет приветственное сообщение."""
    await start_command(mock_update, mock_context)

    # Проверяем, что reply_text вызывался 2 раза (приветствие + клавиатура)
    assert mock_update.message.reply_text.call_count == 2

    # Проверяем первый вызов (приветственное сообщение)
    first_call = mock_update.message.reply_text.call_args_list[0]
    assert "Привет" in first_call[0][0]
    assert first_call[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in first_call[1]


@pytest.mark.asyncio()
async def test_start_command_sends_quick_access_keyboard(mock_update, mock_context):
    """Тест: команда /start отправляет клавиатуру быстрого доступа."""
    await start_command(mock_update, mock_context)

    # Проверяем второй вызов (клавиатура быстрого доступа)
    second_call = mock_update.message.reply_text.call_args_list[1]
    assert "Быстрый доступ" in second_call[0][0]
    assert second_call[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in second_call[1]


@pytest.mark.asyncio()
async def test_start_command_sets_keyboard_enabled_flag(mock_update, mock_context):
    """Тест: команда /start устанавливает флаг keyboard_enabled в user_data."""
    await start_command(mock_update, mock_context)

    # Проверяем, что флаг установлен
    assert mock_context.user_data.get("keyboard_enabled") is True


@pytest.mark.asyncio()
async def test_start_command_with_no_user_data(mock_update, mock_context):
    """Тест: команда /start работает без user_data (нет атрибута hasattr)."""
    # Удаляем user_data
    del mock_context.user_data

    # Должно работать без ошибок
    await start_command(mock_update, mock_context)

    # Проверяем, что сообщения отправлены
    assert mock_update.message.reply_text.call_count == 2


# ============================================================================
# ТЕСТЫ КОМАНДЫ /help
# ============================================================================


@pytest.mark.asyncio()
async def test_help_command_sends_help_message(mock_update, mock_context):
    """Тест: команда /help отправляет справочное сообщение."""
    await help_command(mock_update, mock_context)

    # Проверяем вызов
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    # Проверяем содержимое
    message_text = call_args[0][0]
    assert "Доступные команды" in message_text
    assert "/start" in message_text
    assert "/arbitrage" in message_text
    assert "/balance" in message_text
    assert "/webapp" in message_text

    # Проверяем параметры
    assert call_args[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in call_args[1]


# ============================================================================
# ТЕСТЫ КОМАНДЫ /webapp
# ============================================================================


@pytest.mark.asyncio()
async def test_webapp_command_sends_webapp_message(mock_update, mock_context):
    """Тест: команда /webapp отправляет сообщение с WebApp кнопкой."""
    await webapp_command(mock_update, mock_context)

    # Проверяем вызов
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    # Проверяем содержимое
    message_text = call_args[0][0]
    assert "DMarket WebApp" in message_text
    assert "Telegram" in message_text

    # Проверяем параметры
    assert call_args[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in call_args[1]


# ============================================================================
# ТЕСТЫ КОМАНДЫ /markets
# ============================================================================


@pytest.mark.asyncio()
async def test_markets_command_sends_marketplace_comparison(mock_update, mock_context):
    """Тест: команда /markets отправляет клавиатуру сравнения рынков."""
    await markets_command(mock_update, mock_context)

    # Проверяем вызов
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    # Проверяем содержимое
    message_text = call_args[0][0]
    assert "Сравнение рынков" in message_text

    # Проверяем параметры
    assert call_args[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in call_args[1]


# ============================================================================
# ТЕСТЫ КОМАНДЫ /status
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.commands.dmarket_status_impl")
async def test_dmarket_status_command_sends_status_message(
    mock_dmarket_status, mock_update, mock_context
):
    """Тест: команда /status вызывает dmarket_status_impl."""
    await dmarket_status_command(mock_update, mock_context)

    # Проверяем вызов dmarket_status_impl
    mock_dmarket_status.assert_called_once_with(
        mock_update, mock_context, status_message=mock_update.message
    )


# ============================================================================
# ТЕСТЫ КОМАНДЫ /arbitrage
# ============================================================================


@pytest.mark.asyncio()
async def test_arbitrage_command_sends_typing_action(mock_update, mock_context):
    """Тест: команда /arbitrage отправляет действие 'typing'."""
    await arbitrage_command(mock_update, mock_context)

    # Проверяем, что send_action вызывался с ChatAction.TYPING
    mock_update.effective_chat.send_action.assert_called_once_with(ChatAction.TYPING)


@pytest.mark.asyncio()
async def test_arbitrage_command_sends_arbitrage_keyboard(mock_update, mock_context):
    """Тест: команда /arbitrage отправляет клавиатуру арбитража."""
    await arbitrage_command(mock_update, mock_context)

    # Проверяем вызов
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    # Проверяем содержимое
    message_text = call_args[0][0]
    assert "Меню арбитража" in message_text

    # Проверяем параметры
    assert call_args[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in call_args[1]


# ============================================================================
# ТЕСТЫ ОБРАБОТЧИКА ТЕКСТОВЫХ КНОПОК
# ============================================================================


@pytest.mark.asyncio()
async def test_handle_text_buttons_arbitrage_button(mock_update, mock_context):
    """Тест: текстовая кнопка '🔍 Арбитраж' вызывает arbitrage_command."""
    mock_update.message.text = "🔍 Арбитраж"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем, что send_action вызывался (признак arbitrage_command)
    mock_update.effective_chat.send_action.assert_called_once()

    # Проверяем отправку сообщения
    assert mock_update.message.reply_text.call_count >= 1


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.commands.dmarket_status_impl")
async def test_handle_text_buttons_balance_button(
    mock_dmarket_status, mock_update, mock_context
):
    """Тест: текстовая кнопка '📊 Баланс' вызывает dmarket_status_impl."""
    mock_dmarket_status.return_value = AsyncMock()
    mock_update.message.text = "📊 Баланс"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем вызов dmarket_status_impl
    mock_dmarket_status.assert_called_once_with(
        mock_update, mock_context, status_message=mock_update.message
    )


@pytest.mark.asyncio()
async def test_handle_text_buttons_open_dmarket_button(mock_update, mock_context):
    """Тест: текстовая кнопка '🌐 Открыть DMarket' вызывает webapp_command."""
    mock_update.message.text = "🌐 Открыть DMarket"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем отправку сообщения с WebApp
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "DMarket WebApp" in call_args[0][0]


@pytest.mark.asyncio()
async def test_handle_text_buttons_market_analysis_button(mock_update, mock_context):
    """Тест: текстовая кнопка '📈 Анализ рынка' отправляет сообщение."""
    mock_update.message.text = "📈 Анализ рынка"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем отправку сообщения
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    # Проверяем содержимое (теперь "Аналитика рынка")
    message_text = call_args[0][0]
    assert "Аналитика" in message_text or "Анализ" in message_text

    # Проверяем параметры
    assert call_args[1]["parse_mode"] == ParseMode.HTML
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio()
async def test_handle_text_buttons_settings_button(mock_update, mock_context):
    """Тест: текстовая кнопка '⚙️ Настройки' отправляет сообщение."""
    mock_update.message.text = "⚙️ Настройки"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем отправку сообщения
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    # Проверяем содержимое (теперь полноценное меню настроек)
    message_text = call_args[0][0]
    assert "Настройки" in message_text


@pytest.mark.asyncio()
async def test_handle_text_buttons_help_button(mock_update, mock_context):
    """Тест: текстовая кнопка '❓ Помощь' вызывает help_command."""
    mock_update.message.text = "❓ Помощь"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем отправку справки
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Доступные команды" in call_args[0][0]


@pytest.mark.asyncio()
async def test_handle_text_buttons_unknown_text(mock_update, mock_context):
    """Тест: неизвестная текстовая кнопка не вызывает действий."""
    mock_update.message.text = "Неизвестная кнопка"

    # Не должно быть ошибок
    await handle_text_buttons(mock_update, mock_context)

    # Проверяем, что сообщения не отправлялись
    mock_update.message.reply_text.assert_not_called()


# ============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================================================


@pytest.mark.asyncio()
async def test_full_workflow_start_to_arbitrage(mock_update, mock_context):
    """Интеграционный тест: от /start до /arbitrage."""
    # Шаг 1: /start
    await start_command(mock_update, mock_context)
    assert mock_update.message.reply_text.call_count == 2
    assert mock_context.user_data.get("keyboard_enabled") is True

    # Сброс моков
    mock_update.message.reply_text.reset_mock()
    mock_update.effective_chat.send_action.reset_mock()

    # Шаг 2: /arbitrage
    await arbitrage_command(mock_update, mock_context)
    mock_update.effective_chat.send_action.assert_called_once_with(ChatAction.TYPING)
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
async def test_all_commands_use_html_parse_mode(mock_update, mock_context):
    """Тест: все команды используют ParseMode.HTML."""
    commands = [
        start_command,
        help_command,
        webapp_command,
        markets_command,
        arbitrage_command,
    ]

    for command_func in commands:
        # Сброс моков
        mock_update.message.reply_text.reset_mock()
        mock_update.effective_chat.send_action.reset_mock()

        # Вызов команды
        await command_func(mock_update, mock_context)

        # Проверка: хотя бы один вызов с ParseMode.HTML
        calls = mock_update.message.reply_text.call_args_list
        assert any(
            call[1].get("parse_mode") == ParseMode.HTML for call in calls
        ), f"{command_func.__name__} не использует ParseMode.HTML"


@pytest.mark.asyncio()
async def test_all_commands_send_reply_markup(mock_update, mock_context):
    """Тест: все команды отправляют reply_markup."""
    commands = [
        start_command,
        help_command,
        webapp_command,
        markets_command,
        arbitrage_command,
    ]

    for command_func in commands:
        # Сброс моков
        mock_update.message.reply_text.reset_mock()
        mock_update.effective_chat.send_action.reset_mock()

        # Вызов команды
        await command_func(mock_update, mock_context)

        # Проверка: хотя бы один вызов с reply_markup
        calls = mock_update.message.reply_text.call_args_list
        assert any(
            "reply_markup" in call[1] for call in calls
        ), f"{command_func.__name__} не отправляет reply_markup"


# ============================================================================
# ТЕСТЫ ИМПОРТА И ЭКСПОРТА
# ============================================================================


def test_all_functions_exported():
    """Тест: все функции экспортированы в __all__."""
    from src.telegram_bot.handlers import commands

    expected_exports = [
        "arbitrage_command",
        "dmarket_status_command",
        "handle_text_buttons",
        "help_command",
        "markets_command",
        "start_command",
        "webapp_command",
    ]

    assert hasattr(commands, "__all__")
    assert set(commands.__all__) == set(expected_exports)


def test_all_exported_functions_callable():
    """Тест: все экспортированные функции вызываемы."""
    from src.telegram_bot.handlers import commands

    for func_name in commands.__all__:
        func = getattr(commands, func_name)
        assert callable(func), f"{func_name} должен быть вызываемым"

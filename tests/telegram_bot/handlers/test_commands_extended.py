"""Расширенное тестирование команд Telegram бота.

Этот модуль содержит тесты для всех команд бота:
- /start - приветствие и инициализация
- /help - справка по командам
- /balance - проверка баланса
- /arbitrage - меню арбитража
- /webapp - открытие WebApp
- /markets - сравнение рынков
- Обработка текстовых кнопок
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
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


# Константы для тестов
TEST_USER_ID = 12345
TEST_CHAT_ID = 67890
TEST_USERNAME = "test_user"


@pytest.fixture()
def mock_update():
    """Создает мок объект Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = TEST_USER_ID
    update.effective_user.username = TEST_USERNAME
    update.effective_user.first_name = "Test"

    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = TEST_CHAT_ID
    update.effective_chat.send_action = AsyncMock()

    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = ""

    return update


@pytest.fixture()
def mock_context():
    """Создает мок объект Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}
    context.chat_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    return context


# ==============================================================================
# ТЕСТЫ КОМАНДЫ /start
# ==============================================================================


@pytest.mark.asyncio()
async def test_start_command_basic(mock_update, mock_context):
    """Тест базовой работы команды /start."""
    await start_command(mock_update, mock_context)

    # Проверяем, что были отправлены 2 сообщения
    assert mock_update.message.reply_text.call_count == 2

    # Проверяем первое сообщение (приветствие)
    first_call = mock_update.message.reply_text.call_args_list[0]
    assert "Привет" in first_call[0][0] or "бот" in first_call[0][0]
    assert "reply_markup" in first_call[1]

    # Проверяем второе сообщение (быстрый доступ)
    second_call = mock_update.message.reply_text.call_args_list[1]
    assert "Быстрый доступ" in second_call[0][0]


@pytest.mark.asyncio()
async def test_start_command_sets_keyboard_enabled(mock_update, mock_context):
    """Тест установки флага keyboard_enabled в контексте."""
    await start_command(mock_update, mock_context)

    # Проверяем, что флаг установлен
    assert mock_context.user_data.get("keyboard_enabled") is True


@pytest.mark.asyncio()
async def test_start_command_with_parse_mode(mock_update, mock_context):
    """Тест использования HTML parse_mode в /start."""
    await start_command(mock_update, mock_context)

    # Проверяем, что использован HTML режим
    for call in mock_update.message.reply_text.call_args_list:
        assert call[1].get("parse_mode") == "HTML"


# ==============================================================================
# ТЕСТЫ КОМАНДЫ /help
# ==============================================================================


@pytest.mark.asyncio()
async def test_help_command_basic(mock_update, mock_context):
    """Тест базовой работы команды /help."""
    await help_command(mock_update, mock_context)

    # Проверяем, что отправлено сообщение
    mock_update.message.reply_text.assert_called_once()

    # Получаем текст сообщения
    call_args = mock_update.message.reply_text.call_args
    help_text = call_args[0][0]

    # Проверяем наличие описания команд
    assert "/start" in help_text
    assert "/arbitrage" in help_text
    assert "/balance" in help_text
    assert "/webapp" in help_text


@pytest.mark.asyncio()
async def test_help_command_with_keyboard(mock_update, mock_context):
    """Тест наличия клавиатуры в /help."""
    await help_command(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio()
async def test_help_command_html_formatting(mock_update, mock_context):
    """Тест HTML форматирования в /help."""
    await help_command(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    assert call_args[1].get("parse_mode") == "HTML"


# ==============================================================================
# ТЕСТЫ КОМАНДЫ /arbitrage
# ==============================================================================


@pytest.mark.asyncio()
async def test_arbitrage_command_basic(mock_update, mock_context):
    """Тест базовой работы команды /arbitrage."""
    await arbitrage_command(mock_update, mock_context)

    # Проверяем отправку typing action
    mock_update.effective_chat.send_action.assert_called_once()

    # Проверяем отправку сообщения
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
async def test_arbitrage_command_message_content(mock_update, mock_context):
    """Тест содержания сообщения /arbitrage."""
    await arbitrage_command(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "арбитраж" in message_text.lower()
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio()
async def test_arbitrage_command_typing_action(mock_update, mock_context):
    """Тест отправки typing action в /arbitrage."""
    await arbitrage_command(mock_update, mock_context)

    # Проверяем, что typing был отправлен до сообщения
    assert mock_update.effective_chat.send_action.called


# ==============================================================================
# ТЕСТЫ КОМАНДЫ /webapp
# ==============================================================================


@pytest.mark.asyncio()
async def test_webapp_command_basic(mock_update, mock_context):
    """Тест базовой работы команды /webapp."""
    await webapp_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
async def test_webapp_command_content(mock_update, mock_context):
    """Тест содержания сообщения /webapp."""
    await webapp_command(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "DMarket" in message_text
    assert "WebApp" in message_text


@pytest.mark.asyncio()
async def test_webapp_command_has_button(mock_update, mock_context):
    """Тест наличия кнопки в /webapp."""
    await webapp_command(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    assert "reply_markup" in call_args[1]


# ==============================================================================
# ТЕСТЫ КОМАНДЫ /markets
# ==============================================================================


@pytest.mark.asyncio()
async def test_markets_command_basic(mock_update, mock_context):
    """Тест базовой работы команды /markets."""
    await markets_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
async def test_markets_command_content(mock_update, mock_context):
    """Тест содержания сообщения /markets."""
    await markets_command(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "рынк" in message_text.lower()


# ==============================================================================
# ТЕСТЫ КОМАНДЫ /status
# ==============================================================================


@pytest.mark.asyncio()
async def test_dmarket_status_command(mock_update, mock_context):
    """Тест команды /status."""
    await dmarket_status_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()

    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "статус" in message_text.lower() or "проверка" in message_text.lower()


# ==============================================================================
# ТЕСТЫ ОБРАБОТКИ ТЕКСТОВЫХ КНОПОК
# ==============================================================================


@pytest.mark.asyncio()
async def test_handle_text_buttons_arbitrage(mock_update, mock_context):
    """Тест обработки кнопки '🔍 Арбитраж'."""
    mock_update.message.text = "🔍 Арбитраж"

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем, что был вызван соответствующий handler
    assert mock_update.effective_chat.send_action.called
    mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio()
async def test_handle_text_buttons_balance(mock_update, mock_context):
    """Тест обработки кнопки '📊 Баланс'."""
    mock_update.message.text = "📊 Баланс"

    with patch(
        "src.telegram_bot.handlers.commands.check_balance_command"
    ) as mock_balance:
        mock_balance.return_value = AsyncMock()

        await handle_text_buttons(mock_update, mock_context)

        # Проверяем, что была вызвана функция баланса
        mock_balance.assert_called_once_with(mock_update.message, mock_context)


@pytest.mark.asyncio()
async def test_handle_text_buttons_webapp(mock_update, mock_context):
    """Тест обработки кнопки '🌐 Открыть DMarket'."""
    mock_update.message.text = "🌐 Открыть DMarket"

    await handle_text_buttons(mock_update, mock_context)

    mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio()
async def test_handle_text_buttons_market_analysis(mock_update, mock_context):
    """Тест обработки кнопки '📈 Анализ рынка'."""
    mock_update.message.text = "📈 Анализ рынка"

    await handle_text_buttons(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "Анализ рынка" in message_text


@pytest.mark.asyncio()
async def test_handle_text_buttons_settings(mock_update, mock_context):
    """Тест обработки кнопки '⚙️ Настройки'."""
    mock_update.message.text = "⚙️ Настройки"

    await handle_text_buttons(mock_update, mock_context)

    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "Настройки" in message_text


@pytest.mark.asyncio()
async def test_handle_text_buttons_help(mock_update, mock_context):
    """Тест обработки кнопки '❓ Помощь'."""
    mock_update.message.text = "❓ Помощь"

    await handle_text_buttons(mock_update, mock_context)

    # Должна быть вызвана help_command
    call_args = mock_update.message.reply_text.call_args
    message_text = call_args[0][0]

    assert "/start" in message_text or "команд" in message_text.lower()


@pytest.mark.asyncio()
async def test_handle_text_buttons_unknown(mock_update, mock_context):
    """Тест обработки неизвестной текстовой кнопки."""
    mock_update.message.text = "Неизвестная команда"

    await handle_text_buttons(mock_update, mock_context)

    # Не должно быть вызовов, так как команда не распознана
    # (функция просто ничего не делает для неизвестных команд)


# ==============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК
# ==============================================================================


@pytest.mark.asyncio()
async def test_start_command_error_handling(mock_update, mock_context):
    """Тест обработки ошибок в /start."""
    mock_update.message.reply_text.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        await start_command(mock_update, mock_context)


@pytest.mark.asyncio()
async def test_help_command_error_handling(mock_update, mock_context):
    """Тест обработки ошибок в /help."""
    mock_update.message.reply_text.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        await help_command(mock_update, mock_context)


# ==============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.parametrize(
    "command_func,expected_text",
    [
        (start_command, "бот"),
        (help_command, "/start"),
        (webapp_command, "DMarket"),
        (markets_command, "рынк"),
    ],
)
@pytest.mark.asyncio()
async def test_commands_send_messages(
    mock_update, mock_context, command_func, expected_text
):
    """Параметризованный тест для проверки отправки сообщений командами."""
    await command_func(mock_update, mock_context)

    assert mock_update.message.reply_text.called

    # Проверяем, что в сообщении есть ожидаемый текст
    calls = mock_update.message.reply_text.call_args_list
    all_messages = " ".join([call[0][0].lower() for call in calls])
    assert expected_text.lower() in all_messages


@pytest.mark.parametrize(
    "text_button",
    [
        "🔍 Арбитраж",
        "📊 Баланс",
        "🌐 Открыть DMarket",
        "📈 Анализ рынка",
        "⚙️ Настройки",
        "❓ Помощь",
    ],
)
@pytest.mark.asyncio()
async def test_handle_all_text_buttons(mock_update, mock_context, text_button):
    """Параметризованный тест для всех текстовых кнопок."""
    mock_update.message.text = text_button

    with patch(
        "src.telegram_bot.handlers.commands.check_balance_command"
    ) as mock_balance:
        mock_balance.return_value = AsyncMock()

        # Не должно быть исключений
        await handle_text_buttons(mock_update, mock_context)


# ==============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.asyncio()
async def test_command_flow_start_to_help(mock_update, mock_context):
    """Тест потока: /start -> /help."""
    # Сначала /start
    await start_command(mock_update, mock_context)
    assert mock_context.user_data.get("keyboard_enabled") is True

    # Затем /help
    mock_update.message.reply_text.reset_mock()
    await help_command(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
async def test_command_flow_arbitrage_sequence(mock_update, mock_context):
    """Тест потока: /start -> текстовая кнопка арбитраж."""
    # Сначала /start
    await start_command(mock_update, mock_context)

    # Затем текстовая кнопка
    mock_update.message.text = "🔍 Арбитраж"
    mock_update.message.reply_text.reset_mock()
    mock_update.effective_chat.send_action.reset_mock()

    await handle_text_buttons(mock_update, mock_context)

    # Проверяем, что typing был отправлен
    assert mock_update.effective_chat.send_action.called


# ==============================================================================
# ТЕСТЫ КЛАВИАТУР
# ==============================================================================


@pytest.mark.asyncio()
async def test_keyboards_import():
    """Тест импорта клавиатур."""
    from src.telegram_bot.keyboards import (
        get_game_selection_keyboard,
        get_marketplace_comparison_keyboard,
        get_modern_arbitrage_keyboard,
        get_permanent_reply_keyboard,
        get_webapp_button,
    )

    # Проверяем, что все функции импортируются
    assert callable(get_modern_arbitrage_keyboard)
    assert callable(get_permanent_reply_keyboard)
    assert callable(get_webapp_button)
    assert callable(get_marketplace_comparison_keyboard)
    assert callable(get_game_selection_keyboard)


# ==============================================================================
# ТЕСТЫ ЛОГИРОВАНИЯ
# ==============================================================================


@pytest.mark.asyncio()
async def test_commands_have_logger():
    """Тест наличия логгера в модуле команд."""
    import src.telegram_bot.handlers.commands as commands_module

    assert hasattr(commands_module, "logger")
    assert isinstance(commands_module.logger, logging.Logger)

"""Тесты для обработчиков DMarket команд.

Этот модуль содержит тесты для:
- Инициализации DMarketHandler
- Команды /dmarket (проверка статуса API ключей)
- Команды /balance (получение баланса)
- Регистрации обработчиков
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update, User
from telegram.ext import Application

from src.telegram_bot.handlers.dmarket_handlers import (
    DMarketHandler,
    register_dmarket_handlers,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_update():
    """Создает мок Update с message."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.message = AsyncMock(spec=Message)
    return update


@pytest.fixture()
def mock_context():
    """Создает мок ContextTypes.DEFAULT_TYPE."""
    return MagicMock()


# ============================================================================
# ТЕСТЫ ИНИЦИАЛИЗАЦИИ
# ============================================================================


def test_dmarket_handler_init_with_keys():
    """Тест инициализации DMarketHandler с ключами API."""
    handler = DMarketHandler(
        public_key="test_public_key",
        secret_key="test_secret_key",
        api_url="https://api.dmarket.com",
    )

    assert handler.public_key == "test_public_key"
    assert handler.secret_key == "test_secret_key"
    assert handler.api_url == "https://api.dmarket.com"


def test_dmarket_handler_init_without_keys():
    """Тест инициализации DMarketHandler без ключей API."""
    handler = DMarketHandler(
        public_key="",
        secret_key="",
        api_url="https://api.dmarket.com",
    )

    assert handler.public_key == ""
    assert handler.secret_key == ""
    assert handler.api is None


@patch("src.telegram_bot.handlers.dmarket_handlers.DMarketAPI")
def test_initialize_api_success(mock_dmarket_api):
    """Тест успешной инициализации API."""
    handler = DMarketHandler(
        public_key="test_public",
        secret_key="test_secret",
        api_url="https://api.dmarket.com",
    )

    # Проверяем, что API был инициализирован
    mock_dmarket_api.assert_called_once_with(
        public_key="test_public",
        secret_key="test_secret",
        api_url="https://api.dmarket.com",
    )


# ============================================================================
# ТЕСТЫ КОМАНДЫ /dmarket
# ============================================================================


@pytest.mark.asyncio()
async def test_status_command_with_keys(mock_update, mock_context):
    """Тест команды /dmarket когда ключи настроены."""
    handler = DMarketHandler(
        public_key="test_public_key",
        secret_key="test_secret_key",
        api_url="https://api.dmarket.com",
    )

    await handler.status_command(mock_update, mock_context)

    # Проверяем, что было отправлено сообщение
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "API ключи DMarket настроены" in call_args
    assert "https://api.dmarket.com" in call_args


@pytest.mark.asyncio()
async def test_status_command_without_keys(mock_update, mock_context):
    """Тест команды /dmarket когда ключи не настроены."""
    handler = DMarketHandler(
        public_key="",
        secret_key="",
        api_url="https://api.dmarket.com",
    )

    await handler.status_command(mock_update, mock_context)

    # Проверяем, что было отправлено сообщение об отсутствии ключей
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "API ключи DMarket не настроены" in call_args


@pytest.mark.asyncio()
async def test_status_command_no_message(mock_context):
    """Тест команды /dmarket когда нет message в update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.message = None

    handler = DMarketHandler(
        public_key="test_public",
        secret_key="test_secret",
        api_url="https://api.dmarket.com",
    )

    # Не должно быть ошибки
    await handler.status_command(update, mock_context)


# ============================================================================
# ТЕСТЫ КОМАНДЫ /balance
# ============================================================================


@pytest.mark.asyncio()
async def test_balance_command_no_api(mock_update, mock_context):
    """Тест команды /balance когда API не инициализирован."""
    handler = DMarketHandler(
        public_key="",
        secret_key="",
        api_url="https://api.dmarket.com",
    )

    await handler.balance_command(mock_update, mock_context)

    # Проверяем, что было отправлено сообщение об ошибке
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "API DMarket не инициализирован" in call_args


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_handlers.DMarketAPI")
async def test_balance_command_success(mock_dmarket_api, mock_update, mock_context):
    """Тест успешного получения баланса."""
    # Настройка мока баланса
    mock_balance = MagicMock()
    mock_balance.totalBalance = 100.50
    mock_balance.blockedBalance = 20.30

    mock_api_instance = MagicMock()
    mock_api_instance.get_balance.return_value = mock_balance
    mock_dmarket_api.return_value = mock_api_instance

    handler = DMarketHandler(
        public_key="test_public",
        secret_key="test_secret",
        api_url="https://api.dmarket.com",
    )

    await handler.balance_command(mock_update, mock_context)

    # Проверяем, что было отправлено сообщение с балансом
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Баланс на DMarket" in call_args
    assert "$100.50" in call_args
    assert "$20.30" in call_args
    assert "$80.20" in call_args  # 100.50 - 20.30


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_handlers.DMarketAPI")
async def test_balance_command_error(mock_dmarket_api, mock_update, mock_context):
    """Тест обработки ошибки при получении баланса."""
    mock_api_instance = MagicMock()
    mock_api_instance.get_balance.side_effect = Exception("API Error")
    mock_dmarket_api.return_value = mock_api_instance

    handler = DMarketHandler(
        public_key="test_public",
        secret_key="test_secret",
        api_url="https://api.dmarket.com",
    )

    await handler.balance_command(mock_update, mock_context)

    # Проверяем, что было отправлено сообщение об ошибке
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Не удалось получить информацию о балансе" in call_args


@pytest.mark.asyncio()
async def test_balance_command_no_message(mock_context):
    """Тест команды /balance когда нет message в update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.message = None

    handler = DMarketHandler(
        public_key="",
        secret_key="",
        api_url="https://api.dmarket.com",
    )

    # Не должно быть ошибки, просто возврат
    await handler.balance_command(update, mock_context)


# ============================================================================
# ТЕСТЫ РЕГИСТРАЦИИ ОБРАБОТЧИКОВ
# ============================================================================


@patch("src.telegram_bot.handlers.dmarket_handlers.DMarketAPI")
def test_register_dmarket_handlers(mock_dmarket_api):
    """Тест регистрации обработчиков DMarket."""
    # Создаем мок приложения
    app = MagicMock(spec=Application)

    # Регистрируем обработчики
    register_dmarket_handlers(
        app=app,
        public_key="test_public",
        secret_key="test_secret",
        api_url="https://api.dmarket.com",
    )

    # Проверяем, что обработчики были добавлены
    assert app.add_handler.call_count == 2

    # Проверяем, что были зарегистрированы правильные команды
    calls = app.add_handler.call_args_list
    commands = [call[0][0].commands for call in calls]

    # CommandHandler возвращает frozenset команд
    all_commands = []
    for cmd in commands:
        all_commands.extend(list(cmd))

    assert "dmarket" in all_commands
    assert "balance" in all_commands

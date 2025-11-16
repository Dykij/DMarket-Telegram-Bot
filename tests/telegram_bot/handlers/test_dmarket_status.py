"""Тесты для обработчика статуса DMarket API.

Этот модуль содержит тесты для:
- Проверки статуса DMarket API
- Получения баланса пользователя
- Обработки различных ошибок авторизации
- Локализации сообщений
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.dmarket_status import dmarket_status_impl


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_update():
    """Создает мок Update с необходимыми атрибутами."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_chat = AsyncMock(spec=Chat)
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Создает мок CallbackContext."""
    return MagicMock(spec=CallbackContext)


@pytest.fixture()
def mock_profile():
    """Создает мок профиля пользователя."""
    return {
        "api_key": "test_public_key",
        "api_secret": "test_secret_key",
        "language": "ru",
    }


# ============================================================================
# ТЕСТЫ УСПЕШНОЙ ПРОВЕРКИ СТАТУСА
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_success(
    mock_check_balance,
    mock_api,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
    mock_profile,
):
    """Тест успешной проверки статуса с балансом."""
    # Настройка моков
    mock_get_profile.return_value = mock_profile
    mock_localized_text.return_value = "Проверка API..."

    # Мок баланса
    mock_check_balance.return_value = {
        "error": False,
        "has_funds": True,
        "balance": 150.50,
    }

    # Мок API клиента
    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    # Мок сообщения статуса
    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    # Вызываем функцию
    await dmarket_status_impl(mock_update, mock_context)

    # Проверки
    mock_update.message.reply_text.assert_called_once()
    status_msg.edit_text.assert_called_once()

    # Проверяем, что сообщение содержит нужную информацию
    call_args = status_msg.edit_text.call_args[0][0]
    assert "✅" in call_args
    assert "150.50" in call_args
    assert "USD" in call_args


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_zero_balance(
    mock_check_balance,
    mock_api,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
    mock_profile,
):
    """Тест проверки статуса с нулевым балансом."""
    mock_get_profile.return_value = mock_profile
    mock_localized_text.return_value = "Проверка API..."

    mock_check_balance.return_value = {
        "error": False,
        "has_funds": False,
        "balance": 0.0,
    }

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    await dmarket_status_impl(mock_update, mock_context)

    # Проверяем предупреждение о нулевом балансе
    call_args = status_msg.edit_text.call_args[0][0]
    assert "⚠️" in call_args
    assert "0.00" in call_args


# ============================================================================
# ТЕСТЫ ОШИБОК АВТОРИЗАЦИИ
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_auth_error(
    mock_check_balance,
    mock_api,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
    mock_profile,
):
    """Тест обработки ошибки авторизации."""
    mock_get_profile.return_value = mock_profile
    mock_localized_text.return_value = "Проверка API..."

    # Симулируем ошибку авторизации
    mock_check_balance.return_value = {
        "error": True,
        "error_message": "Unauthorized: invalid token",
    }

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    await dmarket_status_impl(mock_update, mock_context)

    # Проверяем сообщение об ошибке авторизации
    call_args = status_msg.edit_text.call_args[0][0]
    assert "❌" in call_args
    assert "Авторизация" in call_args or "авторизации" in call_args


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_no_keys(
    mock_check_balance,
    mock_api,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
):
    """Тест проверки статуса без API ключей."""
    # Профиль без ключей
    mock_get_profile.return_value = {
        "api_key": "",
        "api_secret": "",
        "language": "ru",
    }
    mock_localized_text.return_value = "Проверка API..."

    mock_check_balance.return_value = {
        "error": False,
        "balance": 0.0,
    }

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    await dmarket_status_impl(mock_update, mock_context)

    # Проверяем сообщение о необходимости настройки ключей
    call_args = status_msg.edit_text.call_args[0][0]
    assert "❌" in call_args or "недоступен" in call_args.lower()


# ============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК API
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_api_error(
    mock_check_balance,
    mock_api,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
    mock_profile,
):
    """Тест обработки общей ошибки API."""
    mock_get_profile.return_value = mock_profile
    mock_localized_text.return_value = "Проверка API..."

    # Симулируем ошибку API
    mock_check_balance.return_value = {
        "error": True,
        "error_message": "API connection timeout",
    }

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    await dmarket_status_impl(mock_update, mock_context)

    # Проверяем сообщение об ошибке
    call_args = status_msg.edit_text.call_args[0][0]
    assert "⚠️" in call_args or "❌" in call_args


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_exception(
    mock_check_balance,
    mock_api,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
    mock_profile,
):
    """Тест обработки неожиданного исключения."""
    mock_get_profile.return_value = mock_profile
    mock_localized_text.return_value = "Проверка API..."

    # Симулируем исключение
    mock_check_balance.side_effect = Exception("Unexpected error")

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    await dmarket_status_impl(mock_update, mock_context)

    # Проверяем, что сообщение об ошибке было отправлено
    call_args = status_msg.edit_text.call_args[0][0]
    assert "❌" in call_args
    assert "соединения" in call_args.lower() or "ошибка" in call_args.lower()


# ============================================================================
# ТЕСТЫ С ПРЕДОСТАВЛЕННЫМ STATUS_MESSAGE
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_with_status_message(
    mock_check_balance,
    mock_api,
    mock_get_profile,
    mock_update,
    mock_context,
    mock_profile,
):
    """Тест с предоставленным status_message."""
    mock_get_profile.return_value = mock_profile

    mock_check_balance.return_value = {
        "error": False,
        "balance": 100.0,
    }

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    # Предоставляем существующее сообщение статуса
    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()

    await dmarket_status_impl(mock_update, mock_context, status_message=status_msg)

    # Проверяем, что reply_text НЕ был вызван (используется предоставленное сообщение)
    mock_update.message.reply_text.assert_not_called()

    # Но edit_text должен быть вызван
    status_msg.edit_text.assert_called_once()


# ============================================================================
# ТЕСТЫ С ПЕРЕМЕННЫМИ ОКРУЖЕНИЯ
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.dmarket_status.get_user_profile")
@patch("src.telegram_bot.handlers.dmarket_status.get_localized_text")
@patch("src.telegram_bot.handlers.dmarket_status.getenv")
@patch("src.telegram_bot.handlers.dmarket_status.DMarketAPI")
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_dmarket_status_impl_env_keys(
    mock_check_balance,
    mock_api,
    mock_getenv,
    mock_localized_text,
    mock_get_profile,
    mock_update,
    mock_context,
):
    """Тест использования ключей из переменных окружения."""
    # Профиль без ключей
    mock_get_profile.return_value = {
        "api_key": "",
        "api_secret": "",
        "language": "ru",
    }
    mock_localized_text.return_value = "Проверка API..."

    # Ключи из переменных окружения
    def getenv_side_effect(key, default=""):
        if key == "DMARKET_PUBLIC_KEY":
            return "env_public_key"
        if key == "DMARKET_SECRET_KEY":
            return "env_secret_key"
        return default

    mock_getenv.side_effect = getenv_side_effect

    mock_check_balance.return_value = {
        "error": False,
        "balance": 50.0,
    }

    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_api.return_value = mock_api_instance

    status_msg = AsyncMock()
    status_msg.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = status_msg

    await dmarket_status_impl(mock_update, mock_context)

    # Проверяем, что сообщение содержит указание на переменные окружения
    call_args = status_msg.edit_text.call_args[0][0]
    assert "переменных окружения" in call_args or "50.00" in call_args

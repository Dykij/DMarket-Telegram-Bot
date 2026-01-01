"""Тесты для модуля settings_handlers.py.

Этот модуль содержит тесты для обработчиков настроек и локализации.
"""

import os
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from telegram import InlineKeyboardMarkup, Message, Update, User
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.settings_handlers import (
    get_localized_text,
    get_user_profile,
    handle_setup_input,
    register_localization_handlers,
    save_user_profiles,
    settings_callback,
    settings_command,
    setup_command,
)


@pytest.fixture()
def mock_update():
    """Создает мок объекта Update для тестирования."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 123456789

    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.from_user = mock_user
    update.callback_query.data = "settings"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Создает мок объекта CallbackContext для тестирования."""
    context = MagicMock(spec=CallbackContext)
    context.user_data = {}
    return context


@pytest.fixture()
def mock_user_profiles():
    """Создает мок для USER_PROFILES."""
    return {
        "123456789": {
            "language": "ru",
            "api_key": "test_key",
            "api_secret": "test_secret",
            "auto_trading_enabled": False,
            "trade_settings": {
                "min_profit": 2.0,
                "max_price": 50.0,
                "max_trades": 3,
                "risk_level": "medium",
            },
            "last_activity": 1625000000,
        },
    }


@patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES", {})
def test_get_user_profile_new_user():
    """Тестирует получение профиля для нового пользователя."""
    # Получаем профиль для нового пользователя
    user_id = 999999
    profile = get_user_profile(user_id)

    # Проверяем, что был создан профиль с умолчаниями
    assert "settings" in profile
    assert "language" in profile["settings"]
    assert profile["settings"]["language"] == "ru"
    assert "api_keys" in profile
    assert "access_level" in profile


def test_get_user_profile_existing_user():
    """Тестирует получение профиля для существующего пользователя."""
    # Настройка - работаем с UserProfileManager
    from src.telegram_bot.handlers import settings_handlers

    # Получаем доступ к _profile_manager
    try:
        manager = settings_handlers._profile_manager
        original_profiles = manager._profiles.copy()

        try:
            manager._profiles.clear()
            user_id = 123456789

            # Создаем профиль пользователя с новой структурой
            manager._profiles[user_id] = {
                "settings": {"language": "en"},
                "api_keys": {
                    "public": "existing_key",
                    "secret": "existing_secret",
                },
                "access_level": "premium",
            }

            # Получаем профиль для существующего пользователя
            profile = get_user_profile(user_id)

            # Проверяем, что был возвращен существующий профиль
            assert profile["settings"]["language"] == "en"
            assert profile["api_keys"]["public"] == "existing_key"
            assert profile["access_level"] == "premium"
        finally:
            # Восстанавливаем исходное состояние
            manager._profiles.clear()
            manager._profiles.update(original_profiles)
    except AttributeError:
        # Если _profile_manager не существует, используем простой USER_PROFILES
        original_profiles = settings_handlers.USER_PROFILES.copy()
        try:
            settings_handlers.USER_PROFILES.clear()
            user_id = 123456789
            user_id_str = str(user_id)

            settings_handlers.USER_PROFILES[user_id_str] = {
                "language": "en",
                "api_key": "existing_key",
                "api_secret": "existing_secret",
                "auto_trading_enabled": True,
            }

            profile = get_user_profile(user_id)

            assert profile["language"] == "en"
            assert profile["api_key"] == "existing_key"
            assert profile["auto_trading_enabled"] is True
        finally:
            settings_handlers.USER_PROFILES.clear()
            settings_handlers.USER_PROFILES.update(original_profiles)


@patch(
    "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
    {
        "ru": {"greeting": "Привет", "settings": "Настройки"},
        "en": {"greeting": "Hello", "settings": "Settings"},
    },
)
def test_get_localized_text():
    """Тестирует получение локализованного текста."""
    # Настройка - работаем с UserProfileManager
    from src.telegram_bot.handlers import settings_handlers

    try:
        manager = settings_handlers._profile_manager
        original_profiles = manager._profiles.copy()

        try:
            manager._profiles.clear()
            user_id = 123456789

            # Создаем профиль пользователя с английским языком
            manager._profiles[user_id] = {"settings": {"language": "en"}}

            # Получаем локализованный текст
            text = get_localized_text(user_id, "greeting")

            # Проверяем, что был возвращен правильный текст
            assert text == "Hello"
        finally:
            manager._profiles.clear()
            manager._profiles.update(original_profiles)
    except AttributeError:
        # Если _profile_manager не существует
        original_profiles = settings_handlers.USER_PROFILES.copy()
        try:
            settings_handlers.USER_PROFILES.clear()
            user_id_str = str(123456789)
            settings_handlers.USER_PROFILES[user_id_str] = {"language": "en"}
            text = get_localized_text(123456789, "greeting")
            assert text == "Hello"
        finally:
            settings_handlers.USER_PROFILES.clear()
            settings_handlers.USER_PROFILES.update(original_profiles)


@patch(
    "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
    {
        "ru": {"greeting": "Привет, {name}!", "settings": "Настройки"},
        "en": {"greeting": "Hello, {name}!", "settings": "Settings"},
    },
)
def test_get_localized_text_with_params():
    """Тестирует получение локализованного текста с параметрами."""
    # Настройка - работаем с UserProfileManager
    from src.telegram_bot.handlers import settings_handlers

    try:
        manager = settings_handlers._profile_manager
        original_profiles = manager._profiles.copy()

        try:
            manager._profiles.clear()
            user_id = 123456789

            # Создаем профиль пользователя с английским языком
            manager._profiles[user_id] = {"settings": {"language": "en"}}

            # Получаем локализованный текст с параметром
            text = get_localized_text(user_id, "greeting", name="John")

            # Проверяем, что был возвращен правильный текст с подставленным параметром
            assert text == "Hello, John!"
        finally:
            manager._profiles.clear()
            manager._profiles.update(original_profiles)
    except AttributeError:
        # Если _profile_manager не существует
        original_profiles = settings_handlers.USER_PROFILES.copy()
        try:
            settings_handlers.USER_PROFILES.clear()
            user_id_str = str(123456789)
            settings_handlers.USER_PROFILES[user_id_str] = {"language": "en"}
            text = get_localized_text(123456789, "greeting", name="John")
            assert text == "Hello, John!"
        finally:
            settings_handlers.USER_PROFILES.clear()
            settings_handlers.USER_PROFILES.update(original_profiles)


@patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES")
@patch(
    "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
    {
        "ru": {"greeting": "Привет", "settings": "Настройки"},
        "en": {"hello": "Hello"},  # "greeting" отсутствует в английском
    },
)
def test_get_localized_text_missing_key(mock_profiles):
    """Тестирует получение локализованного текста при отсутствии ключа."""
    # Настройка мока для USER_PROFILES
    user_id = 123456789
    mock_profiles.get.return_value = {"language": "en"}
    mock_profiles.__getitem__.return_value = mock_profiles.get.return_value
    mock_profiles.__contains__.return_value = True

    # Получаем локализованный текст для отсутствующего ключа
    text = get_localized_text(user_id, "greeting")

    # Проверяем, что был возвращен текст из русского языка
    assert text == "Привет"


@patch("src.telegram_bot.handlers.settings_handlers.USER_PROFILES")
@patch(
    "src.telegram_bot.handlers.settings_handlers.LOCALIZATIONS",
    {
        "ru": {"greeting": "Привет", "settings": "Настройки"},
        "en": {"greeting": "Hello", "settings": "Settings"},
    },
)
def test_get_localized_text_unsupported_language(mock_profiles):
    """Тестирует получение локализованного текста при неподдерживаемом языке."""
    # Настройка мока для USER_PROFILES
    user_id = 123456789
    mock_profiles.get.return_value = {"language": "de"}  # Немецкий не поддерживается
    mock_profiles.__getitem__.return_value = mock_profiles.get.return_value
    mock_profiles.__contains__.return_value = True

    # Получаем локализованный текст с неподдерживаемым языком
    text = get_localized_text(user_id, "greeting")

    # Проверяем, что был возвращен текст из русского языка
    assert text == "Привет"


@patch(
    "src.telegram_bot.handlers.settings_handlers.USER_PROFILES",
    {"123456789": {"language": "ru"}},
)
@patch("os.path.dirname")
@patch("builtins.open", new_callable=mock_open)
@patch("json.dump")
def test_save_user_profiles(mock_json_dump, mock_file_open, mock_dirname):
    """Тестирует сохранение профилей пользователей."""
    # Настройка мока для os.path.dirname
    mock_dirname.return_value = "/test/path"

    # Вызываем тестируемую функцию
    save_user_profiles()

    # Проверяем, что был вызван open с правильным путем
    # Используем os.path.join для правильного формирования пути в разных ОС
    expected_path = os.path.join("/test/path", "user_profiles.json")
    mock_file_open.assert_called_once_with(
        expected_path,
        "w",
        encoding="utf-8",
    )

    # Проверяем, что был вызван json.dump с правильными данными
    mock_json_dump.assert_called_once()
    args, kwargs = mock_json_dump.call_args
    assert args[0] == {"123456789": {"language": "ru"}}
    assert kwargs["ensure_ascii"] is False
    assert kwargs["indent"] == 2


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
async def test_settings_command(
    mock_get_settings_keyboard,
    mock_get_localized_text,
    mock_update,
    mock_context,
):
    """Тестирует обработку команды /settings."""
    # Настройка моков
    # Примечание: get_user_profile больше не вызывается в settings_command
    mock_get_localized_text.return_value = "Настройки бота"
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_settings_keyboard.return_value = mock_keyboard

    # Вызываем тестируемую функцию
    await settings_command(mock_update, mock_context)

    # Проверяем, что были вызваны правильные функции
    mock_get_localized_text.assert_called_once_with(
        mock_update.effective_user.id,
        "settings",
    )
    # get_settings_keyboard вызывается без параметров
    mock_get_settings_keyboard.assert_called_once_with()

    # Проверяем, что был вызван reply_text с правильными аргументами
    mock_update.message.reply_text.assert_called_once_with(
        "Настройки бота",
        reply_markup=mock_keyboard,
    )


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
async def test_settings_callback_main_menu(
    mock_get_settings_keyboard,
    mock_get_localized_text,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с основным меню настроек."""
    # Настройка моков
    # Примечание: get_user_profile больше не вызывается для data == "settings"
    mock_get_localized_text.return_value = "Настройки бота"
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_settings_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "settings"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что были вызваны правильные функции
    mock_get_localized_text.assert_called_once_with(
        mock_update.callback_query.from_user.id,
        "settings",
    )
    # get_settings_keyboard вызывается без параметров
    mock_get_settings_keyboard.assert_called_once_with()

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    mock_update.callback_query.edit_message_text.assert_called_once_with(
        text="Настройки бота",
        reply_markup=mock_keyboard,
    )


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.handlers.settings_handlers.get_language_keyboard")
async def test_settings_callback_language_menu(
    mock_get_language_keyboard,
    mock_get_localized_text,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с меню выбора языка."""
    # Настройка моков
    mock_profile = {"language": "ru"}
    mock_get_user_profile.return_value = mock_profile
    mock_get_localized_text.return_value = "Выберите язык (текущий: Русский)"
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_language_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "settings_language"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что были вызваны правильные функции
    mock_get_user_profile.assert_called_once_with(
        mock_update.callback_query.from_user.id,
    )
    mock_get_localized_text.assert_called_once()
    mock_get_language_keyboard.assert_called_once_with("ru")

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    mock_update.callback_query.edit_message_text.assert_called_once_with(
        text="Выберите язык (текущий: Русский)",
        reply_markup=mock_keyboard,
    )


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
@patch(
    "src.telegram_bot.handlers.settings_handlers.LANGUAGES",
    {"ru": "Русский", "en": "English"},
)
async def test_settings_callback_language_set(
    mock_get_back_keyboard,
    mock_get_localized_text,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с установкой языка."""
    # Настройка моков
    mock_profile = {"language": "ru"}
    mock_get_user_profile.return_value = mock_profile
    mock_get_localized_text.return_value = "Язык изменен на English"
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_back_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "language:en"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что профиль был обновлен
    assert mock_profile["language"] == "en"

    # Проверяем, что профили были сохранены
    mock_save_profiles.assert_called_once()

    # Проверяем, что были вызваны правильные функции
    mock_get_back_keyboard.assert_called_once()

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    mock_update.callback_query.edit_message_text.assert_called_once_with(
        text="Язык изменен на English",
        reply_markup=mock_keyboard,
    )


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.handlers.settings_handlers.get_settings_keyboard")
async def test_settings_callback_toggle_trading(
    mock_get_settings_keyboard,
    mock_get_localized_text,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с переключением режима автоматической торговли."""
    # Настройка моков
    mock_profile = {"auto_trading_enabled": False, "language": "ru"}
    mock_get_user_profile.return_value = mock_profile
    mock_get_localized_text.side_effect = lambda user_id, key: (
        "Настройки бота" if key == "settings" else "Авто-торговля включена"
    )
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_settings_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "settings_toggle_trading"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что профиль был обновлен
    assert mock_profile["auto_trading_enabled"] is True

    # Проверяем, что профили были сохранены
    mock_save_profiles.assert_called_once()

    # Проверяем, что get_settings_keyboard был вызван (без аргументов - функция их не принимает)
    mock_get_settings_keyboard.assert_called_once_with()

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    mock_update.callback_query.edit_message_text.assert_called_once()

    # Исправлено: безопасный доступ к аргументам
    call_args = mock_update.callback_query.edit_message_text.call_args
    # Проверяем сначала kwargs, т.к. в них может быть text
    if call_args.kwargs and "text" in call_args.kwargs:
        message_text = call_args.kwargs["text"]
    # Если вызов был с позиционным аргументом
    elif call_args.args:
        message_text = call_args.args[0]
    else:
        message_text = ""

    assert "Настройки бота" in message_text
    assert "Авто-торговля включена" in message_text
    assert call_args.kwargs.get("reply_markup") == mock_keyboard


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
async def test_settings_callback_api_keys(
    mock_get_back_keyboard,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с отображением настроек API ключей."""
    # Настройка моков
    mock_profile = {
        "api_key": "abcde12345fghij67890",
        "api_secret": "secret123456",
        "language": "ru",
    }
    mock_get_user_profile.return_value = mock_profile
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_back_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "settings_api_keys"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что были вызваны правильные функции
    mock_get_back_keyboard.assert_called_once()

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    mock_update.callback_query.edit_message_text.assert_called_once()

    # Исправлено: безопасный доступ к аргументам
    call_args = mock_update.callback_query.edit_message_text.call_args
    # Проверяем сначала kwargs, т.к. в них может быть text
    if call_args.kwargs and "text" in call_args.kwargs:
        message_text = call_args.kwargs["text"]
    # Если вызов был с позиционным аргументом
    elif call_args.args:
        message_text = call_args.args[0]
    else:
        message_text = ""

    # Проверяем, что показаны маскированные ключи
    assert (
        "abcde...67890" in message_text
    )  # Показаны первые 5 и последние 5 символов ключа
    assert (
        "sec...456" in message_text
    )  # Показаны первые 3 и последние 3 символа секрета
    assert call_args.kwargs.get("reply_markup") == mock_keyboard


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.handlers.settings_handlers.get_language_keyboard")
async def test_settings_callback_language_invalid(
    mock_get_language_keyboard,
    mock_get_localized_text,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с невалидным кодом языка."""
    # Настройка моков
    mock_profile = {"language": "ru"}
    mock_get_user_profile.return_value = mock_profile
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_language_keyboard.return_value = mock_keyboard

    # Настройка данных callback - несуществующий язык
    mock_update.callback_query.data = "language:invalid"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что профиль НЕ был изменен
    assert mock_profile["language"] == "ru"

    # Проверяем, что НЕ было вызова save_user_profiles
    mock_save_profiles.assert_not_called()

    # Проверяем, что был показан error text
    mock_update.callback_query.edit_message_text.assert_called_once()
    call_args = mock_update.callback_query.edit_message_text.call_args

    if call_args.kwargs and "text" in call_args.kwargs:
        message_text = call_args.kwargs["text"]
    elif call_args.args:
        message_text = call_args.args[0]
    else:
        message_text = ""

    assert "invalid" in message_text or "не поддерживается" in message_text


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.get_risk_profile_keyboard")
async def test_settings_callback_settings_limits(
    mock_get_risk_keyboard,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с отображением лимитов торговли."""
    # Настройка моков
    mock_profile = {
        "trade_settings": {
            "min_profit": 3.5,
            "max_price": 75.0,
            "max_trades": 8,
            "risk_level": "high",
        },
    }
    mock_get_user_profile.return_value = mock_profile
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_risk_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "settings_limits"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что были вызваны правильные функции
    mock_get_risk_keyboard.assert_called_once_with("high")

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    mock_update.callback_query.edit_message_text.assert_called_once()
    call_args = mock_update.callback_query.edit_message_text.call_args

    if call_args.kwargs and "text" in call_args.kwargs:
        message_text = call_args.kwargs["text"]
    elif call_args.args:
        message_text = call_args.args[0]
    else:
        message_text = ""

    # Проверяем, что отображены правильные значения
    assert "$3.50" in message_text
    assert "$75.00" in message_text
    assert "8" in message_text
    assert "high" in message_text


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
async def test_settings_callback_risk_low(
    mock_get_back_keyboard,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с установкой низкого уровня риска."""
    # Настройка моков
    mock_profile = {"trade_settings": {}}
    mock_get_user_profile.return_value = mock_profile
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_back_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "risk_profile:low"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что профиль был обновлен правильно
    assert mock_profile["trade_settings"]["risk_level"] == "low"
    assert mock_profile["trade_settings"]["min_profit"] == 1.0
    assert mock_profile["trade_settings"]["max_price"] == 30.0
    assert mock_profile["trade_settings"]["max_trades"] == 2

    # Проверяем, что профили были сохранены
    mock_save_profiles.assert_called_once()

    # Проверяем текст ответа
    call_args = mock_update.callback_query.edit_message_text.call_args
    if call_args.kwargs and "text" in call_args.kwargs:
        message_text = call_args.kwargs["text"]
    elif call_args.args:
        message_text = call_args.args[0]
    else:
        message_text = ""

    assert "low" in message_text
    assert "$1.00" in message_text
    assert "$30.00" in message_text


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
async def test_settings_callback_risk_medium(
    mock_get_back_keyboard,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с установкой среднего уровня риска."""
    # Настройка моков
    mock_profile = {"trade_settings": {}}
    mock_get_user_profile.return_value = mock_profile
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_back_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "risk_profile:medium"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что профиль был обновлен правильно
    assert mock_profile["trade_settings"]["risk_level"] == "medium"
    assert mock_profile["trade_settings"]["min_profit"] == 2.0
    assert mock_profile["trade_settings"]["max_price"] == 50.0
    assert mock_profile["trade_settings"]["max_trades"] == 5


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_back_to_settings_keyboard")
async def test_settings_callback_risk_high(
    mock_get_back_keyboard,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с установкой высокого уровня риска."""
    # Настройка моков
    mock_profile = {"trade_settings": {}}
    mock_get_user_profile.return_value = mock_profile
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_back_keyboard.return_value = mock_keyboard

    # Настройка данных callback
    mock_update.callback_query.data = "risk_profile:high"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что профиль был обновлен правильно
    assert mock_profile["trade_settings"]["risk_level"] == "high"
    assert mock_profile["trade_settings"]["min_profit"] == 5.0
    assert mock_profile["trade_settings"]["max_price"] == 100.0
    assert mock_profile["trade_settings"]["max_trades"] == 10


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
@patch("src.telegram_bot.keyboards.get_arbitrage_keyboard")
async def test_settings_callback_back_to_menu(
    mock_get_arbitrage_keyboard,
    mock_get_localized_text,
    mock_update,
    mock_context,
):
    """Тестирует обработку callback с возвратом в главное меню."""
    # Настройка моков
    mock_get_localized_text.return_value = "Добро пожаловать!"
    mock_keyboard = MagicMock(spec=InlineKeyboardMarkup)
    mock_get_arbitrage_keyboard.return_value = mock_keyboard

    # Настройка mock user для mention_html
    mock_update.callback_query.from_user.mention_html = MagicMock(
        return_value="<a href='tg://user?id=123456789'>Test User</a>",
    )

    # Настройка данных callback
    mock_update.callback_query.data = "back_to_menu"

    # Вызываем тестируемую функцию
    await settings_callback(mock_update, mock_context)

    # Проверяем, что был вызван answer
    mock_update.callback_query.answer.assert_called_once()

    # Проверяем, что были вызваны правильные функции
    mock_get_arbitrage_keyboard.assert_called_once()
    mock_get_localized_text.assert_called_once()

    # Проверяем, что был вызван edit_message_text с правильными аргументами
    call_args = mock_update.callback_query.edit_message_text.call_args
    assert call_args.kwargs.get("parse_mode") == "HTML"
    assert call_args.kwargs.get("reply_markup") == mock_keyboard


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
async def test_setup_command(
    mock_get_localized_text,
    mock_update,
    mock_context,
):
    """Тестирует обработку команды /setup."""
    # Настройка моков
    mock_get_localized_text.return_value = "Введите ваш публичный API ключ:"

    # Вызываем тестируемую функцию
    await setup_command(mock_update, mock_context)

    # Проверяем, что был установлен setup_state
    assert mock_context.user_data.get("setup_state") == "waiting_api_key"

    # Проверяем, что был вызван reply_text с правильными аргументами
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args

    if call_args.args:
        message_text = call_args.args[0]
    else:
        message_text = ""

    assert "Настройка API ключей DMarket" in message_text
    assert "Введите ваш публичный API ключ:" in message_text


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
async def test_handle_setup_input_api_key(
    mock_get_localized_text,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку ввода API ключа."""
    # Настройка моков
    mock_profile = {}
    mock_get_user_profile.return_value = mock_profile
    mock_get_localized_text.return_value = "Введите ваш секретный API ключ:"

    # Устанавливаем состояние - ожидание API ключа
    mock_context.user_data = {"setup_state": "waiting_api_key"}
    mock_update.message.text = "test_public_key_12345"

    # Вызываем тестируемую функцию
    await handle_setup_input(mock_update, mock_context)

    # Проверяем, что API ключ был сохранен
    assert mock_profile["api_key"] == "test_public_key_12345"

    # Проверяем, что профили были сохранены
    mock_save_profiles.assert_called_once()

    # Проверяем, что состояние изменилось на ожидание секретного ключа
    assert mock_context.user_data["setup_state"] == "waiting_api_secret"

    # Проверяем, что был запрошен секретный ключ
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.handlers.settings_handlers.get_user_profile")
@patch("src.telegram_bot.handlers.settings_handlers.save_user_profiles")
@patch("src.telegram_bot.handlers.settings_handlers.get_localized_text")
async def test_handle_setup_input_api_secret(
    mock_get_localized_text,
    mock_save_profiles,
    mock_get_user_profile,
    mock_update,
    mock_context,
):
    """Тестирует обработку ввода секретного ключа."""
    # Настройка моков
    mock_profile = {"api_key": "test_public_key"}
    mock_get_user_profile.return_value = mock_profile
    mock_get_localized_text.return_value = "API ключи успешно сохранены!"

    # Устанавливаем состояние - ожидание секретного ключа
    mock_context.user_data = {"setup_state": "waiting_api_secret"}
    mock_update.message.text = "test_secret_key_67890"

    # Вызываем тестируемую функцию
    await handle_setup_input(mock_update, mock_context)

    # Проверяем, что секретный ключ был сохранен
    assert mock_profile["api_secret"] == "test_secret_key_67890"

    # Проверяем, что профили были сохранены
    mock_save_profiles.assert_called_once()

    # Проверяем, что setup_state был удален
    assert "setup_state" not in mock_context.user_data

    # Проверяем, что было отправлено подтверждение
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio()
async def test_handle_setup_input_no_setup_state(
    mock_update,
    mock_context,
):
    """Тестирует обработку ввода при отсутствии активного setup."""
    # Настройка - нет setup_state
    mock_context.user_data = {}
    mock_update.message.text = "random text"

    # Вызываем тестируемую функцию
    await handle_setup_input(mock_update, mock_context)

    # Проверяем, что reply_text НЕ был вызван
    mock_update.message.reply_text.assert_not_called()


def test_register_localization_handlers():
    """Тестирует регистрацию обработчиков."""

    # Создаем мок application
    mock_app = MagicMock()

    # Вызываем функцию регистрации
    register_localization_handlers(mock_app)

    # Проверяем, что add_handler был вызван несколько раз
    assert mock_app.add_handler.call_count >= 5  # Минимум 5 handlers

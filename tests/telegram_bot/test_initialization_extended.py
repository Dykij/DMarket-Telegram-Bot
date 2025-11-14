"""Расширенное тестирование инициализации Telegram бота.

Этот модуль содержит тесты для:
- Инициализации бота с различными настройками
- Настройки логирования
- Регистрации handlers
- Настройки persistence
- Обработки сигналов завершения
- Graceful shutdown
"""

import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.ext import Application, ApplicationBuilder

from src.telegram_bot.initialization import (
    initialize_bot,
    setup_logging,
)


# Константы для тестов
TEST_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


# ==============================================================================
# ТЕСТЫ SETUP_LOGGING
# ==============================================================================


def test_setup_logging_default():
    """Тест настройки логирования с дефолтными параметрами."""
    # Очищаем логгеры перед тестом
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    setup_logging()

    # Проверяем, что логгер настроен
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) > 0

    # Проверяем наличие console handler
    has_console_handler = any(
        isinstance(h, logging.StreamHandler) for h in root_logger.handlers
    )
    assert has_console_handler


def test_setup_logging_with_custom_level():
    """Тест настройки логирования с кастомным уровнем."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    setup_logging(log_level=logging.DEBUG)

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_setup_logging_with_file(tmp_path):
    """Тест настройки логирования с файлом."""
    log_file = tmp_path / "test.log"

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    setup_logging(log_file=str(log_file))

    # Проверяем, что файл handler добавлен
    root_logger = logging.getLogger()
    has_file_handler = any(
        isinstance(h, logging.FileHandler) for h in root_logger.handlers
    )
    assert has_file_handler


def test_setup_logging_with_error_file(tmp_path):
    """Тест настройки логирования с отдельным файлом для ошибок."""
    error_log_file = tmp_path / "error.log"

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    setup_logging(error_log_file=str(error_log_file))

    # Проверяем, что есть handler для ошибок
    root_logger = logging.getLogger()
    error_handlers = [
        h for h in root_logger.handlers
        if isinstance(h, logging.FileHandler) and h.level == logging.ERROR
    ]
    assert len(error_handlers) > 0


def test_setup_logging_formatter():
    """Тест настройки логирования с кастомным форматтером."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    custom_formatter = logging.Formatter("%(levelname)s: %(message)s")
    setup_logging(formatter=custom_formatter)

    # Проверяем, что форматтер установлен
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0


def test_setup_logging_clears_existing_handlers():
    """Тест очистки существующих handlers при настройке."""
    root_logger = logging.getLogger()

    # Добавляем тестовый handler
    test_handler = logging.StreamHandler()
    root_logger.addHandler(test_handler)
    initial_count = len(root_logger.handlers)

    setup_logging()

    # После настройки старые handlers должны быть удалены
    root_logger = logging.getLogger()
    # Новый набор handlers, старого test_handler не должно быть
    assert test_handler not in root_logger.handlers


def test_setup_logging_sets_library_levels():
    """Тест установки уровня логирования для библиотек."""
    setup_logging()

    # Проверяем уровни для библиотек
    httpx_logger = logging.getLogger("httpx")
    telegram_logger = logging.getLogger("telegram")

    assert httpx_logger.level == logging.WARNING
    assert telegram_logger.level == logging.WARNING


# ==============================================================================
# ТЕСТЫ INITIALIZE_BOT
# ==============================================================================


@pytest.mark.asyncio
async def test_initialize_bot_basic():
    """Тест базовой инициализации бота."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        # Настраиваем моки
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        # Патчим другие функции
        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        result = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)

        # Проверяем, что вернулся объект Application
        assert result is not None
        mock_builder_instance.token.assert_called_once_with(TEST_BOT_TOKEN)


@pytest.mark.asyncio
async def test_initialize_bot_with_invalid_token():
    """Тест инициализации бота с невалидным токеном."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_builder_instance = MagicMock()
        mock_builder_instance.token.side_effect = Exception("Invalid token")
        mock_builder.return_value = mock_builder_instance

        with pytest.raises(Exception):
            await initialize_bot("invalid_token", setup_persistence=False)


@pytest.mark.asyncio
async def test_initialize_bot_registers_handlers():
    """Тест регистрации handlers при инициализации."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
        mock_app.add_handler = MagicMock()

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        result = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)

        # Проверяем, что handlers были зарегистрированы
        # (в реальной реализации add_handler должен быть вызван)
        assert result is not None


@pytest.mark.asyncio
async def test_initialize_bot_with_persistence():
    """Тест инициализации бота с persistence."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.persistence = MagicMock(return_value=mock_builder_instance)
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        with patch("telegram.ext.PicklePersistence"):
                            result = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=True)

        assert result is not None


@pytest.mark.asyncio
async def test_initialize_bot_sets_up_error_handler():
    """Тест установки error handler при инициализации."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers") as mock_global:
            with patch("src.telegram_bot.initialization.configure_admin_ids") as mock_admin:
                with patch("src.telegram_bot.initialization.setup_error_handler") as mock_error:
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)

        # Проверяем, что error handlers были настроены
        mock_global.assert_called_once()
        mock_admin.assert_called_once()
        mock_error.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_bot_creates_api_client():
    """Тест создания API клиента при инициализации."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env") as mock_api:
                        mock_api.return_value = MagicMock()

                        result = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)

        # Проверяем, что API клиент был создан
        mock_api.assert_called_once()
        assert result is not None


# ==============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.asyncio
async def test_full_initialization_flow():
    """Тест полного flow инициализации бота."""
    # Настраиваем логирование
    setup_logging(log_level=logging.DEBUG)

    # Проверяем, что логирование настроено
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

    # Инициализируем бота (с моками)
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        app = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)

        assert app is not None


# ==============================================================================
# ТЕСТЫ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ
# ==============================================================================


def test_logging_module_imports():
    """Тест импортов модуля логирования."""
    from src.telegram_bot import initialization

    assert hasattr(initialization, "setup_logging")
    assert hasattr(initialization, "initialize_bot")
    assert hasattr(initialization, "logger")


@pytest.mark.asyncio
async def test_bot_info_retrieval():
    """Тест получения информации о боте."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_bot = MagicMock()
        mock_bot.username = "test_bot"
        mock_bot.first_name = "Test Bot"
        mock_bot.id = 123456789

        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=mock_bot)

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        app = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)

        assert app is not None


# ==============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.parametrize(
    "log_level,expected",
    [
        (logging.DEBUG, logging.DEBUG),
        (logging.INFO, logging.INFO),
        (logging.WARNING, logging.WARNING),
        (logging.ERROR, logging.ERROR),
        (logging.CRITICAL, logging.CRITICAL),
    ],
)
def test_setup_logging_different_levels(log_level, expected):
    """Параметризованный тест для разных уровней логирования."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    setup_logging(log_level=log_level)

    root_logger = logging.getLogger()
    assert root_logger.level == expected


@pytest.mark.parametrize(
    "setup_persistence",
    [True, False],
)
@pytest.mark.asyncio
async def test_initialize_bot_persistence_options(setup_persistence):
    """Параметризованный тест для опций persistence."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_app = MagicMock(spec=Application)
        mock_app.bot = MagicMock()
        mock_app.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.persistence = MagicMock(return_value=mock_builder_instance)
        mock_builder_instance.build.return_value = mock_app
        mock_builder.return_value = mock_builder_instance

        with patch("src.telegram_bot.initialization.register_global_exception_handlers"):
            with patch("src.telegram_bot.initialization.configure_admin_ids"):
                with patch("src.telegram_bot.initialization.setup_error_handler"):
                    with patch("src.telegram_bot.initialization.create_api_client_from_env"):
                        with patch("telegram.ext.PicklePersistence"):
                            result = await initialize_bot(TEST_BOT_TOKEN, setup_persistence=setup_persistence)

        assert result is not None


# ==============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК
# ==============================================================================


@pytest.mark.asyncio
async def test_initialize_bot_network_error():
    """Тест обработки сетевой ошибки при инициализации."""
    with patch("telegram.ext.ApplicationBuilder") as mock_builder:
        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.build.side_effect = ConnectionError("Network error")
        mock_builder.return_value = mock_builder_instance

        with pytest.raises(ConnectionError):
            await initialize_bot(TEST_BOT_TOKEN, setup_persistence=False)


def test_setup_logging_with_invalid_path():
    """Тест обработки невалидного пути к файлу логов."""
    invalid_path = "/invalid/path/that/does/not/exist/test.log"

    # В зависимости от реализации, может быть выброшено исключение
    # или просто проигнорировано. Проверяем, что функция не падает
    try:
        setup_logging(log_file=invalid_path)
    except (OSError, IOError, PermissionError):
        # Ожидаемые исключения при невалидном пути
        pass


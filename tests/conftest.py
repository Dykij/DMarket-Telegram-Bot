"""Конфигурация pytest для модуля utils.

Этот файл содержит фикстуры для тестирования модулей в директории src/utils.
"""

import logging
import os
from unittest.mock import AsyncMock, MagicMock

import pytest


# ==============================================================================
# HYPOTHESIS ПРОФИЛЬ НАСТРОЙКА (для CI)
# ==============================================================================

def pytest_configure(config):
    """Настроить pytest перед запуском тестов.

    Автоматически устанавливает Hypothesis CI профиль в GitHub Actions.
    """
    # Автоматически используем CI профиль в GitHub Actions
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        os.environ.setdefault("HYPOTHESIS_PROFILE", "ci")

    # Попытка загрузить Hypothesis профили из pyproject.toml
    try:
        from hypothesis import settings as hypothesis_settings
        # Проверяем, существует ли профиль ci
        # Если HYPOTHESIS_PROFILE=ci, hypothesis автоматически использует его
    except ImportError:
        pass  # Hypothesis не установлен


# ==============================================================================
# ФИКСТУРЫ
# ==============================================================================


@pytest.fixture()
def mock_logger():
    """Создает мок объекта логгера для тестирования функций логирования и обработки ошибок."""
    logger = MagicMock(spec=logging.Logger)
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    logger.exception = MagicMock()

    return logger


@pytest.fixture()
def mock_http_response():
    """Создает мок HTTP ответа для тестирования функций обработки API ошибок."""
    response = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={"success": True, "data": {}})
    response.text = '{"success": true, "data": {}}'
    response.headers = {"Content-Type": "application/json"}

    return response


@pytest.fixture()
def mock_http_error_response():
    """Создает мок HTTP ответа с ошибкой для тестирования обработки ошибок API."""
    response = MagicMock()
    response.status_code = 429
    response.json = MagicMock(return_value={"error": "Rate limit exceeded"})
    response.text = '{"error": "Rate limit exceeded"}'
    response.headers = {"Content-Type": "application/json", "Retry-After": "5"}

    return response


@pytest.fixture()
def mock_async_client():
    """Создает мок для асинхронного HTTP клиента."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()

    return client


def generate_test_user_data() -> dict:
    """Generate test user data for database tests."""
    return {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
    }

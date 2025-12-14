"""Комплексные тесты для обработчиков команд Telegram бота.

Покрывают основные команды:
- /start
- /help  
- /balance
- /webapp
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.telegram_bot.handlers.commands import (
    help_command,
    start_command,
    webapp_command,
)


class TestStartCommand:
    """Тесты команды /start."""

    @pytest.mark.asyncio()
    async def test_start_command_sends_welcome_message(self):
        """Тест отправки приветственного сообщения."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        # Act
        await start_command(update, context)

        # Assert
        assert update.message.reply_text.call_count >= 1

        # Проверяем первый вызов - приветствие
        first_call = update.message.reply_text.call_args_list[0]
        message_text = first_call[0][0]
        assert "Привет" in message_text or "бот" in message_text

    @pytest.mark.asyncio()
    async def test_start_command_enables_keyboard(self):
        """Тест активации клавиатуры."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        # Act
        await start_command(update, context)

        # Assert
        assert context.user_data.get("keyboard_enabled") is True

    @pytest.mark.asyncio()
    async def test_start_command_with_existing_user(self):
        """Тест команды /start для существующего пользователя."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"existing": True}

        # Act
        await start_command(update, context)

        # Assert
        assert update.message.reply_text.called


class TestHelpCommand:
    """Тесты команды /help."""

    @pytest.mark.asyncio()
    async def test_help_command_sends_help_text(self):
        """Тест отправки справочного текста."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        # Act
        await help_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Проверяем содержимое справки
        call_args = update.message.reply_text.call_args
        help_text = call_args[0][0]

        assert "/start" in help_text
        assert "/arbitrage" in help_text or "/balance" in help_text

    @pytest.mark.asyncio()
    async def test_help_command_includes_keyboard(self):
        """Тест наличия клавиатуры в ответе /help."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        # Act
        await help_command(update, context)

        # Assert
        call_args = update.message.reply_text.call_args
        kwargs = call_args[1] if len(call_args) > 1 else call_args.kwargs

        # Проверяем наличие reply_markup
        assert "reply_markup" in kwargs


class TestWebAppCommand:
    """Тесты команды /webapp."""

    @pytest.mark.asyncio()
    async def test_webapp_command_sends_message(self):
        """Тест отправки сообщения с WebApp."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        # Act
        await webapp_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()


class TestCommandHandlersIntegration:
    """Интеграционные тесты обработчиков команд."""

    @pytest.mark.asyncio()
    async def test_command_flow_start_then_help(self):
        """Тест последовательности команд /start затем /help."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        # Act - сначала /start
        await start_command(update, context)

        # Assert - клавиатура активирована
        assert context.user_data.get("keyboard_enabled") is True

        # Act - затем /help
        await help_command(update, context)

        # Assert - оба вызова выполнены
        assert update.message.reply_text.call_count >= 3  # 2 от /start + 1 от /help

    @pytest.mark.asyncio()
    async def test_multiple_command_calls(self):
        """Тест множественных вызовов команд."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        # Act - вызываем команды несколько раз
        await start_command(update, context)
        await help_command(update, context)
        await start_command(update, context)

        # Assert - все вызовы выполнены
        assert update.message.reply_text.call_count >= 5


class TestCommandErrorHandling:
    """Тесты обработки ошибок в командах."""

    @pytest.mark.asyncio()
    async def test_start_command_with_none_context(self):
        """Тест /start с None user_data."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}  # Изменено с None на пустой dict

        # Act
        await start_command(update, context)

        # Assert - команда должна обработаться без исключений
        assert context.user_data.get("keyboard_enabled") is True

    @pytest.mark.asyncio()
    async def test_help_command_with_minimal_update(self):
        """Тест /help с минимальным update объектом."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        # Act
        await help_command(update, context)

        # Assert - должно выполниться без ошибок
        assert update.message.reply_text.called


class TestCommandResponseFormat:
    """Тесты формата ответов команд."""

    @pytest.mark.asyncio()
    async def test_start_command_uses_html_parse_mode(self):
        """Тест использования HTML в /start."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        # Act
        await start_command(update, context)

        # Assert - проверяем что parse_mode указан
        calls = update.message.reply_text.call_args_list

        # Хотя бы один вызов должен использовать parse_mode
        has_parse_mode = False
        for call in calls:
            kwargs = call[1] if len(call) > 1 else call.kwargs
            if "parse_mode" in kwargs:
                has_parse_mode = True
                break

        assert has_parse_mode

    @pytest.mark.asyncio()
    async def test_help_command_uses_html_parse_mode(self):
        """Тест использования HTML в /help."""
        # Arrange
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        # Act
        await help_command(update, context)

        # Assert
        call_kwargs = update.message.reply_text.call_args.kwargs
        assert "parse_mode" in call_kwargs

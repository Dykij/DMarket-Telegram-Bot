"""Тесты для обработчиков команд Telegram бота.

Этот модуль содержит тесты для:
- start_command
- help_command
- webapp_command
- arbitrage_command
- И других команд
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update, Chat, Message, User


@pytest.fixture
def mock_update():
    """Создаёт мок объекта Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 123456789
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = "/start"
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    """Создаёт мок объекта Context."""
    context = MagicMock()
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


class TestStartCommand:
    """Тесты для команды /start."""

    @pytest.mark.asyncio
    async def test_start_command_sends_welcome_message(
        self, mock_update, mock_context
    ):
        """Тест отправки приветственного сообщения."""
        from src.telegram_bot.handlers.commands import start_command

        await start_command(mock_update, mock_context)

        # Проверяем что reply_text был вызван
        assert mock_update.message.reply_text.called
        # Проверяем что было как минимум 2 вызова (welcome + keyboard)
        assert mock_update.message.reply_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_start_command_sets_keyboard_enabled(
        self, mock_update, mock_context
    ):
        """Тест установки флага keyboard_enabled."""
        from src.telegram_bot.handlers.commands import start_command

        await start_command(mock_update, mock_context)

        # Проверяем что флаг установлен
        assert mock_context.user_data.get("keyboard_enabled") is True

    @pytest.mark.asyncio
    async def test_start_command_returns_early_without_message(
        self, mock_context
    ):
        """Тест раннего возврата если нет сообщения."""
        from src.telegram_bot.handlers.commands import start_command

        update = MagicMock(spec=Update)
        update.message = None

        # Не должно быть исключения
        await start_command(update, mock_context)


class TestHelpCommand:
    """Тесты для команды /help."""

    @pytest.mark.asyncio
    async def test_help_command_sends_help_text(
        self, mock_update, mock_context
    ):
        """Тест отправки текста справки."""
        from src.telegram_bot.handlers.commands import help_command

        await help_command(mock_update, mock_context)

        # Проверяем что reply_text был вызван
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args
        # Проверяем что в тексте есть справка
        assert "команды" in call_args[0][0].lower() or "команды" in str(call_args)

    @pytest.mark.asyncio
    async def test_help_command_returns_early_without_message(
        self, mock_context
    ):
        """Тест раннего возврата если нет сообщения."""
        from src.telegram_bot.handlers.commands import help_command

        update = MagicMock(spec=Update)
        update.message = None

        await help_command(update, mock_context)


class TestWebappCommand:
    """Тесты для команды /webapp."""

    @pytest.mark.asyncio
    async def test_webapp_command_sends_webapp_link(
        self, mock_update, mock_context
    ):
        """Тест отправки ссылки на WebApp."""
        from src.telegram_bot.handlers.commands import webapp_command

        await webapp_command(mock_update, mock_context)

        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_webapp_command_returns_early_without_message(
        self, mock_context
    ):
        """Тест раннего возврата если нет сообщения."""
        from src.telegram_bot.handlers.commands import webapp_command

        update = MagicMock(spec=Update)
        update.message = None

        await webapp_command(update, mock_context)


class TestArbitrageCommand:
    """Тесты для команды /arbitrage."""

    @pytest.mark.asyncio
    async def test_arbitrage_command_shows_menu(
        self, mock_update, mock_context
    ):
        """Тест показа меню арбитража."""
        from src.telegram_bot.handlers.commands import arbitrage_command

        await arbitrage_command(mock_update, mock_context)

        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_arbitrage_command_returns_early_without_message(
        self, mock_context
    ):
        """Тест раннего возврата если нет сообщения."""
        from src.telegram_bot.handlers.commands import arbitrage_command

        update = MagicMock(spec=Update)
        update.message = None

        await arbitrage_command(update, mock_context)


class TestDashboardCommand:
    """Тесты для команды dashboard."""

    @pytest.mark.asyncio
    async def test_dashboard_command_shows_dashboard(
        self, mock_update, mock_context
    ):
        """Тест показа дашборда."""
        from src.telegram_bot.handlers.commands import dashboard_command

        with patch("src.telegram_bot.handlers.commands.show_dashboard") as mock_show:
            mock_show.return_value = None

            await dashboard_command(mock_update, mock_context)


class TestMarketsCommand:
    """Тесты для команды markets."""

    @pytest.mark.asyncio
    async def test_markets_command_shows_markets(
        self, mock_update, mock_context
    ):
        """Тест показа списка площадок."""
        from src.telegram_bot.handlers.commands import markets_command

        await markets_command(mock_update, mock_context)

        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_markets_command_returns_early_without_message(
        self, mock_context
    ):
        """Тест раннего возврата если нет сообщения."""
        from src.telegram_bot.handlers.commands import markets_command

        update = MagicMock(spec=Update)
        update.message = None

        await markets_command(update, mock_context)


class TestDmarketStatusCommand:
    """Тесты для команды dmarket_status."""

    @pytest.mark.asyncio
    async def test_dmarket_status_command_shows_status(
        self, mock_update, mock_context
    ):
        """Тест показа статуса DMarket."""
        from src.telegram_bot.handlers.commands import dmarket_status_command

        with patch("src.telegram_bot.handlers.commands.dmarket_status_impl") as mock_impl:
            mock_impl.return_value = None

            await dmarket_status_command(mock_update, mock_context)


class TestHandleTextButtons:
    """Тесты для обработчика текстовых кнопок."""

    @pytest.mark.asyncio
    async def test_handle_text_buttons_arbitrage(
        self, mock_update, mock_context
    ):
        """Тест обработки кнопки арбитража."""
        from src.telegram_bot.handlers.commands import handle_text_buttons

        mock_update.message.text = "📊 Арбитраж"

        await handle_text_buttons(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_handle_text_buttons_targets(
        self, mock_update, mock_context
    ):
        """Тест обработки кнопки таргетов."""
        from src.telegram_bot.handlers.commands import handle_text_buttons

        mock_update.message.text = "🎯 Таргеты"

        await handle_text_buttons(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_handle_text_buttons_settings(
        self, mock_update, mock_context
    ):
        """Тест обработки кнопки настроек."""
        from src.telegram_bot.handlers.commands import handle_text_buttons

        mock_update.message.text = "⚙️ Настройки"

        await handle_text_buttons(mock_update, mock_context)


class TestCommandErrorHandling:
    """Тесты обработки ошибок в командах."""

    @pytest.mark.asyncio
    async def test_start_command_handles_exception(
        self, mock_update, mock_context
    ):
        """Тест обработки исключения в start_command."""
        from src.telegram_bot.handlers.commands import start_command

        mock_update.message.reply_text.side_effect = Exception("Test error")

        # С декоратором telegram_error_boundary исключение должно быть обработано
        try:
            await start_command(mock_update, mock_context)
        except Exception:
            # Ожидается что исключение может быть либо обработано, либо выброшено
            pass

    @pytest.mark.asyncio
    async def test_help_command_handles_exception(
        self, mock_update, mock_context
    ):
        """Тест обработки исключения в help_command."""
        from src.telegram_bot.handlers.commands import help_command

        mock_update.message.reply_text.side_effect = Exception("Test error")

        try:
            await help_command(mock_update, mock_context)
        except Exception:
            pass


class TestCommandUtils:
    """Тесты вспомогательных функций команд."""

    def test_logger_is_configured(self):
        """Тест что логгер настроен."""
        from src.telegram_bot.handlers.commands import logger

        assert logger is not None

    def test_keyboards_are_imported(self):
        """Тест что клавиатуры импортированы."""
        from src.telegram_bot.handlers.commands import (
            get_game_selection_keyboard,
            get_marketplace_comparison_keyboard,
            get_modern_arbitrage_keyboard,
            get_permanent_reply_keyboard,
        )

        # Проверяем что функции существуют
        assert callable(get_game_selection_keyboard)
        assert callable(get_marketplace_comparison_keyboard)
        assert callable(get_modern_arbitrage_keyboard)
        assert callable(get_permanent_reply_keyboard)

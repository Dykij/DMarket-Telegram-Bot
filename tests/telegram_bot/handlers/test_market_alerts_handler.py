"""Тесты для обработчиков управления уведомлениями о рынке."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.market_alerts_handler import (
    alerts_callback,
    alerts_command,
    initialize_alerts_manager,
    register_alerts_handlers,
)


@pytest.fixture()
def mock_update():
    """Создать мок объекта Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.from_user = MagicMock()
    update.callback_query.from_user.id = 123456789
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = "alerts:toggle:price_changes"
    return update


@pytest.fixture()
def mock_context():
    """Создать мок объекта CallbackContext."""
    return MagicMock(spec=CallbackContext)


@pytest.fixture()
def mock_alerts_manager():
    """Создать мок менеджера уведомлений."""
    manager = MagicMock()
    manager.get_user_subscriptions = MagicMock(return_value=[])
    manager.subscribe = MagicMock(return_value=True)
    manager.unsubscribe = MagicMock(return_value=True)
    manager.unsubscribe_all = MagicMock(return_value=True)
    manager.update_alert_threshold = MagicMock(return_value=True)
    manager.update_check_interval = MagicMock(return_value=True)
    manager.alert_thresholds = {
        "price_change_percent": 15.0,
        "trending_popularity": 50.0,
        "volatility_threshold": 25.0,
        "arbitrage_profit_percent": 10.0,
    }
    manager.check_intervals = {
        "price_changes": 3600,
        "trending": 3600,
        "volatility": 3600,
        "arbitrage": 3600,
    }
    return manager


class TestAlertsCommand:
    """Тесты для команды /alerts."""

    @pytest.mark.asyncio()
    async def test_alerts_command_no_subscriptions(
        self, mock_update, mock_context, mock_alerts_manager
    ):
        """Тест команды /alerts без подписок."""
        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_alerts_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new=AsyncMock(return_value=[]),
            ),
        ):
            await alerts_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
            assert "🔔" in text

    @pytest.mark.asyncio()
    async def test_alerts_command_with_subscriptions(
        self, mock_update, mock_context, mock_alerts_manager
    ):
        """Тест команды /alerts с активными подписками."""
        mock_alerts_manager.get_user_subscriptions.return_value = [
            "price_changes",
            "trending",
        ]

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_alerts_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new=AsyncMock(return_value=[]),
            ),
        ):
            await alerts_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_alerts_command_exception_handling(self, mock_update, mock_context):
        """Тест обработки исключений в команде /alerts."""
        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
            side_effect=Exception("Test error"),
        ):
            await alerts_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            text = call_args.kwargs.get("text") or call_args.args[0]
            assert "❌" in text or "ошибка" in text.lower()


class TestAlertsCallback:
    """Тесты для обработчика callback запросов."""

    @pytest.mark.asyncio()
    async def test_alerts_callback_toggle_subscribe(
        self, mock_update, mock_context, mock_alerts_manager
    ):
        """Тест переключения подписки."""
        mock_update.callback_query.data = "alerts:toggle:price_changes"

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
            return_value=mock_alerts_manager,
        ):
            await alerts_callback(mock_update, mock_context)

            # Проверяем что был вызов answer (обязателен для callback query)
            mock_update.callback_query.answer.assert_called()

    @pytest.mark.asyncio()
    async def test_alerts_callback_subscribe_all(
        self, mock_update, mock_context, mock_alerts_manager
    ):
        """Тест подписки на все уведомления."""
        mock_update.callback_query.data = "alerts:subscribe_all"

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_alerts_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new=AsyncMock(return_value=[]),
            ),
        ):
            await alerts_callback(mock_update, mock_context)

            # Должны были подписать на все типы
            assert mock_alerts_manager.subscribe.called

    @pytest.mark.asyncio()
    async def test_alerts_callback_unsubscribe_all(
        self, mock_update, mock_context, mock_alerts_manager
    ):
        """Тест отписки от всех уведомлений."""
        mock_update.callback_query.data = "alerts:unsubscribe_all"

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_alerts_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new=AsyncMock(return_value=[]),
            ),
        ):
            await alerts_callback(mock_update, mock_context)

            mock_alerts_manager.unsubscribe_all.assert_called_once_with(123456789)

    @pytest.mark.asyncio()
    async def test_alerts_callback_my_alerts(self, mock_update, mock_context):
        """Тест показа списка оповещений."""
        mock_update.callback_query.data = "alerts:my_alerts"

        sample_alerts = [
            {
                "id": "alert_1",
                "type": "price_drop",
                "title": "AK-47 | Redline (FT)",
                "threshold": 10.50,
            },
        ]

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager"
            ) as mock_get_manager,
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new=AsyncMock(return_value=sample_alerts),
            ),
        ):
            mock_manager = MagicMock()
            mock_manager.get_user_subscriptions = MagicMock(return_value=[])
            mock_get_manager.return_value = mock_manager

            await alerts_callback(mock_update, mock_context)

            mock_update.callback_query.edit_message_text.assert_called()

    @pytest.mark.asyncio()
    async def test_alerts_callback_exception_handling(self, mock_update, mock_context):
        """Тест обработки исключений в callback."""
        mock_update.callback_query.data = "alerts:toggle:price_changes"

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
            side_effect=Exception("Test error"),
        ):
            await alerts_callback(mock_update, mock_context)

            # Должен быть вызван answer даже при ошибке
            mock_update.callback_query.answer.assert_called()


class TestRegisterAlertsHandlers:
    """Тесты для функции регистрации обработчиков."""

    def test_register_alerts_handlers(self):
        """Тест регистрации обработчиков уведомлений."""
        mock_application = MagicMock()
        mock_application.bot = MagicMock()

        with patch("src.telegram_bot.notifier.asyncio.create_task") as mock_create_task:
            register_alerts_handlers(mock_application)

            # Должны были зарегистрировать обработчики команд и callback
            assert mock_application.add_handler.call_count >= 2


class TestInitializeAlertsManager:
    """Тесты для функции инициализации менеджера."""

    @pytest.mark.asyncio()
    async def test_initialize_alerts_manager(self):
        """Тест инициализации менеджера уведомлений."""
        mock_application = MagicMock()
        result = await initialize_alerts_manager(mock_application)

        # Функция-заглушка возвращает None
        assert result is None

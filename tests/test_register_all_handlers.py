"""Тесты для модуля register_all_handlers.

Проверяет корректность регистрации всех обработчиков команд,
callback-запросов и текстовых сообщений.
"""

from unittest.mock import MagicMock, patch

import pytest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
)

from src.telegram_bot.register_all_handlers import register_all_handlers


@pytest.fixture()
def mock_application():
    """Создает mock объект Application для тестирования."""
    app = MagicMock(spec=Application)
    app.add_handler = MagicMock()
    app.bot_data = {}
    return app


@pytest.fixture()
def mock_dmarket_api():
    """Создает mock объект DMarket API."""
    api = MagicMock()
    api.public_key = "test_public_key"
    api.secret_key = "test_secret_key"
    api.api_url = "https://api.dmarket.com"
    return api


class TestRegisterAllHandlers:
    """Тесты для функции register_all_handlers."""

    def test_register_basic_commands(self, mock_application):
        """Тест регистрации базовых команд.

        Проверяет, что все основные команды (/start, /help, /arbitrage и т.д.)
        правильно зарегистрированы.
        """
        register_all_handlers(mock_application)

        # Получаем все зарегистрированные обработчики
        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        # Проверяем наличие CommandHandler для каждой команды
        command_handlers = [
            h for h in registered_handlers if isinstance(h, CommandHandler)
        ]

        # Ожидаемые команды
        expected_commands = [
            "start",
            "help",
            "arbitrage",
            "dmarket",
            "status",
            "markets",
            "webapp",
        ]

        # Получаем все зарегистрированные команды
        registered_commands = []
        for handler in command_handlers:
            if hasattr(handler, "commands"):
                registered_commands.extend(handler.commands)

        # Проверяем, что все ожидаемые команды зарегистрированы
        for cmd in expected_commands:
            assert cmd in registered_commands, f"Команда /{cmd} не зарегистрирована"

    def test_register_callback_query_handler(self, mock_application):
        """Тест регистрации callback-обработчика.

        Проверяет, что CallbackQueryHandler зарегистрирован.
        """
        register_all_handlers(mock_application)

        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        # Проверяем наличие CallbackQueryHandler
        callback_handlers = [
            h for h in registered_handlers if isinstance(h, CallbackQueryHandler)
        ]

        assert len(callback_handlers) > 0, "CallbackQueryHandler не зарегистрирован"

    def test_register_message_handler(self, mock_application):
        """Тест регистрации обработчика текстовых сообщений.

        Проверяет, что MessageHandler для текстовых кнопок зарегистрирован.
        """
        register_all_handlers(mock_application)

        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        # Проверяем наличие MessageHandler
        message_handlers = [
            h for h in registered_handlers if isinstance(h, MessageHandler)
        ]

        assert len(message_handlers) > 0, "MessageHandler не зарегистрирован"

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_logging_on_success(self, mock_logger, mock_application):
        """Тест логирования при успешной регистрации.

        Проверяет, что логируются сообщения о регистрации обработчиков.
        """
        register_all_handlers(mock_application)

        # Проверяем, что были вызовы logger.info
        info_calls = [call for call in mock_logger.info.call_args_list]

        assert len(info_calls) > 0, "Не было вызовов logger.info"

        # Проверяем конкретные сообщения
        logged_messages = [call[0][0] for call in info_calls]

        assert any("Начало регистрации обработчиков" in msg for msg in logged_messages)
        assert any("Базовые команды зарегистрированы" in msg for msg in logged_messages)
        assert any(
            "Callback-обработчики зарегистрированы" in msg for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_handlers_registration_order(self, mock_logger, mock_application):
        """Тест порядка регистрации обработчиков.

        Проверяет, что обработчики регистрируются в правильном порядке:
        сначала команды, потом callback, потом text handlers.
        """
        register_all_handlers(mock_application)

        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        # Найдем индексы разных типов обработчиков
        command_indices = [
            i
            for i, h in enumerate(registered_handlers)
            if isinstance(h, CommandHandler)
        ]
        callback_indices = [
            i
            for i, h in enumerate(registered_handlers)
            if isinstance(h, CallbackQueryHandler)
        ]
        message_indices = [
            i
            for i, h in enumerate(registered_handlers)
            if isinstance(h, MessageHandler)
        ]

        # Команды должны быть зарегистрированы первыми
        if command_indices and callback_indices:
            assert min(command_indices) < min(callback_indices), (
                "CommandHandler должны регистрироваться до CallbackQueryHandler"
            )

        # Callback должны быть до message handlers
        if callback_indices and message_indices:
            assert min(callback_indices) < min(message_indices), (
                "CallbackQueryHandler должны регистрироваться до MessageHandler"
            )

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_optional_handlers_import_error(self, mock_logger, mock_application):
        """Тест обработки ImportError для опциональных обработчиков.

        Проверяет, что при ошибке импорта опциональных обработчиков
        логируется предупреждение, но основные обработчики регистрируются.
        """
        with patch(
            "src.telegram_bot.register_all_handlers.register_enhanced_arbitrage_handlers",
            side_effect=ImportError("Test import error"),
        ):
            register_all_handlers(mock_application)

        # Проверяем, что были вызовы logger.warning
        warning_calls = [call for call in mock_logger.warning.call_args_list]

        # Должно быть предупреждение об ошибке импорта
        logged_warnings = [call[0][0] for call in warning_calls]

        # Проверяем, что логировались предупреждения (может быть несколько)
        assert len(logged_warnings) > 0, "Не было вызовов logger.warning"

    def test_dmarket_handlers_registration_with_api(
        self, mock_application, mock_dmarket_api
    ):
        """Тест регистрации DMarket обработчиков при наличии API."""
        mock_application.bot_data = {"dmarket_api": mock_dmarket_api}

        with patch(
            "src.telegram_bot.register_all_handlers.register_dmarket_handlers"
        ) as mock_register_dmarket:
            register_all_handlers(mock_application)

            # Проверяем, что register_dmarket_handlers был вызван
            mock_register_dmarket.assert_called_once()

            # Проверяем аргументы вызова
            call_kwargs = mock_register_dmarket.call_args[1]
            assert call_kwargs["public_key"] == "test_public_key"
            assert call_kwargs["secret_key"] == "test_secret_key"
            assert call_kwargs["api_url"] == "https://api.dmarket.com"

    def test_dmarket_handlers_registration_without_api(self, mock_application):
        """Тест регистрации DMarket обработчиков без API.

        Проверяет, что DMarket обработчики не регистрируются,
        если API ключи не настроены.
        """
        mock_application.bot_data = {}

        with patch(
            "src.telegram_bot.register_all_handlers.register_dmarket_handlers"
        ) as mock_register_dmarket:
            register_all_handlers(mock_application)

            # register_dmarket_handlers не должен быть вызван
            mock_register_dmarket.assert_not_called()

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_all_handlers_count(self, mock_logger, mock_application):
        """Тест общего количества зарегистрированных обработчиков.

        Проверяет, что регистрируется минимальное ожидаемое количество
        обработчиков (базовые команды + callback + text).
        """
        register_all_handlers(mock_application)

        # Минимальное ожидаемое количество обработчиков:
        # 7 команд + 1 callback + 1 text handler = 9
        min_expected_handlers = 9

        actual_handlers = mock_application.add_handler.call_count

        assert actual_handlers >= min_expected_handlers, (
            f"Ожидалось минимум {min_expected_handlers} обработчиков, "
            f"зарегистрировано: {actual_handlers}"
        )

    def test_no_duplicate_command_handlers(self, mock_application):
        """Тест отсутствия дублирующихся обработчиков команд.

        Проверяет, что каждая команда зарегистрирована только один раз.
        """
        register_all_handlers(mock_application)

        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        command_handlers = [
            h for h in registered_handlers if isinstance(h, CommandHandler)
        ]

        # Собираем все команды
        all_commands = []
        for handler in command_handlers:
            if hasattr(handler, "commands"):
                all_commands.extend(handler.commands)

        # Проверяем на дубликаты
        unique_commands = set(all_commands)

        assert len(all_commands) == len(unique_commands), (
            f"Найдены дублирующиеся команды. "
            f"Всего: {len(all_commands)}, уникальных: {len(unique_commands)}"
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_final_success_log(self, mock_logger, mock_application):
        """Тест финального сообщения об успешной регистрации.

        Проверяет, что в конце логируется сообщение об успешной
        регистрации всех обработчиков.
        """
        register_all_handlers(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        # Последнее сообщение должно быть об успешной регистрации
        assert any(
            "Все обработчики успешно зарегистрированы" in msg for msg in logged_messages
        )


class TestOptionalHandlersRegistration:
    """Тесты для регистрации опциональных обработчиков."""

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_enhanced_arbitrage_handlers",
        create=True,
    )
    def test_enhanced_arbitrage_registration(
        self, mock_register_enhanced, mock_logger, mock_application
    ):
        """Тест успешной регистрации enhanced arbitrage обработчиков."""
        register_all_handlers(mock_application)

        # Проверяем, что функция была вызвана
        mock_register_enhanced.assert_called_once_with(mock_application)

        # Проверяем логирование
        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Enhanced arbitrage обработчики зарегистрированы" in msg
            for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_scanner_handlers", create=True
    )
    def test_scanner_handlers_registration(
        self, mock_register_scanner, mock_logger, mock_application
    ):
        """Тест успешной регистрации scanner обработчиков."""
        register_all_handlers(mock_application)

        mock_register_scanner.assert_called_once_with(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Scanner обработчики зарегистрированы" in msg for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_alerts_handlers", create=True
    )
    def test_alerts_handlers_registration(
        self, mock_register_alerts, mock_logger, mock_application
    ):
        """Тест успешной регистрации market alerts обработчиков."""
        register_all_handlers(mock_application)

        mock_register_alerts.assert_called_once_with(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Market alerts обработчики зарегистрированы" in msg
            for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_market_analysis_handlers",
        create=True,
    )
    def test_market_analysis_registration(
        self, mock_register_analysis, mock_logger, mock_application
    ):
        """Тест успешной регистрации market analysis обработчиков."""
        register_all_handlers(mock_application)

        mock_register_analysis.assert_called_once_with(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Market analysis обработчики зарегистрированы" in msg
            for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_intramarket_handlers",
        create=True,
    )
    def test_intramarket_registration(
        self, mock_register_intramarket, mock_logger, mock_application
    ):
        """Тест успешной регистрации intramarket arbitrage обработчиков."""
        register_all_handlers(mock_application)

        mock_register_intramarket.assert_called_once_with(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Intramarket arbitrage обработчики зарегистрированы" in msg
            for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_localization_handlers",
        create=True,
    )
    def test_localization_registration(
        self, mock_register_localization, mock_logger, mock_application
    ):
        """Тест успешной регистрации localization обработчиков."""
        register_all_handlers(mock_application)

        mock_register_localization.assert_called_once_with(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Localization обработчики зарегистрированы" in msg
            for msg in logged_messages
        )

    @patch("src.telegram_bot.register_all_handlers.logger")
    @patch(
        "src.telegram_bot.register_all_handlers.register_target_handlers", create=True
    )
    def test_target_handlers_registration(
        self, mock_register_targets, mock_logger, mock_application
    ):
        """Тест успешной регистрации target обработчиков."""
        register_all_handlers(mock_application)

        mock_register_targets.assert_called_once_with(mock_application)

        info_calls = [call for call in mock_logger.info.call_args_list]
        logged_messages = [call[0][0] for call in info_calls]

        assert any(
            "Target обработчики зарегистрированы" in msg for msg in logged_messages
        )


class TestErrorHandling:
    """Тесты обработки ошибок при регистрации."""

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_continue_on_import_error(self, mock_logger, mock_application):
        """Тест продолжения работы при ImportError опциональных обработчиков.

        Проверяет, что ошибка импорта одного обработчика не прерывает
        регистрацию остальных.
        """
        with patch(
            "src.telegram_bot.register_all_handlers.register_scanner_handlers",
            side_effect=ImportError("Scanner not found"),
        ):
            # Не должно быть исключений
            register_all_handlers(mock_application)

        # Проверяем, что базовые команды всё равно зарегистрированы
        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        command_handlers = [
            h for h in registered_handlers if isinstance(h, CommandHandler)
        ]

        assert len(command_handlers) > 0, "Базовые команды не зарегистрированы"

    @patch("src.telegram_bot.register_all_handlers.logger")
    def test_dmarket_registration_exception(
        self, mock_logger, mock_application, mock_dmarket_api
    ):
        """Тест обработки исключения при регистрации DMarket обработчиков."""
        mock_application.bot_data = {"dmarket_api": mock_dmarket_api}

        with patch(
            "src.telegram_bot.register_all_handlers.register_dmarket_handlers",
            side_effect=Exception("DMarket error"),
        ):
            # Не должно быть исключений
            register_all_handlers(mock_application)

        # Проверяем логирование предупреждения
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        logged_warnings = [call[0][0] for call in warning_calls]

        assert any(
            "Не удалось зарегистрировать DMarket обработчики" in msg
            for msg in logged_warnings
        )


@pytest.mark.integration()
class TestIntegrationHandlersRegistration:
    """Интеграционные тесты для регистрации обработчиков."""

    def test_full_registration_flow(self, mock_application):
        """Интеграционный тест полного процесса регистрации.

        Проверяет, что все обработчики регистрируются в правильном порядке
        и без ошибок.
        """
        # Регистрация должна пройти без исключений
        register_all_handlers(mock_application)

        # Проверяем, что было зарегистрировано достаточно обработчиков
        assert mock_application.add_handler.call_count >= 9

        registered_handlers = [
            call[0][0] for call in mock_application.add_handler.call_args_list
        ]

        # Проверяем наличие всех типов обработчиков
        has_command = any(isinstance(h, CommandHandler) for h in registered_handlers)
        has_callback = any(
            isinstance(h, CallbackQueryHandler) for h in registered_handlers
        )
        has_message = any(isinstance(h, MessageHandler) for h in registered_handlers)

        assert has_command, "Нет CommandHandler"
        assert has_callback, "Нет CallbackQueryHandler"
        assert has_message, "Нет MessageHandler"

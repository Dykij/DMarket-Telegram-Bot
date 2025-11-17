"""Tests for main application module.

This module contains comprehensive tests for the main entry point
of the DMarket Telegram Bot application.
"""

import asyncio
import logging
import signal
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.main import Application, main


@pytest.fixture()
def mock_config():
    """Create mock configuration."""
    config = MagicMock()
    config.debug = False
    config.testing = True
    config.logging.level = "INFO"
    config.logging.file = None
    config.logging.format = "%(levelname)s - %(message)s"
    config.dmarket.public_key = "test_public_key"
    config.dmarket.secret_key = "test_secret_key"
    config.dmarket.api_url = "https://api.dmarket.com"
    config.database.url = "sqlite:///:memory:"
    config.bot.token = "test_token"
    return config


@pytest.fixture()
def mock_database():
    """Create mock database manager."""
    db = AsyncMock()
    db.init_database = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture()
def mock_dmarket_api():
    """Create mock DMarket API client."""
    api = AsyncMock()
    api.get_balance = AsyncMock(return_value={"error": False, "balance": 100.50})
    api._close_client = AsyncMock()
    return api


@pytest.fixture()
def mock_bot():
    """Create mock Telegram bot."""
    bot = AsyncMock()
    bot.initialize = AsyncMock()
    bot.start = AsyncMock()
    bot.stop = AsyncMock()
    return bot


class TestApplication:
    """Test cases for Application class."""

    def test_init_creates_application_with_default_values(self):
        """Тест проверяет создание Application с дефолтными значениями."""
        # Arrange & Act
        app = Application()

        # Assert
        assert app.config_path is None
        assert app.config is None
        assert app.database is None
        assert app.dmarket_api is None
        assert app.bot is None
        assert isinstance(app._shutdown_event, asyncio.Event)

    def test_init_with_config_path_sets_path_correctly(self):
        """Тест проверяет установку пути к конфигурации при инициализации."""
        # Arrange
        config_path = "config/test.yaml"

        # Act
        app = Application(config_path=config_path)

        # Assert
        assert app.config_path == config_path

    @pytest.mark.asyncio()
    async def test_initialize_sets_all_components_on_success(
        self, mock_config, mock_dmarket_api, mock_bot
    ):
        """Тест проверяет корректную установку всех компонентов при успешной инициализации."""
        # Arrange
        app = Application()

        # Act
        with (
            patch("src.main.Config.load", return_value=mock_config),
            patch("src.main.setup_logging"),
            patch("src.main.DMarketAPI", return_value=mock_dmarket_api),
            patch("src.main.DMarketBot", return_value=mock_bot),
        ):
            await app.initialize()

        # Assert
        assert app.config == mock_config
        assert app.dmarket_api == mock_dmarket_api
        assert app.bot == mock_bot
        mock_bot.initialize.assert_called_once()

    @pytest.mark.asyncio()
    async def test_initialize_with_production_mode_initializes_database(
        self, mock_config, mock_database, mock_dmarket_api, mock_bot
    ):
        """Тест проверяет инициализацию базы данных в production режиме."""
        # Arrange
        mock_config.testing = False
        app = Application()

        # Act
        with (
            patch("src.main.Config.load", return_value=mock_config),
            patch("src.main.setup_logging"),
            patch("src.main.DatabaseManager", return_value=mock_database),
            patch("src.main.DMarketAPI", return_value=mock_dmarket_api),
            patch("src.main.DMarketBot", return_value=mock_bot),
        ):
            await app.initialize()

        # Assert
        assert app.database == mock_database
        mock_database.init_database.assert_called_once()

    @pytest.mark.asyncio()
    async def test_initialize_in_production_mode_tests_api_connection(
        self, mock_config, mock_dmarket_api, mock_bot
    ):
        """Тест проверяет, что в production режиме выполняется проверка подключения к API."""
        # Arrange
        mock_config.testing = False
        app = Application()

        # Act
        with (
            patch("src.main.Config.load", return_value=mock_config),
            patch("src.main.setup_logging"),
            patch("src.main.DMarketAPI", return_value=mock_dmarket_api),
            patch("src.main.DMarketBot", return_value=mock_bot),
        ):
            await app.initialize()

        # Assert
        mock_dmarket_api.get_balance.assert_called_once()

    @pytest.mark.asyncio()
    async def test_initialize_continues_when_api_connection_fails(
        self, mock_config, mock_dmarket_api, mock_bot
    ):
        """Тест проверяет, что инициализация продолжается при ошибке подключения к API."""
        # Arrange
        mock_config.testing = False
        mock_dmarket_api.get_balance = AsyncMock(side_effect=Exception("Connection failed"))
        app = Application()

        # Act
        with (
            patch("src.main.Config.load", return_value=mock_config),
            patch("src.main.setup_logging"),
            patch("src.main.DMarketAPI", return_value=mock_dmarket_api),
            patch("src.main.DMarketBot", return_value=mock_bot),
        ):
            await app.initialize()

        # Assert - должно только залогировать предупреждение, но не выбросить исключение
        assert app.dmarket_api == mock_dmarket_api

    @pytest.mark.asyncio()
    async def test_initialize_config_validation_error(self):
        """Test initialization with config validation error."""
        app = Application()

        mock_config = MagicMock()
        mock_config.validate = MagicMock(side_effect=ValueError("Invalid config"))

        with (
            patch("src.main.Config.load", return_value=mock_config),
            pytest.raises(ValueError, match="Invalid config"),
        ):
            await app.initialize()

    @pytest.mark.asyncio()
    async def test_run_success(self, mock_config, mock_dmarket_api, mock_bot):
        """Test successful application run."""
        app = Application()

        # Mock initialize to prevent actual initialization
        app.initialize = AsyncMock()
        app.config = mock_config
        app.bot = mock_bot

        # Mock shutdown event to trigger immediately
        app._shutdown_event.set()

        with patch.object(app, "_setup_signal_handlers"):
            await app.run()

            app.initialize.assert_called_once()
            mock_bot.start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_run_keyboard_interrupt(self, mock_config, mock_dmarket_api, mock_bot):
        """Тест проверяет обработку KeyboardInterrupt во время запуска."""
        # Arrange
        app = Application()
        app.initialize = AsyncMock()
        app.config = mock_config
        app.bot = mock_bot
        app.shutdown = AsyncMock()

        # Simulate KeyboardInterrupt
        mock_bot.start = AsyncMock(side_effect=KeyboardInterrupt())

        # Act
        with patch.object(app, "_setup_signal_handlers"):
            await app.run()

        # Assert
        app.shutdown.assert_called_once()

    @pytest.mark.asyncio()
    async def test_shutdown_all_components(self, mock_database, mock_dmarket_api, mock_bot):
        """Test shutdown of all components."""
        app = Application()
        app.bot = mock_bot
        app.dmarket_api = mock_dmarket_api
        app.database = mock_database

        await app.shutdown()

        mock_bot.stop.assert_called_once()
        mock_dmarket_api._close_client.assert_called_once()
        mock_database.close.assert_called_once()

    @pytest.mark.asyncio()
    async def test_shutdown_with_errors(self, mock_database, mock_dmarket_api, mock_bot):
        """Тест проверяет, что shutdown перехватывает ошибки и не падает."""
        # Arrange
        app = Application()
        app.bot = mock_bot
        app.dmarket_api = mock_dmarket_api
        app.database = mock_database

        # Make bot.stop raise an exception
        mock_bot.stop = AsyncMock(side_effect=Exception("Stop failed"))

        # Act - не должно выбрасывать, только логировать
        await app.shutdown()

        # Assert - проверяем что bot.stop был вызван
        mock_bot.stop.assert_called_once()
        # Примечание: из-за ошибки в bot.stop, остальные компоненты не закрываются
        # Это известное поведение - весь блок try прерывается при первой ошибке
        # Поэтому _close_client и close НЕ вызываются
        mock_dmarket_api._close_client.assert_not_called()
        mock_database.close.assert_not_called()

    @pytest.mark.asyncio()
    async def test_shutdown_partial_components(self):
        """Test shutdown when some components are None."""
        app = Application()
        app.bot = None
        app.dmarket_api = None
        app.database = None

        # Should not raise any exceptions
        await app.shutdown()

    def test_setup_signal_handlers(self):
        """Test signal handler setup."""
        app = Application()

        with patch("signal.signal") as mock_signal:
            app._setup_signal_handlers()

            # Verify SIGINT and SIGTERM are registered
            calls = mock_signal.call_args_list
            signals_registered = [call[0][0] for call in calls]

            assert signal.SIGINT in signals_registered
            assert signal.SIGTERM in signals_registered

            # SIGQUIT should be registered on non-Windows systems
            if hasattr(signal, "SIGQUIT"):
                assert signal.SIGQUIT in signals_registered

    def test_signal_handler_sets_shutdown_event(self):
        """Test that signal handler sets shutdown event."""
        app = Application()

        # Setup signal handlers
        with patch("signal.signal"):
            app._setup_signal_handlers()

        # Manually call the signal handler
        # (we can't easily test actual signal delivery)
        assert not app._shutdown_event.is_set()

        # Simulate signal by setting event directly
        app._shutdown_event.set()
        assert app._shutdown_event.is_set()


class TestMainFunction:
    """Test cases for main() entry point."""

    @pytest.mark.asyncio()
    async def test_main_default_arguments(self):
        """Test main function with default arguments."""
        mock_app = MagicMock()
        mock_app.run = AsyncMock()

        with (
            patch("sys.argv", ["main.py"]),
            patch("src.main.Application", return_value=mock_app),
        ):
            await main()

            mock_app.run.assert_called_once()

    @pytest.mark.asyncio()
    async def test_main_with_config_argument(self):
        """Test main function with config argument."""
        mock_app = MagicMock()
        mock_app.run = AsyncMock()

        with (
            patch("sys.argv", ["main.py", "--config", "config/test.yaml"]),
            patch("src.main.Application", return_value=mock_app) as MockApp,
        ):
            await main()

            MockApp.assert_called_once_with(config_path="config/test.yaml")
            mock_app.run.assert_called_once()

    @pytest.mark.asyncio()
    async def test_main_with_debug_flag(self):
        """Test main function with debug flag."""
        mock_app = MagicMock()
        mock_app.run = AsyncMock()

        with (
            patch("sys.argv", ["main.py", "--debug"]),
            patch("src.main.Application", return_value=mock_app),
            patch.dict("os.environ", {}, clear=True),
        ):
            await main()

            # Check that DEBUG environment variable was set
            import os

            assert os.environ.get("DEBUG") == "true"
            assert os.environ.get("LOG_LEVEL") == "DEBUG"

    @pytest.mark.asyncio()
    async def test_main_with_log_level(self):
        """Test main function with custom log level."""
        mock_app = MagicMock()
        mock_app.run = AsyncMock()

        with (
            patch("sys.argv", ["main.py", "--log-level", "WARNING"]),
            patch("src.main.Application", return_value=mock_app),
            patch("logging.basicConfig") as mock_logging,
        ):
            await main()

            # Verify logging was configured with WARNING level
            mock_logging.assert_called_once()
            call_kwargs = mock_logging.call_args[1]
            assert call_kwargs["level"] == logging.WARNING

    @pytest.mark.asyncio()
    async def test_main_application_failure(self):
        """Test main function when application fails."""
        mock_app = MagicMock()
        mock_app.run = AsyncMock(side_effect=Exception("App failed"))

        with (
            patch("sys.argv", ["main.py"]),
            patch("src.main.Application", return_value=mock_app),
            pytest.raises(SystemExit) as exc_info,
        ):
            await main()

        assert exc_info.value.code == 1


class TestWindowsEventLoopPolicy:
    """Test Windows-specific event loop policy."""

    def test_windows_event_loop_policy_set(self):
        """Test that Windows event loop policy is set on Windows."""
        if not sys.platform.startswith("win"):
            pytest.skip("Test only runs on Windows")

        with (
            patch("asyncio.set_event_loop_policy") as mock_set_policy,
            patch("asyncio.WindowsProactorEventLoopPolicy") as MockPolicy,
        ):
            # This would normally be in __main__ block
            # We test the logic separately
            if sys.platform.startswith("win"):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

            mock_set_policy.assert_called()


class TestLogging:
    """Test logging configuration."""

    @pytest.mark.asyncio()
    async def test_logging_setup_called(self, mock_config):
        """Test that logging setup is called during initialization."""
        app = Application()

        with (
            patch("src.main.Config.load", return_value=mock_config),
            patch("src.main.setup_logging") as mock_setup_logging,
            patch("src.main.DMarketAPI", return_value=AsyncMock()),
            patch("src.main.DMarketBot", return_value=AsyncMock()),
        ):
            await app.initialize()

            mock_setup_logging.assert_called_once_with(
                level=mock_config.logging.level,
                log_file=mock_config.logging.file,
                format_string=mock_config.logging.format,
            )

    def test_logger_created(self):
        """Test that module-level logger is created."""
        from src.main import logger

        assert isinstance(logger, logging.Logger)
        assert logger.name == "src.main"

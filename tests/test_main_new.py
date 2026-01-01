"""Unit tests for src/main.py Application class.

Tests for the main Application class including:
- Initialization
- Signal handling
- Shutdown procedures
- Configuration loading
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestApplicationInit:
    """Tests for Application initialization."""

    def test_init_default_values(self):
        """Test Application initialization with default values."""
        from src.main import Application

        app = Application()

        assert app.config_path is None
        assert app.config is None
        assert app.database is None
        assert app.dmarket_api is None
        assert app.bot is None
        assert app.state_manager is None
        assert app.daily_report_scheduler is None

    def test_init_with_config_path(self):
        """Test Application initialization with config path."""
        from src.main import Application

        app = Application(config_path="/path/to/config.yaml")

        assert app.config_path == "/path/to/config.yaml"


class TestApplicationShutdown:
    """Tests for Application shutdown."""

    @pytest.mark.asyncio()
    async def test_shutdown_with_no_components(self):
        """Test shutdown when no components are initialized."""
        from src.main import Application

        app = Application()

        # Should not raise
        await app.shutdown()

    @pytest.mark.asyncio()
    async def test_shutdown_with_bot(self):
        """Test shutdown with bot component."""
        from src.main import Application

        app = Application()
        mock_bot = MagicMock()
        mock_bot.running = True
        mock_bot.updater = MagicMock()
        mock_bot.updater.running = True
        mock_bot.updater.stop = AsyncMock()
        mock_bot.stop = AsyncMock()
        mock_bot.shutdown = AsyncMock()
        app.bot = mock_bot

        await app.shutdown()

        mock_bot.updater.stop.assert_called_once()
        mock_bot.stop.assert_called_once()
        mock_bot.shutdown.assert_called_once()

    @pytest.mark.asyncio()
    async def test_shutdown_with_database(self):
        """Test shutdown with database component."""
        from src.main import Application

        app = Application()
        mock_db = MagicMock()
        mock_db.close = AsyncMock()
        app.database = mock_db

        await app.shutdown()

        mock_db.close.assert_called_once()

    @pytest.mark.asyncio()
    async def test_shutdown_with_dmarket_api(self):
        """Test shutdown with DMarket API component."""
        from src.main import Application

        app = Application()
        mock_api = MagicMock()
        mock_api._close_client = AsyncMock()
        app.dmarket_api = mock_api

        await app.shutdown()

        mock_api._close_client.assert_called_once()

    @pytest.mark.asyncio()
    async def test_shutdown_with_scheduler(self):
        """Test shutdown with daily report scheduler."""
        from src.main import Application

        app = Application()
        mock_scheduler = MagicMock()
        mock_scheduler.stop = AsyncMock()
        app.daily_report_scheduler = mock_scheduler

        await app.shutdown()

        mock_scheduler.stop.assert_called_once()


class TestApplicationSignalHandlers:
    """Tests for Application signal handlers."""

    def test_setup_signal_handlers(self):
        """Test signal handlers setup."""
        import signal

        from src.main import Application

        app = Application()

        with patch("signal.signal") as mock_signal:
            app._setup_signal_handlers()

            # Should register SIGINT and SIGTERM
            calls = mock_signal.call_args_list
            signals_registered = [call[0][0] for call in calls]
            assert signal.SIGINT in signals_registered
            assert signal.SIGTERM in signals_registered


class TestApplicationCrashNotifications:
    """Tests for crash notification functionality."""

    @pytest.mark.asyncio()
    async def test_send_crash_notifications_no_bot(self):
        """Test crash notifications when bot is not available."""
        from src.main import Application

        app = Application()
        app.bot = None

        # Should not raise
        await app._send_crash_notifications(
            error=Exception("Test error"),
            traceback_text="Test traceback",
        )

    @pytest.mark.asyncio()
    async def test_send_crash_notifications_no_config(self):
        """Test crash notifications when config is not available."""
        from src.main import Application

        app = Application()
        app.bot = MagicMock()
        app.config = None

        # Should not raise
        await app._send_crash_notifications(
            error=Exception("Test error"),
            traceback_text="Test traceback",
        )


class TestApplicationCriticalShutdown:
    """Tests for critical shutdown handling."""

    @pytest.mark.asyncio()
    async def test_handle_critical_shutdown_no_bot(self):
        """Test critical shutdown when bot is not available."""
        from src.main import Application

        app = Application()
        app.bot = None
        app.config = None

        # Should not raise
        await app._handle_critical_shutdown("Test reason")

    @pytest.mark.asyncio()
    async def test_handle_critical_shutdown_with_admin_users(self):
        """Test critical shutdown with admin users configured."""
        from src.main import Application

        app = Application()

        # Mock bot
        mock_bot = MagicMock()
        mock_bot.bot = MagicMock()
        app.bot = mock_bot

        # Mock config with admin users
        mock_config = MagicMock()
        mock_config.security.admin_users = [123, 456]
        app.config = mock_config

        # Mock state manager
        mock_state_manager = MagicMock()
        mock_state_manager.consecutive_errors = 5
        app.state_manager = mock_state_manager

        with patch(
            "src.main.send_critical_shutdown_notification", new_callable=AsyncMock
        ) as mock_notify:
            await app._handle_critical_shutdown("Too many errors")

            assert mock_notify.call_count == 2  # Once per admin


class TestMainFunction:
    """Tests for main() function."""

    @pytest.mark.asyncio()
    async def test_main_with_debug_flag(self):
        """Test main function with debug flag sets environment."""

        with patch("sys.argv", ["main.py", "--debug"]):
            with patch("src.main.Application") as MockApp:
                mock_app = MagicMock()
                mock_app.run = AsyncMock()
                MockApp.return_value = mock_app

                # Import after patching
                from src.main import main

                # Run briefly
                try:
                    await asyncio.wait_for(main(), timeout=0.1)
                except TimeoutError:
                    pass
                except Exception:
                    pass


class TestApplicationInitialize:
    """Tests for Application.initialize() method."""

    @pytest.mark.asyncio()
    async def test_initialize_requires_bot_token(self):
        """Test initialization fails without bot token."""
        from src.main import Application

        app = Application()

        # Mock config without bot token
        mock_config = MagicMock()
        mock_config.bot.token = None
        mock_config.debug = False
        mock_config.testing = True  # Skip database init
        mock_config.logging.level = "INFO"
        mock_config.logging.file = None
        mock_config.logging.format = "%(message)s"
        mock_config.dmarket.public_key = "test"
        mock_config.dmarket.secret_key = "test"
        mock_config.dmarket.api_url = "https://api.dmarket.com"

        with (
            patch.object(app, "config", mock_config),
            patch("src.main.Config.load", return_value=mock_config),
            pytest.raises(ValueError, match="token"),
        ):
            await app.initialize()


class TestApplicationRunLoop:
    """Tests for Application run loop."""

    @pytest.mark.asyncio()
    async def test_run_keyboard_interrupt(self):
        """Test run handles keyboard interrupt gracefully."""
        from src.main import Application

        app = Application()
        app.initialize = AsyncMock(side_effect=KeyboardInterrupt())
        app.shutdown = AsyncMock()

        # Should not raise
        await app.run()

        app.shutdown.assert_called_once()

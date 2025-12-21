"""Unit tests for telegram_bot/initialization.py module.

This module contains tests for:
- setup_logging function
- initialize_bot function
- setup_bot_commands function
- setup_signal_handlers function
- register_handlers function
- initialize_services function
- start_bot function
- get_bot_token function
- setup_and_run_bot function

Target: 60+ tests to achieve 85%+ coverage
"""

import asyncio
import logging
import os
import signal
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        from src.telegram_bot.initialization import setup_logging

        # Call with defaults
        setup_logging()

        # Verify root logger is configured
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) >= 1

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level."""
        from src.telegram_bot.initialization import setup_logging

        setup_logging(log_level=logging.DEBUG)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_with_file(self):
        """Test setup_logging with log file."""
        from src.telegram_bot.initialization import setup_logging
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        try:
            setup_logging(log_file=log_file)

            root_logger = logging.getLogger()
            # Should have file handler
            file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1
        finally:
            os.unlink(log_file)

    def test_setup_logging_with_error_file(self):
        """Test setup_logging with separate error log file."""
        from src.telegram_bot.initialization import setup_logging
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            error_log_file = f.name

        try:
            setup_logging(error_log_file=error_log_file)

            root_logger = logging.getLogger()
            # Should have error file handler
            error_handlers = [h for h in root_logger.handlers 
                           if isinstance(h, logging.FileHandler) and h.level == logging.ERROR]
            assert len(error_handlers) >= 1
        finally:
            os.unlink(error_log_file)

    def test_setup_logging_custom_formatter(self):
        """Test setup_logging with custom formatter."""
        from src.telegram_bot.initialization import setup_logging

        custom_formatter = logging.Formatter("%(levelname)s - %(message)s")
        setup_logging(formatter=custom_formatter)

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 1

    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        from src.telegram_bot.initialization import setup_logging

        root_logger = logging.getLogger()
        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)
        initial_count = len(root_logger.handlers)

        setup_logging()

        # Handler should be replaced, not duplicated
        assert len(root_logger.handlers) <= initial_count

    def test_setup_logging_sets_library_levels(self):
        """Test that httpx and telegram loggers are set to WARNING."""
        from src.telegram_bot.initialization import setup_logging

        setup_logging()

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("telegram").level == logging.WARNING


class TestInitializeBot:
    """Tests for initialize_bot function."""

    @pytest.mark.asyncio
    async def test_initialize_bot_requires_token(self):
        """Test initialize_bot raises ValueError without token."""
        from src.telegram_bot.initialization import initialize_bot

        with pytest.raises(ValueError, match="Не указан токен"):
            await initialize_bot("")

    @pytest.mark.asyncio
    async def test_initialize_bot_with_valid_token(self):
        """Test initialize_bot with valid token."""
        from src.telegram_bot.initialization import initialize_bot

        with patch("src.telegram_bot.initialization.ApplicationBuilder") as mock_builder, \
             patch("src.telegram_bot.initialization.profile_manager") as mock_profile, \
             patch("src.telegram_bot.initialization.setup_error_handler"), \
             patch("src.telegram_bot.initialization.register_global_exception_handlers"), \
             patch("src.telegram_bot.initialization.setup_signal_handlers"):

            mock_profile.get_admin_ids.return_value = set()
            mock_app = MagicMock()
            mock_builder.return_value.token.return_value.concurrent_updates.return_value.connection_pool_size.return_value.build.return_value = mock_app

            result = await initialize_bot("test_token", setup_persistence=False)

            assert result == mock_app
            mock_builder.return_value.token.assert_called_with("test_token")

    @pytest.mark.asyncio
    async def test_initialize_bot_with_persistence(self):
        """Test initialize_bot with persistence enabled."""
        from src.telegram_bot.initialization import initialize_bot

        with patch("src.telegram_bot.initialization.ApplicationBuilder") as mock_builder, \
             patch("src.telegram_bot.initialization.profile_manager") as mock_profile, \
             patch("src.telegram_bot.initialization.setup_error_handler"), \
             patch("src.telegram_bot.initialization.register_global_exception_handlers"), \
             patch("src.telegram_bot.initialization.setup_signal_handlers"), \
             patch("telegram.ext.PicklePersistence"):

            mock_profile.get_admin_ids.return_value = {123}
            mock_chain = MagicMock()
            mock_builder.return_value.token.return_value = mock_chain
            mock_chain.concurrent_updates.return_value = mock_chain
            mock_chain.connection_pool_size.return_value = mock_chain
            mock_chain.persistence.return_value = mock_chain
            mock_chain.build.return_value = MagicMock()

            await initialize_bot("test_token", setup_persistence=True)

            # Verify persistence was set
            mock_chain.persistence.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_bot_uses_profile_admin_ids(self):
        """Test initialize_bot uses admin IDs from profile manager."""
        from src.telegram_bot.initialization import initialize_bot

        with patch("src.telegram_bot.initialization.ApplicationBuilder") as mock_builder, \
             patch("src.telegram_bot.initialization.profile_manager") as mock_profile, \
             patch("src.telegram_bot.initialization.setup_error_handler") as mock_setup, \
             patch("src.telegram_bot.initialization.register_global_exception_handlers"), \
             patch("src.telegram_bot.initialization.setup_signal_handlers"):

            mock_profile.get_admin_ids.return_value = {111, 222}
            mock_chain = MagicMock()
            mock_builder.return_value.token.return_value = mock_chain
            mock_chain.concurrent_updates.return_value = mock_chain
            mock_chain.connection_pool_size.return_value = mock_chain
            mock_chain.build.return_value = MagicMock()

            await initialize_bot("test_token", setup_persistence=False)

            # Verify admin IDs were used
            call_args = mock_setup.call_args
            assert 111 in call_args[0][1] or 222 in call_args[0][1]


class TestSetupBotCommands:
    """Tests for setup_bot_commands function."""

    @pytest.mark.asyncio
    async def test_setup_bot_commands_success(self):
        """Test setup_bot_commands sets commands successfully."""
        from src.telegram_bot.initialization import setup_bot_commands

        mock_bot = AsyncMock()
        await setup_bot_commands(mock_bot)

        # Should be called 3 times: en, ru, default
        assert mock_bot.set_my_commands.call_count == 3

    @pytest.mark.asyncio
    async def test_setup_bot_commands_sets_english_commands(self):
        """Test setup_bot_commands sets English commands."""
        from src.telegram_bot.initialization import setup_bot_commands

        mock_bot = AsyncMock()
        await setup_bot_commands(mock_bot)

        # Check for English call
        calls = mock_bot.set_my_commands.call_args_list
        en_call = [c for c in calls if c.kwargs.get("language_code") == "en"]
        assert len(en_call) == 1

    @pytest.mark.asyncio
    async def test_setup_bot_commands_sets_russian_commands(self):
        """Test setup_bot_commands sets Russian commands."""
        from src.telegram_bot.initialization import setup_bot_commands

        mock_bot = AsyncMock()
        await setup_bot_commands(mock_bot)

        # Check for Russian call
        calls = mock_bot.set_my_commands.call_args_list
        ru_call = [c for c in calls if c.kwargs.get("language_code") == "ru"]
        assert len(ru_call) == 1

    @pytest.mark.asyncio
    async def test_setup_bot_commands_handles_error(self):
        """Test setup_bot_commands handles exceptions gracefully."""
        from src.telegram_bot.initialization import setup_bot_commands

        mock_bot = AsyncMock()
        mock_bot.set_my_commands.side_effect = Exception("API Error")

        # Should not raise
        await setup_bot_commands(mock_bot)

    @pytest.mark.asyncio
    async def test_setup_bot_commands_contains_expected_commands(self):
        """Test setup_bot_commands includes expected commands."""
        from src.telegram_bot.initialization import setup_bot_commands

        mock_bot = AsyncMock()
        await setup_bot_commands(mock_bot)

        # Get the commands from any call
        call_args = mock_bot.set_my_commands.call_args_list[0]
        commands = call_args[0][0]
        command_names = [c.command for c in commands]

        assert "start" in command_names
        assert "balance" in command_names
        assert "arbitrage" in command_names
        assert "help" in command_names


class TestSetupSignalHandlers:
    """Tests for setup_signal_handlers function."""

    def test_setup_signal_handlers_non_windows(self):
        """Test setup_signal_handlers on non-Windows platform."""
        from src.telegram_bot.initialization import setup_signal_handlers

        mock_app = MagicMock()

        with patch("platform.system", return_value="Linux"), \
             patch("asyncio.get_event_loop") as mock_loop:

            mock_loop.return_value.add_signal_handler = MagicMock()

            setup_signal_handlers(mock_app)

            # Should attempt to add signal handlers
            assert mock_loop.return_value.add_signal_handler.called

    def test_setup_signal_handlers_windows(self):
        """Test setup_signal_handlers on Windows platform."""
        from src.telegram_bot.initialization import setup_signal_handlers

        mock_app = MagicMock()

        with patch("platform.system", return_value="Windows"), \
             patch("asyncio.get_event_loop") as mock_loop:

            setup_signal_handlers(mock_app)

            # Should NOT add signal handlers on Windows
            assert not mock_loop.return_value.add_signal_handler.called

    def test_setup_signal_handlers_not_implemented(self):
        """Test setup_signal_handlers handles NotImplementedError."""
        from src.telegram_bot.initialization import setup_signal_handlers

        mock_app = MagicMock()

        with patch("platform.system", return_value="Linux"), \
             patch("asyncio.get_event_loop") as mock_loop:

            mock_loop.return_value.add_signal_handler.side_effect = NotImplementedError()

            # Should not raise
            setup_signal_handlers(mock_app)


class TestRegisterHandlers:
    """Tests for register_handlers function."""

    def test_register_handlers_empty(self):
        """Test register_handlers with no handlers."""
        from src.telegram_bot.initialization import register_handlers

        mock_app = MagicMock()
        register_handlers(mock_app)

        # Should not add any handlers
        assert mock_app.add_handler.call_count == 0

    def test_register_handlers_command_handlers(self):
        """Test register_handlers with command handlers."""
        from src.telegram_bot.initialization import register_handlers

        mock_app = MagicMock()
        command_handlers = {
            "start": MagicMock(),
            "help": MagicMock(),
        }

        register_handlers(mock_app, command_handlers=command_handlers)

        assert mock_app.add_handler.call_count == 2

    def test_register_handlers_callback_handlers(self):
        """Test register_handlers with callback handlers."""
        from src.telegram_bot.initialization import register_handlers

        mock_app = MagicMock()
        callback_handlers = [
            ("pattern1", MagicMock()),
            ("pattern2", MagicMock()),
        ]

        register_handlers(mock_app, callback_handlers=callback_handlers)

        assert mock_app.add_handler.call_count == 2

    def test_register_handlers_message_handlers(self):
        """Test register_handlers with message handlers."""
        from src.telegram_bot.initialization import register_handlers
        from telegram.ext import filters

        mock_app = MagicMock()
        message_handlers = [
            (filters.TEXT, MagicMock()),
        ]

        register_handlers(mock_app, message_handlers=message_handlers)

        assert mock_app.add_handler.call_count == 1

    def test_register_handlers_conversation_handlers(self):
        """Test register_handlers with conversation handlers."""
        from src.telegram_bot.initialization import register_handlers

        mock_app = MagicMock()
        mock_conv = MagicMock()
        conversation_handlers = [mock_conv]

        register_handlers(mock_app, conversation_handlers=conversation_handlers)

        assert mock_app.add_handler.call_count == 1
        mock_app.add_handler.assert_called_with(mock_conv)

    def test_register_handlers_all_types(self):
        """Test register_handlers with all handler types."""
        from src.telegram_bot.initialization import register_handlers
        from telegram.ext import filters

        mock_app = MagicMock()
        command_handlers = {"start": MagicMock()}
        callback_handlers = [("pattern", MagicMock())]
        message_handlers = [(filters.TEXT, MagicMock())]
        conversation_handlers = [MagicMock()]

        register_handlers(
            mock_app,
            command_handlers=command_handlers,
            callback_handlers=callback_handlers,
            message_handlers=message_handlers,
            conversation_handlers=conversation_handlers,
        )

        assert mock_app.add_handler.call_count == 4


class TestInitializeServices:
    """Tests for initialize_services function."""

    @pytest.mark.asyncio
    async def test_initialize_services_success(self):
        """Test initialize_services successfully creates API client."""
        from src.telegram_bot.initialization import initialize_services

        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_api = MagicMock()

        with patch("src.telegram_bot.initialization.create_api_client_from_env", return_value=mock_api):
            await initialize_services(mock_app)

            assert mock_app.bot_data["dmarket_api"] == mock_api

    @pytest.mark.asyncio
    async def test_initialize_services_api_failure(self):
        """Test initialize_services handles API client creation failure."""
        from src.telegram_bot.initialization import initialize_services

        mock_app = MagicMock()
        mock_app.bot_data = {}

        with patch("src.telegram_bot.initialization.create_api_client_from_env", 
                   side_effect=Exception("No API keys")):
            # Should not raise
            await initialize_services(mock_app)

            # API client should not be in bot_data
            assert "dmarket_api" not in mock_app.bot_data


class TestGetBotToken:
    """Tests for get_bot_token function."""

    def test_get_bot_token_success(self):
        """Test get_bot_token returns token from environment."""
        from src.telegram_bot.initialization import get_bot_token

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token_123"}):
            token = get_bot_token()
            assert token == "test_token_123"

    def test_get_bot_token_missing(self):
        """Test get_bot_token raises ValueError when token missing."""
        from src.telegram_bot.initialization import get_bot_token

        with patch.dict(os.environ, {}, clear=True):
            # Remove the token if it exists
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)

            with pytest.raises(ValueError, match="Не указан токен"):
                get_bot_token()


class TestInitializeBotApplication:
    """Tests for initialize_bot_application alias."""

    def test_initialize_bot_application_is_alias(self):
        """Test initialize_bot_application is alias for initialize_bot."""
        from src.telegram_bot.initialization import initialize_bot, initialize_bot_application

        assert initialize_bot_application is initialize_bot


class TestSetupAndRunBot:
    """Tests for setup_and_run_bot function."""

    @pytest.mark.asyncio
    async def test_setup_and_run_bot_creates_log_dirs(self):
        """Test setup_and_run_bot creates log directories."""
        from src.telegram_bot.initialization import setup_and_run_bot

        with patch("src.telegram_bot.initialization.setup_logging"), \
             patch("src.telegram_bot.initialization.get_bot_token", return_value="token"), \
             patch("src.telegram_bot.initialization.initialize_bot", new_callable=AsyncMock) as mock_init, \
             patch("src.telegram_bot.initialization.register_handlers"), \
             patch("src.telegram_bot.initialization.start_bot", new_callable=AsyncMock) as mock_start, \
             patch("os.makedirs") as mock_makedirs:

            mock_start.side_effect = asyncio.CancelledError()

            try:
                await setup_and_run_bot(error_log_file="logs/errors.log")
            except (asyncio.CancelledError, SystemExit):
                pass

            mock_makedirs.assert_called_with("logs", exist_ok=True)

    @pytest.mark.asyncio
    async def test_setup_and_run_bot_with_token(self):
        """Test setup_and_run_bot uses provided token."""
        from src.telegram_bot.initialization import setup_and_run_bot

        with patch("src.telegram_bot.initialization.setup_logging"), \
             patch("src.telegram_bot.initialization.initialize_bot", new_callable=AsyncMock) as mock_init, \
             patch("src.telegram_bot.initialization.register_handlers"), \
             patch("src.telegram_bot.initialization.start_bot", new_callable=AsyncMock) as mock_start:

            mock_start.side_effect = asyncio.CancelledError()

            try:
                await setup_and_run_bot(token="my_token")
            except asyncio.CancelledError:
                pass

            mock_init.assert_called_once()
            # First arg to initialize_bot should be the token
            assert mock_init.call_args[0][0] == "my_token"

    @pytest.mark.asyncio
    async def test_setup_and_run_bot_uses_env_token(self):
        """Test setup_and_run_bot uses environment token when not provided."""
        from src.telegram_bot.initialization import setup_and_run_bot

        with patch("src.telegram_bot.initialization.setup_logging"), \
             patch("src.telegram_bot.initialization.get_bot_token", return_value="env_token"), \
             patch("src.telegram_bot.initialization.initialize_bot", new_callable=AsyncMock) as mock_init, \
             patch("src.telegram_bot.initialization.register_handlers"), \
             patch("src.telegram_bot.initialization.start_bot", new_callable=AsyncMock) as mock_start:

            mock_start.side_effect = asyncio.CancelledError()

            try:
                await setup_and_run_bot()
            except asyncio.CancelledError:
                pass

            mock_init.assert_called_once()
            assert mock_init.call_args[0][0] == "env_token"

    @pytest.mark.asyncio
    async def test_setup_and_run_bot_registers_handlers(self):
        """Test setup_and_run_bot registers provided handlers."""
        from src.telegram_bot.initialization import setup_and_run_bot

        cmd_handlers = {"test": MagicMock()}

        with patch("src.telegram_bot.initialization.setup_logging"), \
             patch("src.telegram_bot.initialization.get_bot_token", return_value="token"), \
             patch("src.telegram_bot.initialization.initialize_bot", new_callable=AsyncMock), \
             patch("src.telegram_bot.initialization.register_handlers") as mock_register, \
             patch("src.telegram_bot.initialization.start_bot", new_callable=AsyncMock) as mock_start:

            mock_start.side_effect = asyncio.CancelledError()

            try:
                await setup_and_run_bot(command_handlers=cmd_handlers)
            except asyncio.CancelledError:
                pass

            mock_register.assert_called_once()
            assert mock_register.call_args.kwargs.get("command_handlers") == cmd_handlers

    @pytest.mark.asyncio
    async def test_setup_and_run_bot_handles_critical_error(self):
        """Test setup_and_run_bot handles critical errors."""
        from src.telegram_bot.initialization import setup_and_run_bot

        with patch("src.telegram_bot.initialization.setup_logging"), \
             patch("src.telegram_bot.initialization.get_bot_token", return_value="token"), \
             patch("src.telegram_bot.initialization.initialize_bot", new_callable=AsyncMock) as mock_init, \
             patch("sys.exit") as mock_exit:

            mock_init.side_effect = Exception("Critical error")

            await setup_and_run_bot()

            mock_exit.assert_called_once_with(1)


class TestStartBot:
    """Tests for start_bot function."""

    @pytest.mark.asyncio
    async def test_start_bot_initializes_services(self):
        """Test start_bot initializes services."""
        from src.telegram_bot.initialization import start_bot

        mock_app = AsyncMock()
        mock_app.updater = AsyncMock()
        mock_app.builder = MagicMock()
        mock_app.builder.get_updates_allowed_updates.return_value = None

        with patch("src.telegram_bot.initialization.initialize_services", new_callable=AsyncMock) as mock_init, \
             patch("src.telegram_bot.initialization.profile_manager") as mock_profile, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            mock_sleep.side_effect = KeyboardInterrupt()

            try:
                await start_bot(mock_app)
            except KeyboardInterrupt:
                pass

            mock_init.assert_called_once_with(mock_app)

    @pytest.mark.asyncio
    async def test_start_bot_starts_polling(self):
        """Test start_bot starts polling."""
        from src.telegram_bot.initialization import start_bot

        mock_app = AsyncMock()
        mock_app.updater = AsyncMock()
        mock_app.builder = MagicMock()
        mock_app.builder.get_updates_allowed_updates.return_value = None

        with patch("src.telegram_bot.initialization.initialize_services", new_callable=AsyncMock), \
             patch("src.telegram_bot.initialization.profile_manager") as mock_profile, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            mock_sleep.side_effect = KeyboardInterrupt()

            try:
                await start_bot(mock_app)
            except KeyboardInterrupt:
                pass

            mock_app.updater.start_polling.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_bot_saves_profiles_on_shutdown(self):
        """Test start_bot saves profiles on shutdown."""
        from src.telegram_bot.initialization import start_bot

        mock_app = AsyncMock()
        mock_app.updater = AsyncMock()
        mock_app.builder = MagicMock()
        mock_app.builder.get_updates_allowed_updates.return_value = None

        with patch("src.telegram_bot.initialization.initialize_services", new_callable=AsyncMock), \
             patch("src.telegram_bot.initialization.profile_manager") as mock_profile, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            mock_sleep.side_effect = KeyboardInterrupt()

            try:
                await start_bot(mock_app)
            except KeyboardInterrupt:
                pass

            mock_profile.save_profiles.assert_called_with(force=True)


class TestIntegration:
    """Integration tests for initialization module."""

    def test_module_exports(self):
        """Test that all expected functions are exported."""
        from src.telegram_bot import initialization

        assert hasattr(initialization, "setup_logging")
        assert hasattr(initialization, "initialize_bot")
        assert hasattr(initialization, "setup_bot_commands")
        assert hasattr(initialization, "setup_signal_handlers")
        assert hasattr(initialization, "register_handlers")
        assert hasattr(initialization, "initialize_services")
        assert hasattr(initialization, "start_bot")
        assert hasattr(initialization, "get_bot_token")
        assert hasattr(initialization, "setup_and_run_bot")
        assert hasattr(initialization, "initialize_bot_application")

    def test_setup_logging_is_callable(self):
        """Test setup_logging is callable."""
        from src.telegram_bot.initialization import setup_logging

        assert callable(setup_logging)

    def test_initialize_bot_is_coroutine(self):
        """Test initialize_bot is a coroutine function."""
        import asyncio
        from src.telegram_bot.initialization import initialize_bot

        assert asyncio.iscoroutinefunction(initialize_bot)

    def test_setup_bot_commands_is_coroutine(self):
        """Test setup_bot_commands is a coroutine function."""
        import asyncio
        from src.telegram_bot.initialization import setup_bot_commands

        assert asyncio.iscoroutinefunction(setup_bot_commands)


class TestEdgeCases:
    """Edge case tests for initialization module."""

    def test_setup_logging_multiple_calls(self):
        """Test setup_logging can be called multiple times."""
        from src.telegram_bot.initialization import setup_logging

        # Should not raise
        setup_logging()
        setup_logging()
        setup_logging()

    @pytest.mark.asyncio
    async def test_initialize_bot_with_none_token(self):
        """Test initialize_bot with None token."""
        from src.telegram_bot.initialization import initialize_bot

        with pytest.raises((ValueError, TypeError)):
            await initialize_bot(None)

    @pytest.mark.asyncio
    async def test_initialize_bot_with_empty_string(self):
        """Test initialize_bot with empty string token."""
        from src.telegram_bot.initialization import initialize_bot

        with pytest.raises(ValueError, match="Не указан токен"):
            await initialize_bot("")

    def test_register_handlers_with_none_app(self):
        """Test register_handlers handles None application."""
        from src.telegram_bot.initialization import register_handlers

        # Should raise AttributeError when trying to add handlers to None
        with pytest.raises(AttributeError):
            register_handlers(None, command_handlers={"test": lambda: None})

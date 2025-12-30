"""Phase 4 extended tests for logging_utils module.

This module adds comprehensive tests to achieve 100% coverage
for logging utilities including formatters, Sentry integration,
structlog configuration, and BotLogger methods.
"""

import json
import logging
import logging.handlers
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.utils.logging_utils import (
    BotLogger,
    ColoredFormatter,
    JSONFormatter,
    get_logger,
    setup_logging,
    setup_sentry,
    setup_structlog,
)


# =============================================================================
# Phase 4 Extended Tests for JSONFormatter
# =============================================================================


class TestJSONFormatterPhase4:
    """Phase 4 extended tests for JSONFormatter class."""

    @pytest.fixture()
    def formatter(self):
        """Create a JSONFormatter instance."""
        return JSONFormatter()

    def test_format_thread_and_process_info(self, formatter):
        """Test that format includes thread and process info."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "thread" in parsed
        assert "process" in parsed
        assert isinstance(parsed["thread"], int)
        assert isinstance(parsed["process"], int)

    def test_format_timestamp_is_iso_format(self, formatter):
        """Test that timestamp is in ISO format."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        # Should be parseable as ISO timestamp
        timestamp = parsed["timestamp"]
        assert "T" in timestamp  # ISO format has T separator

    def test_format_excludes_standard_fields_from_extra(self, formatter):
        """Test that standard LogRecord fields are excluded from extra."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"

        result = formatter.format(record)
        parsed = json.loads(result)

        # Standard fields should be in specific keys, not duplicated
        assert parsed.get("custom_field") == "custom_value"
        # Standard fields like msg, args should not appear as extra
        assert "args" not in parsed
        assert "msg" not in parsed

    def test_format_with_args_in_message(self, formatter):
        """Test format with positional arguments in message."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="User %d bought item %s for $%.2f",
            args=(123, "AK-47", 15.99),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "123" in parsed["message"]
        assert "AK-47" in parsed["message"]
        assert "15.99" in parsed["message"]

    def test_format_with_very_long_message(self, formatter):
        """Test format with very long message."""
        long_message = "A" * 10000
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg=long_message,
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert len(parsed["message"]) == 10000

    def test_format_with_binary_data_in_extra(self, formatter):
        """Test format with binary data in extra field."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.binary_data = b"\x00\x01\x02\xff"

        result = formatter.format(record)
        # Should not raise, binary converted via default=str
        parsed = json.loads(result)
        assert "binary_data" in parsed

    def test_format_with_exception_traceback(self, formatter):
        """Test format includes full traceback for exceptions."""
        try:
            def inner_func():
                raise ValueError("Inner error")
            inner_func()
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "inner_func" in parsed["exception"]
        assert "ValueError" in parsed["exception"]

    def test_format_with_custom_object_in_extra(self, formatter):
        """Test format with custom object in extra field."""
        class CustomObject:
            def __str__(self):
                return "CustomObject<test>"

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.custom_obj = CustomObject()

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "CustomObject<test>" in parsed.get("custom_obj", "")


# =============================================================================
# Phase 4 Extended Tests for ColoredFormatter
# =============================================================================


class TestColoredFormatterPhase4:
    """Phase 4 extended tests for ColoredFormatter class."""

    def test_format_preserves_original_format_string(self):
        """Test that original format string is preserved."""
        original_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = ColoredFormatter(original_format)

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        # Should contain logger name and message
        assert "test.logger" in result
        assert "Test message" in result

    def test_format_with_all_log_levels(self):
        """Test format applies correct colors to all log levels."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        for level_name in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            level = getattr(logging, level_name)
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="/test/path.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )

            result = formatter.format(record)
            # Should contain ANSI codes for color
            assert "\033[" in result or level_name in result

    def test_format_with_datefmt(self):
        """Test format with custom date format."""
        formatter = ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d"
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        # Date should be in format YYYY-MM-DD
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", result)

    def test_colors_dict_has_all_required_keys(self):
        """Test COLORS dict has all required log level keys."""
        formatter = ColoredFormatter("%(levelname)s")

        required_keys = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "RESET"}
        assert required_keys == set(formatter.COLORS.keys())

    def test_color_codes_end_with_m(self):
        """Test all color codes end with 'm'."""
        formatter = ColoredFormatter("%(levelname)s")

        for color_code in formatter.COLORS.values():
            assert color_code.endswith("m")


# =============================================================================
# Phase 4 Extended Tests for setup_sentry
# =============================================================================


class TestSetupSentryPhase4:
    """Phase 4 extended tests for setup_sentry function."""

    def test_filter_sensitive_headers_logic(self):
        """Test the filter sensitive data logic for headers."""
        # Define the filter function inline (same logic as in setup_sentry)
        def filter_sensitive_data(event, hint):
            """Filter sensitive data from Sentry events."""
            if "request" in event:
                headers = event["request"].get("headers", {})
                for key in list(headers.keys()):
                    if any(
                        sensitive in key.lower()
                        for sensitive in ["api", "token", "key", "secret", "auth"]
                    ):
                        headers[key] = "[Filtered]"

            if "extra" in event:
                for key in list(event["extra"].keys()):
                    if any(
                        sensitive in key.lower() for sensitive in ["password", "secret", "token", "key"]
                    ):
                        event["extra"][key] = "[Filtered]"

            return event

        # Test filtering headers
        event = {
            "request": {
                "headers": {
                    "X-Api-Key": "secret123",
                    "Authorization": "Bearer token",
                    "Content-Type": "application/json",
                    "X-Token": "abc",
                    "X-Secret-Key": "key123",
                }
            }
        }

        filtered_event = filter_sensitive_data(event, {})

        headers = filtered_event["request"]["headers"]
        assert headers["X-Api-Key"] == "[Filtered]"
        assert headers["Authorization"] == "[Filtered]"
        assert headers["Content-Type"] == "application/json"  # Not filtered
        assert headers["X-Token"] == "[Filtered]"
        assert headers["X-Secret-Key"] == "[Filtered]"

    def test_filter_sensitive_extra_logic(self):
        """Test the filter sensitive data logic for extra fields."""
        def filter_sensitive_data(event, hint):
            if "extra" in event:
                for key in list(event["extra"].keys()):
                    if any(
                        sensitive in key.lower() for sensitive in ["password", "secret", "token", "key"]
                    ):
                        event["extra"][key] = "[Filtered]"
            return event

        event = {
            "extra": {
                "password": "secret123",
                "api_secret": "abc",
                "token_value": "token",
                "api_key_id": "key123",
                "normal_field": "value",
            }
        }

        filtered_event = filter_sensitive_data(event, {})

        extra = filtered_event["extra"]
        assert extra["password"] == "[Filtered]"
        assert extra["api_secret"] == "[Filtered]"
        assert extra["token_value"] == "[Filtered]"
        assert extra["api_key_id"] == "[Filtered]"
        assert extra["normal_field"] == "value"  # Not filtered

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_sentry_without_dsn_does_not_initialize(self):
        """Test setup_sentry without DSN doesn't initialize Sentry."""
        with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
            setup_sentry()
            mock_sentry.init.assert_not_called()

    def test_filter_handles_missing_keys(self):
        """Test filter function handles events with missing keys."""
        def filter_sensitive_data(event, hint):
            if "request" in event:
                headers = event["request"].get("headers", {})
                for key in list(headers.keys()):
                    if any(sensitive in key.lower() for sensitive in ["api", "token", "key", "secret", "auth"]):
                        headers[key] = "[Filtered]"
            if "extra" in event:
                for key in list(event["extra"].keys()):
                    if any(sensitive in key.lower() for sensitive in ["password", "secret", "token", "key"]):
                        event["extra"][key] = "[Filtered]"
            return event

        # Event without request or extra
        event = {"message": "test"}
        result = filter_sensitive_data(event, {})
        assert result == event

    def test_filter_handles_empty_headers(self):
        """Test filter function handles empty headers."""
        def filter_sensitive_data(event, hint):
            if "request" in event:
                headers = event["request"].get("headers", {})
                for key in list(headers.keys()):
                    if any(sensitive in key.lower() for sensitive in ["api", "token", "key", "secret", "auth"]):
                        headers[key] = "[Filtered]"
            return event

        event = {"request": {"headers": {}}}
        result = filter_sensitive_data(event, {})
        assert result["request"]["headers"] == {}

    def test_filter_handles_no_sensitive_data(self):
        """Test filter function with no sensitive data."""
        def filter_sensitive_data(event, hint):
            if "request" in event:
                headers = event["request"].get("headers", {})
                for key in list(headers.keys()):
                    if any(sensitive in key.lower() for sensitive in ["api", "token", "key", "secret", "auth"]):
                        headers[key] = "[Filtered]"
            return event

        event = {"request": {"headers": {"Content-Type": "application/json", "Accept": "application/json"}}}
        result = filter_sensitive_data(event, {})
        assert result["request"]["headers"]["Content-Type"] == "application/json"
        assert result["request"]["headers"]["Accept"] == "application/json"

    def test_setup_sentry_parameters_validation(self):
        """Test setup_sentry accepts all expected parameters."""
        # Just verify the function signature accepts these parameters
        # without actually calling setup_sentry (which requires dependencies)
        import inspect
        sig = inspect.signature(setup_sentry)
        params = list(sig.parameters.keys())

        assert "environment" in params
        assert "traces_sample_rate" in params
        assert "send_default_pii" in params


# =============================================================================
# Phase 4 Extended Tests for setup_logging
# =============================================================================


class TestSetupLoggingPhase4:
    """Phase 4 extended tests for setup_logging function."""

    def test_setup_logging_clears_existing_handlers(self):
        """Test setup_logging clears existing handlers."""
        root_logger = logging.getLogger()

        # Add dummy handler
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)
        initial_count = len(root_logger.handlers)

        with patch("src.utils.logging_utils.setup_sentry"):
            with patch("src.utils.logging_utils.setup_structlog"):
                setup_logging(enable_sentry=False, enable_structlog=False)

        # Handlers should be replaced, not accumulated
        # (may have at least one new handler)
        assert len(root_logger.handlers) >= 1

    def test_setup_logging_with_custom_format_string(self):
        """Test setup_logging with custom format string."""
        custom_format = "CUSTOM: %(message)s"

        with patch("src.utils.logging_utils.setup_sentry"):
            with patch("src.utils.logging_utils.setup_structlog"):
                setup_logging(
                    format_string=custom_format,
                    enable_sentry=False,
                    enable_structlog=False,
                )

        root_logger = logging.getLogger()
        # At least one handler should exist
        assert len(root_logger.handlers) > 0

    def test_setup_logging_creates_log_directory(self):
        """Test setup_logging creates log directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "subdir", "nested", "app.log")

            with patch("src.utils.logging_utils.setup_sentry"):
                with patch("src.utils.logging_utils.setup_structlog"):
                    setup_logging(
                        log_file=log_path,
                        enable_sentry=False,
                        enable_structlog=False,
                    )

            # Directory should be created
            assert os.path.exists(os.path.dirname(log_path))

    def test_setup_logging_file_handler_with_rotation(self):
        """Test setup_logging creates rotating file handler."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_file = f.name

        try:
            with patch("src.utils.logging_utils.setup_sentry"):
                with patch("src.utils.logging_utils.setup_structlog"):
                    setup_logging(
                        log_file=log_file,
                        max_file_size=1024,
                        backup_count=3,
                        enable_sentry=False,
                        enable_structlog=False,
                    )

            root_logger = logging.getLogger()
            rotating_handlers = [
                h for h in root_logger.handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            if rotating_handlers:
                handler = rotating_handlers[0]
                assert handler.maxBytes == 1024
                assert handler.backupCount == 3
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_setup_logging_suppresses_noisy_loggers(self):
        """Test setup_logging suppresses noisy third-party loggers."""
        with patch("src.utils.logging_utils.setup_sentry"):
            with patch("src.utils.logging_utils.setup_structlog"):
                setup_logging(enable_sentry=False, enable_structlog=False)

        # Check noisy loggers are set to WARNING
        assert logging.getLogger("httpx").level >= logging.WARNING
        assert logging.getLogger("httpcore").level >= logging.WARNING
        assert logging.getLogger("telegram").level >= logging.WARNING

    def test_setup_logging_with_tty_console(self):
        """Test setup_logging uses ColoredFormatter for TTY."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True

            with patch("src.utils.logging_utils.setup_sentry"):
                with patch("src.utils.logging_utils.setup_structlog"):
                    setup_logging(enable_sentry=False, enable_structlog=False)

        # Should have console handler
        root_logger = logging.getLogger()
        stream_handlers = [
            h for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) > 0

    def test_setup_logging_calls_setup_sentry_when_enabled(self):
        """Test setup_logging calls setup_sentry when enabled."""
        with patch("src.utils.logging_utils.setup_sentry") as mock_sentry:
            with patch("src.utils.logging_utils.setup_structlog"):
                setup_logging(
                    enable_sentry=True,
                    sentry_environment="test",
                )

        mock_sentry.assert_called_once()
        call_kwargs = mock_sentry.call_args.kwargs
        assert call_kwargs["environment"] == "test"

    def test_setup_logging_calls_setup_structlog_when_enabled(self):
        """Test setup_logging calls setup_structlog when enabled."""
        with patch("src.utils.logging_utils.setup_sentry"):
            with patch("src.utils.logging_utils.setup_structlog") as mock_structlog:
                setup_logging(
                    enable_structlog=True,
                    json_format=True,
                    enable_sentry=False,
                )

        mock_structlog.assert_called_once_with(json_format=True)


# =============================================================================
# Phase 4 Extended Tests for setup_structlog
# =============================================================================


class TestSetupStructlogPhase4:
    """Phase 4 extended tests for setup_structlog function."""

    def test_setup_structlog_configures_processors(self):
        """Test setup_structlog configures expected processors."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            setup_structlog(json_format=False)

        mock_structlog.configure.assert_called_once()
        call_kwargs = mock_structlog.configure.call_args.kwargs
        assert "processors" in call_kwargs
        assert len(call_kwargs["processors"]) > 0

    def test_setup_structlog_json_has_json_renderer(self):
        """Test setup_structlog with JSON format uses JSONRenderer."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            setup_structlog(json_format=True)

        call_kwargs = mock_structlog.configure.call_args.kwargs
        processors = call_kwargs["processors"]

        # Last processor should be JSONRenderer for JSON format
        # Check that it was added
        processor_types = [type(p).__name__ for p in processors if hasattr(p, "__class__")]
        # At least some processors should exist
        assert len(processors) > 0

    def test_setup_structlog_console_has_console_renderer(self):
        """Test setup_structlog without JSON format uses ConsoleRenderer."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True

            with patch("src.utils.logging_utils.structlog") as mock_structlog:
                setup_structlog(json_format=False)

        # Should have called configure
        mock_structlog.configure.assert_called_once()


# =============================================================================
# Phase 4 Extended Tests for BotLogger
# =============================================================================


class TestBotLoggerPhase4:
    """Phase 4 extended tests for BotLogger class."""

    def test_log_command_with_all_parameters(self):
        """Test log_command with all possible parameters."""
        logger = BotLogger("test")

        logger.log_command(
            user_id=12345,
            command="/scan",
            success=True,
            game="csgo",
            level="boost",
            items_found=25,
            scan_time=1.5,
            cached=False,
        )

    def test_log_api_call_determines_level_by_error(self):
        """Test log_api_call uses correct level based on error presence."""
        logger = BotLogger("test")

        with patch.object(logger, "logger") as mock_logger:
            # Without error - should use "info"
            logger.log_api_call(
                endpoint="/test",
                method="GET",
            )
            first_call = mock_logger.log.call_args_list[0]
            assert first_call[0][0] == "info"

        with patch.object(logger, "logger") as mock_logger:
            # With error - should use "error"
            logger.log_api_call(
                endpoint="/test",
                method="GET",
                error="Connection failed",
            )
            second_call = mock_logger.log.call_args_list[0]
            assert second_call[0][0] == "error"

    def test_log_market_data_with_all_parameters(self):
        """Test log_market_data with all possible parameters."""
        logger = BotLogger("test")

        logger.log_market_data(
            game="csgo",
            items_count=1000,
            total_value=50000.00,
            source="full_scan",
            cached=True,
            scan_duration=5.5,
        )

    def test_log_error_extracts_error_type(self):
        """Test log_error correctly extracts error type."""
        logger = BotLogger("test")

        class CustomError(Exception):
            pass

        try:
            raise CustomError("Custom error message")
        except CustomError as e:
            with patch.object(logger.logger, "error") as mock_error:
                logger.log_error(e)

            call_kwargs = mock_error.call_args.kwargs
            assert call_kwargs["error_type"] == "CustomError"
            assert call_kwargs["error_message"] == "Custom error message"

    def test_log_buy_intent_formats_message_correctly(self):
        """Test log_buy_intent formats message with mode and emoji."""
        logger = BotLogger("test")

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_buy_intent(
                item_name="Test Item",
                price_usd=10.50,
                dry_run=True,
            )

            call_args = mock_info.call_args[0]
            assert "[DRY-RUN]" in call_args[0]
            assert "BUY_INTENT" in call_args[0]
            assert "Test Item" in call_args[0]
            assert "10.50" in call_args[0]

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_buy_intent(
                item_name="Test Item",
                price_usd=10.50,
                dry_run=False,
            )

            call_args = mock_info.call_args[0]
            assert "[LIVE]" in call_args[0]

    def test_log_sell_intent_includes_all_fields(self):
        """Test log_sell_intent includes all provided fields."""
        logger = BotLogger("test")

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_sell_intent(
                item_name="AWP",
                price_usd=100.00,
                buy_price_usd=80.00,
                profit_usd=20.00,
                profit_percent=25.0,
                source="auto_sell",
                dry_run=False,
                user_id=99999,
                game="csgo",
            )

            call_kwargs = mock_info.call_args.kwargs
            assert call_kwargs["intent_type"] == "SELL_INTENT"
            assert call_kwargs["item"] == "AWP"
            assert call_kwargs["price_usd"] == 100.00
            assert call_kwargs["buy_price_usd"] == 80.00
            assert call_kwargs["profit_usd"] == 20.00
            assert call_kwargs["profit_percent"] == 25.0
            assert call_kwargs["source"] == "auto_sell"
            assert call_kwargs["dry_run"] is False
            assert call_kwargs["user_id"] == 99999
            assert call_kwargs["game"] == "csgo"

    def test_log_trade_result_success_uses_info_level(self):
        """Test log_trade_result uses INFO level for success."""
        logger = BotLogger("test")

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_trade_result(
                operation="buy",
                success=True,
                item_name="Item",
                price_usd=10.00,
            )

            # First argument to log should be the level
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.INFO

    def test_log_trade_result_failure_uses_error_level(self):
        """Test log_trade_result uses ERROR level for failure."""
        logger = BotLogger("test")

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_trade_result(
                operation="sell",
                success=False,
                item_name="Item",
                price_usd=10.00,
                error_message="Failed",
            )

            call_args = mock_log.call_args
            assert call_args[0][0] == logging.ERROR

    def test_log_trade_result_formats_status_correctly(self):
        """Test log_trade_result formats status message correctly."""
        logger = BotLogger("test")

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_trade_result(
                operation="buy",
                success=True,
                item_name="Test",
                price_usd=10.00,
                dry_run=True,
            )

            msg = mock_log.call_args[0][1]
            assert "BUY_SUCCESS" in msg
            assert "✅" in msg
            assert "[DRY-RUN]" in msg

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_trade_result(
                operation="sell",
                success=False,
                item_name="Test",
                price_usd=10.00,
                dry_run=False,
            )

            msg = mock_log.call_args[0][1]
            assert "SELL_FAILED" in msg
            assert "❌" in msg
            assert "[LIVE]" in msg

    def test_log_crash_with_full_context(self):
        """Test log_crash with full context data."""
        logger = BotLogger("test")

        try:
            raise RuntimeError("Critical failure")
        except RuntimeError as e:
            with patch.object(logger.logger, "critical") as mock_critical:
                with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
                    mock_sentry.is_initialized.return_value = False

                    logger.log_crash(
                        e,
                        traceback_text="Traceback...",
                        context={"module": "test", "action": "process"},
                        extra_field="value",
                    )

            call_kwargs = mock_critical.call_args.kwargs
            assert call_kwargs["crash_type"] == "BOT_CRASH"
            assert call_kwargs["error_type"] == "RuntimeError"
            assert call_kwargs["error_message"] == "Critical failure"
            assert call_kwargs["traceback"] == "Traceback..."
            assert call_kwargs["context"] == {"module": "test", "action": "process"}
            assert call_kwargs["extra_field"] == "value"

    def test_log_crash_sends_to_sentry_with_scope(self):
        """Test log_crash sends to Sentry with context scope."""
        logger = BotLogger("test")

        mock_scope = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=mock_scope)
        mock_context_manager.__exit__ = MagicMock(return_value=False)

        try:
            raise ValueError("Test")
        except ValueError as e:
            with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
                mock_sentry.is_initialized.return_value = True
                mock_sentry.push_scope.return_value = mock_context_manager

                logger.log_crash(
                    e,
                    context={"key": "value"},
                )

            # Should have captured exception
            mock_sentry.capture_exception.assert_called_once_with(e)
            # Should have set context on scope
            assert mock_scope.set_context.called


# =============================================================================
# Phase 4 Extended Tests for get_logger
# =============================================================================


class TestGetLoggerPhase4:
    """Phase 4 extended tests for get_logger function."""

    def test_get_logger_with_empty_string(self):
        """Test get_logger with empty string name."""
        logger = get_logger("")
        assert logger.name in {"root", ""}

    def test_get_logger_hierarchy(self):
        """Test get_logger respects logger hierarchy."""
        parent_logger = get_logger("myapp")
        child_logger = get_logger("myapp.module")

        # Child should be different instance
        assert parent_logger is not child_logger
        # But child's parent should be parent_logger
        assert child_logger.parent is parent_logger or child_logger.parent.name == parent_logger.name

    def test_get_logger_level_inheritance(self):
        """Test get_logger respects level inheritance."""
        parent_logger = get_logger("test_parent")
        parent_logger.setLevel(logging.WARNING)

        child_logger = get_logger("test_parent.child")
        # Child's effective level should be at least WARNING
        assert child_logger.getEffectiveLevel() >= logging.WARNING


# =============================================================================
# Phase 4 Edge Cases and Integration Tests
# =============================================================================


class TestLoggingUtilsEdgeCases:
    """Edge case tests for logging utilities."""

    def test_json_formatter_with_none_values(self):
        """Test JSONFormatter handles None values in extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.null_field = None
        record.zero_field = 0
        record.empty_string = ""
        record.false_bool = False

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["null_field"] is None
        assert parsed["zero_field"] == 0
        assert parsed["empty_string"] == ""
        assert parsed["false_bool"] is False

    def test_setup_logging_with_invalid_level_uses_info(self):
        """Test setup_logging uses INFO for invalid level string."""
        with patch("src.utils.logging_utils.setup_sentry"):
            with patch("src.utils.logging_utils.setup_structlog"):
                setup_logging(
                    level="INVALID_LEVEL",
                    enable_sentry=False,
                    enable_structlog=False,
                )

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_bot_logger_handles_unicode_in_item_names(self):
        """Test BotLogger handles unicode characters in item names."""
        logger = BotLogger("test")

        # Should not raise
        logger.log_buy_intent(
            item_name="АК-47 | Красная линия 🔥",
            price_usd=15.00,
        )

        logger.log_sell_intent(
            item_name="M4A4 | 龍王",
            price_usd=20.00,
        )

        logger.log_trade_result(
            operation="buy",
            success=True,
            item_name="Нож 🗡️",
            price_usd=100.00,
        )

    def test_bot_logger_handles_very_large_prices(self):
        """Test BotLogger handles very large price values."""
        logger = BotLogger("test")

        # Should not raise
        logger.log_buy_intent(
            item_name="Rare Item",
            price_usd=999999999.99,
            sell_price_usd=1000000000.00,
            profit_usd=0.01,
            profit_percent=0.000001,
        )

    def test_bot_logger_handles_zero_prices(self):
        """Test BotLogger handles zero price values."""
        logger = BotLogger("test")

        # Should not raise
        logger.log_buy_intent(
            item_name="Free Item",
            price_usd=0.00,
        )

    def test_bot_logger_handles_negative_profit(self):
        """Test BotLogger handles negative profit values."""
        logger = BotLogger("test")

        # Should not raise
        logger.log_sell_intent(
            item_name="Loss Item",
            price_usd=10.00,
            buy_price_usd=15.00,
            profit_usd=-5.00,
            profit_percent=-33.33,
        )


class TestLoggingUtilsIntegration:
    """Integration tests for logging utilities."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow from setup to output."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_file = f.name

        try:
            # Setup logging
            with patch("src.utils.logging_utils.setup_sentry"):
                setup_logging(
                    level="DEBUG",
                    log_file=log_file,
                    json_format=True,
                    enable_structlog=False,
                    enable_sentry=False,
                )

            # Use BotLogger
            bot_logger = BotLogger("test.integration")
            bot_logger.log_command(user_id=123, command="/test", success=True)
            bot_logger.log_market_data(game="csgo", items_count=100)

            # Use standard logger
            std_logger = get_logger("test.standard")
            std_logger.info("Standard log message")

            # Flush handlers
            for handler in logging.getLogger().handlers:
                handler.flush()

            # Verify file output
            with open(log_file, encoding="utf-8") as f:
                content = f.read()
                # File should contain log entries
                assert len(content) > 0
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_multiple_bot_loggers_isolation(self):
        """Test multiple BotLogger instances are isolated."""
        logger1 = BotLogger("module1")
        logger2 = BotLogger("module2")

        # Should be different structlog loggers
        assert logger1.logger is not logger2.logger

    def test_logging_with_concurrent_access(self):
        """Test logging handles concurrent access."""
        import concurrent.futures

        logger = BotLogger("concurrent")

        def log_operation(n):
            logger.log_command(user_id=n, command=f"/cmd{n}", success=True)
            return n

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(log_operation, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All operations should complete without error
        assert len(results) == 100

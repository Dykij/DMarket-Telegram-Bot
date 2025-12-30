"""Unit tests for src/utils/logging_utils.py.

Tests for logging utilities including:
- JSONFormatter
- ColoredFormatter
- Sentry setup
- Logging configuration
- Structlog setup
- BotLogger
"""

from datetime import datetime
import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        from src.utils.logging_utils import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert data["line"] == 10

    def test_format_includes_timestamp(self):
        """Test that format includes timestamp."""
        from src.utils.logging_utils import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "timestamp" in data
        # Should be ISO format
        datetime.fromisoformat(data["timestamp"])

    def test_format_with_exception(self):
        """Test formatting record with exception."""
        from src.utils.logging_utils import JSONFormatter

        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting record with extra fields."""
        from src.utils.logging_utils import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.user_id = 12345
        record.action = "buy"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == 12345
        assert data["action"] == "buy"


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_color_codes_defined(self):
        """Test that color codes are defined."""
        from src.utils.logging_utils import ColoredFormatter

        assert "DEBUG" in ColoredFormatter.COLORS
        assert "INFO" in ColoredFormatter.COLORS
        assert "WARNING" in ColoredFormatter.COLORS
        assert "ERROR" in ColoredFormatter.COLORS
        assert "CRITICAL" in ColoredFormatter.COLORS
        assert "RESET" in ColoredFormatter.COLORS

    def test_format_adds_color(self):
        """Test that format adds color codes."""
        from src.utils.logging_utils import ColoredFormatter

        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should contain ANSI escape codes
        assert "\033[" in result

    def test_format_unknown_level_uses_reset(self):
        """Test that unknown level uses reset color."""
        from src.utils.logging_utils import ColoredFormatter

        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=25,  # Custom level between INFO and WARNING
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.levelname = "CUSTOM"

        result = formatter.format(record)

        # Should still format without error
        assert "Test" in result


class TestSetupSentry:
    """Tests for setup_sentry function."""

    @patch.dict(os.environ, {"SENTRY_DSN": ""})
    def test_no_dsn_logs_info(self):
        """Test that missing DSN logs info message."""
        from src.utils.logging_utils import setup_sentry

        with patch("src.utils.logging_utils.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            setup_sentry()

            mock_logger.info.assert_called()

    @pytest.mark.skipif(
        True,  # Skip due to SQLAlchemy import in setup_sentry
        reason="Test requires SQLAlchemy to be installed for Sentry integration",
    )
    @patch.dict(os.environ, {"SENTRY_DSN": "https://test@sentry.io/123"})
    @patch("src.utils.logging_utils.sentry_sdk")
    def test_with_dsn_initializes_sentry(self, mock_sentry):
        """Test that valid DSN initializes Sentry."""
        from src.utils.logging_utils import setup_sentry

        setup_sentry(environment="test")

        mock_sentry.init.assert_called_once()
        call_kwargs = mock_sentry.init.call_args[1]
        assert call_kwargs["environment"] == "test"

    @pytest.mark.skipif(
        True,  # Skip due to SQLAlchemy import in setup_sentry
        reason="Test requires SQLAlchemy to be installed for Sentry integration",
    )
    @patch.dict(os.environ, {"SENTRY_DSN": "https://test@sentry.io/123"})
    @patch("src.utils.logging_utils.sentry_sdk")
    def test_custom_traces_sample_rate(self, mock_sentry):
        """Test custom traces sample rate."""
        from src.utils.logging_utils import setup_sentry

        setup_sentry(traces_sample_rate=0.8)

        call_kwargs = mock_sentry.init.call_args[1]
        assert call_kwargs["traces_sample_rate"] == 0.8


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_with_defaults(self):
        """Test setup with default parameters."""
        from src.utils.logging_utils import setup_logging

        with patch("src.utils.logging_utils.setup_sentry"):
            setup_logging(enable_sentry=False)

            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO

    def test_setup_with_custom_level(self):
        """Test setup with custom level."""
        from src.utils.logging_utils import setup_logging

        with patch("src.utils.logging_utils.setup_sentry"):
            setup_logging(level="DEBUG", enable_sentry=False)

            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

    def test_setup_suppresses_noisy_loggers(self):
        """Test that noisy loggers are suppressed."""
        from src.utils.logging_utils import setup_logging

        with patch("src.utils.logging_utils.setup_sentry"):
            setup_logging(enable_sentry=False)

            httpx_logger = logging.getLogger("httpx")
            assert httpx_logger.level == logging.WARNING


class TestSetupStructlog:
    """Tests for setup_structlog function."""

    def test_setup_structlog_console(self):
        """Test structlog setup for console."""
        import structlog

        from src.utils.logging_utils import setup_structlog

        setup_structlog(json_format=False)

        # Should configure without error
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_setup_structlog_json(self):
        """Test structlog setup for JSON."""
        import structlog

        from src.utils.logging_utils import setup_structlog

        setup_structlog(json_format=True)

        # Should configure without error
        logger = structlog.get_logger("test")
        assert logger is not None


class TestBotLoggerInit:
    """Tests for BotLogger initialization."""

    def test_init_creates_logger(self):
        """Test initialization creates structlog logger."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test_bot")

        assert bot_logger.logger is not None


class TestBotLoggerLogCommand:
    """Tests for BotLogger.log_command method."""

    def test_log_command_success(self):
        """Test logging successful command."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_command(
                user_id=123456,
                command="/balance",
                success=True,
            )

            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["user_id"] == 123456
            assert call_kwargs["command"] == "/balance"
            assert call_kwargs["success"] is True

    def test_log_command_with_extra(self):
        """Test logging command with extra parameters."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_command(
                user_id=123456,
                command="/scan",
                success=True,
                game="csgo",
                level="standard",
            )

            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["game"] == "csgo"
            assert call_kwargs["level"] == "standard"


class TestBotLoggerLogApiCall:
    """Tests for BotLogger.log_api_call method."""

    def test_log_api_call_success(self):
        """Test logging successful API call."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_api_call(
                endpoint="/market/items",
                method="GET",
                status_code=200,
                response_time=0.5,
            )

            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == "info"

    def test_log_api_call_error(self):
        """Test logging API call with error."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_api_call(
                endpoint="/market/items",
                method="GET",
                status_code=500,
                error="Internal Server Error",
            )

            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == "error"


class TestBotLoggerLogMarketData:
    """Tests for BotLogger.log_market_data method."""

    def test_log_market_data(self):
        """Test logging market data."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_market_data(
                game="csgo",
                items_count=100,
                total_value=5000.0,
            )

            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["game"] == "csgo"
            assert call_kwargs["items_count"] == 100
            assert call_kwargs["total_value"] == 5000.0


class TestBotLoggerLogError:
    """Tests for BotLogger.log_error method."""

    def test_log_error_basic(self):
        """Test logging basic error."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            error = ValueError("Test error")
            bot_logger.log_error(error)

            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs["error_type"] == "ValueError"
            assert call_kwargs["error_message"] == "Test error"

    def test_log_error_with_context(self):
        """Test logging error with context."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            error = ValueError("Test error")
            bot_logger.log_error(
                error,
                context={"user_id": 123, "action": "buy"},
            )

            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs["user_id"] == 123
            assert call_kwargs["action"] == "buy"


class TestBotLoggerLogBuyIntent:
    """Tests for BotLogger.log_buy_intent method."""

    def test_log_buy_intent_dry_run(self):
        """Test logging buy intent in dry run mode."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_buy_intent(
                item_name="AK-47 | Redline",
                price_usd=15.50,
                sell_price_usd=20.00,
                profit_usd=4.50,
                dry_run=True,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "DRY-RUN" in call_args[0][0]
            assert "BUY_INTENT" in call_args[0][0]

    def test_log_buy_intent_live(self):
        """Test logging buy intent in live mode."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_buy_intent(
                item_name="AK-47 | Redline",
                price_usd=15.50,
                dry_run=False,
            )

            call_args = mock_logger.info.call_args
            assert "LIVE" in call_args[0][0]


class TestBotLoggerLogSellIntent:
    """Tests for BotLogger.log_sell_intent method."""

    def test_log_sell_intent(self):
        """Test logging sell intent."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_sell_intent(
                item_name="AK-47 | Redline",
                price_usd=20.00,
                buy_price_usd=15.50,
                profit_usd=4.50,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "SELL_INTENT" in call_args[0][0]


class TestBotLoggerLogTradeResult:
    """Tests for BotLogger.log_trade_result method."""

    def test_log_trade_result_success(self):
        """Test logging successful trade."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_trade_result(
                operation="buy",
                success=True,
                item_name="AK-47",
                price_usd=15.50,
            )

            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == logging.INFO
            assert "SUCCESS" in call_args[0][1]

    def test_log_trade_result_failure(self):
        """Test logging failed trade."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            bot_logger.log_trade_result(
                operation="buy",
                success=False,
                item_name="AK-47",
                price_usd=15.50,
                error_message="Insufficient balance",
            )

            call_args = mock_logger.log.call_args
            assert call_args[0][0] == logging.ERROR
            assert "FAILED" in call_args[0][1]


class TestBotLoggerLogCrash:
    """Tests for BotLogger.log_crash method."""

    def test_log_crash_basic(self):
        """Test logging crash."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            error = RuntimeError("Critical failure")
            bot_logger.log_crash(error)

            mock_logger.critical.assert_called_once()
            call_args = mock_logger.critical.call_args
            assert "CRASH" in call_args[0][0]

    def test_log_crash_with_traceback(self):
        """Test logging crash with traceback."""
        from src.utils.logging_utils import BotLogger

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger") as mock_logger:
            error = RuntimeError("Critical failure")
            bot_logger.log_crash(
                error,
                traceback_text="Traceback...",
            )

            call_kwargs = mock_logger.critical.call_args[1]
            assert call_kwargs["traceback"] == "Traceback..."

    @patch("src.utils.logging_utils.sentry_sdk")
    def test_log_crash_sends_to_sentry(self, mock_sentry):
        """Test logging crash sends to Sentry."""
        from src.utils.logging_utils import BotLogger

        mock_sentry.is_initialized.return_value = True

        bot_logger = BotLogger("test")

        with patch.object(bot_logger, "logger"):
            error = RuntimeError("Critical failure")
            bot_logger.log_crash(error)

            mock_sentry.capture_exception.assert_called_once_with(error)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns logger instance."""
        from src.utils.logging_utils import get_logger

        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_same_name_returns_same_logger(self):
        """Test get_logger with same name returns same instance."""
        from src.utils.logging_utils import get_logger

        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2

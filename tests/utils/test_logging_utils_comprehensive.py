"""Comprehensive tests for logging_utils module.

Tests for BotLogger class and logging configuration functions including
setup_sentry, setup_logging, and setup_structlog.
"""

import logging
import sys
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBotLoggerInit:
    """Tests for BotLogger initialization."""

    def test_init_creates_logger(self):
        """Test that BotLogger creates a logger instance."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            bot_logger = BotLogger("test")
            
            mock_structlog.get_logger.assert_called_once_with("test")

    def test_init_with_various_names(self):
        """Test BotLogger with different logger names."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            names = ["test", "dmarket.api", "telegram_bot.commands", "utils.trading"]
            for name in names:
                BotLogger(name)
                mock_structlog.get_logger.assert_called_with(name)


class TestBotLoggerLogCommand:
    """Tests for BotLogger.log_command method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_command_basic(self, bot_logger):
        """Test logging a basic command."""
        logger, mock_logger = bot_logger
        
        logger.log_command(user_id=123, command="balance")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["user_id"] == 123
        assert call_args.kwargs["command"] == "balance"
        assert call_args.kwargs["success"] is True

    def test_log_command_with_failure(self, bot_logger):
        """Test logging a failed command."""
        logger, mock_logger = bot_logger
        
        logger.log_command(user_id=456, command="scan", success=False)
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["success"] is False

    def test_log_command_with_extra_kwargs(self, bot_logger):
        """Test logging command with extra parameters."""
        logger, mock_logger = bot_logger
        
        logger.log_command(
            user_id=789,
            command="arbitrage",
            success=True,
            game="csgo",
            level="standard",
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["game"] == "csgo"
        assert call_args.kwargs["level"] == "standard"


class TestBotLoggerLogApiCall:
    """Tests for BotLogger.log_api_call method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_api_call_success(self, bot_logger):
        """Test logging successful API call."""
        logger, mock_logger = bot_logger
        
        logger.log_api_call(
            endpoint="/market/items",
            method="GET",
            status_code=200,
            response_time=0.5,
        )
        
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args.args[0] == "info"
        assert call_args.kwargs["endpoint"] == "/market/items"
        assert call_args.kwargs["method"] == "GET"
        assert call_args.kwargs["status_code"] == 200

    def test_log_api_call_with_error(self, bot_logger):
        """Test logging API call with error."""
        logger, mock_logger = bot_logger
        
        logger.log_api_call(
            endpoint="/market/items",
            method="GET",
            error="Rate limit exceeded",
        )
        
        call_args = mock_logger.log.call_args
        assert call_args.args[0] == "error"
        assert call_args.kwargs["error"] == "Rate limit exceeded"

    def test_log_api_call_with_response_time(self, bot_logger):
        """Test logging API call with response time."""
        logger, mock_logger = bot_logger
        
        logger.log_api_call(
            endpoint="/balance",
            method="GET",
            status_code=200,
            response_time=1.234,
        )
        
        call_args = mock_logger.log.call_args
        assert call_args.kwargs["response_time"] == 1.234


class TestBotLoggerLogMarketData:
    """Tests for BotLogger.log_market_data method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_market_data_basic(self, bot_logger):
        """Test logging basic market data."""
        logger, mock_logger = bot_logger
        
        logger.log_market_data(game="csgo", items_count=100)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["game"] == "csgo"
        assert call_args.kwargs["items_count"] == 100

    def test_log_market_data_with_value(self, bot_logger):
        """Test logging market data with total value."""
        logger, mock_logger = bot_logger
        
        logger.log_market_data(
            game="dota2",
            items_count=50,
            total_value=1000.50,
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["total_value"] == 1000.50

    def test_log_market_data_with_extra_fields(self, bot_logger):
        """Test logging market data with extra fields."""
        logger, mock_logger = bot_logger
        
        logger.log_market_data(
            game="tf2",
            items_count=25,
            avg_price=10.0,
            min_price=1.0,
            max_price=50.0,
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["avg_price"] == 10.0
        assert call_args.kwargs["min_price"] == 1.0


class TestBotLoggerLogError:
    """Tests for BotLogger.log_error method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_error_basic(self, bot_logger):
        """Test logging basic error."""
        logger, mock_logger = bot_logger
        
        error = ValueError("Test error")
        logger.log_error(error)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args.kwargs["error_type"] == "ValueError"
        assert call_args.kwargs["error_message"] == "Test error"

    def test_log_error_with_context(self, bot_logger):
        """Test logging error with context."""
        logger, mock_logger = bot_logger
        
        error = RuntimeError("Connection failed")
        context = {"endpoint": "/api/test", "attempt": 3}
        
        logger.log_error(error, context=context)
        
        call_args = mock_logger.error.call_args
        assert call_args.kwargs["endpoint"] == "/api/test"
        assert call_args.kwargs["attempt"] == 3

    def test_log_error_different_types(self, bot_logger):
        """Test logging different error types."""
        logger, mock_logger = bot_logger
        
        errors = [
            ValueError("Value error"),
            TypeError("Type error"),
            KeyError("Key error"),
            RuntimeError("Runtime error"),
        ]
        
        for error in errors:
            logger.log_error(error)
            call_args = mock_logger.error.call_args
            assert call_args.kwargs["error_type"] == type(error).__name__


class TestBotLoggerLogBuyIntent:
    """Tests for BotLogger.log_buy_intent method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_buy_intent_basic(self, bot_logger):
        """Test logging basic buy intent."""
        logger, mock_logger = bot_logger
        
        logger.log_buy_intent(
            item_name="AK-47 | Redline",
            price_usd=10.50,
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["item"] == "AK-47 | Redline"
        assert call_args.kwargs["price_usd"] == 10.50

    def test_log_buy_intent_with_profit(self, bot_logger):
        """Test logging buy intent with profit info."""
        logger, mock_logger = bot_logger
        
        logger.log_buy_intent(
            item_name="Test Item",
            price_usd=10.0,
            sell_price_usd=12.0,
            profit_usd=2.0,
            profit_percent=20.0,
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["sell_price_usd"] == 12.0
        assert call_args.kwargs["profit_usd"] == 2.0
        assert call_args.kwargs["profit_percent"] == 20.0

    def test_log_buy_intent_dry_run_mode(self, bot_logger):
        """Test logging buy intent in dry run mode."""
        logger, mock_logger = bot_logger
        
        logger.log_buy_intent(
            item_name="Test Item",
            price_usd=10.0,
            dry_run=True,
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["dry_run"] is True
        assert "DRY-RUN" in call_args.args[0]

    def test_log_buy_intent_live_mode(self, bot_logger):
        """Test logging buy intent in live mode."""
        logger, mock_logger = bot_logger
        
        logger.log_buy_intent(
            item_name="Test Item",
            price_usd=10.0,
            dry_run=False,
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["dry_run"] is False
        assert "LIVE" in call_args.args[0]


class TestBotLoggerLogSellIntent:
    """Tests for BotLogger.log_sell_intent method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_sell_intent_basic(self, bot_logger):
        """Test logging basic sell intent."""
        logger, mock_logger = bot_logger
        
        logger.log_sell_intent(
            item_name="AWP | Asiimov",
            price_usd=50.0,
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["item"] == "AWP | Asiimov"
        assert call_args.kwargs["intent_type"] == "SELL_INTENT"

    def test_log_sell_intent_with_buy_price(self, bot_logger):
        """Test logging sell intent with original buy price."""
        logger, mock_logger = bot_logger
        
        logger.log_sell_intent(
            item_name="Test Item",
            price_usd=12.0,
            buy_price_usd=10.0,
            profit_usd=2.0,
        )
        
        call_args = mock_logger.info.call_args
        assert call_args.kwargs["buy_price_usd"] == 10.0
        assert call_args.kwargs["profit_usd"] == 2.0


class TestBotLoggerLogTradeResult:
    """Tests for BotLogger.log_trade_result method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_trade_result_success(self, bot_logger):
        """Test logging successful trade result."""
        logger, mock_logger = bot_logger
        
        logger.log_trade_result(
            operation="buy",
            success=True,
            item_name="Test Item",
            price_usd=10.0,
        )
        
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args.kwargs["success"] is True
        assert "SUCCESS" in call_args.args[1]

    def test_log_trade_result_failure(self, bot_logger):
        """Test logging failed trade result."""
        logger, mock_logger = bot_logger
        
        logger.log_trade_result(
            operation="sell",
            success=False,
            item_name="Test Item",
            price_usd=10.0,
            error_message="Insufficient funds",
        )
        
        call_args = mock_logger.log.call_args
        assert call_args.kwargs["success"] is False
        assert call_args.kwargs["error"] == "Insufficient funds"
        assert "FAILED" in call_args.args[1]


class TestBotLoggerLogCrash:
    """Tests for BotLogger.log_crash method."""

    @pytest.fixture
    def bot_logger(self):
        """Create a BotLogger instance with mocked logger."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            mock_logger = MagicMock()
            mock_structlog.get_logger.return_value = mock_logger
            
            from src.utils.logging_utils import BotLogger
            
            logger = BotLogger("test")
            yield logger, mock_logger

    def test_log_crash_basic(self, bot_logger):
        """Test logging basic crash."""
        logger, mock_logger = bot_logger
        
        error = RuntimeError("Critical failure")
        
        with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False
            logger.log_crash(error)
        
        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args
        assert call_args.kwargs["error_type"] == "RuntimeError"

    def test_log_crash_with_traceback(self, bot_logger):
        """Test logging crash with traceback."""
        logger, mock_logger = bot_logger
        
        error = ValueError("Test error")
        traceback_text = "Traceback (most recent call last):\n  File..."
        
        with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False
            logger.log_crash(error, traceback_text=traceback_text)
        
        call_args = mock_logger.critical.call_args
        assert call_args.kwargs["traceback"] == traceback_text

    def test_log_crash_with_context(self, bot_logger):
        """Test logging crash with context."""
        logger, mock_logger = bot_logger
        
        error = Exception("Unexpected error")
        context = {"user_id": 123, "command": "scan"}
        
        with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = False
            logger.log_crash(error, context=context)
        
        call_args = mock_logger.critical.call_args
        assert call_args.kwargs["context"] == context


class TestSetupSentry:
    """Tests for setup_sentry function."""

    def test_setup_sentry_without_dsn(self):
        """Test setup_sentry when DSN is not configured."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove SENTRY_DSN if exists
            with patch("os.getenv", return_value=None):
                with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
                    from src.utils.logging_utils import setup_sentry
                    
                    setup_sentry()
                    
                    # sentry_sdk.init should not be called
                    mock_sentry.init.assert_not_called()

    def test_setup_sentry_with_dsn(self):
        """Test setup_sentry when DSN is configured."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "SENTRY_DSN": "https://test@sentry.io/123",
                "BOT_VERSION": "1.0.0",
            }.get(key, default)
            
            with patch("src.utils.logging_utils.sentry_sdk") as mock_sentry:
                from src.utils.logging_utils import setup_sentry
                
                setup_sentry(
                    environment="production",
                    traces_sample_rate=0.5,
                )
                
                mock_sentry.init.assert_called_once()
                call_kwargs = mock_sentry.init.call_args.kwargs
                assert call_kwargs["dsn"] == "https://test@sentry.io/123"
                assert call_kwargs["environment"] == "production"
                assert call_kwargs["traces_sample_rate"] == 0.5


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        with patch("src.utils.logging_utils.setup_structlog"):
            with patch("src.utils.logging_utils.setup_sentry"):
                from src.utils.logging_utils import setup_logging
                
                setup_logging(
                    level="INFO",
                    enable_structlog=False,
                    enable_sentry=False,
                )
                
                root_logger = logging.getLogger()
                assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = f"{tmpdir}/test.log"
            
            with patch("src.utils.logging_utils.setup_structlog"):
                with patch("src.utils.logging_utils.setup_sentry"):
                    from src.utils.logging_utils import setup_logging
                    
                    setup_logging(
                        level="DEBUG",
                        log_file=log_file,
                        enable_structlog=False,
                        enable_sentry=False,
                    )
                    
                    # Check that file was created
                    import os
                    # The file will be created when something is logged
                    logger = logging.getLogger("test.file.logger")
                    logger.info("Test message")

    def test_setup_logging_with_json_format(self):
        """Test logging setup with JSON format."""
        with patch("src.utils.logging_utils.setup_structlog"):
            with patch("src.utils.logging_utils.setup_sentry"):
                from src.utils.logging_utils import setup_logging
                
                setup_logging(
                    level="INFO",
                    json_format=True,
                    enable_structlog=False,
                    enable_sentry=False,
                )
                
                # Should not raise
                logger = logging.getLogger("test.json")
                logger.info("Test JSON message")

    def test_setup_logging_calls_structlog(self):
        """Test that setup_logging calls setup_structlog when enabled."""
        with patch("src.utils.logging_utils.setup_structlog") as mock_structlog:
            with patch("src.utils.logging_utils.setup_sentry"):
                from src.utils.logging_utils import setup_logging
                
                setup_logging(
                    level="INFO",
                    enable_structlog=True,
                    enable_sentry=False,
                )
                
                mock_structlog.assert_called_once()

    def test_setup_logging_calls_sentry(self):
        """Test that setup_logging calls setup_sentry when enabled."""
        with patch("src.utils.logging_utils.setup_structlog"):
            with patch("src.utils.logging_utils.setup_sentry") as mock_sentry:
                from src.utils.logging_utils import setup_logging
                
                setup_logging(
                    level="INFO",
                    enable_structlog=False,
                    enable_sentry=True,
                    sentry_environment="production",
                )
                
                mock_sentry.assert_called_once_with(
                    environment="production",
                    traces_sample_rate=0.1,
                )


class TestSetupStructlog:
    """Tests for setup_structlog function."""

    def test_setup_structlog_basic(self):
        """Test basic structlog setup."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            from src.utils.logging_utils import setup_structlog
            
            setup_structlog(json_format=False)
            
            mock_structlog.configure.assert_called_once()

    def test_setup_structlog_json_format(self):
        """Test structlog setup with JSON format."""
        with patch("src.utils.logging_utils.structlog") as mock_structlog:
            from src.utils.logging_utils import setup_structlog
            
            setup_structlog(json_format=True)
            
            mock_structlog.configure.assert_called_once()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        from src.utils.logging_utils import get_logger
        
        logger = get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_same_name_returns_same_logger(self):
        """Test that getting the same logger name returns the same instance."""
        from src.utils.logging_utils import get_logger
        
        logger1 = get_logger("same.name")
        logger2 = get_logger("same.name")
        
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names return different loggers."""
        from src.utils.logging_utils import get_logger
        
        logger1 = get_logger("name.one")
        logger2 = get_logger("name.two")
        
        assert logger1 is not logger2
        assert logger1.name == "name.one"
        assert logger2.name == "name.two"

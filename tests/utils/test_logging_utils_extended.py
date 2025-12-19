"""Tests for logging_utils module.

This module tests logging configuration, formatters, and utilities
for structured logging with support for JSON and colored output.
"""

import json
import logging
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.utils.logging_utils import (
    ColoredFormatter,
    JSONFormatter,
)


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a JSONFormatter instance."""
        return JSONFormatter()

    @pytest.fixture
    def log_record(self):
        """Create a sample log record."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        return record

    def test_format_returns_json_string(self, formatter, log_record):
        """Test that format returns valid JSON string."""
        result = formatter.format(log_record)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_contains_required_fields(self, formatter, log_record):
        """Test that formatted output contains required fields."""
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed
        assert "module" in parsed
        assert "function" in parsed
        assert "line" in parsed

    def test_format_level_name(self, formatter, log_record):
        """Test that level name is correct."""
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert parsed["level"] == "INFO"

    def test_format_message(self, formatter, log_record):
        """Test that message is correct."""
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert parsed["message"] == "Test message"

    def test_format_logger_name(self, formatter, log_record):
        """Test that logger name is correct."""
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert parsed["logger"] == "test.logger"

    def test_format_line_number(self, formatter, log_record):
        """Test that line number is correct."""
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert parsed["line"] == 42

    def test_format_with_exception(self, formatter):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_format_with_extra_fields(self, formatter, log_record):
        """Test formatting with extra fields."""
        log_record.user_id = 12345
        log_record.action = "test_action"
        
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert parsed.get("user_id") == 12345
        assert parsed.get("action") == "test_action"

    def test_format_different_log_levels(self, formatter):
        """Test formatting different log levels."""
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]
        
        for level, expected_name in levels:
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
            parsed = json.loads(result)
            assert parsed["level"] == expected_name


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a ColoredFormatter instance."""
        return ColoredFormatter("%(levelname)s - %(message)s")

    @pytest.fixture
    def log_record(self):
        """Create a sample log record."""
        return logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

    def test_format_returns_string(self, formatter, log_record):
        """Test that format returns a string."""
        result = formatter.format(log_record)
        assert isinstance(result, str)

    def test_format_contains_message(self, formatter, log_record):
        """Test that formatted output contains message."""
        result = formatter.format(log_record)
        assert "Test message" in result

    def test_colors_exist(self, formatter):
        """Test that color codes are defined."""
        assert "DEBUG" in formatter.COLORS
        assert "INFO" in formatter.COLORS
        assert "WARNING" in formatter.COLORS
        assert "ERROR" in formatter.COLORS
        assert "CRITICAL" in formatter.COLORS
        assert "RESET" in formatter.COLORS

    def test_color_codes_are_ansi(self, formatter):
        """Test that color codes are ANSI escape sequences."""
        for name, code in formatter.COLORS.items():
            assert code.startswith("\033[")


class TestLoggingConfiguration:
    """Tests for logging configuration functions."""

    def test_json_formatter_with_handler(self):
        """Test JSONFormatter works with a handler."""
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("test.json.handler")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Should not raise
        logger.info("Test message")
        
        logger.removeHandler(handler)

    def test_colored_formatter_with_handler(self):
        """Test ColoredFormatter works with a handler."""
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter("%(levelname)s - %(message)s"))
        
        logger = logging.getLogger("test.colored.handler")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Should not raise
        logger.info("Test message")
        
        logger.removeHandler(handler)


class TestJSONFormatterEdgeCases:
    """Tests for edge cases in JSONFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a JSONFormatter instance."""
        return JSONFormatter()

    def test_format_with_none_message(self, formatter):
        """Test formatting with None message."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg=None,
            args=(),
            exc_info=None,
        )
        
        # Should not raise
        result = formatter.format(record)
        assert isinstance(result, str)

    def test_format_with_unicode(self, formatter):
        """Test formatting with unicode characters."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Тест сообщение 🎮",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        assert "Тест" in parsed["message"]

    def test_format_with_format_args(self, formatter):
        """Test formatting with format arguments."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="User %s performed action %s",
            args=("John", "login"),
            exc_info=None,
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        assert "John" in parsed["message"]
        assert "login" in parsed["message"]

    def test_format_with_dict_extra(self, formatter):
        """Test formatting with dictionary in extra."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.data = {"key": "value", "number": 42}
        
        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed.get("data") == {"key": "value", "number": 42}

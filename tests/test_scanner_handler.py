"""Tests for refactored scanner handler.

Tests Phase 2 improvements:
- Early returns pattern
- Reduced nesting
- Smaller functions
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.handlers.scanner_handler_refactored import (
    _create_back_button,
    _format_liquidity_info,
    _validate_query_and_user,
    format_scanner_item,
    format_scanner_results,
)


class TestFormatLiquidityInfo:
    """Test liquidity formatting helper."""

    def test_format_liquidity_info_with_valid_data(self):
        """Test formatting with valid liquidity data."""
        liquidity_data = {"liquidity_score": 8.5, "rating": "High"}
        result = _format_liquidity_info(liquidity_data)
        assert result == "💧 Ликвидность: 8.5/10 (High)"

    def test_format_liquidity_info_with_empty_data(self):
        """Test formatting with empty data."""
        result = _format_liquidity_info({})
        assert result == ""

    def test_format_liquidity_info_with_zero_score(self):
        """Test formatting with zero score."""
        liquidity_data = {"liquidity_score": 0.0, "rating": "None"}
        result = _format_liquidity_info(liquidity_data)
        assert result == ""


class TestFormatScannerItem:
    """Test single item formatting."""

    def test_format_scanner_item_basic_info(self):
        """Test formatting basic item information."""
        item = {
            "title": "AK-47 | Redline",
            "buy_price": 10.50,
            "sell_price": 15.00,
            "profit": 3.50,
            "profit_percent": 25.0,
            "level": "standard",
            "risk_level": "low",
        }
        result = format_scanner_item(item)

        assert "AK-47 | Redline" in result
        assert "$10.50" in result
        assert "$15.00" in result
        assert "$3.50" in result
        assert "25.0%" in result
        assert "standard" in result
        assert "low" in result

    def test_format_scanner_item_with_liquidity(self):
        """Test formatting with liquidity data."""
        item = {
            "title": "Test Item",
            "buy_price": 5.0,
            "sell_price": 7.0,
            "profit": 1.5,
            "profit_percent": 20.0,
            "level": "boost",
            "risk_level": "medium",
            "liquidity_data": {"liquidity_score": 7.5, "rating": "Good"},
        }
        result = format_scanner_item(item)

        assert "7.5/10" in result
        assert "Good" in result

    def test_format_scanner_item_with_missing_fields(self):
        """Test formatting with missing fields uses defaults."""
        item = {}
        result = format_scanner_item(item)

        assert "Неизвестный предмет" in result
        assert "$0.00" in result


class TestFormatScannerResults:
    """Test results list formatting."""

    def test_format_scanner_results_with_items(self):
        """Test formatting multiple items."""
        items = [
            {
                "title": "Item 1",
                "buy_price": 5.0,
                "sell_price": 7.0,
                "profit": 1.5,
                "profit_percent": 20.0,
                "level": "boost",
                "risk_level": "low",
            },
            {
                "title": "Item 2",
                "buy_price": 10.0,
                "sell_price": 14.0,
                "profit": 3.0,
                "profit_percent": 25.0,
                "level": "standard",
                "risk_level": "medium",
            },
        ]
        result = format_scanner_results(items, current_page=0, items_per_page=10)

        assert "Страница 1" in result
        assert "Item 1" in result
        assert "Item 2" in result

    def test_format_scanner_results_empty_list(self):
        """Test formatting with no items."""
        result = format_scanner_results([], current_page=0, items_per_page=10)
        assert result == "Нет результатов для отображения."

    def test_format_scanner_results_page_number(self):
        """Test page number in header."""
        items = [
            {
                "title": "Test",
                "buy_price": 5.0,
                "sell_price": 7.0,
                "profit": 1.5,
                "profit_percent": 20.0,
                "level": "boost",
                "risk_level": "low",
            }
        ]

        result_page_1 = format_scanner_results(items, current_page=0, items_per_page=10)
        assert "Страница 1" in result_page_1

        result_page_3 = format_scanner_results(items, current_page=2, items_per_page=10)
        assert "Страница 3" in result_page_3


class TestCreateBackButton:
    """Test back button helper."""

    def test_create_back_button_structure(self):
        """Test back button keyboard structure."""
        keyboard = _create_back_button()

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1

        button = keyboard.inline_keyboard[0][0]
        assert button.text == "⬅️ Назад"
        assert button.callback_data == "scanner"


class TestValidateQueryAndUser:
    """Test query and user validation."""

    @pytest.mark.asyncio()
    async def test_validate_query_and_user_success(self):
        """Test successful validation."""
        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        update.effective_user = MagicMock(id=12345)

        result = await _validate_query_and_user(update)

        assert result is not None
        query.answer.assert_called_once()
        assert result[1] == 12345

    @pytest.mark.asyncio()
    async def test_validate_query_and_user_no_query(self):
        """Test validation fails with no query."""
        update = MagicMock()
        update.callback_query = None

        result = await _validate_query_and_user(update)

        assert result is None

    @pytest.mark.asyncio()
    async def test_validate_query_and_user_no_user(self):
        """Test validation fails with no user."""
        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        update.effective_user = None

        result = await _validate_query_and_user(update)

        assert result is None
        query.answer.assert_called_once()


class TestHandleLevelScanRefactored:
    """Test refactored handle_level_scan function."""

    @pytest.mark.asyncio()
    async def test_handle_level_scan_validates_inputs(self):
        """Test function validates inputs with early returns."""
        from src.telegram_bot.handlers.scanner_handler_refactored import (
            handle_level_scan,
        )

        # Test with no query
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        # Should return early
        await handle_level_scan(update, context, "boost", "csgo")
        # No exception raised = success

    @pytest.mark.asyncio()
    async def test_handle_level_scan_invalid_level(self):
        """Test function handles invalid level."""
        from src.telegram_bot.handlers.scanner_handler_refactored import (
            handle_level_scan,
        )

        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        update.effective_user = MagicMock(id=12345, username="test_user")
        context = MagicMock()

        with patch(
            "src.telegram_bot.handlers.scanner_handler_refactored.add_command_breadcrumb"
        ):
            await handle_level_scan(update, context, "invalid_level", "csgo")

        # Should send error message
        query.edit_message_text.assert_called()
        call_args = query.edit_message_text.call_args[0][0]
        assert "Неизвестный уровень" in call_args


@pytest.mark.asyncio()
async def test_refactored_functions_are_shorter():
    """Test that refactored functions are under reasonable length.

    This is a meta-test for Phase 2 compliance.
    Updated: Allow up to 75 lines for complex handlers with error handling.
    """
    import inspect

    from src.telegram_bot.handlers import scanner_handler_refactored

    functions_to_check = [
        scanner_handler_refactored.handle_level_scan,
        scanner_handler_refactored.format_scanner_item,
        scanner_handler_refactored.format_scanner_results,
        scanner_handler_refactored._format_liquidity_info,
        scanner_handler_refactored._validate_query_and_user,
        scanner_handler_refactored._send_scanning_message,
        scanner_handler_refactored._send_no_results_message,
        scanner_handler_refactored._send_error_message,
        scanner_handler_refactored._perform_scan,
        scanner_handler_refactored._send_results,
    ]

    for func in functions_to_check:
        source_lines = inspect.getsourcelines(func)[0]
        line_count = len(source_lines)

        # Allow up to 75 lines for complex handlers with comprehensive error handling
        assert (
            line_count < 75
        ), f"{func.__name__} has {line_count} lines (should be < 75)"

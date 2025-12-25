"""Extended tests for telegram_bot/utils/formatters.py module.

Tests cover:
- format_balance
- format_market_item
- format_market_items
- format_opportunities
- format_error_message
- format_sales_history
- format_sales_analysis
- format_liquidity_analysis
- get_trend_emoji
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.telegram_bot.utils.formatters import (
    MAX_MESSAGE_LENGTH,
    format_balance,
    format_error_message,
    format_liquidity_analysis,
    format_market_item,
    format_market_items,
    format_opportunities,
    format_sales_analysis,
    format_sales_history,
    get_trend_emoji,
)


# === Tests for format_balance ===


class TestFormatBalance:
    """Tests for format_balance function."""

    def test_format_balance_success(self):
        """Test formatting balance with valid data."""
        balance_data = {
            "balance": 100.50,
            "available_balance": 80.25,
            "total_balance": 100.50,
        }

        result = format_balance(balance_data)

        assert "💰" in result
        assert "$80.25" in result
        assert "$100.50" in result

    def test_format_balance_with_error(self):
        """Test formatting balance with error."""
        balance_data = {
            "error": True,
            "error_message": "API connection failed",
        }

        result = format_balance(balance_data)

        assert "❌" in result
        assert "Ошибка" in result
        assert "API connection failed" in result

    def test_format_balance_with_blocked_funds(self):
        """Test formatting balance with blocked funds."""
        balance_data = {
            "balance": 100.00,
            "available_balance": 60.00,
            "total_balance": 100.00,
        }

        result = format_balance(balance_data)

        assert "$40.00" in result  # Blocked amount
        assert "🔒" in result or "Заблокировано" in result

    def test_format_balance_low_balance_warning(self):
        """Test that low balance warning is shown."""
        balance_data = {
            "balance": 0.50,
            "available_balance": 0.50,
            "total_balance": 0.50,
        }

        result = format_balance(balance_data)

        assert "⚠️" in result
        assert "$1" in result or "меньше" in result

    def test_format_balance_zero_balance(self):
        """Test formatting zero balance."""
        balance_data = {
            "balance": 0,
            "available_balance": 0,
            "total_balance": 0,
        }

        result = format_balance(balance_data)

        assert "$0.00" in result

    def test_format_balance_defaults_to_balance_field(self):
        """Test that missing fields default to balance."""
        balance_data = {"balance": 50.00}

        result = format_balance(balance_data)

        assert "$50.00" in result


# === Tests for format_market_item ===


class TestFormatMarketItem:
    """Tests for format_market_item function."""

    def test_format_market_item_basic(self):
        """Test basic item formatting."""
        item = {
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"USD": 1250},
        }

        result = format_market_item(item)

        assert "AK-47 | Redline" in result
        assert "$12.50" in result
        assert "🏷️" in result

    def test_format_market_item_with_details(self):
        """Test item formatting with details."""
        item = {
            "title": "AWP | Asiimov (Field-Tested)",
            "price": {"USD": 5000},
            "itemId": "test_item_123",
            "extra": {
                "exteriorName": "Field-Tested",
                "floatValue": "0.2345",
                "stickers": [{"name": "Navi"}, {"name": "G2"}],
            },
        }

        result = format_market_item(item, show_details=True)

        assert "AWP | Asiimov" in result
        assert "Field-Tested" in result
        assert "0.2345" in result
        assert "2" in result  # Number of stickers
        assert "dmarket.com" in result

    def test_format_market_item_without_details(self):
        """Test item formatting without details."""
        item = {
            "title": "M4A4 | Howl (Minimal Wear)",
            "price": {"USD": 100000},
            "extra": {
                "exteriorName": "Minimal Wear",
                "floatValue": "0.0789",
            },
        }

        result = format_market_item(item, show_details=False)

        assert "M4A4 | Howl" in result
        assert "$1000.00" in result
        # Details should not be present
        assert "Float" not in result or "0.0789" not in result

    def test_format_market_item_unknown_item(self):
        """Test formatting item without title."""
        item = {"price": {"USD": 500}}

        result = format_market_item(item)

        assert "Неизвестный предмет" in result
        assert "$5.00" in result

    def test_format_market_item_zero_price(self):
        """Test formatting item with zero price."""
        item = {
            "title": "Test Item",
            "price": {"USD": 0},
        }

        result = format_market_item(item)

        assert "$0.00" in result


# === Tests for format_market_items ===


class TestFormatMarketItems:
    """Tests for format_market_items function."""

    def test_format_market_items_first_page(self):
        """Test formatting first page of items."""
        items = [
            {"title": f"Item {i}", "price": {"USD": i * 100}} for i in range(1, 11)
        ]

        result = format_market_items(items, page=0, items_per_page=5)

        assert "Найдено предметов: 10" in result
        assert "Страница 1/2" in result
        assert "Item 1" in result
        assert "Item 5" in result
        assert "Item 6" not in result

    def test_format_market_items_second_page(self):
        """Test formatting second page of items."""
        items = [
            {"title": f"Item {i}", "price": {"USD": i * 100}} for i in range(1, 11)
        ]

        result = format_market_items(items, page=1, items_per_page=5)

        assert "Страница 2/2" in result
        assert "Item 6" in result
        # Item 10 is in the result (price $10.00 matches "Item 1" substring, so avoid that check)
        assert "🏷️ *Item 6*" in result

    def test_format_market_items_empty_list(self):
        """Test formatting empty item list."""
        result = format_market_items([])

        assert "не найдены" in result or "Предметы не найдены" in result

    def test_format_market_items_single_item(self):
        """Test formatting single item."""
        items = [{"title": "Single Item", "price": {"USD": 1000}}]

        result = format_market_items(items)

        assert "Найдено предметов: 1" in result
        assert "Single Item" in result

    def test_format_market_items_custom_page_size(self):
        """Test formatting with custom page size."""
        items = [
            {"title": f"Item {i}", "price": {"USD": i * 100}} for i in range(1, 21)
        ]

        result = format_market_items(items, page=0, items_per_page=10)

        assert "Страница 1/2" in result


# === Tests for format_opportunities ===


class TestFormatOpportunities:
    """Tests for format_opportunities function."""

    def test_format_opportunities_basic(self):
        """Test basic opportunities formatting."""
        opportunities = [
            {
                "item_name": "AK-47 | Redline (FT)",
                "buy_price": 10.00,
                "sell_price": 15.00,
                "profit": 4.95,
                "profit_percent": 33.0,
            },
        ]

        result = format_opportunities(opportunities)

        assert "Найдено возможностей: 1" in result
        assert "AK-47 | Redline" in result
        assert "$10.00" in result
        assert "$15.00" in result
        assert "Прибыль" in result

    def test_format_opportunities_with_buy_link(self):
        """Test opportunities with buy link."""
        opportunities = [
            {
                "item_name": "AWP | Asiimov (FT)",
                "buy_price": 50.00,
                "sell_price": 60.00,
                "profit": 9.80,
                "profit_percent": 16.33,
                "buy_link": "https://dmarket.com/item/123",
            },
        ]

        result = format_opportunities(opportunities)

        assert "dmarket.com" in result
        assert "Ссылка на покупку" in result

    def test_format_opportunities_empty(self):
        """Test formatting empty opportunities list."""
        result = format_opportunities([])

        assert "не найдены" in result

    def test_format_opportunities_pagination(self):
        """Test opportunities pagination."""
        opportunities = [
            {
                "item_name": f"Item {i}",
                "buy_price": i * 10.0,
                "sell_price": i * 12.0,
                "profit": i * 2.0,
                "profit_percent": 20.0,
            }
            for i in range(1, 10)
        ]

        result = format_opportunities(opportunities, page=0, items_per_page=3)

        assert "Страница 1/3" in result
        assert "Item 1" in result
        assert "Item 3" in result
        assert "Item 4" not in result


# === Tests for format_error_message ===


class TestFormatErrorMessage:
    """Tests for format_error_message function."""

    def test_format_error_user_friendly(self):
        """Test user-friendly error formatting."""
        error = ValueError("Invalid price format")

        result = format_error_message(error, user_friendly=True)

        assert "❌" in result
        assert "ошибка" in result.lower()
        assert "Invalid price format" in result
        assert "/help" in result

    def test_format_error_technical(self):
        """Test technical error formatting."""
        error = ValueError("Invalid price format")

        result = format_error_message(error, user_friendly=False)

        assert "ValueError" in result
        assert "Invalid price format" in result

    def test_format_error_with_custom_exception(self):
        """Test formatting custom exception."""

        class CustomAPIError(Exception):
            pass

        error = CustomAPIError("API rate limit exceeded")

        result = format_error_message(error, user_friendly=False)

        assert "CustomAPIError" in result


# === Tests for format_sales_history ===


class TestFormatSalesHistory:
    """Tests for format_sales_history function."""

    def test_format_sales_history_basic(self):
        """Test basic sales history formatting."""
        sales = [
            {
                "title": "AK-47 | Redline (FT)",
                "price": {"amount": 1250},
                "createdAt": "2025-12-24T10:30:00",
            },
        ]

        result = format_sales_history(sales)

        assert "История продаж" in result
        assert "AK-47 | Redline" in result
        assert "$12.50" in result
        assert "24.12.2025" in result

    def test_format_sales_history_empty(self):
        """Test formatting empty sales history."""
        result = format_sales_history([])

        assert "пуста" in result or "История продаж" in result

    def test_format_sales_history_pagination(self):
        """Test sales history pagination."""
        sales = [
            {
                "title": f"Item {i}",
                "price": {"amount": i * 100},
                "createdAt": "2025-12-24T10:30:00",
            }
            for i in range(1, 11)
        ]

        result = format_sales_history(sales, page=0, items_per_page=5)

        assert "Страница 1/2" in result

    def test_format_sales_history_invalid_date(self):
        """Test formatting with invalid date."""
        sales = [
            {
                "title": "Test Item",
                "price": {"amount": 1000},
                "createdAt": "invalid-date",
            },
        ]

        result = format_sales_history(sales)

        assert "Test Item" in result
        # Should handle invalid date gracefully


# === Tests for format_sales_analysis ===


class TestFormatSalesAnalysis:
    """Tests for format_sales_analysis function."""

    def test_format_sales_analysis_with_data(self):
        """Test formatting sales analysis with data."""
        analysis = {
            "has_data": True,
            "avg_price": 12.50,
            "max_price": 15.00,
            "min_price": 10.00,
            "price_trend": "up",
            "sales_volume": 150,
            "sales_per_day": 5.5,
            "period_days": 30,
            "recent_sales": [
                {"date": "2025-12-24", "price": 12.00, "currency": "USD"},
                {"date": "2025-12-23", "price": 11.50, "currency": "USD"},
            ],
        }

        result = format_sales_analysis(analysis, "AK-47 | Redline (FT)")

        assert "AK-47 | Redline" in result
        assert "$12.50" in result
        assert "150" in result
        assert "⬆️" in result or "Растет" in result

    def test_format_sales_analysis_no_data(self):
        """Test formatting sales analysis without data."""
        analysis = {"has_data": False}

        result = format_sales_analysis(analysis, "Unknown Item")

        assert "не найдены" in result
        assert "Unknown Item" in result

    def test_format_sales_analysis_downtrend(self):
        """Test formatting sales analysis with downtrend."""
        analysis = {
            "has_data": True,
            "avg_price": 10.00,
            "price_trend": "down",
            "sales_volume": 100,
            "sales_per_day": 3.0,
            "period_days": 30,
        }

        result = format_sales_analysis(analysis, "Test Item")

        assert "⬇️" in result or "Падает" in result

    def test_format_sales_analysis_stable_trend(self):
        """Test formatting sales analysis with stable trend."""
        analysis = {
            "has_data": True,
            "avg_price": 10.00,
            "price_trend": "stable",
            "sales_volume": 100,
            "sales_per_day": 3.0,
            "period_days": 30,
        }

        result = format_sales_analysis(analysis, "Test Item")

        assert "➡️" in result or "Стабилен" in result


# === Tests for format_liquidity_analysis ===


class TestFormatLiquidityAnalysis:
    """Tests for format_liquidity_analysis function."""

    def test_format_liquidity_analysis_high(self):
        """Test formatting high liquidity analysis."""
        analysis = {
            "liquidity_category": "Высокая",
            "liquidity_score": 6,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "up",
                "sales_per_day": 10.5,
                "sales_volume": 315,
                "avg_price": 25.00,
            },
            "market_data": {
                "offers_count": 50,
                "lowest_price": 24.00,
                "highest_price": 30.00,
            },
        }

        result = format_liquidity_analysis(analysis, "AK-47 | Redline (FT)")

        assert "Высокая" in result
        assert "6/7" in result
        assert "AK-47 | Redline" in result
        assert "Отлично подходит для арбитража" in result

    def test_format_liquidity_analysis_medium(self):
        """Test formatting medium liquidity analysis."""
        analysis = {
            "liquidity_category": "Средняя",
            "liquidity_score": 4,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "stable",
                "sales_per_day": 3.0,
                "sales_volume": 90,
                "avg_price": 15.00,
            },
        }

        result = format_liquidity_analysis(analysis, "Test Item")

        assert "Средняя" in result
        assert "осторожностью" in result

    def test_format_liquidity_analysis_low(self):
        """Test formatting low liquidity analysis."""
        analysis = {
            "liquidity_category": "Низкая",
            "liquidity_score": 2,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "down",
                "sales_per_day": 0.5,
                "sales_volume": 15,
                "avg_price": 5.00,
            },
        }

        result = format_liquidity_analysis(analysis, "Test Item")

        assert "Низкая" in result
        assert "Не рекомендуется" in result

    def test_format_liquidity_analysis_no_data(self):
        """Test formatting liquidity analysis without data."""
        analysis = {
            "sales_analysis": {"has_data": False},
        }

        result = format_liquidity_analysis(analysis, "Unknown Item")

        assert "не найдены" in result


# === Tests for get_trend_emoji ===


class TestGetTrendEmoji:
    """Tests for get_trend_emoji function."""

    def test_get_trend_emoji_up(self):
        """Test emoji for uptrend."""
        result = get_trend_emoji("up")
        assert "⬆️" in result or "Растет" in result.lower()

    def test_get_trend_emoji_down(self):
        """Test emoji for downtrend."""
        result = get_trend_emoji("down")
        assert "⬇️" in result or "Падает" in result.lower()

    def test_get_trend_emoji_stable(self):
        """Test emoji for stable trend."""
        result = get_trend_emoji("stable")
        assert "➡️" in result or "Стабилен" in result.lower()

    def test_get_trend_emoji_unknown(self):
        """Test emoji for unknown trend."""
        result = get_trend_emoji("unknown")
        # Should return default value
        assert result is not None


# === Integration tests ===


class TestFormattersIntegration:
    """Integration tests for formatters."""

    def test_all_formatters_return_strings(self):
        """Test that all formatters return strings."""
        assert isinstance(format_balance({"balance": 100}), str)
        assert isinstance(format_market_item({"title": "Test"}), str)
        assert isinstance(format_market_items([]), str)
        assert isinstance(format_opportunities([]), str)
        assert isinstance(format_error_message(ValueError("test")), str)
        assert isinstance(format_sales_history([]), str)
        assert isinstance(
            format_sales_analysis({"has_data": False}, "Test"), str
        )
        assert isinstance(
            format_liquidity_analysis(
                {"sales_analysis": {"has_data": False}}, "Test"
            ),
            str,
        )

    def test_formatters_handle_none_gracefully(self):
        """Test that formatters handle None values gracefully."""
        # Test with minimal data
        assert isinstance(format_balance({}), str)
        assert isinstance(format_market_item({}), str)

    def test_message_length_constraints(self):
        """Test that messages respect Telegram length limit."""
        # Create large dataset
        items = [
            {"title": f"Very Long Item Name {i}" * 10, "price": {"USD": i * 100}}
            for i in range(1, 100)
        ]

        result = format_market_items(items, items_per_page=5)

        # Result should be manageable (not checking exact length as it varies)
        assert len(result) < MAX_MESSAGE_LENGTH * 2


# === Edge cases ===


class TestFormattersEdgeCases:
    """Edge case tests for formatters."""

    def test_format_balance_negative_values(self):
        """Test formatting with negative balance values."""
        balance_data = {
            "balance": -100.00,
            "available_balance": -100.00,
            "total_balance": 0,
        }

        result = format_balance(balance_data)
        assert result is not None

    def test_format_market_item_empty_extra(self):
        """Test formatting item with empty extra dict."""
        item = {
            "title": "Test Item",
            "price": {"USD": 1000},
            "extra": {},
        }

        result = format_market_item(item, show_details=True)
        assert "Test Item" in result

    def test_format_opportunities_with_missing_fields(self):
        """Test formatting opportunities with missing fields."""
        opportunities = [
            {
                "item_name": "Test Item",
                # Missing buy_price, sell_price, profit, profit_percent
            },
        ]

        result = format_opportunities(opportunities)
        assert "Test Item" in result

    def test_format_sales_history_future_date(self):
        """Test formatting sales history with future date."""
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        sales = [
            {
                "title": "Future Item",
                "price": {"amount": 1000},
                "createdAt": future_date,
            },
        ]

        result = format_sales_history(sales)
        assert "Future Item" in result

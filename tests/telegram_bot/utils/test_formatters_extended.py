"""Extended tests for the formatters module.

This module provides comprehensive tests for all formatting functions
in the Telegram bot formatters module.
"""


from src.telegram_bot.utils.formatters import (
    MAX_MESSAGE_LENGTH,
    format_arbitrage_with_sales,
    format_balance,
    format_best_opportunities,
    format_dmarket_results,
    format_error_message,
    format_liquidity_analysis,
    format_market_item,
    format_market_items,
    format_opportunities,
    format_sales_analysis,
    format_sales_history,
    format_sales_volume_stats,
    get_trend_emoji,
    split_long_message,
)


# === Tests for format_balance ===


class TestFormatBalance:
    """Tests for format_balance function."""

    def test_format_balance_with_all_fields(self):
        """Test formatting with all balance fields."""
        balance_data = {
            "balance": 10000,
            "available_balance": 8000,
            "total_balance": 10000,
        }
        result = format_balance(balance_data)
        assert "💰" in result
        assert "$8000.00" in result or "$8,000.00" in result
        assert "$10000.00" in result or "$10,000.00" in result

    def test_format_balance_with_error(self):
        """Test formatting with error."""
        balance_data = {
            "error": True,
            "error_message": "API connection failed",
        }
        result = format_balance(balance_data)
        assert "❌" in result
        assert "API connection failed" in result

    def test_format_balance_with_blocked_amount(self):
        """Test formatting when some balance is blocked."""
        balance_data = {
            "balance": 5000,
            "available_balance": 3000,
            "total_balance": 5000,
        }
        result = format_balance(balance_data)
        assert "🔒" in result or "Заблокировано" in result

    def test_format_balance_low_balance_warning(self):
        """Test low balance warning."""
        balance_data = {
            "balance": 0.5,
            "available_balance": 0.5,
            "total_balance": 0.5,
        }
        result = format_balance(balance_data)
        assert "⚠️" in result

    def test_format_balance_empty_data(self):
        """Test with empty data."""
        result = format_balance({})
        assert result is not None
        assert isinstance(result, str)

    def test_format_balance_zero_balance(self):
        """Test with zero balance."""
        balance_data = {
            "balance": 0,
            "available_balance": 0,
            "total_balance": 0,
        }
        result = format_balance(balance_data)
        assert "$0.00" in result


# === Tests for format_market_item ===


class TestFormatMarketItem:
    """Tests for format_market_item function."""

    def test_format_market_item_basic(self):
        """Test basic formatting."""
        item = {
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"USD": 1234},
        }
        result = format_market_item(item)
        assert "AK-47" in result
        assert "$12.34" in result

    def test_format_market_item_with_details(self):
        """Test formatting with details."""
        item = {
            "title": "AWP | Dragon Lore (FT)",
            "price": {"USD": 150000},
            "extra": {
                "exteriorName": "Field-Tested",
                "floatValue": 0.25,
                "stickers": [{"name": "Sticker 1"}, {"name": "Sticker 2"}],
            },
            "itemId": "item_123",
        }
        result = format_market_item(item, show_details=True)
        assert "AWP" in result
        assert "Field-Tested" in result
        assert "0.25" in result
        assert "2" in result  # sticker count
        assert "DMarket" in result  # link

    def test_format_market_item_without_details(self):
        """Test formatting without details."""
        item = {
            "title": "M4A4 | Howl",
            "price": {"USD": 200000},
            "extra": {
                "exteriorName": "Minimal Wear",
            },
        }
        result = format_market_item(item, show_details=False)
        assert "M4A4" in result
        # Details should not be included
        assert "Minimal Wear" not in result

    def test_format_market_item_empty(self):
        """Test with empty item."""
        result = format_market_item({})
        assert "Неизвестный предмет" in result

    def test_format_market_item_zero_price(self):
        """Test with zero price."""
        item = {"title": "Test Item", "price": {"USD": 0}}
        result = format_market_item(item)
        assert "$0.00" in result


# === Tests for format_market_items ===


class TestFormatMarketItems:
    """Tests for format_market_items function."""

    def test_format_market_items_multiple(self):
        """Test formatting multiple items."""
        items = [
            {"title": f"Item {i}", "price": {"USD": i * 100}}
            for i in range(1, 6)
        ]
        result = format_market_items(items)
        assert "5" in result  # count
        assert "Item 1" in result

    def test_format_market_items_empty(self):
        """Test with empty list."""
        result = format_market_items([])
        assert "не найдены" in result

    def test_format_market_items_pagination(self):
        """Test pagination."""
        items = [{"title": f"Item {i}", "price": {"USD": i * 100}} for i in range(1, 20)]

        result_page1 = format_market_items(items, page=0, items_per_page=5)
        result_page2 = format_market_items(items, page=1, items_per_page=5)

        assert "Item 1" in result_page1
        assert "Item 6" in result_page2

    def test_format_market_items_last_page(self):
        """Test last page with fewer items."""
        items = [{"title": f"Item {i}", "price": {"USD": 100}} for i in range(1, 8)]
        result = format_market_items(items, page=1, items_per_page=5)
        assert "Item 6" in result


# === Tests for format_opportunities ===


class TestFormatOpportunities:
    """Tests for format_opportunities function."""

    def test_format_opportunities_basic(self):
        """Test basic opportunities formatting."""
        opportunities = [
            {
                "item_name": "Test Item",
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit": 5.0,
                "profit_percent": 50.0,
            }
        ]
        result = format_opportunities(opportunities)
        assert "Test Item" in result
        assert "$10.00" in result
        assert "$15.00" in result

    def test_format_opportunities_with_link(self):
        """Test opportunities with buy link."""
        opportunities = [
            {
                "item_name": "Item with Link",
                "buy_price": 20.0,
                "sell_price": 25.0,
                "profit": 5.0,
                "profit_percent": 25.0,
                "buy_link": "https://dmarket.com/item/123",
            }
        ]
        result = format_opportunities(opportunities)
        assert "dmarket.com" in result

    def test_format_opportunities_empty(self):
        """Test with empty list."""
        result = format_opportunities([])
        assert "не найдены" in result

    def test_format_opportunities_pagination(self):
        """Test pagination."""
        opportunities = [
            {
                "item_name": f"Item {i}",
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit": 5.0,
                "profit_percent": 50.0,
            }
            for i in range(1, 10)
        ]
        result = format_opportunities(opportunities, page=0, items_per_page=3)
        assert "9" in result  # total count


# === Tests for format_error_message ===


class TestFormatErrorMessage:
    """Tests for format_error_message function."""

    def test_format_error_message_user_friendly(self):
        """Test user-friendly error message."""
        error = ValueError("Invalid price value")
        result = format_error_message(error, user_friendly=True)
        assert "❌" in result
        assert "Invalid price value" in result
        assert "/help" in result

    def test_format_error_message_technical(self):
        """Test technical error message."""
        error = KeyError("missing_key")
        result = format_error_message(error, user_friendly=False)
        assert "KeyError" in result
        assert "missing_key" in result

    def test_format_error_message_with_exception_types(self):
        """Test with different exception types."""
        exceptions = [
            ValueError("value error"),
            TypeError("type error"),
            RuntimeError("runtime error"),
        ]
        for exc in exceptions:
            result = format_error_message(exc)
            assert "❌" in result


# === Tests for format_sales_history ===


class TestFormatSalesHistory:
    """Tests for format_sales_history function."""

    def test_format_sales_history_basic(self):
        """Test basic sales history formatting."""
        sales = [
            {
                "title": "AK-47 | Redline",
                "price": {"amount": 1200},
                "createdAt": "2025-01-01T12:00:00",
            }
        ]
        result = format_sales_history(sales)
        assert "AK-47" in result
        assert "$12.00" in result
        assert "2025" in result or "01.01" in result

    def test_format_sales_history_empty(self):
        """Test with empty list."""
        result = format_sales_history([])
        assert "пуста" in result

    def test_format_sales_history_invalid_date(self):
        """Test with invalid date format."""
        sales = [
            {
                "title": "Test Item",
                "price": {"amount": 100},
                "createdAt": "invalid-date",
            }
        ]
        result = format_sales_history(sales)
        assert result is not None

    def test_format_sales_history_pagination(self):
        """Test pagination."""
        sales = [
            {"title": f"Item {i}", "price": {"amount": 100}, "createdAt": ""}
            for i in range(10)
        ]
        result = format_sales_history(sales, page=0, items_per_page=5)
        assert "Страница 1/" in result


# === Tests for format_sales_analysis ===


class TestFormatSalesAnalysis:
    """Tests for format_sales_analysis function."""

    def test_format_sales_analysis_with_data(self):
        """Test with sales data."""
        analysis = {
            "has_data": True,
            "avg_price": 15.50,
            "max_price": 20.00,
            "min_price": 10.00,
            "price_trend": "up",
            "sales_volume": 100,
            "sales_per_day": 5.0,
            "period_days": 30,
            "recent_sales": [
                {"date": "2025-01-01", "price": 15.0, "currency": "USD"}
            ],
        }
        result = format_sales_analysis(analysis, "Test Item")
        assert "Test Item" in result
        assert "$15.50" in result
        assert "⬆️" in result or "Растет" in result

    def test_format_sales_analysis_no_data(self):
        """Test with no data."""
        analysis = {"has_data": False}
        result = format_sales_analysis(analysis, "Unknown Item")
        assert "не найдены" in result
        assert "Unknown Item" in result

    def test_format_sales_analysis_trends(self):
        """Test different trends."""
        for trend, expected in [("up", "⬆️"), ("down", "⬇️"), ("stable", "➡️")]:
            analysis = {
                "has_data": True,
                "price_trend": trend,
                "avg_price": 10.0,
                "max_price": 15.0,
                "min_price": 5.0,
                "sales_volume": 50,
                "sales_per_day": 2.5,
                "period_days": 7,
            }
            result = format_sales_analysis(analysis, "Test")
            assert expected in result


# === Tests for format_liquidity_analysis ===


class TestFormatLiquidityAnalysis:
    """Tests for format_liquidity_analysis function."""

    def test_format_liquidity_analysis_high(self):
        """Test high liquidity formatting."""
        analysis = {
            "liquidity_category": "Очень высокая",
            "liquidity_score": 7,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "stable",
                "sales_per_day": 50.0,
                "sales_volume": 500,
                "avg_price": 25.0,
            },
            "market_data": {
                "offers_count": 100,
                "lowest_price": 20.0,
                "highest_price": 30.0,
            },
        }
        result = format_liquidity_analysis(analysis, "Popular Item")
        assert "Popular Item" in result
        assert "💧💧💧💧" in result
        assert "арбитража" in result

    def test_format_liquidity_analysis_low(self):
        """Test low liquidity formatting."""
        analysis = {
            "liquidity_category": "Низкая",
            "liquidity_score": 2,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "down",
                "sales_per_day": 0.5,
                "sales_volume": 5,
                "avg_price": 100.0,
            },
        }
        result = format_liquidity_analysis(analysis, "Rare Item")
        assert "💧" in result
        assert "❌" in result or "Не рекомендуется" in result

    def test_format_liquidity_analysis_no_data(self):
        """Test with no sales data."""
        analysis = {
            "sales_analysis": {"has_data": False},
        }
        result = format_liquidity_analysis(analysis, "Unknown")
        assert "не найдены" in result


# === Tests for get_trend_emoji ===


class TestGetTrendEmoji:
    """Tests for get_trend_emoji function."""

    def test_get_trend_emoji_up(self):
        """Test uptrend emoji."""
        result = get_trend_emoji("up")
        assert "⬆️" in result
        assert "Растет" in result

    def test_get_trend_emoji_down(self):
        """Test downtrend emoji."""
        result = get_trend_emoji("down")
        assert "⬇️" in result
        assert "Падает" in result

    def test_get_trend_emoji_stable(self):
        """Test stable trend emoji."""
        result = get_trend_emoji("stable")
        assert "➡️" in result
        assert "Стабилен" in result

    def test_get_trend_emoji_unknown(self):
        """Test unknown trend returns stable."""
        result = get_trend_emoji("unknown")
        assert "➡️" in result


# === Tests for format_sales_volume_stats ===


class TestFormatSalesVolumeStats:
    """Tests for format_sales_volume_stats function."""

    def test_format_sales_volume_stats_csgo(self):
        """Test formatting for CS:GO."""
        stats = {
            "items": [
                {
                    "item_name": "AK-47 | Redline",
                    "sales_per_day": 50.0,
                    "avg_price": 15.0,
                    "price_trend": "up",
                }
            ],
            "count": 100,
            "summary": {
                "up_trend_count": 40,
                "down_trend_count": 30,
                "stable_trend_count": 30,
            },
        }
        result = format_sales_volume_stats(stats, "csgo")
        assert "CS2" in result
        assert "AK-47" in result

    def test_format_sales_volume_stats_empty(self):
        """Test with empty items."""
        stats = {"items": [], "count": 0, "summary": {}}
        result = format_sales_volume_stats(stats, "dota2")
        assert "не найдена" in result

    def test_format_sales_volume_stats_games(self):
        """Test different game names."""
        stats = {"items": [{"item_name": "Test", "sales_per_day": 10, "avg_price": 5, "price_trend": "stable"}], "count": 1, "summary": {}}

        for game, display in [("csgo", "CS2"), ("dota2", "Dota 2"), ("tf2", "Team Fortress 2"), ("rust", "Rust")]:
            result = format_sales_volume_stats(stats, game)
            assert display in result


# === Tests for format_arbitrage_with_sales ===


class TestFormatArbitrageWithSales:
    """Tests for format_arbitrage_with_sales function."""

    def test_format_arbitrage_with_sales_basic(self):
        """Test basic formatting."""
        results = {
            "opportunities": [
                {
                    "market_hash_name": "Test Item",
                    "profit": 5.0,
                    "profit_percent": 25.0,
                    "buy_price": 20.0,
                    "sell_price": 25.0,
                    "sales_analysis": {
                        "price_trend": "up",
                        "sales_per_day": 10.0,
                    },
                }
            ],
            "filters": {"time_period_days": 7},
        }
        result = format_arbitrage_with_sales(results, "csgo")
        assert "Test Item" in result
        assert "$5.00" in result

    def test_format_arbitrage_with_sales_empty(self):
        """Test with empty opportunities."""
        results = {"opportunities": []}
        result = format_arbitrage_with_sales(results, "csgo")
        assert "не найдены" in result

    def test_format_arbitrage_with_sales_many(self):
        """Test with more than 5 opportunities."""
        results = {
            "opportunities": [
                {
                    "market_hash_name": f"Item {i}",
                    "profit": i * 1.0,
                    "profit_percent": i * 5.0,
                    "buy_price": 10.0,
                    "sell_price": 10.0 + i,
                    "sales_analysis": {"price_trend": "stable", "sales_per_day": 5.0},
                }
                for i in range(1, 10)
            ],
            "filters": {},
        }
        result = format_arbitrage_with_sales(results, "csgo")
        assert "5 из 9" in result


# === Tests for format_dmarket_results ===


class TestFormatDmarketResults:
    """Tests for format_dmarket_results function."""

    def test_format_dmarket_results_market_items(self):
        """Test market items result type."""
        results = {
            "objects": [
                {"title": "Item 1", "price": {"USD": 1000}},
                {"title": "Item 2", "price": {"USD": 2000}},
            ],
            "total": {"items": 50},
        }
        result = format_dmarket_results(results, "market_items")
        assert "Item 1" in result
        assert "50" in result

    def test_format_dmarket_results_empty(self):
        """Test with empty results."""
        result = format_dmarket_results({})
        assert "не найдены" in result

    def test_format_dmarket_results_balance(self):
        """Test balance result type."""
        results = {"balance": 100, "available_balance": 100, "total_balance": 100}
        result = format_dmarket_results(results, "balance")
        assert "$100.00" in result

    def test_format_dmarket_results_unknown_type(self):
        """Test unknown result type."""
        result = format_dmarket_results({"data": "test"}, "unknown_type")
        assert "Неизвестный" in result


# === Tests for format_best_opportunities ===


class TestFormatBestOpportunities:
    """Tests for format_best_opportunities function."""

    def test_format_best_opportunities_basic(self):
        """Test basic formatting."""
        opportunities = [
            {
                "item_name": "Best Item",
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit": 5.0,
                "profit_percent": 50.0,
            }
        ]
        result = format_best_opportunities(opportunities)
        assert "Best Item" in result
        assert "🏆" in result

    def test_format_best_opportunities_with_liquidity(self):
        """Test with liquidity info."""
        opportunities = [
            {
                "item_name": "Liquid Item",
                "buy_price": 20.0,
                "sell_price": 30.0,
                "profit": 10.0,
                "profit_percent": 50.0,
                "sales_per_day": 25.5,
            }
        ]
        result = format_best_opportunities(opportunities)
        assert "25.5" in result or "25.50" in result

    def test_format_best_opportunities_empty(self):
        """Test with empty list."""
        result = format_best_opportunities([])
        assert "не найдены" in result

    def test_format_best_opportunities_limit(self):
        """Test limit parameter."""
        opportunities = [
            {"item_name": f"Item {i}", "buy_price": 10, "sell_price": 15, "profit": 5, "profit_percent": 50}
            for i in range(20)
        ]
        result = format_best_opportunities(opportunities, limit=5)
        assert "Топ-5" in result


# === Tests for split_long_message ===


class TestSplitLongMessage:
    """Tests for split_long_message function."""

    def test_split_long_message_short(self):
        """Test short message is not split."""
        message = "This is a short message"
        result = split_long_message(message)
        assert len(result) == 1
        assert result[0] == message

    def test_split_long_message_long(self):
        """Test long message is split."""
        # Create a message longer than MAX_MESSAGE_LENGTH
        line = "A" * 100 + "\n"
        message = line * 50  # 5050 chars
        result = split_long_message(message, max_length=1000)
        assert len(result) > 1

    def test_split_long_message_preserves_content(self):
        """Test splitting preserves content."""
        lines = [f"Line {i}" for i in range(100)]
        message = "\n".join(lines)
        result = split_long_message(message, max_length=500)
        combined = "".join(result)
        for i in range(100):
            assert f"Line {i}" in combined

    def test_split_long_message_respects_newlines(self):
        """Test splitting respects newlines."""
        message = "Line 1\nLine 2\nLine 3"
        result = split_long_message(message, max_length=100)
        assert len(result) == 1
        assert "Line 1" in result[0]

    def test_split_long_message_empty(self):
        """Test with empty message."""
        result = split_long_message("")
        assert result == [""]


# === Tests for MAX_MESSAGE_LENGTH ===


class TestConstant:
    """Tests for module constants."""

    def test_max_message_length_value(self):
        """Test MAX_MESSAGE_LENGTH is set correctly."""
        assert MAX_MESSAGE_LENGTH == 4096


# === Integration Tests ===


class TestFormattersIntegration:
    """Integration tests for formatters."""

    def test_all_formatters_handle_none_gracefully(self):
        """Test that formatters handle None inputs gracefully."""
        # These should not raise exceptions
        format_balance({})
        format_market_item({})
        format_market_items([])
        format_opportunities([])
        format_error_message(ValueError("test"))
        format_sales_history([])
        format_sales_analysis({"has_data": False}, "Test")
        format_liquidity_analysis({"sales_analysis": {"has_data": False}}, "Test")
        format_sales_volume_stats({"items": []}, "csgo")
        format_arbitrage_with_sales({"opportunities": []}, "csgo")
        format_dmarket_results({})
        format_best_opportunities([])
        split_long_message("")

    def test_all_formatters_return_strings(self):
        """Test that all formatters return strings."""
        assert isinstance(format_balance({}), str)
        assert isinstance(format_market_item({}), str)
        assert isinstance(format_market_items([]), str)
        assert isinstance(format_opportunities([]), str)
        assert isinstance(format_error_message(ValueError("")), str)
        assert isinstance(format_sales_history([]), str)
        assert isinstance(get_trend_emoji("up"), str)
        assert isinstance(split_long_message("test"), list)

    def test_formatters_with_unicode(self):
        """Test formatters handle unicode properly."""
        item = {"title": "АК-47 | Красная линия", "price": {"USD": 1000}}
        result = format_market_item(item)
        assert "АК-47" in result

    def test_formatters_with_special_chars(self):
        """Test formatters handle special characters."""
        item = {"title": "Test <> & \" ' Item", "price": {"USD": 500}}
        result = format_market_item(item)
        assert "Test" in result

    def test_formatter_output_length(self):
        """Test that formatted output doesn't exceed reasonable length."""
        # Test with large data
        items = [{"title": f"Item {i}", "price": {"USD": i * 100}} for i in range(100)]
        result = format_market_items(items, page=0, items_per_page=5)
        assert len(result) < MAX_MESSAGE_LENGTH * 2  # Reasonable limit


# === Edge Case Tests ===


class TestEdgeCases:
    """Edge case tests for formatters."""

    def test_format_balance_negative_values(self):
        """Test with negative balance values."""
        balance_data = {
            "balance": -100,
            "available_balance": -100,
            "total_balance": -100,
        }
        result = format_balance(balance_data)
        # Should handle negative values without crashing
        assert result is not None

    def test_format_market_item_very_high_price(self):
        """Test with very high price."""
        item = {
            "title": "Expensive Item",
            "price": {"USD": 999999999},
        }
        result = format_market_item(item)
        assert "Expensive Item" in result

    def test_format_opportunities_zero_profit(self):
        """Test with zero profit opportunities."""
        opportunities = [
            {
                "item_name": "Zero Profit",
                "buy_price": 10.0,
                "sell_price": 10.0,
                "profit": 0.0,
                "profit_percent": 0.0,
            }
        ]
        result = format_opportunities(opportunities)
        assert "0.00" in result

    def test_format_sales_history_missing_fields(self):
        """Test with missing fields in sales data."""
        sales = [
            {"title": "Item"},  # Missing price and date
        ]
        result = format_sales_history(sales)
        assert result is not None

    def test_split_long_message_single_long_line(self):
        """Test with single very long line."""
        message = "A" * 10000
        result = split_long_message(message, max_length=1000)
        # Should handle gracefully even if can't split on newlines
        assert len(result) >= 1

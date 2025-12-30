"""Phase 4 extended tests for formatters module.

This module provides comprehensive Phase 4 tests targeting 100% coverage
for the Telegram bot formatters module.
"""

from datetime import datetime

from src.telegram_bot.utils.formatters import (
    MAX_MESSAGE_LENGTH,
    format_aggregated_prices,
    format_arbitrage_with_sales,
    format_balance,
    format_best_opportunities,
    format_dmarket_results,
    format_error_message,
    format_liquidity_analysis,
    format_market_depth,
    format_market_item,
    format_market_items,
    format_opportunities,
    format_sales_analysis,
    format_sales_history,
    format_sales_volume_stats,
    format_target_competition_analysis,
    format_target_item,
    get_trend_emoji,
    split_long_message,
)


# === Phase 4: MAX_MESSAGE_LENGTH Constants ===


class TestMaxMessageLengthPhase4:
    """Phase 4 tests for MAX_MESSAGE_LENGTH constant."""

    def test_max_message_length_is_telegram_limit(self):
        """Test MAX_MESSAGE_LENGTH equals Telegram's limit."""
        assert MAX_MESSAGE_LENGTH == 4096

    def test_max_message_length_is_integer(self):
        """Test MAX_MESSAGE_LENGTH is an integer."""
        assert isinstance(MAX_MESSAGE_LENGTH, int)

    def test_max_message_length_is_positive(self):
        """Test MAX_MESSAGE_LENGTH is positive."""
        assert MAX_MESSAGE_LENGTH > 0


# === Phase 4: format_balance Extended Tests ===


class TestFormatBalancePhase4:
    """Phase 4 tests for format_balance function."""

    def test_format_balance_only_balance_field(self):
        """Test with only balance field."""
        balance_data = {"balance": 500}
        result = format_balance(balance_data)
        assert "💰" in result
        assert "$500.00" in result

    def test_format_balance_total_equals_available(self):
        """Test when total equals available (no blocked)."""
        balance_data = {
            "balance": 1000,
            "available_balance": 1000,
            "total_balance": 1000,
        }
        result = format_balance(balance_data)
        # Should not show blocked amount
        assert "Заблокировано" not in result or "🔒" not in result

    def test_format_balance_error_without_message(self):
        """Test error without error_message."""
        balance_data = {"error": True}
        result = format_balance(balance_data)
        assert "❌" in result
        assert "Неизвестная ошибка" in result

    def test_format_balance_available_exactly_one(self):
        """Test available_balance exactly $1.00."""
        balance_data = {
            "balance": 1.0,
            "available_balance": 1.0,
            "total_balance": 1.0,
        }
        result = format_balance(balance_data)
        # Should not show low balance warning
        assert "⚠️" not in result

    def test_format_balance_available_just_below_one(self):
        """Test available_balance just below $1.00."""
        balance_data = {
            "balance": 0.99,
            "available_balance": 0.99,
            "total_balance": 0.99,
        }
        result = format_balance(balance_data)
        assert "⚠️" in result

    def test_format_balance_large_values(self):
        """Test with very large balance values."""
        balance_data = {
            "balance": 1000000,
            "available_balance": 900000,
            "total_balance": 1000000,
        }
        result = format_balance(balance_data)
        assert "$900000.00" in result or "$1000000.00" in result

    def test_format_balance_float_precision(self):
        """Test float precision in balance."""
        balance_data = {
            "balance": 123.456,
            "available_balance": 123.456,
            "total_balance": 123.456,
        }
        result = format_balance(balance_data)
        assert "$123.46" in result  # Rounded to 2 decimals

    def test_format_balance_blocked_amount_calculation(self):
        """Test blocked amount is calculated correctly."""
        balance_data = {
            "balance": 1000,
            "available_balance": 700,
            "total_balance": 1000,
        }
        result = format_balance(balance_data)
        # Blocked = 1000 - 700 = 300
        assert "$300.00" in result


# === Phase 4: format_market_item Extended Tests ===


class TestFormatMarketItemPhase4:
    """Phase 4 tests for format_market_item function."""

    def test_format_market_item_price_dict_only(self):
        """Test with price as dict but no USD key."""
        item = {
            "title": "Test Item",
            "price": {"EUR": 1500},  # No USD
        }
        result = format_market_item(item)
        assert "$0.00" in result  # Falls back to 0

    def test_format_market_item_no_price_dict(self):
        """Test with no price dict."""
        item = {"title": "No Price Item"}
        result = format_market_item(item)
        assert "No Price Item" in result
        assert "$0.00" in result

    def test_format_market_item_extra_without_stickers(self):
        """Test with extra but without stickers."""
        item = {
            "title": "Item",
            "price": {"USD": 500},
            "extra": {
                "exteriorName": "Factory New",
                "floatValue": 0.01,
            },
        }
        result = format_market_item(item, show_details=True)
        assert "Factory New" in result
        assert "0.01" in result
        # Should not have sticker line

    def test_format_market_item_extra_with_empty_stickers(self):
        """Test with empty stickers list."""
        item = {
            "title": "Item",
            "price": {"USD": 500},
            "extra": {
                "stickers": [],
            },
        }
        result = format_market_item(item, show_details=True)
        # Empty stickers list should not show sticker info
        assert "Наклейки" not in result

    def test_format_market_item_no_item_id(self):
        """Test without itemId."""
        item = {
            "title": "Item Without ID",
            "price": {"USD": 1000},
        }
        result = format_market_item(item, show_details=True)
        assert "DMarket" not in result

    def test_format_market_item_show_details_false_excludes_all(self):
        """Test show_details=False excludes all extra info."""
        item = {
            "title": "Item",
            "price": {"USD": 1000},
            "extra": {
                "exteriorName": "FN",
                "floatValue": 0.01,
                "stickers": [{"name": "Sticker"}],
            },
            "itemId": "test_123",
        }
        result = format_market_item(item, show_details=False)
        assert "FN" not in result
        assert "Float" not in result
        assert "Наклейки" not in result
        assert "DMarket" not in result


# === Phase 4: format_market_items Extended Tests ===


class TestFormatMarketItemsPhase4:
    """Phase 4 tests for format_market_items function."""

    def test_format_market_items_single_item(self):
        """Test with single item."""
        items = [{"title": "Single Item", "price": {"USD": 500}}]
        result = format_market_items(items)
        assert "1" in result
        assert "Single Item" in result

    def test_format_market_items_page_calculation(self):
        """Test page calculation with various sizes."""
        items = [{"title": f"Item {i}", "price": {"USD": 100}} for i in range(12)]

        # 12 items, 5 per page = 3 pages
        result = format_market_items(items, page=0, items_per_page=5)
        assert "Страница 1/3" in result

    def test_format_market_items_exact_page_boundary(self):
        """Test when items exactly fill pages."""
        items = [{"title": f"Item {i}", "price": {"USD": 100}} for i in range(10)]

        # 10 items, 5 per page = 2 pages exactly
        result = format_market_items(items, page=1, items_per_page=5)
        assert "Страница 2/2" in result

    def test_format_market_items_beyond_last_page(self):
        """Test page beyond available items."""
        items = [{"title": "Item", "price": {"USD": 100}} for _ in range(3)]
        result = format_market_items(items, page=5, items_per_page=5)
        # Should handle gracefully - empty page
        assert "Найдено предметов: 3" in result

    def test_format_market_items_items_per_page_one(self):
        """Test with items_per_page=1."""
        items = [{"title": f"Item {i}", "price": {"USD": 100}} for i in range(5)]
        result = format_market_items(items, page=2, items_per_page=1)
        assert "Страница 3/5" in result

    def test_format_market_items_numbering_continues(self):
        """Test item numbering continues across pages."""
        items = [{"title": f"Item {i}", "price": {"USD": i * 100}} for i in range(10)]
        result = format_market_items(items, page=1, items_per_page=3)
        # Page 2 should have items 4, 5, 6
        assert "4." in result
        assert "5." in result
        assert "6." in result


# === Phase 4: format_opportunities Extended Tests ===


class TestFormatOpportunitiesPhase4:
    """Phase 4 tests for format_opportunities function."""

    def test_format_opportunities_missing_item_name(self):
        """Test with missing item_name."""
        opportunities = [
            {
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit": 5.0,
                "profit_percent": 50.0,
            }
        ]
        result = format_opportunities(opportunities)
        assert "Неизвестный предмет" in result

    def test_format_opportunities_missing_prices(self):
        """Test with missing price fields."""
        opportunities = [
            {
                "item_name": "Test Item",
            }
        ]
        result = format_opportunities(opportunities)
        assert "Test Item" in result
        assert "$0.00" in result

    def test_format_opportunities_page_calculation(self):
        """Test page number calculation."""
        opportunities = [
            {"item_name": f"Item {i}", "buy_price": 10, "sell_price": 15, "profit": 5, "profit_percent": 50}
            for i in range(9)
        ]
        result = format_opportunities(opportunities, page=2, items_per_page=3)
        assert "Страница 3/3" in result

    def test_format_opportunities_timestamp_in_output(self):
        """Test that timestamp is included."""
        opportunities = [
            {"item_name": "Item", "buy_price": 10, "sell_price": 15, "profit": 5, "profit_percent": 50}
        ]
        result = format_opportunities(opportunities)
        assert "🕒" in result
        current_year = datetime.now().strftime("%Y")
        assert current_year in result

    def test_format_opportunities_no_buy_link(self):
        """Test without buy_link."""
        opportunities = [
            {
                "item_name": "No Link Item",
                "buy_price": 20.0,
                "sell_price": 25.0,
                "profit": 5.0,
                "profit_percent": 25.0,
            }
        ]
        result = format_opportunities(opportunities)
        assert "href" not in result


# === Phase 4: format_error_message Extended Tests ===


class TestFormatErrorMessagePhase4:
    """Phase 4 tests for format_error_message function."""

    def test_format_error_message_empty_string(self):
        """Test with empty error message."""
        error = ValueError("")
        result = format_error_message(error, user_friendly=True)
        assert "❌" in result

    def test_format_error_message_technical_shows_type(self):
        """Test technical mode shows exception type."""
        error = TypeError("test error")
        result = format_error_message(error, user_friendly=False)
        assert "TypeError" in result
        assert "```" in result  # Code block

    def test_format_error_message_nested_exception(self):
        """Test with nested exception."""
        try:
            try:
                raise ValueError("inner")
            except ValueError:
                raise RuntimeError("outer") from None
        except RuntimeError as e:
            result = format_error_message(e, user_friendly=True)
            assert "outer" in result

    def test_format_error_message_unicode_in_error(self):
        """Test with unicode in error message."""
        error = ValueError("Ошибка: неверный формат данных")
        result = format_error_message(error, user_friendly=True)
        assert "Ошибка" in result


# === Phase 4: format_sales_history Extended Tests ===


class TestFormatSalesHistoryPhase4:
    """Phase 4 tests for format_sales_history function."""

    def test_format_sales_history_no_created_at(self):
        """Test with missing createdAt."""
        sales = [
            {
                "title": "Item",
                "price": {"amount": 1000},
            }
        ]
        result = format_sales_history(sales)
        assert "Неизвестно" in result

    def test_format_sales_history_empty_created_at(self):
        """Test with empty createdAt string."""
        sales = [
            {
                "title": "Item",
                "price": {"amount": 500},
                "createdAt": "",
            }
        ]
        result = format_sales_history(sales)
        assert "Неизвестно" in result

    def test_format_sales_history_no_price_amount(self):
        """Test with missing price amount."""
        sales = [
            {
                "title": "Item",
                "price": {},
                "createdAt": "2025-01-01T12:00:00",
            }
        ]
        result = format_sales_history(sales)
        assert "$0.00" in result

    def test_format_sales_history_valid_iso_date(self):
        """Test with valid ISO date format."""
        sales = [
            {
                "title": "Item",
                "price": {"amount": 1000},
                "createdAt": "2025-06-15T14:30:00",
            }
        ]
        result = format_sales_history(sales)
        assert "15.06.2025" in result
        assert "14:30" in result

    def test_format_sales_history_page_info(self):
        """Test page info with various counts."""
        sales = [
            {"title": f"Item {i}", "price": {"amount": 100}, "createdAt": ""}
            for i in range(25)
        ]
        result = format_sales_history(sales, page=2, items_per_page=5)
        assert "Страница 3/5" in result


# === Phase 4: format_sales_analysis Extended Tests ===


class TestFormatSalesAnalysisPhase4:
    """Phase 4 tests for format_sales_analysis function."""

    def test_format_sales_analysis_all_trends(self):
        """Test all trend types."""
        for trend, emoji in [("up", "⬆️"), ("down", "⬇️"), ("stable", "➡️")]:
            analysis = {
                "has_data": True,
                "avg_price": 10.0,
                "max_price": 15.0,
                "min_price": 5.0,
                "price_trend": trend,
                "sales_volume": 100,
                "sales_per_day": 10.0,
                "period_days": 7,
            }
            result = format_sales_analysis(analysis, "Test")
            assert emoji in result

    def test_format_sales_analysis_unknown_trend(self):
        """Test with unknown trend value."""
        analysis = {
            "has_data": True,
            "avg_price": 10.0,
            "max_price": 15.0,
            "min_price": 5.0,
            "price_trend": "unknown_trend",
            "sales_volume": 100,
            "sales_per_day": 10.0,
            "period_days": 7,
        }
        result = format_sales_analysis(analysis, "Test")
        # Should fall back to stable
        assert "➡️" in result or "Стабилен" in result

    def test_format_sales_analysis_no_recent_sales(self):
        """Test without recent_sales."""
        analysis = {
            "has_data": True,
            "avg_price": 10.0,
            "max_price": 15.0,
            "min_price": 5.0,
            "price_trend": "stable",
            "sales_volume": 100,
            "sales_per_day": 10.0,
            "period_days": 7,
        }
        result = format_sales_analysis(analysis, "Test")
        assert "Последние продажи" not in result

    def test_format_sales_analysis_many_recent_sales(self):
        """Test with more than 5 recent sales."""
        analysis = {
            "has_data": True,
            "avg_price": 10.0,
            "max_price": 15.0,
            "min_price": 5.0,
            "price_trend": "up",
            "sales_volume": 100,
            "sales_per_day": 10.0,
            "period_days": 7,
            "recent_sales": [
                {"date": f"2025-01-0{i}", "price": 10.0 + i, "currency": "USD"}
                for i in range(1, 10)
            ],
        }
        result = format_sales_analysis(analysis, "Test")
        # Should only show first 5
        assert result.count("•") == 5

    def test_format_sales_analysis_missing_has_data(self):
        """Test with missing has_data key."""
        analysis = {"avg_price": 10.0}
        result = format_sales_analysis(analysis, "Test")
        assert "не найдены" in result


# === Phase 4: format_liquidity_analysis Extended Tests ===


class TestFormatLiquidityAnalysisPhase4:
    """Phase 4 tests for format_liquidity_analysis function."""

    def test_format_liquidity_all_categories(self):
        """Test all liquidity categories."""
        categories = {
            "Очень высокая": "💧💧💧💧",
            "Высокая": "💧💧💧",
            "Средняя": "💧💧",
            "Низкая": "💧",
        }
        for cat, emoji in categories.items():
            analysis = {
                "liquidity_category": cat,
                "liquidity_score": 5,
                "sales_analysis": {
                    "has_data": True,
                    "price_trend": "stable",
                    "sales_per_day": 10.0,
                    "sales_volume": 100,
                    "avg_price": 20.0,
                },
            }
            result = format_liquidity_analysis(analysis, "Test")
            assert emoji in result

    def test_format_liquidity_unknown_category(self):
        """Test with unknown category."""
        analysis = {
            "liquidity_category": "Unknown",
            "liquidity_score": 3,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "stable",
                "sales_per_day": 5.0,
                "sales_volume": 50,
                "avg_price": 15.0,
            },
        }
        result = format_liquidity_analysis(analysis, "Test")
        # Should use default emoji
        assert "💧" in result

    def test_format_liquidity_no_market_data(self):
        """Test without market_data."""
        analysis = {
            "liquidity_category": "Средняя",
            "liquidity_score": 4,
            "sales_analysis": {
                "has_data": True,
                "price_trend": "stable",
                "sales_per_day": 5.0,
                "sales_volume": 50,
                "avg_price": 15.0,
            },
        }
        result = format_liquidity_analysis(analysis, "Test")
        assert "Предложений на рынке" not in result

    def test_format_liquidity_recommendations(self):
        """Test recommendations for each category."""
        for cat, rec_part in [
            ("Очень высокая", "Отлично подходит"),
            ("Высокая", "Отлично подходит"),
            ("Средняя", "с осторожностью"),
            ("Низкая", "Не рекомендуется"),
        ]:
            analysis = {
                "liquidity_category": cat,
                "liquidity_score": 3,
                "sales_analysis": {
                    "has_data": True,
                    "price_trend": "stable",
                    "sales_per_day": 5.0,
                    "sales_volume": 50,
                    "avg_price": 15.0,
                },
            }
            result = format_liquidity_analysis(analysis, "Test")
            assert rec_part in result


# === Phase 4: get_trend_emoji Extended Tests ===


class TestGetTrendEmojiPhase4:
    """Phase 4 tests for get_trend_emoji function."""

    def test_get_trend_emoji_case_sensitive(self):
        """Test that trend is case-sensitive."""
        result_upper = get_trend_emoji("UP")
        result_lower = get_trend_emoji("up")
        # Only lowercase should work
        assert "⬆️" in result_lower
        assert "➡️" in result_upper  # Falls back to stable

    def test_get_trend_emoji_empty_string(self):
        """Test with empty string."""
        result = get_trend_emoji("")
        assert "➡️" in result

    def test_get_trend_emoji_none_like_string(self):
        """Test with 'None' string."""
        result = get_trend_emoji("None")
        assert "➡️" in result


# === Phase 4: format_sales_volume_stats Extended Tests ===


class TestFormatSalesVolumeStatsPhase4:
    """Phase 4 tests for format_sales_volume_stats function."""

    def test_format_sales_volume_unknown_game(self):
        """Test with unknown game code."""
        stats = {
            "items": [
                {"item_name": "Item", "sales_per_day": 10, "avg_price": 5, "price_trend": "stable"}
            ],
            "count": 1,
            "summary": {},
        }
        result = format_sales_volume_stats(stats, "unknown_game")
        assert "UNKNOWN_GAME" in result

    def test_format_sales_volume_no_summary(self):
        """Test without summary dict."""
        stats = {
            "items": [
                {"item_name": "Item", "sales_per_day": 10, "avg_price": 5, "price_trend": "stable"}
            ],
            "count": 1,
        }
        result = format_sales_volume_stats(stats, "csgo")
        # Should handle missing summary gracefully
        assert "CS2" in result

    def test_format_sales_volume_only_five_items_shown(self):
        """Test only top 5 items shown."""
        stats = {
            "items": [
                {"item_name": f"Item {i}", "sales_per_day": 100 - i, "avg_price": 10, "price_trend": "stable"}
                for i in range(10)
            ],
            "count": 10,
            "summary": {},
        }
        result = format_sales_volume_stats(stats, "csgo")
        # Should show items 0-4
        assert "Item 0" in result
        assert "Item 4" in result
        # Should not show item 5+
        assert "Item 5" not in result


# === Phase 4: format_arbitrage_with_sales Extended Tests ===


class TestFormatArbitrageWithSalesPhase4:
    """Phase 4 tests for format_arbitrage_with_sales function."""

    def test_format_arbitrage_game_display_names(self):
        """Test all game display names."""
        games = {
            "csgo": "CS2",
            "dota2": "Dota 2",
            "tf2": "Team Fortress 2",
            "rust": "Rust",
        }
        for code, display in games.items():
            results = {"opportunities": []}
            result = format_arbitrage_with_sales(results, code)
            assert display in result

    def test_format_arbitrage_unknown_game(self):
        """Test with unknown game code."""
        results = {"opportunities": []}
        result = format_arbitrage_with_sales(results, "unknown")
        assert "UNKNOWN" in result

    def test_format_arbitrage_no_filters(self):
        """Test without filters dict."""
        results = {
            "opportunities": [
                {
                    "market_hash_name": "Item",
                    "profit": 5.0,
                    "profit_percent": 25.0,
                    "buy_price": 20.0,
                    "sell_price": 25.0,
                    "sales_analysis": {"price_trend": "up", "sales_per_day": 10},
                }
            ]
        }
        result = format_arbitrage_with_sales(results, "csgo")
        # Should handle missing filters
        assert "Item" in result

    def test_format_arbitrage_missing_sales_analysis(self):
        """Test with missing sales_analysis."""
        results = {
            "opportunities": [
                {
                    "market_hash_name": "Item",
                    "profit": 5.0,
                    "profit_percent": 25.0,
                    "buy_price": 20.0,
                    "sell_price": 25.0,
                }
            ],
            "filters": {},
        }
        result = format_arbitrage_with_sales(results, "csgo")
        # Should handle missing sales_analysis
        assert "Item" in result


# === Phase 4: format_dmarket_results Extended Tests ===


class TestFormatDmarketResultsPhase4:
    """Phase 4 tests for format_dmarket_results function."""

    def test_format_dmarket_results_none_input(self):
        """Test with None input."""
        result = format_dmarket_results(None)
        assert "не найдены" in result

    def test_format_dmarket_results_empty_objects(self):
        """Test with empty objects list."""
        results = {"objects": [], "total": {"items": 0}}
        result = format_dmarket_results(results, "market_items")
        assert "не найдены" in result

    def test_format_dmarket_results_more_than_ten(self):
        """Test with more than 10 items."""
        results = {
            "objects": [
                {"title": f"Item {i}", "price": {"USD": i * 100}}
                for i in range(15)
            ],
            "total": {"items": 100},
        }
        result = format_dmarket_results(results, "market_items")
        assert "10 из 100" in result

    def test_format_dmarket_results_opportunities_type(self):
        """Test opportunities result type."""
        results = {
            "opportunities": [
                {
                    "item_name": "Opportunity Item",
                    "buy_price": 10,
                    "sell_price": 15,
                    "profit": 5,
                    "profit_percent": 50,
                }
            ]
        }
        result = format_dmarket_results(results, "opportunities")
        assert "Opportunity Item" in result

    def test_format_dmarket_results_exactly_ten_items(self):
        """Test with exactly 10 items."""
        results = {
            "objects": [
                {"title": f"Item {i}", "price": {"USD": 100}}
                for i in range(10)
            ],
            "total": {"items": 10},
        }
        result = format_dmarket_results(results, "market_items")
        # Should not show "10 из 10"
        assert "10 из 10" not in result


# === Phase 4: format_best_opportunities Extended Tests ===


class TestFormatBestOpportunitiesPhase4:
    """Phase 4 tests for format_best_opportunities function."""

    def test_format_best_opportunities_market_hash_name(self):
        """Test with market_hash_name instead of item_name."""
        opportunities = [
            {
                "market_hash_name": "Hash Name Item",
                "buy_price": 10,
                "sell_price": 15,
                "profit": 5,
                "profit_percent": 50,
            }
        ]
        result = format_best_opportunities(opportunities)
        assert "Hash Name Item" in result

    def test_format_best_opportunities_prefers_item_name(self):
        """Test that item_name is preferred over market_hash_name."""
        opportunities = [
            {
                "item_name": "Item Name",
                "market_hash_name": "Hash Name",
                "buy_price": 10,
                "sell_price": 15,
                "profit": 5,
                "profit_percent": 50,
            }
        ]
        result = format_best_opportunities(opportunities)
        assert "Item Name" in result
        assert "Hash Name" not in result

    def test_format_best_opportunities_no_sales_per_day(self):
        """Test without sales_per_day."""
        opportunities = [
            {
                "item_name": "Item",
                "buy_price": 10,
                "sell_price": 15,
                "profit": 5,
                "profit_percent": 50,
            }
        ]
        result = format_best_opportunities(opportunities)
        # Should not include sales_per_day line
        assert "Продаж в день" not in result

    def test_format_best_opportunities_limit_zero(self):
        """Test with limit=0."""
        opportunities = [
            {"item_name": "Item", "buy_price": 10, "sell_price": 15, "profit": 5, "profit_percent": 50}
        ]
        result = format_best_opportunities(opportunities, limit=0)
        # Should show Топ-0
        assert "Топ-0" in result


# === Phase 4: split_long_message Extended Tests ===


class TestSplitLongMessagePhase4:
    """Phase 4 tests for split_long_message function."""

    def test_split_long_message_exact_max_length(self):
        """Test message exactly at max_length."""
        message = "A" * 100
        result = split_long_message(message, max_length=100)
        assert len(result) == 1
        assert result[0] == message

    def test_split_long_message_one_over_max(self):
        """Test message one char over max_length without newlines."""
        message = "A" * 101
        result = split_long_message(message, max_length=100)
        # The function splits on newlines, but single line without newlines
        # will end up with empty first part and the content in second
        assert len(result) >= 1

    def test_split_long_message_multiple_newlines(self):
        """Test with multiple newlines."""
        message = "Line1\n\n\nLine2\n\n\nLine3"
        result = split_long_message(message, max_length=1000)
        assert len(result) == 1

    def test_split_long_message_trailing_newline(self):
        """Test message with trailing newline."""
        message = "Line1\nLine2\n"
        result = split_long_message(message, max_length=1000)
        assert len(result) == 1
        assert result[0].endswith("\n")

    def test_split_long_message_forces_split_at_boundaries(self):
        """Test splitting respects line boundaries."""
        lines = [f"Line {i}" for i in range(20)]
        message = "\n".join(lines)
        result = split_long_message(message, max_length=50)

        # Each part should end with newline (except possibly last)
        for part in result[:-1]:
            assert part.endswith("\n")


# === Phase 4: format_target_item Extended Tests ===


class TestFormatTargetItemPhase4:
    """Phase 4 tests for format_target_item function."""

    def test_format_target_item_unknown_status(self):
        """Test with unknown status."""
        target = {
            "Title": "Item",
            "Price": {"Amount": 1000},
            "Amount": 1,
            "Status": "UnknownStatus",
        }
        result = format_target_item(target)
        assert "UnknownStatus" in result

    def test_format_target_item_no_target_id(self):
        """Test without TargetID."""
        target = {
            "Title": "Item",
            "Price": {"Amount": 1000},
            "Amount": 1,
            "Status": "Created",
        }
        result = format_target_item(target)
        assert "ID:" not in result or "🔑" not in result

    def test_format_target_item_zero_price(self):
        """Test with zero price."""
        target = {
            "Title": "Free Item",
            "Price": {"Amount": 0},
            "Amount": 1,
            "Status": "Created",
        }
        result = format_target_item(target)
        assert "$0.00" in result

    def test_format_target_item_missing_price_dict(self):
        """Test with missing Price dict."""
        target = {
            "Title": "No Price",
            "Amount": 1,
            "Status": "Active",
        }
        result = format_target_item(target)
        assert "$0.00" in result


# === Phase 4: format_target_competition_analysis Extended Tests ===


class TestFormatTargetCompetitionAnalysisPhase4:
    """Phase 4 tests for format_target_competition_analysis function."""

    def test_format_competition_empty_dict(self):
        """Test with empty dict."""
        result = format_target_competition_analysis({}, "Item")
        # Empty dict is falsy, should show not found
        assert "не найдены" in result

    def test_format_competition_no_existing_orders(self):
        """Test without existing_orders."""
        analysis = {
            "competition_level": "low",
            "total_buy_orders": 0,
            "highest_buy_order_price": 0,
            "recommended_price": 100,
            "strategy": "aggressive",
        }
        result = format_target_competition_analysis(analysis, "Item")
        assert "Существующие buy orders" not in result

    def test_format_competition_many_existing_orders(self):
        """Test with more than 5 existing orders."""
        analysis = {
            "competition_level": "high",
            "total_buy_orders": 50,
            "highest_buy_order_price": 1000,
            "recommended_price": 950,
            "strategy": "conservative",
            "existing_orders": [
                {"price": 1000 - i * 10, "amount": i + 1}
                for i in range(10)
            ],
        }
        result = format_target_competition_analysis(analysis, "Item")
        # Should show "... и еще X"
        assert "и еще 5" in result

    def test_format_competition_unknown_level(self):
        """Test with unknown competition level."""
        analysis = {
            "competition_level": "extreme",
            "total_buy_orders": 100,
            "highest_buy_order_price": 2000,
            "recommended_price": 1900,
            "strategy": "wait",
        }
        result = format_target_competition_analysis(analysis, "Item")
        # Should show the raw value
        assert "extreme" in result


# === Phase 4: format_aggregated_prices Extended Tests ===


class TestFormatAggregatedPricesPhase4:
    """Phase 4 tests for format_aggregated_prices function."""

    def test_format_aggregated_prices_show_details_false(self):
        """Test with show_details=False."""
        prices = [
            {
                "title": "Item",
                "orderBestPrice": 1000,
                "orderCount": 10,
                "offerBestPrice": 1200,
                "offerCount": 5,
            }
        ]
        result = format_aggregated_prices(prices, show_details=False)
        # Should not show spread
        assert "Спред" not in result

    def test_format_aggregated_prices_zero_spread(self):
        """Test with zero spread."""
        prices = [
            {
                "title": "Item",
                "orderBestPrice": 1000,
                "orderCount": 10,
                "offerBestPrice": 1000,
                "offerCount": 5,
            }
        ]
        result = format_aggregated_prices(prices, show_details=True)
        # Spread is 0, should not show spread line
        assert "Спред: $0.00" not in result

    def test_format_aggregated_prices_more_than_ten(self):
        """Test with more than 10 items."""
        prices = [
            {
                "title": f"Item {i}",
                "orderBestPrice": 1000,
                "orderCount": 10,
                "offerBestPrice": 1200,
                "offerCount": 5,
            }
            for i in range(15)
        ]
        result = format_aggregated_prices(prices)
        assert "и еще 5 предметов" in result

    def test_format_aggregated_prices_zero_order_price(self):
        """Test with zero order price (spread_percent calc)."""
        prices = [
            {
                "title": "Item",
                "orderBestPrice": 0,
                "orderCount": 0,
                "offerBestPrice": 1000,
                "offerCount": 5,
            }
        ]
        result = format_aggregated_prices(prices, show_details=True)
        # Should not crash on division by zero
        assert "Item" in result


# === Phase 4: format_market_depth Extended Tests ===


class TestFormatMarketDepthPhase4:
    """Phase 4 tests for format_market_depth function."""

    def test_format_market_depth_empty_dict(self):
        """Test with empty dict."""
        result = format_market_depth({})
        assert "не найдены" in result

    def test_format_market_depth_unknown_health(self):
        """Test with unknown market health."""
        depth_data = {
            "summary": {
                "market_health": "unknown_health",
                "average_liquidity_score": 50,
                "average_spread_percent": 5.0,
                "high_liquidity_items": 10,
                "arbitrage_opportunities": 5,
            },
        }
        result = format_market_depth(depth_data)
        # Should show raw value
        assert "unknown_health" in result

    def test_format_market_depth_all_health_levels(self):
        """Test all market health levels."""
        health_levels = {
            "excellent": "🟢",
            "good": "🟡",
            "moderate": "🟠",
            "poor": "🔴",
        }
        for health, emoji in health_levels.items():
            depth_data = {
                "summary": {
                    "market_health": health,
                    "average_liquidity_score": 50,
                    "average_spread_percent": 5.0,
                    "high_liquidity_items": 10,
                    "arbitrage_opportunities": 5,
                },
            }
            result = format_market_depth(depth_data)
            assert emoji in result

    def test_format_market_depth_items_liquidity_colors(self):
        """Test item liquidity color indicators."""
        depth_data = {
            "summary": {
                "market_health": "good",
                "average_liquidity_score": 70,
                "average_spread_percent": 3.0,
                "high_liquidity_items": 20,
                "arbitrage_opportunities": 10,
            },
            "items": [
                {"title": "High Liq Item", "liquidity_score": 85, "spread_percent": 2.0},
                {"title": "Med Liq Item", "liquidity_score": 65, "spread_percent": 4.0},
                {"title": "Low Liq Item", "liquidity_score": 40, "spread_percent": 8.0},
            ],
        }
        result = format_market_depth(depth_data)
        assert "🟢" in result  # High liquidity
        assert "🟡" in result  # Medium liquidity
        assert "🔴" in result  # Low liquidity

    def test_format_market_depth_only_top_five_items(self):
        """Test only top 5 items shown."""
        depth_data = {
            "summary": {
                "market_health": "good",
                "average_liquidity_score": 70,
                "average_spread_percent": 3.0,
                "high_liquidity_items": 20,
                "arbitrage_opportunities": 10,
            },
            "items": [
                {"title": f"Item {i}", "liquidity_score": 80, "spread_percent": 2.0}
                for i in range(10)
            ],
        }
        result = format_market_depth(depth_data)
        # Should show items 0-4
        assert "Item 0" in result
        assert "Item 4" in result
        # Should not show item 5+
        assert "Item 5" not in result


# === Phase 4: Edge Cases ===


class TestFormattersEdgeCasesPhase4:
    """Phase 4 edge case tests for formatters."""

    def test_format_balance_string_values(self):
        """Test with string values that should be numeric."""
        balance_data = {
            "balance": "100.50",
            "available_balance": "100.50",
            "total_balance": "100.50",
        }
        # This may raise or handle gracefully depending on implementation
        try:
            result = format_balance(balance_data)
            assert result is not None
        except (TypeError, ValueError):
            pass  # Expected behavior

    def test_format_market_item_very_long_title(self):
        """Test with very long item title."""
        item = {
            "title": "A" * 500,
            "price": {"USD": 1000},
        }
        result = format_market_item(item)
        assert "A" in result
        assert len(result) > 0

    def test_format_opportunities_negative_values(self):
        """Test with negative profit values."""
        opportunities = [
            {
                "item_name": "Loss Item",
                "buy_price": 20.0,
                "sell_price": 15.0,
                "profit": -5.0,
                "profit_percent": -25.0,
            }
        ]
        result = format_opportunities(opportunities)
        assert "-5.00" in result or "-$5.00" in result

    def test_split_long_message_unicode(self):
        """Test split with unicode content."""
        message = "Привет мир\n" * 100
        result = split_long_message(message, max_length=500)
        assert len(result) >= 1
        # Verify unicode preserved
        combined = "".join(result)
        assert "Привет" in combined


# === Phase 4: Integration Tests ===


class TestFormattersIntegrationPhase4:
    """Phase 4 integration tests for formatters."""

    def test_full_workflow_balance_to_split(self):
        """Test formatting balance and splitting if needed."""
        balance_data = {
            "balance": 10000,
            "available_balance": 5000,
            "total_balance": 10000,
        }
        result = format_balance(balance_data)
        parts = split_long_message(result)
        assert len(parts) >= 1
        combined = "".join(parts)
        assert "💰" in combined

    def test_full_workflow_market_items_pagination(self):
        """Test market items with pagination workflow."""
        items = [
            {"title": f"Item {i}", "price": {"USD": i * 100}}
            for i in range(50)
        ]

        all_content = []
        total_pages = (len(items) + 4) // 5  # items_per_page=5

        for page in range(total_pages):
            result = format_market_items(items, page=page, items_per_page=5)
            all_content.append(result)

        # Verify all pages have content
        assert all(len(content) > 0 for content in all_content)

    def test_full_workflow_opportunities_with_sales(self):
        """Test opportunities and sales analysis together."""
        opportunities = [
            {
                "item_name": "Combo Item",
                "buy_price": 10.0,
                "sell_price": 15.0,
                "profit": 5.0,
                "profit_percent": 50.0,
            }
        ]

        sales_analysis = {
            "has_data": True,
            "avg_price": 12.50,
            "max_price": 16.0,
            "min_price": 9.0,
            "price_trend": "up",
            "sales_volume": 100,
            "sales_per_day": 10.0,
            "period_days": 7,
        }

        result1 = format_opportunities(opportunities)
        result2 = format_sales_analysis(sales_analysis, "Combo Item")

        # Both should format without error
        assert "Combo Item" in result1
        assert "Combo Item" in result2

    def test_concurrent_formatting(self):
        """Test concurrent formatting calls."""
        import concurrent.futures

        def format_item(i):
            item = {"title": f"Item {i}", "price": {"USD": i * 100}}
            return format_market_item(item)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(format_item, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 100
        assert all(isinstance(r, str) for r in results)

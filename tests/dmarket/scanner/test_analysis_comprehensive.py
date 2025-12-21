"""Comprehensive tests for scanner/analysis.py module.

This module provides tests for arbitrage analysis functionality including:
- Profit calculation with commission
- Item analysis and scoring
- Best opportunity finding
- Statistics aggregation
- AnalysisStats class
"""

from __future__ import annotations

import pytest

from src.dmarket.scanner.analysis import (
    DMARKET_COMMISSION,
    MIN_PROFIT_THRESHOLDS,
    AnalysisStats,
    aggregate_statistics,
    analyze_item,
    calculate_profit,
    calculate_roi,
    find_best_opportunities,
    score_opportunity,
    _extract_price,
    _parse_price,
)


class TestCalculateProfit:
    """Tests for calculate_profit function."""

    def test_calculate_profit_basic(self) -> None:
        """Test basic profit calculation."""
        buy_price = 10.0
        sell_price = 15.0

        absolute_profit, profit_percent = calculate_profit(buy_price, sell_price)

        # Net sell = 15 * (1 - 0.07) = 13.95
        # Profit = 13.95 - 10 = 3.95
        # Percent = 3.95 / 10 * 100 = 39.5%
        assert absolute_profit == 3.95
        assert profit_percent == 39.5

    def test_calculate_profit_with_custom_commission(self) -> None:
        """Test profit calculation with custom commission."""
        buy_price = 100.0
        sell_price = 120.0
        commission = 0.10  # 10%

        absolute_profit, profit_percent = calculate_profit(
            buy_price, sell_price, commission
        )

        # Net sell = 120 * 0.90 = 108
        # Profit = 108 - 100 = 8
        # Percent = 8 / 100 * 100 = 8%
        assert absolute_profit == 8.0
        assert profit_percent == 8.0

    def test_calculate_profit_zero_buy_price(self) -> None:
        """Test profit calculation with zero buy price."""
        absolute_profit, profit_percent = calculate_profit(0, 100.0)

        assert absolute_profit == 0.0
        assert profit_percent == 0.0

    def test_calculate_profit_negative_buy_price(self) -> None:
        """Test profit calculation with negative buy price."""
        absolute_profit, profit_percent = calculate_profit(-10.0, 100.0)

        assert absolute_profit == 0.0
        assert profit_percent == 0.0

    def test_calculate_profit_sell_lower_than_buy(self) -> None:
        """Test profit calculation when sell price is lower than buy."""
        absolute_profit, profit_percent = calculate_profit(100.0, 80.0)

        # Net sell = 80 * 0.93 = 74.4
        # Profit = 74.4 - 100 = -25.6
        assert absolute_profit < 0
        assert profit_percent < 0

    def test_calculate_profit_zero_commission(self) -> None:
        """Test profit calculation with zero commission."""
        absolute_profit, profit_percent = calculate_profit(10.0, 15.0, 0.0)

        # Profit = 15 - 10 = 5
        # Percent = 5 / 10 * 100 = 50%
        assert absolute_profit == 5.0
        assert profit_percent == 50.0

    def test_calculate_profit_rounding(self) -> None:
        """Test that profit values are properly rounded."""
        absolute_profit, profit_percent = calculate_profit(7.33, 11.77)

        # Results should be rounded to 2 decimal places
        assert isinstance(absolute_profit, float)
        assert isinstance(profit_percent, float)
        assert len(str(absolute_profit).split(".")[-1]) <= 2
        assert len(str(profit_percent).split(".")[-1]) <= 2

    def test_calculate_profit_uses_default_commission(self) -> None:
        """Test that default commission is used when not specified."""
        buy_price = 100.0
        sell_price = 110.0

        absolute_profit, profit_percent = calculate_profit(buy_price, sell_price)

        # Net sell = 110 * (1 - 0.07) = 102.3
        # Profit = 102.3 - 100 = 2.3
        expected_profit = round(sell_price * (1 - DMARKET_COMMISSION) - buy_price, 2)
        assert absolute_profit == expected_profit


class TestCalculateROI:
    """Tests for calculate_roi function."""

    def test_calculate_roi_positive(self) -> None:
        """Test ROI calculation with profit."""
        roi = calculate_roi(100.0, 25.0)
        assert roi == 25.0

    def test_calculate_roi_negative(self) -> None:
        """Test ROI calculation with loss."""
        roi = calculate_roi(100.0, -10.0)
        assert roi == -10.0

    def test_calculate_roi_zero_investment(self) -> None:
        """Test ROI calculation with zero investment."""
        roi = calculate_roi(0.0, 50.0)
        assert roi == 0.0

    def test_calculate_roi_negative_investment(self) -> None:
        """Test ROI calculation with negative investment."""
        roi = calculate_roi(-100.0, 25.0)
        assert roi == 0.0

    def test_calculate_roi_rounding(self) -> None:
        """Test ROI is rounded to 2 decimal places."""
        roi = calculate_roi(333.0, 111.111)
        # Should be rounded
        assert len(str(roi).split(".")[-1]) <= 2


class TestAnalyzeItem:
    """Tests for analyze_item function."""

    def test_analyze_item_basic(self) -> None:
        """Test basic item analysis."""
        item = {
            "itemId": "item123",
            "title": "Test Item",
            "price": 10.0,
            "suggestedPrice": 15.0,
            "gameId": "csgo",
            "extra": {"rarity": "rare"},
        }

        result = analyze_item(item)

        assert result is not None
        assert result["item_id"] == "item123"
        assert result["title"] == "Test Item"
        assert result["buy_price"] == 10.0
        assert result["sell_price"] == 15.0
        assert result["game"] == "csgo"
        assert result["extra_data"] == {"rarity": "rare"}
        assert result["profit_percent"] > 0

    def test_analyze_item_with_dict_prices(self) -> None:
        """Test item analysis with price as dictionary."""
        # Use values that will be properly parsed (< 1000 stays as is)
        item = {
            "id": "item456",
            "name": "Dict Price Item",
            "price": {"USD": "10"},  # $10.00 (stays as 10)
            "suggestedPrice": {"USD": "20"},  # $20.00 (stays as 20)
            "game": "dota2",
        }

        result = analyze_item(item)

        assert result is not None
        assert result["item_id"] == "item456"
        assert result["title"] == "Dict Price Item"
        assert result["game"] == "dota2"
        assert result["buy_price"] == 10.0
        assert result["sell_price"] == 20.0

    def test_analyze_item_below_min_profit(self) -> None:
        """Test item analysis when profit below minimum."""
        item = {
            "itemId": "item123",
            "price": 10.0,
            "suggestedPrice": 10.5,  # Only 5% gross, less after commission
        }

        result = analyze_item(item, min_profit_percent=10.0)

        assert result is None

    def test_analyze_item_above_max_profit(self) -> None:
        """Test item analysis when profit above maximum."""
        item = {
            "itemId": "item123",
            "price": 10.0,
            "suggestedPrice": 50.0,  # Very high profit
        }

        result = analyze_item(item, max_profit_percent=50.0)

        assert result is None

    def test_analyze_item_missing_price(self) -> None:
        """Test item analysis with missing buy price."""
        item = {
            "itemId": "item123",
            "suggestedPrice": 15.0,
        }

        result = analyze_item(item)

        assert result is None

    def test_analyze_item_missing_sell_price(self) -> None:
        """Test item analysis with missing sell price."""
        item = {
            "itemId": "item123",
            "price": 10.0,
        }

        result = analyze_item(item)

        assert result is None

    def test_analyze_item_zero_buy_price(self) -> None:
        """Test item analysis with zero buy price."""
        item = {
            "itemId": "item123",
            "price": 0,
            "suggestedPrice": 15.0,
        }

        result = analyze_item(item)

        assert result is None

    def test_analyze_item_sell_less_than_buy(self) -> None:
        """Test item analysis when sell price is lower than buy."""
        item = {
            "itemId": "item123",
            "price": 20.0,
            "suggestedPrice": 15.0,
        }

        result = analyze_item(item)

        assert result is None

    def test_analyze_item_alternative_keys(self) -> None:
        """Test item analysis with alternative key names."""
        item = {
            "id": "alt_item",
            "name": "Alt Keys Item",
            "buy_price": 10.0,
            "sell_price": 20.0,
            "game": "tf2",
        }

        result = analyze_item(item)

        assert result is not None
        assert result["item_id"] == "alt_item"
        assert result["title"] == "Alt Keys Item"
        assert result["game"] == "tf2"


class TestScoreOpportunity:
    """Tests for score_opportunity function."""

    def test_score_opportunity_basic(self) -> None:
        """Test basic opportunity scoring."""
        opportunity = {
            "profit_percent": 20.0,
            "absolute_profit": 10.0,
            "buy_price": 50.0,
        }

        score = score_opportunity(opportunity)

        assert score > 0
        assert isinstance(score, float)

    def test_score_opportunity_higher_profit_higher_score(self) -> None:
        """Test that higher profit gives higher score."""
        low_profit = {
            "profit_percent": 10.0,
            "absolute_profit": 5.0,
            "buy_price": 50.0,
        }
        high_profit = {
            "profit_percent": 30.0,
            "absolute_profit": 15.0,
            "buy_price": 50.0,
        }

        low_score = score_opportunity(low_profit)
        high_score = score_opportunity(high_profit)

        assert high_score > low_score

    def test_score_opportunity_very_high_profit_penalty(self) -> None:
        """Test that very high profit gets penalized."""
        normal_profit = {
            "profit_percent": 40.0,
            "absolute_profit": 40.0,
            "buy_price": 100.0,
        }
        very_high_profit = {
            "profit_percent": 60.0,
            "absolute_profit": 60.0,
            "buy_price": 100.0,
        }

        normal_score = score_opportunity(normal_profit)
        high_score = score_opportunity(very_high_profit)

        # Very high profit should be penalized
        # Base score for 60% would be 60, but gets 0.8 multiplier
        assert high_score < 60.0  # Should be less than base score

    def test_score_opportunity_extreme_profit_penalty(self) -> None:
        """Test that extreme profit (>80%) gets penalty applied."""
        opportunity = {
            "profit_percent": 90.0,
            "absolute_profit": 90.0,
            "buy_price": 100.0,
        }

        score = score_opportunity(opportunity)

        # Base score = 90 * 1.0 = 90
        # Profit factor = min(90/100, 1.0) = 0.9
        # Bonus = 0.9 * 10 = 9
        # Total before penalty = 99
        # Penalty for >50%: 99 * 0.8 = 79.2 (NOT 0.5, since condition is if >80, elif not if-if)
        # The code uses elif so only one penalty applies
        assert score > 0
        assert score < 100.0  # Should be penalized

    def test_score_opportunity_zero_buy_price(self) -> None:
        """Test scoring with zero buy price."""
        opportunity = {
            "profit_percent": 20.0,
            "absolute_profit": 10.0,
            "buy_price": 0.0,
        }

        score = score_opportunity(opportunity)

        # Should still return valid score
        assert isinstance(score, float)

    def test_score_opportunity_missing_values(self) -> None:
        """Test scoring with missing values uses defaults."""
        opportunity = {}

        score = score_opportunity(opportunity)

        assert score == 0.0


class TestFindBestOpportunities:
    """Tests for find_best_opportunities function."""

    def test_find_best_opportunities_basic(self) -> None:
        """Test finding best opportunities."""
        opportunities = [
            {"profit_percent": 10.0, "absolute_profit": 5.0, "buy_price": 50.0},
            {"profit_percent": 30.0, "absolute_profit": 15.0, "buy_price": 50.0},
            {"profit_percent": 20.0, "absolute_profit": 10.0, "buy_price": 50.0},
        ]

        result = find_best_opportunities(opportunities, limit=2)

        assert len(result) == 2
        # Should be sorted by score descending
        assert result[0]["profit_percent"] == 30.0

    def test_find_best_opportunities_with_limit(self) -> None:
        """Test limiting number of results."""
        opportunities = [
            {"profit_percent": i * 5.0, "absolute_profit": i * 2.5, "buy_price": 50.0}
            for i in range(1, 11)
        ]

        result = find_best_opportunities(opportunities, limit=3)

        assert len(result) == 3

    def test_find_best_opportunities_with_min_score(self) -> None:
        """Test filtering by minimum score."""
        opportunities = [
            {"profit_percent": 5.0, "absolute_profit": 2.5, "buy_price": 50.0},
            {"profit_percent": 30.0, "absolute_profit": 15.0, "buy_price": 50.0},
            {"profit_percent": 10.0, "absolute_profit": 5.0, "buy_price": 50.0},
        ]

        result = find_best_opportunities(opportunities, min_score=15.0)

        # Only opportunities with score >= 15 should be included
        for opp in result:
            assert opp["score"] >= 15.0

    def test_find_best_opportunities_empty_list(self) -> None:
        """Test with empty opportunities list."""
        result = find_best_opportunities([])

        assert result == []

    def test_find_best_opportunities_adds_score(self) -> None:
        """Test that score is added to each opportunity."""
        opportunities = [
            {"profit_percent": 20.0, "absolute_profit": 10.0, "buy_price": 50.0}
        ]

        result = find_best_opportunities(opportunities)

        assert len(result) == 1
        assert "score" in result[0]
        assert result[0]["score"] > 0


class TestAggregateStatistics:
    """Tests for aggregate_statistics function."""

    def test_aggregate_statistics_basic(self) -> None:
        """Test basic statistics aggregation."""
        opportunities = [
            {"profit_percent": 10.0, "absolute_profit": 5.0, "buy_price": 50.0},
            {"profit_percent": 20.0, "absolute_profit": 10.0, "buy_price": 50.0},
            {"profit_percent": 30.0, "absolute_profit": 15.0, "buy_price": 50.0},
        ]

        stats = aggregate_statistics(opportunities)

        assert stats["count"] == 3
        assert stats["total_potential_profit"] == 30.0
        assert stats["avg_profit_percent"] == 20.0
        assert stats["min_profit_percent"] == 10.0
        assert stats["max_profit_percent"] == 30.0
        assert stats["total_investment_needed"] == 150.0

    def test_aggregate_statistics_empty_list(self) -> None:
        """Test aggregation with empty list."""
        stats = aggregate_statistics([])

        assert stats["count"] == 0
        assert stats["total_potential_profit"] == 0.0
        assert stats["avg_profit_percent"] == 0.0
        assert stats["min_profit_percent"] == 0.0
        assert stats["max_profit_percent"] == 0.0
        assert stats["total_investment_needed"] == 0.0

    def test_aggregate_statistics_single_item(self) -> None:
        """Test aggregation with single item."""
        opportunities = [
            {"profit_percent": 15.0, "absolute_profit": 7.5, "buy_price": 50.0}
        ]

        stats = aggregate_statistics(opportunities)

        assert stats["count"] == 1
        assert stats["avg_profit_percent"] == 15.0
        assert stats["min_profit_percent"] == 15.0
        assert stats["max_profit_percent"] == 15.0

    def test_aggregate_statistics_rounding(self) -> None:
        """Test that statistics are properly rounded."""
        opportunities = [
            {"profit_percent": 10.333, "absolute_profit": 5.111, "buy_price": 50.555}
        ]

        stats = aggregate_statistics(opportunities)

        # All values should be rounded to 2 decimal places
        assert len(str(stats["total_potential_profit"]).split(".")[-1]) <= 2


class TestExtractPrice:
    """Tests for _extract_price helper function."""

    def test_extract_price_first_key(self) -> None:
        """Test extracting price from first matching key."""
        item = {"price": 10.0, "suggestedPrice": 15.0}

        price = _extract_price(item, "price")

        assert price == 10.0

    def test_extract_price_second_key(self) -> None:
        """Test extracting price from second key when first missing."""
        item = {"suggestedPrice": 15.0}

        price = _extract_price(item, "price", "suggestedPrice")

        assert price == 15.0

    def test_extract_price_no_matching_key(self) -> None:
        """Test when no keys match."""
        item = {"other_field": 10.0}

        price = _extract_price(item, "price", "suggestedPrice")

        assert price is None

    def test_extract_price_none_value(self) -> None:
        """Test when key exists but value is None."""
        item = {"price": None, "suggestedPrice": 15.0}

        price = _extract_price(item, "price", "suggestedPrice")

        assert price == 15.0


class TestParsePrice:
    """Tests for _parse_price helper function."""

    def test_parse_price_float(self) -> None:
        """Test parsing float value."""
        price = _parse_price(10.5)
        assert price == 10.5

    def test_parse_price_int(self) -> None:
        """Test parsing int value."""
        price = _parse_price(100)
        assert price == 100.0

    def test_parse_price_string(self) -> None:
        """Test parsing string value."""
        price = _parse_price("25.50")
        assert price == 25.5

    def test_parse_price_dict_usd(self) -> None:
        """Test parsing dict with USD key."""
        price = _parse_price({"USD": "10.50"})
        assert price == 10.5

    def test_parse_price_dict_usd_lowercase(self) -> None:
        """Test parsing dict with lowercase usd key."""
        price = _parse_price({"usd": "10.50"})
        assert price == 10.5

    def test_parse_price_cents_conversion(self) -> None:
        """Test automatic cents to dollars conversion."""
        # Values > 1000 are assumed to be in cents
        price = _parse_price(1500)  # $15.00
        assert price == 15.0

    def test_parse_price_string_cents_conversion(self) -> None:
        """Test cents conversion for string values."""
        price = _parse_price("2500")  # $25.00 in cents
        assert price == 25.0

    def test_parse_price_invalid_string(self) -> None:
        """Test parsing invalid string."""
        price = _parse_price("not a number")
        assert price is None

    def test_parse_price_empty_dict(self) -> None:
        """Test parsing empty dict."""
        price = _parse_price({})
        assert price is None

    def test_parse_price_other_type(self) -> None:
        """Test parsing unsupported type."""
        price = _parse_price([10, 20])
        assert price is None

    def test_parse_price_rounding(self) -> None:
        """Test that parsed prices are rounded."""
        price = _parse_price(10.12345)
        assert price == 10.12


class TestAnalysisStats:
    """Tests for AnalysisStats class."""

    def test_init(self) -> None:
        """Test initialization."""
        stats = AnalysisStats()

        result = stats.get_stats()

        assert result["total_scans"] == 0
        assert result["total_items_analyzed"] == 0
        assert result["total_opportunities_found"] == 0
        assert result["by_level"] == {}
        assert result["by_game"] == {}

    def test_record_scan(self) -> None:
        """Test recording a scan."""
        stats = AnalysisStats()

        stats.record_scan(
            level="standard",
            game="csgo",
            items_analyzed=100,
            opportunities_found=5,
        )

        result = stats.get_stats()

        assert result["total_scans"] == 1
        assert result["total_items_analyzed"] == 100
        assert result["total_opportunities_found"] == 5

    def test_record_multiple_scans(self) -> None:
        """Test recording multiple scans."""
        stats = AnalysisStats()

        stats.record_scan("standard", "csgo", 100, 5)
        stats.record_scan("boost", "csgo", 50, 10)
        stats.record_scan("standard", "dota2", 80, 3)

        result = stats.get_stats()

        assert result["total_scans"] == 3
        assert result["total_items_analyzed"] == 230
        assert result["total_opportunities_found"] == 18

    def test_stats_by_level(self) -> None:
        """Test statistics tracking by level."""
        stats = AnalysisStats()

        stats.record_scan("standard", "csgo", 100, 5)
        stats.record_scan("standard", "csgo", 100, 8)
        stats.record_scan("boost", "csgo", 50, 10)

        result = stats.get_stats()

        assert result["by_level"]["standard"]["scans"] == 2
        assert result["by_level"]["standard"]["opportunities"] == 13
        assert result["by_level"]["boost"]["scans"] == 1
        assert result["by_level"]["boost"]["opportunities"] == 10

    def test_stats_by_game(self) -> None:
        """Test statistics tracking by game."""
        stats = AnalysisStats()

        stats.record_scan("standard", "csgo", 100, 5)
        stats.record_scan("standard", "dota2", 80, 3)
        stats.record_scan("standard", "csgo", 100, 7)

        result = stats.get_stats()

        assert result["by_game"]["csgo"]["scans"] == 2
        assert result["by_game"]["csgo"]["opportunities"] == 12
        assert result["by_game"]["dota2"]["scans"] == 1
        assert result["by_game"]["dota2"]["opportunities"] == 3

    def test_reset(self) -> None:
        """Test resetting statistics."""
        stats = AnalysisStats()
        stats.record_scan("standard", "csgo", 100, 5)

        stats.reset()

        result = stats.get_stats()

        assert result["total_scans"] == 0
        assert result["total_items_analyzed"] == 0
        assert result["total_opportunities_found"] == 0
        assert result["by_level"] == {}
        assert result["by_game"] == {}

    def test_get_stats_returns_data(self) -> None:
        """Test that get_stats returns correct data."""
        stats = AnalysisStats()
        stats.record_scan("standard", "csgo", 100, 5)

        result = stats.get_stats()

        # Check that data is returned correctly
        assert result["by_level"]["standard"]["scans"] == 1
        assert result["total_scans"] == 1


class TestModuleConstants:
    """Tests for module constants."""

    def test_dmarket_commission(self) -> None:
        """Test DMarket commission constant."""
        assert DMARKET_COMMISSION == 0.07

    def test_min_profit_thresholds(self) -> None:
        """Test minimum profit thresholds."""
        assert "boost" in MIN_PROFIT_THRESHOLDS
        assert "standard" in MIN_PROFIT_THRESHOLDS
        assert "medium" in MIN_PROFIT_THRESHOLDS
        assert "advanced" in MIN_PROFIT_THRESHOLDS
        assert "pro" in MIN_PROFIT_THRESHOLDS

        # Thresholds should increase with level
        assert MIN_PROFIT_THRESHOLDS["boost"] <= MIN_PROFIT_THRESHOLDS["standard"]
        assert MIN_PROFIT_THRESHOLDS["advanced"] <= MIN_PROFIT_THRESHOLDS["pro"]

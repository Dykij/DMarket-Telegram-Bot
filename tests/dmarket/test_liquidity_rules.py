"""Unit tests for src/dmarket/liquidity_rules.py.

Tests for liquidity rules including:
- LiquidityRules dataclass
- Preset rule profiles (CONSERVATIVE, BALANCED, AGGRESSIVE)
- LIQUIDITY_SCORE_WEIGHTS
- LIQUIDITY_THRESHOLDS
- LIQUIDITY_RECOMMENDATIONS
- get_liquidity_category function
- get_liquidity_recommendation function
"""

import pytest


class TestLiquidityRulesDataclass:
    """Tests for LiquidityRules dataclass."""

    def test_default_values(self):
        """Test default values for LiquidityRules."""
        from src.dmarket.liquidity_rules import LiquidityRules

        rules = LiquidityRules()
        assert rules.min_sales_per_week == 10.0
        assert rules.max_time_to_sell_days == 7.0
        assert rules.max_active_offers == 50
        assert rules.min_price_stability == 0.85
        assert rules.min_liquidity_score == 60.0

    def test_custom_values(self):
        """Test LiquidityRules with custom values."""
        from src.dmarket.liquidity_rules import LiquidityRules

        rules = LiquidityRules(
            min_sales_per_week=20.0,
            max_time_to_sell_days=3.0,
            max_active_offers=25,
            min_price_stability=0.95,
            min_liquidity_score=80.0,
        )
        assert rules.min_sales_per_week == 20.0
        assert rules.max_time_to_sell_days == 3.0
        assert rules.max_active_offers == 25
        assert rules.min_price_stability == 0.95
        assert rules.min_liquidity_score == 80.0

    def test_partial_custom_values(self):
        """Test LiquidityRules with partial custom values."""
        from src.dmarket.liquidity_rules import LiquidityRules

        rules = LiquidityRules(min_sales_per_week=15.0)
        assert rules.min_sales_per_week == 15.0
        # Other values should be default
        assert rules.max_time_to_sell_days == 7.0


class TestPresetRuleProfiles:
    """Tests for preset rule profiles."""

    def test_conservative_rules_values(self):
        """Test CONSERVATIVE_RULES preset values."""
        from src.dmarket.liquidity_rules import CONSERVATIVE_RULES

        assert CONSERVATIVE_RULES.min_sales_per_week == 15.0
        assert CONSERVATIVE_RULES.max_time_to_sell_days == 5.0
        assert CONSERVATIVE_RULES.max_active_offers == 30
        assert CONSERVATIVE_RULES.min_price_stability == 0.90
        assert CONSERVATIVE_RULES.min_liquidity_score == 70.0

    def test_balanced_rules_values(self):
        """Test BALANCED_RULES preset values."""
        from src.dmarket.liquidity_rules import BALANCED_RULES

        assert BALANCED_RULES.min_sales_per_week == 10.0
        assert BALANCED_RULES.max_time_to_sell_days == 7.0
        assert BALANCED_RULES.max_active_offers == 50
        assert BALANCED_RULES.min_price_stability == 0.85
        assert BALANCED_RULES.min_liquidity_score == 60.0

    def test_aggressive_rules_values(self):
        """Test AGGRESSIVE_RULES preset values."""
        from src.dmarket.liquidity_rules import AGGRESSIVE_RULES

        assert AGGRESSIVE_RULES.min_sales_per_week == 5.0
        assert AGGRESSIVE_RULES.max_time_to_sell_days == 10.0
        assert AGGRESSIVE_RULES.max_active_offers == 70
        assert AGGRESSIVE_RULES.min_price_stability == 0.75
        assert AGGRESSIVE_RULES.min_liquidity_score == 50.0

    def test_conservative_is_more_strict(self):
        """Test that CONSERVATIVE_RULES is more strict than BALANCED."""
        from src.dmarket.liquidity_rules import BALANCED_RULES, CONSERVATIVE_RULES

        # Conservative should require higher min_sales
        assert CONSERVATIVE_RULES.min_sales_per_week > BALANCED_RULES.min_sales_per_week
        # Conservative should require shorter sell time
        assert CONSERVATIVE_RULES.max_time_to_sell_days < BALANCED_RULES.max_time_to_sell_days
        # Conservative should allow fewer offers
        assert CONSERVATIVE_RULES.max_active_offers < BALANCED_RULES.max_active_offers
        # Conservative should require higher price stability
        assert CONSERVATIVE_RULES.min_price_stability > BALANCED_RULES.min_price_stability
        # Conservative should require higher liquidity score
        assert CONSERVATIVE_RULES.min_liquidity_score > BALANCED_RULES.min_liquidity_score

    def test_aggressive_is_less_strict(self):
        """Test that AGGRESSIVE_RULES is less strict than BALANCED."""
        from src.dmarket.liquidity_rules import AGGRESSIVE_RULES, BALANCED_RULES

        # Aggressive should require lower min_sales
        assert AGGRESSIVE_RULES.min_sales_per_week < BALANCED_RULES.min_sales_per_week
        # Aggressive should allow longer sell time
        assert AGGRESSIVE_RULES.max_time_to_sell_days > BALANCED_RULES.max_time_to_sell_days
        # Aggressive should allow more offers
        assert AGGRESSIVE_RULES.max_active_offers > BALANCED_RULES.max_active_offers
        # Aggressive should require lower price stability
        assert AGGRESSIVE_RULES.min_price_stability < BALANCED_RULES.min_price_stability
        # Aggressive should require lower liquidity score
        assert AGGRESSIVE_RULES.min_liquidity_score < BALANCED_RULES.min_liquidity_score


class TestLiquidityScoreWeights:
    """Tests for LIQUIDITY_SCORE_WEIGHTS constant."""

    def test_weights_sum_to_one(self):
        """Test that all weights sum to 1.0 (100%)."""
        from src.dmarket.liquidity_rules import LIQUIDITY_SCORE_WEIGHTS

        total = sum(LIQUIDITY_SCORE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001  # Allow small float precision error

    def test_contains_expected_keys(self):
        """Test that weights contain all expected keys."""
        from src.dmarket.liquidity_rules import LIQUIDITY_SCORE_WEIGHTS

        expected_keys = {"sales_volume", "time_to_sell", "price_stability", "demand_supply", "market_depth"}
        assert set(LIQUIDITY_SCORE_WEIGHTS.keys()) == expected_keys

    def test_sales_volume_has_highest_weight(self):
        """Test that sales_volume has the highest weight."""
        from src.dmarket.liquidity_rules import LIQUIDITY_SCORE_WEIGHTS

        sales_volume_weight = LIQUIDITY_SCORE_WEIGHTS["sales_volume"]
        for key, weight in LIQUIDITY_SCORE_WEIGHTS.items():
            if key != "sales_volume":
                assert sales_volume_weight >= weight

    def test_all_weights_are_positive(self):
        """Test that all weights are positive."""
        from src.dmarket.liquidity_rules import LIQUIDITY_SCORE_WEIGHTS

        for weight in LIQUIDITY_SCORE_WEIGHTS.values():
            assert weight > 0


class TestLiquidityThresholds:
    """Tests for LIQUIDITY_THRESHOLDS constant."""

    def test_contains_expected_categories(self):
        """Test that thresholds contain all expected categories."""
        from src.dmarket.liquidity_rules import LIQUIDITY_THRESHOLDS

        expected_categories = {"very_high", "high", "medium", "low", "very_low"}
        assert set(LIQUIDITY_THRESHOLDS.keys()) == expected_categories

    def test_thresholds_are_ordered(self):
        """Test that thresholds are in descending order."""
        from src.dmarket.liquidity_rules import LIQUIDITY_THRESHOLDS

        assert LIQUIDITY_THRESHOLDS["very_high"] > LIQUIDITY_THRESHOLDS["high"]
        assert LIQUIDITY_THRESHOLDS["high"] > LIQUIDITY_THRESHOLDS["medium"]
        assert LIQUIDITY_THRESHOLDS["medium"] > LIQUIDITY_THRESHOLDS["low"]
        assert LIQUIDITY_THRESHOLDS["low"] > LIQUIDITY_THRESHOLDS["very_low"]

    def test_very_low_is_zero(self):
        """Test that very_low threshold is 0."""
        from src.dmarket.liquidity_rules import LIQUIDITY_THRESHOLDS

        assert LIQUIDITY_THRESHOLDS["very_low"] == 0.0

    def test_very_high_is_reasonable(self):
        """Test that very_high threshold is a reasonable value."""
        from src.dmarket.liquidity_rules import LIQUIDITY_THRESHOLDS

        assert LIQUIDITY_THRESHOLDS["very_high"] >= 70
        assert LIQUIDITY_THRESHOLDS["very_high"] <= 100


class TestLiquidityRecommendations:
    """Tests for LIQUIDITY_RECOMMENDATIONS constant."""

    def test_contains_expected_categories(self):
        """Test that recommendations contain all expected categories."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS

        expected_categories = {"very_high", "high", "medium", "low", "very_low"}
        assert set(LIQUIDITY_RECOMMENDATIONS.keys()) == expected_categories

    def test_positive_recommendations_for_high(self):
        """Test that high liquidity has positive recommendations."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS

        assert "✅" in LIQUIDITY_RECOMMENDATIONS["very_high"]
        assert "✅" in LIQUIDITY_RECOMMENDATIONS["high"]

    def test_warning_for_medium(self):
        """Test that medium liquidity has warning."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS

        assert "⚠️" in LIQUIDITY_RECOMMENDATIONS["medium"]

    def test_negative_recommendations_for_low(self):
        """Test that low liquidity has negative recommendations."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS

        assert "❌" in LIQUIDITY_RECOMMENDATIONS["low"]
        assert "❌" in LIQUIDITY_RECOMMENDATIONS["very_low"]

    def test_all_recommendations_are_non_empty(self):
        """Test that all recommendations are non-empty strings."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS

        for recommendation in LIQUIDITY_RECOMMENDATIONS.values():
            assert isinstance(recommendation, str)
            assert len(recommendation) > 0


class TestGetLiquidityCategory:
    """Tests for get_liquidity_category function."""

    def test_very_high_category(self):
        """Test that scores >= 80 return very_high."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        assert get_liquidity_category(80) == "very_high"
        assert get_liquidity_category(90) == "very_high"
        assert get_liquidity_category(100) == "very_high"

    def test_high_category(self):
        """Test that scores >= 60 and < 80 return high."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        assert get_liquidity_category(60) == "high"
        assert get_liquidity_category(70) == "high"
        assert get_liquidity_category(79.9) == "high"

    def test_medium_category(self):
        """Test that scores >= 40 and < 60 return medium."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        assert get_liquidity_category(40) == "medium"
        assert get_liquidity_category(50) == "medium"
        assert get_liquidity_category(59.9) == "medium"

    def test_low_category(self):
        """Test that scores >= 20 and < 40 return low."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        assert get_liquidity_category(20) == "low"
        assert get_liquidity_category(30) == "low"
        assert get_liquidity_category(39.9) == "low"

    def test_very_low_category(self):
        """Test that scores < 20 return very_low."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        assert get_liquidity_category(0) == "very_low"
        assert get_liquidity_category(10) == "very_low"
        assert get_liquidity_category(19.9) == "very_low"

    def test_boundary_values(self):
        """Test boundary values between categories."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        # Exactly at boundaries
        assert get_liquidity_category(80.0) == "very_high"
        assert get_liquidity_category(60.0) == "high"
        assert get_liquidity_category(40.0) == "medium"
        assert get_liquidity_category(20.0) == "low"
        assert get_liquidity_category(0.0) == "very_low"

    def test_negative_scores(self):
        """Test that negative scores return very_low."""
        from src.dmarket.liquidity_rules import get_liquidity_category

        assert get_liquidity_category(-10) == "very_low"
        assert get_liquidity_category(-100) == "very_low"


class TestGetLiquidityRecommendation:
    """Tests for get_liquidity_recommendation function."""

    def test_very_high_recommendation(self):
        """Test recommendation for very high liquidity."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS, get_liquidity_recommendation

        result = get_liquidity_recommendation(85)
        assert result == LIQUIDITY_RECOMMENDATIONS["very_high"]
        assert "Отличный выбор" in result

    def test_high_recommendation(self):
        """Test recommendation for high liquidity."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS, get_liquidity_recommendation

        result = get_liquidity_recommendation(65)
        assert result == LIQUIDITY_RECOMMENDATIONS["high"]
        assert "Хороший выбор" in result

    def test_medium_recommendation(self):
        """Test recommendation for medium liquidity."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS, get_liquidity_recommendation

        result = get_liquidity_recommendation(45)
        assert result == LIQUIDITY_RECOMMENDATIONS["medium"]
        assert "Осторожно" in result

    def test_low_recommendation(self):
        """Test recommendation for low liquidity."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS, get_liquidity_recommendation

        result = get_liquidity_recommendation(25)
        assert result == LIQUIDITY_RECOMMENDATIONS["low"]
        assert "Не рекомендуется" in result

    def test_very_low_recommendation(self):
        """Test recommendation for very low liquidity."""
        from src.dmarket.liquidity_rules import LIQUIDITY_RECOMMENDATIONS, get_liquidity_recommendation

        result = get_liquidity_recommendation(10)
        assert result == LIQUIDITY_RECOMMENDATIONS["very_low"]
        assert "Избегать" in result

    def test_consistency_with_category(self):
        """Test that recommendation is consistent with category function."""
        from src.dmarket.liquidity_rules import (
            LIQUIDITY_RECOMMENDATIONS,
            get_liquidity_category,
            get_liquidity_recommendation,
        )

        test_scores = [0, 10, 25, 45, 65, 85, 100]
        for score in test_scores:
            category = get_liquidity_category(score)
            expected_recommendation = LIQUIDITY_RECOMMENDATIONS[category]
            actual_recommendation = get_liquidity_recommendation(score)
            assert actual_recommendation == expected_recommendation


class TestLiquidityRulesUseCases:
    """Tests for practical use cases of liquidity rules."""

    def test_item_passes_conservative_rules(self):
        """Test an item that passes conservative rules."""
        from src.dmarket.liquidity_rules import CONSERVATIVE_RULES

        item = {
            "sales_per_week": 20,  # > 15
            "time_to_sell_days": 3,  # < 5
            "active_offers": 20,  # < 30
            "price_stability": 0.95,  # > 0.90
            "liquidity_score": 75,  # > 70
        }

        assert item["sales_per_week"] >= CONSERVATIVE_RULES.min_sales_per_week
        assert item["time_to_sell_days"] <= CONSERVATIVE_RULES.max_time_to_sell_days
        assert item["active_offers"] <= CONSERVATIVE_RULES.max_active_offers
        assert item["price_stability"] >= CONSERVATIVE_RULES.min_price_stability
        assert item["liquidity_score"] >= CONSERVATIVE_RULES.min_liquidity_score

    def test_item_fails_conservative_but_passes_balanced(self):
        """Test an item that fails conservative but passes balanced rules."""
        from src.dmarket.liquidity_rules import BALANCED_RULES, CONSERVATIVE_RULES

        item = {
            "sales_per_week": 12,  # Fails conservative (< 15) but passes balanced (> 10)
            "time_to_sell_days": 6,  # Fails conservative (> 5) but passes balanced (< 7)
            "active_offers": 40,  # Fails conservative (> 30) but passes balanced (< 50)
            "price_stability": 0.87,  # Fails conservative (< 0.90) but passes balanced (> 0.85)
            "liquidity_score": 62,  # Fails conservative (< 70) but passes balanced (> 60)
        }

        # Fails conservative
        assert item["sales_per_week"] < CONSERVATIVE_RULES.min_sales_per_week

        # Passes balanced
        assert item["sales_per_week"] >= BALANCED_RULES.min_sales_per_week
        assert item["time_to_sell_days"] <= BALANCED_RULES.max_time_to_sell_days
        assert item["active_offers"] <= BALANCED_RULES.max_active_offers
        assert item["price_stability"] >= BALANCED_RULES.min_price_stability
        assert item["liquidity_score"] >= BALANCED_RULES.min_liquidity_score

    def test_calculate_weighted_liquidity_score(self):
        """Test calculating a weighted liquidity score using weights."""
        from src.dmarket.liquidity_rules import LIQUIDITY_SCORE_WEIGHTS

        # Sample metrics (normalized to 0-100)
        metrics = {
            "sales_volume": 80,
            "time_to_sell": 70,
            "price_stability": 90,
            "demand_supply": 60,
            "market_depth": 75,
        }

        # Calculate weighted score
        weighted_score = sum(metrics[key] * LIQUIDITY_SCORE_WEIGHTS[key] for key in LIQUIDITY_SCORE_WEIGHTS)

        # Should be between 0 and 100
        assert 0 <= weighted_score <= 100

        # Calculate expected value manually
        expected = (
            80 * 0.30  # sales_volume
            + 70 * 0.25  # time_to_sell
            + 90 * 0.20  # price_stability
            + 60 * 0.15  # demand_supply
            + 75 * 0.10  # market_depth
        )
        assert abs(weighted_score - expected) < 0.001

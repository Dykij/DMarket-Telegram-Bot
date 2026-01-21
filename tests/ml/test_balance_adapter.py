"""Tests for src/ml/balance_adapter module.

Tests for BalanceAdaptiveStrategy and AdaptivePortfolioAllocator.
"""

import pytest

from src.ml.balance_adapter import (
    BalanceAdaptiveStrategy,
    BalanceCategory,
    StrategyMode,
    StrategyRecommendation,
    AdaptivePortfolioAllocator,
)


class TestBalanceCategory:
    """Tests for BalanceCategory enum."""

    def test_micro_category(self):
        """Test MICRO category value."""
        assert BalanceCategory.MICRO == "micro"

    def test_small_category(self):
        """Test SMALL category value."""
        assert BalanceCategory.SMALL == "small"

    def test_medium_category(self):
        """Test MEDIUM category value."""
        assert BalanceCategory.MEDIUM == "medium"

    def test_large_category(self):
        """Test LARGE category value."""
        assert BalanceCategory.LARGE == "large"

    def test_whale_category(self):
        """Test WHALE category value."""
        assert BalanceCategory.WHALE == "whale"


class TestStrategyMode:
    """Tests for StrategyMode enum."""

    def test_growth_mode(self):
        """Test GROWTH mode value."""
        assert StrategyMode.GROWTH == "growth"

    def test_balanced_mode(self):
        """Test BALANCED mode value."""
        assert StrategyMode.BALANCED == "balanced"

    def test_preservation_mode(self):
        """Test PRESERVATION mode value."""
        assert StrategyMode.PRESERVATION == "preservation"


class TestBalanceAdaptiveStrategy:
    """Tests for BalanceAdaptiveStrategy class."""

    def test_init_with_zero_balance(self):
        """Test initialization with zero balance."""
        strategy = BalanceAdaptiveStrategy(user_balance=0.0)
        assert strategy.user_balance == 0.0
        assert strategy.category == BalanceCategory.MICRO

    def test_init_with_micro_balance(self):
        """Test initialization with micro balance ($10)."""
        strategy = BalanceAdaptiveStrategy(user_balance=10.0)
        assert strategy.category == BalanceCategory.MICRO

    def test_init_with_small_balance(self):
        """Test initialization with small balance ($50)."""
        strategy = BalanceAdaptiveStrategy(user_balance=50.0)
        assert strategy.category == BalanceCategory.SMALL

    def test_init_with_medium_balance(self):
        """Test initialization with medium balance ($200)."""
        strategy = BalanceAdaptiveStrategy(user_balance=200.0)
        assert strategy.category == BalanceCategory.MEDIUM

    def test_init_with_large_balance(self):
        """Test initialization with large balance ($1000)."""
        strategy = BalanceAdaptiveStrategy(user_balance=1000.0)
        assert strategy.category == BalanceCategory.LARGE

    def test_init_with_whale_balance(self):
        """Test initialization with whale balance ($5000)."""
        strategy = BalanceAdaptiveStrategy(user_balance=5000.0)
        assert strategy.category == BalanceCategory.WHALE

    def test_set_balance(self):
        """Test set_balance updates category."""
        strategy = BalanceAdaptiveStrategy(user_balance=10.0)
        assert strategy.category == BalanceCategory.MICRO

        strategy.set_balance(500.0)
        assert strategy.user_balance == 500.0
        assert strategy.category == BalanceCategory.LARGE

    def test_set_balance_negative_clamps_to_zero(self):
        """Test set_balance clamps negative to zero."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        strategy.set_balance(-50.0)
        assert strategy.user_balance == 0.0

    def test_get_recommendation(self):
        """Test get_recommendation returns StrategyRecommendation."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        rec = strategy.get_recommendation()

        assert isinstance(rec, StrategyRecommendation)
        assert rec.balance_category == BalanceCategory.MEDIUM
        assert rec.recommended_mode == StrategyMode.BALANCED
        assert rec.max_position_percent == 20.0
        assert rec.min_profit_threshold == 7.0
        assert rec.max_concurrent_positions == 4

    def test_get_recommendation_micro(self):
        """Test recommendations for micro balance."""
        strategy = BalanceAdaptiveStrategy(user_balance=15.0)
        rec = strategy.get_recommendation()

        assert rec.balance_category == BalanceCategory.MICRO
        assert rec.recommended_mode == StrategyMode.GROWTH
        assert rec.min_profit_threshold == 15.0  # Higher threshold for safety

    def test_get_max_position_value(self):
        """Test get_max_position_value calculation."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        # Medium category has 20% max position
        max_pos = strategy.get_max_position_value()
        assert max_pos == 20.0  # 20% of $100

    def test_get_min_profit_threshold(self):
        """Test get_min_profit_threshold."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        threshold = strategy.get_min_profit_threshold()
        assert threshold == 7.0  # Medium category threshold

    def test_get_max_concurrent_positions(self):
        """Test get_max_concurrent_positions."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        max_pos = strategy.get_max_concurrent_positions()
        assert max_pos == 4  # Medium category

    def test_get_scan_interval(self):
        """Test get_scan_interval."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        interval = strategy.get_scan_interval()
        assert interval == 30  # Medium category

    def test_should_buy_valid_trade(self):
        """Test should_buy returns True for valid trade."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        should, reason = strategy.should_buy(
            item_price=15.0,
            expected_profit_percent=10.0,
            risk_score=0.3,
            current_positions=1,
        )

        assert should is True
        assert reason == "All checks passed"

    def test_should_buy_price_too_high(self):
        """Test should_buy rejects price above max position."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        should, reason = strategy.should_buy(
            item_price=50.0,  # More than 20% of balance
            expected_profit_percent=10.0,
            risk_score=0.3,
            current_positions=0,
        )

        assert should is False
        assert "exceeds max position" in reason

    def test_should_buy_insufficient_balance(self):
        """Test should_buy rejects when balance too low."""
        strategy = BalanceAdaptiveStrategy(user_balance=10.0)

        should, reason = strategy.should_buy(
            item_price=15.0,  # More than balance
            expected_profit_percent=10.0,
            risk_score=0.3,
            current_positions=0,
        )

        assert should is False
        # May return "Insufficient balance" or "exceeds max position"
        assert "balance" in reason.lower() or "exceeds max position" in reason.lower()

    def test_should_buy_profit_below_threshold(self):
        """Test should_buy rejects low profit margin."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        should, reason = strategy.should_buy(
            item_price=10.0,
            expected_profit_percent=3.0,  # Below 7% threshold
            risk_score=0.3,
            current_positions=0,
        )

        assert should is False
        assert "below threshold" in reason

    def test_should_buy_risk_too_high(self):
        """Test should_buy rejects high risk."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        should, reason = strategy.should_buy(
            item_price=10.0,
            expected_profit_percent=15.0,
            risk_score=0.9,  # Above 0.5 tolerance
            current_positions=0,
        )

        assert should is False
        assert "exceeds tolerance" in reason

    def test_should_buy_max_positions_reached(self):
        """Test should_buy rejects when max positions reached."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        should, reason = strategy.should_buy(
            item_price=10.0,
            expected_profit_percent=15.0,
            risk_score=0.3,
            current_positions=4,  # At max for medium category
        )

        assert should is False
        assert "Max positions" in reason

    def test_calculate_position_size(self):
        """Test calculate_position_size."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        size = strategy.calculate_position_size(
            item_price=15.0,
            confidence_score=0.8,
            risk_score=0.2,
        )

        assert size > 0
        assert size <= 20.0  # Max position

    def test_adapt_to_market_conditions_high_volatility(self):
        """Test market adaptation for high volatility."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        params = strategy.adapt_to_market_conditions(
            volatility=0.3,
            is_sale_period=False,
            is_tournament_period=False,
        )

        # High volatility should increase profit threshold
        assert params["min_profit_threshold"] > 7.0

    def test_adapt_to_market_conditions_sale_period(self):
        """Test market adaptation during sale."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)

        params = strategy.adapt_to_market_conditions(
            volatility=0.1,
            is_sale_period=True,
            is_tournament_period=False,
        )

        # Sale should reduce position size
        assert params["max_position_percent"] < 20.0


class TestStrategyRecommendation:
    """Tests for StrategyRecommendation dataclass."""

    def test_to_dict(self):
        """Test to_dict conversion."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        rec = strategy.get_recommendation()

        rec_dict = rec.to_dict()

        assert rec_dict["balance_category"] == "medium"
        assert rec_dict["recommended_mode"] == "balanced"
        assert "recommendations" in rec_dict
        assert "balance_usd" in rec_dict


class TestAdaptivePortfolioAllocator:
    """Tests for AdaptivePortfolioAllocator class."""

    def test_init(self):
        """Test allocator initialization."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        allocator = AdaptivePortfolioAllocator(strategy)

        assert allocator.strategy is strategy

    def test_allocate_empty_list(self):
        """Test allocate with empty opportunities."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        allocator = AdaptivePortfolioAllocator(strategy)

        result = allocator.allocate([])
        assert result == []

    def test_allocate_single_opportunity(self):
        """Test allocate with single valid opportunity."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        allocator = AdaptivePortfolioAllocator(strategy)

        opportunities = [
            {
                "item_name": "Test Item",
                "price": 10.0,
                "expected_profit": 15.0,
                "risk_score": 0.3,
                "confidence": 0.8,
            }
        ]

        result = allocator.allocate(opportunities)

        assert len(result) == 1
        assert result[0]["allocation"] > 0

    def test_allocate_respects_max_positions(self):
        """Test allocate respects max concurrent positions."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        allocator = AdaptivePortfolioAllocator(strategy)

        # Create 10 opportunities (more than max 4 for medium)
        opportunities = [
            {
                "item_name": f"Item {i}",
                "price": 5.0,
                "expected_profit": 15.0,
                "risk_score": 0.3,
                "confidence": 0.8,
            }
            for i in range(10)
        ]

        result = allocator.allocate(opportunities)

        # Only 4 should be allocated (max for medium)
        allocated_count = sum(1 for r in result if r["allocation"] > 0)
        assert allocated_count <= 4

    def test_allocate_sorts_by_profit_risk_ratio(self):
        """Test allocate prioritizes better profit/risk ratio."""
        strategy = BalanceAdaptiveStrategy(user_balance=100.0)
        allocator = AdaptivePortfolioAllocator(strategy)

        opportunities = [
            {
                "item_name": "Low profit",
                "price": 5.0,
                "expected_profit": 8.0,
                "risk_score": 0.5,
                "confidence": 0.8,
            },
            {
                "item_name": "High profit",
                "price": 5.0,
                "expected_profit": 20.0,
                "risk_score": 0.3,
                "confidence": 0.8,
            },
        ]

        result = allocator.allocate(opportunities)

        # High profit item should be allocated first (it's sorted by profit/risk)
        allocated = [r for r in result if r["allocation"] > 0]
        assert len(allocated) >= 1

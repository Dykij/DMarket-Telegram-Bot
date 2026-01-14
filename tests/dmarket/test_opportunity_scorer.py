"""Tests for opportunity_scorer module.

This module tests the OpportunityScorer class for ranking
and scoring arbitrage opportunities.
"""

import pytest
from unittest.mock import MagicMock

from src.dmarket.opportunity_scorer import OpportunityScorer


class TestOpportunityScorer:
    """Tests for OpportunityScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create OpportunityScorer instance."""
        return OpportunityScorer()

    def test_init(self, scorer):
        """Test OpportunityScorer initialization."""
        assert scorer is not None

    def test_score_by_profit(self, scorer):
        """Test scoring by profit percentage."""
        opportunity = {
            "profit_percent": 15.0,
            "buy_price": 10.0,
            "liquidity": "high",
        }

        score = scorer.score_opportunity(opportunity)
        assert score > 0
        assert score <= 100

    def test_score_high_profit(self, scorer):
        """Test high profit gets higher score."""
        high_profit = {
            "profit_percent": 25.0,
            "buy_price": 10.0,
            "liquidity": "high",
        }
        low_profit = {
            "profit_percent": 8.0,
            "buy_price": 10.0,
            "liquidity": "high",
        }

        high_score = scorer.score_opportunity(high_profit)
        low_score = scorer.score_opportunity(low_profit)

        assert high_score > low_score

    def test_score_by_liquidity(self, scorer):
        """Test scoring considers liquidity."""
        high_liquidity = {
            "profit_percent": 15.0,
            "buy_price": 10.0,
            "liquidity": "high",
        }
        low_liquidity = {
            "profit_percent": 15.0,
            "buy_price": 10.0,
            "liquidity": "low",
        }

        high_score = scorer.score_opportunity(high_liquidity)
        low_score = scorer.score_opportunity(low_liquidity)

        assert high_score >= low_score  # High liquidity should score same or higher

    def test_score_by_price(self, scorer):
        """Test scoring considers price range."""
        reasonable_price = {
            "profit_percent": 15.0,
            "buy_price": 25.0,  # Reasonable price
            "liquidity": "medium",
        }
        expensive = {
            "profit_percent": 15.0,
            "buy_price": 500.0,  # Expensive
            "liquidity": "medium",
        }

        # Both should get scores
        score1 = scorer.score_opportunity(reasonable_price)
        score2 = scorer.score_opportunity(expensive)

        assert score1 > 0
        assert score2 > 0

    def test_rank_opportunities(self, scorer):
        """Test ranking multiple opportunities."""
        opportunities = [
            {"profit_percent": 10.0, "buy_price": 10.0, "liquidity": "medium"},
            {"profit_percent": 25.0, "buy_price": 10.0, "liquidity": "high"},
            {"profit_percent": 15.0, "buy_price": 10.0, "liquidity": "low"},
        ]

        ranked = scorer.rank_opportunities(opportunities)

        assert len(ranked) == 3
        # First should have highest score
        assert ranked[0]["profit_percent"] == 25.0

    def test_rank_empty_list(self, scorer):
        """Test ranking empty list."""
        ranked = scorer.rank_opportunities([])
        assert ranked == []

    def test_filter_by_minimum_score(self, scorer):
        """Test filtering by minimum score."""
        opportunities = [
            {"profit_percent": 5.0, "buy_price": 10.0, "liquidity": "low"},
            {"profit_percent": 25.0, "buy_price": 10.0, "liquidity": "high"},
            {"profit_percent": 15.0, "buy_price": 10.0, "liquidity": "medium"},
        ]

        filtered = scorer.filter_by_score(opportunities, min_score=50.0)

        # Only high-scoring items should pass
        assert len(filtered) <= 2

    def test_get_top_opportunities(self, scorer):
        """Test getting top N opportunities."""
        opportunities = [
            {"profit_percent": 10.0, "buy_price": 10.0, "liquidity": "medium"},
            {"profit_percent": 25.0, "buy_price": 10.0, "liquidity": "high"},
            {"profit_percent": 15.0, "buy_price": 10.0, "liquidity": "high"},
            {"profit_percent": 20.0, "buy_price": 10.0, "liquidity": "medium"},
        ]

        top = scorer.get_top_opportunities(opportunities, limit=2)

        assert len(top) == 2
        # Should be sorted by score
        assert top[0]["profit_percent"] >= top[1]["profit_percent"]

    def test_calculate_weighted_score(self, scorer):
        """Test weighted score calculation."""
        opportunity = {
            "profit_percent": 15.0,
            "buy_price": 10.0,
            "liquidity": "high",
            "volume_24h": 100,
            "price_stability": 0.95,
        }

        score = scorer._calculate_weighted_score(opportunity)
        assert 0 <= score <= 100

    def test_score_components(self, scorer):
        """Test individual score components."""
        opportunity = {
            "profit_percent": 15.0,
            "buy_price": 10.0,
            "liquidity": "high",
        }

        components = scorer.get_score_breakdown(opportunity)

        assert "profit_score" in components
        assert "liquidity_score" in components
        assert "total_score" in components

"""Tests for targets/competition.py module.

This module provides comprehensive tests for:
- analyze_target_competition function tests
- assess_competition function tests
- filter_low_competition_items function tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.targets.competition import (
    analyze_target_competition,
    assess_competition,
    filter_low_competition_items,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api():
    """Create a mock DMarket API client."""
    api = MagicMock()
    api.get_targets_by_title = AsyncMock()
    api.get_aggregated_prices_bulk = AsyncMock()
    api.get_buy_orders_competition = AsyncMock()
    return api


# ============================================================================
# analyze_target_competition Tests
# ============================================================================


class TestAnalyzeTargetCompetition:
    """Test analyze_target_competition function."""

    @pytest.mark.asyncio
    async def test_analyze_with_existing_targets(self, mock_api):
        """Test analysis with existing targets."""
        mock_api.get_targets_by_title.return_value = [
            {"price": "1000"},  # $10.00
            {"price": "950"},   # $9.50
            {"price": "900"},   # $9.00
        ]
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 1500}]  # $15.00
        }

        result = await analyze_target_competition(mock_api, "csgo", "AK-47 | Redline")

        assert result["title"] == "AK-47 | Redline"
        assert result["game"] == "csgo"
        assert result["total_orders"] == 3
        assert result["best_price"] == 1000
        assert "recommended_price" in result
        assert result["competition_level"] == "low"

    @pytest.mark.asyncio
    async def test_analyze_no_existing_targets(self, mock_api):
        """Test analysis with no existing targets."""
        mock_api.get_targets_by_title.return_value = []
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 2000}]  # $20.00
        }

        result = await analyze_target_competition(mock_api, "csgo", "AWP | Asiimov")

        assert result["total_orders"] == 0
        assert result["best_price"] == 0.0
        assert result["recommended_price"] > 0

    @pytest.mark.asyncio
    async def test_analyze_medium_competition(self, mock_api):
        """Test analysis with medium competition (5-15 orders)."""
        mock_api.get_targets_by_title.return_value = [
            {"price": str(1000 - i * 10)} for i in range(10)
        ]
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 2000}]
        }

        result = await analyze_target_competition(mock_api, "csgo", "Test Item")

        assert result["competition_level"] == "medium"

    @pytest.mark.asyncio
    async def test_analyze_high_competition(self, mock_api):
        """Test analysis with high competition (15+ orders)."""
        mock_api.get_targets_by_title.return_value = [
            {"price": str(1000 - i * 5)} for i in range(20)
        ]
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 2000}]
        }

        result = await analyze_target_competition(mock_api, "csgo", "Test Item")

        assert result["competition_level"] == "high"

    @pytest.mark.asyncio
    async def test_analyze_with_api_error(self, mock_api):
        """Test analysis handles API errors gracefully."""
        mock_api.get_targets_by_title.side_effect = Exception("API Error")

        result = await analyze_target_competition(mock_api, "csgo", "Test Item")

        assert "error" in result
        assert result["title"] == "Test Item"

    @pytest.mark.asyncio
    async def test_analyze_game_id_conversion(self, mock_api):
        """Test game ID conversion from code to DMarket ID."""
        mock_api.get_targets_by_title.return_value = []
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 1000}]
        }

        await analyze_target_competition(mock_api, "csgo", "Test")

        # Verify the API was called with converted game ID
        mock_api.get_targets_by_title.assert_called_once()
        call_args = mock_api.get_targets_by_title.call_args
        assert call_args.kwargs.get("game") == "a8db"

    @pytest.mark.asyncio
    async def test_analyze_strategy_with_competitors(self, mock_api):
        """Test strategy recommendation with competitors."""
        mock_api.get_targets_by_title.return_value = [{"price": "1000"}]
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 1500}]
        }

        result = await analyze_target_competition(mock_api, "csgo", "Test")

        assert "strategy" in result
        assert len(result["strategy"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_strategy_no_competitors(self, mock_api):
        """Test strategy recommendation without competitors."""
        mock_api.get_targets_by_title.return_value = []
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 1500}]
        }

        result = await analyze_target_competition(mock_api, "csgo", "Test")

        assert "strategy" in result
        assert "7%" in result["strategy"] or "нет" in result["strategy"].lower()


# ============================================================================
# assess_competition Tests
# ============================================================================


class TestAssessCompetition:
    """Test assess_competition function."""

    @pytest.mark.asyncio
    async def test_assess_no_competition(self, mock_api):
        """Test assessment with no competition."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 0,
            "total_amount": 0,
            "competition_level": "low",
            "best_price": 0.0,
            "average_price": 0.0,
        }

        result = await assess_competition(mock_api, "csgo", "Test Item")

        assert result["should_proceed"] is True
        assert result["total_orders"] == 0
        assert "отличная возможность" in result["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_assess_low_competition(self, mock_api):
        """Test assessment with low competition."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 2,
            "total_amount": 5,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 9.5,
        }

        result = await assess_competition(mock_api, "csgo", "Test Item", max_competition=3)

        assert result["should_proceed"] is True
        assert result["suggested_price"] == 10.05  # best_price + 0.05

    @pytest.mark.asyncio
    async def test_assess_high_competition(self, mock_api):
        """Test assessment with high competition."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 10,
            "total_amount": 50,
            "competition_level": "high",
            "best_price": 15.0,
            "average_price": 12.0,
        }

        result = await assess_competition(mock_api, "csgo", "Test Item", max_competition=3)

        assert result["should_proceed"] is False
        assert "рекомендуется пропустить" in result["recommendation"].lower()
        assert result["suggested_price"] == round(15.0 * 1.03, 2)

    @pytest.mark.asyncio
    async def test_assess_with_custom_max_competition(self, mock_api):
        """Test assessment with custom max_competition threshold."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 5,
            "total_amount": 10,
            "competition_level": "medium",
            "best_price": 10.0,
            "average_price": 9.0,
        }

        # With max_competition=5, 5 orders should pass
        result = await assess_competition(mock_api, "csgo", "Test", max_competition=5)
        assert result["should_proceed"] is True

        # With max_competition=4, 5 orders should fail
        result = await assess_competition(mock_api, "csgo", "Test", max_competition=4)
        assert result["should_proceed"] is False

    @pytest.mark.asyncio
    async def test_assess_with_price_threshold(self, mock_api):
        """Test assessment with price threshold."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 2,
            "total_amount": 3,
            "competition_level": "low",
            "best_price": 8.0,
            "average_price": 7.5,
        }

        result = await assess_competition(
            mock_api, "csgo", "Test", price_threshold=10.0
        )

        mock_api.get_buy_orders_competition.assert_called_once()
        call_kwargs = mock_api.get_buy_orders_competition.call_args.kwargs
        assert call_kwargs.get("price_threshold") == 10.0

    @pytest.mark.asyncio
    async def test_assess_api_error(self, mock_api):
        """Test assessment handles API errors."""
        mock_api.get_buy_orders_competition.side_effect = Exception("Network error")

        result = await assess_competition(mock_api, "csgo", "Test Item")

        assert result["should_proceed"] is False
        assert "error" in result
        assert "Ошибка" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_assess_game_id_conversion(self, mock_api):
        """Test game ID is converted correctly."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 0,
            "total_amount": 0,
            "competition_level": "low",
            "best_price": 0.0,
            "average_price": 0.0,
        }

        await assess_competition(mock_api, "dota2", "Test Item")

        call_kwargs = mock_api.get_buy_orders_competition.call_args.kwargs
        assert call_kwargs.get("game_id") == "9a92"

    @pytest.mark.asyncio
    async def test_assess_returns_raw_data(self, mock_api):
        """Test that raw API data is included in result."""
        raw_data = {
            "total_orders": 3,
            "total_amount": 10,
            "competition_level": "low",
            "best_price": 5.0,
            "average_price": 4.5,
            "extra_field": "value",
        }
        mock_api.get_buy_orders_competition.return_value = raw_data

        result = await assess_competition(mock_api, "csgo", "Test")

        assert result["raw_data"] == raw_data


# ============================================================================
# filter_low_competition_items Tests
# ============================================================================


class TestFilterLowCompetitionItems:
    """Test filter_low_competition_items function."""

    @pytest.mark.asyncio
    async def test_filter_all_low_competition(self, mock_api):
        """Test filtering when all items have low competition."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 1,
            "total_amount": 2,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 10.0,
        }

        items = [
            {"title": "Item 1", "price": 10.0},
            {"title": "Item 2", "price": 15.0},
        ]

        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=3, request_delay=0
        )

        assert len(result) == 2
        assert all("competition" in item for item in result)

    @pytest.mark.asyncio
    async def test_filter_all_high_competition(self, mock_api):
        """Test filtering when all items have high competition."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 10,
            "total_amount": 50,
            "competition_level": "high",
            "best_price": 10.0,
            "average_price": 9.0,
        }

        items = [
            {"title": "Item 1", "price": 10.0},
            {"title": "Item 2", "price": 15.0},
        ]

        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=3, request_delay=0
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_filter_mixed_competition(self, mock_api):
        """Test filtering with mixed competition levels."""
        # Set up to return low competition for first item, high for second
        mock_api.get_buy_orders_competition.side_effect = [
            {
                "total_orders": 2,
                "total_amount": 5,
                "competition_level": "low",
                "best_price": 10.0,
                "average_price": 9.5,
            },
            {
                "total_orders": 10,
                "total_amount": 50,
                "competition_level": "high",
                "best_price": 15.0,
                "average_price": 14.0,
            },
        ]

        items = [
            {"title": "Low Comp Item", "price": 10.0},
            {"title": "High Comp Item", "price": 15.0},
        ]

        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=3, request_delay=0
        )

        assert len(result) == 1
        assert result[0]["title"] == "Low Comp Item"

    @pytest.mark.asyncio
    async def test_filter_items_without_title(self, mock_api):
        """Test filtering skips items without title."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 1,
            "total_amount": 2,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 10.0,
        }

        items = [
            {"title": "Valid Item", "price": 10.0},
            {"price": 15.0},  # No title
            {"title": "", "price": 20.0},  # Empty title - will be checked
        ]

        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=3, request_delay=0
        )

        # Empty string is falsy, so should be skipped too
        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_filter_empty_items_list(self, mock_api):
        """Test filtering with empty items list."""
        result = await filter_low_competition_items(
            mock_api, "csgo", [], max_competition=3, request_delay=0
        )

        assert result == []
        mock_api.get_buy_orders_competition.assert_not_called()

    @pytest.mark.asyncio
    async def test_filter_preserves_original_item_data(self, mock_api):
        """Test that filtered items preserve original data."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 1,
            "total_amount": 1,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 10.0,
        }

        items = [{"title": "Test Item", "price": 10.0, "extra_field": "value"}]

        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=3, request_delay=0
        )

        assert result[0]["title"] == "Test Item"
        assert result[0]["price"] == 10.0
        assert result[0]["extra_field"] == "value"

    @pytest.mark.asyncio
    async def test_filter_with_custom_max_competition(self, mock_api):
        """Test filtering with custom max_competition threshold."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 5,
            "total_amount": 10,
            "competition_level": "medium",
            "best_price": 10.0,
            "average_price": 9.0,
        }

        items = [{"title": "Test Item", "price": 10.0}]

        # Should pass with max_competition=5
        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=5, request_delay=0
        )
        assert len(result) == 1

        # Should fail with max_competition=4
        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=4, request_delay=0
        )
        assert len(result) == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestCompetitionIntegration:
    """Integration tests for competition module."""

    @pytest.mark.asyncio
    async def test_analyze_and_assess_consistency(self, mock_api):
        """Test analyze and assess give consistent results."""
        # Setup consistent mock data
        mock_api.get_targets_by_title.return_value = [
            {"price": "1000"},
            {"price": "900"},
        ]
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 1500}]
        }
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 2,
            "total_amount": 5,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 9.5,
        }

        analysis = await analyze_target_competition(mock_api, "csgo", "Test Item")
        assessment = await assess_competition(mock_api, "csgo", "Test Item")

        # Both should indicate low competition
        assert analysis["competition_level"] == "low"
        assert assessment["competition_level"] == "low"
        assert assessment["should_proceed"] is True

    @pytest.mark.asyncio
    async def test_filter_uses_assess_internally(self, mock_api):
        """Test filter function uses assess_competition internally."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 2,
            "total_amount": 3,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 9.5,
        }

        items = [{"title": "Item 1", "price": 10.0}]

        result = await filter_low_competition_items(
            mock_api, "csgo", items, max_competition=3, request_delay=0
        )

        # Filter should have called get_buy_orders_competition (via assess)
        mock_api.get_buy_orders_competition.assert_called()
        assert len(result) == 1
        # Competition data should be attached
        assert "competition" in result[0]
        assert result[0]["competition"]["should_proceed"] is True

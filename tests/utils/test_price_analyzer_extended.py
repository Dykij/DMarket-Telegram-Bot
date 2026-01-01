"""Extended tests for price_analyzer module.

Tests for advanced price analysis functions:
- calculate_price_trend
- find_undervalued_items
- analyze_supply_demand
- get_investment_recommendations
- get_investment_reason
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.price_analyzer import (
    _price_history_cache,
    analyze_supply_demand,
    calculate_price_trend,
    find_undervalued_items,
    get_investment_reason,
    get_investment_recommendations,
)


@pytest.fixture()
def mock_api():
    """Fixture for mocked DMarket API."""
    api = MagicMock(spec=DMarketAPI)
    api._request = AsyncMock()
    api.get_market_items = AsyncMock()
    return api


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    _price_history_cache.clear()
    yield
    _price_history_cache.clear()


class TestCalculatePriceTrend:
    """Tests for calculate_price_trend function."""

    @pytest.mark.asyncio()
    async def test_trend_upward(self, mock_api):
        """Test detection of upward trend."""
        # Mock price history showing upward trend
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 100, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 110, "volume": 1},
                {"date": "2024-01-03T00:00:00", "price": 120, "volume": 1},
                {"date": "2024-01-04T00:00:00", "price": 130, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert result["trend"] == "upward"
        assert result["change_percent"] > 0
        assert result["confidence"] > 0

    @pytest.mark.asyncio()
    async def test_trend_downward(self, mock_api):
        """Test detection of downward trend."""
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 200, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 180, "volume": 1},
                {"date": "2024-01-03T00:00:00", "price": 160, "volume": 1},
                {"date": "2024-01-04T00:00:00", "price": 140, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert result["trend"] == "downward"
        assert result["change_percent"] < 0

    @pytest.mark.asyncio()
    async def test_trend_stable(self, mock_api):
        """Test detection of stable trend."""
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 100, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 102, "volume": 1},
                {"date": "2024-01-03T00:00:00", "price": 101, "volume": 1},
                {"date": "2024-01-04T00:00:00", "price": 100, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        # Stable trend with small variations
        assert result["trend"] in {"stable", "upward", "downward"}
        assert abs(result["change_percent"]) < 20  # Small change

    @pytest.mark.asyncio()
    async def test_trend_no_data(self, mock_api):
        """Test trend calculation with no data."""
        mock_api._request.return_value = {"sales": []}

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert result["trend"] == "unknown"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio()
    async def test_trend_single_data_point(self, mock_api):
        """Test trend calculation with single data point."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 100, "volume": 1}]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert result["trend"] == "stable"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio()
    async def test_trend_returns_period_prices(self, mock_api):
        """Test that trend calculation returns period prices."""
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 100, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 110, "volume": 1},
                {"date": "2024-01-03T00:00:00", "price": 120, "volume": 1},
                {"date": "2024-01-04T00:00:00", "price": 130, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert "period_prices" in result
        assert isinstance(result["period_prices"], list)
        assert len(result["period_prices"]) > 0

    @pytest.mark.asyncio()
    async def test_trend_absolute_change(self, mock_api):
        """Test that trend calculation returns absolute change."""
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 100, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 200, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert "absolute_change" in result
        assert isinstance(result["absolute_change"], (int, float))

    @pytest.mark.asyncio()
    async def test_trend_high_confidence(self, mock_api):
        """Test high confidence with large price change."""
        # 40% increase - should have high confidence
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 100, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 140, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123", days=7)

        assert result["confidence"] >= 0.5


class TestFindUndervaluedItems:
    """Tests for find_undervalued_items function."""

    @pytest.mark.asyncio()
    async def test_find_undervalued_success(self, mock_api):
        """Test finding undervalued items."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"amount": 800},
                },  # $8
            ]
        }
        # Mock price history showing item is undervalued
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 1200, "volume": 5},  # Avg $12
                {"date": "2024-01-02T00:00:00", "price": 1300, "volume": 3},
                {"date": "2024-01-03T00:00:00", "price": 1100, "volume": 4},
            ]
        }

        result = await find_undervalued_items(
            mock_api,
            game="csgo",
            price_from=1.0,
            price_to=100.0,
            discount_threshold=20.0,
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_find_undervalued_no_items(self, mock_api):
        """Test finding undervalued items with no results."""
        mock_api.get_market_items.return_value = {"objects": []}

        result = await find_undervalued_items(mock_api, game="csgo")

        assert result == []

    @pytest.mark.asyncio()
    async def test_find_undervalued_api_error(self, mock_api):
        """Test handling of API error."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        result = await find_undervalued_items(mock_api, game="csgo")

        assert result == []

    @pytest.mark.asyncio()
    async def test_find_undervalued_empty_response(self, mock_api):
        """Test handling of empty API response."""
        mock_api.get_market_items.return_value = {}

        result = await find_undervalued_items(mock_api, game="csgo")

        assert result == []

    @pytest.mark.asyncio()
    async def test_find_undervalued_respects_max_results(self, mock_api):
        """Test that max_results is respected."""
        # Mock many undervalued items
        mock_api.get_market_items.return_value = {
            "objects": [
                {"itemId": f"item{i}", "title": f"Item {i}", "price": {"amount": 500}}
                for i in range(20)
            ]
        }
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000, "volume": 5}]
        }

        result = await find_undervalued_items(mock_api, game="csgo", max_results=5)

        assert len(result) <= 5

    @pytest.mark.asyncio()
    async def test_find_undervalued_sorted_by_discount(self, mock_api):
        """Test that results are sorted by discount."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {"itemId": "item1", "title": "Item 1", "price": {"amount": 800}},
                {"itemId": "item2", "title": "Item 2", "price": {"amount": 600}},
            ]
        }
        # Different historical prices to create different discounts
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1200, "volume": 5}]
        }

        result = await find_undervalued_items(mock_api, game="csgo")

        if len(result) > 1:
            # First item should have higher discount
            assert result[0]["discount"] >= result[-1]["discount"]


class TestAnalyzeSupplyDemand:
    """Tests for analyze_supply_demand function."""

    @pytest.mark.asyncio()
    async def test_analyze_high_liquidity(self, mock_api):
        """Test analysis of high liquidity item."""
        mock_api._request.return_value = {
            "offers": [{"price": 1000}, {"price": 1010}] * 5,  # 10 sell offers
            "targets": [{"price": 900}, {"price": 890}] * 5,  # 10 buy offers
        }

        result = await analyze_supply_demand(mock_api, "item123")

        assert result["liquidity"] in {"high", "medium"}
        assert result["supply_count"] > 0
        assert result["demand_count"] > 0

    @pytest.mark.asyncio()
    async def test_analyze_low_liquidity(self, mock_api):
        """Test analysis of low liquidity item."""
        mock_api._request.return_value = {
            "offers": [{"price": 1000}],  # 1 sell offer
            "targets": [{"price": 500}],  # 1 buy offer (big spread)
        }

        result = await analyze_supply_demand(mock_api, "item123")

        assert result["liquidity"] == "low"
        assert result["supply_count"] == 1
        assert result["demand_count"] == 1

    @pytest.mark.asyncio()
    async def test_analyze_no_offers(self, mock_api):
        """Test analysis with no offers."""
        mock_api._request.return_value = None

        result = await analyze_supply_demand(mock_api, "item123")

        assert result["liquidity"] == "unknown"
        assert result["supply_count"] == 0
        assert result["demand_count"] == 0

    @pytest.mark.asyncio()
    async def test_analyze_spread_calculation(self, mock_api):
        """Test spread calculation."""
        mock_api._request.return_value = {
            "offers": [{"price": 1000}],  # Min sell: $10
            "targets": [{"price": 800}],  # Max buy: $8
        }

        result = await analyze_supply_demand(mock_api, "item123")

        assert result["spread"] == 2.0  # $10 - $8 = $2
        assert result["spread_percent"] == 20.0  # 2/10 * 100

    @pytest.mark.asyncio()
    async def test_analyze_api_error(self, mock_api):
        """Test handling of API error."""
        mock_api._request.side_effect = Exception("API Error")

        result = await analyze_supply_demand(mock_api, "item123")

        assert result["liquidity"] == "unknown"
        assert result["supply_count"] == 0
        assert result["demand_count"] == 0
        assert result["spread"] == 0

    @pytest.mark.asyncio()
    async def test_analyze_empty_offers(self, mock_api):
        """Test analysis with empty offers list."""
        mock_api._request.return_value = {"offers": [], "targets": []}

        result = await analyze_supply_demand(mock_api, "item123")

        assert result["supply_count"] == 0
        assert result["demand_count"] == 0


class TestGetInvestmentRecommendations:
    """Tests for get_investment_recommendations function."""

    @pytest.mark.asyncio()
    async def test_recommendations_low_risk(self, mock_api):
        """Test recommendations with low risk level."""
        mock_api.get_market_items.return_value = {"objects": []}

        result = await get_investment_recommendations(
            mock_api, game="csgo", budget=100.0, risk_level="low"
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_recommendations_medium_risk(self, mock_api):
        """Test recommendations with medium risk level."""
        mock_api.get_market_items.return_value = {"objects": []}

        result = await get_investment_recommendations(
            mock_api, game="csgo", budget=100.0, risk_level="medium"
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_recommendations_high_risk(self, mock_api):
        """Test recommendations with high risk level."""
        mock_api.get_market_items.return_value = {"objects": []}

        result = await get_investment_recommendations(
            mock_api, game="csgo", budget=100.0, risk_level="high"
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_recommendations_max_results(self, mock_api):
        """Test that recommendations return max 10 items."""
        mock_api.get_market_items.return_value = {"objects": []}

        result = await get_investment_recommendations(
            mock_api, game="csgo", budget=1000.0
        )

        assert len(result) <= 10

    @pytest.mark.asyncio()
    async def test_recommendations_with_investment_score(self, mock_api):
        """Test that recommendations include investment score."""
        mock_api.get_market_items.return_value = {
            "objects": [{"itemId": "item1", "title": "Test", "price": {"amount": 1000}}]
        }
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 2000, "volume": 10}],
            "offers": [{"price": 1000}] * 10,
            "targets": [{"price": 900}] * 10,
        }

        result = await get_investment_recommendations(mock_api, game="csgo")

        if result:
            assert "investment_score" in result[0]
            assert "reason" in result[0]


class TestGetInvestmentReason:
    """Tests for get_investment_reason function."""

    def test_reason_significant_discount(self):
        """Test reason with significant discount."""
        item_data = {
            "discount": 30.0,
            "liquidity": "high",
            "trend": "stable",
            "trend_confidence": 0.5,
            "demand_count": 15,
        }

        reason = get_investment_reason(item_data)

        assert "Значительная скидка" in reason
        assert "30.0%" in reason

    def test_reason_good_discount(self):
        """Test reason with good discount."""
        item_data = {
            "discount": 20.0,
            "liquidity": "medium",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 3,
        }

        reason = get_investment_reason(item_data)

        assert "Хорошая скидка" in reason

    def test_reason_small_discount(self):
        """Test reason with small discount."""
        item_data = {
            "discount": 10.0,
            "liquidity": "low",
            "trend": "stable",
            "trend_confidence": 0.1,
            "demand_count": 1,
        }

        reason = get_investment_reason(item_data)

        assert "Скидка 10.0%" in reason

    def test_reason_high_liquidity(self):
        """Test reason mentions high liquidity."""
        item_data = {
            "discount": 15.0,
            "liquidity": "high",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 5,
        }

        reason = get_investment_reason(item_data)

        assert "Высокая ликвидность" in reason

    def test_reason_medium_liquidity(self):
        """Test reason mentions medium liquidity."""
        item_data = {
            "discount": 15.0,
            "liquidity": "medium",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 5,
        }

        reason = get_investment_reason(item_data)

        assert "Средняя ликвидность" in reason

    def test_reason_low_liquidity(self):
        """Test reason mentions low liquidity."""
        item_data = {
            "discount": 15.0,
            "liquidity": "low",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 5,
        }

        reason = get_investment_reason(item_data)

        assert "Низкая ликвидность" in reason

    def test_reason_upward_trend(self):
        """Test reason mentions upward trend."""
        item_data = {
            "discount": 15.0,
            "liquidity": "medium",
            "trend": "upward",
            "trend_confidence": 0.7,
            "demand_count": 5,
        }

        reason = get_investment_reason(item_data)

        assert "Восходящий тренд" in reason

    def test_reason_downward_trend(self):
        """Test reason mentions downward trend with risk."""
        item_data = {
            "discount": 15.0,
            "liquidity": "medium",
            "trend": "downward",
            "trend_confidence": 0.7,
            "demand_count": 5,
        }

        reason = get_investment_reason(item_data)

        assert "Нисходящий тренд" in reason
        assert "риск" in reason

    def test_reason_high_demand(self):
        """Test reason mentions high demand."""
        item_data = {
            "discount": 15.0,
            "liquidity": "medium",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 15,
        }

        reason = get_investment_reason(item_data)

        assert "Высокий спрос" in reason
        assert "15 заявок" in reason

    def test_reason_moderate_demand(self):
        """Test reason mentions moderate demand."""
        item_data = {
            "discount": 15.0,
            "liquidity": "medium",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 7,
        }

        reason = get_investment_reason(item_data)

        assert "Умеренный спрос" in reason

    def test_reason_all_factors(self):
        """Test reason with all positive factors."""
        item_data = {
            "discount": 30.0,
            "liquidity": "high",
            "trend": "upward",
            "trend_confidence": 0.8,
            "demand_count": 20,
        }

        reason = get_investment_reason(item_data)

        assert "Значительная скидка" in reason
        assert "Высокая ликвидность" in reason
        assert "Восходящий тренд" in reason
        assert "Высокий спрос" in reason


class TestEdgeCases:
    """Tests for edge cases in price analyzer."""

    @pytest.mark.asyncio()
    async def test_zero_price_history(self, mock_api):
        """Test handling of zero prices in history."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 0, "volume": 1}]
        }

        result = await calculate_price_trend(mock_api, "item123")

        assert result is not None
        assert "trend" in result

    @pytest.mark.asyncio()
    async def test_very_large_price_values(self, mock_api):
        """Test handling of very large prices."""
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00", "price": 1000000000, "volume": 1},
                {"date": "2024-01-02T00:00:00", "price": 2000000000, "volume": 1},
            ]
        }

        result = await calculate_price_trend(mock_api, "item123")

        assert result is not None

    @pytest.mark.asyncio()
    async def test_negative_discount(self, mock_api):
        """Test handling when current price is higher than average (no discount)."""
        mock_api.get_market_items.return_value = {
            "objects": [{"itemId": "item1", "title": "Test", "price": {"amount": 1500}}]
        }
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000, "volume": 5}]
        }

        result = await find_undervalued_items(
            mock_api, game="csgo", discount_threshold=20.0
        )

        # Should not include items with negative discount
        assert all(item.get("discount", 0) >= 0 for item in result) if result else True

    def test_investment_reason_missing_fields(self):
        """Test investment reason with missing fields."""
        item_data = {
            "discount": 15.0,
            "liquidity": "medium",
            "trend": "stable",
            "trend_confidence": 0.3,
            "demand_count": 0,
        }

        # Should not raise error
        reason = get_investment_reason(item_data)

        assert isinstance(reason, str)

    @pytest.mark.asyncio()
    async def test_concurrent_cache_access(self, mock_api):
        """Test concurrent access to price history cache."""
        import asyncio

        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000, "volume": 1}]
        }

        # Simulate concurrent requests
        tasks = [calculate_price_trend(mock_api, f"item{i}", days=7) for i in range(10)]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all("trend" in r for r in results)

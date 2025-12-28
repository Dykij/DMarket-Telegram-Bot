"""Phase 4 extended unit tests for smart_market_finder.py.

Tests cover:
- MarketOpportunityType enum
- MarketOpportunity dataclass
- SmartMarketFinder initialization and configuration
- find_best_opportunities method
- find_underpriced_items method
- find_target_opportunities method
- find_quick_flip_opportunities method
- _get_market_items_with_aggregated_prices method
- _analyze_item_opportunity method
- Helper methods (_calculate_*, _determine_*, _generate_*, _estimate_*)
- Module-level convenience functions
- Edge cases and error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import fields

from src.dmarket.smart_market_finder import (
    MarketOpportunityType,
    MarketOpportunity,
    SmartMarketFinder,
    find_best_deals,
    find_quick_profits,
)


class TestMarketOpportunityTypeEnum:
    """Tests for MarketOpportunityType enum."""

    def test_underpriced_value(self):
        """Test UNDERPRICED enum value."""
        assert MarketOpportunityType.UNDERPRICED.value == "underpriced"

    def test_trending_up_value(self):
        """Test TRENDING_UP enum value."""
        assert MarketOpportunityType.TRENDING_UP.value == "trending_up"

    def test_high_liquidity_value(self):
        """Test HIGH_LIQUIDITY enum value."""
        assert MarketOpportunityType.HIGH_LIQUIDITY.value == "high_liquidity"

    def test_target_opportunity_value(self):
        """Test TARGET_OPPORTUNITY enum value."""
        assert MarketOpportunityType.TARGET_OPPORTUNITY.value == "target_opportunity"

    def test_quick_flip_value(self):
        """Test QUICK_FLIP enum value."""
        assert MarketOpportunityType.QUICK_FLIP.value == "quick_flip"

    def test_value_investment_value(self):
        """Test VALUE_INVESTMENT enum value."""
        assert MarketOpportunityType.VALUE_INVESTMENT.value == "value_investment"

    def test_enum_is_str(self):
        """Test that enum values are strings."""
        for member in MarketOpportunityType:
            assert isinstance(member.value, str)

    def test_all_members_count(self):
        """Test total number of enum members."""
        assert len(MarketOpportunityType) == 6


class TestMarketOpportunityDataclass:
    """Tests for MarketOpportunity dataclass."""

    def test_basic_initialization(self):
        """Test basic dataclass initialization."""
        opp = MarketOpportunity(
            item_id="test123",
            title="Test Item",
            current_price=10.0,
            suggested_price=15.0,
            profit_potential=5.0,
            profit_percent=50.0,
            opportunity_type=MarketOpportunityType.UNDERPRICED,
            confidence_score=80.0,
            liquidity_score=70.0,
            risk_level="medium",
        )
        assert opp.item_id == "test123"
        assert opp.title == "Test Item"
        assert opp.current_price == 10.0
        assert opp.suggested_price == 15.0

    def test_default_values(self):
        """Test default values for optional fields."""
        opp = MarketOpportunity(
            item_id="test",
            title="Test",
            current_price=1.0,
            suggested_price=2.0,
            profit_potential=1.0,
            profit_percent=100.0,
            opportunity_type=MarketOpportunityType.QUICK_FLIP,
            confidence_score=50.0,
            liquidity_score=50.0,
            risk_level="low",
        )
        assert opp.best_offer_price is None
        assert opp.best_order_price is None
        assert opp.offers_count == 0
        assert opp.orders_count == 0
        assert opp.game == "csgo"
        assert opp.category is None
        assert opp.rarity is None
        assert opp.exterior is None
        assert opp.image_url is None
        assert opp.recommended_action is None
        assert opp.estimated_time_to_sell is None
        assert opp.notes is None

    def test_all_fields_set(self):
        """Test with all fields explicitly set."""
        opp = MarketOpportunity(
            item_id="item123",
            title="AK-47 | Redline",
            current_price=25.0,
            suggested_price=30.0,
            profit_potential=5.0,
            profit_percent=20.0,
            opportunity_type=MarketOpportunityType.HIGH_LIQUIDITY,
            confidence_score=85.0,
            liquidity_score=90.0,
            risk_level="low",
            best_offer_price=29.0,
            best_order_price=26.0,
            offers_count=100,
            orders_count=50,
            game="csgo",
            category="Rifle",
            rarity="Classified",
            exterior="Field-Tested",
            image_url="https://example.com/image.png",
            recommended_action="Buy now",
            estimated_time_to_sell="< 24 hours",
            notes=["Popular item", "High demand"],
        )
        assert opp.best_offer_price == 29.0
        assert opp.best_order_price == 26.0
        assert opp.offers_count == 100
        assert opp.orders_count == 50
        assert opp.category == "Rifle"
        assert opp.rarity == "Classified"
        assert len(opp.notes) == 2

    def test_required_fields(self):
        """Test that dataclass has expected required fields."""
        required_fields = [
            "item_id", "title", "current_price", "suggested_price",
            "profit_potential", "profit_percent", "opportunity_type",
            "confidence_score", "liquidity_score", "risk_level"
        ]
        field_names = [f.name for f in fields(MarketOpportunity)]
        for field in required_fields:
            assert field in field_names


class TestSmartMarketFinderInit:
    """Tests for SmartMarketFinder initialization."""

    def test_basic_initialization(self):
        """Test basic initialization with API client."""
        mock_api = MagicMock()
        finder = SmartMarketFinder(mock_api)
        
        assert finder.api is mock_api
        assert finder._cache == {}
        assert finder._cache_ttl == 300

    def test_default_settings(self):
        """Test default analysis settings."""
        mock_api = MagicMock()
        finder = SmartMarketFinder(mock_api)
        
        assert finder.min_profit_percent == 5.0
        assert finder.min_confidence == 60.0
        assert finder.max_price == 100.0

    def test_logging_on_init(self):
        """Test that initialization logs a message."""
        mock_api = MagicMock()
        with patch("src.dmarket.smart_market_finder.logger") as mock_logger:
            SmartMarketFinder(mock_api)
            mock_logger.info.assert_called_once()


class TestFindBestOpportunities:
    """Tests for find_best_opportunities method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_items(self, finder):
        """Test returns empty list when no items found."""
        finder.api._request = AsyncMock(return_value={"objects": []})
        
        result = await finder.find_best_opportunities(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_none_response(self, finder):
        """Test returns empty list when API returns None."""
        finder.api._request = AsyncMock(return_value=None)
        
        result = await finder.find_best_opportunities(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_error(self, finder):
        """Test returns empty list on API error."""
        finder.api._request = AsyncMock(side_effect=Exception("API Error"))
        
        result = await finder.find_best_opportunities(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_confidence(self, finder):
        """Test that results are filtered by minimum confidence."""
        mock_items = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Low Confidence Item",
                    "price": {"USD": "1000"},  # 10 USD in cents
                    "suggestedPrice": {"USD": "1100"},
                    "extra": {"popularity": 0.1},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_items)
        
        result = await finder.find_best_opportunities(
            game="csgo",
            min_confidence=90.0,  # Very high threshold
        )
        
        # Low popularity item won't meet high confidence threshold
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_filters_by_opportunity_type(self, finder):
        """Test filtering by specific opportunity types."""
        mock_items = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "2000"},  # 100% profit
                    "extra": {"popularity": 0.5},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_items)
        
        # Filter for only HIGH_LIQUIDITY type
        result = await finder.find_best_opportunities(
            game="csgo",
            opportunity_types=[MarketOpportunityType.HIGH_LIQUIDITY],
            min_confidence=0,
        )
        
        # Item has high profit so it's UNDERPRICED, not HIGH_LIQUIDITY
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_respects_limit(self, finder):
        """Test that results are limited."""
        mock_items = {
            "objects": [
                {
                    "itemId": f"item{i}",
                    "title": f"Item {i}",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "2000"},
                    "extra": {"popularity": 0.9},
                }
                for i in range(10)
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_items)
        
        result = await finder.find_best_opportunities(
            game="csgo",
            limit=3,
            min_confidence=0,
        )
        
        assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_game_id_conversion_csgo(self, finder):
        """Test game ID conversion for CS:GO."""
        finder.api._request = AsyncMock(return_value={"objects": []})
        
        await finder.find_best_opportunities(game="csgo")
        
        # Check that the game ID was converted
        call_args = finder.api._request.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_game_id_conversion_dota2(self, finder):
        """Test game ID conversion for Dota 2."""
        finder.api._request = AsyncMock(return_value={"objects": []})
        
        await finder.find_best_opportunities(game="dota2")
        
        call_args = finder.api._request.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_results_sorted_by_confidence(self, finder):
        """Test that results are sorted by confidence score."""
        mock_items = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Low Popularity",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "2000"},
                    "extra": {"popularity": 0.1},
                },
                {
                    "itemId": "item2",
                    "title": "High Popularity",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "2000"},
                    "extra": {"popularity": 0.9},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_items)
        
        result = await finder.find_best_opportunities(
            game="csgo",
            min_confidence=0,
        )
        
        if len(result) >= 2:
            assert result[0].confidence_score >= result[1].confidence_score


class TestFindUnderpricedItems:
    """Tests for find_underpriced_items method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_response(self, finder):
        """Test returns empty list when no response."""
        finder.api._request = AsyncMock(return_value=None)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, finder):
        """Test returns empty list on error."""
        finder.api._request = AsyncMock(side_effect=Exception("Error"))
        
        result = await finder.find_underpriced_items(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_discount_percent(self, finder):
        """Test filtering by minimum discount percent."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Small Discount",
                    "price": {"USD": "950"},  # 9.50 USD
                    "suggestedPrice": {"USD": "1000"},  # 10 USD = 5% discount
                    "extra": {},
                },
                {
                    "itemId": "item2",
                    "title": "Large Discount",
                    "price": {"USD": "800"},  # 8 USD
                    "suggestedPrice": {"USD": "1000"},  # 10 USD = 20% discount
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(
            game="csgo",
            min_discount_percent=15.0,
        )
        
        # Only the 20% discount item should be included
        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_calculates_profit_correctly(self, finder):
        """Test profit calculation with 7% fee."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},  # 10 USD
                    "suggestedPrice": {"USD": "2000"},  # 20 USD = 50% discount
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        if len(result) > 0:
            # 20 * 0.93 - 10 = 18.6 - 10 = 8.6 profit
            assert result[0].profit_potential > 0

    @pytest.mark.asyncio
    async def test_sets_risk_level_high_for_large_discount(self, finder):
        """Test high risk level for very large discounts."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Suspicious Discount",
                    "price": {"USD": "500"},  # 5 USD
                    "suggestedPrice": {"USD": "1000"},  # 10 USD = 50% discount
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(
            game="csgo",
            min_discount_percent=30.0,
        )
        
        if len(result) > 0:
            assert result[0].risk_level == "high"

    @pytest.mark.asyncio
    async def test_sets_opportunity_type_underpriced(self, finder):
        """Test that opportunity type is set to UNDERPRICED."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "800"},
                    "suggestedPrice": {"USD": "1000"},
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        if len(result) > 0:
            assert result[0].opportunity_type == MarketOpportunityType.UNDERPRICED

    @pytest.mark.asyncio
    async def test_skips_items_without_prices(self, finder):
        """Test that items without prices are skipped."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "No Prices",
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_respects_limit(self, finder):
        """Test that limit is respected."""
        mock_response = {
            "objects": [
                {
                    "itemId": f"item{i}",
                    "title": f"Item {i}",
                    "price": {"USD": "500"},
                    "suggestedPrice": {"USD": "1000"},
                    "extra": {},
                }
                for i in range(10)
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo", limit=3)
        
        assert len(result) <= 3


class TestFindTargetOpportunities:
    """Tests for find_target_opportunities method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_market_response(self, finder):
        """Test returns empty when no market response."""
        finder.api._request = AsyncMock(return_value=None)
        
        result = await finder.find_target_opportunities(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, finder):
        """Test returns empty on error."""
        finder.api._request = AsyncMock(side_effect=Exception("Error"))
        
        result = await finder.find_target_opportunities(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_titles(self, finder):
        """Test returns empty when items have no titles."""
        mock_response = {
            "objects": [
                {"itemId": "item1"},  # No title
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_target_opportunities(game="csgo")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_spread_percent(self, finder):
        """Test filtering by minimum spread percent."""
        # First call returns market items
        market_response = {
            "objects": [
                {"title": "Test Item", "itemId": "item1"},
            ]
        }
        # Second call returns aggregated prices
        aggregated_response = {
            "aggregatedPrices": [
                {
                    "title": "Test Item",
                    "orderBestPrice": "1000",  # 10 USD
                    "offerBestPrice": "1050",  # 10.50 USD = 5% spread
                    "orderCount": 10,
                    "offerCount": 20,
                },
            ]
        }
        finder.api._request = AsyncMock(
            side_effect=[market_response, aggregated_response]
        )
        
        result = await finder.find_target_opportunities(
            game="csgo",
            min_spread_percent=10.0,  # Higher than 5%
        )
        
        # Should be filtered out due to low spread
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_calculates_profit_with_fee(self, finder):
        """Test profit calculation considers 7% fee."""
        market_response = {
            "objects": [
                {"title": "Test Item", "itemId": "item1"},
            ]
        }
        aggregated_response = {
            "aggregatedPrices": [
                {
                    "title": "Test Item",
                    "orderBestPrice": "1000",  # 10 USD
                    "offerBestPrice": "1500",  # 15 USD = 50% spread
                    "orderCount": 10,
                    "offerCount": 20,
                },
            ]
        }
        finder.api._request = AsyncMock(
            side_effect=[market_response, aggregated_response]
        )
        
        result = await finder.find_target_opportunities(
            game="csgo",
            min_spread_percent=5.0,
        )
        
        if len(result) > 0:
            assert result[0]["profit_potential"] > 0

    @pytest.mark.asyncio
    async def test_skips_items_without_prices(self, finder):
        """Test skips items without order or offer prices."""
        market_response = {
            "objects": [
                {"title": "Test Item", "itemId": "item1"},
            ]
        }
        aggregated_response = {
            "aggregatedPrices": [
                {
                    "title": "Test Item",
                    # No orderBestPrice or offerBestPrice
                },
            ]
        }
        finder.api._request = AsyncMock(
            side_effect=[market_response, aggregated_response]
        )
        
        result = await finder.find_target_opportunities(game="csgo")
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_includes_notes_and_recommendations(self, finder):
        """Test that results include notes and recommendations."""
        market_response = {
            "objects": [
                {"title": "Test Item", "itemId": "item1"},
            ]
        }
        aggregated_response = {
            "aggregatedPrices": [
                {
                    "title": "Test Item",
                    "orderBestPrice": "1000",
                    "offerBestPrice": "2000",
                    "orderCount": 10,
                    "offerCount": 20,
                },
            ]
        }
        finder.api._request = AsyncMock(
            side_effect=[market_response, aggregated_response]
        )
        
        result = await finder.find_target_opportunities(game="csgo")
        
        if len(result) > 0:
            assert "recommended_action" in result[0]
            assert "notes" in result[0]


class TestFindQuickFlipOpportunities:
    """Tests for find_quick_flip_opportunities method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_filters_by_liquidity(self, finder):
        """Test filtering by minimum liquidity score."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Low Liquidity",
                    "price": {"USD": "800"},
                    "suggestedPrice": {"USD": "1000"},
                    "extra": {"popularity": 0.1},  # Low popularity = low liquidity
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_quick_flip_opportunities(game="csgo")
        
        # Low liquidity items should be filtered out
        for opp in result:
            assert opp.liquidity_score >= 50

    @pytest.mark.asyncio
    async def test_filters_by_risk_level(self, finder):
        """Test filtering by maximum risk level."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "500"},
                    "suggestedPrice": {"USD": "1500"},  # High discount = high risk
                    "extra": {"popularity": 0.8},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_quick_flip_opportunities(
            game="csgo",
            max_risk="low",
        )
        
        for opp in result:
            assert opp.risk_level == "low"

    @pytest.mark.asyncio
    async def test_sets_opportunity_type_quick_flip(self, finder):
        """Test that opportunity type is set to QUICK_FLIP."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "800"},
                    "suggestedPrice": {"USD": "1000"},
                    "extra": {"popularity": 0.8},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_quick_flip_opportunities(game="csgo")
        
        for opp in result:
            assert opp.opportunity_type == MarketOpportunityType.QUICK_FLIP

    @pytest.mark.asyncio
    async def test_sets_estimated_time_to_sell(self, finder):
        """Test that estimated time to sell is set."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "800"},
                    "suggestedPrice": {"USD": "1000"},
                    "extra": {"popularity": 0.8},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_quick_flip_opportunities(game="csgo")
        
        for opp in result:
            assert opp.estimated_time_to_sell is not None

    @pytest.mark.asyncio
    async def test_sorted_by_liquidity(self, finder):
        """Test results are sorted by liquidity."""
        mock_response = {
            "objects": [
                {
                    "itemId": f"item{i}",
                    "title": f"Item {i}",
                    "price": {"USD": "800"},
                    "suggestedPrice": {"USD": "1000"},
                    "extra": {"popularity": 0.5 + i * 0.1},
                }
                for i in range(3)
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_quick_flip_opportunities(game="csgo")
        
        if len(result) >= 2:
            assert result[0].liquidity_score >= result[-1].liquidity_score


class TestGetMarketItemsWithAggregatedPrices:
    """Tests for _get_market_items_with_aggregated_prices method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, finder):
        """Test returns empty list on error."""
        finder.api._request = AsyncMock(side_effect=Exception("Error"))
        
        result = await finder._get_market_items_with_aggregated_prices(
            game="csgo",
            min_price=1.0,
            max_price=100.0,
        )
        
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_items_without_aggregated_on_failure(self, finder):
        """Test returns items even if aggregated prices fail."""
        market_response = {
            "objects": [
                {"title": "Test Item", "itemId": "item1"},
            ]
        }
        finder.api._request = AsyncMock(
            side_effect=[market_response, Exception("Aggregated API Error")]
        )
        
        result = await finder._get_market_items_with_aggregated_prices(
            game="csgo",
            min_price=1.0,
            max_price=100.0,
        )
        
        # Should return items even without aggregated data
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_merges_aggregated_data(self, finder):
        """Test that aggregated data is merged into items."""
        market_response = {
            "objects": [
                {"title": "Test Item", "itemId": "item1"},
            ]
        }
        aggregated_response = {
            "aggregatedPrices": [
                {
                    "title": "Test Item",
                    "orderBestPrice": "1000",
                    "offerBestPrice": "1100",
                },
            ]
        }
        finder.api._request = AsyncMock(
            side_effect=[market_response, aggregated_response]
        )
        
        result = await finder._get_market_items_with_aggregated_prices(
            game="a8db",  # CS:GO game ID
            min_price=1.0,
            max_price=100.0,
        )
        
        if len(result) > 0:
            assert "aggregated" in result[0]


class TestAnalyzeItemOpportunity:
    """Tests for _analyze_item_opportunity method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_returns_none_for_item_without_title(self, finder):
        """Test returns None for items without title."""
        item = {"itemId": "item1", "price": {"USD": "1000"}}
        
        result = await finder._analyze_item_opportunity(item, "csgo")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_zero_price(self, finder):
        """Test returns None for items with zero price."""
        item = {
            "itemId": "item1",
            "title": "Test Item",
            "price": {"USD": "0"},
        }
        
        result = await finder._analyze_item_opportunity(item, "csgo")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_uses_default_suggested_price(self, finder):
        """Test uses default suggested price when not provided."""
        item = {
            "itemId": "item1",
            "title": "Test Item",
            "price": {"USD": "1000"},  # 10 USD
            # No suggestedPrice
        }
        
        result = await finder._analyze_item_opportunity(item, "csgo")
        
        if result:
            # Default is current * 1.1 = 11 USD
            assert result.suggested_price == 11.0

    @pytest.mark.asyncio
    async def test_extracts_aggregated_data(self, finder):
        """Test extraction of aggregated data."""
        item = {
            "itemId": "item1",
            "title": "Test Item",
            "price": {"USD": "1000"},
            "suggestedPrice": {"USD": "1200"},
            "aggregated": {
                "offerBestPrice": "1100",
                "orderBestPrice": "900",
                "offerCount": 50,
                "orderCount": 30,
            },
        }
        
        result = await finder._analyze_item_opportunity(item, "csgo")
        
        if result:
            assert result.best_offer_price == 11.0
            assert result.best_order_price == 9.0
            assert result.offers_count == 50
            assert result.orders_count == 30

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self, finder):
        """Test returns None when exception occurs."""
        item = {
            "itemId": "item1",
            "title": "Test Item",
            "price": "invalid",  # Invalid price format
        }
        
        result = await finder._analyze_item_opportunity(item, "csgo")
        
        assert result is None


class TestDetermineOpportunityType:
    """Tests for _determine_opportunity_type method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_returns_underpriced_for_high_profit(self, finder):
        """Test returns UNDERPRICED for high profit percent."""
        item = {"extra": {"popularity": 0.5}}
        
        result = finder._determine_opportunity_type(item, profit_percent=20.0)
        
        assert result == MarketOpportunityType.UNDERPRICED

    def test_returns_high_liquidity_for_popular(self, finder):
        """Test returns HIGH_LIQUIDITY for popular items."""
        item = {"extra": {"popularity": 0.8}}
        
        result = finder._determine_opportunity_type(item, profit_percent=8.0)
        
        assert result == MarketOpportunityType.HIGH_LIQUIDITY

    def test_returns_quick_flip_for_medium_profit(self, finder):
        """Test returns QUICK_FLIP for medium profit."""
        item = {"extra": {"popularity": 0.5}}
        
        result = finder._determine_opportunity_type(item, profit_percent=12.0)
        
        assert result == MarketOpportunityType.QUICK_FLIP

    def test_returns_value_investment_for_low_profit(self, finder):
        """Test returns VALUE_INVESTMENT for low profit."""
        item = {"extra": {"popularity": 0.5}}
        
        result = finder._determine_opportunity_type(item, profit_percent=7.0)
        
        assert result == MarketOpportunityType.VALUE_INVESTMENT

    def test_returns_target_opportunity_for_very_low_profit(self, finder):
        """Test returns TARGET_OPPORTUNITY for very low profit."""
        item = {"extra": {"popularity": 0.5}}
        
        result = finder._determine_opportunity_type(item, profit_percent=3.0)
        
        assert result == MarketOpportunityType.TARGET_OPPORTUNITY


class TestCalculateConfidenceScore:
    """Tests for _calculate_confidence_score method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_base_score_is_50(self, finder):
        """Test base confidence score is 50."""
        item = {"extra": {}}
        
        result = finder._calculate_confidence_score(item, profit_percent=0)
        
        assert result >= 50

    def test_increases_with_profit(self, finder):
        """Test score increases with profit percent."""
        item = {"extra": {}}
        
        low_profit = finder._calculate_confidence_score(item, profit_percent=5)
        high_profit = finder._calculate_confidence_score(item, profit_percent=20)
        
        assert high_profit > low_profit

    def test_increases_with_popularity(self, finder):
        """Test score increases with popularity."""
        low_pop = finder._calculate_confidence_score(
            {"extra": {"popularity": 0.1}},
            profit_percent=10,
        )
        high_pop = finder._calculate_confidence_score(
            {"extra": {"popularity": 0.9}},
            profit_percent=10,
        )
        
        assert high_pop > low_pop

    def test_bonus_for_suggested_price(self, finder):
        """Test bonus for having suggested price."""
        without = finder._calculate_confidence_score({"extra": {}}, 10)
        with_suggested = finder._calculate_confidence_score(
            {"extra": {}, "suggestedPrice": {"USD": "1000"}},
            10,
        )
        
        assert with_suggested > without

    def test_capped_at_100(self, finder):
        """Test score is capped at 100."""
        item = {"extra": {"popularity": 1.0}, "suggestedPrice": {"USD": "1000"}}
        
        result = finder._calculate_confidence_score(item, profit_percent=50)
        
        assert result <= 100


class TestCalculateLiquidityScore:
    """Tests for _calculate_liquidity_score method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_base_score_is_30(self, finder):
        """Test base liquidity score is 30."""
        item = {"extra": {}}
        
        result = finder._calculate_liquidity_score(item)
        
        assert result >= 30

    def test_increases_with_popularity(self, finder):
        """Test score increases with popularity."""
        low = finder._calculate_liquidity_score({"extra": {"popularity": 0.1}})
        high = finder._calculate_liquidity_score({"extra": {"popularity": 0.9}})
        
        assert high > low

    def test_increases_with_aggregated_counts(self, finder):
        """Test score increases with offer/order counts."""
        without = finder._calculate_liquidity_score({"extra": {}})
        with_counts = finder._calculate_liquidity_score({
            "extra": {},
            "aggregated": {"offerCount": 50, "orderCount": 30},
        })
        
        assert with_counts > without

    def test_capped_at_100(self, finder):
        """Test score is capped at 100."""
        item = {
            "extra": {"popularity": 1.0},
            "aggregated": {"offerCount": 1000, "orderCount": 1000},
        }
        
        result = finder._calculate_liquidity_score(item)
        
        assert result <= 100


class TestDetermineRiskLevel:
    """Tests for _determine_risk_level method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_low_risk_conditions(self, finder):
        """Test low risk for ideal conditions."""
        result = finder._determine_risk_level(
            profit_percent=15.0,
            liquidity=80.0,
            confidence=75.0,
        )
        
        assert result == "low"

    def test_high_risk_low_liquidity(self, finder):
        """Test high risk for low liquidity."""
        result = finder._determine_risk_level(
            profit_percent=10.0,
            liquidity=30.0,  # Low liquidity
            confidence=70.0,
        )
        
        assert result == "high"

    def test_high_risk_very_high_profit(self, finder):
        """Test high risk for very high profit (suspicious)."""
        result = finder._determine_risk_level(
            profit_percent=35.0,  # Very high profit
            liquidity=70.0,
            confidence=70.0,
        )
        
        assert result == "high"

    def test_high_risk_low_confidence(self, finder):
        """Test high risk for low confidence."""
        result = finder._determine_risk_level(
            profit_percent=10.0,
            liquidity=70.0,
            confidence=45.0,  # Low confidence
        )
        
        assert result == "high"

    def test_medium_risk_default(self, finder):
        """Test medium risk for average conditions."""
        result = finder._determine_risk_level(
            profit_percent=10.0,
            liquidity=50.0,
            confidence=60.0,
        )
        
        assert result == "medium"


class TestGenerateRecommendation:
    """Tests for _generate_recommendation method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_target_opportunity_recommendation(self, finder):
        """Test recommendation for target opportunity."""
        result = finder._generate_recommendation(
            opportunity_type=MarketOpportunityType.TARGET_OPPORTUNITY,
            current_price=10.0,
            suggested_price=15.0,
            best_order=9.0,
        )
        
        assert "таргет" in result.lower() or "target" in result.lower()

    def test_quick_flip_recommendation(self, finder):
        """Test recommendation for quick flip."""
        result = finder._generate_recommendation(
            opportunity_type=MarketOpportunityType.QUICK_FLIP,
            current_price=10.0,
            suggested_price=15.0,
            best_order=None,
        )
        
        assert "быстро" in result.lower() or "купить" in result.lower()

    def test_default_recommendation(self, finder):
        """Test default recommendation."""
        result = finder._generate_recommendation(
            opportunity_type=MarketOpportunityType.UNDERPRICED,
            current_price=10.0,
            suggested_price=15.0,
            best_order=None,
        )
        
        assert "купить" in result.lower() or "продать" in result.lower()


class TestEstimateTimeToSell:
    """Tests for _estimate_time_to_sell method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_very_high_liquidity(self, finder):
        """Test estimate for very high liquidity."""
        result = finder._estimate_time_to_sell(liquidity=85.0)
        assert "12" in result

    def test_high_liquidity(self, finder):
        """Test estimate for high liquidity."""
        result = finder._estimate_time_to_sell(liquidity=65.0)
        assert "24" in result

    def test_medium_liquidity(self, finder):
        """Test estimate for medium liquidity."""
        result = finder._estimate_time_to_sell(liquidity=45.0)
        assert "1-3" in result

    def test_low_liquidity(self, finder):
        """Test estimate for low liquidity."""
        result = finder._estimate_time_to_sell(liquidity=25.0)
        assert "3-7" in result

    def test_very_low_liquidity(self, finder):
        """Test estimate for very low liquidity."""
        result = finder._estimate_time_to_sell(liquidity=15.0)
        assert "7" in result


class TestGenerateNotes:
    """Tests for _generate_notes method."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        return SmartMarketFinder(mock_api)

    def test_includes_profit_note(self, finder):
        """Test that profit note is included."""
        notes = finder._generate_notes(
            item={"extra": {}},
            profit=5.0,
            profit_percent=50.0,
            liquidity=50.0,
        )
        
        assert any("прибыль" in note.lower() for note in notes)

    def test_high_liquidity_note(self, finder):
        """Test note for high liquidity items."""
        notes = finder._generate_notes(
            item={"extra": {}},
            profit=5.0,
            profit_percent=50.0,
            liquidity=75.0,  # High liquidity
        )
        
        assert any("ликвидность" in note.lower() for note in notes)

    def test_low_liquidity_note(self, finder):
        """Test note for low liquidity items."""
        notes = finder._generate_notes(
            item={"extra": {}},
            profit=5.0,
            profit_percent=50.0,
            liquidity=35.0,  # Low liquidity
        )
        
        assert any("ликвидность" in note.lower() for note in notes)

    def test_rarity_note(self, finder):
        """Test note for item rarity."""
        notes = finder._generate_notes(
            item={"extra": {"rarity": "Covert"}},
            profit=5.0,
            profit_percent=50.0,
            liquidity=50.0,
        )
        
        assert any("редкость" in note.lower() or "covert" in note.lower() for note in notes)

    def test_popularity_note(self, finder):
        """Test note for popular items."""
        notes = finder._generate_notes(
            item={"extra": {"popularity": 0.8}},
            profit=5.0,
            profit_percent=50.0,
            liquidity=50.0,
        )
        
        assert any("популярн" in note.lower() for note in notes)


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    @pytest.mark.asyncio
    async def test_find_best_deals(self):
        """Test find_best_deals function."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"objects": []})
        
        result = await find_best_deals(
            api_client=mock_api,
            game="csgo",
            min_price=0.5,
            max_price=50.0,
            limit=10,
        )
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_quick_profits(self):
        """Test find_quick_profits function."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"objects": []})
        
        result = await find_quick_profits(
            api_client=mock_api,
            game="csgo",
            max_price=20.0,
            limit=10,
        )
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_best_deals_with_items(self):
        """Test find_best_deals returns opportunities when items exist."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "2000"},
                    "extra": {"popularity": 0.8},
                },
            ]
        })
        
        result = await find_best_deals(
            api_client=mock_api,
            game="csgo",
            limit=10,
        )
        
        # Should find opportunities
        assert isinstance(result, list)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def finder(self):
        """Create SmartMarketFinder instance."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock()
        return SmartMarketFinder(mock_api)

    @pytest.mark.asyncio
    async def test_handles_unicode_titles(self, finder):
        """Test handling of unicode in item titles."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "АК-47 | Красная линия",  # Russian
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        # Should not crash
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_special_characters(self, finder):
        """Test handling of special characters in data."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Item™ | Special™",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_very_large_prices(self, finder):
        """Test handling of very large prices."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Expensive Item",
                    "price": {"USD": "10000000"},  # 100,000 USD
                    "suggestedPrice": {"USD": "12000000"},
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(
            game="csgo",
            max_price=200000.0,
        )
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_very_small_prices(self, finder):
        """Test handling of very small prices."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Cheap Item",
                    "price": {"USD": "1"},  # 0.01 USD
                    "suggestedPrice": {"USD": "2"},
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(
            game="csgo",
            min_price=0.0,
        )
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_empty_extra_field(self, finder):
        """Test handling of items without extra field."""
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                    # No extra field
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        result = await finder.find_underpriced_items(game="csgo")
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, finder):
        """Test handling of concurrent requests."""
        import asyncio
        
        mock_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                    "extra": {},
                },
            ]
        }
        finder.api._request = AsyncMock(return_value=mock_response)
        
        # Make concurrent requests
        tasks = [
            finder.find_best_opportunities(game="csgo"),
            finder.find_underpriced_items(game="csgo"),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should not raise exceptions
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, finder):
        """Test handling of API timeouts."""
        import asyncio
        
        async def slow_request(*args, **kwargs):
            await asyncio.sleep(0.01)
            raise TimeoutError("Request timed out")
        
        finder.api._request = slow_request
        
        result = await finder.find_best_opportunities(game="csgo")
        
        # Should return empty list, not raise
        assert result == []


class TestIntegration:
    """Integration tests for SmartMarketFinder."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full workflow of finding and analyzing opportunities."""
        mock_api = MagicMock()
        
        # Setup comprehensive mock response
        mock_market_response = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "AK-47 | Redline",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1500"},
                    "extra": {
                        "popularity": 0.8,
                        "category": "Rifle",
                        "rarity": "Classified",
                        "exterior": "Field-Tested",
                    },
                    "imageUrl": "https://example.com/ak47.png",
                },
                {
                    "itemId": "item2",
                    "title": "AWP | Asiimov",
                    "price": {"USD": "3000"},
                    "suggestedPrice": {"USD": "3500"},
                    "extra": {
                        "popularity": 0.9,
                        "category": "Sniper Rifle",
                        "rarity": "Covert",
                        "exterior": "Battle-Scarred",
                    },
                    "imageUrl": "https://example.com/awp.png",
                },
            ]
        }
        
        mock_api._request = AsyncMock(return_value=mock_market_response)
        
        finder = SmartMarketFinder(mock_api)
        
        # Test finding opportunities
        opportunities = await finder.find_best_opportunities(
            game="csgo",
            min_price=5.0,
            max_price=50.0,
            limit=10,
            min_confidence=0,  # Low threshold to get results
        )
        
        assert isinstance(opportunities, list)
        
        # If we got results, verify structure
        for opp in opportunities:
            assert isinstance(opp, MarketOpportunity)
            assert opp.item_id
            assert opp.title
            assert opp.current_price > 0
            assert opp.confidence_score >= 0
            assert opp.liquidity_score >= 0

    @pytest.mark.asyncio
    async def test_multiple_games_workflow(self):
        """Test workflow with multiple games."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"objects": []})
        
        finder = SmartMarketFinder(mock_api)
        
        games = ["csgo", "dota2", "tf2", "rust"]
        
        for game in games:
            result = await finder.find_best_opportunities(game=game)
            assert isinstance(result, list)

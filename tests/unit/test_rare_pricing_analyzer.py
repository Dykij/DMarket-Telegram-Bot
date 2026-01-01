"""Tests for refactored rare pricing analyzer.

Phase 2 Refactoring Tests (January 1, 2026)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.rare_pricing_analyzer import (
    RarePricingAnalyzer,
    RarityTraits,
    ScoredItem,
    find_mispriced_rare_items,
)


class TestRarityTraits:
    """Tests for RarityTraits class."""

    def test_get_traits_csgo(self):
        """Test getting CS:GO rare traits."""
        # Act
        traits = RarityTraits.get_traits("csgo")

        # Assert
        assert "Knife" in traits
        assert traits["Knife"] == 100
        assert "Doppler" in traits
        assert traits["Doppler"] == 60

    def test_get_traits_dota2(self):
        """Test getting Dota 2 rare traits."""
        # Act
        traits = RarityTraits.get_traits("dota2")

        # Assert
        assert "Arcana" in traits
        assert traits["Arcana"] == 100
        assert "Immortal" in traits

    def test_get_traits_unknown_game(self):
        """Test getting traits for unknown game returns empty."""
        # Act
        traits = RarityTraits.get_traits("unknown_game")

        # Assert
        assert traits == {}


class TestScoredItem:
    """Tests for ScoredItem class."""

    @pytest.fixture()
    def sample_item(self):
        """Create sample item."""
        return {
            "title": "AK-47 | Redline",
            "itemId": "item_123",
        }

    def test_scored_item_initialization(self, sample_item):
        """Test scored item initializes correctly."""
        # Arrange & Act
        scored = ScoredItem(
            item=sample_item,
            rarity_score=50,
            rare_traits=["StatTrak™", "Factory New"],
            current_price=100.0,
            estimated_value=120.0,
        )

        # Assert
        assert scored.item == sample_item
        assert scored.rarity_score == 50
        assert scored.rare_traits == ["StatTrak™", "Factory New"]
        assert scored.current_price == 100.0
        assert scored.estimated_value == 120.0
        assert scored.price_difference == 20.0
        assert scored.price_difference_percent == 20.0

    def test_is_undervalued_true(self, sample_item):
        """Test item identified as undervalued."""
        # Arrange
        scored = ScoredItem(
            item=sample_item,
            rarity_score=50,
            rare_traits=["Knife"],
            current_price=100.0,
            estimated_value=125.0,
        )

        # Act
        is_undervalued = scored.is_undervalued()

        # Assert
        assert is_undervalued is True

    def test_is_undervalued_false_low_difference(self, sample_item):
        """Test item not undervalued with low price difference."""
        # Arrange
        scored = ScoredItem(
            item=sample_item,
            rarity_score=50,
            rare_traits=["Knife"],
            current_price=100.0,
            estimated_value=101.0,  # Only $1 difference
        )

        # Act
        is_undervalued = scored.is_undervalued()

        # Assert
        assert is_undervalued is False

    def test_is_undervalued_false_low_percent(self, sample_item):
        """Test item not undervalued with low percentage."""
        # Arrange
        scored = ScoredItem(
            item=sample_item,
            rarity_score=50,
            rare_traits=["Knife"],
            current_price=100.0,
            estimated_value=105.0,  # Only 5% difference
        )

        # Act
        is_undervalued = scored.is_undervalued()

        # Assert
        assert is_undervalued is False

    def test_to_dict(self, sample_item):
        """Test converting to dictionary."""
        # Arrange
        scored = ScoredItem(
            item=sample_item,
            rarity_score=50,
            rare_traits=["Knife"],
            current_price=100.0,
            estimated_value=120.0,
        )

        # Act
        result = scored.to_dict(game="csgo")

        # Assert
        assert result["item"] == sample_item
        assert result["rarity_score"] == 50
        assert result["rare_traits"] == ["Knife"]
        assert result["current_price"] == 100.0
        assert result["estimated_value"] == 120.0
        assert result["price_difference"] == 20.0
        assert result["price_difference_percent"] == 20.0
        assert result["game"] == "csgo"


class TestRarePricingAnalyzer:
    """Tests for RarePricingAnalyzer class."""

    @pytest.fixture()
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_market_items = AsyncMock()
        api._close_client = AsyncMock()
        return api

    @pytest.fixture()
    def analyzer(self, mock_api):
        """Create analyzer instance."""
        return RarePricingAnalyzer(api_client=mock_api)

    def test_extract_price_dict_format(self, analyzer):
        """Test extracting price from dict format."""
        # Arrange
        item = {"price": {"amount": 10000}}  # $100.00

        # Act
        price = analyzer._extract_price(item)

        # Assert
        assert price == 100.0

    def test_extract_price_number_format(self, analyzer):
        """Test extracting price from number format."""
        # Arrange
        item = {"price": 50.0}

        # Act
        price = analyzer._extract_price(item)

        # Assert
        assert price == 50.0

    def test_extract_price_missing(self, analyzer):
        """Test extracting price when missing."""
        # Arrange
        item = {}

        # Act
        price = analyzer._extract_price(item)

        # Assert
        assert price is None

    def test_is_price_valid_true(self, analyzer):
        """Test price validation returns true."""
        # Act
        is_valid = analyzer._is_price_valid(
            price=50.0,
            min_price=10.0,
            max_price=100.0,
        )

        # Assert
        assert is_valid is True

    def test_is_price_valid_false_none(self, analyzer):
        """Test price validation fails for None."""
        # Act
        is_valid = analyzer._is_price_valid(
            price=None,
            min_price=10.0,
            max_price=100.0,
        )

        # Assert
        assert is_valid is False

    def test_is_price_valid_false_too_low(self, analyzer):
        """Test price validation fails when too low."""
        # Act
        is_valid = analyzer._is_price_valid(
            price=5.0,
            min_price=10.0,
            max_price=100.0,
        )

        # Assert
        assert is_valid is False

    def test_is_price_valid_false_too_high(self, analyzer):
        """Test price validation fails when too high."""
        # Act
        is_valid = analyzer._is_price_valid(
            price=150.0,
            min_price=10.0,
            max_price=100.0,
        )

        # Assert
        assert is_valid is False

    def test_calculate_rarity_score_with_traits(self, analyzer):
        """Test rarity score calculation with traits."""
        # Arrange
        item = {}
        title = "★ Karambit | Doppler Factory New"
        game = "csgo"

        # Act
        score, traits = analyzer._calculate_rarity_score(item, title, game)

        # Assert
        assert score > 0
        assert "★" in traits
        assert "Doppler" in traits
        assert "Factory New" in traits

    def test_calculate_rarity_score_no_traits(self, analyzer):
        """Test rarity score calculation without traits."""
        # Arrange
        item = {}
        title = "Regular Item"
        game = "csgo"

        # Act
        score, traits = analyzer._calculate_rarity_score(item, title, game)

        # Assert
        assert score == 0
        assert traits == []

    def test_get_float_bonus_extremely_low(self, analyzer):
        """Test float bonus for extremely low float."""
        # Arrange
        item = {"float": 0.005}

        # Act
        bonus, trait = analyzer._get_float_bonus(item)

        # Assert
        assert bonus == 70
        assert "Float: 0.0050" in trait

    def test_get_float_bonus_very_low(self, analyzer):
        """Test float bonus for very low float."""
        # Arrange
        item = {"float": 0.05}

        # Act
        bonus, trait = analyzer._get_float_bonus(item)

        # Assert
        assert bonus == 40
        assert "Float: 0.0500" in trait

    def test_get_float_bonus_no_bonus(self, analyzer):
        """Test no float bonus for normal float."""
        # Arrange
        item = {"float": 0.5}

        # Act
        bonus, trait = analyzer._get_float_bonus(item)

        # Assert
        assert bonus == 0
        assert trait is None

    def test_get_float_bonus_missing(self, analyzer):
        """Test float bonus when float is missing."""
        # Arrange
        item = {}

        # Act
        bonus, trait = analyzer._get_float_bonus(item)

        # Assert
        assert bonus == 0
        assert trait is None

    def test_extract_suggested_price_dict(self, analyzer):
        """Test extracting suggested price from dict."""
        # Arrange
        item = {"suggestedPrice": {"amount": 15000}}  # $150.00

        # Act
        suggested = analyzer._extract_suggested_price(item)

        # Assert
        assert suggested == 150.0

    def test_extract_suggested_price_number(self, analyzer):
        """Test extracting suggested price from number."""
        # Arrange
        item = {"suggestedPrice": 75.0}

        # Act
        suggested = analyzer._extract_suggested_price(item)

        # Assert
        assert suggested == 75.0

    def test_extract_suggested_price_missing(self, analyzer):
        """Test extracting suggested price when missing."""
        # Arrange
        item = {}

        # Act
        suggested = analyzer._extract_suggested_price(item)

        # Assert
        assert suggested == 0.0

    def test_estimate_value_with_suggested_price(self, analyzer):
        """Test value estimation with suggested price."""
        # Act
        value = analyzer._estimate_value(
            price=100.0,
            suggested_price=120.0,
            rarity_score=50,
        )

        # Assert
        assert value >= 120.0

    def test_estimate_value_without_suggested_price(self, analyzer):
        """Test value estimation without suggested price."""
        # Act
        value = analyzer._estimate_value(
            price=100.0,
            suggested_price=0.0,
            rarity_score=100,
        )

        # Assert
        assert value > 100.0  # Should be higher than current price

    @pytest.mark.asyncio()
    async def test_fetch_market_items(self, analyzer, mock_api):
        """Test fetching market items."""
        # Arrange
        mock_api.get_market_items.return_value = {
            "items": [{"title": "Item 1"}, {"title": "Item 2"}]
        }

        # Act
        items = await analyzer._fetch_market_items(
            game="csgo",
            min_price=10.0,
            max_price=100.0,
        )

        # Assert
        assert len(items) == 2
        mock_api.get_market_items.assert_called_once_with(
            game="csgo",
            limit=500,
            offset=0,
            price_from=10.0,
            price_to=100.0,
        )

    def test_analyze_single_item_valid(self, analyzer):
        """Test analyzing valid rare item."""
        # Arrange
        item = {
            "title": "★ Karambit | Doppler",
            "price": {"amount": 50000},  # $500
            "suggestedPrice": {"amount": 60000},  # $600
        }

        # Act
        scored = analyzer._analyze_single_item(
            item=item,
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
        )

        # Assert
        assert scored is not None
        assert scored.rarity_score > 30
        assert scored.current_price == 500.0

    def test_analyze_single_item_no_title(self, analyzer):
        """Test analyzing item without title."""
        # Arrange
        item = {"price": {"amount": 10000}}

        # Act
        scored = analyzer._analyze_single_item(
            item=item,
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
        )

        # Assert
        assert scored is None

    def test_analyze_single_item_invalid_price(self, analyzer):
        """Test analyzing item with invalid price."""
        # Arrange
        item = {
            "title": "★ Knife",
            "price": {"amount": 500},  # $5 (below min_price)
        }

        # Act
        scored = analyzer._analyze_single_item(
            item=item,
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
        )

        # Assert
        assert scored is None

    def test_analyze_single_item_low_rarity(self, analyzer):
        """Test analyzing item with low rarity score."""
        # Arrange
        item = {
            "title": "Regular Item",  # No rare traits
            "price": {"amount": 5000},  # $50
        }

        # Act
        scored = analyzer._analyze_single_item(
            item=item,
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
        )

        # Assert
        assert scored is None  # Rarity score <= 30

    @pytest.mark.asyncio()
    async def test_find_mispriced_rare_items_success(self, analyzer, mock_api):
        """Test finding mispriced rare items."""
        # Arrange
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Karambit | Doppler Factory New",
                    "price": {"amount": 50000},  # $500
                    "suggestedPrice": {"amount": 70000},  # $700
                }
            ]
        }

        # Act
        results = await analyzer.find_mispriced_rare_items(
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
            max_results=5,
        )

        # Assert
        assert len(results) > 0
        assert results[0]["game"] == "csgo"
        assert results[0]["rarity_score"] > 30

    @pytest.mark.asyncio()
    async def test_find_mispriced_rare_items_no_results(self, analyzer, mock_api):
        """Test finding rare items with no results."""
        # Arrange
        mock_api.get_market_items.return_value = {"items": []}

        # Act
        results = await analyzer.find_mispriced_rare_items(
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
            max_results=5,
        )

        # Assert
        assert results == []

    @pytest.mark.asyncio()
    async def test_find_mispriced_rare_items_error(self, analyzer, mock_api):
        """Test error handling in find rare items."""
        # Arrange
        mock_api.get_market_items.side_effect = Exception("API Error")

        # Act
        results = await analyzer.find_mispriced_rare_items(
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
            max_results=5,
        )

        # Assert
        assert results == []

    @pytest.mark.asyncio()
    async def test_context_manager(self, mock_api):
        """Test async context manager."""
        # Arrange
        analyzer = RarePricingAnalyzer(api_client=mock_api)

        # Act
        async with analyzer as ctx:
            assert ctx.api_client == mock_api

        # Assert
        assert not mock_api._close_client.called  # Should not close external client

    @pytest.mark.asyncio()
    async def test_legacy_function(self, mock_api):
        """Test legacy function interface."""
        # Arrange
        mock_api.get_market_items.return_value = {"items": []}

        # Act
        results = await find_mispriced_rare_items(
            game="csgo",
            min_price=10.0,
            max_price=1000.0,
            max_results=5,
            dmarket_api=mock_api,
        )

        # Assert
        assert results == []
        mock_api.get_market_items.assert_called_once()

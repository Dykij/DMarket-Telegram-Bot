"""Phase 4 extended tests for market_analysis.py module.

This module contains comprehensive tests for market analysis functionality
including price changes analysis, trending items, volatility analysis,
market depth analysis, and market report generation.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestExtractPriceFromItem:
    """Tests for _extract_price_from_item helper function."""

    def test_extract_price_dict_with_amount(self):
        """Test extraction from price dict with amount."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": {"amount": 1000, "currency": "USD"}}
        result = _extract_price_from_item(item)
        # Price in cents (1000) converted to dollars = 10.0
        assert result == 10.0

    def test_extract_price_numeric(self):
        """Test extraction from numeric price (in cents)."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": 2500}
        result = _extract_price_from_item(item)
        assert result == 25.0

    def test_extract_price_string_with_dollar(self):
        """Test extraction from string price with dollar sign."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": "$10.00"}
        result = _extract_price_from_item(item)
        assert result == 10.0

    def test_extract_price_best_price_dict(self):
        """Test extraction from bestPrice dict."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"bestPrice": {"amount": 500, "currency": "USD"}}
        result = _extract_price_from_item(item)
        assert result == 5.0

    def test_extract_price_best_price_numeric(self):
        """Test extraction from bestPrice numeric."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"bestPrice": 1500}
        result = _extract_price_from_item(item)
        assert result == 15.0

    def test_extract_price_suggested_price(self):
        """Test extraction from suggestedPrice field."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"suggestedPrice": 800}
        result = _extract_price_from_item(item)
        assert result == 8.0

    def test_extract_price_market_price(self):
        """Test extraction from marketPrice field."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"marketPrice": {"amount": 1200}}
        result = _extract_price_from_item(item)
        assert result == 12.0

    def test_extract_price_average_price(self):
        """Test extraction from averagePrice field."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"averagePrice": 950}
        result = _extract_price_from_item(item)
        assert result == 9.5

    def test_extract_price_empty_item(self):
        """Test extraction from empty item returns 0."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {}
        result = _extract_price_from_item(item)
        assert result == 0.0

    def test_extract_price_invalid_value(self):
        """Test extraction with invalid price value returns 0."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": "invalid"}
        result = _extract_price_from_item(item)
        assert result == 0.0

    def test_extract_price_float_value(self):
        """Test extraction with float price."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": 1250.5}
        result = _extract_price_from_item(item)
        assert result == 12.505


class TestCalculatePopularityScore:
    """Tests for _calculate_popularity_score helper function."""

    def test_popularity_basic_calculation(self):
        """Test basic popularity score calculation."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {"salesVolume": 10, "offersCount": 5}
        result = _calculate_popularity_score(item)
        # popularity = 10 * 2 * (10 / (5 + 1)) = 20 * 1.667 = 33.33
        assert result > 0

    def test_popularity_high_sales(self):
        """Test popularity with high sales volume."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {"salesVolume": 100, "offersCount": 10}
        result = _calculate_popularity_score(item)
        # popularity = 100 * 2 * (100 / 11) = 200 * 9.09 ≈ 1818
        assert result > 1000

    def test_popularity_zero_sales(self):
        """Test popularity with zero sales."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {"salesVolume": 0, "offersCount": 5}
        result = _calculate_popularity_score(item)
        assert result == 0.0

    def test_popularity_zero_offers(self):
        """Test popularity with zero offers."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {"salesVolume": 10, "offersCount": 0}
        result = _calculate_popularity_score(item)
        # popularity = 10 * 2 * (10 / 1) = 200
        assert result == 200.0

    def test_popularity_empty_item(self):
        """Test popularity with missing fields."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {}
        result = _calculate_popularity_score(item)
        assert result == 0.0


class TestGetMarketDirection:
    """Tests for _get_market_direction helper function."""

    def test_market_direction_up(self):
        """Test market direction when mostly up."""
        from src.dmarket.market_analysis import _get_market_direction

        price_changes = [
            {"direction": "up"},
            {"direction": "up"},
            {"direction": "up"},
            {"direction": "down"},
        ]
        result = _get_market_direction(price_changes)
        assert result == "up"

    def test_market_direction_down(self):
        """Test market direction when mostly down."""
        from src.dmarket.market_analysis import _get_market_direction

        price_changes = [
            {"direction": "down"},
            {"direction": "down"},
            {"direction": "down"},
            {"direction": "up"},
        ]
        result = _get_market_direction(price_changes)
        assert result == "down"

    def test_market_direction_stable(self):
        """Test market direction when balanced."""
        from src.dmarket.market_analysis import _get_market_direction

        price_changes = [
            {"direction": "up"},
            {"direction": "down"},
        ]
        result = _get_market_direction(price_changes)
        assert result == "stable"

    def test_market_direction_empty(self):
        """Test market direction with empty list."""
        from src.dmarket.market_analysis import _get_market_direction

        result = _get_market_direction([])
        assert result == "stable"


class TestCalculateMarketVolatilityLevel:
    """Tests for _calculate_market_volatility_level helper function."""

    def test_volatility_low(self):
        """Test low volatility level."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        volatile_items = [
            {"volatility_score": 5},
            {"volatility_score": 7},
            {"volatility_score": 8},
        ]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "low"

    def test_volatility_medium(self):
        """Test medium volatility level."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        volatile_items = [
            {"volatility_score": 12},
            {"volatility_score": 15},
            {"volatility_score": 18},
        ]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "medium"

    def test_volatility_high(self):
        """Test high volatility level."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        volatile_items = [
            {"volatility_score": 25},
            {"volatility_score": 30},
            {"volatility_score": 35},
        ]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "high"

    def test_volatility_empty(self):
        """Test volatility with empty list."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        result = _calculate_market_volatility_level([])
        assert result == "low"


class TestExtractTrendingCategories:
    """Tests for _extract_trending_categories helper function."""

    def test_trending_categories_knives(self):
        """Test extraction of knife category."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Karambit | Doppler"},
            {"market_hash_name": "Butterfly Knife | Fade"},
        ]
        result = _extract_trending_categories(trending_items)
        assert "Ножи" in result

    def test_trending_categories_rifles(self):
        """Test extraction of rifle categories."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "AK-47 | Redline"},
            {"market_hash_name": "AWP | Dragon Lore"},
        ]
        result = _extract_trending_categories(trending_items)
        assert any(
            cat in result for cat in ["Штурмовые винтовки", "Снайперские винтовки"]
        )

    def test_trending_categories_empty(self):
        """Test extraction with empty list."""
        from src.dmarket.market_analysis import _extract_trending_categories

        result = _extract_trending_categories([])
        assert result == ["Нет данных"]

    def test_trending_categories_mixed(self):
        """Test extraction with mixed categories."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Karambit | Fade"},
            {"market_hash_name": "AWP | Asiimov"},
            {"market_hash_name": "Gloves | Sport Gloves"},
            {"market_hash_name": "Sticker | iBUYPOWER"},
        ]
        result = _extract_trending_categories(trending_items)
        assert len(result) <= 3  # Max 3 categories

    def test_trending_categories_other(self):
        """Test extraction falls back to 'Другое' for unknown items."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Unknown Item Name"},
            {"market_hash_name": "Another Unknown"},
        ]
        result = _extract_trending_categories(trending_items)
        assert "Другое" in result


class TestGenerateMarketRecommendations:
    """Tests for _generate_market_recommendations helper function."""

    def test_recommendations_rising_items(self):
        """Test recommendations for rising items."""
        from src.dmarket.market_analysis import _generate_market_recommendations

        results = [
            [{"direction": "up", "market_hash_name": "AK-47 | Redline"}],
            [],
            [],
        ]
        recommendations = _generate_market_recommendations(results)
        assert len(recommendations) > 0
        assert any("покупки" in rec or "ростом" in rec for rec in recommendations)

    def test_recommendations_falling_items(self):
        """Test recommendations for falling items."""
        from src.dmarket.market_analysis import _generate_market_recommendations

        results = [
            [{"direction": "down", "market_hash_name": "M4A1-S | Hyper Beast"}],
            [],
            [],
        ]
        recommendations = _generate_market_recommendations(results)
        assert len(recommendations) > 0
        assert any(
            "падающ" in rec.lower() or "избегайте" in rec.lower()
            for rec in recommendations
        )

    def test_recommendations_trending(self):
        """Test recommendations for trending items."""
        from src.dmarket.market_analysis import _generate_market_recommendations

        results = [
            [],
            [{"market_hash_name": "AWP | Dragon Lore"}],
            [],
        ]
        recommendations = _generate_market_recommendations(results)
        assert len(recommendations) > 0
        assert any(
            "популярн" in rec.lower() or "спрос" in rec.lower()
            for rec in recommendations
        )

    def test_recommendations_volatile(self):
        """Test recommendations for volatile items."""
        from src.dmarket.market_analysis import _generate_market_recommendations

        results = [
            [],
            [],
            [{"market_hash_name": "Case Hardened | Blue Gem"}],
        ]
        recommendations = _generate_market_recommendations(results)
        assert len(recommendations) > 0
        assert any(
            "волатильн" in rec.lower() or "осторожн" in rec.lower()
            for rec in recommendations
        )

    def test_recommendations_no_data(self):
        """Test recommendations with no data."""
        from src.dmarket.market_analysis import _generate_market_recommendations

        results = [[], [], []]
        recommendations = _generate_market_recommendations(results)
        assert len(recommendations) == 1
        assert "Недостаточно данных" in recommendations[0]


class TestAnalyzePriceChangesUnit:
    """Unit tests for analyze_price_changes function."""

    @pytest.mark.asyncio()
    async def test_analyze_price_changes_empty_response(self):
        """Test price changes analysis with empty API response."""
        from src.dmarket.market_analysis import analyze_price_changes

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value=None)

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await analyze_price_changes(
                game="csgo",
                dmarket_api=mock_api,
            )
            assert result == []

    @pytest.mark.asyncio()
    async def test_analyze_price_changes_no_items_key(self):
        """Test price changes analysis when response has no items key."""
        from src.dmarket.market_analysis import analyze_price_changes

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={"other": "data"})

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await analyze_price_changes(
                game="csgo",
                dmarket_api=mock_api,
            )
            assert result == []


class TestFindTrendingItemsUnit:
    """Unit tests for find_trending_items function."""

    @pytest.mark.asyncio()
    async def test_find_trending_items_empty_response(self):
        """Test trending items with empty API response."""
        from src.dmarket.market_analysis import find_trending_items

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value=None)

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await find_trending_items(
                game="csgo",
                dmarket_api=mock_api,
            )
            assert result == []

    @pytest.mark.asyncio()
    async def test_find_trending_items_no_items_key(self):
        """Test trending items when response has no items key."""
        from src.dmarket.market_analysis import find_trending_items

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={"other": "data"})

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await find_trending_items(
                game="csgo",
                dmarket_api=mock_api,
            )
            assert result == []


class TestAnalyzeMarketVolatilityUnit:
    """Unit tests for analyze_market_volatility function."""

    @pytest.mark.asyncio()
    async def test_analyze_volatility_empty_response(self):
        """Test volatility analysis with empty response."""
        from src.dmarket.market_analysis import analyze_market_volatility

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value=None)

        with (
            patch(
                "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
            ),
            patch(
                "src.dmarket.market_analysis._get_historical_prices",
                AsyncMock(return_value={}),
            ),
        ):
            result = await analyze_market_volatility(
                game="csgo",
                dmarket_api=mock_api,
            )
            assert result == []


class TestAnalyzeMarketDepthUnit:
    """Unit tests for analyze_market_depth function."""

    @pytest.mark.asyncio()
    async def test_market_depth_empty_items_list(self):
        """Test market depth with empty items list after fetching."""
        from src.dmarket.market_analysis import analyze_market_depth

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={"items": []})

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await analyze_market_depth(
                game="csgo",
                items=None,
                dmarket_api=mock_api,
            )
            assert result["items_analyzed"] == 0
            assert result["market_depth"] == []

    @pytest.mark.asyncio()
    async def test_market_depth_no_aggregated_prices(self):
        """Test market depth when aggregated prices API returns empty."""
        from src.dmarket.market_analysis import analyze_market_depth

        mock_api = AsyncMock()
        mock_api.get_aggregated_prices_bulk = AsyncMock(return_value=None)

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await analyze_market_depth(
                game="csgo",
                items=["Test Item"],
                dmarket_api=mock_api,
            )
            assert result["items_analyzed"] == 0


class TestGenerateMarketReportUnit:
    """Unit tests for generate_market_report function."""

    @pytest.mark.asyncio()
    async def test_generate_report_error_handling(self):
        """Test market report error handling."""
        from src.dmarket.market_analysis import generate_market_report

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(side_effect=Exception("API Error"))

        result = await generate_market_report(
            game="csgo",
            dmarket_api=mock_api,
        )
        # Should return error structure, not raise exception
        assert "game" in result
        assert "timestamp" in result


class TestGetHistoricalPricesUnit:
    """Unit tests for _get_historical_prices helper function."""

    @pytest.mark.asyncio()
    async def test_get_historical_prices_empty_response(self):
        """Test historical prices with empty API response."""
        from src.dmarket.market_analysis import _get_historical_prices

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value=None)

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await _get_historical_prices(
                game="csgo",
                period_hours=24,
                dmarket_api=mock_api,
            )
            assert result == {}

    @pytest.mark.asyncio()
    async def test_get_historical_prices_no_items_key(self):
        """Test historical prices when response has no items key."""
        from src.dmarket.market_analysis import _get_historical_prices

        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={"other": "data"})

        with patch(
            "src.dmarket.market_analysis.rate_limiter.wait_if_needed", AsyncMock()
        ):
            result = await _get_historical_prices(
                game="csgo",
                period_hours=24,
                dmarket_api=mock_api,
            )
            assert result == {}


class TestEdgeCases:
    """Edge case tests for market analysis module."""

    def test_extract_price_none_value(self):
        """Test price extraction with None price."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": None}
        result = _extract_price_from_item(item)
        assert result == 0.0

    def test_extract_price_negative(self):
        """Test price extraction with negative value."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": -100}
        result = _extract_price_from_item(item)
        # Negative price converted to dollars
        assert result == -1.0

    def test_popularity_score_missing_fields(self):
        """Test popularity score with missing fields."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {"otherField": "value"}
        result = _calculate_popularity_score(item)
        assert result == 0.0

    def test_market_direction_all_up(self):
        """Test market direction when all items are up."""
        from src.dmarket.market_analysis import _get_market_direction

        price_changes = [{"direction": "up"}] * 10
        result = _get_market_direction(price_changes)
        assert result == "up"

    def test_market_direction_all_down(self):
        """Test market direction when all items are down."""
        from src.dmarket.market_analysis import _get_market_direction

        price_changes = [{"direction": "down"}] * 10
        result = _get_market_direction(price_changes)
        assert result == "down"

    def test_volatility_single_item(self):
        """Test volatility calculation with single item."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        volatile_items = [{"volatility_score": 15}]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "medium"

    def test_trending_categories_lowercase(self):
        """Test trending categories with lowercase names."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "awp | dragon lore"},
            {"market_hash_name": "AK-47 | REDLINE"},
        ]
        result = _extract_trending_categories(trending_items)
        assert len(result) > 0

    def test_extract_price_empty_dict_amount(self):
        """Test price extraction with empty dict for amount."""
        from src.dmarket.market_analysis import _extract_price_from_item

        item = {"price": {"amount": 0}}
        result = _extract_price_from_item(item)
        assert result == 0.0

    def test_popularity_very_high_sales(self):
        """Test popularity with very high sales volume."""
        from src.dmarket.market_analysis import _calculate_popularity_score

        item = {"salesVolume": 10000, "offersCount": 100}
        result = _calculate_popularity_score(item)
        assert result > 100000

    def test_market_direction_single_item(self):
        """Test market direction with single item."""
        from src.dmarket.market_analysis import _get_market_direction

        price_changes = [{"direction": "up"}]
        result = _get_market_direction(price_changes)
        # Single item cannot be 1.5x more than 0, so should be stable
        assert result in {"up", "stable"}

    def test_volatility_boundary_10(self):
        """Test volatility at boundary of 10."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        volatile_items = [{"volatility_score": 10}]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "medium"

    def test_volatility_boundary_20(self):
        """Test volatility at boundary of 20."""
        from src.dmarket.market_analysis import _calculate_market_volatility_level

        volatile_items = [{"volatility_score": 20}]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "high"


class TestIntegration:
    """Integration tests for market analysis module."""

    def test_full_helper_flow(self):
        """Test full analysis flow with all helper functions."""
        from src.dmarket.market_analysis import (
            _calculate_market_volatility_level,
            _calculate_popularity_score,
            _extract_price_from_item,
            _extract_trending_categories,
            _get_market_direction,
        )

        # Create sample data
        item = {"price": 1000, "salesVolume": 50, "offersCount": 10}
        price_changes = [
            {"direction": "up", "market_hash_name": "Item1"},
            {"direction": "up", "market_hash_name": "Item2"},
            {"direction": "down", "market_hash_name": "Item3"},
        ]
        volatile_items = [
            {"volatility_score": 15},
            {"volatility_score": 18},
        ]
        trending_items = [
            {"market_hash_name": "AWP | Dragon Lore"},
            {"market_hash_name": "Karambit | Fade"},
        ]

        # Test all helper functions
        price = _extract_price_from_item(item)
        assert price == 10.0

        popularity = _calculate_popularity_score(item)
        assert popularity > 0

        direction = _get_market_direction(price_changes)
        assert direction == "up"

        volatility = _calculate_market_volatility_level(volatile_items)
        assert volatility in {"low", "medium", "high"}

        categories = _extract_trending_categories(trending_items)
        assert len(categories) > 0

    def test_recommendations_with_all_data(self):
        """Test recommendations with all types of data."""
        from src.dmarket.market_analysis import _generate_market_recommendations

        results = [
            [
                {"direction": "up", "market_hash_name": "Item1"},
                {"direction": "down", "market_hash_name": "Item2"},
            ],
            [{"market_hash_name": "TrendingItem"}],
            [{"market_hash_name": "VolatileItem"}],
        ]
        recommendations = _generate_market_recommendations(results)
        # Should have multiple recommendations
        assert len(recommendations) >= 3

    def test_trending_categories_gloves(self):
        """Test trending categories with gloves."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Sport Gloves | Hedge Maze"},
            {"market_hash_name": "Driver Gloves | Crimson Weave"},
        ]
        result = _extract_trending_categories(trending_items)
        assert "Перчатки" in result

    def test_trending_categories_pistols(self):
        """Test trending categories with pistols."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Glock-18 | Fade"},
            {"market_hash_name": "USP-S | Kill Confirmed"},
            {"market_hash_name": "Desert Eagle | Blaze"},
        ]
        result = _extract_trending_categories(trending_items)
        assert "Пистолеты" in result

    def test_trending_categories_stickers(self):
        """Test trending categories with stickers."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Sticker | Natus Vincere"},
            {"market_hash_name": "Sticker | Titan (Holo)"},
        ]
        result = _extract_trending_categories(trending_items)
        assert "Наклейки" in result

    def test_trending_categories_cases(self):
        """Test trending categories with cases."""
        from src.dmarket.market_analysis import _extract_trending_categories

        trending_items = [
            {"market_hash_name": "Operation Breakout Case"},
            {"market_hash_name": "Chroma 2 Case"},
        ]
        result = _extract_trending_categories(trending_items)
        assert "Кейсы" in result

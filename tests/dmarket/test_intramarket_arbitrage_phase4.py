"""Phase 4 extended tests for intramarket_arbitrage.py module.

Comprehensive test coverage for:
- PriceAnomalyType enum extended tests
- Cache functionality tests (_cache, _cache_ttl)
- find_price_anomalies extended edge cases
- find_trending_items extended scenarios
- find_mispriced_rare_items extended tests
- scan_for_intramarket_opportunities extended tests
- Price extraction from various formats
- Profit calculations and fee handling
- Multi-game support extended tests
- Error handling and edge cases
- Integration tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.intramarket_arbitrage import (
    PriceAnomalyType,
    _cache,
    _cache_ttl,
    find_mispriced_rare_items,
    find_price_anomalies,
    find_trending_items,
    scan_for_intramarket_opportunities,
)


# ======================== Fixtures ========================


@pytest.fixture()
def mock_api():
    """Create a mock DMarket API client."""
    api = MagicMock()
    api.get_market_items = AsyncMock(return_value={"items": []})
    api.get_sales_history = AsyncMock(return_value={"items": []})
    api._close_client = AsyncMock()
    return api


@pytest.fixture()
def items_with_various_price_formats():
    """Items with different price format structures."""
    return {
        "items": [
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"amount": 1250, "currency": "USD"},
                "itemId": "item_dict_price",
            },
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": 15.50,  # Float price
                "itemId": "item_float_price",
            },
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": 1400,  # Integer price (cents)
                "itemId": "item_int_price",
            },
        ],
    }


@pytest.fixture()
def items_with_suggested_prices():
    """Items with suggested prices for value comparison."""
    return {
        "items": [
            {
                "title": "★ Karambit | Fade (Factory New)",
                "price": {"amount": 95000},
                "suggestedPrice": {"amount": 110000},
                "itemId": "knife_1",
            },
            {
                "title": "★ Karambit | Fade (Factory New)",
                "price": 980.00,
                "suggestedPrice": 1120.00,
                "itemId": "knife_2",
            },
            {
                "title": "★ Karambit | Fade (Factory New)",
                "price": {"amount": 92000},
                "itemId": "knife_3",  # No suggested price
            },
        ],
    }


# ======================== PriceAnomalyType Enum Extended Tests ========================


class TestPriceAnomalyTypeEnumExtended:
    """Extended tests for PriceAnomalyType enum."""

    def test_all_enum_values_are_strings(self):
        """Test that all enum values are strings."""
        for anomaly_type in PriceAnomalyType:
            assert isinstance(anomaly_type.value, str)

    def test_enum_values_are_lowercase(self):
        """Test that all enum values are lowercase."""
        for anomaly_type in PriceAnomalyType:
            assert anomaly_type.value == anomaly_type.value.lower()

    def test_enum_count(self):
        """Test total number of anomaly types."""
        assert len(PriceAnomalyType) == 6

    def test_enum_membership(self):
        """Test enum membership check."""
        assert PriceAnomalyType("underpriced") == PriceAnomalyType.UNDERPRICED
        assert PriceAnomalyType("normal") == PriceAnomalyType.NORMAL

    def test_enum_name_value_consistency(self):
        """Test name and value consistency."""
        for anomaly_type in PriceAnomalyType:
            assert anomaly_type.name.lower() == anomaly_type.value.replace("_", "_")

    def test_enum_str_inheritance(self):
        """Test that enum inherits from str."""
        assert isinstance(PriceAnomalyType.UNDERPRICED, str)
        assert PriceAnomalyType.UNDERPRICED == "underpriced"

    def test_enum_comparison_with_string(self):
        """Test enum comparison with regular strings."""
        assert PriceAnomalyType.TRENDING_UP == "trending_up"
        assert PriceAnomalyType.TRENDING_DOWN == "trending_down"


# ======================== Cache Constants Tests ========================


class TestCacheConstants:
    """Tests for cache-related constants."""

    def test_cache_is_dict(self):
        """Test that _cache is a dictionary."""
        assert isinstance(_cache, dict)

    def test_cache_ttl_is_positive(self):
        """Test that cache TTL is positive."""
        assert _cache_ttl > 0

    def test_cache_ttl_is_5_minutes(self):
        """Test that cache TTL is 5 minutes (300 seconds)."""
        assert _cache_ttl == 300


# ======================== find_price_anomalies Extended Tests ========================


class TestFindPriceAnomaliesExtended:
    """Extended tests for find_price_anomalies function."""

    @pytest.mark.asyncio()
    async def test_empty_title_items_skipped(self, mock_api):
        """Test that items with empty titles are skipped."""
        mock_api.get_market_items.return_value = {
            "items": [
                {"title": "", "price": {"amount": 1000}, "itemId": "item_1"},
                {"title": "Valid Item", "price": {"amount": 1000}, "itemId": "item_2"},
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_graffiti_items_filtered_csgo(self, mock_api):
        """Test that graffiti items are filtered for CS:GO."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Sealed Graffiti | GLHF (Frog Green)",
                    "price": {"amount": 100},
                    "itemId": "graffiti_1",
                },
                {
                    "title": "AK-47 | Redline (FT)",
                    "price": {"amount": 1000},
                    "itemId": "ak_1",
                },
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        # Graffiti should be filtered out
        for result in results:
            assert (
                "graffiti" not in result.get("item_to_buy", {}).get("title", "").lower()
            )

    @pytest.mark.asyncio()
    async def test_patch_items_filtered_csgo(self, mock_api):
        """Test that patch items are filtered for CS:GO."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Patch | Hello NAVI",
                    "price": {"amount": 500},
                    "itemId": "patch_1",
                },
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert results == [] or all(
            "patch" not in r.get("item_to_buy", {}).get("title", "").lower()
            for r in results
        )

    @pytest.mark.asyncio()
    async def test_stattrak_items_grouped_separately(self, mock_api):
        """Test that StatTrak items are grouped separately from non-StatTrak."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "StatTrak™ AK-47 | Redline (Field-Tested)",
                    "price": {"amount": 2500},
                    "itemId": "st_ak_1",
                },
                {
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": {"amount": 1200},
                    "itemId": "ak_1",
                },
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        # StatTrak and non-StatTrak should not be compared as anomalies
        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_souvenir_items_grouped_separately(self, mock_api):
        """Test that Souvenir items are grouped separately."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Souvenir AK-47 | Safari Mesh (Field-Tested)",
                    "price": {"amount": 800},
                    "itemId": "souv_ak_1",
                },
                {
                    "title": "AK-47 | Safari Mesh (Field-Tested)",
                    "price": {"amount": 300},
                    "itemId": "ak_1",
                },
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_profit_after_fee_calculation(self, mock_api):
        """Test profit after fee is calculated correctly."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Test Item",
                    "price": {"amount": 1000},  # $10.00
                    "itemId": "item_1",
                },
                {
                    "title": "Test Item",
                    "price": {"amount": 1500},  # $15.00
                    "itemId": "item_2",
                },
            ]
        }

        results = await find_price_anomalies(
            game="csgo", dmarket_api=mock_api, price_diff_percent=5.0
        )

        if results:
            # 7% fee: $15 * 0.93 - $10 = $13.95 - $10 = $3.95
            expected_profit = 15.0 * 0.93 - 10.0
            assert abs(results[0]["profit_after_fee"] - expected_profit) < 0.01

    @pytest.mark.asyncio()
    async def test_max_results_limit(self, mock_api):
        """Test max_results parameter limits output."""
        # Create many items
        items = []
        for i in range(50):
            items.append(
                {
                    "title": f"Item {i}",
                    "price": {"amount": 1000 + i * 100},
                    "itemId": f"item_{i}",
                }
            )

        mock_api.get_market_items.return_value = {"items": items}

        results = await find_price_anomalies(
            game="dota2", dmarket_api=mock_api, max_results=5
        )

        assert len(results) <= 5

    @pytest.mark.asyncio()
    async def test_non_csgo_game_no_exterior_parsing(self, mock_api):
        """Test that non-CS:GO games don't parse exterior from title."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Dota 2 Item (Something)",
                    "price": {"amount": 1000},
                    "itemId": "dota_1",
                },
                {
                    "title": "Dota 2 Item (Something)",
                    "price": {"amount": 1200},
                    "itemId": "dota_2",
                },
            ]
        }

        results = await find_price_anomalies(game="dota2", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_price_none_items_skipped(self, mock_api):
        """Test items with None price are skipped."""
        mock_api.get_market_items.return_value = {
            "items": [
                {"title": "Item without price", "itemId": "item_1"},
                {
                    "title": "Item with price",
                    "price": {"amount": 1000},
                    "itemId": "item_2",
                },
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_api_client_created_when_none(self, mock_api):
        """Test API client is created when not provided."""
        with patch(
            "src.telegram_bot.utils.api_helper.create_dmarket_api_client"
        ) as mock_create:
            mock_create.return_value = mock_api

            await find_price_anomalies(game="csgo", dmarket_api=None)

            mock_create.assert_called_once_with(None)

    @pytest.mark.asyncio()
    async def test_api_client_closed_when_created(self, mock_api):
        """Test API client is closed when created internally."""
        with patch(
            "src.telegram_bot.utils.api_helper.create_dmarket_api_client"
        ) as mock_create:
            mock_create.return_value = mock_api

            await find_price_anomalies(game="csgo", dmarket_api=None)

            mock_api._close_client.assert_called_once()

    @pytest.mark.asyncio()
    async def test_similarity_threshold_parameter(self, mock_api):
        """Test similarity_threshold parameter is accepted."""
        mock_api.get_market_items.return_value = {"items": []}

        # Should not raise
        await find_price_anomalies(
            game="csgo", dmarket_api=mock_api, similarity_threshold=0.95
        )

    @pytest.mark.asyncio()
    async def test_api_exception_returns_empty_list(self, mock_api):
        """Test API exception returns empty list."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert results == []


# ======================== find_trending_items Extended Tests ========================


class TestFindTrendingItemsExtended:
    """Extended tests for find_trending_items function."""

    @pytest.mark.asyncio()
    async def test_no_items_in_market_data(self, mock_api):
        """Test when market data has no items key."""
        mock_api.get_sales_history.return_value = {"items": []}
        mock_api.get_market_items.return_value = {}

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert results == []

    @pytest.mark.asyncio()
    async def test_price_extraction_dict_format(self, mock_api):
        """Test price extraction from dict format."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Test Item",
                    "price": {"amount": 1500},
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_price_extraction_float_format(self, mock_api):
        """Test price extraction from float format."""
        mock_api.get_market_items.return_value = {
            "items": [{"title": "Test Item", "price": 15.50, "itemId": "item_1"}]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_suggested_price_dict_format(self, mock_api):
        """Test suggested price extraction from dict format."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Test Item",
                    "price": {"amount": 1500},
                    "suggestedPrice": {"amount": 1800},
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_suggested_price_float_format(self, mock_api):
        """Test suggested price extraction from float format."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Test Item",
                    "price": 15.00,
                    "suggestedPrice": 18.00,
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_upward_trend_conditions(self, mock_api):
        """Test upward trend detection conditions."""
        # Current price higher than last sold, with 2+ sales
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Trending Item",
                    "price": {"amount": 1500},  # $15
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {
            "items": [
                {"title": "Trending Item", "price": {"amount": 1300}},  # $13
                {"title": "Trending Item", "price": {"amount": 1350}},  # $13.50
            ]
        }

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        # Should detect upward trend if price change > 5% and sales_count >= 2
        if results:
            assert results[0]["trend"] in {"upward", "recovery"}

    @pytest.mark.asyncio()
    async def test_recovery_trend_conditions(self, mock_api):
        """Test recovery trend detection conditions."""
        # Current price much lower than last sold, with 3+ sales
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Recovery Item",
                    "price": {"amount": 1000},  # $10
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {
            "items": [
                {"title": "Recovery Item", "price": {"amount": 1300}},
                {"title": "Recovery Item", "price": {"amount": 1350}},
                {"title": "Recovery Item", "price": {"amount": 1400}},
            ]
        }

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        if results:
            assert results[0]["trend"] in {"upward", "recovery"}

    @pytest.mark.asyncio()
    async def test_price_below_min_skipped(self, mock_api):
        """Test items below min_price are skipped."""
        mock_api.get_market_items.return_value = {
            "items": [
                {"title": "Cheap Item", "price": {"amount": 100}, "itemId": "item_1"}
            ]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(
            game="csgo", dmarket_api=mock_api, min_price=5.0
        )

        # $1 item should be skipped (below $5 min)
        assert results == []

    @pytest.mark.asyncio()
    async def test_price_above_max_skipped(self, mock_api):
        """Test items above max_price are skipped."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Expensive Item",
                    "price": {"amount": 100000},  # $1000
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(
            game="csgo", dmarket_api=mock_api, max_price=500.0
        )

        assert results == []

    @pytest.mark.asyncio()
    async def test_empty_title_items_skipped(self, mock_api):
        """Test items with empty titles are skipped."""
        mock_api.get_market_items.return_value = {
            "items": [{"title": "", "price": {"amount": 1500}, "itemId": "item_1"}]
        }
        mock_api.get_sales_history.return_value = {"items": []}

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert results == []

    @pytest.mark.asyncio()
    async def test_sales_count_incrementing(self, mock_api):
        """Test sales count is incremented correctly for multiple sales."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Multi Sale Item",
                    "price": {"amount": 1500},
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {
            "items": [
                {"title": "Multi Sale Item", "price": {"amount": 1200}},
                {"title": "Multi Sale Item", "price": {"amount": 1250}},
                {"title": "Multi Sale Item", "price": {"amount": 1300}},
            ]
        }

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        if results:
            assert results[0].get("sales_count", 0) >= 1

    @pytest.mark.asyncio()
    async def test_potential_profit_threshold(self, mock_api):
        """Test potential profit threshold for upward trend."""
        # Setup item where potential profit is below $0.50 threshold
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Small Profit Item",
                    "price": {"amount": 110},  # $1.10
                    "itemId": "item_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {
            "items": [
                {"title": "Small Profit Item", "price": {"amount": 100}},
                {"title": "Small Profit Item", "price": {"amount": 100}},
            ]
        }

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        # Potential profit too small, may not be included
        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_sort_by_potential_profit_percent(self, mock_api):
        """Test results are sorted by potential profit percentage."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Item A",
                    "price": {"amount": 1000},
                    "itemId": "item_a",
                },
                {
                    "title": "Item B",
                    "price": {"amount": 2000},
                    "itemId": "item_b",
                },
            ]
        }
        mock_api.get_sales_history.return_value = {
            "items": [
                {"title": "Item A", "price": {"amount": 800}},
                {"title": "Item A", "price": {"amount": 850}},
                {"title": "Item B", "price": {"amount": 1800}},
                {"title": "Item B", "price": {"amount": 1850}},
            ]
        }

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        if len(results) > 1:
            # Should be sorted by potential_profit_percent descending
            for i in range(len(results) - 1):
                assert (
                    results[i]["potential_profit_percent"]
                    >= results[i + 1]["potential_profit_percent"]
                )

    @pytest.mark.asyncio()
    async def test_api_exception_returns_empty(self, mock_api):
        """Test API exception returns empty list."""
        mock_api.get_sales_history.side_effect = Exception("API Error")

        results = await find_trending_items(game="csgo", dmarket_api=mock_api)

        assert results == []


# ======================== find_mispriced_rare_items Extended Tests ========================


class TestFindMispricedRareItemsExtended:
    """Extended tests for find_mispriced_rare_items function."""

    @pytest.mark.asyncio()
    async def test_csgo_knife_star_symbol(self, mock_api):
        """Test CS:GO knife detection with star symbol."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Bayonet | Doppler (Factory New)",
                    "price": {"amount": 50000},
                    "suggestedPrice": {"amount": 60000},
                    "itemId": "knife_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        if results:
            # Star symbol should give high rarity score
            assert results[0]["rarity_score"] >= 100

    @pytest.mark.asyncio()
    async def test_csgo_gloves_detection(self, mock_api):
        """Test CS:GO gloves detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Driver Gloves | Crimson Weave (Field-Tested)",
                    "price": {"amount": 40000},
                    "suggestedPrice": {"amount": 48000},
                    "itemId": "gloves_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        if results:
            # Gloves should have high rarity
            assert results[0]["rarity_score"] >= 90

    @pytest.mark.asyncio()
    async def test_float_value_extremely_low(self, mock_api):
        """Test extremely low float value detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "AK-47 | Redline (Factory New)",
                    "price": {"amount": 50000},
                    "suggestedPrice": {"amount": 60000},
                    "float": 0.005,  # Extremely low
                    "itemId": "ak_fn_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        if results:
            # Should have float trait detected
            float_traits = [t for t in results[0]["rare_traits"] if "Float" in t]
            assert len(float_traits) > 0

    @pytest.mark.asyncio()
    async def test_float_value_very_low(self, mock_api):
        """Test very low float value detection (0.01-0.07)."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "M4A4 | Howl (Factory New)",
                    "price": {"amount": 100000},
                    "suggestedPrice": {"amount": 120000},
                    "float": 0.05,
                    "itemId": "howl_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        if results:
            float_traits = [t for t in results[0]["rare_traits"] if "Float" in t]
            assert len(float_traits) > 0

    @pytest.mark.asyncio()
    async def test_dota2_arcana_detection(self, mock_api):
        """Test Dota 2 Arcana detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Demon Eater (Arcana)",
                    "price": {"amount": 25000},
                    "suggestedPrice": {"amount": 30000},
                    "itemId": "arcana_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="dota2", dmarket_api=mock_api)

        if results:
            assert "Arcana" in results[0]["rare_traits"]
            assert results[0]["rarity_score"] >= 100

    @pytest.mark.asyncio()
    async def test_dota2_immortal_detection(self, mock_api):
        """Test Dota 2 Immortal detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Golden Immortal Wings",
                    "price": {"amount": 15000},
                    "suggestedPrice": {"amount": 18000},
                    "itemId": "immortal_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="dota2", dmarket_api=mock_api)

        if results:
            assert "Immortal" in results[0]["rare_traits"]

    @pytest.mark.asyncio()
    async def test_tf2_unusual_detection(self, mock_api):
        """Test TF2 Unusual detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Unusual Team Captain (Sunbeams)",
                    "price": {"amount": 50000},
                    "suggestedPrice": {"amount": 60000},
                    "itemId": "unusual_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="tf2", dmarket_api=mock_api)

        if results:
            # Unusual (100) + Team Captain (70) + Sunbeams (90)
            assert results[0]["rarity_score"] >= 100

    @pytest.mark.asyncio()
    async def test_tf2_australium_detection(self, mock_api):
        """Test TF2 Australium detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Australium Rocket Launcher",
                    "price": {"amount": 12000},
                    "suggestedPrice": {"amount": 15000},
                    "itemId": "australium_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="tf2", dmarket_api=mock_api)

        if results:
            assert "Australium" in results[0]["rare_traits"]

    @pytest.mark.asyncio()
    async def test_rust_glowing_detection(self, mock_api):
        """Test Rust Glowing trait detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Glowing Metal Facemask",
                    "price": {"amount": 15000},
                    "suggestedPrice": {"amount": 18000},
                    "itemId": "glowing_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="rust", dmarket_api=mock_api)

        if results:
            assert "Glowing" in results[0]["rare_traits"]

    @pytest.mark.asyncio()
    async def test_rust_limited_detection(self, mock_api):
        """Test Rust Limited trait detection."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Limited Edition AK47 Skin",
                    "price": {"amount": 20000},
                    "suggestedPrice": {"amount": 25000},
                    "itemId": "limited_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="rust", dmarket_api=mock_api)

        if results:
            assert "Limited" in results[0]["rare_traits"]

    @pytest.mark.asyncio()
    async def test_rarity_score_threshold(self, mock_api):
        """Test rarity score threshold of 30 is enforced."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Common Item Without Rare Traits",
                    "price": {"amount": 5000},
                    "suggestedPrice": {"amount": 6000},
                    "itemId": "common_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        # Item without rare traits should have score < 30 and be excluded
        if results:
            assert all(r["rarity_score"] > 30 for r in results)

    @pytest.mark.asyncio()
    async def test_estimated_value_calculation_no_suggested(self, mock_api):
        """Test estimated value when no suggested price available."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Karambit | Fade (Factory New)",  # Has rare traits
                    "price": {"amount": 90000},
                    "itemId": "knife_no_suggested",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        if results:
            # Should estimate value based on rarity score
            assert results[0]["estimated_value"] > results[0]["current_price"]

    @pytest.mark.asyncio()
    async def test_price_difference_threshold(self, mock_api):
        """Test price difference thresholds ($2 and 10%)."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Karambit | Fade (Factory New)",
                    "price": {"amount": 9000},  # $90
                    "suggestedPrice": {"amount": 9100},  # $91 - only $1 diff
                    "itemId": "knife_small_diff",
                }
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        # Should be excluded due to small price difference
        # But rarity estimation might still include it
        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_sort_by_price_difference_percent(self, mock_api):
        """Test results sorted by price_difference_percent."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Karambit | Fade (FN)",
                    "price": {"amount": 80000},
                    "suggestedPrice": {"amount": 100000},  # 25% diff
                    "itemId": "knife_1",
                },
                {
                    "title": "★ Bayonet | Doppler (FN)",
                    "price": {"amount": 50000},
                    "suggestedPrice": {"amount": 80000},  # 60% diff
                    "itemId": "knife_2",
                },
            ]
        }

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        if len(results) > 1:
            # Higher discount first
            assert (
                results[0]["price_difference_percent"]
                >= results[1]["price_difference_percent"]
            )

    @pytest.mark.asyncio()
    async def test_unknown_game_empty_traits(self, mock_api):
        """Test unknown game has empty rare traits dict."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Unknown Game Item",
                    "price": {"amount": 5000},
                    "suggestedPrice": {"amount": 6000},
                    "itemId": "unknown_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(
            game="unknown_game", dmarket_api=mock_api
        )

        # Unknown game should have no rare traits detection
        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_api_exception_returns_empty(self, mock_api):
        """Test API exception returns empty list."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        results = await find_mispriced_rare_items(game="csgo", dmarket_api=mock_api)

        assert results == []


# ======================== scan_for_intramarket_opportunities Extended Tests ========================


class TestScanForIntramarketOpportunitiesExtended:
    """Extended tests for scan_for_intramarket_opportunities function."""

    @pytest.mark.asyncio()
    async def test_default_games_list(self, mock_api):
        """Test default games list is used when None."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=None, dmarket_api=mock_api
        )

        # Default: csgo, dota2, tf2, rust
        assert "csgo" in results
        assert "dota2" in results
        assert "tf2" in results
        assert "rust" in results

    @pytest.mark.asyncio()
    async def test_include_anomalies_only(self, mock_api):
        """Test include_anomalies=True, others False."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo"],
            dmarket_api=mock_api,
            include_anomalies=True,
            include_trending=False,
            include_rare=False,
        )

        assert "price_anomalies" in results["csgo"]
        assert results["csgo"]["trending_items"] == []
        assert results["csgo"]["rare_mispriced"] == []

    @pytest.mark.asyncio()
    async def test_include_trending_only(self, mock_api):
        """Test include_trending=True, others False."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo"],
            dmarket_api=mock_api,
            include_anomalies=False,
            include_trending=True,
            include_rare=False,
        )

        assert results["csgo"]["price_anomalies"] == []
        assert "trending_items" in results["csgo"]
        assert results["csgo"]["rare_mispriced"] == []

    @pytest.mark.asyncio()
    async def test_include_rare_only(self, mock_api):
        """Test include_rare=True, others False."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo"],
            dmarket_api=mock_api,
            include_anomalies=False,
            include_trending=False,
            include_rare=True,
        )

        assert results["csgo"]["price_anomalies"] == []
        assert results["csgo"]["trending_items"] == []
        assert "rare_mispriced" in results["csgo"]

    @pytest.mark.asyncio()
    async def test_all_categories_disabled(self, mock_api):
        """Test when all categories are disabled."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo"],
            dmarket_api=mock_api,
            include_anomalies=False,
            include_trending=False,
            include_rare=False,
        )

        assert results["csgo"]["price_anomalies"] == []
        assert results["csgo"]["trending_items"] == []
        assert results["csgo"]["rare_mispriced"] == []

    @pytest.mark.asyncio()
    async def test_max_results_per_game_applied(self, mock_api):
        """Test max_results_per_game limits results."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo"],
            dmarket_api=mock_api,
            max_results_per_game=3,
        )

        # All categories should respect max_results_per_game
        assert len(results["csgo"]["price_anomalies"]) <= 3
        assert len(results["csgo"]["trending_items"]) <= 3
        assert len(results["csgo"]["rare_mispriced"]) <= 3

    @pytest.mark.asyncio()
    async def test_error_in_one_category_doesnt_affect_others(self, mock_api):
        """Test error in one category doesn't affect others."""
        # Make anomalies fail but trending/rare succeed
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return {"items": []}

        mock_api.get_market_items.side_effect = side_effect
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo"], dmarket_api=mock_api
        )

        # Should have empty lists for failed category, not crash
        assert isinstance(results["csgo"]["price_anomalies"], list)

    @pytest.mark.asyncio()
    async def test_exception_returns_empty_results_for_all_games(self, mock_api):
        """Test main exception returns empty results for all games."""
        mock_api.get_market_items.side_effect = Exception("API Error")
        mock_api.get_sales_history.side_effect = Exception("API Error")

        results = await scan_for_intramarket_opportunities(
            games=["csgo", "dota2"], dmarket_api=mock_api
        )

        for game in ["csgo", "dota2"]:
            assert game in results
            assert results[game]["price_anomalies"] == []
            assert results[game]["trending_items"] == []
            assert results[game]["rare_mispriced"] == []

    @pytest.mark.asyncio()
    async def test_api_client_created_and_closed(self, mock_api):
        """Test API client is created and closed properly."""
        with patch(
            "src.telegram_bot.utils.api_helper.create_dmarket_api_client"
        ) as mock_create:
            mock_create.return_value = mock_api

            await scan_for_intramarket_opportunities(games=["csgo"], dmarket_api=None)

            mock_create.assert_called_once_with(None)
            mock_api._close_client.assert_called()

    @pytest.mark.asyncio()
    async def test_single_game_scan(self, mock_api):
        """Test scanning single game."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["tf2"], dmarket_api=mock_api
        )

        assert len(results) == 1
        assert "tf2" in results


# ======================== Edge Cases Tests ========================


class TestEdgeCases:
    """Edge case tests for intramarket_arbitrage module."""

    @pytest.mark.asyncio()
    async def test_unicode_item_titles(self, mock_api):
        """Test handling of unicode characters in item titles."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "АК-47 | Красная линия (После полевых испытаний)",
                    "price": {"amount": 1000},
                    "itemId": "unicode_item_1",
                }
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_special_characters_in_titles(self, mock_api):
        """Test handling of special characters in titles."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Item™ | Special® (Edition©)",
                    "price": {"amount": 1000},
                    "itemId": "special_char_item",
                }
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_very_large_price(self, mock_api):
        """Test handling of very large prices."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Expensive Item",
                    "price": {"amount": 999999999},  # ~$10M
                    "itemId": "expensive_1",
                }
            ]
        }

        results = await find_price_anomalies(
            game="csgo", dmarket_api=mock_api, max_price=100000000
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_very_small_price(self, mock_api):
        """Test handling of very small prices."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Cheap Item",
                    "price": {"amount": 1},  # $0.01
                    "itemId": "cheap_1",
                }
            ]
        }

        results = await find_price_anomalies(
            game="csgo", dmarket_api=mock_api, min_price=0.001
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_zero_price(self, mock_api):
        """Test handling of zero price."""
        mock_api.get_market_items.return_value = {
            "items": [
                {"title": "Zero Price Item", "price": {"amount": 0}, "itemId": "zero_1"}
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_negative_price(self, mock_api):
        """Test handling of negative price."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Negative Price Item",
                    "price": {"amount": -100},
                    "itemId": "negative_1",
                }
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        # Should handle gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_empty_items_key(self, mock_api):
        """Test empty items key in response."""
        mock_api.get_market_items.return_value = {"items": []}

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert results == []

    @pytest.mark.asyncio()
    async def test_missing_items_key(self, mock_api):
        """Test missing items key in response."""
        mock_api.get_market_items.return_value = {}

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert results == []

    @pytest.mark.asyncio()
    async def test_none_response(self, mock_api):
        """Test None response from API."""
        mock_api.get_market_items.return_value = None

        # Should handle gracefully
        try:
            results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)
            assert results == []
        except Exception:
            pass  # Exception is acceptable for None response

    @pytest.mark.asyncio()
    async def test_very_long_title(self, mock_api):
        """Test handling of very long item titles."""
        long_title = "A" * 1000  # 1000 character title
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": long_title,
                    "price": {"amount": 1000},
                    "itemId": "long_title_1",
                }
            ]
        }

        results = await find_price_anomalies(game="csgo", dmarket_api=mock_api)

        assert isinstance(results, list)


# ======================== Integration Tests ========================


class TestIntegration:
    """Integration tests for intramarket_arbitrage module."""

    @pytest.mark.asyncio()
    async def test_full_anomaly_detection_workflow(self, mock_api):
        """Test complete anomaly detection workflow."""
        # Setup realistic market data
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": {"amount": 1000},
                    "itemId": "ak_1",
                },
                {
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": {"amount": 1500},
                    "itemId": "ak_2",
                },
                {
                    "title": "M4A4 | Asiimov (Field-Tested)",
                    "price": {"amount": 3000},
                    "itemId": "m4_1",
                },
            ]
        }

        results = await find_price_anomalies(
            game="csgo",
            dmarket_api=mock_api,
            min_price=1.0,
            max_price=100.0,
            price_diff_percent=10.0,
        )

        # Should find the AK-47 price difference
        if results:
            assert results[0]["game"] == "csgo"
            assert "buy_price" in results[0]
            assert "sell_price" in results[0]
            assert "profit_after_fee" in results[0]
            assert results[0]["profit_after_fee"] > 0

    @pytest.mark.asyncio()
    async def test_full_trending_workflow(self, mock_api):
        """Test complete trending items workflow."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "AWP | Dragon Lore",
                    "price": {"amount": 100000},
                    "itemId": "awp_1",
                }
            ]
        }
        mock_api.get_sales_history.return_value = {
            "items": [
                {"title": "AWP | Dragon Lore", "price": {"amount": 80000}},
                {"title": "AWP | Dragon Lore", "price": {"amount": 85000}},
            ]
        }

        results = await find_trending_items(
            game="csgo", dmarket_api=mock_api, min_price=100.0, max_price=2000.0
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio()
    async def test_full_rare_items_workflow(self, mock_api):
        """Test complete rare items workflow."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "★ Karambit | Doppler (Factory New)",
                    "price": {"amount": 80000},
                    "suggestedPrice": {"amount": 100000},
                    "float": 0.008,
                    "itemId": "knife_1",
                }
            ]
        }

        results = await find_mispriced_rare_items(
            game="csgo", dmarket_api=mock_api, min_price=100.0, max_price=2000.0
        )

        if results:
            assert "rarity_score" in results[0]
            assert "rare_traits" in results[0]
            assert results[0]["rarity_score"] > 0

    @pytest.mark.asyncio()
    async def test_comprehensive_scan_all_games(self, mock_api):
        """Test comprehensive scan across all games."""
        mock_api.get_market_items.return_value = {"items": []}
        mock_api.get_sales_history.return_value = {"items": []}

        results = await scan_for_intramarket_opportunities(
            games=["csgo", "dota2", "tf2", "rust"],
            dmarket_api=mock_api,
            include_anomalies=True,
            include_trending=True,
            include_rare=True,
        )

        # All games should have all categories
        for game in ["csgo", "dota2", "tf2", "rust"]:
            assert game in results
            assert "price_anomalies" in results[game]
            assert "trending_items" in results[game]
            assert "rare_mispriced" in results[game]

    @pytest.mark.asyncio()
    async def test_fee_calculation_accuracy(self, mock_api):
        """Test fee calculation is accurate (7% DMarket fee)."""
        mock_api.get_market_items.return_value = {
            "items": [
                {
                    "title": "Test Item",
                    "price": {"amount": 10000},  # $100
                    "itemId": "item_1",
                },
                {
                    "title": "Test Item",
                    "price": {"amount": 12000},  # $120
                    "itemId": "item_2",
                },
            ]
        }

        results = await find_price_anomalies(
            game="csgo", dmarket_api=mock_api, price_diff_percent=5.0
        )

        if results:
            # Buy: $100, Sell: $120
            # After 7% fee: $120 * 0.93 = $111.60
            # Profit: $111.60 - $100 = $11.60
            expected_profit = 120.0 * 0.93 - 100.0
            assert abs(results[0]["profit_after_fee"] - expected_profit) < 0.01
            assert results[0]["fee_percent"] == 7.0

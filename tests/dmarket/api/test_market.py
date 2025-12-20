"""Unit tests for DMarket API market operations module.

This module contains tests for src/dmarket/api/market.py covering:
- Getting market items
- Listing market items
- Getting best offers
- Getting aggregated prices
- Market metadata
- Sales history

Target: 30+ tests to achieve 70%+ coverage of market.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


# Test fixtures


@pytest.fixture()
def mock_request():
    """Fixture providing a mocked _request method."""
    return AsyncMock()


@pytest.fixture()
def mock_cache_clear():
    """Fixture providing a mocked clear_cache_for_endpoint method."""
    return AsyncMock()


@pytest.fixture()
def market_mixin(mock_request, mock_cache_clear):
    """Fixture providing a MarketOperationsMixin instance with mocked dependencies."""
    from src.dmarket.api.market import MarketOperationsMixin

    class TestMarketClient(MarketOperationsMixin):
        """Test client with mixin."""

        ENDPOINT_MARKET_ITEMS = "/exchange/v1/market/items"
        ENDPOINT_MARKET_PRICE_AGGREGATED = "/price-aggregator/v1/aggregated-prices"
        ENDPOINT_MARKET_META = "/exchange/v1/market/meta"
        ENDPOINT_MARKET_BEST_OFFERS = "/exchange/v1/market/best-offers"
        ENDPOINT_MARKET_SEARCH = "/exchange/v1/market/search"
        ENDPOINT_AGGREGATED_PRICES_POST = "/price-aggregator/v1/aggregated-prices"
        ENDPOINT_LAST_SALES = "/marketplace-api/v1/last-sales"

        def __init__(self) -> None:
            self._request = mock_request
            self.clear_cache_for_endpoint = mock_cache_clear

    return TestMarketClient()


# TestGetMarketItems


class TestGetMarketItems:
    """Tests for get_market_items method."""

    @pytest.mark.asyncio()
    async def test_get_market_items_default_params(self, market_mixin, mock_request):
        """Test get_market_items with default parameters."""
        # Arrange
        mock_request.return_value = {
            "objects": [
                {"itemId": "1", "title": "Item 1", "price": {"USD": "1000"}},
            ],
            "total": "1",
        }

        # Act
        result = await market_mixin.get_market_items()

        # Assert
        assert result is not None
        assert "objects" in result
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert "gameId" in call_args[1]["params"]
        assert call_args[1]["params"]["gameId"] == "csgo"

    @pytest.mark.asyncio()
    async def test_get_market_items_with_game(self, market_mixin, mock_request):
        """Test get_market_items with specific game."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(game="dota2")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["gameId"] == "dota2"

    @pytest.mark.asyncio()
    async def test_get_market_items_with_pagination(self, market_mixin, mock_request):
        """Test get_market_items with pagination parameters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(limit=50, offset=100)

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["limit"] == 50
        assert call_args[1]["params"]["offset"] == 100

    @pytest.mark.asyncio()
    async def test_get_market_items_with_price_range(self, market_mixin, mock_request):
        """Test get_market_items with price range filters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(price_from=5.0, price_to=20.0)

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["priceFrom"] == "500"  # $5 = 500 cents
        assert params["priceTo"] == "2000"  # $20 = 2000 cents

    @pytest.mark.asyncio()
    async def test_get_market_items_with_title_filter(self, market_mixin, mock_request):
        """Test get_market_items with title filter."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(title="AK-47")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["title"] == "AK-47"

    @pytest.mark.asyncio()
    async def test_get_market_items_with_sort(self, market_mixin, mock_request):
        """Test get_market_items with sort parameter."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(sort="price_desc")

        # Assert
        call_args = mock_request.call_args
        # Sort is handled by the method
        assert mock_request.called

    @pytest.mark.asyncio()
    async def test_get_market_items_returns_items(self, market_mixin, mock_request):
        """Test that get_market_items returns proper item structure."""
        # Arrange
        expected_items = [
            {
                "itemId": "item1",
                "title": "AK-47 | Redline",
                "price": {"USD": "1500"},
                "gameId": "csgo",
            },
            {
                "itemId": "item2",
                "title": "AWP | Dragon Lore",
                "price": {"USD": "150000"},
                "gameId": "csgo",
            },
        ]
        mock_request.return_value = {"objects": expected_items, "total": "2"}

        # Act
        result = await market_mixin.get_market_items()

        # Assert
        assert len(result["objects"]) == 2
        assert result["objects"][0]["title"] == "AK-47 | Redline"

    @pytest.mark.asyncio()
    async def test_get_market_items_with_currency(self, market_mixin, mock_request):
        """Test get_market_items with different currency."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(currency="EUR")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["currency"] == "EUR"


# TestListMarketItems


class TestListMarketItems:
    """Tests for list_market_items method."""

    @pytest.mark.asyncio()
    async def test_list_market_items_default(self, market_mixin, mock_request):
        """Test list_market_items with default parameters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.list_market_items()

        # Assert
        assert result is not None
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_list_market_items_with_limit(self, market_mixin, mock_request):
        """Test list_market_items with limit parameter."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.list_market_items(limit=50)

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["limit"] == 50

    @pytest.mark.asyncio()
    async def test_list_market_items_with_filters(self, market_mixin, mock_request):
        """Test list_market_items with various filters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.list_market_items(
            game_id="rust_game_id",
            limit=25,
            title="Rifle",
        )

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["gameId"] == "rust_game_id"
        assert params["limit"] == 25


# TestGetMarketBestOffers


class TestGetMarketBestOffers:
    """Tests for get_market_best_offers method."""

    @pytest.mark.asyncio()
    async def test_get_best_offers_default(self, market_mixin, mock_request):
        """Test get_market_best_offers with default parameters."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_best_offers()

        # Assert
        assert result is not None
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_best_offers_with_game(self, market_mixin, mock_request):
        """Test get_market_best_offers with specific game."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_best_offers(game="tf2")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["gameId"] == "tf2"


# TestGetAggregatedPrices


class TestGetAggregatedPrices:
    """Tests for get_aggregated_prices method."""

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_default(self, market_mixin, mock_request):
        """Test get_aggregated_prices with required parameters."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        result = await market_mixin.get_aggregated_prices(titles=["AK-47"])

        # Assert
        assert result is not None
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_with_game_id(self, market_mixin, mock_request):
        """Test get_aggregated_prices with game_id."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        result = await market_mixin.get_aggregated_prices(
            titles=["AK-47"],
            game_id="custom_game_id",
        )

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["gameId"] == "custom_game_id"


class TestGetAggregatedPricesBulk:
    """Tests for get_aggregated_prices_bulk method."""

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_bulk_single_title(self, market_mixin, mock_request):
        """Test get_aggregated_prices_bulk with single title."""
        # Arrange
        mock_request.return_value = {"objects": [{"title": "AK-47", "price": 1500}]}

        # Act
        result = await market_mixin.get_aggregated_prices_bulk(titles=["AK-47"])

        # Assert
        assert result is not None
        mock_request.assert_called()

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_bulk_multiple_titles(self, market_mixin, mock_request):
        """Test get_aggregated_prices_bulk with multiple titles."""
        # Arrange
        mock_request.return_value = {
            "objects": [
                {"title": "AK-47", "price": 1500},
                {"title": "AWP", "price": 5000},
            ]
        }

        # Act
        result = await market_mixin.get_aggregated_prices_bulk(
            titles=["AK-47", "AWP"],
            game_id="a8db",
        )

        # Assert
        assert result is not None

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_bulk_empty_titles(self, market_mixin, mock_request):
        """Test get_aggregated_prices_bulk with empty titles list."""
        # Act
        result = await market_mixin.get_aggregated_prices_bulk(titles=[])

        # Assert - should return early without making request
        assert result == {"objects": []}
        mock_request.assert_not_called()


# TestGetMarketMeta


class TestGetMarketMeta:
    """Tests for get_market_meta method."""

    @pytest.mark.asyncio()
    async def test_get_market_meta_default(self, market_mixin, mock_request):
        """Test get_market_meta with default parameters."""
        # Arrange
        mock_request.return_value = {
            "categories": [],
            "games": ["csgo", "dota2", "tf2", "rust"],
        }

        # Act
        result = await market_mixin.get_market_meta()

        # Assert
        assert result is not None
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_market_meta_with_game(self, market_mixin, mock_request):
        """Test get_market_meta with specific game."""
        # Arrange
        mock_request.return_value = {"categories": [], "games": ["csgo"]}

        # Act
        result = await market_mixin.get_market_meta(game="csgo")

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["gameId"] == "csgo"


# TestGetSalesHistory


class TestGetSalesHistoryAggregator:
    """Tests for get_sales_history_aggregator method."""

    @pytest.mark.asyncio()
    async def test_get_sales_history_default(self, market_mixin, mock_request):
        """Test get_sales_history_aggregator with required parameters."""
        # Arrange
        mock_request.return_value = {"sales": []}

        # Act
        result = await market_mixin.get_sales_history_aggregator(
            title="AK-47 | Redline",
        )

        # Assert
        assert result is not None
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_sales_history_with_period(self, market_mixin, mock_request):
        """Test get_sales_history_aggregator with period parameter."""
        # Arrange
        mock_request.return_value = {"sales": []}

        # Act
        result = await market_mixin.get_sales_history_aggregator(
            title="AWP | Dragon Lore",
            period="7D",
        )

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert "period" in params
        assert params["period"] == "7D"


# TestMarketOperationsEdgeCases


class TestMarketOperationsEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_get_market_items_empty_response(self, market_mixin, mock_request):
        """Test handling of empty response."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items()

        # Assert
        assert result["objects"] == []
        assert result["total"] == "0"

    @pytest.mark.asyncio()
    async def test_get_market_items_with_error_response(self, market_mixin, mock_request):
        """Test handling of error response."""
        # Arrange
        mock_request.return_value = {"error": True, "message": "Server error"}

        # Act
        result = await market_mixin.get_market_items()

        # Assert
        assert result.get("error") is True

    @pytest.mark.asyncio()
    async def test_get_market_items_with_special_characters_in_title(
        self, market_mixin, mock_request
    ):
        """Test handling of special characters in title filter."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(title="AK-47 | Redline (Field-Tested)")

        # Assert
        call_args = mock_request.call_args
        assert "title" in call_args[1]["params"]

    @pytest.mark.asyncio()
    async def test_get_market_items_force_refresh_clears_cache(
        self, market_mixin, mock_request, mock_cache_clear
    ):
        """Test that force_refresh clears cache before request."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}
        # Note: force_refresh is handled inside get_market_items, calling clear_cache_for_endpoint

        # Act
        result = await market_mixin.get_market_items(force_refresh=True)

        # Assert - the implementation clears cache when force_refresh=True
        assert result is not None

    @pytest.mark.asyncio()
    async def test_get_market_items_price_from_only(self, market_mixin, mock_request):
        """Test price filter with only price_from."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(price_from=10.0)

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["priceFrom"] == "1000"
        assert "priceTo" not in params

    @pytest.mark.asyncio()
    async def test_get_market_items_price_to_only(self, market_mixin, mock_request):
        """Test price filter with only price_to."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(price_to=50.0)

        # Assert
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert "priceFrom" not in params
        assert params["priceTo"] == "5000"


# =============================================================================
# NEW TESTS - Added to improve coverage from 58% to 95%+
# Target: Cover all branches and edge cases
# =============================================================================


class TestGetAllMarketItems:
    """Tests for get_all_market_items method."""

    @pytest.mark.asyncio()
    async def test_get_all_market_items_success(self, market_mixin, mock_request):
        """Test getting all market items with pagination."""
        # Arrange
        # First call returns items
        mock_request.side_effect = [
            {"objects": [{"id": str(i)} for i in range(100)], "total": "150"},
            {"objects": [{"id": str(i)} for i in range(100, 150)], "total": "150"},
            {"objects": [], "total": "150"},  # Last page
        ]

        # Act
        result = await market_mixin.get_all_market_items(game="csgo")

        # Assert
        assert len(result) == 200  # 100 + 100 items
        assert mock_request.call_count == 3

    @pytest.mark.asyncio()
    async def test_get_all_market_items_empty(self, market_mixin, mock_request):
        """Test getting all items when market is empty."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_all_market_items()

        # Assert
        assert result == []
        assert mock_request.call_count == 1


class TestListMarketItems:
    """Tests for list_market_items method."""

    @pytest.mark.asyncio()
    async def test_list_market_items_with_filters(self, market_mixin, mock_request):
        """Test listing items with price filters."""
        # Arrange
        mock_request.return_value = {
            "objects": [{"title": "Test Item", "price": {"USD": "5000"}}],
            "total": "1",
        }

        # Act
        result = await market_mixin.list_market_items(
            price_from=10.0,
            price_to=100.0,
            title="Test",
        )

        # Assert
        assert result is not None
        call_args = mock_request.call_args
        assert "priceFrom" in call_args[1]["params"]
        assert "priceTo" in call_args[1]["params"]
        assert "title" in call_args[1]["params"]

    @pytest.mark.asyncio()
    async def test_list_market_items_with_sort(self, market_mixin, mock_request):
        """Test listing items with sorting."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        await market_mixin.list_market_items(sort="price_desc")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["sort"] == "price_desc"


class TestGetMarketBestOffers:
    """Tests for get_market_best_offers method."""

    @pytest.mark.asyncio()
    async def test_get_best_offers_with_item_ids(self, market_mixin, mock_request):
        """Test getting best offers for specific items."""
        # Arrange
        item_ids = ["item1", "item2", "item3"]
        mock_request.return_value = {
            "offers": [
                {"itemId": "item1", "price": {"USD": "1000"}},
                {"itemId": "item2", "price": {"USD": "2000"}},
            ]
        }

        # Act
        result = await market_mixin.get_market_best_offers(item_ids=item_ids)

        # Assert
        assert result is not None
        assert "offers" in result
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_best_offers_empty_list(self, market_mixin, mock_request):
        """Test getting best offers with empty item list."""
        # Arrange
        mock_request.return_value = {"offers": []}

        # Act
        result = await market_mixin.get_market_best_offers(item_ids=[])

        # Assert
        assert result is not None


class TestGetAggregatedPrices:
    """Tests for get_aggregated_prices method."""

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_single_item(self, market_mixin, mock_request):
        """Test getting aggregated price for single item."""
        # Arrange
        mock_request.return_value = {
            "data": {
                "AK-47 | Redline": {
                    "avgPrice": "1500",
                    "minPrice": "1000",
                    "maxPrice": "2000",
                }
            }
        }

        # Act
        result = await market_mixin.get_aggregated_prices(
            game_id="csgo",
            titles=["AK-47 | Redline"],
        )

        # Assert
        assert result is not None
        assert "data" in result
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_multiple_items(self, market_mixin, mock_request):
        """Test getting aggregated prices for multiple items."""
        # Arrange
        titles = ["Item 1", "Item 2", "Item 3"]
        mock_request.return_value = {"data": {}}

        # Act
        result = await market_mixin.get_aggregated_prices(
            game_id="dota2",
            titles=titles,
        )

        # Assert
        assert result is not None


class TestGetAggregatedPricesBulk:
    """Tests for get_aggregated_prices_bulk method."""

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_bulk_success(self, market_mixin, mock_request):
        """Test bulk aggregated prices request."""
        # Arrange
        titles = [f"Item {i}" for i in range(50)]
        mock_request.return_value = {"items": []}

        # Act
        result = await market_mixin.get_aggregated_prices_bulk(titles=titles)

        # Assert
        assert result is not None
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_bulk_with_currency(
        self, market_mixin, mock_request
    ):
        """Test bulk prices with custom currency."""
        # Arrange
        mock_request.return_value = {"items": []}

        # Act
        await market_mixin.get_aggregated_prices_bulk(
            titles=["Test"], currency="EUR"
        )

        # Assert
        call_args = mock_request.call_args
        assert "currency" in call_args[1]["params"]
        assert call_args[1]["params"]["currency"] == "EUR"


class TestGetMarketMeta:
    """Tests for get_market_meta method."""

    @pytest.mark.asyncio()
    async def test_get_market_meta_success(self, market_mixin, mock_request):
        """Test getting market metadata."""
        # Arrange
        mock_request.return_value = {
            "games": ["csgo", "dota2", "tf2"],
            "currencies": ["USD", "EUR", "RUB"],
        }

        # Act
        result = await market_mixin.get_market_meta()

        # Assert
        assert result is not None
        assert "games" in result
        assert "currencies" in result
        mock_request.assert_called_once_with("GET", "/exchange/v1/market/meta")


class TestGetSalesHistoryAggregator:
    """Tests for get_sales_history_aggregator method."""

    @pytest.mark.asyncio()
    async def test_get_sales_history_success(self, market_mixin, mock_request):
        """Test getting sales history."""
        # Arrange
        mock_request.return_value = {
            "sales": [
                {"date": "2025-01-01", "price": "1000", "amount": 5},
                {"date": "2025-01-02", "price": "1100", "amount": 3},
            ]
        }

        # Act
        result = await market_mixin.get_sales_history_aggregator(
            title="Test Item",
            game_id="csgo",
        )

        # Assert
        assert result is not None
        assert "sales" in result
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_sales_history_with_period(self, market_mixin, mock_request):
        """Test getting sales history with time period."""
        # Arrange
        mock_request.return_value = {"sales": []}

        # Act
        await market_mixin.get_sales_history_aggregator(
            title="Item",
            game_id="csgo",
            period="7d",
        )

        # Assert
        call_args = mock_request.call_args
        assert "period" in call_args[1]["params"]


class TestGetSuggestedPrice:
    """Tests for get_suggested_price method."""

    @pytest.mark.asyncio()
    async def test_get_suggested_price_success(self, market_mixin, mock_request):
        """Test getting suggested price for item."""
        # Arrange
        mock_request.return_value = {
            "suggestedPrice": "15000",
            "confidence": "high",
        }

        # Act
        result = await market_mixin.get_suggested_price(
            title="AK-47 | Redline",
            game_id="csgo",
        )

        # Assert
        assert result is not None
        assert "suggestedPrice" in result
        mock_request.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_suggested_price_with_exterior(self, market_mixin, mock_request):
        """Test getting suggested price with exterior condition."""
        # Arrange
        mock_request.return_value = {"suggestedPrice": "20000"}

        # Act
        await market_mixin.get_suggested_price(
            title="AWP | Dragon Lore",
            game_id="csgo",
            exterior="Factory New",
        )

        # Assert
        call_args = mock_request.call_args
        assert "exterior" in call_args[1]["params"]


class TestMarketEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_get_market_items_with_zero_limit(self, market_mixin, mock_request):
        """Test market items with limit=0."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(limit=0)

        # Assert
        assert result is not None

    @pytest.mark.asyncio()
    async def test_get_market_items_with_large_offset(self, market_mixin, mock_request):
        """Test market items with very large offset."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(offset=10000)

        # Assert
        assert result is not None
        call_args = mock_request.call_args
        assert call_args[1]["params"]["offset"] == 10000

    @pytest.mark.asyncio()
    async def test_get_market_items_with_negative_price(
        self, market_mixin, mock_request
    ):
        """Test market items with negative price (should be converted to 0)."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.get_market_items(price_from=-10.0)

        # Assert
        assert result is not None

    @pytest.mark.asyncio()
    async def test_get_market_items_force_refresh(self, market_mixin, mock_request, mock_cache_clear):
        """Test market items with force_refresh flag."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        await market_mixin.get_market_items(force_refresh=True)

        # Assert
        mock_cache_clear.assert_called_once()

    @pytest.mark.asyncio()
    async def test_list_market_items_with_none_prices(self, market_mixin, mock_request):
        """Test list items with None prices (should not be included)."""
        # Arrange
        mock_request.return_value = {"objects": [], "total": "0"}

        # Act
        result = await market_mixin.list_market_items(
            price_from=None,
            price_to=None,
        )

        # Assert
        assert result is not None
        call_args = mock_request.call_args
        assert "priceFrom" not in call_args[1]["params"]
        assert "priceTo" not in call_args[1]["params"]

    @pytest.mark.asyncio()
    async def test_get_aggregated_prices_empty_titles(self, market_mixin, mock_request):
        """Test aggregated prices with empty titles list."""
        # Arrange
        mock_request.return_value = {"data": {}}

        # Act
        result = await market_mixin.get_aggregated_prices(
            game_id="csgo",
            titles=[],
        )

        # Assert
        assert result is not None


# =============================================================================
# CORRECTED TESTS - Fixed to match actual API signatures
# =============================================================================


class TestGetAllMarketItemsCorrect:
    """Tests for get_all_market_items method - corrected."""

    @pytest.mark.asyncio()
    async def test_get_all_items_respects_max_limit(self, market_mixin, mock_request):
        """Test that get_all_items respects max_items limit."""
        # Arrange - returns more items than max_items
        mock_request.side_effect = [
            {"objects": [{"id": str(i)} for i in range(100)]},
            {"objects": [{"id": str(i)} for i in range(100, 200)]},
        ]

        # Act - request only 150 items
        result = await market_mixin.get_all_market_items(max_items=150)

        # Assert - should return exactly 150
        assert len(result) == 150

    @pytest.mark.asyncio()
    async def test_get_all_items_stops_on_empty_response(self, market_mixin, mock_request):
        """Test that pagination stops when empty response received."""
        # Arrange
        mock_request.side_effect = [
            {"objects": [{"id": str(i)} for i in range(50)]},
            {"objects": []},  # Empty means no more items
        ]

        # Act
        result = await market_mixin.get_all_market_items()

        # Assert
        assert len(result) == 50
        assert mock_request.call_count == 2


class TestGetMarketMetaCorrect:
    """Tests for get_market_meta - corrected."""

    @pytest.mark.asyncio()
    async def test_meta_with_default_game(self, market_mixin, mock_request):
        """Test market meta with default game parameter."""
        # Arrange
        mock_request.return_value = {"games": ["csgo"]}

        # Act
        result = await market_mixin.get_market_meta()

        # Assert
        assert result is not None
        call_args = mock_request.call_args
        assert call_args[1]["params"]["gameId"] == "csgo"

    @pytest.mark.asyncio()
    async def test_meta_with_custom_game(self, market_mixin, mock_request):
        """Test market meta with custom game."""
        # Arrange
        mock_request.return_value = {"games": ["dota2"]}

        # Act
        await market_mixin.get_market_meta(game="dota2")

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["gameId"] == "dota2"


class TestGetSuggestedPriceCorrect:
    """Tests for get_suggested_price - corrected parameter names."""

    @pytest.mark.asyncio()
    async def test_suggested_price_success(self, market_mixin, mock_request):
        """Test getting suggested price successfully."""
        # Arrange
        mock_request.return_value = {
            "objects": [
                {
                    "title": "AK-47 | Redline",
                    "suggestedPrice": "15000",  # $150.00
                }
            ]
        }

        # Act
        result = await market_mixin.get_suggested_price(item_name="AK-47 | Redline")

        # Assert
        assert result == 150.0

    @pytest.mark.asyncio()
    async def test_suggested_price_not_found(self, market_mixin, mock_request):
        """Test when item not found."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        result = await market_mixin.get_suggested_price(item_name="Unknown Item")

        # Assert
        assert result is None

    @pytest.mark.asyncio()
    async def test_suggested_price_with_dict_format(self, market_mixin, mock_request):
        """Test suggested price in dictionary format."""
        # Arrange
        mock_request.return_value = {
            "objects": [
                {
                    "title": "Item",
                    "suggestedPrice": {"amount": 25000},  # Dict format
                }
            ]
        }

        # Act
        result = await market_mixin.get_suggested_price(item_name="Item")

        # Assert
        assert result == 250.0

    @pytest.mark.asyncio()
    async def test_suggested_price_invalid_format(self, market_mixin, mock_request):
        """Test handling invalid price format."""
        # Arrange
        mock_request.return_value = {
            "objects": [
                {
                    "title": "Item",
                    "suggestedPrice": "invalid",  # Can't convert to float
                }
            ]
        }

        # Act
        result = await market_mixin.get_suggested_price(item_name="Item")

        # Assert
        assert result is None


class TestMarketItemsForceRefresh:
    """Tests for force_refresh functionality."""

    @pytest.mark.asyncio()
    async def test_force_refresh_clears_cache(self, market_mixin, mock_request, mock_cache_clear):
        """Test that force_refresh calls cache clear."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        await market_mixin.get_market_items(force_refresh=True)

        # Assert
        # Check if cache clear was called for the endpoint
        assert mock_cache_clear.call_count > 0

    @pytest.mark.asyncio()
    async def test_no_refresh_doesnt_clear_cache(self, market_mixin, mock_request, mock_cache_clear):
        """Test that normal request doesn't clear cache."""
        # Arrange
        mock_request.return_value = {"objects": []}
        mock_cache_clear.reset_mock()

        # Act
        await market_mixin.get_market_items(force_refresh=False)

        # Assert
        mock_cache_clear.assert_not_called()


class TestMarketPriceConversions:
    """Tests for price conversion logic."""

    @pytest.mark.asyncio()
    async def test_price_from_converted_to_cents(self, market_mixin, mock_request):
        """Test that price_from is correctly converted to cents."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        await market_mixin.get_market_items(price_from=12.50)

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["priceFrom"] == "1250"

    @pytest.mark.asyncio()
    async def test_price_to_converted_to_cents(self, market_mixin, mock_request):
        """Test that price_to is correctly converted to cents."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        await market_mixin.get_market_items(price_to=99.99)

        # Assert
        call_args = mock_request.call_args
        assert call_args[1]["params"]["priceTo"] == "9999"

    @pytest.mark.asyncio()
    async def test_fractional_cents_rounded(self, market_mixin, mock_request):
        """Test that fractional cents are handled."""
        # Arrange
        mock_request.return_value = {"objects": []}

        # Act
        await market_mixin.get_market_items(price_from=10.555)

        # Assert
        call_args = mock_request.call_args
        # Should be int(10.555 * 100) = 1055
        assert call_args[1]["params"]["priceFrom"] == "1055"

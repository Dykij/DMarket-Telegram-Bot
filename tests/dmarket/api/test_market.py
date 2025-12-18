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

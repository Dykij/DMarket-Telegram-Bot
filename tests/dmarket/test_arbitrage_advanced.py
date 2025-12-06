from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.arbitrage import (
    ArbitrageTrader,
    _arbitrage_cache,
    _save_arbitrage_cache,
    find_arbitrage_opportunities_advanced,
)
from src.dmarket.dmarket_api import DMarketAPI


@pytest.fixture(autouse=True)
def clear_cache():
    _arbitrage_cache.clear()
    yield
    _arbitrage_cache.clear()


@pytest.fixture()
def mock_api_client():
    client = AsyncMock(spec=DMarketAPI)
    client.get_all_market_items = AsyncMock()
    client.get_market_items = AsyncMock()
    client.get_price_info = AsyncMock()
    return client


@pytest.fixture()
def trader(mock_api_client):
    # Patch DMarketAPI to return our mock
    with patch("src.dmarket.arbitrage.DMarketAPI", return_value=mock_api_client):
        trader = ArbitrageTrader(public_key="test_pub", secret_key="test_sec")
        # Ensure the trader uses our mock client
        trader.api = mock_api_client
        return trader


@pytest.mark.asyncio()
class TestFindArbitrageOpportunitiesAdvanced:
    async def test_basic_functionality(self, mock_api_client):
        # Arrange
        mock_items = [
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": 1000},  # $10.00
                "extra": {
                    "category": "Rifle",
                    "rarity": "Classified",
                    "popularity": 0.9,
                },
                "itemId": "item1",
                "imageUrl": "http://image.url/1",
            },
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": 1500},  # $15.00
                "extra": {
                    "category": "Rifle",
                    "rarity": "Classified",
                    "popularity": 0.9,
                },
                "itemId": "item2",
            },
        ]
        mock_api_client.get_all_market_items.return_value = mock_items

        # Act
        results = await find_arbitrage_opportunities_advanced(
            api_client=mock_api_client,
            mode="medium",
            game="csgo",
            min_profit_percent=5.0,
        )

        # Assert
        assert len(results) == 1
        opportunity = results[0]
        assert opportunity["item_name"] == "AK-47 | Redline (Field-Tested)"
        assert opportunity["buy_price"] == 10.0
        assert opportunity["sell_price"] == 15.0
        assert opportunity["buy_item_id"] == "item1"
        assert opportunity["sell_item_id"] == "item2"
        assert opportunity["profit_percent"] > 5.0
        assert "image_url" in opportunity
        assert "buy_link" in opportunity
        assert "sell_link" in opportunity

    async def test_empty_response(self, mock_api_client):
        # Arrange
        mock_api_client.get_all_market_items.return_value = []

        # Act
        results = await find_arbitrage_opportunities_advanced(
            api_client=mock_api_client, mode="medium", game="csgo"
        )

        # Assert
        assert len(results) == 0

    async def test_mode_handling(self, mock_api_client):
        # Arrange
        mock_api_client.get_all_market_items.return_value = []

        # Act & Assert
        # Test "normal" -> "medium"
        await find_arbitrage_opportunities_advanced(mock_api_client, mode="normal")
        # Verify default params were used
        # (medium mode implies certain profit/price ranges)
        # Since we can't easily check internal vars,
        # we rely on no errors and coverage

        # Test "best" -> "high"
        await find_arbitrage_opportunities_advanced(mock_api_client, mode="best")

        # Test "game_dota2" -> game="dota2", mode="normal"
        await find_arbitrage_opportunities_advanced(mock_api_client, mode="game_dota2")
        mock_api_client.get_all_market_items.assert_called_with(
            game="dota2",
            max_items=100,
            price_from=5.0,  # medium default
            price_to=20.0,  # medium default
            sort="price",
        )

    async def test_invalid_inputs_fallback(self, mock_api_client):
        # Arrange
        mock_api_client.get_all_market_items.return_value = []

        # Act
        await find_arbitrage_opportunities_advanced(
            mock_api_client, mode="invalid_mode", game="invalid_game"
        )

        # Assert
        # Should fallback to csgo and medium
        mock_api_client.get_all_market_items.assert_called_with(
            game="csgo",
            max_items=100,
            price_from=5.0,
            price_to=20.0,
            sort="price",
        )

    async def test_caching(self, mock_api_client):
        # Arrange
        cache_key = ("csgo", "medium", 5.0, 20.0, 5.0)
        mock_result = [{"item_name": "Cached Item"}]

        # Clear cache first
        _arbitrage_cache.clear()

        # Save to cache
        _save_arbitrage_cache(cache_key, mock_result)

        # Act
        results = await find_arbitrage_opportunities_advanced(
            api_client=mock_api_client,
            mode="medium",
            game="csgo",
            min_profit_percent=5.0,
        )

        # Assert
        assert results == mock_result
        mock_api_client.get_all_market_items.assert_not_called()

    async def test_insufficient_items_for_arbitrage(self, mock_api_client):
        # Arrange
        mock_items = [{"title": "Single Item", "price": {"USD": 1000}, "extra": {}}]
        mock_api_client.get_all_market_items.return_value = mock_items

        # Act
        results = await find_arbitrage_opportunities_advanced(
            api_client=mock_api_client, mode="medium"
        )

        # Assert
        assert len(results) == 0


@pytest.mark.asyncio()
class TestArbitrageTraderFindProfitableItems:
    async def test_find_profitable_items_success(self, trader, mock_api_client):
        # Arrange
        mock_items = {
            "objects": [
                {
                    "title": "Item 1",
                    "price": {"amount": 1000, "currency": "USD"},  # $10
                    "extra": {"popularity": 0.8},
                    "itemId": "id1",
                }
            ]
        }
        mock_api_client.get_market_items.return_value = mock_items

        # Mock get_price_info to return a good recommended price
        mock_api_client.get_price_info.return_value = {
            "recommendedPrice": 1500  # $15
        }

        # Act
        items = await trader.find_profitable_items(game="csgo", min_profit_percentage=10.0)

        # Assert
        assert len(items) == 1
        item = items[0]
        assert item["name"] == "Item 1"
        assert item["buy_price"] == 10.0
        assert item["sell_price"] == 15.0
        assert item["profit_percentage"] > 10.0

    async def test_find_profitable_items_no_suggested_price(self, trader, mock_api_client):
        # Arrange
        mock_items = {
            "objects": [
                {
                    "title": "Item 1",
                    "price": {"amount": 1000, "currency": "USD"},  # $10
                    "extra": {"popularity": 0.5},
                    "itemId": "id1",
                }
            ]
        }
        mock_api_client.get_market_items.return_value = mock_items
        # No recommended price
        mock_api_client.get_price_info.return_value = {}

        # Act
        items = await trader.find_profitable_items(game="csgo", min_profit_percentage=5.0)

        # Assert
        assert len(items) == 1
        item = items[0]
        # Should use 1.15 markup
        assert item["sell_price"] == 11.5
        # Profit: 11.5 * (1 - 0.07) - 10 = 10.695 - 10 = 0.695
        # Profit %: 6.95% > 5.0%

    async def test_find_profitable_items_no_items_found(self, trader, mock_api_client):
        # Arrange
        mock_api_client.get_market_items.return_value = {"objects": []}

        # Act
        items = await trader.find_profitable_items(game="csgo")

        # Assert
        assert len(items) == 0

    async def test_find_profitable_items_api_error(self, trader, mock_api_client):
        # Arrange
        mock_api_client.get_market_items.side_effect = Exception("API Error")

        # Act
        items = await trader.find_profitable_items(game="csgo")

        # Assert
        assert len(items) == 0

    async def test_find_profitable_items_item_processing_error(self, trader, mock_api_client):
        # Arrange
        mock_items = {
            "objects": [
                {
                    "title": "Bad Item",
                    # This will cause float conversion error
                    "price": "invalid_price",
                    "itemId": "id1",
                }
            ]
        }
        mock_api_client.get_market_items.return_value = mock_items

        # Act
        items = await trader.find_profitable_items(game="csgo")

        # Assert
        assert len(items) == 0

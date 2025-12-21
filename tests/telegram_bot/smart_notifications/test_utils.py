"""Tests for smart_notifications/utils.py module.

Covers:
- get_market_data_for_items function
- get_item_by_id function
- get_market_items_for_game function
- get_price_history_for_items function
- get_item_price function
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.smart_notifications.utils import (
    get_item_by_id,
    get_item_price,
    get_market_data_for_items,
    get_market_items_for_game,
    get_price_history_for_items,
)
from src.utils.exceptions import APIError, NetworkError


class TestGetMarketDataForItems:
    """Tests for get_market_data_for_items function."""

    @pytest.mark.asyncio
    async def test_get_market_data_success(self) -> None:
        """Test getting market data successfully."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {"itemId": "item_1", "title": "Item 1", "price": 100},
                    {"itemId": "item_2", "title": "Item 2", "price": 200},
                ]
            }
        )

        result = await get_market_data_for_items(
            api=mock_api,
            item_ids=["item_1", "item_2"],
            game="csgo",
        )

        assert "item_1" in result
        assert "item_2" in result
        assert result["item_1"]["title"] == "Item 1"

    @pytest.mark.asyncio
    async def test_get_market_data_batches_large_requests(self) -> None:
        """Test that large requests are batched."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"items": []})

        # Create 100 item IDs
        item_ids = [f"item_{i}" for i in range(100)]

        with patch("src.telegram_bot.smart_notifications.utils.asyncio.sleep"):
            await get_market_data_for_items(
                api=mock_api,
                item_ids=item_ids,
                game="csgo",
            )

            # Should make 2 requests (batch size is 50)
            assert mock_api._request.call_count == 2

    @pytest.mark.asyncio
    async def test_get_market_data_handles_api_error(self) -> None:
        """Test handling API error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=APIError("API Error"))

        result = await get_market_data_for_items(
            api=mock_api,
            item_ids=["item_1"],
            game="csgo",
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_market_data_handles_network_error(self) -> None:
        """Test handling network error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=NetworkError("Network Error"))

        result = await get_market_data_for_items(
            api=mock_api,
            item_ids=["item_1"],
            game="csgo",
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_market_data_handles_unexpected_error(self) -> None:
        """Test handling unexpected error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=Exception("Unexpected"))

        result = await get_market_data_for_items(
            api=mock_api,
            item_ids=["item_1"],
            game="csgo",
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_market_data_empty_list(self) -> None:
        """Test with empty item list."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"items": []})

        result = await get_market_data_for_items(
            api=mock_api,
            item_ids=[],
            game="csgo",
        )

        assert result == {}
        mock_api._request.assert_not_called()


class TestGetItemById:
    """Tests for get_item_by_id function."""

    @pytest.mark.asyncio
    async def test_get_item_success(self) -> None:
        """Test getting single item successfully."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {"itemId": "item_123", "title": "Test Item", "price": 1000}
                ]
            }
        )

        result = await get_item_by_id(
            api=mock_api,
            item_id="item_123",
            game="csgo",
        )

        assert result is not None
        assert result["itemId"] == "item_123"
        assert result["title"] == "Test Item"

    @pytest.mark.asyncio
    async def test_get_item_not_found(self) -> None:
        """Test getting item that doesn't exist."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"items": []})

        result = await get_item_by_id(
            api=mock_api,
            item_id="nonexistent",
            game="csgo",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_item_handles_api_error(self) -> None:
        """Test handling API error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=APIError("Error"))

        result = await get_item_by_id(
            api=mock_api,
            item_id="item_123",
            game="csgo",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_item_handles_network_error(self) -> None:
        """Test handling network error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=NetworkError("Network Error"))

        result = await get_item_by_id(
            api=mock_api,
            item_id="item_123",
            game="csgo",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_item_handles_unexpected_error(self) -> None:
        """Test handling unexpected error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=Exception("Unexpected"))

        result = await get_item_by_id(
            api=mock_api,
            item_id="item_123",
            game="csgo",
        )

        assert result is None


class TestGetMarketItemsForGame:
    """Tests for get_market_items_for_game function."""

    @pytest.mark.asyncio
    async def test_get_items_success(self) -> None:
        """Test getting market items successfully."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {"itemId": "1", "title": "Item 1"},
                    {"itemId": "2", "title": "Item 2"},
                ]
            }
        )

        result = await get_market_items_for_game(
            api=mock_api,
            game="csgo",
            limit=100,
        )

        assert len(result) == 2
        assert result[0]["title"] == "Item 1"

    @pytest.mark.asyncio
    async def test_get_items_with_custom_limit(self) -> None:
        """Test getting items with custom limit."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"items": []})

        await get_market_items_for_game(
            api=mock_api,
            game="dota2",
            limit=50,
        )

        call_args = mock_api._request.call_args
        assert call_args.kwargs["params"]["limit"] == 50
        assert call_args.kwargs["params"]["gameId"] == "dota2"

    @pytest.mark.asyncio
    async def test_get_items_handles_api_error(self) -> None:
        """Test handling API error returns empty list."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=APIError("Error"))

        result = await get_market_items_for_game(
            api=mock_api,
            game="csgo",
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_items_handles_network_error(self) -> None:
        """Test handling network error returns empty list."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=NetworkError("Error"))

        result = await get_market_items_for_game(
            api=mock_api,
            game="csgo",
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_items_handles_unexpected_error(self) -> None:
        """Test handling unexpected error returns empty list."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=Exception("Unexpected"))

        result = await get_market_items_for_game(
            api=mock_api,
            game="csgo",
        )

        assert result == []


class TestGetPriceHistoryForItems:
    """Tests for get_price_history_for_items function."""

    @pytest.mark.asyncio
    async def test_get_history_success(self) -> None:
        """Test getting price history successfully."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "data": [
                    {"date": "2024-01-01", "price": 100},
                    {"date": "2024-01-02", "price": 110},
                ]
            }
        )

        with patch("src.telegram_bot.smart_notifications.utils.asyncio.sleep"):
            result = await get_price_history_for_items(
                api=mock_api,
                item_ids=["item_1"],
                game="csgo",
            )

        assert "item_1" in result
        assert len(result["item_1"]) == 2

    @pytest.mark.asyncio
    async def test_get_history_multiple_items(self) -> None:
        """Test getting history for multiple items."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={"data": [{"date": "2024-01-01", "price": 100}]}
        )

        with patch("src.telegram_bot.smart_notifications.utils.asyncio.sleep"):
            result = await get_price_history_for_items(
                api=mock_api,
                item_ids=["item_1", "item_2", "item_3"],
                game="csgo",
            )

        # Should make 3 requests
        assert mock_api._request.call_count == 3

    @pytest.mark.asyncio
    async def test_get_history_handles_api_error(self) -> None:
        """Test handling API error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=APIError("Error"))

        result = await get_price_history_for_items(
            api=mock_api,
            item_ids=["item_1"],
            game="csgo",
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_history_handles_network_error(self) -> None:
        """Test handling network error."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=NetworkError("Error"))

        result = await get_price_history_for_items(
            api=mock_api,
            item_ids=["item_1"],
            game="csgo",
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_history_empty_response(self) -> None:
        """Test handling empty response."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"data": []})

        with patch("src.telegram_bot.smart_notifications.utils.asyncio.sleep"):
            result = await get_price_history_for_items(
                api=mock_api,
                item_ids=["item_1"],
                game="csgo",
            )

        # Empty data should not be added
        assert result == {}


class TestGetItemPrice:
    """Tests for get_item_price function."""

    def test_get_price_dict_with_amount(self) -> None:
        """Test getting price from dict with amount field."""
        item_data = {"price": {"amount": 1000}}  # $10.00

        result = get_item_price(item_data)

        assert result == 10.0

    def test_get_price_numeric_value(self) -> None:
        """Test getting price from numeric value."""
        item_data = {"price": 25.50}

        result = get_item_price(item_data)

        assert result == 25.50

    def test_get_price_int_value(self) -> None:
        """Test getting price from integer value."""
        item_data = {"price": 100}

        result = get_item_price(item_data)

        assert result == 100.0

    def test_get_price_no_price_field(self) -> None:
        """Test getting price when no price field."""
        item_data = {"title": "Item without price"}

        result = get_item_price(item_data)

        assert result == 0.0

    def test_get_price_empty_data(self) -> None:
        """Test getting price from empty data."""
        item_data: dict = {}

        result = get_item_price(item_data)

        assert result == 0.0

    def test_get_price_dict_without_amount(self) -> None:
        """Test getting price from dict without amount."""
        item_data = {"price": {"value": 100}}  # No 'amount' key

        result = get_item_price(item_data)

        assert result == 0.0

    def test_get_price_zero_value(self) -> None:
        """Test getting zero price."""
        item_data = {"price": {"amount": 0}}

        result = get_item_price(item_data)

        assert result == 0.0

    def test_get_price_large_amount(self) -> None:
        """Test getting large price value."""
        item_data = {"price": {"amount": 1000000}}  # $10,000

        result = get_item_price(item_data)

        assert result == 10000.0


class TestUtilsIntegration:
    """Integration tests for utils module."""

    @pytest.mark.asyncio
    async def test_get_item_and_extract_price(self) -> None:
        """Test getting item and extracting price."""
        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {
                        "itemId": "item_123",
                        "title": "AK-47 | Redline",
                        "price": {"amount": 5000},  # $50.00
                    }
                ]
            }
        )

        # Get item
        item = await get_item_by_id(mock_api, "item_123", "csgo")
        assert item is not None

        # Extract price
        price = get_item_price(item)
        assert price == 50.0

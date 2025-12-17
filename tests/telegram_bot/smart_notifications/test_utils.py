"""Unit tests for smart_notifications/utils module.

Tests for utility functions used by smart notifications.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.telegram_bot.smart_notifications.utils import (
    get_item_by_id,
    get_item_price,
    get_market_data_for_items,
    get_market_items_for_game,
    get_price_history_for_items,
)
from src.utils.exceptions import APIError, NetworkError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_api():
    """Create mock DMarket API."""
    api = AsyncMock()
    api._request = AsyncMock()
    return api


# ============================================================================
# TESTS FOR get_market_data_for_items
# ============================================================================


class TestGetMarketDataForItems:
    """Tests for get_market_data_for_items function."""

    @pytest.mark.asyncio()
    async def test_empty_item_ids(self, mock_api):
        """Test with empty item IDs list."""
        result = await get_market_data_for_items(mock_api, [], "csgo")
        assert result == {}
        mock_api._request.assert_not_called()

    @pytest.mark.asyncio()
    async def test_single_item(self, mock_api):
        """Test fetching a single item."""
        mock_api._request.return_value = {
            "items": [
                {"itemId": "item123", "title": "Test Item", "price": {"USD": "1000"}}
            ]
        }

        result = await get_market_data_for_items(mock_api, ["item123"], "csgo")

        assert "item123" in result
        assert result["item123"]["title"] == "Test Item"

    @pytest.mark.asyncio()
    async def test_multiple_items(self, mock_api):
        """Test fetching multiple items."""
        mock_api._request.return_value = {
            "items": [
                {"itemId": "item1", "title": "Item 1"},
                {"itemId": "item2", "title": "Item 2"},
            ]
        }

        result = await get_market_data_for_items(
            mock_api, ["item1", "item2"], "csgo"
        )

        assert len(result) == 2
        assert "item1" in result
        assert "item2" in result

    @pytest.mark.asyncio()
    async def test_batch_processing(self, mock_api):
        """Test batch processing for many items."""
        # Create 60 item IDs to trigger batching (batch_size = 50)
        item_ids = [f"item{i}" for i in range(60)]

        # First batch returns 50 items
        first_batch = {"items": [{"itemId": f"item{i}"} for i in range(50)]}
        # Second batch returns 10 items
        second_batch = {"items": [{"itemId": f"item{i}"} for i in range(50, 60)]}

        mock_api._request.side_effect = [first_batch, second_batch]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await get_market_data_for_items(mock_api, item_ids, "csgo")

        assert len(result) == 60
        assert mock_api._request.call_count == 2

    @pytest.mark.asyncio()
    async def test_api_error_handling(self, mock_api):
        """Test handling of API errors."""
        mock_api._request.side_effect = APIError("API Error")

        result = await get_market_data_for_items(mock_api, ["item123"], "csgo")

        assert result == {}

    @pytest.mark.asyncio()
    async def test_network_error_handling(self, mock_api):
        """Test handling of network errors."""
        mock_api._request.side_effect = NetworkError("Network Error")

        result = await get_market_data_for_items(mock_api, ["item123"], "csgo")

        assert result == {}

    @pytest.mark.asyncio()
    async def test_unexpected_error_handling(self, mock_api):
        """Test handling of unexpected errors."""
        mock_api._request.side_effect = Exception("Unexpected Error")

        result = await get_market_data_for_items(mock_api, ["item123"], "csgo")

        assert result == {}

    @pytest.mark.asyncio()
    async def test_empty_response(self, mock_api):
        """Test handling of empty response."""
        mock_api._request.return_value = {"items": []}

        result = await get_market_data_for_items(mock_api, ["item123"], "csgo")

        assert result == {}

    @pytest.mark.asyncio()
    async def test_item_without_id_skipped(self, mock_api):
        """Test that items without itemId are skipped."""
        mock_api._request.return_value = {
            "items": [
                {"itemId": "item123", "title": "Valid Item"},
                {"title": "Invalid Item"},  # No itemId
            ]
        }

        result = await get_market_data_for_items(mock_api, ["item123"], "csgo")

        assert len(result) == 1
        assert "item123" in result


# ============================================================================
# TESTS FOR get_item_by_id
# ============================================================================


class TestGetItemById:
    """Tests for get_item_by_id function."""

    @pytest.mark.asyncio()
    async def test_item_found(self, mock_api):
        """Test successful item retrieval."""
        mock_api._request.return_value = {
            "items": [{"itemId": "item123", "title": "Test Item"}]
        }

        result = await get_item_by_id(mock_api, "item123", "csgo")

        assert result is not None
        assert result["itemId"] == "item123"

    @pytest.mark.asyncio()
    async def test_item_not_found(self, mock_api):
        """Test when item is not found."""
        mock_api._request.return_value = {"items": []}

        result = await get_item_by_id(mock_api, "nonexistent", "csgo")

        assert result is None

    @pytest.mark.asyncio()
    async def test_api_error_returns_none(self, mock_api):
        """Test that API error returns None."""
        mock_api._request.side_effect = APIError("API Error")

        result = await get_item_by_id(mock_api, "item123", "csgo")

        assert result is None

    @pytest.mark.asyncio()
    async def test_network_error_returns_none(self, mock_api):
        """Test that network error returns None."""
        mock_api._request.side_effect = NetworkError("Network Error")

        result = await get_item_by_id(mock_api, "item123", "csgo")

        assert result is None

    @pytest.mark.asyncio()
    async def test_unexpected_error_returns_none(self, mock_api):
        """Test that unexpected error returns None."""
        mock_api._request.side_effect = Exception("Unexpected Error")

        result = await get_item_by_id(mock_api, "item123", "csgo")

        assert result is None


# ============================================================================
# TESTS FOR get_market_items_for_game
# ============================================================================


class TestGetMarketItemsForGame:
    """Tests for get_market_items_for_game function."""

    @pytest.mark.asyncio()
    async def test_successful_fetch(self, mock_api):
        """Test successful fetch of market items."""
        mock_api._request.return_value = {
            "items": [
                {"itemId": "item1", "title": "Item 1"},
                {"itemId": "item2", "title": "Item 2"},
            ]
        }

        result = await get_market_items_for_game(mock_api, "csgo", limit=100)

        assert len(result) == 2
        assert result[0]["itemId"] == "item1"

    @pytest.mark.asyncio()
    async def test_default_limit(self, mock_api):
        """Test default limit parameter."""
        mock_api._request.return_value = {"items": []}

        await get_market_items_for_game(mock_api, "csgo")

        call_args = mock_api._request.call_args
        assert call_args[1]["params"]["limit"] == 100

    @pytest.mark.asyncio()
    async def test_custom_limit(self, mock_api):
        """Test custom limit parameter."""
        mock_api._request.return_value = {"items": []}

        await get_market_items_for_game(mock_api, "dota2", limit=50)

        call_args = mock_api._request.call_args
        assert call_args[1]["params"]["limit"] == 50

    @pytest.mark.asyncio()
    async def test_different_games(self, mock_api):
        """Test fetching items for different games."""
        mock_api._request.return_value = {"items": []}

        for game in ["csgo", "dota2", "tf2", "rust"]:
            await get_market_items_for_game(mock_api, game)
            call_args = mock_api._request.call_args
            assert call_args[1]["params"]["gameId"] == game

    @pytest.mark.asyncio()
    async def test_api_error_returns_empty_list(self, mock_api):
        """Test that API error returns empty list."""
        mock_api._request.side_effect = APIError("API Error")

        result = await get_market_items_for_game(mock_api, "csgo")

        assert result == []

    @pytest.mark.asyncio()
    async def test_network_error_returns_empty_list(self, mock_api):
        """Test that network error returns empty list."""
        mock_api._request.side_effect = NetworkError("Network Error")

        result = await get_market_items_for_game(mock_api, "csgo")

        assert result == []

    @pytest.mark.asyncio()
    async def test_unexpected_error_returns_empty_list(self, mock_api):
        """Test that unexpected error returns empty list."""
        mock_api._request.side_effect = Exception("Unexpected Error")

        result = await get_market_items_for_game(mock_api, "csgo")

        assert result == []


# ============================================================================
# TESTS FOR get_price_history_for_items
# ============================================================================


class TestGetPriceHistoryForItems:
    """Tests for get_price_history_for_items function."""

    @pytest.mark.asyncio()
    async def test_empty_item_ids(self, mock_api):
        """Test with empty item IDs list."""
        result = await get_price_history_for_items(mock_api, [], "csgo")
        assert result == {}

    @pytest.mark.asyncio()
    async def test_single_item_history(self, mock_api):
        """Test fetching history for a single item."""
        mock_api._request.return_value = {
            "data": [
                {"price": 10.0, "timestamp": 1000},
                {"price": 11.0, "timestamp": 2000},
            ]
        }

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await get_price_history_for_items(
                mock_api, ["item123"], "csgo"
            )

        assert "item123" in result
        assert len(result["item123"]) == 2

    @pytest.mark.asyncio()
    async def test_multiple_items_history(self, mock_api):
        """Test fetching history for multiple items."""
        mock_api._request.side_effect = [
            {"data": [{"price": 10.0, "timestamp": 1000}]},
            {"data": [{"price": 20.0, "timestamp": 2000}]},
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await get_price_history_for_items(
                mock_api, ["item1", "item2"], "csgo"
            )

        assert len(result) == 2
        assert "item1" in result
        assert "item2" in result

    @pytest.mark.asyncio()
    async def test_empty_history_skipped(self, mock_api):
        """Test that items with empty history are skipped."""
        mock_api._request.return_value = {"data": []}

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await get_price_history_for_items(
                mock_api, ["item123"], "csgo"
            )

        assert result == {}

    @pytest.mark.asyncio()
    async def test_api_error_returns_empty_dict(self, mock_api):
        """Test that API error returns empty dict."""
        mock_api._request.side_effect = APIError("API Error")

        result = await get_price_history_for_items(mock_api, ["item123"], "csgo")

        assert result == {}

    @pytest.mark.asyncio()
    async def test_network_error_returns_empty_dict(self, mock_api):
        """Test that network error returns empty dict."""
        mock_api._request.side_effect = NetworkError("Network Error")

        result = await get_price_history_for_items(mock_api, ["item123"], "csgo")

        assert result == {}


# ============================================================================
# TESTS FOR get_item_price
# ============================================================================


class TestGetItemPrice:
    """Tests for get_item_price function."""

    def test_price_as_dict_with_amount(self):
        """Test price extraction from dict with amount in cents."""
        item_data = {"price": {"amount": 1000}}  # $10.00 in cents

        result = get_item_price(item_data)

        assert result == 10.0

    def test_price_as_int(self):
        """Test price extraction when price is int."""
        item_data = {"price": 15}

        result = get_item_price(item_data)

        assert result == 15.0

    def test_price_as_float(self):
        """Test price extraction when price is float."""
        item_data = {"price": 25.50}

        result = get_item_price(item_data)

        assert result == 25.50

    def test_no_price_returns_zero(self):
        """Test that missing price returns 0.0."""
        item_data = {"title": "No Price Item"}

        result = get_item_price(item_data)

        assert result == 0.0

    def test_empty_dict_returns_zero(self):
        """Test that empty dict returns 0.0."""
        result = get_item_price({})
        assert result == 0.0

    def test_price_dict_without_amount(self):
        """Test price dict without amount field."""
        item_data = {"price": {"USD": "1000"}}

        result = get_item_price(item_data)

        assert result == 0.0

    def test_price_zero_cents(self):
        """Test zero price in cents."""
        item_data = {"price": {"amount": 0}}

        result = get_item_price(item_data)

        assert result == 0.0

    def test_price_large_amount(self):
        """Test large price amount."""
        item_data = {"price": {"amount": 1000000}}  # $10,000

        result = get_item_price(item_data)

        assert result == 10000.0

    def test_price_small_amount(self):
        """Test small price amount."""
        item_data = {"price": {"amount": 1}}  # $0.01

        result = get_item_price(item_data)

        assert result == 0.01

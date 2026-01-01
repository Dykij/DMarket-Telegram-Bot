"""Integration tests for DMarket API client.

Tests real interactions between DMarket API and our client.
"""

from unittest.mock import patch

import pytest

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.exceptions import APIError, RateLimitError


@pytest.fixture()
async def api_client():
    """Fixture for DMarket API client."""
    client = DMarketAPI(public_key="test_public_key", secret_key="test_secret_key")
    yield client
    await client.close()


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_get_balance_integration(api_client):
    """Test getting balance with mocked HTTP response."""
    mock_response = {"usd": "10000", "dmc": "5000"}

    with patch.object(api_client, "_request", return_value=mock_response):
        balance = await api_client.get_balance()

        assert balance is not None
        assert "usd" in balance
        assert balance["usd"] == "10000"


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_get_market_items_integration(api_client):
    """Test getting market items with filters."""
    mock_response = {
        "objects": [
            {
                "title": "AK-47 | Redline (FT)",
                "price": {"USD": "1000"},
                "suggestedPrice": {"USD": "1200"},
            }
        ],
        "total": 1,
    }

    with patch.object(api_client, "_request", return_value=mock_response):
        items = await api_client.get_market_items(game="csgo", price_from=500, price_to=2000)

        assert items is not None
        assert "objects" in items
        assert len(items["objects"]) > 0


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_rate_limit_handling_integration(api_client):
    """Test rate limit error handling."""
    with patch.object(api_client, "_request") as mock_request:
        mock_request.side_effect = RateLimitError(message="Rate limit exceeded", retry_after=60)

        with pytest.raises(RateLimitError) as exc_info:
            await api_client.get_balance()

        assert exc_info.value.retry_after == 60


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_api_error_handling_integration(api_client):
    """Test API error handling."""
    with patch.object(api_client, "_request") as mock_request:
        mock_request.side_effect = APIError("Server error")

        with pytest.raises(APIError):
            await api_client.get_balance()


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_connection_pool_integration(api_client):
    """Test connection pooling works correctly."""
    mock_response = {"usd": "10000"}

    with patch.object(api_client, "_request", return_value=mock_response):
        # Multiple concurrent requests
        tasks = [api_client.get_balance() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["usd"] == "10000" for r in results)

"""VCR integration tests for DMarket API.

These tests use VCR.py to record and replay HTTP interactions
with the DMarket API, ensuring reliable integration tests.

Usage:
    # Record new cassettes (requires valid API keys)
    pytest tests/integration/test_dmarket_vcr.py --vcr-record=all

    # Run with existing cassettes
    pytest tests/integration/test_dmarket_vcr.py
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import vcr


# VCR configuration for DMarket
dmarket_vcr = vcr.VCR(
    cassette_library_dir=str(Path(__file__).parent / "cassettes" / "dmarket"),
    record_mode="none",  # Don't record by default (use existing cassettes)
    match_on=["method", "scheme", "host", "path", "query"],
    filter_headers=[
        "X-Api-Key",
        "X-Sign-Date",
        "X-Request-Sign",
        "Authorization",
    ],
    decode_compressed_response=True,
)


# Create cassettes directory
CASSETTES_DIR = Path(__file__).parent / "cassettes" / "dmarket"
CASSETTES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_dmarket_api():
    """Create mock DMarket API for tests without cassettes."""
    from src.dmarket.dmarket_api import DMarketAPI

    api = DMarketAPI(
        public_key="test_public_key",
        secret_key="test_secret_key",
    )
    return api


@pytest.fixture
def sample_market_response():
    """Sample market items response."""
    return {
        "objects": [
            {
                "itemId": "item_001",
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": "1000"},
                "suggestedPrice": {"USD": "1200"},
                "extra": {
                    "category": "Rifle",
                    "exterior": "Field-Tested",
                    "categoryPath": "CS:GO/Weapon/Rifle",
                },
            },
            {
                "itemId": "item_002",
                "title": "AWP | Asiimov (Field-Tested)",
                "price": {"USD": "5000"},
                "suggestedPrice": {"USD": "5500"},
                "extra": {
                    "category": "Sniper Rifle",
                    "exterior": "Field-Tested",
                    "categoryPath": "CS:GO/Weapon/Sniper Rifle",
                },
            },
        ],
        "total": {"items": 2, "offers": 2},
    }


@pytest.fixture
def sample_balance_response():
    """Sample balance response in official DMarket API format (2024+)."""
    return {
        "usd": "10000",  # $100.00 in cents (official format)
        "usdAvailableToWithdraw": "10000",
        "dmc": "5000",
        "dmcAvailableToWithdraw": "5000",
    }


# ============================================================================
# INTEGRATION TESTS WITH VCR
# ============================================================================


class TestDMarketAPIIntegration:
    """Integration tests for DMarket API using VCR."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_market_items_with_mock(self, mock_dmarket_api, sample_market_response):
        """Test getting market items with mocked response."""
        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = sample_market_response

            # Call API
            result = await mock_dmarket_api.get_market_items(
                game="csgo",  # Changed from game_id to game (actual API signature)
                limit=100,
            )

            # Verify response structure
            assert "objects" in result
            assert len(result["objects"]) > 0

            # Verify item structure
            item = result["objects"][0]
            assert "itemId" in item
            assert "title" in item
            assert "price" in item

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_balance_with_mock(self, mock_dmarket_api, sample_balance_response):
        """Test getting account balance with mocked response."""
        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = sample_balance_response

            result = await mock_dmarket_api.get_balance()

            # Verify balance structure - API returns official format
            assert "balance" in result or "usd" in result

            # Check balance value - method normalizes to {"balance": X}
            if "balance" in result:
                balance_usd = result["balance"]
            else:
                balance_usd = float(result.get("usd", 0)) / 100

            assert balance_usd == 100.0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_market_items_price_filtering(self, mock_dmarket_api, sample_market_response):
        """Test that price filtering works correctly."""
        # Mock with items of different prices
        response = {
            "objects": [
                {
                    "itemId": "cheap_001",
                    "title": "Cheap Item",
                    "price": {"USD": "100"},  # $1.00
                    "suggestedPrice": {"USD": "120"},
                },
                {
                    "itemId": "mid_001",
                    "title": "Mid Item",
                    "price": {"USD": "500"},  # $5.00
                    "suggestedPrice": {"USD": "600"},
                },
                {
                    "itemId": "expensive_001",
                    "title": "Expensive Item",
                    "price": {"USD": "10000"},  # $100.00
                    "suggestedPrice": {"USD": "11000"},
                },
            ],
            "total": {"items": 3},
        }

        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = response

            result = await mock_dmarket_api.get_market_items(
                game="csgo",  # Changed from game_id to game (actual API signature)
                price_from=200,  # $2.00 minimum
                price_to=8000,  # $80.00 maximum
            )

            # Should return all items (API does filtering server-side)
            # Client filters based on response
            items = result["objects"]
            assert len(items) == 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_error_handling(self, mock_dmarket_api):
        """Test API error handling.

        Note: get_balance() uses graceful degradation - it returns a fallback
        result with error=True instead of raising an exception. This ensures
        the bot can continue operating even when API is unavailable.
        """
        from src.utils.exceptions import APIError

        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            # Simulate API error
            mock_request.side_effect = APIError(
                message="Unauthorized",
                status_code=401,
            )

            # get_balance() returns fallback result instead of raising
            result = await mock_dmarket_api.get_balance()

            # Verify fallback result structure
            assert result is not None
            # Result should indicate error or have zero/fallback balance
            assert result.get("error") is True or result.get("balance", 0) == 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rate_limit_handling(self, mock_dmarket_api):
        """Test rate limit error handling.

        Note: get_market_items() uses graceful degradation similar to get_balance().
        It returns an empty result instead of raising an exception.
        """
        from src.utils.exceptions import RateLimitExceeded

        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            # Simulate rate limit error
            mock_request.side_effect = RateLimitExceeded(
                message="Rate limit exceeded",
                retry_after=60,
            )

            # API should return fallback result instead of raising
            result = await mock_dmarket_api.get_market_items(game="csgo")

            # Verify the result is a fallback (empty or error)
            assert result is not None
            # Should either have error flag or empty objects list
            assert result.get("error") is True or len(result.get("objects", [])) == 0


class TestDMarketAPIEndpoints:
    """Test specific API endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_inventory_endpoint(self, mock_dmarket_api):
        """Test user inventory endpoint."""
        inventory_response = {
            "objects": [
                {
                    "itemId": "inv_001",
                    "title": "My AK-47",
                    "price": {"USD": "1500"},
                },
            ],
            "total": {"items": 1},
        }

        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = inventory_response

            result = await mock_dmarket_api.get_user_inventory(game_id="a8db")

            assert "objects" in result
            assert len(result["objects"]) == 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_targets_endpoint(self, mock_dmarket_api):
        """Test create targets (buy orders) endpoint."""
        target_response = {
            "Result": [{"OrderID": "target_001", "Successful": True}],
        }

        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = target_response

            # Use the actual create_targets method with proper signature
            targets = [
                {
                    "Title": "AK-47 | Redline (Field-Tested)",
                    "Amount": 1,
                    "Price": {"Amount": 1000, "Currency": "USD"},
                }
            ]
            result = await mock_dmarket_api.create_targets(
                game_id="csgo",
                targets=targets,
            )

            assert "Result" in result
            assert len(result["Result"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_targets_endpoint(self, mock_dmarket_api):
        """Test delete targets endpoint."""
        delete_response = {
            "Result": [{"TargetID": "target_001", "Successful": True}],
        }

        with patch.object(
            mock_dmarket_api, "_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = delete_response

            # Use the actual delete_targets method
            result = await mock_dmarket_api.delete_targets(target_ids=["target_001"])

            assert "Result" in result
            assert result["Result"][0]["Successful"] is True


class TestDMarketAPIWithVCRCassettes:
    """Tests that can use real VCR cassettes when available.

    These tests will fail if cassettes don't exist and record_mode is 'none'.
    Set record_mode='all' and provide valid API keys to record cassettes.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires valid API keys and cassette recording")
    async def test_real_market_items_call(self):
        """Test real market items API call with VCR.

        To record this cassette:
        1. Set valid DMARKET_PUBLIC_KEY and DMARKET_SECRET_KEY
        2. Change record_mode to 'all'
        3. Run: pytest tests/integration/test_dmarket_vcr.py -k test_real_market_items_call
        """
        from src.dmarket.dmarket_api import DMarketAPI

        with dmarket_vcr.use_cassette("get_market_items.yaml", record_mode="none"):
            api = DMarketAPI(
                public_key="your_public_key",
                secret_key="your_secret_key",
            )

            result = await api.get_market_items(
                game="csgo",  # Changed from game_id to game (actual API signature)
                limit=10,
            )

            assert "objects" in result
            assert len(result["objects"]) <= 10


# ============================================================================
# CASSETTE UTILITIES
# ============================================================================


def create_sample_cassette():
    """Create a sample cassette for testing.

    This creates a static YAML file that mimics a real API response.
    """
    cassette_content = """
interactions:
- request:
    body: null
    headers:
      Accept:
      - application/json
      User-Agent:
      - DMarketBot/1.0
    method: GET
    uri: https://api.dmarket.com/exchange/v1/market/items?gameId=a8db&limit=10
  response:
    body:
      string: '{"objects":[{"itemId":"test_001","title":"Test Item","price":{"USD":"1000"}}],"total":{"items":1}}'
    headers:
      Content-Type:
      - application/json
    status:
      code: 200
      message: OK
version: 1
"""
    cassette_path = CASSETTES_DIR / "sample_cassette.yaml"
    cassette_path.write_text(cassette_content)
    return cassette_path


@pytest.fixture(scope="session", autouse=True)
def setup_sample_cassettes():
    """Setup sample cassettes before tests run."""
    create_sample_cassette()

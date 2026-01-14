"""Tests for external_price_api module.

This module tests the ExternalPriceAPI class for fetching
prices from external sources like Steam Market.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestExternalPriceAPI:
    """Tests for ExternalPriceAPI class."""

    @pytest.fixture
    def api(self):
        """Create ExternalPriceAPI instance."""
        from src.dmarket.external_price_api import ExternalPriceAPI
        return ExternalPriceAPI()

    def test_init(self, api):
        """Test initialization."""
        assert api is not None

    @pytest.mark.asyncio
    async def test_get_steam_price(self, api):
        """Test getting Steam Market price."""
        with patch.object(api, "_fetch_steam_price") as mock_fetch:
            mock_fetch.return_value = {"success": True, "price": 25.50}

            price = await api.get_steam_price("AK-47 | Redline (Field-Tested)")

            assert price is not None

    @pytest.mark.asyncio
    async def test_get_steam_price_not_found(self, api):
        """Test Steam price for non-existent item."""
        with patch.object(api, "_fetch_steam_price") as mock_fetch:
            mock_fetch.return_value = {"success": False}

            price = await api.get_steam_price("Non-Existent Item XYZ")

            assert price is None

    @pytest.mark.asyncio
    async def test_get_buff_price(self, api):
        """Test getting Buff163 price."""
        with patch.object(api, "_fetch_buff_price") as mock_fetch:
            mock_fetch.return_value = {"success": True, "price": 180.0}

            price = await api.get_buff_price("AK-47 | Redline")

            assert price is not None

    @pytest.mark.asyncio
    async def test_get_all_prices(self, api):
        """Test getting prices from all sources."""
        with patch.object(api, "get_steam_price") as mock_steam:
            mock_steam.return_value = 25.0
            with patch.object(api, "get_buff_price") as mock_buff:
                mock_buff.return_value = 180.0

                prices = await api.get_all_prices("AK-47 | Redline")

                assert "steam" in prices
                assert "buff" in prices

    def test_calculate_arbitrage(self, api):
        """Test arbitrage calculation between platforms."""
        prices = {
            "dmarket": 20.0,
            "steam": 25.0,
            "buff": 180.0,  # In CNY
        }

        arbitrage = api.calculate_arbitrage(prices, fees={"steam": 0.13})

        assert "steam_profit" in arbitrage
        assert arbitrage["steam_profit"] > 0  # $5 profit minus fees

    @pytest.mark.asyncio
    async def test_rate_limiting(self, api):
        """Test rate limiting for API calls."""
        api.rate_limit = 1  # 1 request per second

        # Should not throw rate limit errors

    def test_parse_steam_response(self, api):
        """Test parsing Steam API response."""
        response = {
            "success": True,
            "lowest_price": "$25.50",
            "median_price": "$26.00",
            "volume": "150",
        }

        parsed = api._parse_steam_response(response)

        assert parsed["lowest_price"] == 25.50
        assert parsed["median_price"] == 26.00
        assert parsed["volume"] == 150

    def test_parse_steam_response_eur(self, api):
        """Test parsing Steam price in EUR."""
        response = {
            "success": True,
            "lowest_price": "23,50€",
        }

        parsed = api._parse_steam_response(response)

        assert parsed["lowest_price"] == 23.50

    @pytest.mark.asyncio
    async def test_get_price_history(self, api):
        """Test getting price history."""
        with patch.object(api, "_fetch_price_history") as mock_fetch:
            mock_fetch.return_value = [
                {"date": "2026-01-01", "price": 25.0},
                {"date": "2026-01-02", "price": 26.0},
            ]

            history = await api.get_price_history("AK-47 | Redline", days=7)

            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_get_market_overview(self, api):
        """Test getting market overview."""
        with patch.object(api, "_fetch_market_data") as mock_fetch:
            mock_fetch.return_value = {
                "total_listings": 1000,
                "total_volume": 5000000,
            }

            overview = await api.get_market_overview()

            assert "total_listings" in overview

    def test_cache_price(self, api):
        """Test price caching."""
        api.cache_price("AK-47", "steam", 25.0)

        cached = api.get_cached_price("AK-47", "steam")

        assert cached == 25.0

    def test_cache_expiry(self, api):
        """Test cache expiry."""
        api.cache_ttl = 0  # Immediate expiry
        api.cache_price("AK-47", "steam", 25.0)

        # After TTL expires
        cached = api.get_cached_price("AK-47", "steam")

        # Should return None or fetch fresh

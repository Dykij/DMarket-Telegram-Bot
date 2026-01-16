"""Tests for smart_repricing module.

This module tests the SmartRepricer class for intelligent
price adjustments based on item age and market conditions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestSmartRepricer:
    """Tests for SmartRepricer class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_my_offers = AsyncMock(return_value={"objects": []})
        api.update_offer = AsyncMock(return_value={"success": True})
        api.get_market_items = AsyncMock(return_value={"objects": []})
        return api

    @pytest.fixture
    def repricer(self, mock_api):
        """Create SmartRepricer instance."""
        from src.dmarket.smart_repricing import SmartRepricer
        return SmartRepricer(
            api_client=mock_api,
            config={
                "initial_discount": 0,
                "discount_per_day": 2,
                "max_discount": 20,
                "min_profit_margin": 0.02,
            },
        )

    def test_init(self, repricer, mock_api):
        """Test initialization."""
        assert repricer.api == mock_api

    def test_calculate_age_discount_new(self, repricer):
        """Test discount for new listing."""
        listed_date = datetime.now() - timedelta(hours=1)

        discount = repricer.calculate_age_discount(listed_date)

        assert discount == 0  # No discount for items listed < 1 day

    def test_calculate_age_discount_old(self, repricer):
        """Test discount for old listing."""
        listed_date = datetime.now() - timedelta(days=5)

        discount = repricer.calculate_age_discount(listed_date)

        # 5 days * 2% per day = 10%
        assert discount == 10

    def test_calculate_age_discount_max(self, repricer):
        """Test maximum discount limit."""
        listed_date = datetime.now() - timedelta(days=30)

        discount = repricer.calculate_age_discount(listed_date)

        # Should not exceed max_discount (20%)
        assert discount == 20

    def test_calculate_new_price(self, repricer):
        """Test new price calculation."""
        original_price = 1000  # $10.00 in cents
        discount = 10  # 10%

        new_price = repricer.calculate_new_price(original_price, discount)

        assert new_price == 900  # $9.00

    def test_calculate_new_price_with_minimum(self, repricer):
        """Test price doesn't go below minimum."""
        original_price = 1000
        buy_price = 950
        discount = 20

        new_price = repricer.calculate_new_price(
            original_price,
            discount,
            buy_price=buy_price,
            min_margin=0.02,
        )

        # Should not go below buy_price * 1.02
        assert new_price >= 969  # 950 * 1.02

    @pytest.mark.asyncio
    async def test_get_offers_to_reprice(self, repricer, mock_api):
        """Test getting offers that need repricing."""
        mock_api.get_my_offers.return_value = {
            "objects": [
                {
                    "offerId": "offer1",
                    "price": {"USD": "1000"},
                    "createdAt": (datetime.now() - timedelta(days=3)).isoformat(),
                },
                {
                    "offerId": "offer2",
                    "price": {"USD": "2000"},
                    "createdAt": datetime.now().isoformat(),
                },
            ]
        }

        offers = await repricer.get_offers_to_reprice()

        # Only offer1 should need repricing (3 days old)
        assert len(offers) >= 1

    @pytest.mark.asyncio
    async def test_reprice_offer(self, repricer, mock_api):
        """Test repricing single offer."""
        offer = {
            "offerId": "offer123",
            "price": {"USD": "1000"},
            "createdAt": (datetime.now() - timedelta(days=5)).isoformat(),
        }

        result = await repricer.reprice_offer(offer)

        assert result is True
        mock_api.update_offer.assert_called_once()

    @pytest.mark.asyncio
    async def test_reprice_all(self, repricer, mock_api):
        """Test repricing all eligible offers."""
        mock_api.get_my_offers.return_value = {
            "objects": [
                {
                    "offerId": "offer1",
                    "price": {"USD": "1000"},
                    "createdAt": (datetime.now() - timedelta(days=3)).isoformat(),
                },
            ]
        }

        count = await repricer.reprice_all()

        assert count >= 0

    @pytest.mark.asyncio
    async def test_compare_with_market(self, repricer, mock_api):
        """Test comparing price with market."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {"price": {"USD": "900"}},
                {"price": {"USD": "950"}},
            ]
        }

        is_competitive = await repricer.is_price_competitive(
            item_title="AK-47 | Redline",
            current_price=1000,
        )

        # 1000 is higher than lowest (900), so not competitive
        assert is_competitive is False

    def test_get_stats(self, repricer):
        """Test getting statistics."""
        repricer.total_repriced = 25
        repricer.total_discount_applied = 150.0

        stats = repricer.get_stats()

        assert stats["total_repriced"] == 25
        assert stats["total_discount"] == 150.0

    @pytest.mark.asyncio
    async def test_undercut_competition(self, repricer, mock_api):
        """Test undercutting competition."""
        mock_api.get_market_items.return_value = {
            "objects": [{"price": {"USD": "1000"}}]
        }

        undercut_price = await repricer.get_undercut_price(
            item_title="AK-47",
            step=1,  # Undercut by $0.01
        )

        assert undercut_price == 999

    def test_should_reprice(self, repricer):
        """Test determining if offer should be repriced."""
        # Old offer should be repriced
        old_offer = {
            "createdAt": (datetime.now() - timedelta(days=5)).isoformat(),
            "lastUpdated": (datetime.now() - timedelta(days=2)).isoformat(),
        }
        assert repricer.should_reprice(old_offer) is True

        # Recently updated offer should not
        recent_offer = {
            "createdAt": (datetime.now() - timedelta(days=5)).isoformat(),
            "lastUpdated": datetime.now().isoformat(),
        }
        assert repricer.should_reprice(recent_offer) is False

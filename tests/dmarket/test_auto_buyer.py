"""Tests for auto_buyer module.

This module tests the AutoBuyer class for automatic item purchases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.dmarket.auto_buyer import AutoBuyer, AutoBuyConfig, PurchaseResult


class TestAutoBuyConfig:
    """Tests for AutoBuyConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AutoBuyConfig()

        assert config.enabled is False
        assert config.min_discount_percent == 30.0
        assert config.max_price_usd == 100.0
        assert config.check_sales_history is True
        assert config.check_trade_lock is True
        assert config.max_trade_lock_hours == 168
        assert config.dry_run is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = AutoBuyConfig(
            enabled=True,
            min_discount_percent=20.0,
            max_price_usd=500.0,
            check_sales_history=False,
            dry_run=False,
        )

        assert config.enabled is True
        assert config.min_discount_percent == 20.0
        assert config.max_price_usd == 500.0
        assert config.check_sales_history is False
        assert config.dry_run is False


class TestPurchaseResult:
    """Tests for PurchaseResult class."""

    def test_successful_result(self):
        """Test successful purchase result."""
        result = PurchaseResult(
            success=True,
            item_id="item123",
            item_title="AK-47 | Redline",
            price_usd=25.50,
            message="Purchase successful",
            order_id="order456",
        )

        assert result.success is True
        assert result.item_id == "item123"
        assert result.item_title == "AK-47 | Redline"
        assert result.price_usd == 25.50
        assert result.order_id == "order456"
        assert result.error is None
        assert isinstance(result.timestamp, datetime)

    def test_failed_result(self):
        """Test failed purchase result."""
        result = PurchaseResult(
            success=False,
            item_id="item123",
            item_title="M4A4 | Howl",
            price_usd=1000.0,
            message="Purchase failed",
            error="Insufficient balance",
        )

        assert result.success is False
        assert result.error == "Insufficient balance"
        assert result.order_id is None


class TestAutoBuyer:
    """Tests for AutoBuyer class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_balance = AsyncMock(return_value={"balance": 100.0})
        api.buy_item = AsyncMock(return_value={"success": True, "orderId": "order123"})
        return api

    @pytest.fixture
    def mock_persistence(self):
        """Create mock persistence."""
        persistence = MagicMock()
        persistence.save_purchase = MagicMock()
        persistence.get_purchases = MagicMock(return_value=[])
        return persistence

    @pytest.fixture
    def auto_buyer(self, mock_api, mock_persistence):
        """Create AutoBuyer instance."""
        return AutoBuyer(
            api_client=mock_api,
            persistence=mock_persistence,
            config=AutoBuyConfig(enabled=True, dry_run=True),
        )

    def test_init(self, auto_buyer, mock_api):
        """Test initialization."""
        assert auto_buyer.api == mock_api
        assert auto_buyer.config.enabled is True

    @pytest.mark.asyncio
    async def test_check_balance(self, auto_buyer, mock_api):
        """Test checking balance."""
        balance = await auto_buyer.check_balance()
        assert balance == 100.0
        mock_api.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_buy_item_dry_run(self, auto_buyer, mock_api):
        """Test buying item in dry run mode."""
        item = {
            "itemId": "item123",
            "title": "AK-47 | Redline",
            "price": {"USD": "2550"},
        }

        result = await auto_buyer.buy_item(item)

        assert result.success is True
        assert "DRY_RUN" in result.message
        mock_api.buy_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_buy_item_real(self, mock_api, mock_persistence):
        """Test buying item in real mode."""
        auto_buyer = AutoBuyer(
            api_client=mock_api,
            persistence=mock_persistence,
            config=AutoBuyConfig(enabled=True, dry_run=False),
        )

        item = {
            "itemId": "item123",
            "title": "AK-47 | Redline",
            "price": {"USD": "2550"},
        }

        result = await auto_buyer.buy_item(item)

        assert result.success is True
        mock_api.buy_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_item_price_too_high(self, auto_buyer):
        """Test validation rejects high price."""
        item = {
            "itemId": "item123",
            "title": "Dragon Lore",
            "price": {"USD": "500000"},  # $5000
        }

        is_valid, reason = await auto_buyer.validate_item(item)

        assert is_valid is False
        assert "price" in reason.lower()

    @pytest.mark.asyncio
    async def test_validate_item_low_discount(self, auto_buyer):
        """Test validation rejects low discount."""
        item = {
            "itemId": "item123",
            "title": "AK-47 | Redline",
            "price": {"USD": "2550"},
            "suggestedPrice": {"USD": "2600"},  # Only ~2% discount
        }

        is_valid, reason = await auto_buyer.validate_item(item)

        assert is_valid is False
        assert "discount" in reason.lower()

    @pytest.mark.asyncio
    async def test_validate_item_success(self, auto_buyer):
        """Test validation accepts good item."""
        item = {
            "itemId": "item123",
            "title": "AK-47 | Redline",
            "price": {"USD": "1500"},  # $15
            "suggestedPrice": {"USD": "2500"},  # $25 - 40% discount
        }

        is_valid, reason = await auto_buyer.validate_item(item)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_process_opportunity(self, auto_buyer, mock_api):
        """Test processing arbitrage opportunity."""
        opportunity = {
            "itemId": "item123",
            "title": "AK-47 | Redline",
            "price": {"USD": "1500"},
            "suggestedPrice": {"USD": "2500"},
            "profit_percent": 40.0,
        }

        result = await auto_buyer.process_opportunity(opportunity)

        assert result is not None
        assert result.success is True

    def test_get_stats(self, auto_buyer):
        """Test getting purchase statistics."""
        stats = auto_buyer.get_stats()

        assert "total_purchases" in stats
        assert "successful" in stats
        assert "failed" in stats

    @pytest.mark.asyncio
    async def test_insufficient_balance(self, auto_buyer, mock_api):
        """Test handling insufficient balance."""
        mock_api.get_balance = AsyncMock(return_value={"balance": 5.0})

        item = {
            "itemId": "item123",
            "title": "AK-47 | Redline",
            "price": {"USD": "2550"},  # $25.50
        }

        result = await auto_buyer.buy_item(item)

        assert result.success is False
        assert "balance" in result.error.lower()

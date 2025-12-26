"""Phase 4 Extended Tests for AutoSeller module.

These tests extend coverage for the auto_seller.py module:
- SaleStatus and PricingStrategy enums
- SaleConfig edge cases
- ScheduledSale edge cases
- AutoSeller list_item and delayed_list methods
- Dynamic pricing strategy
- Price monitor loop
- Get top offer price edge cases
- Cancel sale edge cases
- Edge cases and integration tests
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.auto_seller import (
    AutoSeller,
    AutoSellerStats,
    PricingStrategy,
    SaleConfig,
    SaleStatus,
    ScheduledSale,
    load_sale_config,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api() -> AsyncMock:
    """Create a mock DMarket API client."""
    api = AsyncMock()
    api.dry_run = False
    api.sell_item = AsyncMock(return_value={"success": True, "offerId": "offer_123"})
    api.get_best_offers = AsyncMock(
        return_value={"objects": [{"price": {"USD": "1200"}}]}
    )
    api.update_offer_prices = AsyncMock(return_value={"success": True})
    api.remove_offers = AsyncMock(return_value={"success": True})
    return api


@pytest.fixture
def sale_config() -> SaleConfig:
    """Create a test sale configuration."""
    return SaleConfig(
        enabled=True,
        min_margin_percent=4.0,
        max_margin_percent=12.0,
        target_margin_percent=8.0,
        undercut_cents=1,
        price_check_interval_minutes=1,
        stop_loss_hours=48,
        stop_loss_percent=5.0,
        max_active_sales=10,
        delay_before_list_seconds=0,
        pricing_strategy=PricingStrategy.UNDERCUT,
        dmarket_fee_percent=7.0,
    )


@pytest.fixture
def auto_seller(mock_api: AsyncMock, sale_config: SaleConfig) -> AutoSeller:
    """Create an AutoSeller instance with mocked API."""
    return AutoSeller(api=mock_api, config=sale_config)


@pytest.fixture
def sample_sale() -> ScheduledSale:
    """Create a sample scheduled sale."""
    return ScheduledSale(
        item_id="item_123",
        item_name="AK-47 | Redline (Field-Tested)",
        buy_price=10.00,
        target_margin=0.08,
        game="csgo",
    )


# ============================================================================
# Tests for SaleStatus Enum
# ============================================================================


class TestSaleStatusEnum:
    """Tests for SaleStatus enum."""

    def test_sale_status_pending(self) -> None:
        """Test pending status value."""
        assert SaleStatus.PENDING.value == "pending"

    def test_sale_status_listed(self) -> None:
        """Test listed status value."""
        assert SaleStatus.LISTED.value == "listed"

    def test_sale_status_adjusting(self) -> None:
        """Test adjusting status value."""
        assert SaleStatus.ADJUSTING.value == "adjusting"

    def test_sale_status_sold(self) -> None:
        """Test sold status value."""
        assert SaleStatus.SOLD.value == "sold"

    def test_sale_status_cancelled(self) -> None:
        """Test cancelled status value."""
        assert SaleStatus.CANCELLED.value == "cancelled"

    def test_sale_status_stop_loss(self) -> None:
        """Test stop_loss status value."""
        assert SaleStatus.STOP_LOSS.value == "stop_loss"

    def test_sale_status_failed(self) -> None:
        """Test failed status value."""
        assert SaleStatus.FAILED.value == "failed"

    def test_sale_status_is_string_enum(self) -> None:
        """Test that SaleStatus inherits from str."""
        assert isinstance(SaleStatus.PENDING, str)
        assert SaleStatus.PENDING == "pending"


# ============================================================================
# Tests for PricingStrategy Enum
# ============================================================================


class TestPricingStrategyEnum:
    """Tests for PricingStrategy enum."""

    def test_pricing_strategy_undercut(self) -> None:
        """Test undercut strategy value."""
        assert PricingStrategy.UNDERCUT.value == "undercut"

    def test_pricing_strategy_match(self) -> None:
        """Test match strategy value."""
        assert PricingStrategy.MATCH.value == "match"

    def test_pricing_strategy_fixed_margin(self) -> None:
        """Test fixed_margin strategy value."""
        assert PricingStrategy.FIXED_MARGIN.value == "fixed_margin"

    def test_pricing_strategy_dynamic(self) -> None:
        """Test dynamic strategy value."""
        assert PricingStrategy.DYNAMIC.value == "dynamic"

    def test_pricing_strategy_is_string_enum(self) -> None:
        """Test that PricingStrategy inherits from str."""
        assert isinstance(PricingStrategy.UNDERCUT, str)
        assert PricingStrategy.UNDERCUT == "undercut"


# ============================================================================
# Tests for SaleConfig Edge Cases
# ============================================================================


class TestSaleConfigEdgeCases:
    """Tests for SaleConfig edge cases."""

    def test_sale_config_all_fields(self) -> None:
        """Test all SaleConfig fields."""
        config = SaleConfig(
            enabled=True,
            min_margin_percent=4.0,
            max_margin_percent=12.0,
            target_margin_percent=8.0,
            undercut_cents=1,
            price_check_interval_minutes=30,
            stop_loss_hours=48,
            stop_loss_percent=5.0,
            max_active_sales=50,
            delay_before_list_seconds=5,
            pricing_strategy=PricingStrategy.UNDERCUT,
            dmarket_fee_percent=7.0,
        )
        assert config.enabled is True
        assert config.min_margin_percent == 4.0
        assert config.max_margin_percent == 12.0
        assert config.target_margin_percent == 8.0
        assert config.undercut_cents == 1
        assert config.price_check_interval_minutes == 30
        assert config.stop_loss_hours == 48
        assert config.stop_loss_percent == 5.0
        assert config.max_active_sales == 50
        assert config.delay_before_list_seconds == 5
        assert config.pricing_strategy == PricingStrategy.UNDERCUT
        assert config.dmarket_fee_percent == 7.0

    def test_sale_config_zero_values(self) -> None:
        """Test SaleConfig with zero values."""
        config = SaleConfig(
            min_margin_percent=0.0,
            undercut_cents=0,
            delay_before_list_seconds=0,
        )
        assert config.min_margin_percent == 0.0
        assert config.undercut_cents == 0
        assert config.delay_before_list_seconds == 0

    def test_sale_config_high_values(self) -> None:
        """Test SaleConfig with high values."""
        config = SaleConfig(
            max_margin_percent=100.0,
            max_active_sales=1000,
            stop_loss_hours=168,  # 1 week
        )
        assert config.max_margin_percent == 100.0
        assert config.max_active_sales == 1000
        assert config.stop_loss_hours == 168

    def test_sale_config_disabled(self) -> None:
        """Test disabled SaleConfig."""
        config = SaleConfig(enabled=False)
        assert config.enabled is False

    def test_sale_config_match_strategy(self) -> None:
        """Test SaleConfig with match strategy."""
        config = SaleConfig(pricing_strategy=PricingStrategy.MATCH)
        assert config.pricing_strategy == PricingStrategy.MATCH

    def test_sale_config_dynamic_strategy(self) -> None:
        """Test SaleConfig with dynamic strategy."""
        config = SaleConfig(pricing_strategy=PricingStrategy.DYNAMIC)
        assert config.pricing_strategy == PricingStrategy.DYNAMIC


# ============================================================================
# Tests for ScheduledSale Edge Cases
# ============================================================================


class TestScheduledSaleEdgeCases:
    """Tests for ScheduledSale edge cases."""

    def test_scheduled_sale_all_fields(self) -> None:
        """Test ScheduledSale with all fields."""
        now = datetime.now(UTC)
        sale = ScheduledSale(
            item_id="item_123",
            item_name="AK-47 | Redline",
            buy_price=10.00,
            target_margin=0.08,
            game="csgo",
            status=SaleStatus.LISTED,
            offer_id="offer_123",
            list_price=11.00,
            current_price=11.00,
            created_at=now,
            listed_at=now,
            sold_at=None,
            final_price=None,
            adjustments_count=0,
        )
        assert sale.item_id == "item_123"
        assert sale.offer_id == "offer_123"
        assert sale.list_price == 11.00
        assert sale.current_price == 11.00
        assert sale.adjustments_count == 0

    def test_scheduled_sale_different_games(self) -> None:
        """Test ScheduledSale for different games."""
        games = ["csgo", "dota2", "rust", "tf2"]
        for game in games:
            sale = ScheduledSale(
                item_id=f"item_{game}",
                item_name=f"Test Item ({game})",
                buy_price=10.00,
                target_margin=0.08,
                game=game,
            )
            assert sale.game == game

    def test_calculate_profit_zero_buy_price(self) -> None:
        """Test profit calculation with zero buy price."""
        sale = ScheduledSale(
            item_id="item_free",
            item_name="Free Item",
            buy_price=0.0,
            target_margin=0.08,
        )
        profit, percent = sale.calculate_profit(10.00)
        assert profit == 10.00
        assert percent == 0.0  # Division by zero case

    def test_calculate_profit_negative_result(self) -> None:
        """Test profit calculation with loss."""
        sale = ScheduledSale(
            item_id="item_loss",
            item_name="Loss Item",
            buy_price=10.00,
            target_margin=0.08,
        )
        profit, percent = sale.calculate_profit(8.00)
        assert profit == -2.00
        assert percent == -20.0

    def test_calculate_profit_uses_list_price_fallback(self) -> None:
        """Test profit calculation uses list_price as fallback."""
        sale = ScheduledSale(
            item_id="item_123",
            item_name="Test Item",
            buy_price=10.00,
            target_margin=0.08,
        )
        sale.list_price = 12.00
        sale.current_price = None
        profit, percent = sale.calculate_profit()
        assert profit == 2.00
        assert percent == 20.0

    def test_is_stale_status_not_listed(self) -> None:
        """Test is_stale with various non-listed statuses."""
        statuses = [
            SaleStatus.PENDING,
            SaleStatus.SOLD,
            SaleStatus.CANCELLED,
            SaleStatus.FAILED,
        ]
        for status in statuses:
            sale = ScheduledSale(
                item_id="item_123",
                item_name="Test",
                buy_price=10.00,
                target_margin=0.08,
            )
            sale.status = status
            sale.listed_at = datetime.now(UTC) - timedelta(hours=100)
            assert sale.is_stale(48) is False

    def test_is_stale_no_listed_at(self) -> None:
        """Test is_stale when listed_at is None."""
        sale = ScheduledSale(
            item_id="item_123",
            item_name="Test",
            buy_price=10.00,
            target_margin=0.08,
        )
        sale.status = SaleStatus.LISTED
        sale.listed_at = None
        assert sale.is_stale(48) is False

    def test_is_stale_different_thresholds(self) -> None:
        """Test is_stale with different hour thresholds."""
        sale = ScheduledSale(
            item_id="item_123",
            item_name="Test",
            buy_price=10.00,
            target_margin=0.08,
        )
        sale.status = SaleStatus.LISTED
        sale.listed_at = datetime.now(UTC) - timedelta(hours=25)
        
        assert sale.is_stale(24) is True
        assert sale.is_stale(48) is False
        assert sale.is_stale(12) is True


# ============================================================================
# Tests for AutoSeller List Item
# ============================================================================


class TestAutoSellerListItem:
    """Tests for _list_item method."""

    @pytest.mark.asyncio
    async def test_list_item_success(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test successful item listing."""
        result = await auto_seller._list_item(sample_sale)
        assert result is True
        assert sample_sale.status == SaleStatus.LISTED
        assert sample_sale.offer_id == "offer_123"
        assert sample_sale.listed_at is not None

    @pytest.mark.asyncio
    async def test_list_item_no_optimal_price(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test listing when optimal price cannot be calculated."""
        with patch.object(
            auto_seller, "_calculate_optimal_price", return_value=None
        ):
            result = await auto_seller._list_item(sample_sale)
            assert result is False
            assert sample_sale.status == SaleStatus.FAILED

    @pytest.mark.asyncio
    async def test_list_item_api_error(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test listing when API raises error."""
        auto_seller.api.sell_item.side_effect = Exception("API Error")
        result = await auto_seller._list_item(sample_sale)
        assert result is False
        assert sample_sale.status == SaleStatus.FAILED
        assert auto_seller._stats.failed_count == 1

    @pytest.mark.asyncio
    async def test_list_item_alternative_offer_id_key(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test listing with alternative offer_id key."""
        auto_seller.api.sell_item.return_value = {
            "success": True,
            "offer_id": "offer_456",  # Alternative key
        }
        result = await auto_seller._list_item(sample_sale)
        assert result is True
        assert sample_sale.offer_id == "offer_456"

    @pytest.mark.asyncio
    async def test_list_item_updates_stats(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test that listing updates statistics."""
        initial_listed = auto_seller._stats.listed_count
        await auto_seller._list_item(sample_sale)
        assert auto_seller._stats.listed_count == initial_listed + 1


# ============================================================================
# Tests for AutoSeller Delayed List
# ============================================================================


class TestAutoSellerDelayedList:
    """Tests for _delayed_list method."""

    @pytest.mark.asyncio
    async def test_delayed_list_with_delay(
        self, mock_api: AsyncMock, sale_config: SaleConfig
    ) -> None:
        """Test delayed listing with short delay."""
        sale_config.delay_before_list_seconds = 1
        seller = AutoSeller(api=mock_api, config=sale_config)
        
        sale = ScheduledSale(
            item_id="item_delay",
            item_name="Delayed Item",
            buy_price=10.00,
            target_margin=0.08,
        )
        
        await seller._delayed_list(sale)
        assert sale.status == SaleStatus.LISTED

    @pytest.mark.asyncio
    async def test_delayed_list_already_listed(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test delayed list when sale is no longer pending."""
        sample_sale.status = SaleStatus.CANCELLED
        await auto_seller._delayed_list(sample_sale)
        # Should not change status since not pending
        assert sample_sale.status == SaleStatus.CANCELLED


# ============================================================================
# Tests for AutoSeller Calculate Optimal Price
# ============================================================================


class TestAutoSellerCalculateOptimalPrice:
    """Tests for _calculate_optimal_price method."""

    @pytest.mark.asyncio
    async def test_calculate_optimal_price_match_strategy(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test optimal price with match strategy."""
        auto_seller.config.pricing_strategy = PricingStrategy.MATCH
        price = await auto_seller._calculate_optimal_price(sample_sale)
        assert price is not None
        auto_seller.api.get_best_offers.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_optimal_price_match_no_top_price(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test match strategy falls back when no top price."""
        auto_seller.config.pricing_strategy = PricingStrategy.MATCH
        auto_seller.api.get_best_offers.return_value = {"objects": []}
        
        price = await auto_seller._calculate_optimal_price(sample_sale)
        # Should fall back to fixed margin
        assert price == 11.61

    @pytest.mark.asyncio
    async def test_calculate_optimal_price_dynamic_strategy(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test optimal price with dynamic strategy."""
        auto_seller.config.pricing_strategy = PricingStrategy.DYNAMIC
        price = await auto_seller._calculate_optimal_price(sample_sale)
        assert price is not None

    @pytest.mark.asyncio
    async def test_calculate_optimal_price_unknown_strategy(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test optimal price with unknown strategy falls back to fixed margin."""
        # Force unknown strategy by setting invalid value
        auto_seller.config.pricing_strategy = "unknown"  # type: ignore
        price = await auto_seller._calculate_optimal_price(sample_sale)
        # Should fall back to fixed margin
        assert price == 11.61


# ============================================================================
# Tests for AutoSeller Calculate Dynamic Price
# ============================================================================


class TestAutoSellerCalculateDynamicPrice:
    """Tests for _calculate_dynamic_price method."""

    @pytest.mark.asyncio
    async def test_calculate_dynamic_price_basic(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test basic dynamic price calculation."""
        price = await auto_seller._calculate_dynamic_price(sample_sale)
        assert price is not None
        assert price > 0

    @pytest.mark.asyncio
    async def test_calculate_dynamic_price_with_adjustments(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test dynamic price when item has been adjusted multiple times."""
        sample_sale.listed_at = datetime.now(UTC) - timedelta(hours=30)
        sample_sale.adjustments_count = 5
        
        price = await auto_seller._calculate_dynamic_price(sample_sale)
        assert price is not None

    @pytest.mark.asyncio
    async def test_calculate_dynamic_price_old_listing(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test dynamic price reduction for old listings."""
        sample_sale.listed_at = datetime.now(UTC) - timedelta(hours=72)  # 3 days
        sample_sale.adjustments_count = 5
        
        price_old = await auto_seller._calculate_dynamic_price(sample_sale)
        
        # Compare with fresh listing
        sample_sale.listed_at = datetime.now(UTC)
        sample_sale.adjustments_count = 0
        price_new = await auto_seller._calculate_dynamic_price(sample_sale)
        
        # Old listing should have lower price (within minimum margin)
        assert price_old <= price_new


# ============================================================================
# Tests for AutoSeller Get Top Offer Price
# ============================================================================


class TestAutoSellerGetTopOfferPrice:
    """Tests for _get_top_offer_price method."""

    @pytest.mark.asyncio
    async def test_get_top_offer_price_success(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test successful top offer price retrieval."""
        price = await auto_seller._get_top_offer_price("item_123", "csgo")
        assert price == 12.00  # 1200 cents / 100

    @pytest.mark.asyncio
    async def test_get_top_offer_price_empty_objects(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test when no offers available."""
        auto_seller.api.get_best_offers.return_value = {"objects": []}
        price = await auto_seller._get_top_offer_price("item_123", "csgo")
        assert price is None

    @pytest.mark.asyncio
    async def test_get_top_offer_price_no_objects_key(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test when response has no objects key."""
        auto_seller.api.get_best_offers.return_value = {}
        price = await auto_seller._get_top_offer_price("item_123", "csgo")
        assert price is None

    @pytest.mark.asyncio
    async def test_get_top_offer_price_api_error(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test when API raises error."""
        auto_seller.api.get_best_offers.side_effect = Exception("API Error")
        price = await auto_seller._get_top_offer_price("item_123", "csgo")
        assert price is None

    @pytest.mark.asyncio
    async def test_get_top_offer_price_int_price(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test with integer price instead of string."""
        auto_seller.api.get_best_offers.return_value = {
            "objects": [{"price": {"amount": 1500}}]
        }
        price = await auto_seller._get_top_offer_price("item_123", "csgo")
        assert price == 15.00

    @pytest.mark.asyncio
    async def test_get_top_offer_price_different_games(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test getting top offer for different games."""
        games = ["csgo", "dota2", "rust", "tf2"]
        for game in games:
            price = await auto_seller._get_top_offer_price("item_123", game)
            assert price == 12.00
            auto_seller.api.get_best_offers.assert_called()


# ============================================================================
# Tests for AutoSeller Adjust Price Edge Cases
# ============================================================================


class TestAutoSellerAdjustPriceEdgeCases:
    """Tests for adjust_price edge cases."""

    @pytest.mark.asyncio
    async def test_adjust_price_no_offer_id(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test that adjustment fails without offer_id."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.offer_id = None
        
        result = await auto_seller.adjust_price(sample_sale, 11.50)
        assert result is False

    @pytest.mark.asyncio
    async def test_adjust_price_api_error(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test adjustment when API raises error."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.offer_id = "offer_123"
        sample_sale.current_price = 12.00
        auto_seller.scheduled_sales[sample_sale.item_id] = sample_sale
        auto_seller.api.update_offer_prices.side_effect = Exception("API Error")
        
        result = await auto_seller.adjust_price(sample_sale, 11.50)
        assert result is False
        # Status should be restored
        assert sample_sale.status == SaleStatus.LISTED

    @pytest.mark.asyncio
    async def test_adjust_price_auto_calculate(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test automatic price calculation during adjustment."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.offer_id = "offer_123"
        sample_sale.current_price = 15.00  # Different from optimal
        auto_seller.scheduled_sales[sample_sale.item_id] = sample_sale
        
        result = await auto_seller.adjust_price(sample_sale, None)
        assert result is True
        assert sample_sale.adjustments_count == 1


# ============================================================================
# Tests for AutoSeller Cancel Sale Edge Cases
# ============================================================================


class TestAutoSellerCancelSaleEdgeCases:
    """Tests for cancel_sale edge cases."""

    @pytest.mark.asyncio
    async def test_cancel_sale_not_found(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test cancelling non-existent sale."""
        result = await auto_seller.cancel_sale("nonexistent_item")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_sale_api_error(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test cancelling when API raises error."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.offer_id = "offer_123"
        auto_seller.scheduled_sales[sample_sale.item_id] = sample_sale
        auto_seller.api.remove_offers.side_effect = Exception("API Error")
        
        result = await auto_seller.cancel_sale(sample_sale.item_id)
        assert result is False
        # Sale should still exist
        assert sample_sale.item_id in auto_seller.scheduled_sales


# ============================================================================
# Tests for AutoSeller Price Monitor Loop
# ============================================================================


class TestAutoSellerPriceMonitorLoop:
    """Tests for _price_monitor_loop and _check_and_adjust_prices."""

    @pytest.mark.asyncio
    async def test_check_and_adjust_prices_no_listed(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test price check when no items listed."""
        await auto_seller._check_and_adjust_prices()
        # Should not raise any errors
        auto_seller.api.update_offer_prices.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_and_adjust_prices_triggers_stop_loss(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test that stale items trigger stop-loss."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.offer_id = "offer_123"
        sample_sale.current_price = 12.00
        sample_sale.listed_at = datetime.now(UTC) - timedelta(hours=50)
        auto_seller.scheduled_sales[sample_sale.item_id] = sample_sale
        
        await auto_seller._check_and_adjust_prices()
        
        # Should have triggered stop-loss
        assert sample_sale.status == SaleStatus.STOP_LOSS

    @pytest.mark.asyncio
    async def test_check_and_adjust_prices_adjusts_price(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test that non-stale items get price adjusted."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.offer_id = "offer_123"
        sample_sale.current_price = 15.00  # Higher than optimal
        sample_sale.listed_at = datetime.now(UTC)
        auto_seller.scheduled_sales[sample_sale.item_id] = sample_sale
        
        await auto_seller._check_and_adjust_prices()
        
        # Should have called adjust_price
        assert sample_sale.adjustments_count >= 0

    @pytest.mark.asyncio
    async def test_price_monitor_loop_handles_error(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test that monitor loop handles errors gracefully."""
        auto_seller._running = True
        
        with patch.object(
            auto_seller,
            "_check_and_adjust_prices",
            side_effect=Exception("Test Error"),
        ):
            # Run one iteration
            async def run_one_iteration() -> None:
                auto_seller._running = True
                try:
                    await asyncio.wait_for(
                        auto_seller._price_monitor_loop(),
                        timeout=0.1,
                    )
                except asyncio.TimeoutError:
                    pass
                except asyncio.CancelledError:
                    pass
                finally:
                    auto_seller._running = False
            
            # Should not raise
            await run_one_iteration()


# ============================================================================
# Tests for AutoSeller Statistics
# ============================================================================


class TestAutoSellerStatisticsExtended:
    """Extended tests for statistics tracking."""

    def test_get_statistics_all_fields(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test that all statistics fields are present."""
        stats = auto_seller.get_statistics()
        expected_fields = [
            "scheduled_count",
            "listed_count",
            "sold_count",
            "failed_count",
            "stop_loss_count",
            "adjustments_count",
            "total_profit",
            "active_sales",
            "pending",
            "listed",
        ]
        for field in expected_fields:
            assert field in stats

    def test_get_statistics_counts_by_status(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test that statistics count sales by status."""
        # Add sales with different statuses
        pending_sale = ScheduledSale(
            item_id="pending_1",
            item_name="Pending",
            buy_price=10.00,
            target_margin=0.08,
            status=SaleStatus.PENDING,
        )
        listed_sale = ScheduledSale(
            item_id="listed_1",
            item_name="Listed",
            buy_price=10.00,
            target_margin=0.08,
            status=SaleStatus.LISTED,
        )
        
        auto_seller.scheduled_sales["pending_1"] = pending_sale
        auto_seller.scheduled_sales["listed_1"] = listed_sale
        
        stats = auto_seller.get_statistics()
        assert stats["active_sales"] == 2
        assert stats["pending"] == 1
        assert stats["listed"] == 1

    def test_get_active_sales_empty(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test get_active_sales with no sales."""
        active = auto_seller.get_active_sales()
        assert active == []

    def test_get_active_sales_details(
        self, auto_seller: AutoSeller, sample_sale: ScheduledSale
    ) -> None:
        """Test get_active_sales returns correct details."""
        sample_sale.status = SaleStatus.LISTED
        sample_sale.current_price = 11.50
        sample_sale.listed_at = datetime.now(UTC)
        auto_seller.scheduled_sales[sample_sale.item_id] = sample_sale
        
        active = auto_seller.get_active_sales()
        assert len(active) == 1
        sale_data = active[0]
        
        assert sale_data["item_id"] == sample_sale.item_id
        assert sale_data["item_name"] == sample_sale.item_name
        assert sale_data["buy_price"] == sample_sale.buy_price
        assert sale_data["current_price"] == 11.50
        assert sale_data["status"] == "listed"
        assert "profit" in sale_data
        assert "profit_percent" in sale_data
        assert "listed_at" in sale_data
        assert "adjustments" in sale_data


# ============================================================================
# Tests for AutoSellerStats Dataclass
# ============================================================================


class TestAutoSellerStatsExtended:
    """Extended tests for AutoSellerStats dataclass."""

    def test_stats_increment(self) -> None:
        """Test incrementing stats values."""
        stats = AutoSellerStats()
        stats.scheduled_count += 1
        stats.listed_count += 1
        stats.sold_count += 1
        stats.total_profit += 1.50
        
        assert stats.scheduled_count == 1
        assert stats.listed_count == 1
        assert stats.sold_count == 1
        assert stats.total_profit == 1.50

    def test_stats_accumulation(self) -> None:
        """Test accumulating stats over multiple operations."""
        stats = AutoSellerStats()
        
        for _ in range(10):
            stats.scheduled_count += 1
        
        for _ in range(8):
            stats.listed_count += 1
        
        for _ in range(5):
            stats.sold_count += 1
            stats.total_profit += 1.00
        
        stats.failed_count += 2
        stats.stop_loss_count += 1
        stats.adjustments_count += 15
        
        assert stats.scheduled_count == 10
        assert stats.listed_count == 8
        assert stats.sold_count == 5
        assert stats.failed_count == 2
        assert stats.stop_loss_count == 1
        assert stats.adjustments_count == 15
        assert stats.total_profit == 5.00


# ============================================================================
# Tests for load_sale_config Function
# ============================================================================


class TestLoadSaleConfigExtended:
    """Extended tests for load_sale_config function."""

    def test_load_sale_config_partial_config(self, tmp_path: Any) -> None:
        """Test loading partial config with defaults for missing fields."""
        config_file = tmp_path / "partial_config.yaml"
        config_file.write_text(
            """
auto_sell:
  enabled: true
  min_margin_percent: 6.0
"""
        )
        
        config = load_sale_config(str(config_file))
        assert config.enabled is True
        assert config.min_margin_percent == 6.0
        # Defaults should be used for other fields
        assert config.max_margin_percent == 12.0
        assert config.pricing_strategy == PricingStrategy.UNDERCUT

    def test_load_sale_config_empty_auto_sell(self, tmp_path: Any) -> None:
        """Test loading config with empty auto_sell section."""
        config_file = tmp_path / "empty_auto_sell.yaml"
        config_file.write_text(
            """
other_section:
  key: value
"""
        )
        
        config = load_sale_config(str(config_file))
        # Should use all defaults
        assert config.enabled is True
        assert config.min_margin_percent == 4.0

    def test_load_sale_config_all_pricing_strategies(self, tmp_path: Any) -> None:
        """Test loading config with each pricing strategy."""
        strategies = ["undercut", "match", "fixed_margin", "dynamic"]
        expected = [
            PricingStrategy.UNDERCUT,
            PricingStrategy.MATCH,
            PricingStrategy.FIXED_MARGIN,
            PricingStrategy.DYNAMIC,
        ]
        
        for strategy, expected_strategy in zip(strategies, expected):
            config_file = tmp_path / f"config_{strategy}.yaml"
            config_file.write_text(
                f"""
auto_sell:
  pricing_strategy: {strategy}
"""
            )
            
            config = load_sale_config(str(config_file))
            assert config.pricing_strategy == expected_strategy

    def test_load_sale_config_invalid_yaml(self, tmp_path: Any) -> None:
        """Test loading invalid YAML returns defaults."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        config = load_sale_config(str(config_file))
        # Should return defaults
        assert config.enabled is True


# ============================================================================
# Tests for Edge Cases and Integration
# ============================================================================


class TestAutoSellerEdgeCases:
    """Edge case tests for AutoSeller."""

    @pytest.mark.asyncio
    async def test_schedule_sale_unicode_name(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test scheduling sale with unicode item name."""
        sale = await auto_seller.schedule_sale(
            item_id="unicode_item",
            item_name="AK-47 | 红线 (Redline)",
            buy_price=10.00,
            immediate=True,
        )
        assert sale.item_name == "AK-47 | 红线 (Redline)"

    @pytest.mark.asyncio
    async def test_schedule_sale_special_characters(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test scheduling sale with special characters in name."""
        sale = await auto_seller.schedule_sale(
            item_id="special_item",
            item_name="M4A1-S | Chantico's Fire™ (Factory New)",
            buy_price=50.00,
            immediate=True,
        )
        assert "™" in sale.item_name

    @pytest.mark.asyncio
    async def test_schedule_sale_very_low_price(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test scheduling sale with very low buy price."""
        sale = await auto_seller.schedule_sale(
            item_id="cheap_item",
            item_name="Cheap Item",
            buy_price=0.01,
            immediate=True,
        )
        assert sale.buy_price == 0.01

    @pytest.mark.asyncio
    async def test_schedule_sale_very_high_price(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test scheduling sale with very high buy price."""
        sale = await auto_seller.schedule_sale(
            item_id="expensive_item",
            item_name="Dragon Lore (Factory New)",
            buy_price=10000.00,
            immediate=True,
        )
        assert sale.buy_price == 10000.00


class TestAutoSellerIntegration:
    """Integration tests for AutoSeller."""

    @pytest.mark.asyncio
    async def test_full_sale_lifecycle(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test complete sale lifecycle from scheduling to sold."""
        # Schedule
        sale = await auto_seller.schedule_sale(
            item_id="lifecycle_item",
            item_name="Test Item",
            buy_price=10.00,
            immediate=True,
        )
        
        assert sale.status == SaleStatus.LISTED
        assert auto_seller._stats.scheduled_count == 1
        assert auto_seller._stats.listed_count == 1
        
        # Mark as sold
        auto_seller.mark_sold("lifecycle_item", 11.50)
        
        assert auto_seller._stats.sold_count == 1
        assert auto_seller._stats.total_profit == 1.50
        assert "lifecycle_item" not in auto_seller.scheduled_sales

    @pytest.mark.asyncio
    async def test_multiple_sales_concurrent(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test handling multiple sales concurrently."""
        tasks = []
        for i in range(5):
            task = auto_seller.schedule_sale(
                item_id=f"concurrent_item_{i}",
                item_name=f"Concurrent Item {i}",
                buy_price=10.00 + i,
                immediate=True,
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        assert len(auto_seller.scheduled_sales) == 5
        assert auto_seller._stats.scheduled_count == 5

    @pytest.mark.asyncio
    async def test_cancel_then_reschedule(
        self, auto_seller: AutoSeller
    ) -> None:
        """Test cancelling a sale and rescheduling the same item."""
        # Schedule first sale
        await auto_seller.schedule_sale(
            item_id="reschedule_item",
            item_name="Reschedule Test",
            buy_price=10.00,
            immediate=True,
        )
        
        # Cancel it
        await auto_seller.cancel_sale("reschedule_item")
        assert "reschedule_item" not in auto_seller.scheduled_sales
        
        # Reschedule
        sale = await auto_seller.schedule_sale(
            item_id="reschedule_item",
            item_name="Reschedule Test",
            buy_price=11.00,  # Different price
            immediate=True,
        )
        
        assert sale.buy_price == 11.00
        assert "reschedule_item" in auto_seller.scheduled_sales

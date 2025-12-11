"""Auto-sell module for DMarket Bot.

This module provides automatic selling functionality after item purchase:
- Schedule items for sale with target margin
- Competitive pricing with undercut strategy
- Periodic price adjustment to stay at top
- Stop-loss mechanism for stale items

Usage:
    from src.dmarket.auto_seller import AutoSeller

    seller = AutoSeller(api_client)
    await seller.schedule_sale(item_id, buy_price=10.00, target_margin=0.08)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from src.dmarket.dmarket_api import DMarketAPI

logger = logging.getLogger(__name__)

# Default config path
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "auto_sell.yaml"


class SaleStatus(str, Enum):
    """Status of a scheduled sale."""

    PENDING = "pending"  # Waiting to be listed
    LISTED = "listed"  # Listed on market
    SOLD = "sold"  # Successfully sold
    CANCELLED = "cancelled"  # Cancelled by user
    STOP_LOSS = "stop_loss"  # Sold at loss due to timeout
    FAILED = "failed"  # Failed to list


@dataclass
class ScheduledSale:
    """Represents a scheduled sale item."""

    item_id: str
    item_name: str
    buy_price: float  # USD
    target_margin: float  # Percentage (0.08 = 8%)
    sell_price: float  # Calculated sell price in USD
    offer_id: str | None = None
    status: SaleStatus = SaleStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    listed_at: datetime | None = None
    sold_at: datetime | None = None
    actual_sell_price: float | None = None
    game: str = "csgo"
    price_adjustments: int = 0
    last_adjustment_at: datetime | None = None

    @property
    def age_hours(self) -> float:
        """Get age of the scheduled sale in hours."""
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.total_seconds() / 3600

    @property
    def expected_profit(self) -> float:
        """Calculate expected profit in USD."""
        return self.sell_price - self.buy_price

    @property
    def expected_profit_percent(self) -> float:
        """Calculate expected profit percentage."""
        if self.buy_price <= 0:
            return 0.0
        return (self.expected_profit / self.buy_price) * 100

    @property
    def actual_profit(self) -> float | None:
        """Calculate actual profit if sold."""
        if self.actual_sell_price is None:
            return None
        return self.actual_sell_price - self.buy_price

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "buy_price": self.buy_price,
            "target_margin": self.target_margin,
            "sell_price": self.sell_price,
            "offer_id": self.offer_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "listed_at": self.listed_at.isoformat() if self.listed_at else None,
            "sold_at": self.sold_at.isoformat() if self.sold_at else None,
            "actual_sell_price": self.actual_sell_price,
            "game": self.game,
            "price_adjustments": self.price_adjustments,
        }


class AutoSellerConfig:
    """Configuration for AutoSeller."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Initialize AutoSeller configuration.

        Args:
            config_path: Path to config file (optional)

        """
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded auto-sell config from {self.config_path}")
            else:
                logger.info("Auto-sell config not found, using defaults")
                self.config = self._get_defaults()
        except Exception as e:
            logger.error(f"Failed to load auto-sell config: {e}")
            self.config = self._get_defaults()

    def _get_defaults(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "enabled": True,
            "min_margin_percent": 4.0,  # Minimum 4% margin
            "max_margin_percent": 12.0,  # Maximum 12% margin
            "default_margin_percent": 8.0,  # Default 8% margin
            "undercut_cents": 1,  # Undercut by $0.01
            "min_undercut_price_ratio": 1.04,  # Never go below buy_price * 1.04
            "price_adjustment_interval_minutes": 30,  # Adjust every 30 min
            "max_price_adjustments": 10,  # Max adjustments before stop
            "stop_loss_hours": 48,  # Sell at loss after 48h
            "stop_loss_percent": 5.0,  # Max loss 5%
            "dmarket_fee_percent": 7.0,  # DMarket fee
            "auto_list_delay_seconds": 5,  # Delay before listing
        }

    @property
    def enabled(self) -> bool:
        """Check if auto-sell is enabled."""
        return self.config.get("enabled", True)

    @property
    def min_margin_percent(self) -> float:
        """Get minimum margin percentage."""
        return self.config.get("min_margin_percent", 4.0)

    @property
    def max_margin_percent(self) -> float:
        """Get maximum margin percentage."""
        return self.config.get("max_margin_percent", 12.0)

    @property
    def default_margin_percent(self) -> float:
        """Get default margin percentage."""
        return self.config.get("default_margin_percent", 8.0)

    @property
    def undercut_cents(self) -> int:
        """Get undercut amount in cents."""
        return self.config.get("undercut_cents", 1)

    @property
    def min_undercut_price_ratio(self) -> float:
        """Get minimum price ratio for undercut."""
        return self.config.get("min_undercut_price_ratio", 1.04)

    @property
    def price_adjustment_interval_minutes(self) -> int:
        """Get price adjustment interval in minutes."""
        return self.config.get("price_adjustment_interval_minutes", 30)

    @property
    def stop_loss_hours(self) -> float:
        """Get stop-loss timeout in hours."""
        return self.config.get("stop_loss_hours", 48.0)

    @property
    def stop_loss_percent(self) -> float:
        """Get stop-loss percentage."""
        return self.config.get("stop_loss_percent", 5.0)

    @property
    def dmarket_fee_percent(self) -> float:
        """Get DMarket fee percentage."""
        return self.config.get("dmarket_fee_percent", 7.0)

    @property
    def auto_list_delay_seconds(self) -> int:
        """Get delay before auto-listing in seconds."""
        return self.config.get("auto_list_delay_seconds", 5)

    @property
    def max_price_adjustments(self) -> int:
        """Get maximum number of price adjustments."""
        return self.config.get("max_price_adjustments", 10)


class AutoSeller:
    """Automatic item seller for DMarket.

    Handles the complete sell cycle:
    1. Schedule items for sale after purchase
    2. Calculate optimal sell price with target margin
    3. Monitor and adjust prices to stay competitive
    4. Handle stop-loss for stale items
    """

    def __init__(
        self,
        api_client: DMarketAPI | None = None,
        config: AutoSellerConfig | None = None,
    ) -> None:
        """Initialize AutoSeller.

        Args:
            api_client: DMarket API client
            config: AutoSeller configuration

        """
        self.api_client = api_client
        self.config = config or AutoSellerConfig()

        # Scheduled sales storage
        self._scheduled_sales: dict[str, ScheduledSale] = {}

        # Statistics
        self.total_scheduled = 0
        self.total_sold = 0
        self.total_profit = 0.0
        self.total_stop_loss = 0

        # Background task
        self._price_monitor_task: asyncio.Task[None] | None = None

    @property
    def active_sales(self) -> list[ScheduledSale]:
        """Get list of active (pending or listed) sales."""
        return [
            sale
            for sale in self._scheduled_sales.values()
            if sale.status in (SaleStatus.PENDING, SaleStatus.LISTED)
        ]

    @property
    def pending_sales(self) -> list[ScheduledSale]:
        """Get list of pending sales."""
        return [
            sale
            for sale in self._scheduled_sales.values()
            if sale.status == SaleStatus.PENDING
        ]

    @property
    def listed_sales(self) -> list[ScheduledSale]:
        """Get list of listed sales."""
        return [
            sale
            for sale in self._scheduled_sales.values()
            if sale.status == SaleStatus.LISTED
        ]

    def calculate_sell_price(
        self,
        buy_price: float,
        target_margin: float | None = None,
    ) -> float:
        """Calculate sell price based on buy price and target margin.

        Args:
            buy_price: Purchase price in USD
            target_margin: Target margin percentage (e.g., 0.08 for 8%)

        Returns:
            Calculated sell price in USD

        """
        if target_margin is None:
            target_margin = self.config.default_margin_percent / 100

        # Ensure margin is within bounds
        min_margin = self.config.min_margin_percent / 100
        max_margin = self.config.max_margin_percent / 100
        target_margin = max(min_margin, min(max_margin, target_margin))

        # Calculate gross sell price (before fees)
        # net_profit = sell_price * (1 - fee) - buy_price
        # We want: net_profit = buy_price * target_margin
        # sell_price * (1 - fee) = buy_price * (1 + target_margin)
        # sell_price = buy_price * (1 + target_margin) / (1 - fee)
        fee_rate = self.config.dmarket_fee_percent / 100
        sell_price = buy_price * (1 + target_margin) / (1 - fee_rate)

        # Round to 2 decimal places
        return round(sell_price, 2)

    def calculate_undercut_price(
        self,
        current_top_price: float,
        buy_price: float,
    ) -> float:
        """Calculate undercut price for competitive listing.

        Args:
            current_top_price: Current top offer price in USD
            buy_price: Original purchase price in USD

        Returns:
            Calculated undercut price in USD

        """
        # Undercut by configured amount
        undercut_price = current_top_price - (self.config.undercut_cents / 100)

        # Ensure we don't go below minimum acceptable price
        min_price = buy_price * self.config.min_undercut_price_ratio
        undercut_price = max(undercut_price, min_price)

        return round(undercut_price, 2)

    def calculate_stop_loss_price(self, buy_price: float) -> float:
        """Calculate stop-loss price for stale items.

        Args:
            buy_price: Original purchase price in USD

        Returns:
            Stop-loss price in USD

        """
        stop_loss_rate = 1 - (self.config.stop_loss_percent / 100)
        return round(buy_price * stop_loss_rate, 2)

    async def schedule_sale(
        self,
        item_id: str,
        buy_price: float,
        item_name: str = "",
        target_margin: float | None = None,
        game: str = "csgo",
        auto_list: bool = True,
    ) -> ScheduledSale:
        """Schedule an item for automatic sale.

        Args:
            item_id: DMarket item ID
            buy_price: Purchase price in USD
            item_name: Item name for display
            target_margin: Target profit margin (0.08 = 8%)
            game: Game code
            auto_list: Automatically list on market

        Returns:
            Scheduled sale object

        """
        if target_margin is None:
            target_margin = self.config.default_margin_percent / 100

        # Calculate sell price
        sell_price = self.calculate_sell_price(buy_price, target_margin)

        # Create scheduled sale
        sale = ScheduledSale(
            item_id=item_id,
            item_name=item_name or item_id,
            buy_price=buy_price,
            target_margin=target_margin,
            sell_price=sell_price,
            game=game,
        )

        # Store in memory
        self._scheduled_sales[item_id] = sale
        self.total_scheduled += 1

        logger.info(
            f"Scheduled sale: {sale.item_name} | "
            f"Buy: ${buy_price:.2f} | Target sell: ${sell_price:.2f} | "
            f"Expected profit: ${sale.expected_profit:.2f} ({sale.expected_profit_percent:.1f}%)"
        )

        # Auto-list if enabled
        if auto_list and self.config.enabled:
            # Small delay before listing
            await asyncio.sleep(self.config.auto_list_delay_seconds)
            await self.list_item(item_id)

        return sale

    async def list_item(self, item_id: str) -> bool:
        """List a scheduled item on the market.

        Args:
            item_id: Item ID to list

        Returns:
            True if listing was successful

        """
        sale = self._scheduled_sales.get(item_id)
        if not sale:
            logger.warning(f"Item {item_id} not found in scheduled sales")
            return False

        if sale.status != SaleStatus.PENDING:
            logger.warning(f"Item {item_id} is not pending (status: {sale.status})")
            return False

        if not self.api_client:
            logger.error("API client not available")
            sale.status = SaleStatus.FAILED
            return False

        try:
            # Check for competitive pricing first
            top_price = await self.get_top_offer_price(sale.item_name, sale.game)
            if top_price and top_price < sale.sell_price:
                # Adjust to undercut
                new_price = self.calculate_undercut_price(top_price, sale.buy_price)
                if new_price < sale.sell_price:
                    logger.info(
                        f"Adjusting price for competition: ${sale.sell_price:.2f} → ${new_price:.2f}"
                    )
                    sale.sell_price = new_price

            # Call API to create offer
            result = await self.api_client.sell_item(
                item_id=sale.item_id,
                price=sale.sell_price,
                game=sale.game,
                item_name=sale.item_name,
                buy_price=sale.buy_price,
                source="auto_sell",
            )

            if result.get("success") or result.get("Result"):
                sale.status = SaleStatus.LISTED
                sale.listed_at = datetime.now(timezone.utc)
                sale.offer_id = result.get("offerId") or result.get("Result", {}).get("offerId")

                logger.info(
                    f"✅ Listed {sale.item_name} for ${sale.sell_price:.2f}"
                )
                return True
            else:
                sale.status = SaleStatus.FAILED
                logger.error(f"Failed to list {sale.item_name}: {result}")
                return False

        except Exception as e:
            sale.status = SaleStatus.FAILED
            logger.error(f"Error listing {sale.item_name}: {e}")
            return False

    async def get_top_offer_price(
        self,
        item_name: str,
        game: str = "csgo",
    ) -> float | None:
        """Get the current top (lowest) offer price for an item.

        Args:
            item_name: Item name to search
            game: Game code

        Returns:
            Top offer price in USD or None if not found

        """
        if not self.api_client:
            return None

        try:
            # Get market items
            result = await self.api_client.get_market_items(
                game=game,
                title=item_name,
                limit=1,
                order_by="price",
                order_dir="asc",
            )

            items = result.get("objects", [])
            if items:
                price_data = items[0].get("price", {})
                if isinstance(price_data, dict):
                    price_value = price_data.get("USD", price_data.get("amount", 0))
                    if price_value is not None:
                        try:
                            return float(price_value) / 100
                        except (TypeError, ValueError):
                            return None
                elif price_data is not None:
                    try:
                        return float(price_data) / 100
                    except (TypeError, ValueError):
                        return None

        except Exception as e:
            logger.warning(f"Error getting top offer price for {item_name}: {e}")

        return None

    async def adjust_offer_price(self, item_id: str) -> bool:
        """Adjust offer price to stay competitive.

        Args:
            item_id: Item ID to adjust

        Returns:
            True if price was adjusted

        """
        sale = self._scheduled_sales.get(item_id)
        if not sale or sale.status != SaleStatus.LISTED:
            return False

        if not self.api_client or not sale.offer_id:
            return False

        try:
            # Get current top price
            top_price = await self.get_top_offer_price(sale.item_name, sale.game)
            if not top_price or top_price >= sale.sell_price:
                # Already competitive
                return False

            # Calculate new undercut price
            new_price = self.calculate_undercut_price(top_price, sale.buy_price)

            if new_price >= sale.sell_price:
                # No improvement possible
                return False

            # Update offer
            offers = [{
                "OfferID": sale.offer_id,
                "Price": {
                    "Amount": int(new_price * 100),
                    "Currency": "USD",
                },
            }]
            result = await self.api_client.update_offer_prices(offers)

            if result.get("success") or result.get("Result"):
                old_price = sale.sell_price
                sale.sell_price = new_price
                sale.price_adjustments += 1
                sale.last_adjustment_at = datetime.now(timezone.utc)

                logger.info(
                    f"📉 Adjusted price for {sale.item_name}: "
                    f"${old_price:.2f} → ${new_price:.2f} (adjustment #{sale.price_adjustments})"
                )
                return True

        except Exception as e:
            logger.error(f"Error adjusting price for {sale.item_name}: {e}")

        return False

    async def check_stop_loss(self, item_id: str) -> bool:
        """Check if item should be sold at stop-loss.

        Args:
            item_id: Item ID to check

        Returns:
            True if stop-loss was triggered

        """
        sale = self._scheduled_sales.get(item_id)
        if not sale or sale.status != SaleStatus.LISTED:
            return False

        if sale.age_hours < self.config.stop_loss_hours:
            return False

        # Trigger stop-loss
        stop_loss_price = self.calculate_stop_loss_price(sale.buy_price)

        logger.warning(
            f"⚠️ Stop-loss triggered for {sale.item_name} "
            f"(age: {sale.age_hours:.1f}h): ${sale.sell_price:.2f} → ${stop_loss_price:.2f}"
        )

        if self.api_client and sale.offer_id:
            try:
                offers = [{
                    "OfferID": sale.offer_id,
                    "Price": {
                        "Amount": int(stop_loss_price * 100),
                        "Currency": "USD",
                    },
                }]
                result = await self.api_client.update_offer_prices(offers)

                if result.get("success") or result.get("Result"):
                    sale.sell_price = stop_loss_price
                    sale.status = SaleStatus.STOP_LOSS
                    self.total_stop_loss += 1
                    return True

            except Exception as e:
                logger.error(f"Error updating stop-loss price: {e}")

        return False

    def mark_sold(
        self,
        item_id: str,
        actual_price: float | None = None,
    ) -> bool:
        """Mark an item as sold.

        Args:
            item_id: Item ID that was sold
            actual_price: Actual sell price (if different from listed)

        Returns:
            True if item was marked as sold

        """
        sale = self._scheduled_sales.get(item_id)
        if not sale:
            return False

        sale.status = SaleStatus.SOLD
        sale.sold_at = datetime.now(timezone.utc)
        sale.actual_sell_price = actual_price or sale.sell_price

        # Update statistics
        self.total_sold += 1
        if sale.actual_profit:
            self.total_profit += sale.actual_profit

        logger.info(
            f"✅ SOLD {sale.item_name} for ${sale.actual_sell_price:.2f} | "
            f"Profit: ${sale.actual_profit or 0:.2f}"
        )

        return True

    def cancel_sale(self, item_id: str) -> bool:
        """Cancel a scheduled sale.

        Args:
            item_id: Item ID to cancel

        Returns:
            True if sale was cancelled

        """
        sale = self._scheduled_sales.get(item_id)
        if not sale:
            return False

        if sale.status == SaleStatus.SOLD:
            return False

        sale.status = SaleStatus.CANCELLED
        logger.info(f"❌ Cancelled sale: {sale.item_name}")
        return True

    def get_statistics(self) -> dict[str, Any]:
        """Get auto-seller statistics.

        Returns:
            Dictionary with statistics

        """
        return {
            "enabled": self.config.enabled,
            "total_scheduled": self.total_scheduled,
            "total_sold": self.total_sold,
            "total_profit": round(self.total_profit, 2),
            "total_stop_loss": self.total_stop_loss,
            "active_sales": len(self.active_sales),
            "pending_sales": len(self.pending_sales),
            "listed_sales": len(self.listed_sales),
            "average_margin": self._calculate_average_margin(),
            "config": {
                "min_margin": self.config.min_margin_percent,
                "max_margin": self.config.max_margin_percent,
                "default_margin": self.config.default_margin_percent,
                "undercut_cents": self.config.undercut_cents,
                "stop_loss_hours": self.config.stop_loss_hours,
            },
        }

    def _calculate_average_margin(self) -> float:
        """Calculate average margin from sold items."""
        sold_items = [s for s in self._scheduled_sales.values() if s.status == SaleStatus.SOLD]
        if not sold_items:
            return 0.0

        total_margin = sum(
            (s.actual_profit / s.buy_price * 100) if s.actual_profit and s.buy_price > 0 else 0
            for s in sold_items
        )
        return round(total_margin / len(sold_items), 2)

    async def start_price_monitor(self) -> None:
        """Start background price monitoring task."""
        if self._price_monitor_task and not self._price_monitor_task.done():
            logger.warning("Price monitor already running")
            return

        self._price_monitor_task = asyncio.create_task(self._price_monitor_loop())
        logger.info("Started price monitor task")

    async def stop_price_monitor(self) -> None:
        """Stop background price monitoring task."""
        if self._price_monitor_task:
            self._price_monitor_task.cancel()
            try:
                await self._price_monitor_task
            except asyncio.CancelledError:
                pass
            self._price_monitor_task = None
            logger.info("Stopped price monitor task")

    async def _price_monitor_loop(self) -> None:
        """Background loop for price monitoring and adjustment."""
        interval = self.config.price_adjustment_interval_minutes * 60

        while True:
            try:
                await asyncio.sleep(interval)

                for sale in self.listed_sales:
                    # Check stop-loss first
                    if await self.check_stop_loss(sale.item_id):
                        continue

                    # Check max adjustments
                    if sale.price_adjustments >= self.config.max_price_adjustments:
                        continue

                    # Try to adjust price
                    await self.adjust_offer_price(sale.item_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in price monitor loop: {e}")


# Global instance
_auto_seller: AutoSeller | None = None


def get_auto_seller(api_client: DMarketAPI | None = None) -> AutoSeller:
    """Get global AutoSeller instance.

    Args:
        api_client: DMarket API client (required on first call)

    Returns:
        AutoSeller instance

    """
    global _auto_seller
    if _auto_seller is None:
        _auto_seller = AutoSeller(api_client)
    elif api_client and _auto_seller.api_client is None:
        _auto_seller.api_client = api_client
    return _auto_seller

"""Auto-buyer module for instant item purchases (sniping).

This module implements:
- Instant buy functionality with Telegram buttons
- Auto-buy based on discount threshold
- Purchase validation and safety checks
- DRY_RUN mode support

Created: January 2, 2026
"""

from datetime import datetime
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


class AutoBuyConfig:
    """Configuration for auto-buy functionality."""

    def __init__(
        self,
        enabled: bool = False,
        min_discount_percent: float = 30.0,
        max_price_usd: float = 100.0,
        check_sales_history: bool = True,
        check_trade_lock: bool = True,
        max_trade_lock_hours: int = 168,  # 7 days
        dry_run: bool = True,
    ):
        """Initialize auto-buy configuration.

        Args:
            enabled: Enable/disable auto-buy
            min_discount_percent: Minimum discount to trigger auto-buy (%)
            max_price_usd: Maximum price for auto-buy (USD)
            check_sales_history: Verify price trend before buying
            check_trade_lock: Check trade lock duration
            max_trade_lock_hours: Maximum acceptable trade lock (hours)
            dry_run: Simulate purchases without real transactions
        """
        self.enabled = enabled
        self.min_discount_percent = min_discount_percent
        self.max_price_usd = max_price_usd
        self.check_sales_history = check_sales_history
        self.check_trade_lock = check_trade_lock
        self.max_trade_lock_hours = max_trade_lock_hours
        self.dry_run = dry_run


class PurchaseResult:
    """Result of a purchase attempt."""

    def __init__(
        self,
        success: bool,
        item_id: str,
        item_title: str,
        price_usd: float,
        message: str,
        order_id: str | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.item_id = item_id
        self.item_title = item_title
        self.price_usd = price_usd
        self.message = message
        self.order_id = order_id
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "item_id": self.item_id,
            "item_title": self.item_title,
            "price_usd": self.price_usd,
            "message": self.message,
            "order_id": self.order_id,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class AutoBuyer:
    """Automatic item buyer with instant purchase capability."""

    def __init__(self, api_client, config: AutoBuyConfig | None = None):
        """Initialize AutoBuyer.

        Args:
            api_client: DMarket API client instance
            config: Auto-buy configuration
        """
        self.api = api_client
        self.config = config or AutoBuyConfig()
        self.purchase_history: list[PurchaseResult] = []

        logger.info(
            "auto_buyer_initialized",
            enabled=self.config.enabled,
            min_discount=self.config.min_discount_percent,
            max_price=self.config.max_price_usd,
            dry_run=self.config.dry_run,
        )

    async def should_auto_buy(self, item: dict) -> tuple[bool, str]:
        """Check if item meets auto-buy criteria.

        Args:
            item: Item data from DMarket API

        Returns:
            Tuple of (should_buy: bool, reason: str)
        """
        # Early return: Auto-buy disabled
        if not self.config.enabled:
            return False, "Auto-buy is disabled"

        # Extract item data
        price_usd = float(item.get("price", {}).get("USD", 0)) / 100
        suggested_price = item.get("suggestedPrice", {}).get("USD")

        # Early return: No suggested price
        if not suggested_price:
            return False, "No suggested price available"

        suggested_price_usd = float(suggested_price) / 100

        # Calculate discount
        if suggested_price_usd <= 0:
            return False, "Invalid suggested price"

        discount = ((suggested_price_usd - price_usd) / suggested_price_usd) * 100

        # Early return: Discount too low
        if discount < self.config.min_discount_percent:
            return False, f"Discount {discount:.1f}% < {self.config.min_discount_percent}%"

        # Early return: Price too high
        if price_usd > self.config.max_price_usd:
            return False, f"Price ${price_usd:.2f} > ${self.config.max_price_usd:.2f}"

        # Check trade lock if enabled
        if self.config.check_trade_lock:
            trade_lock = item.get("extra", {}).get("tradeLockDuration", 0)
            if trade_lock > self.config.max_trade_lock_hours * 3600:
                return (
                    False,
                    f"Trade lock {trade_lock / 3600:.0f}h > {self.config.max_trade_lock_hours}h",
                )

        # Check liquidity if enabled (sales history)
        if self.config.check_sales_history:
            is_liquid = await self._check_liquidity(item)
            if not is_liquid:
                return False, "Low liquidity (< 5 sales/day)"

        # All checks passed
        return True, f"Discount {discount:.1f}% >= {self.config.min_discount_percent}%"

    async def _check_liquidity(self, item: dict) -> bool:
        """Check item liquidity via sales history.

        Args:
            item: Item data

        Returns:
            True if item is liquid (enough sales)
        """
        try:
            # Get item title
            title = item.get("title", "")
            if not title:
                return True  # Skip check if no title

            # Request sales history (last 7 days)
            # Note: This requires sales_history module
            from src.dmarket.sales_history import get_item_sales_history

            history = await get_item_sales_history(
                api_client=self.api, item_title=title, days=7
            )

            if not history:
                logger.warning("no_sales_history", title=title)
                return True  # Assume liquid if no data

            # Calculate daily sales
            daily_sales = len(history) / 7

            # Require at least 5 sales per day
            if daily_sales < 5:
                logger.debug(
                    "low_liquidity_detected",
                    title=title,
                    daily_sales=daily_sales,
                )
                return False

            logger.debug("liquidity_check_passed", title=title, daily_sales=daily_sales)
            return True

        except ImportError:
            # Sales history module not available, skip check
            logger.warning("sales_history_module_unavailable")
            return True
        except Exception as e:
            logger.exception("liquidity_check_failed", error=str(e))
            return True  # Assume liquid on error

    async def buy_item(self, item_id: str, price_usd: float, force: bool = False) -> PurchaseResult:
        """Purchase an item instantly.

        Args:
            item_id: DMarket item ID
            price_usd: Item price in USD
            force: Bypass auto-buy checks (manual purchase)

        Returns:
            PurchaseResult with purchase details
        """
        logger.info(
            "purchase_attempt",
            item_id=item_id,
            price=price_usd,
            force=force,
            dry_run=self.config.dry_run,
        )

        # Check balance before purchase (not in DRY_RUN)
        if not self.config.dry_run:
            has_balance = await self._check_balance(price_usd)
            if not has_balance:
                result = PurchaseResult(
                    success=False,
                    item_id=item_id,
                    item_title="Unknown",
                    price_usd=price_usd,
                    message="❌ Insufficient balance",
                    error="Insufficient funds",
                )
                self.purchase_history.append(result)
                return result

        # DRY_RUN mode: Simulate purchase
        if self.config.dry_run:
            result = PurchaseResult(
                success=True,
                item_id=item_id,
                item_title="DRY_RUN_ITEM",
                price_usd=price_usd,
                message="✅ DRY_RUN: Purchase simulated successfully",
                order_id=f"DRY_RUN_{item_id}",
            )
            self.purchase_history.append(result)

            logger.info(
                "purchase_simulated",
                item_id=item_id,
                price=price_usd,
                order_id=result.order_id,
            )

            return result

        # Real purchase
        try:
            # Call DMarket API to buy item
            response = await self.api.buy_item(item_id, price_usd)

            if response.get("success"):
                result = PurchaseResult(
                    success=True,
                    item_id=item_id,
                    item_title=response.get("title", "Unknown"),
                    price_usd=price_usd,
                    message="✅ Purchase completed successfully",
                    order_id=response.get("orderId"),
                )

                logger.info(
                    "purchase_completed",
                    item_id=item_id,
                    price=price_usd,
                    order_id=result.order_id,
                )
            else:
                result = PurchaseResult(
                    success=False,
                    item_id=item_id,
                    item_title="Unknown",
                    price_usd=price_usd,
                    message="❌ Purchase failed",
                    error=response.get("error", "Unknown error"),
                )

                logger.error(
                    "purchase_failed",
                    item_id=item_id,
                    error=result.error,
                )

            self.purchase_history.append(result)
            return result

        except Exception as e:
            result = PurchaseResult(
                success=False,
                item_id=item_id,
                item_title="Unknown",
                price_usd=price_usd,
                message=f"❌ Exception during purchase: {e!s}",
                error=str(e),
            )

            logger.exception(
                "purchase_exception",
                item_id=item_id,
                error=str(e),
            )

            self.purchase_history.append(result)
            return result

    async def process_opportunity(self, item: dict) -> PurchaseResult | None:
        """Process arbitrage opportunity and auto-buy if criteria met.

        Args:
            item: Item data from scanner

        Returns:
            PurchaseResult if purchased, None if skipped
        """
        should_buy, reason = await self.should_auto_buy(item)

        if not should_buy:
            logger.debug("auto_buy_skipped", item_id=item.get("itemId"), reason=reason)
            return None

        # Extract item details
        item_id = item.get("itemId") or item.get("extra", {}).get("offerId")
        price_usd = float(item.get("price", {}).get("USD", 0)) / 100

        logger.info(
            "auto_buy_triggered",
            item_id=item_id,
            item_title=item.get("title"),
            price=price_usd,
            reason=reason,
        )

        # Execute purchase
        return await self.buy_item(item_id, price_usd, force=False)

    def get_purchase_stats(self) -> dict[str, Any]:
        """Get purchase statistics.

        Returns:
            Dictionary with purchase stats
        """
        if not self.purchase_history:
            return {
                "total_purchases": 0,
                "successful": 0,
                "failed": 0,
                "total_spent_usd": 0.0,
                "success_rate": 0.0,
            }

        successful = [p for p in self.purchase_history if p.success]
        failed = [p for p in self.purchase_history if not p.success]
        total_spent = sum(p.price_usd for p in successful)

        return {
            "total_purchases": len(self.purchase_history),
            "successful": len(successful),
            "failed": len(failed),
            "total_spent_usd": total_spent,
            "success_rate": len(successful) / len(self.purchase_history) * 100,
            "dry_run_mode": self.config.dry_run,
        }

    def clear_history(self):
        """Clear purchase history."""
        self.purchase_history.clear()
        logger.info("purchase_history_cleared")

    async def _check_balance(self, required_usd: float) -> bool:
        """Check if there's enough balance for purchase.

        Args:
            required_usd: Required amount in USD

        Returns:
            True if balance is sufficient
        """
        try:
            balance = await self.api.get_balance()
            available_cents = balance.get("USD", 0)
            available_usd = float(available_cents) / 100

            logger.debug(
                "balance_check",
                available=available_usd,
                required=required_usd,
            )

            if available_usd < required_usd:
                logger.warning(
                    "insufficient_balance",
                    available=available_usd,
                    required=required_usd,
                    deficit=required_usd - available_usd,
                )
                return False

            return True

        except Exception as e:
            logger.exception("balance_check_failed", error=str(e))
            # On error, assume balance is sufficient to not block purchases
            return True

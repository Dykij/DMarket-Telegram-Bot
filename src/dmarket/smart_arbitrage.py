"""Smart Arbitrage Module - Balance-adaptive trading.

This module provides intelligent trading limits based on current balance,
implementing diversification and risk management automatically.

Key Features:
- Dynamic max item price based on balance (percentage-based, not fixed!)
- Adaptive profit requirements by balance tier
- Automatic inventory limits that scale with balance
- Integration with whitelist/blacklist
- Universal money management (works for $10 to $10,000+)

Usage:
    from src.dmarket.smart_arbitrage import SmartArbitrageEngine

    engine = SmartArbitrageEngine(api_client)
    limits = await engine.calculate_adaptive_limits()
    opportunities = await engine.find_smart_opportunities(game="csgo")
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

from src.dmarket.money_manager import (
    MoneyManager,
    MoneyManagerConfig,
    DynamicLimits,
    BalanceTier,
    calculate_universal_limits,
)

if TYPE_CHECKING:
    from src.interfaces import IDMarketAPI

logger = structlog.get_logger(__name__)


@dataclass
class SmartLimits:
    """Adaptive trading limits based on current balance.
    
    Note: This class is kept for backwards compatibility.
    New code should use DynamicLimits from money_manager.
    """

    max_buy_price: float  # Maximum price for single item
    min_roi: float  # Minimum profit percentage
    inventory_limit: int  # Max items in inventory
    max_same_items: int  # Max duplicates of same item
    usable_balance: float  # Balance minus reserve
    reserve: float  # Safety reserve
    diversification_factor: float  # How much of balance per item (e.g., 0.3 = 30%)
    tier: str = "small"  # Balance tier for strategy selection
    min_item_price: float = 0.10  # Minimum item price

    @classmethod
    def from_dynamic_limits(cls, limits: DynamicLimits) -> "SmartLimits":
        """Convert DynamicLimits to SmartLimits for compatibility."""
        return cls(
            max_buy_price=limits.max_item_price,
            min_roi=limits.min_roi,
            inventory_limit=limits.max_inventory_items,
            max_same_items=limits.max_same_items,
            usable_balance=limits.usable_balance,
            reserve=limits.reserve,
            diversification_factor=limits.diversification_factor,
            tier=limits.tier.value,
            min_item_price=limits.min_item_price,
        )


@dataclass
class SmartOpportunity:
    """An arbitrage opportunity with smart scoring."""

    item_id: str
    title: str
    buy_price: float
    sell_price: float
    profit: float
    profit_percent: float
    game: str
    liquidity_score: float = 0.0
    smart_score: float = 0.0  # Combined score for prioritization
    created_at: datetime = field(default_factory=datetime.now)


class SmartArbitrageEngine:
    """Balance-adaptive arbitrage engine.

    Automatically adjusts trading parameters based on:
    - Current DMarket balance (percentage-based scaling)
    - Balance tier (micro/small/medium/large/whale)
    - Inventory size
    - Market conditions

    Works equally well for $45.50 or $4,550.00 balances!
    """

    def __init__(
        self,
        api_client: IDMarketAPI,
        diversification_factor: float = 0.3,
        reserve_percent: float = 0.05,
        small_balance_threshold: float = 100.0,
        money_manager_config: MoneyManagerConfig | None = None,
    ) -> None:
        """Initialize Smart Arbitrage Engine.

        Args:
            api_client: DMarket API client
            diversification_factor: Max percentage of balance per item (default 30%)
            reserve_percent: Percentage to keep as safety reserve (default 5%)
            small_balance_threshold: Below this balance, use stricter profit requirements
            money_manager_config: Optional config for money manager
        """
        self.api_client = api_client
        self.diversification_factor = diversification_factor
        self.reserve_percent = reserve_percent
        self.small_balance_threshold = small_balance_threshold

        # Initialize the universal money manager
        config = money_manager_config or MoneyManagerConfig(
            max_buy_percent=diversification_factor,
            reserve_percent=reserve_percent,
            micro_threshold=small_balance_threshold,
        )
        self.money_manager = MoneyManager(api_client, config)

        # State
        self._current_balance: float = 0.0
        self._last_balance_check: datetime | None = None
        self._is_running = False

        logger.info(
            "smart_arbitrage_initialized",
            diversification=diversification_factor,
            reserve_percent=reserve_percent,
            threshold=small_balance_threshold,
        )

    async def get_current_balance(self, force_refresh: bool = False) -> float:
        """Get current DMarket balance with caching.

        Args:
            force_refresh: Force API call even if cached

        Returns:
            Current balance in USD
        """
        # Cache balance for 60 seconds to reduce API calls
        if (
            not force_refresh
            and self._last_balance_check
            and (datetime.now() - self._last_balance_check).seconds < 60
        ):
            return self._current_balance

        try:
            balance_data = await self.api_client.get_balance()
            if isinstance(balance_data, dict):
                # Balance is in cents, convert to dollars
                usd_cents = int(balance_data.get("usd", 0))
                self._current_balance = usd_cents / 100.0
            else:
                self._current_balance = 0.0

            self._last_balance_check = datetime.now()
            logger.info("smart_balance_fetched", balance=self._current_balance)
            return self._current_balance

        except Exception as e:
            logger.error("smart_balance_error", error=str(e))
            return self._current_balance  # Return last known balance

    async def calculate_adaptive_limits(self) -> SmartLimits:
        """Calculate trading limits based on current balance.

        Uses the universal MoneyManager for percentage-based calculations.
        This makes the bot work equally well for any balance size!

        Returns:
            SmartLimits with calculated parameters
        """
        # Use the money manager for universal calculations
        dynamic_limits = await self.money_manager.calculate_dynamic_limits()

        # Update internal balance tracking
        self._current_balance = dynamic_limits.total_balance
        self._last_balance_check = datetime.now()

        # Convert to SmartLimits for backwards compatibility
        limits = SmartLimits.from_dynamic_limits(dynamic_limits)

        logger.info(
            "smart_limits_calculated",
            tier=limits.tier,
            balance=dynamic_limits.total_balance,
            max_price=limits.max_buy_price,
            min_roi=limits.min_roi,
            inventory_limit=limits.inventory_limit,
        )

        return limits

    async def get_strategy_description(self) -> str:
        """Get human-readable description of current trading strategy.
        
        Returns:
            Strategy description based on current balance tier
        """
        limits = await self.money_manager.calculate_dynamic_limits()
        return self.money_manager.get_strategy_description(limits)

    def check_balance_safety(self) -> tuple[bool, str]:
        """Check if balance changed significantly (safety feature).
        
        Returns:
            Tuple of (is_safe, warning_message)
        """
        is_paused, reason = self.money_manager.is_paused()
        if is_paused:
            return False, f"⚠️ {reason}\nConfirm to continue trading."
        return True, ""

    def confirm_balance_change(self) -> None:
        """Confirm balance change and resume trading."""
        self.money_manager.resume()

    async def find_smart_opportunities(
        self,
        game: str = "csgo",
        whitelist: list[str] | None = None,
        blacklist: list[str] | None = None,
    ) -> list[SmartOpportunity]:
        """Find arbitrage opportunities within smart limits.

        Args:
            game: Game to scan
            whitelist: Only consider these items (optional)
            blacklist: Exclude these items (optional)

        Returns:
            List of opportunities sorted by smart score
        """
        limits = await self.calculate_adaptive_limits()

        if limits.usable_balance <= 0:
            logger.warning("smart_no_balance", usable=limits.usable_balance)
            return []

        try:
            # Fetch market items within DYNAMIC price range
            # Both min and max are percentage-based!
            min_price_cents = int(limits.min_item_price * 100)
            max_price_cents = int(limits.max_buy_price * 100)

            items = await self.api_client.get_market_items(
                game=game,
                limit=100,
                price_from=min_price_cents,
                price_to=max_price_cents,
            )

            opportunities = []
            objects = items.get("objects", []) if isinstance(items, dict) else []

            for item in objects:
                opp = self._analyze_item(item, limits, whitelist, blacklist)
                if opp:
                    opportunities.append(opp)

            # Sort by smart score (highest first)
            opportunities.sort(key=lambda x: x.smart_score, reverse=True)

            logger.info(
                "smart_opportunities_found",
                game=game,
                count=len(opportunities),
                max_price=limits.max_buy_price,
            )

            return opportunities[:20]  # Return top 20

        except Exception as e:
            logger.error("smart_scan_error", game=game, error=str(e))
            return []

    def _analyze_item(
        self,
        item: dict[str, Any],
        limits: SmartLimits,
        whitelist: list[str] | None,
        blacklist: list[str] | None,
    ) -> SmartOpportunity | None:
        """Analyze single item for smart opportunity.

        Args:
            item: Raw item data from API
            limits: Current smart limits
            whitelist: Allowed items
            blacklist: Blocked items

        Returns:
            SmartOpportunity if valid, None otherwise
        """
        try:
            title = item.get("title", "")

            # Check whitelist (if provided)
            if whitelist:
                if not any(w.lower() in title.lower() for w in whitelist):
                    return None

            # Check blacklist
            if blacklist:
                if any(b.lower() in title.lower() for b in blacklist):
                    return None

            # Get prices (in cents)
            price_data = item.get("price", {})
            buy_price_cents = int(price_data.get("USD", 0))
            buy_price = buy_price_cents / 100.0

            # Get suggested price for profit calculation
            suggested_data = item.get("suggestedPrice", {})
            sell_price_cents = int(suggested_data.get("USD", buy_price_cents))
            sell_price = sell_price_cents / 100.0

            # Skip if price too high or too low (dynamic limits!)
            if buy_price > limits.max_buy_price:
                return None
            if buy_price < limits.min_item_price:
                return None  # Skip items below minimum (avoid dust)

            # Calculate profit
            # DMarket commission is ~7%
            commission = sell_price * 0.07
            profit = sell_price - buy_price - commission
            profit_percent = (profit / buy_price) * 100 if buy_price > 0 else 0

            # Skip if profit too low
            if profit_percent < limits.min_roi:
                return None

            # Calculate smart score
            # Higher profit + lower price = better score
            # This prioritizes affordable high-margin items
            price_factor = 1 - (buy_price / limits.max_buy_price)  # 0-1, higher for cheaper
            profit_factor = profit_percent / 100  # Normalized profit
            smart_score = (profit_factor * 0.7) + (price_factor * 0.3)

            return SmartOpportunity(
                item_id=item.get("itemId", ""),
                title=title,
                buy_price=buy_price,
                sell_price=sell_price,
                profit=round(profit, 2),
                profit_percent=round(profit_percent, 1),
                game=item.get("gameId", "csgo"),
                smart_score=round(smart_score * 100, 1),
            )

        except Exception as e:
            logger.debug("smart_item_analysis_error", error=str(e))
            return None

    async def start_smart_mode(
        self,
        games: list[str] | None = None,
        callback: Any = None,
    ) -> None:
        """Start Smart Arbitrage scanning mode.

        Args:
            games: Games to scan (default: all supported)
            callback: Function to call with opportunities
        """
        if self._is_running:
            logger.warning("smart_already_running")
            return

        self._is_running = True
        games = games or ["csgo", "dota2", "rust", "tf2"]

        logger.info("smart_mode_started", games=games)

        try:
            while self._is_running:
                for game in games:
                    if not self._is_running:
                        break

                    opportunities = await self.find_smart_opportunities(game=game)

                    if opportunities and callback:
                        await callback(opportunities)

                    # Small delay between games
                    await asyncio.sleep(2)

                # Wait before next full scan
                # Adaptive: faster when balance is low (more urgent)
                balance = await self.get_current_balance()
                scan_interval = 30 if balance < 50 else 60
                await asyncio.sleep(scan_interval)

        except asyncio.CancelledError:
            logger.info("smart_mode_cancelled")
        except Exception as e:
            logger.error("smart_mode_error", error=str(e))
        finally:
            self._is_running = False
            logger.info("smart_mode_stopped")

    def stop_smart_mode(self) -> None:
        """Stop Smart Arbitrage scanning mode."""
        self._is_running = False
        logger.info("smart_mode_stop_requested")

    @property
    def is_running(self) -> bool:
        """Check if smart mode is running."""
        return self._is_running


# Standalone helper function for use without full engine
def get_smart_limits(balance: float) -> dict[str, Any]:
    """Calculate smart limits from balance (standalone function).

    This uses the universal money management system, so it works
    equally well for $10, $100, $1000, or $10000 balances.

    Args:
        balance: Current balance in USD

    Returns:
        Dict with max_buy_price, min_roi, inventory_limit, etc.
    """
    return calculate_universal_limits(balance)

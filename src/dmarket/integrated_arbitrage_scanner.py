"""
Integrated Multi-Platform Arbitrage Scanner with Waxpeer Auto-Listing.

This module integrates n8n workflow automation directly into the bot for:
1. Finding liquid arbitrage items on DMarket
2. Checking prices on Steam and Waxpeer
3. Keeping profitable items in DMarket inventory (not selling immediately)
4. Creating a self-updating list for profitable Waxpeer resale prices

Combines cross-platform arbitrage with intelligent holding strategy.

Created: January 13, 2026
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from src.dmarket.dmarket_api import DMarketAPI
    from src.waxpeer.waxpeer_api import WaxpeerAPI
    from src.dmarket.steam_api import SteamAPI

logger = structlog.get_logger(__name__)


# ============================================================================
# Configuration and Constants
# ============================================================================

# Platform commissions
DMARKET_COMMISSION = Decimal("0.07")  # 7%
WAXPEER_COMMISSION = Decimal("0.06")  # 6%
STEAM_COMMISSION = Decimal("0.13")  # 13%

# Profitability thresholds
MIN_PROFIT_PERCENT = Decimal("5.0")  # Minimum 5% profit
OPTIMAL_PROFIT_PERCENT = Decimal("15.0")  # 15%+ is great
EXCELLENT_PROFIT_PERCENT = Decimal("25.0")  # 25%+ is excellent

# Liquidity thresholds
MIN_LIQUIDITY_SCORE = 2  # Must be available on at least 2 platforms
HIGH_LIQUIDITY_SCORE = 3  # Available on all 3 platforms

# Update intervals
PRICE_UPDATE_INTERVAL = 300  # 5 minutes
LISTING_UPDATE_INTERVAL = 600  # 10 minutes


@dataclass
class PlatformPrice:
    """Price information from a platform."""

    platform: str  # "dmarket", "waxpeer", "steam"
    price_usd: Decimal
    available: bool = True
    volume_24h: int | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ArbitrageOpportunity:
    """Discovered arbitrage opportunity with liquidity data."""

    item_name: str
    game: str
    
    # Platform prices
    dmarket_price: Decimal | None = None
    waxpeer_price: Decimal | None = None
    steam_price: Decimal | None = None
    
    # Best buy/sell strategy
    buy_platform: str = ""
    buy_price: Decimal = Decimal("0")
    sell_platform: str = ""
    sell_price: Decimal = Decimal("0")
    net_sell_price: Decimal = Decimal("0")  # After commission
    
    # Profitability
    profit_usd: Decimal = Decimal("0")
    profit_percent: Decimal = Decimal("0")
    
    # Liquidity assessment
    liquidity_score: int = 0  # 1-3 (number of platforms)
    is_liquid: bool = False  # True if liquidity_score >= 2
    
    # Metadata
    item_id: str | None = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def __post_init__(self):
        """Calculate liquidity after initialization."""
        self.liquidity_score = sum([
            self.dmarket_price is not None,
            self.waxpeer_price is not None,
            self.steam_price is not None,
        ])
        self.is_liquid = self.liquidity_score >= MIN_LIQUIDITY_SCORE


@dataclass
class WaxpeerListingTarget:
    """Target price for Waxpeer listing with auto-update."""

    item_name: str
    asset_id: str  # DMarket inventory asset ID
    
    # Purchase info
    bought_from: str  # "dmarket"
    buy_price: Decimal
    bought_at: datetime
    
    # Target listing info
    target_list_price: Decimal  # Calculated optimal price
    current_waxpeer_price: Decimal | None = None
    
    # Profitability tracking
    expected_profit: Decimal = Decimal("0")
    expected_roi: Decimal = Decimal("0")
    
    # Auto-update tracking
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    update_count: int = 0
    
    # Status
    is_listed: bool = False
    waxpeer_item_id: str | None = None
    listed_at: datetime | None = None
    
    def calculate_target_price(self, waxpeer_price: Decimal, markup: Decimal = Decimal("0.10")) -> None:
        """Calculate target listing price with markup.
        
        Args:
            waxpeer_price: Current Waxpeer market price
            markup: Markup percentage (default 10% = 0.10)
        """
        self.current_waxpeer_price = waxpeer_price
        
        # Calculate with commission: net_price = list_price * (1 - 0.06)
        # We want: net_price = waxpeer_price * (1 + markup)
        # So: list_price = waxpeer_price * (1 + markup) / (1 - 0.06)
        target_net = waxpeer_price * (Decimal("1") + markup)
        self.target_list_price = target_net / (Decimal("1") - WAXPEER_COMMISSION)
        
        # Calculate expected profit
        net_after_commission = self.target_list_price * (Decimal("1") - WAXPEER_COMMISSION)
        self.expected_profit = net_after_commission - self.buy_price
        self.expected_roi = (self.expected_profit / self.buy_price) * Decimal("100")
        
        self.last_updated = datetime.now(UTC)
        self.update_count += 1


class IntegratedArbitrageScanner:
    """
    Integrated arbitrage scanner that finds opportunities and manages Waxpeer listings.
    
    Features:
    - Multi-platform price comparison (DMarket, Waxpeer, Steam)
    - Liquidity assessment (2-3 platform availability)
    - Automatic profit calculation with commissions
    - Keep items in DMarket inventory for Waxpeer resale
    - Self-updating price list for optimal Waxpeer listings
    """

    def __init__(
        self,
        dmarket_api: DMarketAPI,
        waxpeer_api: WaxpeerAPI,
        steam_api: SteamAPI | None = None,
        min_profit_percent: Decimal = MIN_PROFIT_PERCENT,
        min_liquidity_score: int = MIN_LIQUIDITY_SCORE,
    ):
        """Initialize integrated arbitrage scanner.
        
        Args:
            dmarket_api: DMarket API client
            waxpeer_api: Waxpeer API client
            steam_api: Steam API client (optional)
            min_profit_percent: Minimum profit percentage to consider
            min_liquidity_score: Minimum liquidity score (1-3)
        """
        self.dmarket = dmarket_api
        self.waxpeer = waxpeer_api
        self.steam = steam_api
        self.min_profit_percent = min_profit_percent
        self.min_liquidity_score = min_liquidity_score
        
        # Storage for discovered opportunities and listing targets
        self.opportunities: list[ArbitrageOpportunity] = []
        self.listing_targets: dict[str, WaxpeerListingTarget] = {}  # asset_id -> target
        
        # Tracking
        self.last_scan: datetime | None = None
        self.total_scans: int = 0
        self.total_opportunities: int = 0

    async def scan_multi_platform(
        self, game: str = "csgo", limit: int = 50
    ) -> list[ArbitrageOpportunity]:
        """Scan all platforms and find arbitrage opportunities.
        
        Args:
            game: Game code (csgo, dota2, tf2, rust)
            limit: Maximum items to check per platform
            
        Returns:
            List of profitable arbitrage opportunities sorted by profit
        """
        logger.info("starting_multi_platform_scan", game=game, limit=limit)
        
        # Fetch prices from all platforms in parallel
        dmarket_task = self._fetch_dmarket_prices(game, limit)
        waxpeer_task = self._fetch_waxpeer_prices(game, limit)
        steam_task = self._fetch_steam_prices(game, limit) if self.steam else None
        
        tasks = [dmarket_task, waxpeer_task]
        if steam_task:
            tasks.append(steam_task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        dmarket_prices = results[0] if not isinstance(results[0], Exception) else {}
        waxpeer_prices = results[1] if not isinstance(results[1], Exception) else {}
        steam_prices = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else {}
        
        logger.info(
            "fetched_platform_prices",
            dmarket_count=len(dmarket_prices),
            waxpeer_count=len(waxpeer_prices),
            steam_count=len(steam_prices),
        )
        
        # Find opportunities by matching items across platforms
        opportunities = self._find_opportunities(
            dmarket_prices, waxpeer_prices, steam_prices, game
        )
        
        # Filter by profitability and liquidity
        filtered = [
            opp for opp in opportunities
            if opp.profit_percent >= self.min_profit_percent
            and opp.liquidity_score >= self.min_liquidity_score
        ]
        
        # Sort by profit percentage (best first)
        filtered.sort(key=lambda x: x.profit_percent, reverse=True)
        
        # Update tracking
        self.opportunities = filtered
        self.last_scan = datetime.now(UTC)
        self.total_scans += 1
        self.total_opportunities += len(filtered)
        
        logger.info(
            "scan_complete",
            total_opportunities=len(filtered),
            avg_profit_percent=sum(o.profit_percent for o in filtered) / len(filtered) if filtered else 0,
        )
        
        return filtered

    async def _fetch_dmarket_prices(self, game: str, limit: int) -> dict[str, PlatformPrice]:
        """Fetch prices from DMarket."""
        try:
            # TODO: Implement actual DMarket API call
            # items = await self.dmarket.get_market_items(game=game, limit=limit)
            # return {item['title']: PlatformPrice(...) for item in items}
            return {}
        except Exception as e:
            logger.error("dmarket_fetch_failed", error=str(e))
            return {}

    async def _fetch_waxpeer_prices(self, game: str, limit: int) -> dict[str, PlatformPrice]:
        """Fetch prices from Waxpeer (prices in mils: 1000 mils = $1)."""
        try:
            # TODO: Implement actual Waxpeer API call
            # items = await self.waxpeer.get_items(game=game, limit=limit)
            # return {item['name']: PlatformPrice(...) for item in items}
            return {}
        except Exception as e:
            logger.error("waxpeer_fetch_failed", error=str(e))
            return {}

    async def _fetch_steam_prices(self, game: str, limit: int) -> dict[str, PlatformPrice]:
        """Fetch prices from Steam Market."""
        try:
            # TODO: Implement actual Steam API call
            # items = await self.steam.get_market_items(game=game, limit=limit)
            # return {item['name']: PlatformPrice(...) for item in items}
            return {}
        except Exception as e:
            logger.error("steam_fetch_failed", error=str(e))
            return {}

    def _find_opportunities(
        self,
        dmarket_prices: dict[str, PlatformPrice],
        waxpeer_prices: dict[str, PlatformPrice],
        steam_prices: dict[str, PlatformPrice],
        game: str,
    ) -> list[ArbitrageOpportunity]:
        """Find arbitrage opportunities by comparing prices."""
        opportunities = []
        
        # Get all unique item names
        all_items = set(dmarket_prices.keys()) | set(waxpeer_prices.keys()) | set(steam_prices.keys())
        
        for item_name in all_items:
            dmarket = dmarket_prices.get(item_name)
            waxpeer = waxpeer_prices.get(item_name)
            steam = steam_prices.get(item_name)
            
            # Need at least 2 platforms
            available_count = sum([dmarket is not None, waxpeer is not None, steam is not None])
            if available_count < 2:
                continue
            
            # Find best buy and sell prices
            prices = []
            if dmarket:
                prices.append(("dmarket", dmarket.price_usd))
            if waxpeer:
                prices.append(("waxpeer", waxpeer.price_usd))
            if steam:
                prices.append(("steam", steam.price_usd))
            
            if len(prices) < 2:
                continue
            
            # Sort by price (cheapest first)
            prices.sort(key=lambda x: x[1])
            
            buy_platform, buy_price = prices[0]
            sell_platform, sell_price = prices[-1]
            
            # Calculate net after commission
            if sell_platform == "dmarket":
                net_sell = sell_price * (Decimal("1") - DMARKET_COMMISSION)
            elif sell_platform == "waxpeer":
                net_sell = sell_price * (Decimal("1") - WAXPEER_COMMISSION)
            elif sell_platform == "steam":
                net_sell = sell_price * (Decimal("1") - STEAM_COMMISSION)
            else:
                net_sell = sell_price
            
            profit = net_sell - buy_price
            profit_percent = (profit / buy_price) * Decimal("100")
            
            # Create opportunity
            opp = ArbitrageOpportunity(
                item_name=item_name,
                game=game,
                dmarket_price=dmarket.price_usd if dmarket else None,
                waxpeer_price=waxpeer.price_usd if waxpeer else None,
                steam_price=steam.price_usd if steam else None,
                buy_platform=buy_platform,
                buy_price=buy_price,
                sell_platform=sell_platform,
                sell_price=sell_price,
                net_sell_price=net_sell,
                profit_usd=profit,
                profit_percent=profit_percent,
            )
            
            opportunities.append(opp)
        
        return opportunities

    async def create_waxpeer_listing_target(
        self, item_name: str, asset_id: str, buy_price: Decimal
    ) -> WaxpeerListingTarget:
        """Create a listing target for Waxpeer resale.
        
        This keeps the item in DMarket inventory and prepares it for Waxpeer listing.
        
        Args:
            item_name: Item name
            asset_id: DMarket inventory asset ID
            buy_price: Price paid on DMarket
            
        Returns:
            WaxpeerListingTarget with calculated optimal price
        """
        logger.info("creating_waxpeer_target", item=item_name, asset_id=asset_id)
        
        # Fetch current Waxpeer price
        current_waxpeer_price = await self._get_current_waxpeer_price(item_name)
        
        if not current_waxpeer_price:
            logger.warning("no_waxpeer_price", item=item_name)
            current_waxpeer_price = buy_price * Decimal("1.15")  # Fallback: +15%
        
        # Create target
        target = WaxpeerListingTarget(
            item_name=item_name,
            asset_id=asset_id,
            bought_from="dmarket",
            buy_price=buy_price,
            bought_at=datetime.now(UTC),
        )
        
        # Calculate optimal listing price (10% above market)
        target.calculate_target_price(current_waxpeer_price, markup=Decimal("0.10"))
        
        # Store in tracking dict
        self.listing_targets[asset_id] = target
        
        logger.info(
            "target_created",
            item=item_name,
            buy_price=float(buy_price),
            target_price=float(target.target_list_price),
            expected_roi=float(target.expected_roi),
        )
        
        return target

    async def _get_current_waxpeer_price(self, item_name: str) -> Decimal | None:
        """Get current Waxpeer price for an item."""
        try:
            # TODO: Implement actual Waxpeer API call
            # result = await self.waxpeer.get_item_price(item_name)
            # return Decimal(str(result['price'])) / 1000  # Convert mils to USD
            return None
        except Exception as e:
            logger.error("waxpeer_price_fetch_failed", item=item_name, error=str(e))
            return None

    async def update_listing_targets(self) -> list[WaxpeerListingTarget]:
        """Update all listing targets with current Waxpeer prices.
        
        Returns:
            List of updated targets
        """
        logger.info("updating_listing_targets", count=len(self.listing_targets))
        
        updated = []
        for asset_id, target in self.listing_targets.items():
            # Fetch latest Waxpeer price
            current_price = await self._get_current_waxpeer_price(target.item_name)
            
            if current_price:
                # Recalculate target price
                target.calculate_target_price(current_price, markup=Decimal("0.10"))
                updated.append(target)
                
                logger.debug(
                    "target_updated",
                    item=target.item_name,
                    new_target=float(target.target_list_price),
                    roi=float(target.expected_roi),
                )
        
        logger.info("targets_updated", count=len(updated))
        return updated

    async def get_listing_recommendations(self) -> list[dict[str, Any]]:
        """Get recommendations for items to list on Waxpeer.
        
        Returns:
            List of items ready for listing with calculated prices
        """
        recommendations = []
        
        for asset_id, target in self.listing_targets.items():
            if target.is_listed:
                continue  # Already listed
            
            # Check if ROI is good enough
            if target.expected_roi < self.min_profit_percent:
                continue
            
            recommendations.append({
                "item_name": target.item_name,
                "asset_id": target.asset_id,
                "buy_price": float(target.buy_price),
                "target_list_price": float(target.target_list_price),
                "expected_profit": float(target.expected_profit),
                "expected_roi": float(target.expected_roi),
                "days_held": (datetime.now(UTC) - target.bought_at).days,
            })
        
        # Sort by ROI (best first)
        recommendations.sort(key=lambda x: x["expected_roi"], reverse=True)
        
        return recommendations

    def get_statistics(self) -> dict[str, Any]:
        """Get scanner statistics."""
        return {
            "total_scans": self.total_scans,
            "total_opportunities_found": self.total_opportunities,
            "current_opportunities": len(self.opportunities),
            "listing_targets": len(self.listing_targets),
            "unlisted_targets": sum(1 for t in self.listing_targets.values() if not t.is_listed),
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "avg_opportunities_per_scan": self.total_opportunities / self.total_scans if self.total_scans > 0 else 0,
        }

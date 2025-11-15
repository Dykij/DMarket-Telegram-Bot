"""Module for filtering game items on DMarket by game-specific attributes.

This module provides a collection of filter classes for different games,
allowing for detailed filtering of game items based on their attributes.
Supported games include CS2/CSGO, Dota 2, Team Fortress 2, and Rust.
"""

from typing import Any


class BaseGameFilter:
    """Base class for game filters."""

    game_name = "base"
    # Common filters for all games
    supported_filters = ["min_price", "max_price"]

    def apply_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if item passes the filters.

        Args:
            item: The item to check.
            filters: The filters to apply.

        Returns:
            True if item passes all filters, False otherwise.

        """
        # Price filters
        if "min_price" in filters:
            price = float(item.get("price", {}).get("USD", 0))
            if price < filters["min_price"]:
                return False

        if "max_price" in filters:
            price = float(item.get("price", {}).get("USD", 0))
            if price > filters["max_price"]:
                return False

        return True


class CS2Filter(BaseGameFilter):
    """Filter for CS2/CSGO items."""

    game_name = "csgo"
    supported_filters = [
        *BaseGameFilter.supported_filters,
        "exterior",
        "rarity",
        "quality",
        "weapon_type",
        "collection",
    ]

    def apply_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Apply CS2-specific filters."""
        if not super().apply_filters(item, filters):
            return False

        # Exterior filter
        if "exterior" in filters:
            item_exterior = item.get("extra", {}).get("exterior", "")
            if item_exterior.lower() != filters["exterior"].lower():
                return False

        # Rarity filter
        if "rarity" in filters:
            item_rarity = item.get("extra", {}).get("rarity", "")
            if item_rarity.lower() != filters["rarity"].lower():
                return False

        # Quality filter
        if "quality" in filters:
            item_quality = item.get("extra", {}).get("quality", "")
            if item_quality.lower() != filters["quality"].lower():
                return False

        # Weapon type filter
        if "weapon_type" in filters:
            item_type = item.get("extra", {}).get("type", "")
            if item_type.lower() != filters["weapon_type"].lower():
                return False

        # Collection filter
        if "collection" in filters:
            item_collection = item.get("extra", {}).get("collection", "")
            if item_collection.lower() != filters["collection"].lower():
                return False

        return True


class Dota2Filter(BaseGameFilter):
    """Filter for Dota 2 items."""

    game_name = "dota2"
    supported_filters = [*BaseGameFilter.supported_filters, "rarity", "hero", "quality", "slot"]

    def apply_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Apply Dota 2-specific filters."""
        if not super().apply_filters(item, filters):
            return False

        # Rarity filter
        if "rarity" in filters:
            item_rarity = item.get("extra", {}).get("rarity", "")
            if item_rarity.lower() != filters["rarity"].lower():
                return False

        # Hero filter
        if "hero" in filters:
            item_hero = item.get("extra", {}).get("hero", "")
            if item_hero.lower() != filters["hero"].lower():
                return False

        # Quality filter
        if "quality" in filters:
            item_quality = item.get("extra", {}).get("quality", "")
            if item_quality.lower() != filters["quality"].lower():
                return False

        # Slot filter
        if "slot" in filters:
            item_slot = item.get("extra", {}).get("slot", "")
            if item_slot.lower() != filters["slot"].lower():
                return False

        return True


class RustFilter(BaseGameFilter):
    """Filter for Rust items."""

    game_name = "rust"
    supported_filters = [*BaseGameFilter.supported_filters, "item_type", "rarity"]

    def apply_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Apply Rust-specific filters."""
        if not super().apply_filters(item, filters):
            return False

        # Item type filter
        if "item_type" in filters:
            item_type = item.get("extra", {}).get("type", "")
            if item_type.lower() != filters["item_type"].lower():
                return False

        # Rarity filter
        if "rarity" in filters:
            item_rarity = item.get("extra", {}).get("rarity", "")
            if item_rarity.lower() != filters["rarity"].lower():
                return False

        return True


class FilterFactory:
    """Factory for creating game-specific filters."""

    _filters = {
        "csgo": CS2Filter,
        "cs2": CS2Filter,
        "dota2": Dota2Filter,
        "rust": RustFilter,
    }

    @classmethod
    def get_filter(cls, game: str) -> BaseGameFilter:
        """Get filter instance for a specific game.

        Args:
            game: Game identifier (csgo, cs2, dota2, rust, etc.)

        Returns:
            BaseGameFilter: Filter instance for the game

        """
        filter_class = cls._filters.get(game.lower(), BaseGameFilter)
        return filter_class()

    @classmethod
    def register_filter(cls, game: str, filter_class: type[BaseGameFilter]) -> None:
        """Register a custom filter for a game.

        Args:
            game: Game identifier
            filter_class: Filter class to register

        """
        cls._filters[game.lower()] = filter_class


def apply_filters_to_items(
    items: list[dict[str, Any]],
    game: str,
    filters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Apply game-specific filters to a list of items.

    Args:
        items: List of items to filter
        game: Game identifier
        filters: Dictionary of filters to apply

    Returns:
        list: Filtered list of items

    """
    if not items:
        return []

    game_filter = FilterFactory.get_filter(game)
    return [item for item in items if game_filter.apply_filters(item, filters)]

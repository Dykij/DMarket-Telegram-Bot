"""Tree filters configuration for optimized market scanning.

This module provides game-specific treeFilters to reduce API response size
by 50-70% by focusing only on profitable item categories.

Based on DMarket API documentation:
https://docs.dmarket.com/v1/swagger.html#/Market/get_exchange_v1_market_items
"""

import json
from typing import Any


def get_tree_filters_for_game(game: str, mode: str = "medium") -> str | None:
    """Get optimized treeFilters JSON for a game and arbitrage mode.

    Args:
        game: Game code (csgo, dota2, tf2, rust)
        mode: Arbitrage mode (low, medium, high)

    Returns:
        JSON string with treeFilters or None if no specific filters
    """
    filters = _get_filters_dict(game, mode)
    if not filters:
        return None

    return json.dumps(filters)


def _get_filters_dict(game: str, mode: str) -> dict[str, Any] | None:
    """Get filters dictionary for a game and mode.

    Returns:
        Dict with filter structure or None
    """
    game_lower = game.lower()

    if game_lower == "csgo":
        return _get_csgo_filters(mode)
    if game_lower == "dota2":
        return _get_dota2_filters(mode)
    if game_lower == "tf2":
        return _get_tf2_filters(mode)
    if game_lower == "rust":
        return _get_rust_filters(mode)

    return None


def _get_csgo_filters(mode: str) -> dict[str, Any] | None:
    """Get CS:GO specific filters based on arbitrage mode.

    CS:GO most profitable categories:
    - Knives (weapon_knife) - highest margins
    - Gloves (weapon_gloves) - high demand
    - Rifles (weapon_rifle) - liquid market
    - Covert/Classified skins - good arbitrage
    """
    if mode == "high":
        # High mode: focus on expensive items (knives, gloves)
        return {
            "category": ["weapon_knife", "weapon_gloves"],
        }
    if mode == "medium":
        # Medium: knives, gloves, rifles
        return {
            "category": ["weapon_knife", "weapon_gloves", "weapon_rifle"],
        }
    if mode == "low":
        # Low mode: include pistols and SMGs for volume
        return {
            "category": [
                "weapon_knife",
                "weapon_gloves",
                "weapon_rifle",
                "weapon_pistol",
                "weapon_smg",
            ],
        }

    return None


def _get_dota2_filters(mode: str) -> dict[str, Any] | None:
    """Get Dota 2 specific filters based on arbitrage mode.

    Dota 2 most profitable:
    - Arcana - highest value
    - Immortal - high demand
    - Mythical - good liquidity
    """
    if mode == "high":
        # High: only Arcana and Immortal
        return {
            "rarity": ["arcana", "immortal"],
        }
    if mode == "medium":
        # Medium: add Mythical
        return {
            "rarity": ["arcana", "immortal", "mythical"],
        }
    if mode == "low":
        # Low: include Rare for volume
        return {
            "rarity": ["arcana", "immortal", "mythical", "rare"],
        }

    return None


def _get_tf2_filters(mode: str) -> dict[str, Any] | None:
    """Get TF2 specific filters based on arbitrage mode.

    TF2 most profitable:
    - Unusual items - highest margins
    - Strange quality - good demand
    - Vintage - collector value
    """
    if mode == "high":
        # High: only Unusual
        return {
            "quality": ["unusual"],
        }
    if mode == "medium":
        # Medium: Unusual and Strange
        return {
            "quality": ["unusual", "strange"],
        }
    if mode == "low":
        # Low: add Vintage and Genuine
        return {
            "quality": ["unusual", "strange", "vintage", "genuine"],
        }

    return None


def _get_rust_filters(mode: str) -> dict[str, Any] | None:
    """Get Rust specific filters based on arbitrage mode.

    Rust categories:
    - Weapons - good liquidity
    - Clothing - high volume
    - Deployables - stable prices
    """
    if mode == "high":
        # High: focus on weapons (best margins)
        return {
            "category": ["weapon"],
        }
    if mode == "medium":
        # Medium: weapons and clothing
        return {
            "category": ["weapon", "clothing"],
        }
    if mode == "low":
        # Low: all major categories
        return {
            "category": ["weapon", "clothing", "deployable"],
        }

    return None


def get_filter_description(game: str, mode: str) -> str:
    """Get human-readable description of active filters.

    Args:
        game: Game code
        mode: Arbitrage mode

    Returns:
        Description string for logging
    """
    filters = _get_filters_dict(game, mode)

    if not filters:
        return f"{game.upper()} - no specific filters"

    filter_parts = []
    for key, values in filters.items():
        filter_parts.append(f"{key}=[{', '.join(values)}]")

    return f"{game.upper()} - {', '.join(filter_parts)}"


# Filter effectiveness estimates (based on empirical data)
FILTER_EFFECTIVENESS = {
    "csgo": {
        "high": 0.75,  # Reduces response by ~75% (knives/gloves only)
        "medium": 0.60,  # Reduces response by ~60%
        "low": 0.40,  # Reduces response by ~40%
    },
    "dota2": {
        "high": 0.80,  # Arcana/Immortal very selective
        "medium": 0.65,
        "low": 0.45,
    },
    "tf2": {
        "high": 0.70,  # Unusual items are rare
        "medium": 0.50,
        "low": 0.30,
    },
    "rust": {
        "high": 0.50,  # Weapons category
        "medium": 0.35,
        "low": 0.20,
    },
}


def get_filter_effectiveness(game: str, mode: str) -> float:
    """Get estimated reduction in API response size.

    Args:
        game: Game code
        mode: Arbitrage mode

    Returns:
        Float between 0 and 1 (0.75 = 75% reduction)
    """
    game_lower = game.lower()
    effectiveness = FILTER_EFFECTIVENESS.get(game_lower, {})
    return effectiveness.get(mode, 0.0)

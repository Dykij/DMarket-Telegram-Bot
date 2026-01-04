"""Whitelist configuration for high-liquidity items.

This module contains curated lists of highly liquid items for each game
that are safe to trade and quick to sell.
"""

import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

# Белый список высоколиквидных предметов по играм
# App ID маппинг: CS2=730, Rust=252490, Dota2=570, TF2=440
WHITELIST_ITEMS = {
    "730": [  # CS:GO/CS2
        "Chroma 3 Case",
        "Clutch Case",
        "Dreams & Nightmares Case",
        "Fracture Case",
        "Recoil Case",
        "Snakebite Case",
        "Revolution Case",
        "Kilowatt Case",
        "AK-47 | Slate (Field-Tested)",
        "Desert Eagle | Mecha Industries (Field-Tested)",
        "Glock-18 | Candy Apple (Factory New)",
        "USP-S | Cyrex (Field-Tested)",
        "M4A4 | Desolate Space (Field-Tested)",
        "AWP | Phobos (Field-Tested)",
    ],
    "252490": [  # Rust
        "Wood Storage Box",
        "Large Wood Box",
        "Sheet Metal Door",
        "Armored Door",
        "Furnace",
        "Sleeping Bag",
        "Metal Chest Plate",
        "Road Sign Kilt",
        "Coffee Can Helmet",
    ],
    "570": [  # Dota 2
        "Immortal Treasure",
        "Inscribed Murder of Crows",
        "Manifold Paradox",
        "Feast of Abscession",
        "Fractal Horns of Inner Abysm",
        "Genuine Monarch Bow",
        "Dragonclaw Hook",
    ],
    "440": [  # TF2 (Самое ликвидное)
        "Mann Co. Supply Crate Key",  # Ключи — лучшая валюта
        "Tour of Duty Ticket",
        "Refined Metal",
        "Scrap Metal",
        "Reclaimed Metal",
        "Taunt: The Schadenfreude",
        "Taunt: The Conga",
        "Strange Part",
    ],
}

# Маппинг коротких имен игр в App ID
GAME_APP_ID_MAP = {
    "csgo": "730",
    "cs2": "730",
    "rust": "252490",
    "dota2": "570",
    "tf2": "440",
}

# Настройки whitelist (могут быть переопределены из JSON)
WHITELIST_SETTINGS: dict[str, Any] = {
    "enabled": True,
    "priority_only": False,
    "max_same_items_in_inventory": 5,
    "buy_max_overpay_percent": 2.0,
    "max_stack_value_percent": 15,
    "min_liquidity_score": 70,
}

# Веса игр для диверсификации (в процентах внимания)
GAME_WEIGHTS: dict[str, int] = {
    "tf2": 30,  # Ключи стабильны, быстро продаются
    "csgo": 40,  # Кейсы и скины, высокая волатильность
    "rust": 20,  # Двери и ящики, стабильный спрос
    "dota2": 10,  # Только Inscribed/Immortal предметы
}


def load_whitelist_from_json(file_path: str = "data/whitelist.json") -> bool:
    """Загружает whitelist из JSON файла.

    Args:
        file_path: Путь к JSON файлу с whitelist

    Returns:
        True если загрузка успешна, False иначе
    """
    global WHITELIST_ITEMS, WHITELIST_SETTINGS, GAME_WEIGHTS

    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Whitelist file not found: {file_path}")
        return False

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Загружаем настройки
        if "settings" in data:
            WHITELIST_SETTINGS.update(data["settings"])
            logger.info(f"Loaded whitelist settings: {WHITELIST_SETTINGS}")

        # Загружаем enabled/priority_only
        if "enabled" in data:
            WHITELIST_SETTINGS["enabled"] = data["enabled"]
        if "priority_only" in data:
            WHITELIST_SETTINGS["priority_only"] = data["priority_only"]

        # Загружаем веса игр для диверсификации
        if "game_weights" in data:
            GAME_WEIGHTS.update(data["game_weights"])
            logger.info(f"Loaded game weights: {GAME_WEIGHTS}")

        # Загружаем предметы по играм
        if "items" in data:
            items_data = data["items"]
            total_items = 0

            # Маппинг имен игр из JSON в App ID
            game_to_appid = {
                "csgo": "730",
                "cs2": "730",
                "dota2": "570",
                "rust": "252490",
                "tf2": "440",
            }

            for game_name, items in items_data.items():
                app_id = game_to_appid.get(game_name.lower())
                if app_id and items:
                    # Добавляем к существующему списку, избегая дубликатов
                    existing = set(WHITELIST_ITEMS.get(app_id, []))
                    new_items = [item for item in items if item not in existing]
                    WHITELIST_ITEMS[app_id] = list(existing) + new_items
                    total_items += len(new_items)
                    logger.debug(f"Loaded {len(new_items)} items for {game_name}")

            logger.info(f"✅ Loaded {total_items} whitelist items from {file_path}")

        return True

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse whitelist JSON: {e}")
        return False
    except Exception as e:
        logger.exception(f"Error loading whitelist: {e}")
        return False


def get_game_weight(game: str) -> int:
    """Получает вес игры для стратегии диверсификации.

    Args:
        game: Код игры (csgo, rust, dota2, tf2)

    Returns:
        Вес игры в процентах (0-100)
    """
    return GAME_WEIGHTS.get(game.lower(), 10)


class WhitelistChecker:
    """Класс для проверки предметов по белому списку."""

    def __init__(self, enable_priority_boost: bool = True, profit_boost_percent: float = 2.0):
        """Инициализирует проверку белого списка.

        Args:
            enable_priority_boost: Включить приоритетную обработку whitelist предметов
            profit_boost_percent: На сколько процентов снизить порог профита для whitelist
        """
        self.enable_priority_boost = enable_priority_boost
        self.profit_boost_percent = profit_boost_percent

    def is_whitelisted(self, item: dict[str, Any], game: str) -> bool:
        """Проверяет, находится ли предмет в белом списке.

        Args:
            item: Словарь с данными предмета
            game: Код игры (csgo, rust, dota2, tf2)

        Returns:
            True если предмет в белом списке, False иначе
        """
        # Получаем App ID игры
        app_id = GAME_APP_ID_MAP.get(game.lower())
        if not app_id:
            return False

        # Получаем whitelist для этой игры
        whitelist = WHITELIST_ITEMS.get(app_id, [])
        if not whitelist:
            return False

        # Проверяем title предмета
        title = item.get("title", "")
        return any(target in title for target in whitelist)

    def get_adjusted_profit_margin(self, base_margin: float, is_whitelist: bool) -> float:
        """Получает скорректированный порог профита.

        Args:
            base_margin: Базовый порог профита
            is_whitelist: Предмет из белого списка

        Returns:
            Скорректированный порог профита
        """
        if is_whitelist and self.enable_priority_boost:
            # Снижаем порог профита для whitelist предметов
            adjusted = base_margin - self.profit_boost_percent
            logger.debug(
                f"🎯 Whitelist priority: profit margin adjusted "
                f"{base_margin:.1f}% -> {adjusted:.1f}%"
            )
            return max(adjusted, 3.0)  # Минимум 3% чистого профита

        return base_margin


def get_whitelist_for_game(game: str) -> list[str]:
    """Получает белый список для конкретной игры.

    Args:
        game: Код игры (csgo, rust, dota2, tf2)

    Returns:
        Список названий предметов в белом списке
    """
    app_id = GAME_APP_ID_MAP.get(game.lower())
    if not app_id:
        return []

    return WHITELIST_ITEMS.get(app_id, [])


def add_to_whitelist(game: str, item_name: str) -> bool:
    """Добавляет предмет в белый список.

    Args:
        game: Код игры (csgo, rust, dota2, tf2)
        item_name: Название предмета

    Returns:
        True если добавлено успешно, False иначе
    """
    app_id = GAME_APP_ID_MAP.get(game.lower())
    if not app_id:
        logger.warning(f"Unknown game: {game}")
        return False

    if app_id not in WHITELIST_ITEMS:
        WHITELIST_ITEMS[app_id] = []

    if item_name not in WHITELIST_ITEMS[app_id]:
        WHITELIST_ITEMS[app_id].append(item_name)
        logger.info(f"✅ Added to whitelist ({game}): {item_name}")
        return True

    logger.warning(f"Item already in whitelist: {item_name}")
    return False


def remove_from_whitelist(game: str, item_name: str) -> bool:
    """Удаляет предмет из белого списка.

    Args:
        game: Код игры (csgo, rust, dota2, tf2)
        item_name: Название предмета

    Returns:
        True если удалено успешно, False иначе
    """
    app_id = GAME_APP_ID_MAP.get(game.lower())
    if not app_id or app_id not in WHITELIST_ITEMS:
        return False

    if item_name in WHITELIST_ITEMS[app_id]:
        WHITELIST_ITEMS[app_id].remove(item_name)
        logger.info(f"🗑️ Removed from whitelist ({game}): {item_name}")
        return True

    return False

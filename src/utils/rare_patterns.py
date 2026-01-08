"""Конфигурация и логика для определения редких предметов (Rare Hold).

Модуль содержит настройки и функции для автоматического определения
редких предметов, которые не должны продаваться по обычной цене:
- Низкий float (Double Zero и т.д.)
- Редкие фазы Doppler (Ruby, Sapphire, Black Pearl и др.)
- Редкие паттерны (Blue Gem и др.)
- Предметы со стикерами

Автор: DMarket Bot Team
Дата: 2026-01-04
"""

from __future__ import annotations

from typing import Any

from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ РЕДКОСТИ
# ═══════════════════════════════════════════════════════════════════════════

RARE_CONFIG: dict[str, Any] = {
    # Float Value пороги
    "max_float_to_hold": 0.01,  # Все предметы с float < 0.01 не продаём (Double Zero)
    "min_float_to_hold": 0.999,  # Все предметы с float > 0.999 (максимальный wear) оставляем
    # Редкие фазы Doppler ножей
    "rare_phases": [
        "Ruby",
        "Sapphire",
        "Black Pearl",
        "Emerald",
        "Phase 2",  # Много розового
        "Phase 4",  # Много синего
    ],
    # Редкие паттерны по названию предмета
    # Формат: {название: [список редких paint_seed]}
    "rare_patterns": {
        # AK-47 Blue Gem паттерны
        "AK-47 | Case Hardened": [661, 670, 321, 955, 387, 151, 179, 695, 809, 868],
        # AWP редкие паттерны
        "AWP | Lightning Strike": [1, 42, 70],
        # Five-SeveN Blue Gem
        "Five-SeveN | Case Hardened": [278, 363, 387, 532, 690, 872],
        # Karambit Blue Gem
        "Karambit | Case Hardened": [387, 442, 463, 470, 509, 601, 617, 661, 670, 853],
        # Bayonet Blue Gem
        "Bayonet | Case Hardened": [151, 387, 442, 601, 617, 695, 854],
        # M9 Bayonet Blue Gem
        "M9 Bayonet | Case Hardened": [442, 601, 617, 857],
        # Falchion Blue Gem
        "Falchion Knife | Case Hardened": [387, 494, 516, 601, 617, 695],
    },
    # Проверять ли стикеры
    "check_stickers": True,
    # Минимальная стоимость стикеров для hold (в долларах)
    "min_sticker_value_to_hold": 50.0,
    # Известные дорогие стикеры (краткие названия)
    "valuable_stickers": [
        "Katowice 2014",
        "IBuyPower",
        "Titan",
        "Reason Gaming",
        "HellRaisers (Holo)",
        "compLexity Gaming (Holo)",
        "Crown (Foil)",
        "Howling Dawn",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ ОПРЕДЕЛЕНИЯ РЕДКОСТИ
# ═══════════════════════════════════════════════════════════════════════════


def is_item_rare(item_data: dict[str, Any]) -> bool:
    """Проверить, является ли предмет редким и нужно ли его оставить в инвентаре.

    Args:
        item_data: Данные предмета из API DMarket

    Returns:
        True если предмет редкий и его не стоит продавать автоматически
    """
    title = item_data.get("title", "")

    # Извлекаем атрибуты
    attributes = _extract_attributes(item_data)

    # 1. Проверка float value
    if _is_rare_float(attributes):
        logger.info(f"💎 [RARE HOLD] Float value: {title}")
        return True

    # 2. Проверка фаз Doppler
    if _is_rare_doppler_phase(title):
        logger.info(f"💎 [RARE HOLD] Doppler phase: {title}")
        return True

    # 3. Проверка паттернов (Blue Gem и др.)
    if _is_rare_pattern(title, attributes):
        logger.info(f"💎 [RARE HOLD] Rare pattern: {title}")
        return True

    # 4. Проверка стикеров
    if RARE_CONFIG["check_stickers"] and _has_valuable_stickers(item_data):
        logger.info(f"💎 [RARE HOLD] Valuable stickers: {title}")
        return True

    return False


def _extract_attributes(item_data: dict[str, Any]) -> dict[str, str]:
    """Извлечь атрибуты из данных предмета.

    Args:
        item_data: Данные предмета

    Returns:
        Словарь атрибутов {type: value}
    """
    attributes_list = item_data.get("attributes", [])
    if not attributes_list:
        # Попробуем альтернативные поля
        extra = item_data.get("extra", {})
        if extra:
            # Используем None-безопасные значения
            float_val = extra.get("floatValue")
            paint_seed = extra.get("paintSeed")
            return {
                "float_value": str(float_val) if float_val is not None else "",
                "paint_seed": str(paint_seed) if paint_seed is not None else "-1",
                "phase": extra.get("phase", ""),
            }
        return {}

    return {attr.get("type", ""): attr.get("value", "") for attr in attributes_list}


def _is_rare_float(attributes: dict[str, str]) -> bool:
    """Проверить, имеет ли предмет редкий float.

    Args:
        attributes: Атрибуты предмета

    Returns:
        True если float редкий
    """
    float_str = attributes.get("float_value") or attributes.get("floatValue", "")

    # Если float не указан - не считаем редким
    if not float_str:
        return False

    try:
        float_val = float(float_str)
    except (ValueError, TypeError):
        return False

    # Очень низкий float (Double Zero и т.д.)
    if float_val <= RARE_CONFIG["max_float_to_hold"]:
        return True

    # Очень высокий float (Battle-Scarred максимум)
    return float_val >= RARE_CONFIG["min_float_to_hold"]


def _is_rare_doppler_phase(title: str) -> bool:
    """Проверить, является ли предмет редкой фазой Doppler.

    Args:
        title: Название предмета

    Returns:
        True если редкая фаза
    """
    if "Doppler" not in title:
        return False

    title_lower = title.lower()

    # Проверяем специальные фазы (Ruby, Sapphire, Black Pearl, Emerald)
    special_phases = ["ruby", "sapphire", "black pearl", "emerald"]
    for phase in special_phases:
        if phase in title_lower:
            return True

    # Проверяем Phase 2 и Phase 4 точно (не Phase 1, Phase 3)
    if "phase 2" in title_lower or "(phase 2)" in title_lower:
        return True
    return bool("phase 4" in title_lower or "(phase 4)" in title_lower)


def _is_rare_pattern(title: str, attributes: dict[str, str]) -> bool:
    """Проверить, имеет ли предмет редкий паттерн.

    Args:
        title: Название предмета
        attributes: Атрибуты предмета

    Returns:
        True если редкий паттерн
    """
    # Получаем paint_seed
    seed_str = attributes.get("paint_seed") or attributes.get("paintSeed", "-1")

    try:
        pattern_index = int(seed_str)
    except (ValueError, TypeError):
        return False

    if pattern_index < 0:
        return False

    # Проверяем по базе редких паттернов
    for item_name, rare_seeds in RARE_CONFIG["rare_patterns"].items():
        if item_name in title:
            if pattern_index in rare_seeds:
                return True

    return False


def _has_valuable_stickers(item_data: dict[str, Any]) -> bool:
    """Проверить, есть ли на предмете дорогие стикеры.

    Args:
        item_data: Данные предмета

    Returns:
        True если есть дорогие стикеры
    """
    # Проверяем в extra
    extra = item_data.get("extra", {})
    stickers = extra.get("stickers", [])

    if not stickers:
        # Попробуем найти в строковом представлении
        item_str = str(item_data).lower()
        for sticker_name in RARE_CONFIG["valuable_stickers"]:
            if sticker_name.lower() in item_str:
                return True
        return False

    # Проверяем список стикеров
    for sticker in stickers:
        sticker_name = sticker.get("name", "")
        sticker_value = sticker.get("price", 0)

        # По названию
        for valuable in RARE_CONFIG["valuable_stickers"]:
            if valuable.lower() in sticker_name.lower():
                return True

        # По стоимости
        if sticker_value >= RARE_CONFIG["min_sticker_value_to_hold"] * 100:  # В центах
            return True

    return False


def get_rarity_reason(item_data: dict[str, Any]) -> str | None:
    """Получить причину, почему предмет считается редким.

    Args:
        item_data: Данные предмета

    Returns:
        Строка с причиной или None если предмет не редкий
    """
    title = item_data.get("title", "")
    attributes = _extract_attributes(item_data)

    if _is_rare_float(attributes):
        float_str = attributes.get("float_value") or attributes.get("floatValue", "")
        return f"Редкий float: {float_str}"

    if _is_rare_doppler_phase(title):
        return "Редкая фаза Doppler"

    if _is_rare_pattern(title, attributes):
        seed = attributes.get("paint_seed") or attributes.get("paintSeed", "")
        return f"Редкий паттерн (seed: {seed})"

    if RARE_CONFIG["check_stickers"] and _has_valuable_stickers(item_data):
        return "Дорогие стикеры"

    return None


# ═══════════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════════


def add_rare_pattern(item_name: str, pattern_seed: int) -> None:
    """Добавить редкий паттерн в конфигурацию.

    Args:
        item_name: Полное название предмета
        pattern_seed: Номер паттерна (paint_seed)
    """
    if item_name not in RARE_CONFIG["rare_patterns"]:
        RARE_CONFIG["rare_patterns"][item_name] = []

    if pattern_seed not in RARE_CONFIG["rare_patterns"][item_name]:
        RARE_CONFIG["rare_patterns"][item_name].append(pattern_seed)
        logger.info(f"Added rare pattern: {item_name} seed={pattern_seed}")


def set_max_float_threshold(value: float) -> None:
    """Установить порог float для hold.

    Args:
        value: Максимальный float для удержания (например, 0.01)
    """
    RARE_CONFIG["max_float_to_hold"] = value
    logger.info(f"Max float threshold set to: {value}")


def get_rare_config() -> dict[str, Any]:
    """Получить текущую конфигурацию редкости.

    Returns:
        Копия конфигурации
    """
    return RARE_CONFIG.copy()

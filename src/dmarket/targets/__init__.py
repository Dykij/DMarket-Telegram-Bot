"""Пакет для управления таргетами (buy orders) на DMarket.

Таргеты - это заявки на покупку предметов по указанной цене.
Когда продавец выставляет предмет по цене таргета или ниже,
происходит автоматическая покупка.

Основные возможности:
- Создание таргетов с указанием цены и атрибутов
- Управление активными таргетами
- Автоматическое создание умных таргетов
- Мониторинг исполненных таргетов
- Анализ конкуренции

Рефакторинг выполнен 14.12.2025 в рамках задачи R-8.
"""

from .competition import (
    analyze_target_competition,
    assess_competition,
    filter_low_competition_items,
)
from .manager import TargetManager
from .validators import GAME_IDS, extract_attributes_from_title, validate_attributes


__all__ = [
    # Manager
    "TargetManager",
    # Competition
    "analyze_target_competition",
    "assess_competition",
    "filter_low_competition_items",
    # Validators
    "GAME_IDS",
    "extract_attributes_from_title",
    "validate_attributes",
]

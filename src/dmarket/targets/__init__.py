"""Пакет для управления таргетами (buy orders) на DMarket.

Этот пакет предоставляет расширенную функциональность для работы с таргетами:

Основные компоненты:
- manager.py: Основной менеджер таргетов
- validators.py: Базовые валидаторы
- competition.py: Анализ конкуренции
- enhanced_validators.py: Расширенные валидаторы (NEW)
- batch_operations.py: Пакетные операции (NEW)

Новые возможности (январь 2026):
- 🎯 Пакетное создание ордеров на несколько предметов
- 🔍 Обнаружение существующих ордеров и проверка дубликатов
- 🎨 Фильтры по стикерам (CS:GO)
- 💎 Фильтры по редкости (Dota 2, TF2)
- 🔄 Автоматическое перебитие конкурентов
- 📊 Контроль лимитов перевыставлений
- 💵 Мониторинг диапазона цен
- ⚙️ Дефолтные параметры для базы предметов
- ✅ Проверка количества условий (DMarket API лимиты)
- 📝 Расширенные сообщения об ошибках с подсказками

Документация:
- docs/DMARKET_API_FULL_SPEC.md - спецификация DMarket API
- docs/ARBITRAGE.md - руководство по арбитражу и таргетам

Рефакторинг выполнен 14.12.2025 в рамках задачи R-8.
Расширение выполнено 01.01.2026 (новые возможности таргетов).

Примеры использования:
    >>> from src.dmarket.targets.manager import TargetManager
    >>> from src.dmarket.models.target_enhancements import (
    ...     TargetDefaults,
    ...     TargetOverbidConfig,
    ...     StickerFilter,
    ... )
    >>>
    >>> # Создать менеджер с дефолтами
    >>> defaults = TargetDefaults(
    ...     default_amount=1, default_overbid_config=TargetOverbidConfig(enabled=True)
    ... )
    >>> manager = TargetManager(api_client=api, defaults=defaults)
"""

# Новые функции и контроллеры (январь 2026)
from .batch_operations import check_duplicate_order, create_batch_target, detect_existing_orders
from .competition import (
    analyze_target_competition,
    assess_competition,
    filter_low_competition_items,
)
from .enhanced_validators import (
    count_target_conditions,
    validate_filter_compatibility,
    validate_target_attributes,
    validate_target_complete,
    validate_target_conditions,
    validate_target_price,
)
from .manager import TargetManager
from .overbid_controller import OverbidController
from .price_range_monitor import PriceRangeMonitor
from .relist_manager import RelistManager
from .validators import GAME_IDS, extract_attributes_from_title, validate_attributes

__all__ = [
    # Основные компоненты
    "GAME_IDS",
    "TargetManager",
    "extract_attributes_from_title",
    "validate_attributes",
    # Конкуренция
    "analyze_target_competition",
    "assess_competition",
    "filter_low_competition_items",
    # Пакетные операции (NEW)
    "create_batch_target",
    "detect_existing_orders",
    "check_duplicate_order",
    # Расширенные валидаторы (NEW)
    "validate_target_complete",
    "validate_target_conditions",
    "validate_target_price",
    "validate_target_attributes",
    "validate_filter_compatibility",
    "count_target_conditions",
    # Контроллеры и менеджеры (NEW)
    "OverbidController",
    "RelistManager",
    "PriceRangeMonitor",
]

"""Константы и типы для системы уведомлений.

Этот модуль содержит все константы, используемые в системе уведомлений,
включая типы уведомлений и настройки кэширования.
"""

from __future__ import annotations

from typing import Final


# Типы уведомлений
NOTIFICATION_TYPES: Final[dict[str, str]] = {
    "price_drop": "📉 Падение цены",
    "price_rise": "📈 Рост цены",
    "volume_increase": "📊 Увеличение объема торгов",
    "good_deal": "💰 Выгодная сделка",
    "arbitrage": "🔄 Арбитраж",
    "trend_change": "📊 Изменение тренда",
    "buy_intent": "🛒 Намерение купить",
    "buy_success": "✅ Успешная покупка",
    "buy_failed": "❌ Ошибка покупки",
    "sell_success": "✅ Успешная продажа",
    "sell_failed": "❌ Ошибка продажи",
    "critical_shutdown": "🛑 Критическая остановка",
}

# TTL кэша цен в секундах
_PRICE_CACHE_TTL: Final[int] = 300  # 5 минут

# Настройки по умолчанию для пользователей
DEFAULT_USER_SETTINGS: Final[dict[str, object]] = {
    "enabled": True,
    "language": "ru",
    "min_interval": 300,  # 5 минут между уведомлениями
    "quiet_hours": {"start": 23, "end": 7},  # Тихие часы
    "max_alerts_per_day": 50,
}

# Приоритеты уведомлений
NOTIFICATION_PRIORITIES: Final[dict[str, int]] = {
    "critical_shutdown": 100,
    "buy_success": 90,
    "buy_failed": 90,
    "sell_success": 85,
    "sell_failed": 85,
    "buy_intent": 80,
    "arbitrage": 70,
    "good_deal": 60,
    "price_drop": 50,
    "price_rise": 50,
    "volume_increase": 40,
    "trend_change": 30,
}

__all__ = [
    "DEFAULT_USER_SETTINGS",
    "NOTIFICATION_PRIORITIES",
    "NOTIFICATION_TYPES",
    "_PRICE_CACHE_TTL",
]

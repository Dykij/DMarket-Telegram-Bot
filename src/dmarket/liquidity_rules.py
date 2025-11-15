"""Правила и константы для анализа ликвидности предметов."""

from dataclasses import dataclass


@dataclass
class LiquidityRules:
    """Правила оценки ликвидности предметов."""

    # Минимальное количество продаж в неделю для ликвидного предмета
    min_sales_per_week: float = 10.0

    # Максимальное время до продажи (дни) для ликвидного предмета
    max_time_to_sell_days: float = 7.0

    # Максимальное количество активных предложений
    # (больше = перенасыщение рынка)
    max_active_offers: int = 50

    # Минимальная стабильность цены (0-1)
    # (ниже = слишком волатильно)
    min_price_stability: float = 0.85

    # Минимальный liquidity score для покупки
    min_liquidity_score: float = 60.0


# Предустановленные профили правил для разных стратегий
CONSERVATIVE_RULES = LiquidityRules(
    min_sales_per_week=15.0,
    max_time_to_sell_days=5.0,
    max_active_offers=30,
    min_price_stability=0.90,
    min_liquidity_score=70.0,
)

BALANCED_RULES = LiquidityRules(
    min_sales_per_week=10.0,
    max_time_to_sell_days=7.0,
    max_active_offers=50,
    min_price_stability=0.85,
    min_liquidity_score=60.0,
)

AGGRESSIVE_RULES = LiquidityRules(
    min_sales_per_week=5.0,
    max_time_to_sell_days=10.0,
    max_active_offers=70,
    min_price_stability=0.75,
    min_liquidity_score=50.0,
)


# Веса для расчета liquidity score
LIQUIDITY_SCORE_WEIGHTS = {
    "sales_volume": 0.30,  # 30% - объем продаж
    "time_to_sell": 0.25,  # 25% - скорость продажи
    "price_stability": 0.20,  # 20% - стабильность цены
    "demand_supply": 0.15,  # 15% - соотношение спроса/предложения
    "market_depth": 0.10,  # 10% - глубина рынка (объем торгов)
}


# Пороги для категоризации ликвидности
LIQUIDITY_THRESHOLDS = {
    "very_high": 80.0,  # 🟢 Очень высокая ликвидность
    "high": 60.0,  # 🟡 Высокая ликвидность
    "medium": 40.0,  # 🟠 Средняя ликвидность
    "low": 20.0,  # 🔴 Низкая ликвидность
    "very_low": 0.0,  # ⚫ Очень низкая ликвидность
}


# Рекомендации для разных уровней ликвидности
LIQUIDITY_RECOMMENDATIONS = {
    "very_high": ("✅ Отличный выбор! Предмет быстро продается и имеет стабильный спрос."),
    "high": ("✅ Хороший выбор! Предмет имеет достаточную ликвидность для безопасной торговли."),
    "medium": ("⚠️ Осторожно! Предмет может продаваться медленнее ожидаемого."),
    "low": ("❌ Не рекомендуется! Низкая ликвидность, высокий риск долгой продажи."),
    "very_low": ("❌ Избегать! Предмет практически неликвиден, очень высокий риск."),
}


def get_liquidity_category(liquidity_score: float) -> str:
    """Получить категорию ликвидности по score.

    Args:
        liquidity_score: Liquidity score (0-100)

    Returns:
        Категория ликвидности (very_high, high, medium, low, very_low)
    """
    if liquidity_score >= LIQUIDITY_THRESHOLDS["very_high"]:
        return "very_high"
    if liquidity_score >= LIQUIDITY_THRESHOLDS["high"]:
        return "high"
    if liquidity_score >= LIQUIDITY_THRESHOLDS["medium"]:
        return "medium"
    if liquidity_score >= LIQUIDITY_THRESHOLDS["low"]:
        return "low"
    return "very_low"


def get_liquidity_recommendation(liquidity_score: float) -> str:
    """Получить рекомендацию по ликвидности.

    Args:
        liquidity_score: Liquidity score (0-100)

    Returns:
        Текстовая рекомендация
    """
    category = get_liquidity_category(liquidity_score)
    return LIQUIDITY_RECOMMENDATIONS[category]

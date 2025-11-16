"""Тесты для модуля liquidity_rules."""

import pytest

from src.dmarket.liquidity_rules import (
    AGGRESSIVE_RULES,
    BALANCED_RULES,
    CONSERVATIVE_RULES,
    LIQUIDITY_RECOMMENDATIONS,
    LIQUIDITY_SCORE_WEIGHTS,
    LIQUIDITY_THRESHOLDS,
    LiquidityRules,
    get_liquidity_category,
    get_liquidity_recommendation,
)


class TestLiquidityRules:
    """Тесты для класса LiquidityRules."""

    def test_default_initialization(self):
        """Тест создания LiquidityRules с параметрами по умолчанию."""
        rules = LiquidityRules()

        assert rules.min_sales_per_week == 10.0
        assert rules.max_time_to_sell_days == 7.0
        assert rules.max_active_offers == 50
        assert rules.min_price_stability == 0.85
        assert rules.min_liquidity_score == 60.0

    def test_custom_initialization(self):
        """Тест создания LiquidityRules с кастомными параметрами."""
        rules = LiquidityRules(
            min_sales_per_week=20.0,
            max_time_to_sell_days=3.0,
            max_active_offers=100,
            min_price_stability=0.95,
            min_liquidity_score=75.0,
        )

        assert rules.min_sales_per_week == 20.0
        assert rules.max_time_to_sell_days == 3.0
        assert rules.max_active_offers == 100
        assert rules.min_price_stability == 0.95
        assert rules.min_liquidity_score == 75.0


class TestPredefinedRules:
    """Тесты для предустановленных профилей правил."""

    def test_conservative_rules(self):
        """Тест консервативных правил."""
        assert CONSERVATIVE_RULES.min_sales_per_week == 15.0
        assert CONSERVATIVE_RULES.max_time_to_sell_days == 5.0
        assert CONSERVATIVE_RULES.max_active_offers == 30
        assert CONSERVATIVE_RULES.min_price_stability == 0.90
        assert CONSERVATIVE_RULES.min_liquidity_score == 70.0

    def test_balanced_rules(self):
        """Тест сбалансированных правил."""
        assert BALANCED_RULES.min_sales_per_week == 10.0
        assert BALANCED_RULES.max_time_to_sell_days == 7.0
        assert BALANCED_RULES.max_active_offers == 50
        assert BALANCED_RULES.min_price_stability == 0.85
        assert BALANCED_RULES.min_liquidity_score == 60.0

    def test_aggressive_rules(self):
        """Тест агрессивных правил."""
        assert AGGRESSIVE_RULES.min_sales_per_week == 5.0
        assert AGGRESSIVE_RULES.max_time_to_sell_days == 10.0
        assert AGGRESSIVE_RULES.max_active_offers == 70
        assert AGGRESSIVE_RULES.min_price_stability == 0.75
        assert AGGRESSIVE_RULES.min_liquidity_score == 50.0


class TestLiquidityScoreWeights:
    """Тесты для весов liquidity score."""

    def test_weights_sum_to_one(self):
        """Проверка что сумма весов равна 1.0."""
        total_weight = sum(LIQUIDITY_SCORE_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01  # Допускаем погрешность округления

    def test_all_weights_positive(self):
        """Проверка что все веса положительные."""
        for weight in LIQUIDITY_SCORE_WEIGHTS.values():
            assert weight > 0

    def test_weights_structure(self):
        """Проверка наличия всех необходимых весов."""
        required_keys = {
            "sales_volume",
            "time_to_sell",
            "price_stability",
            "demand_supply",
            "market_depth",
        }
        assert set(LIQUIDITY_SCORE_WEIGHTS.keys()) == required_keys


class TestLiquidityThresholds:
    """Тесты для порогов ликвидности."""

    def test_thresholds_descending_order(self):
        """Проверка что пороги расположены в порядке убывания."""
        thresholds = [
            LIQUIDITY_THRESHOLDS["very_high"],
            LIQUIDITY_THRESHOLDS["high"],
            LIQUIDITY_THRESHOLDS["medium"],
            LIQUIDITY_THRESHOLDS["low"],
            LIQUIDITY_THRESHOLDS["very_low"],
        ]

        for i in range(len(thresholds) - 1):
            assert thresholds[i] > thresholds[i + 1]

    def test_thresholds_range(self):
        """Проверка что пороги находятся в разумных пределах."""
        for threshold in LIQUIDITY_THRESHOLDS.values():
            assert 0 <= threshold <= 100


class TestGetLiquidityCategory:
    """Тесты для функции get_liquidity_category."""

    def test_very_high_liquidity(self):
        """Тест категории very_high."""
        assert get_liquidity_category(95.0) == "very_high"
        assert get_liquidity_category(80.0) == "very_high"

    def test_high_liquidity(self):
        """Тест категории high."""
        assert get_liquidity_category(75.0) == "high"
        assert get_liquidity_category(60.0) == "high"

    def test_medium_liquidity(self):
        """Тест категории medium."""
        assert get_liquidity_category(55.0) == "medium"
        assert get_liquidity_category(40.0) == "medium"

    def test_low_liquidity(self):
        """Тест категории low."""
        assert get_liquidity_category(35.0) == "low"
        assert get_liquidity_category(20.0) == "low"

    def test_very_low_liquidity(self):
        """Тест категории very_low."""
        assert get_liquidity_category(15.0) == "very_low"
        assert get_liquidity_category(0.0) == "very_low"

    def test_boundary_values(self):
        """Тест граничных значений."""
        # Граница very_high/high
        assert get_liquidity_category(79.99) == "high"
        assert get_liquidity_category(80.0) == "very_high"

        # Граница high/medium
        assert get_liquidity_category(59.99) == "medium"
        assert get_liquidity_category(60.0) == "high"


class TestGetLiquidityRecommendation:
    """Тесты для функции get_liquidity_recommendation."""

    def test_very_high_recommendation(self):
        """Тест рекомендации для very_high ликвидности."""
        recommendation = get_liquidity_recommendation(90.0)
        assert "✅" in recommendation
        assert "Отличный выбор" in recommendation

    def test_high_recommendation(self):
        """Тест рекомендации для high ликвидности."""
        recommendation = get_liquidity_recommendation(70.0)
        assert "✅" in recommendation
        assert "Хороший выбор" in recommendation

    def test_medium_recommendation(self):
        """Тест рекомендации для medium ликвидности."""
        recommendation = get_liquidity_recommendation(50.0)
        assert "⚠️" in recommendation
        assert "Осторожно" in recommendation

    def test_low_recommendation(self):
        """Тест рекомендации для low ликвидности."""
        recommendation = get_liquidity_recommendation(30.0)
        assert "❌" in recommendation
        assert "Не рекомендуется" in recommendation

    def test_very_low_recommendation(self):
        """Тест рекомендации для very_low ликвидности."""
        recommendation = get_liquidity_recommendation(10.0)
        assert "❌" in recommendation
        assert "Избегать" in recommendation

    def test_all_recommendations_have_icons(self):
        """Проверка что все рекомендации содержат иконки."""
        for recommendation in LIQUIDITY_RECOMMENDATIONS.values():
            # Проверяем наличие хотя бы одной эмодзи
            assert any(char in recommendation for char in ["✅", "⚠️", "❌"])

    def test_recommendations_not_empty(self):
        """Проверка что все рекомендации не пустые."""
        for category in ["very_high", "high", "medium", "low", "very_low"]:
            recommendation = get_liquidity_recommendation(
                LIQUIDITY_THRESHOLDS[category],
            )
            assert len(recommendation) > 0
            assert isinstance(recommendation, str)


class TestLiquidityRulesIntegration:
    """Интеграционные тесты для работы с правилами ликвидности."""

    def test_conservative_vs_aggressive_comparison(self):
        """Сравнение консервативных и агрессивных правил."""
        # Консервативные правила должны быть строже
        assert CONSERVATIVE_RULES.min_sales_per_week > AGGRESSIVE_RULES.min_sales_per_week
        assert CONSERVATIVE_RULES.max_time_to_sell_days < AGGRESSIVE_RULES.max_time_to_sell_days
        assert CONSERVATIVE_RULES.max_active_offers < AGGRESSIVE_RULES.max_active_offers
        assert CONSERVATIVE_RULES.min_price_stability > AGGRESSIVE_RULES.min_price_stability
        assert CONSERVATIVE_RULES.min_liquidity_score > AGGRESSIVE_RULES.min_liquidity_score

    def test_balanced_between_conservative_and_aggressive(self):
        """Проверка что balanced правила находятся между conservative и aggressive."""
        # Проверяем min_sales_per_week
        assert AGGRESSIVE_RULES.min_sales_per_week <= BALANCED_RULES.min_sales_per_week
        assert BALANCED_RULES.min_sales_per_week <= CONSERVATIVE_RULES.min_sales_per_week

        # Проверяем min_liquidity_score
        assert AGGRESSIVE_RULES.min_liquidity_score <= BALANCED_RULES.min_liquidity_score
        assert BALANCED_RULES.min_liquidity_score <= CONSERVATIVE_RULES.min_liquidity_score

    @pytest.mark.parametrize(
        "score,expected_category",
        [
            (100, "very_high"),
            (85, "very_high"),
            (75, "high"),
            (65, "high"),
            (50, "medium"),
            (45, "medium"),
            (30, "low"),
            (25, "low"),
            (10, "very_low"),
            (0, "very_low"),
        ],
    )
    def test_category_score_mapping(self, score, expected_category):
        """Параметризованный тест для проверки соответствия score и категории."""
        assert get_liquidity_category(score) == expected_category


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_negative_score(self):
        """Тест отрицательного score."""
        # Функция должна обрабатывать отрицательные значения
        category = get_liquidity_category(-10.0)
        assert category == "very_low"

    def test_extremely_high_score(self):
        """Тест очень высокого score."""
        # Функция должна обрабатывать значения выше 100
        category = get_liquidity_category(150.0)
        assert category == "very_high"

    def test_zero_values_in_rules(self):
        """Тест создания правил с нулевыми значениями."""
        rules = LiquidityRules(
            min_sales_per_week=0.0,
            max_time_to_sell_days=0.0,
            max_active_offers=0,
            min_price_stability=0.0,
            min_liquidity_score=0.0,
        )

        assert rules.min_sales_per_week == 0.0
        assert rules.max_time_to_sell_days == 0.0
        assert rules.max_active_offers == 0
        assert rules.min_price_stability == 0.0
        assert rules.min_liquidity_score == 0.0

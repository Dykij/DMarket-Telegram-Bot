"""Тесты для модуля formatters."""

from src.telegram_bot.utils.formatters import (
    format_aggregated_prices,
    format_market_depth,
    format_target_competition_analysis,
    format_target_item,
)


# === Тесты для format_target_item ===


def test_format_target_item_active():
    """Тест форматирования активного таргета."""
    target = {
        "Title": "AK-47 | Redline (Field-Tested)",
        "Price": {"Amount": 1250},
        "Amount": 5,
        "Status": "TargetStatusActive",
        "TargetID": "target_123",
    }

    result = format_target_item(target)

    assert "✅" in result or "Активен" in result
    assert "AK-47" in result
    assert "$12.50" in result


def test_format_target_item_inactive():
    """Тест форматирования неактивного таргета."""
    target = {
        "Title": "AWP | Asiimov (Field-Tested)",
        "Price": {"Amount": 2500},
        "Amount": 1,
        "Status": "TargetStatusInactive",
    }

    result = format_target_item(target)

    assert "❌" in result or "Неактивен" in result
    assert "AWP" in result
    assert "$25.00" in result


def test_format_target_item_created():
    """Тест форматирования созданного таргета."""
    target = {
        "Title": "M4A4 | Howl (Minimal Wear)",
        "Price": {"Amount": 100000},
        "Amount": 1,
        "Status": "Created",
    }

    result = format_target_item(target)

    assert "🆕" in result or "Создан" in result
    assert "M4A4" in result


def test_format_target_item_none():
    """Тест обработки пустого словаря."""
    result = format_target_item({})

    assert result is not None
    assert len(result) > 0
    assert "Неизвестный предмет" in result


# === Тесты для format_target_competition_analysis ===


def test_format_target_competition_analysis_low():
    """Тест форматирования с низкой конкуренцией."""
    analysis = {
        "competition_level": "low",
        "total_buy_orders": 3,
        "highest_buy_order_price": 1200,
        "recommended_price": 1150,
        "strategy": "Установить цену немного выше заявок",
        "existing_orders": [
            {"price": 1200, "amount": 2},
            {"price": 1150, "amount": 1},
        ],
    }

    result = format_target_competition_analysis(analysis, "AK-47 | Redline (FT)")

    assert "🟢" in result or "Низкая" in result
    assert "3" in result
    assert "AK-47" in result


def test_format_target_competition_analysis_medium():
    """Тест форматирования со средней конкуренцией."""
    analysis = {
        "competition_level": "medium",
        "total_buy_orders": 15,
        "highest_buy_order_price": 2500,
        "recommended_price": 2400,
        "strategy": "aggressive",
        "existing_orders": [{"price": 2500, "amount": 5}],
    }

    result = format_target_competition_analysis(analysis, "Test Item")

    assert "🟡" in result or "Средняя" in result


def test_format_target_competition_analysis_high():
    """Тест форматирования с высокой конкуренцией."""
    analysis = {
        "competition_level": "high",
        "total_buy_orders": 50,
        "highest_buy_order_price": 100000,
        "recommended_price": 98000,
        "strategy": "conservative",
        "existing_orders": [{"price": 100000, "amount": 10}],
    }

    result = format_target_competition_analysis(analysis, "M4A4 | Howl")

    assert "🔴" in result or "Высокая" in result


def test_format_target_competition_analysis_none():
    """Тест обработки None."""
    result = format_target_competition_analysis(None, "Test")
    assert result is not None
    assert isinstance(result, str)


# === Тесты для format_aggregated_prices ===


def test_format_aggregated_prices_with_data():
    """Тест форматирования с данными."""
    prices = [
        {
            "title": "AK-47 | Redline (FT)",
            "offer_price": 1200,
            "order_price": 1100,
            "offer_count": 25,
            "order_count": 15,
        },
        {
            "title": "AWP | Asiimov (FT)",
            "offer_price": 5100,
            "order_price": 4900,
            "offer_count": 10,
            "order_count": 8,
        },
    ]

    result = format_aggregated_prices(prices)

    assert "AK-47 | Redline" in result
    assert "AWP | Asiimov" in result
    assert result is not None
    assert len(result) > 0


def test_format_aggregated_prices_empty():
    """Тест форматирования с пустым списком."""
    result = format_aggregated_prices([])

    assert result is not None
    assert len(result) > 0


def test_format_aggregated_prices_none():
    """Тест обработки None."""
    result = format_aggregated_prices(None)
    assert result is not None


# === Тесты для format_market_depth ===


def test_format_market_depth_excellent():
    """Тест с отличным здоровьем рынка."""
    depth_data = {
        "summary": {
            "market_health": "excellent",
            "average_liquidity_score": 85.5,
            "average_spread_percent": 2.5,
            "high_liquidity_items": 25,
            "arbitrage_opportunities": 10,
        },
        "items": [],
    }

    result = format_market_depth(depth_data)

    assert "85" in result
    assert "2.5" in result or "2.50" in result


def test_format_market_depth_good():
    """Тест с хорошим здоровьем рынка."""
    depth_data = {
        "market_health": "good",
        "average_liquidity": 70.0,
        "average_spread": 3.5,
    }

    result = format_market_depth(depth_data)

    assert result is not None
    assert len(result) > 0


def test_format_market_depth_moderate():
    """Тест с умеренным здоровьем рынка."""
    depth_data = {
        "market_health": "moderate",
        "average_liquidity": 50.0,
        "average_spread": 5.0,
    }

    result = format_market_depth(depth_data)

    assert result is not None


def test_format_market_depth_poor():
    """Тест с плохим здоровьем рынка."""
    depth_data = {
        "market_health": "poor",
        "average_liquidity": 25.0,
        "average_spread": 10.0,
    }

    result = format_market_depth(depth_data)

    assert result is not None


def test_format_market_depth_none():
    """Тест обработки None."""
    result = format_market_depth(None)
    assert result is not None


# === Интеграционные тесты ===


def test_all_formatters_return_strings():
    """Тест что все форматтеры возвращают строки."""
    target = {
        "title": "Test",
        "price": 1000,
        "amount": 1,
        "status": "active",
    }
    assert isinstance(format_target_item(target), str)

    analysis = {"competition_level": "low", "existing_orders": []}
    assert isinstance(format_target_competition_analysis(analysis, "Test"), str)

    prices = [{"title": "Test", "offer_price": 100, "order_price": 90}]
    assert isinstance(format_aggregated_prices(prices), str)

    depth = {"market_health": "good", "average_liquidity": 75.0}
    assert isinstance(format_market_depth(depth), str)

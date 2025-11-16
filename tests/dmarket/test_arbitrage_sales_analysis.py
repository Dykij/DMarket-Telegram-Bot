"""Модуль тестирования анализа продаж для арбитража.

Тестирует модуль src/dmarket/arbitrage_sales_analysis.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.arbitrage_sales_analysis import SalesAnalyzer


# ======================== Фикстуры ========================


@pytest.fixture()
def mock_dmarket_api():
    """Создать мок DMarket API клиента."""
    api = MagicMock()
    api.get_sales_history = AsyncMock()
    api.get_market_items = AsyncMock()
    api.get_aggregated_prices = AsyncMock()
    api._request = AsyncMock()  # Мок для внутреннего метода _request
    return api


@pytest.fixture()
def sales_analyzer(mock_dmarket_api):
    """Создать экземпляр SalesAnalyzer с моком API."""
    return SalesAnalyzer(mock_dmarket_api)


@pytest.fixture()
def sample_sales_data():
    """Пример данных о продажах предмета."""
    return {
        "sales": [
            {
                "date": 1699876543,
                "price": {"amount": 1200, "currency": "USD"},
            },
            {
                "date": 1699790143,
                "price": {"amount": 1250, "currency": "USD"},
            },
            {
                "date": 1699703743,
                "price": {"amount": 1180, "currency": "USD"},
            },
            {
                "date": 1699617343,
                "price": {"amount": 1230, "currency": "USD"},
            },
            {
                "date": 1699530943,
                "price": {"amount": 1220, "currency": "USD"},
            },
        ],
    }


@pytest.fixture()
def sample_market_items():
    """Пример предметов с рынка."""
    return {
        "items": [
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"amount": 1250, "currency": "USD"},
                "itemId": "item_1",
            },
            {
                "title": "AWP | Asiimov (Field-Tested)",
                "price": {"amount": 5000, "currency": "USD"},
                "itemId": "item_2",
            },
        ],
    }


@pytest.fixture()
def sample_tf2_sales_data():
    """Пример данных о продажах TF2 предмета."""
    return {
        "sales": [
            {
                "date": 1699876543,
                "price": {"amount": 8500, "currency": "USD"},
            },
            {
                "date": 1699790143,
                "price": {"amount": 8800, "currency": "USD"},
            },
            {
                "date": 1699703743,
                "price": {"amount": 8200, "currency": "USD"},
            },
            {
                "date": 1699617343,
                "price": {"amount": 8600, "currency": "USD"},
            },
            {
                "date": 1699530943,
                "price": {"amount": 8400, "currency": "USD"},
            },
        ],
    }


@pytest.fixture()
def sample_rust_sales_data():
    """Пример данных о продажах Rust предмета."""
    return {
        "sales": [
            {
                "date": 1699876543,
                "price": {"amount": 3200, "currency": "USD"},
            },
            {
                "date": 1699790143,
                "price": {"amount": 3400, "currency": "USD"},
            },
            {
                "date": 1699703743,
                "price": {"amount": 3100, "currency": "USD"},
            },
            {
                "date": 1699617343,
                "price": {"amount": 3300, "currency": "USD"},
            },
            {
                "date": 1699530943,
                "price": {"amount": 3250, "currency": "USD"},
            },
        ],
    }


# ======================== Тесты get_item_sales_history ========================


@pytest.mark.asyncio()
async def test_get_item_sales_history_success(sales_analyzer, mock_dmarket_api, sample_sales_data):
    """Тест успешного получения истории продаж предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.get_item_sales_history(
        item_name="AK-47 | Redline (Field-Tested)",
        game="csgo",
        days=7,
    )

    # Проверяем что API вызван с правильными параметрами
    mock_dmarket_api.get_sales_history.assert_called_once_with(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        days=7,
    )

    # Проверяем результат
    assert result is not None
    assert "sales" in result
    assert len(result["sales"]) == 5


@pytest.mark.asyncio()
async def test_get_item_sales_history_no_sales(sales_analyzer, mock_dmarket_api):
    """Тест когда нет истории продаж."""
    mock_dmarket_api.get_sales_history.return_value = {"sales": []}

    result = await sales_analyzer.get_item_sales_history(
        game="csgo",
        title="Nonexistent Item",
    )

    assert result["sales"] == []


@pytest.mark.asyncio()
async def test_get_item_sales_history_api_error(sales_analyzer, mock_dmarket_api):
    """Тест обработки ошибки API."""
    mock_dmarket_api.get_sales_history.side_effect = Exception("API Error")

    result = await sales_analyzer.get_item_sales_history(
        game="csgo",
        title="Test Item",
    )

    # При ошибке должны вернуться пустые данные
    assert result == {"sales": []}


# ======================== Тесты analyze_sales_volume ========================


@pytest.mark.asyncio()
async def test_analyze_sales_volume_success(sales_analyzer, mock_dmarket_api, sample_sales_data):
    """Тест успешного анализа объема продаж."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.analyze_sales_volume(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        days=7,
    )

    # Проверяем структуру результата
    assert "total_sales" in result
    assert "daily_average" in result
    assert "liquidity_score" in result
    assert "price_range" in result

    # Проверяем значения
    assert result["total_sales"] == 5
    assert result["daily_average"] > 0
    assert "min" in result["price_range"]
    assert "max" in result["price_range"]


@pytest.mark.asyncio()
async def test_analyze_sales_volume_no_sales(sales_analyzer, mock_dmarket_api):
    """Тест анализа при отсутствии продаж."""
    mock_dmarket_api.get_sales_history.return_value = {"sales": []}

    result = await sales_analyzer.analyze_sales_volume(
        game="csgo",
        title="Rare Item",
    )

    # Проверяем что возвращаются нулевые значения
    assert result["total_sales"] == 0
    assert result["daily_average"] == 0
    assert result["liquidity_score"] == "low"


@pytest.mark.asyncio()
async def test_analyze_sales_volume_high_liquidity(sales_analyzer, mock_dmarket_api):
    """Тест определения высокой ликвидности."""
    # Создаем данные с большим количеством продаж
    many_sales = {
        "sales": [{"date": 1699876543 - i * 3600, "price": {"amount": 1200}} for i in range(50)],
    }
    mock_dmarket_api.get_sales_history.return_value = many_sales

    result = await sales_analyzer.analyze_sales_volume(
        game="csgo",
        title="Popular Item",
    )

    # Проверяем высокую ликвидность
    assert result["liquidity_score"] in ["high", "very_high"]


# ======================== Тесты estimate_time_to_sell ========================


@pytest.mark.asyncio()
async def test_estimate_time_to_sell_success(sales_analyzer, mock_dmarket_api, sample_sales_data):
    """Тест успешной оценки времени продажи."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.estimate_time_to_sell(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        current_price=1250,
    )

    # Проверяем структуру
    assert "estimated_hours" in result
    assert "confidence" in result
    assert "recommendation" in result

    # Проверяем значения
    assert result["estimated_hours"] >= 0
    assert result["confidence"] in ["low", "medium", "high"]


@pytest.mark.asyncio()
async def test_estimate_time_to_sell_overpriced(
    sales_analyzer, mock_dmarket_api, sample_sales_data
):
    """Тест оценки для завышенной цены."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.estimate_time_to_sell(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        current_price=5000,  # Значительно выше средней
    )

    # Время продажи должно быть больше
    assert result["estimated_hours"] > 24
    assert "overpriced" in result["recommendation"].lower()


@pytest.mark.asyncio()
async def test_estimate_time_to_sell_underpriced(
    sales_analyzer, mock_dmarket_api, sample_sales_data
):
    """Тест оценки для заниженной цены."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.estimate_time_to_sell(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        current_price=500,  # Значительно ниже средней
    )

    # Должна продаться быстро
    assert result["estimated_hours"] < 24
    assert result["confidence"] == "high"


# ======================== Тесты analyze_price_trends ========================


@pytest.mark.asyncio()
async def test_analyze_price_trends_success(sales_analyzer, mock_dmarket_api, sample_sales_data):
    """Тест успешного анализа трендов цен."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.analyze_price_trends(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
    )

    # Проверяем структуру
    assert "trend_direction" in result
    assert "price_change_percent" in result
    assert "volatility" in result
    assert "average_price" in result

    # Проверяем значения
    assert result["trend_direction"] in ["rising", "falling", "stable"]
    assert isinstance(result["price_change_percent"], float)


@pytest.mark.asyncio()
async def test_analyze_price_trends_rising(sales_analyzer, mock_dmarket_api):
    """Тест обнаружения растущего тренда."""
    rising_prices = {
        "sales": [
            {"date": 1699876543, "price": {"amount": 1500}},
            {"date": 1699790143, "price": {"amount": 1400}},
            {"date": 1699703743, "price": {"amount": 1300}},
            {"date": 1699617343, "price": {"amount": 1200}},
            {"date": 1699530943, "price": {"amount": 1100}},
        ],
    }
    mock_dmarket_api.get_sales_history.return_value = rising_prices

    result = await sales_analyzer.analyze_price_trends(
        game="csgo",
        title="Rising Item",
    )

    assert result["trend_direction"] == "rising"
    assert result["price_change_percent"] > 0


@pytest.mark.asyncio()
async def test_analyze_price_trends_falling(sales_analyzer, mock_dmarket_api):
    """Тест обнаружения падающего тренда."""
    falling_prices = {
        "sales": [
            {"date": 1699876543, "price": {"amount": 1000}},
            {"date": 1699790143, "price": {"amount": 1100}},
            {"date": 1699703743, "price": {"amount": 1200}},
            {"date": 1699617343, "price": {"amount": 1300}},
            {"date": 1699530943, "price": {"amount": 1400}},
        ],
    }
    mock_dmarket_api.get_sales_history.return_value = falling_prices

    result = await sales_analyzer.analyze_price_trends(
        game="csgo",
        title="Falling Item",
    )

    assert result["trend_direction"] == "falling"
    assert result["price_change_percent"] < 0


@pytest.mark.asyncio()
async def test_analyze_price_trends_stable(sales_analyzer, mock_dmarket_api):
    """Тест обнаружения стабильных цен."""
    stable_prices = {
        "sales": [
            {"date": 1699876543, "price": {"amount": 1200}},
            {"date": 1699790143, "price": {"amount": 1210}},
            {"date": 1699703743, "price": {"amount": 1195}},
            {"date": 1699617343, "price": {"amount": 1205}},
            {"date": 1699530943, "price": {"amount": 1198}},
        ],
    }
    mock_dmarket_api.get_sales_history.return_value = stable_prices

    result = await sales_analyzer.analyze_price_trends(
        game="csgo",
        title="Stable Item",
    )

    assert result["trend_direction"] == "stable"
    assert abs(result["price_change_percent"]) < 3


# ===================== Тесты evaluate_arbitrage_potential =====================


@pytest.mark.asyncio()
async def test_evaluate_arbitrage_potential_success(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест успешной оценки потенциала арбитража."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    result = await sales_analyzer.evaluate_arbitrage_potential(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        buy_price=1200,
        sell_price=1400,
    )

    # Проверяем структуру
    assert "expected_profit" in result
    assert "profit_percentage" in result
    assert "risk_level" in result
    assert "recommendation" in result
    assert "estimated_sell_time_hours" in result

    # Проверяем значения
    assert result["expected_profit"] > 0
    assert result["risk_level"] in ["low", "medium", "high"]


@pytest.mark.asyncio()
async def test_evaluate_arbitrage_potential_unprofitable(
    sales_analyzer, mock_dmarket_api, sample_sales_data
):
    """Тест оценки для невыгодного арбитража."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.evaluate_arbitrage_potential(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        buy_price=1400,
        sell_price=1300,  # Убыток
    )

    # Должна быть отрицательная прибыль
    assert result["expected_profit"] < 0
    assert "not recommended" in result["recommendation"].lower()


@pytest.mark.asyncio()
async def test_evaluate_arbitrage_potential_high_profit(
    sales_analyzer, mock_dmarket_api, sample_sales_data
):
    """Тест оценки высокоприбыльного арбитража."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data

    result = await sales_analyzer.evaluate_arbitrage_potential(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        buy_price=1000,
        sell_price=1500,  # 50% прибыль
    )

    # Высокая прибыль
    assert result["profit_percentage"] > 40
    assert result["risk_level"] == "low"
    assert "recommended" in result["recommendation"].lower()


# ======================== Тесты batch_analyze_items ========================


@pytest.mark.asyncio()
async def test_batch_analyze_items_success(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест пакетного анализа нескольких предметов."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    items_to_analyze = [
        {"title": "AK-47 | Redline (Field-Tested)", "buy_price": 1200},
        {"title": "AWP | Asiimov (Field-Tested)", "buy_price": 5000},
    ]

    results = await sales_analyzer.batch_analyze_items(
        game="csgo",
        items=items_to_analyze,
    )

    # Проверяем количество результатов
    assert len(results) == 2

    # Проверяем структуру каждого результата
    for result in results:
        assert "title" in result
        assert "sales_volume" in result
        assert "price_trend" in result
        assert "liquidity" in result


@pytest.mark.asyncio()
async def test_batch_analyze_items_empty_list(sales_analyzer):
    """Тест пакетного анализа с пустым списком."""
    results = await sales_analyzer.batch_analyze_items(
        game="csgo",
        items=[],
    )

    assert results == []


@pytest.mark.asyncio()
async def test_batch_analyze_items_with_errors(sales_analyzer, mock_dmarket_api):
    """Тест пакетного анализа с ошибками для некоторых предметов."""
    # Первый запрос успешен, второй - ошибка
    mock_dmarket_api.get_sales_history.side_effect = [
        {"sales": [{"date": 1699876543, "price": {"amount": 1200}}]},
        Exception("API Error"),
    ]

    items_to_analyze = [
        {"title": "Item 1", "buy_price": 1200},
        {"title": "Item 2", "buy_price": 5000},
    ]

    results = await sales_analyzer.batch_analyze_items(
        game="csgo",
        items=items_to_analyze,
    )

    # Должен быть хотя бы один успешный результат
    assert len(results) >= 1


# =================== Тесты find_best_arbitrage_opportunities ===================


@pytest.mark.asyncio()
async def test_find_best_arbitrage_opportunities_success(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест поиска лучших арбитражных возможностей."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    results = await sales_analyzer.find_best_arbitrage_opportunities(
        game="csgo",
        min_profit_percent=5.0,
        max_risk_level="medium",
    )

    # Проверяем результаты
    assert isinstance(results, list)

    # Если есть результаты, проверяем структуру
    if results:
        assert "title" in results[0]
        assert "expected_profit" in results[0]
        assert "profit_percentage" in results[0]
        assert "risk_level" in results[0]


@pytest.mark.asyncio()
async def test_find_best_arbitrage_opportunities_sorted(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест сортировки результатов по прибыли."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    results = await sales_analyzer.find_best_arbitrage_opportunities(
        game="csgo",
    )

    # Проверяем что отсортировано по убыванию прибыли
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i]["profit_percentage"] >= results[i + 1]["profit_percentage"]


@pytest.mark.asyncio()
async def test_find_best_arbitrage_opportunities_filters(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест фильтрации по минимальной прибыли и уровню риска."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    results = await sales_analyzer.find_best_arbitrage_opportunities(
        game="csgo",
        min_profit_percent=10.0,
        max_risk_level="low",
    )

    # Проверяем фильтрацию
    for result in results:
        assert result["profit_percentage"] >= 10.0
        assert result["risk_level"] == "low"


@pytest.mark.asyncio()
async def test_find_best_arbitrage_opportunities_limit(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест ограничения количества результатов."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    results = await sales_analyzer.find_best_arbitrage_opportunities(
        game="csgo",
        limit=5,
    )

    # Проверяем что не больше лимита
    assert len(results) <= 5


# ======================== Интеграционные тесты ========================


@pytest.mark.asyncio()
async def test_full_analysis_workflow(
    sales_analyzer, mock_dmarket_api, sample_sales_data, sample_market_items
):
    """Тест полного цикла анализа предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_sales_data
    mock_dmarket_api.get_market_items.return_value = sample_market_items

    item_title = "AK-47 | Redline (Field-Tested)"

    # 1. Получить историю продаж
    history = await sales_analyzer.get_item_sales_history(
        game="csgo",
        title=item_title,
    )
    assert history is not None

    # 2. Анализ объема
    volume = await sales_analyzer.analyze_sales_volume(
        game="csgo",
        title=item_title,
    )
    assert "total_sales" in volume

    # 3. Анализ трендов
    trends = await sales_analyzer.analyze_price_trends(
        game="csgo",
        title=item_title,
    )
    assert "trend_direction" in trends

    # 4. Оценка времени продажи
    time_estimate = await sales_analyzer.estimate_time_to_sell(
        game="csgo",
        title=item_title,
        current_price=1250,
    )
    assert "estimated_hours" in time_estimate

    # 5. Оценка арбитража
    arbitrage = await sales_analyzer.evaluate_arbitrage_potential(
        game="csgo",
        title=item_title,
        buy_price=1200,
        sell_price=1400,
    )
    assert "expected_profit" in arbitrage


# ======================== Тесты для TF2 ========================


@pytest.mark.asyncio()
async def test_get_item_sales_history_tf2(sales_analyzer, mock_dmarket_api, sample_tf2_sales_data):
    """Тест получения истории продаж для TF2 предмета."""
    # Мокаем get_market_items для получения item_id
    mock_dmarket_api.get_market_items.return_value = {
        "items": [{"itemId": "tf2_item_1", "title": "Unusual Team Captain"}]
    }
    # Мокаем _request для возврата данных о продажах
    mock_dmarket_api._request.return_value = sample_tf2_sales_data

    result = await sales_analyzer.get_item_sales_history(
        item_name="Unusual Team Captain",
        game="tf2",
    )

    # get_item_sales_history возвращает список продаж
    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio()
async def test_analyze_price_trends_tf2(sales_analyzer, mock_dmarket_api, sample_tf2_sales_data):
    """Тест анализа трендов цен TF2 предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_tf2_sales_data

    result = await sales_analyzer.analyze_price_trends(
        item_name="Unusual Team Captain",
        game="tf2",
    )

    assert result is not None
    # Проверяем наличие ключа 'trend' вместо 'trend_direction'
    assert "trend" in result
    assert "price_change_percent" in result or result["price_change_percent"] is None


@pytest.mark.asyncio()
async def test_estimate_time_to_sell_tf2(sales_analyzer, mock_dmarket_api, sample_tf2_sales_data):
    """Тест оценки времени продажи TF2 предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_tf2_sales_data

    result = await sales_analyzer.estimate_time_to_sell(
        item_name="Vintage Tyrolean",
        target_price=8500,  # target_price, а не current_price
        game="tf2",
    )

    assert result is not None
    # Проверяем наличие ключа 'estimated_days' вместо 'estimated_hours'
    assert "estimated_days" in result or "message" in result


@pytest.mark.asyncio()
async def test_evaluate_arbitrage_potential_tf2(
    sales_analyzer, mock_dmarket_api, sample_tf2_sales_data
):
    """Тест оценки арбитража для TF2 предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_tf2_sales_data

    result = await sales_analyzer.evaluate_arbitrage_potential(
        item_name="Unusual Team Captain",
        game="tf2",
        buy_price=8000,  # Покупка за $80
        sell_price=9000,  # Продажа за $90
    )

    assert result is not None
    # Проверяем наличие ключа 'rating' вместо 'is_profitable'
    assert "rating" in result
    assert "profit_percent" in result
    # Профит 12.5% должен быть положительным
    assert result["profit_percent"] > 0


# ======================== Тесты для Rust ========================


@pytest.mark.asyncio()
async def test_get_item_sales_history_rust(
    sales_analyzer, mock_dmarket_api, sample_rust_sales_data
):
    """Тест получения истории продаж для Rust предмета."""
    # Мокаем get_market_items для получения item_id
    mock_dmarket_api.get_market_items.return_value = {
        "items": [{"itemId": "rust_item_1", "title": "Metal Facemask"}]
    }
    # Мокаем _request для возврата данных о продажах
    mock_dmarket_api._request.return_value = sample_rust_sales_data

    result = await sales_analyzer.get_item_sales_history(
        item_name="Metal Facemask",
        game="rust",
    )

    # get_item_sales_history возвращает список продаж
    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio()
async def test_analyze_price_trends_rust(sales_analyzer, mock_dmarket_api, sample_rust_sales_data):
    """Тест анализа трендов цен Rust предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_rust_sales_data

    result = await sales_analyzer.analyze_price_trends(
        item_name="Glowing Alien Relic Trophy",
        game="rust",
    )

    assert result is not None
    # Проверяем наличие ключа 'trend' вместо 'trend_direction'
    assert "trend" in result
    assert "price_change_percent" in result or result["price_change_percent"] is None


@pytest.mark.asyncio()
async def test_estimate_time_to_sell_rust(sales_analyzer, mock_dmarket_api, sample_rust_sales_data):
    """Тест оценки времени продажи Rust предмета."""
    # Мокаем get_market_items для получения item_id
    mock_dmarket_api.get_market_items.return_value = {
        "items": [{"itemId": "rust_item_1", "title": "Unique Burlap Headwrap"}]
    }
    mock_dmarket_api.get_sales_history.return_value = sample_rust_sales_data

    result = await sales_analyzer.estimate_time_to_sell(
        item_name="Unique Burlap Headwrap",
        target_price=3250,  # target_price, а не current_price
        game="rust",
    )

    assert result is not None
    # Проверяем наличие ключа 'estimated_days' вместо 'estimated_hours'
    assert "estimated_days" in result or "message" in result


@pytest.mark.asyncio()
async def test_evaluate_arbitrage_potential_rust(
    sales_analyzer, mock_dmarket_api, sample_rust_sales_data
):
    """Тест оценки арбитража для Rust предмета."""
    mock_dmarket_api.get_sales_history.return_value = sample_rust_sales_data

    result = await sales_analyzer.evaluate_arbitrage_potential(
        item_name="Glowing Alien Relic Trophy",
        game="rust",
        buy_price=3000,  # Покупка за $30
        sell_price=3500,  # Продажа за $35
    )

    assert result is not None
    # Проверяем наличие ключа 'rating' вместо 'is_profitable'
    assert "rating" in result
    assert "profit_percent" in result
    # Профит 16.67% должен быть положительным
    assert result["profit_percent"] > 0

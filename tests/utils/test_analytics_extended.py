"""Расширенное тестирование модуля аналитики.

Этот модуль содержит тесты для функциональности генерации графиков:
- ChartGenerator - создание различных графиков
- MarketAnalyzer - анализ рыночных данных
"""

import io
from datetime import datetime, timedelta

import pytest

from src.utils.analytics import ChartGenerator, MarketAnalyzer


# ==============================================================================
# ФИКСТУРЫ
# ==============================================================================


@pytest.fixture()
def sample_price_data():
    """Создает пример данных о ценах."""
    base_date = datetime.now()
    return [
        {
            "date": (base_date - timedelta(days=i)).isoformat(),
            "price": 100 + i * 5,
        }
        for i in range(10)
    ]


@pytest.fixture()
def sample_items_data():
    """Создает пример данных о предметах."""
    return [{"name": f"Item {i}", "price": 100 + i * 10} for i in range(5)]


@pytest.fixture()
def sample_arbitrage_data():
    """Создает пример данных об арбитраже."""
    return [
        {
            "title": f"Item {i}",
            "profit": 10 + i * 5,
            "profit_percentage": 10 + i * 2,
            "buy_price": 100,
            "sell_price": 110 + i * 5,
        }
        for i in range(5)
    ]


@pytest.fixture()
def chart_generator():
    """Создает экземпляр ChartGenerator."""
    return ChartGenerator(style="default", figsize=(10, 6))


@pytest.fixture()
def market_analyzer():
    """Создает экземпляр MarketAnalyzer."""
    return MarketAnalyzer()


# ==============================================================================
# ТЕСТЫ CHARTGENERATOR - ИНИЦИАЛИЗАЦИЯ
# ==============================================================================


def test_chart_generator_init_default():
    """Тест инициализации ChartGenerator с параметрами по умолчанию."""
    generator = ChartGenerator()

    assert generator.style == "default"
    assert generator.figsize == (12, 8)


def test_chart_generator_init_custom():
    """Тест инициализации ChartGenerator с кастомными параметрами."""
    generator = ChartGenerator(style="bmh", figsize=(10, 6))

    assert generator.style == "bmh"
    assert generator.figsize == (10, 6)


def test_chart_generator_init_invalid_style():
    """Тест инициализации с несуществующим стилем (должен использовать default)."""
    generator = ChartGenerator(style="nonexistent_style")

    # Должен быть создан, используя fallback
    assert generator.style == "nonexistent_style"
    assert generator.figsize == (12, 8)


# ==============================================================================
# ТЕСТЫ CREATE_PRICE_HISTORY_CHART
# ==============================================================================


def test_create_price_history_chart_basic(chart_generator, sample_price_data):
    """Тест создания базового графика истории цен."""
    result = chart_generator.create_price_history_chart(sample_price_data)

    assert isinstance(result, io.BytesIO)
    # Проверяем, что что-то записано (getvalue вместо tell, так как seek(0) сбрасывает позицию)
    assert len(result.getvalue()) > 0


def test_create_price_history_chart_empty_data(chart_generator):
    """Тест создания графика с пустыми данными."""
    result = chart_generator.create_price_history_chart([])

    # Должен вернуть BytesIO с сообщением об ошибке
    assert isinstance(result, io.BytesIO)


def test_create_price_history_chart_custom_title(chart_generator, sample_price_data):
    """Тест создания графика с кастомным заголовком."""
    title = "Custom Price Chart"
    result = chart_generator.create_price_history_chart(sample_price_data, title=title)

    assert isinstance(result, io.BytesIO)


def test_create_price_history_chart_custom_currency(chart_generator, sample_price_data):
    """Тест создания графика с кастомной валютой."""
    result = chart_generator.create_price_history_chart(sample_price_data, currency="EUR")

    assert isinstance(result, io.BytesIO)


# ==============================================================================
# ТЕСТЫ CREATE_MARKET_OVERVIEW_CHART
# ==============================================================================


def test_create_market_overview_chart_basic(chart_generator, sample_items_data):
    """Тест создания базового графика обзора рынка."""
    result = chart_generator.create_market_overview_chart(sample_items_data)

    assert isinstance(result, io.BytesIO)
    assert len(result.getvalue()) > 0


def test_create_market_overview_chart_empty(chart_generator):
    """Тест создания графика с пустыми данными."""
    result = chart_generator.create_market_overview_chart([])

    assert isinstance(result, io.BytesIO)


def test_create_market_overview_chart_custom_title(chart_generator, sample_items_data):
    """Тест создания графика с кастомным заголовком."""
    title = "Top Market Items"
    result = chart_generator.create_market_overview_chart(sample_items_data, title=title)

    assert isinstance(result, io.BytesIO)


def test_create_market_overview_chart_many_items(chart_generator):
    """Тест создания графика с большим количеством предметов."""
    items = [{"name": f"Item {i}", "price": 50 + i * 5} for i in range(20)]
    result = chart_generator.create_market_overview_chart(items)

    assert isinstance(result, io.BytesIO)


# ==============================================================================
# ТЕСТЫ CREATE_ARBITRAGE_OPPORTUNITIES_CHART
# ==============================================================================


def test_create_arbitrage_chart_basic(chart_generator, sample_arbitrage_data):
    """Тест создания базового графика арбитражных возможностей."""
    result = chart_generator.create_arbitrage_opportunities_chart(sample_arbitrage_data)

    assert isinstance(result, io.BytesIO)
    assert len(result.getvalue()) > 0


def test_create_arbitrage_chart_empty(chart_generator):
    """Тест создания графика с пустыми данными."""
    result = chart_generator.create_arbitrage_opportunities_chart([])

    assert isinstance(result, io.BytesIO)


def test_create_arbitrage_chart_custom_title(chart_generator, sample_arbitrage_data):
    """Тест создания графика с кастомным заголовком."""
    title = "Best Opportunities"
    result = chart_generator.create_arbitrage_opportunities_chart(
        sample_arbitrage_data, title=title
    )

    assert isinstance(result, io.BytesIO)


# ==============================================================================
# ТЕСТЫ MARKETANALYZER - ИНИЦИАЛИЗАЦИЯ
# ==============================================================================


def test_market_analyzer_init_default(market_analyzer):
    """Тест инициализации MarketAnalyzer."""
    assert market_analyzer is not None
    assert isinstance(market_analyzer, MarketAnalyzer)


# ==============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.parametrize(
    ("style", "figsize"),
    (
        ("default", (12, 8)),
        ("bmh", (10, 6)),
        ("ggplot", (14, 10)),
        ("seaborn-v0_8", (12, 8)),
    ),
)
def test_chart_generator_init_parametrized(style, figsize):
    """Параметризованный тест инициализации ChartGenerator."""
    generator = ChartGenerator(style=style, figsize=figsize)

    assert generator.style == style
    assert generator.figsize == figsize


@pytest.mark.parametrize(
    "num_items",
    (1, 5, 10, 20, 50),
)
def test_create_market_overview_chart_various_sizes(chart_generator, num_items):
    """Параметризованный тест с различным количеством предметов."""
    items = [{"name": f"Item {i}", "price": 50 + i * 5} for i in range(num_items)]
    result = chart_generator.create_market_overview_chart(items)

    assert isinstance(result, io.BytesIO)


# ==============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ==============================================================================


def test_chart_generation_workflow(chart_generator):
    """Интеграционный тест создания нескольких графиков."""
    # Создаем данные
    price_data = [
        {"date": (datetime.now() - timedelta(days=i)).isoformat(), "price": 100 + i * 5}
        for i in range(5)
    ]

    items_data = [{"name": f"Item {i}", "price": 50 + i * 10} for i in range(5)]

    arbitrage_data = [
        {
            "title": f"Item {i}",
            "profit": 20 + i * 5,
            "profit_percentage": 10 + i * 2,
            "buy_price": 100,
            "sell_price": 120 + i * 5,
        }
        for i in range(5)
    ]

    # Генерируем все графики
    price_chart = chart_generator.create_price_history_chart(price_data)
    items_chart = chart_generator.create_market_overview_chart(items_data)
    arb_chart = chart_generator.create_arbitrage_opportunities_chart(arbitrage_data)

    # Проверяем, что все созданы
    assert isinstance(price_chart, io.BytesIO)
    assert isinstance(items_chart, io.BytesIO)
    assert isinstance(arb_chart, io.BytesIO)


def test_multiple_generators_isolation():
    """Тест изоляции между несколькими генераторами."""
    gen1 = ChartGenerator(style="default", figsize=(10, 6))
    gen2 = ChartGenerator(style="bmh", figsize=(12, 8))

    # Проверяем, что генераторы независимы
    assert gen1.style != gen2.style
    assert gen1.figsize != gen2.figsize


def test_chart_generator_reusability(chart_generator):
    """Тест повторного использования генератора."""
    data = [{"date": datetime.now().isoformat(), "price": 100 + i * 10} for i in range(3)]

    # Создаем несколько графиков подряд
    chart1 = chart_generator.create_price_history_chart(data, title="Chart 1")
    chart2 = chart_generator.create_price_history_chart(data, title="Chart 2")
    chart3 = chart_generator.create_price_history_chart(data, title="Chart 3")

    # Все должны быть созданы успешно
    assert isinstance(chart1, io.BytesIO)
    assert isinstance(chart2, io.BytesIO)
    assert isinstance(chart3, io.BytesIO)


# ==============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК
# ==============================================================================


def test_chart_with_invalid_date_format(chart_generator):
    """Тест создания графика с неверным форматом даты."""
    invalid_data = [
        {"date": "not-a-date", "price": 100},
    ]

    # Должен обработать ошибку и вернуть error chart
    result = chart_generator.create_price_history_chart(invalid_data)
    assert isinstance(result, io.BytesIO)


def test_chart_with_missing_fields(chart_generator):
    """Тест создания графика с отсутствующими полями."""
    incomplete_data = [
        {"date": datetime.now().isoformat()},  # Нет price
    ]

    # Должен обработать ошибку
    result = chart_generator.create_price_history_chart(incomplete_data)
    assert isinstance(result, io.BytesIO)


def test_chart_with_negative_prices(chart_generator):
    """Тест создания графика с отрицательными ценами."""
    negative_data = [
        {"date": datetime.now().isoformat(), "price": -100},
    ]

    # Должен создать график даже с отрицательными ценами
    result = chart_generator.create_price_history_chart(negative_data)
    assert isinstance(result, io.BytesIO)


# ==============================================================================
# ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ
# ==============================================================================


def test_chart_generation_performance(chart_generator):
    """Тест производительности генерации графика."""
    # Большой набор данных
    large_data = [
        {"date": (datetime.now() - timedelta(days=i)).isoformat(), "price": 100 + i}
        for i in range(100)
    ]

    import time

    start = time.time()
    result = chart_generator.create_price_history_chart(large_data)
    duration = time.time() - start

    # Должен создать за разумное время (< 5 секунд)
    assert duration < 5.0
    assert isinstance(result, io.BytesIO)


def test_multiple_charts_generation_performance(chart_generator):
    """Тест производительности создания нескольких графиков."""
    data = [{"date": datetime.now().isoformat(), "price": 100 + i * 5} for i in range(10)]

    import time

    start = time.time()

    # Создаем 10 графиков
    for _ in range(10):
        chart_generator.create_price_history_chart(data)

    duration = time.time() - start

    # Должен создать все за разумное время (< 30 секунд)
    assert duration < 30.0

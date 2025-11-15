"""Тесты для модуля smart_market_finder.

Этот модуль содержит тесты для умного поиска выгодных предметов на рынке,
включая:
- Инициализацию SmartMarketFinder
- Поиск лучших возможностей
- Поиск предметов с заниженной ценой
- Расчет confidence и liquidity scores
- Определение типов возможностей и уровней риска
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.smart_market_finder import (
    MarketOpportunity,
    MarketOpportunityType,
    SmartMarketFinder,
    find_best_deals,
    find_quick_profits,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_api_client():
    """Создает мок DMarketAPI клиента."""
    mock_api = AsyncMock()
    mock_api._request = AsyncMock()
    return mock_api


@pytest.fixture()
def sample_market_item():
    """Создает образец предмета с рынка."""
    return {
        "itemId": "item123",
        "title": "AWP | Asiimov (Field-Tested)",
        "price": {"USD": "5000"},  # $50 в центах
        "suggestedPrice": {"USD": "6000"},  # $60 в центах
        "extra": {
            "offersCount": 25,
            "ordersCount": 15,
            "offersPrice": {"USD": "4900"},
            "ordersPrice": {"USD": "6100"},
            "category": "Rifle",
            "exterior": "Field-Tested",
        },
        "image": "https://example.com/image.png",
    }


# ============================================================================
# ТЕСТЫ ИНИЦИАЛИЗАЦИИ
# ============================================================================


def test_smart_market_finder_initialization(mock_api_client):
    """Тест инициализации SmartMarketFinder."""
    finder = SmartMarketFinder(mock_api_client)

    assert finder.api is mock_api_client
    assert finder._cache == {}
    assert finder._cache_ttl == 300
    assert finder.min_profit_percent == 5.0
    assert finder.min_confidence == 60.0
    assert finder.max_price == 100.0


def test_smart_market_finder_custom_settings(mock_api_client):
    """Тест изменения настроек SmartMarketFinder."""
    finder = SmartMarketFinder(mock_api_client)

    # Изменяем настройки
    finder.min_profit_percent = 10.0
    finder.min_confidence = 70.0
    finder.max_price = 200.0

    assert finder.min_profit_percent == 10.0
    assert finder.min_confidence == 70.0
    assert finder.max_price == 200.0


# ============================================================================
# ТЕСТЫ ПОИСКА ВОЗМОЖНОСТЕЙ
# ============================================================================


@pytest.mark.asyncio()
@patch.object(SmartMarketFinder, "_get_market_items_with_aggregated_prices")
@patch.object(SmartMarketFinder, "_analyze_item_opportunity")
async def test_find_best_opportunities_success(
    mock_analyze,
    mock_get_items,
    mock_api_client,
    sample_market_item,
):
    """Тест успешного поиска лучших возможностей."""
    # Настройка моков
    mock_get_items.return_value = [sample_market_item]

    mock_opportunity = MarketOpportunity(
        item_id="item123",
        title="AWP | Asiimov",
        current_price=50.0,
        suggested_price=60.0,
        profit_potential=10.0,
        profit_percent=20.0,
        opportunity_type=MarketOpportunityType.UNDERPRICED,
        confidence_score=75.0,
        liquidity_score=80.0,
        risk_level="low",
    )
    mock_analyze.return_value = mock_opportunity

    # Создаем finder и вызываем метод
    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_best_opportunities(
        game="csgo",
        min_price=10.0,
        max_price=100.0,
        limit=10,
    )

    # Проверки
    assert len(opportunities) == 1
    assert opportunities[0].item_id == "item123"
    assert opportunities[0].confidence_score == 75.0
    mock_get_items.assert_called_once()
    mock_analyze.assert_called_once()


@pytest.mark.asyncio()
@patch.object(SmartMarketFinder, "_get_market_items_with_aggregated_prices")
async def test_find_best_opportunities_no_items(
    mock_get_items,
    mock_api_client,
):
    """Тест поиска возможностей когда предметов нет."""
    # Настройка мока - возвращаем пустой список
    mock_get_items.return_value = []

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_best_opportunities(game="csgo")

    # Проверки
    assert opportunities == []
    mock_get_items.assert_called_once()


@pytest.mark.asyncio()
@patch.object(SmartMarketFinder, "_get_market_items_with_aggregated_prices")
async def test_find_best_opportunities_api_error(
    mock_get_items,
    mock_api_client,
):
    """Тест обработки ошибки API при поиске возможностей."""
    # Настройка мока - выбрасываем исключение
    mock_get_items.side_effect = Exception("API Error")

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_best_opportunities(game="csgo")

    # Проверки - должен вернуть пустой список при ошибке
    assert opportunities == []


@pytest.mark.asyncio()
async def test_find_underpriced_items_success(mock_api_client, sample_market_item):
    """Тест успешного поиска предметов с заниженной ценой."""
    # Настройка мока API
    mock_api_client._request = AsyncMock(
        return_value={"objects": [sample_market_item]},
    )

    finder = SmartMarketFinder(mock_api_client)
    underpriced = await finder.find_underpriced_items(
        game="csgo",
        min_price=10.0,
        max_price=100.0,
        min_discount_percent=10.0,
        limit=10,
    )

    # Проверки
    assert isinstance(underpriced, list)
    mock_api_client._request.assert_called_once()


@pytest.mark.asyncio()
async def test_find_underpriced_items_no_results(mock_api_client):
    """Тест поиска предметов с заниженной ценой когда нет результатов."""
    # Настройка мока API - пустой ответ
    mock_api_client._request = AsyncMock(return_value={"objects": []})

    finder = SmartMarketFinder(mock_api_client)
    underpriced = await finder.find_underpriced_items(game="csgo")

    # Проверки
    assert underpriced == []


# ============================================================================
# ТЕСТЫ ВСПОМОГАТЕЛЬНЫХ МЕТОДОВ
# ============================================================================


def test_determine_opportunity_type_underpriced(mock_api_client):
    """Тест определения типа возможности - заниженная цена."""
    finder = SmartMarketFinder(mock_api_client)

    # Предмет с заниженной ценой
    item_data = {
        "extra": {"popularity": 0.5},
    }
    profit_percent = 20.0  # > 15%

    opp_type = finder._determine_opportunity_type(item_data, profit_percent)

    assert opp_type == MarketOpportunityType.UNDERPRICED


def test_determine_opportunity_type_high_liquidity(mock_api_client):
    """Тест определения типа возможности - высокая ликвидность."""
    finder = SmartMarketFinder(mock_api_client)

    # Предмет с высокой ликвидностью
    item_data = {
        "extra": {"popularity": 0.8},  # Высокая популярность
    }
    profit_percent = 3.0  # Небольшая прибыль

    opp_type = finder._determine_opportunity_type(item_data, profit_percent)

    assert opp_type == MarketOpportunityType.HIGH_LIQUIDITY


def test_calculate_confidence_score(mock_api_client):
    """Тест расчета confidence score."""
    finder = SmartMarketFinder(mock_api_client)

    # Хорошие показатели
    item_data = {
        "extra": {"popularity": 0.8},
        "suggestedPrice": {"USD": "5000"},
    }
    profit_percent = 20.0

    score = finder._calculate_confidence_score(item_data, profit_percent)

    # Проверяем, что score находится в диапазоне 0-100
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_calculate_liquidity_score(mock_api_client, sample_market_item):
    """Тест расчета liquidity score."""
    finder = SmartMarketFinder(mock_api_client)

    score = finder._calculate_liquidity_score(sample_market_item)

    # Проверяем, что score находится в диапазоне 0-100
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_determine_risk_level_low(mock_api_client):
    """Тест определения низкого уровня риска."""
    finder = SmartMarketFinder(mock_api_client)

    # Низкий риск: высокая ликвидность, умеренная прибыль, высокая уверенность
    profit_percent = 10.0
    liquidity = 85.0
    confidence = 80.0

    risk = finder._determine_risk_level(profit_percent, liquidity, confidence)

    assert risk == "low"


def test_determine_risk_level_high(mock_api_client):
    """Тест определения высокого уровня риска."""
    finder = SmartMarketFinder(mock_api_client)

    # Высокий риск: низкая ликвидность или очень высокая прибыль
    profit_percent = 35.0  # Очень высокая прибыль
    liquidity = 30.0  # Низкая ликвидность
    confidence = 45.0  # Низкая уверенность

    risk = finder._determine_risk_level(profit_percent, liquidity, confidence)

    assert risk == "high"


def test_estimate_time_to_sell(mock_api_client):
    """Тест оценки времени продажи."""
    finder = SmartMarketFinder(mock_api_client)

    # Высокая ликвидность - быстрая продажа
    time_high = finder._estimate_time_to_sell(90.0)
    assert "час" in time_high.lower()  # Проверяем русский текст

    # Низкая ликвидность - медленная продажа
    time_low = finder._estimate_time_to_sell(20.0)
    assert "дн" in time_low.lower() or "нед" in time_low.lower()


# ============================================================================
# ТЕСТЫ АВТОНОМНЫХ ФУНКЦИЙ
# ============================================================================


@pytest.mark.asyncio()
@patch.object(SmartMarketFinder, "find_best_opportunities")
async def test_find_best_deals(mock_method):
    """Тест автономной функции find_best_deals."""
    # Настройка мока - возвращаем пустой список
    mock_method.return_value = []

    # Создаем мок API
    mock_api = AsyncMock()

    # Вызываем функцию
    results = await find_best_deals(mock_api, game="csgo")

    # Проверки
    assert isinstance(results, list)
    assert results == []


@pytest.mark.asyncio()
@patch("src.dmarket.smart_market_finder.SmartMarketFinder")
async def test_find_quick_profits(mock_finder_class):
    """Тест автономной функции find_quick_profits."""
    # Настройка мока
    mock_finder = AsyncMock()
    mock_finder.find_quick_flip_opportunities = AsyncMock(return_value=[])
    mock_finder_class.return_value = mock_finder

    # Создаем мок API
    mock_api = AsyncMock()

    # Вызываем функцию
    results = await find_quick_profits(mock_api, game="csgo")

    # Проверки
    assert isinstance(results, list)
    mock_finder.find_quick_flip_opportunities.assert_called_once()


# ============================================================================
# ТЕСТЫ ТИПОВ И КЛАССОВ
# ============================================================================


def test_market_opportunity_type_enum():
    """Тест enum MarketOpportunityType."""
    assert MarketOpportunityType.UNDERPRICED == "underpriced"
    assert MarketOpportunityType.TRENDING_UP == "trending_up"
    assert MarketOpportunityType.HIGH_LIQUIDITY == "high_liquidity"
    assert MarketOpportunityType.QUICK_FLIP == "quick_flip"
    assert MarketOpportunityType.VALUE_INVESTMENT == "value_investment"


def test_market_opportunity_dataclass():
    """Тест dataclass MarketOpportunity."""
    opp = MarketOpportunity(
        item_id="test123",
        title="Test Item",
        current_price=50.0,
        suggested_price=60.0,
        profit_potential=10.0,
        profit_percent=20.0,
        opportunity_type=MarketOpportunityType.UNDERPRICED,
        confidence_score=75.0,
        liquidity_score=80.0,
        risk_level="low",
    )

    assert opp.item_id == "test123"
    assert opp.title == "Test Item"
    assert opp.current_price == 50.0
    assert opp.profit_percent == 20.0
    assert opp.opportunity_type == MarketOpportunityType.UNDERPRICED
    assert opp.risk_level == "low"

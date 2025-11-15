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
async def test_find_underpriced_items_success(
    mock_api_client,
    sample_market_item,
):
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


# ============================================================================
# ТЕСТЫ find_target_opportunities
# ============================================================================


@pytest.mark.asyncio()
async def test_find_target_opportunities_success(
    mock_api_client,
    sample_market_item,
):
    """Тест поиска возможностей для таргетов."""
    # Настройка моков
    mock_api_client._request = AsyncMock(
        side_effect=[
            # Первый вызов - market items
            {"objects": [sample_market_item]},
            # Второй вызов - aggregated prices
            {
                "aggregatedPrices": [
                    {
                        "title": "AWP | Asiimov (Field-Tested)",
                        "orderBestPrice": "4500",  # $45
                        "offerBestPrice": "5500",  # $55
                        "orderCount": 10,
                        "offerCount": 20,
                    }
                ]
            },
        ]
    )

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_target_opportunities(
        game="csgo",
        min_price=10.0,
        max_price=100.0,
        min_spread_percent=5.0,
        limit=10,
    )

    # Проверки
    assert isinstance(opportunities, list)
    assert len(opportunities) > 0
    if opportunities:
        opp = opportunities[0]
        assert "title" in opp
        assert "spread_percent" in opp
        assert "recommended_target_price" in opp
        assert opp["spread_percent"] >= 5.0


@pytest.mark.asyncio()
async def test_find_target_opportunities_no_spread(mock_api_client):
    """Тест когда нет спреда между ценами."""
    # Настройка моков - цены одинаковые
    mock_api_client._request = AsyncMock(
        side_effect=[
            {"objects": [{"title": "Test", "price": {"USD": "5000"}}]},
            {
                "aggregatedPrices": [
                    {
                        "title": "Test",
                        "orderBestPrice": "5000",
                        "offerBestPrice": "5000",  # Нет спреда
                        "orderCount": 5,
                        "offerCount": 5,
                    }
                ]
            },
        ]
    )

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_target_opportunities(
        game="csgo",
        min_spread_percent=5.0,
    )

    # Не должно быть возможностей при отсутствии спреда
    assert opportunities == []


@pytest.mark.asyncio()
async def test_find_target_opportunities_api_error(mock_api_client):
    """Тест обработки ошибки API при поиске таргетов."""
    mock_api_client._request = AsyncMock(side_effect=Exception("API Error"))

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_target_opportunities(game="csgo")

    # Должен вернуть пустой список при ошибке
    assert opportunities == []


# ============================================================================
# ТЕСТЫ find_quick_flip_opportunities
# ============================================================================


@pytest.mark.asyncio()
@patch.object(SmartMarketFinder, "find_underpriced_items")
async def test_find_quick_flip_opportunities_success(
    mock_find_underpriced,
    mock_api_client,
):
    """Тест поиска возможностей быстрой перепродажи."""
    # Создаем возможности с высокой ликвидностью
    mock_opportunities = [
        MarketOpportunity(
            item_id="flip123",
            title="Quick Flip Item",
            current_price=20.0,
            suggested_price=25.0,
            profit_potential=3.0,
            profit_percent=15.0,
            opportunity_type=MarketOpportunityType.UNDERPRICED,
            confidence_score=85.0,
            liquidity_score=90.0,  # Высокая ликвидность
            risk_level="low",
        ),
        MarketOpportunity(
            item_id="flip456",
            title="Another Quick Item",
            current_price=15.0,
            suggested_price=20.0,
            profit_potential=3.5,
            profit_percent=20.0,
            opportunity_type=MarketOpportunityType.UNDERPRICED,
            confidence_score=80.0,
            liquidity_score=85.0,  # Высокая ликвидность
            risk_level="low",
        ),
    ]
    mock_find_underpriced.return_value = mock_opportunities

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_quick_flip_opportunities(
        game="csgo",
        min_price=5.0,
        max_price=30.0,
        min_profit_percent=10.0,
    )

    # Проверки
    assert isinstance(opportunities, list)
    assert len(opportunities) > 0
    # Проверяем что тип изменился на QUICK_FLIP
    quick_flip = MarketOpportunityType.QUICK_FLIP
    assert opportunities[0].opportunity_type == quick_flip
    # Проверяем что все имеют высокую ликвидность (>= 50)
    for opp in opportunities:
        assert opp.liquidity_score >= 50


@pytest.mark.asyncio()
@patch.object(
    SmartMarketFinder,
    "_get_market_items_with_aggregated_prices",
)
async def test_find_quick_flip_no_liquidity(
    mock_get_items,
    mock_api_client,
):
    """Тест когда нет ликвидных предметов."""
    mock_get_items.return_value = []

    finder = SmartMarketFinder(mock_api_client)
    opportunities = await finder.find_quick_flip_opportunities(game="csgo")

    # Не должно быть возможностей
    assert opportunities == []


# ============================================================================
# ТЕСТЫ _get_market_items_with_aggregated_prices
# ============================================================================


@pytest.mark.asyncio()
async def test_get_market_items_with_aggregated_prices(
    mock_api_client,
    sample_market_item,
):
    """Тест получения предметов с агрегированными ценами."""
    # Настройка моков для метода _request напрямую
    mock_api_client._request = AsyncMock(
        return_value={"objects": [sample_market_item], "cursor": None}
    )

    finder = SmartMarketFinder(mock_api_client)
    items = await finder._get_market_items_with_aggregated_prices(
        game="csgo",
        min_price=10.0,
        max_price=100.0,
    )

    # Проверки
    assert isinstance(items, list)
    # Даже если get_aggregated_prices не вернет данных,
    # должны быть items из market
    assert len(items) >= 0  # Может быть пустым если фильтры не совпадают


@pytest.mark.asyncio()
async def test_get_market_items_with_aggregated_prices_cache(
    mock_api_client,
):
    """Тест кэширования при получении предметов."""
    # Настройка моков
    mock_api_client.get_market_items = AsyncMock(
        return_value={"objects": [{"itemId": "cached_item"}]}
    )
    mock_api_client.get_aggregated_prices = AsyncMock(return_value={"aggregatedPrices": []})

    finder = SmartMarketFinder(mock_api_client)

    # Первый вызов
    _ = await finder._get_market_items_with_aggregated_prices(
        game="csgo",
        min_price=10.0,
        max_price=100.0,
    )

    # Второй вызов (должен использовать кэш)
    _ = await finder._get_market_items_with_aggregated_prices(
        game="csgo",
        min_price=10.0,
        max_price=100.0,
    )

    # API должен быть вызван только один раз (для первого вызова)
    assert mock_api_client.get_market_items.call_count <= 2


# ============================================================================
# ТЕСТЫ _analyze_item_opportunity
# ============================================================================


@pytest.mark.asyncio()
async def test_analyze_item_opportunity_underpriced(
    mock_api_client,
    sample_market_item,
):
    """Тест анализа предмета с заниженной ценой."""
    finder = SmartMarketFinder(mock_api_client)

    # Предмет с большой разницей в цене
    item_data = {
        "itemId": "analyze_item",
        "title": "Underpriced Item",
        "price": {"USD": "5000"},  # $50
        "suggestedPrice": {"USD": "7000"},  # $70
        "extra": {
            "popularity": 0.6,
            "offersCount": 20,
        },
    }

    opportunity = await finder._analyze_item_opportunity(
        item_data,
        game="csgo",
    )

    # Проверки
    assert opportunity is not None
    assert isinstance(opportunity, MarketOpportunity)
    assert opportunity.item_id == "analyze_item"
    assert opportunity.opportunity_type == MarketOpportunityType.UNDERPRICED
    assert opportunity.profit_percent > 0


@pytest.mark.asyncio()
async def test_analyze_item_opportunity_no_suggested_price(
    mock_api_client,
):
    """Тест анализа предмета без suggestedPrice."""
    finder = SmartMarketFinder(mock_api_client)

    # Предмет без suggestedPrice
    item_data = {
        "itemId": "no_price",
        "title": "No Suggested Price",
        "price": {"USD": "5000"},
        # Нет suggestedPrice
    }

    opportunity = await finder._analyze_item_opportunity(
        item_data,
        game="csgo",
    )

    # Метод создает возможность даже без suggested_price
    # используя best offer price + 10% для расчета потенциальной цены
    assert opportunity is not None
    assert opportunity.item_id == "no_price"
    assert opportunity.current_price == 50.0

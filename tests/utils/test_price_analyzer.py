"""Тесты для модуля price_analyzer.

Проверяет функции анализа цен и истории продаж.
"""

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.price_analyzer import (
    _CACHE_TTL,
    _price_history_cache,
    calculate_price_statistics,
    get_item_price_history,
)


@pytest.fixture()
def mock_api():
    """Фикстура мокированного API."""
    api = MagicMock(spec=DMarketAPI)
    api._request = AsyncMock()
    return api


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищать кэш перед каждым тестом."""
    _price_history_cache.clear()
    yield
    _price_history_cache.clear()


class TestCacheConstants:
    """Тесты констант кэша."""

    def test_cache_ttl_defined(self):
        """Тест что CACHE_TTL определен."""
        assert _CACHE_TTL == 3600

    def test_cache_ttl_is_int(self):
        """Тест что CACHE_TTL это int."""
        assert isinstance(_CACHE_TTL, int)

    def test_cache_ttl_positive(self):
        """Тест что CACHE_TTL положительный."""
        assert _CACHE_TTL > 0


class TestPriceHistoryCache:
    """Тесты кэширования истории цен."""

    def test_cache_initially_empty(self):
        """Тест что кэш изначально пуст."""
        assert len(_price_history_cache) == 0

    def test_can_add_to_cache(self):
        """Тест добавления в кэш."""
        _price_history_cache["test_key"] = {
            "data": [],
            "last_update": time.time(),
        }
        assert "test_key" in _price_history_cache

    def test_cache_structure(self):
        """Тест структуры кэша."""
        cache_entry = {
            "data": [{"price": 10.0}],
            "last_update": time.time(),
        }
        _price_history_cache["test"] = cache_entry

        assert "data" in _price_history_cache["test"]
        assert "last_update" in _price_history_cache["test"]


class TestGetItemPriceHistory:
    """Тесты функции get_item_price_history."""

    @pytest.mark.asyncio()
    async def test_get_price_history_success(self, mock_api):
        """Тест успешного получения истории цен."""
        mock_api._request.return_value = {
            "sales": [
                {
                    "date": "2024-01-01T00:00:00",
                    "price": 1000,  # В центах
                    "volume": 5,
                }
            ]
        }

        result = await get_item_price_history(mock_api, "item123", days=7)

        assert len(result) == 1
        assert result[0]["price"] == 10.0  # Конвертировано из центов
        assert result[0]["volume"] == 5

    @pytest.mark.asyncio()
    async def test_get_price_history_empty_response(self, mock_api):
        """Тест пустого ответа."""
        mock_api._request.return_value = {}

        result = await get_item_price_history(mock_api, "item123")

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_price_history_no_sales(self, mock_api):
        """Тест ответа без продаж."""
        mock_api._request.return_value = {"sales": []}

        result = await get_item_price_history(mock_api, "item123")

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_price_history_api_error(self, mock_api):
        """Тест обработки ошибки API."""
        mock_api._request.side_effect = Exception("API Error")

        result = await get_item_price_history(mock_api, "item123")

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_price_history_uses_cache(self, mock_api):
        """Тест использования кэша."""
        # Первый запрос
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000, "volume": 1}]
        }

        result1 = await get_item_price_history(mock_api, "item123", days=7)

        # Второй запрос (должен использовать кэш)
        result2 = await get_item_price_history(mock_api, "item123", days=7)

        # API должен быть вызван только один раз
        assert mock_api._request.call_count == 1
        assert result1 == result2

    @pytest.mark.asyncio()
    async def test_get_price_history_cache_expiry(self, mock_api):
        """Тест истечения кэша."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000, "volume": 1}]
        }

        # Первый запрос
        await get_item_price_history(mock_api, "item123", days=7)

        # Искусственно устанавливаем старый timestamp
        cache_key = "item123_7"
        _price_history_cache[cache_key]["last_update"] = time.time() - _CACHE_TTL - 1

        # Второй запрос (кэш истек)
        await get_item_price_history(mock_api, "item123", days=7)

        # API должен быть вызван дважды
        assert mock_api._request.call_count == 2

    @pytest.mark.asyncio()
    async def test_get_price_history_different_days(self, mock_api):
        """Тест с разным количеством дней."""
        mock_api._request.return_value = {"sales": []}

        await get_item_price_history(mock_api, "item123", days=7)
        await get_item_price_history(mock_api, "item123", days=30)

        # Должно быть два вызова для разных периодов
        assert mock_api._request.call_count == 2

    @pytest.mark.asyncio()
    async def test_get_price_history_price_conversion(self, mock_api):
        """Тест конвертации цены из центов."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 2500, "volume": 1}]
        }

        result = await get_item_price_history(mock_api, "item123")

        assert result[0]["price"] == 25.0

    @pytest.mark.asyncio()
    async def test_get_price_history_invalid_date(self, mock_api):
        """Тест обработки невалидной даты."""
        mock_api._request.return_value = {
            "sales": [{"date": "invalid_date", "price": 1000, "volume": 1}]
        }

        result = await get_item_price_history(mock_api, "item123")

        # Запись с невалидной датой должна быть пропущена
        assert len(result) == 0

    @pytest.mark.asyncio()
    async def test_get_price_history_missing_fields(self, mock_api):
        """Тест обработки отсутствующих полей."""
        mock_api._request.return_value = {
            "sales": [
                {"date": "2024-01-01T00:00:00"}  # Нет price и volume
            ]
        }

        result = await get_item_price_history(mock_api, "item123")

        # Запись должна быть обработана с дефолтными значениями или пропущена
        assert isinstance(result, list)


class TestCalculatePriceStatistics:
    """Тесты функции calculate_price_statistics."""

    def test_calculate_statistics_empty_history(self):
        """Тест расчета статистики для пустой истории."""
        result = calculate_price_statistics([])

        assert result["avg_price"] == 0
        assert result["min_price"] == 0
        assert result["max_price"] == 0
        assert result["volatility"] == 0

    def test_calculate_statistics_single_price(self):
        """Тест расчета статистики для одной цены."""
        history = [{"price": 10.0, "date": datetime.now(), "volume": 1}]

        result = calculate_price_statistics(history)

        assert result["avg_price"] == 10.0
        assert result["min_price"] == 10.0
        assert result["max_price"] == 10.0
        assert result["volatility"] == 0

    def test_calculate_statistics_multiple_prices(self):
        """Тест расчета статистики для нескольких цен."""
        history = [
            {"price": 10.0, "date": datetime.now(), "volume": 1},
            {"price": 20.0, "date": datetime.now(), "volume": 1},
            {"price": 30.0, "date": datetime.now(), "volume": 1},
        ]

        result = calculate_price_statistics(history)

        assert result["avg_price"] == 20.0
        assert result["min_price"] == 10.0
        assert result["max_price"] == 30.0
        assert result["volatility"] > 0

    def test_calculate_statistics_weighted_average(self):
        """Тест расчета взвешенного среднего."""
        history = [
            {"price": 10.0, "date": datetime.now(), "volume": 1},
            {"price": 20.0, "date": datetime.now(), "volume": 2},
        ]

        result = calculate_price_statistics(history)

        # Взвешенное среднее: (10*1 + 20*2) / 3 = 16.67
        assert 16 < result["weighted_avg_price"] < 17

    def test_calculate_statistics_returns_dict(self):
        """Тест что функция возвращает словарь."""
        result = calculate_price_statistics([])

        assert isinstance(result, dict)

    def test_calculate_statistics_has_required_fields(self):
        """Тест что результат содержит требуемые поля."""
        result = calculate_price_statistics([])

        required_fields = ["avg_price", "min_price", "max_price", "volatility", "volume"]
        for field in required_fields:
            assert field in result


class TestCacheManagement:
    """Тесты управления кэшем."""

    def test_cache_key_format(self):
        """Тест формата ключа кэша."""
        cache_key = "item123_7"
        _price_history_cache[cache_key] = {
            "data": [],
            "last_update": time.time(),
        }

        assert cache_key in _price_history_cache

    def test_cache_stores_timestamp(self):
        """Тест что кэш сохраняет timestamp."""
        cache_key = "test"
        timestamp = time.time()
        _price_history_cache[cache_key] = {
            "data": [],
            "last_update": timestamp,
        }

        stored_timestamp = _price_history_cache[cache_key]["last_update"]
        assert abs(stored_timestamp - timestamp) < 0.1

    def test_cache_independence(self):
        """Тест независимости записей кэша."""
        _price_history_cache["item1_7"] = {
            "data": [{"price": 10.0}],
            "last_update": time.time(),
        }
        _price_history_cache["item2_7"] = {
            "data": [{"price": 20.0}],
            "last_update": time.time(),
        }

        assert _price_history_cache["item1_7"]["data"] != _price_history_cache["item2_7"]["data"]


class TestPriceConversion:
    """Тесты конвертации цен."""

    @pytest.mark.asyncio()
    async def test_price_cents_to_dollars(self, mock_api):
        """Тест конвертации центов в доллары."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 100, "volume": 1}]
        }

        result = await get_item_price_history(mock_api, "item123")

        assert result[0]["price"] == 1.0

    @pytest.mark.asyncio()
    async def test_price_zero_cents(self, mock_api):
        """Тест обработки нулевой цены."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 0, "volume": 1}]
        }

        result = await get_item_price_history(mock_api, "item123")

        assert result[0]["price"] == 0.0


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio()
    async def test_very_large_price(self, mock_api):
        """Тест очень большой цены."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000000, "volume": 1}]
        }

        result = await get_item_price_history(mock_api, "item123")

        assert result[0]["price"] == 10000.0

    @pytest.mark.asyncio()
    async def test_very_large_volume(self, mock_api):
        """Тест очень большого объема."""
        mock_api._request.return_value = {
            "sales": [{"date": "2024-01-01T00:00:00", "price": 1000, "volume": 999999}]
        }

        result = await get_item_price_history(mock_api, "item123")

        assert result[0]["volume"] == 999999

    def test_statistics_with_extreme_values(self):
        """Тест статистики с экстремальными значениями."""
        history = [
            {"price": 0.01, "date": datetime.now(), "volume": 1},
            {"price": 10000.0, "date": datetime.now(), "volume": 1},
        ]

        result = calculate_price_statistics(history)

        assert result["min_price"] == 0.01
        assert result["max_price"] == 10000.0
        assert result["volatility"] > 0

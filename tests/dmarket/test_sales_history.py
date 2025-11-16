"""Тесты для модуля sales_history."""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.sales_history import (
    _calculate_median,
    _calculate_std_dev,
    _extract_price_from_item,
    _get_cache_file_path,
    _load_from_cache,
    _save_to_cache,
    analyze_sales_history,
    calculate_price_trend,
    detect_price_anomalies,
    execute_api_request,
    get_arbitrage_opportunities_with_sales_history,
    get_item_sales_history,
    get_sales_history,
)


class TestHelperFunctions:
    """Тесты вспомогательных функций."""

    def test_calculate_median_odd_count(self):
        """Тест медианы для нечетного количества чисел."""
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert _calculate_median(numbers) == 3.0

    def test_calculate_median_even_count(self):
        """Тест медианы для четного количества чисел."""
        numbers = [1.0, 2.0, 3.0, 4.0]
        assert _calculate_median(numbers) == 2.5

    def test_calculate_median_empty(self):
        """Тест медианы для пустого списка."""
        assert _calculate_median([]) == 0

    def test_calculate_median_single(self):
        """Тест медианы для одного числа."""
        assert _calculate_median([5.0]) == 5.0

    def test_calculate_std_dev(self):
        """Тест стандартного отклонения."""
        numbers = [2.0, 4.0, 6.0, 8.0]
        std_dev = _calculate_std_dev(numbers)
        assert std_dev > 0

    def test_calculate_std_dev_empty(self):
        """Тест стандартного отклонения для пустого списка."""
        assert _calculate_std_dev([]) == 0

    def test_calculate_std_dev_single(self):
        """Тест стандартного отклонения для одного числа."""
        assert _calculate_std_dev([5.0]) == 0

    def test_extract_price_from_item_sales_price(self):
        """Тест извлечения цены из salesPrice."""
        item = {"salesPrice": 1250}  # $12.50 в центах
        assert _extract_price_from_item(item) == 12.5

    def test_extract_price_from_item_price_usd(self):
        """Тест извлечения цены из price.USD."""
        item = {"price": {"USD": 2000}}  # $20.00 в центах
        assert _extract_price_from_item(item) == 20.0

    def test_extract_price_from_item_no_price(self):
        """Тест извлечения цены при отсутствии данных."""
        item = {}
        assert _extract_price_from_item(item) == 0

    def test_extract_price_from_item_invalid_format(self):
        """Тест извлечения цены при неверном формате."""
        item = {"price": "invalid"}
        assert _extract_price_from_item(item) == 0

    def test_get_cache_file_path(self):
        """Тест генерации пути к файлу кэша."""
        path = _get_cache_file_path("AK-47 | Redline", "csgo", "24h")
        assert "csgo" in str(path)
        assert "24h" in str(path)
        assert path.suffix == ".json"


class TestCacheOperations:
    """Тесты операций с кэшем."""

    @pytest.fixture()
    def temp_cache_dir(self, tmp_path):
        """Создать временную директорию для кэша."""
        cache_dir = tmp_path / "sales_cache"
        cache_dir.mkdir()
        return cache_dir

    def test_save_and_load_cache(self, temp_cache_dir, monkeypatch):
        """Тест сохранения и загрузки кэша."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", temp_cache_dir)

        test_data = [
            {"price": 12.5, "timestamp": 1234567890, "market_hash_name": "Test Item"},
        ]

        # Сохраняем в кэш
        _save_to_cache("Test Item", "csgo", "24h", test_data)

        # Загружаем из кэша
        loaded_data = _load_from_cache("Test Item", "csgo", "24h")

        assert loaded_data == test_data

    def test_load_cache_expired(self, temp_cache_dir, monkeypatch):
        """Тест загрузки устаревшего кэша."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", temp_cache_dir)
        monkeypatch.setattr(
            "src.dmarket.sales_history.CACHE_TTL", {"24h": 0}
        )  # Мгновенное устаревание

        test_data = [{"price": 12.5}]

        # Сохраняем в кэш
        _save_to_cache("Test Item", "csgo", "24h", test_data)

        # Ждем немного
        time.sleep(0.1)

        # Загружаем из кэша (должен быть пустым, так как устарел)
        loaded_data = _load_from_cache("Test Item", "csgo", "24h")

        assert loaded_data == []

    def test_load_cache_not_exists(self, temp_cache_dir, monkeypatch):
        """Тест загрузки несуществующего кэша."""
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", temp_cache_dir)

        loaded_data = _load_from_cache("Nonexistent Item", "csgo", "24h")

        assert loaded_data == []


class TestGetItemSalesHistory:
    """Тесты функции get_item_sales_history."""

    @pytest.mark.asyncio()
    async def test_get_sales_history_success(self):
        """Тест успешного получения истории продаж."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[
                {"date": 1234567890, "price": 1250},
                {"date": 1234567900, "price": 1300},
            ],
        )

        result = await get_item_sales_history(
            item_name="AK-47 | Redline",
            game="csgo",
            period="24h",
            use_cache=False,
            dmarket_api=mock_api,
        )

        assert len(result) == 2
        assert result[0]["price"] == 13.0  # 1300 / 100
        assert result[1]["price"] == 12.5  # 1250 / 100

    @pytest.mark.asyncio()
    async def test_get_sales_history_empty(self):
        """Тест получения пустой истории продаж."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(return_value=[])

        result = await get_item_sales_history(
            item_name="Rare Item",
            game="csgo",
            use_cache=False,
            dmarket_api=mock_api,
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_sales_history_invalid_response(self):
        """Тест обработки неверного ответа API."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(return_value=None)

        result = await get_item_sales_history(
            item_name="Test Item",
            game="csgo",
            use_cache=False,
            dmarket_api=mock_api,
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_get_sales_history_with_cache(self, tmp_path, monkeypatch):
        """Тест использования кэша."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setattr("src.dmarket.sales_history.SALES_CACHE_DIR", cache_dir)

        cached_data = [{"price": 10.0, "timestamp": 123, "market_hash_name": "Test"}]

        # Создаем кэш файл
        cache_file = cache_dir / "csgo_Test_Item_24h.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cached_data, f)

        mock_api = MagicMock()

        # API не должен вызываться, так как используется кэш
        result = await get_item_sales_history(
            item_name="Test Item",
            game="csgo",
            period="24h",
            use_cache=True,
            dmarket_api=mock_api,
        )

        assert result == cached_data


class TestDetectPriceAnomalies:
    """Тесты функции detect_price_anomalies."""

    @pytest.mark.asyncio()
    async def test_detect_anomalies_found(self):
        """Тест обнаружения аномалий."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            return_value=[
                {"date": 123, "price": 1000},  # $10
                {"date": 124, "price": 1000},  # $10
                {"date": 125, "price": 2000},  # $20 (аномалия!)
                {"date": 126, "price": 1000},  # $10
            ],
        )

        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = [
                {"price": 10.0, "timestamp": 123},
                {"price": 10.0, "timestamp": 124},
                {"price": 20.0, "timestamp": 125},
                {"price": 10.0, "timestamp": 126},
            ]

            result = await detect_price_anomalies(
                item_name="Test Item",
                game="csgo",
                threshold_percent=50.0,
                dmarket_api=mock_api,
            )

            assert len(result["anomalies"]) >= 1
            assert result["median_price"] == 10.0

    @pytest.mark.asyncio()
    async def test_detect_anomalies_none(self):
        """Тест отсутствия аномалий."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = [
                {"price": 10.0, "timestamp": 123},
                {"price": 10.1, "timestamp": 124},
                {"price": 9.9, "timestamp": 125},
            ]

            result = await detect_price_anomalies(
                item_name="Stable Item",
                threshold_percent=50.0,
            )

            assert len(result["anomalies"]) == 0

    @pytest.mark.asyncio()
    async def test_detect_anomalies_no_data(self):
        """Тест обработки отсутствия данных."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = []

            result = await detect_price_anomalies(item_name="No Data Item")

            assert result["num_sales"] == 0
            assert result["anomalies"] == []


class TestCalculatePriceTrend:
    """Тесты функции calculate_price_trend."""

    @pytest.mark.asyncio()
    async def test_price_trend_up(self):
        """Тест растущего тренда."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = [
                {"price": 10.0, "timestamp": 100},
                {"price": 12.0, "timestamp": 200},
                {"price": 14.0, "timestamp": 300},
            ]

            result = await calculate_price_trend(item_name="Rising Item")

            assert result["trend"] == "up"
            assert result["change_percent"] > 0

    @pytest.mark.asyncio()
    async def test_price_trend_down(self):
        """Тест падающего тренда."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = [
                {"price": 14.0, "timestamp": 100},
                {"price": 12.0, "timestamp": 200},
                {"price": 10.0, "timestamp": 300},
            ]

            result = await calculate_price_trend(item_name="Falling Item")

            assert result["trend"] == "down"
            assert result["change_percent"] < 0

    @pytest.mark.asyncio()
    async def test_price_trend_stable(self):
        """Тест стабильного тренда."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = [
                {"price": 10.0, "timestamp": 100},
                {"price": 10.1, "timestamp": 200},
                {"price": 10.2, "timestamp": 300},
            ]

            result = await calculate_price_trend(item_name="Stable Item")

            assert result["trend"] == "stable"

    @pytest.mark.asyncio()
    async def test_price_trend_no_data(self):
        """Тест обработки отсутствия данных."""
        with patch("src.dmarket.sales_history.get_item_sales_history") as mock_get:
            mock_get.return_value = []

            result = await calculate_price_trend(item_name="No Data Item")

            assert result["trend"] == "unknown"


class TestCompatibilityFunctions:
    """Тесты функций совместимости."""

    @pytest.mark.asyncio()
    async def test_get_sales_history_success(self):
        """Тест функции get_sales_history."""
        mock_api = MagicMock()
        mock_api.request = AsyncMock(
            return_value={"LastSales": [{"price": 1000}], "Total": 1},
        )

        result = await get_sales_history(items=["Test Item"], api_client=mock_api)

        assert "LastSales" in result
        assert result["Total"] >= 0

    @pytest.mark.asyncio()
    async def test_get_sales_history_empty_items(self):
        """Тест функции get_sales_history с пустым списком."""
        result = await get_sales_history(items=[])

        assert result["Total"] == 0
        assert result["LastSales"] == []

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_success(self):
        """Тест функции analyze_sales_history."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock_get:
            mock_get.return_value = {
                "LastSales": [
                    {"date": 123, "price": {"USD": 1000}},
                    {"date": 124, "price": {"USD": 1100}},
                ],
                "Total": 2,
            }

            result = await analyze_sales_history(item_name="Test Item", days=7)

            assert result["has_data"] is True
            assert result["total_sales"] == 2

    @pytest.mark.asyncio()
    async def test_analyze_sales_history_no_data(self):
        """Тест функции analyze_sales_history без данных."""
        with patch("src.dmarket.sales_history.get_sales_history") as mock_get:
            mock_get.return_value = {"LastSales": [], "Total": 0}

            result = await analyze_sales_history(item_name="No Data Item")

            assert result["has_data"] is False
            assert result["total_sales"] == 0

    @pytest.mark.asyncio()
    async def test_execute_api_request(self):
        """Тест функции execute_api_request."""
        mock_api = MagicMock()
        mock_api.request = AsyncMock(return_value={"data": "test"})

        result = await execute_api_request(
            endpoint="/test",
            params={"key": "value"},
            api_client=mock_api,
        )

        assert "data" in result

    @pytest.mark.asyncio()
    async def test_get_arbitrage_opportunities_with_sales_history(self):
        """Тест функции get_arbitrage_opportunities_with_sales_history."""
        with (
            patch("src.dmarket.sales_history.find_arbitrage_items") as mock_arb,
            patch("src.dmarket.sales_history.analyze_sales_history") as mock_analyze,
        ):
            mock_arb.return_value = [{"market_hash_name": "Test Item"}]
            mock_analyze.return_value = {
                "has_data": True,
                "sales_per_day": 5.0,
                "price_trend": "up",
            }

            result = await get_arbitrage_opportunities_with_sales_history(
                min_sales_per_day=1.0,
            )

            assert len(result) > 0


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio()
    async def test_get_sales_history_api_error(self):
        """Тест обработки ошибки API."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(
            side_effect=Exception("API Error"),
        )

        result = await get_item_sales_history(
            item_name="Test",
            use_cache=False,
            dmarket_api=mock_api,
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_invalid_period(self):
        """Тест обработки неверного периода."""
        mock_api = MagicMock()
        mock_api.get_item_price_history = AsyncMock(return_value=[])

        # Должен использовать период по умолчанию (24h)
        await get_item_sales_history(
            item_name="Test",
            period="invalid_period",
            use_cache=False,
            dmarket_api=mock_api,
        )

        # Проверяем что функция не упала
        assert True

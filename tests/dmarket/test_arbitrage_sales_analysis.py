"""Тесты для модуля arbitrage_sales_analysis."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.arbitrage_sales_analysis import (
    SalesAnalyzer,
    analyze_sales_volume,
    estimate_sell_time,
    get_price_trend,
)


class TestSalesAnalyzer:
    """Тесты для класса SalesAnalyzer."""

    @pytest.fixture()
    def mock_api(self):
        """Фикстура для мокирования API клиента."""
        api = MagicMock()
        api.get_sales_history = AsyncMock()
        api.get_price_history = AsyncMock()
        return api

    @pytest.fixture()
    def analyzer(self, mock_api):
        """Фикстура для создания SalesAnalyzer."""
        return SalesAnalyzer(api_client=mock_api)

    @pytest.mark.asyncio()
    async def test_init(self, mock_api):
        """Тест инициализации SalesAnalyzer."""
        analyzer = SalesAnalyzer(api_client=mock_api)

        assert analyzer.api_client == mock_api
        assert analyzer.cache is not None

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_success(self, analyzer, mock_api):
        """Тест успешного получения истории продаж."""
        mock_sales = [
            {
                "date": "2023-11-01T10:00:00Z",
                "price": {"amount": 1000},
                "quantity": 1,
            },
            {
                "date": "2023-11-02T10:00:00Z",
                "price": {"amount": 1100},
                "quantity": 1,
            },
        ]

        mock_api.get_sales_history.return_value = {
            "sales": mock_sales,
            "total": 2,
        }

        result = await analyzer.get_item_sales_history(
            game="csgo",
            title="AK-47 | Redline (Field-Tested)",
            days=7,
        )

        assert result == mock_sales
        mock_api.get_sales_history.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_item_sales_history_empty(self, analyzer, mock_api):
        """Тест получения пустой истории продаж."""
        mock_api.get_sales_history.return_value = {"sales": [], "total": 0}

        result = await analyzer.get_item_sales_history(
            game="csgo",
            title="Rare Item",
            days=7,
        )

        assert result == []

    @pytest.mark.asyncio()
    async def test_analyze_sales_volume_high(self, analyzer, mock_api):
        """Тест анализа объема продаж (высокий)."""
        # 50 продаж за 7 дней = ~7 продаж/день
        mock_sales = [
            {"date": f"2023-11-{i:02d}T10:00:00Z", "price": 1000, "quantity": 1}
            for i in range(1, 51)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.analyze_sales_volume(
            game="csgo",
            title="AK-47 | Redline",
            days=7,
        )

        assert result["volume"] == "high"
        assert result["sales_count"] == 50
        assert result["avg_sales_per_day"] > 5

    @pytest.mark.asyncio()
    async def test_analyze_sales_volume_medium(self, analyzer, mock_api):
        """Тест анализа объема продаж (средний)."""
        # 20 продаж за 7 дней = ~3 продажи/день
        mock_sales = [
            {"date": f"2023-11-{i:02d}T10:00:00Z", "price": 1000, "quantity": 1}
            for i in range(1, 21)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.analyze_sales_volume(
            game="csgo",
            title="Test Item",
            days=7,
        )

        assert result["volume"] in ["medium", "high"]
        assert result["sales_count"] == 20

    @pytest.mark.asyncio()
    async def test_analyze_sales_volume_low(self, analyzer, mock_api):
        """Тест анализа объема продаж (низкий)."""
        # 3 продажи за 7 дней = <1 продажа/день
        mock_sales = [
            {"date": f"2023-11-0{i}T10:00:00Z", "price": 1000, "quantity": 1} for i in range(1, 4)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.analyze_sales_volume(
            game="csgo",
            title="Rare Item",
            days=7,
        )

        assert result["volume"] == "low"
        assert result["sales_count"] == 3

    @pytest.mark.asyncio()
    async def test_estimate_time_to_sell_fast(self, analyzer, mock_api):
        """Тест оценки времени продажи (быстро)."""
        # Много продаж = быстро
        mock_sales = [{"date": f"2023-11-{i:02d}T10:00:00Z", "price": 1000} for i in range(1, 51)]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.estimate_time_to_sell(
            game="csgo",
            title="Popular Item",
        )

        assert result["estimated_days"] < 7
        assert result["confidence"] in ["high", "medium"]

    @pytest.mark.asyncio()
    async def test_estimate_time_to_sell_slow(self, analyzer, mock_api):
        """Тест оценки времени продажи (медленно)."""
        # Мало продаж = медленно
        mock_sales = [{"date": "2023-11-01T10:00:00Z", "price": 1000}]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.estimate_time_to_sell(
            game="csgo",
            title="Rare Item",
        )

        assert result["estimated_days"] > 7
        assert result["confidence"] == "low"

    @pytest.mark.asyncio()
    async def test_analyze_price_trends_rising(self, analyzer, mock_api):
        """Тест анализа тренда цен (рост)."""
        # Растущие цены: от 1000 до 2000
        mock_sales = [
            {"date": f"2023-11-{i:02d}T10:00:00Z", "price": {"amount": 1000 + i * 100}}
            for i in range(1, 11)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.analyze_price_trends(
            game="csgo",
            title="Trending Item",
            days=10,
        )

        assert result["trend"] == "rising"
        assert result["price_change_percent"] > 0

    @pytest.mark.asyncio()
    async def test_analyze_price_trends_falling(self, analyzer, mock_api):
        """Тест анализа тренда цен (падение)."""
        # Падающие цены: от 2000 до 1000
        mock_sales = [
            {"date": f"2023-11-{i:02d}T10:00:00Z", "price": {"amount": 2000 - i * 100}}
            for i in range(1, 11)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.analyze_price_trends(
            game="csgo",
            title="Declining Item",
            days=10,
        )

        assert result["trend"] == "falling"
        assert result["price_change_percent"] < 0

    @pytest.mark.asyncio()
    async def test_analyze_price_trends_stable(self, analyzer, mock_api):
        """Тест анализа тренда цен (стабильно)."""
        # Стабильные цены: около 1000 +/- 2%
        mock_sales = [
            {"date": f"2023-11-{i:02d}T10:00:00Z", "price": {"amount": 1000 + (i % 2) * 10}}
            for i in range(1, 11)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.analyze_price_trends(
            game="csgo",
            title="Stable Item",
            days=10,
        )

        assert result["trend"] == "stable"
        assert abs(result["price_change_percent"]) < 5

    @pytest.mark.asyncio()
    async def test_evaluate_arbitrage_potential_excellent(self, analyzer, mock_api):
        """Тест оценки потенциала арбитража (отлично)."""
        # Высокий объем + стабильные цены + быстрая продажа
        mock_sales = [
            {"date": f"2023-11-{i:02d}T10:00:00Z", "price": {"amount": 1000 + (i % 2) * 5}}
            for i in range(1, 51)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.evaluate_arbitrage_potential(
            game="csgo",
            title="Excellent Item",
            buy_price=900,
            expected_sell_price=1050,
        )

        assert result["rating"] in ["excellent", "good"]
        assert result["profit_potential"] > 0
        assert result["risk_level"] in ["low", "medium"]

    @pytest.mark.asyncio()
    async def test_evaluate_arbitrage_potential_poor(self, analyzer, mock_api):
        """Тест оценки потенциала арбитража (плохо)."""
        # Низкий объем + нестабильные цены
        mock_sales = [
            {"date": f"2023-11-0{i}T10:00:00Z", "price": {"amount": 1000 + i * 200}}
            for i in range(1, 4)
        ]

        mock_api.get_sales_history.return_value = {"sales": mock_sales}

        result = await analyzer.evaluate_arbitrage_potential(
            game="csgo",
            title="Risky Item",
            buy_price=1000,
            expected_sell_price=1050,
        )

        assert result["rating"] in ["poor", "fair"]
        assert result["risk_level"] in ["high", "very_high"]

    @pytest.mark.asyncio()
    async def test_caching_works(self, analyzer, mock_api):
        """Тест работы кэширования."""
        mock_api.get_sales_history.return_value = {"sales": [{"price": 1000}]}

        # Первый вызов
        await analyzer.get_item_sales_history("csgo", "Test Item", 7)

        # Второй вызов (должен использовать кэш)
        await analyzer.get_item_sales_history("csgo", "Test Item", 7)

        # API должно быть вызвано только один раз
        assert mock_api.get_sales_history.call_count == 1


class TestCompatibilityFunctions:
    """Тесты для функций совместимости."""

    @pytest.mark.asyncio()
    async def test_analyze_sales_volume_function(self):
        """Тест функции analyze_sales_volume."""
        mock_api = MagicMock()
        mock_api.get_sales_history = AsyncMock(
            return_value={
                "sales": [{"date": f"2023-11-{i:02d}", "price": 1000} for i in range(1, 21)],
            },
        )

        result = await analyze_sales_volume(
            api_client=mock_api,
            game="csgo",
            title="Test Item",
        )

        assert "volume" in result
        assert "sales_count" in result

    @pytest.mark.asyncio()
    async def test_estimate_sell_time_function(self):
        """Тест функции estimate_sell_time."""
        mock_api = MagicMock()
        mock_api.get_sales_history = AsyncMock(
            return_value={
                "sales": [{"date": f"2023-11-{i:02d}", "price": 1000} for i in range(1, 11)],
            },
        )

        result = await estimate_sell_time(
            api_client=mock_api,
            game="csgo",
            title="Test Item",
        )

        assert "estimated_days" in result
        assert "confidence" in result

    @pytest.mark.asyncio()
    async def test_get_price_trend_function(self):
        """Тест функции get_price_trend."""
        mock_api = MagicMock()
        mock_api.get_sales_history = AsyncMock(
            return_value={
                "sales": [
                    {"date": f"2023-11-{i:02d}", "price": {"amount": 1000 + i * 50}}
                    for i in range(1, 11)
                ],
            },
        )

        result = await get_price_trend(
            api_client=mock_api,
            game="csgo",
            title="Test Item",
        )

        assert "trend" in result
        assert "price_change_percent" in result


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio()
    async def test_no_sales_history(self):
        """Тест обработки отсутствия истории продаж."""
        mock_api = MagicMock()
        mock_api.get_sales_history = AsyncMock(return_value={"sales": []})

        analyzer = SalesAnalyzer(api_client=mock_api)

        result = await analyzer.analyze_sales_volume("csgo", "No Sales Item")

        assert result["volume"] == "none"
        assert result["sales_count"] == 0

    @pytest.mark.asyncio()
    async def test_api_error_handling(self):
        """Тест обработки ошибок API."""
        mock_api = MagicMock()
        mock_api.get_sales_history = AsyncMock(side_effect=Exception("API Error"))

        analyzer = SalesAnalyzer(api_client=mock_api)

        with pytest.raises(Exception):
            await analyzer.get_item_sales_history("csgo", "Test Item")

    @pytest.mark.asyncio()
    async def test_invalid_price_format(self):
        """Тест обработки неверного формата цены."""
        mock_api = MagicMock()
        mock_api.get_sales_history = AsyncMock(
            return_value={
                "sales": [
                    {"date": "2023-11-01", "price": "invalid"},
                ],
            },
        )

        analyzer = SalesAnalyzer(api_client=mock_api)

        # Должно обработать без ошибки
        result = await analyzer.analyze_sales_volume("csgo", "Test Item")
        assert isinstance(result, dict)

"""Тесты для рефакторенного модуля market_analysis."""

from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.market_analysis_refactored import (
    _calculate_market_volatility_level,
    _determine_market_balance,
    _determine_market_health,
    _get_market_direction,
    _get_period_hours,
    _should_include_change,
    analyze_market_depth,
    analyze_market_volatility,
    analyze_price_changes,
    find_trending_items,
    generate_market_report,
)


@pytest.fixture()
def mock_dmarket_api():
    """Фикстура мокированного DMarket API клиента."""
    api = AsyncMock()
    api.get_market_items = AsyncMock(
        return_value={
            "items": [
                {
                    "title": "AK-47 | Redline (FT)",
                    "price": {"USD": "1000"},
                    "salesVolume": 10,
                    "offersCount": 5,
                    "imageUrl": "https://example.com/image.png",
                },
            ],
        }
    )
    api.get_aggregated_prices_bulk = AsyncMock(
        return_value={
            "aggregatedPrices": [
                {
                    "title": "AK-47 | Redline (FT)",
                    "orderCount": 10,
                    "offerCount": 15,
                    "orderBestPrice": "950",
                    "offerBestPrice": "1050",
                },
            ],
        }
    )
    return api


class TestPeriodHours:
    """Тесты функции _get_period_hours."""

    @pytest.mark.parametrize(
        ("period", "expected"),
        (
            ("1h", 1),
            ("3h", 3),
            ("6h", 6),
            ("12h", 12),
            ("24h", 24),
            ("7d", 168),
            ("30d", 720),
            ("invalid", 24),
        ),
    )
    def test_get_period_hours_returns_correct_value(self, period, expected):
        """Тест корректного возврата часов для периода."""
        result = _get_period_hours(period)
        assert result == expected


class TestShouldIncludeChange:
    """Тесты функции _should_include_change."""

    def test_should_include_change_up_direction_positive(self):
        """Тест включения роста цены при направлении 'up'."""
        result = _should_include_change(10.0, "up", 5.0)
        assert result is True

    def test_should_include_change_up_direction_negative(self):
        """Тест исключения падения цены при направлении 'up'."""
        result = _should_include_change(-10.0, "up", 5.0)
        assert result is False

    def test_should_include_change_down_direction_negative(self):
        """Тест включения падения цены при направлении 'down'."""
        result = _should_include_change(-10.0, "down", 5.0)
        assert result is True

    def test_should_include_change_down_direction_positive(self):
        """Тест исключения роста цены при направлении 'down'."""
        result = _should_include_change(10.0, "down", 5.0)
        assert result is False

    def test_should_include_change_below_threshold(self):
        """Тест исключения изменения ниже порога."""
        result = _should_include_change(3.0, "any", 5.0)
        assert result is False

    def test_should_include_change_above_threshold(self):
        """Тест включения изменения выше порога."""
        result = _should_include_change(10.0, "any", 5.0)
        assert result is True


class TestDetermineMarketBalance:
    """Тесты функции _determine_market_balance."""

    def test_determine_market_balance_buyer_dominated(self):
        """Тест определения рынка с преобладанием покупателей."""
        balance, description = _determine_market_balance(70, 30)
        assert balance == "buyer_dominated"
        assert "покупатели" in description.lower()

    def test_determine_market_balance_seller_dominated(self):
        """Тест определения рынка с преобладанием продавцов."""
        balance, description = _determine_market_balance(30, 70)
        assert balance == "seller_dominated"
        assert "продавцы" in description.lower()

    def test_determine_market_balance_balanced(self):
        """Тест определения сбалансированного рынка."""
        balance, description = _determine_market_balance(50, 50)
        assert balance == "balanced"
        assert "сбалансированный" in description.lower()


class TestDetermineMarketHealth:
    """Тесты функции _determine_market_health."""

    def test_determine_market_health_excellent(self):
        """Тест определения отличного здоровья рынка."""
        health = _determine_market_health(60, 3)
        assert health == "excellent"

    def test_determine_market_health_good(self):
        """Тест определения хорошего здоровья рынка."""
        health = _determine_market_health(40, 8)
        assert health == "good"

    def test_determine_market_health_fair(self):
        """Тест определения удовлетворительного здоровья рынка."""
        health = _determine_market_health(25, 12)
        assert health == "fair"

    def test_determine_market_health_poor(self):
        """Тест определения плохого здоровья рынка."""
        health = _determine_market_health(10, 20)
        assert health == "poor"


class TestGetMarketDirection:
    """Тесты функции _get_market_direction."""

    def test_get_market_direction_empty_list(self):
        """Тест определения направления при пустом списке."""
        result = _get_market_direction([])
        assert result == "stable"

    def test_get_market_direction_bullish(self):
        """Тест определения бычьего рынка."""
        price_changes = [
            {"direction": "up"},
            {"direction": "up"},
            {"direction": "up"},
            {"direction": "down"},
        ]
        result = _get_market_direction(price_changes)
        assert result == "bullish"

    def test_get_market_direction_bearish(self):
        """Тест определения медвежьего рынка."""
        price_changes = [
            {"direction": "down"},
            {"direction": "down"},
            {"direction": "down"},
            {"direction": "up"},
        ]
        result = _get_market_direction(price_changes)
        assert result == "bearish"

    def test_get_market_direction_neutral(self):
        """Тест определения нейтрального рынка."""
        price_changes = [
            {"direction": "up"},
            {"direction": "up"},
            {"direction": "down"},
            {"direction": "down"},
        ]
        result = _get_market_direction(price_changes)
        assert result == "neutral"


class TestCalculateMarketVolatilityLevel:
    """Тесты функции _calculate_market_volatility_level."""

    def test_calculate_market_volatility_level_empty(self):
        """Тест определения волатильности при пустом списке."""
        result = _calculate_market_volatility_level([])
        assert result == "unknown"

    def test_calculate_market_volatility_level_high(self):
        """Тест определения высокой волатильности."""
        volatile_items = [
            {"volatility_score": 25},
            {"volatility_score": 30},
        ]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "high"

    def test_calculate_market_volatility_level_medium(self):
        """Тест определения средней волатильности."""
        volatile_items = [
            {"volatility_score": 12},
            {"volatility_score": 15},
        ]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "medium"

    def test_calculate_market_volatility_level_low(self):
        """Тест определения низкой волатильности."""
        volatile_items = [
            {"volatility_score": 5},
            {"volatility_score": 8},
        ]
        result = _calculate_market_volatility_level(volatile_items)
        assert result == "low"


class TestAnalyzePriceChanges:
    """Тесты функции analyze_price_changes."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    @patch("src.dmarket.market_analysis_refactored._get_historical_prices")
    async def test_analyze_price_changes_returns_results(
        self,
        mock_historical,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест успешного анализа изменений цен."""
        mock_rate_limiter.wait_if_needed = AsyncMock()
        mock_historical.return_value = {"AK-47 | Redline (FT)": 8.0}

        result = await analyze_price_changes(
            game="csgo",
            period="24h",
            dmarket_api=mock_dmarket_api,
        )

        assert isinstance(result, list)
        mock_dmarket_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    async def test_analyze_price_changes_handles_empty_response(
        self,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест обработки пустого ответа API."""
        mock_rate_limiter.wait_if_needed = AsyncMock()
        mock_dmarket_api.get_market_items = AsyncMock(return_value=None)

        result = await analyze_price_changes(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result == []


class TestFindTrendingItems:
    """Тесты функции find_trending_items."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    async def test_find_trending_items_returns_results(
        self,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест успешного поиска трендовых предметов."""
        mock_rate_limiter.wait_if_needed = AsyncMock()

        result = await find_trending_items(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert isinstance(result, list)
        mock_dmarket_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    async def test_find_trending_items_filters_by_min_sales(
        self,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест фильтрации по минимальным продажам."""
        mock_rate_limiter.wait_if_needed = AsyncMock()
        mock_dmarket_api.get_market_items = AsyncMock(
            return_value={
                "items": [
                    {
                        "title": "Item 1",
                        "price": {"USD": "1000"},
                        "salesVolume": 3,
                        "offersCount": 5,
                    },
                    {
                        "title": "Item 2",
                        "price": {"USD": "2000"},
                        "salesVolume": 10,
                        "offersCount": 8,
                    },
                ],
            }
        )

        result = await find_trending_items(
            game="csgo",
            min_sales=5,
            dmarket_api=mock_dmarket_api,
        )

        assert len(result) == 1
        assert result[0]["market_hash_name"] == "Item 2"


class TestAnalyzeMarketVolatility:
    """Тесты функции analyze_market_volatility."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    @patch("src.dmarket.market_analysis_refactored._get_historical_prices")
    async def test_analyze_market_volatility_returns_results(
        self,
        mock_historical,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест успешного анализа волатильности."""
        mock_rate_limiter.wait_if_needed = AsyncMock()
        mock_historical.side_effect = [
            {"AK-47 | Redline (FT)": 9.0},  # 24h
            {"AK-47 | Redline (FT)": 8.0},  # 7d
        ]

        result = await analyze_market_volatility(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert isinstance(result, list)


class TestAnalyzeMarketDepth:
    """Тесты функции analyze_market_depth."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    async def test_analyze_market_depth_returns_results(
        self,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест успешного анализа глубины рынка."""
        mock_rate_limiter.wait_if_needed = AsyncMock()

        result = await analyze_market_depth(
            game="csgo",
            items=["AK-47 | Redline (FT)"],
            dmarket_api=mock_dmarket_api,
        )

        assert result["game"] == "csgo"
        assert result["items_analyzed"] == 1
        assert "market_depth" in result
        assert "summary" in result

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.rate_limiter")
    async def test_analyze_market_depth_handles_no_items(
        self,
        mock_rate_limiter,
        mock_dmarket_api,
    ):
        """Тест обработки отсутствия предметов."""
        mock_rate_limiter.wait_if_needed = AsyncMock()
        mock_dmarket_api.get_aggregated_prices_bulk = AsyncMock(return_value=None)

        result = await analyze_market_depth(
            game="csgo",
            items=["Test Item"],
            dmarket_api=mock_dmarket_api,
        )

        assert result["items_analyzed"] == 0
        assert result["market_depth"] == []


class TestGenerateMarketReport:
    """Тесты функции generate_market_report."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.analyze_price_changes")
    @patch("src.dmarket.market_analysis_refactored.find_trending_items")
    @patch("src.dmarket.market_analysis_refactored.analyze_market_volatility")
    @patch("src.dmarket.market_analysis_refactored.analyze_market_depth")
    async def test_generate_market_report_returns_complete_report(
        self,
        mock_depth,
        mock_volatility,
        mock_trending,
        mock_changes,
        mock_dmarket_api,
    ):
        """Тест генерации полного отчета о рынке."""
        mock_changes.return_value = []
        mock_trending.return_value = []
        mock_volatility.return_value = []
        mock_depth.return_value = {"summary": {}}

        result = await generate_market_report(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert result["game"] == "csgo"
        assert "timestamp" in result
        assert "price_changes" in result
        assert "trending_items" in result
        assert "volatile_items" in result
        assert "market_depth" in result
        assert "market_summary" in result

    @pytest.mark.asyncio()
    @patch("src.dmarket.market_analysis_refactored.analyze_price_changes")
    async def test_generate_market_report_handles_error(
        self,
        mock_changes,
        mock_dmarket_api,
    ):
        """Тест обработки ошибки при генерации отчета."""
        mock_changes.side_effect = Exception("Test error")

        result = await generate_market_report(
            game="csgo",
            dmarket_api=mock_dmarket_api,
        )

        assert "error" in result
        assert result["price_changes"] == []

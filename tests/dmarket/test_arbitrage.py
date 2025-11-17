"""Тесты для модуля arbitrage."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.arbitrage import (
    DEFAULT_FEE,
    GAMES,
    HIGH_FEE,
    LOW_FEE,
    MIN_PROFIT_PERCENT,
    PRICE_RANGES,
    ArbitrageTrader,
    _arbitrage_cache,
    _get_cached_results,
    _save_to_cache,
    arbitrage_boost,
    arbitrage_mid,
    arbitrage_pro,
    fetch_market_items,
    find_arbitrage_items,
    find_arbitrage_opportunities,
)


class TestConstants:
    """Тесты констант модуля."""

    def test_games_defined(self):
        """Тест наличия всех поддерживаемых игр."""
        expected_games = ["csgo", "dota2", "tf2", "rust"]
        for game in expected_games:
            assert game in GAMES

    def test_fee_values(self):
        """Тест корректности значений комиссий."""
        assert 0 < DEFAULT_FEE < 1
        assert 0 < LOW_FEE < DEFAULT_FEE
        assert DEFAULT_FEE < HIGH_FEE < 1

    def test_min_profit_percent_modes(self):
        """Тест наличия всех режимов прибыли."""
        expected_modes = ["low", "medium", "high", "boost", "pro"]
        for mode in expected_modes:
            assert mode in MIN_PROFIT_PERCENT

    def test_price_ranges_ascending(self):
        """Тест что диапазоны цен идут по возрастанию."""
        # Диапазоны: boost(0.5-3), low(1-5), medium(5-20),
        # high(20-100), pro(100-1000)
        # Проверяем, что минимальные цены растут для основных режимов
        assert PRICE_RANGES["low"][0] < PRICE_RANGES["medium"][0]
        assert PRICE_RANGES["medium"][0] < PRICE_RANGES["high"][0]
        assert PRICE_RANGES["high"][0] < PRICE_RANGES["pro"][0]


class TestCacheFunctions:
    """Тесты функций кэширования."""

    def setup_method(self):
        """Очистить кэш перед каждым тестом."""
        _arbitrage_cache.clear()

    def test_save_to_cache(self):
        """Тест сохранения в кэш."""
        cache_key = ("csgo", "medium", 5.0, 20.0)
        items = [{"title": "AK-47 | Redline", "price": 10.0}]

        _save_to_cache(cache_key, items)

        assert cache_key in _arbitrage_cache
        cached_items, timestamp = _arbitrage_cache[cache_key]
        assert cached_items == items
        assert timestamp > 0

    def test_get_cached_results_fresh(self):
        """Тест получения свежих данных из кэша."""
        cache_key = ("csgo", "medium", 5.0, 20.0)
        items = [{"title": "Test Item", "price": 15.0}]

        _save_to_cache(cache_key, items)
        cached_items = _get_cached_results(cache_key)

        assert cached_items == items

    def test_get_cached_results_expired(self):
        """Тест получения устаревших данных из кэша."""
        cache_key = ("csgo", "medium", 5.0, 20.0)
        items = [{"title": "Test Item", "price": 15.0}]

        # Старше 5 минут (300 секунд)
        expired_timestamp = time.time() - 400
        _arbitrage_cache[cache_key] = (items, expired_timestamp)

        cached_items = _get_cached_results(cache_key)
        assert cached_items is None

    def test_get_cached_results_not_exists(self):
        """Тест получения несуществующих данных из кэша."""
        cache_key = ("dota2", "high", 20.0, 100.0)
        cached_items = _get_cached_results(cache_key)
        assert cached_items is None

    def test_cache_key_uniqueness(self):
        """Тест уникальности ключей кэша."""
        key1 = ("csgo", "medium", 5.0, 20.0)
        key2 = ("csgo", "medium", 5.0, 20.1)
        key3 = ("dota2", "medium", 5.0, 20.0)

        items1 = [{"title": "Item1"}]
        items2 = [{"title": "Item2"}]
        items3 = [{"title": "Item3"}]

        _save_to_cache(key1, items1)
        _save_to_cache(key2, items2)
        _save_to_cache(key3, items3)

        assert _get_cached_results(key1) == items1
        assert _get_cached_results(key2) == items2
        assert _get_cached_results(key3) == items3


class TestFetchMarketItems:
    """Тесты функции fetch_market_items."""

    @pytest.mark.asyncio()
    async def test_fetch_market_items_success(self):
        """Тест успешного получения предметов."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(
            return_value={
                "objects": [
                    {"title": "AK-47 | Redline", "price": {"USD": 1250}},
                    {"title": "AWP | Asimov", "price": {"USD": 3500}},
                ],
            },
        )

        result = await fetch_market_items(
            game="csgo",
            limit=100,
            price_from=10.0,
            price_to=50.0,
            dmarket_api=mock_api,
        )

        assert len(result) == 2
        assert result[0]["title"] == "AK-47 | Redline"

    @pytest.mark.asyncio()
    async def test_fetch_market_items_empty(self):
        """Тест получения пустого списка предметов."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(return_value={"items": []})

        result = await fetch_market_items(dmarket_api=mock_api)
        assert result == []

    @pytest.mark.asyncio()
    async def test_fetch_market_items_api_error(self):
        """Тест обработки ошибки API."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(
            side_effect=Exception("API Error"),
        )

        result = await fetch_market_items(dmarket_api=mock_api)
        assert result == []


class TestArbitrageFunctions:
    """Тесты функций арбитража."""

    def test_arbitrage_boost(self):
        """Тест функции arbitrage_boost."""
        with patch("src.dmarket.arbitrage._find_arbitrage_async") as mock:
            mock.return_value = []
            result = arbitrage_boost(game="csgo")
            assert isinstance(result, list)

    def test_arbitrage_mid(self):
        """Тест функции arbitrage_mid."""
        with patch("src.dmarket.arbitrage._find_arbitrage_async") as mock:
            mock.return_value = []
            result = arbitrage_mid(game="csgo")
            assert isinstance(result, list)

    def test_arbitrage_pro(self):
        """Тест функции arbitrage_pro."""
        with patch("src.dmarket.arbitrage._find_arbitrage_async") as mock:
            mock.return_value = []
            result = arbitrage_pro(game="csgo")
            assert isinstance(result, list)


class TestArbitrageTrader:
    """Тесты класса ArbitrageTrader."""

    def test_arbitrage_trader_instantiation(self):
        """Тест создания экземпляра ArbitrageTrader."""
        trader = ArbitrageTrader(public_key="test_public", secret_key="test_secret")

        assert trader is not None
        assert trader.public_key == "test_public"
        assert trader.secret_key == "test_secret"
        assert trader.api is not None

    def test_arbitrage_trader_has_methods(self):
        """Тест наличия основных методов."""
        trader = ArbitrageTrader(public_key="test_public", secret_key="test_secret")

        assert hasattr(trader, "check_balance")
        assert hasattr(trader, "get_status")
        assert hasattr(trader, "get_transaction_history")
        assert trader.api is not None


class TestFindArbitrageItems:
    """Тесты функции find_arbitrage_items."""

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_basic(self):
        """Тест базового поиска арбитражных возможностей."""
        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=[],
        ):
            result = await find_arbitrage_items(
                game="csgo",
                mode="mid",
            )

            assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_different_modes(self):
        """Тест поиска с разными режимами."""
        for mode in ["low", "mid", "pro", "boost"]:
            with patch(
                "src.dmarket.arbitrage.fetch_market_items",
                return_value=[],
            ):
                result = await find_arbitrage_items(
                    game="csgo",
                    mode=mode,
                )

                assert isinstance(result, list)


class TestFindArbitrageOpportunities:
    """Тесты функции find_arbitrage_opportunities."""

    def test_find_arbitrage_opportunities_basic(self):
        """Тест базового поиска возможностей."""
        with patch(
            "src.dmarket.arbitrage.find_arbitrage_opportunities_async",
            return_value=[],
        ):
            result = find_arbitrage_opportunities(
                game="csgo",
                min_profit_percentage=10.0,
                max_results=5,
            )

            assert isinstance(result, list)


class TestIntegration:
    """Интеграционные тесты."""

    def setup_method(self):
        """Очистить кэш перед каждым тестом."""
        _arbitrage_cache.clear()

    @pytest.mark.asyncio()
    async def test_cache_workflow(self):
        """Тест полного цикла кэширования."""
        cache_key = ("csgo", "medium", 10.0, 50.0)
        test_items = [
            {"title": "Test Item 1", "price": 15.0},
            {"title": "Test Item 2", "price": 25.0},
        ]

        # Сохраняем в кэш
        _save_to_cache(cache_key, test_items)

        # Проверяем что данные сохранились
        assert cache_key in _arbitrage_cache

        # Получаем из кэша
        cached = _get_cached_results(cache_key)
        assert cached == test_items

        # Очищаем кэш
        _arbitrage_cache.clear()

        # Проверяем что кэш пуст
        cached = _get_cached_results(cache_key)
        assert cached is None

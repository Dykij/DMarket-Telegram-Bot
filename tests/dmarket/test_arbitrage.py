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


class TestFindArbitrageAsync:
    """Тесты функции _find_arbitrage_async."""

    def setup_method(self):
        """Очистить кэш перед каждым тестом."""
        _arbitrage_cache.clear()

    @pytest.mark.asyncio()
    async def test_find_arbitrage_async_with_items(self):
        """Тест поиска арбитража с реальными предметами."""
        from src.dmarket.arbitrage import _find_arbitrage_async

        mock_items = [
            {
                "title": "AK-47 | Redline (FT)",
                "itemId": "item_1",
                "price": {"amount": 1250},  # $12.50
                "suggestedPrice": {"amount": 1500},  # $15.00
                "extra": {"popularity": 0.8},
            },
            {
                "title": "AWP | Asiimov (FT)",
                "itemId": "item_2",
                "price": {"amount": 3500},  # $35.00
                "suggestedPrice": {"amount": 4200},  # $42.00
                "extra": {"popularity": 0.5},
            },
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            # Ищем прибыль от $1 до $10
            result = await _find_arbitrage_async(
                min_profit=1.0,
                max_profit=10.0,
                game="csgo",
            )

            assert isinstance(result, list)
            assert len(result) > 0
            # Проверяем структуру результата
            if result:
                item = result[0]
                assert "name" in item
                assert "buy" in item
                assert "sell" in item
                assert "profit" in item
                assert "profit_percent" in item

    @pytest.mark.asyncio()
    async def test_find_arbitrage_async_no_suggested_price(self):
        """Тест расчета цены продажи без suggestedPrice."""
        from src.dmarket.arbitrage import _find_arbitrage_async

        mock_items = [
            {
                "title": "M4A4 | Howl (FN)",
                "itemId": "item_3",
                "price": {"amount": 10000},  # $100.00
                "extra": {"popularity": 0.9},  # Высокая популярность
            },
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            result = await _find_arbitrage_async(
                min_profit=5.0,
                max_profit=20.0,
                game="csgo",
            )

            # Должен использовать markup
            assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_find_arbitrage_async_different_liquidity(self):
        """Тест учета ликвидности предметов."""
        from src.dmarket.arbitrage import _find_arbitrage_async

        mock_items = [
            {
                "title": "High Liquidity Item",
                "itemId": "item_high",
                "price": {"amount": 1000},
                "suggestedPrice": {"amount": 1200},
                "extra": {"popularity": 0.95},  # Высокая ликвидность
            },
            {
                "title": "Low Liquidity Item",
                "itemId": "item_low",
                "price": {"amount": 1000},
                "suggestedPrice": {"amount": 1200},
                "extra": {"popularity": 0.2},  # Низкая ликвидность
            },
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            result = await _find_arbitrage_async(
                min_profit=0.5,
                max_profit=5.0,
                game="csgo",
            )

            # Разная ликвидность должна давать разные комиссии
            assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_find_arbitrage_async_uses_cache(self):
        """Тест использования кэша."""
        from src.dmarket.arbitrage import _find_arbitrage_async

        cache_key = ("csgo", "1.0-5.0", 0.0, float("inf"))
        cached_data = [{"name": "Cached Item", "profit": "$3.00"}]
        _save_to_cache(cache_key, cached_data)

        # Не должен вызывать fetch_market_items
        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
        ) as mock_fetch:
            result = await _find_arbitrage_async(
                min_profit=1.0,
                max_profit=5.0,
                game="csgo",
            )

            # fetch_market_items не должен быть вызван
            mock_fetch.assert_not_called()
            assert result == cached_data


class TestFindArbitrageOpportunitiesAsync:
    """Тесты функции find_arbitrage_opportunities_async."""

    def setup_method(self):
        """Очистить кэш перед каждым тестом."""
        _arbitrage_cache.clear()

    @pytest.mark.asyncio()
    async def test_find_opportunities_with_items(self):
        """Тест поиска возможностей с предметами."""
        from src.dmarket.arbitrage import find_arbitrage_opportunities_async

        mock_items = [
            {
                "title": "AK-47 | Redline (FT)",
                "itemId": "item_1",
                "price": {"amount": 1000},  # $10.00
                "suggestedPrice": {"amount": 1300},  # $13.00
                "extra": {"popularity": 0.7},
            },
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            result = await find_arbitrage_opportunities_async(
                min_profit_percentage=10.0,
                max_results=5,
                game="csgo",
            )

            assert isinstance(result, list)
            if result:
                opp = result[0]
                assert "item_title" in opp
                assert "buy_price" in opp
                assert "sell_price" in opp
                assert "profit_amount" in opp
                assert "profit_percentage" in opp

    @pytest.mark.asyncio()
    async def test_find_opportunities_max_results_limit(self):
        """Тест ограничения количества результатов."""
        from src.dmarket.arbitrage import find_arbitrage_opportunities_async

        # Создаем 10 предметов
        mock_items = [
            {
                "title": f"Item {i}",
                "itemId": f"item_{i}",
                "price": {"amount": 1000 + i * 100},
                "suggestedPrice": {"amount": 1500 + i * 100},
                "extra": {"popularity": 0.5},
            }
            for i in range(10)
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            result = await find_arbitrage_opportunities_async(
                min_profit_percentage=5.0,
                max_results=3,
                game="csgo",
            )

            # Должно вернуть не более 3 результатов
            assert len(result) <= 3

    @pytest.mark.asyncio()
    async def test_find_opportunities_sorting(self):
        """Тест сортировки по проценту прибыли."""
        from src.dmarket.arbitrage import find_arbitrage_opportunities_async

        mock_items = [
            {
                "title": "Low Profit Item",
                "itemId": "item_low",
                "price": {"amount": 1000},
                "suggestedPrice": {"amount": 1100},  # 10% прибыли
                "extra": {"popularity": 0.5},
            },
            {
                "title": "High Profit Item",
                "itemId": "item_high",
                "price": {"amount": 1000},
                "suggestedPrice": {"amount": 1500},  # 50% прибыли
                "extra": {"popularity": 0.5},
            },
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            result = await find_arbitrage_opportunities_async(
                min_profit_percentage=5.0,
                max_results=2,
                game="csgo",
            )

            # Первый элемент должен иметь большую прибыль
            if len(result) >= 2:
                assert result[0]["profit_percentage"] >= result[1]["profit_percentage"]


class TestArbitrageTraderMethods:
    """Тесты методов класса ArbitrageTrader."""

    @pytest.mark.asyncio()
    async def test_trader_check_balance(self):
        """Тест проверки баланса."""
        # Мокаем DMarketAPI при создании трейдера
        with patch("src.dmarket.arbitrage.DMarketAPI") as mock_api_class:
            # Настраиваем мок API
            mock_api_instance = AsyncMock()
            mock_api_instance.__aenter__ = AsyncMock(return_value=mock_api_instance)
            mock_api_instance.__aexit__ = AsyncMock(return_value=None)
            mock_api_instance.get_user_balance = AsyncMock(
                return_value={"usd": {"amount": "100000"}, "dmc": {"amount": "50000"}}
            )
            mock_api_class.return_value = mock_api_instance

            # Создаем трейдера
            trader = ArbitrageTrader(
                public_key="test",
                secret_key="test",
            )

            has_funds, balance = await trader.check_balance()

            assert has_funds is True
            assert balance == 1000.0  # Проверяем конвертацию из центов

    @pytest.mark.asyncio()
    async def test_trader_check_balance_insufficient_funds(self):
        """Тест проверки баланса при недостаточных средствах."""
        # Мокаем DMarketAPI
        with patch("src.dmarket.arbitrage.DMarketAPI") as mock_api_class:
            mock_api_instance = AsyncMock()
            mock_api_instance.__aenter__ = AsyncMock(return_value=mock_api_instance)
            mock_api_instance.__aexit__ = AsyncMock(return_value=None)
            mock_api_instance.get_user_balance = AsyncMock(
                return_value={"usd": {"amount": "50"}}  # $0.50
            )
            mock_api_class.return_value = mock_api_instance

            trader = ArbitrageTrader(public_key="test", secret_key="test")

            has_funds, balance = await trader.check_balance()

            assert has_funds is False
            assert balance == 0.50

    def test_trader_get_status(self):
        """Тест получения статуса трейдера (НЕ async)."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")

        status = trader.get_status()  # Без await!

        assert isinstance(status, dict)
        assert "active" in status
        assert "min_profit_percentage" in status
        assert "current_game" in status
        assert status["active"] is False  # По умолчанию неактивен

    @pytest.mark.asyncio()
    async def test_trader_get_transaction_history(self):
        """Тест получения истории транзакций."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")

        history = trader.get_transaction_history()

        assert isinstance(history, list)
        assert len(history) == 0  # Изначально пустая

    @pytest.mark.asyncio()
    async def test_trader_reset_daily_limits(self):
        """Тест сброса дневных лимитов."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")

        # Устанавливаем дневную торговлю
        trader.daily_traded = 100.0
        # Устанавливаем время сброса на 25 часов назад
        trader.last_day_reset = time.time() - 90000  # >24 часа

        await trader._reset_daily_limits()

        # Должно сброситься
        assert trader.daily_traded == 0.0

    @pytest.mark.asyncio()
    async def test_trader_check_trading_limits_ok(self):
        """Тест проверки лимитов - допустимая сделка."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.max_trade_value = 100.0
        trader.daily_limit = 500.0
        trader.daily_traded = 0.0

        result = await trader._check_trading_limits(trade_value=50.0)

        assert result is True

    @pytest.mark.asyncio()
    async def test_trader_check_trading_limits_exceeds_max(self):
        """Тест проверки лимитов - превышение макс. сделки."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.max_trade_value = 100.0

        result = await trader._check_trading_limits(trade_value=150.0)

        assert result is False

    @pytest.mark.asyncio()
    async def test_trader_check_trading_limits_exceeds_daily(self):
        """Тест проверки лимитов - превышение дневного лимита."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.daily_limit = 500.0
        trader.daily_traded = 480.0  # Уже много торговали

        result = await trader._check_trading_limits(trade_value=30.0)

        assert result is False  # 480 + 30 > 500


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

    @pytest.mark.asyncio()
    async def test_full_arbitrage_workflow(self):
        """Тест полного цикла арбитража от поиска до результата."""
        from src.dmarket.arbitrage import find_arbitrage_opportunities_async

        mock_items = [
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "itemId": "item_ak47",
                "price": {"amount": 1250},
                "suggestedPrice": {"amount": 1500},
                "extra": {"popularity": 0.75},
            },
        ]

        with patch(
            "src.dmarket.arbitrage.fetch_market_items",
            return_value=mock_items,
        ):
            # Шаг 1: Поиск возможностей
            opportunities = await find_arbitrage_opportunities_async(
                min_profit_percentage=10.0,
                max_results=5,
                game="csgo",
            )

            assert len(opportunities) > 0

            # Шаг 2: Проверка структуры
            opp = opportunities[0]
            assert opp["item_title"] == "AK-47 | Redline (Field-Tested)"
            assert opp["buy_price"] == 12.50
            assert opp["sell_price"] == 15.00
            assert opp["profit_percentage"] >= 10.0

            # Шаг 3: Проверка кэширования
            cache_key = ("csgo", "arb-10.0", 0.0, float("inf"))
            assert cache_key in _arbitrage_cache


class TestArbitrageTraderAutoTrading:
    """Тесты автоматической торговли ArbitrageTrader."""

    @pytest.mark.asyncio()
    async def test_start_auto_trading_success(self):
        """Тест успешного запуска автоматической торговли."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.active = False

        # Mock check_balance для имитации достаточного баланса
        with patch.object(trader, "check_balance", return_value=(True, 100.0)):
            success, message = await trader.start_auto_trading(
                game="csgo",
                min_profit_percentage=5.0,
            )

        assert success is True
        assert "автоторговля запущена" in message.lower()
        assert trader.active is True
        assert trader.current_game == "csgo"

    @pytest.mark.asyncio()
    async def test_start_auto_trading_already_active(self):
        """Тест запуска автоторговли когда она уже запущена."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.active = True

        success, message = await trader.start_auto_trading()

        assert success is False
        assert "уже запущена" in message.lower()

    @pytest.mark.asyncio()
    async def test_start_auto_trading_insufficient_balance(self):
        """Тест запуска автоторговли с недостаточным балансом."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")

        with patch.object(trader, "check_balance", return_value=(False, 0.5)):
            success, message = await trader.start_auto_trading()

        assert success is False
        assert "недостаточно средств" in message.lower()
        assert trader.active is False

    @pytest.mark.asyncio()
    async def test_stop_auto_trading_success(self):
        """Тест успешной остановки автоторговли."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.active = True

        success, message = await trader.stop_auto_trading()

        assert success is True
        assert "остановлена" in message.lower()
        assert trader.active is False

    @pytest.mark.asyncio()
    async def test_stop_auto_trading_not_active(self):
        """Тест остановки неактивной автоторговли."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.active = False

        success, message = await trader.stop_auto_trading()

        assert success is False
        assert "не запущена" in message.lower()

    @pytest.mark.asyncio()
    async def test_execute_arbitrage_trade_insufficient_balance(self):
        """Тест выполнения сделки при недостаточном балансе."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")

        item = {
            "name": "Test Item",
            "market_hash_name": "Test Item",
            "buy_price": 100.0,
            "sell_price": 120.0,
            "profit": 16.0,
            "game": "csgo",
        }

        with (
            patch.object(trader, "_can_trade_now", return_value=True),
            patch.object(trader, "check_balance", return_value=(False, 50.0)),
        ):
            result = await trader.execute_arbitrage_trade(item)

        assert result["success"] is False
        assert "недостаточно средств" in str(result["errors"]).lower()

    @pytest.mark.asyncio()
    async def test_execute_arbitrage_trade_exceeds_limits(self):
        """Тест выполнения сделки при превышении лимитов."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")
        trader.max_trade_value = 50.0

        item = {
            "name": "Expensive Item",
            "market_hash_name": "Expensive Item",
            "buy_price": 100.0,
            "sell_price": 120.0,
            "profit": 16.0,
            "game": "csgo",
        }

        with (
            patch.object(trader, "_can_trade_now", return_value=True),
            patch.object(trader, "check_balance", return_value=(True, 200.0)),
            patch.object(trader, "_check_trading_limits", return_value=False),
        ):
            result = await trader.execute_arbitrage_trade(item)

        assert result["success"] is False
        assert "превышены лимиты" in str(result["errors"]).lower()

    @pytest.mark.asyncio()
    async def test_execute_arbitrage_trade_buy_error(self):
        """Тест ошибки при покупке предмета."""
        trader = ArbitrageTrader(public_key="test", secret_key="test")

        item = {
            "name": "Test Item",
            "market_hash_name": "Test Item",
            "buy_price": 10.0,
            "sell_price": 12.0,
            "profit": 1.6,
            "profit_percentage": 16.0,
            "game": "csgo",
        }

        mock_buy_error = {"error": "Предмет недоступен"}

        # Mock контекст-менеджер API
        mock_api_context = AsyncMock()
        mock_api_context.__aenter__ = AsyncMock(return_value=trader.api)
        mock_api_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch.object(trader, "_can_trade_now", return_value=True),
            patch.object(trader, "check_balance", return_value=(True, 100.0)),
            patch.object(trader, "_check_trading_limits", return_value=True),
            patch.object(trader, "api", mock_api_context),
            patch.object(trader.api, "buy_item", return_value=mock_buy_error),
            patch.object(trader, "_handle_trading_error"),
        ):
            result = await trader.execute_arbitrage_trade(item)

        assert result["success"] is False
        # Проверка наличия ошибки покупки
        error_found = any("ошибка при покупке" in str(e).lower() for e in result["errors"])
        assert error_found


class TestFindArbitrageItemsNew:
    """Тесты для функции find_arbitrage_items (новые)."""

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_low_mode(self):
        """Тест поиска предметов в режиме low/boost."""
        mock_results = [
            {
                "name": "Test Item",
                "buy_price": 1.0,
                "sell_price": 1.2,
                "profit": 0.16,
                "profit_percent": 16.0,
            }
        ]

        with patch(
            "src.dmarket.arbitrage.arbitrage_boost_async",
            return_value=mock_results,
        ):
            result = await find_arbitrage_items(
                game="csgo",
                mode="low",
                min_price=0.5,
                max_price=5.0,
            )

        assert len(result) == 1
        assert result[0]["name"] == "Test Item"

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_mid_mode(self):
        """Тест поиска предметов в режиме mid."""
        mock_results = [
            {
                "name": "Test Item 2",
                "buy_price": 10.0,
                "sell_price": 12.0,
                "profit": 1.6,
                "profit_percent": 16.0,
            }
        ]

        with patch(
            "src.dmarket.arbitrage.arbitrage_mid_async",
            return_value=mock_results,
        ):
            result = await find_arbitrage_items(
                game="csgo",
                mode="mid",
                min_price=5.0,
                max_price=20.0,
            )

        assert len(result) == 1
        assert result[0]["name"] == "Test Item 2"

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_pro_mode(self):
        """Тест поиска предметов в режиме pro."""
        mock_results = [
            {
                "name": "Expensive Item",
                "buy_price": 500.0,
                "sell_price": 600.0,
                "profit": 80.0,
                "profit_percent": 16.0,
            }
        ]

        with patch(
            "src.dmarket.arbitrage.arbitrage_pro_async",
            return_value=mock_results,
        ):
            result = await find_arbitrage_items(
                game="csgo",
                mode="pro",
                min_price=100.0,
                max_price=1000.0,
            )

        assert len(result) == 1
        assert result[0]["name"] == "Expensive Item"

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_tuple_conversion(self):
        """Тест конвертации результатов из формата кортежа."""
        # Возвращаем кортежи вместо словарей
        mock_results = [
            ("Item Name", 10.0, 12.0, 1.6, 16.0),
        ]

        with patch(
            "src.dmarket.arbitrage.arbitrage_mid_async",
            return_value=mock_results,
        ):
            result = await find_arbitrage_items(
                game="csgo",
                mode="mid",
            )

        assert len(result) == 1
        assert result[0]["market_hash_name"] == "Item Name"
        assert result[0]["buy_price"] == 10.0
        assert result[0]["sell_price"] == 12.0
        assert result[0]["profit"] == 1.6
        assert result[0]["profit_percent"] == 16.0

    @pytest.mark.asyncio()
    async def test_find_arbitrage_items_default_mode(self):
        """Тест режима по умолчанию при неизвестном режиме."""
        mock_results = [
            {
                "name": "Default Item",
                "buy_price": 5.0,
                "sell_price": 6.0,
                "profit": 0.8,
                "profit_percent": 16.0,
            }
        ]

        with patch(
            "src.dmarket.arbitrage.arbitrage_mid_async",
            return_value=mock_results,
        ):
            result = await find_arbitrage_items(
                game="csgo",
                mode="unknown_mode",
            )

        assert len(result) == 1
        assert result[0]["name"] == "Default Item"

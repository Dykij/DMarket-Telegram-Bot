"""Расширенные тесты для модуля arbitrage_scanner.

Этот модуль содержит тесты для ArbitrageScanner:
- Инициализация и конфигурация
- Сканирование игр
- Фильтрация результатов
- Кэширование
"""

from unittest.mock import MagicMock


class TestArbitrageScannerInit:
    """Тесты инициализации ArbitrageScanner."""

    def test_scanner_init_without_api_client(self):
        """Тест инициализации без API клиента."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner()

        assert scanner.api_client is None
        assert scanner._scanner_cache is not None
        assert scanner._scanner_filters is not None

    def test_scanner_init_with_api_client(self):
        """Тест инициализации с API клиентом."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        mock_client = MagicMock()
        scanner = ArbitrageScanner(api_client=mock_client)

        assert scanner.api_client is mock_client

    def test_scanner_init_with_filters(self):
        """Тест инициализации с фильтрами."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        from src.dmarket.item_filters import ItemFilters

        item_filters = ItemFilters()
        scanner = ArbitrageScanner(item_filters=item_filters)

        assert scanner._scanner_filters is not None

    def test_scanner_init_liquidity_filter_enabled(self):
        """Тест инициализации с включенным фильтром ликвидности."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(enable_liquidity_filter=True)

        assert scanner.enable_liquidity_filter is True

    def test_scanner_init_liquidity_filter_disabled(self):
        """Тест инициализации с выключенным фильтром ликвидности."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(enable_liquidity_filter=False)

        assert scanner.enable_liquidity_filter is False

    def test_scanner_init_competition_filter(self):
        """Тест инициализации с фильтром конкуренции."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(
            enable_competition_filter=True,
            max_competition=5,
        )

        assert scanner.enable_competition_filter is True
        assert scanner.max_competition == 5


class TestArbitrageLevels:
    """Тесты уровней арбитража."""

    def test_arbitrage_levels_defined(self):
        """Тест что уровни арбитража определены."""
        from src.dmarket.scanner import ARBITRAGE_LEVELS

        assert ARBITRAGE_LEVELS is not None
        assert isinstance(ARBITRAGE_LEVELS, dict)
        assert len(ARBITRAGE_LEVELS) > 0

    def test_arbitrage_levels_have_profit_keys(self):
        """Тест что уровни имеют ключи прибыли."""
        from src.dmarket.scanner import ARBITRAGE_LEVELS

        for level_name, level_config in ARBITRAGE_LEVELS.items():
            # Проверяем наличие хотя бы min_profit_percent
            assert (
                "min_profit_percent" in level_config
            ), f"Уровень {level_name} не имеет ключа min_profit_percent"

    def test_boost_level_exists(self):
        """Тест существования уровня boost."""
        from src.dmarket.scanner import ARBITRAGE_LEVELS

        assert "boost" in ARBITRAGE_LEVELS
        boost = ARBITRAGE_LEVELS["boost"]
        assert "min_profit_percent" in boost
        assert boost["min_profit_percent"] > 0


class TestGameIDs:
    """Тесты идентификаторов игр."""

    def test_game_ids_defined(self):
        """Тест что идентификаторы игр определены."""
        from src.dmarket.scanner import GAME_IDS

        assert GAME_IDS is not None
        assert isinstance(GAME_IDS, dict)

    def test_csgo_game_id(self):
        """Тест ID для CS:GO."""
        from src.dmarket.scanner import GAME_IDS

        assert "csgo" in GAME_IDS or "cs2" in GAME_IDS

    def test_dota2_game_id(self):
        """Тест ID для Dota 2."""
        from src.dmarket.scanner import GAME_IDS

        assert "dota2" in GAME_IDS


class TestScannerCache:
    """Тесты для кэша сканера."""

    def test_scanner_cache_init(self):
        """Тест инициализации кэша."""
        from src.dmarket.scanner import ScannerCache

        cache = ScannerCache(ttl=300, max_size=1000)

        assert cache is not None
        assert cache._ttl == 300
        assert cache._max_size == 1000

    def test_scanner_cache_get_set(self):
        """Тест получения и установки значений в кэше."""
        from src.dmarket.scanner import ScannerCache

        cache = ScannerCache(ttl=300, max_size=100)

        cache.set("test_key", {"value": 123})
        result = cache.get("test_key")

        assert result == {"value": 123}

    def test_scanner_cache_miss(self):
        """Тест промаха кэша."""
        from src.dmarket.scanner import ScannerCache

        cache = ScannerCache(ttl=300, max_size=100)

        result = cache.get("nonexistent_key")

        assert result is None

    def test_scanner_cache_clear(self):
        """Тест очистки кэша."""
        from src.dmarket.scanner import ScannerCache

        cache = ScannerCache(ttl=300, max_size=100)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestScannerFilters:
    """Тесты для фильтров сканера."""

    def test_scanner_filters_init(self):
        """Тест инициализации фильтров."""
        from src.dmarket.scanner import ScannerFilters

        filters = ScannerFilters()

        assert filters is not None

    def test_scanner_filters_with_item_filters(self):
        """Тест инициализации с ItemFilters."""
        from src.dmarket.item_filters import ItemFilters
        from src.dmarket.scanner import ScannerFilters

        item_filters = ItemFilters()
        scanner_filters = ScannerFilters(item_filters)

        assert scanner_filters is not None


class TestScannerHelperFunctions:
    """Тесты для вспомогательных функций."""

    def test_check_user_balance(self):
        """Тест проверки баланса пользователя."""
        from src.dmarket.arbitrage_scanner import check_user_balance

        # Функция должна существовать
        assert callable(check_user_balance)


class TestArbitrageScannerMethods:
    """Тесты методов ArbitrageScanner."""

    def test_scanner_has_scan_game_method(self):
        """Тест наличия метода scan_game."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner()

        assert hasattr(scanner, "scan_game")
        assert callable(scanner.scan_game)

    def test_scanner_get_cache_key(self):
        """Тест генерации ключа кэша."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner()

        # Проверяем что метод существует
        if hasattr(scanner, "_get_cache_key"):
            key = scanner._get_cache_key("csgo", "boost")
            assert isinstance(key, str)
            assert len(key) > 0

    def test_scanner_is_item_valid(self):
        """Тест валидации предмета."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner()

        # Проверяем что метод существует
        if hasattr(scanner, "_is_item_valid"):
            item = {"title": "Test Item", "price": {"USD": "1000"}}
            result = scanner._is_item_valid(item)
            assert isinstance(result, bool)


class TestMultiGameScanning:
    """Тесты сканирования нескольких игр."""

    def test_scan_multiple_games_function_exists(self):
        """Тест существования функции scan_multiple_games."""
        from src.dmarket.arbitrage_scanner import scan_multiple_games

        assert callable(scan_multiple_games)

    def test_find_multi_game_arbitrage_opportunities(self):
        """Тест поиска мульти-игровых арбитражных возможностей."""
        from src.dmarket.arbitrage_scanner import (
            find_multi_game_arbitrage_opportunities,
        )

        assert callable(find_multi_game_arbitrage_opportunities)


class TestArbitrageFunctions:
    """Тесты арбитражных функций."""

    def test_arbitrage_boost_function(self):
        """Тест функции arbitrage_boost."""
        from src.dmarket.arbitrage import arbitrage_boost

        assert callable(arbitrage_boost)

    def test_arbitrage_mid_function(self):
        """Тест функции arbitrage_mid."""
        from src.dmarket.arbitrage import arbitrage_mid

        assert callable(arbitrage_mid)

    def test_arbitrage_pro_function(self):
        """Тест функции arbitrage_pro."""
        from src.dmarket.arbitrage import arbitrage_pro

        assert callable(arbitrage_pro)


class TestArbitrageTrader:
    """Тесты для ArbitrageTrader."""

    def test_arbitrage_trader_exists(self):
        """Тест существования ArbitrageTrader."""
        from src.dmarket.arbitrage import ArbitrageTrader

        assert ArbitrageTrader is not None

    def test_arbitrage_trader_init(self):
        """Тест инициализации ArbitrageTrader."""
        from src.dmarket.arbitrage import ArbitrageTrader

        mock_api = MagicMock()
        trader = ArbitrageTrader(api_client=mock_api)

        # Trader инициализируется успешно
        assert trader is not None

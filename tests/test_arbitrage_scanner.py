"""Тесты для модуля arbitrage_scanner."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.arbitrage_scanner import ARBITRAGE_LEVELS, ArbitrageScanner


@pytest.fixture
def mock_api():
    """Мок DMarketAPI для тестирования."""
    api = MagicMock()
    api.get_market_items = AsyncMock()
    return api


@pytest.fixture
def scanner(mock_api):
    """Экземпляр ArbitrageScanner с моком API."""
    return ArbitrageScanner(api_client=mock_api)


@pytest.fixture
def sample_market_items():
    """Образец данных с рынка DMarket."""
    return {
        "objects": [
            {
                "itemId": "item1",
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": 1500},  # $15.00 в центах
                "suggestedPrice": {"USD": 1800},  # $18.00
                "image": "https://example.com/image1.png",
                "extra": {"float": 0.25},
            },
            {
                "itemId": "item2",
                "title": "AWP | Asiimov (Well-Worn)",
                "price": {"USD": 5000},  # $50.00
                "suggestedPrice": {"USD": 6000},  # $60.00
                "image": "https://example.com/image2.png",
                "extra": {"float": 0.42},
            },
            {
                "itemId": "item3",
                "title": "Cheap Skin",
                "price": {"USD": 150},  # $1.50
                "suggestedPrice": {"USD": 170},  # $1.70
                "image": "https://example.com/image3.png",
                "extra": {},
            },
        ],
    }


class TestArbitrageScanner:
    """Тесты для класса ArbitrageScanner."""

    def test_initialization(self, mock_api):
        """Тест инициализации сканера."""
        scanner = ArbitrageScanner(api_client=mock_api)
        assert scanner.api_client == mock_api
        assert scanner._cache == {}

    def test_get_level_config_valid(self, scanner):
        """Тест получения конфигурации существующего уровня."""
        config = scanner.get_level_config("boost")
        assert config == ARBITRAGE_LEVELS["boost"]
        assert config["name"] == "🚀 Разгон баланса"
        assert config["price_range"] == (0.5, 3.0)

    def test_get_level_config_invalid(self, scanner):
        """Тест получения конфигурации несуществующего уровня."""
        with pytest.raises(ValueError, match="Неизвестный уровень"):
            scanner.get_level_config("invalid_level")

    def test_cache_operations(self, scanner):
        """Тест операций с кэшем."""
        cache_key = "test_key"
        test_data = [{"item": "data"}]

        # Сначала кэш пустой
        assert scanner._get_from_cache(cache_key) is None

        # Сохраняем в кэш
        scanner._save_to_cache(cache_key, test_data)

        # Проверяем что данные вернулись
        cached = scanner._get_from_cache(cache_key)
        assert cached == test_data

    def test_cache_expiration(self, scanner):
        """Тест истечения срока кэша."""
        scanner.cache_ttl = -1  # Кэш истекает сразу
        cache_key = "test_key"
        test_data = [{"item": "data"}]

        scanner._save_to_cache(cache_key, test_data)

        # Кэш должен быть удален из-за истечения срока
        assert scanner._get_from_cache(cache_key) is None

    @pytest.mark.asyncio
    async def test_scan_level_boost(self, scanner, mock_api, sample_market_items):
        """Тест сканирования уровня 'boost'."""
        mock_api.get_market_items.return_value = sample_market_items

        results = await scanner.scan_level("boost", game="csgo", max_results=10)

        # Проверяем что API был вызван с правильными параметрами
        mock_api.get_market_items.assert_called_once()
        call_kwargs = mock_api.get_market_items.call_args[1]
        assert call_kwargs["game"] == "a8db"  # csgo game ID
        assert call_kwargs["price_from"] == 50  # $0.5 в центах
        assert call_kwargs["price_to"] == 300  # $3.0 в центах

        # Проверяем результаты - только item3 подходит под boost ($1.50)
        assert isinstance(results, list)
        assert len(results) <= 10

    @pytest.mark.asyncio
    async def test_scan_level_standard(self, scanner, mock_api, sample_market_items):
        """Тест сканирования уровня 'standard'."""
        mock_api.get_market_items.return_value = sample_market_items

        results = await scanner.scan_level("standard", game="csgo", max_results=10)

        # Проверяем что API был вызван
        mock_api.get_market_items.assert_called_once()
        call_kwargs = mock_api.get_market_items.call_args[1]
        assert call_kwargs["price_from"] == 300  # $3.0 в центах
        assert call_kwargs["price_to"] == 1000  # $10.0 в центах

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_level_with_cache(self, scanner, mock_api, sample_market_items):
        """Тест использования кэша при сканировании."""
        mock_api.get_market_items.return_value = sample_market_items

        # Первый вызов - должен обратиться к API
        results1 = await scanner.scan_level("boost", game="csgo", use_cache=True)
        assert mock_api.get_market_items.call_count == 1

        # Второй вызов - должен использовать кэш
        results2 = await scanner.scan_level("boost", game="csgo", use_cache=True)
        assert mock_api.get_market_items.call_count == 1  # Не увеличился
        assert results1 == results2

    @pytest.mark.asyncio
    async def test_scan_level_without_cache(
        self,
        scanner,
        mock_api,
        sample_market_items,
    ):
        """Тест сканирования без использования кэша."""
        mock_api.get_market_items.return_value = sample_market_items

        # Два вызова без кэша
        await scanner.scan_level("boost", game="csgo", use_cache=False)
        await scanner.scan_level("boost", game="csgo", use_cache=False)

        # Оба раза должен обращаться к API
        assert mock_api.get_market_items.call_count == 2

    @pytest.mark.asyncio
    async def test_scan_level_invalid_game(self, scanner):
        """Тест сканирования с неподдерживаемой игрой."""
        with pytest.raises(ValueError, match="не поддерживается"):
            await scanner.scan_level("boost", game="invalid_game")

    @pytest.mark.asyncio
    async def test_analyze_item_profitable(self, scanner):
        """Тест анализа прибыльного предмета."""
        item = {
            "itemId": "test1",
            "title": "Test Item",
            "price": {"USD": 1000},  # $10.00
            "suggestedPrice": {"USD": 1200},  # $12.00
            "image": "test.png",
            "extra": {},
        }
        config = ARBITRAGE_LEVELS["standard"]

        result = await scanner._analyze_item(item, config, "csgo")

        assert result is not None
        assert result["buy_price"] == 10.0
        assert result["suggested_price"] == 12.0
        assert result["profit"] > 0
        assert result["profit_percent"] > config["min_profit_percent"]

    @pytest.mark.asyncio
    async def test_analyze_item_not_profitable(self, scanner):
        """Тест анализа неприбыльного предмета."""
        item = {
            "itemId": "test2",
            "title": "Test Item",
            "price": {"USD": 1000},  # $10.00
            "suggestedPrice": {"USD": 1010},  # $10.10 - мало прибыли
            "image": "test.png",
            "extra": {},
        }
        config = ARBITRAGE_LEVELS["standard"]

        result = await scanner._analyze_item(item, config, "csgo")

        # Не должно пройти проверку минимальной прибыли
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_item_out_of_range(self, scanner):
        """Тест анализа предмета вне ценового диапазона."""
        item = {
            "itemId": "test3",
            "title": "Expensive Item",
            "price": {"USD": 5000},  # $50.00 - вне диапазона standard
            "suggestedPrice": {"USD": 6000},
            "image": "test.png",
            "extra": {},
        }
        config = ARBITRAGE_LEVELS["standard"]  # $3-$10 range

        result = await scanner._analyze_item(item, config, "csgo")

        # Не должно пройти проверку ценового диапазона
        assert result is None

    @pytest.mark.asyncio
    async def test_scan_all_levels(self, scanner, mock_api, sample_market_items):
        """Тест сканирования всех уровней."""
        mock_api.get_market_items.return_value = sample_market_items

        results = await scanner.scan_all_levels("csgo", max_results_per_level=5)

        # Должны быть результаты для всех уровней
        assert len(results) == len(ARBITRAGE_LEVELS)
        assert all(level in results for level in ARBITRAGE_LEVELS)
        assert all(isinstance(opps, list) for opps in results.values())

    @pytest.mark.asyncio
    async def test_find_best_opportunities(
        self,
        scanner,
        mock_api,
        sample_market_items,
    ):
        """Тест поиска лучших возможностей."""
        mock_api.get_market_items.return_value = sample_market_items

        results = await scanner.find_best_opportunities(
            game="csgo",
            top_n=5,
            min_level="boost",
            max_level="standard",
        )

        assert isinstance(results, list)
        assert len(results) <= 5
        # Результаты должны быть отсортированы по profit_percent
        if len(results) > 1:
            profits = [r["profit_percent"] for r in results]
            assert profits == sorted(profits, reverse=True)

    @pytest.mark.asyncio
    async def test_find_best_opportunities_invalid_level(self, scanner):
        """Тест с неверными уровнями."""
        with pytest.raises(ValueError):
            await scanner.find_best_opportunities(
                game="csgo",
                min_level="invalid",
                max_level="boost",
            )

    def test_get_level_stats(self, scanner):
        """Тест получения статистики уровней."""
        stats = scanner.get_level_stats()

        assert len(stats) == len(ARBITRAGE_LEVELS)
        assert "boost" in stats
        assert "name" in stats["boost"]
        assert "price_range" in stats["boost"]
        assert "min_profit" in stats["boost"]

    @pytest.mark.asyncio
    async def test_get_market_overview(self, scanner, mock_api, sample_market_items):
        """Тест получения обзора рынка."""
        mock_api.get_market_items.return_value = sample_market_items

        overview = await scanner.get_market_overview("csgo")

        assert overview["game"] == "csgo"
        assert "total_opportunities" in overview
        assert "best_profit_percent" in overview
        assert "best_level" in overview
        assert "results_by_level" in overview
        assert "scanned_at" in overview

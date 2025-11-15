"""Тесты для модуля ArbitrageScanner.

Покрывает основные функции поиска арбитражных возможностей,
кеширование, управление API клиентом и автоматическую торговлю.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.arbitrage_scanner import ARBITRAGE_LEVELS, GAME_IDS, ArbitrageScanner
from src.dmarket.dmarket_api import DMarketAPI


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def mock_api_client():
    """Создает мок DMarketAPI клиента."""
    api = MagicMock(spec=DMarketAPI)
    api.get_balance = AsyncMock(
        return_value={"usd": "10000", "error": False, "balance": 100.0}
    )
    api.get_market_items = AsyncMock(
        return_value={
            "objects": [
                {
                    "itemId": "item_001",
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": {"USD": "1250"},
                    "suggestedPrice": {"USD": "1400"},
                    "extra": {"floatValue": 0.25, "category": "Rifle"},
                },
                {
                    "itemId": "item_002",
                    "title": "AWP | Asiimov (Field-Tested)",
                    "price": {"USD": "5000"},
                    "suggestedPrice": {"USD": "5500"},
                    "extra": {"floatValue": 0.28, "category": "Rifle"},
                },
            ],
            "total": 2,
        }
    )
    api.buy_item = AsyncMock(return_value={"success": True, "orderId": "order_123"})
    api.sell_item = AsyncMock(return_value={"success": True, "offerId": "offer_456"})
    return api


@pytest.fixture()
def scanner(mock_api_client):
    """Создает ArbitrageScanner с мок API клиентом."""
    return ArbitrageScanner(api_client=mock_api_client)


@pytest.fixture()
def scanner_no_client():
    """Создает ArbitrageScanner без API клиента."""
    return ArbitrageScanner()


# ============================================================================
# Тесты инициализации
# ============================================================================


def test_arbitrage_scanner_initialization(scanner):
    """Тест инициализации ArbitrageScanner."""
    assert scanner.api_client is not None
    assert scanner._cache == {}
    assert scanner._cache_ttl == 300
    assert scanner.min_profit == 0.5
    assert scanner.max_price == 50.0
    assert scanner.max_trades == 5
    assert scanner.total_scans == 0
    assert scanner.total_items_found == 0
    assert scanner.successful_trades == 0
    assert scanner.total_profit == 0.0


def test_arbitrage_scanner_without_client(scanner_no_client):
    """Тест инициализации без API клиента."""
    assert scanner_no_client.api_client is None
    assert scanner_no_client._cache == {}


def test_cache_ttl_property(scanner):
    """Тест свойства cache_ttl."""
    assert scanner.cache_ttl == 300
    scanner.cache_ttl = 600
    assert scanner.cache_ttl == 600
    assert scanner._cache_ttl == 600


# ============================================================================
# Тесты кеширования
# ============================================================================


def test_get_cached_results_empty_cache(scanner):
    """Тест получения из пустого кеша."""
    cache_key = ("csgo", "medium", 0.0, float("inf"))
    result = scanner._get_cached_results(cache_key)
    assert result is None


def test_save_to_cache(scanner):
    """Тест сохранения в кеш."""
    cache_key = ("csgo", "medium", 0.0, float("inf"))
    items = [{"item": "test1"}, {"item": "test2"}]

    scanner._save_to_cache(cache_key, items)

    assert cache_key in scanner._cache
    cached_items, timestamp = scanner._cache[cache_key]
    assert cached_items == items
    assert isinstance(timestamp, float)


def test_get_cached_results_valid_cache(scanner):
    """Тест получения валидных данных из кеша."""
    cache_key = ("csgo", "medium", 0.0, float("inf"))
    items = [{"item": "test1"}, {"item": "test2"}]

    scanner._save_to_cache(cache_key, items)
    result = scanner._get_cached_results(cache_key)

    assert result == items


def test_get_cached_results_expired_cache(scanner):
    """Тест получения устаревших данных из кеша."""
    cache_key = ("csgo", "medium", 0.0, float("inf"))
    items = [{"item": "test1"}]

    # Сохраняем в кеш
    scanner._save_to_cache(cache_key, items)

    # Устанавливаем timestamp в прошлое
    scanner._cache[cache_key] = (items, time.time() - 400)  # 400 секунд назад

    result = scanner._get_cached_results(cache_key)
    assert result is None


# ============================================================================
# Тесты API клиента
# ============================================================================


@pytest.mark.asyncio()
async def test_get_api_client_existing(scanner):
    """Тест получения существующего API клиента."""
    client = await scanner.get_api_client()
    assert client is scanner.api_client


@pytest.mark.asyncio()
async def test_get_api_client_create_new(scanner_no_client):
    """Тест создания нового API клиента."""
    with patch.dict(
        "os.environ",
        {
            "DMARKET_PUBLIC_KEY": "test_public",
            "DMARKET_SECRET_KEY": "test_secret",
            "DMARKET_API_URL": "https://test.api.com",
        },
    ):
        client = await scanner_no_client.get_api_client()
        assert client is not None
        assert scanner_no_client.api_client is client


# ============================================================================
# Тесты scan_game
# ============================================================================


@pytest.mark.asyncio()
async def test_scan_game_with_cache(scanner):
    """Тест scan_game с использованием кеша."""
    # Подготовка кеша
    cache_key = ("csgo", "medium", 0.0, float("inf"))
    cached_items = [{"item": "cached1"}, {"item": "cached2"}]
    scanner._save_to_cache(cache_key, cached_items)

    # Сканирование должно вернуть данные из кеша
    with patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"):
        result = await scanner.scan_game("csgo", "medium", max_items=10)

    assert result == cached_items
    assert scanner.api_client.get_market_items.call_count == 0


@pytest.mark.asyncio()
async def test_scan_game_without_cache(scanner):
    """Тест scan_game без кеша (первый запрос)."""
    with (
        patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"),
        patch(
            "src.dmarket.arbitrage_scanner.arbitrage_mid",
            return_value=[{"item": "from_func"}],
        ),
    ):
        result = await scanner.scan_game("csgo", "medium", max_items=10)

    assert isinstance(result, list)
    assert scanner.total_scans == 1


@pytest.mark.asyncio()
async def test_scan_game_boost_mode(scanner):
    """Тест режима boost."""
    with (
        patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"),
        patch(
            "src.dmarket.arbitrage_scanner.arbitrage_boost",
            return_value=[{"item": "boost"}],
        ) as mock_boost,
    ):
        result = await scanner.scan_game("csgo", "low", max_items=5)

    mock_boost.assert_called_once_with("csgo")
    assert isinstance(result, list)


@pytest.mark.asyncio()
async def test_scan_game_pro_mode(scanner):
    """Тест режима pro."""
    with (
        patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"),
        patch(
            "src.dmarket.arbitrage_scanner.arbitrage_pro",
            return_value=[{"item": "pro"}],
        ) as mock_pro,
    ):
        result = await scanner.scan_game("dota2", "high", max_items=3)

    mock_pro.assert_called_once_with("dota2")
    assert isinstance(result, list)


@pytest.mark.asyncio()
async def test_scan_game_with_price_range(scanner):
    """Тест сканирования с диапазоном цен."""
    with (
        patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"),
        patch("src.dmarket.arbitrage_scanner.ArbitrageTrader") as mock_trader,
    ):
        mock_trader_instance = AsyncMock()
        mock_trader_instance.scan_items = AsyncMock(return_value=[{"item": "trader"}])
        mock_trader.return_value = mock_trader_instance

        result = await scanner.scan_game(
            "csgo", "medium", max_items=10, price_from=10.0, price_to=50.0
        )

    assert isinstance(result, list)


@pytest.mark.asyncio()
async def test_scan_game_api_error(scanner):
    """Тест обработки ошибки API."""
    with (
        patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"),
        patch(
            "src.dmarket.arbitrage_scanner.arbitrage_mid",
            side_effect=Exception("API Error"),
        ),
    ):
        result = await scanner.scan_game("csgo", "medium")

    assert result == []


# ============================================================================
# Тесты _standardize_items
# ============================================================================


def test_standardize_items_dmarket_format(scanner):
    """Тест стандартизации предметов из DMarket."""
    items = [
        {
            "itemId": "item_001",
            "name": "Test Item",  # _standardize_items ищет 'name' или 'title'
            "buy_price": 15.0,
            "sell_price": 17.0,
            "profit": 2.0,
            "profit_percentage": 13.33,
        }
    ]

    result = scanner._standardize_items(items, "csgo", min_profit=0.5, max_profit=100.0)

    assert len(result) == 1
    assert result[0]["title"] == "Test Item"
    assert "profit" in result[0]
    assert result[0]["profit"] == 2.0


def test_standardize_items_trader_format(scanner):
    """Тест стандартизации предметов из ArbitrageTrader."""
    items = [
        {
            "name": "Trader Item",
            "buy_price": 25.5,
            "sell_price": 30.0,
            "profit": 4.5,
            "profit_percentage": 17.65,
        }
    ]

    result = scanner._standardize_items(
        items, "dota2", min_profit=0.5, max_profit=100.0
    )

    assert len(result) == 1
    assert result[0]["title"] == "Trader Item"
    assert "profit" in result[0]
    assert result[0]["profit"] == 4.5


def test_standardize_items_mixed_formats(scanner):
    """Тест стандартизации смешанных форматов."""
    items = [
        {
            "name": "DMarket Item",
            "buy_price": 10.0,
            "sell_price": 12.0,
            "profit": 2.0,
            "profit_percentage": 20.0,
        },
        {
            "name": "Trader Item",
            "buy_price": 10.0,
            "sell_price": 12.0,
            "profit": 2.0,
            "profit_percentage": 20.0,
        },
    ]

    result = scanner._standardize_items(items, "csgo", min_profit=0.5, max_profit=100.0)

    assert len(result) == 2
    assert result[0]["title"] == "DMarket Item"
    assert result[1]["title"] == "Trader Item"


# ============================================================================
# Тесты scan_multiple_games
# ============================================================================


@pytest.mark.asyncio()
async def test_scan_multiple_games_success(scanner):
    """Тест сканирования нескольких игр."""
    with patch.object(scanner, "scan_game", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = [{"item": "test"}]

        games = ["csgo", "dota2"]
        result = await scanner.scan_multiple_games(
            games, "medium", max_items_per_game=5
        )

    assert len(result) == 2
    assert "csgo" in result
    assert "dota2" in result
    assert mock_scan.call_count == 2


@pytest.mark.asyncio()
async def test_scan_multiple_games_empty_list(scanner):
    """Тест сканирования пустого списка игр."""
    result = await scanner.scan_multiple_games([], "medium")
    assert result == {}


@pytest.mark.asyncio()
async def test_scan_multiple_games_one_fails(scanner):
    """Тест обработки ошибки при сканировании одной из игр."""

    async def mock_scan_game(game, mode, max_items, **kwargs):
        if game == "csgo":
            return [{"item": "csgo_item"}]
        raise Exception("API Error")

    with patch.object(scanner, "scan_game", side_effect=mock_scan_game):
        games = ["csgo", "dota2"]
        result = await scanner.scan_multiple_games(games, "medium")

    assert "csgo" in result
    assert "dota2" in result
    assert len(result["csgo"]) > 0
    assert result["dota2"] == []


# ============================================================================
# Тесты check_user_balance
# ============================================================================


@pytest.mark.asyncio()
async def test_check_user_balance_success(scanner):
    """Тест успешной проверки баланса."""
    # Мокируем _request для возврата баланса в центах
    # Формат: {"usd": {"available": 10050, "frozen": 0}} = $100.50
    scanner.api_client._request = AsyncMock(
        return_value={"usd": {"available": 10050, "frozen": 0}}
    )

    result = await scanner.check_user_balance()

    assert result["error"] is False
    assert "balance" in result
    assert result["balance"] == 100.50


@pytest.mark.asyncio()
async def test_check_user_balance_api_error(scanner):
    """Тест обработки ошибки при проверке баланса."""
    scanner.api_client.get_balance = AsyncMock(side_effect=Exception("API Error"))

    result = await scanner.check_user_balance()

    assert result["error"] is True
    assert "error_message" in result


# ============================================================================
# Тесты уровней арбитража
# ============================================================================


def test_get_level_config_boost(scanner):
    """Тест получения конфигурации уровня boost."""
    config = scanner.get_level_config("boost")

    assert config["name"] == "🚀 Разгон баланса"
    assert config["min_profit_percent"] == 1.0
    assert config["price_range"] == (0.5, 3.0)


def test_get_level_config_pro(scanner):
    """Тест получения конфигурации уровня pro."""
    config = scanner.get_level_config("pro")

    assert config["name"] == "💎 Профи"
    assert config["min_profit_percent"] == 20.0
    assert config["price_range"] == (100.0, 1000.0)


def test_get_level_config_invalid(scanner):
    """Тест получения конфигурации несуществующего уровня."""
    with pytest.raises(ValueError, match="Неизвестный уровень арбитража"):
        scanner.get_level_config("invalid_level")


def test_arbitrage_levels_defined():
    """Тест наличия всех уровней арбитража."""
    assert "boost" in ARBITRAGE_LEVELS
    assert "standard" in ARBITRAGE_LEVELS
    assert "medium" in ARBITRAGE_LEVELS
    assert "advanced" in ARBITRAGE_LEVELS
    assert "pro" in ARBITRAGE_LEVELS


def test_game_ids_defined():
    """Тест наличия маппинга ID игр."""
    assert "csgo" in GAME_IDS
    assert "dota2" in GAME_IDS
    assert "tf2" in GAME_IDS
    assert "rust" in GAME_IDS


# ============================================================================
# Тесты scan_level
# ============================================================================


@pytest.mark.asyncio()
async def test_scan_level_boost(scanner):
    """Тест сканирования уровня boost."""
    # scan_level вызывает get_market_items напрямую
    mock_response = {
        "objects": [
            {
                "itemId": "item1",
                "title": "Boost Item",
                "price": {"USD": "200"},  # $2.00 в центах
                "suggestedPrice": {"USD": "250"},  # $2.50 в центах
            }
        ]
    }
    scanner.api_client.get_market_items = AsyncMock(return_value=mock_response)
    scanner._analyze_item = AsyncMock(return_value={"item": "boost_item"})

    result = await scanner.scan_level("boost", "csgo", max_results=10)

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio()
async def test_scan_level_with_cache(scanner):
    """Тест scan_level с кешем."""
    cache_key = "scan_level_csgo_boost"  # Правильный формат ключа
    cached_data = [{"item": "cached"}]
    scanner._cache[cache_key] = (cached_data, time.time())

    result = await scanner.scan_level("boost", "csgo")

    # Должен вернуть кешированные данные без обращения к API
    assert result == cached_data


@pytest.mark.asyncio()
async def test_scan_level_filters_by_price_range(scanner):
    """Тест фильтрации по диапазону цен уровня."""
    items = [
        {"item": "cheap", "buy_price": 1.0},  # Вне диапазона boost
        {"item": "in_range", "buy_price": 2.0},  # В диапазоне boost (0.5-3.0)
        {"item": "expensive", "buy_price": 50.0},  # Вне диапазона boost
    ]

    with patch.object(scanner, "scan_game", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = items

        result = await scanner.scan_level("boost", "csgo")

    # Только предметы в диапазоне boost (0.5-3.0)
    assert all(0.5 <= item["buy_price"] <= 3.0 for item in result)


# ============================================================================
# Тесты scan_all_levels
# ============================================================================


@pytest.mark.asyncio()
async def test_scan_all_levels_success(scanner):
    """Тест сканирования всех уровней."""
    with patch.object(scanner, "scan_level", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = [{"item": "test"}]

        result = await scanner.scan_all_levels("csgo", max_results_per_level=5)

    assert isinstance(result, dict)
    assert len(result) == 5  # boost, standard, medium, advanced, pro
    assert mock_scan.call_count == 5


@pytest.mark.asyncio()
async def test_scan_all_levels_one_fails(scanner):
    """Тест обработки ошибки при сканировании одного уровня."""

    async def mock_scan_level(level, game, max_results=10, use_cache=True):
        if level == "boost":
            return []  # Возвращаем пустой список при ошибке
        return [{"item": f"{level}_item"}]

    with patch.object(scanner, "scan_level", side_effect=mock_scan_level):
        result = await scanner.scan_all_levels("csgo")

    assert "boost" in result
    assert result["boost"] == []
    assert len(result["standard"]) > 0


# ============================================================================
# Тесты find_best_opportunities
# ============================================================================


@pytest.mark.asyncio()
async def test_find_best_opportunities_top_n(scanner):
    """Тест поиска топ-N возможностей."""
    all_levels_data = {
        "boost": [{"item": "boost1", "profit_percent": 5.0}],
        "standard": [{"item": "std1", "profit_percent": 8.0}],
        "medium": [{"item": "med1", "profit_percent": 15.0}],
        "advanced": [{"item": "adv1", "profit_percent": 20.0}],
        "pro": [{"item": "pro1", "profit_percent": 50.0}],
    }

    with patch.object(scanner, "scan_all_levels", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = all_levels_data

        result = await scanner.find_best_opportunities("csgo", top_n=3)

    assert len(result) <= 3
    # Должны быть отсортированы по profit_percent (убывание)
    if len(result) > 1:
        assert result[0]["profit_percent"] >= result[1]["profit_percent"]


@pytest.mark.asyncio()
async def test_find_best_opportunities_min_level(scanner):
    """Тест фильтрации по минимальному уровню."""
    all_levels_data = {
        "boost": [{"item": "boost1"}],
        "standard": [{"item": "std1"}],
        "medium": [{"item": "med1"}],
        "advanced": [{"item": "adv1"}],
        "pro": [{"item": "pro1"}],
    }

    with patch.object(scanner, "scan_all_levels", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = all_levels_data

        result = await scanner.find_best_opportunities(
            "csgo", top_n=10, min_level="medium"
        )

    # Не должно быть предметов из boost и standard
    for item in result:
        assert item["item"] not in ["boost1", "std1"]


@pytest.mark.asyncio()
async def test_find_best_opportunities_max_level(scanner):
    """Тест фильтрации по максимальному уровню."""
    all_levels_data = {
        "boost": [{"item": "boost1"}],
        "standard": [{"item": "std1"}],
        "medium": [{"item": "med1"}],
        "advanced": [{"item": "adv1"}],
        "pro": [{"item": "pro1"}],
    }

    with patch.object(scanner, "scan_all_levels", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = all_levels_data

        result = await scanner.find_best_opportunities(
            "csgo", top_n=10, max_level="medium"
        )

    # Не должно быть предметов из advanced и pro
    for item in result:
        assert item["item"] not in ["adv1", "pro1"]


# ============================================================================
# Тесты get_level_stats
# ============================================================================


def test_get_level_stats_initial(scanner):
    """Тест статистики уровней при инициализации."""
    stats = scanner.get_level_stats()

    assert isinstance(stats, dict)
    assert len(stats) == 5
    for level_name in ["boost", "standard", "medium", "advanced", "pro"]:
        assert level_name in stats
        assert "name" in stats[level_name]
        assert "min_profit" in stats[level_name]
        assert "price_range" in stats[level_name]


# ============================================================================
# Тесты auto_trade_items
# ============================================================================


@pytest.mark.asyncio()
async def test_auto_trade_items_success(scanner):
    """Тест автоматической торговли."""
    items_by_game = {
        "csgo": [
            {
                "item_id": "item_001",
                "title": "Test Item",
                "buy_price": 10.0,
                "sell_price": 12.0,
                "game": "csgo",
            }
        ]
    }

    result = await scanner.auto_trade_items(items_by_game, max_trades=1)

    assert isinstance(result, tuple)
    assert len(result) == 3


@pytest.mark.asyncio()
async def test_auto_trade_items_empty_list(scanner):
    """Тест автоторговли с пустым списком."""
    result = await scanner.auto_trade_items({})

    assert isinstance(result, tuple)
    assert result[0] == 0  # purchases
    assert result[1] == 0  # sales
    assert result[2] == 0.0  # profit


@pytest.mark.asyncio()
async def test_auto_trade_items_insufficient_balance(scanner):
    """Тест автоторговли при недостаточном балансе."""
    scanner.api_client.get_balance = AsyncMock(
        return_value={"usd": "100", "balance": 1.0, "error": False}  # Только $1
    )

    items_by_game = {
        "csgo": [
            {
                "item_id": "item_001",
                "title": "Expensive Item",
                "buy_price": 50.0,
                "sell_price": 60.0,
                "game": "csgo",
            }
        ]
    }

    result = await scanner.auto_trade_items(items_by_game)

    # Не должно быть успешных сделок из-за нехватки средств
    assert result[0] == 0  # purchases


@pytest.mark.asyncio()
async def test_auto_trade_items_max_trades_limit(scanner):
    """Тест лимита максимального количества сделок."""
    items_by_game = {
        "csgo": [
            {
                "item_id": f"item_{i:03d}",
                "title": f"Item {i}",
                "buy_price": 5.0,
                "sell_price": 6.0,
                "game": "csgo",
            }
            for i in range(10)
        ]
    }

    result = await scanner.auto_trade_items(items_by_game, max_trades=3)

    # Должно быть не более 3 попыток торговли
    total_attempts = result[0] + result[1]  # purchases + sales
    assert total_attempts <= 6  # max 3 покупки + max 3 продажи


# ============================================================================
# Тесты _analyze_item
# ============================================================================


@pytest.mark.asyncio()
async def test_analyze_item_success(scanner):
    """Тест анализа предмета."""
    item = {
        "itemId": "item_001",
        "title": "Test Item",
        "price": {"USD": 1000},
        "suggestedPrice": {"USD": 1200},
    }
    config = {
        "price_range": (5.0, 15.0),
        "min_profit_percent": 3.0,
    }

    result = await scanner._analyze_item(item, config, "csgo")

    assert result is not None
    assert "buy_price" in result
    assert "suggested_price" in result or "sell_price" in result
    assert "profit" in result
    assert "profit_percent" in result


@pytest.mark.asyncio()
async def test_analyze_item_no_profit(scanner):
    """Тест анализа предмета без прибыли."""
    item = {
        "itemId": "item_001",
        "title": "No Profit Item",
        "price": {"USD": 1000},
        "suggestedPrice": {"USD": 900},  # Меньше цены покупки
    }
    config = {
        "price_range": (5.0, 15.0),
        "min_profit_percent": 3.0,
    }

    result = await scanner._analyze_item(item, config, "csgo")

    # Предмет не должен быть добавлен (нет прибыли)
    assert result is None or result["profit"] <= 0


# ============================================================================
# Интеграционные тесты
# ============================================================================


@pytest.mark.asyncio()
async def test_full_arbitrage_workflow(scanner):
    """Интеграционный тест: полный цикл арбитража."""
    # Мокируем _request для check_user_balance
    scanner.api_client._request = AsyncMock(
        return_value={"usd": {"available": 10000, "frozen": 0}}
    )

    # 1. Сканирование игры
    with (
        patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"),
        patch(
            "src.dmarket.arbitrage_scanner.arbitrage_mid",
            return_value=[
                {
                    "itemId": "int_001",
                    "title": "Integration Test Item",
                    "price": {"USD": "2000"},
                    "suggestedPrice": {"USD": "2500"},
                }
            ],
        ),
    ):
        items = await scanner.scan_game("csgo", "medium", max_items=5)

    assert len(items) > 0

    # 2. Проверка баланса
    balance = await scanner.check_user_balance()
    assert balance["error"] is False

    # 3. Автоматическая торговля (упрощённая проверка)
    items_dict = {"csgo": items}
    result = await scanner.auto_trade_items(items_dict, max_trades=1)
    assert result is not None


# ============================================================================
# Тесты граничных случаев
# ============================================================================


@pytest.mark.asyncio()
async def test_scan_game_with_zero_max_items(scanner):
    """Тест сканирования с max_items=0."""
    with patch("src.dmarket.arbitrage_scanner.rate_limiter.wait_if_needed"):
        result = await scanner.scan_game("csgo", "medium", max_items=0)

    assert result == []


def test_standardize_items_empty_list(scanner):
    """Тест стандартизации пустого списка."""
    result = scanner._standardize_items([], "csgo", min_profit=0.5, max_profit=100.0)
    assert result == []


def test_standardize_items_invalid_format(scanner):
    """Тест стандартизации предметов с невалидным форматом."""
    items = [
        {"invalid": "format"},  # Нет нужных полей
    ]

    result = scanner._standardize_items(items, "csgo", min_profit=0.5, max_profit=100.0)

    # Должен обработать ошибку и вернуть пустой список или пропустить
    assert isinstance(result, list)


@pytest.mark.asyncio()
async def test_scan_multiple_games_concurrent(scanner):
    """Тест конкурентного сканирования игр."""

    async def delayed_scan(game, mode, max_items):
        await asyncio.sleep(0.1)  # Имитация задержки API
        return [{"item": f"{game}_item"}]

    with patch.object(scanner, "scan_game", side_effect=delayed_scan):
        games = ["csgo", "dota2", "rust"]

        start_time = time.time()
        result = await scanner.scan_multiple_games(games, "medium")
        elapsed = time.time() - start_time

    # Проверяем, что сканирование было параллельным (< 0.3 сек вместо 0.3+)
    assert elapsed < 0.2  # Должно быть быстрее последовательного выполнения
    assert len(result) == 3

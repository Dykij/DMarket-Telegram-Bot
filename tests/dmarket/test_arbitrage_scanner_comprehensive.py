"""Комплексные тесты для модуля arbitrage_scanner.

Этот модуль содержит полное тестирование ArbitrageScanner класса и связанных функций,
включая:
- Инициализацию и конфигурацию сканера
- Базовое сканирование с разными режимами
- Кэширование результатов
- Фильтрацию по цене и прибыли
- Обработку ошибок API
- Интеграцию с ArbitrageTrader
- Мульти-игровое сканирование
"""

import time
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.arbitrage_scanner import (
    ARBITRAGE_LEVELS,
    GAME_IDS,
    ArbitrageScanner,
    check_user_balance,
    find_arbitrage_opportunities_async,
    find_multi_game_arbitrage_opportunities,
    scan_game_for_arbitrage,
    scan_multiple_games,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_arbitrage_items() -> list[dict[str, Any]]:
    """Создает фиктивные данные арбитражных предметов для тестирования."""
    return [
        {
            "id": "item1",
            "itemId": "item1",
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"amount": 1000},  # $10.00
            "profit": 200,  # $2.00 прибыль в центах
            "profit_percent": 20.0,
            "game": "csgo",
            "marketHashName": "AK-47 | Redline (Field-Tested)",
        },
        {
            "id": "item2",
            "itemId": "item2",
            "title": "AWP | Asiimov (Field-Tested)",
            "price": {"amount": 5000},  # $50.00
            "profit": 800,  # $8.00 прибыль в центах
            "profit_percent": 16.0,
            "game": "csgo",
            "marketHashName": "AWP | Asiimov (Field-Tested)",
        },
        {
            "id": "item3",
            "itemId": "item3",
            "title": "Desert Eagle | Blaze (Factory New)",
            "price": {"amount": 3000},  # $30.00
            "profit": 500,  # $5.00 прибыль в центах
            "profit_percent": 16.7,
            "game": "csgo",
            "marketHashName": "Desert Eagle | Blaze (Factory New)",
        },
    ]


@pytest.fixture()
def mock_api_client():
    """Создает мок DMarketAPI клиента."""
    mock_api = AsyncMock()
    mock_api.get_market_items = AsyncMock(return_value={"objects": []})
    mock_api.get_item_details = AsyncMock(return_value={"price": 100})
    return mock_api


# ============================================================================
# ТЕСТЫ ИНИЦИАЛИЗАЦИИ И КОНФИГУРАЦИИ
# ============================================================================


def test_arbitrage_scanner_initialization():
    """Тест инициализации ArbitrageScanner с параметрами по умолчанию."""
    scanner = ArbitrageScanner()

    # Проверяем начальные значения
    assert scanner.api_client is None
    assert scanner._cache == {}
    assert scanner._cache_ttl == 300  # 5 минут
    assert scanner.min_profit == 0.5
    assert scanner.max_price == 50.0
    assert scanner.max_trades == 5

    # Проверяем статистику
    assert scanner.total_scans == 0
    assert scanner.total_items_found == 0
    assert scanner.successful_trades == 0
    assert scanner.total_profit == 0.0


def test_arbitrage_scanner_initialization_with_api_client(mock_api_client):
    """Тест инициализации ArbitrageScanner с предоставленным API клиентом."""
    scanner = ArbitrageScanner(api_client=mock_api_client)

    assert scanner.api_client is mock_api_client


def test_arbitrage_scanner_cache_ttl_property():
    """Тест свойства cache_ttl (геттер и сеттер)."""
    scanner = ArbitrageScanner()

    # Проверяем начальное значение
    assert scanner.cache_ttl == 300

    # Проверяем сеттер
    scanner.cache_ttl = 600
    assert scanner.cache_ttl == 600
    assert scanner._cache_ttl == 600


# ============================================================================
# ТЕСТЫ КЭШИРОВАНИЯ
# ============================================================================


def test_get_cached_results_empty_cache():
    """Тест получения результатов из пустого кеша."""
    scanner = ArbitrageScanner()
    cache_key = ("csgo", "medium", 0, float("inf"))

    result = scanner._get_cached_results(cache_key)

    assert result is None


def test_get_cached_results_valid_cache(mock_arbitrage_items):
    """Тест получения валидных результатов из кеша."""
    scanner = ArbitrageScanner()
    cache_key = ("csgo", "medium", 0, float("inf"))

    # Сохраняем в кеш
    scanner._save_to_cache(cache_key, mock_arbitrage_items)

    # Получаем из кеша
    result = scanner._get_cached_results(cache_key)

    assert result == mock_arbitrage_items


def test_get_cached_results_expired_cache(mock_arbitrage_items):
    """Тест получения результатов из устаревшего кеша."""
    scanner = ArbitrageScanner()
    cache_key = ("csgo", "medium", 0, float("inf"))

    # Сохраняем в кеш
    scanner._save_to_cache(cache_key, mock_arbitrage_items)

    # Искусственно делаем кеш устаревшим
    scanner._cache[cache_key] = (mock_arbitrage_items, time.time() - 400)

    # Пробуем получить из кеша
    result = scanner._get_cached_results(cache_key)

    assert result is None


def test_save_to_cache(mock_arbitrage_items):
    """Тест сохранения результатов в кеш."""
    scanner = ArbitrageScanner()
    cache_key = ("csgo", "medium", 0, float("inf"))

    scanner._save_to_cache(cache_key, mock_arbitrage_items)

    # Проверяем, что данные сохранены
    assert cache_key in scanner._cache
    items, timestamp = scanner._cache[cache_key]
    assert items == mock_arbitrage_items
    assert isinstance(timestamp, float)
    assert time.time() - timestamp < 1  # Сохранено только что


# ============================================================================
# ТЕСТЫ БАЗОВОГО СКАНИРОВАНИЯ
# ============================================================================


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_boost")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_low_mode(
    mock_rate_limiter,
    mock_arbitrage_boost,
    mock_arbitrage_items,
):
    """Тест сканирования игры в режиме 'low'."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_boost.return_value = mock_arbitrage_items

    scanner = ArbitrageScanner()

    # Вызываем scan_game
    result = await scanner.scan_game(game="csgo", mode="low", max_items=2)

    # Проверки
    mock_arbitrage_boost.assert_called_once_with("csgo")
    assert len(result) == 2
    assert result[0]["id"] == "item1"
    assert result[1]["id"] == "item2"
    assert scanner.total_scans == 1
    assert scanner.total_items_found == 2


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_mid")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_medium_mode(
    mock_rate_limiter,
    mock_arbitrage_mid,
    mock_arbitrage_items,
):
    """Тест сканирования игры в режиме 'medium'."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_mid.return_value = mock_arbitrage_items

    scanner = ArbitrageScanner()

    # Вызываем scan_game
    result = await scanner.scan_game(game="csgo", mode="medium", max_items=3)

    # Проверки
    mock_arbitrage_mid.assert_called_once_with("csgo")
    assert len(result) == 3
    assert scanner.total_scans == 1


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_pro")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_high_mode(
    mock_rate_limiter,
    mock_arbitrage_pro,
    mock_arbitrage_items,
):
    """Тест сканирования игры в режиме 'high'."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_pro.return_value = mock_arbitrage_items

    scanner = ArbitrageScanner()

    # Вызываем scan_game
    result = await scanner.scan_game(game="csgo", mode="high", max_items=1)

    # Проверки
    mock_arbitrage_pro.assert_called_once_with("csgo")
    assert len(result) == 1
    assert result[0]["id"] == "item1"


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_mid")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_uses_cache(
    mock_rate_limiter,
    mock_arbitrage_mid,
    mock_arbitrage_items,
):
    """Тест использования кеша при повторном сканировании."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_mid.return_value = mock_arbitrage_items

    scanner = ArbitrageScanner()

    # Первое сканирование - должно вызвать API
    result1 = await scanner.scan_game(game="csgo", mode="medium", max_items=3)
    assert len(result1) == 3
    assert mock_arbitrage_mid.call_count == 1

    # Второе сканирование - должно использовать кеш
    result2 = await scanner.scan_game(game="csgo", mode="medium", max_items=3)
    assert len(result2) == 3
    assert mock_arbitrage_mid.call_count == 1  # Не вызвано повторно!
    assert result1 == result2


# ============================================================================
# ТЕСТЫ ФИЛЬТРАЦИИ
# ============================================================================


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageTrader")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_with_price_filter(
    mock_rate_limiter,
    mock_trader_class,
    mock_arbitrage_items,
):
    """Тест сканирования с фильтром по цене."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_trader = AsyncMock()
    mock_trader_class.return_value = mock_trader
    mock_trader.find_profitable_items = AsyncMock(return_value=mock_arbitrage_items)

    scanner = ArbitrageScanner()

    # Вызываем с фильтром по цене
    result = await scanner.scan_game(
        game="csgo",
        mode="medium",
        max_items=10,
        price_from=10.0,
        price_to=50.0,
    )

    # Проверяем, что использован ArbitrageTrader
    assert mock_trader.find_profitable_items.called


# ============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК
# ============================================================================


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_mid")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_api_error(mock_rate_limiter, mock_arbitrage_mid):
    """Тест обработки ошибки API при сканировании."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_mid.side_effect = Exception("API Error")

    scanner = ArbitrageScanner()

    # Вызываем scan_game - должен вернуть пустой список при ошибке
    result = await scanner.scan_game(game="csgo", mode="medium", max_items=10)

    assert result == []
    assert scanner.total_scans == 1


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_mid")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_scan_game_with_empty_results(
    mock_rate_limiter,
    mock_arbitrage_mid,
):
    """Тест сканирования, возвращающего пустой результат."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_mid.return_value = []

    scanner = ArbitrageScanner()

    # Вызываем scan_game
    result = await scanner.scan_game(game="csgo", mode="medium", max_items=10)

    assert result == []


# ============================================================================
# ТЕСТЫ АВТОНОМНЫХ ФУНКЦИЙ
# ============================================================================


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.arbitrage_boost")
@patch("src.dmarket.arbitrage_scanner.rate_limiter")
async def test_find_arbitrage_opportunities_async(
    mock_rate_limiter,
    mock_arbitrage_boost,
    mock_arbitrage_items,
):
    """Тест функции find_arbitrage_opportunities_async."""
    # Настройка моков
    mock_rate_limiter.wait_if_needed = AsyncMock()
    mock_arbitrage_boost.return_value = mock_arbitrage_items

    # Вызываем функцию
    result = await find_arbitrage_opportunities_async(
        game="csgo",
        mode="low",
        max_items=2,
    )

    # Проверки
    assert len(result) == 2
    assert result[0]["id"] == "item1"


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageScanner.scan_game")
async def test_find_multi_game_arbitrage_opportunities(
    mock_scan_game,
    mock_arbitrage_items,
):
    """Тест функции find_multi_game_arbitrage_opportunities."""
    # Настройка мока - разные результаты для разных игр
    mock_scan_game.side_effect = [
        mock_arbitrage_items[:2],  # csgo
        mock_arbitrage_items[2:],  # dota2
        [],  # rust
    ]

    # Вызываем функцию
    games = ["csgo", "dota2", "rust"]
    result = await find_multi_game_arbitrage_opportunities(
        games=games,
        mode="medium",
        max_items_per_game=2,
    )

    # Проверки
    assert len(result) == 3
    assert len(result["csgo"]) == 2
    assert len(result["dota2"]) == 1
    assert len(result["rust"]) == 0
    assert mock_scan_game.call_count == 3


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageScanner.scan_game")
async def test_scan_game_for_arbitrage(mock_scan_game, mock_arbitrage_items):
    """Тест функции scan_game_for_arbitrage."""
    # Настройка мока
    mock_scan_game.return_value = mock_arbitrage_items

    # Вызываем функцию
    result = await scan_game_for_arbitrage(game="csgo", mode="medium", max_items=3)

    # Проверки
    assert len(result) == 3
    mock_scan_game.assert_called_once()


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageScanner.scan_game")
async def test_scan_multiple_games(mock_scan_game, mock_arbitrage_items):
    """Тест функции scan_multiple_games."""
    # Настройка мока
    mock_scan_game.side_effect = [
        mock_arbitrage_items[:2],
        mock_arbitrage_items[2:],
    ]

    # Вызываем функцию
    games = ["csgo", "dota2"]
    result = await scan_multiple_games(
        games=games,
        mode="medium",
        max_items_per_game=2,
    )

    # Проверки
    assert "csgo" in result
    assert "dota2" in result
    assert len(result["csgo"]) == 2
    assert len(result["dota2"]) == 1


# ============================================================================
# ТЕСТЫ ПРОВЕРКИ БАЛАНСА
# ============================================================================


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageScanner.check_user_balance")
async def test_check_user_balance_success(mock_method):
    """Тест успешной проверки баланса пользователя."""
    # Мокируем метод check_user_balance класса ArbitrageScanner
    mock_method.return_value = {
        "balance": 100.50,
        "has_funds": True,
        "error": False,
    }

    # Создаем мок API
    mock_api = AsyncMock()

    # Вызываем функцию
    result = await check_user_balance(mock_api)

    # Проверки
    assert result["balance"] == 100.50
    assert result["has_funds"] is True
    assert result["error"] is False
    assert mock_method.called


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageScanner.check_user_balance")
async def test_check_user_balance_insufficient_funds(mock_method):
    """Тест проверки баланса с недостаточными средствами."""
    # Мокируем метод check_user_balance класса ArbitrageScanner
    mock_method.return_value = {
        "balance": 0.50,
        "has_funds": False,
        "error": False,
    }

    # Создаем мок API
    mock_api = AsyncMock()

    # Вызываем функцию
    result = await check_user_balance(mock_api)

    # Проверки
    assert result["balance"] == 0.50
    assert result["has_funds"] is False
    assert mock_method.called


@pytest.mark.asyncio()
@patch("src.dmarket.arbitrage_scanner.ArbitrageScanner.check_user_balance")
async def test_check_user_balance_api_error(mock_method):
    """Тест обработки ошибки API при проверке баланса."""
    # Мокируем метод check_user_balance класса ArbitrageScanner
    mock_method.return_value = {
        "error": True,
        "error_message": "API Error",
        "balance": 0.0,
        "has_funds": False,
    }

    # Создаем мок API
    mock_api = AsyncMock()

    # Вызываем функцию
    result = await check_user_balance(mock_api)

    # Проверки
    assert result["error"] is True
    assert "error_message" in result
    assert mock_method.called


# ============================================================================
# ТЕСТЫ КОНСТАНТ И КОНФИГУРАЦИИ
# ============================================================================


def test_game_ids_defined():
    """Тест наличия определения GAME_IDS."""
    assert "csgo" in GAME_IDS
    assert "dota2" in GAME_IDS
    assert "tf2" in GAME_IDS
    assert "rust" in GAME_IDS


def test_arbitrage_levels_defined():
    """Тест наличия определения ARBITRAGE_LEVELS."""
    assert "boost" in ARBITRAGE_LEVELS
    assert "standard" in ARBITRAGE_LEVELS
    assert "medium" in ARBITRAGE_LEVELS
    assert "advanced" in ARBITRAGE_LEVELS
    assert "pro" in ARBITRAGE_LEVELS

    # Проверяем структуру каждого уровня
    for level_data in ARBITRAGE_LEVELS.values():
        assert "name" in level_data
        assert "min_profit_percent" in level_data
        assert "max_profit_percent" in level_data
        assert "description" in level_data

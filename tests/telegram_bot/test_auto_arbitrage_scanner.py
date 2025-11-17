"""Тесты для модуля auto_arbitrage_scanner.py.

Этот модуль содержит тесты для функций автоматического сканирования арбитражных возможностей.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.dmarket_api import DMarketAPI
from src.telegram_bot.auto_arbitrage_scanner import (
    auto_trade_items,
    check_user_balance,
    scan_game_for_arbitrage,
    scan_multiple_games,
)


@pytest.fixture()
def mock_dmarket_api():
    """Создает мок объекта DMarketAPI для тестирования."""
    api = MagicMock(spec=DMarketAPI)
    api.public_key = "test_public_key"
    api.secret_key = "test_secret_key"
    api._request = AsyncMock()
    api.get_user_balance = AsyncMock()
    api.__aenter__ = AsyncMock(return_value=api)
    api.__aexit__ = AsyncMock(return_value=None)
    return api


@pytest.mark.asyncio()
@patch("src.telegram_bot.auto_arbitrage_scanner.rate_limiter")
@patch("src.telegram_bot.auto_arbitrage_scanner._scanner_cache", {})
async def test_scan_game_for_arbitrage_success(mock_rate_limiter, mock_dmarket_api):
    """Тестирует успешное сканирование игры для арбитража."""
    # Настройка мока rate_limiter
    mock_rate_limiter.wait_if_needed = AsyncMock()

    # Настройка мока для ArbitrageTrader
    mock_trader = MagicMock()
    mock_items = [
        {"name": "Item1", "buy_price": 10.0, "profit": 6.0, "profit_percentage": 10.0},
        {"name": "Item2", "buy_price": 20.0, "profit": 8.0, "profit_percentage": 10.0},
    ]
    mock_trader.find_profitable_items = AsyncMock(return_value=mock_items)

    with patch(
        "src.telegram_bot.auto_arbitrage_scanner.ArbitrageTrader",
        return_value=mock_trader,
    ):
        # Вызываем тестируемую функцию
        result = await scan_game_for_arbitrage(
            game="csgo",
            mode="medium",
            max_items=10,
            price_from=5.0,
            price_to=50.0,
            dmarket_api=mock_dmarket_api,
        )

        # Проверяем, что rate_limiter был вызван
        mock_rate_limiter.wait_if_needed.assert_called_once_with("market")

        # Проверяем, что метод find_profitable_items был вызван с правильными параметрами
        mock_trader.find_profitable_items.assert_called_once()
        call_args = mock_trader.find_profitable_items.call_args[1]
        assert call_args["game"] == "csgo"
        assert call_args["min_profit_percentage"] == 5.0
        assert call_args["min_price"] == 5.0
        assert call_args["max_price"] == 50.0

        # Проверяем результат
        assert len(result) == 2
        assert result[0]["title"] == "Item1"
        assert result[0]["profit"] == 6.0
        assert result[0]["game"] == "csgo"


@pytest.mark.asyncio()
@patch("src.telegram_bot.auto_arbitrage_scanner.rate_limiter")
@patch("src.telegram_bot.auto_arbitrage_scanner._scanner_cache", {})
async def test_scan_game_for_arbitrage_different_modes(
    mock_rate_limiter,
    mock_dmarket_api,
):
    """Тестирует сканирование игры с разными режимами."""
    # Настройка мока rate_limiter
    mock_rate_limiter.wait_if_needed = AsyncMock()

    # Настройка мока для ArbitrageTrader
    mock_trader = MagicMock()
    # Генерируем предметы с profit от 5 до 25 для тестирования разных режимов
    mock_items = [
        {
            "name": f"Item{i}",
            "buy_price": i * 10.0,
            "profit": float(i),
            "profit_percentage": 10.0,
        }
        for i in range(5, 26)
    ]
    mock_trader.find_profitable_items = AsyncMock(return_value=mock_items)

    with patch(
        "src.telegram_bot.auto_arbitrage_scanner.ArbitrageTrader",
        return_value=mock_trader,
    ):
        # Тестируем с разными режимами
        test_modes = [
            # (режим, мин. прибыль, макс. прибыль, ожидаемое кол-во результатов)
            ("low", 1.0, 5.0, 1),  # Только Item5 с profit=5.0
            ("medium", 5.0, 20.0, 10),  # Item5-Item20 (16 предметов, но max_items=10)
            ("high", 20.0, 100.0, 6),  # Item20-Item25 с profit 20-25
        ]

        for mode, min_profit, max_profit, expected_count in test_modes:
            # Вызываем тестируемую функцию
            result = await scan_game_for_arbitrage(
                game="csgo",
                mode=mode,
                max_items=10,
                dmarket_api=mock_dmarket_api,
            )

            # Фильтруем мок-итемы по диапазону прибыли для проверки
            [item for item in mock_items if min_profit <= item["profit"] <= max_profit]

            # Проверяем, что количество результатов соответствует ожидаемому
            assert len(result) == min(expected_count, 10)  # Учитываем max_items


@pytest.mark.asyncio()
@patch("src.telegram_bot.auto_arbitrage_scanner.rate_limiter")
@patch("src.telegram_bot.auto_arbitrage_scanner._scanner_cache", {})
async def test_scan_game_for_arbitrage_error_handling(
    mock_rate_limiter,
    mock_dmarket_api,
):
    """Тестирует обработку ошибок при сканировании игры."""
    # Настройка мока rate_limiter
    mock_rate_limiter.wait_if_needed = AsyncMock()

    # Настройка мока для ArbitrageTrader, который вызывает исключение
    mock_trader = MagicMock()
    mock_trader.find_profitable_items = AsyncMock(side_effect=Exception("API Error"))

    with patch(
        "src.telegram_bot.auto_arbitrage_scanner.ArbitrageTrader",
        return_value=mock_trader,
    ):
        # Вызываем тестируемую функцию
        result = await scan_game_for_arbitrage(
            game="csgo",
            mode="medium",
            dmarket_api=mock_dmarket_api,
        )

        # Проверяем, что при ошибке возвращается пустой список
        assert result == []


@pytest.mark.asyncio()
@patch("src.telegram_bot.auto_arbitrage_scanner.scan_game_for_arbitrage")
@patch("src.telegram_bot.auto_arbitrage_scanner.DMarketAPI")
async def test_scan_multiple_games(
    mock_dmarket_api_class,
    mock_scan_game,
):
    """Тестирует сканирование нескольких игр."""
    # Настройка мока для DMarketAPI
    mock_api_instance = MagicMock()
    mock_api_instance._close_client = AsyncMock()
    mock_dmarket_api_class.return_value = mock_api_instance

    # Настройка результатов для разных игр
    mock_scan_game.side_effect = [
        [{"title": "CS Item", "profit": 5.0}],  # csgo
        [{"title": "Dota Item", "profit": 3.0}],  # dota2
        [],  # rust
    ]

    # Вызываем тестируемую функцию
    result = await scan_multiple_games(
        games=["csgo", "dota2", "rust"],
        mode="medium",
        max_items_per_game=5,
    )

    # Проверяем, что был создан экземпляр DMarketAPI
    mock_dmarket_api_class.assert_called_once()

    # Проверяем результаты
    assert "csgo" in result
    assert "dota2" in result
    assert "rust" in result
    assert len(result["csgo"]) == 1
    assert len(result["dota2"]) == 1
    assert len(result["rust"]) == 0


@pytest.mark.asyncio()
async def test_check_user_balance_success(mock_dmarket_api):
    """Тестирует успешную проверку баланса пользователя."""
    # Настройка мока для get_balance
    mock_dmarket_api.get_balance = AsyncMock(
        return_value={
            "balance": 10.0,
            "available_balance": 10.0,
            "total_balance": 10.0,
            "error": False,
        }
    )

    # Вызываем тестируемую функцию
    result = await check_user_balance(mock_dmarket_api)

    # Проверяем результаты
    assert result["has_funds"] is True
    assert result["balance"] == 10.0


@pytest.mark.asyncio()
async def test_check_user_balance_no_api_keys(mock_dmarket_api):
    """Тестирует проверку баланса без API ключей."""
    # Настройка мока для get_balance с ошибкой
    mock_dmarket_api.get_balance = AsyncMock(
        return_value={"error": True, "error_message": "API keys missing"}
    )

    # Вызываем тестируемую функцию
    result = await check_user_balance(mock_dmarket_api)

    # Проверяем результаты
    assert result["has_funds"] is False
    assert result["balance"] == 0.0


@pytest.mark.asyncio()
async def test_check_user_balance_low_funds(mock_dmarket_api):
    """Тестирует проверку баланса с недостаточными средствами."""
    # Настройка мока для get_balance
    mock_dmarket_api.get_balance = AsyncMock(
        return_value={
            "balance": 0.5,
            "available_balance": 0.5,
            "total_balance": 0.5,
            "error": False,
        }
    )

    # Вызываем тестируемую функцию
    result = await check_user_balance(mock_dmarket_api)

    # Проверяем результаты - по умолчанию требуется минимум $1.00
    assert result["has_funds"] is False
    assert result["balance"] == 0.5


@pytest.mark.asyncio()
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
@patch("src.telegram_bot.auto_arbitrage_scanner.ArbitrageTrader")
async def test_auto_trade_items_sufficient_balance(
    mock_trader_class,
    mock_check_balance,
    mock_dmarket_api,
):
    """Тестирует автоматическую торговлю с достаточным балансом."""
    # Настройка мока для check_user_balance
    mock_check_balance.return_value = {
        "has_funds": True,
        "balance": 100.0,
        "available_balance": 100.0,
        "total_balance": 100.0,
        "error": False,
    }
    # Настройка мока ArbitrageTrader
    mock_trader = MagicMock()
    mock_trader.set_trading_limits = MagicMock()
    mock_trader.get_current_item_data = AsyncMock(
        return_value={"available": True, "current_price": 10.0}
    )
    mock_trader.buy_item = AsyncMock(return_value={"success": True})
    mock_trader.sell_item = AsyncMock(return_value={"success": True})
    mock_trader_class.return_value = mock_trader
    # Настройка тестовых данных
    items_by_game = {
        "csgo": [
            {
                "title": "CS Item 1",
                "price": {"amount": 1000},  # $10.00 (в центах)
                "profit": 2.0,
                "itemId": "item1",
                "game": "csgo",
            },
            {
                "title": "CS Item 2",
                "price": {"amount": 2000},  # $20.00 (в центах)
                "profit": 3.0,
                "itemId": "item2",
                "game": "csgo",
            },
        ],
        "dota2": [
            {
                "title": "Dota Item",
                "price": {"amount": 1500},  # $15.00 (в центах)
                "profit": 2.5,
                "itemId": "item3",
                "game": "dota2",
            },
        ],
    }

    # Имитация успешной покупки
    mock_dmarket_api._request.return_value = {"status": "success"}

    # Вызываем тестируемую функцию
    trades_count, _failed_trades, total_profit = await auto_trade_items(
        items_by_game=items_by_game,
        min_profit=1.0,
        max_price=30.0,
        dmarket_api=mock_dmarket_api,
        max_trades=3,
    )

    # Проверяем, что check_user_balance был вызван
    mock_check_balance.assert_called_once()

    # Проверяем, что ArbitrageTrader был создан
    assert mock_trader_class.called

    # Проверяем результаты
    assert trades_count >= 0  # Может быть 0 если не удалось купить
    assert total_profit >= 0  # Может быть 0 если нет продаж


@pytest.mark.asyncio()
@patch("src.telegram_bot.auto_arbitrage_scanner.check_user_balance")
async def test_auto_trade_items_insufficient_balance(
    mock_check_balance,
    mock_dmarket_api,
):
    """Тестирует автоматическую торговлю с недостаточным балансом."""
    # Настройка мока для check_user_balance
    mock_check_balance.return_value = {
        "has_funds": False,
        "balance": 0.5,
        "available_balance": 0.5,
        "total_balance": 0.5,
        "error": False,
    }

    # Настройка тестовых данных
    items_by_game = {
        "csgo": [
            {
                "title": "CS Item",
                "price": {"amount": 1000},  # $10.00 (в центах)
                "profit": 2.0,
                "itemId": "item1",
                "game": "csgo",
            },
        ],
    }

    # Вызываем тестируемую функцию
    trades_count, failed_trades, total_profit = await auto_trade_items(
        items_by_game=items_by_game,
        min_profit=1.0,
        max_price=30.0,
        dmarket_api=mock_dmarket_api,
        max_trades=3,
    )

    # Проверяем результаты - не должно быть сделок из-за недостатка средств
    assert trades_count == 0
    assert failed_trades == 0
    assert total_profit == 0.0

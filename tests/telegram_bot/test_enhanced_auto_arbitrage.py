"""Тесты для модуля enhanced_auto_arbitrage.

Этот модуль содержит тесты для улучшенного автоматического арбитража, включая:
- Константы и конфигурацию
- Мульти-игровое сканирование
- Progress callbacks для отслеживания прогресса
- Запуск улучшенного автоарбитража
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.enhanced_auto_arbitrage import (
    DEFAULT_PRICE_CHUNKS,
    DEFAULT_PRICE_RANGES,
    scan_multiple_games_enhanced,
    start_auto_arbitrage_enhanced,
)


# ============================================================================
# ТЕСТЫ КОНСТАНТ
# ============================================================================


def test_default_price_ranges_defined():
    """Тест наличия определения ценовых диапазонов по умолчанию."""
    assert "csgo" in DEFAULT_PRICE_RANGES
    assert "dota2" in DEFAULT_PRICE_RANGES
    assert "tf2" in DEFAULT_PRICE_RANGES
    assert "rust" in DEFAULT_PRICE_RANGES

    # Проверяем структуру для CS:GO
    csgo_range = DEFAULT_PRICE_RANGES["csgo"]
    assert "min" in csgo_range
    assert "max" in csgo_range
    assert csgo_range["min"] > 0
    assert csgo_range["max"] > csgo_range["min"]


def test_default_price_chunks_defined():
    """Тест наличия определения ценовых чанков."""
    assert len(DEFAULT_PRICE_CHUNKS) > 0
    assert isinstance(DEFAULT_PRICE_CHUNKS, list)

    # Проверяем структуру чанков
    for chunk in DEFAULT_PRICE_CHUNKS:
        assert isinstance(chunk, tuple)
        assert len(chunk) == 2
        assert chunk[0] < chunk[1]  # min < max


# ============================================================================
# ТЕСТЫ МУЛЬТИ-ИГРОВОГО СКАНИРОВАНИЯ
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_game_comprehensively")
async def test_scan_multiple_games_enhanced_basic(mock_scan_game):
    """Тест базового сканирования нескольких игр."""
    # Настройка мока
    mock_arbitrage_items = [
        {"id": "item1", "profit": 200},
        {"id": "item2", "profit": 100},
    ]
    mock_scan_game.return_value = mock_arbitrage_items

    # Вызываем функцию
    games = ["csgo", "dota2"]
    result = await scan_multiple_games_enhanced(
        games=games,
        mode="medium",
    )

    # Проверки
    assert isinstance(result, dict)
    assert "csgo" in result
    assert "dota2" in result
    assert mock_scan_game.call_count == 2


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_game_comprehensively")
async def test_scan_multiple_games_enhanced_with_progress(mock_scan_game):
    """Тест мульти-игрового сканирования с progress callback."""
    # Настройка мока
    mock_scan_game.return_value = [{"id": "item1"}]

    # Создаем мок callback
    progress_callback = MagicMock()

    # Вызываем функцию
    result = await scan_multiple_games_enhanced(
        games=["csgo"],
        mode="medium",
        progress_callback=progress_callback,
    )

    # Проверки
    assert isinstance(result, dict)
    assert progress_callback.called


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_game_comprehensively")
async def test_scan_multiple_games_enhanced_empty_games(mock_scan_game):
    """Тест сканирования с пустым списком игр."""
    # Вызываем функцию с пустым списком
    result = await scan_multiple_games_enhanced(
        games=[],
        mode="medium",
    )

    # Проверки
    assert isinstance(result, dict)
    assert len(result) == 0
    mock_scan_game.assert_not_called()


# ============================================================================
# ТЕСТЫ START_AUTO_ARBITRAGE_ENHANCED
# ============================================================================


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_multiple_games_enhanced")
async def test_start_auto_arbitrage_enhanced_basic(mock_scan_multiple):
    """Тест запуска улучшенного автоарбитража."""
    # Настройка мока
    mock_scan_multiple.return_value = {
        "csgo": [{"id": "item1", "profit": 100, "profit_percentage": 20}],
    }

    # Создаем мок callback
    progress_callback = MagicMock()

    # Вызываем функцию
    result = await start_auto_arbitrage_enhanced(
        games=["csgo"],
        mode="medium",
        progress_callback=progress_callback,
    )

    # Проверки - возвращает список, а не словарь
    assert isinstance(result, list)
    mock_scan_multiple.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_multiple_games_enhanced")
async def test_start_auto_arbitrage_enhanced_no_items(mock_scan_multiple):
    """Тест запуска автоарбитража без найденных предметов."""
    # Настройка мока - пустые результаты
    mock_scan_multiple.return_value = {
        "csgo": [],
        "dota2": [],
    }

    # Вызываем функцию
    result = await start_auto_arbitrage_enhanced(
        games=["csgo", "dota2"],
        mode="medium",
    )

    # Проверки - возвращает список
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_multiple_games_enhanced")
async def test_start_auto_arbitrage_enhanced_default_game(mock_scan_multiple):
    """Тест запуска автоарбитража без указания игр (дефолт: csgo)."""
    # Настройка мока
    mock_scan_multiple.return_value = {"csgo": []}

    # Вызываем функцию без указания игр
    result = await start_auto_arbitrage_enhanced(
        games=None,  # Должен использовать дефолтную игру
        mode="medium",
    )

    # Проверки
    assert isinstance(result, list)
    mock_scan_multiple.assert_called_once()


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_multiple_games_enhanced")
async def test_start_auto_arbitrage_enhanced_sorting(mock_scan_multiple):
    """Тест сортировки результатов по profit_percentage."""
    # Настройка мока - предметы с разной прибылью
    mock_scan_multiple.return_value = {
        "csgo": [
            {"id": "item1", "profit_percentage": 10},
            {"id": "item2", "profit_percentage": 30},
            {"id": "item3", "profit_percentage": 20},
        ]
    }

    # Вызываем функцию
    result = await start_auto_arbitrage_enhanced(
        games=["csgo"],
        mode="medium",
    )

    # Проверки - должно быть отсортировано по profit_percentage
    assert len(result) == 3
    assert result[0]["profit_percentage"] == 30  # Максимальная прибыль первая
    assert result[1]["profit_percentage"] == 20
    assert result[2]["profit_percentage"] == 10


@pytest.mark.asyncio()
@patch("src.telegram_bot.enhanced_auto_arbitrage.scan_multiple_games_enhanced")
async def test_start_auto_arbitrage_enhanced_max_items_limit(mock_scan_multiple):
    """Тест ограничения количества возвращаемых предметов."""
    # Настройка мока - много предметов
    items = [{"id": f"item{i}", "profit_percentage": i} for i in range(50)]
    mock_scan_multiple.return_value = {"csgo": items}

    # Вызываем функцию с ограничением
    result = await start_auto_arbitrage_enhanced(
        games=["csgo"],
        mode="medium",
        max_items=10,  # Ограничиваем до 10 предметов
    )

    # Проверки - должно вернуть не больше 10 предметов
    assert len(result) <= 10

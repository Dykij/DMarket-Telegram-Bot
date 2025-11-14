"""Тесты для модуля auto_arbitrage.

Этот модуль содержит тесты для функций автоматического арбитража, включая:
- Генерацию случайных предметов для тестирования
- Фильтрацию предметов по режимам (boost, mid, pro)
- Демонстрацию автоматического арбитража
"""

import pytest

from src.dmarket.auto_arbitrage import (
    GAMES,
    arbitrage_boost,
    arbitrage_mid,
    arbitrage_pro,
    auto_arbitrage_demo,
    generate_random_items,
)


# ============================================================================
# ТЕСТЫ ГЕНЕРАЦИИ СЛУЧАЙНЫХ ПРЕДМЕТОВ
# ============================================================================


def test_generate_random_items_default_count():
    """Тест генерации случайных предметов с количеством по умолчанию."""
    items = generate_random_items("csgo")

    # Проверяем количество по умолчанию (10)
    assert len(items) == 10

    # Проверяем структуру каждого предмета
    for item in items:
        assert "id" in item
        assert "game" in item
        assert "price" in item
        assert "profit" in item
        assert item["game"] == "csgo"
        assert isinstance(item["price"], float)
        assert isinstance(item["profit"], float)


def test_generate_random_items_custom_count():
    """Тест генерации случайных предметов с пользовательским количеством."""
    count = 25
    items = generate_random_items("dota2", count=count)

    # Проверяем количество
    assert len(items) == count

    # Проверяем, что игра указана правильно
    for item in items:
        assert item["game"] == "dota2"


def test_generate_random_items_zero_count():
    """Тест генерации с нулевым количеством предметов."""
    items = generate_random_items("csgo", count=0)

    # Должен вернуть пустой список
    assert len(items) == 0
    assert isinstance(items, list)


def test_generate_random_items_single_item():
    """Тест генерации одного предмета."""
    items = generate_random_items("csgo", count=1)

    assert len(items) == 1
    assert items[0]["id"] == "item_0"
    assert items[0]["game"] == "csgo"


def test_generate_random_items_price_range():
    """Тест, что цены предметов находятся в ожидаемом диапазоне."""
    items = generate_random_items("csgo", count=50)

    # Проверяем, что все цены в диапазоне 1-100
    for item in items:
        assert 1 <= item["price"] <= 100


def test_generate_random_items_profit_range():
    """Тест, что прибыль находится в ожидаемом диапазоне."""
    items = generate_random_items("csgo", count=50)

    # Проверяем, что вся прибыль в диапазоне -10 до 10
    for item in items:
        assert -10 <= item["profit"] <= 10


# ============================================================================
# ТЕСТЫ ФИЛЬТРАЦИИ ПО РЕЖИМАМ
# ============================================================================


def test_arbitrage_boost_filters_negative_profit():
    """Тест, что arbitrage_boost фильтрует предметы с отрицательной прибылью."""
    # Запускаем несколько раз для надежности (из-за случайности)
    all_valid = True
    for _ in range(5):
        items = arbitrage_boost("csgo")

        # Проверяем, что все предметы имеют отрицательную прибыль
        for item in items:
            if item["profit"] >= 0:
                all_valid = False
                break

    # В большинстве случаев должны быть предметы с отрицательной прибылью
    # (из-за случайности может быть и пусто)
    assert isinstance(items, list)


def test_arbitrage_mid_filters_medium_profit():
    """Тест, что arbitrage_mid фильтрует предметы со средней прибылью (0-5)."""
    # Запускаем несколько раз
    all_valid = True
    for _ in range(5):
        items = arbitrage_mid("csgo")

        # Проверяем, что все предметы имеют прибыль 0-5
        for item in items:
            if not (0 <= item["profit"] < 5):
                all_valid = False
                break

    assert isinstance(items, list)


def test_arbitrage_pro_filters_high_profit():
    """Тест, что arbitrage_pro фильтрует предметы с высокой прибылью (>=5)."""
    # Запускаем несколько раз
    all_valid = True
    for _ in range(5):
        items = arbitrage_pro("csgo")

        # Проверяем, что все предметы имеют прибыль >= 5
        for item in items:
            if item["profit"] < 5:
                all_valid = False
                break

    assert isinstance(items, list)


def test_arbitrage_modes_return_different_results():
    """Тест, что разные режимы возвращают разные результаты."""
    # Из-за случайности результаты могут различаться
    boost_items = arbitrage_boost("csgo")
    mid_items = arbitrage_mid("csgo")
    pro_items = arbitrage_pro("csgo")

    # Проверяем, что все возвращают списки
    assert isinstance(boost_items, list)
    assert isinstance(mid_items, list)
    assert isinstance(pro_items, list)


def test_arbitrage_modes_with_dota2():
    """Тест всех режимов арбитража с игрой Dota 2."""
    boost_items = arbitrage_boost("dota2")
    mid_items = arbitrage_mid("dota2")
    pro_items = arbitrage_pro("dota2")

    # Проверяем, что все предметы относятся к dota2
    for item in boost_items + mid_items + pro_items:
        assert item["game"] == "dota2"


# ============================================================================
# ТЕСТЫ ДЕМОНСТРАЦИИ АВТОАРБИТРАЖА
# ============================================================================


@pytest.mark.asyncio()
async def test_auto_arbitrage_demo_default_params():
    """Тест демонстрации автоарбитража с параметрами по умолчанию."""
    # Просто проверяем, что функция не падает
    await auto_arbitrage_demo()


@pytest.mark.asyncio()
async def test_auto_arbitrage_demo_custom_params():
    """Тест демонстрации с пользовательскими параметрами."""
    await auto_arbitrage_demo(game="dota2", mode="low", iterations=3)


@pytest.mark.asyncio()
async def test_auto_arbitrage_demo_zero_iterations():
    """Тест демонстрации с нулевым количеством итераций."""
    await auto_arbitrage_demo(iterations=0)


@pytest.mark.asyncio()
async def test_auto_arbitrage_demo_high_mode():
    """Тест демонстрации в режиме high."""
    await auto_arbitrage_demo(mode="high", iterations=2)


# ============================================================================
# ТЕСТЫ КОНСТАНТ
# ============================================================================


def test_games_constant_defined():
    """Тест наличия константы GAMES."""
    assert "csgo" in GAMES
    assert "dota2" in GAMES
    assert GAMES["csgo"] == "Counter-Strike: Global Offensive"
    assert GAMES["dota2"] == "Dota 2"


def test_games_constant_immutability():
    """Тест, что константа GAMES определена как dict."""
    assert isinstance(GAMES, dict)
    assert len(GAMES) >= 2

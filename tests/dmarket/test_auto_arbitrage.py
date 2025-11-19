"""Тесты для модуля auto_arbitrage.py.

Модуль тестирует функциональность автоматического арбитража с генерацией
случайных предметов и различными режимами фильтрации.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.auto_arbitrage import (
    GAMES,
    arbitrage_boost,
    arbitrage_mid,
    arbitrage_pro,
    auto_arbitrage_demo,
    generate_random_items,
    main,
)


class TestConstants:
    """Тесты для констант модуля."""

    def test_games_constant_exists(self):
        """Проверка наличия константы GAMES."""
        assert isinstance(GAMES, dict)

    def test_games_contains_csgo(self):
        """Проверка наличия csgo в словаре игр."""
        assert "csgo" in GAMES
        assert GAMES["csgo"] == "Counter-Strike: Global Offensive"

    def test_games_contains_dota2(self):
        """Проверка наличия dota2 в словаре игр."""
        assert "dota2" in GAMES
        assert GAMES["dota2"] == "Dota 2"


class TestGenerateRandomItems:
    """Тесты для функции generate_random_items."""

    def test_generate_random_items_returns_list(self):
        """Проверка что функция возвращает список."""
        result = generate_random_items("csgo")
        assert isinstance(result, list)

    def test_generate_random_items_default_count(self):
        """Проверка генерации по умолчанию 10 предметов."""
        result = generate_random_items("csgo")
        assert len(result) == 10

    def test_generate_random_items_custom_count(self):
        """Проверка генерации кастомного количества предметов."""
        result = generate_random_items("csgo", count=5)
        assert len(result) == 5

    def test_generate_random_items_zero_count(self):
        """Проверка генерации 0 предметов."""
        result = generate_random_items("csgo", count=0)
        assert len(result) == 0

    def test_generate_random_items_large_count(self):
        """Проверка генерации большого количества предметов."""
        result = generate_random_items("csgo", count=100)
        assert len(result) == 100

    def test_generate_random_items_structure(self):
        """Проверка структуры сгенерированных предметов."""
        result = generate_random_items("csgo", count=1)
        assert len(result) == 1

        item = result[0]
        assert "id" in item
        assert "game" in item
        assert "price" in item
        assert "profit" in item

    def test_generate_random_items_game_field(self):
        """Проверка что поле game соответствует переданной игре."""
        result = generate_random_items("dota2", count=1)
        assert result[0]["game"] == "dota2"

    def test_generate_random_items_id_format(self):
        """Проверка формата ID предметов."""
        result = generate_random_items("csgo", count=3)
        assert result[0]["id"] == "item_0"
        assert result[1]["id"] == "item_1"
        assert result[2]["id"] == "item_2"

    def test_generate_random_items_price_range(self):
        """Проверка что цена в допустимом диапазоне."""
        result = generate_random_items("csgo", count=20)
        for item in result:
            assert 1 <= item["price"] <= 100

    def test_generate_random_items_profit_range(self):
        """Проверка что прибыль в допустимом диапазоне."""
        result = generate_random_items("csgo", count=20)
        for item in result:
            assert -10 <= item["profit"] <= 10


class TestArbitrageBoost:
    """Тесты для режима 'Разгон баланса' (boost)."""

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_boost_filters_negative_profit(self, mock_generate):
        """Проверка фильтрации предметов с отрицательной прибылью."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": -5},
            {"id": "2", "game": "csgo", "price": 20, "profit": 3},
            {"id": "3", "game": "csgo", "price": 15, "profit": -2},
        ]

        result = arbitrage_boost("csgo")

        assert len(result) == 2
        assert result[0]["profit"] == -5
        assert result[1]["profit"] == -2

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_boost_excludes_positive_profit(self, mock_generate):
        """Проверка исключения предметов с положительной прибылью."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 5},
            {"id": "2", "game": "csgo", "price": 20, "profit": 10},
        ]

        result = arbitrage_boost("csgo")

        assert len(result) == 0

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_boost_excludes_zero_profit(self, mock_generate):
        """Проверка исключения предметов с нулевой прибылью."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 0},
        ]

        result = arbitrage_boost("csgo")

        assert len(result) == 0

    def test_arbitrage_boost_calls_generate_with_game(self):
        """Проверка что функция вызывает генератор с правильной игрой."""
        with patch("src.dmarket.auto_arbitrage.generate_random_items") as mock:
            mock.return_value = []
            arbitrage_boost("dota2")
            mock.assert_called_once_with("dota2")


class TestArbitrageMid:
    """Тесты для режима 'Средний трейдер' (mid)."""

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_mid_filters_range(self, mock_generate):
        """Проверка фильтрации предметов в диапазоне 0-5."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": -1},
            {"id": "2", "game": "csgo", "price": 20, "profit": 0},
            {"id": "3", "game": "csgo", "price": 15, "profit": 3},
            {"id": "4", "game": "csgo", "price": 25, "profit": 5},
            {"id": "5", "game": "csgo", "price": 30, "profit": 6},
        ]

        result = arbitrage_mid("csgo")

        assert len(result) == 2
        assert result[0]["profit"] == 0
        assert result[1]["profit"] == 3

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_mid_includes_zero(self, mock_generate):
        """Проверка включения нулевой прибыли."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 0},
        ]

        result = arbitrage_mid("csgo")

        assert len(result) == 1
        assert result[0]["profit"] == 0

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_mid_excludes_five(self, mock_generate):
        """Проверка исключения прибыли >= 5."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 5},
        ]

        result = arbitrage_mid("csgo")

        assert len(result) == 0

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_mid_excludes_negative(self, mock_generate):
        """Проверка исключения отрицательной прибыли."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": -1},
        ]

        result = arbitrage_mid("csgo")

        assert len(result) == 0


class TestArbitragePro:
    """Тесты для режима 'Trade Pro' (pro)."""

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_pro_filters_high_profit(self, mock_generate):
        """Проверка фильтрации предметов с высокой прибылью."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 3},
            {"id": "2", "game": "csgo", "price": 20, "profit": 5},
            {"id": "3", "game": "csgo", "price": 15, "profit": 10},
        ]

        result = arbitrage_pro("csgo")

        assert len(result) == 2
        assert result[0]["profit"] == 5
        assert result[1]["profit"] == 10

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_pro_includes_exactly_five(self, mock_generate):
        """Проверка включения прибыли ровно 5."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 5},
        ]

        result = arbitrage_pro("csgo")

        assert len(result) == 1
        assert result[0]["profit"] == 5

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_arbitrage_pro_excludes_below_five(self, mock_generate):
        """Проверка исключения прибыли < 5."""
        mock_generate.return_value = [
            {"id": "1", "game": "csgo", "price": 10, "profit": 4.99},
        ]

        result = arbitrage_pro("csgo")

        assert len(result) == 0


class TestAutoArbitrageDemo:
    """Тесты для асинхронной демонстрации арбитража."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_boost")
    async def test_auto_arbitrage_demo_low_mode(self, mock_boost, mock_sleep):
        """Проверка работы демо в режиме low."""
        mock_boost.return_value = [{"id": "1", "profit": -1}]

        await auto_arbitrage_demo("csgo", mode="low", iterations=2)

        assert mock_boost.call_count == 2
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_mid")
    async def test_auto_arbitrage_demo_medium_mode(self, mock_mid, mock_sleep):
        """Проверка работы демо в режиме medium."""
        mock_mid.return_value = [{"id": "1", "profit": 2}]

        await auto_arbitrage_demo("csgo", mode="medium", iterations=3)

        assert mock_mid.call_count == 3
        assert mock_sleep.call_count == 3

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_pro")
    async def test_auto_arbitrage_demo_high_mode(self, mock_pro, mock_sleep):
        """Проверка работы демо в режиме high."""
        mock_pro.return_value = [{"id": "1", "profit": 7}]

        await auto_arbitrage_demo("csgo", mode="high", iterations=1)

        assert mock_pro.call_count == 1
        assert mock_sleep.call_count == 1

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_mid")
    async def test_auto_arbitrage_demo_default_mode(self, mock_mid, mock_sleep):
        """Проверка работы демо с режимом по умолчанию (medium)."""
        mock_mid.return_value = []

        await auto_arbitrage_demo("csgo", iterations=1)

        mock_mid.assert_called_once()

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_mid")
    async def test_auto_arbitrage_demo_default_iterations(self, mock_mid, mock_sleep):
        """Проверка работы демо с итерациями по умолчанию (5)."""
        mock_mid.return_value = []

        await auto_arbitrage_demo("csgo")

        assert mock_mid.call_count == 5

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_boost")
    async def test_auto_arbitrage_demo_passes_game(self, mock_boost, mock_sleep):
        """Проверка передачи игры в функции фильтрации."""
        mock_boost.return_value = []

        await auto_arbitrage_demo("dota2", mode="low", iterations=1)

        mock_boost.assert_called_once_with("dota2")


class TestMain:
    """Тесты для функции main."""

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.auto_arbitrage_demo", new_callable=AsyncMock)
    async def test_main_calls_all_demos(self, mock_demo):
        """Проверка вызова всех комбинаций игр и режимов."""
        await main()

        assert mock_demo.call_count == 6

        # Проверяем все вызовы
        expected_calls = [
            (("csgo", "low"), {}),
            (("csgo", "medium"), {}),
            (("csgo", "high"), {}),
            (("dota2", "low"), {}),
            (("dota2", "medium"), {}),
            (("dota2", "high"), {}),
        ]

        actual_calls = [(call.args, call.kwargs) for call in mock_demo.call_args_list]

        assert actual_calls == expected_calls

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.auto_arbitrage_demo", new_callable=AsyncMock)
    async def test_main_order_of_calls(self, mock_demo):
        """Проверка порядка вызовов демо функций."""
        await main()

        calls = mock_demo.call_args_list

        # Проверяем порядок: csgo перед dota2, low->medium->high для каждой игры
        assert calls[0].args == ("csgo", "low")
        assert calls[1].args == ("csgo", "medium")
        assert calls[2].args == ("csgo", "high")
        assert calls[3].args == ("dota2", "low")
        assert calls[4].args == ("dota2", "medium")
        assert calls[5].args == ("dota2", "high")


class TestEdgeCases:
    """Тесты для граничных случаев и edge cases."""

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_all_modes_with_empty_items(self, mock_generate):
        """Проверка работы всех режимов с пустым списком предметов."""
        mock_generate.return_value = []

        assert arbitrage_boost("csgo") == []
        assert arbitrage_mid("csgo") == []
        assert arbitrage_pro("csgo") == []

    @pytest.mark.asyncio()
    @patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.dmarket.auto_arbitrage.arbitrage_mid")
    async def test_demo_with_zero_iterations(self, mock_mid, mock_sleep):
        """Проверка работы демо с нулевым количеством итераций."""
        mock_mid.return_value = []

        await auto_arbitrage_demo("csgo", iterations=0)

        mock_mid.assert_not_called()
        mock_sleep.assert_not_called()

    def test_generate_random_items_different_games(self):
        """Проверка генерации для разных игр."""
        csgo_items = generate_random_items("csgo", count=5)
        dota_items = generate_random_items("dota2", count=5)

        assert all(item["game"] == "csgo" for item in csgo_items)
        assert all(item["game"] == "dota2" for item in dota_items)

    @patch("src.dmarket.auto_arbitrage.generate_random_items")
    def test_filters_preserve_item_structure(self, mock_generate):
        """Проверка сохранения структуры предметов после фильтрации."""
        mock_generate.return_value = [
            {
                "id": "1",
                "game": "csgo",
                "price": 10,
                "profit": -1,
                "extra_field": "test",
            }
        ]

        result = arbitrage_boost("csgo")

        assert len(result) == 1
        assert result[0]["extra_field"] == "test"
        assert result[0]["id"] == "1"


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio()
    async def test_full_workflow_low_mode(self):
        """Тест полного workflow в режиме low."""
        with patch("src.dmarket.auto_arbitrage.asyncio.sleep", new_callable=AsyncMock):
            with patch("src.dmarket.auto_arbitrage.generate_random_items") as mock_gen:
                mock_gen.return_value = [{"id": "1", "game": "csgo", "price": 10, "profit": -5}]

                await auto_arbitrage_demo("csgo", mode="low", iterations=1)

                # Проверяем что генерация вызвана и предметы отфильтрованы
                mock_gen.assert_called_once()

    def test_real_generation_produces_valid_items(self):
        """Тест реальной генерации предметов без моков."""
        items = generate_random_items("csgo", count=50)

        assert len(items) == 50
        assert all(isinstance(item["id"], str) for item in items)
        assert all(isinstance(item["price"], (int, float)) for item in items)
        assert all(isinstance(item["profit"], (int, float)) for item in items)
        assert all(item["game"] == "csgo" for item in items)

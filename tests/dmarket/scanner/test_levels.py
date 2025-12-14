"""
Тесты для модуля scanner/levels.

Этот модуль тестирует конфигурации уровней арбитража
и вспомогательные функции для работы с уровнями.
"""

import pytest

from src.dmarket.scanner import levels


class TestGameIds:
    """Тесты для маппинга игр."""

    def test_game_ids_contains_all_games(self):
        """Тест наличия всех поддерживаемых игр."""
        # Arrange
        expected_games = ["csgo", "dota2", "tf2", "rust"]

        # Act & Assert
        for game in expected_games:
            assert game in levels.GAME_IDS

    def test_game_ids_values_are_strings(self):
        """Тест что все ID игр - строки."""
        # Act & Assert
        for game_id in levels.GAME_IDS.values():
            assert isinstance(game_id, str)
            assert len(game_id) > 0

    def test_csgo_game_id(self):
        """Тест ID для CS:GO."""
        # Act & Assert
        assert levels.GAME_IDS["csgo"] == "a8db"

    def test_dota2_game_id(self):
        """Тест ID для Dota 2."""
        # Act & Assert
        assert levels.GAME_IDS["dota2"] == "9a92"


class TestArbitrageLevels:
    """Тесты для определений уровней арбитража."""

    def test_all_levels_exist(self):
        """Тест наличия всех основных уровней."""
        # Arrange
        expected_levels = ["boost", "standard", "medium", "advanced", "pro"]

        # Act & Assert
        for level in expected_levels:
            assert level in levels.ARBITRAGE_LEVELS

    def test_each_level_has_required_fields(self):
        """Тест наличия обязательных полей в каждом уровне."""
        # Arrange
        required_fields = [
            "name",
            "min_profit_percent",
            "max_profit_percent",
            "price_range",
            "description",
        ]

        # Act & Assert
        for level_name, level_config in levels.ARBITRAGE_LEVELS.items():
            for field in required_fields:
                assert field in level_config, f"Level '{level_name}' missing field '{field}'"

    def test_boost_level_config(self):
        """Тест конфигурации уровня boost."""
        # Act
        boost = levels.ARBITRAGE_LEVELS["boost"]

        # Assert
        assert boost["name"] == "🚀 Разгон баланса"
        assert boost["min_profit_percent"] == 1.0
        assert boost["max_profit_percent"] == 5.0
        assert boost["price_range"] == (0.5, 3.0)
        assert "Low-risk" in boost["description"]

    def test_standard_level_config(self):
        """Тест конфигурации уровня standard."""
        # Act
        standard = levels.ARBITRAGE_LEVELS["standard"]

        # Assert
        assert standard["name"] == "⚡ Стандарт"
        assert standard["min_profit_percent"] == 5.0
        assert standard["max_profit_percent"] == 10.0
        assert standard["price_range"] == (3.0, 10.0)

    def test_pro_level_config(self):
        """Тест конфигурации уровня pro."""
        # Act
        pro = levels.ARBITRAGE_LEVELS["pro"]

        # Assert
        assert pro["name"] == "💎 Профи"
        assert pro["min_profit_percent"] == 20.0
        assert pro["max_profit_percent"] >= 20.0
        assert "High-risk" in pro["description"]

    def test_profit_percentages_are_ascending(self):
        """Тест что минимальные проценты прибыли возрастают с уровнем."""
        # Arrange
        level_order = ["boost", "standard", "medium", "advanced", "pro"]

        # Act
        min_profits = [
            levels.ARBITRAGE_LEVELS[level]["min_profit_percent"] for level in level_order
        ]

        # Assert
        for i in range(len(min_profits) - 1):
            assert min_profits[i] <= min_profits[i + 1], (
                f"Profit percentages should increase: {level_order[i]} -> {level_order[i + 1]}"
            )


class TestGetLevelConfig:
    """Тесты функции get_level_config."""

    def test_get_level_config_boost(self):
        """Тест получения конфигурации уровня boost."""
        # Act
        config = levels.get_level_config("boost")

        # Assert
        assert isinstance(config, dict)
        assert config["name"] == "🚀 Разгон баланса"
        assert config["min_profit_percent"] == 1.0

    def test_get_level_config_returns_copy(self):
        """Тест что функция возвращает копию конфигурации."""
        # Act
        config1 = levels.get_level_config("boost")
        config2 = levels.get_level_config("boost")

        # Modify first copy
        config1["custom_field"] = "test"

        # Assert
        assert "custom_field" not in config2
        assert "custom_field" not in levels.ARBITRAGE_LEVELS["boost"]

    def test_get_level_config_invalid_level(self):
        """Тест обработки невалидного уровня."""
        # Act & Assert
        with pytest.raises(KeyError) as exc_info:
            levels.get_level_config("invalid_level")

        assert "Unknown level" in str(exc_info.value)
        assert "Available levels" in str(exc_info.value)

    def test_get_level_config_all_levels(self):
        """Тест получения конфигурации для всех уровней."""
        # Arrange
        all_levels = ["boost", "standard", "medium", "advanced", "pro"]

        # Act & Assert
        for level in all_levels:
            config = levels.get_level_config(level)
            assert isinstance(config, dict)
            assert "name" in config
            assert "min_profit_percent" in config


class TestGetPriceRangeForLevel:
    """Тесты функции get_price_range_for_level."""

    def test_get_price_range_boost(self):
        """Тест получения диапазона цен для boost."""
        # Act
        price_range = levels.get_price_range_for_level("boost")

        # Assert
        assert isinstance(price_range, tuple)
        assert len(price_range) == 2
        assert price_range == (0.5, 3.0)

    def test_get_price_range_pro(self):
        """Тест получения диапазона цен для pro."""
        # Act
        price_range = levels.get_price_range_for_level("pro")

        # Assert
        assert isinstance(price_range, tuple)
        assert price_range == (100.0, 1000.0)

    def test_get_price_range_invalid_level(self):
        """Тест обработки невалидного уровня."""
        # Act & Assert
        with pytest.raises(KeyError):
            levels.get_price_range_for_level("nonexistent")

    def test_price_ranges_are_valid(self):
        """Тест что все диапазоны цен валидны (min < max)."""
        # Arrange
        all_levels = levels.get_all_levels()

        # Act & Assert
        for level in all_levels:
            min_price, max_price = levels.get_price_range_for_level(level)
            assert min_price < max_price, (
                f"Invalid price range for level '{level}': {min_price} >= {max_price}"
            )


class TestGetAllLevels:
    """Тесты функции get_all_levels."""

    def test_get_all_levels_returns_list(self):
        """Тест что функция возвращает список."""
        # Act
        all_levels = levels.get_all_levels()

        # Assert
        assert isinstance(all_levels, list)

    def test_get_all_levels_count(self):
        """Тест количества уровней."""
        # Act
        all_levels = levels.get_all_levels()

        # Assert
        assert len(all_levels) == 5

    def test_get_all_levels_content(self):
        """Тест содержимого списка уровней."""
        # Act
        all_levels = levels.get_all_levels()

        # Assert
        expected = ["boost", "standard", "medium", "advanced", "pro"]
        assert all_levels == expected

    def test_get_all_levels_returns_new_list(self):
        """Тест что функция возвращает новый список каждый раз."""
        # Act
        list1 = levels.get_all_levels()
        list2 = levels.get_all_levels()

        # Modify first list
        list1.append("custom")

        # Assert
        assert "custom" not in list2


class TestGetLevelDescription:
    """Тесты функции get_level_description."""

    def test_get_level_description_boost(self):
        """Тест получения описания для boost."""
        # Act
        description = levels.get_level_description("boost")

        # Assert
        assert isinstance(description, str)
        assert len(description) > 0
        assert "Low-risk" in description

    def test_get_level_description_all_levels(self):
        """Тест получения описания для всех уровней."""
        # Arrange
        all_levels = levels.get_all_levels()

        # Act & Assert
        for level in all_levels:
            description = levels.get_level_description(level)
            assert isinstance(description, str)
            assert len(description) > 0

    def test_get_level_description_invalid_level(self):
        """Тест обработки невалидного уровня."""
        # Act & Assert
        with pytest.raises(KeyError):
            levels.get_level_description("invalid")


class TestGetProfitRangeForLevel:
    """Тесты функции get_profit_range_for_level."""

    def test_get_profit_range_boost(self):
        """Тест получения диапазона прибыли для boost."""
        # Act
        profit_range = levels.get_profit_range_for_level("boost")

        # Assert
        assert isinstance(profit_range, tuple)
        assert len(profit_range) == 2
        assert profit_range == (1.0, 5.0)

    def test_get_profit_range_pro(self):
        """Тест получения диапазона прибыли для pro."""
        # Act
        profit_range = levels.get_profit_range_for_level("pro")

        # Assert
        assert isinstance(profit_range, tuple)
        assert profit_range == (20.0, 100.0)

    def test_get_profit_range_all_levels(self):
        """Тест получения диапазона прибыли для всех уровней."""
        # Arrange
        all_levels = levels.get_all_levels()

        # Act & Assert
        for level in all_levels:
            min_profit, max_profit = levels.get_profit_range_for_level(level)
            assert isinstance(min_profit, float)
            assert isinstance(max_profit, float)
            assert min_profit < max_profit

    def test_get_profit_range_invalid_level(self):
        """Тест обработки невалидного уровня."""
        # Act & Assert
        with pytest.raises(KeyError):
            levels.get_profit_range_for_level("nonexistent")


class TestLevelConsistency:
    """Тесты согласованности данных между уровнями."""

    def test_level_names_have_emojis(self):
        """Тест что все имена уровней содержат эмодзи."""
        # Arrange
        all_levels = levels.get_all_levels()

        # Act & Assert
        for level in all_levels:
            config = levels.get_level_config(level)
            name = config["name"]
            # Проверяем наличие эмодзи или специальных символов Unicode
            has_emoji = any(ord(char) > 0x2000 for char in name)
            assert has_emoji, (
                f"Level '{level}' name '{name}' should contain emoji or special Unicode char"
            )

    def test_descriptions_are_in_english(self):
        """Тест что все описания на английском."""
        # Arrange
        all_levels = levels.get_all_levels()

        # Act & Assert
        for level in all_levels:
            description = levels.get_level_description(level)
            # Проверяем отсутствие кириллицы
            has_cyrillic = any("\u0400" <= char <= "\u04ff" for char in description)
            assert not has_cyrillic, (
                f"Level '{level}' description should be in English, got: {description}"
            )

    def test_price_ranges_dont_overlap_significantly(self):
        """Тест что ценовые диапазоны уровней логично разнесены."""
        # Arrange
        level_order = ["boost", "standard", "medium", "advanced", "pro"]

        # Act
        ranges = [levels.get_price_range_for_level(level) for level in level_order]

        # Assert - каждый следующий уровень должен иметь более высокую минимальную цену
        for i in range(len(ranges) - 1):
            current_min, current_max = ranges[i]
            next_min, next_max = ranges[i + 1]

            # Проверяем что минимальная цена следующего уровня больше или равна текущей
            assert next_min >= current_min, (
                f"Level {level_order[i + 1]} min price should be >= {level_order[i]} min price"
            )

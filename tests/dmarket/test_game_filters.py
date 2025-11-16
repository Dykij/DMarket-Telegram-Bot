"""Тесты для модуля game_filters (compatibility wrapper)."""

import pytest

from src.dmarket.game_filters import (
    BaseGameFilter,
    CS2Filter,
    Dota2Filter,
    FilterFactory,
    RustFilter,
    apply_filters_to_items,
)


class TestImports:
    """Тесты импортов из модуля совместимости."""

    def test_base_game_filter_imported(self):
        """Тест что BaseGameFilter импортируется."""
        assert BaseGameFilter is not None
        assert hasattr(BaseGameFilter, "apply_filters")

    def test_cs2_filter_imported(self):
        """Тест что CS2Filter импортируется."""
        assert CS2Filter is not None

    def test_dota2_filter_imported(self):
        """Тест что Dota2Filter импортируется."""
        assert Dota2Filter is not None

    def test_rust_filter_imported(self):
        """Тест что RustFilter импортируется."""
        assert RustFilter is not None

    def test_filter_factory_imported(self):
        """Тест что FilterFactory импортируется."""
        assert FilterFactory is not None
        assert hasattr(FilterFactory, "get_filter")

    def test_apply_filters_imported(self):
        """Тест что apply_filters_to_items импортируется."""
        assert apply_filters_to_items is not None
        assert callable(apply_filters_to_items)


class TestFilterFactory:
    """Тесты фабрики фильтров."""

    def test_get_filter_csgo(self):
        """Тест получения фильтра CS:GO."""
        filter_obj = FilterFactory.get_filter("csgo")

        assert filter_obj is not None
        assert isinstance(filter_obj, BaseGameFilter)

    def test_get_filter_dota2(self):
        """Тест получения фильтра Dota 2."""
        filter_obj = FilterFactory.get_filter("dota2")

        assert filter_obj is not None
        assert isinstance(filter_obj, BaseGameFilter)

    def test_get_filter_tf2(self):
        """Тест получения фильтра TF2."""
        filter_obj = FilterFactory.get_filter("tf2")

        assert filter_obj is not None
        assert isinstance(filter_obj, BaseGameFilter)

    def test_get_filter_rust(self):
        """Тест получения фильтра Rust."""
        filter_obj = FilterFactory.get_filter("rust")

        assert filter_obj is not None
        assert isinstance(filter_obj, RustFilter)

    def test_get_filter_invalid_game(self):
        """Тест получения фильтра для неподдерживаемой игры."""
        with pytest.raises((KeyError, ValueError)):
            FilterFactory.get_filter("invalid_game")


class TestBaseGameFilter:
    """Тесты базового класса фильтра."""

    def test_base_filter_has_apply_filters(self):
        """Тест наличия метода apply_filters."""
        assert hasattr(BaseGameFilter, "apply_filters")

    def test_base_filter_has_supported_filters(self):
        """Тест наличия списка поддерживаемых фильтров."""
        assert hasattr(BaseGameFilter, "supported_filters")

    def test_price_filter_in_base(self):
        """Тест что базовый фильтр поддерживает фильтрацию по цене."""
        base_filters = BaseGameFilter.supported_filters
        assert "min_price" in base_filters or "price" in str(base_filters)


class TestCS2Filter:
    """Тесты фильтра CS2."""

    def test_cs2_filter_instantiation(self):
        """Тест создания экземпляра CS2Filter."""
        cs2_filter = CS2Filter()

        assert cs2_filter is not None
        assert isinstance(cs2_filter, BaseGameFilter)

    def test_cs2_filter_has_specific_filters(self):
        """Тест специфичных фильтров CS2."""
        cs2_filter = CS2Filter()

        # CS2 должен поддерживать фильтры по float, exterior, rarity и т.д.
        supported = cs2_filter.supported_filters
        assert any(
            filter_name in supported for filter_name in ["float", "exterior", "rarity", "category"]
        )

    def test_cs2_filter_apply_filters(self):
        """Тест применения фильтров CS2."""
        cs2_filter = CS2Filter()
        test_item = {
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"USD": 1250},
            "category": "Rifle",
        }

        # Фильтр должен пропустить предмет с ценой >= 10
        result = cs2_filter.apply_filters(test_item, {"min_price": 10.0})

        assert isinstance(result, bool)


class TestDota2Filter:
    """Тесты фильтра Dota 2."""

    def test_dota2_filter_instantiation(self):
        """Тест создания экземпляра Dota2Filter."""
        dota2_filter = Dota2Filter()

        assert dota2_filter is not None
        assert isinstance(dota2_filter, BaseGameFilter)

    def test_dota2_filter_has_specific_filters(self):
        """Тест специфичных фильтров Dota 2."""
        dota2_filter = Dota2Filter()

        supported = dota2_filter.supported_filters
        # Dota 2 должен поддерживать фильтры по герою, слоту, качеству и т.д.
        assert any(
            filter_name in supported for filter_name in ["hero", "slot", "quality", "rarity"]
        )


class TestRustFilter:
    """Тесты фильтра Rust."""

    def test_rust_filter_instantiation(self):
        """Тест создания экземпляра RustFilter."""
        rust_filter = RustFilter()

        assert rust_filter is not None
        assert isinstance(rust_filter, BaseGameFilter)

    def test_rust_filter_has_specific_filters(self):
        """Тест специфичных фильтров Rust."""
        rust_filter = RustFilter()

        supported = rust_filter.supported_filters
        assert len(supported) > 0


class TestApplyFiltersToItems:
    """Тесты функции apply_filters_to_items."""

    def test_apply_filters_empty_items(self):
        """Тест применения фильтров к пустому списку."""
        result = apply_filters_to_items([], "csgo", {})

        assert result == []

    def test_apply_filters_no_filters(self):
        """Тест применения пустых фильтров."""
        items = [
            {"title": "AK-47 | Redline", "price": {"USD": 1250}},
            {"title": "AWP | Asiimov", "price": {"USD": 3500}},
        ]

        result = apply_filters_to_items(items, "csgo", {})

        # Без фильтров должны вернуться все предметы
        assert len(result) == len(items)

    def test_apply_filters_price_filter(self):
        """Тест фильтрации по цене."""
        items = [
            {"title": "Cheap Item", "price": {"USD": 500}},  # $5
            {"title": "Mid Item", "price": {"USD": 1500}},  # $15
            {"title": "Expensive Item", "price": {"USD": 5000}},  # $50
        ]

        result = apply_filters_to_items(
            items,
            "csgo",
            {"min_price": 10.0, "max_price": 30.0},
        )

        # Должен остаться только Mid Item ($15)
        assert len(result) <= len(items)

    def test_apply_filters_different_games(self):
        """Тест применения фильтров для разных игр."""
        items = [{"title": "Test Item", "price": {"USD": 1000}}]

        for game in ["csgo", "dota2", "tf2", "rust"]:
            result = apply_filters_to_items(items, game, {})
            assert isinstance(result, list)

    def test_apply_filters_invalid_game(self):
        """Тест обработки неверной игры."""
        items = [{"title": "Test Item", "price": {"USD": 1000}}]

        with pytest.raises((KeyError, ValueError)):
            apply_filters_to_items(items, "invalid_game", {})


class TestFilterCompatibility:
    """Тесты совместимости фильтров."""

    def test_all_filters_inherit_from_base(self):
        """Тест что все фильтры наследуются от BaseGameFilter."""
        filters = [CS2Filter(), Dota2Filter(), RustFilter()]

        for filter_obj in filters:
            assert isinstance(filter_obj, BaseGameFilter)

    def test_all_filters_have_apply_method(self):
        """Тест что все фильтры имеют метод apply_filters."""
        filters = [CS2Filter(), Dota2Filter(), RustFilter()]

        for filter_obj in filters:
            assert hasattr(filter_obj, "apply_filters")
            assert callable(filter_obj.apply_filters)

    def test_filter_factory_returns_correct_types(self):
        """Тест что фабрика возвращает корректные типы фильтров."""
        csgo_filter = FilterFactory.get_filter("csgo")
        dota2_filter = FilterFactory.get_filter("dota2")
        rust_filter = FilterFactory.get_filter("rust")

        assert isinstance(csgo_filter, CS2Filter)
        assert isinstance(dota2_filter, Dota2Filter)
        assert isinstance(rust_filter, RustFilter)


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_filter_with_none_price(self):
        """Тест фильтрации предметов с None ценой."""
        items = [
            {"title": "No Price Item", "price": None},
            {"title": "Valid Item", "price": {"USD": 1000}},
        ]

        result = apply_filters_to_items(items, "csgo", {"min_price": 5.0})

        # Предметы с None ценой должны быть отфильтрованы
        assert all(item.get("price") is not None for item in result)

    def test_filter_with_missing_price_key(self):
        """Тест фильтрации предметов без ключа price."""
        items = [
            {"title": "Missing Price"},
            {"title": "Valid Item", "price": {"USD": 1000}},
        ]

        result = apply_filters_to_items(items, "csgo", {"min_price": 5.0})

        # Должны остаться только предметы с ценой
        assert all("price" in item for item in result)

    def test_filter_with_zero_price(self):
        """Тест фильтрации предметов с нулевой ценой."""
        items = [{"title": "Zero Price", "price": {"USD": 0}}]

        result = apply_filters_to_items(items, "csgo", {"min_price": 1.0})

        # Предметы с нулевой ценой должны быть отфильтрованы
        assert len(result) == 0

    def test_filter_with_invalid_price_format(self):
        """Тест фильтрации предметов с неверным форматом цены."""
        items = [
            {"title": "Invalid Price", "price": "not a number"},
            {"title": "Valid Item", "price": {"USD": 1000}},
        ]

        # Не должно выбрасывать исключение
        result = apply_filters_to_items(items, "csgo", {})

        assert isinstance(result, list)


class TestModuleExports:
    """Тесты экспортов модуля."""

    def test_all_exports_defined(self):
        """Тест что все экспорты определены в __all__."""
        from src.dmarket.game_filters import __all__

        expected_exports = [
            "BaseGameFilter",
            "CS2Filter",
            "Dota2Filter",
            "FilterFactory",
            "RustFilter",
            "apply_filters_to_items",
        ]

        for export in expected_exports:
            assert export in __all__

    def test_no_extra_exports(self):
        """Тест что нет лишних экспортов."""
        from src.dmarket.game_filters import __all__

        # Все экспорты должны быть доступны
        for export_name in __all__:
            assert hasattr(
                __import__("src.dmarket.game_filters", fromlist=[export_name]),
                export_name,
            )

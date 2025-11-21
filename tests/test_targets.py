"""Тесты для модуля управления таргетами (buy orders) DMarket.

Этот модуль тестирует функциональность TargetManager для создания,
управления и мониторинга таргетов (buy orders) на платформе DMarket.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.targets import TargetManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def mock_api():
    """Создать мок DMarket API клиента."""
    api = MagicMock()
    # Настроить async методы как AsyncMock
    api.create_targets = AsyncMock()
    api.get_user_targets = AsyncMock()
    api.delete_targets = AsyncMock()
    api.get_targets_by_title = AsyncMock()
    api.get_market_items = AsyncMock()
    api.get_closed_targets = AsyncMock()
    return api


@pytest.fixture()
def target_manager(mock_api):
    """Создать экземпляр TargetManager с моком API."""
    return TargetManager(mock_api)


@pytest.fixture()
def sample_target_data():
    """Пример данных таргета."""
    return {
        "title": "AK-47 | Redline (Field-Tested)",
        "price": 8.50,
        "amount": 2,
        "game": "csgo",
        "attrs": {"exterior": "Field-Tested"},
    }


@pytest.fixture()
def sample_api_response():
    """Пример успешного ответа API при создании таргета."""
    return {
        "Result": [
            {
                "TargetID": "target_123456",
                "Title": "AK-47 | Redline (Field-Tested)",
                "Status": "Created",
            }
        ]
    }


@pytest.fixture()
def sample_targets_list():
    """Пример списка таргетов пользователя."""
    return {
        "Items": [
            {
                "TargetID": "target_1",
                "Title": "AK-47 | Redline (Field-Tested)",
                "Price": {"Amount": 850, "Currency": "USD"},
                "Amount": 1,
                "Status": "TargetStatusActive",
                "CreatedAt": 1699000000,
                "Attrs": {},
            },
            {
                "TargetID": "target_2",
                "Title": "AWP | Asiimov (Field-Tested)",
                "Price": {"Amount": 4500, "Currency": "USD"},
                "Amount": 2,
                "Status": "TargetStatusActive",
                "CreatedAt": 1699000100,
                "Attrs": {"exterior": "Field-Tested"},
            },
        ],
        "Total": "2",
    }


@pytest.fixture()
def sample_market_items():
    """Пример предметов с маркета."""
    return {
        "objects": [
            {
                "itemId": "item_123",
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": "1000"},
            },
            {
                "itemId": "item_124",
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": "1050"},
            },
        ]
    }


@pytest.fixture()
def sample_closed_targets():
    """Пример закрытых таргетов."""
    return {
        "Trades": [
            {
                "TargetID": "target_old_1",
                "Title": "M4A4 | Howl (Field-Tested)",
                "Price": {"Amount": 150000, "Currency": "USD"},
                "Status": "successful",
                "ClosedAt": 1699500000,
                "CreatedAt": 1699000000,
            },
            {
                "TargetID": "target_old_2",
                "Title": "AWP | Dragon Lore (Factory New)",
                "Price": {"Amount": 500000, "Currency": "USD"},
                "Status": "successful",
                "ClosedAt": 1699600000,
                "CreatedAt": 1699100000,
            },
        ],
        "Total": "2",
    }


# ============================================================================
# Tests: Initialization
# ============================================================================


class TestTargetManagerInitialization:
    """Тесты инициализации TargetManager."""

    def test_init_creates_manager_with_api_client_reference(self, mock_api):
        """Тест проверяет создание менеджера со ссылкой на API клиент."""
        # Arrange & Act
        manager = TargetManager(mock_api)

        # Assert
        assert manager.api == mock_api

    def test_init_stores_api_reference_correctly(self, target_manager, mock_api):
        """Тест проверяет корректное сохранение ссылки на API."""
        # Arrange & Act - фикстура уже создала target_manager

        # Assert
        assert target_manager.api is mock_api


# ============================================================================
# Tests: Create Target
# ============================================================================


class TestCreateTarget:
    """Тесты создания таргетов."""

    @pytest.mark.asyncio()
    async def test_create_target_returns_success_with_valid_data(
        self, target_manager, mock_api, sample_api_response
    ):
        """Тест проверяет успешное создание таргета с корректными данными."""
        # Arrange
        mock_api.create_targets.return_value = sample_api_response

        # Act
        result = await target_manager.create_target(
            game="csgo",
            title="AK-47 | Redline (Field-Tested)",
            price=8.50,
            amount=1,
        )

        # Assert
        assert result["success"] is True
        assert result["target_id"] == "target_123456"
        assert result["title"] == "AK-47 | Redline (Field-Tested)"
        assert result["price"] == 8.50
        assert result["amount"] == 1
        assert result["game"] == "csgo"

        # Проверка вызова API
        mock_api.create_targets.assert_called_once()
        call_args = mock_api.create_targets.call_args
        assert call_args.kwargs["game_id"] == "a8db"
        targets_data = call_args.kwargs["targets"]
        assert len(targets_data) == 1
        assert targets_data[0]["Title"] == "AK-47 | Redline (Field-Tested)"
        assert targets_data[0]["Price"]["Amount"] == 850  # $8.50 -> 850 центов

    @pytest.mark.asyncio()
    async def test_create_target_with_attributes_includes_attrs_in_api_call(
        self, target_manager, mock_api, sample_api_response
    ):
        """Тест проверяет передачу атрибутов при создании таргета."""
        # Arrange
        mock_api.create_targets.return_value = sample_api_response
        attrs = {"floatPartValue": 0.15, "phase": "Phase 2"}

        # Act
        result = await target_manager.create_target(
            game="csgo",
            title="Karambit | Doppler (Factory New)",
            price=250.00,
            amount=1,
            attrs=attrs,
        )

        # Assert
        assert result["success"] is True

        # Проверка передачи атрибутов
        call_args = mock_api.create_targets.call_args
        targets_data = call_args.kwargs["targets"]
        assert targets_data[0]["Attrs"] == attrs

    @pytest.mark.asyncio()
    async def test_create_target_raises_error_when_price_is_invalid(self, target_manager):
        """Тест проверяет выброс ошибки при невалидной цене."""
        # Arrange & Act & Assert - нулевая цена
        with pytest.raises(ValueError, match="Цена должна быть больше 0"):
            await target_manager.create_target(
                game="csgo",
                title="Test Item",
                price=0.0,
            )

        # Arrange & Act & Assert - отрицательная цена
        with pytest.raises(ValueError, match="Цена должна быть больше 0"):
            await target_manager.create_target(
                game="csgo",
                title="Test Item",
                price=-5.0,
            )

    @pytest.mark.asyncio()
    async def test_create_target_raises_error_when_price_is_too_high(self, target_manager):
        """Тест проверяет выброс ошибки при слишком высокой цене."""
        with pytest.raises(ValueError, match="Цена не может превышать"):
            await target_manager.create_target(
                game="csgo",
                title="Expensive Item",
                price=100001.0,
            )

    @pytest.mark.asyncio()
    async def test_create_target_raises_error_when_price_has_too_many_decimals(
        self, target_manager
    ):
        """Тест проверяет выброс ошибки при цене с > 2 знаками после запятой."""
        with pytest.raises(ValueError, match="Цена не может иметь более 2 знаков"):
            await target_manager.create_target(
                game="csgo",
                title="Precise Item",
                price=10.555,
            )

    @pytest.mark.asyncio()
    async def test_create_target_raises_error_when_amount_is_out_of_range(self, target_manager):
        """Тест проверяет выброс ошибки при невалидном количестве."""
        # Arrange & Act & Assert - нулевое количество
        with pytest.raises(ValueError, match="Количество должно быть от 1 до 100"):
            await target_manager.create_target(
                game="csgo",
                title="Test Item",
                price=10.0,
                amount=0,
            )

        # Arrange & Act & Assert - превышение максимума
        with pytest.raises(ValueError, match="Количество должно быть от 1 до 100"):
            await target_manager.create_target(
                game="csgo",
                title="Test Item",
                price=10.0,
                amount=101,
            )

    @pytest.mark.asyncio()
    async def test_create_target_title_validation(self, target_manager):
        """Тест валидации названия предмета."""
        with pytest.raises(ValueError, match="Название предмета не может быть пустым"):
            await target_manager.create_target(
                game="csgo",
                title="",
                price=10.0,
            )

        with pytest.raises(ValueError, match="Название предмета не может быть пустым"):
            await target_manager.create_target(
                game="csgo",
                title="   ",
                price=10.0,
            )

    @pytest.mark.asyncio()
    async def test_create_target_game_conversion(
        self, target_manager, mock_api, sample_api_response
    ):
        """Тест конвертации кода игры в gameId."""
        mock_api.create_targets.return_value = sample_api_response

        test_cases = [
            ("csgo", "a8db"),
            ("dota2", "9a92"),
            ("tf2", "tf2"),
            ("rust", "rust"),
            ("CSGO", "a8db"),  # Проверка case-insensitive
        ]

        for game_code, expected_game_id in test_cases:
            await target_manager.create_target(
                game=game_code,
                title="Test Item",
                price=10.0,
            )

            call_args = mock_api.create_targets.call_args
            assert call_args.kwargs["game_id"] == expected_game_id

    @pytest.mark.asyncio()
    async def test_create_target_price_conversion_to_cents(
        self, target_manager, mock_api, sample_api_response
    ):
        """Тест конвертации цены из долларов в центы."""
        mock_api.create_targets.return_value = sample_api_response

        test_prices = [
            (1.00, 100),
            (10.50, 1050),
            (0.05, 5),
            (99.99, 9999),
        ]

        for price_usd, expected_cents in test_prices:
            await target_manager.create_target(
                game="csgo",
                title="Test Item",
                price=price_usd,
            )

            call_args = mock_api.create_targets.call_args
            targets_data = call_args.kwargs["targets"]
            assert targets_data[0]["Price"]["Amount"] == expected_cents

    @pytest.mark.asyncio()
    async def test_create_target_api_error(self, target_manager, mock_api):
        """Тест обработки ошибки API."""
        mock_api.create_targets.side_effect = Exception("API Error")

        result = await target_manager.create_target(
            game="csgo",
            title="Test Item",
            price=10.0,
        )

        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]

    @pytest.mark.asyncio()
    async def test_create_target_invalid_api_response(self, target_manager, mock_api):
        """Тест обработки некорректного ответа API."""
        mock_api.create_targets.return_value = {"invalid": "response"}

        result = await target_manager.create_target(
            game="csgo",
            title="Test Item",
            price=10.0,
        )

        assert result["success"] is False
        assert "Некорректный ответ от API" in result["error"]


# ============================================================================
# Tests: Get User Targets
# ============================================================================


class TestGetUserTargets:
    """Тесты получения таргетов пользователя."""

    @pytest.mark.asyncio()
    async def test_get_user_targets_success(self, target_manager, mock_api, sample_targets_list):
        """Тест успешного получения списка таргетов."""
        mock_api.get_user_targets.return_value = sample_targets_list

        targets = await target_manager.get_user_targets(game="csgo", status="active")

        assert len(targets) == 2
        assert targets[0]["target_id"] == "target_1"
        assert targets[0]["title"] == "AK-47 | Redline (Field-Tested)"
        assert targets[0]["price"] == 8.50
        assert targets[0]["amount"] == 1
        assert targets[1]["price"] == 45.00

        # Проверка вызова API
        mock_api.get_user_targets.assert_called_once()
        call_args = mock_api.get_user_targets.call_args
        assert call_args.kwargs["game_id"] == "a8db"
        assert call_args.kwargs["status"] == "TargetStatusActive"

    @pytest.mark.asyncio()
    async def test_get_user_targets_status_filter(self, target_manager, mock_api):
        """Тест фильтрации по статусу."""
        mock_api.get_user_targets.return_value = {"Items": []}

        test_cases = [
            ("active", "TargetStatusActive"),
            ("inactive", "TargetStatusInactive"),
            ("all", None),
        ]

        for status_input, expected_filter in test_cases:
            await target_manager.get_user_targets(game="csgo", status=status_input)

            call_args = mock_api.get_user_targets.call_args
            assert call_args.kwargs["status"] == expected_filter

    @pytest.mark.asyncio()
    async def test_get_user_targets_empty_result(self, target_manager, mock_api):
        """Тест получения пустого списка таргетов."""
        mock_api.get_user_targets.return_value = {"Items": []}

        targets = await target_manager.get_user_targets(game="csgo")

        assert len(targets) == 0

    @pytest.mark.asyncio()
    async def test_get_user_targets_no_items_key(self, target_manager, mock_api):
        """Тест обработки ответа без ключа Items."""
        mock_api.get_user_targets.return_value = {"invalid": "response"}

        targets = await target_manager.get_user_targets(game="csgo")

        assert len(targets) == 0

    @pytest.mark.asyncio()
    async def test_get_user_targets_api_error(self, target_manager, mock_api):
        """Тест обработки ошибки API."""
        mock_api.get_user_targets.side_effect = Exception("API Error")

        targets = await target_manager.get_user_targets(game="csgo")

        assert len(targets) == 0


# ============================================================================
# Tests: Delete Target
# ============================================================================


class TestDeleteTarget:
    """Тесты удаления таргетов."""

    @pytest.mark.asyncio()
    async def test_delete_target_success(self, target_manager, mock_api):
        """Тест успешного удаления таргета."""
        mock_api.delete_targets.return_value = {
            "Result": [{"TargetID": "target_123", "Status": "Deleted"}]
        }

        success = await target_manager.delete_target("target_123")

        assert success is True
        mock_api.delete_targets.assert_called_once_with(target_ids=["target_123"])

    @pytest.mark.asyncio()
    async def test_delete_target_failed_status(self, target_manager, mock_api):
        """Тест обработки неудачного статуса удаления."""
        mock_api.delete_targets.return_value = {
            "Result": [{"TargetID": "target_123", "Status": "Failed"}]
        }

        success = await target_manager.delete_target("target_123")

        assert success is False

    @pytest.mark.asyncio()
    async def test_delete_target_invalid_response(self, target_manager, mock_api):
        """Тест обработки некорректного ответа API."""
        mock_api.delete_targets.return_value = {"invalid": "response"}

        success = await target_manager.delete_target("target_123")

        assert success is False

    @pytest.mark.asyncio()
    async def test_delete_target_api_error(self, target_manager, mock_api):
        """Тест обработки ошибки API при удалении."""
        mock_api.delete_targets.side_effect = Exception("API Error")

        success = await target_manager.delete_target("target_123")

        assert success is False


# ============================================================================
# Tests: Delete All Targets
# ============================================================================


class TestDeleteAllTargets:
    """Тесты массового удаления таргетов."""

    @pytest.mark.asyncio()
    async def test_delete_all_targets_without_confirmation(self, target_manager):
        """Тест отказа удаления без подтверждения."""
        result = await target_manager.delete_all_targets(game="csgo", confirm=False)

        assert result["success"] is False
        assert "подтверждение" in result["error"].lower()

    @pytest.mark.asyncio()
    async def test_delete_all_targets_with_confirmation(
        self, target_manager, mock_api, sample_targets_list
    ):
        """Тест успешного удаления всех таргетов с подтверждением."""
        mock_api.get_user_targets.return_value = sample_targets_list
        mock_api.delete_targets.return_value = {
            "Result": [{"TargetID": "target_1", "Status": "Deleted"}]
        }

        result = await target_manager.delete_all_targets(game="csgo", confirm=True)

        assert result["success"] is True
        assert result["deleted_count"] == 2
        assert result["failed_count"] == 0
        assert result["total"] == 2

        # Проверка вызовов API
        assert mock_api.delete_targets.call_count == 2

    @pytest.mark.asyncio()
    async def test_delete_all_targets_no_active_targets(self, target_manager, mock_api):
        """Тест удаления когда нет активных таргетов."""
        mock_api.get_user_targets.return_value = {"Items": []}

        result = await target_manager.delete_all_targets(game="csgo", confirm=True)

        assert result["success"] is True
        assert result["deleted_count"] == 0
        assert "Нет активных таргетов" in result["message"]

    @pytest.mark.asyncio()
    async def test_delete_all_targets_partial_failure(
        self, target_manager, mock_api, sample_targets_list
    ):
        """Тест частичного успеха при удалении."""
        mock_api.get_user_targets.return_value = sample_targets_list

        # Первый успешен, второй провален
        mock_api.delete_targets.side_effect = [
            {"Result": [{"TargetID": "target_1", "Status": "Deleted"}]},
            {"Result": [{"TargetID": "target_2", "Status": "Failed"}]},
        ]

        result = await target_manager.delete_all_targets(game="csgo", confirm=True)

        assert result["success"] is True
        assert result["deleted_count"] == 1
        assert result["failed_count"] == 1
        assert result["total"] == 2


# ============================================================================
# Tests: Get Targets by Title
# ============================================================================


class TestGetTargetsByTitle:
    """Тесты получения таргетов по названию предмета."""

    @pytest.mark.asyncio()
    async def test_get_targets_by_title_success(self, target_manager, mock_api):
        """Тест успешного получения таргетов для предмета."""
        mock_api.get_targets_by_title.return_value = {
            "orders": [
                {
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": "800",
                    "amount": 5,
                    "attributes": {"exterior": "Field-Tested"},
                },
                {
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": "850",
                    "amount": 3,
                    "attributes": {},
                },
            ]
        }

        targets = await target_manager.get_targets_by_title(
            game="csgo", title="AK-47 | Redline (Field-Tested)"
        )

        assert len(targets) == 2
        assert targets[0]["price"] == 8.00
        assert targets[0]["amount"] == 5
        assert targets[1]["price"] == 8.50
        assert targets[1]["amount"] == 3

        # Проверка вызова API
        mock_api.get_targets_by_title.assert_called_once()
        call_args = mock_api.get_targets_by_title.call_args
        assert call_args.kwargs["game_id"] == "a8db"
        assert call_args.kwargs["title"] == "AK-47 | Redline (Field-Tested)"

    @pytest.mark.asyncio()
    async def test_get_targets_by_title_empty_result(self, target_manager, mock_api):
        """Тест получения пустого списка таргетов для предмета."""
        mock_api.get_targets_by_title.return_value = {"orders": []}

        targets = await target_manager.get_targets_by_title(game="csgo", title="Rare Item")

        assert len(targets) == 0

    @pytest.mark.asyncio()
    async def test_get_targets_by_title_api_error(self, target_manager, mock_api):
        """Тест обработки ошибки API."""
        mock_api.get_targets_by_title.side_effect = Exception("API Error")

        targets = await target_manager.get_targets_by_title(game="csgo", title="Test Item")

        assert len(targets) == 0


# ============================================================================
# Tests: Create Smart Targets
# ============================================================================


class TestCreateSmartTargets:
    """Тесты автоматического создания умных таргетов."""

    @pytest.mark.asyncio()
    async def test_create_smart_targets_success(
        self, target_manager, mock_api, sample_market_items, sample_api_response
    ):
        """Тест успешного создания умных таргетов."""
        mock_api.get_market_items.return_value = sample_market_items
        mock_api.create_targets.return_value = sample_api_response

        items = [{"title": "AK-47 | Redline (Field-Tested)"}]

        results = await target_manager.create_smart_targets(
            game="csgo", items=items, price_reduction_percent=5.0
        )

        assert len(results) == 1
        assert results[0]["success"] is True

        # Проверка расчета цены (рыночная $10.00, снижение 5% = $9.50)
        call_args = mock_api.create_targets.call_args
        targets_data = call_args.kwargs["targets"]
        created_price = targets_data[0]["Price"]["Amount"] / 100
        assert 9.0 <= created_price <= 10.0  # $9.50 ±0.50

    @pytest.mark.asyncio()
    async def test_create_smart_targets_multiple_items(
        self, target_manager, mock_api, sample_market_items, sample_api_response
    ):
        """Тест создания умных таргетов для нескольких предметов."""
        mock_api.get_market_items.return_value = sample_market_items
        mock_api.create_targets.return_value = sample_api_response

        items = [
            {"title": "AK-47 | Redline (Field-Tested)"},
            {"title": "AWP | Asiimov (Field-Tested)"},
        ]

        results = await target_manager.create_smart_targets(
            game="csgo", items=items, price_reduction_percent=10.0
        )

        assert len(results) == 2

    @pytest.mark.asyncio()
    async def test_create_smart_targets_max_limit(
        self, target_manager, mock_api, sample_market_items, sample_api_response
    ):
        """Тест ограничения максимального количества таргетов."""
        mock_api.get_market_items.return_value = sample_market_items
        mock_api.create_targets.return_value = sample_api_response

        items = [{"title": f"Item {i}"} for i in range(20)]

        results = await target_manager.create_smart_targets(game="csgo", items=items, max_targets=5)

        assert len(results) == 5

    @pytest.mark.asyncio()
    async def test_create_smart_targets_item_not_found(self, target_manager, mock_api):
        """Тест обработки отсутствия предмета на маркете."""
        mock_api.get_market_items.return_value = {"objects": []}

        items = [{"title": "Nonexistent Item"}]

        results = await target_manager.create_smart_targets(game="csgo", items=items)

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "не найден на маркете" in results[0]["error"].lower()

    @pytest.mark.asyncio()
    async def test_create_smart_targets_minimum_price(
        self, target_manager, mock_api, sample_api_response
    ):
        """Тест минимальной цены таргета ($0.10)."""
        # Маркет с очень дешевым предметом
        mock_api.get_market_items.return_value = {
            "objects": [{"itemId": "item_1", "price": {"USD": "5"}}]  # $0.05
        }
        mock_api.create_targets.return_value = sample_api_response

        items = [{"title": "Cheap Item"}]

        results = await target_manager.create_smart_targets(
            game="csgo", items=items, price_reduction_percent=50.0
        )

        # Цена должна быть не менее $0.10
        call_args = mock_api.create_targets.call_args
        targets_data = call_args.kwargs["targets"]
        created_price = targets_data[0]["Price"]["Amount"] / 100
        assert created_price >= 0.10

    @pytest.mark.asyncio()
    async def test_create_smart_targets_with_attributes(
        self, target_manager, mock_api, sample_market_items, sample_api_response
    ):
        """Тест создания умных таргетов с атрибутами."""
        mock_api.get_market_items.return_value = sample_market_items
        mock_api.create_targets.return_value = sample_api_response

        items = [
            {
                "title": "Karambit | Doppler (Factory New)",
                "amount": 2,
                "attrs": {"phase": "Phase 2"},
            }
        ]

        results = await target_manager.create_smart_targets(game="csgo", items=items)

        # Проверка передачи атрибутов
        call_args = mock_api.create_targets.call_args
        targets_data = call_args.kwargs["targets"]
        assert targets_data[0]["Amount"] == 2
        assert targets_data[0]["Attrs"]["phase"] == "Phase 2"

    @pytest.mark.asyncio()
    async def test_create_smart_targets_skip_invalid_items(self, target_manager, mock_api):
        """Тест пропуска предметов без названия."""
        items = [{"title": "Valid Item"}, {"price": 10.0}, {"title": ""}]

        mock_api.get_market_items.return_value = {"objects": []}

        results = await target_manager.create_smart_targets(game="csgo", items=items)

        # Должен обработать только 1 валидный предмет
        assert len(results) == 1


# ============================================================================
# Tests: Get Closed Targets
# ============================================================================


class TestGetClosedTargets:
    """Тесты получения истории закрытых таргетов."""

    @pytest.mark.asyncio()
    async def test_get_closed_targets_success(
        self, target_manager, mock_api, sample_closed_targets
    ):
        """Тест успешного получения закрытых таргетов."""
        mock_api.get_closed_targets.return_value = sample_closed_targets

        targets = await target_manager.get_closed_targets(limit=50, days=7)

        assert len(targets) == 2
        assert targets[0]["target_id"] == "target_old_1"
        assert targets[0]["title"] == "M4A4 | Howl (Field-Tested)"
        assert targets[0]["price"] == 1500.00
        assert targets[0]["status"] == "successful"

        # Проверка вызова API
        mock_api.get_closed_targets.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_closed_targets_with_status_filter(self, target_manager, mock_api):
        """Тест фильтрации по статусу."""
        mock_api.get_closed_targets.return_value = {"Trades": []}

        await target_manager.get_closed_targets(limit=20, status="successful", days=30)

        call_args = mock_api.get_closed_targets.call_args
        assert call_args.kwargs["status"] == "successful"
        assert call_args.kwargs["limit"] == 20

    @pytest.mark.asyncio()
    async def test_get_closed_targets_empty_result(self, target_manager, mock_api):
        """Тест получения пустой истории."""
        mock_api.get_closed_targets.return_value = {"Trades": []}

        targets = await target_manager.get_closed_targets()

        assert len(targets) == 0

    @pytest.mark.asyncio()
    async def test_get_closed_targets_api_error(self, target_manager, mock_api):
        """Тест обработки ошибки API."""
        mock_api.get_closed_targets.side_effect = Exception("API Error")

        targets = await target_manager.get_closed_targets()

        assert len(targets) == 0


# ============================================================================
# Tests: Get Target Statistics
# ============================================================================


class TestGetTargetStatistics:
    """Тесты получения статистики по таргетам."""

    @pytest.mark.asyncio()
    async def test_get_target_statistics_success(
        self, target_manager, mock_api, sample_targets_list, sample_closed_targets
    ):
        """Тест успешного получения статистики."""
        mock_api.get_user_targets.return_value = sample_targets_list
        mock_api.get_closed_targets.return_value = sample_closed_targets

        stats = await target_manager.get_target_statistics(game="csgo", days=7)

        assert stats["game"] == "csgo"
        assert stats["period_days"] == 7
        assert stats["active_count"] == 2
        assert stats["closed_count"] == 2
        assert stats["successful_count"] == 2
        assert stats["success_rate"] == 100.0
        assert stats["average_price"] == 3250.00  # (1500 + 5000) / 2
        assert stats["total_spent"] == 6500.00

    @pytest.mark.asyncio()
    async def test_get_target_statistics_no_closed_targets(
        self, target_manager, mock_api, sample_targets_list
    ):
        """Тест статистики без закрытых таргетов."""
        mock_api.get_user_targets.return_value = sample_targets_list
        mock_api.get_closed_targets.return_value = {"Trades": []}

        stats = await target_manager.get_target_statistics(game="csgo")

        assert stats["active_count"] == 2
        assert stats["closed_count"] == 0
        assert stats["successful_count"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["average_price"] == 0.0
        assert stats["total_spent"] == 0.0

    @pytest.mark.asyncio()
    async def test_get_target_statistics_partial_success(
        self, target_manager, mock_api, sample_targets_list
    ):
        """Тест статистики с частичным успехом."""
        mock_api.get_user_targets.return_value = sample_targets_list
        mock_api.get_closed_targets.return_value = {
            "Trades": [
                {
                    "TargetID": "t1",
                    "Title": "Item 1",
                    "Price": {"Amount": 100000},
                    "Status": "successful",
                    "ClosedAt": 1699000000,
                    "CreatedAt": 1699000000,
                },
                {
                    "TargetID": "t2",
                    "Title": "Item 2",
                    "Price": {"Amount": 50000},
                    "Status": "reverted",
                    "ClosedAt": 1699000000,
                    "CreatedAt": 1699000000,
                },
            ],
            "Total": "2",
        }

        stats = await target_manager.get_target_statistics(game="csgo")

        assert stats["closed_count"] == 2
        assert stats["successful_count"] == 1
        assert stats["success_rate"] == 50.0
        assert stats["average_price"] == 1000.00


# ============================================================================
# Tests: Integration
# ============================================================================


class TestTargetManagerIntegration:
    """Интеграционные тесты TargetManager."""

    @pytest.mark.asyncio()
    async def test_full_target_workflow(
        self,
        target_manager,
        mock_api,
        sample_api_response,
        sample_targets_list,
        sample_closed_targets,
    ):
        """Тест полного workflow работы с таргетами."""
        # 1. Создание таргета
        mock_api.create_targets.return_value = sample_api_response
        create_result = await target_manager.create_target(
            game="csgo",
            title="AK-47 | Redline (Field-Tested)",
            price=8.50,
        )
        assert create_result["success"] is True

        # 2. Получение списка таргетов
        mock_api.get_user_targets.return_value = sample_targets_list
        targets = await target_manager.get_user_targets(game="csgo")
        assert len(targets) == 2

        # 3. Получение статистики
        mock_api.get_closed_targets.return_value = sample_closed_targets
        stats = await target_manager.get_target_statistics(game="csgo")
        assert stats["active_count"] == 2

        # 4. Удаление таргета
        mock_api.delete_targets.return_value = {
            "Result": [{"TargetID": "target_1", "Status": "Deleted"}]
        }
        delete_success = await target_manager.delete_target("target_1")
        assert delete_success is True

    @pytest.mark.asyncio()
    async def test_smart_targets_workflow(
        self, target_manager, mock_api, sample_market_items, sample_api_response
    ):
        """Тест workflow создания умных таргетов."""
        mock_api.get_market_items.return_value = sample_market_items
        mock_api.create_targets.return_value = sample_api_response

        items = [
            {"title": "AK-47 | Redline (Field-Tested)"},
            {"title": "AWP | Asiimov (Field-Tested)"},
        ]

        results = await target_manager.create_smart_targets(
            game="csgo",
            items=items,
            price_reduction_percent=5.0,
        )

        assert len(results) == 2
        assert all(r["success"] for r in results)


# ============================================================================
# Tests: Edge Cases
# ============================================================================


class TestTargetManagerEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio()
    async def test_concurrent_target_creation(self, target_manager, mock_api, sample_api_response):
        """Тест одновременного создания нескольких таргетов."""
        mock_api.create_targets.return_value = sample_api_response

        tasks = [
            target_manager.create_target(game="csgo", title=f"Item {i}", price=10.0 + i)
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio()
    async def test_extremely_high_price(self, target_manager, mock_api, sample_api_response):
        """Тест создания таргета с очень высокой ценой."""
        mock_api.create_targets.return_value = sample_api_response

        result = await target_manager.create_target(
            game="csgo",
            title="Rare Item",
            price=99999.99,
        )

        assert result["success"] is True

        # Проверка конвертации в центы
        call_args = mock_api.create_targets.call_args
        targets_data = call_args.kwargs["targets"]
        assert targets_data[0]["Price"]["Amount"] == 9999999

    @pytest.mark.asyncio()
    async def test_extremely_low_price(self, target_manager, mock_api, sample_api_response):
        """Тест создания таргета с очень низкой ценой."""
        mock_api.create_targets.return_value = sample_api_response

        result = await target_manager.create_target(
            game="csgo",
            title="Cheap Item",
            price=0.01,
        )

        assert result["success"] is True

        # Проверка конвертации в центы
        call_args = mock_api.create_targets.call_args
        targets_data = call_args.kwargs["targets"]
        assert targets_data[0]["Price"]["Amount"] == 1

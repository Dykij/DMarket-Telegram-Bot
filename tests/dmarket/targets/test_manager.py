"""Tests for targets/manager.py module.

This module provides comprehensive tests for:
- TargetManager class initialization and methods
- create_target tests
- get_user_targets tests
- delete_target and delete_all_targets tests
- get_targets_by_title tests
- create_smart_targets tests
- get_closed_targets tests
- get_target_statistics tests
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.targets.manager import TargetManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api():
    """Create a mock DMarket API client."""
    api = MagicMock()
    api.create_target = AsyncMock(return_value={"id": "target_123", "status": "active"})
    api.get_user_targets = AsyncMock(return_value={"items": []})
    api.delete_target = AsyncMock()
    api.get_targets_by_title = AsyncMock(return_value={"items": []})
    api.get_closed_targets = AsyncMock(return_value={"trades": []})
    api.get_aggregated_prices_bulk = AsyncMock()
    api.get_buy_orders_competition = AsyncMock()
    return api


@pytest.fixture
def manager(mock_api):
    """Create a TargetManager with mock API."""
    return TargetManager(api_client=mock_api, enable_liquidity_filter=False)


@pytest.fixture
def manager_with_liquidity(mock_api):
    """Create a TargetManager with liquidity filter enabled."""
    return TargetManager(api_client=mock_api, enable_liquidity_filter=True)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestTargetManagerInitialization:
    """Test TargetManager initialization."""

    def test_init_with_api_client(self, mock_api):
        """Test initialization with API client."""
        manager = TargetManager(api_client=mock_api)
        assert manager.api is mock_api

    def test_init_liquidity_filter_disabled(self, mock_api):
        """Test initialization with liquidity filter disabled."""
        manager = TargetManager(api_client=mock_api, enable_liquidity_filter=False)
        assert manager.enable_liquidity_filter is False
        assert manager.liquidity_analyzer is None

    def test_init_liquidity_filter_enabled(self, mock_api):
        """Test initialization with liquidity filter enabled."""
        manager = TargetManager(api_client=mock_api, enable_liquidity_filter=True)
        assert manager.enable_liquidity_filter is True
        assert manager.liquidity_analyzer is not None


# ============================================================================
# create_target Tests
# ============================================================================


class TestCreateTarget:
    """Test create_target method."""

    @pytest.mark.asyncio
    async def test_create_target_success(self, manager, mock_api):
        """Test successful target creation."""
        result = await manager.create_target(
            game="csgo",
            title="AK-47 | Redline (Field-Tested)",
            price=10.50,
            amount=1,
        )

        mock_api.create_target.assert_called_once()
        call_args = mock_api.create_target.call_args[0][0]
        assert call_args["gameId"] == "a8db"  # csgo -> a8db
        assert call_args["title"] == "AK-47 | Redline (Field-Tested)"
        assert call_args["price"] == "1050"  # USD to cents
        assert call_args["amount"] == "1"

    @pytest.mark.asyncio
    async def test_create_target_with_attrs(self, manager, mock_api):
        """Test target creation with attributes."""
        attrs = {"floatPartValue": "0.25", "paintSeed": "100"}
        result = await manager.create_target(
            game="csgo",
            title="AK-47 | Redline (Field-Tested)",
            price=10.50,
            amount=1,
            attrs=attrs,
        )

        call_args = mock_api.create_target.call_args[0][0]
        assert call_args["attrs"] == attrs

    @pytest.mark.asyncio
    async def test_create_target_empty_title_raises(self, manager):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Название предмета не может быть пустым"):
            await manager.create_target(
                game="csgo",
                title="",
                price=10.00,
            )

    @pytest.mark.asyncio
    async def test_create_target_whitespace_title_raises(self, manager):
        """Test that whitespace-only title raises ValueError."""
        with pytest.raises(ValueError, match="Название предмета не может быть пустым"):
            await manager.create_target(
                game="csgo",
                title="   ",
                price=10.00,
            )

    @pytest.mark.asyncio
    async def test_create_target_zero_price_raises(self, manager):
        """Test that zero price raises ValueError."""
        with pytest.raises(ValueError, match="Цена должна быть больше 0"):
            await manager.create_target(
                game="csgo",
                title="Test Item",
                price=0,
            )

    @pytest.mark.asyncio
    async def test_create_target_negative_price_raises(self, manager):
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="Цена должна быть больше 0"):
            await manager.create_target(
                game="csgo",
                title="Test Item",
                price=-5.00,
            )

    @pytest.mark.asyncio
    async def test_create_target_amount_below_1_raises(self, manager):
        """Test that amount below 1 raises ValueError."""
        with pytest.raises(ValueError, match="Количество должно быть от 1 до 100"):
            await manager.create_target(
                game="csgo",
                title="Test Item",
                price=10.00,
                amount=0,
            )

    @pytest.mark.asyncio
    async def test_create_target_amount_above_100_raises(self, manager):
        """Test that amount above 100 raises ValueError."""
        with pytest.raises(ValueError, match="Количество должно быть от 1 до 100"):
            await manager.create_target(
                game="csgo",
                title="Test Item",
                price=10.00,
                amount=101,
            )

    @pytest.mark.asyncio
    async def test_create_target_extracts_phase_from_title(self, manager, mock_api):
        """Test that phase is extracted from doppler title."""
        await manager.create_target(
            game="csgo",
            title="Karambit | Doppler (Factory New) Phase 2",
            price=500.00,
        )

        call_args = mock_api.create_target.call_args[0][0]
        assert "attrs" in call_args
        assert call_args["attrs"].get("phase") == "Phase 2"

    @pytest.mark.asyncio
    async def test_create_target_dota2_game(self, manager, mock_api):
        """Test target creation for Dota 2."""
        await manager.create_target(
            game="dota2",
            title="Dragonclaw Hook",
            price=100.00,
        )

        call_args = mock_api.create_target.call_args[0][0]
        assert call_args["gameId"] == "9a92"

    @pytest.mark.asyncio
    async def test_create_target_api_error(self, manager, mock_api):
        """Test handling of API errors."""
        mock_api.create_target.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await manager.create_target(
                game="csgo",
                title="Test Item",
                price=10.00,
            )


# ============================================================================
# get_user_targets Tests
# ============================================================================


class TestGetUserTargets:
    """Test get_user_targets method."""

    @pytest.mark.asyncio
    async def test_get_user_targets_default(self, manager, mock_api):
        """Test getting user targets with defaults."""
        mock_api.get_user_targets.return_value = {
            "items": [{"id": "target_1"}, {"id": "target_2"}]
        }

        result = await manager.get_user_targets()

        assert len(result) == 2
        mock_api.get_user_targets.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_targets_with_game_filter(self, manager, mock_api):
        """Test getting targets filtered by game."""
        mock_api.get_user_targets.return_value = {"items": []}

        await manager.get_user_targets(game="csgo")

        call_args = mock_api.get_user_targets.call_args[0][0]
        assert call_args["gameId"] == "a8db"

    @pytest.mark.asyncio
    async def test_get_user_targets_with_status(self, manager, mock_api):
        """Test getting targets with status filter."""
        mock_api.get_user_targets.return_value = {"items": []}

        await manager.get_user_targets(status="inactive")

        call_args = mock_api.get_user_targets.call_args[0][0]
        assert call_args["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_get_user_targets_all_status(self, manager, mock_api):
        """Test getting all targets regardless of status."""
        mock_api.get_user_targets.return_value = {"items": []}

        await manager.get_user_targets(status="all")

        call_args = mock_api.get_user_targets.call_args[0][0]
        assert "status" not in call_args

    @pytest.mark.asyncio
    async def test_get_user_targets_pagination(self, manager, mock_api):
        """Test pagination parameters."""
        mock_api.get_user_targets.return_value = {"items": []}

        await manager.get_user_targets(limit=50, offset=10)

        call_args = mock_api.get_user_targets.call_args[0][0]
        assert call_args["limit"] == 50
        assert call_args["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_user_targets_api_error_returns_empty(self, manager, mock_api):
        """Test that API errors return empty list."""
        mock_api.get_user_targets.side_effect = Exception("API Error")

        result = await manager.get_user_targets()

        assert result == []


# ============================================================================
# delete_target Tests
# ============================================================================


class TestDeleteTarget:
    """Test delete_target method."""

    @pytest.mark.asyncio
    async def test_delete_target_success(self, manager, mock_api):
        """Test successful target deletion."""
        result = await manager.delete_target("target_123")

        assert result is True
        mock_api.delete_target.assert_called_once_with("target_123")

    @pytest.mark.asyncio
    async def test_delete_target_failure(self, manager, mock_api):
        """Test failed target deletion."""
        mock_api.delete_target.side_effect = Exception("Not found")

        result = await manager.delete_target("invalid_id")

        assert result is False


# ============================================================================
# delete_all_targets Tests
# ============================================================================


class TestDeleteAllTargets:
    """Test delete_all_targets method."""

    @pytest.mark.asyncio
    async def test_delete_all_dry_run(self, manager, mock_api):
        """Test dry run mode returns what would be deleted."""
        mock_api.get_user_targets.return_value = {
            "items": [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}]
        }

        result = await manager.delete_all_targets(dry_run=True)

        assert result["dry_run"] is True
        assert result["would_delete"] == 3
        mock_api.delete_target.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_all_execute(self, manager, mock_api):
        """Test actual deletion of all targets."""
        mock_api.get_user_targets.return_value = {
            "items": [{"id": "t1"}, {"id": "t2"}]
        }

        result = await manager.delete_all_targets(dry_run=False)

        assert result["deleted"] == 2
        assert result["failed"] == 0
        assert result["total"] == 2
        assert mock_api.delete_target.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_all_with_game_filter(self, manager, mock_api):
        """Test deletion filtered by game."""
        mock_api.get_user_targets.return_value = {"items": []}

        await manager.delete_all_targets(game="csgo", dry_run=True)

        # Verify game filter was applied
        mock_api.get_user_targets.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all_partial_failure(self, manager, mock_api):
        """Test handling of partial failures."""
        mock_api.get_user_targets.return_value = {
            "items": [{"id": "t1"}, {"id": "t2"}]
        }
        mock_api.delete_target.side_effect = [None, Exception("Error")]

        result = await manager.delete_all_targets(dry_run=False)

        assert result["deleted"] == 1
        assert result["failed"] == 1


# ============================================================================
# get_targets_by_title Tests
# ============================================================================


class TestGetTargetsByTitle:
    """Test get_targets_by_title method."""

    @pytest.mark.asyncio
    async def test_get_targets_by_title_success(self, manager, mock_api):
        """Test getting targets by title."""
        mock_api.get_targets_by_title.return_value = {
            "items": [{"id": "t1", "price": "1000"}]
        }

        result = await manager.get_targets_by_title(
            game="csgo", title="AK-47 | Redline"
        )

        assert len(result) == 1
        mock_api.get_targets_by_title.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_targets_by_title_empty(self, manager, mock_api):
        """Test getting targets when none exist."""
        mock_api.get_targets_by_title.return_value = {"items": []}

        result = await manager.get_targets_by_title(
            game="csgo", title="Nonexistent Item"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_targets_by_title_api_error(self, manager, mock_api):
        """Test handling of API errors."""
        mock_api.get_targets_by_title.side_effect = Exception("Error")

        result = await manager.get_targets_by_title(game="csgo", title="Test")

        assert result == []


# ============================================================================
# create_smart_targets Tests
# ============================================================================


class TestCreateSmartTargets:
    """Test create_smart_targets method."""

    @pytest.mark.asyncio
    async def test_create_smart_targets_success(self, manager, mock_api):
        """Test successful smart target creation."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 1,
            "total_amount": 2,
            "competition_level": "low",
            "best_price": 8.0,
            "average_price": 7.5,
        }

        items = [
            {"title": "AK-47 | Redline", "price": 15.0},
        ]

        with patch.object(manager, "_delay", new_callable=AsyncMock):
            result = await manager.create_smart_targets(
                game="csgo",
                items=items,
                profit_margin=0.15,
                max_targets=5,
            )

        assert len(result) == 1
        assert result[0]["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_smart_targets_skip_high_competition(self, manager, mock_api):
        """Test skipping items with high competition."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 10,
            "total_amount": 50,
            "competition_level": "high",
            "best_price": 10.0,
            "average_price": 9.0,
        }

        items = [{"title": "High Comp Item", "price": 15.0}]

        result = await manager.create_smart_targets(
            game="csgo",
            items=items,
            check_competition=True,
        )

        assert len(result) == 1
        assert result[0]["status"] == "skipped"
        assert result[0]["reason"] == "high_competition"

    @pytest.mark.asyncio
    async def test_create_smart_targets_without_competition_check(
        self, manager, mock_api
    ):
        """Test creating targets without competition check."""
        items = [{"title": "Test Item", "price": 15.0}]

        with patch.object(manager, "_delay", new_callable=AsyncMock):
            result = await manager.create_smart_targets(
                game="csgo",
                items=items,
                check_competition=False,
            )

        assert len(result) == 1
        mock_api.get_buy_orders_competition.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_smart_targets_skip_invalid_items(self, manager, mock_api):
        """Test skipping items without title or price."""
        items = [
            {"title": "", "price": 15.0},  # Empty title
            {"title": "Valid", "price": 0},  # Zero price
            {"price": 10.0},  # Missing title
        ]

        result = await manager.create_smart_targets(
            game="csgo",
            items=items,
            check_competition=False,
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_create_smart_targets_max_targets_limit(self, manager, mock_api):
        """Test max_targets parameter limits creation."""
        items = [{"title": f"Item {i}", "price": 10.0} for i in range(10)]

        with patch.object(manager, "_delay", new_callable=AsyncMock):
            result = await manager.create_smart_targets(
                game="csgo",
                items=items,
                max_targets=3,
                check_competition=False,
            )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_create_smart_targets_api_error(self, manager, mock_api):
        """Test handling of API errors during creation."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 0,
            "total_amount": 0,
            "competition_level": "low",
            "best_price": 0.0,
            "average_price": 0.0,
        }
        mock_api.create_target.side_effect = Exception("API Error")

        items = [{"title": "Test Item", "price": 15.0}]

        result = await manager.create_smart_targets(
            game="csgo",
            items=items,
            check_competition=True,
        )

        assert result[0]["status"] == "error"
        assert "error" in result[0]


# ============================================================================
# get_closed_targets Tests
# ============================================================================


class TestGetClosedTargets:
    """Test get_closed_targets method."""

    @pytest.mark.asyncio
    async def test_get_closed_targets_success(self, manager, mock_api):
        """Test getting closed targets."""
        mock_api.get_closed_targets.return_value = {
            "trades": [
                {
                    "TargetID": "t1",
                    "Title": "AK-47 | Redline",
                    "Price": 1000,
                    "GameID": "a8db",
                    "Status": "successful",
                    "ClosedAt": "2024-01-01T00:00:00Z",
                    "CreatedAt": "2024-01-01T00:00:00Z",
                }
            ]
        }

        result = await manager.get_closed_targets(limit=50, days=7)

        assert len(result) == 1
        assert result[0]["title"] == "AK-47 | Redline"
        assert result[0]["price"] == 10.0  # 1000 cents -> $10

    @pytest.mark.asyncio
    async def test_get_closed_targets_empty(self, manager, mock_api):
        """Test getting closed targets when none exist."""
        mock_api.get_closed_targets.return_value = {"trades": []}

        result = await manager.get_closed_targets()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_closed_targets_time_range(self, manager, mock_api):
        """Test time range calculation for closed targets."""
        mock_api.get_closed_targets.return_value = {"trades": []}

        await manager.get_closed_targets(days=30)

        call_kwargs = mock_api.get_closed_targets.call_args.kwargs
        assert "start_time" in call_kwargs
        assert "end_time" in call_kwargs
        # end_time should be close to now
        assert call_kwargs["end_time"] <= int(time.time()) + 10

    @pytest.mark.asyncio
    async def test_get_closed_targets_api_error(self, manager, mock_api):
        """Test handling of API errors."""
        mock_api.get_closed_targets.side_effect = Exception("Error")

        result = await manager.get_closed_targets()

        assert result == []


# ============================================================================
# get_target_statistics Tests
# ============================================================================


class TestGetTargetStatistics:
    """Test get_target_statistics method."""

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, manager, mock_api):
        """Test getting target statistics."""
        mock_api.get_user_targets.return_value = {
            "items": [{"id": "t1"}, {"id": "t2"}]
        }
        mock_api.get_closed_targets.return_value = {
            "trades": [
                {"TargetID": "t3", "Status": "successful", "Price": 1000},
                {"TargetID": "t4", "Status": "successful", "Price": 2000},
                {"TargetID": "t5", "Status": "cancelled", "Price": 500},
            ]
        }

        result = await manager.get_target_statistics(game="csgo", days=7)

        assert result["game"] == "csgo"
        assert result["active_count"] == 2
        assert result["closed_count"] == 3
        assert result["successful_count"] == 2
        # 2 out of 3 = 66.67%
        assert result["success_rate"] == pytest.approx(66.67, rel=0.1)

    @pytest.mark.asyncio
    async def test_get_statistics_no_closed_targets(self, manager, mock_api):
        """Test statistics when no closed targets exist."""
        mock_api.get_user_targets.return_value = {"items": []}
        mock_api.get_closed_targets.return_value = {"trades": []}

        result = await manager.get_target_statistics(game="csgo")

        assert result["closed_count"] == 0
        assert result["success_rate"] == 0.0


# ============================================================================
# analyze_target_competition Tests
# ============================================================================


class TestAnalyzeTargetCompetition:
    """Test analyze_target_competition delegation."""

    @pytest.mark.asyncio
    async def test_analyze_delegates_to_competition_module(self, manager, mock_api):
        """Test that analysis delegates to competition module."""
        mock_api.get_targets_by_title.return_value = []
        mock_api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [{"offerBestPrice": 1000}]
        }

        result = await manager.analyze_target_competition(
            game="csgo", title="Test Item"
        )

        assert "title" in result
        assert "game" in result


# ============================================================================
# assess_competition Tests
# ============================================================================


class TestAssessCompetition:
    """Test assess_competition delegation."""

    @pytest.mark.asyncio
    async def test_assess_delegates_to_competition_module(self, manager, mock_api):
        """Test that assessment delegates to competition module."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 2,
            "total_amount": 5,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 9.5,
        }

        result = await manager.assess_competition(
            game="csgo",
            title="Test Item",
            max_competition=5,
        )

        assert "should_proceed" in result


# ============================================================================
# filter_low_competition_items Tests
# ============================================================================


class TestFilterLowCompetitionItems:
    """Test filter_low_competition_items delegation."""

    @pytest.mark.asyncio
    async def test_filter_delegates_to_competition_module(self, manager, mock_api):
        """Test that filtering delegates to competition module."""
        mock_api.get_buy_orders_competition.return_value = {
            "total_orders": 1,
            "total_amount": 2,
            "competition_level": "low",
            "best_price": 10.0,
            "average_price": 10.0,
        }

        items = [{"title": "Test Item", "price": 15.0}]

        result = await manager.filter_low_competition_items(
            game="csgo",
            items=items,
            max_competition=5,
            request_delay=0,
        )

        assert len(result) == 1


# ============================================================================
# _delay Tests
# ============================================================================


class TestDelay:
    """Test _delay method."""

    @pytest.mark.asyncio
    async def test_delay_method(self, manager):
        """Test that delay method works."""
        import asyncio
        import time

        start = time.time()
        await manager._delay(0.1)
        elapsed = time.time() - start

        assert elapsed >= 0.1

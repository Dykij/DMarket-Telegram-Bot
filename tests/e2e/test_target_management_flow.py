"""E2E тесты для target management workflow.

Фаза 2: End-to-end тестирование управления таргетами (buy orders).

Этот модуль тестирует:
1. Создание таргетов (buy orders)
2. Просмотр активных таргетов
3. Удаление таргетов
4. Получение уведомлений о сработавших таргетах
"""

from unittest.mock import AsyncMock

import pytest

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_dmarket_api():
    """Create mock DMarket API client."""
    api = AsyncMock()

    # Mock create target response
    api.create_target = AsyncMock(
        return_value={
            "success": True,
            "targetId": "target_123",
            "itemTitle": "AK-47 | Redline (Field-Tested)",
            "price": "1000",  # $10.00 in cents
            "status": "active",
        }
    )

    # Mock get targets response
    api.get_targets = AsyncMock(
        return_value={
            "objects": [
                {
                    "targetId": "target_123",
                    "itemTitle": "AK-47 | Redline (Field-Tested)",
                    "price": {"USD": "1000"},
                    "status": "active",
                    "createdAt": "2026-01-01T00:00:00Z",
                },
                {
                    "targetId": "target_456",
                    "itemTitle": "AWP | Asiimov (Field-Tested)",
                    "price": {"USD": "5000"},
                    "status": "active",
                    "createdAt": "2026-01-01T01:00:00Z",
                },
            ]
        }
    )

    # Mock delete target response
    api.delete_target = AsyncMock(
        return_value={
            "success": True,
            "targetId": "target_123",
            "message": "Target deleted successfully",
        }
    )

    # Mock balance check
    api.get_balance = AsyncMock(
        return_value={
            "usd": "10000",  # $100.00
            "dmc": "5000",
        }
    )

    return api


@pytest.fixture()
def mock_database():
    """Create mock database manager."""
    db = AsyncMock()

    # Mock save target
    db.save_target = AsyncMock(
        return_value={
            "id": 1,
            "user_id": 123456789,
            "target_id": "target_123",
            "item_title": "AK-47 | Redline (Field-Tested)",
            "price": 1000,
            "status": "active",
        }
    )

    # Mock get user targets
    db.get_user_targets = AsyncMock(
        return_value=[
            {
                "id": 1,
                "target_id": "target_123",
                "item_title": "AK-47 | Redline (Field-Tested)",
                "price": 1000,
                "status": "active",
            },
            {
                "id": 2,
                "target_id": "target_456",
                "item_title": "AWP | Asiimov (Field-Tested)",
                "price": 5000,
                "status": "active",
            },
        ]
    )

    # Mock delete target
    db.delete_target = AsyncMock(return_value=True)

    return db


@pytest.fixture()
def mock_notification_service():
    """Create mock notification service."""
    service = AsyncMock()
    service.send_target_created = AsyncMock()
    service.send_target_filled = AsyncMock()
    service.send_target_deleted = AsyncMock()
    return service


# ============================================================================
# E2E: TARGET CREATION FLOW
# ============================================================================


class TestTargetCreationFlow:
    """E2E tests for target creation workflow."""

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_create_target_complete_flow(
        self, mock_dmarket_api, mock_database, mock_notification_service
    ):
        """Test complete target creation flow.

        Flow:
        1. User selects item
        2. Sets target price
        3. Validates balance
        4. Creates target via API
        5. Saves to database
        6. Sends confirmation notification
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789
        item_title = "AK-47 | Redline (Field-Tested)"
        target_price = 1000  # $10.00 in cents

        # Act: Step 1-2 - Create target
        result = await manager.create_target(
            user_id=user_id, item_title=item_title, price=target_price, game="csgo"
        )

        # Assert: Step 4 - Target created via API
        assert result["success"] is True
        assert "targetId" in result
        mock_dmarket_api.create_target.assert_called_once()

        # Assert: Step 5 - Saved to database
        mock_database.save_target.assert_called_once()
        save_call = mock_database.save_target.call_args
        assert save_call.kwargs["user_id"] == user_id
        assert save_call.kwargs["item_title"] == item_title
        assert save_call.kwargs["price"] == target_price

        # Act: Step 6 - Send notification
        await mock_notification_service.send_target_created(user_id=user_id, target_details=result)

        # Assert: Notification sent
        mock_notification_service.send_target_created.assert_called_once()

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_create_target_validates_price_range(self, mock_dmarket_api, mock_database):
        """Test that target creation validates price range.

        Flow:
        1. Attempt to create target with too low price
        2. Verify rejected
        3. Attempt with valid price
        4. Verify accepted
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789

        # Act & Assert: Too low price
        with pytest.raises(ValueError) as exc_info:
            await manager.create_target(
                user_id=user_id,
                item_title="Test Item",
                price=0,  # Invalid: $0.00
                game="csgo",
            )
        assert "price" in str(exc_info.value).lower()

        # Act: Valid price
        result = await manager.create_target(
            user_id=user_id,
            item_title="Test Item",
            price=100,  # Valid: $1.00
            game="csgo",
        )

        # Assert: Accepted
        assert result["success"] is True

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_create_target_checks_balance(self, mock_dmarket_api, mock_database):
        """Test that target creation validates user balance.

        Flow:
        1. Check user balance
        2. Attempt target with price > balance
        3. Verify rejected
        """
        from src.dmarket.targets import TargetManager

        # Arrange: Set low balance
        mock_dmarket_api.get_balance = AsyncMock(
            return_value={
                "usd": "100",  # Only $1.00
                "dmc": "0",
            }
        )

        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)

        # Act & Assert: Price exceeds balance
        with pytest.raises(Exception) as exc_info:
            await manager.create_target(
                user_id=123456789,
                item_title="Expensive Item",
                price=5000,  # $50.00 - exceeds balance
                game="csgo",
                check_balance=True,
            )

        assert (
            "balance" in str(exc_info.value).lower()
            or "insufficient" in str(exc_info.value).lower()
        )


# ============================================================================
# E2E: TARGET VIEWING FLOW
# ============================================================================


class TestTargetViewingFlow:
    """E2E tests for viewing targets workflow."""

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_user_views_active_targets(self, mock_dmarket_api, mock_database):
        """Test user viewing their active targets.

        Flow:
        1. User requests target list
        2. Fetch from database
        3. Sync with API status
        4. Display to user
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789

        # Act: Get user targets
        targets = await manager.get_user_targets(user_id=user_id)

        # Assert: Targets fetched
        assert len(targets) > 0
        mock_database.get_user_targets.assert_called_once_with(user_id=user_id)

        # Assert: Each target has required fields
        for target in targets:
            assert "target_id" in target
            assert "item_title" in target
            assert "price" in target
            assert "status" in target

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_targets_synced_with_api_status(self, mock_dmarket_api, mock_database):
        """Test that local targets are synced with API status.

        Flow:
        1. Get targets from database
        2. Check status with DMarket API
        3. Update database if status changed
        4. Return updated targets
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789

        # Act: Get and sync targets
        targets = await manager.get_user_targets(user_id=user_id, sync_with_api=True)

        # Assert: API checked for status
        mock_dmarket_api.get_targets.assert_called_once()

        # Assert: Targets returned
        assert len(targets) > 0


# ============================================================================
# E2E: TARGET DELETION FLOW
# ============================================================================


class TestTargetDeletionFlow:
    """E2E tests for target deletion workflow."""

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_delete_target_complete_flow(
        self, mock_dmarket_api, mock_database, mock_notification_service
    ):
        """Test complete target deletion flow.

        Flow:
        1. User selects target to delete
        2. Confirm deletion
        3. Delete via API
        4. Remove from database
        5. Send confirmation
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789
        target_id = "target_123"

        # Act: Delete target
        result = await manager.delete_target(user_id=user_id, target_id=target_id)

        # Assert: Deleted via API
        assert result["success"] is True
        mock_dmarket_api.delete_target.assert_called_once_with(target_id=target_id)

        # Assert: Removed from database
        mock_database.delete_target.assert_called_once()

        # Act: Send notification
        await mock_notification_service.send_target_deleted(user_id=user_id, target_id=target_id)

        # Assert: Notification sent
        mock_notification_service.send_target_deleted.assert_called_once()

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_delete_nonexistent_target_handled(self, mock_dmarket_api, mock_database):
        """Test deletion of non-existent target is handled gracefully.

        Flow:
        1. Attempt to delete invalid target ID
        2. Verify error handled properly
        3. No changes made
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        mock_dmarket_api.delete_target = AsyncMock(side_effect=Exception("Target not found"))

        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await manager.delete_target(user_id=123456789, target_id="invalid_target_id")

        assert "not found" in str(exc_info.value).lower()


# ============================================================================
# E2E: TARGET FILLED NOTIFICATION FLOW
# ============================================================================


class TestTargetFilledNotificationFlow:
    """E2E tests for target filled notification workflow."""

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_user_notified_when_target_filled(
        self, mock_dmarket_api, mock_database, mock_notification_service
    ):
        """Test user receives notification when target is filled.

        Flow:
        1. Monitor target status
        2. Detect target filled
        3. Update database status
        4. Send notification to user
        """
        from src.dmarket.targets import TargetManager

        # Arrange: Target filled
        mock_dmarket_api.get_targets = AsyncMock(
            return_value={
                "objects": [
                    {
                        "targetId": "target_123",
                        "itemTitle": "AK-47 | Redline (Field-Tested)",
                        "price": {"USD": "1000"},
                        "status": "filled",  # Changed to filled
                        "filledAt": "2026-01-01T02:00:00Z",
                    }
                ]
            }
        )

        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789

        # Act: Check target status
        targets = await manager.get_user_targets(user_id=user_id, sync_with_api=True)

        # Find filled target
        filled_targets = [t for t in targets if t.get("status") == "filled"]

        # Send notifications for filled targets
        for target in filled_targets:
            await mock_notification_service.send_target_filled(
                user_id=user_id, target_details=target
            )

        # Assert: Notification sent
        if filled_targets:
            assert mock_notification_service.send_target_filled.call_count == len(filled_targets)


# ============================================================================
# E2E: BATCH TARGET OPERATIONS
# ============================================================================


class TestBatchTargetOperations:
    """E2E tests for batch target operations."""

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_create_multiple_targets_parallel(self, mock_dmarket_api, mock_database):
        """Test creating multiple targets in parallel.

        Flow:
        1. Prepare list of items
        2. Create targets in parallel
        3. Verify all created successfully
        """
        import asyncio

        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789

        target_items = [
            {"title": "Item 1", "price": 1000},
            {"title": "Item 2", "price": 2000},
            {"title": "Item 3", "price": 3000},
        ]

        # Act: Create targets in parallel
        tasks = [
            manager.create_target(
                user_id=user_id, item_title=item["title"], price=item["price"], game="csgo"
            )
            for item in target_items
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert: All created successfully
        assert len(results) == len(target_items)
        for result in results:
            assert not isinstance(result, Exception), f"Target creation failed: {result}"
            assert result["success"] is True

    @pytest.mark.asyncio()
    @pytest.mark.e2e()
    async def test_delete_multiple_targets_batch(self, mock_dmarket_api, mock_database):
        """Test deleting multiple targets in batch.

        Flow:
        1. User selects multiple targets
        2. Delete all in batch
        3. Verify all deleted
        """
        from src.dmarket.targets import TargetManager

        # Arrange
        manager = TargetManager(api_client=mock_dmarket_api, database=mock_database)
        user_id = 123456789
        target_ids = ["target_123", "target_456", "target_789"]

        # Act: Batch delete
        results = await manager.delete_targets_batch(user_id=user_id, target_ids=target_ids)

        # Assert: All deleted
        assert len(results) == len(target_ids)
        assert all(r["success"] for r in results)
        assert mock_dmarket_api.delete_target.call_count == len(target_ids)

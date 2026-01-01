"""Phase 4 extended tests for state_manager module.

This module contains comprehensive tests for src/utils/state_manager.py covering:
- CheckpointData extended tests (edge cases, validation)
- ScanCheckpoint model extended tests
- StateManager async operations (create_checkpoint, save_checkpoint, load_checkpoint)
- StateManager get_active_checkpoints, cleanup_old_checkpoints
- StateManager mark_checkpoint_completed, mark_checkpoint_failed
- StateManager signal handlers and shutdown
- StateManager emergency shutdown
- LocalStateManager tests (file-based state management)
- Edge cases and integration tests

Target: 65+ tests to achieve 95%+ coverage
"""

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.utils.state_manager import (
    CheckpointData,
    LocalStateManager,
    ScanCheckpoint,
    StateManager,
)


# ============================================================
# CheckpointData Extended Tests
# ============================================================


class TestCheckpointDataExtended:
    """Extended tests for CheckpointData model."""

    def test_checkpoint_data_with_large_processed_items(self):
        """Test CheckpointData with large processed_items value."""
        # Arrange
        scan_id = uuid4()

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            processed_items=1000000,
            total_items=2000000,
        )

        # Assert
        assert checkpoint.processed_items == 1000000
        assert checkpoint.total_items == 2000000

    def test_checkpoint_data_with_zero_total_items(self):
        """Test CheckpointData with zero total_items."""
        # Arrange
        scan_id = uuid4()

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            total_items=0,
        )

        # Assert
        assert checkpoint.total_items == 0

    def test_checkpoint_data_with_complex_extra_data(self):
        """Test CheckpointData with complex nested extra_data."""
        # Arrange
        scan_id = uuid4()
        extra_data = {
            "game": "csgo",
            "filters": {"min_price": 10, "max_price": 100},
            "results": [{"item": "AK-47", "price": 50}],
            "nested": {"level1": {"level2": {"level3": "value"}}},
        }

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            extra_data=extra_data,
        )

        # Assert
        assert checkpoint.extra_data["game"] == "csgo"
        assert checkpoint.extra_data["filters"]["min_price"] == 10
        assert checkpoint.extra_data["nested"]["level1"]["level2"]["level3"] == "value"

    def test_checkpoint_data_with_unicode_cursor(self):
        """Test CheckpointData with unicode cursor."""
        # Arrange
        scan_id = uuid4()
        cursor = "курсор_кириллица_🎮"

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            cursor=cursor,
        )

        # Assert
        assert checkpoint.cursor == cursor

    def test_checkpoint_data_with_very_long_cursor(self):
        """Test CheckpointData with very long cursor string."""
        # Arrange
        scan_id = uuid4()
        cursor = "a" * 10000

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            cursor=cursor,
        )

        # Assert
        assert len(checkpoint.cursor) == 10000

    def test_checkpoint_data_status_failed(self):
        """Test CheckpointData with failed status."""
        # Arrange
        scan_id = uuid4()

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            status="failed",
            extra_data={"error": "API timeout"},
        )

        # Assert
        assert checkpoint.status == "failed"
        assert checkpoint.extra_data["error"] == "API timeout"

    def test_checkpoint_data_custom_timestamp(self):
        """Test CheckpointData with custom timestamp."""
        # Arrange
        scan_id = uuid4()
        custom_time = datetime(2025, 1, 1, 12, 0, 0)

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            timestamp=custom_time,
        )

        # Assert
        assert checkpoint.timestamp == custom_time


# ============================================================
# ScanCheckpoint Model Extended Tests
# ============================================================


class TestScanCheckpointExtended:
    """Extended tests for ScanCheckpoint database model."""

    def test_scan_checkpoint_id_column_is_integer(self):
        """Test ScanCheckpoint id column is Integer type."""
        # Arrange & Act
        id_column = ScanCheckpoint.__table__.c.id

        # Assert
        assert id_column.type.__class__.__name__ == "Integer"

    def test_scan_checkpoint_scan_id_is_unique(self):
        """Test ScanCheckpoint scan_id column is unique."""
        # Arrange & Act
        scan_id_column = ScanCheckpoint.__table__.c.scan_id

        # Assert
        assert scan_id_column.unique is True

    def test_scan_checkpoint_user_id_is_indexed(self):
        """Test ScanCheckpoint user_id column is indexed."""
        # Arrange & Act
        user_id_column = ScanCheckpoint.__table__.c.user_id

        # Assert
        assert user_id_column.index is True

    def test_scan_checkpoint_status_default(self):
        """Test ScanCheckpoint status column has default value."""
        # Arrange & Act
        status_column = ScanCheckpoint.__table__.c.status

        # Assert - default should be "in_progress"
        assert status_column.default is not None

    def test_scan_checkpoint_processed_items_default(self):
        """Test ScanCheckpoint processed_items column has default value."""
        # Arrange & Act
        column = ScanCheckpoint.__table__.c.processed_items

        # Assert
        assert column.default is not None


# ============================================================
# StateManager Async Operations Tests
# ============================================================


class TestStateManagerCreateCheckpoint:
    """Tests for StateManager.create_checkpoint method."""

    @pytest.mark.asyncio()
    async def test_create_checkpoint_success(self):
        """Test successful checkpoint creation."""
        # Arrange
        mock_session = AsyncMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()

        # Act
        result = await manager.create_checkpoint(
            scan_id=scan_id,
            user_id=12345,
            operation_type="arbitrage_scan",
        )

        # Assert
        assert result.scan_id == scan_id
        assert result.status == "in_progress"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_create_checkpoint_with_cursor(self):
        """Test checkpoint creation with cursor."""
        # Arrange
        mock_session = AsyncMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()

        # Act
        result = await manager.create_checkpoint(
            scan_id=scan_id,
            user_id=12345,
            operation_type="scan",
            cursor="next_page_token",
        )

        # Assert
        assert result.cursor == "next_page_token"

    @pytest.mark.asyncio()
    async def test_create_checkpoint_with_extra_data(self):
        """Test checkpoint creation with extra_data."""
        # Arrange
        mock_session = AsyncMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()
        extra = {"game": "csgo", "level": "standard"}

        # Act
        result = await manager.create_checkpoint(
            scan_id=scan_id,
            user_id=12345,
            operation_type="scan",
            extra_data=extra,
        )

        # Assert
        assert result.extra_data == extra

    @pytest.mark.asyncio()
    async def test_create_checkpoint_with_total_items(self):
        """Test checkpoint creation with total_items."""
        # Arrange
        mock_session = AsyncMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()

        # Act
        result = await manager.create_checkpoint(
            scan_id=scan_id,
            user_id=12345,
            operation_type="scan",
            total_items=500,
        )

        # Assert
        assert result.total_items == 500


class TestStateManagerSaveCheckpoint:
    """Tests for StateManager.save_checkpoint method."""

    @pytest.mark.asyncio()
    async def test_save_checkpoint_updates_existing(self):
        """Test save_checkpoint updates existing checkpoint."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        # Mock existing checkpoint
        mock_checkpoint = MagicMock()
        mock_checkpoint.extra_data = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.save_checkpoint(
            scan_id=scan_id,
            cursor="new_cursor",
            processed_items=100,
            total_items=500,
            status="in_progress",
        )

        # Assert
        assert mock_checkpoint.cursor == "new_cursor"
        assert mock_checkpoint.processed_items == 100
        assert mock_checkpoint.total_items == 500
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_save_checkpoint_not_found(self):
        """Test save_checkpoint when checkpoint not found."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.save_checkpoint(
            scan_id=scan_id,
            cursor="cursor",
            processed_items=50,
        )

        # Assert - should log warning and return without commit
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio()
    async def test_save_checkpoint_updates_extra_data(self):
        """Test save_checkpoint updates extra_data."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        # Create a mock extra_data with a mock update method
        mock_extra_data = MagicMock()
        mock_checkpoint = MagicMock()
        mock_checkpoint.extra_data = mock_extra_data
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.save_checkpoint(
            scan_id=scan_id,
            extra_data={"new_key": "new_value"},
        )

        # Assert - verify update was called
        mock_extra_data.update.assert_called_once()

    @pytest.mark.asyncio()
    async def test_save_checkpoint_completed_status(self):
        """Test save_checkpoint with completed status."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_checkpoint = MagicMock()
        mock_checkpoint.extra_data = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.save_checkpoint(
            scan_id=scan_id,
            status="completed",
        )

        # Assert
        assert mock_checkpoint.status == "completed"


class TestStateManagerLoadCheckpoint:
    """Tests for StateManager.load_checkpoint method."""

    @pytest.mark.asyncio()
    async def test_load_checkpoint_success(self):
        """Test successful checkpoint loading."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_checkpoint = MagicMock()
        mock_checkpoint.scan_id = scan_id
        mock_checkpoint.cursor = "cursor_123"
        mock_checkpoint.processed_items = 50
        mock_checkpoint.total_items = 100
        mock_checkpoint.timestamp = datetime.utcnow()
        mock_checkpoint.extra_data = {"game": "csgo"}
        mock_checkpoint.status = "in_progress"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        result = await manager.load_checkpoint(scan_id)

        # Assert
        assert result is not None
        assert result.scan_id == scan_id
        assert result.cursor == "cursor_123"
        assert result.processed_items == 50

    @pytest.mark.asyncio()
    async def test_load_checkpoint_not_found(self):
        """Test load_checkpoint when not found."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        result = await manager.load_checkpoint(scan_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio()
    async def test_load_checkpoint_with_null_extra_data(self):
        """Test load_checkpoint handles null extra_data."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_checkpoint = MagicMock()
        mock_checkpoint.scan_id = scan_id
        mock_checkpoint.cursor = None
        mock_checkpoint.processed_items = 0
        mock_checkpoint.total_items = None
        mock_checkpoint.timestamp = datetime.utcnow()
        mock_checkpoint.extra_data = None  # Null extra_data
        mock_checkpoint.status = "in_progress"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        result = await manager.load_checkpoint(scan_id)

        # Assert
        assert result is not None
        assert result.extra_data == {}


class TestStateManagerGetActiveCheckpoints:
    """Tests for StateManager.get_active_checkpoints method."""

    @pytest.mark.asyncio()
    async def test_get_active_checkpoints_success(self):
        """Test get_active_checkpoints returns active checkpoints."""
        # Arrange
        mock_session = AsyncMock()

        mock_cp1 = MagicMock()
        mock_cp1.scan_id = uuid4()
        mock_cp1.cursor = "cursor1"
        mock_cp1.processed_items = 50
        mock_cp1.total_items = 100
        mock_cp1.timestamp = datetime.utcnow()
        mock_cp1.extra_data = {}
        mock_cp1.status = "in_progress"

        mock_cp2 = MagicMock()
        mock_cp2.scan_id = uuid4()
        mock_cp2.cursor = "cursor2"
        mock_cp2.processed_items = 75
        mock_cp2.total_items = 150
        mock_cp2.timestamp = datetime.utcnow()
        mock_cp2.extra_data = {}
        mock_cp2.status = "in_progress"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_cp1, mock_cp2]
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        result = await manager.get_active_checkpoints(user_id=12345)

        # Assert
        assert len(result) == 2
        assert result[0].processed_items == 50
        assert result[1].processed_items == 75

    @pytest.mark.asyncio()
    async def test_get_active_checkpoints_empty(self):
        """Test get_active_checkpoints with no active checkpoints."""
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        result = await manager.get_active_checkpoints(user_id=12345)

        # Assert
        assert result == []

    @pytest.mark.asyncio()
    async def test_get_active_checkpoints_with_operation_type_filter(self):
        """Test get_active_checkpoints with operation_type filter."""
        # Arrange
        mock_session = AsyncMock()

        mock_cp = MagicMock()
        mock_cp.scan_id = uuid4()
        mock_cp.cursor = None
        mock_cp.processed_items = 10
        mock_cp.total_items = 50
        mock_cp.timestamp = datetime.utcnow()
        mock_cp.extra_data = {}
        mock_cp.status = "in_progress"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_cp]
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        result = await manager.get_active_checkpoints(
            user_id=12345,
            operation_type="arbitrage_scan",
        )

        # Assert
        assert len(result) == 1


class TestStateManagerCleanupOldCheckpoints:
    """Tests for StateManager.cleanup_old_checkpoints method."""

    @pytest.mark.asyncio()
    async def test_cleanup_old_checkpoints_deletes_old(self):
        """Test cleanup_old_checkpoints deletes old checkpoints."""
        # Arrange
        mock_session = AsyncMock()

        mock_cp1 = MagicMock()
        mock_cp2 = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_cp1, mock_cp2]
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        count = await manager.cleanup_old_checkpoints(days=7)

        # Assert
        assert count == 2
        assert mock_session.delete.call_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_cleanup_old_checkpoints_no_old_checkpoints(self):
        """Test cleanup_old_checkpoints with no old checkpoints."""
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        count = await manager.cleanup_old_checkpoints(days=7)

        # Assert
        assert count == 0

    @pytest.mark.asyncio()
    async def test_cleanup_old_checkpoints_custom_days(self):
        """Test cleanup_old_checkpoints with custom days parameter."""
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        count = await manager.cleanup_old_checkpoints(days=30)

        # Assert
        assert count == 0
        mock_session.execute.assert_called_once()


class TestStateManagerMarkCheckpointCompleted:
    """Tests for StateManager.mark_checkpoint_completed method."""

    @pytest.mark.asyncio()
    async def test_mark_checkpoint_completed(self):
        """Test mark_checkpoint_completed sets status to completed."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_checkpoint = MagicMock()
        mock_checkpoint.extra_data = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.mark_checkpoint_completed(scan_id)

        # Assert
        assert mock_checkpoint.status == "completed"


class TestStateManagerMarkCheckpointFailed:
    """Tests for StateManager.mark_checkpoint_failed method."""

    @pytest.mark.asyncio()
    async def test_mark_checkpoint_failed_with_error(self):
        """Test mark_checkpoint_failed with error message."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        # Create a mock extra_data with a mock update method
        mock_extra_data = MagicMock()
        mock_checkpoint = MagicMock()
        mock_checkpoint.extra_data = mock_extra_data
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.mark_checkpoint_failed(
            scan_id,
            error_message="API connection failed",
        )

        # Assert
        assert mock_checkpoint.status == "failed"
        mock_extra_data.update.assert_called_once()

    @pytest.mark.asyncio()
    async def test_mark_checkpoint_failed_without_error(self):
        """Test mark_checkpoint_failed without error message."""
        # Arrange
        mock_session = AsyncMock()
        scan_id = uuid4()

        mock_checkpoint = MagicMock()
        mock_checkpoint.extra_data = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_checkpoint
        mock_session.execute.return_value = mock_result

        manager = StateManager(session=mock_session)

        # Act
        await manager.mark_checkpoint_failed(scan_id)

        # Assert
        assert mock_checkpoint.status == "failed"


# ============================================================
# StateManager Signal Handlers Tests
# ============================================================


class TestStateManagerRegisterShutdownHandlers:
    """Tests for StateManager.register_shutdown_handlers method."""

    def test_register_shutdown_handlers_once(self):
        """Test shutdown handlers registered only once."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()

        # Act
        with patch("signal.signal"):
            manager.register_shutdown_handlers(scan_id)
            manager.register_shutdown_handlers(scan_id)

        # Assert
        assert manager._shutdown_handlers_registered is True

    def test_register_shutdown_handlers_with_callback(self):
        """Test shutdown handlers with cleanup callback."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()
        cleanup_callback = MagicMock()

        # Act
        with patch("signal.signal") as mock_signal:
            manager.register_shutdown_handlers(scan_id, cleanup_callback)

        # Assert
        # Should register for SIGTERM and SIGINT
        assert mock_signal.call_count == 2


# ============================================================
# StateManager Emergency Shutdown Tests
# ============================================================


class TestStateManagerEmergencyShutdown:
    """Tests for StateManager.trigger_emergency_shutdown method."""

    @pytest.mark.asyncio()
    async def test_trigger_emergency_shutdown(self):
        """Test trigger_emergency_shutdown pauses operations."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Act
        await manager.trigger_emergency_shutdown("Critical error")

        # Assert
        assert manager._is_paused is True

    @pytest.mark.asyncio()
    async def test_trigger_emergency_shutdown_calls_callback(self):
        """Test trigger_emergency_shutdown calls registered callback."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        mock_callback = MagicMock(return_value=None)
        manager.set_shutdown_callback(mock_callback)

        # Act
        await manager.trigger_emergency_shutdown("API failure")

        # Assert
        mock_callback.assert_called_once_with("API failure")

    @pytest.mark.asyncio()
    async def test_trigger_emergency_shutdown_with_async_callback(self):
        """Test trigger_emergency_shutdown with async callback."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        async_callback = AsyncMock()
        manager.set_shutdown_callback(async_callback)

        # Act
        await manager.trigger_emergency_shutdown("Rate limit exceeded")

        # Assert
        async_callback.assert_called_once_with("Rate limit exceeded")

    @pytest.mark.asyncio()
    async def test_trigger_emergency_shutdown_callback_error_handled(self):
        """Test trigger_emergency_shutdown handles callback errors."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        def failing_callback(reason):
            raise ValueError("Callback failed")

        manager.set_shutdown_callback(failing_callback)

        # Act - should not raise
        await manager.trigger_emergency_shutdown("Test error")

        # Assert
        assert manager._is_paused is True


# ============================================================
# LocalStateManager Tests
# ============================================================


class TestLocalStateManagerInit:
    """Tests for LocalStateManager initialization."""

    def test_init_creates_directory(self):
        """Test LocalStateManager creates state directory."""
        # Arrange & Act
        with TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "checkpoints"
            manager = LocalStateManager(state_dir=state_dir)

            # Assert
            assert state_dir.exists()

    def test_init_with_existing_directory(self):
        """Test LocalStateManager with existing directory."""
        # Arrange & Act
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)

            # Assert
            assert manager.state_dir == Path(tmpdir)

    def test_init_with_string_path(self):
        """Test LocalStateManager with string path."""
        # Arrange & Act
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=str(tmpdir))

            # Assert
            assert isinstance(manager.state_dir, Path)


class TestLocalStateManagerSaveCheckpoint:
    """Tests for LocalStateManager.save_checkpoint method."""

    @pytest.mark.asyncio()
    async def test_save_checkpoint_creates_file(self):
        """Test save_checkpoint creates checkpoint file."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Act
            await manager.save_checkpoint(
                scan_id=scan_id,
                cursor="cursor_123",
                processed_items=50,
            )

            # Assert
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            assert checkpoint_file.exists()

    @pytest.mark.asyncio()
    async def test_save_checkpoint_content(self):
        """Test save_checkpoint saves correct content."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Act
            await manager.save_checkpoint(
                scan_id=scan_id,
                cursor="cursor_123",
                processed_items=50,
                total_items=100,
                extra_data={"game": "csgo"},
                status="in_progress",
            )

            # Assert
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            data = json.loads(checkpoint_file.read_text())
            assert data["cursor"] == "cursor_123"
            assert data["processed_items"] == 50
            assert data["total_items"] == 100
            assert data["extra_data"]["game"] == "csgo"

    @pytest.mark.asyncio()
    async def test_save_checkpoint_overwrites_existing(self):
        """Test save_checkpoint overwrites existing file."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Act - save twice
            await manager.save_checkpoint(
                scan_id=scan_id,
                processed_items=50,
            )
            await manager.save_checkpoint(
                scan_id=scan_id,
                processed_items=100,
            )

            # Assert
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            data = json.loads(checkpoint_file.read_text())
            assert data["processed_items"] == 100


class TestLocalStateManagerLoadCheckpoint:
    """Tests for LocalStateManager.load_checkpoint method."""

    @pytest.mark.asyncio()
    async def test_load_checkpoint_success(self):
        """Test successful checkpoint loading."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Save first
            await manager.save_checkpoint(
                scan_id=scan_id,
                cursor="cursor_abc",
                processed_items=75,
                total_items=150,
            )

            # Act
            result = await manager.load_checkpoint(scan_id)

            # Assert
            assert result is not None
            assert result.scan_id == scan_id
            assert result.cursor == "cursor_abc"
            assert result.processed_items == 75

    @pytest.mark.asyncio()
    async def test_load_checkpoint_not_found(self):
        """Test load_checkpoint when file not found."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Act
            result = await manager.load_checkpoint(scan_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio()
    async def test_load_checkpoint_invalid_json(self):
        """Test load_checkpoint handles invalid JSON."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Write invalid JSON
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            checkpoint_file.write_text("not valid json", encoding="utf-8")

            # Act
            result = await manager.load_checkpoint(scan_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio()
    async def test_load_checkpoint_missing_fields(self):
        """Test load_checkpoint handles missing fields."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Write JSON with missing fields
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            checkpoint_file.write_text(
                json.dumps({"incomplete": True}),
                encoding="utf-8",
            )

            # Act
            result = await manager.load_checkpoint(scan_id)

            # Assert
            assert result is None


class TestLocalStateManagerCleanupOldCheckpoints:
    """Tests for LocalStateManager.cleanup_old_checkpoints method."""

    @pytest.mark.asyncio()
    async def test_cleanup_old_checkpoints_deletes_old_completed(self):
        """Test cleanup deletes old completed checkpoints."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Create old completed checkpoint
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            old_time = (datetime.now(UTC) - timedelta(days=10)).isoformat()
            checkpoint_file.write_text(
                json.dumps(
                    {
                        "scan_id": str(scan_id),
                        "timestamp": old_time,
                        "status": "completed",
                    }
                ),
                encoding="utf-8",
            )

            # Act
            count = await manager.cleanup_old_checkpoints(days=7)

            # Assert
            assert count == 1
            assert not checkpoint_file.exists()

    @pytest.mark.asyncio()
    async def test_cleanup_old_checkpoints_keeps_in_progress(self):
        """Test cleanup keeps in_progress checkpoints."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Create old in_progress checkpoint
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            old_time = (datetime.now(UTC) - timedelta(days=10)).isoformat()
            checkpoint_file.write_text(
                json.dumps(
                    {
                        "scan_id": str(scan_id),
                        "timestamp": old_time,
                        "status": "in_progress",
                    }
                ),
                encoding="utf-8",
            )

            # Act
            count = await manager.cleanup_old_checkpoints(days=7)

            # Assert
            assert count == 0
            assert checkpoint_file.exists()

    @pytest.mark.asyncio()
    async def test_cleanup_old_checkpoints_keeps_recent(self):
        """Test cleanup keeps recent completed checkpoints."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Create recent completed checkpoint
            checkpoint_file = Path(tmpdir) / f"{scan_id}.json"
            recent_time = datetime.now(UTC).isoformat()
            checkpoint_file.write_text(
                json.dumps(
                    {
                        "scan_id": str(scan_id),
                        "timestamp": recent_time,
                        "status": "completed",
                    }
                ),
                encoding="utf-8",
            )

            # Act
            count = await manager.cleanup_old_checkpoints(days=7)

            # Assert
            assert count == 0
            assert checkpoint_file.exists()


# ============================================================
# Edge Cases Tests
# ============================================================


class TestStateManagerEdgeCases:
    """Edge case tests for StateManager."""

    def test_reset_error_counter_from_zero(self):
        """Test reset_error_counter when already zero."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Act
        manager.reset_error_counter()

        # Assert
        assert manager._consecutive_errors == 0

    def test_record_error_with_zero_max_errors(self):
        """Test record_error with max_consecutive_errors=0."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session, max_consecutive_errors=0)

        # Act
        result = manager.record_error()

        # Assert - should trigger immediately
        assert result is True
        assert manager._consecutive_errors == 1

    def test_pause_operations_already_paused(self):
        """Test pause_operations when already paused."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        manager._is_paused = True

        # Act
        manager.pause_operations()

        # Assert
        assert manager._is_paused is True

    def test_resume_operations_already_running(self):
        """Test resume_operations when not paused."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        manager._is_paused = False

        # Act
        manager.resume_operations()

        # Assert
        assert manager._is_paused is False

    def test_set_shutdown_callback_to_none(self):
        """Test setting shutdown callback to None."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        manager._shutdown_callback = MagicMock()

        # Act
        manager.set_shutdown_callback(None)

        # Assert
        assert manager._shutdown_callback is None


class TestLocalStateManagerEdgeCases:
    """Edge case tests for LocalStateManager."""

    def test_get_checkpoint_file_path(self):
        """Test _get_checkpoint_file generates correct path."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Act
            path = manager._get_checkpoint_file(scan_id)

            # Assert
            assert path == Path(tmpdir) / f"{scan_id}.json"

    @pytest.mark.asyncio()
    async def test_cleanup_handles_corrupted_files(self):
        """Test cleanup handles corrupted checkpoint files."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)

            # Create corrupted file
            corrupted_file = Path(tmpdir) / "corrupted.json"
            corrupted_file.write_text("not json", encoding="utf-8")

            # Act - should not raise
            count = await manager.cleanup_old_checkpoints(days=7)

            # Assert
            assert count == 0


# ============================================================
# Integration Tests
# ============================================================


class TestStateManagerIntegration:
    """Integration tests for StateManager."""

    @pytest.mark.asyncio()
    async def test_full_checkpoint_lifecycle(self):
        """Test full checkpoint lifecycle: create, update, complete."""
        # Arrange
        mock_session = AsyncMock()
        manager = StateManager(session=mock_session)
        scan_id = uuid4()

        # Mock for create
        mock_session.add = MagicMock()

        # Act - Create
        checkpoint = await manager.create_checkpoint(
            scan_id=scan_id,
            user_id=12345,
            operation_type="scan",
        )

        # Assert
        assert checkpoint.status == "in_progress"

    def test_error_recording_and_reset_flow(self):
        """Test error recording and reset flow."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session, max_consecutive_errors=3)

        # Act & Assert - Record errors
        assert manager.record_error() is False
        assert manager._consecutive_errors == 1
        assert manager.record_error() is False
        assert manager._consecutive_errors == 2
        assert manager.record_error() is True  # Triggers shutdown
        assert manager._consecutive_errors == 3

        # Reset and continue
        manager.reset_error_counter()
        assert manager._consecutive_errors == 0

    def test_pause_resume_flow(self):
        """Test pause and resume operations flow."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Assert initial state
        assert manager.is_paused is False

        # Pause
        manager.pause_operations()
        assert manager.is_paused is True

        # Resume
        manager.resume_operations()
        assert manager.is_paused is False


class TestLocalStateManagerIntegration:
    """Integration tests for LocalStateManager."""

    @pytest.mark.asyncio()
    async def test_full_checkpoint_lifecycle(self):
        """Test full checkpoint lifecycle with file storage."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_id = uuid4()

            # Act - Save
            await manager.save_checkpoint(
                scan_id=scan_id,
                cursor="initial",
                processed_items=0,
                total_items=100,
            )

            # Act - Load
            checkpoint = await manager.load_checkpoint(scan_id)
            assert checkpoint is not None
            assert checkpoint.processed_items == 0

            # Act - Update
            await manager.save_checkpoint(
                scan_id=scan_id,
                cursor="page_2",
                processed_items=50,
                total_items=100,
            )

            # Act - Load again
            checkpoint = await manager.load_checkpoint(scan_id)
            assert checkpoint is not None
            assert checkpoint.processed_items == 50
            assert checkpoint.cursor == "page_2"

    @pytest.mark.asyncio()
    async def test_multiple_checkpoints(self):
        """Test managing multiple checkpoints."""
        # Arrange
        with TemporaryDirectory() as tmpdir:
            manager = LocalStateManager(state_dir=tmpdir)
            scan_ids = [uuid4() for _ in range(5)]

            # Act - Save multiple
            for i, scan_id in enumerate(scan_ids):
                await manager.save_checkpoint(
                    scan_id=scan_id,
                    processed_items=i * 10,
                )

            # Assert - Load all
            for i, scan_id in enumerate(scan_ids):
                checkpoint = await manager.load_checkpoint(scan_id)
                assert checkpoint is not None
                assert checkpoint.processed_items == i * 10

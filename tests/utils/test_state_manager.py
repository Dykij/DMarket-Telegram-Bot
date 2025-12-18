"""Unit tests for state manager module.

This module contains tests for src/utils/state_manager.py covering:
- CheckpointData model
- StateManager initialization
- Properties and basic functionality

Target: 15+ tests to achieve 70%+ coverage
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.utils.state_manager import CheckpointData, StateManager


# TestCheckpointData


class TestCheckpointData:
    """Tests for CheckpointData model."""

    def test_checkpoint_data_defaults(self):
        """Test CheckpointData with default values."""
        # Arrange
        scan_id = uuid4()

        # Act
        checkpoint = CheckpointData(scan_id=scan_id)

        # Assert
        assert checkpoint.scan_id == scan_id
        assert checkpoint.cursor is None
        assert checkpoint.processed_items == 0
        assert checkpoint.total_items is None
        assert checkpoint.status == "in_progress"
        assert checkpoint.extra_data == {}

    def test_checkpoint_data_with_values(self):
        """Test CheckpointData with custom values."""
        # Arrange
        scan_id = uuid4()

        # Act
        checkpoint = CheckpointData(
            scan_id=scan_id,
            cursor="cursor_abc",
            processed_items=50,
            total_items=100,
            extra_data={"game": "csgo"},
            status="completed",
        )

        # Assert
        assert checkpoint.cursor == "cursor_abc"
        assert checkpoint.processed_items == 50
        assert checkpoint.total_items == 100
        assert checkpoint.extra_data == {"game": "csgo"}
        assert checkpoint.status == "completed"

    def test_checkpoint_data_timestamp(self):
        """Test that timestamp is set automatically."""
        # Arrange
        scan_id = uuid4()
        before = datetime.utcnow()

        # Act
        checkpoint = CheckpointData(scan_id=scan_id)

        # Assert
        assert checkpoint.timestamp >= before


# TestStateManagerInit


class TestStateManagerInit:
    """Tests for StateManager initialization."""

    def test_init_with_defaults(self):
        """Test StateManager initialization with default values."""
        # Arrange
        mock_session = MagicMock()

        # Act
        manager = StateManager(session=mock_session)

        # Assert
        assert manager.session == mock_session
        assert manager.checkpoint_interval == 100
        assert manager.max_consecutive_errors == 5
        assert manager._consecutive_errors == 0
        assert manager._is_paused is False

    def test_init_with_custom_values(self):
        """Test StateManager initialization with custom values."""
        # Arrange
        mock_session = MagicMock()

        # Act
        manager = StateManager(
            session=mock_session,
            checkpoint_interval=50,
            max_consecutive_errors=3,
        )

        # Assert
        assert manager.checkpoint_interval == 50
        assert manager.max_consecutive_errors == 3


# TestStateManagerProperties


class TestStateManagerProperties:
    """Tests for StateManager properties."""

    def test_consecutive_errors_property(self):
        """Test consecutive_errors property."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Assert - initial value
        assert manager.consecutive_errors == 0

    def test_is_paused_property(self):
        """Test is_paused property."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Assert - initial value
        assert manager.is_paused is False


# TestStateManagerMethods


class TestStateManagerMethods:
    """Tests for StateManager methods."""

    def test_pause_operations_method(self):
        """Test pause_operations method."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Act
        manager.pause_operations()

        # Assert
        assert manager._is_paused is True

    def test_resume_operations_method(self):
        """Test resume_operations method."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        manager._is_paused = True
        manager._consecutive_errors = 3

        # Act
        manager.resume_operations()

        # Assert
        assert manager._is_paused is False
        assert manager._consecutive_errors == 0

    def test_record_error_increments_counter(self):
        """Test that record_error increments counter."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Act
        result = manager.record_error()

        # Assert
        assert manager._consecutive_errors == 1
        assert result is False  # Should not trigger shutdown yet

    def test_record_error_multiple_times(self):
        """Test recording multiple errors."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session, max_consecutive_errors=5)

        # Act
        for _ in range(3):
            manager.record_error()

        # Assert
        assert manager._consecutive_errors == 3

    def test_reset_error_counter(self):
        """Test that reset_error_counter resets counter."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        manager._consecutive_errors = 3

        # Act
        manager.reset_error_counter()

        # Assert
        assert manager._consecutive_errors == 0

    def test_record_error_returns_false_below_threshold(self):
        """Test record_error returns False below threshold."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session, max_consecutive_errors=5)
        manager._consecutive_errors = 2

        # Act
        result = manager.record_error()

        # Assert
        assert result is False

    def test_record_error_returns_true_at_threshold(self):
        """Test record_error returns True at threshold."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session, max_consecutive_errors=5)
        manager._consecutive_errors = 4

        # Act
        result = manager.record_error()

        # Assert
        assert result is True

    def test_record_error_returns_true_above_threshold(self):
        """Test record_error returns True above threshold."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session, max_consecutive_errors=5)
        manager._consecutive_errors = 10

        # Act
        result = manager.record_error()

        # Assert
        assert result is True


# TestStateManagerCallbacks


class TestStateManagerCallbacks:
    """Tests for StateManager callback functionality."""

    def test_set_shutdown_callback(self):
        """Test setting shutdown callback."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)
        callback = MagicMock()

        # Act
        manager.set_shutdown_callback(callback)

        # Assert
        assert manager._shutdown_callback == callback

    def test_shutdown_callback_none_by_default(self):
        """Test that shutdown callback is None by default."""
        # Arrange
        mock_session = MagicMock()
        manager = StateManager(session=mock_session)

        # Assert
        assert manager._shutdown_callback is None

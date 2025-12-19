"""Tests for state_manager module.

This module tests the StateManager class and CheckpointData model
for managing operation state and checkpoints.
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.utils.state_manager import (
    CheckpointData,
    ScanCheckpoint,
    StateManagerBase,
)


class TestCheckpointData:
    """Tests for CheckpointData model."""

    def test_create_checkpoint_data_minimal(self):
        """Test creating CheckpointData with minimal fields."""
        scan_id = uuid4()
        
        checkpoint = CheckpointData(scan_id=scan_id)
        
        assert checkpoint.scan_id == scan_id
        assert checkpoint.cursor is None
        assert checkpoint.processed_items == 0
        assert checkpoint.total_items is None
        assert checkpoint.status == "in_progress"

    def test_create_checkpoint_data_full(self):
        """Test creating CheckpointData with all fields."""
        scan_id = uuid4()
        timestamp = datetime.utcnow()
        
        checkpoint = CheckpointData(
            scan_id=scan_id,
            cursor="next_page_token",
            processed_items=50,
            total_items=100,
            timestamp=timestamp,
            extra_data={"key": "value"},
            status="completed",
        )
        
        assert checkpoint.scan_id == scan_id
        assert checkpoint.cursor == "next_page_token"
        assert checkpoint.processed_items == 50
        assert checkpoint.total_items == 100
        assert checkpoint.timestamp == timestamp
        assert checkpoint.extra_data == {"key": "value"}
        assert checkpoint.status == "completed"

    def test_checkpoint_data_default_timestamp(self):
        """Test CheckpointData has default timestamp."""
        checkpoint = CheckpointData(scan_id=uuid4())
        
        assert checkpoint.timestamp is not None
        assert isinstance(checkpoint.timestamp, datetime)

    def test_checkpoint_data_default_extra_data(self):
        """Test CheckpointData has default empty extra_data."""
        checkpoint = CheckpointData(scan_id=uuid4())
        
        assert checkpoint.extra_data == {}

    def test_checkpoint_data_with_various_statuses(self):
        """Test CheckpointData with different status values."""
        statuses = ["in_progress", "completed", "failed"]
        
        for status in statuses:
            checkpoint = CheckpointData(scan_id=uuid4(), status=status)
            assert checkpoint.status == status


class TestScanCheckpoint:
    """Tests for ScanCheckpoint database model."""

    def test_scan_checkpoint_tablename(self):
        """Test ScanCheckpoint table name."""
        assert ScanCheckpoint.__tablename__ == "scan_checkpoints"

    def test_scan_checkpoint_columns(self):
        """Test ScanCheckpoint has required columns."""
        columns = [col.name for col in ScanCheckpoint.__table__.columns]
        
        assert "id" in columns
        assert "scan_id" in columns
        assert "user_id" in columns
        assert "operation_type" in columns
        assert "cursor" in columns
        assert "processed_items" in columns
        assert "total_items" in columns
        assert "timestamp" in columns
        assert "extra_data" in columns
        assert "status" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_scan_checkpoint_primary_key(self):
        """Test ScanCheckpoint has id as primary key."""
        pk_columns = [col.name for col in ScanCheckpoint.__table__.primary_key.columns]
        
        assert "id" in pk_columns


class TestStateManagerBase:
    """Tests for StateManagerBase declarative base."""

    def test_state_manager_base_is_declarative(self):
        """Test StateManagerBase is a declarative base."""
        # Should be a valid declarative base class
        assert hasattr(StateManagerBase, "metadata")


class TestCheckpointDataSerialization:
    """Tests for CheckpointData serialization."""

    def test_checkpoint_data_to_dict(self):
        """Test CheckpointData can be converted to dict."""
        scan_id = uuid4()
        checkpoint = CheckpointData(
            scan_id=scan_id,
            processed_items=10,
        )
        
        data = checkpoint.model_dump()
        
        assert data["scan_id"] == scan_id
        assert data["processed_items"] == 10

    def test_checkpoint_data_json_serialization(self):
        """Test CheckpointData can be serialized to JSON."""
        scan_id = uuid4()
        checkpoint = CheckpointData(
            scan_id=scan_id,
            processed_items=10,
        )
        
        json_str = checkpoint.model_dump_json()
        
        assert str(scan_id) in json_str
        assert "10" in json_str


class TestCheckpointDataValidation:
    """Tests for CheckpointData validation."""

    def test_checkpoint_data_requires_scan_id(self):
        """Test CheckpointData requires scan_id."""
        with pytest.raises(Exception):  # ValidationError
            CheckpointData()  # type: ignore

    def test_checkpoint_data_validates_uuid(self):
        """Test CheckpointData validates scan_id as UUID."""
        scan_id = uuid4()
        checkpoint = CheckpointData(scan_id=scan_id)
        
        assert isinstance(checkpoint.scan_id, UUID)

    def test_checkpoint_data_processed_items_default(self):
        """Test CheckpointData processed_items defaults to 0."""
        checkpoint = CheckpointData(scan_id=uuid4())
        
        assert checkpoint.processed_items == 0

    def test_checkpoint_data_accepts_string_uuid(self):
        """Test CheckpointData accepts string UUID."""
        scan_id = str(uuid4())
        checkpoint = CheckpointData(scan_id=scan_id)  # type: ignore
        
        # Should convert to UUID
        assert isinstance(checkpoint.scan_id, UUID)

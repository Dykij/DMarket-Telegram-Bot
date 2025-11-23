"""State management for long-running operations.

This module provides checkpoint and state persistence functionality
for long-running operations like market scans, ensuring recovery
after crashes or restarts without losing progress.
"""

import asyncio
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import signal
import sys
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import Base
from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


class CheckpointData(BaseModel):
    """Checkpoint data model."""

    scan_id: UUID
    cursor: str | None = None
    processed_items: int = 0
    total_items: int | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = "in_progress"  # in_progress, completed, failed


class ScanCheckpoint(Base):
    """Database model for scan checkpoints."""

    __tablename__ = "scan_checkpoints"

    id = Column(Integer, primary_key=True)
    scan_id = Column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)  # scan, arbitrage, etc.
    cursor = Column(Text, nullable=True)
    processed_items = Column(Integer, default=0)
    total_items = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, default={})
    status = Column(String(20), default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class StateManager:
    """Manager for operation state and checkpoints."""

    def __init__(
        self,
        session: AsyncSession,
        checkpoint_interval: int = 100,
        max_consecutive_errors: int = 5,
    ):
        """Initialize state manager.

        Args:
            session: Database session
            checkpoint_interval: Save checkpoint every N items
            max_consecutive_errors: Max consecutive errors before shutdown

        """
        self.session = session
        self.checkpoint_interval = checkpoint_interval
        self.max_consecutive_errors = max_consecutive_errors
        self._shutdown_handlers_registered = False
        self._consecutive_errors = 0
        self._is_paused = False
        self._shutdown_callback: callable | None = None

    async def create_checkpoint(
        self,
        scan_id: UUID,
        user_id: int,
        operation_type: str,
        **kwargs: Any,
    ) -> CheckpointData:
        """Create a new checkpoint.

        Args:
            scan_id: Unique scan identifier
            user_id: User ID
            operation_type: Type of operation (scan, arbitrage, etc.)
            **kwargs: Additional metadata

        Returns:
            CheckpointData: Created checkpoint

        """
        checkpoint = ScanCheckpoint(
            scan_id=scan_id,
            user_id=user_id,
            operation_type=operation_type,
            cursor=kwargs.get("cursor"),
            processed_items=kwargs.get("processed_items", 0),
            total_items=kwargs.get("total_items"),
            metadata=kwargs.get("metadata", {}),
            status="in_progress",
        )

        self.session.add(checkpoint)
        await self.session.commit()

        logger.info(
            "Checkpoint created",
            scan_id=str(scan_id),
            user_id=user_id,
            operation_type=operation_type,
        )

        return CheckpointData(
            scan_id=scan_id,
            cursor=kwargs.get("cursor"),
            processed_items=kwargs.get("processed_items", 0),
            total_items=kwargs.get("total_items"),
            metadata=kwargs.get("metadata", {}),
        )

    async def save_checkpoint(
        self,
        scan_id: UUID,
        cursor: str | None = None,
        processed_items: int = 0,
        total_items: int | None = None,
        metadata: dict[str, Any] | None = None,
        status: str = "in_progress",
    ) -> None:
        """Save or update checkpoint.

        Args:
            scan_id: Scan identifier
            cursor: Current cursor position
            processed_items: Number of processed items
            total_items: Total number of items (if known)
            metadata: Additional metadata
            status: Checkpoint status

        """
        stmt = select(ScanCheckpoint).where(ScanCheckpoint.scan_id == scan_id)
        result = await self.session.execute(stmt)
        checkpoint = result.scalar_one_or_none()

        if checkpoint:
            checkpoint.cursor = cursor
            checkpoint.processed_items = processed_items
            checkpoint.total_items = total_items
            checkpoint.status = status
            checkpoint.timestamp = datetime.now(UTC)

            if metadata:
                checkpoint.metadata.update(metadata)
        else:
            logger.warning(
                "Checkpoint not found for save operation",
                scan_id=str(scan_id),
            )
            return

        await self.session.commit()

        logger.debug(
            "Checkpoint saved",
            scan_id=str(scan_id),
            processed=processed_items,
            total=total_items,
            status=status,
        )

    async def load_checkpoint(self, scan_id: UUID) -> CheckpointData | None:
        """Load checkpoint by scan ID.

        Args:
            scan_id: Scan identifier

        Returns:
            CheckpointData or None if not found

        """
        stmt = select(ScanCheckpoint).where(ScanCheckpoint.scan_id == scan_id)
        result = await self.session.execute(stmt)
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            return None

        return CheckpointData(
            scan_id=checkpoint.scan_id,
            cursor=checkpoint.cursor,
            processed_items=checkpoint.processed_items,
            total_items=checkpoint.total_items,
            timestamp=checkpoint.timestamp,
            metadata=checkpoint.metadata,
            status=checkpoint.status,
        )

    async def get_active_checkpoints(
        self,
        user_id: int,
        operation_type: str | None = None,
    ) -> list[CheckpointData]:
        """Get active checkpoints for user.

        Args:
            user_id: User ID
            operation_type: Filter by operation type

        Returns:
            List of active checkpoints

        """
        stmt = select(ScanCheckpoint).where(
            ScanCheckpoint.user_id == user_id,
            ScanCheckpoint.status == "in_progress",
        )

        if operation_type:
            stmt = stmt.where(ScanCheckpoint.operation_type == operation_type)

        result = await self.session.execute(stmt)
        checkpoints = result.scalars().all()

        return [
            CheckpointData(
                scan_id=cp.scan_id,
                cursor=cp.cursor,
                processed_items=cp.processed_items,
                total_items=cp.total_items,
                timestamp=cp.timestamp,
                metadata=cp.metadata,
                status=cp.status,
            )
            for cp in checkpoints
        ]

    async def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """Clean up old completed or failed checkpoints.

        Args:
            days: Delete checkpoints older than N days

        Returns:
            Number of deleted checkpoints

        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        stmt = select(ScanCheckpoint).where(
            ScanCheckpoint.timestamp < cutoff_date,
            ScanCheckpoint.status.in_(["completed", "failed"]),
        )

        result = await self.session.execute(stmt)
        checkpoints = result.scalars().all()

        count = len(checkpoints)
        for checkpoint in checkpoints:
            await self.session.delete(checkpoint)

        await self.session.commit()

        logger.info(f"Cleaned up {count} old checkpoints (older than {days} days)")

        return count

    async def mark_checkpoint_completed(self, scan_id: UUID) -> None:
        """Mark checkpoint as completed.

        Args:
            scan_id: Scan identifier

        """
        await self.save_checkpoint(
            scan_id=scan_id,
            status="completed",
        )

    async def mark_checkpoint_failed(
        self,
        scan_id: UUID,
        error_message: str | None = None,
    ) -> None:
        """Mark checkpoint as failed.

        Args:
            scan_id: Scan identifier
            error_message: Error message

        """
        metadata = {}
        if error_message:
            metadata["error"] = error_message

        await self.save_checkpoint(
            scan_id=scan_id,
            status="failed",
            metadata=metadata,
        )

    def register_shutdown_handlers(
        self,
        scan_id: UUID,
        cleanup_callback: callable | None = None,
    ) -> None:
        """Register graceful shutdown handlers.

        Args:
            scan_id: Scan identifier
            cleanup_callback: Optional callback for cleanup

        """
        if self._shutdown_handlers_registered:
            return

        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            logger.warning(f"Received signal {signum}, saving checkpoint and shutting down...")

            # Save final checkpoint
            asyncio.create_task(
                self.save_checkpoint(
                    scan_id=scan_id,
                    status="interrupted",
                    metadata={"signal": signum},
                )
            )

            # Run cleanup callback
            if cleanup_callback:
                cleanup_callback()

            sys.exit(0)

        # Register for SIGTERM and SIGINT
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self._shutdown_handlers_registered = True
        logger.info("Shutdown handlers registered for graceful termination")

    def record_error(self) -> bool:
        """Record a consecutive error.

        Returns:
            bool: True if should trigger shutdown, False otherwise

        """
        self._consecutive_errors += 1
        logger.warning(
            f"Consecutive error recorded: {self._consecutive_errors}/{self.max_consecutive_errors}",
        )

        if self._consecutive_errors >= self.max_consecutive_errors:
            logger.critical(
                f"Maximum consecutive errors ({self.max_consecutive_errors}) reached! Triggering shutdown...",
            )
            return True

        return False

    def reset_error_counter(self) -> None:
        """Reset consecutive error counter after successful operation."""
        if self._consecutive_errors > 0:
            logger.info(
                f"Resetting error counter from {self._consecutive_errors} to 0",
            )
            self._consecutive_errors = 0

    def pause_operations(self) -> None:
        """Pause bot operations until manual resume."""
        self._is_paused = True
        logger.warning("Bot operations PAUSED")

    def resume_operations(self) -> None:
        """Resume bot operations after pause."""
        self._is_paused = False
        self._consecutive_errors = 0
        logger.info("Bot operations RESUMED")

    @property
    def is_paused(self) -> bool:
        """Check if operations are paused."""
        return self._is_paused

    @property
    def consecutive_errors(self) -> int:
        """Get current consecutive error count."""
        return self._consecutive_errors

    def set_shutdown_callback(self, callback: callable) -> None:
        """Set callback to be called on critical shutdown.

        Args:
            callback: Async function to call on shutdown

        """
        self._shutdown_callback = callback
        logger.info("Shutdown callback registered")

    async def trigger_emergency_shutdown(self, reason: str) -> None:
        """Trigger emergency shutdown.

        Args:
            reason: Reason for shutdown

        """
        logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
        self.pause_operations()

        if self._shutdown_callback:
            try:
                await self._shutdown_callback(reason)
            except Exception as e:
                logger.exception(f"Error in shutdown callback: {e}")


class LocalStateManager:
    """File-based state manager for development/testing."""

    def __init__(self, state_dir: str | Path = "data/checkpoints"):
        """Initialize local state manager.

        Args:
            state_dir: Directory for checkpoint files

        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_file(self, scan_id: UUID) -> Path:
        """Get checkpoint file path."""
        return self.state_dir / f"{scan_id}.json"

    async def save_checkpoint(
        self,
        scan_id: UUID,
        cursor: str | None = None,
        processed_items: int = 0,
        total_items: int | None = None,
        metadata: dict[str, Any] | None = None,
        status: str = "in_progress",
    ) -> None:
        """Save checkpoint to file."""
        checkpoint_file = self._get_checkpoint_file(scan_id)

        checkpoint_data = {
            "scan_id": str(scan_id),
            "cursor": cursor,
            "processed_items": processed_items,
            "total_items": total_items,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
            "status": status,
        }

        checkpoint_file.write_text(
            json.dumps(checkpoint_data, indent=2),
            encoding="utf-8",
        )

        logger.debug(
            "Checkpoint saved to file",
            scan_id=str(scan_id),
            file=str(checkpoint_file),
        )

    async def load_checkpoint(self, scan_id: UUID) -> CheckpointData | None:
        """Load checkpoint from file."""
        checkpoint_file = self._get_checkpoint_file(scan_id)

        if not checkpoint_file.exists():
            return None

        try:
            data = json.loads(checkpoint_file.read_text(encoding="utf-8"))

            return CheckpointData(
                scan_id=UUID(data["scan_id"]),
                cursor=data.get("cursor"),
                processed_items=data.get("processed_items", 0),
                total_items=data.get("total_items"),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                metadata=data.get("metadata", {}),
                status=data.get("status", "in_progress"),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.exception(
                "Failed to load checkpoint",
                scan_id=str(scan_id),
                error=str(e),
            )
            return None

    async def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """Clean up old checkpoint files."""
        cutoff_time = datetime.now(UTC) - timedelta(days=days)
        count = 0

        for checkpoint_file in self.state_dir.glob("*.json"):
            try:
                data = json.loads(checkpoint_file.read_text(encoding="utf-8"))
                timestamp = datetime.fromisoformat(data["timestamp"])
                status = data.get("status", "in_progress")

                if timestamp < cutoff_time and status in ["completed", "failed"]:
                    checkpoint_file.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                continue

        logger.info(f"Cleaned up {count} old checkpoint files")
        return count

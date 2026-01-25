"""Knowledge Base models for user-specific trading memory.

This module provides database models for storing user knowledge entries,
including trading patterns, lessons learned, and market insights.

Inspired by Anthropic's Knowledge Bases concept for proactive
context checking and automatic knowledge accumulation.

Created: January 2026
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    String,
    Text,
)
from sqlalchemy.types import JSON

from src.models.base import Base, UUIDType


class KnowledgeEntry(Base):
    """Knowledge entry model.

    Stores individual knowledge items accumulated from user's trading activity.
    Each entry represents a piece of learned information that can be used
    to personalize recommendations and improve trading decisions.

    Attributes:
        id: Unique identifier
        user_id: Reference to the user who owns this knowledge
        knowledge_type: Type of knowledge (pattern, lesson, insight, etc.)
        title: Short description of the knowledge
        content: Full JSON content of the knowledge
        relevance_score: Current relevance (0.0-1.0), decays over time
        game: Game this knowledge applies to (csgo, dota2, etc.)
        item_category: Optional item category filter
        use_count: Number of times this knowledge was used
        created_at: When knowledge was first recorded
        updated_at: Last update timestamp
        last_used_at: Last time this knowledge was retrieved
        is_active: Whether this knowledge is still active
    """

    __tablename__ = "knowledge_entries"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(BigInteger, nullable=False, index=True)
    knowledge_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(JSON, nullable=False, default=dict)
    relevance_score = Column(Float, default=1.0)
    game = Column(String(50), nullable=True, index=True)
    item_category = Column(String(100), nullable=True)
    use_count = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_knowledge_user_type", "user_id", "knowledge_type"),
        Index("ix_knowledge_user_game", "user_id", "game"),
        Index("ix_knowledge_relevance", "user_id", "relevance_score"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<KnowledgeEntry(id={self.id}, user_id={self.user_id}, "
            f"type='{self.knowledge_type}', title='{self.title[:30]}...')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "knowledge_type": self.knowledge_type,
            "title": self.title,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "game": self.game,
            "item_category": self.item_category,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "is_active": self.is_active,
        }


class TradingPattern(Base):
    """Trading pattern model.

    Stores detected trading patterns for a user, such as:
    - Profitable item categories
    - Best trading times
    - Successful price ranges
    """

    __tablename__ = "trading_patterns"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(BigInteger, nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)
    pattern_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    pattern_data = Column(JSON, nullable=False, default=dict)
    confidence = Column(Float, default=0.5)
    occurrences = Column(BigInteger, default=1)
    total_profit = Column(Float, default=0.0)
    avg_profit_percent = Column(Float, default=0.0)
    game = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_pattern_user_type", "user_id", "pattern_type"),
        Index("ix_pattern_confidence", "user_id", "confidence"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TradingPattern(id={self.id}, user_id={self.user_id}, "
            f"type='{self.pattern_type}', name='{self.pattern_name}')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "pattern_type": self.pattern_type,
            "pattern_name": self.pattern_name,
            "description": self.description,
            "pattern_data": self.pattern_data,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "total_profit": self.total_profit,
            "avg_profit_percent": self.avg_profit_percent,
            "game": self.game,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }


class LessonLearned(Base):
    """Lesson learned model.

    Stores lessons from unsuccessful trades or market events.
    Helps avoid repeating mistakes in future trading decisions.
    """

    __tablename__ = "lessons_learned"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(BigInteger, nullable=False, index=True)
    lesson_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    context = Column(JSON, nullable=False, default=dict)
    severity = Column(String(20), default="medium")  # low, medium, high
    loss_amount = Column(Float, nullable=True)
    item_name = Column(String(255), nullable=True)
    game = Column(String(50), nullable=True, index=True)
    trigger_conditions = Column(JSON, nullable=True)  # Conditions to show warning
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    reminder_count = Column(BigInteger, default=0)
    last_reminded_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (Index("ix_lesson_user_type", "user_id", "lesson_type"),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<LessonLearned(id={self.id}, user_id={self.user_id}, "
            f"type='{self.lesson_type}', title='{self.title[:30]}...')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "lesson_type": self.lesson_type,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "severity": self.severity,
            "loss_amount": self.loss_amount,
            "item_name": self.item_name,
            "game": self.game,
            "trigger_conditions": self.trigger_conditions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reminder_count": self.reminder_count,
            "last_reminded_at": (
                self.last_reminded_at.isoformat() if self.last_reminded_at else None
            ),
            "is_active": self.is_active,
        }

"""Logging models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from src.models.base import Base, UUIDType


class CommandLog(Base):
    """Command log model."""

    __tablename__ = "command_log"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(UUIDType, index=True)
    command = Column(String(100), nullable=False, index=True)
    parameters = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class AnalyticsEvent(Base):
    """Analytics event model."""

    __tablename__ = "events"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(UUIDType, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON)
    session_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

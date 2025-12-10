"""Base model configuration."""

from typing import Any
from uuid import UUID

from sqlalchemy import String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase


class SQLiteUUID(TypeDecorator[UUID]):
    """UUID type for SQLite - stores as string."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(
        self,
        value: UUID | str | None,
        dialect: Any,
    ) -> str | None:
        """Convert UUID to string when storing."""
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    def process_result_value(
        self,
        value: str | None,
        dialect: Any,
    ) -> UUID | None:
        """Convert string back to UUID when retrieving."""
        if value is None:
            return None
        return UUID(value)


# Use SQLiteUUID for all UUID columns
UUIDType = SQLiteUUID


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

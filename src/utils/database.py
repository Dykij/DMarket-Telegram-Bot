"""Database utilities for DMarket Bot.

This module provides database connection management, model definitions,
and common database operations.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    TypeDecorator,
    create_engine,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


logger = logging.getLogger(__name__)


class SQLiteUUID(TypeDecorator):
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
        return str(value) if isinstance(value, UUID) else value

    def process_result_value(
        self,
        value: str | None,
        dialect: Any,
    ) -> UUID | None:
        """Convert string back to UUID when retrieving."""
        if value is None:
            return None
        return UUID(value) if isinstance(value, str) else value


# Use SQLiteUUID for all UUID columns
UUIDType = SQLiteUUID


logger = logging.getLogger(__name__)


# SQLAlchemy Base (updated for 2.0)
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


T = TypeVar("T", bound=Base)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language_code = Column(String(10), default="en")
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class UserSettings(Base):
    """User settings model."""

    __tablename__ = "user_settings"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(UUIDType, nullable=False, index=True)
    notifications_enabled = Column(Boolean, default=True)
    price_alerts_enabled = Column(Boolean, default=True)
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class MarketData(Base):
    """Market data model."""

    __tablename__ = "market_data"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    item_id = Column(String(255), nullable=False, index=True)
    game = Column(String(100), nullable=False, index=True)
    item_name = Column(Text, nullable=False)
    price_usd = Column(Float, nullable=False)
    price_change_24h = Column(Float)
    volume_24h = Column(Integer)
    market_cap = Column(Float)
    data_source = Column(String(50), default="dmarket")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class PriceAlert(Base):
    """Price alert model."""

    __tablename__ = "price_alerts"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    user_id = Column(UUIDType, nullable=False, index=True)
    item_id = Column(String(255), nullable=False)
    target_price = Column(Float, nullable=False)
    condition = Column(String(10), nullable=False)  # 'above' or 'below'
    is_active = Column(Boolean, default=True, index=True)
    triggered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


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


class DatabaseManager:
    """Database connection and operations manager."""

    def __init__(self, database_url: str, echo: bool = False):
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL queries

        """
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._async_engine = None
        self._session_maker = None
        self._async_session_maker = None

    @property
    def engine(self):
        """Get synchronous SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                echo=self.echo,
                pool_pre_ping=True,
            )
        return self._engine

    @property
    def async_engine(self):
        """Get asynchronous SQLAlchemy engine."""
        if self._async_engine is None:
            # Convert sync URL to async URL if needed
            async_url = self.database_url
            if async_url.startswith("postgresql://"):
                async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
            elif async_url.startswith("sqlite:///"):
                async_url = async_url.replace("sqlite:///", "sqlite+aiosqlite:///")

            self._async_engine = create_async_engine(
                async_url,
                echo=self.echo,
                pool_pre_ping=True,
            )
        return self._async_engine

    @property
    def session_maker(self):
        """Get session maker for synchronous operations."""
        if self._session_maker is None:
            self._session_maker = sessionmaker(bind=self.engine)
        return self._session_maker

    @property
    def async_session_maker(self):
        """Get session maker for asynchronous operations."""
        if self._async_session_maker is None:
            self._async_session_maker = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
            )
        return self._async_session_maker

    def get_session(self) -> Session:
        """Get synchronous database session."""
        return self.session_maker()

    def get_async_session(self) -> AsyncSession:
        """Get asynchronous database session."""
        return self.async_session_maker()

    async def init_database(self) -> None:
        """Initialize database tables."""
        try:
            async with self.async_engine.begin() as conn:
                # SQLite doesn't support CREATE SCHEMA
                # Create tables directly
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize database: {e}")
            raise

    async def close(self) -> None:
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._engine:
            self._engine.dispose()

    # User operations
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str = "en",
    ) -> User:
        """Get existing user or create new one."""
        async with self.get_async_session() as session:
            # Try to find existing user
            result = await session.execute(
                text("SELECT * FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": telegram_id},
            )
            user_row = result.fetchone()

            if user_row:
                # Update last activity
                await session.execute(
                    text(
                        """
                        UPDATE users
                        SET last_activity = :now, username = :username,
                            first_name = :first_name, last_name = :last_name
                        WHERE telegram_id = :telegram_id
                    """,
                    ),
                    {
                        "now": datetime.now(UTC),
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                        "telegram_id": telegram_id,
                    },
                )
                await session.commit()

                # Return existing user
                return User(
                    id=(
                        UUID(user_row.id)
                        if isinstance(user_row.id, str)
                        else user_row.id
                    ),
                    telegram_id=user_row.telegram_id,
                    username=user_row.username,
                    first_name=user_row.first_name,
                    last_name=user_row.last_name,
                    language_code=user_row.language_code,
                    is_active=user_row.is_active,
                    is_admin=user_row.is_admin,
                    created_at=user_row.created_at,
                    updated_at=user_row.updated_at,
                    last_activity=user_row.last_activity,
                )
            # Create new user
            user_id = uuid4()
            now = datetime.now(UTC)

            await session.execute(
                text(
                    """
                        INSERT INTO users (
                            id, telegram_id, username, first_name, last_name,
                            language_code, is_active, is_admin, created_at,
                            updated_at, last_activity
                        ) VALUES (
                            :id, :telegram_id, :username, :first_name, :last_name,
                            :language_code, :is_active, :is_admin, :created_at,
                            :updated_at, :last_activity
                        )
                    """,
                ),
                {
                    "id": str(user_id),
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "language_code": language_code,
                    "is_active": True,
                    "is_admin": False,
                    "created_at": now,
                    "updated_at": now,
                    "last_activity": now,
                },
            )
            await session.commit()

            return User(
                id=user_id,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                is_active=True,
                is_admin=False,
                created_at=now,
                updated_at=now,
                last_activity=now,
            )

    async def log_command(
        self,
        user_id: UUID,
        command: str,
        parameters: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
        execution_time_ms: int | None = None,
    ) -> None:
        """Log command execution."""
        async with self.get_async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO command_log (
                        id, user_id, command, parameters, success,
                        error_message, execution_time_ms, created_at
                    ) VALUES (
                        :id, :user_id, :command, :parameters, :success,
                        :error_message, :execution_time_ms, :created_at
                    )
                """,
                ),
                {
                    "id": str(uuid4()),
                    "user_id": str(user_id),
                    "command": command,
                    "parameters": json.dumps(parameters) if parameters else None,
                    "success": success,
                    "error_message": error_message,
                    "execution_time_ms": execution_time_ms,
                    "created_at": datetime.now(UTC),
                },
            )
            await session.commit()

    async def save_market_data(
        self,
        item_id: str,
        game: str,
        item_name: str,
        price_usd: float,
        price_change_24h: float | None = None,
        volume_24h: int | None = None,
        market_cap: float | None = None,
        data_source: str = "dmarket",
    ) -> None:
        """Save market data."""
        async with self.get_async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO market_data (
                        id, item_id, game, item_name, price_usd,
                        price_change_24h, volume_24h, market_cap,
                        data_source, created_at
                    ) VALUES (
                        :id, :item_id, :game, :item_name, :price_usd,
                        :price_change_24h, :volume_24h, :market_cap,
                        :data_source, :created_at
                    )
                """,
                ),
                {
                    "id": str(uuid4()),
                    "item_id": item_id,
                    "game": game,
                    "item_name": item_name,
                    "price_usd": price_usd,
                    "price_change_24h": price_change_24h,
                    "volume_24h": volume_24h,
                    "market_cap": market_cap,
                    "data_source": data_source,
                    "created_at": datetime.now(UTC),
                },
            )
            await session.commit()

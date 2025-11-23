"""Database utilities for DMarket Bot.

This module provides database connection management, model definitions,
and common database operations.
"""

from datetime import UTC, datetime
import json
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.models.base import Base
from src.models.user import User


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and operations manager."""

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL queries
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to overflow

        """
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._session_maker: sessionmaker[Session] | None = None
        self._async_session_maker: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> Engine:
        """Get synchronous SQLAlchemy engine."""
        if self._engine is None:
            kwargs: dict[str, Any] = {
                "echo": self.echo,
                "pool_pre_ping": True,
            }

            # Check for in-memory SQLite
            is_memory = ":memory:" in self.database_url or "mode=memory" in self.database_url

            if not is_memory:
                kwargs["pool_size"] = self.pool_size
                kwargs["max_overflow"] = self.max_overflow
            else:
                from sqlalchemy.pool import StaticPool

                kwargs["poolclass"] = StaticPool
                kwargs["connect_args"] = {"check_same_thread": False}

            self._engine = create_engine(
                self.database_url,
                **kwargs,
            )
        return self._engine

    @property
    def async_engine(self) -> AsyncEngine:
        """Get asynchronous SQLAlchemy engine."""
        if self._async_engine is None:
            # Convert sync URL to async URL if needed
            async_url = self.database_url
            if async_url.startswith("postgresql://"):
                async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
            elif async_url.startswith("sqlite:///"):
                async_url = async_url.replace("sqlite:///", "sqlite+aiosqlite:///")

            kwargs: dict[str, Any] = {
                "echo": self.echo,
                "pool_pre_ping": True,
            }

            # Check for in-memory SQLite
            is_memory = ":memory:" in self.database_url or "mode=memory" in self.database_url

            if not is_memory:
                kwargs["pool_size"] = self.pool_size
                kwargs["max_overflow"] = self.max_overflow
            else:
                from sqlalchemy.pool import StaticPool

                kwargs["poolclass"] = StaticPool

            self._async_engine = create_async_engine(
                async_url,
                **kwargs,
            )
        return self._async_engine

    @property
    def session_maker(self) -> sessionmaker[Session]:
        """Get session maker for synchronous operations."""
        if self._session_maker is None:
            self._session_maker = sessionmaker(bind=self.engine)
        return self._session_maker

    @property
    def async_session_maker(self) -> async_sessionmaker[AsyncSession]:
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

    async def get_db_status(self) -> dict[str, Any]:
        """Get database connection pool status."""
        status: dict[str, Any] = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "sync_engine": "Not initialized",
            "async_engine": "Not initialized",
        }

        if self._engine:
            pool = self._engine.pool
            status["sync_engine"] = {
                "size": pool.size(),
                "checkedin": pool.checkedin(),
                "checkedout": pool.checkedout(),
                "overflow": pool.overflow(),
            }

        if self._async_engine:
            # Async engine pool status might be accessed differently
            # depending on the driver. But usually it wraps a sync pool
            pool = self._async_engine.sync_engine.pool
            status["async_engine"] = {
                "size": pool.size(),
                "checkedin": pool.checkedin(),
                "checkedout": pool.checkedout(),
                "overflow": pool.overflow(),
            }

        return status

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

                # Return updated user with new data
                return User(
                    id=(UUID(user_row.id) if isinstance(user_row.id, str) else user_row.id),
                    telegram_id=user_row.telegram_id,
                    username=username or user_row.username,
                    first_name=first_name or user_row.first_name,
                    last_name=last_name or user_row.last_name,
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
                            id, telegram_id, username, first_name,
                            last_name, language_code, is_active,
                            is_admin, created_at, updated_at,
                            last_activity
                        ) VALUES (
                            :id, :telegram_id, :username, :first_name,
                            :last_name, :language_code, :is_active,
                            :is_admin, :created_at, :updated_at,
                            :last_activity
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
                    "parameters": (json.dumps(parameters) if parameters else None),
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

    async def get_price_history(
        self,
        item_name: str,
        game: str,
        start_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get price history for an item.

        Args:
            item_name: Name of the item
            game: Game identifier (csgo, dota2, etc.)
            start_date: Start date for history

        Returns:
            list: List of price records with timestamp and price_usd
        """
        async with self.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT price_usd, created_at as timestamp
                    FROM market_data
                    WHERE item_name = :item_name
                      AND game = :game
                      AND created_at >= :start_date
                    ORDER BY created_at DESC
                """
                ),
                {
                    "item_name": item_name,
                    "game": game,
                    "start_date": start_date,
                },
            )

            rows = result.fetchall()
            return [
                {
                    "price_usd": row[0],
                    "timestamp": row[1],
                }
                for row in rows
            ]

    async def get_trade_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get trade statistics for a date range.

        Args:
            start_date: Start of the period
            end_date: End of the period

        Returns:
            Dictionary with trade statistics

        """
        async with self.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)
                            as successful_trades,
                        SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)
                            as cancelled_trades,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
                            as failed_trades,
                        COALESCE(SUM(profit_usd), 0.0) as total_profit_usd,
                        COALESCE(AVG(profit_percent), 0.0)
                            as avg_profit_percent
                    FROM trades
                    WHERE created_at >= :start_date
                      AND created_at < :end_date
                """
                ),
                {"start_date": start_date, "end_date": end_date},
            )

            row = result.fetchone()
            if row:
                return {
                    "total_trades": row[0] or 0,
                    "successful_trades": row[1] or 0,
                    "cancelled_trades": row[2] or 0,
                    "failed_trades": row[3] or 0,
                    "total_profit_usd": float(row[4] or 0.0),
                    "avg_profit_percent": float(row[5] or 0.0),
                }
            return {}

    async def get_error_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get error statistics for a date range.

        Args:
            start_date: Start of the period
            end_date: End of the period

        Returns:
            Dictionary with error statistics

        """
        async with self.get_async_session() as session:
            # API errors breakdown
            result = await session.execute(
                text(
                    """
                    SELECT error_message, COUNT(*) as count
                    FROM command_log
                    WHERE success = false
                      AND created_at >= :start_date
                      AND created_at < :end_date
                      AND error_message LIKE '%API%'
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT 10
                """
                ),
                {"start_date": start_date, "end_date": end_date},
            )

            api_errors = {}
            for row in result.fetchall():
                error_type = self._categorize_error(row[0])
                api_errors[error_type] = row[1]

            # Critical errors count
            result_critical = await session.execute(
                text(
                    """
                    SELECT COUNT(*) as critical_count
                    FROM command_log
                    WHERE success = false
                      AND created_at >= :start_date
                      AND created_at < :end_date
                      AND error_message LIKE '%CRITICAL%'
                """
                ),
                {"start_date": start_date, "end_date": end_date},
            )

            critical_row = result_critical.fetchone()
            critical_errors = critical_row[0] if critical_row else 0

            return {
                "api_errors": api_errors,
                "critical_errors": critical_errors,
            }

    async def get_scan_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get scan statistics for a date range.

        Args:
            start_date: Start of the period
            end_date: End of the period

        Returns:
            Dictionary with scan statistics

        """
        async with self.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as scans_performed,
                        COALESCE(
                            SUM(
                                CAST(
                                    json_extract(
                                        parameters, '$.opportunities_found'
                                    ) AS INTEGER
                                )
                            ), 0
                        ) as opportunities_found
                    FROM command_log
                    WHERE command LIKE '%scan%'
                      AND success = true
                      AND created_at >= :start_date
                      AND created_at < :end_date
                """
                ),
                {"start_date": start_date, "end_date": end_date},
            )

            row = result.fetchone()
            if row:
                return {
                    "scans_performed": row[0] or 0,
                    "opportunities_found": row[1] or 0,
                }
            return {}

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error message into a type.

        Args:
            error_message: Full error message

        Returns:
            Error category/type

        """
        if "rate_limit" in error_message.lower():
            return "rate_limit"
        if "timeout" in error_message.lower():
            return "timeout"
        if "connection" in error_message.lower():
            return "connection"
        if "authentication" in error_message.lower():
            return "authentication"
        return "other"

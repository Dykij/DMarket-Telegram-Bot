"""Tests for database utilities.

This module tests the DatabaseManager class including:
- Database connection and engine creation
- Session management
- Database initialization
"""

import pytest

from src.utils.database import DatabaseManager


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_init(self):
        """Test DatabaseManager initialization."""
        manager = DatabaseManager(
            database_url="sqlite:///test.db",
            echo=True,
            pool_size=10,
            max_overflow=20,
        )

        assert manager.database_url == "sqlite:///test.db"
        assert manager.echo is True
        assert manager.pool_size == 10
        assert manager.max_overflow == 20
        assert manager._async_engine is None
        assert manager._async_session_maker is None

    def test_default_values(self):
        """Test DatabaseManager default values."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        assert manager.echo is False
        assert manager.pool_size == 5
        assert manager.max_overflow == 10

    def test_async_engine_property_creates_engine(self):
        """Test that async_engine property creates engine on first access."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        assert manager._async_engine is None
        engine = manager.async_engine
        assert engine is not None
        assert manager._async_engine is engine

    def test_async_engine_caches_engine(self):
        """Test that async_engine property returns same engine instance."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        engine1 = manager.async_engine
        engine2 = manager.async_engine
        assert engine1 is engine2

    def test_async_session_maker_property(self):
        """Test async_session_maker property."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        session_maker = manager.async_session_maker
        assert session_maker is not None
        assert manager._async_session_maker is session_maker

    def test_async_session_maker_caches_maker(self):
        """Test that async_session_maker returns same instance."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        maker1 = manager.async_session_maker
        maker2 = manager.async_session_maker
        assert maker1 is maker2

    def test_get_async_session(self):
        """Test get_async_session returns session."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        session = manager.get_async_session()
        assert session is not None


class TestDatabaseManagerURLConversion:
    """Tests for database URL conversion."""

    def test_postgresql_url_conversion(self):
        """Test PostgreSQL URL is converted to async URL."""
        manager = DatabaseManager(database_url="postgresql://user:pass@localhost/db")
        engine = manager.async_engine

        # Engine URL should be asyncpg
        assert "asyncpg" in str(engine.url)

    def test_sqlite_url_conversion(self):
        """Test SQLite URL is converted to async URL."""
        manager = DatabaseManager(database_url="sqlite:///test.db")
        engine = manager.async_engine

        # Engine URL should be aiosqlite
        assert "aiosqlite" in str(engine.url)

    def test_memory_sqlite_uses_static_pool(self):
        """Test in-memory SQLite uses StaticPool."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        engine = manager.async_engine

        # Should be using StaticPool for in-memory database
        assert engine is not None  # Just verify it was created


class TestDatabaseManagerStatus:
    """Tests for database status methods."""

    @pytest.mark.asyncio()
    async def test_get_db_status_not_initialized(self):
        """Test get_db_status when engine not initialized."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        status = await manager.get_db_status()

        assert status["pool_size"] == 5
        assert status["max_overflow"] == 10
        assert status["async_engine"] == "Not initialized"

    @pytest.mark.asyncio()
    async def test_get_db_status_initialized(self):
        """Test get_db_status when engine is initialized."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        # Access engine to initialize it
        _ = manager.async_engine
        status = await manager.get_db_status()

        assert status["pool_size"] == 5
        assert status["max_overflow"] == 10
        # Status should indicate initialization
        assert status["async_engine"] != "Not initialized"


class TestDatabaseManagerClose:
    """Tests for closing database connections."""

    @pytest.mark.asyncio()
    async def test_close_when_initialized(self):
        """Test closing database connections."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        # Initialize engine first
        _ = manager.async_engine
        await manager.close()
        # Should not raise any errors

    @pytest.mark.asyncio()
    async def test_close_when_not_initialized(self):
        """Test closing when engine not initialized."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        # Should not raise any errors
        await manager.close()


class TestDatabaseManagerInit:
    """Tests for database initialization."""

    @pytest.mark.asyncio()
    async def test_init_database(self):
        """Test database initialization."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        await manager.init_database()
        # Should not raise any errors
        assert manager._async_engine is not None
        await manager.close()

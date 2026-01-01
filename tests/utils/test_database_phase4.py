"""
Phase 4 extended unit tests for src/utils/database.py.

Tests for DatabaseManager class including:
- Initialization and configuration
- Engine and session management
- User operations (get_or_create, caching)
- Command logging
- Market data operations
- Trade and error statistics
- Cache management
- Batch operations
- Cleanup operations
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# Import the module under test
try:
    from src.utils.database import DatabaseManager
except ImportError:
    DatabaseManager = None


# Skip all tests if module not available
pytestmark = pytest.mark.skipif(
    DatabaseManager is None, reason="DatabaseManager not available"
)


class TestDatabaseManagerInit:
    """Tests for DatabaseManager initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        db = DatabaseManager("sqlite:///test.db")
        assert db.database_url == "sqlite:///test.db"
        assert db.echo is False
        assert db.pool_size == 5
        assert db.max_overflow == 10
        assert db._async_engine is None
        assert db._async_session_maker is None

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        db = DatabaseManager(
            "postgresql://localhost/test", echo=True, pool_size=10, max_overflow=20
        )
        assert db.database_url == "postgresql://localhost/test"
        assert db.echo is True
        assert db.pool_size == 10
        assert db.max_overflow == 20

    def test_init_with_sqlite_memory(self):
        """Test initialization with in-memory SQLite."""
        db = DatabaseManager("sqlite:///:memory:")
        assert ":memory:" in db.database_url

    def test_init_with_postgres_url(self):
        """Test initialization with PostgreSQL URL."""
        db = DatabaseManager("postgresql://user:pass@host:5432/db")
        assert "postgresql" in db.database_url


class TestAsyncEngineProperty:
    """Tests for async_engine property."""

    def test_async_engine_creates_on_first_access(self):
        """Test that async engine is created on first access."""
        db = DatabaseManager("sqlite:///:memory:")
        # First access should create the engine
        engine = db.async_engine
        assert engine is not None
        assert db._async_engine is not None

    def test_async_engine_reuses_existing(self):
        """Test that same engine is returned on subsequent access."""
        db = DatabaseManager("sqlite:///:memory:")
        engine1 = db.async_engine
        engine2 = db.async_engine
        assert engine1 is engine2

    def test_async_engine_converts_postgres_url(self):
        """Test that PostgreSQL URL is converted to async format."""
        db = DatabaseManager("postgresql://localhost/test")
        # This will fail to connect but we can check URL conversion happens
        with patch("src.utils.database.create_async_engine") as mock_create:
            mock_create.return_value = MagicMock()
            _ = db.async_engine
            call_args = mock_create.call_args
            assert "postgresql+asyncpg://" in call_args[0][0]

    def test_async_engine_converts_sqlite_url(self):
        """Test that SQLite URL is converted to async format."""
        db = DatabaseManager("sqlite:///test.db")
        with patch("src.utils.database.create_async_engine") as mock_create:
            mock_create.return_value = MagicMock()
            _ = db.async_engine
            call_args = mock_create.call_args
            assert "sqlite+aiosqlite://" in call_args[0][0]


class TestAsyncSessionMaker:
    """Tests for async_session_maker property."""

    def test_session_maker_creates_on_first_access(self):
        """Test that session maker is created on first access."""
        db = DatabaseManager("sqlite:///:memory:")
        with patch.object(db, "async_engine", MagicMock()):
            session_maker = db.async_session_maker
            assert session_maker is not None
            assert db._async_session_maker is not None

    def test_session_maker_reuses_existing(self):
        """Test that same session maker is returned on subsequent access."""
        db = DatabaseManager("sqlite:///:memory:")
        with patch.object(db, "async_engine", MagicMock()):
            maker1 = db.async_session_maker
            maker2 = db.async_session_maker
            assert maker1 is maker2

    def test_get_async_session_returns_session(self):
        """Test that get_async_session returns a session."""
        db = DatabaseManager("sqlite:///:memory:")
        mock_session = MagicMock()
        mock_maker = MagicMock(return_value=mock_session)
        db._async_session_maker = mock_maker

        session = db.get_async_session()
        mock_maker.assert_called_once()


class TestGetDbStatus:
    """Tests for get_db_status method."""

    @pytest.mark.asyncio()
    async def test_get_db_status_no_engine(self):
        """Test status when engine not initialized."""
        db = DatabaseManager("sqlite:///:memory:")
        status = await db.get_db_status()
        assert status["pool_size"] == 5
        assert status["max_overflow"] == 10
        assert status["async_engine"] == "Not initialized"

    @pytest.mark.asyncio()
    async def test_get_db_status_with_engine(self):
        """Test status when engine is initialized."""
        db = DatabaseManager("sqlite:///:memory:")

        # Create mock engine with pool
        mock_pool = MagicMock()
        mock_pool.size.return_value = 5
        mock_pool.checkedin.return_value = 3
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0

        mock_sync_engine = MagicMock()
        mock_sync_engine.pool = mock_pool

        mock_engine = MagicMock()
        mock_engine.sync_engine = mock_sync_engine
        db._async_engine = mock_engine

        status = await db.get_db_status()
        assert status["async_engine"]["size"] == 5
        assert status["async_engine"]["checkedin"] == 3
        assert status["async_engine"]["checkedout"] == 2
        assert status["async_engine"]["overflow"] == 0

    @pytest.mark.asyncio()
    async def test_get_db_status_pool_stats_unavailable(self):
        """Test status when pool stats are unavailable."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_engine = MagicMock()
        # Simulate AttributeError when accessing sync_engine
        type(mock_engine).sync_engine = property(
            lambda self: (_ for _ in ()).throw(AttributeError())
        )
        db._async_engine = mock_engine

        status = await db.get_db_status()
        assert "Initialized" in status["async_engine"]


class TestInitDatabase:
    """Tests for init_database method."""

    @pytest.mark.asyncio()
    async def test_init_database_success(self):
        """Test successful database initialization."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_context
        db._async_engine = mock_engine

        await db.init_database()
        mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio()
    async def test_init_database_creates_indexes(self):
        """Test that init_database creates indexes."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_context
        db._async_engine = mock_engine

        with patch.object(
            db, "_create_indexes", new_callable=AsyncMock
        ) as mock_indexes:
            with patch.object(db, "_optimize_sqlite", new_callable=AsyncMock):
                await db.init_database()
                mock_indexes.assert_called_once()


class TestOptimizeSqlite:
    """Tests for _optimize_sqlite method."""

    @pytest.mark.asyncio()
    async def test_optimize_sqlite_executes_pragmas(self):
        """Test that SQLite optimizations are applied."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        await db._optimize_sqlite(mock_conn)

        # Should execute multiple PRAGMA statements
        assert mock_conn.execute.call_count >= 7

    @pytest.mark.asyncio()
    async def test_optimize_sqlite_handles_errors(self):
        """Test that errors during optimization are handled."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("PRAGMA error"))

        # Should not raise exception
        await db._optimize_sqlite(mock_conn)


class TestCreateIndexes:
    """Tests for _create_indexes method."""

    @pytest.mark.asyncio()
    async def test_create_indexes_success(self):
        """Test successful index creation."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        await db._create_indexes(mock_conn)

        # Should execute multiple CREATE INDEX statements
        assert mock_conn.execute.call_count >= 10

    @pytest.mark.asyncio()
    async def test_create_indexes_handles_errors(self):
        """Test that errors during index creation are handled gracefully."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Index exists"))

        # Should not raise exception
        await db._create_indexes(mock_conn)


class TestCloseDatabase:
    """Tests for close method."""

    @pytest.mark.asyncio()
    async def test_close_disposes_engine(self):
        """Test that close disposes the engine."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        db._async_engine = mock_engine

        await db.close()
        mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio()
    async def test_close_no_engine(self):
        """Test close when no engine exists."""
        db = DatabaseManager("sqlite:///:memory:")

        # Should not raise exception
        await db.close()


class TestGetOrCreateUser:
    """Tests for get_or_create_user method."""

    @pytest.mark.asyncio()
    async def test_get_existing_user(self):
        """Test getting existing user updates last activity."""
        db = DatabaseManager("sqlite:///:memory:")

        user_id = uuid4()
        mock_row = MagicMock()
        mock_row.id = str(user_id)
        mock_row.telegram_id = 123456
        mock_row.username = "testuser"
        mock_row.first_name = "Test"
        mock_row.last_name = "User"
        mock_row.language_code = "en"
        mock_row.is_active = True
        mock_row.is_admin = False
        mock_row.created_at = datetime.now(UTC)
        mock_row.updated_at = datetime.now(UTC)
        mock_row.last_activity = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            with patch.object(db, "invalidate_user_cache", new_callable=AsyncMock):
                user = await db.get_or_create_user(123456, "newuser")
                assert user.telegram_id == 123456

    @pytest.mark.asyncio()
    async def test_create_new_user(self):
        """Test creating new user when not found."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # User not found

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            user = await db.get_or_create_user(
                999999, username="newuser", first_name="New", last_name="User"
            )
            assert user.telegram_id == 999999
            assert user.username == "newuser"
            assert user.is_active is True


class TestLogCommand:
    """Tests for log_command method."""

    @pytest.mark.asyncio()
    async def test_log_command_success(self):
        """Test logging successful command."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            await db.log_command(
                user_id=uuid4(),
                command="/scan",
                parameters={"game": "csgo"},
                success=True,
                execution_time_ms=150,
            )
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_log_command_with_error(self):
        """Test logging failed command."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            await db.log_command(
                user_id=uuid4(),
                command="/scan",
                success=False,
                error_message="API rate limit exceeded",
            )
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio()
    async def test_log_command_no_parameters(self):
        """Test logging command without parameters."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            await db.log_command(user_id=uuid4(), command="/help")
            mock_session.execute.assert_called_once()


class TestSaveMarketData:
    """Tests for save_market_data method."""

    @pytest.mark.asyncio()
    async def test_save_market_data_basic(self):
        """Test saving basic market data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            await db.save_market_data(
                item_id="item123",
                game="csgo",
                item_name="AK-47 | Redline",
                price_usd=15.50,
            )
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_save_market_data_with_all_fields(self):
        """Test saving market data with all optional fields."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            await db.save_market_data(
                item_id="item456",
                game="dota2",
                item_name="Arcana",
                price_usd=35.00,
                price_change_24h=2.5,
                volume_24h=1000,
                market_cap=500000.0,
                data_source="custom",
            )
            mock_session.execute.assert_called_once()


class TestGetPriceHistory:
    """Tests for get_price_history method."""

    @pytest.mark.asyncio()
    async def test_get_price_history_with_data(self):
        """Test getting price history with data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_rows = [
            (15.50, datetime.now(UTC)),
            (15.25, datetime.now(UTC) - timedelta(hours=1)),
            (15.00, datetime.now(UTC) - timedelta(hours=2)),
        ]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            history = await db.get_price_history(
                item_name="AK-47 | Redline",
                game="csgo",
                start_date=datetime.now(UTC) - timedelta(days=1),
            )
            assert len(history) == 3
            assert history[0]["price_usd"] == 15.50

    @pytest.mark.asyncio()
    async def test_get_price_history_empty(self):
        """Test getting price history with no data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            history = await db.get_price_history(
                item_name="NonExistent", game="csgo", start_date=datetime.now(UTC)
            )
            assert len(history) == 0


class TestGetTradeStatistics:
    """Tests for get_trade_statistics method."""

    @pytest.mark.asyncio()
    async def test_get_trade_statistics_with_data(self):
        """Test getting trade statistics with data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_row = (100, 80, 10, 10, 150.50, 5.5)

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            stats = await db.get_trade_statistics(
                start_date=datetime.now(UTC) - timedelta(days=7),
                end_date=datetime.now(UTC),
            )
            assert stats["total_trades"] == 100
            assert stats["successful_trades"] == 80
            assert stats["cancelled_trades"] == 10
            assert stats["failed_trades"] == 10
            assert stats["total_profit_usd"] == 150.50
            assert stats["avg_profit_percent"] == 5.5

    @pytest.mark.asyncio()
    async def test_get_trade_statistics_empty(self):
        """Test getting trade statistics with no data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            stats = await db.get_trade_statistics(
                start_date=datetime.now(UTC) - timedelta(days=7),
                end_date=datetime.now(UTC),
            )
            assert stats == {}


class TestGetErrorStatistics:
    """Tests for get_error_statistics method."""

    @pytest.mark.asyncio()
    async def test_get_error_statistics_with_api_errors(self):
        """Test getting error statistics with API errors."""
        db = DatabaseManager("sqlite:///:memory:")

        api_rows = [
            ("API rate_limit exceeded", 50),
            ("API timeout error", 20),
            ("API connection failed", 10),
        ]
        critical_row = (5,)

        mock_result1 = MagicMock()
        mock_result1.fetchall.return_value = api_rows

        mock_result2 = MagicMock()
        mock_result2.fetchone.return_value = critical_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=[mock_result1, mock_result2])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            stats = await db.get_error_statistics(
                start_date=datetime.now(UTC) - timedelta(days=1),
                end_date=datetime.now(UTC),
            )
            assert "rate_limit" in stats["api_errors"]
            assert stats["critical_errors"] == 5


class TestCategorizeError:
    """Tests for _categorize_error method."""

    def test_categorize_rate_limit_error(self):
        """Test categorizing rate limit error."""
        db = DatabaseManager("sqlite:///:memory:")
        result = db._categorize_error("API rate_limit exceeded")
        assert result == "rate_limit"

    def test_categorize_timeout_error(self):
        """Test categorizing timeout error."""
        db = DatabaseManager("sqlite:///:memory:")
        result = db._categorize_error("Request timeout after 30s")
        assert result == "timeout"

    def test_categorize_connection_error(self):
        """Test categorizing connection error."""
        db = DatabaseManager("sqlite:///:memory:")
        result = db._categorize_error("Connection refused")
        assert result == "connection"

    def test_categorize_authentication_error(self):
        """Test categorizing authentication error."""
        db = DatabaseManager("sqlite:///:memory:")
        result = db._categorize_error("Authentication failed")
        assert result == "authentication"

    def test_categorize_other_error(self):
        """Test categorizing unknown error."""
        db = DatabaseManager("sqlite:///:memory:")
        result = db._categorize_error("Some random error")
        assert result == "other"


class TestGetScanStatistics:
    """Tests for get_scan_statistics method."""

    @pytest.mark.asyncio()
    async def test_get_scan_statistics_with_data(self):
        """Test getting scan statistics with data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_row = (50, 150)  # scans_performed, opportunities_found

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            stats = await db.get_scan_statistics(
                start_date=datetime.now(UTC) - timedelta(days=1),
                end_date=datetime.now(UTC),
            )
            assert stats["scans_performed"] == 50
            assert stats["opportunities_found"] == 150

    @pytest.mark.asyncio()
    async def test_get_scan_statistics_empty(self):
        """Test getting scan statistics with no data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            stats = await db.get_scan_statistics(
                start_date=datetime.now(UTC) - timedelta(days=1),
                end_date=datetime.now(UTC),
            )
            assert stats == {}


class TestCachedMethods:
    """Tests for cached database methods."""

    @pytest.mark.asyncio()
    async def test_get_user_by_telegram_id_cached_found(self):
        """Test getting cached user when found."""
        db = DatabaseManager("sqlite:///:memory:")

        user_id = uuid4()
        mock_row = MagicMock()
        mock_row.id = str(user_id)
        mock_row.telegram_id = 123456
        mock_row.username = "testuser"
        mock_row.first_name = "Test"
        mock_row.last_name = "User"
        mock_row.language_code = "en"
        mock_row.is_active = True
        mock_row.is_admin = False
        mock_row.created_at = datetime.now(UTC)
        mock_row.updated_at = datetime.now(UTC)
        mock_row.last_activity = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            user = await db.get_user_by_telegram_id_cached(123456)
            assert user is not None
            assert user.telegram_id == 123456

    @pytest.mark.asyncio()
    async def test_get_user_by_telegram_id_cached_not_found(self):
        """Test getting cached user when not found."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            user = await db.get_user_by_telegram_id_cached(999999)
            assert user is None

    @pytest.mark.asyncio()
    async def test_get_recent_scans_cached(self):
        """Test getting recent scans cached."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_rows = [
            ("/scan csgo", '{"game": "csgo"}', datetime.now(UTC), True, 150),
            ("/scan dota2", '{"game": "dota2"}', datetime.now(UTC), True, 200),
        ]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            scans = await db.get_recent_scans_cached(uuid4(), limit=5)
            assert len(scans) == 2
            assert scans[0]["command"] == "/scan csgo"


class TestCacheManagement:
    """Tests for cache management methods."""

    @pytest.mark.asyncio()
    async def test_get_cache_stats(self):
        """Test getting cache statistics."""
        db = DatabaseManager("sqlite:///:memory:")

        with patch(
            "src.utils.database.get_all_cache_stats", new_callable=AsyncMock
        ) as mock_stats:
            mock_stats.return_value = {"hits": 100, "misses": 10}
            stats = await db.get_cache_stats()
            assert stats["hits"] == 100
            assert stats["misses"] == 10

    @pytest.mark.asyncio()
    async def test_invalidate_user_cache(self):
        """Test invalidating user cache."""
        db = DatabaseManager("sqlite:///:memory:")

        with patch("src.utils.database._user_cache") as mock_cache:
            mock_cache.delete = AsyncMock()
            await db.invalidate_user_cache(123456)
            mock_cache.delete.assert_called_once()


class TestBatchOperations:
    """Tests for batch operations."""

    @pytest.mark.asyncio()
    async def test_bulk_save_market_data_empty(self):
        """Test bulk save with empty list."""
        db = DatabaseManager("sqlite:///:memory:")

        # Should return early without executing
        await db.bulk_save_market_data([])

    @pytest.mark.asyncio()
    async def test_bulk_save_market_data_with_items(self):
        """Test bulk save with items."""
        db = DatabaseManager("sqlite:///:memory:")

        items = [
            {
                "item_id": "item1",
                "game": "csgo",
                "item_name": "AK-47",
                "price_usd": 15.50,
            },
            {
                "item_id": "item2",
                "game": "csgo",
                "item_name": "M4A1-S",
                "price_usd": 12.00,
            },
        ]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            await db.bulk_save_market_data(items)
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()


class TestCleanupOperations:
    """Tests for cleanup operations."""

    @pytest.mark.asyncio()
    async def test_cleanup_old_market_data(self):
        """Test cleaning up old market data."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.rowcount = 100

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            deleted = await db.cleanup_old_market_data(days=30)
            assert deleted == 100

    @pytest.mark.asyncio()
    async def test_cleanup_expired_cache(self):
        """Test cleaning up expired cache."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_result = MagicMock()
        mock_result.rowcount = 50

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            deleted = await db.cleanup_expired_cache()
            assert deleted == 50

    @pytest.mark.asyncio()
    async def test_vacuum_database_sqlite(self):
        """Test vacuuming SQLite database."""
        db = DatabaseManager("sqlite:///test.db")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_context
        db._async_engine = mock_engine

        await db.vacuum_database()
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio()
    async def test_vacuum_database_non_sqlite(self):
        """Test vacuum is skipped for non-SQLite databases."""
        db = DatabaseManager("postgresql://localhost/test")

        # Should not execute anything for PostgreSQL
        await db.vacuum_database()

    @pytest.mark.asyncio()
    async def test_vacuum_database_handles_error(self):
        """Test vacuum handles errors gracefully."""
        db = DatabaseManager("sqlite:///test.db")

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=Exception("Vacuum failed"))

        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_context
        db._async_engine = mock_engine

        # Should not raise exception
        await db.vacuum_database()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_init_empty_url(self):
        """Test initialization with empty URL."""
        db = DatabaseManager("")
        assert db.database_url == ""

    def test_init_special_characters_in_url(self):
        """Test initialization with special characters in URL."""
        db = DatabaseManager("postgresql://user:p@ss%word@host/db")
        assert "p@ss%word" in db.database_url

    @pytest.mark.asyncio()
    async def test_concurrent_sessions(self):
        """Test handling concurrent sessions."""
        db = DatabaseManager("sqlite:///:memory:")

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_maker = MagicMock(return_value=mock_session)
        db._async_session_maker = mock_maker

        # Multiple sessions should work
        session1 = db.get_async_session()
        session2 = db.get_async_session()
        assert mock_maker.call_count == 2


class TestIntegration:
    """Integration tests for DatabaseManager."""

    @pytest.mark.asyncio()
    async def test_full_user_workflow(self):
        """Test complete user workflow."""
        db = DatabaseManager("sqlite:///:memory:")

        # Mock for create user
        mock_result_none = MagicMock()
        mock_result_none.fetchone.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result_none)
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(db, "get_async_session", return_value=mock_session):
            # Create user
            user = await db.get_or_create_user(123456, "testuser")
            assert user.telegram_id == 123456

            # Log command
            await db.log_command(user.id, "/scan", {"game": "csgo"})

            # Save market data
            await db.save_market_data("item1", "csgo", "AK-47", 15.50)

    @pytest.mark.asyncio()
    async def test_statistics_workflow(self):
        """Test statistics gathering workflow."""
        db = DatabaseManager("sqlite:///:memory:")

        start_date = datetime.now(UTC) - timedelta(days=7)
        end_date = datetime.now(UTC)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock for trade stats
        mock_trade_result = MagicMock()
        mock_trade_result.fetchone.return_value = (10, 8, 1, 1, 50.0, 5.0)

        # Mock for scan stats
        mock_scan_result = MagicMock()
        mock_scan_result.fetchone.return_value = (20, 100)

        mock_session.execute = AsyncMock(
            side_effect=[mock_trade_result, mock_scan_result]
        )

        with patch.object(db, "get_async_session", return_value=mock_session):
            trade_stats = await db.get_trade_statistics(start_date, end_date)
            assert trade_stats["total_trades"] == 10

#!/usr/bin/env python
"""Test database performance improvements.

This script tests the database optimizations including:
- aiosqlite integration
- Index performance
- Batch operations
- Cache cleanup
"""

import asyncio
import logging
import time

from src.utils.config import Config
from src.utils.database import DatabaseManager


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_database_init():
    """Test database initialization."""
    logger.info("Testing database initialization...")

    config = Config.load()
    db = DatabaseManager(config.database.url)

    try:
        await db.init_database()
        logger.info("✅ Database initialized successfully")
        return db
    except Exception as e:
        logger.exception(f"❌ Database initialization failed: {e}")
        raise


async def test_user_operations(db: DatabaseManager):
    """Test user operations with caching."""
    logger.info("Testing user operations...")

    try:
        # Create user
        user = await db.get_or_create_user(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
        )
        logger.info(f"✅ User created: {user.id}")

        # Test cached retrieval
        start = time.time()
        user1 = await db.get_user_by_telegram_id_cached(123456789)
        first_call = time.time() - start

        start = time.time()
        user2 = await db.get_user_by_telegram_id_cached(123456789)
        cached_call = time.time() - start

        if cached_call > 0:
            speedup = first_call / cached_call
            logger.info(
                f"✅ Cache speedup: {speedup:.2f}x faster "
                f"({first_call * 1000:.2f}ms → {cached_call * 1000:.2f}ms)"
            )
        else:
            logger.info(
                f"✅ Cache extremely fast: first call {first_call * 1000:.2f}ms, "
                "cached call < 0.001ms"
            )

    except Exception as e:
        logger.exception(f"❌ User operations failed: {e}")
        raise


async def test_bulk_operations(db: DatabaseManager):
    """Test bulk market data operations."""
    logger.info("Testing bulk operations...")

    try:
        # Prepare test data
        items = []
        for i in range(100):
            items.append({
                "item_id": f"test_item_{i}",
                "game": "csgo",
                "item_name": f"Test Item {i}",
                "price_usd": 10.0 + i * 0.5,
                "volume_24h": 100 + i,
            })

        # Test bulk insert
        start = time.time()
        await db.bulk_save_market_data(items)
        bulk_time = time.time() - start

        logger.info(
            f"✅ Bulk inserted {len(items)} records in "
            f"{bulk_time * 1000:.2f}ms "
            f"({len(items) / bulk_time:.0f} records/sec)"
        )

    except Exception as e:
        logger.exception(f"❌ Bulk operations failed: {e}")
        raise


async def test_cleanup_operations(db: DatabaseManager):
    """Test cleanup operations."""
    logger.info("Testing cleanup operations...")

    try:
        # Test old data cleanup
        deleted = await db.cleanup_old_market_data(days=1)
        logger.info(f"✅ Cleaned up {deleted} old market data records")

        # Test cache cleanup
        cache_deleted = await db.cleanup_expired_cache()
        logger.info(f"✅ Cleaned up {cache_deleted} expired cache records")

        # Test vacuum (SQLite only)
        await db.vacuum_database()
        logger.info("✅ Database vacuumed successfully")

    except Exception as e:
        logger.exception(f"❌ Cleanup operations failed: {e}")
        raise


async def test_cache_stats(db: DatabaseManager):
    """Test cache statistics."""
    logger.info("Testing cache statistics...")

    try:
        stats = await db.get_cache_stats()
        logger.info(f"✅ Cache statistics: {stats}")
    except Exception as e:
        logger.exception(f"❌ Cache stats failed: {e}")
        raise


async def main():
    """Run all database tests."""
    logger.info("=" * 60)
    logger.info("Database Performance Test Suite")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # Initialize database
        db = await test_database_init()

        # Run tests
        await test_user_operations(db)
        await test_bulk_operations(db)
        await test_cleanup_operations(db)
        await test_cache_stats(db)

        # Get final database status
        db_status = await db.get_db_status()
        logger.info(f"Database status: {db_status}")

        # Close database
        await db.close()

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ All tests passed in {elapsed:.2f} seconds")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

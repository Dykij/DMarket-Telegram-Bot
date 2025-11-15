"""Health check script for DMarket Bot.

This script checks the health of all required services and dependencies:
- Telegram API connectivity
- DMarket API connectivity
- Database connectivity
- Redis connectivity (if configured)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.config import Config
from src.utils.database import DatabaseManager


async def check_telegram_api(config: Config) -> bool:
    """Check Telegram API connectivity.

    Args:
        config: Application configuration

    Returns:
        True if Telegram API is accessible, False otherwise

    """
    print("🔍 Checking Telegram API...")

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://api.telegram.org/bot{config.bot.token}/getMe"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    print(
                        f"  ✅ Telegram API accessible "
                        f"(@{bot_info.get('username', 'unknown')})"
                    )
                    return True

            print(f"  ❌ Telegram API error: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ Telegram API connection failed: {e}")
        return False


async def check_dmarket_api(config: Config) -> bool:
    """Check DMarket API connectivity.

    Args:
        config: Application configuration

    Returns:
        True if DMarket API is accessible, False otherwise

    """
    print("🔍 Checking DMarket API...")

    try:
        api = DMarketAPI(
            public_key=config.dmarket.public_key,
            secret_key=config.dmarket.secret_key,
            api_url=config.dmarket.api_url,
        )

        balance = await api.get_balance()

        if balance.get("error"):
            print(f"  ❌ DMarket API error: {balance.get('error_message')}")
            return False

        print(
            f"  ✅ DMarket API accessible (Balance: ${balance.get('balance', 0):.2f})"
        )
        await api._close_client()
        return True

    except Exception as e:
        print(f"  ❌ DMarket API connection failed: {e}")
        return False


async def check_database(config: Config) -> bool:
    """Check database connectivity.

    Args:
        config: Application configuration

    Returns:
        True if database is accessible, False otherwise

    """
    print("🔍 Checking database...")

    try:
        db = DatabaseManager(database_url=config.database.url, echo=False)

        # Try to connect
        await db.init_database()

        print(f"  ✅ Database accessible ({config.database.url.split(':')[0]})")
        await db.close()
        return True

    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False


async def check_redis(config: Config) -> bool:
    """Check Redis connectivity (if configured).

    Args:
        config: Application configuration

    Returns:
        True if Redis is accessible or not configured, False if configured but not accessible

    """
    # Check if Redis URL is configured
    import os

    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        print("ℹ️  Redis not configured (optional)")
        return True

    print("🔍 Checking Redis...")

    try:
        import redis.asyncio as redis

        client = redis.from_url(redis_url)
        await client.ping()
        print("  ✅ Redis accessible")
        await client.close()
        return True

    except ImportError:
        print("  ⚠️  redis package not installed")
        return True
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        return False


async def main() -> int:
    """Run health checks.

    Returns:
        0 if all checks pass, 1 otherwise

    """
    print("=" * 60)
    print("DMarket Bot - Health Check")
    print("=" * 60)
    print()

    try:
        # Load configuration
        config = Config.load()
        config.validate()

        # Run all health checks
        results = await asyncio.gather(
            check_telegram_api(config),
            check_dmarket_api(config),
            check_database(config),
            check_redis(config),
            return_exceptions=False,
        )

        print()
        print("=" * 60)

        # Check if all tests passed
        if all(results):
            print("✅ All health checks passed!")
            print("=" * 60)
            return 0
        print("❌ Some health checks failed!")
        print("=" * 60)
        return 1

    except ValueError as e:
        print()
        print("❌ Configuration validation failed!")
        print(str(e))
        return 1

    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""Database initialization script.

This script initializes the database schema using Alembic migrations.
"""

from pathlib import Path
import subprocess
import sys
import traceback


# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config


def run_alembic_command(command: list[str]) -> int:
    """Run an Alembic command.

    Args:
        command: Alembic command to run

    Returns:
        Exit code

    """
    try:
        result = subprocess.run(  # noqa: S603
            ["alembic", *command],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

    except FileNotFoundError:
        print("Error: Alembic is not installed. Install it with: pip install alembic")
        return 1
    else:
        return result.returncode


def main() -> int:
    """Initialize database schema.

    Returns:
        Exit code

    """
    print("=" * 60)
    print("DMarket Bot - Database Initialization")
    print("=" * 60)
    print()

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = Config.load()
        config.validate()
        print(f"✅ Database URL: {config.database.url}")
        print()

        # Check current database version
        print("🔍 Checking current database version...")
        result = run_alembic_command(["current"])

        if result != 0:
            print()
            print("⚠️  Database not initialized or migration history not found")
            print()

        # Run migrations
        print("🔄 Running database migrations...")
        result = run_alembic_command(["upgrade", "head"])

        if result != 0:
            print()
            print("❌ Migration failed!")
            return 1

        print()
        print("✅ Database migrations completed successfully!")
        print()

        # Show current version
        print("📊 Current database version:")
        run_alembic_command(["current"])
        print()

        print("=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)

        return 0

    except ValueError as e:
        print()
        print("❌ Configuration validation failed!")
        print(str(e))
        return 1

    except Exception as e:  # noqa: BLE001
        print()
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

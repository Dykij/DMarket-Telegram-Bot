#!/usr/bin/env python3
"""Database backup script for DMarket Bot.

This script creates backups of the bot's database:
- SQLite: copies the database file
- PostgreSQL: uses pg_dump

Supports:
- Manual backups
- Scheduled backups via cron
- Retention policy (auto-delete old backups)
- Compression (gzip)

Usage:
    python scripts/backup_database.py                    # Interactive backup
    python scripts/backup_database.py --cron             # Silent mode for cron
    python scripts/backup_database.py --restore FILE     # Restore from backup
    python scripts/backup_database.py --list             # List available backups
    python scripts/backup_database.py --cleanup          # Remove old backups

Cron example (daily at 3 AM):
    0 3 * * * cd /path/to/bot && python scripts/backup_database.py --cron
"""

import argparse
import asyncio
import gzip
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config

logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = Path(__file__).parent.parent / "backups"
MAX_BACKUPS = 30  # Keep last 30 backups
BACKUP_PREFIX = "dmarket_bot_backup"


def setup_logging(quiet: bool = False) -> None:
    """Setup logging configuration.

    Args:
        quiet: If True, only log errors

    """
    level = logging.ERROR if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def ensure_backup_dir() -> Path:
    """Ensure backup directory exists.

    Returns:
        Path to backup directory

    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def get_timestamp() -> str:
    """Get current timestamp for backup filename.

    Returns:
        Formatted timestamp string

    """
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def backup_sqlite(db_path: str, compress: bool = True) -> Path | None:
    """Create backup of SQLite database.

    Args:
        db_path: Path to SQLite database file
        compress: Whether to compress the backup

    Returns:
        Path to backup file or None if failed

    """
    db_file = Path(db_path.replace("sqlite:///", ""))

    if not db_file.exists():
        logger.error(f"Database file not found: {db_file}")
        return None

    ensure_backup_dir()
    timestamp = get_timestamp()
    backup_name = f"{BACKUP_PREFIX}_{timestamp}.db"

    if compress:
        backup_name += ".gz"
        backup_path = BACKUP_DIR / backup_name

        try:
            with open(db_file, "rb") as f_in:
                with gzip.open(backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"SQLite backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create compressed backup: {e}")
            return None
    else:
        backup_path = BACKUP_DIR / backup_name

        try:
            shutil.copy2(db_file, backup_path)
            logger.info(f"SQLite backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None


def backup_postgresql(db_url: str, compress: bool = True) -> Path | None:
    """Create backup of PostgreSQL database using pg_dump.

    Args:
        db_url: PostgreSQL connection URL
        compress: Whether to compress the backup

    Returns:
        Path to backup file or None if failed

    """
    ensure_backup_dir()
    timestamp = get_timestamp()
    backup_name = f"{BACKUP_PREFIX}_{timestamp}.sql"

    if compress:
        backup_name += ".gz"

    backup_path = BACKUP_DIR / backup_name

    try:
        # pg_dump command
        cmd = ["pg_dump", db_url, "--format=plain"]

        if compress:
            # Pipe through gzip
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"pg_dump failed: {stderr.decode()}")
                return None

            with gzip.open(backup_path, "wb") as f:
                f.write(stdout)
        else:
            with open(backup_path, "w") as f:
                subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    check=True,
                )

        logger.info(f"PostgreSQL backup created: {backup_path}")
        return backup_path

    except FileNotFoundError:
        logger.error("pg_dump not found. Make sure PostgreSQL client tools are installed.")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL backup: {e}")
        return None


def restore_sqlite(backup_path: Path, db_path: str) -> bool:
    """Restore SQLite database from backup.

    Args:
        backup_path: Path to backup file
        db_path: Path to restore to

    Returns:
        True if successful

    """
    db_file = Path(db_path.replace("sqlite:///", ""))

    try:
        # Create backup of current database before restore
        if db_file.exists():
            current_backup = db_file.with_suffix(".db.bak")
            shutil.copy2(db_file, current_backup)
            logger.info(f"Current database backed up to: {current_backup}")

        # Restore from backup
        if str(backup_path).endswith(".gz"):
            with gzip.open(backup_path, "rb") as f_in:
                with open(db_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, db_file)

        logger.info(f"Database restored from: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to restore database: {e}")
        return False


def restore_postgresql(backup_path: Path, db_url: str) -> bool:
    """Restore PostgreSQL database from backup.

    Args:
        backup_path: Path to backup file
        db_url: PostgreSQL connection URL

    Returns:
        True if successful

    """
    try:
        # Read backup file
        if str(backup_path).endswith(".gz"):
            with gzip.open(backup_path, "rb") as f:
                sql_content = f.read()
        else:
            with open(backup_path, "rb") as f:
                sql_content = f.read()

        # Restore using psql
        process = subprocess.Popen(
            ["psql", db_url],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(input=sql_content)

        if process.returncode != 0:
            logger.error(f"psql restore failed: {stderr.decode()}")
            return False

        logger.info(f"Database restored from: {backup_path}")
        return True

    except FileNotFoundError:
        logger.error("psql not found. Make sure PostgreSQL client tools are installed.")
        return False
    except Exception as e:
        logger.error(f"Failed to restore database: {e}")
        return False


def list_backups() -> list[dict[str, Any]]:
    """List available backup files.

    Returns:
        List of backup info dictionaries

    """
    if not BACKUP_DIR.exists():
        return []

    backups = []

    for file in sorted(BACKUP_DIR.glob(f"{BACKUP_PREFIX}_*"), reverse=True):
        stat = file.stat()
        backups.append({
            "name": file.name,
            "path": str(file),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        })

    return backups


def cleanup_old_backups(keep: int = MAX_BACKUPS) -> int:
    """Remove old backup files, keeping the most recent ones.

    Args:
        keep: Number of backups to keep

    Returns:
        Number of files removed

    """
    backups = list_backups()

    if len(backups) <= keep:
        logger.info(f"No cleanup needed. {len(backups)} backups exist (max: {keep})")
        return 0

    to_remove = backups[keep:]
    removed = 0

    for backup in to_remove:
        try:
            Path(backup["path"]).unlink()
            logger.info(f"Removed old backup: {backup['name']}")
            removed += 1
        except Exception as e:
            logger.error(f"Failed to remove {backup['name']}: {e}")

    return removed


def create_backup(config: Config, compress: bool = True) -> Path | None:
    """Create database backup based on configuration.

    Args:
        config: Application configuration
        compress: Whether to compress the backup

    Returns:
        Path to backup file or None if failed

    """
    db_url = config.database.url

    if db_url.startswith("sqlite"):
        return backup_sqlite(db_url, compress)
    elif db_url.startswith("postgresql"):
        return backup_postgresql(db_url, compress)
    else:
        logger.error(f"Unsupported database type: {db_url.split(':')[0]}")
        return None


def restore_backup(config: Config, backup_path: Path) -> bool:
    """Restore database from backup.

    Args:
        config: Application configuration
        backup_path: Path to backup file

    Returns:
        True if successful

    """
    db_url = config.database.url

    if db_url.startswith("sqlite"):
        return restore_sqlite(backup_path, db_url)
    elif db_url.startswith("postgresql"):
        return restore_postgresql(backup_path, db_url)
    else:
        logger.error(f"Unsupported database type: {db_url.split(':')[0]}")
        return False


async def send_backup_notification(
    config: Config,
    success: bool,
    backup_path: Path | None = None,
    error: str | None = None,
) -> None:
    """Send backup notification to Telegram.

    Args:
        config: Application configuration
        success: Whether backup was successful
        backup_path: Path to backup file (if successful)
        error: Error message (if failed)

    """
    import httpx

    admin_chat_id = os.getenv("ADMIN_TELEGRAM_CHAT_ID")
    if not admin_chat_id:
        logger.debug("ADMIN_TELEGRAM_CHAT_ID not configured, skipping notification")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if success and backup_path:
        size_mb = round(backup_path.stat().st_size / (1024 * 1024), 2)
        message = (
            f"✅ <b>Database Backup Successful</b>\n"
            f"<code>{timestamp}</code>\n\n"
            f"📁 <b>File:</b> {backup_path.name}\n"
            f"📊 <b>Size:</b> {size_mb} MB"
        )
    else:
        message = (
            f"❌ <b>Database Backup Failed</b>\n"
            f"<code>{timestamp}</code>\n\n"
            f"⚠️ <b>Error:</b> {error or 'Unknown error'}"
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://api.telegram.org/bot{config.bot.token}/sendMessage"
            await client.post(
                url,
                json={
                    "chat_id": admin_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
    except Exception as e:
        logger.error(f"Failed to send backup notification: {e}")


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    parser = argparse.ArgumentParser(description="DMarket Bot Database Backup")
    parser.add_argument(
        "--cron",
        action="store_true",
        help="Cron mode: quiet output, auto-cleanup",
    )
    parser.add_argument(
        "--restore",
        type=str,
        metavar="FILE",
        help="Restore database from backup file",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove old backups",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress backup",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send Telegram notification",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=MAX_BACKUPS,
        help=f"Number of backups to keep (default: {MAX_BACKUPS})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force restore without confirmation (for scripted usage)",
    )

    args = parser.parse_args()
    setup_logging(quiet=args.cron)

    # List backups
    if args.list:
        backups = list_backups()
        if not backups:
            print("No backups found.")
            return 0

        print(f"\n{'='*60}")
        print("Available Backups")
        print(f"{'='*60}\n")

        for i, backup in enumerate(backups, 1):
            created = backup["created"].strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i}. {backup['name']}")
            print(f"   Size: {backup['size_mb']} MB | Created: {created}")
            print()

        print(f"Total: {len(backups)} backups")
        return 0

    # Cleanup old backups
    if args.cleanup:
        removed = cleanup_old_backups(args.keep)
        print(f"Removed {removed} old backup(s)")
        return 0

    # Load configuration
    try:
        config = Config.load()
        config.validate()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Restore from backup
    if args.restore:
        backup_path = Path(args.restore)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return 1

        # Confirmation for restore (skip if --force is used)
        if not args.force:
            print(f"\n⚠️  WARNING: This will overwrite the current database!")
            print(f"Restoring from: {backup_path}")
            confirm = input("Continue? [y/N]: ")

            if confirm.lower() != "y":
                print("Restore cancelled.")
                return 0

        success = restore_backup(config, backup_path)
        return 0 if success else 1

    # Create backup
    if not args.cron:
        print(f"\n{'='*60}")
        print("DMarket Bot - Database Backup")
        print(f"{'='*60}\n")

    backup_path = create_backup(config, compress=not args.no_compress)

    if backup_path:
        if not args.cron:
            size_mb = round(backup_path.stat().st_size / (1024 * 1024), 2)
            print(f"\n✅ Backup created successfully!")
            print(f"   File: {backup_path}")
            print(f"   Size: {size_mb} MB")

        # Auto-cleanup in cron mode
        if args.cron:
            cleanup_old_backups(args.keep)

        # Send notification if requested
        if args.notify or args.cron:
            await send_backup_notification(config, True, backup_path)

        return 0
    else:
        if args.notify or args.cron:
            await send_backup_notification(config, False, error="Backup creation failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

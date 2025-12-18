"""add_performance_indexes

Revision ID: fb67d208311d
Revises: fb05e6a3795a
Create Date: 2025-11-23 19:08:59.649204

"""

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "fb67d208311d"
down_revision: str | None = "fb05e6a3795a"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    This function applies schema changes to the database.
    Add detailed comments for complex operations.
    """
    # User-related composite indexes for common query patterns
    op.create_index(
        "idx_users_active_telegram",
        "users",
        ["is_active", "telegram_id"],
        unique=False,
    )
    op.create_index(
        "idx_users_banned_telegram",
        "users",
        ["is_banned", "telegram_id"],
        unique=False,
    )

    # User settings indexes
    op.create_index(
        "idx_user_settings_user_id",
        "user_settings",
        ["user_id"],
        unique=True,
    )

    # Command log composite indexes for analytics
    op.create_index(
        "idx_cmdlog_user_success",
        "command_log",
        ["user_id", "success"],
        unique=False,
    )
    op.create_index(
        "idx_cmdlog_command_date",
        "command_log",
        ["command", "created_at"],
        unique=False,
    )

    # Market data composite indexes for price history queries
    op.create_index(
        "idx_market_item_game_date",
        "market_data",
        ["item_name", "game", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_market_game_source",
        "market_data",
        ["game", "data_source"],
        unique=False,
    )

    # Market data cache indexes for expiration cleanup
    op.create_index(
        "idx_cache_game_expires",
        "market_data_cache",
        ["game", "expires_at"],
        unique=False,
    )
    op.create_index(
        "idx_cache_type_expires",
        "market_data_cache",
        ["data_type", "expires_at"],
        unique=False,
    )

    # Analytics events indexes
    op.create_index(
        "idx_events_user_type",
        "events",
        ["user_id", "event_type"],
        unique=False,
    )
    op.create_index(
        "idx_events_type_date",
        "events",
        ["event_type", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema.

    This function reverts schema changes from the upgrade.
    Ensure this is always the inverse of upgrade().
    """
    # Drop indexes in reverse order
    op.drop_index("idx_events_type_date", table_name="events")
    op.drop_index("idx_events_user_type", table_name="events")
    op.drop_index("idx_cache_type_expires", table_name="market_data_cache")
    op.drop_index("idx_cache_game_expires", table_name="market_data_cache")
    op.drop_index("idx_market_game_source", table_name="market_data")
    op.drop_index("idx_market_item_game_date", table_name="market_data")
    op.drop_index("idx_cmdlog_command_date", table_name="command_log")
    op.drop_index("idx_cmdlog_user_success", table_name="command_log")
    op.drop_index("idx_user_settings_user_id", table_name="user_settings")
    op.drop_index("idx_users_banned_telegram", table_name="users")
    op.drop_index("idx_users_active_telegram", table_name="users")

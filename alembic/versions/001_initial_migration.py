"""Initial migration - create all tables.

Revision ID: 001
Revises:
Create Date: 2025-11-15 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("language_code", sa.String(10), default="ru"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_admin", sa.Boolean, default=False),
        sa.Column("is_banned", sa.Boolean, default=False),
        sa.Column("dmarket_api_key_encrypted", sa.Text, nullable=True),
        sa.Column("dmarket_secret_key_encrypted", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("last_activity", sa.DateTime),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_banned", "users", ["is_banned"])

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("default_game", sa.String(50), default="csgo"),
        sa.Column("notification_enabled", sa.Boolean, default=True),
        sa.Column("price_alert_enabled", sa.Boolean, default=True),
        sa.Column("arbitrage_alert_enabled", sa.Boolean, default=True),
        sa.Column("min_profit_percent", sa.String(10), default="5.0"),
        sa.Column("preferred_currency", sa.String(10), default="USD"),
        sa.Column("timezone", sa.String(50), default="UTC"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])

    # Create price_alerts table
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("item_id", sa.String(255), nullable=True),
        sa.Column("market_hash_name", sa.String(500), nullable=False),
        sa.Column("game", sa.String(50), nullable=False),
        sa.Column("target_price", sa.String(20), nullable=False),
        sa.Column("condition", sa.String(20), default="below"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("triggered", sa.Boolean, default=False),
        sa.Column("triggered_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_price_alerts_user_id", "price_alerts", ["user_id"])
    op.create_index("ix_price_alerts_is_active", "price_alerts", ["is_active"])

    # Create targets table
    op.create_table(
        "targets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False, unique=True),
        sa.Column("game", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("amount", sa.Integer, default=1, nullable=False),
        sa.Column("status", sa.String(50), default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("attributes", sa.JSON, nullable=True),
    )
    op.create_index("ix_targets_user_id", "targets", ["user_id"])
    op.create_index("ix_targets_target_id", "targets", ["target_id"])
    op.create_index("ix_targets_game", "targets", ["game"])
    op.create_index("ix_targets_status", "targets", ["status"])

    # Create trade_history table
    op.create_table(
        "trade_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("trade_type", sa.String(50), nullable=False),
        sa.Column("item_title", sa.String(500), nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("profit", sa.Float, default=0.0),
        sa.Column("game", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
    )
    op.create_index("ix_trade_history_user_id", "trade_history", ["user_id"])
    op.create_index("ix_trade_history_status", "trade_history", ["status"])

    # Create trading_settings table
    op.create_table(
        "trading_settings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("max_trade_value", sa.Float, default=50.0),
        sa.Column("daily_limit", sa.Float, default=500.0),
        sa.Column("min_profit_percent", sa.Float, default=5.0),
        sa.Column("strategy", sa.String(50), default="balanced"),
        sa.Column("auto_trading_enabled", sa.Integer, default=0),
        sa.Column("games_enabled", sa.JSON),
        sa.Column("notifications_enabled", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_trading_settings_user_id", "trading_settings", ["user_id"])

    # Create market_data_cache table
    op.create_table(
        "market_data_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cache_key", sa.String(500), nullable=False, unique=True),
        sa.Column("game", sa.String(50), nullable=False),
        sa.Column("item_hash_name", sa.String(500), nullable=True),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_market_data_cache_key", "market_data_cache", ["cache_key"])
    op.create_index("ix_market_data_cache_game", "market_data_cache", ["game"])
    op.create_index(
        "ix_market_data_cache_expires",
        "market_data_cache",
        ["expires_at"],
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("market_data_cache")
    op.drop_table("trading_settings")
    op.drop_table("trade_history")
    op.drop_table("targets")
    op.drop_table("price_alerts")
    op.drop_table("user_preferences")
    op.drop_table("users")

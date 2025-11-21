"""Add scan_checkpoints table for state management

Revision ID: fb05e6a3795a
Revises: 001
Create Date: 2025-11-20 22:16:34.903665

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fb05e6a3795a"
down_revision: str | None = "001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    This function applies schema changes to the database.
    Add detailed comments for complex operations.
    """
    op.create_table(
        "scan_checkpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("processed_items", sa.Integer(), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id"),
    )
    op.create_index(
        op.f("ix_scan_checkpoints_scan_id"), "scan_checkpoints", ["scan_id"], unique=True
    )
    op.create_index(
        op.f("ix_scan_checkpoints_user_id"), "scan_checkpoints", ["user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade database schema.

    This function reverts schema changes from the upgrade.
    Ensure this is always the inverse of upgrade().
    """
    op.drop_index(op.f("ix_scan_checkpoints_user_id"), table_name="scan_checkpoints")
    op.drop_index(op.f("ix_scan_checkpoints_scan_id"), table_name="scan_checkpoints")
    op.drop_table("scan_checkpoints")

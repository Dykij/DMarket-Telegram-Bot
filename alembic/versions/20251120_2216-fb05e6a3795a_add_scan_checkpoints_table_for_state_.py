"""Add scan_checkpoints table for state management

Revision ID: fb05e6a3795a
Revises: 001
Create Date: 2025-11-20 22:16:34.903665

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb05e6a3795a'
down_revision: str | None = '001'
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    This function applies schema changes to the database.
    Add detailed comments for complex operations.
    """
    pass


def downgrade() -> None:
    """Downgrade database schema.

    This function reverts schema changes from the upgrade.
    Ensure this is always the inverse of upgrade().
    """
    pass

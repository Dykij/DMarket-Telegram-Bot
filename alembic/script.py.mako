"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | tuple[str, ...] | None = ${repr(branch_labels)}
depends_on: str | tuple[str, ...] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema.

    This function applies schema changes to the database.
    Add detailed comments for complex operations.
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade database schema.

    This function reverts schema changes from the upgrade.
    Ensure this is always the inverse of upgrade().
    """
    ${downgrades if downgrades else "pass"}

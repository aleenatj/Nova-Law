"""update_resolve_status_enum_draft_to_in_progress

Revision ID: 77c3350df6d
Revises: 093ab290a04a
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '77c3350df6d'
down_revision = '093ab290a04a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update existing data from 'Draft' to 'In progress'
    op.execute("ALTER TYPE resolve_status_enum RENAME VALUE 'Draft' TO 'In progress'")


def downgrade() -> None:
    # Update existing data from 'In progress' back to 'Draft'
    op.execute("ALTER TYPE resolve_status_enum RENAME VALUE 'In progress' TO 'Draft'")

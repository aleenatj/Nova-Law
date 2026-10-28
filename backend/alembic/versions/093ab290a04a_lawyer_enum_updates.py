"""lawyer enum updates

Revision ID: 093ab290a04a
Revises: cef3a8f2576f
Create Date: 2026-01-23 09:53:15.552221

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '093ab290a04a'
down_revision = 'cef3a8f2576f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Order matters: rename values that don't share prefixes first to avoid conflicts
    op.execute("ALTER TYPE expert_type_enum RENAME VALUE 'CILEx' TO 'Cilex'")
    op.execute("ALTER TYPE expert_type_enum RENAME VALUE 'barrister' TO 'Barrister'")
    op.execute("ALTER TYPE expert_type_enum RENAME VALUE 'solicitor' TO 'Solicitor'")


def downgrade() -> None:
    op.execute("ALTER TYPE expert_type_enum RENAME VALUE 'Solicitor' TO 'solicitor'")
    op.execute("ALTER TYPE expert_type_enum RENAME VALUE 'Barrister' TO 'barrister'")
    op.execute("ALTER TYPE expert_type_enum RENAME VALUE 'Cilex' TO 'CILEx'")

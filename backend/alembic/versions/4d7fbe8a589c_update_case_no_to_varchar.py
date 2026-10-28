"""update case_no to varchar

Revision ID: 4d7fbe8a589c
Revises: 1a2b3c4d5e6f
Create Date: 2025-11-28 15:00:17.666616

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4d7fbe8a589c'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: drop identity from the integer column
    op.execute('ALTER TABLE "case" ALTER COLUMN case_no DROP IDENTITY IF EXISTS')

    # Step 2: convert integer → varchar and make it unique
    op.alter_column(
        'case',
        'case_no',
        existing_type=sa.INTEGER(),
        type_=sa.String(length=15),
        existing_nullable=False
    )

    # Step 3: add unique index
    op.create_index(op.f('ix_case_case_no'), 'case', ['case_no'], unique=True)

def downgrade() -> None:
    pass

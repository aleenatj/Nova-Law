"""add_kyc_complete_to_engage_table

Revision ID: a2add8b0f40d
Revises: fe3e14170b09
Create Date: 2025-10-14 14:45:27.904903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2add8b0f40d'
down_revision = 'fe3e14170b09'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('engage', sa.Column('is_kyc_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('engage', 'is_kyc_completed')

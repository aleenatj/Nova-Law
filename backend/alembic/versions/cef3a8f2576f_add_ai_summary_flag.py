"""add ai summary flag

Revision ID: cef3a8f2576f
Revises: 539d8e8491f7
Create Date: 2026-01-19 16:19:08.935867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cef3a8f2576f'
down_revision = '539d8e8491f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('case', sa.Column('is_ai_summary_generated', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('case', 'is_ai_summary_generated')

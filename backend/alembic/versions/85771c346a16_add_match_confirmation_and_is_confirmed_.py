"""add match_confirmation and is_confirmed boolean fields

Revision ID: 85771c346a16
Revises: 17d35431e4fd
Create Date: 2025-09-01 17:13:49.161573

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '85771c346a16'
down_revision = '17d35431e4fd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('case', sa.Column('is_match_confirmed', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('match', sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('case', 'is_match_confirmed')
    op.drop_column('match', 'is_confirmed')

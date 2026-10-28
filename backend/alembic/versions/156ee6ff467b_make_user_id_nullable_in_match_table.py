"""Make user_id nullable in match table

Revision ID: 156ee6ff467b
Revises: d0b5b04d0bd4
Create Date: 2025-09-11 12:16:20.516922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '156ee6ff467b'
down_revision = 'd0b5b04d0bd4'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('match', 'user_id',
        existing_type=sa.Integer(),
        nullable=True
    )

def downgrade():
    op.alter_column('match', 'user_id',
        existing_type=sa.Integer(),
        nullable=False
    )

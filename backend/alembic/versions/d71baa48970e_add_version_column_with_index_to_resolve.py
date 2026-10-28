"""Add version column with index to resolve

Revision ID: d71baa48970e
Revises: 8f22d64bd034
Create Date: 2025-08-11 17:41:43.576808

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd71baa48970e'
down_revision = '8f22d64bd034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resolve', sa.Column('result_version', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_resolve_result_version'), 'resolve', ['result_version'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resolve_result_version'), table_name='resolve')
    op.drop_column('resolve', 'result_version')

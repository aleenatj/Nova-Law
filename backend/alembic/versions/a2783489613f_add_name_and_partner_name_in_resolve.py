"""add_name and partner name in resolve

Revision ID: a2783489613f
Revises: 5914b133849f
Create Date: 2025-09-23 15:28:22.847956

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2783489613f'
down_revision = '5914b133849f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resolve', sa.Column('customer_name', sa.String(length=100), nullable=True))
    op.add_column('resolve', sa.Column('partner_name', sa.String(length=100), nullable=True))
    op.add_column('resolve', sa.Column('customer_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('resolve', 'customer_name')
    op.drop_column('resolve', 'partner_name')
    op.drop_column('resolve', 'customer_email')

"""lawyer country

Revision ID: 5914b133849f
Revises: bc7efd6d5b6f
Create Date: 2025-09-19 15:11:53.677494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5914b133849f'
down_revision = 'bc7efd6d5b6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lawyer', sa.Column('country', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('lawyer', 'country')

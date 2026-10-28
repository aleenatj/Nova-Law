"""resolve_name_length_increase

Revision ID: 65fdc1dc51b6
Revises: cfad85f0c5bf
Create Date: 2026-02-27 13:49:58.603386

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '65fdc1dc51b6'
down_revision = 'cfad85f0c5bf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'resolve',
        'customer_name',
        existing_type=sa.String(length=100),
        type_=sa.String(length=250),
        existing_nullable=True,
    )
    op.alter_column(
        'resolve',
        'partner_name',
        existing_type=sa.String(length=100),
        type_=sa.String(length=250),
        existing_nullable=True,
    )


def downgrade() -> None:
    pass

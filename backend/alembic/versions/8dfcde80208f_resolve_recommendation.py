"""resolve recommendation

Revision ID: 8dfcde80208f
Revises: 65fdc1dc51b6
Create Date: 2026-05-26 13:58:01.083394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8dfcde80208f'
down_revision = 'cac3775c68eb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'resolve',
        sa.Column('recommended_approach', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'resolve',
        sa.Column('personalised_ai_recommendation', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('resolve', 'personalised_ai_recommendation')
    op.drop_column('resolve', 'recommended_approach')

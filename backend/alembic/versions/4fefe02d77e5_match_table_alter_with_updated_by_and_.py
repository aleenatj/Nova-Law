"""match table alter with updated by and date

Revision ID: 4fefe02d77e5
Revises: 85771c346a16
Create Date: 2025-09-03 19:00:23.036115

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fefe02d77e5'
down_revision = '85771c346a16'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('match',
        sa.Column('confirmed_by', sa.Integer(), nullable=True)
    )
    op.add_column('match',
        sa.Column('confirmed_date', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_match_confirmed_by_user',      # Name for the constraint
        'match',                           # Source table
        'user',                            # Target table
        ['confirmed_by'],                  # Source columns
        ['id']                             # Target columns
    )


def downgrade() -> None:
    op.drop_constraint('fk_match_confirmed_by_user', 'match', type_='foreignkey')
    op.drop_column('match', 'confirmed_date')
    op.drop_column('match', 'confirmed_by') 

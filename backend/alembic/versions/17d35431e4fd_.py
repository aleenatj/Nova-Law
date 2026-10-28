"""empty message

Revision ID: 17d35431e4fd
Revises: add_law_firm_fields_correct, ff301f5ddd61
Create Date: 2025-08-28 18:09:28.550631

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17d35431e4fd'
down_revision = ('add_law_firm_fields_correct', 'ff301f5ddd61')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 

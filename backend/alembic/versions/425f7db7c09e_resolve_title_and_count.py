"""resolve-title and count

Revision ID: 425f7db7c09e
Revises: b98f9b5c5701
Create Date: 2025-09-08 14:13:35.376726

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '425f7db7c09e'
down_revision = 'b98f9b5c5701'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('resolve', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('resolve', sa.Column('questions_answered', sa.Integer(), nullable=True, default=0, server_default='0'))


def downgrade() -> None:
    op.drop_column('resolve', 'questions_answered')
    op.drop_column('resolve', 'title')

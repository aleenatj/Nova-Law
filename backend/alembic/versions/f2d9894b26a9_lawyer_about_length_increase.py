"""lawyer about length increase

Revision ID: f2d9894b26a9
Revises: 82d360c4a78c
Create Date: 2025-10-23 17:52:23.532312

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f2d9894b26a9'
down_revision = '82d360c4a78c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('lawyer', 'about',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Text(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('lawyer', 'about',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

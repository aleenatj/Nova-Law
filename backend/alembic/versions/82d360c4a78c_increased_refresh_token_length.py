"""Increased refresh_token length

Revision ID: 82d360c4a78c
Revises: 410c60274a06
Create Date: 2025-10-21 10:23:06.399426

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '82d360c4a78c'
down_revision = '410c60274a06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('refresh_tokens', 'refresh_token',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=1000),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('refresh_tokens', 'refresh_token',
               existing_type=sa.String(length=1000),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)

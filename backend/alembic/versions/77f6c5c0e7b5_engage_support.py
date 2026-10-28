"""Engage support

Revision ID: 77f6c5c0e7b5
Revises: b255671cbbc5
Create Date: 2026-06-23 14:04:23.256890

Engage support form table. Option columns store integer keys (1, 2, 3, ...);
option labels are defined in application code, not as DB enums.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77f6c5c0e7b5'
down_revision = 'b255671cbbc5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'engage_support',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('how_can_help', sa.Integer(), nullable=True),
        sa.Column('trouble_with_any', sa.Integer(), nullable=True),
        sa.Column('trouble_navigating_engage', sa.Integer(), nullable=True),
        sa.Column('section_stuck_on', sa.Integer(), nullable=True),
        sa.Column('issues_listed', sa.Integer(), nullable=True),
        sa.Column('new_lawfirm', sa.String(length=255), nullable=True),
        sa.Column('helped_resolve_issue', sa.Integer(), nullable=True),
        sa.Column('support_query_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('engage_support')

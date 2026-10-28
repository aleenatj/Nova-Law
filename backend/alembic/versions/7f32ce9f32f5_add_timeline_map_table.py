"""add timeline_map table

Revision ID: 7f32ce9f32f5
Revises: 031717a0a6fc
Create Date: 2025-09-30 15:07:37.402407

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f32ce9f32f5'
down_revision = '031717a0a6fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'timeline_map',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column('timeline_event_id', sa.Integer(), sa.ForeignKey('timeline_event.id'), nullable=False),
        sa.Column('timeline_type', sa.String(length=100), nullable=False),
        sa.Column('related_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('timeline_map')

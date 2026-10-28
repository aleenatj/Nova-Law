"""Add case_lawyer, timeline_event and timeline_type tables

Revision ID: 736ca6af31db
Revises: 71f4cffbd38c
Create Date: 2025-08-20 11:52:49.994088

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '736ca6af31db'
down_revision = '71f4cffbd38c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'timeline_type',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True, unique=True),
        sa.Column('type_name', sa.String(length=150), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('role_code', sa.String(length=25), nullable=False),
    )
    op.create_table(
        'timeline_event',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True, unique=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('case.id'), nullable=False),
        sa.Column('timeline_type_id', sa.Integer(), sa.ForeignKey('timeline_type.id'), nullable=False),
        sa.Column('action_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('notify_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('meta_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_table(
        'case_lawyer',
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('case.id'), primary_key=True, index=True),
        sa.Column('lawyer_id', sa.Integer(), sa.ForeignKey('lawyer.id'), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('timeline_event')
    op.drop_table('timeline_type')
    op.drop_table('case_lawyer')

"""add_engage_feedback_table

Revision ID: 7c9a71aa75c8
Revises: eb91c0359337
Create Date: 2026-02-05 10:35:11.520512

Engage feedback form table. All option columns store integer keys (1, 2, 3, ...);
option labels are defined in application code, not as DB enums.
Multi-select fields (helper_type, help_reason) store JSON key-value with integer keys.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7c9a71aa75c8'
down_revision = 'eb91c0359337'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'engage_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column('time_value_feedback', sa.Integer(), nullable=True),
        sa.Column('completion_time', sa.Integer(), nullable=True),
        sa.Column('session_count', sa.Integer(), nullable=True),
        sa.Column('help_level', sa.Integer(), nullable=True),
        sa.Column('helper_type', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('help_reason', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preparedness_level', sa.Integer(), nullable=True),
        sa.Column('age_range', sa.Integer(), nullable=True),
        sa.Column('gender', sa.Integer(), nullable=True),
        sa.Column('gender_other', sa.String(length=255), nullable=True),
        sa.Column('overall_experience', sa.Integer(), nullable=True),
        sa.Column('improvement_feedback', sa.Text(), nullable=True),
        sa.Column('recommendation_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('engage_feedback') 

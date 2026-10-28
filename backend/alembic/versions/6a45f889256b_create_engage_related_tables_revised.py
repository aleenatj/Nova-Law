"""create engage related tables revised

Revision ID: 6a45f889256b
Revises: 0e920ae4be19
Create Date: 2025-08-26 11:40:16.187853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a45f889256b'
down_revision = '0e920ae4be19'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create "engage" table
    op.create_table(
        'engage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create "case_engage" table
    op.create_table(
        'case_engage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('case.id'), nullable=False),
        sa.Column('engage_id', sa.Integer(), sa.ForeignKey('engage.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create "engage_question_answers" table
    op.create_table(
        'engage_question_answers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column('engage_id', sa.Integer(), sa.ForeignKey('engage.id'), nullable=False),
        sa.Column('question_answer_id', sa.Integer(), sa.ForeignKey('question_answers.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # Drop in reverse order to avoid dependency issues
    op.drop_table('engage_question_answers')
    op.drop_table('case_engage')
    op.drop_table('engage')

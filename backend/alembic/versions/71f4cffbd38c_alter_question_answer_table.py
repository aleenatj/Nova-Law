"""Alter question-answer table

Revision ID: 71f4cffbd38c
Revises: d71baa48970e
Create Date: 2025-08-13 15:04:01.287476

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '71f4cffbd38c'
down_revision = 'd71baa48970e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop constraint related to 'question' column
    op.drop_constraint('question_answers_question_key', 'question_answers', type_='unique')
    # Drop the 'question' column
    op.drop_column('question_answers', 'question')
    # Change 'version' column to String(20)
    op.alter_column('question_answers', 'version',
                    type_=sa.String(20),
                    existing_type=sa.String(50),
                    nullable=True)
    # Change 'answer' column to Text
    op.alter_column('question_answers', 'answer',
                    type_=sa.Text(),
                    existing_type=sa.String(1000),
                    nullable=True)


def downgrade() -> None:
    # Add the 'question' column back
    op.add_column('question_answers', sa.Column('question', sa.String(500), nullable=False))
    # Restore the unique constraint
    op.create_unique_constraint('question_answers_question_key', 'question_answers', ['question'])
    # Revert 'version' column to String(50)
    op.alter_column('question_answers', 'version',
                    type_=sa.String(50),
                    existing_type=sa.String(20),
                    nullable=True)
    # Revert 'answer' column to String(1000)
    op.alter_column('question_answers', 'answer',
                    type_=sa.String(1000),
                    existing_type=sa.Text(),
                    nullable=True)

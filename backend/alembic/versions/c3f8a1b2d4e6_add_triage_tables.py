"""add triage, case_triage and triage_question_answers tables

Revision ID: c3f8a1b2d4e6
Revises: 32b2fe3fea5b
Create Date: 2026-08-14 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f8a1b2d4e6'
down_revision = '32b2fe3fea5b'
branch_labels = None
depends_on = None


TIMELINE_TYPES = [
    ("triage_submitted", 1, "Customer"),
    ("triage_submitted", 1, "Navigator"),
]


def upgrade() -> None:
    op.add_column(
        'case',
        sa.Column('is_triage', sa.Boolean(), server_default='false', nullable=False),
    )

    op.create_table(
        'triage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column(
            'status',
            sa.Enum('In progress', 'Completed', name='triage_status_enum'),
            nullable=True,
            server_default='In progress',
        ),
        sa.Column('questions_answered', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_triage_id'), 'triage', ['id'], unique=False)

    op.create_table(
        'case_triage',
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('triage_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['case.id']),
        sa.ForeignKeyConstraint(['triage_id'], ['triage.id']),
        sa.PrimaryKeyConstraint('case_id', 'triage_id'),
    )

    op.create_table(
        'triage_question_answers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('triage_id', sa.Integer(), nullable=False),
        sa.Column('question_answer_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_answer_id'], ['question_answers.id']),
        sa.ForeignKeyConstraint(['triage_id'], ['triage.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_triage_question_answers_id'), 'triage_question_answers', ['id'], unique=False)

    insert_sql = sa.text(
        """
        INSERT INTO timeline_type (type_name, version, role_code)
        SELECT :type_name, :version, :role_code
        WHERE NOT EXISTS (
            SELECT 1
            FROM timeline_type
            WHERE type_name = :type_name
              AND version = :version
              AND role_code = :role_code
        )
        """
    )

    for type_name, version, role_code in TIMELINE_TYPES:
        op.execute(
            insert_sql.bindparams(
                type_name=type_name,
                version=version,
                role_code=role_code,
            )
        )


def downgrade() -> None:
    delete_sql = sa.text(
        """
        DELETE FROM timeline_type
        WHERE type_name = :type_name
          AND version = :version
          AND role_code = :role_code
        """
    )

    for type_name, version, role_code in TIMELINE_TYPES:
        op.execute(
            delete_sql.bindparams(
                type_name=type_name,
                version=version,
                role_code=role_code,
            )
        )

    op.drop_index(op.f('ix_triage_question_answers_id'), table_name='triage_question_answers')
    op.drop_table('triage_question_answers')
    op.drop_table('case_triage')
    op.drop_index(op.f('ix_triage_id'), table_name='triage')
    op.drop_table('triage')
    op.drop_column('case', 'is_triage')
    op.execute('DROP TYPE IF EXISTS triage_status_enum')

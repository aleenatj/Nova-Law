"""engage b2b registration case open timeline type

Revision ID: 32b2fe3fea5b
Revises: d205cf4733bf
Create Date: 2026-08-03 15:05:33.816348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32b2fe3fea5b'
down_revision = 'd205cf4733bf'
branch_labels = None
depends_on = None

TIMELINE_TYPES = [
    ("case_open_b2b", 1, "Navigator"),
    ("case_open_b2b", 1, "Customer"),
]


def upgrade() -> None:
    op.create_table(
        'lawfirm_engage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column('lawfirm_id', sa.Integer(), sa.ForeignKey('law_firm.id'), nullable=False),
        sa.Column('engage_id', sa.Integer(), sa.ForeignKey('engage.id'), nullable=False),
        sa.Column('status', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

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

    op.drop_table('lawfirm_engage')
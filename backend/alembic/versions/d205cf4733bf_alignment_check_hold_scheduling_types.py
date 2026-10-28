"""alignment check hold, scheduling types

Revision ID: d205cf4733bf
Revises: 77f6c5c0e7b5
Create Date: 2026-07-17 10:32:10.339757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd205cf4733bf'
down_revision = '77f6c5c0e7b5'
branch_labels = None
depends_on = None


TIMELINE_TYPES = [
    ("customer_kyc_hold", 1, "Navigator"),
    ("customer_kyc_hold", 1, "Customer"),
    ("book_free_call", 1, "Navigator"),
    ("book_free_call", 1, "Customer"),
]


def upgrade() -> None:
    op.add_column(
        'case',
        sa.Column('is_alignment_check_hold', sa.Boolean(), server_default='false', nullable=False),
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

    op.drop_column('case', 'is_alignment_check_hold')

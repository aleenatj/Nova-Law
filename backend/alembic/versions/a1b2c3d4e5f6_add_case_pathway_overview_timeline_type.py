"""add case_pathway_overview and customer_kyc_submitted timeline types

Revision ID: a1b2c3d4e5f6
Revises: d6d6a73f1469
Create Date: 2025-12-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d6d6a73f1469"
branch_labels = None
depends_on = None


# Timeline types to add
TIMELINE_TYPES = [
    ("case_pathway_overview", 1, "Customer"),
    ("customer_kyc_submitted", 1, "Customer"),
]


def upgrade() -> None:
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

"""add case_awarded_to_other_lawyer timeline type


Revision ID: d5b7c6b0ab12
Revises: cb91d6a98904
Create Date: 2025-10-31 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d5b7c6b0ab12"
down_revision = "cb91d6a98904"
branch_labels = None
depends_on = None


TYPE_NAME = "case_awarded_to_other_lawyer"
VERSION = 1
ROLE_CODE = "Lawyer"


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

    op.execute(
        insert_sql.bindparams(
            type_name=TYPE_NAME,
            version=VERSION,
            role_code=ROLE_CODE,
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

    op.execute(
        delete_sql.bindparams(
            type_name=TYPE_NAME,
            version=VERSION,
            role_code=ROLE_CODE,
        )
    )


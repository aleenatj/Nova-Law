"""add case_archived timeline type

Revision ID: c8e342d1545a
Revises: 5985c24a0e35
Create Date: 2025-12-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c8e342d1545a"
down_revision = "5985c24a0e35"
branch_labels = None
depends_on = None


TYPE_NAME = "case_archived"
VERSION = 1
ROLE_CODE = "Navigator"


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


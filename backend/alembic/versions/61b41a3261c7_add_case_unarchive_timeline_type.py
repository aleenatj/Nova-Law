"""add case unarchive timeline type

Revision ID: 61b41a3261c7
Revises: cac3775c68eb
Create Date: 2026-05-27 13:49:15.180575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '61b41a3261c7'
down_revision = 'cac3775c68eb'
branch_labels = None
depends_on = None

TYPE_NAME = "case_unarchived"
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

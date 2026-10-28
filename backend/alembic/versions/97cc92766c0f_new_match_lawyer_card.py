"""new match lawyer card

Revision ID: 97cc92766c0f
Revises: d9d44e3f057c
Create Date: 2026-01-02 12:17:03.391926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97cc92766c0f'
down_revision = 'd9d44e3f057c'
branch_labels = None
depends_on = None

TYPE_NAME = "new_match"
VERSION = 1
ROLE_CODE = "Lawyer"

def upgrade() -> None:

    # Insert timeline_type for case summary updates
    op.execute(
        sa.text(
            "INSERT INTO timeline_type (type_name, version, role_code) "
            "VALUES (:type_name, :version, :role_code)"
        ).bindparams(
            type_name=TYPE_NAME,
            version=VERSION,
            role_code=ROLE_CODE,
        )
    )


def downgrade() -> None:
    # Delete timeline_type record
    op.execute(
        "DELETE FROM timeline_type WHERE type_name = 'new_match'"
    )

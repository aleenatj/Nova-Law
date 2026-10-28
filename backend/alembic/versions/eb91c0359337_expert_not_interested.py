"""expert not interested

Revision ID: eb91c0359337
Revises: 77c3350df6d
Create Date: 2026-02-03 17:31:17.896396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb91c0359337'
down_revision = '77c3350df6d'
branch_labels = None
depends_on = None

TYPE_NAME = "expert_not_interested"
VERSION = 1
ROLE_CODE = "Navigator"


def upgrade() -> None:
    # Insert timeline_type for expert not interested
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

    # Add is_no_interest_notified column to case table
    op.add_column('case', sa.Column('is_no_interest_notified', sa.Boolean(), server_default='false', nullable=False))

    # Add match_confirmed_at column to case table
    op.add_column('case', sa.Column('match_confirmed_at', sa.DateTime(timezone=True), server_default=None, nullable=True))

    # Update is_no_interest_notified flag to true
    op.execute(
        'UPDATE "case" SET is_no_interest_notified = true'
    )

def downgrade() -> None:
    # Drop profile_card_sent_at column from case table
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

    # Drop is_no_interest_notified column from case table
    op.drop_column('case', 'is_no_interest_notified')

    # Drop match_confirmed_at column from case table
    op.drop_column('case', 'match_confirmed_at')

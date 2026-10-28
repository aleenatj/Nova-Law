"""Change question_identifier to string

Revision ID: 539d8e8491f7
Revises: 97cc92766c0f
Create Date: 2026-01-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '539d8e8491f7'
down_revision = '97cc92766c0f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert existing float values to string before changing column type
    # This handles any existing data by converting it to string representation
    op.execute(
        sa.text(
            "ALTER TABLE question_answers "
            "ALTER COLUMN question_identifier TYPE VARCHAR(30) "
            "USING question_identifier::text"
        )
    )


def downgrade() -> None:
    # Convert back to float, but this may fail if non-numeric strings exist
    # Only numeric strings can be converted back
    op.execute(
        sa.text(
            "ALTER TABLE question_answers "
            "ALTER COLUMN question_identifier TYPE DOUBLE PRECISION "
            "USING question_identifier::double precision"
        )
    )


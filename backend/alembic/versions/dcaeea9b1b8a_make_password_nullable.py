"""make_password_nullable

Revision ID: dcaeea9b1b8a
Revises: f3975fcd8d6f
Create Date: 2025-08-19 18:46:43.524131

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'dcaeea9b1b8a'
down_revision = 'f3975fcd8d6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make password column nullable and set default to NULL
    op.alter_column('user', 'password',
                    existing_type=sa.String(length=255),
                    nullable=True,
                    server_default=None)


def downgrade() -> None:
    # Revert password column to not nullable
    op.alter_column('user', 'password',
                    existing_type=sa.String(length=255),
                    nullable=False,
                    server_default='')

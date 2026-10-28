"""increase phone number length

Revision ID: 7761f2d817bb
Revises: 93172876ffa4
Create Date: 2025-10-10 13:40:54.181033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7761f2d817bb'
down_revision = '93172876ffa4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Increase phone column lengths from 15 to 20 characters."""
    
    # Increase user.phone column length from 15 to 20
    op.alter_column(
        'user',
        'phone',
        existing_type=sa.String(length=15),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
    
    # Increase law_firm.contact_no column length from 15 to 20
    op.alter_column(
        'law_firm',
        'contact_no',
        existing_type=sa.String(length=15),
        type_=sa.String(length=20),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Revert phone column lengths from 20 to 15 characters."""
    
    # Revert user.phone column length from 20 to 15
    op.alter_column(
        'user',
        'phone',
        existing_type=sa.String(length=20),
        type_=sa.String(length=15),
        existing_nullable=True,
    )
    
    # Revert law_firm.contact_no column length from 20 to 15
    op.alter_column(
        'law_firm',
        'contact_no',
        existing_type=sa.String(length=20),
        type_=sa.String(length=15),
        existing_nullable=True,
    )
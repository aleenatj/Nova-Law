"""case type in resolve

Revision ID: 05e8b11232bc
Revises: 425f7db7c09e
Create Date: 2025-09-08 21:21:04.784234

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '05e8b11232bc'
down_revision = '425f7db7c09e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resolve', sa.Column('case_type', sa.Enum('FAMILY_LAW', name='case_type_new_enum'), server_default='FAMILY_LAW', nullable=True))


def downgrade() -> None:
    op.drop_column('resolve', 'case_type')

"""add_case_status_flags

Revision ID: 410c60274a06
Revises: a2add8b0f40d
Create Date: 2025-10-17 13:14:16.443626

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '410c60274a06'
down_revision = 'a2add8b0f40d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add boolean status fields to case table
    op.add_column("case", sa.Column("is_kyc_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("case", sa.Column("is_onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("case", sa.Column("is_initial_payment_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("case", sa.Column("is_lawyer_assigned", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("case", sa.Column("total_paid_amount", sa.Float(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    # Remove boolean status fields from case table
    op.drop_column("case", "is_lawyer_assigned")
    op.drop_column("case", "is_initial_payment_completed")
    op.drop_column("case", "is_onboarding_completed")
    op.drop_column("case", "is_kyc_completed")
    op.drop_column("case", "total_paid_amount")
"""add status to law_firm and financial_claims_exemptions to lawyer

Revision ID: 93172876ffa4
Revises: 2f6c063ff23d
Create Date: 2025-10-08 18:34:29.880724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93172876ffa4'
down_revision = '2f6c063ff23d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    law_firm_status_enum = sa.Enum('ACTIVE', 'INACTIVE', name='law_firm_status_enum')
    law_firm_status_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('law_firm', sa.Column('status', law_firm_status_enum, nullable=False, server_default='ACTIVE'))
    op.add_column("lawyer", sa.Column("financial_claims_exemptions",sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("resolve", sa.Column("finance_flag", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('law_firm', 'status')
    op.drop_column("lawyer", "financial_claims_exemptions")
    op.drop_column("resolve", "finance_flag")
    op.execute("DROP TYPE IF EXISTS law_firm_status_enum")

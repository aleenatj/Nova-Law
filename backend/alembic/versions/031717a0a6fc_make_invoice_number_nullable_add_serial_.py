"""Make invoice_number nullable, add serial_number

Revision ID: 031717a0a6fc
Revises: 5808f189157d
Create Date: 2025-09-26 13:41:40.935958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031717a0a6fc'
down_revision = '5808f189157d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('invoice', 'invoice_number',
    existing_type=sa.String(length=50),
    nullable=True)
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS invoice_serial_number_seq MINVALUE 0 START 0"))
    op.add_column('invoice',
        sa.Column('serial_number', sa.Integer(),
                server_default=sa.text("nextval('invoice_serial_number_seq')"),
                nullable=False)
    )


def downgrade() -> None:
    op.alter_column('invoice', 'invoice_number',
    existing_type=sa.String(length=50),
    nullable=False)
    op.drop_column('invoice', 'serial_number')
    op.execute(sa.text("DROP SEQUENCE IF EXISTS invoice_serial_number_seq"))

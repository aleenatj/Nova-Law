"""add invoice, payment, invoice_payment tables

Revision ID: a3fd02bf3598
Revises: 5914b133849f
Create Date: 2025-09-24 12:24:35.217575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3fd02bf3598'
down_revision = '5914b133849f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create invoice table
    op.create_table(
        'invoice',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('case.id'), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), sa.ForeignKey('lawyer.id'), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('invoice_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PARTIALLY_PAID', 'COMPLETED', 'CANCELLED', name='invoice_status_enum'), nullable=False, server_default='PENDING'),
        sa.Column('remarks', sa.String(length=250), nullable=True),
        sa.Column('action_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.func.now()),
    )

    # Create payment table
    op.create_table(
        'payment',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('transaction_id', sa.String(length=50), nullable=True),
        sa.Column('payment_intent_id', sa.String(length=50), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('amount_paid', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'CANCELLED', name='payment_status_enum'), nullable=False, server_default='PENDING'),
        sa.Column('remarks', sa.String(length=250), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.func.now()), 
    )

    # Create invoice_payment table
    op.create_table(
        'invoice_payment',
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('payment.id'), primary_key=True, nullable=False),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoice.id'), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'),onupdate=sa.func.now()),
    )

def downgrade():
    op.drop_table('invoice_payment')
    op.drop_table('payment')
    op.drop_table('invoice')
    op.execute('DROP TYPE IF EXISTS invoice_status_enum')
    op.execute('DROP TYPE IF EXISTS payment_status_enum')
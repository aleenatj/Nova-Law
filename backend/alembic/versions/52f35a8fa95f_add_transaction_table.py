"""add transaction table

Revision ID: 52f35a8fa95f
Revises: f2d9894b26a9
Create Date: 2025-10-24 16:17:12.333064

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = '52f35a8fa95f'
down_revision = 'f2d9894b26a9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'transaction',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('payment.id'), nullable=False),
        sa.Column('transaction_id', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.String(length=250), nullable=True),
        sa.Column(
            'status',
            ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'CANCELLED', 
                 name='payment_status_enum', create_type=False),
            nullable=False,
            server_default='PENDING'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    

def downgrade():
    op.drop_table('transaction')
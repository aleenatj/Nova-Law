"""Add audit_log table

Revision ID: 1a343f6a07e9
Revises: a1b2c3d4e5f6
Create Date: 2025-12-16 12:22:56.934568

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, JSONB

# revision identifiers, used by Alembic.
revision = '1a343f6a07e9'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


# Create enum type
audit_action_enum = ENUM('CREATE', 'UPDATE', 'DELETE', name='audit_action_enum', create_type=False)


def upgrade():
    # Create the enum type first
    audit_action_enum.create(op.get_bind(), checkfirst=True)
    
    # Create the audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column('table_name', sa.String(length=100), nullable=False, index=True),
        sa.Column('record_id', sa.Integer(), nullable=False, index=True),
        sa.Column('action', audit_action_enum, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('old_values', JSONB, nullable=True),
        sa.Column('new_values', JSONB, nullable=True),
        sa.Column('changed_fields', JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, index=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('extra_metadata', JSONB, nullable=True),
    )
    
    # Create composite indexes for common query patterns
    op.create_index('ix_audit_log_table_record', 'audit_log', ['table_name', 'record_id'])
    op.create_index('ix_audit_log_user_timestamp', 'audit_log', ['user_id', 'timestamp'])
    op.create_index('ix_audit_log_table_timestamp', 'audit_log', ['table_name', 'timestamp'])


def downgrade():
    # Drop indexes first
    op.drop_index('ix_audit_log_table_timestamp', table_name='audit_log')
    op.drop_index('ix_audit_log_user_timestamp', table_name='audit_log')
    op.drop_index('ix_audit_log_table_record', table_name='audit_log')
    
    # Drop the table
    op.drop_table('audit_log')
    
    # Drop the enum type
    audit_action_enum.drop(op.get_bind(), checkfirst=True)

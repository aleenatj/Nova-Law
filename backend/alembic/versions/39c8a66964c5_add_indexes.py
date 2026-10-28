"""add indexes

Revision ID: 39c8a66964c5
Revises: d0b5b04d0bd4
Create Date: 2025-09-09 20:02:03.196474

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '39c8a66964c5'
down_revision = 'd0b5b04d0bd4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    
    # Add indexes for case_resolve table  
    op.create_index('ix_case_resolve_case_id', 'case_resolve', ['case_id'])
    op.create_index('ix_case_resolve_resolve_id', 'case_resolve', ['resolve_id'])
    
    # Add indexes for match table
    op.create_index('ix_match_lawyer_id', 'match', ['lawyer_id'])
    op.create_index('ix_match_case_id', 'match', ['case_id'])
    op.create_index('ix_match_user_id', 'match', ['user_id'])
    
    # Add indexes for resolve table
    op.create_index('ix_resolve_customer_id', 'resolve', ['customer_id'])
    op.create_index('ix_resolve_user_id', 'resolve', ['user_id'])
    op.create_index('ix_resolve_status', 'resolve', ['status'])
    op.create_index('ix_resolve_created_at', 'resolve', ['created_at'])
    
    # Add indexes for user_role table (missing indexes for foreign keys)
    op.create_index('ix_user_role_user_id', 'user_role', ['user_id'])
    op.create_index('ix_user_role_role_id', 'user_role', ['role_id'])
    
    # Add indexes for user table (status is commonly filtered)
    op.create_index('ix_user_status', 'user', ['status'])
    
    # Add indexes for customer table (user_id is commonly joined)
    op.create_index('ix_customer_user_id', 'customer', ['user_id'])
    
    # Add indexes for lawyer table (user_id is commonly joined)
    op.create_index('ix_lawyer_user_id', 'lawyer', ['user_id'])
    
    op.execute("UPDATE \"user\" SET updated_at = NOW() WHERE updated_at IS NULL;")
    op.alter_column('user', 'updated_at', server_default=sa.text('now()'), existing_type=sa.DateTime(timezone=True), nullable=False)
    
    op.create_index('ix_user_refresh_token', 'user', ['refresh_token'])
    op.create_index('ix_customer_status', 'customer', ['status'])
    op.create_index('ix_lawyer_status', 'lawyer', ['status'])     
    
def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_lawyer_user_id', table_name='lawyer')
    op.drop_index('ix_customer_user_id', table_name='customer')
    op.drop_index('ix_user_status', table_name='user')
    op.drop_index('ix_user_role_role_id', table_name='user_role')
    op.drop_index('ix_user_role_user_id', table_name='user_role')
    
    op.drop_index('ix_resolve_created_at', table_name='resolve')
    op.drop_index('ix_resolve_status', table_name='resolve')
    op.drop_index('ix_resolve_user_id', table_name='resolve')
    op.drop_index('ix_resolve_customer_id', table_name='resolve')
    
    op.drop_index('ix_match_user_id', table_name='match')
    op.drop_index('ix_match_case_id', table_name='match')
    op.drop_index('ix_match_lawyer_id', table_name='match')
    
    op.drop_index('ix_case_resolve_resolve_id', table_name='case_resolve')
    op.drop_index('ix_case_resolve_case_id', table_name='case_resolve')

    
    op.alter_column('user', 'updated_at', server_default=None, existing_type=sa.DateTime(timezone=True), nullable=True)
    op.drop_index('ix_user_refresh_token', table_name='user')
    op.drop_index('ix_lawyer_status', table_name='lawyer')
    op.drop_index('ix_customer_status', table_name='customer')  
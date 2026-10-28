"""add_websocket_connections_table

Revision ID: 89c268cb5a61
Revises: a2783489613f
Create Date: 2025-09-29 11:40:22.506141

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89c268cb5a61'
down_revision = 'a2783489613f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create websocket_connections table
    op.create_table(
        'websocket_connections',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_code', sa.String(30), nullable=False),
        sa.Column('connection_id', sa.String(100), nullable=False),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(timezone=True), onupdate=sa.func.now(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'connection_id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for better performance
    op.create_index('ix_websocket_connections_user_id', 'websocket_connections', ['user_id'])
    op.create_index('ix_websocket_connections_connection_id', 'websocket_connections', ['connection_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_websocket_connections_connection_id', table_name='websocket_connections')
    op.drop_index('ix_websocket_connections_user_id', table_name='websocket_connections')
    
    # Drop the table
    op.drop_table('websocket_connections')

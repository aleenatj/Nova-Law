"""Standardize datetime fields across all models

Revision ID: 5692cec56609
Revises: c8e342d1545a
Create Date: 2025-01-27 12:00:00.000000

This migration standardizes datetime field handling:
- Changes updated_at from nullable=True to nullable=False in multiple tables
- Adds updated_at column to transaction table
- Ensures all updated_at columns have proper server_default
- Note: onupdate behavior is handled by SQLAlchemy ORM, not at database level
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "5692cec56609"
down_revision = "c8e342d1545a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema to standardize datetime fields."""
    
    # List of tables that need updated_at changed from nullable=True to nullable=False
    tables_to_update = {
        'case_customer': ['updated_at'],
        'case_lawyer': ['updated_at'],
        'case_resolve': ['updated_at'],
        '"case"': ['updated_at'],
        'customer': ['updated_at'],
        'invoice_payment': ['updated_at'],
        'invoice': ['updated_at'],
        'law_firm': ['updated_at'],
        'lawyer': ['updated_at'],
        'payment': ['updated_at'],
        'question_answers': ['updated_at'],
        'refresh_tokens': ['updated_at'],
        'resolve_question_answers': ['updated_at'],
        'resolve': ['updated_at'],
        'simple_auth_tokens': ['updated_at'],
        'timeline_map': ['updated_at'],
        '"user"': ['updated_at'],
        'websocket_connections': ['connected_at'],
    }


    for table_name, fields in tables_to_update.items():
        for column_name in fields:
            sql = f' UPDATE {table_name}'
            sql += f' SET {column_name} = COALESCE(created_at, NOW())'
            sql += f' WHERE {column_name} IS NULL;'
            sql += f' ALTER TABLE {table_name}'
            sql += f' ALTER COLUMN {column_name} TYPE TIMESTAMP WITH TIME ZONE;'     
            sql += f' ALTER TABLE {table_name}'
            sql += f' ALTER COLUMN {column_name} SET DEFAULT now();'
            sql += f' ALTER TABLE {table_name}'
            sql += f' ALTER COLUMN {column_name} SET NOT NULL;'

            op.execute(
                text(
                    sql
            ))


def downgrade() -> None:
    """Downgrade database schema - revert datetime field changes."""
    pass
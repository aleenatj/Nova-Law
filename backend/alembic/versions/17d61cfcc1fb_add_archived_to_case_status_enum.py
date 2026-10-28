"""Add ARCHIVED to case status enum

Revision ID: 17d61cfcc1fb
Revises: 1a2b3c4d5e6f
Create Date: 2025-11-13 12:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "17d61cfcc1fb"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ARCHIVED value to case_status_new_enum
    # Using DO block to safely add the value only if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'ARCHIVED' 
                AND enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'case_status_new_enum'
                )
            ) THEN
                ALTER TYPE case_status_new_enum ADD VALUE 'ARCHIVED';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Note: PostgreSQL does not support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the value in place but it won't be used
    # If full downgrade is needed, you would need to:
    # 1. Create a new enum without ARCHIVED
    # 2. Update all rows to use the new enum
    # 3. Drop and recreate the column
    
    # For safety, we'll just comment out the downgrade
    # If you need to remove ARCHIVED, you would need to manually update
    # all cases with ARCHIVED status to another status first
    pass


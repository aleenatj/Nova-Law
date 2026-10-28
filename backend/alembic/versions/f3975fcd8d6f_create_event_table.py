"""create_event_table

Revision ID: f3975fcd8d6f
Revises: 71f4cffbd38c
Create Date: 2025-08-18 21:15:58.710460

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f3975fcd8d6f"
down_revision = "71f4cffbd38c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create event table with final schema (consolidated from multiple migrations)
    op.create_table(
        "event",
        sa.Column(
            "event_id", sa.String(36), nullable=False
        ),  # String for SQLite compatibility
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column(
            "aggregate_id", sa.Integer(), nullable=True, index=True
        ),  # Integer for efficiency
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PROCESSED", "FAILED", name="eventstatus"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),  # Auto-set timestamp
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),  # Auto-update timestamp
        sa.PrimaryKeyConstraint("event_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
    )

    # Create index on event_type for faster lookups
    op.create_index(op.f("ix_event_event_type"), "event", ["event_type"], unique=False)

    # Create index on status for filtering
    op.create_index(op.f("ix_event_status"), "event", ["status"], unique=False)

    # Create index on created_at for time-based queries
    op.create_index(op.f("ix_event_created_at"), "event", ["created_at"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_event_created_at'), table_name='event')
    op.drop_index(op.f('ix_event_status'), table_name='event')
    op.drop_index(op.f('ix_event_event_type'), table_name='event')
    
    # Drop event table
    op.drop_table('event')
    
    # Drop enum type
    op.execute("DROP TYPE eventstatus") 

"""Add simple_auth_tokens table

Revision ID: 1a2b3c4d5e6f
Revises: 031717a0a6fc
Create Date: 2025-11-13 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1a2b3c4d5e6f"
down_revision = "15c228f60b28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create simple_auth_tokens table."""
    op.create_table(
        "simple_auth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=1000), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_simple_auth_tokens_user_id"), "simple_auth_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop simple_auth_tokens table."""
    op.drop_index(op.f("ix_simple_auth_tokens_user_id"), table_name="simple_auth_tokens")
    op.drop_table("simple_auth_tokens")


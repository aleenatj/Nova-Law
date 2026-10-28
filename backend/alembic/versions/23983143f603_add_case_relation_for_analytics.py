"""add case relation for analytics

Revision ID: 23983143f603
Revises: cec359ef0c61
Create Date: 2026-05-07 12:04:12.693361

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "23983143f603"
down_revision = "cec359ef0c61"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "case",
        sa.Column("kyc_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "case",
        sa.Column("profile_card_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "case",
        sa.Column("lawyer_assigned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "case",
        sa.Column(
            "initial_payment_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "case",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column("analytics_event", sa.Column("case_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_analytics_event_case_id_case",
        "analytics_event",
        "case",
        ["case_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Convert analytics_event.id from UUID PK to auto-incrementing integer PK.
    # No other tables reference analytics_event.id, so we can replace the PK in place.
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS analytics_event_id_seq"))
    op.add_column("analytics_event", sa.Column("id_new", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE analytics_event "
            "SET id_new = nextval('analytics_event_id_seq'::regclass) "
            "WHERE id_new IS NULL"
        )
    )
    op.drop_constraint("analytics_event_pkey", "analytics_event", type_="primary")
    op.drop_column("analytics_event", "id")
    op.alter_column("analytics_event", "id_new", new_column_name="id", nullable=False)
    op.execute(
        sa.text(
            "ALTER TABLE analytics_event "
            "ALTER COLUMN id SET DEFAULT nextval('analytics_event_id_seq'::regclass)"
        )
    )
    op.create_primary_key("analytics_event_pkey", "analytics_event", ["id"])
    op.execute(sa.text("ALTER SEQUENCE analytics_event_id_seq OWNED BY analytics_event.id"))


def downgrade() -> None:
    # Restore analytics_event.id as a UUID PK.
    op.drop_constraint("analytics_event_pkey", "analytics_event", type_="primary")
    op.add_column(
        "analytics_event",
        sa.Column(
            "id_old",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.execute(
        sa.text(
            "UPDATE analytics_event "
            "SET id_old = gen_random_uuid() "
            "WHERE id_old IS NULL"
        )
    )
    op.drop_column("analytics_event", "id")
    op.alter_column("analytics_event", "id_old", new_column_name="id", nullable=False)
    op.create_primary_key("analytics_event_pkey", "analytics_event", ["id"])
    op.execute(sa.text("DROP SEQUENCE IF EXISTS analytics_event_id_seq"))

    op.drop_constraint(
        "fk_analytics_event_case_id_case",
        "analytics_event",
        type_="foreignkey",
    )
    op.drop_column("analytics_event", "case_id")

    op.drop_column("case", "onboarding_completed_at")
    op.drop_column("case", "initial_payment_completed_at")
    op.drop_column("case", "lawyer_assigned_at")
    op.drop_column("case", "profile_card_sent_at")
    op.drop_column("case", "kyc_completed_at")

"""Alter deletion request

Revision ID: cac3775c68eb
Revises: 23983143f603
Create Date: 2026-05-11 16:48:26.427711

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'cac3775c68eb'
down_revision = '23983143f603'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert deletion_request.request_id from UUID PK to auto-incrementing integer PK.
    op.drop_constraint(
        "ck_deletion_request_subject_type",
        "deletion_request",
        type_="check",
    )
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS deletion_request_request_id_seq"))
    op.add_column("deletion_request", sa.Column("request_id_new", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE deletion_request "
            "SET request_id_new = nextval('deletion_request_request_id_seq'::regclass) "
            "WHERE request_id_new IS NULL"
        )
    )
    op.drop_constraint("deletion_request_pkey", "deletion_request", type_="primary")
    op.drop_column("deletion_request", "request_id")
    op.alter_column(
        "deletion_request",
        "request_id_new",
        new_column_name="request_id",
        nullable=False,
    )
    op.execute(
        sa.text(
            "ALTER TABLE deletion_request "
            "ALTER COLUMN request_id "
            "SET DEFAULT nextval('deletion_request_request_id_seq'::regclass)"
        )
    )
    op.create_primary_key("deletion_request_pkey", "deletion_request", ["request_id"])
    op.create_check_constraint(
        "ck_deletion_request_subject_type",
        "deletion_request",
        "subject_type IN ('user_id', 'session_id', 'anonymous_id')",
    )
    op.execute(
        sa.text(
            "ALTER SEQUENCE deletion_request_request_id_seq "
            "OWNED BY deletion_request.request_id"
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_deletion_request_subject_type",
        "deletion_request",
        type_="check",
    )
    op.drop_constraint("deletion_request_pkey", "deletion_request", type_="primary")
    op.add_column(
        "deletion_request",
        sa.Column(
            "request_id_old",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.execute(
        sa.text(
            "UPDATE deletion_request "
            "SET request_id_old = gen_random_uuid() "
            "WHERE request_id_old IS NULL"
        )
    )
    op.drop_column("deletion_request", "request_id")
    op.alter_column(
        "deletion_request",
        "request_id_old",
        new_column_name="request_id",
        nullable=False,
    )
    op.create_primary_key("deletion_request_pkey", "deletion_request", ["request_id"])
    op.create_check_constraint(
        "ck_deletion_request_subject_type",
        "deletion_request",
        "subject_type IN ('user_id', 'anonymous_id')",
    )
    op.execute(sa.text("DROP SEQUENCE IF EXISTS deletion_request_request_id_seq"))

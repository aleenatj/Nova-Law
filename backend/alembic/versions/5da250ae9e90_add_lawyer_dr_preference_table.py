"""Add lawyer DR preference table

Revision ID: 5da250ae9e90
Revises: cb91d6a98904
Create Date: 2025-11-10 17:21:15.225223

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5da250ae9e90'
down_revision = 'cb91d6a98904'
branch_labels = None
depends_on = None


DR_PREFERENCE_VALUES = [
    "Direct Negotiation",
    "Mediation",
    "One Lawyer One Couple",
    "Collaborative",
    "Hybrid Mediation-Support",
    "Hybrid Mediation-Mediator",
    "Lawyer Negotiation",
    "Early Neutral Evaluation/Private FDR-Support",
    "Early Neutral Evaluation/Private FDR-Evaluator",
    "Arbitration-Support",
    "Arbitration-Arbitrator",
    "Court",
]


def upgrade() -> None:
    """Create lawyer DR preference table and enum type."""

    dr_preference_enum = postgresql.ENUM(
        *DR_PREFERENCE_VALUES,
        name="dr_preference_enum",
        create_type=True,
    )
    dr_preference_enum.create(op.get_bind(), checkfirst=True)

    dr_preference_enum = postgresql.ENUM(
        *DR_PREFERENCE_VALUES,
        name="dr_preference_enum",
        create_type=False,
    )

    op.create_table(
        "lawyer_dr_preference",
        sa.Column("lawyer_id", sa.Integer(), nullable=False),
        sa.Column("dr_preference", dr_preference_enum, nullable=False),
        sa.ForeignKeyConstraint(["lawyer_id"], ["lawyer.id"]),
        sa.PrimaryKeyConstraint("lawyer_id", "dr_preference"),
    )


def downgrade() -> None:
    """Drop lawyer DR preference table and enum type."""

    op.drop_table("lawyer_dr_preference")
    op.execute("DROP TYPE IF EXISTS dr_preference_enum")

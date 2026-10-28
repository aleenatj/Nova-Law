"""Add engage_form_url and law_firm_type to LawFirm

Revision ID: add_law_firm_fields_correct
Revises: dcaeea9b1b8a
Create Date: 2025-08-25 17:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_law_firm_fields_correct"
down_revision = "dcaeea9b1b8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add engage_form_url and law_firm_type columns to law_firm table."""

    # Create the LawFirmType enum first
    law_firm_type_enum = postgresql.ENUM(
        "SOLO_PRACTITIONER", "BOUTIQUE", "MULTI_SPECIALITY", name="lawfirmtype"
    )
    law_firm_type_enum.create(op.get_bind())

    # Update contact_email column length from 100 to 255
    op.alter_column(
        "law_firm",
        "contact_email",
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    # Make contact_no column nullable
    op.alter_column(
        "law_firm",
        "contact_no",
        existing_type=sa.String(length=15),
        nullable=True,
    )

    # Add the engage_form_url column (varchar, nullable, unique)
    op.add_column(
        "law_firm", sa.Column("engage_form_url", sa.String(length=500), nullable=True)
    )

    # Add the law_firm_type column (enum, nullable)
    op.add_column(
        "law_firm", sa.Column("law_firm_type", law_firm_type_enum, nullable=True)
    )

    # Create unique constraints
    op.create_unique_constraint(
        "uq_law_firm_engage_form_url", "law_firm", ["engage_form_url"]
    )


def downgrade() -> None:
    """Remove engage_form_url and law_firm_type columns from law_firm table."""

    # Drop the unique constraints
    op.drop_constraint("uq_law_firm_engage_form_url", "law_firm", type_="unique")

    # Drop the columns
    op.drop_column("law_firm", "law_firm_type")
    op.drop_column("law_firm", "engage_form_url")

    # Revert contact_email column length from 255 back to 100
    op.alter_column(
        "law_firm",
        "contact_email",
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=False,
    )

    # Revert contact_no column to not nullable
    op.alter_column(
        "law_firm",
        "contact_no",
        existing_type=sa.String(length=15),
        nullable=False,
    )

    # Drop the enum type
    op.execute("DROP TYPE lawfirmtype")

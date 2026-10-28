"""timeline_map_related_id_change_string

Revision ID: cb91d6a98904
Revises: 52f35a8fa95f
Create Date: 2025-10-29 13:24:06.993258

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cb91d6a98904'
down_revision = '52f35a8fa95f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('timeline_map', 'related_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=100),
                    existing_nullable=False,
                    postgresql_using='related_id::text')
    
    # Create index on related_id
    op.create_index(op.f('ix_timeline_map_related_id'), 'timeline_map', ['related_id'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_timeline_map_related_id'), table_name='timeline_map')

    # When downgrading, the 'related_id' column may contain non-integer strings, which will fail the cast.
    # To ensure the migration proceeds safely, non-integer entries should be set to NULL or another default value.
    # Here, we'll use a CASE statement to safely cast only valid integers, else NULL.
    op.execute("""
        UPDATE timeline_map
        SET related_id = 0
        WHERE related_id !~ '^[0-9]+$'
    """)
    op.alter_column('timeline_map', 'related_id',
        existing_type=sa.String(length=100),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="CASE WHEN related_id ~ '^[0-9]+$' THEN related_id::integer ELSE NULL END"
    )

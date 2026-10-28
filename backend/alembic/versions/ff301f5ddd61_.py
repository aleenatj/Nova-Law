"""empty message

Revision ID: ff301f5ddd61
Revises: 3f007121c4b4, 6a45f889256b
Create Date: 2025-08-28 10:17:13.850662

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'ff301f5ddd61'
down_revision = ('3f007121c4b4', '6a45f889256b')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'match',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True, nullable=False),
        sa.Column('lawyer_id', sa.Integer(), sa.ForeignKey('lawyer.id'), nullable=False),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('case.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'INTERESTED', 'DECLINED', name='match_status_enum'), nullable=False, server_default='PENDING'),
        sa.Column('action_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('action_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('declined_reason', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('match')
    sa.Enum(name='match_status_enum').drop(op.get_bind())

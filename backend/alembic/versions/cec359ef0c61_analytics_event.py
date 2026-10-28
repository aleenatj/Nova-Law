"""analytics event

Revision ID: cec359ef0c61
Revises: 65fdc1dc51b6
Create Date: 2026-05-05 10:05:49.142851

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cec359ef0c61'
down_revision = '65fdc1dc51b6'
branch_labels = None
depends_on = None

deletion_request_status_enum = postgresql.ENUM(
    'PENDING',
    'PROGRESS',
    'COMPLETED',
    'FAILED',
    name='deletion_request_status_enum',
    create_type=False,
)

TYPE_NAME = "email_cta_clicked"
VERSION = 1
ROLE_CODE = "Navigator"


def upgrade() -> None:
    op.add_column('user', sa.Column('first_touch_source', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('first_touch_medium', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('first_touch_campaign', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('first_touch_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user', sa.Column('last_touch_source', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('last_touch_medium', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('last_touch_campaign', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('last_touch_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'user',
        sa.Column(
            'traits',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.add_column('case', sa.Column('analytics_data', sa.JSON(), nullable=True))

    op.create_table(
        'identities',
        sa.Column('anonymous_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'first_seen_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column(
            'last_seen_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('anonymous_id', 'user_id'),
    )

    op.create_table(
        'session',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('anonymous_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'last_event_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('entry_page', sa.Text(), nullable=False),
        sa.Column('exit_page', sa.Text(), nullable=True),
        sa.Column('source', sa.Text(), nullable=True),
        sa.Column('medium', sa.Text(), nullable=True),
        sa.Column('campaign', sa.Text(), nullable=True),
        sa.Column('term', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('gclid', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.Text(), nullable=True),
        sa.Column('browser', sa.Text(), nullable=True),
        sa.Column('os', sa.Text(), nullable=True),
        sa.Column('country', sa.Text(), nullable=True),
        sa.Column('locale', sa.Text(), nullable=True),
        sa.Column('timezone', sa.Text(), nullable=True),
        sa.Column('event_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_bot', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_session_anonymous_id'), 'session', ['anonymous_id'], unique=False)
    op.create_index(op.f('ix_session_user_id'), 'session', ['user_id'], unique=False)
    op.create_index(op.f('ix_session_started_at'), 'session', ['started_at'], unique=False)
    op.create_index(op.f('ix_session_entry_page'), 'session', ['entry_page'], unique=False)
    op.create_index('ix_session_source_medium', 'session', ['source', 'medium'], unique=False)

    op.create_table(
        'analytics_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_code', sa.Text(), nullable=False),
        sa.Column('anonymous_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'received_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column('page_url', sa.Text(), nullable=True),
        sa.Column('page_path', sa.Text(), nullable=True),
        sa.Column('page_title', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column(
            'properties',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column('is_bot', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_internal', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['session_id'], ['session.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_analytics_event_event_code_timestamp',
        'analytics_event',
        ['event_code', 'timestamp'],
        unique=False,
    )
    op.create_index(op.f('ix_analytics_event_anonymous_id'), 'analytics_event', ['anonymous_id'], unique=False)
    op.create_index(op.f('ix_analytics_event_session_id'), 'analytics_event', ['session_id'], unique=False)
    op.create_index(op.f('ix_analytics_event_user_id'), 'analytics_event', ['user_id'], unique=False)
    op.create_index(
        'ix_analytics_event_page_path_page_view',
        'analytics_event',
        ['page_path'],
        unique=False,
        postgresql_where=sa.text("event_code = 'page_view'"),
    )
    op.create_index(
        'ix_analytics_event_properties_gin',
        'analytics_event',
        ['properties'],
        unique=False,
        postgresql_using='gin',
    )

    deletion_request_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'deletion_request',
        sa.Column(
            'request_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'requested_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subject_type', sa.Text(), nullable=False),
        sa.Column('subject_id', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column(
            'status',
            deletion_request_status_enum,
            nullable=False,
            server_default=sa.text("'PENDING'::deletion_request_status_enum"),
        ),
        sa.PrimaryKeyConstraint('request_id'),
        sa.CheckConstraint(
            "subject_type IN ('user_id', 'anonymous_id')",
            name='ck_deletion_request_subject_type',
        ),
    )
    op.create_index(op.f('ix_deletion_request_status'), 'deletion_request', ['status'], unique=False)

    # Insert timeline_type for email cta clicked
    op.execute(
        sa.text(
            "INSERT INTO timeline_type (type_name, version, role_code) "
            "VALUES (:type_name, :version, :role_code)"
        ).bindparams(
            type_name=TYPE_NAME,
            version=VERSION,
            role_code=ROLE_CODE,
        )
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_deletion_request_status'), table_name='deletion_request')
    op.drop_table('deletion_request')
    deletion_request_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index('ix_analytics_event_properties_gin', table_name='analytics_event')
    op.drop_index('ix_analytics_event_page_path_page_view', table_name='analytics_event')
    op.drop_index(op.f('ix_analytics_event_user_id'), table_name='analytics_event')
    op.drop_index(op.f('ix_analytics_event_session_id'), table_name='analytics_event')
    op.drop_index(op.f('ix_analytics_event_anonymous_id'), table_name='analytics_event')
    op.drop_index('ix_analytics_event_event_code_timestamp', table_name='analytics_event')
    op.drop_table('analytics_event')

    op.drop_index('ix_session_source_medium', table_name='session')
    op.drop_index(op.f('ix_session_entry_page'), table_name='session')
    op.drop_index(op.f('ix_session_started_at'), table_name='session')
    op.drop_index(op.f('ix_session_user_id'), table_name='session')
    op.drop_index(op.f('ix_session_anonymous_id'), table_name='session')
    op.drop_table('session')

    op.drop_table('identities')

    op.drop_column('case', 'analytics_data')

    op.drop_column('user', 'traits')
    op.drop_column('user', 'last_touch_at')
    op.drop_column('user', 'last_touch_campaign')
    op.drop_column('user', 'last_touch_medium')
    op.drop_column('user', 'last_touch_source')
    op.drop_column('user', 'first_touch_at')
    op.drop_column('user', 'first_touch_campaign')
    op.drop_column('user', 'first_touch_medium')
    op.drop_column('user', 'first_touch_source')

    # Delete timeline_type record
    op.execute(
        "DELETE FROM timeline_type WHERE type_name = 'email_cta_clicked'"
    )

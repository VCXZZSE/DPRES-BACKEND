"""add sos events table

Revision ID: e12a9c4b7f21
Revises: 5da962ed614a
Create Date: 2026-03-31 11:15:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e12a9c4b7f21'
down_revision = '5da962ed614a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sos_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('location_text', sa.String(length=255), nullable=True),
        sa.Column('accuracy_meters', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sos_events_id'), 'sos_events', ['id'], unique=False)
    op.create_index(op.f('ix_sos_events_user_id'), 'sos_events', ['user_id'], unique=False)
    op.create_index('ix_sos_events_status_created_at', 'sos_events', ['status', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sos_events_status_created_at', table_name='sos_events')
    op.drop_index(op.f('ix_sos_events_user_id'), table_name='sos_events')
    op.drop_index(op.f('ix_sos_events_id'), table_name='sos_events')
    op.drop_table('sos_events')

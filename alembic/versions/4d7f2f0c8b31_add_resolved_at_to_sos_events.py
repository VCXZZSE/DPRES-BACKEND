"""add resolved_at to sos events

Revision ID: 4d7f2f0c8b31
Revises: e12a9c4b7f21
Create Date: 2026-03-31 12:25:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d7f2f0c8b31'
down_revision = 'e12a9c4b7f21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sos_events', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('sos_events', 'resolved_at')

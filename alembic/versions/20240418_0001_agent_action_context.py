"""Add ChatKit context to agent action audits."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20240418_0001"
down_revision = "20240210_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_action_audits",
        sa.Column("channel_slug", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "agent_action_audits",
        sa.Column("initiator_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_action_audits", "initiator_id")
    op.drop_column("agent_action_audits", "channel_slug")

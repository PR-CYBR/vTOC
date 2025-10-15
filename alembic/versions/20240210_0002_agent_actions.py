"""Agent action audit log."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20240210_0002"
down_revision = "20240120_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_action_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_agent_action_audits_status",
        "agent_action_audits",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_action_audits_status", table_name="agent_action_audits")
    op.drop_table("agent_action_audits")

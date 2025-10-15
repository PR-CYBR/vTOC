"""Initial telemetry tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20240120_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telemetry_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("connection_mode", sa.String(length=50), nullable=False, server_default="online"),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("last_ingested_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("telemetry_sources.id", ondelete="CASCADE")),
        sa.Column("event_time", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="received"),
    )

    op.create_index("idx_telemetry_events_event_time", "telemetry_events", ["event_time"])


def downgrade() -> None:
    op.drop_index("idx_telemetry_events_event_time", table_name="telemetry_events")
    op.drop_table("telemetry_events")
    op.drop_table("telemetry_sources")

"""Create telemetry source and event tables

Revision ID: 20240108_telemetry
Revises: 
Create Date: 2024-01-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240108_telemetry"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telemetry_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("connection_mode", sa.String(length=50), nullable=False, server_default="online"),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("last_ingested_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_telemetry_sources_name"),
        sa.UniqueConstraint("slug", name="uq_telemetry_sources_slug"),
    )

    op.create_index("ix_telemetry_sources_slug", "telemetry_sources", ["slug"], unique=False)

    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("telemetry_sources.id", ondelete="CASCADE")),
        sa.Column("event_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
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

    op.create_index("ix_telemetry_events_event_time", "telemetry_events", ["event_time"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_telemetry_events_event_time", table_name="telemetry_events")
    op.drop_table("telemetry_events")
    op.drop_index("ix_telemetry_sources_slug", table_name="telemetry_sources")
    op.drop_table("telemetry_sources")


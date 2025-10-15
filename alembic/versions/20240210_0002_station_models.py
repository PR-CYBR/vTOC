"""Add station tables and relationships."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20240210_0002"
down_revision = "20240120_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=False, server_default="UTC"),
        sa.Column("telemetry_schema", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stations_slug", "stations", ["slug"], unique=True)

    op.add_column(
        "telemetry_sources",
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="SET NULL")),
    )
    op.add_column(
        "telemetry_events",
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="SET NULL")),
    )

    op.create_table(
        "station_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("telemetry_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False, server_default="primary"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("station_id", "source_id", name="uq_station_assignment"),
    )


def downgrade() -> None:
    op.drop_table("station_assignments")
    op.drop_column("telemetry_events", "station_id")
    op.drop_column("telemetry_sources", "station_id")
    op.drop_index("ix_stations_slug", table_name="stations")
    op.drop_table("stations")

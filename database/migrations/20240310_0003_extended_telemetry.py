"""Add infrastructure tables for base stations, devices, RF streams, overlays, and telemetry feeds."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20240310_0003"
down_revision = "20240210_0002"
branch_labels = None
depends_on = None


BASE_STATION_STATUS_DEFAULT = "active"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS telemetry")

    op.create_table(
        "base_stations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "station_id",
            sa.Integer(),
            sa.ForeignKey("stations.id", ondelete="CASCADE"),
            nullable=True,
            unique=True,
        ),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=BASE_STATION_STATUS_DEFAULT),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("altitude_m", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_base_stations_slug", "base_stations", ["slug"], unique=True)

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "base_station_id",
            sa.Integer(),
            sa.ForeignKey("base_stations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "station_id",
            sa.Integer(),
            sa.ForeignKey("stations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=100), nullable=False),
        sa.Column("manufacturer", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("serial_number", sa.String(length=255), nullable=True),
        sa.Column("firmware_version", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_devices_slug", "devices", ["slug"], unique=True)
    op.create_index("ix_devices_base_station_id", "devices", ["base_station_id"])
    op.create_index("ix_devices_station_id", "devices", ["station_id"])

    op.create_table(
        "rf_streams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("telemetry_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("center_frequency_hz", sa.BigInteger(), nullable=True),
        sa.Column("bandwidth_hz", sa.BigInteger(), nullable=True),
        sa.Column("sample_rate", sa.BigInteger(), nullable=True),
        sa.Column("modulation", sa.String(length=100), nullable=True),
        sa.Column("gain", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rf_streams_slug", "rf_streams", ["slug"], unique=True)
    op.create_index("ix_rf_streams_device_id", "rf_streams", ["device_id"])
    op.create_index("ix_rf_streams_source_id", "rf_streams", ["source_id"])

    op.create_table(
        "overlays",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "station_id",
            sa.Integer(),
            sa.ForeignKey("stations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("overlay_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_overlays_slug", "overlays", ["slug"], unique=True)
    op.create_index("ix_overlays_station_id", "overlays", ["station_id"])

    op.create_table(
        "gps_fixes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("telemetry_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "station_id",
            sa.Integer(),
            sa.ForeignKey("stations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("recorded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("horizontal_accuracy", sa.Float(), nullable=True),
        sa.Column("vertical_accuracy", sa.Float(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema="telemetry",
    )
    op.create_index(
        "ix_gps_fixes_recorded_at",
        "gps_fixes",
        ["recorded_at"],
        schema="telemetry",
    )
    op.create_index(
        "ix_gps_fixes_source_id",
        "gps_fixes",
        ["source_id"],
        schema="telemetry",
    )

    op.create_table(
        "aircraft_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("telemetry_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "station_id",
            sa.Integer(),
            sa.ForeignKey("stations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("icao_address", sa.String(length=6), nullable=True),
        sa.Column("callsign", sa.String(length=16), nullable=True),
        sa.Column("squawk", sa.String(length=8), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("ground_speed", sa.Float(), nullable=True),
        sa.Column("vertical_rate", sa.Float(), nullable=True),
        sa.Column("position_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema="telemetry",
    )
    op.create_index(
        "ix_aircraft_positions_position_time",
        "aircraft_positions",
        ["position_time"],
        schema="telemetry",
    )
    op.create_index(
        "ix_aircraft_positions_source_id",
        "aircraft_positions",
        ["source_id"],
        schema="telemetry",
    )

    connection = op.get_bind()
    stations = list(connection.execute(sa.text("SELECT id, slug, name FROM stations")))
    for station in stations:
        connection.execute(
            sa.text(
                """
                INSERT INTO base_stations (station_id, slug, name, description, status)
                VALUES (:station_id, :slug, :name, '', :status)
                ON CONFLICT (slug) DO NOTHING
                """
            ),
            {
                "station_id": station.id,
                "slug": station.slug,
                "name": station.name,
                "status": BASE_STATION_STATUS_DEFAULT,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_aircraft_positions_source_id", table_name="aircraft_positions", schema="telemetry")
    op.drop_index("ix_aircraft_positions_position_time", table_name="aircraft_positions", schema="telemetry")
    op.drop_table("aircraft_positions", schema="telemetry")

    op.drop_index("ix_gps_fixes_source_id", table_name="gps_fixes", schema="telemetry")
    op.drop_index("ix_gps_fixes_recorded_at", table_name="gps_fixes", schema="telemetry")
    op.drop_table("gps_fixes", schema="telemetry")

    op.drop_index("ix_overlays_station_id", table_name="overlays")
    op.drop_index("ix_overlays_slug", table_name="overlays")
    op.drop_table("overlays")

    op.drop_index("ix_rf_streams_source_id", table_name="rf_streams")
    op.drop_index("ix_rf_streams_device_id", table_name="rf_streams")
    op.drop_index("ix_rf_streams_slug", table_name="rf_streams")
    op.drop_table("rf_streams")

    op.drop_index("ix_devices_station_id", table_name="devices")
    op.drop_index("ix_devices_base_station_id", table_name="devices")
    op.drop_index("ix_devices_slug", table_name="devices")
    op.drop_table("devices")

    op.drop_index("ix_base_stations_slug", table_name="base_stations")
    op.drop_table("base_stations")

    op.execute("DROP SCHEMA IF EXISTS telemetry CASCADE")

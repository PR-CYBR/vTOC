"""Add POI and IMEI watchlist tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20241113_0001"
down_revision = "20240418_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create poi table
    op.create_table(
        "poi",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, index=True),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="person"),
        sa.Column("risk_level", sa.String(length=100), nullable=False, server_default="info"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create poi_identifier table
    op.create_table(
        "poi_identifier",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("poi_id", sa.Integer(), sa.ForeignKey("poi.id", ondelete="CASCADE"), nullable=False),
        sa.Column("identifier_type", sa.String(length=100), nullable=False),
        sa.Column("identifier_value", sa.String(length=255), nullable=False, index=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create imei_watch_entry table
    op.create_table(
        "imei_watch_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identifier_value", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("list_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("linked_poi_id", sa.Integer(), sa.ForeignKey("poi.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("imei_watch_entry")
    op.drop_table("poi_identifier")
    op.drop_table("poi")

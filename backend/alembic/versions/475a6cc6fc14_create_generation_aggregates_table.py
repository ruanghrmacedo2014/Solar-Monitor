"""create generation aggregates table

Revision ID: 475a6cc6fc14
Revises: 68129b988328
Create Date: 2026-10-05 12:46:19.933222

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "475a6cc6fc14"
down_revision: Union[str, Sequence[str], None] = "68129b988328"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generation_aggregates",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "solar_plant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "period_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "granularity",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "generation_kwh",
            sa.Numeric(precision=14, scale=3),
            nullable=False,
        ),
        sa.Column(
            "raw_data",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["solar_plant_id"],
            ["solar_plants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "solar_plant_id",
            "period_start",
            "granularity",
            name=(
                "uq_generation_aggregates_tenant_plant_"
                "period_granularity"
            ),
        ),
    )

    op.create_index(
        op.f("ix_generation_aggregates_tenant_id"),
        "generation_aggregates",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_generation_aggregates_solar_plant_id"),
        "generation_aggregates",
        ["solar_plant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_generation_aggregates_solar_plant_id"),
        table_name="generation_aggregates",
    )

    op.drop_index(
        op.f("ix_generation_aggregates_tenant_id"),
        table_name="generation_aggregates",
    )

    op.drop_table("generation_aggregates")
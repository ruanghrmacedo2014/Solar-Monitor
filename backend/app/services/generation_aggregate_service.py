from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.generation_aggregate import GenerationAggregate


class GenerationAggregateService:

    def __init__(self, db: Session):
        self.db = db

    def save_aggregates(
        self,
        records: list[dict],
    ) -> list[GenerationAggregate]:
        if not records:
            return []

        now = datetime.now(timezone.utc)

        normalized_records = []

        for record in records:
            normalized_records.append(
                {
                    **record,
                    "generation_kwh": Decimal(
                        str(record["generation_kwh"])
                    ),
                    "synced_at": now,
                }
            )

        statement = insert(
            GenerationAggregate
        ).values(normalized_records)

        statement = statement.on_conflict_do_update(
            constraint=(
                "uq_generation_aggregates_tenant_plant_"
                "period_granularity"
            ),
            set_={
                "generation_kwh": statement.excluded.generation_kwh,
                "raw_data": statement.excluded.raw_data,
                "synced_at": statement.excluded.synced_at,
            },
        ).returning(GenerationAggregate)

        result = self.db.execute(statement)

        self.db.commit()

        return list(result.scalars().all())
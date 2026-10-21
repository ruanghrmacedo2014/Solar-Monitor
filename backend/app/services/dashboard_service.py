from datetime import datetime, timezone, timedelta
from app.services.generation_service import GenerationService
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.generation_record import GenerationRecord
from app.models.generation_sync_log import GenerationSyncLog
from app.models.solar_device import SolarDevice
from app.models.solar_plant import SolarPlant
from app.models.customer import Customer
from collections import defaultdict


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
    ) -> dict:
        now = datetime.now(timezone.utc)

        start_of_day = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        generation_service = GenerationService(self.db)

                # ---------------------------------------------------------
        # Usinas visíveis para o usuário
        # ---------------------------------------------------------

        plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in plant_query.all()
            ]

        # ---------------------------------------------------------
        # Pico e média da potência total do sistema
        # ---------------------------------------------------------

        today_timestamp_power = (
            self.db.query(
                GenerationRecord.measured_at.label("measured_at"),
                func.sum(
                    GenerationRecord.power_w
                ).label("total_power_w"),
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id.in_(
                    visible_plant_ids
                ),
                GenerationRecord.measured_at >= start_of_day,
                GenerationRecord.measured_at <= now,
                GenerationRecord.power_w.is_not(None),
            )
            .group_by(
                GenerationRecord.measured_at,
            )
            .subquery()
        )

        today_result = (
            self.db.query(
                func.max(
                    today_timestamp_power.c.total_power_w
                ),
                func.avg(
                    today_timestamp_power.c.total_power_w
                ),
            )
            .first()
        )

        today_peak_power_w = (
            float(today_result[0])
            if today_result[0] is not None
            else None
        )

        today_average_power_w = (
            float(today_result[1])
            if today_result[1] is not None
            else None
        )

        # ---------------------------------------------------------
        # Potência atual
        # ---------------------------------------------------------

        current_power_w = None

        if visible_plant_ids:
            latest_measured_at = (
                self.db.query(
                    GenerationRecord.solar_plant_id,
                    func.max(
                        GenerationRecord.measured_at
                    ).label("measured_at"),
                )
                .filter(
                    GenerationRecord.tenant_id == tenant_id,
                    GenerationRecord.solar_plant_id.in_(
                        visible_plant_ids
                    ),
                )
                .group_by(
                    GenerationRecord.solar_plant_id,
                )
                .subquery()
            )

            latest_records = (
                self.db.query(GenerationRecord)
                .join(
                    latest_measured_at,
                    (
                        GenerationRecord.solar_plant_id
                        == latest_measured_at.c.solar_plant_id
                    )
                    & (
                        GenerationRecord.measured_at
                        == latest_measured_at.c.measured_at
                    ),
                )
                .filter(
                    GenerationRecord.tenant_id == tenant_id,
                    GenerationRecord.power_w.is_not(None),
                )
                .all()
            )

            current_power_total = 0.0
            has_current_power = False

            for record in latest_records:
                age_minutes = (
                    now - record.measured_at
                ).total_seconds() / 60

                if age_minutes <= 30:
                    current_power_total += float(
                        record.power_w
                    )
                    has_current_power = True

            if has_current_power:
                current_power_w = current_power_total

        # ---------------------------------------------------------
        # Plantas
        # ---------------------------------------------------------

        plants_total = len(visible_plant_ids)

        # ---------------------------------------------------------
        # Dispositivos
        # ---------------------------------------------------------

        devices_total = (
            self.db.query(func.count(SolarDevice.id))
            .filter(
                SolarDevice.tenant_id == tenant_id,
                SolarDevice.solar_plant_id.in_(
                    visible_plant_ids
                ),
            )
            .scalar()
            or 0
        )

        devices_online = (
            self.db.query(func.count(SolarDevice.id))
            .filter(
                SolarDevice.tenant_id == tenant_id,
                SolarDevice.solar_plant_id.in_(
                    visible_plant_ids
                ),
                SolarDevice.connect_status == 1,
            )
            .scalar()
            or 0
        )

        devices_offline = devices_total - devices_online

        # ---------------------------------------------------------
        # Última sincronização
        # ---------------------------------------------------------

        latest_sync = (
            self.db.query(GenerationSyncLog)
            .filter(
                GenerationSyncLog.tenant_id == tenant_id,
            )
            .order_by(
                GenerationSyncLog.finished_at.desc()
            )
            .first()
        )

        last_sync_at = (
            latest_sync.finished_at
            if latest_sync is not None
            else None
        )

        all_plant_statuses = generation_service.get_plant_statuses(
            tenant_id=tenant_id,
            reference_time=now,
        )

        plant_statuses = {
            plant_id: status
            for plant_id, status in all_plant_statuses.items()
            if plant_id in visible_plant_ids
        }

        plants_generating = sum(
            1
            for status in plant_statuses.values()
            if status == "GENERATING"
        )

        plants_offline = sum(
            1
            for status in plant_statuses.values()
            if status == "OFFLINE"
        )

        plants_online = sum(
            1
            for status in plant_statuses.values()
            if status == "ONLINE"
        )

        return {
            "current_power_w": current_power_w,
            "today_energy_kwh": sum(
                generation_service.calculate_energy(
                    tenant_id=tenant_id,
                    solar_plant_id=plant_id,
                    start_at=start_of_day,
                    end_at=now,
                )
                for plant_id in visible_plant_ids
            ),
            "today_peak_power_w": today_peak_power_w,
            "today_average_power_w": today_average_power_w,
            "plants_total": plants_total,
            "plants_generating": plants_generating,
            "plants_online": plants_online,
            "plants_offline": plants_offline,
            "devices_total": devices_total,
            "devices_online": devices_online,
            "devices_offline": devices_offline,
            "last_sync_at": last_sync_at,
        }

    def get_generation(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        visible_plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in visible_plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in visible_plant_query.all()
            ]

        records = (
            self.db.query(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id.in_(
                    visible_plant_ids
                ),
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
            )
            .order_by(
                GenerationRecord.measured_at,
                GenerationRecord.solar_plant_id,
            )
            .all()
        )

        return [
            {
                "solar_plant_id": solar_plant_id,
                "measured_at": measured_at,
                "power_w": (
                    float(power_w)
                    if power_w is not None
                    else None
                ),
            }
            for solar_plant_id, measured_at, power_w in records
        ]
    
    def get_generation_summary_by_hour(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        from sqlalchemy import func

        visible_plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in visible_plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in visible_plant_query.all()
            ]

        timestamp_power = (
            self.db.query(
                GenerationRecord.measured_at.label(
                    "measured_at"
                ),
                func.sum(
                    GenerationRecord.power_w
                ).label(
                    "total_power_w"
                ),
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id.in_(
                    visible_plant_ids
                ),
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .group_by(
                GenerationRecord.measured_at,
            )
            .subquery()
        )

        hour = func.date_trunc(
            "hour",
            timestamp_power.c.measured_at,
        ).label("hour")

        result = (
            self.db.query(
                hour,
                func.avg(
                    timestamp_power.c.total_power_w
                ).label(
                    "average_power_w"
                ),
                func.max(
                    timestamp_power.c.total_power_w
                ).label(
                    "peak_power_w"
                ),
                func.min(
                    timestamp_power.c.total_power_w
                ).label(
                    "minimum_power_w"
                ),
            )
            .group_by(hour)
            .order_by(hour)
            .all()
        )

        return [
            {
                "measured_at": row.hour,
                "average_power_w": (
                    float(row.average_power_w)
                    if row.average_power_w is not None
                    else None
                ),
                "peak_power_w": (
                    float(row.peak_power_w)
                    if row.peak_power_w is not None
                    else None
                ),
                "minimum_power_w": (
                    float(row.minimum_power_w)
                    if row.minimum_power_w is not None
                    else None
                ),
            }
            for row in result
        ]

    def get_generation_daily(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        visible_plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in visible_plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in visible_plant_query.all()
            ]

        if not visible_plant_ids:
            return []

        records = (
            self.db.query(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id.in_(
                    visible_plant_ids
                ),
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .order_by(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
            )
            .all()
        )

        daily_energy: dict[datetime, float] = {}

        current_plant_id = None
        previous_time = None
        previous_power = None
        previous_day = None

        for plant_id, measured_at, power_w in records:
            current_day = measured_at.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if plant_id != current_plant_id:
                current_plant_id = plant_id
                previous_time = None
                previous_power = None
                previous_day = None

            if (
                previous_time is not None
                and previous_power is not None
                and previous_day == current_day
            ):
                interval_minutes = (
                    measured_at - previous_time
                ).total_seconds() / 60

                if interval_minutes <= 30:
                    interval_hours = interval_minutes / 60

                    average_power_w = (
                        float(previous_power)
                        + float(power_w)
                    ) / 2

                    energy_kwh = (
                        average_power_w * interval_hours
                    ) / 1000

                    daily_energy[current_day] = (
                        daily_energy.get(current_day, 0.0)
                        + energy_kwh
                    )

            previous_time = measured_at
            previous_power = power_w
            previous_day = current_day

        return [
            {
                "measured_at": measured_at,
                "energy_kwh": energy_kwh,
            }
            for measured_at, energy_kwh
            in sorted(daily_energy.items())
        ]

    def get_generation_monthly(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        visible_plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in visible_plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in visible_plant_query.all()
            ]

        if not visible_plant_ids:
            return []

        records = (
            self.db.query(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id.in_(
                    visible_plant_ids
                ),
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .order_by(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
            )
            .all()
        )

        monthly_energy: dict[datetime, float] = {}

        current_plant_id = None
        previous_time = None
        previous_power = None
        previous_month = None

        for plant_id, measured_at, power_w in records:
            current_month = measured_at.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if plant_id != current_plant_id:
                current_plant_id = plant_id
                previous_time = None
                previous_power = None
                previous_month = None

            if (
                previous_time is not None
                and previous_power is not None
                and previous_month == current_month
            ):
                interval_minutes = (
                    measured_at - previous_time
                ).total_seconds() / 60

                if interval_minutes <= 30:
                    interval_hours = interval_minutes / 60

                    average_power_w = (
                        float(previous_power)
                        + float(power_w)
                    ) / 2

                    energy_kwh = (
                        average_power_w * interval_hours
                    ) / 1000

                    monthly_energy[current_month] = (
                        monthly_energy.get(current_month, 0.0)
                        + energy_kwh
                    )

            previous_time = measured_at
            previous_power = power_w
            previous_month = current_month

        return [
            {
                "measured_at": measured_at,
                "energy_kwh": energy_kwh,
            }
            for measured_at, energy_kwh
            in sorted(monthly_energy.items())
        ]

    def get_generation_yearly(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        visible_plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in visible_plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in visible_plant_query.all()
            ]

        if not visible_plant_ids:
            return []

        records = (
            self.db.query(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id.in_(
                    visible_plant_ids
                ),
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .order_by(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
            )
            .all()
        )

        yearly_energy: dict[datetime, float] = {}

        current_plant_id = None
        previous_time = None
        previous_power = None
        previous_year = None

        for plant_id, measured_at, power_w in records:
            current_year = measured_at.replace(
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if plant_id != current_plant_id:
                current_plant_id = plant_id
                previous_time = None
                previous_power = None
                previous_year = None

            if (
                previous_time is not None
                and previous_power is not None
                and previous_year == current_year
            ):
                interval_minutes = (
                    measured_at - previous_time
                ).total_seconds() / 60

                if interval_minutes <= 30:
                    interval_hours = interval_minutes / 60

                    average_power_w = (
                        float(previous_power)
                        + float(power_w)
                    ) / 2

                    energy_kwh = (
                        average_power_w * interval_hours
                    ) / 1000

                    yearly_energy[current_year] = (
                        yearly_energy.get(current_year, 0.0)
                        + energy_kwh
                    )

            previous_time = measured_at
            previous_power = power_w
            previous_year = current_year

        return [
            {
                "measured_at": measured_at,
                "energy_kwh": energy_kwh,
            }
            for measured_at, energy_kwh
            in sorted(yearly_energy.items())
        ]
    
    def get_generation_system_by_timestamp(
        self,
        tenant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        from sqlalchemy import func

        result = (
            self.db.query(
                GenerationRecord.measured_at,
                func.sum(GenerationRecord.power_w).label(
                    "total_power_w"
                ),
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .group_by(
                GenerationRecord.measured_at,
            )
            .order_by(
                GenerationRecord.measured_at,
            )
            .all()
        )

        return [
            {
                "measured_at": measured_at,
                "total_power_w": (
                    float(total_power_w)
                    if total_power_w is not None
                    else None
                ),
            }
            for measured_at, total_power_w in result
        ]

    def get_plants(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
    ) -> dict:

        generation_service = GenerationService(self.db)

        # ---------------------------------------------------------
        # Usinas visíveis para o usuário
        # ---------------------------------------------------------

        plant_query = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                visible_plant_ids = []
            else:
                visible_plant_ids = [
                    row.id
                    for row in plant_query
                    .filter(
                        SolarPlant.customer_id == customer.id,
                    )
                    .all()
                ]
        else:
            visible_plant_ids = [
                row.id
                for row in plant_query.all()
            ]

        now = datetime.now(timezone.utc)

        plant_statuses = generation_service.get_plant_statuses(
            tenant_id=tenant_id,
            reference_time=now,
        )

        plant_query = (
            self.db.query(SolarPlant)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                return {
                    "total": 0,
                    "generating": 0,
                    "online": 0,
                    "offline": 0,
                    "by_provider": [],
                    "plants": [],
                }

            plant_query = plant_query.filter(
                SolarPlant.customer_id == customer.id,
            )

        plants = (
            plant_query
            .order_by(SolarPlant.id)
            .all()
        )

        plant_ids = [plant.id for plant in plants]

        latest_records = {}

        if plant_ids:
            latest_measured_at = (
                self.db.query(
                    GenerationRecord.solar_plant_id,
                    func.max(
                        GenerationRecord.measured_at
                    ).label("measured_at"),
                )
                .filter(
                    GenerationRecord.tenant_id == tenant_id,
                    GenerationRecord.solar_plant_id.in_(plant_ids),
                )
                .group_by(
                    GenerationRecord.solar_plant_id,
                )
                .subquery()
            )

            records = (
                self.db.query(GenerationRecord)
                .join(
                    latest_measured_at,
                    (
                        GenerationRecord.solar_plant_id
                        == latest_measured_at.c.solar_plant_id
                    )
                    & (
                        GenerationRecord.measured_at
                        == latest_measured_at.c.measured_at
                    ),
                )
                .filter(
                    GenerationRecord.tenant_id == tenant_id,
                )
                .all()
            )

            latest_records = {
                record.solar_plant_id: record
                for record in records
            }

        provider_summary = defaultdict(
            lambda: {
                "total": 0,
                "generating": 0,
                "online": 0,
                "offline": 0,
            }
        )

        plant_items = []

        for plant in plants:
            status = plant_statuses.get(
                plant.id,
                "OFFLINE",
            )

            provider = plant.source_provider or "UNKNOWN"

            provider_summary[provider]["total"] += 1

            if status == "GENERATING":
                provider_summary[provider]["generating"] += 1
            elif status == "ONLINE":
                provider_summary[provider]["online"] += 1
            else:
                provider_summary[provider]["offline"] += 1

            latest_record = latest_records.get(plant.id)

            plant_items.append(
                {
                    "id": plant.id,
                    "name": plant.name,
                    "source_provider": provider,
                    "status": status,
                    "latest_power_w": (
                        float(latest_record.power_w)
                        if latest_record
                        and latest_record.power_w is not None
                        else None
                    ),
                    "last_measured_at": (
                        latest_record.measured_at
                        if latest_record
                        else None
                    ),
                }
            )

        generating = sum(
            1
            for item in plant_items
            if item["status"] == "GENERATING"
        )

        online = sum(
            1
            for item in plant_items
            if item["status"] == "ONLINE"
        )

        offline = sum(
            1
            for item in plant_items
            if item["status"] == "OFFLINE"
        )

        by_provider = [
            {
                "provider": provider,
                "total": values["total"],
                "generating": values["generating"],
                "online": values["online"],
                "offline": values["offline"],
            }
            for provider, values in sorted(
                provider_summary.items()
            )
        ]

        return {
            "total": len(plants),
            "generating": generating,
            "online": online,
            "offline": offline,
            "by_provider": by_provider,
            "plants": plant_items,
        }

    def get_devices(
        self,
        tenant_id: int,
        user_id: int,
        user_role: str,
    ) -> dict:
        from collections import defaultdict

        device_query = (
            self.db.query(
                SolarDevice,
                SolarPlant.name.label("plant_name"),
                SolarPlant.source_provider.label("source_provider"),
            )
            .join(
                SolarPlant,
                SolarDevice.solar_plant_id == SolarPlant.id,
            )
            .filter(
                SolarDevice.tenant_id == tenant_id,
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
        )

        if user_role == "CUSTOMER":
            customer = (
                self.db.query(Customer)
                .filter(
                    Customer.user_id == user_id,
                    Customer.tenant_id == tenant_id,
                    Customer.is_active.is_(True),
                )
                .first()
            )

            if customer is None:
                return {
                    "total": 0,
                    "online": 0,
                    "offline": 0,
                    "by_provider": [],
                    "devices": [],
                }

            device_query = device_query.filter(
                SolarPlant.customer_id == customer.id,
            )

        device_rows = (
            device_query
            .order_by(SolarDevice.id)
            .all()
        )

        provider_summary = defaultdict(
            lambda: {
                "total": 0,
                "online": 0,
                "offline": 0,
            }
        )

        device_items = []

        for device, plant_name, source_provider in device_rows:
            status = (
                "ONLINE"
                if device.connect_status == 1
                else "OFFLINE"
            )

            provider = source_provider or "UNKNOWN"

            provider_summary[provider]["total"] += 1

            if status == "ONLINE":
                provider_summary[provider]["online"] += 1
            else:
                provider_summary[provider]["offline"] += 1

            device_items.append(
                {
                    "id": device.id,
                    "solar_plant_id": device.solar_plant_id,
                    "plant_name": plant_name,
                    "source_provider": provider,
                    "solarman_device_id": device.solarman_device_id,
                    "device_sn": device.device_sn,
                    "device_type": device.device_type,
                    "connect_status": status,
                    "collection_time": device.collection_time,
                }
            )

        online = sum(
            1
            for item in device_items
            if item["connect_status"] == "ONLINE"
        )

        offline = sum(
            1
            for item in device_items
            if item["connect_status"] == "OFFLINE"
        )

        by_provider = [
            {
                "provider": provider,
                "total": values["total"],
                "online": values["online"],
                "offline": values["offline"],
            }
            for provider, values in sorted(
                provider_summary.items()
            )
        ]

        return {
            "total": len(device_items),
            "online": online,
            "offline": offline,
            "by_provider": by_provider,
            "devices": device_items,
        }

    def get_sync(
        self,
        tenant_id: int,
    ) -> dict:
        last_sync = (
            self.db.query(GenerationSyncLog)
            .filter(
                GenerationSyncLog.tenant_id == tenant_id,
            )
            .order_by(
                GenerationSyncLog.started_at.desc(),
            )
            .first()
        )

        if last_sync is None:
            return {
                "last_sync_at": None,
                "status": None,
                "started_at": None,
                "finished_at": None,
                "total_plants": 0,
                "successful_plants": 0,
                "failed_plants": 0,
                "total_records_received": 0,
                "total_records_saved": 0,
                "failures": None,
            }

        return {
            "last_sync_at": last_sync.finished_at,
            "status": last_sync.status,
            "started_at": last_sync.started_at,
            "finished_at": last_sync.finished_at,
            "total_plants": last_sync.total_plants,
            "successful_plants": last_sync.successful_plants,
            "failed_plants": last_sync.failed_plants,
            "total_records_received": last_sync.total_records_received,
            "total_records_saved": last_sync.total_records_saved,
            "failures": last_sync.failures,
        }
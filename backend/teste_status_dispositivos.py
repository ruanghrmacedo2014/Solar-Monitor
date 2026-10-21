from sqlalchemy import func

from app.api.database import SessionLocal
from app.models.solar_device import SolarDevice


db = SessionLocal()

try:
    result = (
        db.query(
            SolarDevice.connect_status,
            func.count(SolarDevice.id),
        )
        .group_by(SolarDevice.connect_status)
        .order_by(SolarDevice.connect_status)
        .all()
    )

    print("=== STATUS DOS DISPOSITIVOS ===")

    for status, total in result:
        print(
            f"connect_status={status} | "
            f"total={total}"
        )

finally:
    db.close()
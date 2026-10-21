from sqlalchemy import inspect

from app.api.database import SessionLocal


db = SessionLocal()

try:
    inspector = inspect(db.bind)

    tables = inspector.get_table_names()

    print(
        "generation_aggregates existe:",
        "generation_aggregates" in tables,
    )

    print(
        "Tabelas encontradas:",
        len(tables),
    )

finally:
    db.close()
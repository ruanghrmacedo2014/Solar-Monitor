from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Importa os modelos para garantir que todas as tabelas
# estejam registradas no mesmo Base.metadata.
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_tenant import UserTenant
from app.models.customer import Customer
from app.models.tenant_integration import TenantIntegration
from app.models.solar_plant import SolarPlant


engine = create_engine(
    settings.database_url,
    echo=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
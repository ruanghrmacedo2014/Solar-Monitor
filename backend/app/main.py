from fastapi import FastAPI

from app.api.routes.tenants import router as tenants_router
from app.api.routes.users import router as users_router
from app.api.routes.user_tenants import router as user_tenants_router
from app.api.routes.auth import router as auth_router
from app.api.routes.customers import router as customers_router
from app.api.routes import solar_plants
from app.api.routes import tenant_integrations
from app.api.routes import generation
from app.api.routes import dashboard
from app.api.routes import tags
from app.api.routes import customer_tags
from app.api.routes import tickets
from app.api.routes import platform
from app.api.routes import ticket_tags
from app.api.routes import plant_performance_configs
from app.api.routes.tenant_performance_configs import (
    router as tenant_performance_config_router,
)
from app.api.routes import reports
from contextlib import asynccontextmanager
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.api.routes import notifications

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    stop_scheduler()

app = FastAPI(
    title="Solar Monitor API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(tenants_router)
app.include_router(users_router)
app.include_router(user_tenants_router)
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(solar_plants.router)
app.include_router(tenant_integrations.router)
app.include_router(generation.router)
app.include_router(dashboard.router)
app.include_router(tags.router)
app.include_router(customer_tags.router)
app.include_router(tickets.router)
app.include_router(platform.router)
app.include_router(ticket_tags.router)
app.include_router(plant_performance_configs.router)
app.include_router(tenant_performance_config_router)
app.include_router(reports.router)
app.include_router(notifications.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
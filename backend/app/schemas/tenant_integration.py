from datetime import datetime

from pydantic import BaseModel

from app.models.tenant_integration import IntegrationProvider, SyncStatus


class TenantIntegrationCreate(BaseModel):
    provider: IntegrationProvider
    name: str

class SolarmanCredentialsUpdate(BaseModel):
    app_id: str
    app_secret: str
    email: str
    password: str
    org_id: str | None = None
    language: str = "en"

class TenantIntegrationResponse(BaseModel):
    id: int
    tenant_id: int
    provider: IntegrationProvider
    name: str
    is_active: bool
    last_sync_at: datetime | None
    last_sync_status: SyncStatus
    last_sync_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
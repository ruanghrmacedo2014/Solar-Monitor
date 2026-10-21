from pydantic import BaseModel

from app.models.user_tenant import TenantRole


class UserTenantCreate(BaseModel):
    user_id: int
    tenant_id: int
    role: TenantRole
from pydantic import BaseModel, EmailStr


class TenantCreate(BaseModel):
    name: str
    slug: str
    cnpj: str
    email: EmailStr
    phone: str | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    cnpj: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class TenantSelect(BaseModel):
    tenant_id: int
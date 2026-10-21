from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserTenantResponse(BaseModel):
    tenant_id: int
    tenant_name: str
    role: str

class CreatePasswordRequest(BaseModel):
    token: str
    password: str
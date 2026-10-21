from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    document: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None

class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    document: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None

class CustomerUserLink(BaseModel):
    user_id: int
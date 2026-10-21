from datetime import datetime

from pydantic import BaseModel


class CustomerTagCreate(BaseModel):
    tag_id: int


class CustomerTagResponse(BaseModel):
    id: int
    tenant_id: int
    customer_id: int
    tag_id: int
    created_at: datetime
from datetime import datetime

from pydantic import BaseModel


class TicketTagCreate(BaseModel):
    tag_id: int


class TicketTagResponse(BaseModel):
    id: int
    tenant_id: int
    ticket_id: int
    tag_id: int
    created_at: datetime
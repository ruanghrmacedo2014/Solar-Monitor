from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    color: str = Field(
        min_length=1,
        max_length=20,
    )

    description: str | None = None


class TagUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    color: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    description: str | None = None

    is_active: bool | None = None


class TagResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    tenant_id: int
    name: str
    color: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
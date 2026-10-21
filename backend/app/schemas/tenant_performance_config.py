from pydantic import BaseModel, Field


class TenantPerformanceConfigBase(BaseModel):
    performance_ratio: float | None = Field(
        default=None,
        gt=0,
        le=1,
    )

    availability_target: float | None = Field(
        default=None,
        gt=0,
        le=1,
    )

    degradation_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    alert_threshold_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    configuration_source: str | None = Field(
        default=None,
        max_length=50,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class TenantPerformanceConfigCreate(
    TenantPerformanceConfigBase
):
    pass


class TenantPerformanceConfigUpdate(BaseModel):
    performance_ratio: float | None = Field(
        default=None,
        gt=0,
        le=1,
    )

    availability_target: float | None = Field(
        default=None,
        gt=0,
        le=1,
    )

    degradation_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    alert_threshold_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    configuration_source: str | None = Field(
        default=None,
        max_length=50,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class TenantPerformanceConfigResponse(
    TenantPerformanceConfigBase
):
    id: int
    tenant_id: int
    is_active: bool

    model_config = {
        "from_attributes": True,
    }
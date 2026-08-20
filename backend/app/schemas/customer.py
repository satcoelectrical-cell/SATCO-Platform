from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _CustomerFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=320)

    @field_validator("company", "phone", "email")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CustomerCreate(_CustomerFields):
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Customer name is required")
        return normalized


class CustomerUpdate(_CustomerFields):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_updated_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Customer name is required")
        return normalized

    @model_validator(mode="after")
    def require_update_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one Customer field is required")
        return self


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    name: str
    company: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime

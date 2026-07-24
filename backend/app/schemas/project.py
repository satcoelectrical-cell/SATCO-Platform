from datetime import datetime

from pydantic import BaseModel

from app.enums import ProjectStatus


class CustomerShortResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    customer_id: int


class ProjectUpdate(BaseModel):
    name: str | None = None
    customer_id: int | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    customer: CustomerShortResponse
    status: ProjectStatus
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    customer: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    customer: str |None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
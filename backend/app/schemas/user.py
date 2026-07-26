from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.permissions.roles import Role


class UserRegistration(BaseModel):
    email: str
    username: str
    full_name: Optional[str] = None
    password: str

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    role: Role
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

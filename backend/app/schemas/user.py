from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):

    email: str

    username: str

    full_name: Optional[str] = None

    role: str = "engineer"


class UserCreate(UserBase):

    password: str


class UserResponse(UserBase):

    id: int

    is_active: bool

    created_at: datetime


    model_config = ConfigDict(
        from_attributes=True
    )

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    customer_id: int

    first_name: str

    last_name: Optional[str] = None

    position: Optional[str] = None

    mobile: Optional[str] = None

    phone: Optional[str] = None

    email: Optional[str] = None

    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
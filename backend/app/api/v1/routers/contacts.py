from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
)

from app.services.contact_service import ContactService


router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)

service = ContactService()


@router.get(
    "/",
    response_model=list[ContactResponse],
)
def get_contacts(
    db: Session = Depends(get_db),
):
    return service.get_all(db)


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    contact = service.get_by_id(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return contact


@router.post(
    "/",
    response_model=ContactResponse,
)
def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
):
    return service.create(
        db,
        contact,
    )


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
)
def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
):
    updated = service.update(
        db,
        contact_id,
        contact,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return updated


@router.delete(
    "/{contact_id}",
)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    deleted = service.delete(
        db,
        contact_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return {
        "message": "Contact deleted successfully",
    }
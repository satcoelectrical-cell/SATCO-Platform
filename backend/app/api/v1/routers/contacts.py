from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app import schemas

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


@router.get(
    "/",
    response_model=schemas.PaginatedResponse[
        ContactResponse
    ],
)
def get_contacts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = ContactService(db)

    items, total = service.get_all(
        page,
        size,
        customer_id,
    )

    return schemas.PaginatedResponse[
        ContactResponse
    ](
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = ContactService(db)

    contact = service.get_by_id(
        contact_id
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
    current_user: User = Depends(get_current_user),
):

    service = ContactService(db)

    return service.create(
        contact,
        current_user.id,
    )


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
)
def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = ContactService(db)

    updated = service.update(
        contact_id,
        contact,
        current_user.id,
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
    current_user: User = Depends(get_current_user),
):

    service = ContactService(db)

    deleted = service.delete(
        contact_id,
        current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return {
        "message": "Contact deleted successfully",
        "contact_id": contact_id,
    }

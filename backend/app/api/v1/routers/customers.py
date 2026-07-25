from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.models.user import User

from app import schemas

from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)

from app.services.customer_service import CustomerService


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


@router.get(
    "/",
    response_model=schemas.PaginatedResponse[
        CustomerResponse
    ]
)
def get_customers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = CustomerService(db)

    items, total = service.get_all(
        page,
        size,
        search,
    )

    return schemas.PaginatedResponse[
        CustomerResponse
    ](
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "/",
    response_model=CustomerResponse
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = CustomerService(db)

    return service.create(customer)
from uuid import UUID

from sqlalchemy import exists, or_
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.customer import Customer
from app.models.engineering_object import EngineeringObject
from app.models.project import Project
from app.schemas.customer import CustomerCreate


class CustomerRepository:

    def __init__(self, db: Session):
        self.db = db


    def list_scoped(
        self,
        *,
        organization_id: UUID,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ):

        query = self.db.query(Customer).filter(
            Customer.organization_id == organization_id
        )

        search = search.strip() if search else None
        if search:
            query = query.filter(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.company.ilike(f"%{search}%"),
                    Customer.email.ilike(f"%{search}%"),
                    Customer.phone.ilike(f"%{search}%"),
                )
            )


        total = query.count()

        items = (
            query.order_by(Customer.name.asc(), Customer.id.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return items, total


    def get_scoped(
        self,
        customer_id: int,
        *,
        organization_id: UUID,
    ):
        return self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id,
        ).first()

    def get_by_id(self, customer_id: int):
        """Legacy internal Contact compatibility; not an authority boundary."""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_detail(
        self,
        customer_id: int,
        *,
        organization_id: UUID | None = None,
    ):
        customer = (
            self.get_scoped(customer_id, organization_id=organization_id)
            if organization_id is not None
            else self.get_by_id(customer_id)
        )

        if customer is None:
            return None

        contacts = list(customer.contacts)

        return customer, contacts


    def create(
        self,
        customer: CustomerCreate,
        *,
        organization_id: UUID,
    ):

        db_customer = Customer(
            organization_id=organization_id,
            name=customer.name,
            company=customer.company,
            phone=customer.phone,
            email=customer.email,
        )

        self.db.add(db_customer)
        self.db.flush()
        self.db.refresh(db_customer)

        return db_customer

    def update(
        self,
        customer,
        customer_data: dict,
    ):

        for field, value in customer_data.items():
            setattr(customer, field, value)
        self.db.flush()
        self.db.refresh(customer)

        return customer



    def delete(
        self,
        customer,
    ):

        self.db.delete(customer)
        self.db.flush()

        return True

    def has_governed_references(self, customer_id: int) -> bool:
        return bool(
            self.db.query(
                or_(
                    exists().where(Project.customer_id == customer_id),
                    exists().where(Contact.customer_id == customer_id),
                    exists().where(
                        EngineeringObject.customer_id == customer_id
                    ),
                )
            ).scalar()
        )

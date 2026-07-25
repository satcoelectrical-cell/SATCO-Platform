from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


class CustomerRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ):

        query = self.db.query(Customer)

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
            query
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return items, total


    def get_by_id(self, customer_id: int):
        return (
            self.db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )


    def create(self, customer: CustomerCreate):

        db_customer = Customer(
            name=customer.name,
            company=customer.company,
            phone=customer.phone,
            email=customer.email,
        )

        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)

        return db_customer

    def update(
        self,
        customer,
        customer_data,
    ):

        if customer_data.name is not None:
            customer.name = customer_data.name

        if customer_data.company is not None:
            customer.company = customer_data.company

        if customer_data.phone is not None:
            customer.phone = customer_data.phone

        if customer_data.email is not None:
            customer.email = customer_data.email


        self.db.commit()
        self.db.refresh(customer)

        return customer



    def delete(
        self,
        customer,
    ):

        self.db.delete(customer)
        self.db.commit()

        return True

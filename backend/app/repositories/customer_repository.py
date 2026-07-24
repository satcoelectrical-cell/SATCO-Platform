from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


class CustomerRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Customer).all()

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
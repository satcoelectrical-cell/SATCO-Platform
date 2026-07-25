from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:

    def __init__(self, db: Session):
        self.repository = CustomerRepository(db)


    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ):
        return self.repository.get_all(
            page,
            size,
            search,
        )


    def get_by_id(self, customer_id: int):
        return self.repository.get_by_id(customer_id)


    def create(self, customer: CustomerCreate):
        return self.repository.create(customer)
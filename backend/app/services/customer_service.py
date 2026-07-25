from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate
from app.services.audit_service import create_audit_log


class CustomerService:

    def __init__(self, db: Session):
        self.db = db
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


    def get_by_id(
        self,
        customer_id: int
    ):
        return self.repository.get_by_id(
            customer_id
        )


    def create(
        self,
        customer: CustomerCreate,
        user_id: int,
    ):

        result = self.repository.create(
            customer
        )

        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="CREATE",
            entity="CUSTOMER",
            entity_id=result.id,
            details={
                "customer_name": result.name
            },
        )

        return result


    def update(
        self,
        customer_id: int,
        customer_data,
        user_id: int,
    ):

        customer = self.repository.get_by_id(
            customer_id
        )

        if not customer:
            return None


        result = self.repository.update(
            customer,
            customer_data,
        )


        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="UPDATE",
            entity="CUSTOMER",
            entity_id=result.id,
            details={
                "customer_name": result.name
            },
        )


        return result



    def delete(
        self,
        customer_id: int,
        user_id: int,
    ):

        customer = self.repository.get_by_id(
            customer_id
        )

        if not customer:
            return False


        customer_name = customer.name


        self.repository.delete(
            customer
        )


        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="DELETE",
            entity="CUSTOMER",
            entity_id=customer_id,
            details={
                "customer_name": customer_name
            },
        )


        return True

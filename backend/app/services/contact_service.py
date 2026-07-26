from sqlalchemy.orm import Session

from app.repositories.contact_repository import ContactRepository
from app.repositories.customer_repository import CustomerRepository
from app.schemas.contact import ContactCreate, ContactUpdate
from app.services.audit_service import create_audit_log


class ContactService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ContactRepository(db)
        self.customer_repository = CustomerRepository(db)


    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        customer_id: int | None = None,
    ):
        return self.repository.get_all(
            page,
            size,
            customer_id,
        )


    def get_by_id(
        self,
        contact_id: int
    ):
        return self.repository.get_by_id(
            contact_id
        )


    def create(
        self,
        contact: ContactCreate,
        user_id: int,
    ):
        customer = self.customer_repository.get_by_id(
            contact.customer_id
        )

        if customer is None:
            raise ValueError("Customer not found")

        result = self.repository.create(
            contact
        )

        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="CREATE",
            entity="CONTACT",
            entity_id=result.id,
            details={
                "contact_name": f"{result.first_name} {result.last_name}"
            },
        )

        return result


    def update(
        self,
        contact_id: int,
        contact_data: ContactUpdate,
        user_id: int,
    ):

        contact = self.repository.get_by_id(
            contact_id
        )

        if not contact:
            return None


        result = self.repository.update(
            contact,
            contact_data,
        )


        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="UPDATE",
            entity="CONTACT",
            entity_id=result.id,
            details={
                "contact_name": f"{result.first_name} {result.last_name}"
            },
        )


        return result


    def delete(
        self,
        contact_id: int,
        user_id: int,
    ):

        contact = self.repository.get_by_id(
            contact_id
        )

        if not contact:
            return False


        contact_name = f"{contact.first_name} {contact.last_name}"


        self.repository.delete(
            contact
        )


        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="DELETE",
            entity="CONTACT",
            entity_id=contact_id,
            details={
                "contact_name": contact_name
            },
        )


        return True

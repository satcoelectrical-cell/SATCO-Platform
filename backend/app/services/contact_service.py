from sqlalchemy.orm import Session

from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactUpdate


class ContactService:

    def __init__(self):
        self.repository = ContactRepository()


    def get_all(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        customer_id: int | None = None,
    ):
        return self.repository.get_all(
            db,
            page,
            size,
            customer_id,
        )


    def get_by_id(
        self,
        db: Session,
        contact_id: int
    ):
        return self.repository.get_by_id(
            db,
            contact_id
        )


    def create(
        self,
        db: Session,
        contact: ContactCreate
    ):
        return self.repository.create(
            db,
            contact
        )


    def update(
        self,
        db: Session,
        contact_id: int,
        contact: ContactUpdate
    ):
        db_contact = self.repository.get_by_id(
            db,
            contact_id
        )

        if not db_contact:
            return None

        return self.repository.update(
            db,
            db_contact,
            contact
        )


    def delete(
        self,
        db: Session,
        contact_id: int
    ):
        db_contact = self.repository.get_by_id(
            db,
            contact_id
        )

        if not db_contact:
            return False

        self.repository.delete(
            db,
            db_contact
        )

        return True
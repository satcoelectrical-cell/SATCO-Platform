from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


class ContactRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        customer_id: int | None = None,
    ):
        query = self.db.query(Contact)

        if customer_id:
            query = query.filter(
                Contact.customer_id == customer_id
            )

        total = query.count()

        items = (
            query
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return items, total

    def get_by_id(
        self,
        contact_id: int,
    ):
        return (
            self.db.query(Contact)
            .filter(Contact.id == contact_id)
            .first()
        )

    def create(
        self,
        contact: ContactCreate,
    ):
        db_contact = Contact(
            **contact.model_dump()
        )

        self.db.add(db_contact)
        self.db.commit()
        self.db.refresh(db_contact)

        return db_contact

    def update(
        self,
        db_contact: Contact,
        contact: ContactUpdate,
    ):
        update_data = contact.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(db_contact, key, value)

        self.db.commit()
        self.db.refresh(db_contact)

        return db_contact

    def delete(
        self,
        db_contact: Contact,
    ):
        self.db.delete(db_contact)
        self.db.commit()
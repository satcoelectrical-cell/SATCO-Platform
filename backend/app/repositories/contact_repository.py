from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


class ContactRepository:

    def get_all(
        self,
        db: Session
    ):
        return db.query(Contact).all()

    def get_by_id(
        self,
        db: Session,
        contact_id: int
    ):
        return (
            db.query(Contact)
            .filter(Contact.id == contact_id)
            .first()
        )

    def create(
        self,
        db: Session,
        contact: ContactCreate
    ):
        db_contact = Contact(**contact.model_dump())

        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)

        return db_contact

    def update(
        self,
        db: Session,
        db_contact: Contact,
        contact: ContactUpdate
    ):
        update_data = contact.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_contact, key, value)

        db.commit()
        db.refresh(db_contact)

        return db_contact

    def delete(
        self,
        db: Session,
        db_contact: Contact
    ):
        db.delete(db_contact)
        db.commit()
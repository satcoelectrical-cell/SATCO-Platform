from typing import Generic
from typing import TypeVar

from sqlalchemy.orm import Session


ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        model: type[ModelType],
    ):
        self.model = model

    def get(
        self,
        db: Session,
        object_id: int,
    ):
        return (
            db.query(self.model)
            .filter(self.model.id == object_id)
            .first()
        )

    def list(
        self,
        db: Session,
    ):
        return db.query(self.model).all()

    def create(
        self,
        db: Session,
        obj,
    ):
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(
        self,
        db: Session,
        obj,
    ):
        db.delete(obj)
        db.commit()

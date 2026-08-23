"""One authoritative Session boundary for Supporting File mutations."""
from sqlalchemy.orm import Session

from app.repositories.supporting_file_repository import SqlAlchemySupportingFileRepository


class SqlAlchemySupportingFileUnitOfWork:
    def __init__(self, session: Session):
        self.session = session
        self.repository = SqlAlchemySupportingFileRepository(session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

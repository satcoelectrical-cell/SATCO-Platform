"""Query/stage-only SQLAlchemy adapter for Engineering Identifiers."""

from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_object import EngineeringObject


class SqlAlchemyEngineeringIdentifierRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_object_locked(self, object_id: UUID, organization_id: UUID):
        return self.session.query(EngineeringObject).filter_by(
            id=object_id, organization_id=organization_id,
        ).with_for_update().one_or_none()

    def get_locked(self, identifier_id: UUID, organization_id: UUID):
        return self.session.query(EngineeringIdentifier).filter_by(
            identifier_id=identifier_id, organization_id=organization_id,
        ).with_for_update().one_or_none()

    def get_object_id(self, identifier_id: UUID, organization_id: UUID):
        return self.session.scalar(select(
            EngineeringIdentifier.engineering_object_id
        ).where(
            EngineeringIdentifier.identifier_id == identifier_id,
            EngineeringIdentifier.organization_id == organization_id,
        ))

    def current_set_locked(self, object_id: UUID, organization_id: UUID):
        return list(self.session.query(EngineeringIdentifier).filter_by(
            engineering_object_id=object_id,
            organization_id=organization_id,
            lifecycle="current",
        ).order_by(
            EngineeringIdentifier.primary_role.desc(),
            EngineeringIdentifier.identifier_kind,
            EngineeringIdentifier.normalized_value,
            EngineeringIdentifier.identifier_id,
        ).with_for_update().all())

    def history(self, object_id: UUID, organization_id: UUID, *, limit: int, before=None):
        query = self.session.query(EngineeringIdentifier).filter_by(
            engineering_object_id=object_id, organization_id=organization_id,
        )
        if before is not None:
            created_at, identifier_id = before
            query = query.filter(or_(
                EngineeringIdentifier.created_at < created_at,
                (EngineeringIdentifier.created_at == created_at) &
                (EngineeringIdentifier.identifier_id < identifier_id),
            ))
        return list(query.order_by(
            EngineeringIdentifier.created_at.desc(),
            EngineeringIdentifier.identifier_id.desc(),
        ).limit(limit).all())

    def add(self, value) -> None:
        self.session.add(value)
        self.session.flush()

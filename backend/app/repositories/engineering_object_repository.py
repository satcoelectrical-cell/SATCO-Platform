"""SQLAlchemy persistence adapter for EngineeringObject aggregates."""

from typing import Mapping
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import Scalar


class SqlAlchemyEngineeringObjectRepository:
    """Persist complete aggregates without authorization or transaction control."""

    def __init__(self, session: Session):
        self.session = session

    def _query(self):
        return self.session.query(EngineeringObject).options(
            joinedload(EngineeringObject.customer),
            joinedload(EngineeringObject.project),
            joinedload(EngineeringObject.workspace),
            joinedload(EngineeringObject.creator),
            joinedload(EngineeringObject.steward),
        )

    def get_authorized(
        self, object_id: UUID, organization_id: UUID
    ) -> EngineeringObject | None:
        item = self._query().filter(
            EngineeringObject.id == object_id,
            EngineeringObject.organization_id == organization_id,
        ).first()
        if item is not None:
            self.session.expunge(item)
        return item

    def list_authorized(
        self, *, organization_id: UUID, project_id: int,
        filters: Mapping[str, Scalar], page: int, size: int,
    ) -> tuple[list[EngineeringObject], int]:
        query = self._query().filter(
            EngineeringObject.organization_id == organization_id,
            EngineeringObject.project_id == project_id,
        )
        for name in (
            "workspace_id", "family", "discipline", "object_type",
            "lifecycle", "authority_standing",
        ):
            value = filters.get(name)
            if value is not None:
                value = getattr(value, "value", value)
                query = query.filter(getattr(EngineeringObject, name) == value)
        total = query.count()
        items = query.order_by(EngineeringObject.created_at, EngineeringObject.id).offset(
            (page - 1) * size
        ).limit(size).all()
        for item in items:
            self.session.expunge(item)
        return items, total

    def add(self, engineering_object: EngineeringObject) -> None:
        self.session.add(engineering_object)
        self.session.flush()

    def persist_expected_version(
        self, engineering_object: EngineeringObject, expected_version: int
    ) -> bool:
        values = {
            "family": engineering_object.family,
            "discipline": engineering_object.discipline,
            "object_type": engineering_object.object_type,
            "subtype": engineering_object.subtype,
            "lifecycle": engineering_object.lifecycle,
            "authority_standing": engineering_object.authority_standing,
            "steward_id": engineering_object.steward_id,
            "version": engineering_object.version,
            "updated_at": engineering_object.updated_at,
        }
        result = self.session.execute(
            update(EngineeringObject).where(
                EngineeringObject.id == engineering_object.id,
                EngineeringObject.organization_id
                == engineering_object.organization_id,
                EngineeringObject.version == expected_version,
            ).values(**values)
        )
        self.session.flush()
        return result.rowcount == 1


"""SQLAlchemy Capture repository with no transaction or policy ownership."""

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.engineering_experience_capture import EngineeringExperienceCapture


class SqlAlchemyEngineeringExperienceCaptureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, capture: EngineeringExperienceCapture) -> None:
        self.session.add(capture)
        self.session.flush()

    def get_scoped(self, capture_id: UUID, organization_id: UUID):
        capture = self.session.query(EngineeringExperienceCapture).filter_by(
            id=capture_id, organization_id=organization_id
        ).first()
        if capture is not None:
            self.session.expunge(capture)
        return capture

    def _list(self, *, organization_id: UUID, project_id: int, workspace_id: int | None,
              filters: Mapping[str, object], page: int, size: int,
              authorized_workspace_ids=None):
        query = self.session.query(EngineeringExperienceCapture).filter_by(
            organization_id=organization_id, project_id=project_id
        )
        if workspace_id is not None:
            query = query.filter(EngineeringExperienceCapture.workspace_id == workspace_id)
        elif authorized_workspace_ids is not None:
            query = query.filter(
                EngineeringExperienceCapture.workspace_id.in_(authorized_workspace_ids)
            )
        for name in ("lifecycle", "source_kind", "creator_id", "engineering_object_id"):
            value = filters.get(name)
            if value is not None:
                query = query.filter(getattr(EngineeringExperienceCapture, name) == getattr(value, "value", value))
        total = query.count()
        items = query.order_by(
            EngineeringExperienceCapture.created_at.desc(),
            EngineeringExperienceCapture.id.desc(),
        ).offset((page - 1) * size).limit(size).all()
        return items, total

    def list_project_scoped(self, **values):
        return self._list(workspace_id=None, **values)

    def list_workspace_scoped(self, **values):
        return self._list(**values)

    def persist_expected_version(self, capture: EngineeringExperienceCapture, expected_version: int) -> bool:
        if capture in self.session:
            self.session.expunge(capture)
        with self.session.no_autoflush:
            result = self.session.execute(
                update(EngineeringExperienceCapture)
                .where(
                    EngineeringExperienceCapture.id == capture.id,
                    EngineeringExperienceCapture.organization_id == capture.organization_id,
                    EngineeringExperienceCapture.version == expected_version,
                )
                .values(
                    lifecycle=capture.lifecycle,
                    superseded_by_capture_id=capture.superseded_by_capture_id,
                    version=capture.version,
                    updated_at=capture.updated_at,
                )
                .execution_options(synchronize_session=False)
            )
        self.session.flush()
        return result.rowcount == 1

    def replacement_is_used(self, replacement_capture_id: UUID) -> bool:
        return self.session.query(EngineeringExperienceCapture.id).filter(
            EngineeringExperienceCapture.superseded_by_capture_id == replacement_capture_id
        ).first() is not None

    def predecessor_chain(self, capture_id: UUID, *, maximum_depth: int):
        chain = []
        current_id = capture_id
        seen: set[UUID] = set()
        for _ in range(maximum_depth):
            if current_id in seen:
                break
            seen.add(current_id)
            item = self.session.query(EngineeringExperienceCapture).filter(
                EngineeringExperienceCapture.superseded_by_capture_id == current_id
            ).first()
            if item is None:
                break
            chain.append(item)
            current_id = item.id
        return tuple(chain)

"""SQLAlchemy Capture repository with no transaction or policy ownership."""

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureReadPage,
    EngineeringExperienceCaptureSummary,
)


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

    def read_authorized_page(
        self,
        *,
        organization_id: UUID,
        project_id: int,
        workspace_id: int | None,
        engineering_object_id: UUID | None,
        lifecycle: EngineeringExperienceCaptureLifecycle,
        source_kind: EngineeringExperienceSourceKind | None,
        discipline: str | None,
        page: int,
        size: int,
        authorized_workspace_ids: tuple[int, ...] | None,
    ) -> EngineeringExperienceCaptureReadPage:
        """Return one selected-field page and protected counts without writes."""

        query = self.session.query(EngineeringExperienceCapture).filter(
            EngineeringExperienceCapture.organization_id == organization_id,
            EngineeringExperienceCapture.project_id == project_id,
            EngineeringExperienceCapture.lifecycle
            == getattr(lifecycle, "value", lifecycle),
        )
        if workspace_id is not None:
            query = query.filter(
                EngineeringExperienceCapture.workspace_id == workspace_id
            )
        elif authorized_workspace_ids is not None:
            query = query.filter(
                EngineeringExperienceCapture.workspace_id.in_(
                    authorized_workspace_ids
                )
            )
        if engineering_object_id is not None:
            query = query.filter(
                EngineeringExperienceCapture.engineering_object_id
                == engineering_object_id
            )

        authorized_total = query.count()
        if source_kind is not None:
            query = query.filter(
                EngineeringExperienceCapture.source_kind
                == getattr(source_kind, "value", source_kind)
            )
        if discipline is not None:
            query = query.filter(
                EngineeringExperienceCapture.discipline == discipline
            )
        filtered_total = query.count()

        rows = (
            query.with_entities(
                EngineeringExperienceCapture.id,
                EngineeringExperienceCapture.project_id,
                EngineeringExperienceCapture.workspace_id,
                EngineeringExperienceCapture.discipline,
                EngineeringExperienceCapture.engineering_object_id,
                EngineeringExperienceCapture.source_kind,
                EngineeringExperienceCapture.creator_id,
                EngineeringExperienceCapture.lifecycle,
                EngineeringExperienceCapture.version,
                EngineeringExperienceCapture.created_at,
                EngineeringExperienceCapture.updated_at,
            )
            .order_by(
                EngineeringExperienceCapture.created_at.desc(),
                EngineeringExperienceCapture.id.desc(),
            )
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        items = tuple(
            EngineeringExperienceCaptureSummary(
                id=row.id,
                project_id=row.project_id,
                workspace_id=row.workspace_id,
                discipline=row.discipline,
                engineering_object_id=row.engineering_object_id,
                source_kind=row.source_kind,
                creator_id=row.creator_id,
                lifecycle=row.lifecycle,
                version=row.version,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        )
        return EngineeringExperienceCaptureReadPage(
            items=items,
            authorized_total=authorized_total,
            filtered_total=filtered_total,
            visible_total=len(items),
            page=page,
            size=size,
        )

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

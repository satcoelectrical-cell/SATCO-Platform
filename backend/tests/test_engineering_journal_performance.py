"""PATCH-029 Sprint 2 structural performance-boundary evidence."""

import ast
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.adapters.engineering_journal import EngineeringJournalCaptureReadAdapter
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.enums.engineering_journal import EngineeringJournalView
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureIdempotency,
    EngineeringExperienceCaptureOutbox,
)
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.organization import UserOrganizationMembership
from app.exceptions.project import ProjectForbiddenException
import pytest
from app.repositories.engineering_experience_capture_repository import (
    SqlAlchemyEngineeringExperienceCaptureRepository,
)
from app.schemas.project import ProjectSelectionActor
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)
from app.services.project_service import ProjectService

from test_engineering_journal_service import CapturePort, _actor, _service
from test_engineering_experience_capture_service import (
    SharedSessionCaptureUnitOfWork,
    _actor as capture_actor,
    _create as create_capture,
    _service as capture_service,
)


def test_projectless_shell_performs_zero_capture_page_operations() -> None:
    service, _, _, capture, _ = _service()
    service.workspace(actor=_actor(), view=EngineeringJournalView.INBOX)
    assert capture.list_calls == []


def test_unavailable_views_perform_zero_capture_page_operations() -> None:
    service, _, _, capture, _ = _service()
    service.workspace(
        actor=_actor(), view=EngineeringJournalView.DRAFTS, project_id=10
    )
    assert capture.list_calls == []


def test_member_view_uses_exactly_one_bounded_page_operation() -> None:
    capture = CapturePort((), 0, 0)
    service, _, _, _, _ = _service(capture)
    service.workspace(
        actor=_actor(), view=EngineeringJournalView.INBOX, project_id=10
    )
    assert len(capture.list_calls) == 1
    assert capture.list_calls[0][3].size == 20


def test_sprint_two_application_has_no_persistence_or_transport_imports() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    paths = (
        backend_root / "app/adapters/engineering_journal.py",
        backend_root / "app/services/engineering_journal_service.py",
    )
    forbidden = {
        "fastapi",
        "sqlalchemy",
        "alembic",
        "app.repositories",
        "app.api",
    }
    for path in paths:
        tree = ast.parse(path.read_text())
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imports.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert not any(
            name == root or name.startswith(f"{root}.")
            for name in imports
            for root in forbidden
        )


def test_no_journal_transaction_or_write_operations_exist() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    source = "\n".join(
        (backend_root / path).read_text()
        for path in (
            "app/adapters/engineering_journal.py",
            "app/services/engineering_journal_service.py",
        )
    )
    for forbidden in (
        ".commit(",
        ".rollback(",
        ".flush(",
        ".add(",
        ".delete(",
        "UnitOfWork",
        "Session",
    ):
        assert forbidden not in source


def test_canonical_reads_create_no_audit_outbox_or_idempotency_writes(
    db_session, relationship_domain
) -> None:
    service = capture_service(db_session)
    actor = capture_actor(relationship_domain)
    created = create_capture(service, relationship_domain, actor)
    before = (
        db_session.query(AuditLog).count(),
        db_session.query(EngineeringExperienceCaptureOutbox).count(),
        db_session.query(EngineeringExperienceCaptureIdempotency).count(),
    )
    service.read_authorized_page(
        actor=actor,
        project_id=relationship_domain["project"].id,
        workspace_id=relationship_domain["consumer_workspace"].id,
        engineering_object_id=None,
        lifecycle="captured",
        source_kind=None,
        discipline=None,
        page=1,
        size=20,
    )
    service.read_authorized_detail(
        actor=actor,
        project_id=relationship_domain["project"].id,
        workspace_id=relationship_domain["consumer_workspace"].id,
        engineering_object_id=None,
        capture_id=created.id,
    )
    after = (
        db_session.query(AuditLog).count(),
        db_session.query(EngineeringExperienceCaptureOutbox).count(),
        db_session.query(EngineeringExperienceCaptureIdempotency).count(),
    )
    assert after == before


def test_project_selection_continues_safely_beyond_one_hundred(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    actor = domain["actors"]["consumer"]
    projects = [
        Project(
            organization_id=domain["project"].organization_id,
            project_code=f"SAT-PRJ-2088-{index + 5000:04d}",
            name=f"Authorized Continuation {index:03d}",
            customer_id=domain["project"].customer_id,
            owner_id=actor.id,
            status="new",
            priority="medium",
            progress=0,
        )
        for index in range(101)
    ]
    db_session.add_all(projects)
    db_session.flush()
    service = ProjectService(db_session)
    selection_actor = ProjectSelectionActor(
        actor_id=actor.id,
        organization_id=domain["project"].organization_id,
    )
    first = service.list_authorized_selection(
        actor=selection_actor, page=1, size=100
    )
    second = service.list_authorized_selection(
        actor=selection_actor, page=2, size=100
    )
    combined = first.items + second.items
    assert first.returned_count == 100
    assert first.has_more is True
    assert second.has_more is False
    assert len(combined) > 100
    assert [(item.display_name, item.project_id) for item in combined] == sorted(
        (item.display_name, item.project_id) for item in combined
    )
    assert "total" not in type(first).model_fields


def test_each_project_continuation_page_reauthorizes_current_membership(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    actor = domain["actors"]["project_owner"]
    selection_actor = ProjectSelectionActor(
        actor_id=actor.id,
        organization_id=domain["project"].organization_id,
    )
    service = ProjectService(db_session)
    service.list_authorized_selection(actor=selection_actor, page=1, size=1)
    membership = db_session.get(
        UserOrganizationMembership,
        (actor.id, domain["project"].organization_id),
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    with pytest.raises(ProjectForbiddenException):
        service.list_authorized_selection(
            actor=selection_actor, page=2, size=1
        )


def test_capture_summary_order_is_deterministic_by_timestamp_then_uuid(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    timestamp = datetime(2026, 8, 8, tzinfo=timezone.utc)
    lower = UUID("00000000-0000-4000-8000-000000000001")
    higher = UUID("00000000-0000-4000-8000-000000000002")
    records = [
        EngineeringExperienceCapture(
            id=identifier,
            organization_id=domain["project"].organization_id,
            project_id=domain["project"].id,
            workspace_id=domain["consumer_workspace"].id,
            discipline="electrical",
            engineering_object_id=None,
            source_kind=EngineeringExperienceSourceKind.OBSERVATION.value,
            original_content="Detail-only plaintext",
            creator_id=domain["actors"]["project_owner"].id,
            lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED.value,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
        )
        for identifier in (lower, higher)
    ]
    db_session.add_all(records)
    db_session.flush()
    page = SqlAlchemyEngineeringExperienceCaptureRepository(
        db_session
    ).read_authorized_page(
        organization_id=domain["project"].organization_id,
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        engineering_object_id=None,
        lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED,
        source_kind=None,
        discipline=None,
        page=1,
        size=20,
        authorized_workspace_ids=None,
    )
    assert [item.id for item in page.items] == [higher, lower]
    assert "original_content" not in type(page.items[0]).model_fields


def test_capture_adapter_privately_owns_canonical_service_construction(
    db_session,
) -> None:
    adapter = EngineeringJournalCaptureReadAdapter(
        uow_factory=lambda: SharedSessionCaptureUnitOfWork(db_session)
    )
    assert isinstance(
        adapter._capture_service, EngineeringExperienceCaptureService
    )
    assert not hasattr(adapter, "uow_factory")

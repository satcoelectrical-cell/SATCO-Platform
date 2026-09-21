from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.adapters.engineering_performance import (
    EngineeringPerformanceProtectedNotFound, EngineeringPerformanceScope,
    EngineeringPerformanceSourceAdapter,
)
from app.enums.technical_report import TechnicalReportLifecycle
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
from app.models.technical_report_command import TechnicalReportActor, TechnicalReportDomainEvent
from app.ports.technical_report import TechnicalReportLifecycleEvidencePage
from app.services.engineering_performance import technical_report_acceptance_flow
from app.services.technical_report_service import TechnicalReportService


CUTOFF = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)


class Clock:
    def now(self): return CUTOFF


class Authorization:
    def __init__(self, allowed=True): self.allowed = allowed; self.calls = 0
    def require(self, request):
        self.calls += 1
        assert request.operation == "list_lifecycle_evidence"
        if not self.allowed:
            raise TechnicalReportAuthorizationDenied()


class Repository:
    def __init__(self, reports): self.reports = reports; self.reads = 0
    def list_lifecycle_roots(self, *, scope, limit):
        self.reads += 1
        assert limit == 1001 and scope.project_id == 7
        return tuple(SimpleNamespace(id=report.id, updated_at=report.updated_at)
                     for report in self.reports)
    def get_scoped(self, report_id, organization_id):
        self.reads += 1
        return next((report for report in self.reports
                     if report.id == report_id and report.organization_id == organization_id), None)


class Uow:
    def __init__(self, reports, allowed=True):
        self.authorization = Authorization(allowed)
        self.technical_reports = Repository(reports)
        self.commits = 0
    def __enter__(self): return self
    def __exit__(self, *_args): pass
    def commit(self): self.commits += 1


def report(organization_id, *, accepted=False, predecessor=None, created_at=None):
    created = created_at or CUTOFF - timedelta(days=2)
    accepted_at = created + timedelta(days=1) if accepted else None
    return SimpleNamespace(
        id=uuid4(), organization_id=organization_id, project_id=7, workspace_id=11,
        version=2 if accepted else 1,
        lifecycle=TechnicalReportLifecycle.ACCEPTED if accepted else TechnicalReportLifecycle.DRAFT,
        created_at=created, updated_at=accepted_at or created,
        acceptance_record=None if not accepted else SimpleNamespace(
            accepted_at=accepted_at, snapshot_digest="a" * 64,
            accepted_aggregate_version=2,
        ),
        predecessor_report_id=predecessor,
    )


def test_canonical_lifecycle_has_no_review_state_or_event():
    assert set(TechnicalReportLifecycle) == {TechnicalReportLifecycle.DRAFT, TechnicalReportLifecycle.ACCEPTED}
    assert "TechnicalReportReviewed" not in inspect.getsource(TechnicalReportDomainEvent)


def test_owner_authorized_read_exposes_draft_acceptance_and_independent_lineage():
    organization_id = uuid4()
    actor = TechnicalReportActor(3, organization_id)
    predecessor = report(organization_id, accepted=True)
    successor = report(organization_id, predecessor=predecessor.id,
                       created_at=CUTOFF - timedelta(hours=12))
    uow = Uow([predecessor, successor])
    owner = TechnicalReportService(lambda: uow, Clock())
    page = owner.list_authorized_lifecycle_evidence(actor=actor, project_id=7)
    assert isinstance(page, TechnicalReportLifecycleEvidencePage)
    assert page.complete and len(page.items) == 2
    accepted, draft = page.items
    assert accepted.accepted_at == predecessor.acceptance_record.accepted_at
    assert accepted.accepted_snapshot_digest == predecessor.acceptance_record.snapshot_digest
    assert draft.accepted_at is None and draft.accepted_snapshot_digest is None
    assert draft.predecessor_report_id == accepted.report_id
    assert accepted.predecessor_report_id is None
    assert uow.commits == 0
    # Successor creation does not reopen or lengthen the predecessor's own cycle.
    observed = technical_report_acceptance_flow(
        [replace(accepted, report_id=uuid4()) for _ in range(5)] + [draft], source_cutoff=CUTOFF,
    )
    assert observed.value["average_acceptance_hours"] == 24


def test_denial_precedes_owner_report_selection_and_overflow_is_not_complete():
    organization_id = uuid4()
    actor = TechnicalReportActor(3, organization_id)
    denied = Uow([report(organization_id)], allowed=False)
    owner = TechnicalReportService(lambda: denied, Clock())
    with pytest.raises(TechnicalReportAuthorizationDenied):
        owner.list_authorized_lifecycle_evidence(actor=actor, project_id=7)
    assert denied.technical_reports.reads == 0
    many = Uow([report(organization_id)] * 1001)
    assert TechnicalReportService(lambda: many, Clock()).list_authorized_lifecycle_evidence(
        actor=actor, project_id=7,
    ) is None
    assert many.technical_reports.reads == 1


def test_patch056_adapter_consumes_owner_read_without_report_write_or_orm():
    organization_id = uuid4()
    scope = EngineeringPerformanceScope(organization_id, 7, None, 3)
    page = TechnicalReportService(lambda: Uow([report(organization_id)]), Clock()).list_authorized_lifecycle_evidence(
        actor=TechnicalReportActor(3, organization_id), project_id=7,
    )

    class NoOrm:
        def query(self, *_args): raise AssertionError("PATCH-056 must not query Technical Report ORM")

    class Policy:
        def __init__(self, allowed=True): self.allowed = allowed
        def authorize(self, **_kwargs): return self.allowed

    class Owner:
        reads = 0
        def list_authorized_lifecycle_evidence(self, **_kwargs):
            self.reads += 1
            return page

    owner = Owner()
    adapter = EngineeringPerformanceSourceAdapter(NoOrm(), authorization_policy=Policy(),
                                                  technical_report_service=owner)
    assert len(adapter.technical_report_rows(scope).items) == 1
    assert owner.reads == 1
    denied = EngineeringPerformanceSourceAdapter(NoOrm(), authorization_policy=Policy(False),
                                                 technical_report_service=owner)
    with pytest.raises(EngineeringPerformanceProtectedNotFound):
        denied.technical_report_rows(scope)
    assert owner.reads == 1

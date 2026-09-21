from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.adapters.engineering_performance import (
    EngineeringPerformanceProtectedNotFound, EngineeringPerformanceScope,
    EngineeringPerformanceSourceAdapter,
)
from app.api.v1.routers.engineering_performance import _observations
from app.schemas.project_control import ControlActor, ControlAgingEvidencePage
from app.services.engineering_performance import risk_issue_change_aging_from_evidence
from app.services.project_control_service import ProjectControlService


NOW = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)


class Repository:
    def __init__(self, organization_id, rows):
        self.organization_id = organization_id
        self.rows = rows
        self.page_reads = 0
        self.fail_after_first = False

    def get_project(self, *, project_id, organization_id):
        if project_id != 7 or organization_id != self.organization_id:
            return None
        return SimpleNamespace(id=7, organization_id=organization_id,
                               owner_id=3, primary_assignee_id=None)

    def aging_population_changed(self, kind, **_kwargs):
        return self.fail_after_first and self.page_reads > 0

    def list_aging_page(self, kind, *, organization_id, project_id, workspace_id,
                        cutoff, after, limit):
        self.page_reads += 1
        selected = sorted((row for row in self.rows[kind]
                           if row.organization_id == organization_id
                           and row.project_id == project_id
                           and (workspace_id is None or row.workspace_id == workspace_id)
                           and row.created_at <= cutoff
                           and (after is None or (row.created_at, row.id) > after)),
                          key=lambda row: (row.created_at, row.id))
        return selected[:limit + 1]


class Uow:
    def __init__(self, repository): self.repository = repository; self.committed = False
    def __enter__(self): return self
    def __exit__(self, *_args): pass
    def commit(self): self.committed = True


class Authorization:
    def __init__(self, allowed=True): self.allowed = allowed
    def can_read_project(self, **_kwargs): return self.allowed


class Policy:
    def __init__(self, allowed=True): self.allowed = allowed
    def authorize(self, **_kwargs): return self.allowed


def row(organization_id, kind, ordinal, *, standing=None, workspace_id=11):
    defaults = {"risk": "open", "issue": "open", "change": "recorded"}
    created = NOW - timedelta(days=3, minutes=ordinal)
    return SimpleNamespace(id=uuid4(), kind=kind, organization_id=organization_id, project_id=7,
                           workspace_id=workspace_id, created_at=created,
                           updated_at=created, standing=standing or defaults[kind], version=1)


def service(repository, *, authorized=True):
    uow = Uow(repository)
    return ProjectControlService(uow_factory=lambda: uow,
                                 authorization=Authorization(authorized),
                                 clock=lambda: NOW), uow


def test_owner_pages_more_than_100_without_duplicate_or_omission():
    organization_id = uuid4()
    rows = [row(organization_id, "risk", index) for index in range(205)]
    repo = Repository(organization_id, {"risk": rows, "issue": [], "change": []})
    owner, uow = service(repo)
    actor = ControlActor(actor_id=3, organization_id=organization_id)
    seen = []
    continuation = None
    while True:
        page = owner.list_authorized_aging_evidence(
            kind="risk", project_id=7, actor=actor, workspace_id=11,
            page_size=100, continuation=continuation,
        )
        assert isinstance(page, ControlAgingEvidencePage)
        seen.extend(page.items)
        if page.complete:
            assert page.next_continuation is None
            break
        assert len(page.items) == 100 and page.next_continuation
        continuation = page.next_continuation
    assert [item.id for item in seen] == [item.id for item in sorted(rows, key=lambda r: (r.created_at, r.id))]
    assert len(seen) == 205 and repo.page_reads == 3
    assert all(item.created_at == next(row.created_at for row in rows if row.id == item.id)
               for item in seen)
    assert not uow.committed


def test_owner_denies_before_protected_page_selection_and_binds_continuation():
    organization_id = uuid4()
    repo = Repository(organization_id, {"risk": [row(organization_id, "risk", index)
                                                for index in range(101)],
                                        "issue": [], "change": []})
    actor = ControlActor(actor_id=3, organization_id=organization_id)
    denied, _ = service(repo, authorized=False)
    assert denied.list_authorized_aging_evidence(kind="risk", project_id=7,
                                                 actor=actor).outcome == "protected_not_found"
    assert repo.page_reads == 0
    owner, _ = service(repo)
    first = owner.list_authorized_aging_evidence(kind="risk", project_id=7,
                                                 actor=actor, page_size=100)
    assert first.next_continuation
    other_actor = ControlActor(actor_id=4, organization_id=organization_id)
    assert owner.list_authorized_aging_evidence(kind="risk", project_id=7,
                                                actor=other_actor, page_size=100,
                                                continuation=first.next_continuation).outcome == "invalid_request"
    assert owner.list_authorized_aging_evidence(kind="risk", project_id=7,
                                                actor=actor, workspace_id=11,
                                                page_size=100,
                                                continuation=first.next_continuation).outcome == "invalid_request"
    assert repo.page_reads == 1
    foreign = ControlActor(actor_id=3, organization_id=uuid4())
    assert owner.list_authorized_aging_evidence(kind="risk", project_id=7,
                                                actor=foreign).outcome == "protected_not_found"
    assert repo.page_reads == 1


def test_patch056_requires_complete_owner_traversal_and_never_queries_control_orm():
    organization_id = uuid4()
    repo = Repository(organization_id, {"risk": [row(organization_id, "risk", index)
                                                for index in range(101)],
                                        "issue": [], "change": []})
    owner, uow = service(repo)

    class NoOrm:
        def query(self, *_args): raise AssertionError("PATCH-056 must not query Project Control ORM")

    scope = EngineeringPerformanceScope(organization_id, 7, None, 3)
    adapter = EngineeringPerformanceSourceAdapter(NoOrm(), authorization_policy=Policy(),
                                                  project_control_service=owner, clock=lambda: NOW)
    complete = adapter.control_aging_rows(scope)
    assert complete is not None and len(complete.items) == 101
    repo.page_reads = 0
    repo.fail_after_first = True
    assert adapter.control_aging_rows(scope) is None
    assert not uow.committed
    denied = EngineeringPerformanceSourceAdapter(NoOrm(), authorization_policy=Policy(False),
                                                 project_control_service=owner, clock=lambda: NOW)
    with pytest.raises(EngineeringPerformanceProtectedNotFound):
        denied.control_aging_rows(scope)

    class IncompleteSources:
        def required_input_standings(self, _scope): return []
        def execution_activity_rows(self, _scope): return []
        def milestone_rows(self, _scope): return []
        def deliverable_transition_rows(self, _scope): return []
        def control_aging_rows(self, _scope): return None
        def interface_commitment_rows(self, _scope): return None
        def completeness_history(self, _scope, *, window_days): return None
        def technical_report_rows(self, _scope): return None

    observation = _observations(IncompleteSources(), scope)["risk_issue_change_aging"]
    assert observation.state == "indeterminate" and observation.eligible_count is None
    assert observation.denominator is None and observation.value == {}


def test_aging_uses_canonical_created_at_and_suppresses_unknown_or_small_cohorts():
    organization_id = uuid4()
    evidence = [row(organization_id, "risk", index) for index in range(5)]
    result = risk_issue_change_aging_from_evidence(evidence, source_cutoff=NOW)
    assert result.state == "complete" and result.eligible_count == 5
    assert result.value["by_kind"]["risk"]["oldest_days"] > 3
    assert risk_issue_change_aging_from_evidence(evidence[:4], source_cutoff=NOW).state == "indeterminate"
    closed = row(organization_id, "risk", 9, standing="closed")
    partial = risk_issue_change_aging_from_evidence(evidence + [closed], source_cutoff=NOW)
    assert partial.state == "partial" and partial.value["excluded_closed_count"] == 1
    unknown = row(organization_id, "risk", 10, standing="protected")
    suppressed = risk_issue_change_aging_from_evidence(evidence + [unknown], source_cutoff=NOW)
    assert suppressed.state == "indeterminate" and suppressed.denominator is None

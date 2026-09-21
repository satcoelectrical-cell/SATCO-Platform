"""Prospective Human-owned rework semantics; no database or external writes."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.engineering_deliverable import EngineeringDeliverableHistory
from app.schemas.engineering_deliverable import (
    CreateRevisionRequest, DeliverableActor, DeliverableInvalidResult,
    DeliverableProtectedResult, DeliverableReworkEvidencePage,
    ResolveReworkRequest,
)
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.services.engineering_performance import rework_revision_trend
from app.services.engineering_performance_intelligence import compose_health


NOW = datetime(2026, 9, 20, tzinfo=timezone.utc)


class Repo:
    def __init__(self, row, current):
        self.row, self.current = row, current
        self.added = []
        self.creation = []
        self.resolution = []
        self.history_rows = []
        self.revision_count = 0

    def get(self, *, deliverable_id, organization_id, lock=False):
        return self.row if (deliverable_id, organization_id) == (
            self.row.id, self.row.organization_id,
        ) else None

    def get_current_revision(self, *, deliverable, lock=False):
        return self.current

    def get_revision(self, *, revision_id, organization_id, lock=False):
        return self.current if (revision_id, organization_id) == (
            self.current.id, self.current.organization_id,
        ) else None

    def revision_creation_history(self, **kwargs):
        return self.creation

    def rework_resolution_history(self, **kwargs):
        return self.resolution

    def revisions(self, *, deliverable_id):
        return [self.current]

    def add(self, value):
        self.added.append(value)

    def list_rework_history(self, **kwargs):
        return self.history_rows

    def count_project_revisions_at(self, **kwargs):
        return self.revision_count


class Uow:
    def __init__(self, repo):
        self.repository = repo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class Auth:
    allowed = True

    def project(self, *, actor, project_id, lock=False):
        return SimpleNamespace(id=project_id) if self.allowed else None

    def can_read_project(self, *, actor, project):
        return self.allowed


def owner(*, allowed=True):
    actor = DeliverableActor(actor_id=11, organization_id=uuid4())
    project = SimpleNamespace(id=7)
    row = SimpleNamespace(id=uuid4(), organization_id=actor.organization_id,
                          project_id=7, workspace_id=None, version=1,
                          current_revision_sequence=1, standing="reviewed")
    revision = SimpleNamespace(id=uuid4(), deliverable_id=row.id,
                               organization_id=actor.organization_id,
                               project_id=7, version=1, standing="reviewed",
                               supporting_file_id=None)
    repo, auth = Repo(row, revision), Auth()
    auth.allowed = allowed
    service = EngineeringDeliverableService(
        uow_factory=lambda: Uow(repo), authorization=auth, clock=lambda: NOW,
    )
    return service, repo, row, revision, actor, project


def revision_request(reason):
    return CreateRevisionRequest(
        expected_deliverable_version=1, expected_current_revision_version=1,
        external_label="B", source_reference=None, supporting_file_id=None,
        revision_reason=reason, rationale="Human engineering classification",
    )


def test_classification_requires_human_typed_reason_and_records_creation_event():
    with pytest.raises(ValidationError):
        CreateRevisionRequest(
            expected_deliverable_version=1, expected_current_revision_version=1,
            external_label="B", rationale="Missing Human reason",
        )
    for reason in ("normal_revision", "change_driven_revision",
                   "corrective_rework", "review_return_rework"):
        service, repo, row, revision, actor, project = owner()
        result = service._create_revision(Uow(repo), project, row.id,
                                          revision_request(reason), actor, NOW)
        assert result.outcome == "success"
        event = next(value for value in repo.added
                     if isinstance(value, EngineeringDeliverableHistory))
        assert event.event_type == "revision_created"
        assert event.revision_reason == reason
        assert event.actor_id == actor.actor_id
    # Classification does not rewrite the prior revision's standing as rework.
    assert revision.standing == "superseded"


def test_rework_resolution_is_explicit_and_does_not_follow_successor_or_standing():
    service, repo, row, revision, actor, project = owner()
    repo.creation = [SimpleNamespace(revision_reason="corrective_rework")]
    row.version = 2
    request = ResolveReworkRequest(expected_deliverable_version=2,
                                   rationale="Correction verified by Human")
    result = service._resolve_rework(Uow(repo), project, row.id, revision.id,
                                     request, actor, NOW)
    assert result.outcome == "success"
    event = next(value for value in repo.added
                 if isinstance(value, EngineeringDeliverableHistory))
    assert event.event_type == "rework_resolved"
    assert event.rework_resolution_rationale == request.rationale
    assert revision.standing == "reviewed"  # no lifecycle rewriting
    repo.resolution = [event]
    request = ResolveReworkRequest(expected_deliverable_version=3,
                                   rationale="Duplicate resolution")
    assert isinstance(service._resolve_rework(Uow(repo), project, row.id,
                                              revision.id, request, actor, NOW),
                      DeliverableInvalidResult)


def _history(repo, reasons, *, resolved=()):
    rows = []
    for index, reason in enumerate(reasons):
        revision = SimpleNamespace(id=uuid4(), deliverable_id=repo.row.id,
                                   organization_id=repo.row.organization_id,
                                   project_id=7, supporting_file_id=None)
        event = SimpleNamespace(
            id=uuid4(), revision_id=revision.id,
            event_type="deliverable_created" if index == 0 else "revision_created",
            revision_reason=reason, workspace_scope_recorded=True,
            workspace_id_at_event=None,
            occurred_at=NOW - timedelta(days=2),
        )
        rows.append((event, repo.row, revision))
        if index in resolved:
            rows.append((SimpleNamespace(
                id=uuid4(), revision_id=revision.id,
                event_type="rework_resolved", revision_reason=None,
                workspace_scope_recorded=True, workspace_id_at_event=None,
                occurred_at=NOW - timedelta(days=1),
            ), repo.row, revision))
    repo.history_rows = rows
    repo.revision_count = len(reasons)


def test_owner_projection_trend_health_and_unknown_history():
    service, repo, row, revision, actor, project = owner()
    _history(repo, ["normal_revision", "change_driven_revision",
                    "corrective_rework", "review_return_rework", None], resolved=(2,))
    result = service.list_authorized_rework_evidence(
        project_id=7, actor=actor, source_cutoff=NOW,
    )
    assert isinstance(result, DeliverableReworkEvidencePage)
    facts = result.items
    assert [item.resolution_state for item in facts] == [
        "not_applicable", "not_applicable", "resolved", "unresolved", "unknown",
    ]
    trend = rework_revision_trend(facts, source_cutoff=NOW,
                                  population_complete=True)
    assert trend.state == "indeterminate"  # four classified: minimum-safe population
    assert compose_health({}, rework_facts=facts,
                          rework_population_complete=True)[3].state == "indeterminate"
    known = facts[:-1]
    assert compose_health({}, rework_facts=known,
                          rework_population_complete=True)[3].state == "attention"
    resolved = known[:-1]
    assert compose_health({}, rework_facts=resolved,
                          rework_population_complete=True)[3].state == "healthy"
    assert compose_health({}, rework_facts=known,
                          rework_population_complete=False)[3].state == "indeterminate"


def test_constrained_requires_explicit_blocking_event_and_denial_is_nondisclosing():
    service, repo, row, revision, actor, project = owner()
    _history(repo, ["corrective_rework"])
    result = service.list_authorized_rework_evidence(
        project_id=7, actor=actor, source_cutoff=NOW,
    )
    fact = result.items[0]
    assert fact.blocking_event_id is None
    assert compose_health({}, rework_facts=(fact,),
                          rework_population_complete=True)[3].state == "attention"
    explicit = fact.model_copy(update={"blocking_event_id": uuid4()})
    assert compose_health({}, rework_facts=(explicit,),
                          rework_population_complete=True)[3].state == "constrained"
    denied, repo2, *_ = owner(allowed=False)
    repo2.history_rows = repo.history_rows
    assert isinstance(denied.list_authorized_rework_evidence(
        project_id=7, actor=actor, source_cutoff=NOW,
    ), DeliverableProtectedResult)


def test_missing_canonical_creation_event_fails_closed():
    service, repo, row, revision, actor, project = owner()
    repo.revision_count = 1
    assert service.list_authorized_rework_evidence(
        project_id=7, actor=actor, source_cutoff=NOW,
    ).outcome == "unavailable"

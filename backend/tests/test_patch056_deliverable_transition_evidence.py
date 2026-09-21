from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models.engineering_deliverable import EngineeringDeliverableHistory
from app.adapters.engineering_performance import (
    EngineeringPerformanceProtectedNotFound, EngineeringPerformanceScope,
    EngineeringPerformanceSourceAdapter,
)
from app.schemas.engineering_deliverable import (
    DeliverableActor, DeliverableTransitionEvidencePage, TransitionRevisionRequest,
)
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.services.engineering_performance import deliverable_review_cycle_from_events


class Repository:
    def __init__(self, row=None, revision=None, history_rows=()):
        self.row = row
        self.revision = revision
        self.history_rows = history_rows
        self.items = []
        self.history_reads = 0

    def get(self, **_kwargs): return self.row
    def revisions(self, **_kwargs): return [self.revision]
    def get_revision(self, **_kwargs): return self.revision
    def get_idempotency(self, **_kwargs): return None
    def list_transition_history(self, **_kwargs):
        self.history_reads += 1
        return self.history_rows
    def add(self, item): self.items.append(item)
    def flush(self): pass


class Uow:
    def __init__(self, repository): self.repository = repository; self.committed = False
    def __enter__(self): return self
    def __exit__(self, *_args): pass
    def stage_audit(self, **_kwargs): pass
    def commit(self): self.committed = True


class Authorization:
    def __init__(self, read=True): self.read = read
    def project(self, **_kwargs): return SimpleNamespace(id=7, status="active")
    def can_mutate(self, **_kwargs): return True
    def can_read_project(self, **_kwargs): return self.read


def _fixture(now):
    organization_id, deliverable_id, revision_id = uuid4(), uuid4(), uuid4()
    row = SimpleNamespace(id=deliverable_id, organization_id=organization_id,
                          project_id=7, workspace_id=13, current_revision_sequence=1,
                          standing="planned", version=1)
    revision = SimpleNamespace(id=revision_id, deliverable_id=deliverable_id,
                               organization_id=organization_id, project_id=7,
                               sequence=1, version=1, standing="draft",
                               supporting_file_id=None, transitioned_at=now)
    return DeliverableActor(actor_id=3, organization_id=organization_id), row, revision


def test_future_human_transition_records_authoritative_target_and_clock():
    now = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    actor, row, revision = _fixture(now)
    repo = Repository(row, revision)
    uow = Uow(repo)
    service = EngineeringDeliverableService(
        uow_factory=lambda: uow, authorization=Authorization(), clock=lambda: now,
    )
    result = service.transition_revision(
        project_id=7, deliverable_id=row.id, revision_id=revision.id,
        data=TransitionRevisionRequest(expected_deliverable_version=1,
                                       expected_revision_version=1,
                                       target_standing="ready_for_review", rationale="Human review entry"),
        actor=actor, idempotency_key=uuid4(),
    )
    event = next(item for item in repo.items if isinstance(item, EngineeringDeliverableHistory))
    assert result.outcome == "success" and uow.committed
    assert event.revision_id == revision.id and event.revision_target_standing == "ready_for_review"
    assert event.occurred_at == now and event.actor_id == actor.actor_id
    assert event.workspace_id_at_event == 13 and event.workspace_scope_recorded is True
    assert revision.standing == "ready_for_review" and row.standing == "ready_for_review"


def test_owner_read_is_authorized_before_event_selection_and_does_not_mutate():
    now = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    actor, row, revision = _fixture(now)
    event = SimpleNamespace(id=uuid4(), event_type="revision_transitioned",
                            revision_target_standing="ready_for_review",
                            superseded_revision_id=None, aggregate_version=2,
                            occurred_at=now, workspace_scope_recorded=True,
                            workspace_id_at_event=13)
    repo = Repository(row, revision, [(event, row, revision)])
    uow = Uow(repo)
    denied = EngineeringDeliverableService(uow_factory=lambda: uow,
                                           authorization=Authorization(read=False))
    assert denied.list_authorized_transition_evidence(project_id=7, actor=actor).outcome == "protected_not_found"
    assert repo.history_reads == 0
    allowed = EngineeringDeliverableService(uow_factory=lambda: uow,
                                            authorization=Authorization())
    result = allowed.list_authorized_transition_evidence(project_id=7, actor=actor,
                                                         workspace_id=13)
    assert isinstance(result, DeliverableTransitionEvidencePage)
    assert len(result.items) == 1 and result.items[0].target_standing.value == "ready_for_review"
    assert result.items[0].source_event_id == event.id and result.items[0].occurred_at == now
    assert repo.history_reads == 1 and not uow.committed and revision.standing == "draft"


def test_historical_target_and_workspace_remain_unknown_even_if_current_standing_is_reviewed():
    now = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    actor, row, revision = _fixture(now)
    revision.standing = "reviewed"
    event = SimpleNamespace(id=uuid4(), event_type="revision_transitioned",
                            revision_target_standing=None, superseded_revision_id=None,
                            aggregate_version=2, occurred_at=now,
                            workspace_scope_recorded=None, workspace_id_at_event=None)
    repo = Repository(row, revision, [(event, row, revision)])
    service = EngineeringDeliverableService(uow_factory=lambda: Uow(repo),
                                            authorization=Authorization())
    result = service.list_authorized_transition_evidence(project_id=7, actor=actor)
    assert result.items[0].target_standing is None
    assert result.items[0].workspace_scope_recorded is False
    assert service.list_authorized_transition_evidence(project_id=7, actor=actor,
                                                       workspace_id=13).outcome == "unavailable"


def test_patch056_consumes_only_authorized_deliverable_owner_read():
    now = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    actor, row, revision = _fixture(now)
    event = SimpleNamespace(id=uuid4(), event_type="revision_transitioned",
                            revision_target_standing="ready_for_review",
                            superseded_revision_id=None, aggregate_version=2,
                            occurred_at=now, workspace_scope_recorded=True,
                            workspace_id_at_event=13)
    owner_repo = Repository(row, revision, [(event, row, revision)])
    owner = EngineeringDeliverableService(uow_factory=lambda: Uow(owner_repo),
                                          authorization=Authorization())

    class Policy:
        def __init__(self, allowed): self.allowed = allowed
        def authorize(self, **_kwargs): return self.allowed

    class NoOrm:
        def query(self, *_args): raise AssertionError("PATCH-056 must not query Deliverable ORM")

    scope = EngineeringPerformanceScope(actor.organization_id, 7, None, actor.actor_id)
    adapter = EngineeringPerformanceSourceAdapter(NoOrm(), authorization_policy=Policy(True),
                                                  deliverable_service=owner)
    assert adapter.deliverable_transition_rows(scope)[0].source_event_id == event.id
    denied = EngineeringPerformanceSourceAdapter(NoOrm(), authorization_policy=Policy(False),
                                                 deliverable_service=owner)
    try:
        denied.deliverable_transition_rows(scope)
        assert False, "protected actor must not receive transition evidence"
    except EngineeringPerformanceProtectedNotFound:
        pass
    assert owner_repo.history_reads == 1


def _transition(revision_id, target, when, version=1):
    return SimpleNamespace(source_event_type="revision_transitioned", revision_id=revision_id,
                           target_standing=target, occurred_at=when, aggregate_version=version)


def test_review_cycle_requires_owner_attested_open_and_close_pair():
    now = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    revision_id = uuid4()
    opening = _transition(revision_id, "ready_for_review", now)
    closing = _transition(revision_id, "reviewed", now + timedelta(hours=3), 2)
    result = deliverable_review_cycle_from_events((opening, closing))
    assert result.state == "complete" and result.value["average_hours"] == 3
    assert deliverable_review_cycle_from_events((opening,)).state == "indeterminate"
    assert "review_open_without_close" in deliverable_review_cycle_from_events((opening,)).limitations
    historical = _transition(uuid4(), None, now)
    unknown = deliverable_review_cycle_from_events((historical,))
    assert unknown.state == "indeterminate" and unknown.value == {}
    partial = deliverable_review_cycle_from_events((opening, closing, historical))
    assert partial.state == "partial" and partial.value["average_hours"] == 3
    ambiguous = deliverable_review_cycle_from_events((opening, opening, closing))
    assert ambiguous.state == "indeterminate" and ambiguous.value == {}

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.adapters.engineering_performance import (
    EngineeringPerformanceProtectedNotFound,
    EngineeringPerformanceScope,
    EngineeringPerformanceSourceAdapter,
)
from app.exceptions.engineering_context_relationship import CommitmentNotFound, InvalidCommitment
from app.models.engineering_context_relationship import InterfaceCommitment
from app.services.engineering_context_relationship_service import EngineeringContextRelationshipService
from app.services.engineering_performance import interface_commitment_fulfilment


CUTOFF = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)


class NoWriteDb:
    def query(self, *_args):
        raise AssertionError("PATCH-056 must not query Interface Commitment ORM")


class Policy:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def authorize(self, **_kwargs):
        return self.allowed


def _commitment(state="identified", due_at=None, current_use=True):
    return {"state": state, "due_at": due_at, "current_use": current_use}


def test_explicit_due_is_canonical_and_prose_is_never_parsed():
    owner = EngineeringContextRelationshipService.__new__(EngineeringContextRelationshipService)
    actor = SimpleNamespace(id=3, role="admin", is_active=True)
    project = SimpleNamespace(id=7, owner_id=3, primary_assignee_id=None)
    relationship = SimpleNamespace(id=2, commitment=None, lifecycle="current", project=project)
    saved = []

    class Repo:
        def get_relationship(self, _id): return relationship
        def is_workspace_participant(self, *_args): return True
        def create_commitment(self, values):
            saved.append(values)
            return InterfaceCommitment(id=len(saved), **values)

    owner.repository = Repo()
    owner.db = SimpleNamespace(rollback=lambda: None)
    owner._provider = lambda _project, _data: {"kind": "workspace", "workspace_id": 11}
    owner._workspace = lambda _id, _project_id, operational: SimpleNamespace(id=12)
    owner._active_user = lambda _id: actor
    owner._audit = lambda **_kwargs: None
    data = {
        "relationship_id": 2, "consumer_workspace_id": 12,
        "required_information": "Load schedule", "intended_use": "Design",
        "completeness_expectation": "Complete", "expected_source_basis": "Approved basis",
        "stage_or_due_condition": "Before 2020-01-01 design use",
        "criticality": "important", "confidentiality": "project",
        "steward_id": 3, "consumer_reviewer_id": 3,
    }
    historical = owner.create_commitment(data=data, current_user=actor)
    assert historical["due_at"] is None and saved[0]["due_at"] is None
    assert historical["stage_or_due_condition"] == data["stage_or_due_condition"]
    due = CUTOFF + timedelta(days=1)
    current = owner.create_commitment(data={**data, "due_at": due.isoformat()}, current_user=actor)
    assert current["due_at"] == due and saved[1]["due_at"] == due
    with pytest.raises(InvalidCommitment):
        owner.create_commitment(data={**data, "due_at": "2026-09-20T12:00:00"}, current_user=actor)


def test_owner_authorizes_before_due_evidence_and_never_returns_hidden_counts():
    owner = EngineeringContextRelationshipService.__new__(EngineeringContextRelationshipService)
    actor = SimpleNamespace(id=3, is_active=True)
    project = SimpleNamespace(id=7, organization_id=uuid4())
    reads = []

    class Repo:
        allowed = True
        def get_project(self, project_id, current_user):
            return project if self.allowed else None
        def list_visible_due_evidence(self, **kwargs):
            reads.append(kwargs)
            return [SimpleNamespace(
                id=1, commitment_key="c-1", project_id=7,
                provider_workspace_id=11, consumer_workspace_id=12,
                state="identified", current_use=True, due_at=CUTOFF,
                stage_or_due_condition="Before use", version=1,
                updated_at=CUTOFF,
            )]

    owner.repository = Repo()
    result = owner.list_authorized_due_evidence(project_id=7, workspace_id=None, current_user=actor)
    assert result["outcome"] == "success"
    assert result["items"][0]["due_at"] == CUTOFF
    assert result["items"][0]["fulfilled_at"] is None
    assert "total" not in result and result["population_scope"] == "actor_visible_only"
    owner.repository.allowed = False
    with pytest.raises(CommitmentNotFound):
        owner.list_authorized_due_evidence(project_id=7, workspace_id=None, current_user=actor)
    assert len(reads) == 1


def test_overdue_is_cutoff_based_and_null_is_not_on_time():
    overdue = _commitment(due_at=CUTOFF - timedelta(seconds=1))
    on_time = _commitment(due_at=CUTOFF + timedelta(seconds=1))
    result = interface_commitment_fulfilment([overdue] * 5, source_cutoff=CUTOFF)
    assert result.state == "partial" and result.value["open_overdue"] == 5
    result = interface_commitment_fulfilment([on_time] * 5, source_cutoff=CUTOFF)
    assert result.value["open_on_time"] == 5 and result.value["open_overdue"] == 0
    missing = interface_commitment_fulfilment([on_time] * 5 + [_commitment()], source_cutoff=CUTOFF)
    assert missing.state == "indeterminate" and missing.denominator is None
    assert "typed_due_evidence_unavailable" in missing.limitations


def test_unknown_or_protected_standing_cannot_enter_denominator():
    known = [_commitment("fulfilled_for_stated_use")] * 5
    result = interface_commitment_fulfilment(known + [_commitment("protected")], source_cutoff=CUTOFF)
    assert result.state == "indeterminate" and result.denominator is None
    assert result.value == {}


def test_patch056_adapter_reads_owner_only_after_authorization_and_never_writes():
    actor = SimpleNamespace(id=3, is_active=True)
    organization_id = uuid4()
    scope = EngineeringPerformanceScope(organization_id, 7, None, actor.id)

    class Owner:
        def __init__(self): self.reads = 0
        def list_authorized_due_evidence(self, **kwargs):
            self.reads += 1
            assert kwargs["current_user"] is actor
            return {"outcome": "success", "population_scope": "actor_visible_only",
                    "source_cutoff": CUTOFF, "items": (_commitment(due_at=CUTOFF),)}

    owner = Owner()
    adapter = EngineeringPerformanceSourceAdapter(
        NoWriteDb(), authorization_policy=Policy(),
        interface_commitment_service=owner, current_user=actor,
    )
    assert len(adapter.interface_commitment_rows(scope)["items"]) == 1
    assert owner.reads == 1
    denied = EngineeringPerformanceSourceAdapter(
        NoWriteDb(), authorization_policy=Policy(False),
        interface_commitment_service=owner, current_user=actor,
    )
    with pytest.raises(EngineeringPerformanceProtectedNotFound):
        denied.interface_commitment_rows(scope)
    assert owner.reads == 1

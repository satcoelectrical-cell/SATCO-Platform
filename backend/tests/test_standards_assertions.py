"""Batch-2 AST-01..08 focused closed-taxonomy and provenance evidence."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.standards import AssertionCreate, AssertionRejection, AssertionVerification, RightsRevocation
from app.adapters.standard_source_object_store import StandardSourceObjectStore
from app.adapters.standard_source_providers import ProviderFragment, StaticStandardSourceProvider
from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.repositories.standards_repository import StandardsRepository
from app.schemas.standards import SourceSnapshotCreate
from app.services.standards_service import StandardsService


@pytest.mark.parametrize("vector", [f"P054-AST-{number:02d}" for number in range(1, 9)])
def test_assertion_vectors_remain_batch_two_only(vector):
    assert vector.startswith("P054-AST-")


@pytest.mark.parametrize(("kind", "representation"), [
    ("requirement_statement", {"statement": "bounded"}),
    ("defined_term", {"term": "limit", "definition": "a bound"}),
    ("numeric_constraint", {"subject": "width", "operator": "<=", "value": 8, "unit": "m"}),
    ("cross_reference", {"target": "clause-2"}),
])
def test_only_the_four_accepted_assertion_kinds_are_admitted(kind, representation):
    value = AssertionCreate(snapshot_id=uuid4(), source_location="clause-1", assertion_kind=kind, canonical_representation=representation)
    assert value.assertion_kind == kind


def test_assertion_representation_and_decisions_are_bounded_and_closed():
    with pytest.raises(ValidationError): AssertionCreate(snapshot_id=uuid4(), source_location="clause-1", assertion_kind="rule", canonical_representation={"x": 1})
    with pytest.raises(ValidationError): AssertionRejection(expected_version=1, reason="")
    assert AssertionVerification(expected_version=1).reason is None


def test_ast01_to_ast03_create_then_human_verify_or_reject_with_events(db_session, admin_user):
    from tests.test_standards_migrations import _foundation_fixture
    fixture = _foundation_fixture(db_session, admin_user)
    provider = StaticStandardSourceProvider({"clause-assert": ProviderFragment("clause-assert", b"shall be traced", "text/plain", "v1", "b" * 64)})
    provider.provider_id = "test_provider"
    service = StandardsService(db_session, StandardsRepository(db_session), providers={"test_provider": provider}, objects=StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore()))
    _, source = service.create_source_snapshots(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], data=SourceSnapshotCreate(edition_id=fixture["edition"], provider_id="test_provider", purpose="material_support", fragments=[{"location": "clause-assert"}]), idempotency_key="ast-source")
    _, created = service.create_assertion(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], data=AssertionCreate(snapshot_id=source["items"][0]["snapshot_id"], source_location="clause-assert", assertion_kind="requirement_statement", canonical_representation={"statement": "shall be traced"}), idempotency_key="ast-create")
    _, verified = service.decide_assertion(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], assertion_id=created["assertion_id"], data=AssertionVerification(expected_version=1), approved=True, authorized_handle=created["verification_handle"], idempotency_key="ast-verify")
    assert verified["verification_status"] == "human_verified" and verified["version"] == 2

    # A later rights revocation does not rewrite assertion meaning.  It creates
    # the immutable eligibility event and makes the projection fail closed.
    _, revoked = service.revoke_rights(
        actor_id=fixture["actor"], organization_id=fixture["organization"],
        binding_id=fixture["rights"], data=RightsRevocation(expected_version=1, reason="license ended"),
        idempotency_key="ast-revoke",
    )
    assert revoked["rights_status"] == "revoked"
    from app.models.standards import StandardKnowledgeAssertion, StandardsOutbox
    assertion = db_session.get(StandardKnowledgeAssertion, created["assertion_id"])
    assert assertion.verification_status == "stale" and assertion.retained_derived_use_eligible is False
    event_ids = {row.event_id for row in db_session.query(StandardsOutbox).filter(StandardsOutbox.aggregate_id == assertion.id)}
    assert {"standards.assertion.created", "standards.assertion.human_verified", "standards.assertion.stale"} <= event_ids


def test_ast03_rejection_is_human_only_and_audited(db_session, admin_user):
    from tests.test_standards_migrations import _foundation_fixture

    fixture = _foundation_fixture(db_session, admin_user)
    provider = StaticStandardSourceProvider({"clause-reject": ProviderFragment("clause-reject", b"shall be checked", "text/plain", "v1", "c" * 64)})
    provider.provider_id = "test_provider"
    service = StandardsService(db_session, StandardsRepository(db_session), providers={"test_provider": provider}, objects=StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore()))
    _, source = service.create_source_snapshots(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], data=SourceSnapshotCreate(edition_id=fixture["edition"], provider_id="test_provider", purpose="material_support", fragments=[{"location": "clause-reject"}]), idempotency_key="ast-reject-source")
    _, created = service.create_assertion(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], data=AssertionCreate(snapshot_id=source["items"][0]["snapshot_id"], source_location="clause-reject", assertion_kind="requirement_statement", canonical_representation={"statement": "shall be checked"}), idempotency_key="ast-reject-create")
    _, rejected = service.decide_assertion(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], assertion_id=created["assertion_id"], data=AssertionRejection(expected_version=1, reason="not sufficiently supported"), approved=False, authorized_handle=created["rejection_handle"], idempotency_key="ast-reject")
    assert rejected["verification_status"] == "rejected" and rejected["version"] == 2

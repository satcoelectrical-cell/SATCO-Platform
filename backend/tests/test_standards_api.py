import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text


@pytest.mark.parametrize("route", ["CAT-01", "CAT-02", "CAT-03", "CAT-04", "CAT-05", "RGT-01", "RGT-02", "RGT-03"])
def test_batch_one_route_contracts_are_registered(route):
    from app.main import app
    paths = app.openapi()["paths"]
    expected = {"CAT-01": "/standards", "CAT-02": "/standards/{standard_id}", "CAT-03": "/standards", "CAT-04": "/standards/{standard_id}/editions", "CAT-05": "/standards/{standard_id}/editions/{edition_id}/standing-observations", "RGT-01": "/organizations/current/standard-rights", "RGT-02": "/organizations/current/standard-rights/{edition_id}/{source_provider_id}", "RGT-03": "/organizations/current/standard-rights/{rights_binding_id}/revocations"}
    assert expected[route] in paths


def test_catalog_edition_and_rights_commands_are_atomic(client, admin_headers, db_session):
    """Level-B: actual CAT/RGT command path commits catalog, audit and outbox together."""
    response = client.post("/standards", headers={**admin_headers, "Idempotency-Key": "p054-private-identity"}, json={"catalog_scope": "organization_private", "issuer_display": "ISO", "designation": "9001", "title": "Quality management", "metadata_source_reference": "catalog-record"})
    assert response.status_code == 201
    identity_id = response.json()["standard_id"]
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(f"/standards/{identity_id}/editions", headers={**admin_headers, "Idempotency-Key": "p054-edition"}, json={"edition_designation": "2015", "metadata_source_reference": "catalog-record", "initial_standing": "current", "observed_effective_at": now, "standing_source_reference": "catalog-record"})
    assert response.status_code == 201
    edition_id = response.json()["edition_id"]
    detail = client.get(f"/standards/{identity_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["editions"][0]["standing_history"] == [{
        "standing": "current",
        "observed_effective_at": now,
        "version": 1,
    }]
    response = client.put(f"/organizations/current/standard-rights/{edition_id}/registry_metadata", headers={**admin_headers, "Idempotency-Key": "p054-rights"}, json={"rights_basis": "metadata_only", "rights_status": "active", "allow_metadata_visibility": True, "effective_from": now, "rights_authority_reference": "rights-record", "rights_authority_digest": "a" * 64, "expected_version": 0})
    assert response.status_code == 200
    response = client.put(f"/organizations/current/standard-rights/{edition_id}/registry_metadata", headers={**admin_headers, "Idempotency-Key": "p054-rights-replacement"}, json={"rights_basis": "metadata_only", "rights_status": "active", "allow_metadata_visibility": True, "effective_from": now, "rights_authority_reference": "rights-record", "rights_authority_digest": "b" * 64, "expected_version": 1})
    assert response.status_code == 200
    assert response.json()["version"] == 2
    assert client.get("/standards", headers=admin_headers).status_code == 200
    assert client.get("/organizations/current/standard-rights", headers=admin_headers).status_code == 200
    from app.models.audit_log import AuditLog
    from app.models.standards import StandardsOutbox
    assert db_session.query(AuditLog).filter(AuditLog.action == "standards.rights.created").count() == 1
    assert db_session.query(StandardsOutbox).filter(StandardsOutbox.event_id == "standards.rights.replaced").count() == 1


@pytest.mark.parametrize("vector", ["P054-APP-01", "P054-APP-02", "P054-APP-03", "P054-APP-04"])
def test_batch_three_applicability_route_contracts_are_registered(vector):
    from app.main import app

    expected = {
        "P054-APP-01": "/projects/{project_id}/standards/applicability",
        "P054-APP-02": "/projects/{project_id}/standards/candidates",
        "P054-APP-03": "/projects/{project_id}/standards/applicability",
        "P054-APP-04": "/projects/{project_id}/standards/applicability/{applicability_id}/retirements",
    }
    assert expected[vector] in app.openapi()["paths"]


def test_applicability_api_declares_lists_retires_and_replays(client, admin_headers, db_session, admin_user):
    from tests.test_standards_migrations import _foundation_fixture

    values = _foundation_fixture(db_session, admin_user)
    request = {"edition_id": str(values["edition"]), "status": "declared_applicable", "applicability_role": "design_basis", "rationale_code": "human_review", "rationale": "Human declaration", "expected_revision": 0}
    response = client.post(f"/projects/{values['project']}/standards/applicability", headers={**admin_headers, "Idempotency-Key": "p054-app-declare"}, json=request)
    assert response.status_code == 201
    declared = response.json()
    replay = client.post(f"/projects/{values['project']}/standards/applicability", headers={**admin_headers, "Idempotency-Key": "p054-app-declare"}, json=request)
    assert replay.status_code == 201 and replay.json() == declared
    assert client.get(f"/projects/{values['project']}/standards/applicability", headers=admin_headers).json()["items"][0]["applicability_id"] == declared["applicability_id"]
    # APP-02 is a deterministic read: a Project without a frozen package
    # configuration has no advisory candidates and no side effect.
    assert client.get(f"/projects/{values['project']}/standards/candidates", headers=admin_headers).json() == {"items": []}
    retired = client.post(f"/projects/{values['project']}/standards/applicability/{declared['applicability_id']}/retirements", headers={**admin_headers, "Idempotency-Key": "p054-app-retire"}, json={"expected_revision": 1, "reason": "Human retirement"})
    assert retired.status_code == 201 and retired.json()["status"] == "retired"


def test_selector_options_are_bounded_and_revision_is_specific_to_each_edition(client, admin_headers, db_session, admin_user):
    from tests.test_standards_applicability_migrations import _insert, _row
    from tests.test_standards_migrations import _foundation_fixture

    values = _foundation_fixture(db_session, admin_user)
    _insert(db_session, _row(values))
    other_edition = uuid4()
    db_session.execute(text("""
      INSERT INTO standard_editions(id,standard_identity_id,edition_designation,edition_key,edition_disambiguator,
        jurisdiction,metadata_source_reference,edition_digest,created_by)
      VALUES (:id,:identity,'2027','2027','','{}','test-catalog',:digest,:actor)
    """), {**values, "id": other_edition})
    response = client.get(f"/projects/{values['project']}/standards/selector-options", headers=admin_headers)
    assert response.status_code == 200
    editions = {item["handle"]: item for item in response.json()["editions"]}
    assert editions[str(values["edition"])]["current_revision"] == 1
    assert editions[str(other_edition)]["current_revision"] == 0
    assert all(item["label"] and item["handle"] not in item["label"] for item in editions.values())


def test_intelligence_options_mask_foreign_project_before_selector_disclosure(client, admin_headers, db_session, admin_user):
    from uuid import uuid4
    from app.models.organization import Organization
    from app.models.customer import Customer
    from app.models.project import Project
    foreign_org = Organization(id=uuid4(), is_active=True)
    foreign_customer = Customer(name=f"Foreign standards selector {uuid4().hex}", organization_id=foreign_org.id)
    db_session.add_all((foreign_org, foreign_customer)); db_session.flush()
    foreign_project = Project(organization_id=foreign_org.id, project_code=f"SAT-PRJ-2099-{uuid4().int % 900000 + 100000}", name="Foreign standards", customer_id=foreign_customer.id, owner_id=admin_user.id)
    db_session.add(foreign_project); db_session.flush()
    response = client.get(f"/projects/{foreign_project.id}/standards/intelligence-options", headers=admin_headers)
    assert response.status_code == 404
    assert response.json() == {"outcome": "protected_not_found"}


def test_intelligence_options_are_bounded_eligible_and_read_only_for_authorized_project(client, admin_headers, db_session, admin_user):
    from app.models.audit_log import AuditLog
    from app.models.standards import StandardIntelligenceRun, StandardsOutbox
    from app.repositories.standards_repository import StandardsRepository
    from app.schemas.standards import SourceSnapshotCreate
    from app.services.standards_service import StandardsService
    from app.adapters.standard_source_object_store import StandardSourceObjectStore
    from app.adapters.standard_source_providers import ProviderFragment, StaticStandardSourceProvider
    from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
    from tests.test_standards_applicability_migrations import _insert, _row
    from tests.test_standards_migrations import _foundation_fixture

    values = _foundation_fixture(db_session, admin_user)
    _insert(db_session, _row(values))
    fragments = {f"clause-{index}": ProviderFragment(f"clause-{index}", f"content-{index}".encode(), "text/plain", f"v{index}", f"{index:064x}") for index in range(16)}
    provider = StaticStandardSourceProvider(fragments); provider.provider_id = "test_provider"
    service = StandardsService(db_session, StandardsRepository(db_session), providers={"test_provider": provider}, objects=StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore()))
    for batch in range(2):
        locations = [f"clause-{index}" for index in range(batch * 8, batch * 8 + 8)]
        service.create_source_snapshots(actor_id=values["actor"], organization_id=values["organization"], project_id=values["project"], data=SourceSnapshotCreate(edition_id=values["edition"], provider_id="test_provider", purpose="material_support", fragments=[{"location": location} for location in locations]), idempotency_key=f"selector-sources-{batch}")
    before = (db_session.query(AuditLog).count(), db_session.query(StandardsOutbox).count(), db_session.query(StandardIntelligenceRun).count())
    response = client.get(f"/projects/{values['project']}/standards/intelligence-options", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["snapshots"]) == 8
    assert len(payload["assertions"]) <= 20
    assert all(item["availability_status"] == "available" for item in payload["snapshots"])
    assert all(item["verification_status"] == "human_verified" for item in payload["assertions"])
    snapshot_handles = {item["handle"] for item in payload["snapshots"]}
    assert all(item["snapshot_handle"] in snapshot_handles for item in payload["assertions"])
    after = (db_session.query(AuditLog).count(), db_session.query(StandardsOutbox).count(), db_session.query(StandardIntelligenceRun).count())
    assert after == before


@pytest.mark.parametrize("condition", [
    "not_applicable", "unavailable", "integrity_failed", "non_current",
    "revoked_rights", "expired_rights", "derived_use_denied",
])
def test_intelligence_options_exclude_ineligible_snapshots(condition, client, admin_headers, db_session, admin_user):
    from tests.test_standards_applicability_migrations import _insert, _row
    from tests.test_standards_migrations import _foundation_fixture

    fixture_options = {
        "unavailable": {"availability_status": "rights_restricted"},
        "integrity_failed": {"availability_status": "integrity_failed"},
        "non_current": {"standing": "withdrawn"},
        "revoked_rights": {"rights_status": "revoked", "allow_excerpt_display": False,
                           "allow_source_retrieval": False, "allow_derived_current_use": False},
        "expired_rights": {"effective_from": datetime(2020, 1, 1, tzinfo=timezone.utc),
                           "effective_until": datetime(2020, 1, 2, tzinfo=timezone.utc)},
        "derived_use_denied": {"allow_derived_current_use": False},
    }
    values = _foundation_fixture(db_session, admin_user, **fixture_options.get(condition, {}))
    applicability = _row(values, status="declared_not_applicable" if condition == "not_applicable" else "declared_applicable")
    _insert(db_session, applicability)
    response = client.get(f"/projects/{values['project']}/standards/intelligence-options", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"snapshots": [], "assertions": []}


def test_intelligence_options_expose_only_verified_retained_assertions_from_eligible_snapshots(client, admin_headers, db_session, admin_user):
    from tests.test_standards_applicability_migrations import _insert, _row
    from app.adapters.standard_source_object_store import StandardSourceObjectStore
    from app.adapters.standard_source_providers import ProviderFragment, StaticStandardSourceProvider
    from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
    from app.repositories.standards_repository import StandardsRepository
    from app.schemas.standards import AssertionCreate, AssertionRejection, AssertionVerification, SourceSnapshotCreate
    from app.services.standards_service import StandardsService
    from tests.test_standards_migrations import _foundation_fixture

    values = _foundation_fixture(db_session, admin_user)
    _insert(db_session, _row(values))
    fragments = {name: ProviderFragment(name, name.encode(), "text/plain", "v1", f"{index:064x}")
                 for index, name in enumerate(("valid", "unverified", "rejected"), 1)}
    provider = StaticStandardSourceProvider(fragments); provider.provider_id = "test_provider"
    service = StandardsService(db_session, StandardsRepository(db_session), providers={"test_provider": provider}, objects=StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore()))
    _, sources = service.create_source_snapshots(actor_id=values["actor"], organization_id=values["organization"], project_id=values["project"], data=SourceSnapshotCreate(edition_id=values["edition"], provider_id="test_provider", purpose="material_support", fragments=[{"location": name} for name in fragments]), idempotency_key="selector-assertion-sources")
    assertions = []
    for item in sources["items"]:
        _, created = service.create_assertion(actor_id=values["actor"], organization_id=values["organization"], project_id=values["project"], data=AssertionCreate(snapshot_id=item["snapshot_id"], source_location=item["source_location"], assertion_kind="requirement_statement", canonical_representation={"statement": item["source_location"]}), idempotency_key=f"selector-assertion-{item['source_location']}")
        assertions.append((created, item["snapshot_id"]))
    (valid, valid_snapshot), (unverified, _), (rejected, _) = assertions
    service.decide_assertion(actor_id=values["actor"], organization_id=values["organization"], project_id=values["project"], assertion_id=valid["assertion_id"], data=AssertionVerification(expected_version=1), approved=True, authorized_handle=valid["verification_handle"], idempotency_key="selector-verify")
    service.decide_assertion(actor_id=values["actor"], organization_id=values["organization"], project_id=values["project"], assertion_id=rejected["assertion_id"], data=AssertionRejection(expected_version=1, reason="Human rejected"), approved=False, authorized_handle=rejected["rejection_handle"], idempotency_key="selector-reject")
    payload = client.get(f"/projects/{values['project']}/standards/intelligence-options", headers=admin_headers).json()
    assert [item["handle"] for item in payload["assertions"]] == [valid["assertion_id"]]
    assert payload["assertions"][0]["snapshot_handle"] == valid_snapshot

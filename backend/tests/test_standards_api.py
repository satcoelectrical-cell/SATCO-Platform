import pytest
from datetime import datetime, timezone


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

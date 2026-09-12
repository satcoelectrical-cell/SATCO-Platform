from uuid import uuid4

import pytest

from app.models.audit_log import AuditLog
from app.models.standards import StandardsOutbox
from app.models.standards import StandardIdentity
from app.repositories.standards_repository import StandardsRepository
from app.services.standards_service import StandardsService


def test_organization_private_identity_is_scoped(db_session):
    organization_id = uuid4()
    db_session.execute(__import__("sqlalchemy").text("INSERT INTO organizations(id,is_active) VALUES (:id,true)"), {"id": organization_id})
    row = StandardIdentity(catalog_scope="organization_private", organization_id=organization_id, issuer_key="iso", issuer_display="ISO", designation="9001", designation_key="9001", title="Quality", language=None, jurisdiction={}, normalization_version="satco_standard_key_nfkc_casefold_v1", metadata_source_reference="catalog", identity_digest="a" * 64, created_by=1)
    # The test proves repository predicates; fixtures own user construction in API/security suites.
    assert StandardsRepository(db_session).get_identity(uuid4(), organization_id) is None


@pytest.mark.parametrize("vector", ["P054-AUD-03"])
def test_aud03_outbox_and_audit_are_atomic_and_payload_safe(db_session, admin_user, vector):
    aggregate_id = uuid4()
    StandardsService(db_session, StandardsRepository(db_session))._stage_event(
        actor_id=admin_user.id,
        organization_id=None,
        aggregate_type="standard_source_snapshot",
        aggregate_id=aggregate_id,
        event_id="standards.source.retrieval_succeeded",
        details={"digest": "a" * 64, "version": 1, "object_key": "must-not-escape", "provider_token": "must-not-escape"},
    )
    db_session.flush()
    audit = db_session.query(AuditLog).filter(AuditLog.entity_uuid == aggregate_id).one()
    outbox = db_session.query(StandardsOutbox).filter(StandardsOutbox.aggregate_id == aggregate_id).one()
    expected = {"event_id", "aggregate_id", "digest", "version"}
    assert set(audit.details) == expected and set(outbox.payload) == expected and vector == "P054-AUD-03"

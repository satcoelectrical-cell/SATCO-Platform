from pathlib import Path
from app.models.commercial_entitlement import CommercialEntitlementActivation, CommercialEntitlementState, CommercialSeatAssignment

MIGRATION=Path(__file__).resolve().parents[1]/"migrations"/"versions"/"e05900000001_patch_059_commercial_entitlements.py"

def test_patch059_tables_registered():
    assert {CommercialEntitlementState.__tablename__,CommercialEntitlementActivation.__tablename__,CommercialSeatAssignment.__tablename__} == {
        "commercial_entitlement_states","commercial_entitlement_activations","commercial_seat_assignments"}

def test_current_state_has_no_raw_entitlement_or_private_key():
    cols=set(CommercialEntitlementState.__table__.columns.keys())
    assert "canonical_payload_digest" in cols
    assert "raw_envelope" not in cols
    assert "private_key" not in cols
    assert "signature" not in cols

def test_activation_history_has_no_raw_entitlement():
    cols=set(CommercialEntitlementActivation.__table__.columns.keys())
    assert "canonical_payload_digest" in cols
    assert "raw_envelope" not in cols
    assert "signature" not in cols

def test_seat_has_composite_membership_foreign_key():
    table=CommercialSeatAssignment.__table__
    targets={tuple(fk.target_fullname for fk in c.elements) for c in table.foreign_key_constraints}
    assert ("user_organization_memberships.user_id","user_organization_memberships.organization_id") in targets

def test_migration_has_exact_parent_and_three_tables():
    source=MIGRATION.read_text()
    assert 'revision = "e05900000001"' in source
    assert 'down_revision = "e05800000001"' in source
    for table in ("commercial_entitlement_states","commercial_entitlement_activations","commercial_seat_assignments"):
        assert f'"{table}"' in source

def test_migration_has_least_privilege_runtime_grants_and_downgrade_guard():
    source=MIGRATION.read_text()
    assert "GRANT SELECT, INSERT, UPDATE ON commercial_entitlement_states TO satco_runtime" in source
    assert "GRANT SELECT, INSERT ON commercial_entitlement_activations TO satco_runtime" in source
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON commercial_seat_assignments TO satco_runtime" in source
    assert "Cannot discard PATCH-059 commercial entitlement state" in source

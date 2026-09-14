from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from app.adapters.standards_cross_discipline import project_standards_advisory
from app.api.v1.routers.standards import router as standards_router
from app.api.v1.routers.technical_reports import router as reports_router
from app.repositories.standards_repository import StandardsRepository
from app.schemas.standards import StandardEditionCreate
from app.services.standards_service import StandardsError, StandardsService

P054_BATCH_VECTORS = {
    1: tuple([f"P054-ID-{item:02d}" for item in range(1, 9)]
             + [f"P054-RGT-{item:02d}" for item in range(1, 13)]
             + [f"P054-AUTH-{item:02d}" for item in range(1, 11)]
             + ["P054-AUD-01", "P054-AUD-02", "P054-DB-01"]),
    2: tuple([f"P054-RET-{item:02d}" for item in range(1, 11)]
             + [f"P054-AST-{item:02d}" for item in range(1, 9)]
             + ["P054-AUD-03"]),
    3: tuple([f"P054-APP-{item:02d}" for item in range(1, 9)] + ["P054-AUD-04"]),
    4: tuple([f"P054-RPT-{item:02d}" for item in range(1, 13)]
             + ["P054-AUD-06", "P054-DB-02", "P054-DB-03"]),
    5: tuple([f"P054-AI-{item:02d}" for item in range(1, 9)]
             + [f"P054-UX-{item:02d}" for item in range(1, 7)]
             + [f"P054-LIM-{item:02d}" for item in range(1, 5)]
             + ["P054-AUD-05", "P054-DB-04"]),
}
P054_BATCH5_VECTORS = P054_BATCH_VECTORS[5]

P054_BATCH5_EVIDENCE = {
    "P054-AI-01": ("backend/tests/test_standards_intelligence_races.py", "test_initial_rights_mode_blocks_external_egress"),
    "P054-AI-02": ("backend/tests/test_standards_intelligence_races.py", "test_initial_rights_mode_blocks_external_egress"),
    "P054-AI-03": ("backend/tests/test_standards_intelligence_races.py", "test_unchanged_valid_state_dispatches_exactly_once_and_replay_never_retries"),
    "P054-AI-04": ("backend/tests/test_standards_intelligence_races.py", "test_timeout_has_no_retry_and_preserves_deterministic_result"),
    "P054-AI-05": ("backend/tests/test_standards_intelligence_races.py", "test_context_limit_is_enforced_before_provider_egress"),
    "P054-AI-06": ("backend/tests/test_standards_intelligence_races.py", "test_service_rejects_entire_ai_result_for_invented_handle_or_reference"),
    "P054-AI-07": ("backend/tests/test_standards_intelligence_races.py", "test_service_rejects_entire_ai_result_for_authoritative_claims"),
    "P054-AI-08": ("backend/tests/test_standards_intelligence_races.py", "test_prompt_injection_source_is_data_and_never_enters_provider_envelope"),
    "P054-UX-01": ("backend/tests/test_standards_conformance.py", "test_exact_twenty_two_operation_inventory"),
    "P054-UX-02": ("frontend/src/test/standards-rights.test.tsx", "shows independent rights"),
    "P054-UX-03": ("frontend/src/test/report-standards.test.tsx", "uses only canonical source_type standard"),
    "P054-UX-04": ("frontend/src/test/standards-intelligence.test.tsx", "closed not-permitted outcome"),
    "P054-UX-05": ("frontend/src/test/standards-accessibility-rtl.test.tsx", "semantic label in RTL context"),
    "P054-UX-06": ("frontend/src/test/standards-accessibility-rtl.test.tsx", "dir=\"rtl\""),
    "P054-LIM-01": ("backend/tests/test_standards_applicability_migrations.py", "test_current_head_limit_lineage_and_immutability"),
    "P054-LIM-02": ("backend/tests/test_standards_performance.py", "test_report_basis_selection_accepts_16_and_rejects_17_without_truncation"),
    "P054-LIM-03": ("backend/tests/test_standards_performance.py", "test_ai_context_accepts_exact_32768_bytes_and_rejects_plus_one"),
    "P054-LIM-04": ("backend/tests/test_standards_intelligence_races.py", "provider.timeouts == [30.0]"),
    "P054-AUD-05": ("backend/tests/test_standards_intelligence_races.py", "test_ai_provenance_has_requested_and_correct_safe_terminal_event"),
    "P054-DB-04": ("backend/tests/test_standards_intelligence_races.py", "test_transient_database_work_has_three_fresh_attempts_but_no_provider_retry"),
}

def test_batch_five_has_exactly_twenty_allocated_vectors():
    assert {batch: len(vectors) for batch, vectors in P054_BATCH_VECTORS.items()} == {
        1: 33, 2: 19, 3: 9, 4: 15, 5: 20,
    }
    all_vectors = [vector for vectors in P054_BATCH_VECTORS.values() for vector in vectors]
    assert len(all_vectors) == len(set(all_vectors)) == 96
    assert set(P054_BATCH5_EVIDENCE) == set(P054_BATCH5_VECTORS)


def test_each_batch_five_vector_has_executable_evidence_not_just_a_count():
    repository_root = Path(__file__).resolve().parents[2]
    for vector, (relative_path, test_marker) in P054_BATCH5_EVIDENCE.items():
        evidence = repository_root / relative_path
        assert evidence.is_file(), vector
        assert test_marker in evidence.read_text(), vector


def test_exact_twenty_two_operation_inventory():
    expected = {
        ("GET", "/standards"),
        ("GET", "/standards/{standard_id}"),
        ("POST", "/standards"),
        ("POST", "/standards/{standard_id}/editions"),
        ("POST", "/standards/{standard_id}/editions/{edition_id}/standing-observations"),
        ("GET", "/organizations/current/standard-rights"),
        ("PUT", "/organizations/current/standard-rights/{edition_id}/{source_provider_id}"),
        ("POST", "/organizations/current/standard-rights/{rights_binding_id}/revocations"),
        ("GET", "/projects/{project_id}/standards/applicability"),
        ("GET", "/projects/{project_id}/standards/candidates"),
        ("POST", "/projects/{project_id}/standards/applicability"),
        ("POST", "/projects/{project_id}/standards/applicability/{applicability_id}/retirements"),
        ("POST", "/projects/{project_id}/standards/source-snapshots"),
        ("GET", "/projects/{project_id}/standards/source-snapshots/{snapshot_id}/display"),
        ("POST", "/projects/{project_id}/standards/assertions"),
        ("POST", "/projects/{project_id}/standards/assertions/{assertion_id}/verifications"),
        ("POST", "/projects/{project_id}/standards/assertions/{assertion_id}/rejections"),
        ("POST", "/technical-reports/{report_id}/standards-basis-revisions"),
        ("GET", "/technical-reports/{report_id}/standards/candidates"),
        ("POST", "/technical-reports/{report_id}/acceptance"),
        ("POST", "/projects/{project_id}/standards/intelligence-runs"),
        ("GET", "/projects/{project_id}/standards/intelligence-runs/{run_id}"),
    }
    contract_routes = [*standards_router.routes] + [
        route for route in reports_router.routes
        if "/standards" in route.path or route.path.endswith("/acceptance")
    ]
    exposed = {
        (method, route.path)
        for route in contract_routes
        for method in route.methods
        if method != "HEAD"
    }
    assert exposed == expected
    assert len(exposed) == 22
    assert not any(
        forbidden in path
        for _, path in exposed
        for forbidden in ("browser", "scraper", "raw-text", "bulk-export", "passthrough")
    )


def test_metadata_and_protected_pagination_defaults_and_maxima_are_exact():
    from app.main import app

    paths = app.openapi()["paths"]
    catalog = next(
        item for item in paths["/standards"]["get"]["parameters"]
        if item["name"] == "page_size"
    )["schema"]
    protected = next(
        item for item in paths["/organizations/current/standard-rights"]["get"]["parameters"]
        if item["name"] == "page_size"
    )["schema"]
    assert (catalog["default"], catalog["maximum"]) == (20, 100)
    assert (protected["default"], protected["maximum"]) == (20, 20)


def test_registry_edition_limit_rejects_65_without_changing_existing_64(
    db_session, admin_user
):
    from tests.test_standards_migrations import _foundation_fixture

    values = _foundation_fixture(db_session, admin_user)
    for item in range(63):
        db_session.execute(text("""
          INSERT INTO standard_editions(
            id,standard_identity_id,edition_designation,edition_key,
            edition_disambiguator,jurisdiction,metadata_source_reference,
            edition_digest,created_by
          ) VALUES (
            :id,:identity,:designation,:designation,'','{}','limit-fixture',
            :digest,:actor
          )
        """), {
            "id": uuid4(), "identity": values["identity"],
            "designation": f"limit-{item}", "digest": f"{item + 1:064x}",
            "actor": admin_user.id,
        })
    service = StandardsService(db_session, StandardsRepository(db_session))
    with pytest.raises(StandardsError, match="RESOURCE_LIMIT_EXCEEDED"):
        service.create_edition(
            actor_id=admin_user.id, organization_id=values["organization"],
            identity_id=values["identity"],
            data=StandardEditionCreate(
                edition_designation="overflow", metadata_source_reference="limit-fixture",
                initial_standing="current", observed_effective_at=datetime.now(timezone.utc),
                standing_source_reference="limit-fixture",
            ), idempotency_key="edition-65",
        )
    assert db_session.execute(text(
        "SELECT count(*) FROM standard_editions WHERE standard_identity_id=:identity"
    ), values).scalar_one() == 64

def test_patch_053_projection_is_read_only_and_advisory():
    source = {"assessment_id":"a", "finding_id":"f", "unsafe":"excluded"}
    result = project_standards_advisory(retained_context=source, deterministic={"rights_eligibility":"pass"})
    assert result["advisory"] and result["human_authority_required"]
    assert result["retained_context"] == {"assessment_id":"a", "finding_id":"f"}
    assert source["unsafe"] == "excluded"

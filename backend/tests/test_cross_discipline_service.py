from app.services.cross_discipline_service import CrossDisciplineService
from app.schemas.cross_discipline_intelligence import (
    AssessmentCreate, ReassessmentCreate, SupersessionCreate,
    VerificationQuery,
)
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from uuid import UUID, uuid4
from app.models.discipline_package import RegistryRelease
from app.adapters.cross_discipline_sources import AuthorizedScope, build_batch_three_projection
from app.discipline_packages.cross_discipline.contracts import FindingIdentityInputV1, RangeV1, SourceIdentityV1
from app.discipline_packages.cross_discipline.definitions.eic_v1 import (
    BATCH_THREE_APPLICABILITY_ID, BATCH_THREE_INTERFACE_ID, BATCH_THREE_PROJECTION_IDS,
    BATCH_THREE_RULE_IDS, BATCH_THREE_VERSION, batch_three_rule_definition,
    load_batch_three_definition_set,
)
from datetime import datetime, timezone
from decimal import Decimal


def test_batch_one_readiness_and_scope_eligibility():
    service = CrossDisciplineService()
    assert service.readiness()["state"] == "ready"
    assert service.eligibility(tuple(range(1, 13)))["state"] == "eligible"
    assert service.eligibility(tuple(range(1, 14))) == {
        "state": "ineligible", "reason_codes": ("invalid_scope",),
    }
    assert service.unsupported_create() == {
        "outcome": "unavailable", "reason_code": "artifact_unavailable",
    }


def test_single_or_future_discipline_scope_is_not_supported():
    service = CrossDisciplineService()
    result = service.eligibility((1,), combination_id="cross.future.v1")
    assert result == {"state": "ineligible", "reason_codes": ("invalid_scope",)}


def _batch_three_identity(rule_id, category, subcode):
    declaration = batch_three_rule_definition(rule_id)
    interface = load_batch_three_definition_set().interface_definitions[1]
    return FindingIdentityInputV1(
        "00000000-0000-4000-8000-000000000041", "00000000-0000-4000-8000-000000000042",
        category, subcode, rule_id, BATCH_THREE_VERSION, declaration.digest,
        BATCH_THREE_INTERFACE_ID, BATCH_THREE_VERSION, interface.digest, "c" * 64,
        "xdi.sel.v1/instrumentation/engineering_object/00000000-0000-4000-8000-000000000043/signal_endpoint",
        (SourceIdentityV1("engineering_object", "00000000-0000-4000-8000-000000000043", "aggregate_version", "1", "d" * 64),),
        registry_digest="e" * 64, combination_id="cross.ic.v1",
        workspace_binding_revisions=((1, "instrumentation", 1), (2, "control_automation", 1)),
    )


def test_batch_three_signal_rules_fail_closed_and_preserve_shared_evaluator_identity():
    service = CrossDisciplineService()
    equal_values = {BATCH_THREE_RULE_IDS[0]: {
        "applicability_id": BATCH_THREE_APPLICABILITY_ID, "complete": True,
        "instrumentation_signal_type": "signal_current", "control_io_type": "analog_current",
        "identity": _batch_three_identity(BATCH_THREE_RULE_IDS[0], "inconsistent", "ic.signal_type"),
    }}
    assert service.evaluate_batch_three(execution_id="e", snapshot_id="s", values_by_rule=equal_values).status == "completed_no_findings"
    range_values = {BATCH_THREE_RULE_IDS[1]: {
        "applicability_id": BATCH_THREE_APPLICABILITY_ID, "complete": True,
        "instrumentation_range": RangeV1(Decimal("4"), Decimal("20")),
        "control_accepted_range": RangeV1(Decimal("0"), Decimal("10")),
        "identity": _batch_three_identity(BATCH_THREE_RULE_IDS[1], "inconsistent", "ic.signal_range"),
    }}
    result = service.evaluate_batch_three(execution_id="e", snapshot_id="s", values_by_rule=range_values)
    assert result.status == "completed_with_findings"
    assert result.findings[0].identity.subcode == "ic.signal_range"
    unknown = {BATCH_THREE_RULE_IDS[0]: {**equal_values[BATCH_THREE_RULE_IDS[0]], "instrumentation_signal_type": "signal_unknown"}}
    assert service.evaluate_batch_three(execution_id="e", snapshot_id="s", values_by_rule=unknown).reason_code == "unsupported_value"


def test_batch_three_projection_is_minimal_immutable_and_scope_bound():
    scope = AuthorizedScope(7, uuid4(), 3, (1, 2), False, "a" * 64)
    projection = build_batch_three_projection(
        authorized=scope, projection_id=BATCH_THREE_PROJECTION_IDS[1], owner_kind="engineering_object",
        owner_id="00000000-0000-4000-8000-000000000044", owner_revision="1",
        values=(("accepted_range", "0..20"), ("quantity_type", "analog_current")),
        complete=True, observed_at=datetime.now(timezone.utc),
    )
    assert projection.authorization_scope_digest == scope.authorization_scope_digest
    assert projection.values == (("accepted_range", "0..20"), ("quantity_type", "analog_current"))


def test_generic_empty_assessment_is_atomic_and_idempotent_on_real_postgresql(db_session, relationship_domain):
    service = CrossDisciplineService()
    project = relationship_domain["project"]
    workspaces = tuple(sorted((
        relationship_domain["provider_workspace"],
        relationship_domain["consumer_workspace"],
    ), key=lambda item: item.id))
    relationship_domain["provider_workspace"].canonical_discipline_id = "instrumentation"
    db_session.flush()
    actor = relationship_domain["actors"]["admin"]
    if db_session.query(RegistryRelease).filter(RegistryRelease.is_current.is_(True)).one_or_none() is None:
        db_session.add(RegistryRelease(
            registry_digest="9" * 64, release_id="patch-052.eic-v1",
            core_contract_version=1, is_current=True,
            manifest_json={"schema_version": 1},
        ))
        db_session.flush()
    key = uuid4()
    data = AssessmentCreate.model_validate({
        "scope": {
            "workspace_ids": [item.id for item in workspaces], "combination_id": "cross.ei.v1",
            "interface_definition_ids": [], "endpoint_selectors": [],
            "purpose": "interface_assessment",
        },
        "rationale": "Exercise the generic Batch-1 empty pipeline.",
        "correlation_id": uuid4(), "idempotency_key": key,
    })
    factory = sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    first = service.create_foundation_assessment(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id, data=data,
    )
    second = service.create_foundation_assessment(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id, data=data,
    )
    assert first == second
    assert first["outcome"] == "success"
    assert first["status"] == "completed_no_findings"
    counts = db_session.execute(text("""
      SELECT
        (SELECT count(*) FROM cross_discipline_assessments WHERE id=CAST(:id AS uuid)),
        (SELECT count(*) FROM cross_discipline_assessment_snapshots WHERE assessment_id=CAST(:id AS uuid)),
        (SELECT count(*) FROM cross_discipline_idempotency WHERE assessment_id=CAST(:id AS uuid)),
        (SELECT count(*) FROM cross_discipline_outbox WHERE assessment_id=CAST(:id AS uuid))
    """), {"id": first["assessment_id"]}).one()
    assert tuple(counts) == (1, 1, 1, 3)

    verified = service.verify_historical(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=UUID(first["assessment_id"]),
        data=VerificationQuery(
            expected_snapshot_digest=db_session.execute(text(
                "SELECT snapshot_digest FROM cross_discipline_assessment_snapshots WHERE assessment_id=CAST(:id AS uuid)"
            ), {"id": first["assessment_id"]}).scalar_one(),
            correlation_id=uuid4(),
        ),
    )
    assert verified["outcome"] == "verified"

    reassessment_data = ReassessmentCreate.model_validate({
        "scope": data.scope.model_dump(mode="json"),
        "expected_predecessor_version": 1,
        "rationale": "Reassess the retained generic scope.",
        "correlation_id": uuid4(), "idempotency_key": uuid4(),
    })
    reassessment = service.create_foundation_assessment(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        data=reassessment_data, operation="create_reassessment",
        predecessor_id=UUID(first["assessment_id"]), expected_predecessor_version=1,
    )
    assert reassessment["outcome"] == "success"
    assert reassessment["predecessor_assessment_id"] == first["assessment_id"]

    supersession_data = SupersessionCreate(
        successor_assessment_id=reassessment["assessment_id"],
        expected_predecessor_version=1, expected_successor_version=1,
        rationale="Make the current-use lineage explicit.",
        correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    supersession = service.supersede_assessment(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        predecessor_id=UUID(first["assessment_id"]), data=supersession_data,
    )
    assert supersession["outcome"] == "success"
    assert supersession["predecessor_aggregate_version"] == 2

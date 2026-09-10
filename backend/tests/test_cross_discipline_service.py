from app.services.cross_discipline_service import CrossDisciplineService
from app.schemas.cross_discipline_intelligence import (
    AssessmentCreate, ReassessmentCreate, SupersessionCreate,
    VerificationQuery,
)
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from uuid import UUID, uuid4
from app.models.discipline_package import RegistryRelease


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

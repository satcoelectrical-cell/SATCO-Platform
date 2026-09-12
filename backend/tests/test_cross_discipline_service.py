from app.services.cross_discipline_service import CrossDisciplineService
from app.schemas.cross_discipline_intelligence import (
    AssessmentCreate, PotentialImpactRequest, ReassessmentCreate,
    SupersessionCreate, VerificationQuery,
)
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from uuid import UUID, uuid4
from app.models.discipline_package import RegistryRelease
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.project_control import ProjectChange
from app.models.cross_discipline_intelligence import (
    CrossDisciplineCompletenessAttestation, CrossDisciplineFinding,
    CrossDisciplineFindingAttestation, CrossDisciplineFindingSource,
    CrossDisciplineOccurrence, CrossDisciplineOccurrenceSource,
    CrossDisciplineSnapshot, CrossDisciplineSourceProjection,
)
from app.adapters.cross_discipline_sources import AuthorizedScope, build_batch_five_change_projection, build_batch_four_projection, build_batch_three_projection
from app.discipline_packages.cross_discipline.contracts import ExplicitRelationshipV1, FindingIdentityInputV1, RangeV1, SourceIdentityV1
from app.discipline_packages.cross_discipline.definitions.eic_v1 import (
    BATCH_TWO_RULE_IDS,
    BATCH_THREE_APPLICABILITY_ID, BATCH_THREE_INTERFACE_ID, BATCH_THREE_PROJECTION_IDS,
    BATCH_THREE_RULE_IDS, BATCH_THREE_VERSION, batch_three_rule_definition,
    BATCH_FOUR_APPLICABILITY_ID, BATCH_FOUR_INTERFACE_ID, BATCH_FOUR_PROJECTION_IDS,
    BATCH_FOUR_RULE_IDS, BATCH_FOUR_VERSION, batch_four_rule_definition, load_batch_four_definition_set,
    load_batch_three_definition_set,
    BATCH_FIVE_APPLICABILITY_ID, BATCH_FIVE_INTERFACE_ID, BATCH_FIVE_RULE_IDS,
    BATCH_FIVE_VERSION, BATCH_FIVE_PATH_ID, batch_five_rule_definition, load_batch_five_definition_set,
)
from datetime import datetime, timezone
from decimal import Decimal


def _selected_ei_subject(db_session, relationship_domain):
    """Create only canonical owners; the assessed artifacts come from the reader."""
    project = relationship_domain["project"]
    electrical = relationship_domain["consumer_workspace"]
    instrumentation = relationship_domain["provider_workspace"]
    actor = relationship_domain["actors"]["admin"]
    instrumentation.canonical_discipline_id = "instrumentation"
    electrical.canonical_discipline_id = "electrical"
    transmitter = EngineeringObject(
        organization_id=project.organization_id, customer_id=project.customer_id,
        project_id=project.id, workspace_id=instrumentation.id,
        family="instrumentation", discipline="instrumentation", object_type="transmitter",
        creator_id=actor.id, steward_id=actor.id,
    )
    supply = EngineeringObject(
        organization_id=project.organization_id, customer_id=project.customer_id,
        project_id=project.id, workspace_id=electrical.id,
        family="electrical", discipline="electrical", object_type="electrical_power_source",
        creator_id=actor.id, steward_id=actor.id,
    )
    db_session.add_all((transmitter, supply))
    if db_session.query(RegistryRelease).filter(RegistryRelease.is_current.is_(True)).one_or_none() is None:
        db_session.add(RegistryRelease(
            registry_digest="9" * 64, release_id="patch-052.eic-v1",
            core_contract_version=1, is_current=True, manifest_json={"schema_version": 1},
        ))
    db_session.flush()
    data = AssessmentCreate.model_validate({
        "scope": {
            "workspace_ids": sorted((electrical.id, instrumentation.id)),
            "combination_id": "cross.ei.v1",
            "interface_definition_ids": ["cross.interface.ei.power_handoff.v1"],
            "endpoint_selectors": [
                f"xdi.sel.v1/electrical/engineering_object/{supply.id}/supply_terminal",
                f"xdi.sel.v1/instrumentation/engineering_object/{transmitter.id}/signal_endpoint",
            ],
            "purpose": "interface_assessment",
        },
        "rationale": "Run selected interface through authorized canonical sources.",
        "correlation_id": uuid4(), "idempotency_key": uuid4(),
    })
    factory = sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    return project, actor, transmitter, supply, data, factory


def test_selected_interface_uses_authorized_canonical_sources_and_retains_complete_provenance(
    db_session, relationship_domain,
):
    project, actor, transmitter, supply, data, factory = _selected_ei_subject(
        db_session, relationship_domain,
    )
    service = CrossDisciplineService()
    result = service.create_foundation_assessment(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id, data=data,
    )
    assert result["outcome"] == "success"
    assert result["status"] == "completed_with_findings"
    assessment_id = UUID(result["assessment_id"])
    snapshot = db_session.get(CrossDisciplineSnapshot, assessment_id)
    assert snapshot is not None
    assert snapshot.payload["rule_ids"] == sorted(BATCH_TWO_RULE_IDS[:3])
    assert db_session.query(CrossDisciplineSourceProjection).filter_by(assessment_id=assessment_id).count() == 5
    assert db_session.query(CrossDisciplineCompletenessAttestation).filter_by(assessment_id=assessment_id).count() == 5
    assert db_session.query(CrossDisciplineOccurrence).filter_by(assessment_id=assessment_id).count() == 1
    finding = db_session.query(CrossDisciplineFinding).filter_by(assessment_id=assessment_id).one()
    assert finding.rule_id == BATCH_TWO_RULE_IDS[2]
    assert db_session.query(CrossDisciplineOccurrenceSource).filter_by(assessment_id=assessment_id).count() == 5
    assert db_session.query(CrossDisciplineFindingSource).filter_by(assessment_id=assessment_id, finding_id=finding.id).count() == 5
    assert db_session.query(CrossDisciplineFindingAttestation).filter_by(assessment_id=assessment_id, finding_id=finding.id).count() == 5

    # Historical replay reads only the retained snapshot; current owner changes
    # cannot rewrite the prior assessment result.
    supply.version = 2
    db_session.flush()
    verified = service.verify_historical(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id,
        data=VerificationQuery(expected_snapshot_digest=snapshot.snapshot_digest, correlation_id=uuid4()),
    )
    assert verified["outcome"] == "verified"


def test_selected_eic_uuid_change_produces_a_real_finding_and_handoffs(
    db_session, relationship_domain,
):
    project = relationship_domain["project"]
    electrical = relationship_domain["consumer_workspace"]
    instrumentation = relationship_domain["provider_workspace"]
    control = relationship_domain["unrelated_workspace"]
    actor = relationship_domain["actors"]["admin"]
    electrical.canonical_discipline_id = "electrical"
    instrumentation.canonical_discipline_id = "instrumentation"
    control.canonical_discipline_id = "control_automation"
    now = datetime.now(timezone.utc)
    root = EngineeringObject(
        id=UUID("00000000-0000-4000-8000-000000000101"),
        organization_id=project.organization_id, customer_id=project.customer_id,
        project_id=project.id, workspace_id=electrical.id, family="electrical",
        discipline="electrical", object_type="electrical_power_source",
        creator_id=actor.id, steward_id=actor.id,
    )
    target = EngineeringObject(
        id=UUID("00000000-0000-4000-8000-000000000102"),
        organization_id=project.organization_id, customer_id=project.customer_id,
        project_id=project.id, workspace_id=instrumentation.id, family="instrumentation",
        discipline="instrumentation", object_type="transmitter",
        creator_id=actor.id, steward_id=actor.id,
    )
    change = ProjectChange(
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=electrical.id, version=1, created_by_id=actor.id,
        updated_by_id=actor.id, created_at=now, updated_at=now,
        statement="Assess the explicit electrical-to-instrument change path.",
        rationale="PATCH-053 integration evidence.", standing="recorded",
    )
    edge = EngineeringRelationship(
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=electrical.id, source_object_id=root.id, target_object_id=target.id,
        relationship_family="electrical", relationship_type="powered_by",
        creator_id=actor.id, steward_id=actor.id,
    )
    db_session.add_all((root, target, change))
    db_session.flush()
    db_session.add(edge)
    if db_session.query(RegistryRelease).filter(RegistryRelease.is_current.is_(True)).one_or_none() is None:
        db_session.add(RegistryRelease(registry_digest="9" * 64, release_id="patch-052.eic-v1", core_contract_version=1, is_current=True, manifest_json={"schema_version": 1}))
    db_session.flush()
    data = AssessmentCreate.model_validate({
        "scope": {
            "workspace_ids": sorted((electrical.id, instrumentation.id, control.id)), "combination_id": "cross.eic.v1",
            "interface_definition_ids": [BATCH_FIVE_INTERFACE_ID],
            "endpoint_selectors": [
                f"xdi.sel.v1/electrical/engineering_object/{root.id}/power_endpoint",
                f"xdi.sel.v1/instrumentation/engineering_object/{target.id}/signal_endpoint",
            ], "purpose": "explicit_change_impact", "project_change_id": str(change.id), "project_change_version": 1,
        }, "rationale": "Evaluate a UUID ProjectChange through the public assessment command.",
        "correlation_id": uuid4(), "idempotency_key": uuid4(),
    })
    factory = sessionmaker(bind=db_session.connection(), expire_on_commit=False, join_transaction_mode="create_savepoint")
    owner_calls = []
    class Owner:
        def create_potential(self, **values):
            owner_calls.append(values)
            return {"outcome": "success", "id": uuid4()}
    service = CrossDisciplineService(impact_handoff=Owner())
    result = service.create_foundation_assessment(session_factory=factory, actor_id=actor.id, actor_role="admin", organization_id=project.organization_id, project_id=project.id, data=data)
    assert result["status"] == "completed_with_findings"
    assessment_id = UUID(result["assessment_id"])
    finding = db_session.query(CrossDisciplineFinding).filter_by(assessment_id=assessment_id).one()
    assert finding.rule_id == BATCH_FIVE_RULE_IDS[0]
    handoff = service.handoff_potential_impact(
        session_factory=factory, actor_id=actor.id, actor_role="admin", organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, finding_id=finding.id,
        data=PotentialImpactRequest(assessment_id=assessment_id, finding_id=finding.id, change_id=change.id, change_version=change.version, target_id=target.id, target_kind="deliverable", rationale="Create the governed advisory potential impact.", correlation_id=uuid4(), idempotency_key=uuid4()),
    )
    assert handoff["outcome"] == "success" and len(owner_calls) == 1


def test_selected_ec_no_violation_retains_nonempty_executed_rule_ids(
    db_session, relationship_domain,
):
    project = relationship_domain["project"]
    electrical = relationship_domain["consumer_workspace"]
    control = relationship_domain["provider_workspace"]
    actor = relationship_domain["actors"]["admin"]
    electrical.canonical_discipline_id = "electrical"
    control.canonical_discipline_id = "control_automation"
    cabinet = EngineeringObject(
        organization_id=project.organization_id, customer_id=project.customer_id,
        project_id=project.id, workspace_id=control.id, family="automation",
        discipline="industrial_automation", object_type="control_cabinet",
        creator_id=actor.id, steward_id=actor.id,
    )
    supply = EngineeringObject(
        organization_id=project.organization_id, customer_id=project.customer_id,
        project_id=project.id, workspace_id=electrical.id, family="electrical",
        discipline="electrical", object_type="electrical_power_source",
        creator_id=actor.id, steward_id=actor.id,
    )
    db_session.add_all((cabinet, supply))
    db_session.flush()
    db_session.add(EngineeringRelationship(
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=control.id, source_object_id=cabinet.id, target_object_id=supply.id,
        relationship_family="electrical", relationship_type="powered_by",
        creator_id=actor.id, steward_id=actor.id,
    ))
    if db_session.query(RegistryRelease).filter(RegistryRelease.is_current.is_(True)).one_or_none() is None:
        db_session.add(RegistryRelease(registry_digest="9" * 64, release_id="patch-052.eic-v1", core_contract_version=1, is_current=True, manifest_json={"schema_version": 1}))
    db_session.flush()
    data = AssessmentCreate.model_validate({
        "scope": {
            "workspace_ids": sorted((electrical.id, control.id)), "combination_id": "cross.ec.v1",
            "interface_definition_ids": [BATCH_FOUR_INTERFACE_ID],
            "endpoint_selectors": [
                f"xdi.sel.v1/control_automation/engineering_object/{cabinet.id}/cabinet",
                f"xdi.sel.v1/electrical/engineering_object/{supply.id}/supply_terminal",
            ], "purpose": "interface_assessment",
        }, "rationale": "Prove the selected no-violation terminal path.",
        "correlation_id": uuid4(), "idempotency_key": uuid4(),
    })
    factory = sessionmaker(bind=db_session.connection(), expire_on_commit=False, join_transaction_mode="create_savepoint")
    result = CrossDisciplineService().create_foundation_assessment(session_factory=factory, actor_id=actor.id, actor_role="admin", organization_id=project.organization_id, project_id=project.id, data=data)
    assert result["status"] == "completed_no_findings"
    assessment_id = UUID(result["assessment_id"])
    snapshot = db_session.get(CrossDisciplineSnapshot, assessment_id)
    assert snapshot.payload["rule_ids"] == sorted(BATCH_FOUR_RULE_IDS[:3])
    assert db_session.query(CrossDisciplineFinding).filter_by(assessment_id=assessment_id).count() == 0


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


def _batch_four_identity(rule_id, category, subcode):
    declaration = batch_four_rule_definition(rule_id)
    interface = load_batch_four_definition_set().interface_definitions[-1]
    return FindingIdentityInputV1(
        "00000000-0000-4000-8000-000000000071", "00000000-0000-4000-8000-000000000072",
        category, subcode, rule_id, BATCH_FOUR_VERSION, declaration.digest,
        BATCH_FOUR_INTERFACE_ID, BATCH_FOUR_VERSION, interface.digest, "c" * 64,
        "xdi.sel.v1/electrical/engineering_object/00000000-0000-4000-8000-000000000073/mcc",
        (SourceIdentityV1("engineering_object", "00000000-0000-4000-8000-000000000073", "aggregate_version", "1", "d" * 64),),
        registry_digest="e" * 64, combination_id="cross.ec.v1",
        workspace_binding_revisions=((1, "electrical", 1), (2, "control_automation", 1)),
    )


def test_batch_four_mcc_is_explicit_and_projection_is_scope_bound():
    service = CrossDisciplineService()
    values = {BATCH_FOUR_RULE_IDS[0]: {"applicability_id": BATCH_FOUR_APPLICABILITY_ID, "complete": True,
        "command_presence": "present", "status_presence": "absent",
        "identity": _batch_four_identity(BATCH_FOUR_RULE_IDS[0], "incomplete_handoff", "ec.mcc_command_status")}}
    result = service.evaluate_batch_four(execution_id="e", snapshot_id="s", values_by_rule=values)
    assert result.findings[0].identity.subcode == "ec.mcc_command_status"
    assert service.evaluate_batch_four(execution_id="e", snapshot_id="s", values_by_rule={BATCH_FOUR_RULE_IDS[0]: {**values[BATCH_FOUR_RULE_IDS[0]], "complete": False}}).reason_code == "source_incomplete"
    scope = AuthorizedScope(7, uuid4(), 3, (1, 2), False, "a" * 64)
    projection = build_batch_four_projection(authorized=scope, projection_id=BATCH_FOUR_PROJECTION_IDS[2], owner_kind="engineering_object",
        owner_id="00000000-0000-4000-8000-000000000074", owner_revision="1", values=(("cabinet", "explicit"),), complete=True, observed_at=datetime.now(timezone.utc))
    assert projection.authorization_scope_digest == scope.authorization_scope_digest


def test_batch_five_change_path_is_explicit_bounded_and_advisory():
    service = CrossDisciplineService()
    root, target, change = ("00000000-0000-4000-8000-000000000081", "00000000-0000-4000-8000-000000000082", "00000000-0000-4000-8000-000000000083")
    declaration = batch_five_rule_definition(BATCH_FIVE_RULE_IDS[0])
    interface = load_batch_five_definition_set().interface_definitions[-1]
    identity = FindingIdentityInputV1("e", "s", "potential_change_impact", "eic.explicit_change_path", BATCH_FIVE_RULE_IDS[0], BATCH_FIVE_VERSION, declaration.digest, BATCH_FIVE_INTERFACE_ID, BATCH_FIVE_VERSION, interface.digest, "a" * 64, "xdi.sel.v1/electrical/engineering_object/" + target + "/power_endpoint", (), change=(change, 1))
    values = {BATCH_FIVE_RULE_IDS[0]: {"applicability_id": BATCH_FIVE_APPLICABILITY_ID, "complete": True, "path_id": BATCH_FIVE_PATH_ID, "change_present": True, "change_id": change, "change_version": 1, "root_object_id": root, "target_id": target, "edges": (ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000084", 1, "electrical", "powered_by", root, target),), "identity": identity}}
    result = service.evaluate_batch_five(execution_id="e", snapshot_id="s", values_by_rule=values)
    assert result.status == "completed_with_findings"
    assert service.evaluate_batch_five(execution_id="e", snapshot_id="s", values_by_rule={BATCH_FIVE_RULE_IDS[0]: {**values[BATCH_FIVE_RULE_IDS[0]], "edges": ()}}).status == "completed_no_findings"
    scope = AuthorizedScope(7, uuid4(), 3, (1, 2, 3), False, "a" * 64)
    projection = build_batch_five_change_projection(authorized=scope, owner_id=change, owner_revision="1", values=(("change_id", change),), complete=True, observed_at=datetime.now(timezone.utc))
    assert projection.projection_id == "xdi.proj.change_seed.v1"


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

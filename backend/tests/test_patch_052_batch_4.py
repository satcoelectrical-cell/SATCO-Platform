"""PATCH-052 Batch-4 Control & Automation acceptance evidence."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization
from app.discipline_packages.conformance_harness_052 import verify_package_subset
from app.discipline_packages.conformance_manifest import CONFORMANCE_VECTORS_V1, VECTOR_SUFFIXES
from app.discipline_packages.descriptors.eic_v1 import (
    CONTROL_AUTOMATION_OBJECT_DECLARATIONS,
    CONTROL_AUTOMATION_RELATIONSHIP_DECLARATIONS,
    DESCRIPTORS_V1,
    DESCRIPTOR_DIGESTS_V1,
)
from app.discipline_packages.legacy import (
    LegacyDisposition, LegacySourceContract, translate_legacy_identity,
)
from app.discipline_packages.operational import (
    OperationalContractError, execute_control_automation_rule,
)
from app.discipline_packages.readiness_052 import (
    control_automation_operational_readiness_snapshot,
)
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.discipline_package import (
    CompatibilityProfile, OrganizationPackageConfigurationHead,
    OrganizationPackageSelection, PackageDescriptor,
    ProjectPackageConfigurationHead, ProjectPackageConfigurationRevision,
    ProjectPackageConfigurationSelection, RegistryMembership,
    RegistryProfileMembership, RegistryRelease,
)
from app.models.engineering_context import (
    EngineeringContext, EngineeringContextFact,
    EngineeringContextSubjectReference,
)
from app.models.engineering_deliverable import (
    EngineeringDeliverable, EngineeringDeliverableRevision,
)
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_object import EngineeringObject
from app.models.engineering_identifier_command import EngineeringIdentifierOutbox
from app.models.engineering_object_command import (
    EngineeringObjectIdempotency, EngineeringObjectOutbox,
)
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.evidence import Evidence
from app.models.evidence_command import EvidenceOutbox
from app.models.package_input_binding import (
    EngineeringContextPackageInputBinding, EvidencePackageInputBinding,
)
from app.models.project import Project
from app.repositories.engineering_deliverable_unit_of_work import (
    SqlAlchemyEngineeringDeliverableUnitOfWork,
)
from app.repositories.patch_052_operation_unit_of_work import Patch052OperationUnitOfWork
from app.schemas.discipline_package_operations import (
    PackageCaptureCreateRequest, PackageContextBindingRequest,
    PackageDeliverableCreateRequest, PackageEvidenceBindingRequest,
    PackageObjectCreateRequest, PackageRelationshipCreateRequest,
    PackageTransitionRequest,
)
from app.schemas.engineering_deliverable import (
    DeliverableActor, DeliverableMutationSuccess, TransitionRevisionRequest,
)
from app.services.control_automation_package_service import ControlAutomationPackageService
from app.services.electrical_package_service import (
    PackageConflict, PackageDeclarationMismatch, PackageProtectedNotFound,
    PackageUnavailable,
)
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.services.package_declaration_binding_service import PackageDeclarationBindingService
from conftest import TEST_DATABASE_REVISION


ORG_ID = UUID("02810000-0000-4000-8000-000000000001")


def _factory(db_session):
    return sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


def _control_scope(db_session, engineer_user, *, standing="executable_supported"):
    descriptor = next(d for d in DESCRIPTORS_V1 if d.package_key == "control_automation")
    digest = str(DESCRIPTOR_DIGESTS_V1["control_automation"])
    registry_digest, profile_digest = "9" * 64, "a" * 64
    profile_id = f"patch-052-b4-{uuid4().hex}"
    db_session.add_all((
        RegistryRelease(
            registry_digest=registry_digest, release_id=f"patch-052-b4-{uuid4().hex}",
            core_contract_version=1, is_current=True,
            manifest_json={"release": "patch-052"},
        ),
        PackageDescriptor(
            package_key="control_automation", package_version="1.0.0",
            descriptor_digest=digest, primary_discipline_id="control_automation",
            adapter_id="discipline.control_automation.v1",
            descriptor_json=descriptor.model_dump(mode="json"),
        ),
        CompatibilityProfile(
            profile_id=profile_id, profile_digest=profile_digest,
            profile_json={"profile": "patch-052-b4"},
        ),
    ))
    db_session.flush()
    db_session.add_all((
        RegistryMembership(
            registry_digest=registry_digest, package_key="control_automation",
            package_version="1.0.0", standing=standing,
        ),
        RegistryProfileMembership(
            registry_digest=registry_digest, profile_id=profile_id,
            profile_digest=profile_digest,
        ),
        OrganizationPackageConfigurationHead(
            organization_id=ORG_ID, configuration_version=1,
        ),
        OrganizationPackageSelection(
            organization_id=ORG_ID, package_key="control_automation",
            package_version="1.0.0", state="enabled", configuration_version=1,
        ),
    ))
    customer = Customer(organization_id=ORG_ID, name="PATCH-052 Batch-4")
    db_session.add(customer); db_session.flush()
    project = Project(
        organization_id=ORG_ID,
        project_code=f"SAT-PRJ-2099-{customer.id + 9000:04d}",
        name="PATCH-052 Control & Automation", customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project); db_session.flush()
    db_session.add(ProjectPackageConfigurationRevision(
        project_id=project.id, configuration_revision=1, organization_id=ORG_ID,
        observed_registry_digest=registry_digest, profile_id=profile_id,
        profile_digest=profile_digest, rationale="Batch-4 isolated proof",
    ))
    db_session.flush()
    db_session.add_all((
        ProjectPackageConfigurationSelection(
            project_id=project.id, configuration_revision=1,
            package_key="control_automation", package_version="1.0.0",
            descriptor_digest=digest,
        ),
        ProjectPackageConfigurationHead(
            project_id=project.id, organization_id=ORG_ID,
            current_revision=1, configuration_version=1,
        ),
    ))
    workspace = EngineeringWorkspace(
        project_id=project.id, discipline="control", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id, version=1,
        canonical_discipline_id="control_automation",
        package_binding_state="OPERATIONAL_PACKAGE_BOUND",
        bound_package_key="control_automation",
        bound_project_configuration_revision=1,
    )
    db_session.add(workspace); db_session.commit()
    return project, workspace


def test_control_catalogs_are_exact_and_rules_are_static_bounded():
    descriptor = next(d for d in DESCRIPTORS_V1 if d.package_key == "control_automation")
    values = descriptor.contributions
    assert [d.object_type for d in CONTROL_AUTOMATION_OBJECT_DECLARATIONS] == [
        "plc", "dcs_controller", "esd_controller", "control_cabinet",
        "io_channel", "hmi", "control_logic",
    ]
    assert [d.required_primary_identifier_kind for d in CONTROL_AUTOMATION_OBJECT_DECLARATIONS] == [
        "equipment_number", "equipment_number", "equipment_number", "panel_number",
        "controlled_external_key", "panel_number", "system_identifier",
    ]
    assert [d.relationship_type for d in CONTROL_AUTOMATION_RELATIONSHIP_DECLARATIONS] == [
        "controlled_by", "commands", "receives_signal_from", "sends_signal_to",
        "implemented_in", "interlocked_with", "trips", "initiates", "inhibits",
        "participates_in_sequence", "monitored_by", "generates_alarm_for",
        "executes_logic_for",
    ]
    assert (len(values.object_types), len(values.relationship_types),
            len(values.engineering_inputs), len(values.deliverables),
            len(values.evidence_requirements), len(values.deterministic_rule_hooks)) == (
        7, 13, 9, 5, 4, 5,
    )
    assert {d.family_id for d in values.object_types} == {"automation"}
    assert {d.context_kind_id for d in values.context_contributions} == {
        "control_automation.control_philosophy_basis",
        "control_automation.io_allocation_basis",
        "control_automation.alarm_interlock_basis",
        "control_automation.cause_effect_basis",
        "control_automation.availability_redundancy_basis",
    }
    assert {d.id for d in values.evidence_requirements} == {
        "control_automation.control_philosophy_evidence",
        "control_automation.io_allocation_evidence",
        "control_automation.cause_effect_interlock_evidence",
        "control_automation.deliverable_review_evidence",
    }
    deliverables = {d.deliverable_type_id: (d.required_input_ids, d.output_representation_ids)
                    for d in values.deliverables}
    assert set(deliverables["control_io_list"][0]) == {
        "control_automation.control_philosophy_basis.input",
        "control_automation.io_allocation_basis.input",
        "control_automation.availability_redundancy_basis.input",
        "control_automation.control_philosophy_evidence.input",
        "control_automation.io_allocation_evidence.input",
    }
    assert deliverables["control_io_list"][1] == ("spreadsheet",)
    assert deliverables["cause_effect_matrix"][1] == ("document", "spreadsheet")
    assert deliverables["control_system_architecture_diagram"][1] == ("cad", "document")
    first = execute_control_automation_rule(
        hook_id="control_automation.io_logic_connectivity", hook_version="1.0.0",
        envelope={"missing_relationship_ids": ["implemented_in"]},
    )
    second = execute_control_automation_rule(
        hook_id="control_automation.io_logic_connectivity", hook_version="1.0.0",
        envelope={"missing_relationship_ids": ["implemented_in"]},
    )
    assert first == second and first.status == "FINDINGS"
    assert execute_control_automation_rule(
        hook_id="control_automation.unknown", hook_version="1.0.0", envelope={},
    ).status == "UNAVAILABLE"
    with pytest.raises(OperationalContractError):
        execute_control_automation_rule(
            hook_id="control_automation.object_relationship_integrity",
            hook_version="1.0.0", envelope={"objects": [{}] * 65},
        )


def test_control_relationship_contract_has_only_exact_endpoint_shapes():
    declarations = {d.relationship_type: d for d in CONTROL_AUTOMATION_RELATIONSHIP_DECLARATIONS}
    positives = {
        "controlled_by": ("hmi", "plc", False),
        "commands": ("plc", "motor", True),
        "receives_signal_from": ("io_channel", "transmitter", True),
        "sends_signal_to": ("dcs_controller", "control_valve", True),
        "implemented_in": ("control_logic", "esd_controller", False),
        "interlocked_with": ("plc", "dcs_controller", False),
        "trips": ("esd_controller", "motor", True),
        "initiates": ("plc", "control_logic", False),
        "inhibits": ("control_logic", "control_logic", False),
        "participates_in_sequence": ("control_cabinet", "control_logic", False),
        "monitored_by": ("io_channel", "hmi", False),
        "generates_alarm_for": ("control_logic", "instrument", True),
        "executes_logic_for": ("dcs_controller", "control_valve", True),
    }
    for name, (source, target, cross) in positives.items():
        assert declarations[name].permits(source, target, cross_workspace=cross)
    assert not declarations["commands"].permits("plc", "hmi")
    assert not declarations["commands"].permits("plc", "io_channel", cross_workspace=True)
    assert not declarations["receives_signal_from"].permits("plc", "motor", cross_workspace=True)
    assert declarations["interlocked_with"].direction == "bidirectional"
    assert declarations["interlocked_with"].cardinality == "many_to_many"
    assert declarations["participates_in_sequence"].cardinality == "many_to_many"


def test_control_legacy_identities_are_exact_and_unknown_aliases_fail_closed():
    workspace = translate_legacy_identity(LegacySourceContract.WORKSPACE, "control")
    assert (workspace.canonical_discipline_id, workspace.eligible_package_key) == (
        "control_automation", "control_automation",
    )
    ekg = translate_legacy_identity(LegacySourceContract.EKG, "industrial_automation")
    assert ekg.canonical_discipline_id == "control_automation" and ekg.eligible_package_key is None
    assert translate_legacy_identity(
        LegacySourceContract.OBJECT_RELATIONSHIP, "automation",
    ).disposition is LegacyDisposition.TAXONOMY_ONLY
    assert translate_legacy_identity(
        LegacySourceContract.GUIDANCE, "automation_and_control",
    ).disposition is LegacyDisposition.ADVISORY_CATEGORY_ONLY
    for source, value in (
        (LegacySourceContract.WORKSPACE, "control_automation"),
        (LegacySourceContract.WORKSPACE, " Control "),
        (LegacySourceContract.EKG, "control"),
        (LegacySourceContract.OBJECT_RELATIONSHIP, "automation_and_control"),
        (LegacySourceContract.GUIDANCE, "automation"),
    ):
        assert translate_legacy_identity(source, value).disposition is LegacyDisposition.UNRESOLVED


def test_only_the_exact_control_conformance_subset_is_verified():
    vectors = tuple(v for v in CONFORMANCE_VECTORS_V1
                    if v.vector_id.startswith("patch_052.control_automation.v1."))
    result = verify_package_subset(vectors, package_key="control_automation")
    assert result.vector_count == 13
    assert [vector_id for vector_id, _ in result.digests] == [
        f"patch_052.control_automation.v1.{suffix}" for suffix in VECTOR_SUFFIXES
    ]
    assert all(len(digest) == 64 for _, digest in result.digests)


def _create_control_objects(service, actor, project, workspace):
    rows = {}
    for index, declaration in enumerate(CONTROL_AUTOMATION_OBJECT_DECLARATIONS, 1):
        rows[declaration.object_type] = service.create_object(
            actor_id=actor.id, organization_id=ORG_ID, project_id=project.id,
            workspace_id=workspace.id,
            data=PackageObjectCreateRequest(
                declaration_id=declaration.declaration_id,
                primary_identifier_display_value=f"CA-{index:02d}",
                rationale="Batch-4 exact Object fixture",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    return rows


def _external_object(db_session, actor, project, workspace, *, family, discipline, object_type):
    now = datetime.now(timezone.utc)
    row = EngineeringObject(
        organization_id=ORG_ID, customer_id=project.customer_id,
        project_id=project.id, workspace_id=workspace.id, family=family,
        discipline=discipline, object_type=object_type, creator_id=actor.id,
        steward_id=actor.id, created_at=now, updated_at=now,
    )
    db_session.add(row); db_session.flush()
    return row


def test_control_objects_identifiers_all_thirteen_relationships_and_capture(
    db_session, engineer_user,
):
    project, workspace = _control_scope(db_session, engineer_user)
    service = ControlAutomationPackageService(_factory(db_session))
    created = _create_control_objects(service, engineer_user, project, workspace)
    for object_type, (obj, identifier) in created.items():
        persisted = db_session.get(EngineeringObject, obj.id)
        declaration = next(d for d in CONTROL_AUTOMATION_OBJECT_DECLARATIONS
                           if d.object_type == object_type)
        assert (persisted.family, persisted.discipline) == ("automation", "industrial_automation")
        assert identifier.identifier_kind.value == declaration.required_primary_identifier_kind
        assert db_session.scalar(select(EngineeringIdentifier).where(
            EngineeringIdentifier.engineering_object_id == obj.id,
        )) is not None

    electrical = EngineeringWorkspace(
        project_id=project.id, discipline="electrical", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id, version=1,
        canonical_discipline_id="electrical", package_binding_state="FUTURE_UNAVAILABLE_UNBOUND",
    )
    instrumentation = EngineeringWorkspace(
        project_id=project.id, discipline="instrumentation", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id, version=1,
        canonical_discipline_id="instrumentation", package_binding_state="FUTURE_UNAVAILABLE_UNBOUND",
    )
    db_session.add_all((electrical, instrumentation)); db_session.flush()
    motor = _external_object(db_session, engineer_user, project, electrical,
                             family="electrical", discipline="electrical", object_type="motor")
    valve = _external_object(db_session, engineer_user, project, instrumentation,
                             family="instrumentation", discipline="instrumentation", object_type="control_valve")
    instrument = _external_object(db_session, engineer_user, project, instrumentation,
                                  family="instrumentation", discipline="instrumentation", object_type="instrument")
    transmitter = _external_object(db_session, engineer_user, project, instrumentation,
                                   family="instrumentation", discipline="instrumentation", object_type="transmitter")
    pairs = {
        "controlled_by": ("hmi", "plc"), "commands": ("plc", motor),
        "receives_signal_from": ("io_channel", instrument),
        "sends_signal_to": ("dcs_controller", valve),
        "implemented_in": ("control_logic", "esd_controller"),
        "interlocked_with": ("plc", "dcs_controller"),
        "trips": ("esd_controller", motor), "initiates": ("plc", "control_logic"),
        "inhibits": ("esd_controller", "control_logic"),
        "participates_in_sequence": ("control_cabinet", "control_logic"),
        "monitored_by": ("io_channel", "hmi"),
        "generates_alarm_for": ("control_logic", transmitter),
        "executes_logic_for": ("dcs_controller", valve),
    }
    results = []
    for relationship_type, (source, target) in pairs.items():
        source_obj = created[source][0] if isinstance(source, str) else source
        target_obj = created[target][0] if isinstance(target, str) else target
        results.append(service.create_relationship(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageRelationshipCreateRequest(
                declaration_id=f"control_automation.relationship.{relationship_type}",
                source_object_id=source_obj.id, target_object_id=target_obj.id,
                rationale="Batch-4 exact Relationship fixture",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        ))
    assert len(results) == 13
    assert {row.relationship_family.value for row in results} == {"automation"}
    assert db_session.query(EngineeringRelationship).filter_by(
        origin_package_key="control_automation",
    ).count() == 13
    with pytest.raises(PackageDeclarationMismatch):
        service.create_relationship(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageRelationshipCreateRequest(
                declaration_id="control_automation.relationship.commands",
                source_object_id=created["plc"][0].id,
                target_object_id=created["hmi"][0].id,
                rationale="Reject an adjacent but undeclared tuple",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    capture = service.create_capture(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageCaptureCreateRequest(
            declaration_id="control_automation.control_philosophy_basis.input",
            engineering_object_id=created["plc"][0].id, source_kind="observation",
            original_content="Observed control philosophy basis",
            rationale="Canonical capture provenance only",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert capture.discipline == "industrial_automation"
    assert capture.origin_package_key == "control_automation"


def _context(db_session, actor, project, workspace, *, subject_kind, obj=None):
    now = datetime.now(timezone.utc)
    row = EngineeringContext(
        context_key=str(uuid4()), kind="qualified_fact", scope="workspace",
        project_id=project.id, workspace_id=workspace.id, owner_id=actor.id,
        steward_id=actor.id, created_by_id=actor.id,
        authority="engineer_verified_fact", lifecycle="current", version=1,
        created_at=now, updated_at=now,
    )
    db_session.add(row); db_session.flush()
    db_session.add(EngineeringContextFact(context_id=row.id, statement="Verified Control basis"))
    subject = EngineeringContextSubjectReference(
        context_id=row.id, subject_kind=subject_kind,
        subject_workspace_id=workspace.id if subject_kind == "workspace" else None,
        subject_engineering_object_id=obj.id if subject_kind == "engineering_object" else None,
    )
    db_session.add(subject); db_session.flush()
    return row, subject


def _evidence(db_session, actor, project, workspace, *, source_kind="engineering_record",
              deliverable_id=None, revision_id=None):
    now = datetime.now(timezone.utc)
    row = Evidence(
        organization_id=ORG_ID, project_id=project.id, workspace_id=workspace.id,
        lifecycle="current", source_kind=source_kind,
        source_reference=str(deliverable_id or uuid4()),
        source_revision=str(revision_id or uuid4()), source_standing="current",
        supported_fact="Human-verified Control basis", creator_id=actor.id,
        version=2, created_at=now, updated_at=now,
    )
    db_session.add(row); db_session.flush()
    db_session.add(EvidenceOutbox(
        event_id=uuid4(), aggregate_id=row.id, aggregate_version=2,
        event_type="EvidenceLifecycleTransitioned", payload={"lifecycle": "current"},
        occurred_at=now,
    ))
    db_session.flush()
    return row


def _bind_context(service, actor, project, workspace, context, subject, input_id):
    return service.bind_context(
        actor_id=actor.id, organization_id=ORG_ID, project_id=project.id,
        workspace_id=workspace.id,
        data=PackageContextBindingRequest(
            input_declaration_id=input_id, context_id=context.id,
            context_subject_reference_id=subject.id,
            expected_context_version=context.version,
            expected_configuration_revision=1, rationale="Bind exact Control Context",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )


def _bind_evidence(service, actor, project, workspace, evidence, input_id):
    return service.bind_evidence(
        actor_id=actor.id, organization_id=ORG_ID, project_id=project.id,
        workspace_id=workspace.id,
        data=PackageEvidenceBindingRequest(
            input_declaration_id=input_id, evidence_id=evidence.id,
            expected_evidence_version=evidence.version,
            expected_configuration_revision=1, rationale="Bind exact Control Evidence",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )


def test_control_exact_context_evidence_deliverable_readiness_and_transitions(
    db_session, engineer_user,
):
    project, workspace = _control_scope(db_session, engineer_user)
    package = ControlAutomationPackageService(_factory(db_session))
    logic = package.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageObjectCreateRequest(
            declaration_id="control_automation.object.control_logic",
            primary_identifier_display_value="LOGIC-001", rationale="Readiness fixture",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )[0]
    binding = PackageDeclarationBindingService(
        _factory(db_session), package_key="control_automation",
    )
    for name, subject_kind in (
        ("control_philosophy_basis", "workspace"),
        ("alarm_interlock_basis", "engineering_object"),
        ("cause_effect_basis", "engineering_object"),
    ):
        context, subject = _context(
            db_session, engineer_user, project, workspace,
            subject_kind=subject_kind, obj=logic,
        )
        _bind_context(
            binding, engineer_user, project, workspace, context, subject,
            f"control_automation.{name}.input",
        )
    philosophy = _evidence(db_session, engineer_user, project, workspace)
    cause_effect = _evidence(db_session, engineer_user, project, workspace)
    _bind_evidence(
        binding, engineer_user, project, workspace, philosophy,
        "control_automation.control_philosophy_evidence.input",
    )
    _bind_evidence(
        binding, engineer_user, project, workspace, cause_effect,
        "control_automation.cause_effect_interlock_evidence.input",
    )
    deliverables = EngineeringDeliverableService(
        uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(db_session),
        authorization=SqlAlchemyDeliverableAuthorization(db_session),
        package_uow_factory=lambda: Patch052OperationUnitOfWork(_factory(db_session)),
    )
    created = deliverables.create_package_control_automation(
        project_id=project.id,
        data=PackageDeliverableCreateRequest(
            declaration_id="control_automation.deliverable.cause_effect_matrix",
            code="CEM-001", title="Cause and effect matrix",
            discipline="industrial_automation", deliverable_type="cause_effect_matrix",
            external_authority="spreadsheet", workspace_id=workspace.id,
            initial_external_label="Rev 0", rationale="Initial Control deliverable",
        ), actor=DeliverableActor(actor_id=engineer_user.id, organization_id=ORG_ID),
        idempotency_key=uuid4(), correlation_id=uuid4(),
    )
    assert isinstance(created, DeliverableMutationSuccess)
    row = db_session.get(EngineeringDeliverable, created.deliverable_id)
    assert (row.discipline, row.origin_package_key, row.origin_declaration_id) == (
        "industrial_automation", "control_automation",
        "control_automation.deliverable.cause_effect_matrix",
    )
    ready = binding.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=created.deliverable_id, revision_id=created.revision_id,
        expected_configuration_revision=1, object_ids=(logic.id,),
        evidence_ids=(philosophy.id, cause_effect.id), correlation_id=uuid4(),
    )
    assert ready.status == "PASS" and ready.transition_allowed, ready.model_dump()
    assert set(ready.required_input_ids) == {
        "control_automation.control_philosophy_basis.input",
        "control_automation.alarm_interlock_basis.input",
        "control_automation.cause_effect_basis.input",
        "control_automation.control_philosophy_evidence.input",
        "control_automation.cause_effect_interlock_evidence.input",
    }
    reviewed_gate = binding.transition(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=created.deliverable_id, revision_id=created.revision_id,
        data=PackageTransitionRequest(
            target_standing="ready_for_review", expected_deliverable_version=1,
            expected_revision_version=1, expected_configuration_revision=1,
            object_ids=(logic.id,),
            evidence_ids=tuple(sorted((philosophy.id, cause_effect.id), key=str)),
            rationale="Exact Control package gate passed",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert reviewed_gate.status == "PASS"
    db_session.refresh(row)
    revision = db_session.get(EngineeringDeliverableRevision, created.revision_id)
    owner_review = deliverables.transition_revision(
        project_id=project.id, deliverable_id=row.id, revision_id=revision.id,
        data=TransitionRevisionRequest(
            expected_deliverable_version=2, expected_revision_version=2,
            target_standing="reviewed", rationale="Human review completed",
        ), actor=DeliverableActor(actor_id=engineer_user.id, organization_id=ORG_ID),
        idempotency_key=uuid4(),
    )
    assert isinstance(owner_review, DeliverableMutationSuccess)
    db_session.refresh(row); db_session.refresh(revision)
    human_review = _evidence(
        db_session, engineer_user, project, workspace, source_kind="human_review",
        deliverable_id=row.id, revision_id=revision.id,
    )
    _bind_evidence(
        binding, engineer_user, project, workspace, human_review,
        "control_automation.deliverable_review_evidence.input",
    )
    issued = binding.transition(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=row.id, revision_id=revision.id,
        data=PackageTransitionRequest(
            target_standing="issued", expected_deliverable_version=row.version,
            expected_revision_version=revision.version,
            expected_configuration_revision=1, object_ids=(),
            evidence_ids=(human_review.id,), rationale="Issue exact reviewed revision",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert issued.status == "PASS"
    assert db_session.query(EngineeringContextPackageInputBinding).count() == 3
    assert db_session.query(EvidencePackageInputBinding).count() == 3


def test_control_authorization_rebind_historical_and_readiness_fail_closed(
    db_session, engineer_user,
):
    project, workspace = _control_scope(
        db_session, engineer_user, standing="historical_read_only",
    )
    service = ControlAutomationPackageService(_factory(db_session))
    request = PackageObjectCreateRequest(
        declaration_id="control_automation.object.plc",
        primary_identifier_display_value="PLC-AUTH-01", rationale="Authorization proof",
    )
    with pytest.raises(PackageProtectedNotFound):
        service.create_object(
            actor_id=engineer_user.id, organization_id=uuid4(),
            project_id=project.id, workspace_id=workspace.id, data=request,
            correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    with pytest.raises(PackageUnavailable):
        service.create_object(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id, data=request,
            correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    workspace.package_binding_state = "FUTURE_UNAVAILABLE_UNBOUND"
    workspace.bound_package_key = None
    workspace.bound_project_configuration_revision = None
    db_session.commit()
    with pytest.raises(PackageUnavailable):
        service.create_object(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id, data=request,
            correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    snapshot = control_automation_operational_readiness_snapshot(
        db_session.connection(),
        frontend_component_keys=frozenset({"workspace.control_automation.v1"}),
    )
    assert snapshot.ready and snapshot.migration_revision == TEST_DATABASE_REVISION
    assert (snapshot.object_count, snapshot.relationship_count,
            snapshot.input_count, snapshot.deliverable_count,
            snapshot.evidence_count, snapshot.rule_count) == (7, 13, 9, 5, 4, 5)
    assert not control_automation_operational_readiness_snapshot(
        db_session.connection(), frontend_component_keys=frozenset(),
    ).ready


def test_control_object_identifier_audit_and_outboxes_roll_back_atomically(
    db_session, engineer_user,
):
    project, workspace = _control_scope(db_session, engineer_user)
    service = ControlAutomationPackageService(_factory(db_session))
    replay_request = PackageObjectCreateRequest(
        declaration_id="control_automation.object.plc",
        primary_identifier_display_value="PLC-REPLAY",
        rationale="Control immutable replay proof",
    )
    replay_key = uuid4()
    original = service.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=replay_request,
        correlation_id=uuid4(), idempotency_key=replay_key,
    )
    replay = service.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=replay_request,
        correlation_id=uuid4(), idempotency_key=replay_key,
    )
    assert replay == original
    counts = (
        db_session.query(EngineeringObject).count(),
        db_session.query(EngineeringIdentifier).count(),
        db_session.query(EngineeringObjectIdempotency).count(),
        db_session.query(EngineeringObjectOutbox).count(),
        db_session.query(EngineeringIdentifierOutbox).count(),
        db_session.query(AuditLog).count(),
    )
    with pytest.raises(PackageConflict):
        service.create_object(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageObjectCreateRequest(
                declaration_id="control_automation.object.plc",
                primary_identifier_display_value="PLC-ROLLBACK",
                primary_identifier_evidence_references=(uuid4(),),
                rationale="Force Evidence FK rollback",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    assert counts == (
        db_session.query(EngineeringObject).count(),
        db_session.query(EngineeringIdentifier).count(),
        db_session.query(EngineeringObjectIdempotency).count(),
        db_session.query(EngineeringObjectOutbox).count(),
        db_session.query(EngineeringIdentifierOutbox).count(),
        db_session.query(AuditLog).count(),
    )


def test_control_public_api_dispatch_and_server_effective_state(
    client, db_session, engineer_user, engineer_headers, monkeypatch,
):
    from app.api.v1.routers import discipline_package_operations as routes

    project, workspace = _control_scope(db_session, engineer_user)
    monkeypatch.setattr(routes, "SessionLocal", _factory(db_session))
    base = f"/projects/{project.id}/discipline-packages/workspaces/{workspace.id}"
    headers = {
        **engineer_headers, "X-Correlation-ID": str(uuid4()),
        "Idempotency-Key": str(uuid4()),
    }
    created = client.post(f"{base}/operations/objects", headers=headers, json={
        "declaration_id": "control_automation.object.plc",
        "primary_identifier_display_value": "PLC-API-01",
        "primary_identifier_evidence_references": [], "steward_id": None,
        "rationale": "Public Control object route",
    })
    assert created.status_code == 201
    assert created.json()["object"]["origin_package_key"] == "control_automation"
    evaluated = client.post(f"{base}/rule-evaluations", headers=headers, json={
        "hook_id": "control_automation.io_logic_connectivity",
        "hook_version": "1.0.0",
        "envelope": {"missing_relationship_ids": []},
    })
    assert evaluated.status_code == 200 and evaluated.json()["status"] == "PASS"
    applicability = client.get(
        f"/workspaces/{workspace.id}/package-applicability",
        headers=engineer_headers,
    )
    assert applicability.status_code == 200
    assert applicability.json()["operational_state"] == "OPERATIONAL_AVAILABLE"
    assert applicability.json()["component_key"] == "workspace.control_automation.v1"
    assert client.post(f"{base}/operations/objects", headers={
        **headers, "Idempotency-Key": str(uuid4()),
    }, json={
        "declaration_id": "control_automation.object.customer_plc",
        "primary_identifier_display_value": "PLC-API-02",
        "rationale": "Unknown declaration must fail closed",
    }).status_code == 422

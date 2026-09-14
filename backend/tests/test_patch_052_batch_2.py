"""PATCH-052 Batch-2 Electrical/shared-cutover acceptance evidence."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker

from app.discipline_packages.descriptors.eic_v1 import (
    DESCRIPTORS_V1,
    DESCRIPTOR_DIGESTS_V1,
    ELECTRICAL_OBJECT_DECLARATIONS,
    ELECTRICAL_RELATIONSHIP_DECLARATIONS,
)
from app.discipline_packages.operational import (
    OperationalContractError,
    execute_electrical_rule,
)
from app.discipline_packages import readiness_052
from app.discipline_packages.readiness_052 import electrical_operational_readiness_snapshot
from app.exceptions.engineering_identifier import EngineeringIdentifierConflict
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.discipline_package import (
    CompatibilityProfile,
    OrganizationPackageConfigurationHead,
    OrganizationPackageSelection,
    PackageDescriptor,
    ProjectPackageConfigurationHead,
    ProjectPackageConfigurationRevision,
    ProjectPackageConfigurationSelection,
    RegistryMembership,
    RegistryProfileMembership,
    RegistryRelease,
)
from app.models.engineering_identifier import (
    EngineeringIdentifier,
    normalize_engineering_identifier,
)
from app.models.engineering_identifier_command import EngineeringIdentifierOutbox
from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import (
    EngineeringObjectIdempotency,
    EngineeringObjectOutbox,
)
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_deliverable import EngineeringDeliverable
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.repositories.engineering_identifier_unit_of_work import (
    SqlAlchemyEngineeringIdentifierUnitOfWork,
)
from app.repositories.engineering_deliverable_unit_of_work import (
    SqlAlchemyEngineeringDeliverableUnitOfWork,
)
from app.repositories.patch_052_operation_unit_of_work import Patch052OperationUnitOfWork
from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization
from app.schemas.discipline_package_operations import (
    PackageCaptureCreateRequest,
    PackageDeliverableCreateRequest,
    PackageObjectCreateRequest,
    PackageRelationshipCreateRequest,
)
from app.schemas.engineering_identifier import (
    CreateEngineeringIdentifierRequest,
    ReassignPrimaryIdentifierRequest,
    ReplaceEngineeringIdentifierRequest,
    WithdrawEngineeringIdentifierRequest,
)
from app.services.electrical_package_service import (
    ElectricalPackageService,
    PackageConflict,
    PackageDeclarationMismatch,
    PackageProtectedNotFound,
)
from app.services.engineering_identifier_service import EngineeringIdentifierService
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.schemas.engineering_deliverable import DeliverableActor, DeliverableMutationSuccess


ORG_ID = UUID("02810000-0000-4000-8000-000000000001")


def _factory(db_session):
    return sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


def _electrical_scope(db_session, engineer_user):
    descriptor = next(item for item in DESCRIPTORS_V1 if item.package_key == "electrical")
    digest = str(DESCRIPTOR_DIGESTS_V1["electrical"])
    registry_digest = "5" * 64
    profile_digest = "6" * 64
    db_session.add_all((
        RegistryRelease(
            registry_digest=registry_digest, release_id=f"patch-052-b2-{uuid4().hex}",
            core_contract_version=1, is_current=True, manifest_json={"release": "patch-052"},
        ),
        PackageDescriptor(
            package_key="electrical", package_version="1.0.0",
            descriptor_digest=digest, primary_discipline_id="electrical",
            adapter_id="discipline.electrical.v1",
            descriptor_json=descriptor.model_dump(mode="json"),
        ),
        CompatibilityProfile(
            profile_id="patch-052-b2", profile_digest=profile_digest,
            profile_json={"profile": "patch-052-b2"},
        ),
    ))
    db_session.flush()
    db_session.add_all((
        RegistryMembership(
            registry_digest=registry_digest, package_key="electrical",
            package_version="1.0.0", standing="executable_supported",
        ),
        RegistryProfileMembership(
            registry_digest=registry_digest, profile_id="patch-052-b2",
            profile_digest=profile_digest,
        ),
        OrganizationPackageConfigurationHead(
            organization_id=ORG_ID, configuration_version=1,
        ),
        OrganizationPackageSelection(
            organization_id=ORG_ID, package_key="electrical",
            package_version="1.0.0", state="enabled",
            configuration_version=1,
        ),
    ))
    customer = Customer(organization_id=ORG_ID, name="PATCH-052 Batch-2")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        organization_id=ORG_ID,
        project_code=f"SAT-PRJ-2099-{customer.id + 7000:04d}",
        name="PATCH-052 Electrical", customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(ProjectPackageConfigurationRevision(
        project_id=project.id, configuration_revision=1,
        organization_id=ORG_ID, observed_registry_digest=registry_digest,
        profile_id="patch-052-b2", profile_digest=profile_digest,
        rationale="Batch-2 isolated proof",
    ))
    db_session.flush()
    db_session.add(ProjectPackageConfigurationSelection(
        project_id=project.id, configuration_revision=1,
        package_key="electrical", package_version="1.0.0",
        descriptor_digest=digest,
    ))
    db_session.add(ProjectPackageConfigurationHead(
        project_id=project.id,
        organization_id=ORG_ID,
        current_revision=1,
        configuration_version=1,
    ))
    workspace = EngineeringWorkspace(
        project_id=project.id, discipline="electrical", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id, version=1,
        canonical_discipline_id="electrical",
        package_binding_state="OPERATIONAL_PACKAGE_BOUND",
        bound_package_key="electrical",
        bound_project_configuration_revision=1,
    )
    db_session.add(workspace)
    db_session.commit()
    return project, workspace


def test_electrical_catalogs_and_rules_are_exact_and_fail_closed():
    assert len(ELECTRICAL_OBJECT_DECLARATIONS) == 8
    assert len(ELECTRICAL_RELATIONSHIP_DECLARATIONS) == 7
    descriptor = next(item for item in DESCRIPTORS_V1 if item.package_key == "electrical")
    contributions = descriptor.contributions
    assert (
        len(contributions.engineering_inputs),
        len(contributions.deliverables),
        len(contributions.evidence_requirements),
        len(contributions.deterministic_rule_hooks),
    ) == (9, 4, 4, 5)
    first = execute_electrical_rule(
        hook_id="electrical.required_input_completeness", hook_version="1.0.0",
        envelope={"missing_required_ids": ["electrical.system_voltage_basis.input"]},
    )
    second = execute_electrical_rule(
        hook_id="electrical.required_input_completeness", hook_version="1.0.0",
        envelope={"missing_required_ids": ["electrical.system_voltage_basis.input"]},
    )
    assert first == second and first.status == "FINDINGS"
    assert execute_electrical_rule(
        hook_id="electrical.unknown", hook_version="1.0.0", envelope={},
    ).status == "UNAVAILABLE"
    with pytest.raises(OperationalContractError):
        execute_electrical_rule(
            hook_id="electrical.object_relationship_integrity", hook_version="1.0.0",
            envelope={"objects": [{}] * 65},
        )


def test_shared_schema_has_one_head_and_required_guards(db_session):
    observed_revision = db_session.execute(text("select version_num from alembic_version")).scalar_one()
    assert observed_revision == "e05400000006"
    schema = inspect(db_session.connection())
    assert {
        "engineering_identifiers", "engineering_identifier_idempotency",
        "engineering_identifier_outbox",
    } <= set(schema.get_table_names())
    assert {column["name"] for column in schema.get_columns("engineering_objects")} >= {
        "origin_package_key", "origin_project_configuration_revision", "origin_declaration_id",
    }
    indexes = {item["name"] for item in schema.get_indexes("engineering_identifiers")}
    assert {
        "uq_engineering_identifier_current_value",
        "uq_engineering_identifier_current_primary",
        "ix_engineering_identifier_current_set",
        "ix_engineering_identifier_scope_history",
    } <= indexes
    functions = set(db_session.execute(text(
        "select proname from pg_proc where proname like 'satco_patch052_%'"
    )).scalars())
    assert {
        "satco_patch052_origin_immutable", "satco_patch052_identifier_guard",
        "satco_patch052_identifier_cardinality", "satco_patch052_context_object_coherence",
    } <= functions
    readiness = electrical_operational_readiness_snapshot(
        db_session.connection(),
        frontend_component_keys=frozenset({"workspace.electrical.v1"}),
    )
    assert readiness.ready is True and readiness.migration_revision == observed_revision
    assert readiness_052._patch_052_revision_is_in_lineage("e05200000002") is True
    assert electrical_operational_readiness_snapshot(
        db_session.connection(), frontend_component_keys=frozenset(),
    ).ready is False


@pytest.mark.parametrize(
    ("revision", "expected"),
    (
        ("e05200000002", True),
        ("e05300000001", True),
        ("e05300000002", True),
        ("e05400000006", True),
        ("e05200000001", False),
        ("unknown-revision", False),
    ),
)
def test_patch_052_readiness_revision_lineage_is_closed(revision, expected):
    assert readiness_052._patch_052_revision_is_in_lineage(revision) is expected


def test_patch_052_readiness_rejects_a_divergent_revision(monkeypatch):
    class _Revision:
        revision = "divergent-head"

    class _DivergentScripts:
        def walk_revisions(self, *, base, head):
            assert (base, head) == ("base", "divergent-head")
            return (_Revision(),)

    monkeypatch.setattr(
        readiness_052.ScriptDirectory,
        "from_config",
        lambda config: _DivergentScripts(),
    )
    assert readiness_052._patch_052_revision_is_in_lineage("divergent-head") is False


def test_package_object_and_required_primary_identifier_are_atomic(
    db_session, engineer_user,
):
    project, workspace = _electrical_scope(db_session, engineer_user)
    service = ElectricalPackageService(_factory(db_session))
    request = PackageObjectCreateRequest(
        declaration_id="electrical.object.electrical_feeder",
        primary_identifier_display_value="  FDR\u00a0 01 ",
        rationale="Create governed feeder",
    )
    key = uuid4()
    obj, identifier = service.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=request,
        correlation_id=uuid4(), idempotency_key=key,
    )
    replay_object, replay_identifier = service.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=request,
        correlation_id=uuid4(), idempotency_key=key,
    )
    assert replay_object.id == obj.id and replay_identifier.identifier_id == identifier.identifier_id
    assert identifier.identifier_kind.value == "feeder_number"
    assert identifier.normalized_value == "fdr 01"
    assert (
        obj.origin_package_key,
        obj.origin_project_configuration_revision,
        obj.origin_declaration_id,
    ) == ("electrical", 1, "electrical.object.electrical_feeder")
    persisted = db_session.get(EngineeringObject, obj.id)
    current = db_session.scalars(select(EngineeringIdentifier).where(
        EngineeringIdentifier.engineering_object_id == obj.id,
        EngineeringIdentifier.lifecycle == "current",
    )).all()
    assert persisted is not None and len(current) == 1 and current[0].primary_role == "primary"
    assert db_session.scalar(select(AuditLog).where(AuditLog.entity_uuid == obj.id)) is not None
    assert db_session.scalar(select(EngineeringIdentifierOutbox).where(
        EngineeringIdentifierOutbox.identifier_id == identifier.identifier_id,
    )) is not None


def test_object_identifier_audit_and_outboxes_roll_back_together(
    db_session, engineer_user,
):
    project, workspace = _electrical_scope(db_session, engineer_user)
    service = ElectricalPackageService(_factory(db_session))
    before = db_session.query(EngineeringObject).count()
    audit_before = db_session.query(AuditLog).count()
    object_outbox_before = db_session.query(EngineeringObjectOutbox).count()
    identifier_outbox_before = db_session.query(EngineeringIdentifierOutbox).count()
    idempotency_before = db_session.query(EngineeringObjectIdempotency).count()
    with pytest.raises(PackageConflict):
        service.create_object(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageObjectCreateRequest(
                declaration_id="electrical.object.motor",
                primary_identifier_display_value="MTR-ROLLBACK",
                primary_identifier_evidence_references=(uuid4(),),
                rationale="Force an Evidence FK guard rejection",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    assert db_session.query(EngineeringObject).count() == before
    assert db_session.query(AuditLog).count() == audit_before
    assert db_session.query(EngineeringObjectOutbox).count() == object_outbox_before
    assert db_session.query(EngineeringIdentifierOutbox).count() == identifier_outbox_before
    assert db_session.query(EngineeringObjectIdempotency).count() == idempotency_before


def test_relationship_endpoints_are_authorized_before_exact_tuple_resolution(
    db_session, engineer_user,
):
    project, workspace = _electrical_scope(db_session, engineer_user)
    service = ElectricalPackageService(_factory(db_session))
    def create(declaration, display):
        return service.create_object(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageObjectCreateRequest(
                declaration_id=declaration,
                primary_identifier_display_value=display,
                rationale="Relationship fixture",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )[0]
    motor = create("electrical.object.motor", "MTR-R1")
    source = create("electrical.object.electrical_power_source", "SRC-R1")
    request = PackageRelationshipCreateRequest(
        declaration_id="electrical.relationship.powered_by",
        source_object_id=motor.id, target_object_id=source.id,
        rationale="Record authorized supply",
    )
    relationship = service.create_relationship(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=request,
        correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    stored = db_session.get(EngineeringRelationship, relationship.id)
    assert stored is not None and stored.origin_declaration_id == "electrical.relationship.powered_by"
    with pytest.raises(PackageDeclarationMismatch):
        service.create_relationship(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=request.model_copy(update={
                "source_object_id": source.id, "target_object_id": motor.id,
            }), correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    with pytest.raises(PackageProtectedNotFound):
        service.create_relationship(
            actor_id=engineer_user.id, organization_id=uuid4(),
            project_id=project.id, workspace_id=workspace.id, data=request,
            correlation_id=uuid4(), idempotency_key=uuid4(),
        )


def test_identifier_lifecycle_idempotency_uniqueness_and_no_delete(
    db_session, engineer_user,
):
    project, workspace = _electrical_scope(db_session, engineer_user)
    package = ElectricalPackageService(_factory(db_session))
    package_request = PackageObjectCreateRequest(
        declaration_id="electrical.object.motor",
        primary_identifier_display_value="MTR-001",
        rationale="Create motor",
    )
    package_key = uuid4()
    obj, primary = package.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=package_request, correlation_id=uuid4(), idempotency_key=package_key,
    )
    identifiers = EngineeringIdentifierService(
        lambda: SqlAlchemyEngineeringIdentifierUnitOfWork(_factory(db_session))
    )
    request = CreateEngineeringIdentifierRequest(
        identifier_kind="vendor_reference", display_value="Vendor\u00a0 A",
        expected_object_version=1, rationale="Add vendor reference",
    )
    key = uuid4()
    alternate = identifiers.create(
        actor_id=engineer_user.id, organization_id=ORG_ID, object_id=obj.id,
        data=request, correlation_id=uuid4(), idempotency_key=key,
    )
    replay = identifiers.create(
        actor_id=engineer_user.id, organization_id=ORG_ID, object_id=obj.id,
        data=request, correlation_id=uuid4(), idempotency_key=key,
    )
    assert replay.identifier_id == alternate.identifier_id
    assert alternate.normalized_value == "vendor a"
    with pytest.raises(EngineeringIdentifierConflict):
        identifiers.reassign_primary(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            object_id=obj.id,
            data=ReassignPrimaryIdentifierRequest(
                target_identifier_id=alternate.identifier_id,
                expected_object_version=1,
                expected_identifier_versions={
                    primary.identifier_id: 1,
                    alternate.identifier_id: 1,
                },
                rationale="Package primary cannot lose its governed origin",
            ),
            correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    with pytest.raises(EngineeringIdentifierConflict):
        identifiers.create(
            actor_id=engineer_user.id, organization_id=ORG_ID, object_id=obj.id,
            data=request, correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    withdrawn = identifiers.withdraw(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        identifier_id=alternate.identifier_id, expected_version=1,
        rationale="Reference retired", correlation_id=uuid4(),
        idempotency_key=uuid4(),
    )
    assert withdrawn.lifecycle.value == "withdrawn" and withdrawn.version == 2
    late_create_replay = identifiers.create(
        actor_id=engineer_user.id, organization_id=ORG_ID, object_id=obj.id,
        data=request, correlation_id=uuid4(), idempotency_key=key,
    )
    assert late_create_replay == alternate
    with pytest.raises(EngineeringIdentifierConflict):
        identifiers.withdraw(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            identifier_id=primary.identifier_id, expected_version=1,
            rationale="Invalid primary withdrawal", correlation_id=uuid4(),
            idempotency_key=uuid4(),
        )
    with pytest.raises(EngineeringIdentifierConflict):
        identifiers.replace(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            identifier_id=primary.identifier_id,
            data=ReplaceEngineeringIdentifierRequest(
                identifier_kind="vendor_reference", display_value="INVALID-PRIMARY",
                expected_object_version=1, expected_identifier_version=1,
                rationale="Package required kind must be retained",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )
    successor = identifiers.replace(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        identifier_id=primary.identifier_id,
        data=ReplaceEngineeringIdentifierRequest(
            identifier_kind="equipment_number", display_value="MTR-001A",
            expected_object_version=1, expected_identifier_version=1,
            rationale="Correct primary identifier",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert successor.predecessor_identifier_id == primary.identifier_id
    assert successor.primary_role.value == "primary"
    assert successor.origin_declaration_id == "electrical.object.motor"
    replay_object, replayed_original_primary = package.create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=package_request, correlation_id=uuid4(), idempotency_key=package_key,
    )
    assert replay_object.id == obj.id
    assert replayed_original_primary == primary
    history, cursor = identifiers.history(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        object_id=obj.id, limit=2,
    )
    assert len(history) == 2 and cursor is not None
    second_page, _ = identifiers.history(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        object_id=obj.id, limit=2, cursor=cursor,
    )
    assert second_page
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text(
                "delete from engineering_identifiers where identifier_id=:identifier_id"
            ), {"identifier_id": primary.identifier_id})


def test_package_capture_is_canonical_provenance_only_affordance(
    db_session, engineer_user,
):
    project, workspace = _electrical_scope(db_session, engineer_user)
    service = ElectricalPackageService(_factory(db_session))
    request = PackageCaptureCreateRequest(
        declaration_id="electrical.load_duty_basis.input",
        source_kind="field_note", original_content="Observed duty statement",
        source_reference="field note 17", rationale="Retain source affordance",
    )
    key = uuid4()
    capture = service.create_capture(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=request,
        correlation_id=uuid4(), idempotency_key=key,
    )
    replay = service.create_capture(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id, data=request,
        correlation_id=uuid4(), idempotency_key=key,
    )
    assert replay.id == capture.id
    assert capture.origin_declaration_id == "electrical.load_duty_basis.input"
    assert capture.lifecycle.value == "captured"


def test_package_deliverable_creation_retains_exact_origin(
    db_session, engineer_user,
):
    project, workspace = _electrical_scope(db_session, engineer_user)
    service = EngineeringDeliverableService(
        uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(db_session),
        authorization=SqlAlchemyDeliverableAuthorization(db_session),
        package_uow_factory=lambda: Patch052OperationUnitOfWork(_factory(db_session)),
    )
    result = service.create_package_electrical(
        project_id=project.id,
        data=PackageDeliverableCreateRequest(
            declaration_id="electrical.deliverable.electrical_load_list",
            code="ELL-001", title="Electrical load list",
            discipline="electrical", deliverable_type="electrical_load_list",
            external_authority="spreadsheet", workspace_id=workspace.id,
            initial_external_label="Rev 0", rationale="Initial package deliverable",
        ),
        actor=DeliverableActor(actor_id=engineer_user.id, organization_id=ORG_ID),
        idempotency_key=uuid4(), correlation_id=uuid4(),
    )
    assert isinstance(result, DeliverableMutationSuccess)
    row = db_session.get(EngineeringDeliverable, result.deliverable_id)
    assert row is not None
    assert (
        row.origin_package_key,
        row.origin_project_configuration_revision,
        row.origin_declaration_id,
    ) == ("electrical", 1, "electrical.deliverable.electrical_load_list")


def test_legacy_object_keeps_null_origin_and_gets_no_fabricated_identifier(
    db_session, engineer_user,
):
    customer = Customer(organization_id=ORG_ID, name="Legacy PATCH-052")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        organization_id=ORG_ID,
        project_code=f"SAT-PRJ-2098-{customer.id + 8000:04d}",
        name="Legacy project", customer_id=customer.id, owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    workspace = EngineeringWorkspace(
        project_id=project.id, discipline="electrical", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id,
    )
    db_session.add(workspace)
    db_session.flush()
    obj = EngineeringObject(
        organization_id=ORG_ID, customer_id=customer.id, project_id=project.id,
        workspace_id=workspace.id, family="electrical", discipline="electrical",
        object_type="motor", creator_id=engineer_user.id, steward_id=engineer_user.id,
    )
    db_session.add(obj)
    db_session.commit()
    assert obj.origin_package_key is None
    assert db_session.scalar(select(EngineeringIdentifier).where(
        EngineeringIdentifier.engineering_object_id == obj.id,
    )) is None
    assert normalize_engineering_identifier("  MTR\u00a0 01 ") == "mtr 01"

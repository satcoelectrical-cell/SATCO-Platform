"""PATCH-052 Batch-3 Instrumentation evidence up to the migration stop gate."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.discipline_packages.descriptors.eic_v1 import (
    DESCRIPTORS_V1, DESCRIPTOR_DIGESTS_V1,
    INSTRUMENTATION_OBJECT_DECLARATIONS,
    INSTRUMENTATION_RELATIONSHIP_DECLARATIONS,
)
from app.discipline_packages.operational import (
    OperationalContractError, execute_instrumentation_rule,
)
from app.discipline_packages.readiness_052 import (
    instrumentation_operational_readiness_snapshot,
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
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.schemas.discipline_package_operations import (
    PackageCaptureCreateRequest, PackageObjectCreateRequest,
    PackageRelationshipCreateRequest,
)
from app.services.electrical_package_service import PackageDeclarationMismatch
from app.services.instrumentation_package_service import InstrumentationPackageService


ORG_ID = UUID("02810000-0000-4000-8000-000000000001")


def _factory(db_session):
    return sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


def _instrumentation_scope(db_session, engineer_user):
    descriptor = next(
        item for item in DESCRIPTORS_V1
        if item.package_key == "instrumentation"
    )
    digest = str(DESCRIPTOR_DIGESTS_V1["instrumentation"])
    registry_digest, profile_digest = "7" * 64, "8" * 64
    db_session.add_all((
        RegistryRelease(
            registry_digest=registry_digest,
            release_id=f"patch-052-b3-{uuid4().hex}",
            core_contract_version=1, is_current=True,
            manifest_json={"release": "patch-052"},
        ),
        PackageDescriptor(
            package_key="instrumentation", package_version="1.0.0",
            descriptor_digest=digest,
            primary_discipline_id="instrumentation",
            adapter_id="discipline.instrumentation.v1",
            descriptor_json=descriptor.model_dump(mode="json"),
        ),
        CompatibilityProfile(
            profile_id="patch-052-b3", profile_digest=profile_digest,
            profile_json={"profile": "patch-052-b3"},
        ),
    ))
    db_session.flush()
    db_session.add_all((
        RegistryMembership(
            registry_digest=registry_digest, package_key="instrumentation",
            package_version="1.0.0", standing="executable_supported",
        ),
        RegistryProfileMembership(
            registry_digest=registry_digest, profile_id="patch-052-b3",
            profile_digest=profile_digest,
        ),
        OrganizationPackageConfigurationHead(
            organization_id=ORG_ID, configuration_version=1,
        ),
        OrganizationPackageSelection(
            organization_id=ORG_ID, package_key="instrumentation",
            package_version="1.0.0", state="enabled",
            configuration_version=1,
        ),
    ))
    customer = Customer(organization_id=ORG_ID, name="PATCH-052 Batch-3")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        organization_id=ORG_ID,
        project_code=f"SAT-PRJ-2099-{customer.id + 8000:04d}",
        name="PATCH-052 Instrumentation", customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(ProjectPackageConfigurationRevision(
        project_id=project.id, configuration_revision=1,
        organization_id=ORG_ID, observed_registry_digest=registry_digest,
        profile_id="patch-052-b3", profile_digest=profile_digest,
        rationale="Batch-3 isolated proof",
    ))
    db_session.flush()
    db_session.add_all((
        ProjectPackageConfigurationSelection(
            project_id=project.id, configuration_revision=1,
            package_key="instrumentation", package_version="1.0.0",
            descriptor_digest=digest,
        ),
        ProjectPackageConfigurationHead(
            project_id=project.id, organization_id=ORG_ID,
            current_revision=1, configuration_version=1,
        ),
    ))
    workspace = EngineeringWorkspace(
        project_id=project.id, discipline="instrumentation", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id, version=1,
        canonical_discipline_id="instrumentation",
        package_binding_state="OPERATIONAL_PACKAGE_BOUND",
        bound_package_key="instrumentation",
        bound_project_configuration_revision=1,
    )
    db_session.add(workspace)
    db_session.commit()
    return project, workspace


def test_instrumentation_catalog_is_exact_and_rules_are_bounded():
    assert [item.object_type for item in INSTRUMENTATION_OBJECT_DECLARATIONS] == [
        "instrument", "transmitter", "analyzer", "flowmeter", "control_valve",
        "instrument_loop", "junction_box", "instrument_panel",
    ]
    assert len(INSTRUMENTATION_RELATIONSHIP_DECLARATIONS) == 5
    feedback = next(
        item for item in INSTRUMENTATION_RELATIONSHIP_DECLARATIONS
        if item.relationship_type == "provides_feedback_to"
    )
    assert feedback.permits("transmitter", "io_channel", cross_workspace=True)
    assert not feedback.permits("transmitter", "instrument_loop", cross_workspace=True)
    first = execute_instrumentation_rule(
        hook_id="instrumentation.loop_signal_connectivity",
        hook_version="1.0.0",
        envelope={"missing_relationship_ids": ["connected_to_loop"]},
    )
    assert first.status == "FINDINGS"
    assert first == execute_instrumentation_rule(
        hook_id="instrumentation.loop_signal_connectivity",
        hook_version="1.0.0",
        envelope={"missing_relationship_ids": ["connected_to_loop"]},
    )
    with pytest.raises(OperationalContractError):
        execute_instrumentation_rule(
            hook_id="instrumentation.object_relationship_integrity",
            hook_version="1.0.0", envelope={"objects": [{}] * 65},
        )


def test_instrumentation_object_identifier_capture_and_relationship(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    service = InstrumentationPackageService(_factory(db_session))

    def create(kind, identifier):
        return service.create_object(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageObjectCreateRequest(
                declaration_id=f"instrumentation.object.{kind}",
                primary_identifier_display_value=identifier,
                rationale="Batch-3 representative fixture",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )

    transmitter, primary = create("transmitter", "  FT\u00a0 101 ")
    junction_box, _ = create("junction_box", "JB-101")
    assert primary.identifier_kind.value == "tag_number"
    assert primary.normalized_value == "ft 101"
    assert transmitter.origin_package_key == "instrumentation"
    assert db_session.scalar(select(EngineeringIdentifier).where(
        EngineeringIdentifier.engineering_object_id == transmitter.id,
    )) is not None

    relationship = service.create_relationship(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageRelationshipCreateRequest(
            declaration_id="instrumentation.relationship.transmits_to",
            source_object_id=transmitter.id, target_object_id=junction_box.id,
            rationale="Record exact signal path",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert relationship.origin_declaration_id == "instrumentation.relationship.transmits_to"

    control_workspace = EngineeringWorkspace(
        project_id=project.id, discipline="control", status="active",
        owner_id=engineer_user.id, created_by_id=engineer_user.id, version=1,
        canonical_discipline_id="control_automation",
        package_binding_state="FUTURE_UNAVAILABLE_UNBOUND",
    )
    db_session.add(control_workspace)
    db_session.flush()
    now = datetime.now(timezone.utc)
    io_channel = EngineeringObject(
        organization_id=ORG_ID, customer_id=project.customer_id,
        project_id=project.id, workspace_id=control_workspace.id,
        family="automation", discipline="industrial_automation",
        object_type="io_channel", creator_id=engineer_user.id,
        steward_id=engineer_user.id, created_at=now, updated_at=now,
    )
    db_session.add(io_channel)
    db_session.flush()
    cross_workspace = service.create_relationship(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageRelationshipCreateRequest(
            declaration_id="instrumentation.relationship.connected_to_io_channel",
            source_object_id=transmitter.id, target_object_id=io_channel.id,
            rationale="Record independently authorized I/O channel endpoint",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert cross_workspace.target_object_id == io_channel.id
    with pytest.raises(PackageDeclarationMismatch):
        service.create_relationship(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageRelationshipCreateRequest(
                declaration_id="instrumentation.relationship.calibrated_against",
                source_object_id=transmitter.id, target_object_id=junction_box.id,
                rationale="Reject undeclared tuple",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )

    capture = service.create_capture(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageCaptureCreateRequest(
            declaration_id="instrumentation.measurement_service.input",
            engineering_object_id=transmitter.id, source_kind="observation",
            original_content="Differential pressure measurement service",
            rationale="Capture source affordance",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert capture.origin_package_key == "instrumentation"
    assert db_session.get(EngineeringRelationship, relationship.id) is not None
    assert db_session.scalar(select(AuditLog).where(
        AuditLog.entity_uuid == transmitter.id,
    )).details["package_key"] == "instrumentation"


def test_instrumentation_readiness_checks_schema_and_component(db_session):
    snapshot = instrumentation_operational_readiness_snapshot(
        db_session.connection(),
        frontend_component_keys=frozenset({"workspace.instrumentation.v1"}),
    )
    assert snapshot.ready is True
    assert snapshot.migration_revision == "e05200000002"
    assert snapshot.object_count == 8 and snapshot.relationship_count == 5
    assert not instrumentation_operational_readiness_snapshot(
        db_session.connection(), frontend_component_keys=frozenset(),
    ).ready

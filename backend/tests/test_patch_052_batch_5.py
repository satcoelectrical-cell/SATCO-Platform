"""PATCH-052 Batch-5 combined release and executable conformance evidence."""

from dataclasses import fields, replace
from hashlib import sha256
import inspect
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

from app.discipline_packages.canonical import canonical_json_bytes
from app.discipline_packages.conformance_harness_052 import execute_manifest
from app.discipline_packages.conformance_manifest import (
    COMBINATION_IDS,
    CONFORMANCE_VECTORS_V1,
    EXPECTED_RESULT_DIGESTS_V1,
    PACKAGE_KEYS,
    VECTOR_SUFFIXES,
    ConformanceVectorV1,
    expected_result_digest,
    validate_conformance_manifest,
)
from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1
from app.discipline_packages.descriptors.releases.release_052_eic_v1 import (
    RELEASE_052_EIC_V1,
)
from app.discipline_packages.registry import assemble_registry
from app.dependencies.auth import AuthenticatedOrganizationContext
from app.api.v1.routers.discipline_packages import (
    effective_discipline_packages,
    workspace_package_applicability,
)
from app.models.customer import Customer
from app.models.project import Project
from app.repositories.discipline_package_unit_of_work import (
    DisciplinePackageUnitOfWork,
)
from app.services.discipline_package_configuration_service import (
    DisciplinePackageConfigurationService,
    ExactPackageSelection,
    GuardedRequestIdentity,
    OrganizationConfigurationRequest,
    ProjectConfigurationRequest,
)
from app.services.discipline_package_registry_service import (
    DisciplinePackageRegistryService,
    validate_source_projection_parity,
)
from app.services.discipline_package_service import (
    DisciplinePackageWorkspaceService,
    FrozenGuardedIdentity,
    WorkspaceCreateCommand,
)
from app.exceptions.discipline_package import RegistryAssemblyError
from app.enums.discipline_package import DisciplinePackageStanding


def test_exact_manifest_schema_inventory_and_all_vectors_execute():
    assert tuple(item.name for item in fields(ConformanceVectorV1)) == (
        "schema_version", "vector_id", "subject_kind", "subject_id",
        "release_id", "package_selection", "descriptor_digest_selector",
        "scenario_purpose", "fixture_id", "setup_preconditions",
        "authoritative_inputs", "operation_id", "executor_reference",
        "expected_result", "expected_provenance",
        "authorization_expectation", "tenant_expectation",
        "historical_expectation", "failure_expectation",
    )
    assert len(CONFORMANCE_VECTORS_V1) == 46
    assert tuple(item.vector_id for item in CONFORMANCE_VECTORS_V1[:39]) == tuple(
        f"patch_052.{package_key}.v1.{suffix}"
        for package_key in PACKAGE_KEYS
        for suffix in VECTOR_SUFFIXES
    )
    assert tuple(item.vector_id for item in CONFORMANCE_VECTORS_V1[39:]) == tuple(
        f"patch_052.eic_v1.combination.{combination_id}"
        for combination_id in COMBINATION_IDS
    )
    result = execute_manifest()
    assert (
        result.vector_count,
        result.package_vector_count,
        result.combination_vector_count,
        len(result.executions),
    ) == (46, 39, 7, 46)
    assert all(dict(item.actual_result)["status"] == "PASS" for item in result.executions)


def test_seven_combined_vectors_are_actually_evaluated_with_exact_units():
    result = execute_manifest()
    combinations = [
        item for item in result.executions
        if item.subject_kind == "release_combination"
    ]
    assert [item.vector_id.rsplit(".", 1)[-1] for item in combinations] == list(
        COMBINATION_IDS
    )
    assert [dict(item.actual_result)["aggregate_units"] for item in combinations] == [
        62, 60, 68, 122, 130, 128, 190,
    ]
    for item in combinations:
        actual = dict(item.actual_result)
        provenance = dict(item.provenance)
        assert actual["compatible"] is True
        assert actual["catalog_collisions"] == 0
        assert actual["cross_package_rule_invocations"] == 0
        assert actual["dependency_traversal_depth"] == 0
        assert len(provenance["registry_digest"]) == 64
        assert len(provenance["profile_digest"]) == 64
        assert len(provenance["combination_digest"]) == 64
        assert len(provenance["selected_descriptor_set_digest"]) == 64


def test_expected_result_digest_is_canonical_deterministic_and_descriptor_bound():
    declared = dict(EXPECTED_RESULT_DIGESTS_V1)
    assert len(declared) == 46
    for vector in CONFORMANCE_VECTORS_V1:
        expected = sha256(canonical_json_bytes(vector.expected_result)).hexdigest()
        assert expected_result_digest(vector) == expected == declared[vector.vector_id]
        assert expected_result_digest(vector) == expected_result_digest(vector)
    for descriptor in DESCRIPTORS_V1:
        for declaration in descriptor.contributions.conformance_evidence:
            vector = next(
                item for item in CONFORMANCE_VECTORS_V1
                if item.vector_id == declaration.vector_id
            )
            assert declaration.expected_result_digest == expected_result_digest(vector)
            assert declaration.expected_result_digest != vector.digest()


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda rows: rows[:-1], "exactly 46"),
        (lambda rows: (*rows[:-1], rows[0]), "46 unique"),
        (
            lambda rows: (*rows[:-1], replace(
                rows[-1], vector_id="patch_052.unknown.v1.vector",
            )),
            "unknown or missing",
        ),
        (
            lambda rows: (*rows[:-1], replace(
                rows[-1], subject_id="patch_052.release.combination.wrong",
            )),
            "descriptor mismatch",
        ),
        (
            lambda rows: (*rows[:-1], replace(
                rows[-1], release_id="patch-052.wrong",
            )),
            "Registry release mismatch",
        ),
        (
            lambda rows: (replace(
                rows[0], package_selection=(("electrical", "9.9.9"),),
            ), *rows[1:]),
            "package/version mismatch",
        ),
        (
            lambda rows: (*rows[:-1], replace(
                rows[-1],
                package_selection=(("electrical", "1.0.0"),),
            )),
            "unsupported package combination",
        ),
        (
            lambda rows: (replace(
                rows[0], expected_result=(("status", "FAIL"),),
            ), *rows[1:]),
            "malformed conformance vector",
        ),
    ),
)
def test_manifest_fails_closed_on_inventory_and_identity_drift(mutation, message):
    with pytest.raises(ValueError, match=message):
        validate_conformance_manifest(mutation(CONFORMANCE_VECTORS_V1))


def test_manifest_rejects_malformed_shape_and_expected_result_digest_drift():
    malformed = tuple([object(), *CONFORMANCE_VECTORS_V1[1:]])
    with pytest.raises(ValueError, match="malformed conformance vector"):
        validate_conformance_manifest(malformed)  # type: ignore[arg-type]
    vector = CONFORMANCE_VECTORS_V1[0]
    changed = replace(vector, expected_result=(*vector.expected_result, ("extra", True)))
    assert expected_result_digest(changed) != expected_result_digest(vector)
    with pytest.raises(ValueError, match="malformed conformance vector"):
        execute_manifest((changed, *CONFORMANCE_VECTORS_V1[1:]))


def test_registry_rejects_descriptor_expected_result_digest_mismatch():
    original = RELEASE_052_EIC_V1.descriptors[0]
    descriptor = original.descriptor
    declarations = descriptor.contributions.conformance_evidence
    bad_declaration = declarations[0].model_copy(update={
        "expected_result_digest": "0" * 64,
    })
    bad_contributions = descriptor.contributions.model_copy(update={
        "conformance_evidence": (bad_declaration, *declarations[1:]),
    })
    bad_descriptor = descriptor.model_copy(update={
        "contributions": bad_contributions,
    })
    bad_registration = original.model_copy(update={"descriptor": bad_descriptor})
    bad_release = RELEASE_052_EIC_V1.model_copy(update={
        "descriptors": (bad_registration, *RELEASE_052_EIC_V1.descriptors[1:]),
    })
    with pytest.raises(RegistryAssemblyError):
        assemble_registry(bad_release)


def test_harness_remains_precompiled_and_contains_no_dynamic_execution_path():
    modules = (
        "app.discipline_packages.conformance_manifest",
        "app.discipline_packages.conformance_harness_052",
        "app.discipline_packages.descriptors.eic_v1",
        "app.discipline_packages.operational",
    )
    for module_name in modules:
        source = inspect.getsource(__import__(module_name, fromlist=["*"]))
        assert "eval(" not in source
        assert "exec(" not in source
        assert "importlib" not in source
        assert "subprocess" not in source
        assert "requests." not in source


_SEVEN_SELECTIONS = (
    ("electrical",),
    ("instrumentation",),
    ("control_automation",),
    ("electrical", "instrumentation"),
    ("control_automation", "electrical"),
    ("control_automation", "instrumentation"),
    ("control_automation", "electrical", "instrumentation"),
)
_RAW_DISCIPLINES = {
    "electrical": "electrical",
    "instrumentation": "instrumentation",
    "control_automation": "control",
}
_COMPONENTS = {
    "electrical": "workspace.electrical.v1",
    "instrumentation": "workspace.instrumentation.v1",
    "control_automation": "workspace.control_automation.v1",
}
_ORG_ID = UUID("02810000-0000-4000-8000-000000000001")


@pytest.mark.parametrize("package_keys", _SEVEN_SELECTIONS)
def test_each_combination_projects_binds_and_resolves_server_effective_state(
    db_session, admin_user, package_keys,
):
    factory = sessionmaker(
        bind=db_session.connection(),
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    registry = assemble_registry(RELEASE_052_EIC_V1)
    with DisciplinePackageUnitOfWork(factory) as uow:
        service = DisciplinePackageRegistryService()
        service.install(registry, uow)
        service.activate(str(registry.digest), uow)
        uow.commit()
    validate_source_projection_parity(db_session, registry)

    selections = tuple(
        ExactPackageSelection(
            package_key=key,
            package_version="1.0.0",
            descriptor_digest=str(registry.descriptor_digests[(key, "1.0.0")]),
        )
        for key in package_keys
    )
    identity = GuardedRequestIdentity(
        actor_id=admin_user.id,
        organization_id=_ORG_ID,
        auth_version=admin_user.auth_version,
        correlation_id=uuid4(),
    )
    configuration = DisciplinePackageConfigurationService(factory)
    assert configuration.replace_organization_configuration(
        identity,
        OrganizationConfigurationRequest(
            expected_configuration_version=0,
            selections=selections,
            rationale="PATCH-052 Batch-5 exact combination proof",
        ),
    ) == 1
    customer = Customer(
        organization_id=_ORG_ID,
        name=f"PATCH-052 Batch-5 {uuid4().hex[:8]}",
    )
    db_session.add(customer)
    db_session.flush()
    project = Project(
        organization_id=_ORG_ID,
        project_code=f"SAT-PRJ-2096-{customer.id + 12000:04d}",
        name="PATCH-052 Batch-5 combination",
        customer_id=customer.id,
        owner_id=admin_user.id,
    )
    db_session.add(project)
    db_session.commit()
    profile_digest = str(
        registry.profile_digests[("commercial_v1.eic", "1.0.0")]
    )
    assert configuration.replace_project_configuration(
        identity,
        project.id,
        ProjectConfigurationRequest(
            expected_configuration_version=0,
            profile_id="commercial_v1.eic",
            profile_digest=profile_digest,
            selections=selections,
            rationale="PATCH-052 Batch-5 exact combination proof",
        ),
    ) == 1

    workspace_service = DisciplinePackageWorkspaceService(factory)
    workspace_ids = {}
    for package_key in package_keys:
        workspace_ids[package_key] = workspace_service.create(
            FrozenGuardedIdentity(
                admin_user.id,
                _ORG_ID,
                admin_user.auth_version,
                uuid4(),
            ),
            WorkspaceCreateCommand(
                project_id=project.id,
                discipline=_RAW_DISCIPLINES[package_key],
                description="PATCH-052 Batch-5 exact Workspace",
                owner_id=admin_user.id,
                primary_assignee_id=None,
                collaborator_ids=(),
            ),
        )

    context = AuthenticatedOrganizationContext(admin_user, _ORG_ID)
    effective = effective_discipline_packages(project.id, context, db_session)
    by_key = {
        item["package_key"]: item
        for item in effective["items"]
        if item["package_key"] is not None
    }
    assert set(by_key) == set(package_keys)
    for package_key, workspace_id in workspace_ids.items():
        assert by_key[package_key]["availability"] == "OPERATIONAL_AVAILABLE"
        assert by_key[package_key]["project_configuration_revision"] == 1
        applicability = workspace_package_applicability(
            workspace_id, context, db_session,
        )
        assert applicability["package_key"] == package_key
        assert applicability["project_configuration_revision"] == 1
        assert applicability["operational_state"] == "OPERATIONAL_AVAILABLE"
        assert applicability["component_key"] == _COMPONENTS[package_key]
        assert applicability["allowed_actions"] == [
            "create_object", "create_relationship", "evaluate",
        ]

    foreign_context = AuthenticatedOrganizationContext(
        admin_user,
        UUID("02810000-0000-4000-8000-000000000002"),
    )
    with pytest.raises(HTTPException) as protected:
        effective_discipline_packages(project.id, foreign_context, db_session)
    assert protected.value.status_code == 404

    historical_release = RELEASE_052_EIC_V1.model_copy(update={
        "release_id": "patch-052.eic-v1-historical-fixture",
        "descriptors": tuple(
            registration.model_copy(update={
                "standing": DisciplinePackageStanding.HISTORICAL_READ_ONLY,
            })
            for registration in RELEASE_052_EIC_V1.descriptors
        ),
        "expected_registry_digest": None,
    })
    historical_registry = assemble_registry(historical_release)
    with DisciplinePackageUnitOfWork(factory) as uow:
        service = DisciplinePackageRegistryService()
        service.install(historical_registry, uow)
        service.activate(str(historical_registry.digest), uow)
        uow.commit()
    for workspace_id in workspace_ids.values():
        historical = workspace_package_applicability(
            workspace_id, context, db_session,
        )
        assert historical["operational_state"] == "HISTORICAL_READ_ONLY"
        assert historical["allowed_actions"] == []

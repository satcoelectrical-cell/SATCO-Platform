"""Batch-1 static foundation tests; no database, migration, or owner mutation."""

import inspect

import pytest

from app.adapters.discipline_package_operations import StaticDisciplinePackageCatalogAdapter
from app.adapters.discipline_package_registry import static_adapter_table
from app.discipline_packages.conformance_harness_052 import verify_manifest
from app.discipline_packages.conformance_manifest import CONFORMANCE_VECTORS_V1, validate_conformance_manifest
from app.discipline_packages.descriptors.releases import RELEASES
from app.discipline_packages.descriptors.releases.release_052_eic_v1 import RELEASE_052_EIC_V1
from app.discipline_packages.operational import OperationalContractError, validate_evaluation_limits
from app.discipline_packages.readiness_052 import static_readiness_snapshot
from app.discipline_packages.registry import assemble_registry
from app.services.discipline_package_operation_service import DisciplinePackageOperationService


def test_batch_1_static_release_has_exact_memberships_combinations_and_resource_units():
    registry = assemble_registry(RELEASE_052_EIC_V1)
    assert RELEASES["patch-052.eic-v1"] is RELEASE_052_EIC_V1
    assert tuple(registry.descriptors) == (
        ("control_automation", "1.0.0"), ("electrical", "1.0.0"), ("instrumentation", "1.0.0"),
    )
    profile = registry.profiles[("commercial_v1.eic", "1.0.0")]
    assert len(profile.combinations) == 7
    assert profile.aggregate_resource_ceiling == 190
    assert {item.package_key: item.contributions.resource_declaration.aggregate_units() for item in registry.descriptors.values()} == {
        "electrical": 62, "instrumentation": 60, "control_automation": 68,
    }
    assert {item.adapter_id for item in static_adapter_table()} == {
        "discipline.electrical.v1", "discipline.instrumentation.v1", "discipline.control_automation.v1",
    }


def test_manifest_is_closed_deterministic_and_has_exact_inventory():
    validate_conformance_manifest()
    result = verify_manifest(CONFORMANCE_VECTORS_V1)
    assert result.vector_count == 46
    assert len(result.digests) == 46
    with pytest.raises(ValueError, match="46 unique"):
        validate_conformance_manifest(CONFORMANCE_VECTORS_V1[:-1])
    changed = (*CONFORMANCE_VECTORS_V1[:-1], CONFORMANCE_VECTORS_V1[0])
    with pytest.raises(ValueError, match="46 unique"):
        validate_conformance_manifest(changed)


def test_static_catalog_is_authorization_first_and_never_imports_customer_code():
    service = DisciplinePackageOperationService(StaticDisciplinePackageCatalogAdapter())
    assert service.catalog_entry(authorized=False, package_key="electrical", package_version="1.0.0") is None
    entry = service.catalog_entry(authorized=True, package_key="electrical", package_version="1.0.0")
    assert entry is not None and entry.component_key == "workspace.electrical.v1"
    assert service.catalog_entry(authorized=True, package_key="__import__", package_version="1.0.0") is None
    for module in (
        "app.discipline_packages.operational", "app.discipline_packages.conformance_manifest",
        "app.discipline_packages.conformance_harness_052", "app.adapters.discipline_package_operations",
    ):
        source = inspect.getsource(__import__(module, fromlist=["*"]))
        assert "eval(" not in source and "exec(" not in source and "importlib" not in source


def test_shared_resource_limits_fail_closed_and_static_readiness_is_non_empty():
    validate_evaluation_limits(object_count=64, relationship_count=128, deliverable_count=32, context_projection_count=322, evidence_projection_count=24, rule_hook_count=5, envelope_bytes=384 * 1024)
    with pytest.raises(OperationalContractError):
        validate_evaluation_limits(object_count=65, relationship_count=0, deliverable_count=0, context_projection_count=0, evidence_projection_count=0, rule_hook_count=0, envelope_bytes=0)
    with pytest.raises(OperationalContractError):
        validate_evaluation_limits(object_count=0, relationship_count=0, deliverable_count=0, context_projection_count=0, evidence_projection_count=0, rule_hook_count=6, envelope_bytes=0)
    snapshot = static_readiness_snapshot()
    assert snapshot.ready is True
    assert (snapshot.release_id, snapshot.descriptor_count, snapshot.vector_count) == ("patch-052.eic-v1", 3, 46)

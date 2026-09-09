"""Read-only, fail-closed static readiness checks for PATCH-052 Batch 1."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import inspect, text

from app.discipline_packages.conformance_harness_052 import (
    verify_manifest, verify_package_subset,
)
from app.discipline_packages.conformance_manifest import CONFORMANCE_VECTORS_V1
from app.discipline_packages.descriptors.eic_v1 import PACKAGE_CONTRACTS_V1
from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1
from app.discipline_packages.operational import (
    CONTROL_AUTOMATION_RULE_EXECUTORS, ELECTRICAL_RULE_EXECUTORS,
    INSTRUMENTATION_RULE_EXECUTORS,
)
from app.discipline_packages.descriptors.releases.release_052_eic_v1 import RELEASE_052_EIC_V1
from app.discipline_packages.operational import static_operation_table
from app.discipline_packages.registry import assemble_registry


@dataclass(frozen=True, slots=True)
class Patch052ReadinessSnapshot:
    ready: bool
    reason: str | None
    release_id: str
    descriptor_count: int
    vector_count: int


@dataclass(frozen=True, slots=True)
class ElectricalOperationalReadinessSnapshot:
    ready: bool
    reason: str | None
    migration_revision: str | None
    object_count: int
    relationship_count: int
    input_count: int
    deliverable_count: int
    evidence_count: int
    rule_count: int
    frontend_component_key: str


def static_readiness_snapshot() -> Patch052ReadinessSnapshot:
    """Validate source-only prerequisites without installing or repairing a projection."""

    try:
        registry = assemble_registry(RELEASE_052_EIC_V1)
        operations = static_operation_table(PACKAGE_CONTRACTS_V1)
        result = verify_manifest(CONFORMANCE_VECTORS_V1)
        if len(registry.descriptors) != 3 or len(registry.profiles) != 1 or len(operations) != 3:
            raise ValueError("incomplete static release")
        return Patch052ReadinessSnapshot(True, None, registry.manifest.release_id, len(registry.descriptors), result.vector_count)
    except Exception:
        return Patch052ReadinessSnapshot(False, "static_contract_unavailable", "patch-052.eic-v1", 0, 0)


def electrical_operational_readiness_snapshot(
    connection, *, frontend_component_keys: frozenset[str],
) -> ElectricalOperationalReadinessSnapshot:
    """Read schema/source/component state without installing or repairing it."""

    component_key = "workspace.electrical.v1"
    empty = (False, "operational_dependency_unavailable", None, 0, 0, 0, 0, 0, 0, component_key)
    try:
        descriptor = next(item for item in DESCRIPTORS_V1 if item.package_key == "electrical")
        values = descriptor.contributions
        counts = (
            len(values.object_types), len(values.relationship_types),
            len(values.engineering_inputs), len(values.deliverables),
            len(values.evidence_requirements), len(values.deterministic_rule_hooks),
        )
        if counts != (8, 7, 9, 4, 4, 5):
            return ElectricalOperationalReadinessSnapshot(*empty)
        hooks = {key[2] for key in ELECTRICAL_RULE_EXECUTORS}
        if hooks != {item.hook_id for item in values.deterministic_rule_hooks}:
            return ElectricalOperationalReadinessSnapshot(*empty)
        if component_key not in frontend_component_keys:
            return ElectricalOperationalReadinessSnapshot(
                False, "frontend_component_unavailable", None, *counts, component_key,
            )
        schema = inspect(connection)
        required_tables = {
            "engineering_identifiers", "engineering_identifier_idempotency",
            "engineering_identifier_outbox", "engineering_context_subject_references",
            "engineering_context_package_input_bindings",
            "evidence_package_input_bindings",
        }
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one()
        functions = set(connection.execute(text(
            "select proname from pg_proc where proname in "
            "('satco_patch052_origin_immutable','satco_patch052_identifier_guard',"
            "'satco_patch052_identifier_cardinality','satco_patch052_context_object_coherence',"
            "'satco_patch052_binding_coherent','satco_patch052_binding_immutable',"
            "'technical_report_historical_basis_v2_valid')"
        )).scalars())
        if revision != "e05200000002" or not required_tables <= set(schema.get_table_names()) or len(functions) != 7:
            return ElectricalOperationalReadinessSnapshot(
                False, "schema_projection_unavailable", revision, *counts, component_key,
            )
        return ElectricalOperationalReadinessSnapshot(
            True, None, revision, *counts, component_key,
        )
    except Exception:
        return ElectricalOperationalReadinessSnapshot(*empty)


def instrumentation_operational_readiness_snapshot(
    connection, *, frontend_component_keys: frozenset[str],
) -> ElectricalOperationalReadinessSnapshot:
    """Read-only Instrumentation source/schema/component readiness."""

    component_key = "workspace.instrumentation.v1"
    empty = (False, "operational_dependency_unavailable", None, 0, 0, 0, 0, 0, 0, component_key)
    try:
        descriptor = next(
            item for item in DESCRIPTORS_V1
            if item.package_key == "instrumentation"
        )
        values = descriptor.contributions
        counts = (
            len(values.object_types), len(values.relationship_types),
            len(values.engineering_inputs), len(values.deliverables),
            len(values.evidence_requirements), len(values.deterministic_rule_hooks),
        )
        if counts != (8, 5, 9, 4, 4, 5):
            return ElectricalOperationalReadinessSnapshot(*empty)
        hooks = {key[2] for key in INSTRUMENTATION_RULE_EXECUTORS}
        if hooks != {item.hook_id for item in values.deterministic_rule_hooks}:
            return ElectricalOperationalReadinessSnapshot(*empty)
        if component_key not in frontend_component_keys:
            return ElectricalOperationalReadinessSnapshot(
                False, "frontend_component_unavailable", None, *counts,
                component_key,
            )
        schema = inspect(connection)
        required_tables = {
            "engineering_identifiers", "engineering_identifier_idempotency",
            "engineering_identifier_outbox", "engineering_context_subject_references",
            "engineering_context_package_input_bindings",
            "evidence_package_input_bindings",
        }
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one()
        functions = set(connection.execute(text(
            "select proname from pg_proc where proname in "
            "('satco_patch052_origin_immutable','satco_patch052_identifier_guard',"
            "'satco_patch052_identifier_cardinality','satco_patch052_context_object_coherence',"
            "'satco_patch052_binding_coherent','satco_patch052_binding_immutable',"
            "'technical_report_historical_basis_v2_valid')"
        )).scalars())
        if revision != "e05200000002" or not required_tables <= set(schema.get_table_names()) or len(functions) != 7:
            return ElectricalOperationalReadinessSnapshot(
                False, "schema_projection_unavailable", revision, *counts,
                component_key,
            )
        return ElectricalOperationalReadinessSnapshot(
            True, None, revision, *counts, component_key,
        )
    except Exception:
        return ElectricalOperationalReadinessSnapshot(*empty)


def control_automation_operational_readiness_snapshot(
    connection, *, frontend_component_keys: frozenset[str],
) -> ElectricalOperationalReadinessSnapshot:
    """Read-only Control & Automation source/schema/component readiness."""

    component_key = "workspace.control_automation.v1"
    empty = (False, "operational_dependency_unavailable", None, 0, 0, 0, 0, 0, 0, component_key)
    try:
        registry = assemble_registry(RELEASE_052_EIC_V1)
        identity = ("control_automation", "1.0.0")
        vectors = tuple(
            vector for vector in CONFORMANCE_VECTORS_V1
            if vector.vector_id.startswith("patch_052.control_automation.v1.")
        )
        conformance = verify_package_subset(vectors, package_key="control_automation")
        if (
            registry.manifest.release_id != "patch-052.eic-v1"
            or registry.descriptor(*identity) is None
            or registry.membership_standing(*identity).value != "executable_supported"
            or registry.adapters.get(identity) is None
            or conformance.vector_count != 13
        ):
            return ElectricalOperationalReadinessSnapshot(*empty)
        descriptor = next(
            item for item in DESCRIPTORS_V1
            if item.package_key == "control_automation"
        )
        values = descriptor.contributions
        counts = (
            len(values.object_types), len(values.relationship_types),
            len(values.engineering_inputs), len(values.deliverables),
            len(values.evidence_requirements), len(values.deterministic_rule_hooks),
        )
        if counts != (7, 13, 9, 5, 4, 5):
            return ElectricalOperationalReadinessSnapshot(*empty)
        hooks = {key[2] for key in CONTROL_AUTOMATION_RULE_EXECUTORS}
        if hooks != {item.hook_id for item in values.deterministic_rule_hooks}:
            return ElectricalOperationalReadinessSnapshot(*empty)
        if component_key not in frontend_component_keys:
            return ElectricalOperationalReadinessSnapshot(
                False, "frontend_component_unavailable", None, *counts,
                component_key,
            )
        schema = inspect(connection)
        required_tables = {
            "engineering_identifiers", "engineering_identifier_idempotency",
            "engineering_identifier_outbox", "engineering_context_subject_references",
            "engineering_context_package_input_bindings",
            "evidence_package_input_bindings",
        }
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one()
        functions = set(connection.execute(text(
            "select proname from pg_proc where proname in "
            "('satco_patch052_origin_immutable','satco_patch052_identifier_guard',"
            "'satco_patch052_identifier_cardinality','satco_patch052_context_object_coherence',"
            "'satco_patch052_binding_coherent','satco_patch052_binding_immutable',"
            "'technical_report_historical_basis_v2_valid')"
        )).scalars())
        if revision != "e05200000002" or not required_tables <= set(schema.get_table_names()) or len(functions) != 7:
            return ElectricalOperationalReadinessSnapshot(
                False, "schema_projection_unavailable", revision, *counts,
                component_key,
            )
        return ElectricalOperationalReadinessSnapshot(
            True, None, revision, *counts, component_key,
        )
    except Exception:
        return ElectricalOperationalReadinessSnapshot(*empty)

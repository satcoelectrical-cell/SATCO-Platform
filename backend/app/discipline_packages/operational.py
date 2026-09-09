"""Closed PATCH-052 operational-package primitives.

This module deliberately contains no owner mutation, dynamic dispatch, plug-in
loading, network I/O, or customer supplied executable content.  Later batches
may bind the reviewed operation identifiers to owner services; Batch 1 only
admits and evaluates the static contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from time import monotonic_ns
from types import MappingProxyType
from typing import Mapping


MAX_OPERATION_OBJECTS = 64
MAX_OPERATION_RELATIONSHIPS = 128
MAX_OPERATION_DELIVERABLES = 32
MAX_OPERATION_CONTEXT_PROJECTIONS = 322
MAX_OPERATION_EVIDENCE_PROJECTIONS = 24
MAX_OPERATION_RULE_HOOKS = 5
MAX_OPERATION_ENVELOPE_BYTES = 384 * 1024


@dataclass(frozen=True, slots=True)
class ObjectOperationDeclarationV1:
    declaration_id: str
    object_type: str
    required_primary_identifier_kind: str
    required_context_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationshipOperationDeclarationV1:
    declaration_id: str
    relationship_type: str
    source_types: frozenset[str]
    target_types: frozenset[str]
    direction: str = "directed"
    cardinality: str = "many_to_one"
    cross_workspace: bool = False
    cross_workspace_target_types: frozenset[str] = frozenset()

    def permits(self, source_type: str, target_type: str, *, cross_workspace: bool = False) -> bool:
        return (
            source_type in self.source_types
            and target_type in self.target_types
            and (
                not cross_workspace
                or self.cross_workspace
                and target_type in self.cross_workspace_target_types
            )
        )


class OperationalContractError(ValueError):
    """A closed operational contract is malformed or exceeds its budget."""


@dataclass(frozen=True, slots=True)
class DeterministicRuleResultV1:
    status: str
    finding_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    result_digest: str


def _result(status: str, findings=(), limitations=()) -> DeterministicRuleResultV1:
    ordered_findings = tuple(sorted(set(findings)))
    ordered_limitations = tuple(sorted(set(limitations)))
    payload = {
        "finding_codes": ordered_findings,
        "limitations": ordered_limitations,
        "status": status,
    }
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return DeterministicRuleResultV1(status, ordered_findings, ordered_limitations, digest)


def _integrity_rule(envelope: Mapping[str, object]) -> DeterministicRuleResultV1:
    violations = tuple(str(value) for value in envelope.get("violations", ()))
    return _result("PASS" if not violations else "FINDINGS", violations)


def _completeness_rule(envelope: Mapping[str, object]) -> DeterministicRuleResultV1:
    if envelope.get("partial") or envelope.get("protected") or envelope.get("stale"):
        return _result("INDETERMINATE", limitations=("SOURCE_PROJECTION_INCOMPLETE",))
    missing = tuple(str(value) for value in envelope.get("missing_required_ids", ()))
    return _result("PASS" if not missing else "FINDINGS", (f"MISSING:{value}" for value in missing))


def _relationship_rule(envelope: Mapping[str, object]) -> DeterministicRuleResultV1:
    missing = tuple(str(value) for value in envelope.get("missing_relationship_ids", ()))
    return _result("PASS" if not missing else "FINDINGS", (f"MISSING_RELATIONSHIP:{value}" for value in missing))


def _evidence_rule(envelope: Mapping[str, object]) -> DeterministicRuleResultV1:
    if envelope.get("protected"):
        return _result("INDETERMINATE", limitations=("EVIDENCE_NOT_DISCLOSED",))
    missing = tuple(str(value) for value in envelope.get("missing_evidence_ids", ()))
    return _result("PASS" if not missing else "FINDINGS", (f"MISSING_EVIDENCE:{value}" for value in missing))


def _deliverable_rule(envelope: Mapping[str, object]) -> DeterministicRuleResultV1:
    if envelope.get("partial") or envelope.get("protected"):
        return _result("INDETERMINATE", limitations=("READINESS_SOURCE_INCOMPLETE",))
    missing = tuple(str(value) for value in envelope.get("missing_required_ids", ()))
    return _result("PASS" if not missing else "FINDINGS", (f"NOT_READY:{value}" for value in missing))


ELECTRICAL_RULE_EXECUTORS = MappingProxyType({
    ("electrical", "1.0.0", "electrical.object_relationship_integrity", "1.0.0"): _integrity_rule,
    ("electrical", "1.0.0", "electrical.required_input_completeness", "1.0.0"): _completeness_rule,
    ("electrical", "1.0.0", "electrical.source_feeder_connectivity", "1.0.0"): _relationship_rule,
    ("electrical", "1.0.0", "electrical.evidence_sufficiency", "1.0.0"): _evidence_rule,
    ("electrical", "1.0.0", "electrical.deliverable_readiness", "1.0.0"): _deliverable_rule,
})

INSTRUMENTATION_RULE_EXECUTORS = MappingProxyType({
    ("instrumentation", "1.0.0", "instrumentation.object_relationship_integrity", "1.0.0"): _integrity_rule,
    ("instrumentation", "1.0.0", "instrumentation.required_input_completeness", "1.0.0"): _completeness_rule,
    ("instrumentation", "1.0.0", "instrumentation.loop_signal_connectivity", "1.0.0"): _relationship_rule,
    ("instrumentation", "1.0.0", "instrumentation.evidence_sufficiency", "1.0.0"): _evidence_rule,
    ("instrumentation", "1.0.0", "instrumentation.deliverable_readiness", "1.0.0"): _deliverable_rule,
})

CONTROL_AUTOMATION_RULE_EXECUTORS = MappingProxyType({
    ("control_automation", "1.0.0", "control_automation.object_relationship_integrity", "1.0.0"): _integrity_rule,
    ("control_automation", "1.0.0", "control_automation.required_input_completeness", "1.0.0"): _completeness_rule,
    ("control_automation", "1.0.0", "control_automation.io_logic_connectivity", "1.0.0"): _relationship_rule,
    ("control_automation", "1.0.0", "control_automation.evidence_sufficiency", "1.0.0"): _evidence_rule,
    ("control_automation", "1.0.0", "control_automation.deliverable_readiness", "1.0.0"): _deliverable_rule,
})

_OPERATIONAL_RULE_EXECUTORS = {
    "electrical": ELECTRICAL_RULE_EXECUTORS,
    "instrumentation": INSTRUMENTATION_RULE_EXECUTORS,
    "control_automation": CONTROL_AUTOMATION_RULE_EXECUTORS,
}


def execute_package_rule(
    *, package_key: str, hook_id: str, hook_version: str,
    envelope: Mapping[str, object],
) -> DeterministicRuleResultV1:
    """Execute a reviewed E/I function; no runtime code discovery is permitted."""

    serialized = json.dumps(envelope, sort_keys=True, separators=(",", ":"), default=str).encode()
    validate_evaluation_limits(
        object_count=len(envelope.get("objects", ())),
        relationship_count=len(envelope.get("relationships", ())),
        deliverable_count=len(envelope.get("deliverables", ())),
        context_projection_count=len(envelope.get("contexts", ())),
        evidence_projection_count=len(envelope.get("evidence", ())),
        rule_hook_count=1,
        envelope_bytes=len(serialized),
    )
    executors = _OPERATIONAL_RULE_EXECUTORS.get(package_key)
    executor = None if executors is None else executors.get(
        (package_key, "1.0.0", hook_id, hook_version)
    )
    if executor is None:
        return _result("UNAVAILABLE", limitations=("UNKNOWN_RULE",))
    suffix = hook_id.removeprefix(f"{package_key}.")
    budgets = {
        "object_relationship_integrity": (50, 16, 256 * 1024),
        "required_input_completeness": (100, 32, 384 * 1024),
        "source_feeder_connectivity": (100, 32, 256 * 1024),
        "loop_signal_connectivity": (100, 32, 256 * 1024),
        "io_logic_connectivity": (100, 32, 256 * 1024),
        "evidence_sufficiency": (100, 32, 128 * 1024),
        "deliverable_readiness": (100, 32, 384 * 1024),
    }
    timeout_ms, max_findings, input_bytes = budgets[suffix]
    if len(serialized) > input_bytes:
        raise OperationalContractError("rule input resource limit exceeded")
    started = monotonic_ns()
    result = executor(envelope)
    elapsed_ms = (monotonic_ns() - started) / 1_000_000
    output = json.dumps(
        {"status": result.status, "finding_codes": result.finding_codes,
         "limitations": result.limitations, "result_digest": result.result_digest},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    if elapsed_ms > timeout_ms or len(result.finding_codes) > max_findings or len(output) > 64 * 1024:
        return _result("UNAVAILABLE", limitations=("RULE_RESOURCE_LIMIT_EXCEEDED",))
    return result


def execute_electrical_rule(*, hook_id: str, hook_version: str, envelope: Mapping[str, object]) -> DeterministicRuleResultV1:
    """Execute one reviewed function from the closed table; unknown is unavailable."""
    return execute_package_rule(
        package_key="electrical", hook_id=hook_id,
        hook_version=hook_version, envelope=envelope,
    )


def execute_instrumentation_rule(
    *, hook_id: str, hook_version: str, envelope: Mapping[str, object],
) -> DeterministicRuleResultV1:
    return execute_package_rule(
        package_key="instrumentation", hook_id=hook_id,
        hook_version=hook_version, envelope=envelope,
    )


def execute_control_automation_rule(
    *, hook_id: str, hook_version: str, envelope: Mapping[str, object],
) -> DeterministicRuleResultV1:
    return execute_package_rule(
        package_key="control_automation", hook_id=hook_id,
        hook_version=hook_version, envelope=envelope,
    )


@dataclass(frozen=True, slots=True)
class RuleSpecV1:
    rule_id: str
    hook_id: str
    input_schema_id: str
    output_schema_id: str
    timeout_ms: int
    max_findings: int


@dataclass(frozen=True, slots=True)
class OperationalPackageContractV1:
    package_key: str
    package_version: str
    adapter_id: str
    component_key: str
    rule_specs: tuple[RuleSpecV1, ...]

    def __post_init__(self) -> None:
        if len(self.rule_specs) != MAX_OPERATION_RULE_HOOKS:
            raise OperationalContractError("exactly five deterministic rules are required")
        identities = tuple(spec.rule_id for spec in self.rule_specs)
        hooks = tuple(spec.hook_id for spec in self.rule_specs)
        if len(identities) != len(set(identities)) or len(hooks) != len(set(hooks)):
            raise OperationalContractError("rule identities and hooks must be unique")
        if any(spec.timeout_ms not in {50, 100} or spec.max_findings < 0 for spec in self.rule_specs):
            raise OperationalContractError("rule budgets are not accepted")

    @property
    def capability_ids(self) -> frozenset[str]:
        return frozenset(spec.rule_id for spec in self.rule_specs)


def validate_evaluation_limits(
    *,
    object_count: int,
    relationship_count: int,
    deliverable_count: int,
    context_projection_count: int,
    evidence_projection_count: int,
    rule_hook_count: int,
    envelope_bytes: int,
) -> None:
    """Fail closed before any later package evaluator can consume over-budget input."""

    values = (
        object_count,
        relationship_count,
        deliverable_count,
        context_projection_count,
        evidence_projection_count,
        rule_hook_count,
        envelope_bytes,
    )
    if any(type(value) is not int or value < 0 for value in values):
        raise OperationalContractError("evaluation limits require non-negative integers")
    if (
        object_count > MAX_OPERATION_OBJECTS
        or relationship_count > MAX_OPERATION_RELATIONSHIPS
        or deliverable_count > MAX_OPERATION_DELIVERABLES
        or context_projection_count > MAX_OPERATION_CONTEXT_PROJECTIONS
        or evidence_projection_count > MAX_OPERATION_EVIDENCE_PROJECTIONS
        or rule_hook_count > MAX_OPERATION_RULE_HOOKS
        or envelope_bytes > MAX_OPERATION_ENVELOPE_BYTES
    ):
        raise OperationalContractError("evaluation resource limit exceeded")


def static_operation_table(
    contracts: tuple[OperationalPackageContractV1, ...],
) -> Mapping[tuple[str, str], OperationalPackageContractV1]:
    """Freeze a reviewed literal package table; caller input cannot select code."""

    table = {(contract.package_key, contract.package_version): contract for contract in contracts}
    if len(table) != len(contracts):
        raise OperationalContractError("duplicate package contract")
    return MappingProxyType(table)

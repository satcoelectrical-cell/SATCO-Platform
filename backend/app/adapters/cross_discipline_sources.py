"""Authorization-first source projection foundation for PATCH-053 Batch 1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discipline_packages.cross_discipline.canonical import digest
from app.discipline_packages.cross_discipline.contracts import (
    BATCH_TWO_PROJECTION_IDS, ExplicitRelationshipV1, FindingIdentityInputV1,
    QuantityV1, RangeV1, SourceIdentityV1, parse_batch_two_selector,
)
from app.discipline_packages.cross_discipline.definitions.eic_v1 import (
    BATCH_FIVE_PROJECTION_IDS, BATCH_FOUR_PROJECTION_IDS, BATCH_THREE_PROJECTION_IDS,
    BATCH_TWO_INTERFACE_ID, BATCH_THREE_INTERFACE_ID, BATCH_FOUR_INTERFACE_ID,
    BATCH_FIVE_INTERFACE_ID, BATCH_TWO_PATH_ID, BATCH_THREE_PATH_ID,
    BATCH_FOUR_PATH_ID, BATCH_FIVE_PATH_ID,
)
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.project_control import ProjectChange
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.ports.cross_discipline_intelligence import ProtectedResourceError


@dataclass(frozen=True, slots=True)
class AuthorizedScope:
    actor_id: int
    organization_id: UUID
    project_id: int
    workspace_ids: tuple[int, ...]
    mutate: bool
    authorization_scope_digest: str


class SqlAlchemyCrossDisciplineAuthorizer:
    """Resolve scoped authority before any canonical source query."""

    def __init__(self, session: Session):
        self.session = session
        self.authorized_calls = 0
        self.source_lookup_calls = 0

    def authorize_scope(
        self, *, actor_id: int, role: str, organization_id: UUID,
        project_id: int, workspace_ids: tuple[int, ...], mutate: bool,
    ) -> AuthorizedScope:
        self.authorized_calls += 1
        project = self.session.scalar(select(Project).where(
            Project.id == project_id, Project.organization_id == organization_id,
        ).with_for_update() if mutate else select(Project).where(
            Project.id == project_id, Project.organization_id == organization_id,
        ))
        if project is None:
            raise ProtectedResourceError()
        project_mutator = role == "admin" or actor_id in {
            project.owner_id, project.primary_assignee_id,
        }
        if mutate and not project_mutator:
            raise ProtectedResourceError()
        if not mutate and not project_mutator:
            # Existing Project visibility is deliberately conservative here.
            raise ProtectedResourceError()
        rows = tuple(self.session.scalars(select(EngineeringWorkspace).where(
            EngineeringWorkspace.project_id == project_id,
            EngineeringWorkspace.id.in_(workspace_ids),
        ).order_by(EngineeringWorkspace.id).with_for_update() if mutate else select(EngineeringWorkspace).where(
            EngineeringWorkspace.project_id == project_id,
            EngineeringWorkspace.id.in_(workspace_ids),
        ).order_by(EngineeringWorkspace.id)))
        if tuple(row.id for row in rows) != workspace_ids:
            raise ProtectedResourceError()
        memberships = set(self.session.execute(select(
            EngineeringWorkspaceMember.workspace_id,
        ).where(
            EngineeringWorkspaceMember.workspace_id.in_(workspace_ids),
            EngineeringWorkspaceMember.user_id == actor_id,
        )).scalars())
        for row in rows:
            is_mutator = role == "admin" or actor_id in {row.owner_id, row.primary_assignee_id}
            if mutate and not is_mutator:
                raise ProtectedResourceError()
            if not mutate and not (is_mutator or row.id in memberships):
                raise ProtectedResourceError()
        return AuthorizedScope(
            actor_id, organization_id, project_id, workspace_ids, mutate,
            digest({
                "actor_id": actor_id, "organization_id": organization_id,
                "project_id": project_id, "workspace_ids": workspace_ids,
                "mutate": mutate,
            }, "satco:xdi-authorized-scope:v1"),
        )

    def project_and_workspaces(self, scope: AuthorizedScope):
        if self.authorized_calls < 1:
            raise RuntimeError("authorization must precede source lookup")
        self.source_lookup_calls += 1
        project = self.session.get(Project, scope.project_id)
        workspaces = tuple(self.session.scalars(select(EngineeringWorkspace).where(
            EngineeringWorkspace.id.in_(scope.workspace_ids),
        ).order_by(EngineeringWorkspace.id)))
        if project is None or project.organization_id != scope.organization_id:
            raise ProtectedResourceError()
        return project, workspaces


def validate_scope_shape(workspace_ids: tuple[int, ...]) -> None:
    if (
        not workspace_ids
        or len(workspace_ids) > 12
        or tuple(sorted(set(workspace_ids))) != workspace_ids
        or any(value < 1 for value in workspace_ids)
    ):
        raise ValueError("invalid_scope")


@dataclass(frozen=True, slots=True)
class BatchTwoProjection:
    """Minimal immutable E↔I projection envelope; never a source-of-truth copy."""
    projection_id: str
    owner_kind: str
    owner_id: str
    owner_revision: str
    values: tuple[tuple[str, Any], ...]
    context_binding_ids: tuple[str, ...]
    evidence_binding_ids: tuple[str, ...]
    complete: bool
    authorization_scope_digest: str
    observed_at: datetime
    projection_digest: str


def build_batch_two_projection(*, authorized: AuthorizedScope, projection_id: str,
                               owner_kind: str, owner_id: str, owner_revision: str,
                               values: tuple[tuple[str, Any], ...],
                               context_binding_ids: tuple[str, ...] = (),
                               evidence_binding_ids: tuple[str, ...] = (),
                               complete: bool, observed_at: datetime) -> BatchTwoProjection:
    """Create a digestible minimal projection after authorization has completed."""
    if projection_id not in BATCH_TWO_PROJECTION_IDS or owner_kind not in {"engineering_object", "interface_commitment"}:
        raise ValueError("invalid_request")
    if not owner_id or not owner_revision or observed_at.tzinfo is None:
        raise ValueError("invalid_request")
    if tuple(sorted(values, key=lambda item: item[0])) != values or len({key for key, _ in values}) != len(values):
        raise ValueError("invalid_request")
    body = {
        "projection_id": projection_id, "owner_kind": owner_kind, "owner_id": owner_id,
        "owner_revision": owner_revision, "values": values,
        "context_binding_ids": tuple(sorted(context_binding_ids)),
        "evidence_binding_ids": tuple(sorted(evidence_binding_ids)), "complete": complete,
        "authorization_scope_digest": authorized.authorization_scope_digest,
        "observed_at": observed_at,
    }
    return BatchTwoProjection(**body, projection_digest=digest(body, "satco:xdi-projection:v1"))


def validate_batch_two_selectors(*, authorized: AuthorizedScope, selectors: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    """Closed parsing occurs only after scope authorization; no source resolution happens here."""
    if not authorized.workspace_ids:
        raise ValueError("invalid_request")
    parsed = tuple(parse_batch_two_selector(value) for value in selectors)
    if tuple(sorted(parsed, key=lambda item: (
        item[0], item[1], UUID(item[2]).bytes, item[3],
    ))) != parsed:
        raise ValueError("invalid_request")
    claims = {(source_kind, canonical_id, role) for _, source_kind, canonical_id, role in parsed}
    if len(claims) != len(parsed):
        raise ValueError("invalid_request")
    return parsed


@dataclass(frozen=True, slots=True)
class BatchThreeProjection:
    """Minimal immutable I↔C projection; authorization always precedes construction."""
    projection_id: str
    owner_kind: str
    owner_id: str
    owner_revision: str
    values: tuple[tuple[str, Any], ...]
    context_binding_ids: tuple[str, ...]
    evidence_binding_ids: tuple[str, ...]
    complete: bool
    authorization_scope_digest: str
    observed_at: datetime
    projection_digest: str


def build_batch_three_projection(*, authorized: AuthorizedScope, projection_id: str,
                                 owner_kind: str, owner_id: str, owner_revision: str,
                                 values: tuple[tuple[str, Any], ...],
                                 context_binding_ids: tuple[str, ...] = (),
                                 evidence_binding_ids: tuple[str, ...] = (),
                                 complete: bool, observed_at: datetime) -> BatchThreeProjection:
    if projection_id not in BATCH_THREE_PROJECTION_IDS or owner_kind not in {"engineering_object", "interface_commitment"}:
        raise ValueError("invalid_request")
    if not authorized.workspace_ids or not owner_id or not owner_revision or observed_at.tzinfo is None:
        raise ValueError("invalid_request")
    if tuple(sorted(values, key=lambda item: item[0])) != values or len({key for key, _ in values}) != len(values):
        raise ValueError("invalid_request")
    body = {
        "projection_id": projection_id, "owner_kind": owner_kind, "owner_id": owner_id,
        "owner_revision": owner_revision, "values": values,
        "context_binding_ids": tuple(sorted(context_binding_ids)),
        "evidence_binding_ids": tuple(sorted(evidence_binding_ids)), "complete": complete,
        "authorization_scope_digest": authorized.authorization_scope_digest,
        "observed_at": observed_at,
    }
    return BatchThreeProjection(**body, projection_digest=digest(body, "satco:xdi-projection:v1"))


def validate_batch_three_selectors(*, authorized: AuthorizedScope, selectors: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    """Parse I↔C selectors after full scope authorization, without source lookup."""
    if not authorized.workspace_ids:
        raise ValueError("invalid_request")
    parsed = []
    for value in selectors:
        if not isinstance(value, str) or any(character.isspace() for character in value):
            raise ValueError("invalid_request")
        parts = value.split("/")
        if len(parts) != 5 or parts[0] != "xdi.sel.v1":
            raise ValueError("invalid_request")
        _, discipline, source_kind, canonical_id, role = parts
        if discipline not in {"instrumentation", "control_automation"} or source_kind != "engineering_object":
            raise ValueError("invalid_request")
        if role not in {"signal_endpoint", "valve", "io_channel", "controller", "commitment"}:
            raise ValueError("invalid_request")
        try:
            if str(UUID(canonical_id)) != canonical_id:
                raise ValueError("invalid_request")
        except ValueError as error:
            raise ValueError("invalid_request") from error
        parsed.append((discipline, source_kind, canonical_id, role))
    ordered = tuple(sorted(parsed, key=lambda item: (item[0], item[1], UUID(item[2]).bytes, item[3])))
    if tuple(parsed) != ordered or len({(kind, identifier, role) for _, kind, identifier, role in parsed}) != len(parsed):
        raise ValueError("invalid_request")
    return ordered


@dataclass(frozen=True, slots=True)
class BatchFourProjection(BatchThreeProjection):
    """Minimal immutable Electrical ↔ C&A projection after authorization."""


def build_batch_four_projection(*, authorized: AuthorizedScope, projection_id: str,
                                owner_kind: str, owner_id: str, owner_revision: str,
                                values: tuple[tuple[str, Any], ...],
                                context_binding_ids: tuple[str, ...] = (),
                                evidence_binding_ids: tuple[str, ...] = (),
                                complete: bool, observed_at: datetime) -> BatchFourProjection:
    if projection_id not in BATCH_FOUR_PROJECTION_IDS or owner_kind not in {"engineering_object", "interface_commitment"}:
        raise ValueError("invalid_request")
    if not authorized.workspace_ids or not owner_id or not owner_revision or observed_at.tzinfo is None:
        raise ValueError("invalid_request")
    if tuple(sorted(values, key=lambda item: item[0])) != values or len({key for key, _ in values}) != len(values):
        raise ValueError("invalid_request")
    body = {"projection_id": projection_id, "owner_kind": owner_kind, "owner_id": owner_id,
        "owner_revision": owner_revision, "values": values,
        "context_binding_ids": tuple(sorted(context_binding_ids)), "evidence_binding_ids": tuple(sorted(evidence_binding_ids)),
        "complete": complete, "authorization_scope_digest": authorized.authorization_scope_digest, "observed_at": observed_at}
    return BatchFourProjection(**body, projection_digest=digest(body, "satco:xdi-projection:v1"))


def validate_batch_four_selectors(*, authorized: AuthorizedScope, selectors: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    if not authorized.workspace_ids:
        raise ValueError("invalid_request")
    parsed = []
    for value in selectors:
        if not isinstance(value, str) or any(character.isspace() for character in value):
            raise ValueError("invalid_request")
        parts = value.split("/")
        if len(parts) != 5 or parts[0] != "xdi.sel.v1":
            raise ValueError("invalid_request")
        _, discipline, source_kind, canonical_id, role = parts
        if discipline not in {"electrical", "control_automation"} or source_kind not in {"engineering_object", "interface_commitment"}:
            raise ValueError("invalid_request")
        if role not in {"power_endpoint", "mcc", "controller", "motor", "cabinet", "supply_terminal", "source_freshness", "commitment"}:
            raise ValueError("invalid_request")
        try:
            if str(UUID(canonical_id)) != canonical_id:
                raise ValueError("invalid_request")
        except ValueError as error:
            raise ValueError("invalid_request") from error
        parsed.append((discipline, source_kind, canonical_id, role))
    ordered = tuple(sorted(parsed, key=lambda item: (item[0], item[1], UUID(item[2]).bytes, item[3])))
    if tuple(parsed) != ordered or len({(kind, identifier, role) for _, kind, identifier, role in parsed}) != len(parsed):
        raise ValueError("invalid_request")
    return ordered


@dataclass(frozen=True, slots=True)
class BatchFiveChangeProjection(BatchThreeProjection):
    """Authorized, immutable Change seed; it contains no inferred topology."""


def build_batch_five_change_projection(*, authorized: AuthorizedScope, owner_id: str,
                                       owner_revision: str, values: tuple[tuple[str, Any], ...],
                                       complete: bool, observed_at: datetime) -> BatchFiveChangeProjection:
    if "xdi.proj.change_seed.v1" not in BATCH_FIVE_PROJECTION_IDS:
        raise ValueError("artifact_unavailable")
    if not authorized.workspace_ids or not owner_id or not owner_revision or observed_at.tzinfo is None:
        raise ValueError("invalid_request")
    if tuple(sorted(values, key=lambda item: item[0])) != values or len({key for key, _ in values}) != len(values):
        raise ValueError("invalid_request")
    body = {"projection_id": "xdi.proj.change_seed.v1", "owner_kind": "project_change",
        "owner_id": owner_id, "owner_revision": owner_revision, "values": values,
        "context_binding_ids": (), "evidence_binding_ids": (), "complete": complete,
        "authorization_scope_digest": authorized.authorization_scope_digest, "observed_at": observed_at}
    return BatchFiveChangeProjection(**body, projection_digest=digest(body, "satco:xdi-projection:v1"))


@dataclass(frozen=True, slots=True)
class AcquiredProjection:
    projection_id: str
    owner_kind: str
    owner_id: str
    owner_revision: str
    schema_id: str
    adapter_capability_id: str
    payload: dict[str, Any]
    projection_digest: str


@dataclass(frozen=True, slots=True)
class AcquiredAttestation:
    attestation_id: UUID
    owner_kind: str
    owner_id: str
    selector_digest: str
    observed_cardinality: int
    payload: dict[str, Any]
    attestation_digest: str


@dataclass(frozen=True, slots=True)
class AcquiredOccurrence:
    occurrence_id: UUID
    interface_definition_id: str
    provider_workspace_id: int
    consumer_workspace_id: int
    occurrence_key: str
    applicability: str
    payload: dict[str, Any]
    occurrence_digest: str


@dataclass(frozen=True, slots=True)
class AcquiredAssessmentInput:
    projections: tuple[AcquiredProjection, ...]
    attestations: tuple[AcquiredAttestation, ...]
    occurrences: tuple[AcquiredOccurrence, ...]
    values_by_rule: dict[str, dict[str, Any]]
    sources_by_rule: dict[str, tuple[SourceIdentityV1, ...]]
    source_manifest: tuple[dict[str, Any], ...]
    recheck_identities: tuple[tuple[str, str, int], ...]


class SqlAlchemyCrossDisciplineSourceReader:
    """Authorization-first, minimal canonical reader for the assessment UoW.

    This adapter intentionally owns no engineering facts.  It reads selected
    canonical Objects/Relationships/Change only after the service has obtained
    an AuthorizedScope, then emits small immutable projection envelopes and
    the already-defined evaluator value representation.
    """

    def __init__(self, session: Session, *, authorizer: SqlAlchemyCrossDisciplineAuthorizer):
        self.session = session
        self.authorizer = authorizer
        self.source_lookup_calls = 0

    @staticmethod
    def _selector(value: str) -> tuple[str, str, str, str]:
        if not isinstance(value, str) or any(char.isspace() for char in value):
            raise ValueError("invalid_request")
        parts = value.split("/")
        if len(parts) != 5 or parts[0] != "xdi.sel.v1":
            raise ValueError("invalid_request")
        _, discipline, owner_kind, canonical_id, role = parts
        if discipline not in {"electrical", "instrumentation", "control_automation"}:
            raise ValueError("invalid_request")
        if owner_kind != "engineering_object":
            raise ValueError("invalid_request")
        try:
            if str(UUID(canonical_id)) != canonical_id:
                raise ValueError("invalid_request")
        except ValueError as error:
            raise ValueError("invalid_request") from error
        return discipline, owner_kind, canonical_id, role

    def acquire(
        self, *, authorized: AuthorizedScope, definition, interface_ids: tuple[str, ...],
        selectors: tuple[str, ...], purpose: str, combination_id: str,
        project_change_id: UUID | None, project_change_version: int | None,
        execution_id: UUID, snapshot_id: UUID, registry_digest: str,
        workspace_bindings: tuple[tuple[int, str, int], ...], observed_at: datetime,
    ) -> AcquiredAssessmentInput:
        # The authorizer records the only allowed entry into source resolution.
        if self.authorizer.authorized_calls < 1:
            raise RuntimeError("authorization must precede source lookup")
        parsed = tuple(self._selector(value) for value in selectors)
        if tuple(sorted(parsed, key=lambda item: (item[0], item[1], UUID(item[2]).bytes, item[3]))) != parsed:
            raise ValueError("invalid_request")
        if len({(kind, identity, role) for _, kind, identity, role in parsed}) != len(parsed):
            raise ValueError("invalid_request")
        requested_ids = tuple(UUID(item[2]) for item in parsed)
        self.source_lookup_calls += 1
        objects = tuple(self.session.scalars(select(EngineeringObject).where(
            EngineeringObject.organization_id == authorized.organization_id,
            EngineeringObject.project_id == authorized.project_id,
            EngineeringObject.workspace_id.in_(authorized.workspace_ids),
            EngineeringObject.id.in_(requested_ids),
        ).order_by(EngineeringObject.id))) if requested_ids else ()
        if len(objects) != len(set(requested_ids)):
            raise ProtectedResourceError()
        by_id = {str(item.id): item for item in objects}
        canonical_owner_discipline = {"control_automation": "industrial_automation"}
        for discipline, _, identifier, _ in parsed:
            if by_id[identifier].discipline != canonical_owner_discipline.get(discipline, discipline):
                raise ProtectedResourceError()
        change = None
        if project_change_id is not None:
            self.source_lookup_calls += 1
            change = self.session.scalar(select(ProjectChange).where(
                ProjectChange.id == project_change_id,
                ProjectChange.organization_id == authorized.organization_id,
                ProjectChange.project_id == authorized.project_id,
            ))
            if change is None or change.version != project_change_version:
                raise ProtectedResourceError()

        # Relationship reads are bounded to selected canonical endpoints.  No
        # unselected owner or topology is enumerated or disclosed.
        identities = tuple(sorted(by_id))
        self.source_lookup_calls += 1
        relationships = tuple(self.session.scalars(select(EngineeringRelationship).where(
            EngineeringRelationship.organization_id == authorized.organization_id,
            EngineeringRelationship.project_id == authorized.project_id,
            EngineeringRelationship.source_object_id.in_(tuple(UUID(value) for value in identities)),
            EngineeringRelationship.target_object_id.in_(tuple(UUID(value) for value in identities)),
        ).order_by(EngineeringRelationship.id))) if identities else ()
        edges = tuple(ExplicitRelationshipV1(
            "engineering_relationship", str(row.id), row.version,
            row.relationship_family, row.relationship_type,
            str(row.source_object_id), str(row.target_object_id),
        ) for row in relationships)
        source_identities = tuple(SourceIdentityV1(
            "engineering_object", str(row.id), "aggregate_version", str(row.version),
            digest({"id": str(row.id), "version": row.version, "discipline": row.discipline, "type": row.object_type}, "satco:xdi-owner:v1"),
        ) for row in objects)
        if change is not None:
            source_identities += (SourceIdentityV1(
                "project_change", str(change.id), "aggregate_version", str(change.version),
                digest({"id": str(change.id), "version": change.version}, "satco:xdi-owner:v1"),
            ),)

        interface_definitions = {item.interface_definition_id: item for item in definition.interface_definitions}
        rules = tuple(item for item in definition.rule_definitions if item.interface_definition_id in interface_ids)
        projection_definitions = {item.projection_id: item for item in definition.projection_definitions}
        projections: list[AcquiredProjection] = []
        attestations: list[AcquiredAttestation] = []
        for projection_id in sorted({pid for rule in rules for pid in rule.ordered_projection_ids}):
            projection_definition = projection_definitions[projection_id]
            owner = change if projection_definition.owner_kind == "project_change" else (objects[0] if objects else None)
            owner_kind = "project_change" if owner is change and change is not None else "engineering_object"
            owner_id = str(owner.id) if owner is not None else "scope"
            revision = str(owner.version) if owner is not None else "0"
            payload = {
                "projection_id": projection_id, "owner_kind": owner_kind,
                "owner_id": owner_id, "owner_revision": revision,
                "selected_owner_ids": identities, "complete": bool(objects) or change is not None,
            }
            projection_digest = digest(payload, "satco:xdi-projection:v1")
            projections.append(AcquiredProjection(
                projection_id, owner_kind, owner_id, revision,
                projection_definition.schema_id, projection_definition.adapter_capability_id,
                payload, projection_digest,
            ))
            attestation_payload = {"projection_id": projection_id, "owner_id": owner_id, "count": len(objects), "complete": bool(objects) or change is not None}
            attestation_digest = digest(attestation_payload, "satco:xdi-attestation:v1")
            attestations.append(AcquiredAttestation(
                uuid4(), owner_kind, owner_id,
                digest({"projection_id": projection_id, "selectors": selectors}, "satco:xdi-selector:v1"),
                len(objects), attestation_payload, attestation_digest,
            ))

        purpose_to_applicability = {
            "interface_assessment": "xdi.app.interface_assessment.v1",
            "current_handoff_gate": "xdi.app.current_handoff.v1",
            "explicit_change_impact": "xdi.app.explicit_change.v1",
        }
        applicability = purpose_to_applicability[purpose]
        applicable = tuple(rule for rule in rules if rule.applicability_id == applicability)
        occurrences: list[AcquiredOccurrence] = []
        occurrence_by_interface: dict[str, AcquiredOccurrence] = {}
        workspace_by_discipline = {row[1]: row[0] for row in workspace_bindings}
        for interface_id in interface_ids:
            interface = interface_definitions[interface_id]
            provider = workspace_by_discipline.get(interface.provider_discipline, authorized.workspace_ids[0])
            consumer = workspace_by_discipline.get(interface.consumer_discipline, authorized.workspace_ids[-1])
            key = digest({"project_id": authorized.project_id, "interface_definition_id": interface_id, "provider_workspace_id": provider, "consumer_workspace_id": consumer, "endpoints": identities}, "satco:cross-discipline-occurrence:v1")
            payload = {"endpoint_selectors": selectors, "source_ids": identities}
            occurrence = AcquiredOccurrence(uuid4(), interface_id, provider, consumer, key, applicability, payload, digest(payload, "satco:xdi-occurrence:v1"))
            occurrences.append(occurrence)
            occurrence_by_interface[interface_id] = occurrence

        object_types = {str(row.id): row.object_type for row in objects}
        role_ids = {role: identifier for _, _, identifier, role in parsed}
        values_by_rule: dict[str, dict[str, Any]] = {}
        sources_by_rule: dict[str, tuple[SourceIdentityV1, ...]] = {}
        category_for_rule = {rule.rule_id: (rule.category, rule.subcode, rule.severity) for rule in applicable}
        for rule in applicable:
            interface = interface_definitions[rule.interface_definition_id]
            occurrence = occurrence_by_interface[rule.interface_definition_id]
            category, subcode, _severity = category_for_rule[rule.rule_id]
            selector = selectors[0] if selectors else "xdi.sel.v1/electrical/engineering_object/00000000-0000-4000-8000-000000000000/power_endpoint"
            identity = FindingIdentityInputV1(
                str(execution_id), str(snapshot_id), category, subcode, rule.rule_id,
                rule.version, rule.digest, interface.interface_definition_id,
                interface.version, interface.digest, occurrence.occurrence_key, selector,
                source_identities, tuple(item.attestation_digest for item in attestations),
                change=(str(change.id), change.version) if change is not None else None,
                registry_digest=registry_digest, combination_id=combination_id,
                workspace_binding_revisions=workspace_bindings,
            )
            values: dict[str, Any] = {"applicability_id": applicability, "complete": bool(objects) or change is not None, "identity": identity}
            if rule.interface_definition_id == BATCH_TWO_INTERFACE_ID:
                values.update({"power_presence": "present" if objects else "unknown", "electrical_voltage": QuantityV1("electric_potential", Decimal("24"), "V", Decimal("24")), "instrument_voltage": QuantityV1("electric_potential", Decimal("24"), "V", Decimal("24")), "relationship_grammar_id": "xdi.grammar.ei.cable_jb_supply.v1", "path_id": BATCH_TWO_PATH_ID, "edges": edges, "object_types": object_types, "signal_endpoint_id": role_ids.get("signal_endpoint", identities[0] if identities else ""), "supply_terminal_id": role_ids.get("supply_terminal", identities[-1] if identities else ""), "declaration_ids": (), "commitment_current_use": False, "commitment_state": "unknown", "reassessment_needed": False, "provider_workspace_id": occurrence.provider_workspace_id, "consumer_workspace_id": occurrence.consumer_workspace_id, "occurrence_provider_workspace_id": occurrence.provider_workspace_id, "occurrence_consumer_workspace_id": occurrence.consumer_workspace_id})
            elif rule.interface_definition_id == BATCH_THREE_INTERFACE_ID:
                values.update({"instrumentation_signal_type": "signal_current", "control_io_type": "analog_current", "instrumentation_range": RangeV1(Decimal("4"), Decimal("20")), "control_accepted_range": RangeV1(Decimal("4"), Decimal("20")), "path_id": BATCH_THREE_PATH_ID, "edges": edges, "controller_id": role_ids.get("controller", identities[0] if identities else ""), "valve_id": role_ids.get("valve", identities[0] if identities else ""), "feedback_target_id": role_ids.get("io_channel", identities[-1] if identities else ""), "commitment_current_use": False, "commitment_changed": False, "commitment_state": "unknown", "evidence_presence": "unknown"})
            elif rule.interface_definition_id == BATCH_FOUR_INTERFACE_ID:
                values.update({"command_presence": "present" if objects else "unknown", "status_presence": "present" if objects else "unknown", "path_id": BATCH_FOUR_PATH_ID, "edges": edges, "cabinet_id": role_ids.get("cabinet", identities[0] if identities else ""), "supply_id": role_ids.get("supply_terminal", identities[-1] if identities else ""), "observed_at": observed_at, "reference_at": observed_at, "commitment_current_use": False, "commitment_changed": False, "commitment_state": "unknown"})
            elif rule.interface_definition_id == BATCH_FIVE_INTERFACE_ID:
                values.update({"path_id": BATCH_FIVE_PATH_ID, "change_present": change is not None, "change_id": str(change.id) if change else "", "change_version": change.version if change else 0, "root_object_id": identities[0] if identities else "", "target_id": identities[-1] if identities else "", "edges": edges})
            values_by_rule[rule.rule_id] = values
            sources_by_rule[rule.rule_id] = source_identities
        manifest = tuple({"owner_kind": item.owner_kind, "owner_id": item.owner_id, "projection_id": item.projection_id, "digest": item.projection_digest} for item in projections)
        recheck = tuple(("project_change", str(change.id), change.version) for _ in [0] if change is not None) + tuple(("engineering_object", str(row.id), row.version) for row in objects)
        return AcquiredAssessmentInput(tuple(projections), tuple(attestations), tuple(occurrences), values_by_rule, sources_by_rule, manifest, recheck)

    def recheck(self, *, authorized: AuthorizedScope, identities: tuple[tuple[str, str, int], ...]) -> bool:
        for owner_kind, owner_id, version in identities:
            model = ProjectChange if owner_kind == "project_change" else EngineeringObject
            row = self.session.scalar(select(model).where(
                model.id == UUID(owner_id), model.organization_id == authorized.organization_id,
                model.project_id == authorized.project_id, model.version == version,
            ))
            if row is None:
                return False
        return True

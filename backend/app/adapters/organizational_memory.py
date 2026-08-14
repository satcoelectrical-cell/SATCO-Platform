"""Canonical read adapters for PATCH-034 Organizational Memory.

This module composes application-service reads only.  It owns no canonical
persistence, authorization policy, transaction, or mutation behavior.
"""

from __future__ import annotations

from typing import Protocol

from app.exceptions.engineering_experience_capture import (
    EngineeringExperienceCaptureAuthorizationDenied,
    EngineeringExperienceCaptureProtectedNotFound,
)
from app.exceptions.engineering_object import (
    EngineeringObjectAuthorizationDenied,
    EngineeringObjectProtectedNotFound,
)
from app.exceptions.engineering_relationship import (
    EngineeringRelationshipAuthorizationDenied,
    EngineeringRelationshipProtectedNotFound,
)
from app.exceptions.evidence import EvidenceAuthorizationDenied, EvidenceProtectedNotFound
from app.exceptions.organizational_memory import (
    OrganizationalMemoryIntegrityError,
    OrganizationalMemoryValidationError,
)
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
)
from app.models.engineering_object_command import AuthenticatedActor, AuthorizationContext
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor,
    RelationshipAuthorizationContext,
)
from app.models.evidence_command import EvidenceActor
from app.models.organizational_memory_command import (
    AcceptedReportProjection,
    AcceptedReportProtectedNotFound,
    AcceptedReportReadResult,
    AcceptedReportSource,
    AcceptedReportUnavailable,
    CaptureProvenanceAuthorization,
    EngineeringObjectProvenanceAuthorization,
    EngineeringRelationshipProvenanceAuthorization,
    EvidenceProvenanceAuthorization,
    MemoryActor,
    MemoryProvenanceAuthorizationRequest,
    MemoryProvenanceAuthorizationResult,
    ProvenanceAuthorized,
    ProvenanceProtectedNotFound,
    ProvenanceUnavailable,
    SafeAuthorizedProvenance,
    admission_material_from_snapshot,
)
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    TechnicalReportActor,
    TechnicalReportLifecycle,
)


class _TechnicalReportService(Protocol):
    def get_report(self, actor: TechnicalReportActor, report_id): ...


class _CaptureService(Protocol):
    def read_authorized_detail(self, **kwargs): ...


class _EvidenceService(Protocol):
    def get(self, evidence_id, actor): ...


class _EngineeringObjectService(Protocol):
    def get(self, object_id, actor, context): ...


class _EngineeringRelationshipService(Protocol):
    def get(self, relationship_id, actor, context): ...


_PROTECTED_FAILURES = (
    TechnicalReportAuthorizationDenied,
    EngineeringExperienceCaptureAuthorizationDenied,
    EngineeringExperienceCaptureProtectedNotFound,
    EvidenceAuthorizationDenied,
    EvidenceProtectedNotFound,
    EngineeringObjectAuthorizationDenied,
    EngineeringObjectProtectedNotFound,
    EngineeringRelationshipAuthorizationDenied,
    EngineeringRelationshipProtectedNotFound,
)


class TechnicalReportAcceptedSourceAdapter:
    """Read one exact Human-accepted report through its application service."""

    def __init__(self, technical_reports: _TechnicalReportService) -> None:
        self._technical_reports = technical_reports

    def read_authorized_accepted(
        self, actor: MemoryActor, source: AcceptedReportSource,
    ) -> AcceptedReportReadResult:
        try:
            view = self._technical_reports.get_report(
                TechnicalReportActor(actor.actor_id, actor.organization_id),
                source.report_id,
            )
            snapshot = view.accepted_snapshot
            if (
                view.id != source.report_id
                or view.organization_id != actor.organization_id
                or view.lifecycle is not TechnicalReportLifecycle.ACCEPTED
                or snapshot is None
                or view.workspace_id != snapshot.workspace_id
                or view.project_id != snapshot.project_id
                or view.version != source.accepted_aggregate_version
                or snapshot.report_id != source.report_id
                or snapshot.organization_id != actor.organization_id
                or snapshot.accepted_aggregate_version
                != source.accepted_aggregate_version
                or snapshot.integrity_digest != source.accepted_snapshot_digest
            ):
                return AcceptedReportProtectedNotFound()
            # Constructing both closed artifacts is the V1 eligibility gate.
            # The application receives the exact immutable snapshot and may
            # reconstruct the same artifacts without semantic transformation.
            admission_material_from_snapshot(snapshot)
            return AcceptedReportProjection(
                source=source,
                owner_id=view.owner_id,
                scope=_memory_scope(snapshot),
                snapshot=snapshot,
            )
        except _PROTECTED_FAILURES:
            return AcceptedReportProtectedNotFound()
        except (OrganizationalMemoryValidationError, OrganizationalMemoryIntegrityError):
            # Admission-ineligible is an authorized request error, not source
            # absence or dependency unavailability.  Batch 4 translates this
            # typed failure to its closed invalid_request result.
            raise
        except Exception:
            return AcceptedReportUnavailable()


class CanonicalMemoryProvenanceAuthorizer:
    """Authorize retained provenance through each owning application service."""

    def __init__(
        self,
        *,
        accepted_reports: TechnicalReportAcceptedSourceAdapter,
        captures: _CaptureService,
        evidence: _EvidenceService,
        engineering_objects: _EngineeringObjectService,
        engineering_relationships: _EngineeringRelationshipService,
    ) -> None:
        self._accepted_reports = accepted_reports
        self._captures = captures
        self._evidence = evidence
        self._engineering_objects = engineering_objects
        self._engineering_relationships = engineering_relationships

    def authorize_and_resolve(
        self, request: MemoryProvenanceAuthorizationRequest,
    ) -> MemoryProvenanceAuthorizationResult:
        return self.authorize_logical_operation((request,))

    def authorize_logical_operation(
        self,
        requests: tuple[MemoryProvenanceAuthorizationRequest, ...],
    ) -> MemoryProvenanceAuthorizationResult:
        try:
            request, items = _logical_operation(requests)
        except OrganizationalMemoryValidationError:
            return ProvenanceProtectedNotFound()

        source = self._accepted_reports.read_authorized_accepted(
            request.actor, request.source,
        )
        if isinstance(source, AcceptedReportProtectedNotFound):
            return ProvenanceProtectedNotFound()
        if isinstance(source, AcceptedReportUnavailable):
            return ProvenanceUnavailable()
        if source.scope != request.memory_scope:
            return ProvenanceProtectedNotFound()

        try:
            _, manifest = admission_material_from_snapshot(source.snapshot)
            retained = {
                (entry.entry_id, entry.ordinal): entry
                for entry in manifest.provenance_entries
            }
            historical = {
                (entry.entry_id, entry.ordinal): entry.locator
                for entry in source.snapshot.provenance
            }
            resolved: list[SafeAuthorizedProvenance] = []
            canonical_responses: dict[tuple[type, object, int], object] = {}
            for item in items:
                key = (item.entry_id, item.ordinal)
                digest_entry = retained.get(key)
                basis = historical.get(key)
                if digest_entry is None or not _request_matches_basis(item, basis):
                    return ProvenanceProtectedNotFound()
                canonical_key = _canonical_identity(item)
                response = canonical_responses.get(canonical_key)
                if response is None:
                    response = self._read_canonical(request.actor, item)
                    canonical_responses[canonical_key] = response
                if not _response_matches(item, response):
                    return ProvenanceProtectedNotFound()
                resolved.append(SafeAuthorizedProvenance(
                    entry_id=digest_entry.entry_id,
                    ordinal=digest_entry.ordinal,
                    source_class=digest_entry.source_class,
                    source_type=digest_entry.source_type,
                    owning_capability=digest_entry.owning_capability,
                    is_material=digest_entry.is_material,
                    reliance_role=digest_entry.reliance_role,
                    locator_digest=digest_entry.locator_digest,
                    source_integrity_algorithm=digest_entry.source_integrity_algorithm,
                    source_integrity_digest=digest_entry.source_integrity_digest,
                ))
            return ProvenanceAuthorized("success", tuple(resolved))
        except _PROTECTED_FAILURES:
            return ProvenanceProtectedNotFound()
        except (OrganizationalMemoryValidationError, OrganizationalMemoryIntegrityError):
            return ProvenanceProtectedNotFound()
        except Exception:
            return ProvenanceUnavailable()

    def _read_canonical(self, actor: MemoryActor, item):
        if type(item) is CaptureProvenanceAuthorization:
            return self._captures.read_authorized_detail(
                actor=EngineeringExperienceCaptureActor(
                    actor.actor_id, actor.organization_id,
                ),
                project_id=item.project_id,
                workspace_id=item.workspace_id,
                engineering_object_id=item.engineering_object_id,
                capture_id=item.capture_id,
            )
        if type(item) is EvidenceProvenanceAuthorization:
            return self._evidence.get(
                item.evidence_id, EvidenceActor(actor.actor_id, actor.organization_id),
            )
        if type(item) is EngineeringObjectProvenanceAuthorization:
            return self._engineering_objects.get(
                item.engineering_object_id,
                AuthenticatedActor(actor.actor_id, actor.organization_id),
                AuthorizationContext(
                    "ReadEngineeringObject", {"object_id": item.engineering_object_id},
                ),
            )
        if type(item) is EngineeringRelationshipProvenanceAuthorization:
            return self._engineering_relationships.get(
                item.engineering_relationship_id,
                AuthenticatedRelationshipActor(actor.actor_id, actor.organization_id),
                RelationshipAuthorizationContext(
                    "ReadEngineeringRelationship",
                    {"relationship_id": item.engineering_relationship_id},
                ),
            )
        raise OrganizationalMemoryValidationError("unsupported provenance identity")


def _memory_scope(snapshot):
    from app.models.organizational_memory_command import MemoryScope

    return MemoryScope(
        snapshot.organization_id, snapshot.workspace_id, snapshot.project_id,
    )


def _request_matches_basis(item, basis) -> bool:
    common = (
        getattr(basis, "organization_id", None) == item.organization_id
        and getattr(basis, "source_version", None) == item.source_version
    )
    if type(item) is CaptureProvenanceAuthorization:
        return common and isinstance(basis, CaptureHistoricalBasisV1) and (
            basis.capture_id, basis.project_id, basis.workspace_id,
            basis.engineering_object_id,
        ) == (
            item.capture_id, item.project_id, item.workspace_id,
            item.engineering_object_id,
        )
    if type(item) is EvidenceProvenanceAuthorization:
        return common and isinstance(basis, EvidenceHistoricalBasisV1) and (
            basis.evidence_id, basis.project_id, basis.workspace_id,
        ) == (item.evidence_id, item.project_id, item.workspace_id)
    if type(item) is EngineeringObjectProvenanceAuthorization:
        return common and isinstance(basis, EngineeringObjectHistoricalBasisV1) and (
            basis.engineering_object_id, basis.project_id, basis.workspace_id,
        ) == (item.engineering_object_id, item.project_id, item.workspace_id)
    if type(item) is EngineeringRelationshipProvenanceAuthorization:
        return common and isinstance(basis, EngineeringRelationshipHistoricalBasisV1) and (
            basis.engineering_relationship_id, basis.project_id, basis.workspace_id,
            basis.source_object_id, basis.target_object_id,
        ) == (
            item.engineering_relationship_id, item.project_id, item.workspace_id,
            item.source_object_id, item.target_object_id,
        )
    return False


def _response_matches(item, response) -> bool:
    if type(item) is CaptureProvenanceAuthorization:
        # The canonical Capture detail deliberately omits Organization after
        # authorizing the trusted actor/context.  Match every scalar it does
        # disclose; the service call above supplies the Organization actor.
        return (
            getattr(response, "id", None) == item.capture_id
            and getattr(response, "project_id", None) == item.project_id
            and getattr(response, "workspace_id", None) == item.workspace_id
            and getattr(response, "engineering_object_id", None)
            == item.engineering_object_id
        )
    common = (
        getattr(response, "id", None) == _identity(item)
        and getattr(response, "organization_id", None) == item.organization_id
        and getattr(response, "project_id", None) == item.project_id
        and getattr(response, "workspace_id", None) == item.workspace_id
    )
    if type(item) is EngineeringRelationshipProvenanceAuthorization:
        return common and (
            getattr(response, "source_object_id", None),
            getattr(response, "target_object_id", None),
        ) == (item.source_object_id, item.target_object_id)
    return common


def _identity(item):
    for name in (
        "capture_id", "evidence_id", "engineering_object_id",
        "engineering_relationship_id",
    ):
        if hasattr(item, name):
            return getattr(item, name)
    return None


def _canonical_identity(item) -> tuple[type, object, int]:
    return type(item), _identity(item), item.source_version


def _logical_operation(
    requests: tuple[MemoryProvenanceAuthorizationRequest, ...],
):
    if not isinstance(requests, tuple) or not 1 <= len(requests) <= 3:
        raise OrganizationalMemoryValidationError(
            "logical provenance operation requires one to three requests"
        )
    if any(type(request) is not MemoryProvenanceAuthorizationRequest for request in requests):
        raise OrganizationalMemoryValidationError("logical provenance request is invalid")
    first = requests[0]
    common = (first.actor, first.operation, first.memory_scope, first.source)
    if any(
        (request.actor, request.operation, request.memory_scope, request.source) != common
        for request in requests[1:]
    ):
        raise OrganizationalMemoryValidationError(
            "logical provenance request context is incoherent"
        )

    by_entry: dict[tuple[object, int], object] = {}
    for request in requests:
        for item in request.items:
            entry_key = (item.entry_id, item.ordinal)
            prior = by_entry.get(entry_key)
            if prior is not None and prior != item:
                raise OrganizationalMemoryValidationError(
                    "logical provenance entry is contradictory"
                )
            by_entry[entry_key] = item
    items = tuple(sorted(by_entry.values(), key=lambda item: item.ordinal))
    if len({item.ordinal for item in items}) != len(items):
        raise OrganizationalMemoryValidationError(
            "logical provenance ordinals are contradictory"
        )
    if len({_canonical_identity(item) for item in items}) > 256:
        raise OrganizationalMemoryValidationError(
            "logical provenance identity limit exceeds 256"
        )
    return first, items

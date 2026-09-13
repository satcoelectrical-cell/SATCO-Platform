"""Session-bound Technical Report resolvers and authoritative Unit of Work."""

from __future__ import annotations

import base64
import hmac
from datetime import datetime
from enum import Enum
from typing import Final, Self
from uuid import UUID

from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.enums.technical_report import TechnicalReportSourceType
from app.enums.workspace_status import WorkspaceStatus
from app.enums.engineering_knowledge import (
    EngineeringAuthorityStanding,
    EngineeringLifecycle,
)
from app.enums.engineering_relationship import (
    RELATIONSHIP_TYPES_BY_FAMILY,
    RelationshipFamily,
    RelationshipLifecycle,
    RelationshipType,
)
from app.enums.evidence import EvidenceLifecycle, EvidenceSourceStanding
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
)
from app.exceptions.technical_report import (
    TechnicalReportAcceptedImmutable,
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportIntegrityMismatch,
    TechnicalReportAuthorizationDenied,
    TechnicalReportAcceptanceAuthorityDenied,
    TechnicalReportIdempotencyConflict,
    TechnicalReportVersionConflict,
    TechnicalReportValidationError,
)
from app.models.audit_log import AuditLog
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_object import EngineeringObject
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_relationship import EngineeringRelationship
from app.models.evidence import Evidence
from app.models.cross_discipline_intelligence import CrossDisciplineAssessment, CrossDisciplineSnapshot
from app.models.engineering_workspace import (
    EngineeringWorkspace,
    EngineeringWorkspaceMember,
)
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.models.standards import (
    OrganizationRightsBinding,
    ProjectStandardApplicability,
    StandardAssertionVerificationEvent,
    StandardEdition,
    StandardEditionStandingObservation,
    StandardIdentity,
    StandardKnowledgeAssertion,
    StandardSourceSnapshot,
)
from app.models.technical_report import (
    TechnicalReportProvenanceRecord,
    TechnicalReportRecord,
)
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1,
    CaptureHistoricalBasisV2,
    EngineeringIdentifierHistoricalSnapshotV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV2,
    EngineeringRelationshipHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV2,
    CrossDisciplineAssessmentHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    HistoricalBasis,
    StandardHistoricalBasisV1,
    TechnicalReportCommandResult,
    TechnicalReportDomainEvent,
    TechnicalReportStandardsDomainEvent,
    TechnicalReportDraftRevision,
    TechnicalReportIdempotencyRecord,
    TechnicalReportOutboxRecord,
    historical_basis_digest,
    verify_historical_basis_digest,
    standard_basis_digest,
)
from app.standards.handles import OpaqueAuthorizedHandleInvalid, verify_handle
from app.services.supporting_file_service import (
    SqlAlchemySupportingFileTechnicalReportCollaborator,
)
from app.ports.technical_report import (
    AcceptExactDraftHistoricalAuthority,
    CreateDraftHistoricalAuthority,
    CreateSuccessorHistoricalAuthority,
    ReviseDraftHistoricalAuthority,
    RequestAIProposalHistoricalAuthority,
    TechnicalReportAuditRecord,
    TechnicalReportAuthorizationRequest,
    TechnicalReportFinalRecheckRequest,
    TechnicalReportHistoricalOperation,
    TechnicalReportHistoricalRequest,
    TechnicalReportIdempotencyKey,
    TechnicalReportReferenceRequest,
    TechnicalReportRejectionAuditRecord,
    TechnicalReportRejectionReason,
)
from app.repositories.technical_report_repository import (
    SqlAlchemyTechnicalReportRepository,
)


_SOURCES: Final = {
    TechnicalReportSourceType.UNIVERSAL_CAPTURE.value,
    TechnicalReportSourceType.EVIDENCE.value,
    TechnicalReportSourceType.ENGINEERING_OBJECT.value,
    TechnicalReportSourceType.ENGINEERING_RELATIONSHIP.value,
    TechnicalReportSourceType.CROSS_DISCIPLINE_ASSESSMENT.value,
}


def _json_value(value: object) -> object:
    """Return a JSON-safe value without admitting arbitrary object state."""

    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TechnicalReportValidationError("operational record contains an invalid value")


class SqlAlchemyTechnicalReportAuditRecorder:
    """Stage minimal successful-command Audit in the authoritative Session."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, record: TechnicalReportAuditRecord) -> None:
        details = {
            "outcome": "succeeded",
            "organization_id": str(record.organization_id),
            "command_id": str(record.command_id),
            "correlation_id": str(record.correlation_id),
        }
        if record.event_id is not None:
            details["event_id"] = str(record.event_id)
        if record.standards_basis_digest is not None:
            details["standards_basis_digest"] = record.standards_basis_digest
        self.session.add(
            AuditLog(
                user_id=record.actor_id,
                action=record.operation,
                entity="TECHNICAL_REPORT",
                entity_uuid=record.report_id,
                details=details,
                created_at=record.occurred_at,
            )
        )


class SqlAlchemyTechnicalReportDomainEventRecorder:
    """Stage minimal Domain Events in the capability-owned outbox."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, events: tuple[TechnicalReportDomainEvent, ...]) -> None:
        for event in events:
            payload = {
                "report_id": str(event.report_id),
                "aggregate_version": event.aggregate_version,
                "command_id": str(event.command_id),
                "correlation_id": str(event.correlation_id),
                "occurred_at": event.occurred_at.isoformat(),
                "organization_id": str(event.organization_id),
                "workspace_id": event.workspace_id,
                "project_id": event.project_id,
                "purpose": event.purpose.value,
                "lifecycle": event.lifecycle,
                "draft_revision_id": str(event.draft_revision_id),
                "actor_id": event.actor_id,
                "causation_id": str(event.causation_id),
                "predecessor_report_id": (
                    None if event.predecessor_report_id is None
                    else str(event.predecessor_report_id)
                ),
                "source_entry_count": event.source_entry_count,
            }
            standards_basis_digest = getattr(event, "standards_basis_digest", None)
            if standards_basis_digest is not None:
                payload["standards_basis_ids"] = [
                    str(basis_id) for basis_id in event.standards_basis_ids
                ]
                payload["standards_basis_digest"] = standards_basis_digest
            self.session.add(
                TechnicalReportOutboxRecord(
                    event_id=event.event_id,
                    aggregate_id=event.report_id,
                    aggregate_version=event.aggregate_version,
                    event_type=event.event_type,
                    schema_version=1,
                    payload=payload,
                    occurred_at=event.occurred_at,
                )
            )


def _result_payload(result: TechnicalReportCommandResult) -> dict[str, object]:
    def event_payload(event: TechnicalReportDomainEvent) -> dict[str, object]:
        payload = {
            "event_id": str(event.event_id),
            "report_id": str(event.report_id),
            "aggregate_version": event.aggregate_version,
            "event_type": event.event_type,
            "command_id": str(event.command_id),
            "correlation_id": str(event.correlation_id),
            "occurred_at": event.occurred_at.isoformat(),
            "organization_id": str(event.organization_id),
            "workspace_id": event.workspace_id,
            "project_id": event.project_id,
            "purpose": event.purpose.value,
            "lifecycle": event.lifecycle,
            "draft_revision_id": str(event.draft_revision_id),
            "actor_id": event.actor_id,
            "causation_id": str(event.causation_id),
            "predecessor_report_id": (
                None if event.predecessor_report_id is None
                else str(event.predecessor_report_id)
            ),
            "source_entry_count": event.source_entry_count,
        }
        standards_basis_digest = getattr(event, "standards_basis_digest", None)
        if standards_basis_digest is not None:
            payload["standards_basis_ids"] = [
                str(basis_id) for basis_id in event.standards_basis_ids
            ]
            payload["standards_basis_digest"] = standards_basis_digest
        return payload

    return {
        "safe_result_schema_version": 1,
        "report_id": str(result.report_id),
        "previous_version": result.previous_version,
        "version": result.version,
        "draft_revision": {
            "revision_id": str(result.draft_revision.revision_id),
            "revision_number": result.draft_revision.revision_number,
        },
        "command_type": result.command_type,
        "correlation_id": str(result.correlation_id),
        "events": [event_payload(event) for event in result.events],
    }


def _result_from_payload(payload: object) -> TechnicalReportCommandResult:
    if not isinstance(payload, dict):
        raise TechnicalReportValidationError("idempotency result is invalid")
    try:
        if set(payload) != {
            "safe_result_schema_version", "report_id", "previous_version",
            "version", "draft_revision", "command_type", "correlation_id",
            "events",
        }:
            raise TypeError
        if payload.get("safe_result_schema_version") != 1:
            raise TypeError
        revision = payload["draft_revision"]
        events = payload["events"]
        if not isinstance(revision, dict) or not isinstance(events, list):
            raise TypeError
        return TechnicalReportCommandResult(
            report_id=UUID(payload["report_id"]),
            previous_version=payload["previous_version"],
            version=payload["version"],
            draft_revision=TechnicalReportDraftRevision(
                UUID(revision["revision_id"]), revision["revision_number"]
            ),
            command_type=payload["command_type"],
            correlation_id=UUID(payload["correlation_id"]),
            events=tuple(
                (TechnicalReportStandardsDomainEvent if item.get("standards_basis_digest") is not None else TechnicalReportDomainEvent)(
                    event_id=UUID(item["event_id"]),
                    report_id=UUID(item["report_id"]),
                    aggregate_version=item["aggregate_version"],
                    event_type=item["event_type"],
                    command_id=UUID(item["command_id"]),
                    correlation_id=UUID(item["correlation_id"]),
                    occurred_at=datetime.fromisoformat(item["occurred_at"]),
                    organization_id=UUID(item["organization_id"]),
                    workspace_id=item["workspace_id"],
                    project_id=item["project_id"],
                    purpose=item["purpose"],
                    lifecycle=item["lifecycle"],
                    draft_revision_id=UUID(item["draft_revision_id"]),
                    actor_id=item["actor_id"],
                    causation_id=UUID(item["causation_id"]),
                    predecessor_report_id=(
                        None if item["predecessor_report_id"] is None
                        else UUID(item["predecessor_report_id"])
                    ),
                    source_entry_count=item["source_entry_count"],
                    **(
                        {
                            "standards_basis_ids": tuple(
                                UUID(value) for value in item["standards_basis_ids"]
                            ),
                            "standards_basis_digest": item["standards_basis_digest"],
                        }
                        if item.get("standards_basis_digest") is not None else {}
                    ),
                )
                for item in events
            ),
        )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise TechnicalReportValidationError("idempotency result is invalid") from exc


class SqlAlchemyTechnicalReportIdempotencyStore:
    """Stage and recover only the typed, plaintext-free command result."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def find(self, key: TechnicalReportIdempotencyKey, request_fingerprint: str) -> TechnicalReportCommandResult | None:
        row = self.session.query(TechnicalReportIdempotencyRecord).filter_by(
            organization_id=key.organization_id,
            actor_id=key.actor_id,
            command_type=key.command_type,
            idempotency_id=key.idempotency_id,
        ).with_for_update().first()
        if row is None:
            return None
        if row.request_fingerprint != request_fingerprint or row.status != "completed" or row.result is None:
            raise TechnicalReportIdempotencyConflict()
        return _result_from_payload(row.result)

    def reserve(
        self,
        key: TechnicalReportIdempotencyKey,
        request_fingerprint: str,
    ) -> None:
        if (
            not isinstance(request_fingerprint, str)
            or len(request_fingerprint) != 64
            or request_fingerprint != request_fingerprint.lower()
            or any(character not in "0123456789abcdef" for character in request_fingerprint)
        ):
            raise TechnicalReportValidationError("request fingerprint is invalid")
        existing = self.session.query(TechnicalReportIdempotencyRecord).filter_by(
            organization_id=key.organization_id, actor_id=key.actor_id,
            command_type=key.command_type, idempotency_id=key.idempotency_id,
        ).with_for_update().first()
        if existing is not None:
            raise TechnicalReportIdempotencyConflict()
        try:
            with self.session.begin_nested():
                self.session.add(TechnicalReportIdempotencyRecord(
                organization_id=key.organization_id,
                actor_id=key.actor_id,
                command_type=key.command_type,
                idempotency_id=key.idempotency_id,
                request_fingerprint=request_fingerprint,
                status="pending",
                ))
                self.session.flush()
        except IntegrityError as exc:
            raise TechnicalReportIdempotencyConflict() from exc

    def record_result(
        self,
        key: TechnicalReportIdempotencyKey,
        result: TechnicalReportCommandResult,
    ) -> None:
        row = self.session.query(TechnicalReportIdempotencyRecord).filter_by(
            organization_id=key.organization_id,
            actor_id=key.actor_id,
            command_type=key.command_type,
            idempotency_id=key.idempotency_id,
            status="pending",
        ).one_or_none()
        if row is None or result.command_type != key.command_type:
            raise TechnicalReportValidationError("idempotency reservation is required")
        row.status = "completed"
        row.aggregate_id = result.report_id
        row.result = _json_value(_result_payload(result))


class SqlAlchemyTechnicalReportRejectionAuditRecorder:
    """Persist bounded rejection accountability after authoritative rollback."""

    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory
        self._authoritative_rollback_complete = False

    def _permit_after_authoritative_rollback(self) -> None:
        self._authoritative_rollback_complete = True

    def record_rejection(self, record: TechnicalReportRejectionAuditRecord) -> None:
        if not self._authoritative_rollback_complete:
            raise TechnicalReportValidationError(
                "rejection Audit requires authoritative rollback"
            )
        self._authoritative_rollback_complete = False
        if record.reason not in set(TechnicalReportRejectionReason):
            raise TechnicalReportValidationError("rejection Audit reason is invalid")
        session = self.session_factory()
        try:
            session.add(
                AuditLog(
                    user_id=record.actor_id,
                    action=record.operation,
                    entity="TECHNICAL_REPORT",
                    entity_uuid=record.report_id,
                    details={
                        "outcome": "rejected",
                        "reason": record.reason.value,
                        "organization_id": str(record.organization_id),
                        "command_id": (
                            None if record.command_id is None else str(record.command_id)
                        ),
                        "correlation_id": str(record.correlation_id),
                    },
                    created_at=record.occurred_at,
                )
            )
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


class SqlAlchemyTechnicalReportUnitOfWork:
    """Own the sole authoritative Technical Report transaction boundary."""

    def __init__(self, session_factory, rejection_session_factory=None) -> None:
        self.session_factory = session_factory
        self.rejection_audit = SqlAlchemyTechnicalReportRejectionAuditRecorder(
            rejection_session_factory or session_factory
        )

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.technical_reports = SqlAlchemyTechnicalReportRepository(self.session)
        self.authorization = SqlAlchemyTechnicalReportAuthorizationPolicy(self.session)
        self.references = SqlAlchemyTechnicalReportReferenceValidator(self.session)
        self.historical = SqlAlchemyTechnicalReportHistoricalResolver(self.session)
        self.audit = SqlAlchemyTechnicalReportAuditRecorder(self.session)
        self.domain_events = SqlAlchemyTechnicalReportDomainEventRecorder(self.session)
        self.idempotency = SqlAlchemyTechnicalReportIdempotencyStore(self.session)
        self.final_recheck = SqlAlchemyTechnicalReportFinalRecheckPolicy(
            self.session, self.authorization, self.references, self.historical
        )
        self.standards = SqlAlchemyTechnicalReportStandardsPolicy(self.session)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
        self.rejection_audit._permit_after_authoritative_rollback()


class SqlAlchemyTechnicalReportAuthorizationPolicy:
    """Authorize trusted scope through the authoritative UoW Session."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def require(self, request: TechnicalReportAuthorizationRequest) -> None:
        allowed_operations = {
            "create_draft", "revise_draft", "accept_exact_draft",
            "create_successor", "get", "list", "retrieve_lineage",
            "request_ai_proposal",
        }
        if request.operation not in allowed_operations:
            raise TechnicalReportAuthorizationDenied()
        if request.actor.organization_id != request.scope.organization_id:
            raise TechnicalReportAuthorizationDenied()
        user = self.session.get(User, request.actor.actor_id, with_for_update=True)
        organization = self.session.get(
            Organization, request.scope.organization_id, with_for_update=True
        )
        membership = self.session.get(
            UserOrganizationMembership,
            (request.actor.actor_id, request.scope.organization_id),
            with_for_update=True,
        )
        workspace = self.session.get(
            EngineeringWorkspace, request.scope.workspace_id, with_for_update=True
        )
        project = None if workspace is None else self.session.get(
            Project, workspace.project_id, with_for_update=True
        )
        if (
            user is None or not user.is_active or user.role not in {"admin", "engineer"}
            or organization is None or not organization.is_active
            or membership is None or not membership.is_enabled or not membership.is_selected
            or workspace is None or workspace.status != WorkspaceStatus.ACTIVE.value
            or project is None
            or project.organization_id != request.scope.organization_id
            or (request.scope.project_id is not None and request.scope.project_id != project.id)
        ):
            raise TechnicalReportAuthorizationDenied()
        allowed = user.role == "admin" or request.actor.actor_id in {
            project.owner_id, project.primary_assignee_id,
            workspace.owner_id, workspace.primary_assignee_id,
        }
        if not allowed:
            allowed = self.session.get(
                EngineeringWorkspaceMember,
                (workspace.id, request.actor.actor_id),
                with_for_update=True,
            ) is not None
        if not allowed:
            raise TechnicalReportAuthorizationDenied()
        if request.report_id is not None:
            report = self.session.query(TechnicalReportRecord).filter_by(
                id=request.report_id,
                organization_id=request.scope.organization_id,
                workspace_id=request.scope.workspace_id,
                project_id=request.scope.project_id,
            ).with_for_update().first()
            if report is None:
                raise TechnicalReportAuthorizationDenied()
            owner_operations = {
                "revise_draft", "accept_exact_draft", "create_successor",
                "request_ai_proposal",
            }
            if request.operation in owner_operations and report.owner_id != request.actor.actor_id:
                if request.operation == "accept_exact_draft":
                    raise TechnicalReportAcceptanceAuthorityDenied()
                raise TechnicalReportAuthorizationDenied()


class SqlAlchemyTechnicalReportReferenceValidator:
    """Validate and lock accepted reference types in the UoW Session."""

    _MODELS = {
        "technical_report": TechnicalReportRecord,
        "universal_capture": EngineeringExperienceCapture,
        "evidence": Evidence,
        "engineering_object": EngineeringObject,
        "engineering_relationship": EngineeringRelationship,
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    def validate(self, request: TechnicalReportReferenceRequest) -> None:
        model = self._MODELS.get(request.reference_type)
        if model is None or request.actor.organization_id != request.scope.organization_id:
            raise TechnicalReportAuthorizationDenied()
        row = self.session.query(model).filter(
            model.id == request.reference_id,
            model.organization_id == request.scope.organization_id,
        ).with_for_update().first()
        if row is None:
            raise TechnicalReportAuthorizationDenied()


class SqlAlchemyTechnicalReportFinalRecheckPolicy:
    """Lock and recheck every mutable acceptance predicate before CAS/commit."""

    _SOURCE_MODELS = SqlAlchemyTechnicalReportReferenceValidator._MODELS

    def __init__(self, session, authorization, references, historical) -> None:
        self.session = session
        self.authorization = authorization
        self.references = references
        self.historical = historical

    def require_current(self, request: TechnicalReportFinalRecheckRequest) -> None:
        self.authorization.require(TechnicalReportAuthorizationRequest(
            request.actor, "accept_exact_draft", request.scope, request.report_id
        ))
        report = self.session.query(TechnicalReportRecord).filter_by(
            id=request.report_id,
            organization_id=request.scope.organization_id,
            workspace_id=request.scope.workspace_id,
            project_id=request.scope.project_id,
            owner_id=request.owner_id,
            lifecycle="draft",
            version=request.expected_version,
            draft_revision_id=request.expected_draft_revision_id,
        ).with_for_update().first()
        if report is None or report.owner_id != request.actor.actor_id:
            raise TechnicalReportVersionConflict()
        for source in request.sources:
            if source.actor != request.actor or source.scope != request.scope:
                raise TechnicalReportAuthorizationDenied()
            model = self._SOURCE_MODELS.get(source.source_type)
            row = None if model is None else self.session.query(model).filter(
                model.id == source.source_id,
                model.organization_id == request.scope.organization_id,
            ).with_for_update().first()
            if row is None or row.version != source.source_version:
                raise TechnicalReportHistoricalBasisIncomplete()
            if isinstance(row, EngineeringRelationship):
                related_objects = self.session.query(EngineeringObject).filter(
                    EngineeringObject.id.in_((row.source_object_id, row.target_object_id)),
                    EngineeringObject.organization_id == request.scope.organization_id,
                ).with_for_update().all()
                if len(related_objects) != 2:
                    raise TechnicalReportHistoricalBasisIncomplete()
                evidence_ids = tuple(UUID(str(value)) for value in row.evidence_references)
                if evidence_ids:
                    related_evidence = self.session.query(Evidence).filter(
                        Evidence.id.in_(evidence_ids),
                        Evidence.organization_id == request.scope.organization_id,
                    ).with_for_update().all()
                    if len(related_evidence) != len(set(evidence_ids)):
                        raise TechnicalReportHistoricalBasisIncomplete()
            if isinstance(row, Evidence):
                try:
                    self.historical.supporting_files.resolve_for_evidence(
                        evidence_id=row.id,
                        organization_id=request.scope.organization_id,
                        project_id=request.scope.project_id,
                        workspace_id=request.scope.workspace_id,
                        lock=True,
                    )
                except Exception as exc:
                    raise TechnicalReportHistoricalBasisIncomplete() from exc
            self.historical.resolve(source)


class SqlAlchemyTechnicalReportStandardsPolicy:
    """Report-owned standards locks, handle resolution, and final rechecks."""

    _CAPABILITY_COLUMNS = {
        "metadata_visibility": "allow_metadata_visibility",
        "content_storage": "allow_content_storage",
        "indexing": "allow_indexing",
        "excerpt_display": "allow_excerpt_display",
        "source_retrieval": "allow_source_retrieval",
        "derived_retention": "allow_derived_retention",
        "derived_current_use": "allow_derived_current_use",
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _rights_active(rights: OrganizationRightsBinding, now: datetime) -> bool:
        return (
            rights.is_current is True
            and rights.rights_status == "active"
            and rights.effective_from <= now
            and (rights.effective_until is None or rights.effective_until > now)
        )

    def _candidate_query(self, actor, scope, now, *, lock: bool):
        query = (
            self.session.query(
                StandardSourceSnapshot, StandardEdition, StandardIdentity,
                StandardEditionStandingObservation, OrganizationRightsBinding,
            )
            .join(StandardEdition, StandardEdition.id == StandardSourceSnapshot.standard_edition_id)
            .join(StandardIdentity, StandardIdentity.id == StandardEdition.standard_identity_id)
            .join(StandardEditionStandingObservation, and_(
                StandardEditionStandingObservation.standard_edition_id == StandardEdition.id,
                StandardEditionStandingObservation.is_current.is_(True),
            ))
            .join(OrganizationRightsBinding, and_(
                OrganizationRightsBinding.organization_id == scope.organization_id,
                OrganizationRightsBinding.standard_edition_id == StandardEdition.id,
                OrganizationRightsBinding.source_provider_id == StandardSourceSnapshot.source_provider_id,
                OrganizationRightsBinding.is_current.is_(True),
            ))
            .filter(
                StandardSourceSnapshot.organization_id == scope.organization_id,
                StandardSourceSnapshot.project_id == scope.project_id,
                OrganizationRightsBinding.rights_status == "active",
                OrganizationRightsBinding.effective_from <= now,
                (OrganizationRightsBinding.effective_until.is_(None)
                 | (OrganizationRightsBinding.effective_until > now)),
                OrganizationRightsBinding.allow_metadata_visibility.is_(True),
                StandardIdentity.retired_from_new_selection.is_(False),
                StandardSourceSnapshot.request_purpose.in_((
                    "reference_only", "material_support",
                )),
                ((StandardIdentity.catalog_scope == "global_trusted")
                 | (StandardIdentity.organization_id == scope.organization_id)),
            )
            .order_by(
                StandardIdentity.issuer_key, StandardIdentity.designation_key,
                StandardEdition.edition_key, StandardSourceSnapshot.source_provider_id,
                StandardSourceSnapshot.source_location, StandardSourceSnapshot.id,
            )
        )
        # Snapshot/edition history is DB-immutable and the runtime role has no
        # UPDATE authority on it.  Lock only mutable current heads plus the
        # identity retirement flag; immutable rows are read in the same MVCC
        # snapshot and are protected by their history guards.
        return query.with_for_update(of=(
            StandardIdentity, StandardEditionStandingObservation,
            OrganizationRightsBinding,
        )) if lock else query

    def list_candidates(self, actor, scope, now):
        if scope.project_id is None:
            return ()
        visible = []
        for rows in self._candidate_query(actor, scope, now, lock=False).limit(64).all():
            source, _edition, _identity, standing, rights = rows
            material = source.request_purpose == "material_support"
            eligible_material = (
                source.availability_status == "available"
                and source.integrity_verified is True
                and rights.allow_source_retrieval is True
                and source.byte_count is not None
                and (source.content_sha256 is not None or source.provider_version_digest is not None)
            )
            if material and not eligible_material:
                continue
            visible.append(rows)
        visible.sort(key=lambda rows: (
            0 if rows[0].request_purpose == "material_support" else 1,
            rows[2].issuer_key, rows[2].designation_key, rows[1].edition_key,
            rows[0].source_location, str(rows[0].id),
        ))
        return tuple(visible[:12])

    def resolve_selection(self, actor, scope, handle, materiality, assertion_id, now):
        if scope.project_id is None:
            raise TechnicalReportAuthorizationDenied()
        for source, edition, identity, standing, rights in self._candidate_query(
            actor, scope, now, lock=True,
        ).limit(64).all():
            try:
                verify_handle(
                    handle, actor_id=actor.actor_id,
                    organization_id=str(scope.organization_id), project_id=scope.project_id,
                    operation="RPT-02", resource_id=str(source.id),
                    edition_id=str(edition.id), rights_binding_id=str(rights.id),
                    rights_version=rights.version, rights_digest=rights.rights_digest,
                    purpose=source.request_purpose, provider_id=source.source_provider_id,
                    source_location=source.source_location,
                    integrity_digest=source.snapshot_digest,
                )
            except OpaqueAuthorizedHandleInvalid:
                continue
            if source.request_purpose != materiality:
                break
            if materiality == "material_support" and (
                source.availability_status != "available"
                or source.integrity_verified is not True
                or source.byte_count is None
                or rights.allow_source_retrieval is not True
                or (source.content_sha256 is None and source.provider_version_digest is None)
            ):
                break
            applicability = self.session.query(ProjectStandardApplicability).filter_by(
                organization_id=scope.organization_id, project_id=scope.project_id,
                standard_edition_id=edition.id, is_current=True,
            ).with_for_update().one_or_none()
            assertion = verifier = None
            if assertion_id is not None:
                assertion = self.session.query(StandardKnowledgeAssertion).filter_by(
                    id=assertion_id, organization_id=scope.organization_id,
                    project_id=scope.project_id, source_snapshot_id=source.id,
                ).with_for_update().one_or_none()
                if assertion is None or assertion.current_verification_event_id is None:
                    break
                verifier = self.session.query(StandardAssertionVerificationEvent).filter_by(
                    id=assertion.current_verification_event_id,
                    assertion_id=assertion.id,
                ).with_for_update().one_or_none()
                if verifier is None:
                    break
            sealed = None
            if materiality == "material_support" and source.provider_version_digest is not None:
                sealed = self.session.execute(text(
                    "SELECT public.resolve_standard_provider_handle(:s,:o,:a,'retrieval')"
                ), {"s": source.id, "o": scope.organization_id, "a": actor.actor_id}).scalar_one_or_none()
                if sealed is None:
                    break
            return source, edition, identity, standing, rights, applicability, assertion, verifier, sealed
        raise TechnicalReportAuthorizationDenied()

    def require_current(self, actor, scope, bases, now):
        """Execute the standards-owned portion of all 13 acceptance rechecks."""
        if len(bases) > 16 or len({item.basis_id for item in bases}) != len(bases):
            raise TechnicalReportHistoricalBasisIncomplete()
        ordered = tuple(sorted(bases, key=lambda item: str(item.basis_id)))
        if any(item.accepted_report_id is not None for item in ordered):
            raise TechnicalReportHistoricalBasisIncomplete()

        def selected(model, identifiers, *, lock):
            values = tuple(sorted(set(identifiers), key=str))
            if not values:
                return {}
            query = (
                self.session.query(model)
                .filter(model.id.in_(values))
                .order_by(model.id)
            )
            rows = (query.with_for_update() if lock else query).all()
            return {row.id: row for row in rows}

        # Accepted IDS §19 lock order: every identity, edition/standing, right,
        # applicability head, source, assertion/event, then intelligence run.
        identities = selected(
            StandardIdentity, (item.standard_identity_id for item in ordered), lock=True,
        )
        editions = selected(
            StandardEdition, (item.standard_edition_id for item in ordered), lock=False,
        )
        standings = selected(
            StandardEditionStandingObservation,
            (item.standing_observation_id for item in ordered),
            lock=True,
        )
        rights_rows = selected(
            OrganizationRightsBinding, (item.rights_binding_id for item in ordered), lock=True,
        )
        applicability_rows = selected(
            ProjectStandardApplicability,
            (item.applicability_id for item in ordered if item.applicability_id is not None),
            lock=True,
        )
        sources = selected(
            StandardSourceSnapshot, (item.source_snapshot_id for item in ordered), lock=False,
        )
        assertions = selected(
            StandardKnowledgeAssertion,
            (item.assertion_id for item in ordered if item.assertion_id is not None),
            lock=True,
        )
        verifications = selected(
            StandardAssertionVerificationEvent,
            (
                item.current_verification_event_id
                for item in assertions.values()
                if item.current_verification_event_id is not None
            ),
            lock=False,
        )

        intelligence = {}
        for interaction_id in sorted({
            item.intelligence_interaction_id for item in ordered
            if item.intelligence_interaction_id is not None
        }, key=str):
            row = self.session.execute(text(
                "SELECT id,provider_id,provider_model,template_digest,input_digest,output_digest,processor_policy_id "
                "FROM public.standard_intelligence_runs "
                "WHERE id=:id AND organization_id=:org AND project_id=:project FOR UPDATE"
            ), {"id": interaction_id, "org": scope.organization_id, "project": scope.project_id}).mappings().one_or_none()
            if row is not None:
                intelligence[row["id"]] = row

        for basis in ordered:
            identity = identities.get(basis.standard_identity_id)
            edition = editions.get(basis.standard_edition_id)
            standing = standings.get(basis.standing_observation_id)
            rights = rights_rows.get(basis.rights_binding_id)
            source = sources.get(basis.source_snapshot_id)
            if identity is None or edition is None or standing is None or rights is None or source is None:
                raise TechnicalReportHistoricalBasisIncomplete()
            if (
                not (
                    identity.catalog_scope == "global_trusted"
                    or identity.organization_id == scope.organization_id
                )
                or identity.retired_from_new_selection is True
                or identity.identity_digest != basis.identity_digest
                or identity.issuer_display != basis.issuer
                or identity.designation != basis.designation
                or identity.title != basis.title
                or edition.standard_identity_id != basis.standard_identity_id
                or edition.edition_digest != basis.edition_digest
                or edition.edition_designation != basis.edition_designation
                or edition.official_publication_identifier != basis.official_publication_identifier
                or edition.publication_date != basis.publication_date
                or standing.standard_edition_id != basis.standard_edition_id
                or standing.is_current is not True
                or standing.standing != basis.standing.value
                or standing.observation_digest != basis.standing_observation_digest
                or rights.organization_id != scope.organization_id
                or rights.standard_edition_id != basis.standard_edition_id
                or rights.source_provider_id != basis.source_provider_id
                or rights.is_current is not True
                or rights.version != basis.rights_binding_version
                or rights.rights_digest != basis.rights_digest
                or rights.rights_basis != basis.rights_basis.value
                or rights.rights_status != basis.rights_status.value
                or rights.ai_processing_permission != basis.ai_processing_permission.value
                or not self._rights_active(rights, now)
                or source.organization_id != scope.organization_id
                or source.project_id != scope.project_id
                or source.standard_identity_id != basis.standard_identity_id
                or source.standard_edition_id != basis.standard_edition_id
                or source.source_provider_id != basis.source_provider_id
                or source.source_location != basis.source_location
                or source.snapshot_digest != basis.snapshot_digest
                or source.availability_status != basis.source_availability_status
                or source.byte_count != basis.byte_count
                or source.content_sha256 != basis.content_digest
                or source.request_purpose != basis.materiality
                or basis.selected_by_id != actor.actor_id
                or standard_basis_digest(basis) != basis.basis_digest
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
            if basis.immutable_provider_token is not None and (
                source.provider_version_digest != basis.provider_version_digest
                or source.provider_handle_key_version != basis.provider_handle_key_version
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
            current_capabilities = {
                key: bool(getattr(rights, column))
                for key, column in self._CAPABILITY_COLUMNS.items()
            }
            if current_capabilities != basis.evaluated_capabilities:
                raise TechnicalReportHistoricalBasisIncomplete()
            if not rights.allow_metadata_visibility:
                raise TechnicalReportAuthorizationDenied()
            if basis.materiality == "material_support" and (
                not rights.allow_source_retrieval
                or source.availability_status != "available"
                or source.integrity_verified is not True
                or basis.byte_count is None
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
            if basis.immutable_provider_token is not None:
                sealed = self.session.execute(text(
                    "SELECT public.resolve_standard_provider_handle(:s,:o,:a,'retrieval')"
                ), {"s": source.id, "o": scope.organization_id, "a": actor.actor_id}).scalar_one_or_none()
                if sealed is None or not hmac.compare_digest(
                    base64.b64encode(sealed).decode("ascii"), basis.immutable_provider_token,
                ):
                    raise TechnicalReportHistoricalBasisIncomplete()
            if basis.applicability_id is not None:
                applicability = applicability_rows.get(basis.applicability_id)
                if applicability is None or (
                    applicability.organization_id != scope.organization_id
                    or applicability.project_id != scope.project_id
                    or applicability.standard_edition_id != basis.standard_edition_id
                    or applicability.is_current is not True
                    or applicability.revision != basis.applicability_revision
                    or applicability.applicability_digest != basis.applicability_digest
                    or applicability.status != basis.applicability_status
                    or applicability.applicability_role != basis.applicability_role
                ):
                    raise TechnicalReportHistoricalBasisIncomplete()
            if basis.standing in {"superseded", "withdrawn"} and (
                basis.applicability_id is None
                or basis.standing_acknowledged_by_id != actor.actor_id
                or not basis.standing_acknowledgement_rationale
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
            if basis.assertion_id is not None:
                assertion = assertions.get(basis.assertion_id)
                verifier = (
                    None if assertion is None
                    else verifications.get(assertion.current_verification_event_id)
                )
                if assertion is None or verifier is None or (
                    assertion.organization_id != scope.organization_id
                    or assertion.project_id != scope.project_id
                    or assertion.standard_edition_id != basis.standard_edition_id
                    or assertion.source_snapshot_id != basis.source_snapshot_id
                    or assertion.assertion_digest != basis.assertion_digest
                    or assertion.assertion_kind != basis.assertion_kind
                    or assertion.assertion_origin != basis.assertion_origin
                    or assertion.verification_status != basis.assertion_verification_status
                    or assertion.retained_derived_use_eligible != basis.assertion_current_use_eligible
                    or verifier.assertion_id != assertion.id
                    or verifier.verified_by != basis.assertion_verified_by_id
                    or (basis.materiality == "material_support" and (
                        assertion.verification_status != "human_verified"
                        or assertion.retained_derived_use_eligible is not True
                        or not rights.allow_derived_current_use
                    ))
                ):
                    raise TechnicalReportHistoricalBasisIncomplete()
            if basis.intelligence_interaction_id is not None:
                run = intelligence.get(basis.intelligence_interaction_id)
                if run is None or (
                    run["provider_id"] != basis.intelligence_provider_id
                    or run["provider_model"] != basis.intelligence_model
                    or run["template_digest"] != basis.intelligence_template_digest
                    or run["input_digest"] != basis.intelligence_input_digest
                    or run["output_digest"] != basis.intelligence_output_digest
                    or run["processor_policy_id"] != basis.intelligence_processor_decision
                ):
                    raise TechnicalReportHistoricalBasisIncomplete()


class SqlAlchemyTechnicalReportHistoricalResolver:
    """Resolve closed historical contracts through a caller-owned Session."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.supporting_files = SqlAlchemySupportingFileTechnicalReportCollaborator(
            session
        )

    def resolve(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis:
        if request.source_type not in _SOURCES:
            raise TechnicalReportHistoricalBasisIncomplete("canonical source type is invalid")
        factories = {
            TechnicalReportSourceType.UNIVERSAL_CAPTURE.value: self._capture,
            TechnicalReportSourceType.EVIDENCE.value: self._evidence,
            TechnicalReportSourceType.ENGINEERING_OBJECT.value: self._engineering_object,
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP.value: self._relationship,
            TechnicalReportSourceType.CROSS_DISCIPLINE_ASSESSMENT.value: self._cross_discipline_assessment,
        }
        return factories[request.source_type](request)

    def resolve_with_fallback(
        self,
        request: TechnicalReportHistoricalRequest,
        fallback: HistoricalBasis,
        expected_digest: str,
    ) -> HistoricalBasis:
        """Use only a complete, integrity-protected report-owned fallback."""

        expected_type = {
            TechnicalReportSourceType.UNIVERSAL_CAPTURE.value: (CaptureHistoricalBasisV1, CaptureHistoricalBasisV2),
            TechnicalReportSourceType.EVIDENCE.value: (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2),
            TechnicalReportSourceType.ENGINEERING_OBJECT.value: (EngineeringObjectHistoricalBasisV1, EngineeringObjectHistoricalBasisV2),
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP.value: (EngineeringRelationshipHistoricalBasisV1, EngineeringRelationshipHistoricalBasisV2),
            TechnicalReportSourceType.CROSS_DISCIPLINE_ASSESSMENT.value: CrossDisciplineAssessmentHistoricalBasisV1,
        }.get(request.source_type)
        self._authorize_scope(request)
        if expected_type is None or not isinstance(fallback, expected_type):
            raise TechnicalReportHistoricalBasisIncomplete("historical fallback type is incoherent")
        if fallback.organization_id != request.actor.organization_id:
            raise TechnicalReportHistoricalBasisIncomplete()
        if isinstance(fallback, (CaptureHistoricalBasisV1, CaptureHistoricalBasisV2)): identity = fallback.capture_id
        elif isinstance(fallback, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2)): identity = fallback.evidence_id
        elif isinstance(fallback, (EngineeringObjectHistoricalBasisV1, EngineeringObjectHistoricalBasisV2)): identity = fallback.engineering_object_id
        elif isinstance(fallback, CrossDisciplineAssessmentHistoricalBasisV1): identity = fallback.assessment_id
        else: identity = fallback.engineering_relationship_id
        if identity != request.source_id or fallback.source_version != request.source_version:
            raise TechnicalReportHistoricalBasisIncomplete()
        self._validate_basis(request, fallback)
        verify_historical_basis_digest(fallback, expected_digest)
        return fallback

    def _capture(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis:
        item = self._load(EngineeringExperienceCapture, request)
        if item.lifecycle != EngineeringExperienceCaptureLifecycle.CAPTURED.value:
            raise TechnicalReportHistoricalBasisIncomplete()
        values = (
            item.id, item.version, item.organization_id,
            item.project_id, item.workspace_id,
        )
        if item.origin_package_key is not None:
            return CaptureHistoricalBasisV2(
                2, "universal_capture", *values,
                item.origin_package_key, item.origin_project_configuration_revision,
                item.origin_declaration_id, item.discipline,
                item.engineering_object_id, item.source_kind, item.original_content,
                item.source_reference, item.creator_id, item.lifecycle, item.created_at,
            )
        return CaptureHistoricalBasisV1(
            1, "universal_capture", item.id, item.version, item.organization_id,
            item.project_id, item.workspace_id, item.discipline,
            item.engineering_object_id, item.source_kind, item.original_content,
            item.source_reference, item.creator_id, item.lifecycle, item.created_at,
        )

    def _evidence(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis:
        item = self._load(Evidence, request)
        if (
            item.lifecycle != EvidenceLifecycle.CURRENT.value
            or item.source_standing != EvidenceSourceStanding.CURRENT.value
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        base = (item.id, item.version, item.organization_id,
            item.project_id, item.workspace_id, item.lifecycle, item.source_kind,
            item.source_reference, item.source_revision, item.source_standing,
            item.effective_at, item.supported_fact, item.creator_id)
        try:
            files = self.supporting_files.resolve_for_evidence(
                evidence_id=item.id,
                organization_id=item.organization_id,
                project_id=item.project_id,
                workspace_id=item.workspace_id,
                lock=False,
            )
        except Exception as exc:
            raise TechnicalReportHistoricalBasisIncomplete() from exc
        if not files:
            return EvidenceHistoricalBasisV1(1, "evidence", *base)
        return EvidenceHistoricalBasisV2(
            2, "evidence", *base, files,
        )

    def _engineering_object(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis:
        item = self._load(EngineeringObject, request)
        self._require_approved_object(item, request)
        if item.origin_package_key is not None:
            rows = list(self.session.query(EngineeringIdentifier).filter_by(
                engineering_object_id=item.id,
                organization_id=item.organization_id,
                lifecycle="current",
            ).order_by(
                EngineeringIdentifier.primary_role.desc(),
                EngineeringIdentifier.identifier_kind,
                EngineeringIdentifier.normalized_value,
                EngineeringIdentifier.identifier_id,
            ).with_for_update().all())
            snapshots = tuple(EngineeringIdentifierHistoricalSnapshotV1(
                row.identifier_id, row.version, row.identifier_kind,
                row.display_value, row.normalized_value,
                row.normalization_algorithm_version, row.issuing_scope_kind,
                row.issuing_scope_value, row.lifecycle, row.authority_standing,
                row.primary_role, tuple(UUID(str(value)) for value in row.evidence_references),
                row.predecessor_identifier_id, row.successor_identifier_id,
                row.creator_id, row.steward_id, row.reviewer_id, row.approver_id,
                row.created_at, row.updated_at, row.origin_package_key,
                row.origin_project_configuration_revision, row.origin_declaration_id,
            ) for row in rows)
            return EngineeringObjectHistoricalBasisV2(
                2, "engineering_object", item.id, item.version, item.organization_id,
                item.customer_id, item.project_id, item.workspace_id,
                item.origin_package_key, item.origin_project_configuration_revision,
                item.origin_declaration_id, snapshots, item.family,
                item.discipline, item.object_type, item.subtype, item.lifecycle,
                item.authority_standing, item.creator_id, item.steward_id,
            )
        return EngineeringObjectHistoricalBasisV1(
            1, "engineering_object", item.id, item.version, item.organization_id,
            item.customer_id, item.project_id, item.workspace_id, item.family,
            item.discipline, item.object_type, item.subtype, item.lifecycle,
            item.authority_standing, item.creator_id, item.steward_id,
        )

    def _relationship(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis:
        item = self._load(EngineeringRelationship, request)
        if (
            item.lifecycle != RelationshipLifecycle.CURRENT.value
            or item.authority_standing != EngineeringAuthorityStanding.APPROVED.value
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        try:
            family = RelationshipFamily(item.relationship_family)
            relationship_type = RelationshipType(item.relationship_type)
        except ValueError as exc:
            raise TechnicalReportHistoricalBasisIncomplete() from exc
        if relationship_type not in RELATIONSHIP_TYPES_BY_FAMILY[family]:
            raise TechnicalReportHistoricalBasisIncomplete()
        self._require_related_object(item.source_object_id, request)
        self._require_related_object(item.target_object_id, request)
        for evidence_id in item.evidence_references:
            self._require_related_evidence(evidence_id, request)
        base = (
            item.id, item.version, item.organization_id, item.project_id,
            item.workspace_id,
        )
        tail = (
            item.source_object_id, item.target_object_id,
            item.relationship_family, item.relationship_type, item.lifecycle,
            item.authority_standing,
            tuple(UUID(str(value)) for value in item.evidence_references),
            item.creator_id, item.steward_id, item.reviewer_id, item.approver_id,
        )
        if item.origin_package_key is not None:
            return EngineeringRelationshipHistoricalBasisV2(
                2, "engineering_relationship", *base,
                item.origin_package_key, item.origin_project_configuration_revision,
                item.origin_declaration_id, *tail,
            )
        return EngineeringRelationshipHistoricalBasisV1(
            1, "engineering_relationship", item.id, item.version,
            item.organization_id, item.project_id, item.workspace_id,
            item.source_object_id, item.target_object_id,
            item.relationship_family, item.relationship_type, item.lifecycle,
            item.authority_standing,
            tuple(UUID(str(value)) for value in item.evidence_references),
            item.creator_id, item.steward_id, item.reviewer_id, item.approver_id,
        )

    def _cross_discipline_assessment(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis:
        project_id = self._authorize_scope(request)
        item = self.session.query(CrossDisciplineAssessment).filter(
            CrossDisciplineAssessment.id == request.source_id,
            CrossDisciplineAssessment.organization_id == request.scope.organization_id,
            CrossDisciplineAssessment.project_id == project_id,
        ).with_for_update().first()
        if item is None or item.aggregate_version != request.source_version:
            raise TechnicalReportHistoricalBasisIncomplete()
        snapshot = self.session.query(CrossDisciplineSnapshot).filter(
            CrossDisciplineSnapshot.assessment_id == item.id,
            CrossDisciplineSnapshot.organization_id == item.organization_id,
            CrossDisciplineSnapshot.project_id == item.project_id,
        ).with_for_update().first()
        if snapshot is None:
            raise TechnicalReportHistoricalBasisIncomplete()
        return CrossDisciplineAssessmentHistoricalBasisV1(
            1, "cross_discipline_assessment", item.id, item.aggregate_version,
            item.organization_id, item.project_id, None, item.status,
            snapshot.snapshot_digest, snapshot.definition_digest, snapshot.result_digest,
            item.completed_at,
        )

    def _load(self, model: type, request: TechnicalReportHistoricalRequest):
        project_id = self._authorize_scope(request)
        item = self.session.query(model).filter(
            model.id == request.source_id,
            model.organization_id == request.actor.organization_id,
        ).first()
        if (
            item is None
            or item.version != request.source_version
            or not self._source_scope_compatible(
                item, request, project_id, model is Evidence
            )
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        return item

    def _authorize_scope(self, request: TechnicalReportHistoricalRequest) -> int:
        """Prove trusted actor and governed scope without disclosing source state."""

        if request.scope.organization_id != request.actor.organization_id:
            raise TechnicalReportHistoricalBasisIncomplete()
        user = self.session.get(User, request.actor.actor_id)
        organization = self.session.get(Organization, request.actor.organization_id)
        membership = self.session.get(
            UserOrganizationMembership,
            (request.actor.actor_id, request.actor.organization_id),
        )
        if (
            user is None
            or not user.is_active
            or user.role not in {"admin", "engineer"}
            or organization is None
            or not organization.is_active
            or membership is None
            or not membership.is_enabled
            or not membership.is_selected
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        workspace = self.session.query(EngineeringWorkspace).join(
            Project, Project.id == EngineeringWorkspace.project_id
        ).filter(
            EngineeringWorkspace.id == request.scope.workspace_id,
            Project.organization_id == request.scope.organization_id,
        ).first()
        if workspace is None:
            raise TechnicalReportHistoricalBasisIncomplete()
        project_id = workspace.project_id
        if (
            request.scope.project_id is not None
            and request.scope.project_id != project_id
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        project = self.session.get(Project, project_id)
        authorized = user.role == "admin" or request.actor.actor_id in {
            project.owner_id,
            project.primary_assignee_id,
            workspace.owner_id,
            workspace.primary_assignee_id,
        }
        if not authorized:
            authorized = self.session.get(
                EngineeringWorkspaceMember,
                (workspace.id, request.actor.actor_id),
            ) is not None
        if not authorized:
            raise TechnicalReportHistoricalBasisIncomplete()
        authority = request.authority
        if isinstance(authority, CreateDraftHistoricalAuthority):
            return project_id
        if isinstance(
            authority,
            (
                ReviseDraftHistoricalAuthority,
                AcceptExactDraftHistoricalAuthority,
                RequestAIProposalHistoricalAuthority,
            ),
        ):
            self._require_owned_draft(request, authority.report_id, authority.owner_id)
            return project_id
        if isinstance(authority, CreateSuccessorHistoricalAuthority):
            self._require_authorized_predecessor_input(request, authority)
            return project_id
        raise TechnicalReportHistoricalBasisIncomplete()

    def _require_owned_draft(
        self, request: TechnicalReportHistoricalRequest, report_id: UUID, owner_id: int
    ) -> None:
        report = self.session.query(TechnicalReportRecord).filter(
            TechnicalReportRecord.id == report_id,
            TechnicalReportRecord.organization_id == request.scope.organization_id,
            TechnicalReportRecord.workspace_id == request.scope.workspace_id,
            TechnicalReportRecord.project_id == request.scope.project_id,
        ).first()
        if (
            report is None
            or report.owner_id != owner_id
            or report.owner_id != request.actor.actor_id
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        if report.lifecycle == "accepted":
            raise TechnicalReportAcceptedImmutable()
        if report.lifecycle != "draft":
            raise TechnicalReportHistoricalBasisIncomplete()

    def _require_authorized_predecessor_input(
        self,
        request: TechnicalReportHistoricalRequest,
        authority: CreateSuccessorHistoricalAuthority,
    ) -> None:
        if authority.copy_protected_inputs is not True:
            raise TechnicalReportHistoricalBasisIncomplete()
        predecessor = self.session.query(TechnicalReportRecord).filter(
            TechnicalReportRecord.id == authority.predecessor_report_id,
            TechnicalReportRecord.organization_id == request.scope.organization_id,
            TechnicalReportRecord.workspace_id == request.scope.workspace_id,
            TechnicalReportRecord.project_id == request.scope.project_id,
            TechnicalReportRecord.lifecycle == "accepted",
        ).first()
        if predecessor is None:
            raise TechnicalReportHistoricalBasisIncomplete()
        identity_columns = {
            TechnicalReportSourceType.UNIVERSAL_CAPTURE.value: (
                TechnicalReportProvenanceRecord.capture_id,
                TechnicalReportProvenanceRecord.capture_version,
            ),
            TechnicalReportSourceType.EVIDENCE.value: (
                TechnicalReportProvenanceRecord.evidence_id,
                TechnicalReportProvenanceRecord.evidence_version,
            ),
            TechnicalReportSourceType.ENGINEERING_OBJECT.value: (
                TechnicalReportProvenanceRecord.engineering_object_id,
                TechnicalReportProvenanceRecord.engineering_object_version,
            ),
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP.value: (
                TechnicalReportProvenanceRecord.engineering_relationship_id,
                TechnicalReportProvenanceRecord.engineering_relationship_version,
            ),
            TechnicalReportSourceType.CROSS_DISCIPLINE_ASSESSMENT.value: (
                TechnicalReportProvenanceRecord.cross_discipline_assessment_id,
                TechnicalReportProvenanceRecord.cross_discipline_assessment_version,
            ),
        }.get(request.source_type)
        if identity_columns is None:
            raise TechnicalReportHistoricalBasisIncomplete()
        protected_input = self.session.query(TechnicalReportProvenanceRecord.id).filter(
            TechnicalReportProvenanceRecord.technical_report_id == predecessor.id,
            TechnicalReportProvenanceRecord.source_type == request.source_type,
            identity_columns[0] == request.source_id,
            identity_columns[1] == request.source_version,
        ).first()
        if protected_input is None:
            raise TechnicalReportHistoricalBasisIncomplete()

    def _require_approved_object(
        self, item: EngineeringObject, request: TechnicalReportHistoricalRequest
    ) -> None:
        if (
            item.lifecycle != EngineeringLifecycle.ACTIVE.value
            or item.authority_standing != EngineeringAuthorityStanding.APPROVED.value
            or item.organization_id != request.scope.organization_id
            or item.project_id != self._authorize_scope(request)
            or item.workspace_id != request.scope.workspace_id
        ):
            raise TechnicalReportHistoricalBasisIncomplete()

    def _require_related_object(
        self, object_id, request: TechnicalReportHistoricalRequest
    ) -> None:
        item = self.session.query(EngineeringObject).filter(
            EngineeringObject.id == object_id,
            EngineeringObject.organization_id == request.scope.organization_id,
        ).first()
        if item is None:
            raise TechnicalReportHistoricalBasisIncomplete()
        self._require_approved_object(item, request)

    def _require_related_evidence(
        self, evidence_id, request: TechnicalReportHistoricalRequest
    ) -> None:
        try:
            evidence_id = UUID(str(evidence_id))
        except ValueError as exc:
            raise TechnicalReportHistoricalBasisIncomplete() from exc
        item = self.session.query(Evidence).filter(
            Evidence.id == evidence_id,
            Evidence.organization_id == request.scope.organization_id,
        ).first()
        if (
            item is None
            or item.project_id not in {None, self._authorize_scope(request)}
            or item.workspace_id not in {None, request.scope.workspace_id}
            or item.lifecycle != EvidenceLifecycle.CURRENT.value
            or item.source_standing != EvidenceSourceStanding.CURRENT.value
        ):
            raise TechnicalReportHistoricalBasisIncomplete()

    def _validate_basis(
        self, request: TechnicalReportHistoricalRequest, basis: HistoricalBasis
    ) -> None:
        project_id = self._authorize_scope(request)
        if (
            basis.organization_id != request.scope.organization_id
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        project_optional = isinstance(basis, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2))
        if (
            basis.project_id not in ({None, project_id} if project_optional else {project_id})
            or basis.workspace_id not in {None, request.scope.workspace_id}
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        if isinstance(basis, (CaptureHistoricalBasisV1, CaptureHistoricalBasisV2)):
            if basis.lifecycle != EngineeringExperienceCaptureLifecycle.CAPTURED:
                raise TechnicalReportHistoricalBasisIncomplete()
        elif isinstance(basis, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2)):
            if (
                basis.lifecycle != EvidenceLifecycle.CURRENT
                or basis.source_standing != EvidenceSourceStanding.CURRENT
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
        elif isinstance(basis, (EngineeringObjectHistoricalBasisV1, EngineeringObjectHistoricalBasisV2)):
            if (
                basis.lifecycle != EngineeringLifecycle.ACTIVE
                or basis.authority_standing
                != EngineeringAuthorityStanding.APPROVED
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
            if isinstance(basis, EngineeringObjectHistoricalBasisV2):
                rows = list(self.session.query(EngineeringIdentifier).filter_by(
                    engineering_object_id=basis.engineering_object_id,
                    organization_id=basis.organization_id,
                    lifecycle="current",
                ).order_by(
                    EngineeringIdentifier.primary_role.desc(),
                    EngineeringIdentifier.identifier_kind,
                    EngineeringIdentifier.normalized_value,
                    EngineeringIdentifier.identifier_id,
                ).with_for_update().all())
                observed = tuple((row.identifier_id, row.version) for row in rows)
                recorded = tuple((row.identifier_id, row.identifier_version) for row in basis.identifiers)
                if observed != recorded:
                    raise TechnicalReportHistoricalBasisIncomplete()
        elif isinstance(basis, (EngineeringRelationshipHistoricalBasisV1, EngineeringRelationshipHistoricalBasisV2)):
            if (
                basis.lifecycle != RelationshipLifecycle.CURRENT
                or basis.authority_standing
                != EngineeringAuthorityStanding.APPROVED
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
            if basis.relationship_type not in RELATIONSHIP_TYPES_BY_FAMILY[
                basis.relationship_family
            ]:
                raise TechnicalReportHistoricalBasisIncomplete()
            self._require_related_object(basis.source_object_id, request)
            self._require_related_object(basis.target_object_id, request)
            for evidence_id in basis.evidence_references:
                self._require_related_evidence(evidence_id, request)
        elif isinstance(basis, CrossDisciplineAssessmentHistoricalBasisV1):
            if basis.status not in {"completed_no_findings", "completed_with_findings", "indeterminate", "unavailable"}:
                raise TechnicalReportHistoricalBasisIncomplete()

    @staticmethod
    def _source_scope_compatible(
        item, request: TechnicalReportHistoricalRequest, project_id: int,
        project_optional: bool,
    ) -> bool:
        allowed_projects = {None, project_id} if project_optional else {project_id}
        return (
            item.project_id in allowed_projects
            and item.workspace_id in {None, request.scope.workspace_id}
        )


def verified_historical_digest(value: HistoricalBasis) -> str:
    """Expose deterministic evidence without transferring source ownership."""

    digest = historical_basis_digest(value)
    if len(digest) != 64:
        raise TechnicalReportIntegrityMismatch()
    return digest

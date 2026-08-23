"""Session-bound Technical Report resolvers and authoritative Unit of Work."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final, Self
from uuid import UUID

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
from app.models.engineering_relationship import EngineeringRelationship
from app.models.evidence import Evidence
from app.models.engineering_workspace import (
    EngineeringWorkspace,
    EngineeringWorkspaceMember,
)
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.models.technical_report import (
    TechnicalReportProvenanceRecord,
    TechnicalReportRecord,
)
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    HistoricalBasis,
    TechnicalReportCommandResult,
    TechnicalReportDomainEvent,
    TechnicalReportDraftRevision,
    TechnicalReportIdempotencyRecord,
    TechnicalReportOutboxRecord,
    historical_basis_digest,
    verify_historical_basis_digest,
)
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
        self.session.add(
            AuditLog(
                user_id=record.actor_id,
                action=record.operation,
                entity="TECHNICAL_REPORT",
                entity_uuid=record.report_id,
                details={
                    "outcome": "succeeded",
                    "organization_id": str(record.organization_id),
                    "command_id": str(record.command_id),
                    "correlation_id": str(record.correlation_id),
                },
                created_at=record.occurred_at,
            )
        )


class SqlAlchemyTechnicalReportDomainEventRecorder:
    """Stage minimal Domain Events in the capability-owned outbox."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, events: tuple[TechnicalReportDomainEvent, ...]) -> None:
        for event in events:
            self.session.add(
                TechnicalReportOutboxRecord(
                    event_id=event.event_id,
                    aggregate_id=event.report_id,
                    aggregate_version=event.aggregate_version,
                    event_type=event.event_type,
                    schema_version=1,
                    payload={
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
                    },
                    occurred_at=event.occurred_at,
                )
            )


def _result_payload(result: TechnicalReportCommandResult) -> dict[str, object]:
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
        "events": [
            {
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
            for event in result.events
        ],
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
                TechnicalReportDomainEvent(
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
                )
                for item in events
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
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
        ).first()
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


class SqlAlchemyTechnicalReportHistoricalResolver:
    """Resolve four closed historical contracts through a caller-owned Session."""

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
            TechnicalReportSourceType.UNIVERSAL_CAPTURE.value: CaptureHistoricalBasisV1,
            TechnicalReportSourceType.EVIDENCE.value: (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2),
            TechnicalReportSourceType.ENGINEERING_OBJECT.value: EngineeringObjectHistoricalBasisV1,
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP.value: EngineeringRelationshipHistoricalBasisV1,
        }.get(request.source_type)
        self._authorize_scope(request)
        if expected_type is None or not isinstance(fallback, expected_type):
            raise TechnicalReportHistoricalBasisIncomplete("historical fallback type is incoherent")
        if fallback.organization_id != request.actor.organization_id:
            raise TechnicalReportHistoricalBasisIncomplete()
        if isinstance(fallback, CaptureHistoricalBasisV1): identity = fallback.capture_id
        elif isinstance(fallback, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2)): identity = fallback.evidence_id
        elif isinstance(fallback, EngineeringObjectHistoricalBasisV1): identity = fallback.engineering_object_id
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
        return EngineeringRelationshipHistoricalBasisV1(
            1, "engineering_relationship", item.id, item.version,
            item.organization_id, item.project_id, item.workspace_id,
            item.source_object_id, item.target_object_id,
            item.relationship_family, item.relationship_type, item.lifecycle,
            item.authority_standing,
            tuple(UUID(str(value)) for value in item.evidence_references),
            item.creator_id, item.steward_id, item.reviewer_id, item.approver_id,
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
        if isinstance(basis, CaptureHistoricalBasisV1):
            if basis.lifecycle != EngineeringExperienceCaptureLifecycle.CAPTURED:
                raise TechnicalReportHistoricalBasisIncomplete()
        elif isinstance(basis, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2)):
            if (
                basis.lifecycle != EvidenceLifecycle.CURRENT
                or basis.source_standing != EvidenceSourceStanding.CURRENT
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
        elif isinstance(basis, EngineeringObjectHistoricalBasisV1):
            if (
                basis.lifecycle != EngineeringLifecycle.ACTIVE
                or basis.authority_standing
                != EngineeringAuthorityStanding.APPROVED
            ):
                raise TechnicalReportHistoricalBasisIncomplete()
        elif isinstance(basis, EngineeringRelationshipHistoricalBasisV1):
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

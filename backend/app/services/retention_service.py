"""PATCH-055 retention-governance application service."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from tempfile import SpooledTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import json
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.enums.retention import (
    DispositionDecision,
    DispositionEligibility,
    HoldStatus,
    RetentionMode,
    RetentionPolicySource,
    RetentionSubjectKind,
    ExportStatus,
    RecoveryStatus,
)
from app.models.retention import (
    RetentionDispositionDecision, RetentionExport, RetentionExportSubject,
    RetentionHold, RetentionRecord, RetentionRecovery,
)
from app.models.retention_command import (
    RetentionGovernanceHeadV1,
    RetentionSubject,
    sha256_digest,
)
from app.schemas.retention import (
    ApplyRetentionPolicyRequestV1,
    CreateRetentionExportRequestV1,
    CreateRetentionRecoveryRequestV1,
    EvidenceWorkbenchResponseV1, EvidenceWorkbenchEvidenceV1, EvidenceWorkbenchFileV1, EvidenceWorkbenchRelianceV1,
    PlaceRetentionHoldRequestV1,
    RecordDispositionDecisionRequestV1,
    ReleaseRetentionHoldRequestV1,
    RetentionExportResponseV1,
    RetentionMutationResponseV1,
    RetentionRecoveryResponseV1,
    RetentionStateResponseV1,
    RetentionSubjectV1,
)


class RetentionServiceError(Exception):
    """Base PATCH-055 application error."""


class RetentionProtectedNotFound(RetentionServiceError):
    pass


class RetentionNotPermitted(RetentionServiceError):
    pass


class RetentionConflict(RetentionServiceError):
    pass


class RetentionInvalidRequest(RetentionServiceError):
    pass


class RetentionIndeterminate(RetentionServiceError):
    pass


class RetentionUnavailable(RetentionServiceError):
    pass


def _subject_response(subject: RetentionSubject) -> RetentionSubjectV1:
    return RetentionSubjectV1(
        subject_kind=subject.subject_kind,
        subject_id=subject.subject_id,
        organization_id=subject.organization_id,
        project_id=subject.project_id,
        workspace_id=subject.workspace_id,
    )


def _eligibility(record, active_hold, now: datetime) -> DispositionEligibility:
    if record is None:
        return DispositionEligibility.INDETERMINATE

    try:
        mode = RetentionMode(record.mode)
    except (TypeError, ValueError):
        return DispositionEligibility.INDETERMINATE

    if not record.basis_code or not record.policy_source:
        return DispositionEligibility.INDETERMINATE

    try:
        RetentionPolicySource(record.policy_source)
    except (TypeError, ValueError):
        return DispositionEligibility.INDETERMINATE

    if active_hold is not None:
        return DispositionEligibility.BLOCKED_BY_HOLD

    if mode is RetentionMode.RETAIN_INDEFINITELY:
        if record.retain_until is not None:
            return DispositionEligibility.INDETERMINATE
        return DispositionEligibility.NOT_ELIGIBLE

    if record.retain_until is None:
        return DispositionEligibility.INDETERMINATE
    if record.retain_until.tzinfo is None or record.retain_until.utcoffset() is None:
        return DispositionEligibility.INDETERMINATE

    normalized_now = now.astimezone(timezone.utc)
    normalized_until = record.retain_until.astimezone(timezone.utc)

    if normalized_now < normalized_until:
        return DispositionEligibility.NOT_ELIGIBLE
    return DispositionEligibility.ELIGIBLE


def _governance_head(
    *,
    subject: RetentionSubject,
    record,
    active_hold,
    decision,
    now: datetime,
) -> RetentionGovernanceHeadV1 | None:
    if record is None:
        return None

    eligibility = _eligibility(record, active_hold, now)
    try:
        retention_mode = RetentionMode(record.mode)
        policy_source = RetentionPolicySource(record.policy_source)
        disposition = (
            DispositionDecision(decision.decision)
            if decision is not None
            else DispositionDecision.NONE
        )
    except (TypeError, ValueError):
        return None

    return RetentionGovernanceHeadV1(
        retention_record_id=record.id,
        subject=subject,
        retention_mode=retention_mode,
        retention_until=record.retain_until,
        policy_basis_code=record.basis_code,
        basis_rationale=record.rationale,
        policy_source=policy_source,
        hold_status=(
            HoldStatus(active_hold.status)
            if active_hold is not None
            else None
        ),
        active_hold_id=(
            active_hold.hold_id
            if active_hold is not None
            else None
        ),
        active_hold_version=(
            active_hold.version
            if active_hold is not None
            else None
        ),
        disposition_eligibility=eligibility,
        disposition_decision=disposition,
        version=record.version,
        predecessor_record_id=record.supersedes_id,
        created_by_user_id=record.created_by_user_id,
        created_at=record.created_at,
        record_digest=record.record_digest,
    )


def _state_response(
    *,
    subject: RetentionSubject,
    record,
    active_hold,
    decision,
    now: datetime,
) -> RetentionStateResponseV1:
    head = _governance_head(
        subject=subject,
        record=record,
        active_hold=active_hold,
        decision=decision,
        now=now,
    )

    if head is None:
        hold_status = None
        active_hold_id = None
        active_hold_version = None
        if active_hold is not None:
            try:
                hold_status = HoldStatus(active_hold.status)
                active_hold_id = active_hold.hold_id
                active_hold_version = active_hold.version
            except (TypeError, ValueError):
                hold_status = None
                active_hold_id = None
                active_hold_version = None

        if record is None:
            return RetentionStateResponseV1(
                retention_record_id=None,
                subject=_subject_response(subject),
                retention_mode=None,
                retention_until=None,
                policy_basis_code=None,
                basis_rationale=None,
                policy_source=None,
                hold_status=hold_status,
                active_hold_id=active_hold_id,
                active_hold_version=active_hold_version,
                disposition_eligibility=DispositionEligibility.INDETERMINATE,
                disposition_decision=DispositionDecision.NONE,
                version=None,
                predecessor_record_id=None,
                record_digest=None,
            )

        return RetentionStateResponseV1(
            retention_record_id=record.id,
            subject=_subject_response(subject),
            retention_mode=None,
            retention_until=record.retain_until,
            policy_basis_code=record.basis_code,
            basis_rationale=record.rationale,
            policy_source=None,
            hold_status=hold_status,
            active_hold_id=active_hold_id,
            active_hold_version=active_hold_version,
            disposition_eligibility=DispositionEligibility.INDETERMINATE,
            disposition_decision=DispositionDecision.NONE,
            version=record.version,
            predecessor_record_id=record.supersedes_id,
            record_digest=record.record_digest,
        )

    return RetentionStateResponseV1(
        retention_record_id=head.retention_record_id,
        subject=_subject_response(head.subject),
        retention_mode=head.retention_mode,
        retention_until=head.retention_until,
        policy_basis_code=head.policy_basis_code,
        basis_rationale=head.basis_rationale,
        policy_source=head.policy_source,
        hold_status=head.hold_status,
        active_hold_id=head.active_hold_id,
        active_hold_version=head.active_hold_version,
        disposition_eligibility=head.disposition_eligibility,
        disposition_decision=head.disposition_decision,
        version=head.version,
        predecessor_record_id=head.predecessor_record_id,
        record_digest=head.record_digest,
    )


def _safe_result(
    response: RetentionMutationResponseV1,
    *,
    correlation_id: UUID,
) -> dict:
    state = response.state
    return {
        "outcome": response.outcome,
        "retention_record_id": (
            str(state.retention_record_id)
            if state.retention_record_id is not None
            else None
        ),
        "version": state.version,
        "disposition_eligibility": state.disposition_eligibility.value,
        "disposition_decision": state.disposition_decision.value,
        "hold_status": (
            state.hold_status.value
            if state.hold_status is not None
            else None
        ),
        "active_hold_id": (
            str(state.active_hold_id)
            if state.active_hold_id is not None
            else None
        ),
        "correlation_id": str(correlation_id),
    }


def _replay_mutation(row) -> RetentionMutationResponseV1:
    if row.status != "completed" or row.safe_result is None:
        raise RetentionConflict()

    safe = row.safe_result
    if safe.get("outcome") != "success":
        raise RetentionConflict()

    raise RetentionConflict(
        "completed idempotency replay requires authorized state reread"
    )


def _replay_policy_response(
    *,
    subject: RetentionSubject,
    record,
    safe: dict,
) -> RetentionMutationResponseV1:
    if record is None:
        raise RetentionConflict()

    try:
        if (
            safe.get("outcome") != "success"
            or safe.get("retention_record_id") != str(record.id)
            or safe.get("version") != record.version
        ):
            raise RetentionConflict()

        hold_status = (
            HoldStatus(safe["hold_status"])
            if safe.get("hold_status") is not None
            else None
        )
        active_hold_id = (
            UUID(safe["active_hold_id"])
            if safe.get("active_hold_id") is not None
            else None
        )

        state = RetentionStateResponseV1(
            retention_record_id=record.id,
            subject=_subject_response(subject),
            retention_mode=RetentionMode(record.mode),
            retention_until=record.retain_until,
            policy_basis_code=record.basis_code,
            basis_rationale=record.rationale,
            policy_source=RetentionPolicySource(record.policy_source),
            hold_status=hold_status,
            active_hold_id=active_hold_id,
            disposition_eligibility=DispositionEligibility(
                safe["disposition_eligibility"]
            ),
            disposition_decision=DispositionDecision(
                safe["disposition_decision"]
            ),
            version=record.version,
            predecessor_record_id=record.supersedes_id,
            record_digest=record.record_digest,
        )
    except (KeyError, TypeError, ValueError):
        raise RetentionConflict() from None

    return RetentionMutationResponseV1(
        outcome="success",
        state=state,
    )


def _safe_hold_result(
    response: RetentionMutationResponseV1,
    *,
    hold_id: UUID,
    hold_version: int,
    correlation_id: UUID,
) -> dict:
    result = _safe_result(
        response,
        correlation_id=correlation_id,
    )
    result.update({
        "hold_id": str(hold_id),
        "hold_version": hold_version,
    })
    return result


def _record_hold_event(
    *,
    uow,
    subject: RetentionSubject,
    actor_id: int,
    action: str,
    hold_id: UUID,
    hold_version: int,
    hold_digest: str,
    correlation_id: UUID,
    occurred_at: datetime,
) -> None:
    safe_payload = {
        "subject_kind": subject.subject_kind.value,
        "project_id": subject.project_id,
        "workspace_id": subject.workspace_id,
        "actor_user_id": actor_id,
        "operation": action,
        "version": hold_version,
        "hold_digest": hold_digest,
        "correlation_id": str(correlation_id),
    }

    uow.audit.record(
        actor_id=actor_id,
        action=action,
        aggregate_id=hold_id,
        project_id=subject.project_id,
        workspace_id=subject.workspace_id,
        version=hold_version,
        correlation_id=correlation_id,
    )
    uow.outbox.record(
        event_id=uuid4(),
        organization_id=subject.organization_id,
        project_id=subject.project_id,
        workspace_id=subject.workspace_id,
        aggregate_kind="retention_hold",
        aggregate_id=hold_id,
        aggregate_version=hold_version,
        event_type=action,
        payload=safe_payload,
        occurred_at=occurred_at,
    )


def _record_governance_event(
    *,
    uow,
    subject: RetentionSubject,
    actor_id: int,
    action: str,
    aggregate_id: UUID,
    aggregate_version: int,
    event_type: str,
    record_digest: str,
    aggregate_kind: str = "retention_record",
    correlation_id: UUID,
    occurred_at: datetime,
) -> None:
    safe_payload = {
        "subject_kind": subject.subject_kind.value,
        "project_id": subject.project_id,
        "workspace_id": subject.workspace_id,
        "actor_user_id": actor_id,
        "operation": action,
        "version": aggregate_version,
        "record_digest": record_digest,
        "correlation_id": str(correlation_id),
    }

    uow.audit.record(
        actor_id=actor_id,
        action=action,
        aggregate_id=aggregate_id,
        project_id=subject.project_id,
        workspace_id=subject.workspace_id,
        version=aggregate_version,
        correlation_id=correlation_id,
    )
    uow.outbox.record(
        event_id=uuid4(),
        organization_id=subject.organization_id,
        project_id=subject.project_id,
        workspace_id=subject.workspace_id,
        aggregate_kind=aggregate_kind,
        aggregate_id=aggregate_id,
        aggregate_version=aggregate_version,
        event_type=event_type,
        payload=safe_payload,
        occurred_at=occurred_at,
    )


def _record_transport_event(
    *, uow, subject: RetentionSubject, actor_id: int, action: str,
    aggregate_kind: str, aggregate_id: UUID, status_code: str,
    correlation_id: UUID, occurred_at: datetime,
) -> None:
    safe_payload = {
        "subject_kind": subject.subject_kind.value,
        "project_id": subject.project_id,
        "workspace_id": subject.workspace_id,
        "actor_user_id": actor_id,
        "operation": action,
        "version": 1,
        "status": status_code,
        "correlation_id": str(correlation_id),
    }
    uow.audit.record(
        actor_id=actor_id, action=action, aggregate_id=aggregate_id,
        project_id=subject.project_id, workspace_id=subject.workspace_id,
        version=1, correlation_id=correlation_id,
    )
    uow.outbox.record(
        event_id=uuid4(), organization_id=subject.organization_id,
        project_id=subject.project_id, workspace_id=subject.workspace_id,
        aggregate_kind=aggregate_kind, aggregate_id=aggregate_id,
        aggregate_version=1, event_type=action, payload=safe_payload,
        occurred_at=occurred_at,
    )


class RetentionService:
    def __init__(
        self,
        *,
        uow_factory,
        clock,
        export_store=None,
        recovery_resolver=None,
    ):
        self.uow_factory = uow_factory
        self.clock = clock
        self.export_store = export_store
        self.recovery_resolver = recovery_resolver

    @staticmethod
    def _authorized_subject(
        uow,
        *,
        organization_id: UUID,
        actor_id: int,
        subject_kind: str,
        subject_id: UUID,
        mutation: bool,
        lock: bool = False,
    ):
        if not uow.authorization.authorize_actor(
            actor_id=actor_id,
            organization_id=organization_id,
        ):
            raise RetentionProtectedNotFound()

        resolved = uow.retention.resolve_subject(
            organization_id=organization_id,
            subject_kind=subject_kind,
            subject_id=subject_id,
            lock=lock,
        )
        if resolved is None:
            raise RetentionProtectedNotFound()

        subject, subject_version = resolved

        if not uow.authorization.authorize_read(
            actor_id=actor_id,
            subject=subject,
        ):
            raise RetentionProtectedNotFound()

        if mutation and not uow.authorization.authorize_mutation(
            actor_id=actor_id,
            subject=subject,
        ):
            raise RetentionNotPermitted()

        return subject, subject_version

    def create_export(
        self, *, organization_id: UUID, actor_id: int,
        data: CreateRetentionExportRequestV1, idempotency_key: UUID,
        correlation_id: UUID,
    ) -> RetentionExportResponseV1:
        now = self.clock.now()
        resolved = []
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_actor(actor_id=actor_id, organization_id=organization_id):
                raise RetentionProtectedNotFound()
            project_id = workspace_id = None
            for ordinal, item in enumerate(data.subjects):
                subject, version = self._authorized_subject(
                    uow, organization_id=organization_id, actor_id=actor_id,
                    subject_kind=item.subject.subject_kind.value,
                    subject_id=item.subject.subject_id, mutation=False,
                )
                if item.subject.organization_id != subject.organization_id or item.subject.project_id != subject.project_id or item.subject.workspace_id != subject.workspace_id:
                    raise RetentionProtectedNotFound()
                if item.subject_version is not None and item.subject_version != version:
                    raise RetentionConflict()
                if project_id is None:
                    project_id, workspace_id = subject.project_id, subject.workspace_id
                elif (project_id, workspace_id) != (subject.project_id, subject.workspace_id):
                    raise RetentionInvalidRequest()
                asset = uow.retention.get_supporting_file_asset(subject=subject)
                digest = asset.content_digest if asset is not None else None
                resolved.append((ordinal, subject, version, digest))
            request_digest = sha256_digest({
                "operation": "CreateRetentionExport", "subjects": [
                    {"kind": x[1].subject_kind.value, "id": x[1].subject_id, "version": x[2]} for x in resolved
                ], "purpose": data.purpose, "format": data.format,
            })
            prior = uow.idempotency.get(organization_id=organization_id, actor_id=actor_id, operation="CreateRetentionExport", idempotency_key=idempotency_key, lock=True)
            if prior is not None:
                if prior.request_digest != request_digest or prior.status != "completed": raise RetentionConflict()
                export = uow.retention.get_export(organization_id=organization_id, export_id=UUID(prior.safe_result["export_id"]))
                if export is None: raise RetentionConflict()
                return RetentionExportResponseV1(export_id=export.id, status=export.status, requested_at=export.requested_at, completed_at=export.completed_at, aggregate_digest=export.aggregate_digest, byte_count=export.byte_count)
            reservation = uow.idempotency.reserve(organization_id=organization_id, actor_user_id=actor_id, operation="CreateRetentionExport", idempotency_key=idempotency_key, request_digest=request_digest, created_at=now, updated_at=now)
            export = RetentionExport(id=uuid4(), organization_id=organization_id, project_id=project_id, workspace_id=workspace_id, requested_by_user_id=actor_id, purpose=data.purpose, status=ExportStatus.REQUESTED.value, format=data.format, requested_at=now, request_digest=request_digest)
            uow.retention.add(export)
            for ordinal, subject, version, digest in resolved:
                uow.retention.add(RetentionExportSubject(export_id=export.id, ordinal=ordinal, organization_id=organization_id, project_id=subject.project_id, workspace_id=subject.workspace_id, subject_kind=subject.subject_kind.value, subject_id=subject.subject_id, subject_version=version, content_digest=digest))
            _record_transport_event(uow=uow, subject=resolved[0][1], actor_id=actor_id, action="RETENTION_EXPORT_REQUESTED", aggregate_kind="retention_export", aggregate_id=export.id, status_code=export.status, correlation_id=correlation_id, occurred_at=now)
            uow.retention.flush()
            uow.idempotency.complete(reservation, safe_result={"outcome":"success", "export_id":str(export.id), "status":export.status, "correlation_id":str(correlation_id)}, completed_at=now)
            uow.commit()
            return RetentionExportResponseV1(export_id=export.id, status=export.status, requested_at=export.requested_at)

    def complete_export(self, *, organization_id: UUID, actor_id: int, export_id: UUID, correlation_id: UUID) -> RetentionExportResponseV1:
        if self.export_store is None:
            raise RetentionUnavailable()
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_actor(actor_id=actor_id, organization_id=organization_id):
                raise RetentionProtectedNotFound()
            export = uow.retention.get_export(organization_id=organization_id, export_id=export_id, lock=True)
            if export is None:
                raise RetentionProtectedNotFound()
            if export.status == ExportStatus.COMPLETED.value:
                return RetentionExportResponseV1(export_id=export.id, status=export.status, requested_at=export.requested_at, completed_at=export.completed_at, aggregate_digest=export.aggregate_digest, byte_count=export.byte_count)
            if export.status != ExportStatus.REQUESTED.value:
                raise RetentionConflict()
            bound_rows = uow.retention.list_export_subjects(export_id=export.id)
            metadata = []
            file_entries = []
            protected_total = 0
            for bound in bound_rows:
                subject, version = self._authorized_subject(uow, organization_id=organization_id, actor_id=actor_id, subject_kind=bound.subject_kind, subject_id=bound.subject_id, mutation=False)
                if version != bound.subject_version or (subject.project_id, subject.workspace_id) != (bound.project_id, bound.workspace_id):
                    raise RetentionConflict()
                entry = {"ordinal": bound.ordinal, "subject_kind": bound.subject_kind, "subject_id": str(bound.subject_id), "subject_version": bound.subject_version, "content_digest": bound.content_digest}
                metadata.append(entry)
                asset = uow.retention.get_supporting_file_asset(subject=subject)
                if asset is not None:
                    if asset.content_digest != bound.content_digest:
                        raise RetentionConflict()
                    protected_total += int(asset.byte_size)
                    if protected_total > 838_860_800:
                        raise RetentionInvalidRequest()
                    file_entries.append((bound.ordinal, subject, bound.content_digest))
            with SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as artifact:
                with ZipFile(artifact, "w", compression=ZIP_DEFLATED, allowZip64=True) as archive:
                    archive.writestr("manifest.json", json.dumps({"schema":"satco.retention.export.v1", "export_id":str(export.id), "subjects":metadata}, sort_keys=True, separators=(",", ":")))
                    for ordinal, subject, expected_digest in file_entries:
                        stream = self.recovery_resolver.resolve_authorized(subject=subject, expected_digest=expected_digest) if self.recovery_resolver is not None else None
                        if stream is None:
                            raise RetentionUnavailable()
                        digest = sha256(); total = 0
                        with archive.open(f"protected/{ordinal:02d}.bin", "w", force_zip64=True) as target:
                            while True:
                                chunk = stream.read(1024 * 1024)
                                if not chunk: break
                                total += len(chunk)
                                if total > 26_214_400:
                                    raise RetentionInvalidRequest()
                                digest.update(chunk); target.write(chunk)
                        if digest.hexdigest() != expected_digest:
                            raise RetentionUnavailable()
                artifact.seek(0)
                receipt = self.export_store.put_private(export_id=export.id, stream=artifact, media_type="application/zip")
            export.status = ExportStatus.COMPLETED.value
            export.completed_at = self.clock.now()
            export.aggregate_digest = receipt.sha256
            export.byte_count = receipt.byte_count
            export.artifact_storage_key = receipt.key
            export.artifact_object_version = receipt.version
            _record_transport_event(uow=uow, subject=RetentionSubject(subject_kind=RetentionSubjectKind(bound_rows[0].subject_kind), subject_id=bound_rows[0].subject_id, organization_id=organization_id, project_id=bound_rows[0].project_id, workspace_id=bound_rows[0].workspace_id), actor_id=actor_id, action="RETENTION_EXPORT_COMPLETED", aggregate_kind="retention_export", aggregate_id=export.id, status_code=export.status, correlation_id=correlation_id, occurred_at=export.completed_at)
            uow.retention.flush(); uow.commit()
            return RetentionExportResponseV1(export_id=export.id, status=export.status, requested_at=export.requested_at, completed_at=export.completed_at, aggregate_digest=export.aggregate_digest, byte_count=export.byte_count)

    def fail_export(self, *, organization_id: UUID, actor_id: int, export_id: UUID, correlation_id: UUID, failure_code: str = "artifact_unavailable") -> RetentionExportResponseV1:
        now = self.clock.now()
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_actor(actor_id=actor_id, organization_id=organization_id):
                raise RetentionProtectedNotFound()
            export = uow.retention.get_export(organization_id=organization_id, export_id=export_id, lock=True)
            if export is None:
                raise RetentionProtectedNotFound()
            if export.status == ExportStatus.COMPLETED.value:
                raise RetentionConflict()
            bound_rows = uow.retention.list_export_subjects(export_id=export.id)
            if not bound_rows:
                raise RetentionConflict()
            for bound in bound_rows:
                subject, _ = self._authorized_subject(uow, organization_id=organization_id, actor_id=actor_id, subject_kind=bound.subject_kind, subject_id=bound.subject_id, mutation=False)
                if (subject.project_id, subject.workspace_id) != (bound.project_id, bound.workspace_id):
                    raise RetentionProtectedNotFound()
            if export.status == ExportStatus.FAILED.value:
                return RetentionExportResponseV1(export_id=export.id, status=export.status, requested_at=export.requested_at, completed_at=export.completed_at)
            export.status = ExportStatus.FAILED.value
            export.completed_at = now
            export.failure_code = failure_code
            subject = RetentionSubject(subject_kind=RetentionSubjectKind(bound_rows[0].subject_kind), subject_id=bound_rows[0].subject_id, organization_id=organization_id, project_id=bound_rows[0].project_id, workspace_id=bound_rows[0].workspace_id)
            _record_transport_event(uow=uow, subject=subject, actor_id=actor_id, action="RETENTION_EXPORT_FAILED", aggregate_kind="retention_export", aggregate_id=export.id, status_code=export.status, correlation_id=correlation_id, occurred_at=now)
            uow.retention.flush(); uow.commit()
            return RetentionExportResponseV1(export_id=export.id, status=export.status, requested_at=export.requested_at, completed_at=export.completed_at)

    def get_export_status(self, *, organization_id: UUID, actor_id: int, export_id: UUID) -> RetentionExportResponseV1:
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_actor(actor_id=actor_id, organization_id=organization_id):
                raise RetentionProtectedNotFound()
            export = uow.retention.get_export(organization_id=organization_id, export_id=export_id)
            if export is None:
                raise RetentionProtectedNotFound()
            for bound in uow.retention.list_export_subjects(export_id=export.id):
                subject, _ = self._authorized_subject(
                    uow, organization_id=organization_id, actor_id=actor_id,
                    subject_kind=bound.subject_kind, subject_id=bound.subject_id, mutation=False,
                )
                if (subject.project_id, subject.workspace_id) != (bound.project_id, bound.workspace_id):
                    raise RetentionProtectedNotFound()
            return RetentionExportResponseV1(
                export_id=export.id, status=export.status, requested_at=export.requested_at,
                completed_at=export.completed_at, aggregate_digest=export.aggregate_digest, byte_count=export.byte_count,
            )

    def open_export_content(self, *, organization_id: UUID, actor_id: int, export_id: UUID):
        if self.export_store is None:
            raise RetentionUnavailable()
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_actor(actor_id=actor_id, organization_id=organization_id):
                raise RetentionProtectedNotFound()
            export = uow.retention.get_export(organization_id=organization_id, export_id=export_id)
            if export is None or export.status != ExportStatus.COMPLETED.value:
                raise RetentionProtectedNotFound()
            for bound in uow.retention.list_export_subjects(export_id=export.id):
                subject, _ = self._authorized_subject(uow, organization_id=organization_id, actor_id=actor_id, subject_kind=bound.subject_kind, subject_id=bound.subject_id, mutation=False)
                if (subject.project_id, subject.workspace_id) != (bound.project_id, bound.workspace_id):
                    raise RetentionProtectedNotFound()
            receipt = self.export_store.head_exact(export_id=export.id, version=export.artifact_object_version)
            if receipt is None or receipt.sha256 != export.aggregate_digest or receipt.byte_count != export.byte_count:
                raise RetentionUnavailable()
            return self.export_store.open_exact(export_id=export.id, version=export.artifact_object_version)

    def create_recovery(
        self, *, organization_id: UUID, actor_id: int, data: CreateRetentionRecoveryRequestV1,
        idempotency_key: UUID, correlation_id: UUID,
    ) -> RetentionRecoveryResponseV1:
        now = self.clock.now()
        with self.uow_factory() as uow:
            subject, _ = self._authorized_subject(
                uow, organization_id=organization_id, actor_id=actor_id,
                subject_kind=data.subject.subject_kind.value, subject_id=data.subject.subject_id, mutation=False,
            )
            if (data.subject.organization_id, data.subject.project_id, data.subject.workspace_id) != (subject.organization_id, subject.project_id, subject.workspace_id):
                raise RetentionProtectedNotFound()
            asset = uow.retention.get_supporting_file_asset(subject=subject)
            expected_digest = asset.content_digest if asset is not None else None
            request_digest = sha256_digest({"operation":"CreateRetentionRecovery", "kind":subject.subject_kind.value, "id":subject.subject_id, "expected_digest":expected_digest})
            prior = uow.idempotency.get(organization_id=organization_id, actor_id=actor_id, operation="CreateRetentionRecovery", idempotency_key=idempotency_key, lock=True)
            if prior is not None:
                if prior.request_digest != request_digest or prior.status != "completed": raise RetentionConflict()
                row = uow.retention.get_recovery(organization_id=organization_id, recovery_id=UUID(prior.safe_result["recovery_id"]))
                if row is None: raise RetentionConflict()
                return RetentionRecoveryResponseV1(recovery_id=row.id, status=row.status, requested_at=row.requested_at, completed_at=row.completed_at, expected_digest=row.expected_digest, verified_digest=row.verified_digest)
            reservation = uow.idempotency.reserve(organization_id=organization_id, actor_user_id=actor_id, operation="CreateRetentionRecovery", idempotency_key=idempotency_key, request_digest=request_digest, created_at=now, updated_at=now)
            stream = None if self.recovery_resolver is None else self.recovery_resolver.resolve_authorized(subject=subject, expected_digest=expected_digest)
            status = RecoveryStatus.TEMPORARILY_UNAVAILABLE.value
            verified_digest = None
            if stream is not None and expected_digest is not None:
                from hashlib import sha256 as _sha256
                digest = _sha256(); total = 0
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk: break
                    total += len(chunk)
                    if total > 26_214_400: raise RetentionInvalidRequest()
                    digest.update(chunk)
                verified_digest = digest.hexdigest()
                if verified_digest != expected_digest: raise RetentionIndeterminate()
                status = RecoveryStatus.NOT_REQUIRED.value
            row = RetentionRecovery(id=uuid4(), organization_id=organization_id, project_id=subject.project_id, workspace_id=subject.workspace_id, subject_kind=subject.subject_kind.value, subject_id=subject.subject_id, requested_by_user_id=actor_id, status=status, requested_at=now, completed_at=now, expected_digest=expected_digest, verified_digest=verified_digest, failure_code=None if verified_digest else "content_unavailable", request_digest=request_digest)
            uow.retention.add(row)
            _record_transport_event(uow=uow, subject=subject, actor_id=actor_id, action="RETENTION_RECOVERY_REQUESTED", aggregate_kind="retention_recovery", aggregate_id=row.id, status_code="requested", correlation_id=correlation_id, occurred_at=now)
            terminal_action = "RETENTION_RECOVERY_COMPLETED" if verified_digest is not None else "RETENTION_RECOVERY_UNAVAILABLE"
            _record_transport_event(uow=uow, subject=subject, actor_id=actor_id, action=terminal_action, aggregate_kind="retention_recovery", aggregate_id=row.id, status_code=row.status, correlation_id=correlation_id, occurred_at=row.completed_at)
            uow.retention.flush()
            uow.idempotency.complete(reservation, safe_result={"outcome":"success", "recovery_id":str(row.id), "status":row.status, "correlation_id":str(correlation_id)}, completed_at=now)
            uow.commit()
            return RetentionRecoveryResponseV1(recovery_id=row.id, status=row.status, requested_at=row.requested_at, completed_at=row.completed_at, expected_digest=row.expected_digest, verified_digest=row.verified_digest)

    def get_recovery_status(self, *, organization_id: UUID, actor_id: int, recovery_id: UUID) -> RetentionRecoveryResponseV1:
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_actor(actor_id=actor_id, organization_id=organization_id): raise RetentionProtectedNotFound()
            row = uow.retention.get_recovery(organization_id=organization_id, recovery_id=recovery_id)
            if row is None: raise RetentionProtectedNotFound()
            self._authorized_subject(uow, organization_id=organization_id, actor_id=actor_id, subject_kind=row.subject_kind, subject_id=row.subject_id, mutation=False)
            return RetentionRecoveryResponseV1(recovery_id=row.id, status=row.status, requested_at=row.requested_at, completed_at=row.completed_at, expected_digest=row.expected_digest, verified_digest=row.verified_digest)

    def release_hold(
        self,
        *,
        organization_id: UUID,
        actor_id: int,
        subject_kind: str,
        subject_id: UUID,
        hold_id: UUID,
        data: ReleaseRetentionHoldRequestV1,
        idempotency_key: UUID,
        correlation_id: UUID,
        authority_context: str = "human",
    ) -> RetentionMutationResponseV1:
        operation = "ReleaseRetentionHold"
        if authority_context != "human":
            raise RetentionNotPermitted()
        now = self.clock.now()

        request_digest = sha256_digest({
            "operation": operation,
            "organization_id": organization_id,
            "subject_kind": subject_kind,
            "subject_id": subject_id,
            "hold_id": hold_id,
            "release_rationale": data.release_rationale,
            "expected_version": data.expected_version,
        })

        with self.uow_factory() as uow:
            subject, _ = self._authorized_subject(
                uow,
                organization_id=organization_id,
                actor_id=actor_id,
                subject_kind=subject_kind,
                subject_id=subject_id,
                mutation=True,
                lock=True,
            )

            prior = uow.idempotency.get(
                organization_id=organization_id,
                actor_id=actor_id,
                operation=operation,
                idempotency_key=idempotency_key,
                lock=True,
            )
            if prior is not None:
                if prior.request_digest != request_digest:
                    raise RetentionConflict()
                if prior.status != "completed" or prior.safe_result is None:
                    raise RetentionConflict()

                try:
                    replay_hold_id = UUID(
                        prior.safe_result["hold_id"]
                    )
                    replay_hold_version = int(
                        prior.safe_result["hold_version"]
                    )
                    replay_record_id = UUID(
                        prior.safe_result["retention_record_id"]
                    )
                    replay_eligibility = DispositionEligibility(
                        prior.safe_result["disposition_eligibility"]
                    )
                    replay_decision = DispositionDecision(
                        prior.safe_result["disposition_decision"]
                    )
                except (KeyError, TypeError, ValueError):
                    raise RetentionConflict() from None

                released = uow.retention.get_hold_revision(
                    subject=subject,
                    hold_id=replay_hold_id,
                    version=replay_hold_version,
                )
                if (
                    released is None
                    or released.status != HoldStatus.RELEASED.value
                    or released.hold_id != replay_hold_id
                    or replay_hold_id != hold_id
                    or released.version != replay_hold_version
                ):
                    raise RetentionConflict()

                record = uow.retention.get_record_by_id(
                    subject=subject,
                    record_id=replay_record_id,
                )
                if record is None:
                    raise RetentionConflict()

                try:
                    replay_mode = RetentionMode(record.mode)
                    replay_source = RetentionPolicySource(
                        record.policy_source
                    )
                except (TypeError, ValueError):
                    raise RetentionConflict() from None

                return RetentionMutationResponseV1(
                    outcome="success",
                    state=RetentionStateResponseV1(
                        retention_record_id=record.id,
                        subject=_subject_response(subject),
                        retention_mode=replay_mode,
                        retention_until=record.retain_until,
                        policy_basis_code=record.basis_code,
                        basis_rationale=record.rationale,
                        policy_source=replay_source,
                        hold_status=None,
                        active_hold_id=None,
                        disposition_eligibility=replay_eligibility,
                        disposition_decision=replay_decision,
                        version=record.version,
                        predecessor_record_id=record.supersedes_id,
                        record_digest=record.record_digest,
                    ),
                )

            active = uow.retention.get_active_hold(
                subject=subject,
                lock=True,
            )
            if (
                active is None
                or active.hold_id != hold_id
                or active.version != data.expected_version
            ):
                raise RetentionConflict()

            current = uow.retention.get_current_record(
                subject=subject,
                lock=True,
            )
            if current is None:
                raise RetentionConflict()

            reservation = uow.idempotency.reserve(
                organization_id=organization_id,
                actor_user_id=actor_id,
                operation=operation,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )

            successor_row_id = uuid4()
            successor_version = active.version + 1

            successor_digest = sha256_digest({
                "row_id": successor_row_id,
                "hold_id": active.hold_id,
                "subject": subject,
                "status": HoldStatus.RELEASED,
                "reason_code": active.reason_code,
                "rationale": active.rationale,
                "authority_reference": active.authority_reference,
                "placed_by_user_id": active.placed_by_user_id,
                "placed_at": active.placed_at,
                "released_by_user_id": actor_id,
                "released_at": now,
                "release_rationale": data.release_rationale,
                "version": successor_version,
                "predecessor_row_id": active.row_id,
            })

            if not uow.retention.close_hold_revision(
                row_id=active.row_id,
                expected_version=active.version,
            ):
                raise RetentionConflict()

            released = RetentionHold(
                row_id=successor_row_id,
                hold_id=active.hold_id,
                organization_id=active.organization_id,
                project_id=active.project_id,
                workspace_id=active.workspace_id,
                subject_kind=active.subject_kind,
                subject_id=active.subject_id,
                status=HoldStatus.RELEASED.value,
                reason_code=active.reason_code,
                rationale=active.rationale,
                authority_reference=active.authority_reference,
                placed_by_user_id=active.placed_by_user_id,
                placed_at=active.placed_at,
                released_by_user_id=actor_id,
                released_at=now,
                release_rationale=data.release_rationale,
                version=successor_version,
                predecessor_row_id=active.row_id,
                digest=successor_digest,
                is_current=True,
            )
            uow.retention.add(released)

            try:
                uow.retention.flush()
            except IntegrityError as exc:
                raise RetentionConflict() from exc

            decision = uow.retention.get_latest_decision(
                retention_record_id=current.id
            )

            response = RetentionMutationResponseV1(
                outcome="success",
                state=_state_response(
                    subject=subject,
                    record=current,
                    active_hold=None,
                    decision=decision,
                    now=now,
                ),
            )

            _record_hold_event(
                uow=uow,
                subject=subject,
                actor_id=actor_id,
                action="RETENTION_HOLD_RELEASED",
                hold_id=released.hold_id,
                hold_version=released.version,
                hold_digest=released.digest,
                correlation_id=correlation_id,
                occurred_at=now,
            )

            uow.idempotency.complete(
                reservation,
                safe_result=_safe_hold_result(
                    response,
                    hold_id=released.hold_id,
                    hold_version=released.version,
                    correlation_id=correlation_id,
                ),
                completed_at=now,
            )
            uow.commit()
            return response

    def place_hold(
        self,
        *,
        organization_id: UUID,
        actor_id: int,
        subject_kind: str,
        subject_id: UUID,
        data: PlaceRetentionHoldRequestV1,
        idempotency_key: UUID,
        correlation_id: UUID,
        authority_context: str = "human",
    ) -> RetentionMutationResponseV1:
        operation = "PlaceRetentionHold"
        if authority_context != "human":
            raise RetentionNotPermitted()
        now = self.clock.now()

        request_digest = sha256_digest({
            "operation": operation,
            "organization_id": organization_id,
            "subject_kind": subject_kind,
            "subject_id": subject_id,
            "reason_code": data.reason_code,
            "rationale": data.rationale,
            "authority_reference": data.authority_reference,
            "expected_version": data.expected_version,
        })

        with self.uow_factory() as uow:
            subject, _ = self._authorized_subject(
                uow,
                organization_id=organization_id,
                actor_id=actor_id,
                subject_kind=subject_kind,
                subject_id=subject_id,
                mutation=True,
                lock=True,
            )

            prior = uow.idempotency.get(
                organization_id=organization_id,
                actor_id=actor_id,
                operation=operation,
                idempotency_key=idempotency_key,
                lock=True,
            )
            if prior is not None:
                if prior.request_digest != request_digest:
                    raise RetentionConflict()
                if prior.status != "completed" or prior.safe_result is None:
                    raise RetentionConflict()

                safe_hold_id = prior.safe_result.get("hold_id")
                try:
                    replay_hold_id = UUID(safe_hold_id)
                except (TypeError, ValueError):
                    raise RetentionConflict() from None

                if prior.safe_result.get("hold_version") != 1:
                    raise RetentionConflict()

                hold = uow.retention.get_hold_revision(
                    subject=subject,
                    hold_id=replay_hold_id,
                    version=1,
                )
                if (
                    hold is None
                    or hold.hold_id != replay_hold_id
                    or hold.version != 1
                ):
                    raise RetentionConflict()

                try:
                    replay_record_id = UUID(
                        prior.safe_result["retention_record_id"]
                    )
                    replay_decision = DispositionDecision(
                        prior.safe_result["disposition_decision"]
                    )
                except (KeyError, TypeError, ValueError):
                    raise RetentionConflict() from None

                record = uow.retention.get_record_by_id(
                    subject=subject,
                    record_id=replay_record_id,
                )
                if record is None:
                    raise RetentionConflict()

                try:
                    replay_mode = RetentionMode(record.mode)
                    replay_source = RetentionPolicySource(
                        record.policy_source
                    )
                except (TypeError, ValueError):
                    raise RetentionConflict() from None

                return RetentionMutationResponseV1(
                    outcome="success",
                    state=RetentionStateResponseV1(
                        retention_record_id=record.id,
                        subject=_subject_response(subject),
                        retention_mode=replay_mode,
                        retention_until=record.retain_until,
                        policy_basis_code=record.basis_code,
                        basis_rationale=record.rationale,
                        policy_source=replay_source,
                        hold_status=HoldStatus.ACTIVE,
                        active_hold_id=replay_hold_id,
                        disposition_eligibility=(
                            DispositionEligibility.BLOCKED_BY_HOLD
                        ),
                        disposition_decision=replay_decision,
                        version=record.version,
                        predecessor_record_id=record.supersedes_id,
                        record_digest=record.record_digest,
                    ),
                )

            current = uow.retention.get_current_record(
                subject=subject,
                lock=True,
            )
            if (
                current is None
                or current.version != data.expected_version
            ):
                raise RetentionConflict()

            if uow.retention.get_active_hold(
                subject=subject,
                lock=True,
            ) is not None:
                raise RetentionConflict()

            reservation = uow.idempotency.reserve(
                organization_id=organization_id,
                actor_user_id=actor_id,
                operation=operation,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )

            hold_id = uuid4()
            row_id = uuid4()
            hold_version = 1

            hold_digest = sha256_digest({
                "row_id": row_id,
                "hold_id": hold_id,
                "subject": subject,
                "status": HoldStatus.ACTIVE,
                "reason_code": data.reason_code,
                "rationale": data.rationale,
                "authority_reference": data.authority_reference,
                "placed_by_user_id": actor_id,
                "placed_at": now,
                "released_by_user_id": None,
                "released_at": None,
                "release_rationale": None,
                "version": hold_version,
                "predecessor_row_id": None,
            })

            hold = RetentionHold(
                row_id=row_id,
                hold_id=hold_id,
                organization_id=subject.organization_id,
                project_id=subject.project_id,
                workspace_id=subject.workspace_id,
                subject_kind=subject.subject_kind.value,
                subject_id=subject.subject_id,
                status=HoldStatus.ACTIVE.value,
                reason_code=data.reason_code,
                rationale=data.rationale,
                authority_reference=data.authority_reference,
                placed_by_user_id=actor_id,
                placed_at=now,
                released_by_user_id=None,
                released_at=None,
                release_rationale=None,
                version=hold_version,
                predecessor_row_id=None,
                digest=hold_digest,
                is_current=True,
            )
            uow.retention.add(hold)
            try:
                uow.retention.flush()
            except IntegrityError as exc:
                raise RetentionConflict() from exc

            decision = uow.retention.get_latest_decision(
                retention_record_id=current.id
            )

            response = RetentionMutationResponseV1(
                outcome="success",
                state=_state_response(
                    subject=subject,
                    record=current,
                    active_hold=hold,
                    decision=decision,
                    now=now,
                ),
            )

            _record_hold_event(
                uow=uow,
                subject=subject,
                actor_id=actor_id,
                action="RETENTION_HOLD_PLACED",
                hold_id=hold.hold_id,
                hold_version=hold.version,
                hold_digest=hold.digest,
                correlation_id=correlation_id,
                occurred_at=now,
            )

            uow.idempotency.complete(
                reservation,
                safe_result=_safe_hold_result(
                    response,
                    hold_id=hold.hold_id,
                    hold_version=hold.version,
                    correlation_id=correlation_id,
                ),
                completed_at=now,
            )
            uow.commit()
            return response

    def materialize_default_policy(
        self,
        *,
        organization_id: UUID,
        actor_id: int,
        subject_kind: str,
        subject_id: UUID,
        idempotency_key: UUID,
        correlation_id: UUID,
    ) -> RetentionMutationResponseV1:
        """Materialize the Commercial-V1 fail-safe platform default.

        Legacy reads remain unestablished; this is an explicit governed mutation.
        No Organization-default provider is fabricated by PATCH-055.
        """
        return self.apply_policy(
            organization_id=organization_id,
            actor_id=actor_id,
            subject_kind=subject_kind,
            subject_id=subject_id,
            data=ApplyRetentionPolicyRequestV1(
                retention_mode=RetentionMode.RETAIN_INDEFINITELY,
                retention_until=None,
                policy_source=RetentionPolicySource.PLATFORM_DEFAULT,
                basis_code="platform.default",
                rationale="Commercial V1 fail-safe retention default",
                expected_version=0,
            ),
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def apply_policy(
        self,
        *,
        organization_id: UUID,
        actor_id: int,
        subject_kind: str,
        subject_id: UUID,
        data: ApplyRetentionPolicyRequestV1,
        idempotency_key: UUID,
        correlation_id: UUID,
    ) -> RetentionMutationResponseV1:
        operation = "ApplyRetentionPolicy"
        now = self.clock.now()

        request_digest = sha256_digest({
            "operation": operation,
            "organization_id": organization_id,
            "subject_kind": subject_kind,
            "subject_id": subject_id,
            "retention_mode": data.retention_mode,
            "retention_until": data.retention_until,
            "policy_source": data.policy_source,
            "basis_code": data.basis_code,
            "rationale": data.rationale,
            "expected_version": data.expected_version,
        })

        if (
            data.retention_mode is RetentionMode.RETAIN_UNTIL
            and data.retention_until is not None
            and data.retention_until.astimezone(timezone.utc)
            < now.astimezone(timezone.utc)
        ):
            raise RetentionInvalidRequest(
                "retention_until must not precede the authoritative clock"
            )

        with self.uow_factory() as uow:
            subject, _ = self._authorized_subject(
                uow,
                organization_id=organization_id,
                actor_id=actor_id,
                subject_kind=subject_kind,
                subject_id=subject_id,
                mutation=True,
                lock=True,
            )

            prior = uow.idempotency.get(
                organization_id=organization_id,
                actor_id=actor_id,
                operation=operation,
                idempotency_key=idempotency_key,
                lock=True,
            )
            if prior is not None:
                if prior.request_digest != request_digest:
                    raise RetentionConflict()
                if prior.status != "completed" or prior.safe_result is None:
                    raise RetentionConflict()

                safe_record_id = prior.safe_result.get(
                    "retention_record_id"
                )
                try:
                    replay_record_id = UUID(safe_record_id)
                except (TypeError, ValueError):
                    raise RetentionConflict() from None

                replay_record = uow.retention.get_record_by_id(
                    subject=subject,
                    record_id=replay_record_id,
                )
                return _replay_policy_response(
                    subject=subject,
                    record=replay_record,
                    safe=prior.safe_result,
                )

            current = uow.retention.get_current_record(
                subject=subject,
                lock=True,
            )

            if current is None:
                if data.expected_version != 0:
                    raise RetentionConflict()
                next_version = 1
                predecessor_id = None
                action = "RETENTION_POLICY_APPLIED"
                event_type = "RETENTION_POLICY_APPLIED"
            else:
                if current.version != data.expected_version:
                    raise RetentionConflict()
                next_version = current.version + 1
                predecessor_id = current.id
                action = "RETENTION_POLICY_REPLACED"
                event_type = "RETENTION_POLICY_REPLACED"

            reservation = uow.idempotency.reserve(
                organization_id=organization_id,
                actor_user_id=actor_id,
                operation=operation,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )

            record_id = uuid4()
            digest_payload = {
                "retention_record_id": record_id,
                "subject": subject,
                "version": next_version,
                "retention_mode": data.retention_mode,
                "retention_until": data.retention_until,
                "policy_source": data.policy_source,
                "basis_code": data.basis_code,
                "rationale": data.rationale,
                "created_by_user_id": actor_id,
                "created_at": now,
                "supersedes_id": predecessor_id,
                "request_digest": request_digest,
            }
            record_digest = sha256_digest(digest_payload)

            if current is not None and not uow.retention.close_current_record(
                record_id=current.id,
                expected_version=current.version,
            ):
                raise RetentionConflict()

            record = RetentionRecord(
                id=record_id,
                organization_id=subject.organization_id,
                project_id=subject.project_id,
                workspace_id=subject.workspace_id,
                subject_kind=subject.subject_kind.value,
                subject_id=subject.subject_id,
                version=next_version,
                is_current=True,
                mode=data.retention_mode.value,
                retain_until=data.retention_until,
                policy_source=data.policy_source.value,
                basis_code=data.basis_code,
                rationale=data.rationale,
                created_by_user_id=actor_id,
                created_at=now,
                supersedes_id=predecessor_id,
                request_digest=request_digest,
                record_digest=record_digest,
            )
            uow.retention.add(record)
            uow.retention.flush()

            active_hold = uow.retention.get_active_hold(
                subject=subject,
                lock=True,
            )

            response = RetentionMutationResponseV1(
                outcome="success",
                state=_state_response(
                    subject=subject,
                    record=record,
                    active_hold=active_hold,
                    decision=None,
                    now=now,
                ),
            )

            _record_governance_event(
                uow=uow,
                subject=subject,
                actor_id=actor_id,
                action=action,
                aggregate_id=record.id,
                aggregate_version=record.version,
                event_type=event_type,
                record_digest=record.record_digest,
                correlation_id=correlation_id,
                occurred_at=now,
            )

            uow.idempotency.complete(
                reservation,
                safe_result=_safe_result(
                    response,
                    correlation_id=correlation_id,
                ),
                completed_at=now,
            )
            uow.commit()
            return response

    def record_disposition_decision(
        self, *, organization_id: UUID, actor_id: int, subject_kind: str,
        subject_id: UUID, data: RecordDispositionDecisionRequestV1,
        idempotency_key: UUID, correlation_id: UUID,
    ) -> RetentionMutationResponseV1:
        operation = "RecordDispositionDecision"
        now = self.clock.now()

        request_digest = sha256_digest({
            "operation": operation, "organization_id": organization_id,
            "subject_kind": subject_kind, "subject_id": subject_id,
            "decision": data.decision, "reason": data.reason,
            "retention_record_id": data.retention_record_id,
            "subject_version_snapshot": data.subject_version_snapshot,
            "expected_version": data.expected_version,
        })

        with self.uow_factory() as uow:
            subject, subject_version = self._authorized_subject(
                uow, organization_id=organization_id, actor_id=actor_id,
                subject_kind=subject_kind, subject_id=subject_id,
                mutation=True, lock=True,
            )

            prior = uow.idempotency.get(
                organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key, lock=True,
            )
            if prior is not None:
                if prior.request_digest != request_digest:
                    raise RetentionConflict()
                if prior.status != "completed" or prior.safe_result is None:
                    raise RetentionConflict()
                safe_record_id = prior.safe_result.get("retention_record_id")
                try:
                    replay_record_id = UUID(safe_record_id)
                except (TypeError, ValueError):
                    raise RetentionConflict() from None
                replay_record = uow.retention.get_record_by_id(subject=subject, record_id=replay_record_id)
                if replay_record is None:
                    raise RetentionConflict()
                replay_decision = uow.retention.get_decision_by_request_digest(retention_record_id=replay_record.id, request_digest=request_digest)
                if replay_decision is None or replay_decision.request_digest != request_digest:
                    raise RetentionConflict()
                active_hold = uow.retention.get_active_hold(subject=subject, lock=False)
                return RetentionMutationResponseV1(
                    outcome="success",
                    state=_state_response(subject=subject, record=replay_record, active_hold=active_hold, decision=replay_decision, now=now),
                )

            current = uow.retention.get_current_record(subject=subject, lock=True)
            if current is None:
                raise RetentionConflict()
            if current.id != data.retention_record_id or current.version != data.expected_version:
                raise RetentionConflict()
            if subject_version != data.subject_version_snapshot:
                raise RetentionConflict()

            active_hold = uow.retention.get_active_hold(subject=subject, lock=True)
            eligibility = _eligibility(current, active_hold, now)
            if data.decision == "approve_disposition" and eligibility is not DispositionEligibility.ELIGIBLE:
                raise RetentionInvalidRequest("approve_disposition requires currently eligible state")

            reservation = uow.idempotency.reserve(
                organization_id=organization_id, actor_user_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                request_digest=request_digest,
            )

            decision_row = RetentionDispositionDecision(
                id=uuid4(), organization_id=subject.organization_id,
                project_id=subject.project_id, workspace_id=subject.workspace_id,
                subject_kind=subject.subject_kind.value, subject_id=subject.subject_id,
                retention_record_id=current.id, eligibility_snapshot=eligibility.value,
                decision=data.decision, reason=data.reason,
                decided_by_user_id=actor_id, decided_at=now,
                subject_version_snapshot=data.subject_version_snapshot,
                request_digest=request_digest,
            )
            uow.retention.add(decision_row)
            try:
                uow.retention.flush()
            except IntegrityError:
                raise RetentionConflict() from None

            response = RetentionMutationResponseV1(
                outcome="success",
                state=_state_response(subject=subject, record=current, active_hold=active_hold, decision=decision_row, now=now),
            )

            _record_governance_event(
                uow=uow, subject=subject, actor_id=actor_id,
                action="RETENTION_DISPOSITION_DECISION_RECORDED",
                aggregate_id=decision_row.id, aggregate_version=1,
                event_type="RETENTION_DISPOSITION_DECISION_RECORDED",
                record_digest=current.record_digest,
                aggregate_kind="retention_disposition_decision",
                correlation_id=correlation_id, occurred_at=now,
            )

            uow.idempotency.complete(
                reservation,
                safe_result=_safe_result(response, correlation_id=correlation_id),
                completed_at=now,
            )
            uow.commit()
            return response


    def get_evidence_workbench(self, *, organization_id: UUID, actor_id: int, project_id: int, workspace_id: int | None, limit: int = 20) -> EvidenceWorkbenchResponseV1:
        if not 1 <= limit <= 100: raise RetentionInvalidRequest()
        with self.uow_factory() as uow:
            if not uow.authorization.authorize_workbench(actor_id=actor_id, organization_id=organization_id, project_id=project_id, workspace_id=workspace_id): raise RetentionProtectedNotFound()
            rows = uow.retention.list_workbench_evidence(organization_id=organization_id, project_id=project_id, workspace_id=workspace_id, limit=limit)
            items = []
            for row in rows:
                subject = RetentionSubject(RetentionSubjectKind.EVIDENCE, row.id, organization_id, project_id, row.workspace_id)
                if not uow.authorization.authorize_read(actor_id=actor_id, subject=subject): continue
                record = uow.retention.get_current_record(subject=subject); hold = uow.retention.get_active_hold(subject=subject)
                decision = None if record is None else uow.retention.get_latest_decision(retention_record_id=record.id)
                state = _state_response(subject=subject, record=record, active_hold=hold, decision=decision, now=self.clock.now())
                predecessor_rows = uow.retention.list_workbench_predecessors(organization_id=organization_id, project_id=project_id, workspace_id=row.workspace_id, evidence_id=row.id, limit=32)
                predecessors = tuple(x.id for x in predecessor_rows if uow.authorization.authorize_read(actor_id=actor_id, subject=RetentionSubject(RetentionSubjectKind.EVIDENCE, x.id, organization_id, project_id, x.workspace_id)))
                replacement = uow.retention.get_workbench_replacement(organization_id=organization_id, project_id=project_id, workspace_id=row.workspace_id, replacement_evidence_id=row.replacement_evidence_id)
                replacement_id = replacement.id if replacement is not None and uow.authorization.authorize_read(actor_id=actor_id, subject=RetentionSubject(RetentionSubjectKind.EVIDENCE, replacement.id, organization_id, project_id, replacement.workspace_id)) else None
                reliance = tuple(EvidenceWorkbenchRelianceV1(report_id=report.id, evidence_version=entry.evidence_version, report_version=report.version, accepted_at=report.accepted_at) for entry, report in uow.retention.list_accepted_report_reliance(organization_id=organization_id, project_id=project_id, workspace_id=row.workspace_id, evidence_id=row.id) if entry.evidence_version is not None and report.accepted_at is not None)
                items.append(EvidenceWorkbenchEvidenceV1(evidence_id=row.id,lifecycle=row.lifecycle,source_standing=row.source_standing,supported_fact=row.supported_fact,version=row.version,replacement_evidence_id=replacement_id,predecessor_evidence_ids=predecessors,reliance=reliance,retention_state=state))
            files = tuple(EvidenceWorkbenchFileV1(asset_id=x.id,safe_filename=x.safe_filename,lifecycle=x.lifecycle,version=x.version) for x in uow.retention.list_workbench_files(organization_id=organization_id,project_id=project_id,workspace_id=workspace_id,limit=min(limit,50)))
            return EvidenceWorkbenchResponseV1(project_id=project_id,workspace_id=workspace_id,evidence=tuple(items),supporting_files=files,visible_count=len(items))

    def get_state(
        self,
        *,
        organization_id: UUID,
        actor_id: int,
        subject_kind: str,
        subject_id: UUID,
    ) -> RetentionStateResponseV1:
        with self.uow_factory() as uow:
            subject, _ = self._authorized_subject(
                uow,
                organization_id=organization_id,
                actor_id=actor_id,
                subject_kind=subject_kind,
                subject_id=subject_id,
                mutation=False,
            )
            record = uow.retention.get_current_record(subject=subject)
            active_hold = uow.retention.get_active_hold(subject=subject)
            decision = (
                None
                if record is None
                else uow.retention.get_latest_decision(
                    retention_record_id=record.id
                )
            )
            return _state_response(
                subject=subject,
                record=record,
                active_hold=active_hold,
                decision=decision,
                now=self.clock.now(),
            )

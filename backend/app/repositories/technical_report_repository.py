"""No-commit SQLAlchemy repository for PATCH-032 Technical Reports."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import null, update
from sqlalchemy.orm import Session

from app.enums.technical_report import (
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportPurpose,
)
from app.exceptions.technical_report import TechnicalReportValidationError
from app.models.technical_report import (
    TechnicalReport,
    TechnicalReportProvenanceRecord,
    TechnicalReportRecord,
)
from app.models.technical_report_command import (
    ContextualLocator,
    ExternalHumanLocator,
    PreliminaryQualification,
    StandardLocator,
    TechnicalReportAcceptanceRecord,
    TechnicalReportAcceptedSnapshot,
    TechnicalReportContent,
    TechnicalReportDraftRevision,
    TechnicalReportProvenanceEntry,
    _locator_from_payload,
    _provenance_from_payload,
    accepted_snapshot_payload,
    canonical_json,
    validate_accepted_snapshot_payload,
)
from app.ports.technical_report import (
    TechnicalReportReadCriteria,
    TechnicalReportReadItem,
    TechnicalReportReadPage,
)


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _uuid(value: str | None) -> UUID | None:
    return None if value is None else UUID(value)


def _snapshot(payload: object, digest: str) -> TechnicalReportAcceptedSnapshot:
    """Validate and reconstruct the immutable accepted representation."""

    value = validate_accepted_snapshot_payload(payload, digest)
    content = value["content"]
    qualification = value["qualification"]
    revision = value["accepted_draft_revision"]
    return TechnicalReportAcceptedSnapshot(
        report_id=UUID(value["report_id"]),
        purpose=value["purpose"],
        organization_id=UUID(value["organization_id"]),
        workspace_id=value["workspace_id"],
        project_id=value["project_id"],
        content=TechnicalReportContent(
            engineering_scope=content["engineering_scope"],
            technical_content=content["technical_content"],
            assumptions=tuple(content["assumptions"]),
            uncertainty=content["uncertainty"],
            limitations=tuple(content["limitations"]),
            conclusions=content["conclusions"],
            recommendations=tuple(content["recommendations"]),
        ),
        qualification=PreliminaryQualification(
            qualification["is_preliminary"],
            tuple(qualification["evidence_deficiencies"]),
            tuple(qualification["unresolved_issues"]),
            tuple(qualification["follow_up_requirements"]),
        ),
        provenance=tuple(_provenance_from_payload(item) for item in value["provenance"]),
        accepted_draft_revision=TechnicalReportDraftRevision(
            UUID(revision["revision_id"]), revision["revision_number"]
        ),
        accepted_aggregate_version=value["accepted_aggregate_version"],
        accepted_by_id=value["accepted_by_id"],
        accepted_at=_utc(value["accepted_at"]),
        predecessor_report_id=_uuid(value["predecessor_report_id"]),
    )


def _locator_payload(locator: object) -> dict[str, object]:
    value = json.loads(canonical_json(locator))
    if not isinstance(value, dict):
        raise TechnicalReportValidationError("provenance locator is invalid")
    return value


def _record_for_entry(report_id: UUID, entry: TechnicalReportProvenanceEntry) -> TechnicalReportProvenanceRecord:
    locator = entry.locator
    payload = _locator_payload(locator)
    values: dict[str, object] = {
        "id": entry.entry_id,
        "technical_report_id": report_id,
        "ordinal": entry.ordinal,
        "source_class": entry.source_class.value,
        "source_type": entry.source_type.value,
        "is_material": entry.is_material,
        "owning_capability": None if entry.owning_capability is None else entry.owning_capability.value,
        "reliance_role": entry.reliance_role,
        "verification_status": entry.verification_status.value,
        "availability_status": entry.availability_status.value,
        "origin_attribution": entry.origin_attribution,
        "limitations": list(entry.limitations),
        "integrity_algorithm": None if entry.integrity_algorithm is None else entry.integrity_algorithm.value,
        "integrity_digest": entry.integrity_digest,
        "minimal_historical_representation": null(),
    }
    if entry.source_type.value in {
        "universal_capture", "evidence", "engineering_object", "engineering_relationship"
    }:
        values["minimal_historical_representation"] = payload
        identity = {
            "universal_capture": ("capture_id", "capture_version", "capture_id"),
            "evidence": ("evidence_id", "evidence_version", "evidence_id"),
            "engineering_object": ("engineering_object_id", "engineering_object_version", "engineering_object_id"),
            "engineering_relationship": ("engineering_relationship_id", "engineering_relationship_version", "engineering_relationship_id"),
        }[entry.source_type.value]
        values[identity[0]] = UUID(payload[identity[2]])
        values[identity[1]] = payload["source_version"]
    elif isinstance(locator, ExternalHumanLocator):
        values.update(
            report_local_source_id=locator.report_local_source_id,
            external_reference=locator.external_reference,
            submitted_by_id=locator.submitted_by_id,
            observed_at=locator.observed_at,
            retrieved_at=locator.retrieved_at,
            submitted_at=locator.submitted_at,
            minimal_historical_representation=payload,
        )
    elif isinstance(locator, StandardLocator):
        values.update(
            standard_identity=locator.standard_identity,
            issuing_authority=locator.issuing_authority,
            edition=locator.edition,
            clause_or_location=locator.clause_or_location,
            retrieved_at=locator.retrieved_at,
            minimal_historical_representation=payload,
        )
    elif isinstance(locator, ContextualLocator):
        values.update(context_id=locator.context_id, owning_context=locator.owning_context)
    else:
        raise TechnicalReportValidationError("unsupported provenance locator")
    return TechnicalReportProvenanceRecord(**values)


def _entry_from_record(record: TechnicalReportProvenanceRecord) -> TechnicalReportProvenanceEntry:
    if record.source_type == "contextual":
        locator_payload: object = {
            "context_id": str(record.context_id), "owning_context": record.owning_context
        }
    else:
        locator_payload = record.minimal_historical_representation
    locator = _locator_from_payload(locator_payload, record.source_type)
    return TechnicalReportProvenanceEntry(
        entry_id=record.id,
        ordinal=record.ordinal,
        source_class=record.source_class,
        source_type=record.source_type,
        is_material=record.is_material,
        owning_capability=record.owning_capability,
        reliance_role=record.reliance_role,
        verification_status=record.verification_status,
        availability_status=record.availability_status,
        origin_attribution=record.origin_attribution,
        limitations=tuple(record.limitations),
        locator=locator,
        integrity_algorithm=(
            None if record.integrity_algorithm is None
            else TechnicalReportIntegrityAlgorithm(record.integrity_algorithm)
        ),
        integrity_digest=record.integrity_digest,
    )


class SqlAlchemyTechnicalReportRepository:
    """Persist complete aggregates without authorization or transaction ownership."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, report: TechnicalReport) -> None:
        root = self._root_from_aggregate(report)
        self.session.add(root)
        self.session.flush()
        self.session.add_all([_record_for_entry(report.id, item) for item in report.provenance])
        self.session.flush()

    def get_scoped(self, report_id: UUID, organization_id: UUID) -> TechnicalReport | None:
        root = self.session.query(TechnicalReportRecord).filter_by(
            id=report_id, organization_id=organization_id
        ).first()
        return None if root is None else self._aggregate(root)

    def list_scoped(self, criteria: TechnicalReportReadCriteria) -> TechnicalReportReadPage:
        query = self.session.query(TechnicalReportRecord).filter_by(
            organization_id=criteria.scope.organization_id,
            workspace_id=criteria.scope.workspace_id,
        )
        if criteria.scope.project_id is not None:
            query = query.filter(
                TechnicalReportRecord.project_id == criteria.scope.project_id
            )
        if criteria.purpose is not None:
            query = query.filter(
                TechnicalReportRecord.purpose == criteria.purpose.value
            )
        if criteria.lifecycle is not None:
            query = query.filter(
                TechnicalReportRecord.lifecycle == criteria.lifecycle.value
            )
        total = query.count()
        roots = query.order_by(
            TechnicalReportRecord.updated_at.desc(), TechnicalReportRecord.id.desc()
        ).offset((criteria.page - 1) * criteria.size).limit(criteria.size).all()
        return TechnicalReportReadPage(
            tuple(TechnicalReportReadItem(item.id, item.version) for item in roots),
            total,
            criteria.page,
            criteria.size,
        )

    def list_successors_scoped(
        self, predecessor_id: UUID, criteria: TechnicalReportReadCriteria
    ) -> TechnicalReportReadPage:
        query = self.session.query(TechnicalReportRecord).filter_by(
            predecessor_report_id=predecessor_id,
            organization_id=criteria.scope.organization_id,
            workspace_id=criteria.scope.workspace_id,
            project_id=criteria.scope.project_id,
        )
        total = query.count()
        roots = query.order_by(
            TechnicalReportRecord.created_at.asc(), TechnicalReportRecord.id.asc()
        ).offset((criteria.page - 1) * criteria.size).limit(criteria.size).all()
        return TechnicalReportReadPage(
            tuple(TechnicalReportReadItem(item.id, item.version) for item in roots),
            total,
            criteria.page,
            criteria.size,
        )

    def provenance_for_report(self, report_id: UUID) -> tuple[TechnicalReportProvenanceEntry, ...]:
        rows = self.session.query(TechnicalReportProvenanceRecord).filter_by(
            technical_report_id=report_id
        ).order_by(TechnicalReportProvenanceRecord.ordinal).all()
        entries = tuple(_entry_from_record(row) for row in rows)
        if [entry.ordinal for entry in entries] != list(range(len(entries))):
            raise TechnicalReportValidationError("persisted provenance ordinals are incoherent")
        return entries

    def persist_draft_expected_version(self, report: TechnicalReport, expected_version: int) -> bool:
        if report.lifecycle is not TechnicalReportLifecycle.DRAFT:
            raise TechnicalReportValidationError("draft persistence requires draft state")
        values = self._mutable_values(report)
        result = self.session.execute(
            update(TechnicalReportRecord).where(
                TechnicalReportRecord.id == report.id,
                TechnicalReportRecord.organization_id == report.organization_id,
                TechnicalReportRecord.version == expected_version,
                TechnicalReportRecord.lifecycle == TechnicalReportLifecycle.DRAFT.value,
            ).values(**values)
        )
        if result.rowcount != 1:
            return False
        self._replace_provenance(report)
        self.session.flush()
        return True

    def persist_acceptance_expected_version(self, report: TechnicalReport, expected_version: int) -> bool:
        if report.lifecycle is not TechnicalReportLifecycle.ACCEPTED or report.accepted_snapshot is None:
            raise TechnicalReportValidationError("acceptance persistence requires accepted state")
        result = self.session.execute(
            update(TechnicalReportRecord).where(
                TechnicalReportRecord.id == report.id,
                TechnicalReportRecord.organization_id == report.organization_id,
                TechnicalReportRecord.version == expected_version,
                TechnicalReportRecord.lifecycle == TechnicalReportLifecycle.DRAFT.value,
                TechnicalReportRecord.draft_revision_id == report.draft_revision_id,
            ).values(**self._mutable_values(report))
        )
        self.session.flush()
        return result.rowcount == 1

    def _replace_provenance(self, report: TechnicalReport) -> None:
        self.session.query(TechnicalReportProvenanceRecord).filter_by(
            technical_report_id=report.id
        ).delete(synchronize_session=False)
        self.session.add_all([_record_for_entry(report.id, item) for item in report.provenance])

    def _aggregate(self, root: TechnicalReportRecord) -> TechnicalReport:
        if root.lifecycle == TechnicalReportLifecycle.ACCEPTED.value:
            return self._accepted(root)
        if root.lifecycle != TechnicalReportLifecycle.DRAFT.value:
            raise TechnicalReportValidationError("persisted lifecycle is invalid")
        if any(value is not None for value in (
            root.accepted_snapshot, root.accepted_snapshot_digest, root.accepted_by_id,
            root.accepted_at, root.accepted_draft_revision_id, root.accepted_aggregate_version,
        )):
            raise TechnicalReportValidationError("persisted draft acceptance state is incoherent")
        provenance = self.provenance_for_report(root.id)
        return TechnicalReport._build(
            id=root.id,
            organization_id=root.organization_id,
            workspace_id=root.workspace_id,
            project_id=root.project_id,
            owner_id=root.owner_id,
            purpose=TechnicalReportPurpose(root.purpose),
            content=TechnicalReportContent(
                root.engineering_scope, root.draft_content, tuple(root.assumptions),
                root.uncertainty, tuple(root.limitations), root.conclusions,
                tuple(root.recommendations),
            ),
            qualification=PreliminaryQualification(
                root.is_preliminary, tuple(root.evidence_deficiencies),
                tuple(root.unresolved_issues), tuple(root.follow_up_requirements),
            ),
            provenance=provenance,
            draft_revision=TechnicalReportDraftRevision(root.draft_revision_id, root.draft_revision_number),
            lifecycle=TechnicalReportLifecycle.DRAFT,
            predecessor_report_id=root.predecessor_report_id,
            version=root.version,
            accepted_snapshot=None,
            acceptance_record=None,
            created_at=root.created_at,
            updated_at=root.updated_at,
        )

    def _accepted(self, root: TechnicalReportRecord) -> TechnicalReport:
        if root.accepted_snapshot is None or root.accepted_snapshot_digest is None:
            raise TechnicalReportValidationError("accepted snapshot is missing")
        snapshot = _snapshot(root.accepted_snapshot, root.accepted_snapshot_digest)
        if (
            snapshot.report_id != root.id
            or snapshot.organization_id != root.organization_id
            or snapshot.workspace_id != root.workspace_id
            or snapshot.project_id != root.project_id
            or snapshot.purpose.value != root.purpose
            or snapshot.accepted_aggregate_version != root.version
            or snapshot.accepted_by_id != root.accepted_by_id
            or snapshot.accepted_at != root.accepted_at
            or snapshot.accepted_draft_revision.revision_id != root.draft_revision_id
            or snapshot.accepted_draft_revision.revision_id != root.accepted_draft_revision_id
            or snapshot.accepted_draft_revision.revision_number != root.draft_revision_number
            or snapshot.accepted_aggregate_version != root.accepted_aggregate_version
            or snapshot.predecessor_report_id != root.predecessor_report_id
        ):
            raise TechnicalReportValidationError("accepted root and snapshot are incoherent")
        record = TechnicalReportAcceptanceRecord(
            snapshot.accepted_by_id, snapshot.accepted_at,
            snapshot.accepted_draft_revision, snapshot.accepted_aggregate_version,
            root.accepted_snapshot_digest,
        )
        return TechnicalReport._build(
            id=snapshot.report_id,
            organization_id=snapshot.organization_id,
            workspace_id=snapshot.workspace_id,
            project_id=snapshot.project_id,
            owner_id=root.owner_id,
            purpose=snapshot.purpose,
            content=snapshot.content,
            qualification=snapshot.qualification,
            provenance=snapshot.provenance,
            draft_revision=snapshot.accepted_draft_revision,
            lifecycle=TechnicalReportLifecycle.ACCEPTED,
            predecessor_report_id=snapshot.predecessor_report_id,
            version=snapshot.accepted_aggregate_version,
            accepted_snapshot=snapshot,
            acceptance_record=record,
            created_at=root.created_at,
            updated_at=root.updated_at,
        )

    @staticmethod
    def _root_from_aggregate(report: TechnicalReport) -> TechnicalReportRecord:
        return TechnicalReportRecord(
            id=report.id,
            organization_id=report.organization_id,
            workspace_id=report.workspace_id,
            project_id=report.project_id,
            owner_id=report.owner_id,
            purpose=report.purpose.value,
            **SqlAlchemyTechnicalReportRepository._mutable_values(report),
            created_at=report.created_at,
        )

    @staticmethod
    def _mutable_values(report: TechnicalReport) -> dict[str, object]:
        snapshot = report.accepted_snapshot
        return {
            "engineering_scope": report.content.engineering_scope,
            "draft_content": report.content.technical_content,
            "assumptions": list(report.content.assumptions),
            "uncertainty": report.content.uncertainty,
            "limitations": list(report.content.limitations),
            "conclusions": report.content.conclusions,
            "recommendations": list(report.content.recommendations),
            "is_preliminary": report.qualification.is_preliminary,
            "evidence_deficiencies": list(report.qualification.evidence_deficiencies),
            "unresolved_issues": list(report.qualification.unresolved_issues),
            "follow_up_requirements": list(report.qualification.follow_up_requirements),
            "draft_revision_id": report.draft_revision_id,
            "draft_revision_number": report.draft_revision.revision_number,
            "lifecycle": report.lifecycle.value,
            "predecessor_report_id": report.predecessor_report_id,
            "version": report.version,
            "accepted_snapshot": null() if snapshot is None else accepted_snapshot_payload(snapshot),
            "accepted_snapshot_digest": None if snapshot is None else snapshot.integrity_digest,
            "accepted_by_id": report.accepted_by_id,
            "accepted_at": report.accepted_at,
            "accepted_draft_revision_id": report.accepted_draft_revision_id,
            "accepted_aggregate_version": report.accepted_aggregate_version,
            "updated_at": report.updated_at,
        }

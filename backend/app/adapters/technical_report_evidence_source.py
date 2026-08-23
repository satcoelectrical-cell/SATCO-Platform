"""Authorized Evidence-to-Technical-Report provenance composition for PATCH-043."""

from dataclasses import asdict
from uuid import NAMESPACE_URL, uuid5

from app.enums import EvidenceLifecycle, EvidenceSourceStanding
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportOwningCapability,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
from app.models.technical_report_command import (
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    historical_basis_digest,
)
from app.schemas.evidence import EvidenceFilter
from app.schemas.technical_report import (
    EvidenceHistoricalBasisSchema,
    TechnicalReportEvidenceSourceCandidate,
    TechnicalReportEvidenceSourceCandidateList,
    TechnicalReportProvenanceSchema,
)


class TechnicalReportEvidenceSourceAdapter:
    """Composes current Evidence through canonical application collaborators."""

    def __init__(self, *, evidence_service, supporting_files, actor):
        self._evidence_service = evidence_service
        self._supporting_files = supporting_files
        self._actor = actor

    def list_candidates(self, *, project_id: int, workspace_id: int, page: int, size: int):
        try:
            result = self._evidence_service.list(
                project_id=project_id,
                filters=EvidenceFilter(
                    workspace_id=workspace_id,
                    lifecycle=EvidenceLifecycle.CURRENT,
                    source_standing=EvidenceSourceStanding.CURRENT,
                ),
                page=page,
                size=size,
                actor=self._actor,
            )
            candidates = tuple(self._candidate(item, project_id, workspace_id) for item in result.items)
        except Exception as exc:
            raise TechnicalReportAuthorizationDenied() from exc
        return TechnicalReportEvidenceSourceCandidateList(
            items=list(candidates), total=result.total,
            page=result.page, size=result.size,
        )

    def _candidate(self, item, project_id: int, workspace_id: int):
        if (
            item.organization_id != self._actor.organization_id
            or item.project_id != project_id
            or item.workspace_id not in {None, workspace_id}
            or item.lifecycle != EvidenceLifecycle.CURRENT
            or item.source_standing != EvidenceSourceStanding.CURRENT
        ):
            raise TechnicalReportAuthorizationDenied()
        files = self._supporting_files.resolve_for_evidence(
            evidence_id=item.id,
            organization_id=item.organization_id,
            project_id=item.project_id,
            workspace_id=item.workspace_id,
            lock=False,
        )
        base = dict(
            basis_schema_version=2 if files else 1,
            source_category="evidence",
            evidence_id=item.id,
            source_version=item.version,
            organization_id=item.organization_id,
            project_id=item.project_id,
            workspace_id=item.workspace_id,
            lifecycle=item.lifecycle,
            source_kind=item.source_kind,
            source_reference=item.source_reference,
            source_revision=item.source_revision,
            source_standing=item.source_standing,
            effective_at=item.effective_at,
            supported_fact=item.supported_fact,
            creator_id=item.creator_id,
        )
        domain = (
            EvidenceHistoricalBasisV2(**base, supporting_files=files)
            if files else EvidenceHistoricalBasisV1(**base)
        )
        basis = EvidenceHistoricalBasisSchema.model_validate(
            {**base, "supporting_files": tuple(asdict(item) for item in files)}
        )
        provenance = TechnicalReportProvenanceSchema(
            entry_id=uuid5(
                NAMESPACE_URL,
                f"satco:technical-report:evidence:{item.id}:v{item.version}",
            ),
            ordinal=0,
            source_class=TechnicalReportSourceClass.CANONICAL_MATERIAL,
            source_type=TechnicalReportSourceType.EVIDENCE,
            is_material=True,
            owning_capability=TechnicalReportOwningCapability.EVIDENCE,
            reliance_role="supporting_evidence",
            verification_status=TechnicalReportVerificationStatus.VERIFIED,
            availability_status=TechnicalReportAvailabilityStatus.AVAILABLE,
            origin_attribution="Canonical Evidence",
            limitations=[],
            locator=basis,
            integrity_algorithm=TechnicalReportIntegrityAlgorithm.SHA256,
            integrity_digest=historical_basis_digest(domain),
        )
        preview = " ".join(item.supported_fact.split())[:240]
        return TechnicalReportEvidenceSourceCandidate(
            evidence_id=item.id, project_id=project_id,
            workspace_id=item.workspace_id, source_kind=item.source_kind,
            version=item.version, updated_at=item.updated_at,
            preview=preview, supporting_file_count=len(files),
            provenance=provenance,
        )

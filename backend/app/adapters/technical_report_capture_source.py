"""Authorized Capture-to-Technical-Report provenance composition for PATCH-039."""

from uuid import NAMESPACE_URL, uuid5

from app.enums.engineering_experience_capture import EngineeringExperienceCaptureLifecycle
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportOwningCapability,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.engineering_experience_capture import EngineeringExperienceCaptureError
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.models.technical_report_command import historical_basis_digest
from app.schemas.engineering_experience_capture import EngineeringExperienceCaptureFilter
from app.schemas.technical_report import (
    CaptureHistoricalBasisSchema,
    TechnicalReportCaptureSourceCandidate,
    TechnicalReportCaptureSourceCandidateList,
    TechnicalReportProvenanceSchema,
)


class TechnicalReportCaptureSourceAdapter:
    """Composes an authorized canonical Capture response; owns no Capture state."""

    def __init__(self, capture_service):
        self._capture_service = capture_service

    def list_candidates(
        self,
        *,
        actor: EngineeringExperienceCaptureActor,
        project_id: int,
        workspace_id: int,
        page: int,
        size: int,
    ) -> TechnicalReportCaptureSourceCandidateList:
        try:
            result = self._capture_service.list_workspace(
                workspace_id,
                EngineeringExperienceCaptureFilter(
                    lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED
                ),
                page,
                size,
                actor,
            )
        except EngineeringExperienceCaptureError as exc:
            raise TechnicalReportAuthorizationDenied() from exc

        if any(
            item.organization_id != actor.organization_id
            or item.project_id != project_id
            or item.workspace_id != workspace_id
            or item.lifecycle is not EngineeringExperienceCaptureLifecycle.CAPTURED
            for item in result.items
        ):
            raise TechnicalReportAuthorizationDenied()

        candidates = [self._candidate(item) for item in result.items]
        return TechnicalReportCaptureSourceCandidateList(
            items=candidates, total=result.total, page=result.page, size=result.size
        )

    @staticmethod
    def _candidate(capture) -> TechnicalReportCaptureSourceCandidate:
        basis = CaptureHistoricalBasisSchema(
            basis_schema_version=1,
            source_category="universal_capture",
            capture_id=capture.id,
            source_version=capture.version,
            organization_id=capture.organization_id,
            project_id=capture.project_id,
            workspace_id=capture.workspace_id,
            discipline=capture.discipline,
            engineering_object_id=capture.engineering_object_id,
            source_kind=capture.source_kind,
            original_content=capture.original_content,
            source_reference=capture.source_reference,
            creator_id=capture.creator_id,
            lifecycle=capture.lifecycle,
            created_at=capture.created_at,
        )
        provenance = TechnicalReportProvenanceSchema(
            entry_id=uuid5(
                NAMESPACE_URL,
                f"satco:technical-report:capture:{capture.id}:v{capture.version}",
            ),
            ordinal=0,
            source_class=TechnicalReportSourceClass.CANONICAL_MATERIAL,
            source_type=TechnicalReportSourceType.UNIVERSAL_CAPTURE,
            is_material=True,
            owning_capability=TechnicalReportOwningCapability.UNIVERSAL_CAPTURE,
            reliance_role="source_capture",
            verification_status=TechnicalReportVerificationStatus.VERIFIED,
            availability_status=TechnicalReportAvailabilityStatus.AVAILABLE,
            origin_attribution="Universal Engineering Capture",
            limitations=[],
            locator=basis,
            integrity_algorithm=TechnicalReportIntegrityAlgorithm.SHA256,
            integrity_digest=historical_basis_digest(basis.to_domain()),
        )
        preview = " ".join(capture.original_content.split())[:240]
        return TechnicalReportCaptureSourceCandidate(
            capture_id=capture.id,
            project_id=capture.project_id,
            workspace_id=capture.workspace_id,
            source_kind=capture.source_kind,
            version=capture.version,
            created_at=capture.created_at,
            preview=preview,
            provenance=provenance,
        )

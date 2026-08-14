"""Request-scoped composition root for PATCH-034 Organizational Memory."""

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.organizational_memory import (
    CanonicalMemoryProvenanceAuthorizer,
    TechnicalReportAcceptedSourceAdapter,
)
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.models.organizational_memory_command import MemoryActor
from app.repositories.engineering_experience_capture_unit_of_work import (
    SqlAlchemyEngineeringExperienceCaptureUnitOfWork,
)
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyAuthorizationPolicy,
    SqlAlchemyEngineeringObjectUnitOfWork,
    SqlAlchemyReferenceValidator,
    UtcClock,
)
from app.repositories.engineering_relationship_repository import (
    SqlAlchemyEngineeringRelationshipRepository,
)
from app.repositories.engineering_relationship_unit_of_work import (
    SqlAlchemyEngineeringRelationshipUnitOfWork,
    SqlAlchemyRelationshipAuthorizationPolicy,
    SqlAlchemyRelationshipValidator,
    UtcRelationshipClock,
)
from app.repositories.evidence_unit_of_work import (
    SqlAlchemyEvidenceAuthorizationPolicy,
    SqlAlchemyEvidenceUnitOfWork,
    SqlAlchemyEvidenceValidator,
    UtcEvidenceClock,
)
from app.repositories.organizational_memory_unit_of_work import (
    SqlAlchemyOrganizationalMemoryUnitOfWork,
)
from app.repositories.technical_report_unit_of_work import (
    SqlAlchemyTechnicalReportUnitOfWork,
)
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)
from app.services.engineering_object_service import EngineeringObjectService
from app.services.engineering_relationship_service import (
    EngineeringRelationshipService,
)
from app.services.evidence_service import EvidenceService
from app.services.organizational_memory_service import OrganizationalMemoryService
from app.services.technical_report_service import TechnicalReportService


class _UtcClock:
    def now(self):
        return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class OrganizationalMemoryApplication:
    """One request-scoped service and its server-trusted actor."""

    service: OrganizationalMemoryService
    actor: MemoryActor


def get_organizational_memory_service(
    db: Session = Depends(get_db),
) -> OrganizationalMemoryService:
    """Compose the request-scoped service without transport involvement."""
    technical_reports = TechnicalReportService(
        lambda: SqlAlchemyTechnicalReportUnitOfWork(SessionLocal), _UtcClock()
    )
    accepted_reports = TechnicalReportAcceptedSourceAdapter(technical_reports)

    captures = EngineeringExperienceCaptureService(
        uow_factory=lambda: SqlAlchemyEngineeringExperienceCaptureUnitOfWork(
            SessionLocal
        )
    )
    evidence = EvidenceService(
        uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal),
        authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),
        validator=SqlAlchemyEvidenceValidator(db),
        clock=UtcEvidenceClock(),
    )
    engineering_objects = EngineeringObjectService(
        uow_factory=lambda: SqlAlchemyEngineeringObjectUnitOfWork(SessionLocal),
        authorization=SqlAlchemyAuthorizationPolicy(db),
        references=SqlAlchemyReferenceValidator(db),
        clock=UtcClock(),
    )
    relationship_repository = SqlAlchemyEngineeringRelationshipRepository(db)
    relationship_evidence = SqlAlchemyEvidenceValidator(db)
    engineering_relationships = EngineeringRelationshipService(
        uow_factory=lambda: SqlAlchemyEngineeringRelationshipUnitOfWork(
            SessionLocal
        ),
        authorization=SqlAlchemyRelationshipAuthorizationPolicy(db),
        validator=SqlAlchemyRelationshipValidator(
            db, relationship_repository, relationship_evidence
        ),
        clock=UtcRelationshipClock(),
    )
    provenance = CanonicalMemoryProvenanceAuthorizer(
        accepted_reports=accepted_reports,
        captures=captures,
        evidence=evidence,
        engineering_objects=engineering_objects,
        engineering_relationships=engineering_relationships,
    )
    return OrganizationalMemoryService(
        uow_factory=lambda: SqlAlchemyOrganizationalMemoryUnitOfWork(
            SessionLocal, SessionLocal
        ),
        accepted_reports=accepted_reports,
        provenance=provenance,
        clock=_UtcClock(),
    )


def get_organizational_memory_application(
    organization: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    service: OrganizationalMemoryService = Depends(
        get_organizational_memory_service
    ),
) -> OrganizationalMemoryApplication:
    """Bind only server-trusted request identity to the composed service."""

    return OrganizationalMemoryApplication(
        service=service,
        actor=MemoryActor(
            actor_id=organization.user.id,
            organization_id=organization.organization_id,
        ),
    )

"""Request-scoped composition root for PATCH-043 Supporting Files."""

from dataclasses import dataclass
from datetime import datetime
import json
from urllib.request import Request, urlopen

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.adapters.supporting_file_object_store import S3PrivateSupportingFileObjectStore
from app.adapters.supporting_file_scanner import (
    CallbackSupportingFileScanner,
    SupportingFileScannerCredentialVerifier,
)
from app.core.config import settings
from app.core.database import get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.exceptions.supporting_file import SupportingFileProtectedNotFound, SupportingFileScannerUnavailable
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.ports.supporting_file import SupportingFileScannerPrincipal
from app.repositories.supporting_file_unit_of_work import SqlAlchemySupportingFileUnitOfWork
from app.services.supporting_file_service import SupportingFileService
from app.adapters.technical_report_evidence_source import TechnicalReportEvidenceSourceAdapter
from app.models.evidence_command import EvidenceActor
from app.repositories.evidence_unit_of_work import (
    SqlAlchemyEvidenceAuthorizationPolicy,
    SqlAlchemyEvidenceUnitOfWork,
    SqlAlchemyEvidenceValidator,
    UtcEvidenceClock,
)
from app.services.evidence_service import EvidenceService
from app.services.supporting_file_service import SqlAlchemySupportingFileTechnicalReportCollaborator
from app.core.database import SessionLocal


class SqlAlchemySupportingFileScopePolicy:
    def __init__(self, session: Session):
        self.session = session

    def _require(self, *, actor_id, organization_id, project_id, workspace_id):
        user = self.session.get(User, actor_id)
        project = self.session.query(Project).filter_by(
            id=project_id, organization_id=organization_id,
        ).first()
        if user is None or not user.is_active or project is None:
            raise SupportingFileProtectedNotFound()
        if user.role == "admin" or actor_id in {project.owner_id, project.primary_assignee_id}:
            return user
        if workspace_id is None:
            raise SupportingFileProtectedNotFound()
        workspace = self.session.query(EngineeringWorkspace).filter_by(
            id=workspace_id, project_id=project_id,
        ).first()
        if workspace is None or (
            actor_id not in {workspace.owner_id, workspace.primary_assignee_id}
            and self.session.get(EngineeringWorkspaceMember, (workspace.id, actor_id)) is None
        ):
            raise SupportingFileProtectedNotFound()
        return user

    def require_mutation(self, **request):
        self._require(**request)

    def require_read(self, **request):
        self._require(**request)

    def require_withdraw(self, *, uploader_id, **request):
        user = self._require(**request)
        if user.role != "admin" and user.id != uploader_id:
            raise SupportingFileProtectedNotFound()


@dataclass(frozen=True, slots=True)
class SupportingFileApplication:
    service: SupportingFileService
    actor_id: int
    organization_id: object


def _scanner_callback(**payload):
    token = settings.resolved_supporting_file_scanner_token()
    try:
        request = Request(
            settings.SUPPORTING_FILE_SCANNER_ENDPOINT,
            data=json.dumps(payload, default=str, separators=(",", ":")).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=30.0) as response:
            value = json.loads(response.read())
        value["observed_at"] = datetime.fromisoformat(
            value["observed_at"].replace("Z", "+00:00")
        )
        return value
    except Exception:
        raise SupportingFileScannerUnavailable() from None


def _service(db: Session) -> SupportingFileService:
    objects = S3PrivateSupportingFileObjectStore(
        endpoint_url=settings.SUPPORTING_FILE_OBJECT_ENDPOINT,
        bucket=settings.SUPPORTING_FILE_OBJECT_BUCKET,
        region=settings.SUPPORTING_FILE_OBJECT_REGION,
        access_key=settings.resolved_supporting_file_object_access_key(),
        secret_key=settings.resolved_supporting_file_object_secret_key(),
    )
    return SupportingFileService(
        uow=SqlAlchemySupportingFileUnitOfWork(db), objects=objects,
        scanner=CallbackSupportingFileScanner(_scanner_callback),
        authorization=SqlAlchemySupportingFileScopePolicy(db),
    )


def get_supporting_file_application(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> SupportingFileApplication:
    return SupportingFileApplication(
        _service(db), context.user.id, context.organization_id,
    )


@dataclass(frozen=True, slots=True)
class SupportingFileScannerApplication:
    service: SupportingFileService
    principal: SupportingFileScannerPrincipal


def get_supporting_file_scanner_application(
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> SupportingFileScannerApplication:
    prefix = "Bearer "
    supplied = authorization[len(prefix):] if authorization and authorization.startswith(prefix) else None
    principal = SupportingFileScannerCredentialVerifier(
        settings.resolved_supporting_file_scanner_token()
    ).authenticate(supplied)
    return SupportingFileScannerApplication(_service(db), principal)


def get_technical_report_evidence_source_adapter(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> TechnicalReportEvidenceSourceAdapter:
    evidence = EvidenceService(
        uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal),
        authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),
        validator=SqlAlchemyEvidenceValidator(db),
        clock=UtcEvidenceClock(),
    )
    return TechnicalReportEvidenceSourceAdapter(
        evidence_service=evidence,
        supporting_files=SqlAlchemySupportingFileTechnicalReportCollaborator(db),
        actor=EvidenceActor(context.user.id, context.organization_id),
    )

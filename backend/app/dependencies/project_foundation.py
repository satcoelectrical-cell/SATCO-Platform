from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy import and_, exists, or_
from sqlalchemy.orm import Session

from app.adapters.project_foundation import CanonicalProjectInputSourceAdapter
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.supporting_file import _service as supporting_file_service
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.repositories.project_foundation_unit_of_work import SqlAlchemyProjectFoundationUnitOfWork
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceAuthorizationPolicy, SqlAlchemyEvidenceUnitOfWork, SqlAlchemyEvidenceValidator, UtcEvidenceClock
from app.schemas.project_foundation import ProjectFoundationActor
from app.services.project_foundation_service import ProjectFoundationService
from app.services.evidence_service import EvidenceService


class SqlAlchemyProjectFoundationAuthorization:
    def __init__(self, session: Session):
        self.session = session

    def _active(self, actor: ProjectFoundationActor):
        return self.session.query(User).join(
            UserOrganizationMembership,
            and_(UserOrganizationMembership.user_id == User.id, UserOrganizationMembership.organization_id == actor.organization_id),
        ).join(Organization, Organization.id == actor.organization_id).filter(
            User.id == actor.actor_id, User.is_active.is_(True), User.role.in_(("admin", "engineer")),
            UserOrganizationMembership.is_enabled.is_(True), Organization.is_active.is_(True),
        ).first()

    def can_read(self, *, actor, project):
        user = self._active(actor)
        if user is None or project.organization_id != actor.organization_id:
            return False
        if user.role == "admin" or actor.actor_id in {project.owner_id, project.primary_assignee_id}:
            return True
        return self.session.query(EngineeringWorkspace.id).filter(
            EngineeringWorkspace.project_id == project.id,
            or_(
                EngineeringWorkspace.owner_id == actor.actor_id,
                EngineeringWorkspace.primary_assignee_id == actor.actor_id,
                exists().where(and_(EngineeringWorkspaceMember.workspace_id == EngineeringWorkspace.id, EngineeringWorkspaceMember.user_id == actor.actor_id)),
            ),
        ).first() is not None

    def can_mutate(self, *, actor, project):
        user = self._active(actor)
        return bool(user and project.organization_id == actor.organization_id and (user.role == "admin" or actor.actor_id in {project.owner_id, project.primary_assignee_id}))


@dataclass(frozen=True, slots=True)
class ProjectFoundationApplication:
    service: ProjectFoundationService
    actor: ProjectFoundationActor


def get_project_foundation_application(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    actor = ProjectFoundationActor(actor_id=context.user.id, organization_id=context.organization_id)
    sources = CanonicalProjectInputSourceAdapter(
        evidence_service=EvidenceService(
            uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal),
            authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),
            validator=SqlAlchemyEvidenceValidator(db),
            clock=UtcEvidenceClock(),
        ),
        supporting_file_service=supporting_file_service(db),
    )
    service = ProjectFoundationService(
        uow_factory=lambda: SqlAlchemyProjectFoundationUnitOfWork(db),
        authorization=SqlAlchemyProjectFoundationAuthorization(db),
        sources=sources,
    )
    return ProjectFoundationApplication(service=service, actor=actor)

from sqlalchemy import and_, exists, or_

from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.exceptions.engineering_execution_plan import ExecutionPlanUnavailable
from app.schemas.project_foundation import ProjectFoundationActor


class SqlAlchemyExecutionPlanAuthorization:
    def __init__(self, session): self.session = session

    def _active(self, actor):
        return self.session.query(User).join(
            UserOrganizationMembership, and_(UserOrganizationMembership.user_id == User.id, UserOrganizationMembership.organization_id == actor.organization_id),
        ).join(Organization, Organization.id == actor.organization_id).filter(
            User.id == actor.actor_id, User.is_active.is_(True), User.role.in_(("admin", "engineer")),
            UserOrganizationMembership.is_enabled.is_(True), Organization.is_active.is_(True),
        ).first()

    def get_project(self, *, actor, project_id, lock=False):
        query = self.session.query(Project).filter(Project.id == project_id, Project.organization_id == actor.organization_id)
        return (query.with_for_update() if lock else query).first()

    def can_read(self, *, actor, project):
        user = self._active(actor)
        if user is None or project.organization_id != actor.organization_id: return False
        if user.role == "admin" or actor.actor_id in {project.owner_id, project.primary_assignee_id}: return True
        return self.session.query(EngineeringWorkspace.id).filter(
            EngineeringWorkspace.project_id == project.id,
            or_(EngineeringWorkspace.owner_id == actor.actor_id, EngineeringWorkspace.primary_assignee_id == actor.actor_id,
                exists().where(and_(EngineeringWorkspaceMember.workspace_id == EngineeringWorkspace.id, EngineeringWorkspaceMember.user_id == actor.actor_id))),
        ).first() is not None

    def can_mutate(self, *, actor, project):
        user = self._active(actor)
        return bool(user and project.organization_id == actor.organization_id and (user.role == "admin" or actor.actor_id in {project.owner_id, project.primary_assignee_id}))

    def validate_workspace(self, *, actor, project, workspace_id):
        if workspace_id is None: return True
        return self.session.query(EngineeringWorkspace.id).filter(
            EngineeringWorkspace.id == workspace_id, EngineeringWorkspace.project_id == project.id,
        ).first() is not None

    @staticmethod
    def validate_responsible_user(*, project, user_id):
        return user_id is None or user_id in {project.owner_id, project.primary_assignee_id}


class ProjectFoundationApplicationAdapter:
    """Uses the accepted Foundation application API; never a Foundation repository."""
    def __init__(self, application): self.application = application
    def is_established(self, *, actor, project_id):
        result = self.application.service.get(
            project_id=project_id,
            actor=ProjectFoundationActor(actor_id=actor.actor_id, organization_id=actor.organization_id),
        )
        if getattr(result, "outcome", None) == "unavailable":
            raise ExecutionPlanUnavailable()
        return getattr(result, "availability", None) == "established"

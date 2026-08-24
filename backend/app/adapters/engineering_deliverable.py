from sqlalchemy import and_, exists, or_

from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.exceptions.supporting_file import SupportingFileIntegrityError, SupportingFileProtectedNotFound, SupportingFileValidationError
from app.models.supporting_file_command import SupportingFileScope


class SqlAlchemyDeliverableAuthorization:
    """Capability-local policy; it reads only Project/Workspace authority facts."""
    def __init__(self, session): self.session=session
    def _active(self, actor):
        return self.session.query(User).join(UserOrganizationMembership, and_(UserOrganizationMembership.user_id==User.id, UserOrganizationMembership.organization_id==actor.organization_id)).join(Organization, Organization.id==actor.organization_id).filter(User.id==actor.actor_id, User.is_active.is_(True), User.role.in_(("admin","engineer")), UserOrganizationMembership.is_enabled.is_(True), Organization.is_active.is_(True)).first()
    def project(self, *, actor, project_id, lock=False):
        query=self.session.query(Project).filter(Project.id==project_id, Project.organization_id==actor.organization_id)
        return (query.with_for_update() if lock else query).first()
    def can_read(self, *, actor, project):
        user=self._active(actor)
        if user is None or project is None: return False
        if user.role=="admin" or actor.actor_id in {project.owner_id, project.primary_assignee_id}: return True
        return self.session.query(EngineeringWorkspace.id).filter(EngineeringWorkspace.project_id==project.id, or_(EngineeringWorkspace.owner_id==actor.actor_id, EngineeringWorkspace.primary_assignee_id==actor.actor_id, exists().where(and_(EngineeringWorkspaceMember.workspace_id==EngineeringWorkspace.id, EngineeringWorkspaceMember.user_id==actor.actor_id)))).first() is not None
    def can_mutate(self, *, actor, project):
        user=self._active(actor)
        return bool(user and project and (user.role=="admin" or actor.actor_id in {project.owner_id,project.primary_assignee_id}))
    def valid_links(self, *, project, data):
        if data.workspace_id is not None and self.session.query(EngineeringWorkspace.id).filter_by(id=data.workspace_id, project_id=project.id).first() is None: return False
        if data.responsible_user_id not in {None, project.owner_id, project.primary_assignee_id}: return False
        # The execution relation is optional; supplied identities must remain in the Project.
        if data.activity_id is not None and self.session.execute(__import__('sqlalchemy').text("SELECT 1 FROM engineering_execution_activities WHERE id=:id AND project_id=:project"), {"id": str(data.activity_id), "project": project.id}).first() is None: return False
        if data.milestone_id is not None and self.session.execute(__import__('sqlalchemy').text("SELECT 1 FROM engineering_execution_milestones WHERE id=:id AND project_id=:project"), {"id": str(data.milestone_id), "project": project.id}).first() is None: return False
        return True


class SupportingFileApplicationAdapter:
    """Uses Supporting File's application boundary; it never queries file persistence."""
    def __init__(self, application): self.application=application
    def visible(self, *, actor, project, workspace_id, asset_id):
        if asset_id is None: return True
        try:
            asset=self.application.service.get_metadata(actor_id=actor.actor_id, scope=SupportingFileScope(actor.organization_id, project.id, workspace_id), asset_id=asset_id)
            return asset.lifecycle == "available"
        except (SupportingFileProtectedNotFound, SupportingFileValidationError, SupportingFileIntegrityError):
            return False

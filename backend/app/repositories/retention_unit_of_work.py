"""Atomic PATCH-055 retention governance Unit of Work."""
from datetime import datetime, timezone
from typing import Self
from uuid import UUID

from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.retention import RetentionIdempotency, RetentionOutbox
from app.models.user import User
from app.repositories.retention_repository import SqlAlchemyRetentionRepository


class SqlAlchemyRetentionAuthorization:
    def __init__(self, session):
        self.session = session

    def _actor(self, *, actor_id, organization_id):
        user = self.session.get(User, actor_id)
        if user is None or not user.is_active or user.role not in {"admin", "engineer"}:
            return None
        membership = self.session.get(UserOrganizationMembership, (actor_id, organization_id))
        organization = self.session.get(Organization, organization_id)
        if membership is None or not membership.is_enabled or organization is None or not organization.is_active:
            return None
        return user

    def authorize_actor(self, *, actor_id, organization_id):
        return self._actor(actor_id=actor_id, organization_id=organization_id) is not None

    def authorize_read(self, *, actor_id, subject):
        user = self._actor(actor_id=actor_id, organization_id=subject.organization_id)
        if user is None:
            return False
        project = self.session.scalar(select(Project).where(
            Project.id == subject.project_id,
            Project.organization_id == subject.organization_id,
        ))
        if project is None:
            return False
        if user.role == "admin" or actor_id in {project.owner_id, project.primary_assignee_id}:
            return True
        if subject.workspace_id is None:
            return False
        workspace = self.session.scalar(select(EngineeringWorkspace).where(
            EngineeringWorkspace.id == subject.workspace_id,
            EngineeringWorkspace.project_id == subject.project_id,
        ))
        if workspace is None:
            return False
        if actor_id in {workspace.owner_id, workspace.primary_assignee_id}:
            return True
        return self.session.get(EngineeringWorkspaceMember, (workspace.id, actor_id)) is not None

    def authorize_workbench(self, *, actor_id, organization_id, project_id, workspace_id):
        user = self._actor(actor_id=actor_id, organization_id=organization_id)
        if user is None: return False
        project = self.session.scalar(select(Project).where(Project.id == project_id, Project.organization_id == organization_id))
        if project is None: return False
        if user.role == "admin" or actor_id in {project.owner_id, project.primary_assignee_id}: return True
        if workspace_id is None: return False
        workspace = self.session.scalar(select(EngineeringWorkspace).where(EngineeringWorkspace.id == workspace_id, EngineeringWorkspace.project_id == project_id))
        return workspace is not None and (actor_id in {workspace.owner_id, workspace.primary_assignee_id} or self.session.get(EngineeringWorkspaceMember, (workspace.id, actor_id)) is not None)

    def authorize_mutation(self, *, actor_id, subject):
        user = self._actor(actor_id=actor_id, organization_id=subject.organization_id)
        if user is None:
            return False
        project = self.session.scalar(select(Project).where(
            Project.id == subject.project_id,
            Project.organization_id == subject.organization_id,
        ))
        return project is not None and (
            user.role == "admin" or actor_id in {project.owner_id, project.primary_assignee_id}
        )


class SqlAlchemyRetentionIdempotencyStore:
    def __init__(self, session, repository):
        self.session = session
        self.repository = repository

    def get(
        self,
        *,
        organization_id,
        actor_id,
        operation,
        idempotency_key,
        lock=False,
    ):
        return self.repository.get_idempotency(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=idempotency_key,
            lock=lock,
        )

    def reserve(self, **values):
        row = RetentionIdempotency(
            status="pending",
            completed_at=None,
            **values,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def complete(self, row, *, safe_result, completed_at):
        row.status = "completed"
        row.safe_result = safe_result
        row.completed_at = completed_at
        row.updated_at = completed_at
        self.session.flush()


class SqlAlchemyRetentionAuditRecorder:
    def __init__(self, session):
        self.session = session

    def record(self, **values):
        self.session.add(
            AuditLog(
                user_id=values["actor_id"],
                action=values["action"],
                entity="RETENTION_GOVERNANCE",
                entity_uuid=values.get("aggregate_id"),
                details={
                    "correlation_id": str(values["correlation_id"]),
                    "project_id": values["project_id"],
                    "workspace_id": values.get("workspace_id"),
                    "version": values["version"],
                    "outcome": "success",
                },
            )
        )


class SqlAlchemyRetentionOutboxRecorder:
    def __init__(self, session):
        self.session = session

    def record(self, **values):
        self.session.add(
            RetentionOutbox(
                event_id=values["event_id"],
                organization_id=values["organization_id"],
                project_id=values.get("project_id"),
                workspace_id=values.get("workspace_id"),
                aggregate_kind=values["aggregate_kind"],
                aggregate_id=values["aggregate_id"],
                aggregate_version=values["aggregate_version"],
                event_type=values["event_type"],
                payload_schema_version=1,
                payload=values["payload"],
                occurred_at=values["occurred_at"],
                attempt_count=0,
            )
        )


class UtcRetentionClock:
    def now(self):
        return datetime.now(timezone.utc)


class SqlAlchemyRetentionUnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.retention = SqlAlchemyRetentionRepository(self.session)
        self.authorization = SqlAlchemyRetentionAuthorization(self.session)
        self.idempotency = SqlAlchemyRetentionIdempotencyStore(
            self.session,
            self.retention,
        )
        self.audit = SqlAlchemyRetentionAuditRecorder(self.session)
        self.outbox = SqlAlchemyRetentionOutboxRecorder(self.session)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

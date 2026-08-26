"""Request-scoped composition root for the PATCH-048 Project Context read."""
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.engineering_context_project_context import EngineeringContextProjectContextAdapter
from app.adapters.engineering_context_relationship_project_context import EngineeringContextRelationshipProjectContextAdapter
from app.adapters.project_context import (
    DeliverableProjectContextAdapter, EngineeringObjectProjectContextAdapter,
    EvidenceProjectContextAdapter, ExecutionProjectContextAdapter,
    OrganizationalMemoryProjectContextAdapter, ProjectBasisProjectContextAdapter,
    ProjectControlProjectContextAdapter, SupportingFileProjectContextAdapter,
    TechnicalReportProjectContextAdapter, ProjectContextGraphAdapter,
)
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.engineering_deliverable import get_engineering_deliverable_application
from app.dependencies.engineering_execution_plan import get_engineering_execution_plan_application
from app.dependencies.organizational_memory import get_organizational_memory_application
from app.dependencies.project_control import get_project_control_application
from app.dependencies.project_foundation import get_project_foundation_application
from app.dependencies.supporting_file import get_supporting_file_application
from app.repositories.engineering_object_unit_of_work import SqlAlchemyAuthorizationPolicy, SqlAlchemyEngineeringObjectUnitOfWork, SqlAlchemyReferenceValidator, UtcClock
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceAuthorizationPolicy, SqlAlchemyEvidenceUnitOfWork, SqlAlchemyEvidenceValidator, UtcEvidenceClock
from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork
from app.schemas.project_context import ProjectContextActor
from app.services.engineering_context_service import EngineeringContextService
from app.services.engineering_context_relationship_service import EngineeringContextRelationshipService
from app.services.engineering_workspace_service import EngineeringWorkspaceService
from app.services.engineering_object_service import EngineeringObjectService
from app.services.evidence_service import EvidenceService
from app.services.project_context_service import ProjectContextService
from app.services.project_service import ProjectService
from app.services.technical_report_service import TechnicalReportService


class _ProjectContextOwners:
    """Fixed named calls only; this is not a service locator or generic loader."""
    def __init__(self, *, basis, execution, deliverables, controls, context, objects, evidence, files, reports, memory, graph) -> None:
        self._basis, self._execution, self._deliverables, self._controls = basis, execution, deliverables, controls
        self._context, self._objects, self._evidence, self._files, self._reports, self._memory = context, objects, evidence, files, reports, memory
        self._graph = graph
    def project_basis(self, **kw): return self._basis.get_authorized_basis(**kw)
    def execution(self, **kw): return self._execution.get_authorized_plan(**kw)
    def deliverables(self, **kw): return self._deliverables.list_authorized_deliverables(**kw)
    def project_control(self, **kw): return self._controls.list_authorized_controls(**kw)
    def engineering_context(self, **kw): return self._context.list_authorized_current(**kw)
    def engineering_objects(self, **kw): return self._objects.list_authorized_objects(**kw)
    def evidence(self, **kw): return self._evidence.list_authorized_current(**kw)
    def supporting_files(self, **kw): return self._files.list_authorized_available(**kw)
    def technical_reports(self, **kw): return self._reports.list_authorized_accepted(**kw)
    def organizational_memory(self, **kw): return self._memory.list_authorized_active(**kw)
    def project_node(self, **kw): return self._graph.project_node(**kw)
    def workspace_node(self, **kw): return self._graph.workspace_node(**kw)
    def execution_plan_node(self, **kw): return self._graph.execution_plan_node(**kw)
    def activity_node(self, **kw): return self._graph.activity_node(**kw)
    def milestone_node(self, **kw): return self._graph.milestone_node(**kw)
    def deliverable_node(self, **kw): return self._graph.deliverable_node(**kw)
    def deliverable_revision_node(self, **kw): return self._graph.deliverable_revision_node(**kw)
    def risk_node(self, **kw): return self._graph.risk_node(**kw)
    def issue_node(self, **kw): return self._graph.issue_node(**kw)
    def decision_node(self, **kw): return self._graph.decision_node(**kw)
    def change_node(self, **kw): return self._graph.change_node(**kw)
    def change_impact_node(self, **kw): return self._graph.change_impact_node(**kw)
    def engineering_object_node(self, **kw): return self._graph.engineering_object_node(**kw)
    def engineering_context_node(self, **kw): return self._graph.engineering_context_node(**kw)
    def evidence_node(self, **kw): return self._graph.evidence_node(**kw)
    def supporting_file_node(self, **kw): return self._graph.supporting_file_node(**kw)
    def technical_report_node(self, **kw): return self._graph.technical_report_node(**kw)
    def organizational_memory_node(self, **kw): return self._graph.organizational_memory_node(**kw)
    def engineering_relationship_edges(self, **kw): return self._graph.engineering_relationship_edges(**kw)
    def context_relationship_edges(self, **kw): return self._graph.context_relationship_edges(**kw)
    def execution_edges(self, **kw): return self._graph.execution_edges(**kw)
    def deliverable_edges(self, **kw): return self._graph.deliverable_edges(**kw)
    def project_control_edges(self, **kw): return self._graph.project_control_edges(**kw)
    def evidence_file_edges(self, **kw): return self._graph.evidence_file_edges(**kw)
    def technical_report_edges(self, **kw): return self._graph.technical_report_edges(**kw)
    def organizational_memory_edges(self, **kw): return self._graph.organizational_memory_edges(**kw)


@dataclass(frozen=True, slots=True)
class ProjectContextApplication:
    service: ProjectContextService
    actor: ProjectContextActor
    current_user: object


def get_project_context_application(
    db: Session = Depends(get_db),
    organization: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
) -> ProjectContextApplication:
    """The sole infrastructure composition boundary; adapters receive public services only."""
    actor = ProjectContextActor(actor_id=organization.user.id, organization_id=organization.organization_id)
    foundation = get_project_foundation_application(db, organization)
    execution = get_engineering_execution_plan_application(db, organization, foundation)
    deliverables = get_engineering_deliverable_application(db, organization, get_supporting_file_application(db, organization))
    controls = get_project_control_application(db, organization)
    objects = EngineeringObjectService(uow_factory=lambda: SqlAlchemyEngineeringObjectUnitOfWork(SessionLocal), authorization=SqlAlchemyAuthorizationPolicy(db), references=SqlAlchemyReferenceValidator(db), clock=UtcClock())
    evidence = EvidenceService(uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal), authorization=SqlAlchemyEvidenceAuthorizationPolicy(db), validator=SqlAlchemyEvidenceValidator(db), clock=UtcEvidenceClock())
    reports = TechnicalReportService(lambda: SqlAlchemyTechnicalReportUnitOfWork(SessionLocal), UtcClock())
    files = get_supporting_file_application(db, organization)
    memory = get_organizational_memory_application(organization, get_organizational_memory_service_for_context(db))
    project = ProjectService(db)
    workspace = EngineeringWorkspaceService(db, organization.organization_id)
    context_adapter = EngineeringContextProjectContextAdapter(EngineeringContextService(db))
    context_relationships = EngineeringContextRelationshipProjectContextAdapter(EngineeringContextRelationshipService(db))
    relationships = _engineering_relationship_application(db, organization)
    graph = ProjectContextGraphAdapter(
        project=project, workspace=workspace,
        execution=execution.service, execution_actor=execution.actor,
        deliverables=deliverables.service, deliverable_actor=deliverables.actor,
        controls=controls.service, control_actor=controls.actor,
        objects=objects, object_actor=_engineering_object_actor(actor),
        context=context_adapter, evidence=evidence, evidence_actor=_evidence_actor(actor),
        files=files.service, file_actor_id=files.actor_id,
        reports=reports, report_actor=_technical_report_actor(actor),
        memory=memory.service, memory_actor=memory.actor,
        relationships=relationships.service, relationship_actor=relationships.actor,
        context_relationships=context_relationships,
    )
    owners = _ProjectContextOwners(
        basis=ProjectBasisProjectContextAdapter(foundation.service, foundation.actor, "project_basis"),
        execution=ExecutionProjectContextAdapter(execution.service, execution.actor, "execution"),
        deliverables=DeliverableProjectContextAdapter(deliverables.service, deliverables.actor, "deliverable"),
        controls=ProjectControlProjectContextAdapter(controls.service, controls.actor),
        context=context_adapter,
        objects=EngineeringObjectProjectContextAdapter(objects, _engineering_object_actor(actor), "engineering_object"),
        evidence=EvidenceProjectContextAdapter(evidence, _evidence_actor(actor), "evidence"),
        files=SupportingFileProjectContextAdapter(files.service, files.actor_id, "supporting_file"),
        reports=TechnicalReportProjectContextAdapter(reports, actor, "technical_report"),
        memory=OrganizationalMemoryProjectContextAdapter(memory.service, memory.actor, "organizational_memory"),
        graph=graph,
    )
    return ProjectContextApplication(ProjectContextService(owners), actor, organization.user)


def get_organizational_memory_service_for_context(db: Session):
    from app.dependencies.organizational_memory import get_organizational_memory_service
    return get_organizational_memory_service(db)




def _engineering_object_actor(actor):
    from app.models.engineering_object_command import AuthenticatedActor
    return AuthenticatedActor(actor_id=actor.actor_id, organization_id=actor.organization_id)
def _evidence_actor(actor):
    from app.models.evidence_command import EvidenceActor
    return EvidenceActor(actor_id=actor.actor_id, organization_id=actor.organization_id)
def _technical_report_actor(actor):
    from app.models.technical_report_command import TechnicalReportActor
    return TechnicalReportActor(actor_id=actor.actor_id, organization_id=actor.organization_id)
def _engineering_relationship_application(db, organization):
    """Compose the canonical service without importing a transport module."""
    from types import SimpleNamespace
    from app.models.engineering_relationship_command import AuthenticatedRelationshipActor
    from app.repositories.engineering_relationship_repository import SqlAlchemyEngineeringRelationshipRepository
    from app.repositories.engineering_relationship_unit_of_work import (
        SqlAlchemyEngineeringRelationshipUnitOfWork,
        SqlAlchemyRelationshipAuthorizationPolicy,
        SqlAlchemyRelationshipValidator,
        UtcRelationshipClock,
    )
    from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceValidator
    from app.services.engineering_relationship_service import EngineeringRelationshipService
    repository=SqlAlchemyEngineeringRelationshipRepository(db)
    evidence=SqlAlchemyEvidenceValidator(db)
    actor=AuthenticatedRelationshipActor(actor_id=organization.user.id,organization_id=organization.organization_id)
    service=EngineeringRelationshipService(
        uow_factory=lambda:SqlAlchemyEngineeringRelationshipUnitOfWork(SessionLocal),
        authorization=SqlAlchemyRelationshipAuthorizationPolicy(db),
        validator=SqlAlchemyRelationshipValidator(db,repository,evidence),
        clock=UtcRelationshipClock(),
    )
    return SimpleNamespace(service=service,actor=actor)
def _file_scope(actor, scope):
    from app.models.supporting_file_command import SupportingFileScope
    return SupportingFileScope(organization_id=actor.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)

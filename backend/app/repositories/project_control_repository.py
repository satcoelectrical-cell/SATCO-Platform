from sqlalchemy.orm import Session
from app.models.project_control import ProjectRisk,ProjectIssue,ProjectDecision,ProjectChange,ProjectChangeImpact,ProjectControlIdempotency,ProjectRiskHistory,ProjectIssueHistory,ProjectDecisionHistory,ProjectChangeHistory
class ProjectControlRepository:
    def __init__(self,session:Session): self.session=session
    def add(self,value): self.session.add(value)
    def flush(self): self.session.flush()
    def get(self,kind,*,id,organization_id,lock=False):
        model={"risk":ProjectRisk,"issue":ProjectIssue,"decision":ProjectDecision,"change":ProjectChange}[kind]; query=self.session.query(model).filter_by(id=id,organization_id=organization_id); return (query.with_for_update() if lock else query).first()
    def list(self,kind,*,organization_id,project_id,limit=100):
        model={"risk":ProjectRisk,"issue":ProjectIssue,"decision":ProjectDecision,"change":ProjectChange}[kind]; return self.session.query(model).filter_by(organization_id=organization_id,project_id=project_id).order_by(model.created_at.desc(),model.id.asc()).limit(limit).all()
    def list_history(self,kind,*,control_id,organization_id,project_id,limit=100):
        model={"risk":ProjectRiskHistory,"issue":ProjectIssueHistory,"decision":ProjectDecisionHistory,"change":ProjectChangeHistory}[kind]
        key=f"{kind}_id"
        return self.session.query(model).filter_by(**{key:control_id, "organization_id":organization_id, "project_id":project_id}).order_by(model.aggregate_version.asc(),model.id.asc()).limit(limit).all()
    def list_impacts(self,*,change_id,organization_id,project_id):
        return self.session.query(ProjectChangeImpact).filter_by(change_id=change_id,organization_id=organization_id,project_id=project_id).order_by(ProjectChangeImpact.id.asc()).limit(100).all()
    def get_idempotency(self,*,organization_id,project_id,actor_id,operation,idempotency_key,lock=True):
        query=self.session.query(ProjectControlIdempotency).filter_by(organization_id=organization_id,project_id=project_id,actor_id=actor_id,operation=operation,idempotency_key=idempotency_key); return (query.with_for_update() if lock else query).first()
    def get_project(self,*,project_id,organization_id,lock=False):
        from app.models.project import Project
        query=self.session.query(Project).filter_by(id=project_id,organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()
    def get_impact(self,*,impact_id,organization_id,lock=False):
        query=self.session.query(ProjectChangeImpact).filter_by(id=impact_id,organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()
    def get_impact_by_target(self,*,change_id,target_kind,target_id,organization_id,lock=False):
        query=self.session.query(ProjectChangeImpact).filter_by(change_id=change_id,target_kind=target_kind,target_id=target_id,organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()

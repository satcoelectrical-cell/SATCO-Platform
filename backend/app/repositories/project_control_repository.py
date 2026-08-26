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
    def list_graph_incident(self,*,selector_kind,selector_id,organization_id,project_id,limit=91):
        """Exact predecessor/impact/target incidence; never lists all controls."""
        rows=[]
        if selector_kind in {"human_decision","change"}:
            kind="decision" if selector_kind=="human_decision" else "change"
            model={"decision":ProjectDecision,"change":ProjectChange}[kind]
            current=self.get(kind,id=selector_id,organization_id=organization_id)
            values=[] if current is None or current.project_id!=project_id else [current]
            successors=(self.session.query(model).filter_by(predecessor_id=selector_id,
                organization_id=organization_id,project_id=project_id).order_by(model.id).limit(limit+1).all())
            relation=f"{kind}_successor"; node_kind=selector_kind
            for value in values:
                if value.predecessor_id is not None:
                    rows.append((relation,node_kind,value.predecessor_id,node_kind,value.id,value.version))
                if kind=="change":
                    for impact in self.list_impacts(change_id=value.id,organization_id=organization_id,project_id=project_id):
                        rows.append(("change_impact","change",value.id,"change_impact",impact.id,value.version))
            rows.extend((relation,node_kind,selector_id,node_kind,value.id,value.version) for value in successors)
        elif selector_kind=="change_impact":
            impact=self.get_impact(impact_id=selector_id,organization_id=organization_id)
            if impact is not None and impact.project_id==project_id:
                change=self.get("change",id=impact.change_id,organization_id=organization_id)
                version=1 if change is None else change.version
                rows.extend((("change_impact","change",impact.change_id,"change_impact",impact.id,version),
                             ("impact_target","change_impact",impact.id,impact.target_kind,impact.target_id,version)))
        elif selector_kind in {"activity","milestone","deliverable","deliverable_revision","evidence","supporting_file"}:
            impacts=(self.session.query(ProjectChangeImpact).filter_by(target_kind=selector_kind,target_id=selector_id,
                organization_id=organization_id,project_id=project_id).order_by(ProjectChangeImpact.id).limit(limit+1).all())
            for impact in impacts:
                change=self.get("change",id=impact.change_id,organization_id=organization_id)
                rows.append(("impact_target","change_impact",impact.id,selector_kind,selector_id,1 if change is None else change.version))
        ordered=sorted(set(rows),key=lambda item:(item[0],str(item[2]),str(item[4])))
        return tuple(ordered[:limit]),len(ordered)>limit

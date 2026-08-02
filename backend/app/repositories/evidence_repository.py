"""SQLAlchemy Evidence repository without policy or transaction ownership."""
from typing import Mapping
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models.evidence import Evidence

class SqlAlchemyEvidenceRepository:
    def __init__(self, session: Session): self.session = session
    def get_scoped(self, evidence_id: UUID, organization_id: UUID):
        item = self.session.query(Evidence).filter_by(id=evidence_id, organization_id=organization_id).first()
        if item is not None: self.session.expunge(item)
        return item
    def list_scoped(self, *, organization_id: UUID, project_id: int, filters: Mapping, page: int, size: int):
        query = self.session.query(Evidence).filter(Evidence.organization_id==organization_id, (Evidence.project_id==project_id)|(Evidence.project_id.is_(None)))
        for name in ("workspace_id","lifecycle","source_kind","source_standing"):
            value=filters.get(name)
            if value is not None: query=query.filter(getattr(Evidence,name)==getattr(value,"value",value))
        total=query.count(); items=query.order_by(Evidence.created_at,Evidence.id).offset((page-1)*size).limit(size).all()
        for item in items: self.session.expunge(item)
        return items,total
    def add(self, evidence: Evidence): self.session.add(evidence); self.session.flush()
    def persist_expected_version(self, evidence: Evidence, expected_version: int):
        result=self.session.execute(update(Evidence).where(Evidence.id==evidence.id,Evidence.organization_id==evidence.organization_id,Evidence.version==expected_version).values(lifecycle=evidence.lifecycle,version=evidence.version,updated_at=evidence.updated_at))
        self.session.flush(); return result.rowcount==1

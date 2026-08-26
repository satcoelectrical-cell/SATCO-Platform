"""SQLAlchemy Evidence repository without policy or transaction ownership."""
from typing import Mapping
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models.evidence import Evidence
from app.models.supporting_file import EvidenceSupportingFileLink

class SqlAlchemyEvidenceRepository:
    def __init__(self, session: Session): self.session = session
    def get_scoped(self, evidence_id: UUID, organization_id: UUID):
        item = self.session.query(Evidence).filter_by(id=evidence_id, organization_id=organization_id).first()
        if item is not None: self.session.expunge(item)
        return item
    def get_scoped_for_update(self, evidence_id: UUID, organization_id: UUID):
        return self.session.query(Evidence).filter_by(id=evidence_id, organization_id=organization_id).with_for_update().first()
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
        with self.session.no_autoflush:
            result=self.session.execute(update(Evidence).where(Evidence.id==evidence.id,Evidence.organization_id==evidence.organization_id,Evidence.version==expected_version).values(lifecycle=evidence.lifecycle,version=evidence.version,updated_at=evidence.updated_at).execution_options(synchronize_session=False))
        if result.rowcount == 1 and evidence in self.session:
            self.session.expire(evidence)
        self.session.flush(); return result.rowcount==1
    def stage_supporting_file_links(self, *, evidence, asset_ids, actor_id, linked_at):
        for ordinal, asset_id in enumerate(asset_ids):
            self.session.add(EvidenceSupportingFileLink(
                evidence_id=evidence.id, asset_id=asset_id,
                organization_id=evidence.organization_id,
                project_id=evidence.project_id, workspace_id=evidence.workspace_id,
                evidence_version=evidence.version, ordinal=ordinal,
                linked_by_id=actor_id, linked_at=linked_at,
            ))
        self.session.flush()
    def list_graph_links_for_evidence(self, *, evidence_id, organization_id, project_id, workspace_id, limit=91):
        return self.session.query(EvidenceSupportingFileLink).filter_by(evidence_id=evidence_id,organization_id=organization_id,project_id=project_id,workspace_id=workspace_id).order_by(EvidenceSupportingFileLink.ordinal,EvidenceSupportingFileLink.asset_id).limit(limit).all()
    def list_graph_links_for_asset(self, *, asset_id, organization_id, project_id, workspace_id, limit=91):
        query=self.session.query(EvidenceSupportingFileLink).filter_by(asset_id=asset_id,organization_id=organization_id,project_id=project_id)
        if workspace_id is not None: query=query.filter(EvidenceSupportingFileLink.workspace_id==workspace_id)
        return query.order_by(EvidenceSupportingFileLink.evidence_id,EvidenceSupportingFileLink.ordinal).limit(limit).all()

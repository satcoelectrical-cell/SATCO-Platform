from sqlalchemy.orm import Session

from app.models.engineering_deliverable import EngineeringDeliverable, EngineeringDeliverableRevision, EngineeringDeliverableHistory, EngineeringDeliverableIdempotency


class EngineeringDeliverableRepository:
    """No-commit persistence boundary for deliverable control."""
    def __init__(self, session: Session): self.session = session
    def get(self, *, deliverable_id, organization_id, lock=False):
        query = self.session.query(EngineeringDeliverable).filter_by(id=deliverable_id, organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()
    def get_current_revision(self, *, deliverable, lock=False):
        query = self.session.query(EngineeringDeliverableRevision).filter_by(deliverable_id=deliverable.id, sequence=deliverable.current_revision_sequence)
        return (query.with_for_update() if lock else query).first()
    def get_revision(self, *, revision_id, organization_id, lock=False):
        """Exact canonical selector; deliberately no history/list fallback."""
        query = self.session.query(EngineeringDeliverableRevision).filter_by(
            id=revision_id, organization_id=organization_id,
        )
        return (query.with_for_update() if lock else query).first()
    def get_revision_by_supporting_file(self, *, asset_id, organization_id):
        return self.session.query(EngineeringDeliverableRevision).filter_by(
            supporting_file_id=asset_id, organization_id=organization_id,
        ).first()
    def list(self, *, organization_id, project_id, limit=100):
        return self.session.query(EngineeringDeliverable).filter_by(organization_id=organization_id, project_id=project_id).order_by(EngineeringDeliverable.target_date.asc().nullslast(), EngineeringDeliverable.code, EngineeringDeliverable.id).limit(limit).all()
    def list_graph_incident(self, *, selector_kind, selector_id, organization_id, project_id, limit=91):
        """Targeted FK/identity incident read; no project-wide deliverable list."""
        rows=[]; selected_revision=None
        if selector_kind == "deliverable":
            values=[self.get(deliverable_id=selector_id, organization_id=organization_id)]
        elif selector_kind == "activity":
            values=(self.session.query(EngineeringDeliverable).filter_by(
                activity_id=selector_id, organization_id=organization_id, project_id=project_id
            ).order_by(EngineeringDeliverable.id).limit(limit + 1).all())
        elif selector_kind == "milestone":
            values=(self.session.query(EngineeringDeliverable).filter_by(
                milestone_id=selector_id, organization_id=organization_id, project_id=project_id
            ).order_by(EngineeringDeliverable.id).limit(limit + 1).all())
        elif selector_kind in {"deliverable_revision", "supporting_file"}:
            revision=(self.get_revision(revision_id=selector_id, organization_id=organization_id)
                      if selector_kind == "deliverable_revision"
                      else self.get_revision_by_supporting_file(asset_id=selector_id, organization_id=organization_id))
            selected_revision=revision
            values=[] if revision is None else [self.get(deliverable_id=revision.deliverable_id, organization_id=organization_id)]
        else:
            return (), False
        for value in values:
            if value is None or value.project_id != project_id:
                continue
            if value.activity_id is not None:
                rows.append(("deliverable_activity", "deliverable", value.id, "activity", value.activity_id, value.version))
            if value.milestone_id is not None:
                rows.append(("deliverable_milestone", "deliverable", value.id, "milestone", value.milestone_id, value.version))
            revision=selected_revision or self.get_current_revision(deliverable=value)
            if revision is not None:
                rows.append(("deliverable_revision", "deliverable", value.id, "deliverable_revision", revision.id, revision.version))
                if revision.supporting_file_id is not None:
                    rows.append(("revision_representation", "deliverable_revision", revision.id, "supporting_file", revision.supporting_file_id, revision.version))
        ordered=sorted(set(rows), key=lambda item:(item[0],str(item[2]),str(item[4])))
        return tuple(ordered[:limit]), len(ordered)>limit
    def revisions(self, *, deliverable_id):
        return self.session.query(EngineeringDeliverableRevision).filter_by(deliverable_id=deliverable_id).order_by(EngineeringDeliverableRevision.sequence).all()
    def revision_creation_history(self, *, revision_id, organization_id):
        return self.session.query(EngineeringDeliverableHistory).filter(
            EngineeringDeliverableHistory.revision_id == revision_id,
            EngineeringDeliverableHistory.organization_id == organization_id,
            EngineeringDeliverableHistory.event_type.in_(("deliverable_created", "revision_created")),
        ).order_by(EngineeringDeliverableHistory.occurred_at).all()
    def rework_resolution_history(self, *, revision_id, organization_id):
        return self.session.query(EngineeringDeliverableHistory).filter_by(
            revision_id=revision_id, organization_id=organization_id,
            event_type="rework_resolved",
        ).all()
    def list_rework_history(self, *, organization_id, project_id, source_cutoff, limit=1001):
        return (self.session.query(EngineeringDeliverableHistory, EngineeringDeliverable, EngineeringDeliverableRevision)
                .join(EngineeringDeliverable, EngineeringDeliverable.id == EngineeringDeliverableHistory.deliverable_id)
                .join(EngineeringDeliverableRevision, EngineeringDeliverableRevision.id == EngineeringDeliverableHistory.revision_id)
                .filter(EngineeringDeliverableHistory.organization_id == organization_id,
                        EngineeringDeliverable.organization_id == organization_id,
                        EngineeringDeliverable.project_id == project_id,
                        EngineeringDeliverableRevision.organization_id == organization_id,
                        EngineeringDeliverableRevision.project_id == project_id,
                        EngineeringDeliverableHistory.occurred_at <= source_cutoff,
                        EngineeringDeliverableHistory.event_type.in_((
                            "deliverable_created", "revision_created", "rework_resolved",
                        )))
                .order_by(EngineeringDeliverableHistory.occurred_at,
                          EngineeringDeliverableHistory.deliverable_id,
                          EngineeringDeliverableHistory.aggregate_version)
                .limit(limit).all())
    def count_project_revisions_at(self, *, organization_id, project_id, source_cutoff):
        return (self.session.query(EngineeringDeliverableRevision)
                .join(EngineeringDeliverable,
                      EngineeringDeliverable.id == EngineeringDeliverableRevision.deliverable_id)
                .filter(EngineeringDeliverableRevision.organization_id == organization_id,
                        EngineeringDeliverableRevision.project_id == project_id,
                        EngineeringDeliverable.organization_id == organization_id,
                        EngineeringDeliverable.project_id == project_id,
                        EngineeringDeliverableRevision.created_at <= source_cutoff)
                .count())
    def list_transition_history(self, *, organization_id, project_id, limit=1001):
        """Canonical history only; caller must authorize before this selection."""
        return (self.session.query(EngineeringDeliverableHistory, EngineeringDeliverable, EngineeringDeliverableRevision)
                .join(EngineeringDeliverable, EngineeringDeliverable.id == EngineeringDeliverableHistory.deliverable_id)
                .join(EngineeringDeliverableRevision, EngineeringDeliverableRevision.id == EngineeringDeliverableHistory.revision_id)
                .filter(EngineeringDeliverableHistory.organization_id == organization_id,
                        EngineeringDeliverable.organization_id == organization_id,
                        EngineeringDeliverable.project_id == project_id,
                        EngineeringDeliverableRevision.organization_id == organization_id,
                        EngineeringDeliverableHistory.event_type.in_((
                            "deliverable_created", "revision_created", "revision_transitioned",
                            "package_revision_transitioned",
                        )))
                .order_by(EngineeringDeliverableHistory.occurred_at,
                          EngineeringDeliverableHistory.deliverable_id,
                          EngineeringDeliverableHistory.aggregate_version)
                .limit(limit).all())
    def get_idempotency(self, *, organization_id, actor_id, operation, idempotency_key, lock=True):
        query = self.session.query(EngineeringDeliverableIdempotency).filter_by(organization_id=organization_id, actor_id=actor_id, operation=operation, idempotency_key=idempotency_key)
        return (query.with_for_update() if lock else query).first()
    def add(self, value): self.session.add(value)
    def flush(self): self.session.flush()

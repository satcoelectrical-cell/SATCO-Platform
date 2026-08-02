"""SQLAlchemy persistence adapter for EngineeringRelationship."""

from collections import deque
from typing import Mapping
from uuid import UUID

from sqlalchemy import or_, text, update
from sqlalchemy.orm import Session

from app.enums import RelationshipFamily, RelationshipType
from app.models.engineering_relationship import EngineeringRelationship


class SqlAlchemyEngineeringRelationshipRepository:
    """Persist and query aggregates without authorization or transaction control."""

    def __init__(self, session: Session):
        self.session = session

    def get_authorized(self, relationship_id: UUID, organization_id: UUID):
        item = self.session.query(EngineeringRelationship).filter_by(
            id=relationship_id, organization_id=organization_id
        ).first()
        if item is not None:
            self.session.expunge(item)
        return item

    def add(self, relationship: EngineeringRelationship) -> None:
        self.session.add(relationship)
        self.session.flush()

    def persist_expected_version(self, relationship, expected_version: int) -> bool:
        values = {
            "lifecycle": relationship.lifecycle,
            "authority_standing": relationship.authority_standing,
            "evidence_references": relationship.evidence_references,
            "version": relationship.version,
            "steward_id": relationship.steward_id,
            "reviewer_id": relationship.reviewer_id,
            "approver_id": relationship.approver_id,
            "updated_at": relationship.updated_at,
        }
        result = self.session.execute(
            update(EngineeringRelationship).where(
                EngineeringRelationship.id == relationship.id,
                EngineeringRelationship.organization_id == relationship.organization_id,
                EngineeringRelationship.version == expected_version,
            ).values(**values)
        )
        self.session.flush()
        return result.rowcount == 1

    def active_duplicate_exists(self, **identity) -> bool:
        values = {
            key: getattr(value, "value", value) for key, value in identity.items()
        }
        return self.session.query(EngineeringRelationship.id).filter_by(
            **values
        ).filter(
            EngineeringRelationship.lifecycle.in_(("proposed", "current"))
        ).first() is not None

    def acquire_cycle_lock(self, *, organization_id: UUID, project_id: int,
                           relationship_family: RelationshipFamily,
                           relationship_type: RelationshipType) -> None:
        key = f"{organization_id}:{project_id}:{relationship_family.value}:{relationship_type.value}"
        self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": key},
        )

    def creates_cycle(self, *, organization_id: UUID, project_id: int,
                      source_object_id: UUID, target_object_id: UUID,
                      relationship_family: RelationshipFamily,
                      relationship_type: RelationshipType) -> bool:
        self.acquire_cycle_lock(
            organization_id=organization_id, project_id=project_id,
            relationship_family=relationship_family,
            relationship_type=relationship_type,
        )
        frontier = [target_object_id]
        visited: set[UUID] = set()
        while frontier:
            if source_object_id in frontier:
                return True
            visited.update(frontier)
            rows = self.session.query(
                EngineeringRelationship.target_object_id
            ).filter(
                EngineeringRelationship.organization_id == organization_id,
                EngineeringRelationship.project_id == project_id,
                EngineeringRelationship.relationship_family
                == relationship_family.value,
                EngineeringRelationship.relationship_type
                == relationship_type.value,
                EngineeringRelationship.lifecycle.in_(("proposed", "current")),
                EngineeringRelationship.source_object_id.in_(frontier),
            ).all()
            frontier = [row[0] for row in rows if row[0] not in visited]
        return False

    def list_for_endpoint(self, *, organization_id: UUID, object_id: UUID,
                          filters: Mapping, page: int, size: int):
        query = self._filtered(
            self.session.query(EngineeringRelationship).filter(
                EngineeringRelationship.organization_id == organization_id
            ), filters,
        )
        direction = filters.get("direction", "both")
        if direction == "outgoing":
            query = query.filter(EngineeringRelationship.source_object_id == object_id)
        elif direction == "incoming":
            query = query.filter(EngineeringRelationship.target_object_id == object_id)
        else:
            query = query.filter(or_(
                EngineeringRelationship.source_object_id == object_id,
                EngineeringRelationship.target_object_id == object_id,
            ))
        total = query.count()
        items = query.order_by(
            EngineeringRelationship.relationship_type,
            EngineeringRelationship.source_object_id,
            EngineeringRelationship.target_object_id,
            EngineeringRelationship.id,
        ).offset((page - 1) * size).limit(size).all()
        for item in items:
            self.session.expunge(item)
        return items, total

    def bounded_neighborhood(self, *, organization_id: UUID, object_id: UUID,
                             filters: Mapping, max_depth: int,
                             max_results: int):
        visited = {object_id}
        queue = deque([(object_id, 0)])
        found: dict[UUID, EngineeringRelationship] = {}
        while queue and len(found) <= max_results:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            query = self.session.query(EngineeringRelationship).filter(
                EngineeringRelationship.organization_id == organization_id
            )
            direction = filters.get("direction", "both")
            if direction == "outgoing":
                query = query.filter(
                    EngineeringRelationship.source_object_id == node
                )
            elif direction == "incoming":
                query = query.filter(
                    EngineeringRelationship.target_object_id == node
                )
            else:
                query = query.filter(or_(
                    EngineeringRelationship.source_object_id == node,
                    EngineeringRelationship.target_object_id == node,
                ))
            query = self._filtered(query, filters)
            for edge in query.order_by(EngineeringRelationship.id).all():
                found.setdefault(edge.id, edge)
                other = (
                    edge.target_object_id
                    if edge.source_object_id == node else edge.source_object_id
                )
                if other not in visited:
                    visited.add(other); queue.append((other, depth + 1))
                if len(found) > max_results:
                    break
        ordered = sorted(found.values(), key=lambda edge: (
            edge.relationship_type, str(edge.source_object_id),
            str(edge.target_object_id), str(edge.id),
        ))
        truncated = len(ordered) > max_results
        return ordered[:max_results], visited, truncated

    def bounded_path(self, *, organization_id: UUID, source_object_id: UUID,
                     target_object_id: UUID, filters: Mapping,
                     max_depth: int, max_results: int):
        visited = {source_object_id}
        queue = deque([(source_object_id, 0)])
        predecessor: dict[UUID, tuple[UUID, EngineeringRelationship]] = {}
        examined = 0
        while queue and examined < max_results:
            node, depth = queue.popleft()
            if node == target_object_id:
                break
            if depth >= max_depth:
                continue
            query = self.session.query(EngineeringRelationship).filter(
                EngineeringRelationship.organization_id == organization_id
            )
            direction = filters.get("direction", "both")
            if direction == "outgoing":
                query = query.filter(EngineeringRelationship.source_object_id == node)
            elif direction == "incoming":
                query = query.filter(EngineeringRelationship.target_object_id == node)
            else:
                query = query.filter(or_(
                    EngineeringRelationship.source_object_id == node,
                    EngineeringRelationship.target_object_id == node,
                ))
            for edge in self._filtered(query, filters).order_by(
                EngineeringRelationship.relationship_type,
                EngineeringRelationship.source_object_id,
                EngineeringRelationship.target_object_id,
                EngineeringRelationship.id,
            ).all():
                examined += 1
                other = edge.target_object_id if edge.source_object_id == node else edge.source_object_id
                if other not in visited:
                    visited.add(other)
                    predecessor[other] = (node, edge)
                    queue.append((other, depth + 1))
                if examined >= max_results:
                    break
        if target_object_id not in predecessor and target_object_id != source_object_id:
            return [], visited, examined >= max_results
        path = []
        node = target_object_id
        while node != source_object_id:
            prior, edge = predecessor[node]
            path.append(edge)
            node = prior
        path.reverse()
        return path, visited, examined >= max_results

    @staticmethod
    def _filtered(query, filters: Mapping):
        for name in ("relationship_family", "relationship_type", "lifecycle",
                     "authority_standing", "workspace_id"):
            value = filters.get(name)
            if value is not None:
                query = query.filter(
                    getattr(EngineeringRelationship, name)
                    == getattr(value, "value", value)
                )
        return query

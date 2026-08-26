"""Typed owner adapter over the public Context Relationship service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Protocol

from app.exceptions.engineering_context_relationship import (
    RelationshipForbidden,
    RelationshipNotFound,
)
from app.schemas.project_context import (
    AuthorityClassification,
    ContextNodeKind,
    ContextNodeSelector,
    ContextRelationshipEndpointKind,
    ContextRelationshipEndpointProjection,
    ContextRelationshipKind,
    ContextRelationshipProjection,
    FactProvenance,
    GraphDirection,
    OwnerPage,
    OwnerProtected,
    OwnerReadResult,
    OwnerUnavailable,
    ProjectContextActor,
    ProjectContextScope,
    SectionPageRequest,
    TemporalClassification,
)

class OwnerPrincipal(Protocol):
    id: int


MEANING_MAP = {
    "requires": ContextRelationshipKind.CONTEXT_REQUIRES,
    "provided_by": ContextRelationshipKind.CONTEXT_PROVIDED_BY,
    "consumed_by": ContextRelationshipKind.CONTEXT_CONSUMED_BY,
    "potentially_affects": ContextRelationshipKind.CONTEXT_POTENTIALLY_AFFECTS,
}


class EngineeringContextRelationshipProjectContextAdapter:
    """Expose only current eligible owner relationships; no graph expansion."""

    def __init__(self, service: object) -> None:
        self._service = service

    def list_authorized_incident(
        self, *, actor: ProjectContextActor, scope: ProjectContextScope,
        selector: ContextNodeSelector, direction: GraphDirection,
        page: SectionPageRequest, current_user: OwnerPrincipal,
    ) -> OwnerPage | OwnerReadResult:
        if selector.kind not in {
            ContextNodeKind.PROJECT, ContextNodeKind.WORKSPACE,
            ContextNodeKind.ENGINEERING_CONTEXT,
        }:
            return OwnerProtected()
        if current_user.id != actor.actor_id:
            return OwnerProtected()
        try:
            response = self._service.list_relationships(
                project_id=scope.project_id, workspace_id=scope.workspace_id,
                current_user=current_user, page=1, size=min(page.page_size, 50),
                include_withdrawn=False,
            )
            items = tuple(
                item for item in (
                    self._project(record, actor, scope)
                    for record in self._items(response)
                )
                if self._incident(item, selector, direction)
            )
            return OwnerPage(
                items=items,
                last_evaluated_key=str(items[-1].relationship_id) if items else None,
                observed_at=datetime.now(timezone.utc),
            )
        except (RelationshipForbidden, RelationshipNotFound):
            return OwnerProtected()
        except Exception:
            return OwnerUnavailable()

    @staticmethod
    def _items(response: object) -> tuple[Mapping[str, object], ...]:
        if not isinstance(response, Mapping):
            raise ValueError("owner response is invalid")
        items = response.get("items")
        if not isinstance(items, list) or len(items) > 50:
            raise ValueError("owner items are invalid")
        if any(not isinstance(item, Mapping) for item in items):
            raise ValueError("owner items are invalid")
        return tuple(items)

    @staticmethod
    def _endpoint(record: Mapping[str, object], prefix: str) -> ContextRelationshipEndpointProjection:
        raw_kind = record.get(f"{prefix}_kind")
        kind_map = {
            "project": ContextRelationshipEndpointKind.PROJECT,
            "workspace": ContextRelationshipEndpointKind.WORKSPACE,
            "context": ContextRelationshipEndpointKind.ENGINEERING_CONTEXT,
        }
        kind = kind_map.get(raw_kind)
        if kind is None:
            raise ValueError("endpoint kind is excluded")
        key = {
            ContextRelationshipEndpointKind.PROJECT: f"{prefix}_project_id",
            ContextRelationshipEndpointKind.WORKSPACE: f"{prefix}_workspace_id",
            ContextRelationshipEndpointKind.ENGINEERING_CONTEXT: f"{prefix}_context_id",
        }[kind]
        selector = record.get(key)
        if type(selector) is not int or selector < 1:
            raise ValueError("endpoint selector is invalid")
        return ContextRelationshipEndpointProjection(kind=kind, selector=selector)

    @classmethod
    def _project(
        cls, record: Mapping[str, object], actor: ProjectContextActor,
        scope: ProjectContextScope,
    ) -> ContextRelationshipProjection:
        if record.get("project_id") != scope.project_id:
            raise RelationshipForbidden()
        if record.get("lifecycle") != "current":
            raise RelationshipForbidden()
        meaning = MEANING_MAP.get(record.get("meaning"))
        if meaning is None:
            raise ValueError("relationship meaning is excluded")
        relationship_id = record.get("id")
        version = record.get("version")
        key = record.get("relationship_key")
        if type(relationship_id) is not int or relationship_id < 1:
            raise ValueError("relationship selector is invalid")
        if type(version) is not int or version < 1 or not isinstance(key, str) or not key:
            raise ValueError("relationship metadata is invalid")
        return ContextRelationshipProjection(
            relationship_id=relationship_id, relationship_key=key,
            project_id=scope.project_id, meaning=meaning,
            source=cls._endpoint(record, "source"),
            target=cls._endpoint(record, "target"),
            lifecycle="current", version=version,
            provenance=FactProvenance(
                owner_kind="engineering_context_relationship",
                selector=str(relationship_id), version=version, standing="current",
                source_observed_at=None, observed_at=datetime.now(timezone.utc),
                authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,
                temporal_class=TemporalClassification.CURRENT,
            ),
        )

    @staticmethod
    def _incident(
        item: ContextRelationshipProjection, selector: ContextNodeSelector,
        direction: GraphDirection,
    ) -> bool:
        expected_kind = {
            ContextNodeKind.PROJECT: ContextRelationshipEndpointKind.PROJECT,
            ContextNodeKind.WORKSPACE: ContextRelationshipEndpointKind.WORKSPACE,
            ContextNodeKind.ENGINEERING_CONTEXT: ContextRelationshipEndpointKind.ENGINEERING_CONTEXT,
        }[selector.kind]
        value = int(selector.value)
        source_match = item.source.kind is expected_kind and item.source.selector == value
        target_match = item.target.kind is expected_kind and item.target.selector == value
        return (
            source_match if direction is GraphDirection.OUTGOING
            else target_match if direction is GraphDirection.INCOMING
            else source_match or target_match
        )

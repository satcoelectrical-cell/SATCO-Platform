"""Typed owner adapter over the public Engineering Context service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Protocol

from app.exceptions.engineering_context import ContextForbidden, ContextNotFound
from app.schemas.project_context import (
    AuthorityClassification,
    ContextAssumptionPayload,
    ContextEngineeringValuePayload,
    ContextFactPayload,
    ContextNodeKind,
    ContextNodeSelector,
    ContextPayloadAbsent,
    EngineeringContextProjection,
    FactProvenance,
    OwnerPage,
    OwnerProtected,
    OwnerReadResult,
    OwnerResolved,
    OwnerUnavailable,
    ProjectContextActor,
    ProjectContextScope,
    SectionPageRequest,
    TemporalClassification,
)

class OwnerPrincipal(Protocol):
    id: int


class EngineeringContextProjectContextAdapter:
    """Narrow public owner-service responses; never inspect owner persistence."""

    def __init__(self, service: object) -> None:
        self._service = service

    def list_authorized_current(
        self, *, actor: ProjectContextActor, scope: ProjectContextScope,
        page: SectionPageRequest, current_user: OwnerPrincipal,
    ) -> OwnerPage | OwnerReadResult:
        if current_user.id != actor.actor_id:
            return OwnerProtected()
        try:
            response = self._service.list_for_scope(
                project_id=scope.project_id, workspace_id=scope.workspace_id,
                current_user=current_user, page=1, size=page.page_size,
                include_withdrawn=False,
            )
            items = tuple(
                self._project(item, actor, scope)
                for item in self._items(response)
            )
            return OwnerPage(
                items=items,
                last_evaluated_key=str(items[-1].context_id) if items else None,
                observed_at=datetime.now(timezone.utc),
            )
        except (ContextForbidden, ContextNotFound):
            return OwnerProtected()
        except Exception:
            return OwnerUnavailable()

    def get_authorized_context(
        self, *, actor: ProjectContextActor, scope: ProjectContextScope,
        selector: ContextNodeSelector, current_user: OwnerPrincipal,
    ) -> OwnerReadResult:
        if selector.kind is not ContextNodeKind.ENGINEERING_CONTEXT:
            return OwnerProtected()
        if current_user.id != actor.actor_id:
            return OwnerProtected()
        try:
            response = self._service.get(int(selector.value), current_user)
            return OwnerResolved(item=self._project(response, actor, scope))
        except (ContextForbidden, ContextNotFound):
            return OwnerProtected()
        except Exception:
            return OwnerUnavailable()

    @staticmethod
    def _items(response: object) -> tuple[Mapping[str, object], ...]:
        if not isinstance(response, Mapping):
            raise ValueError("owner response is invalid")
        items = response.get("items")
        if not isinstance(items, list):
            raise ValueError("owner items are invalid")
        if len(items) > 100 or any(not isinstance(item, Mapping) for item in items):
            raise ValueError("owner items exceed contract")
        return tuple(items)

    @staticmethod
    def _project(
        response: Mapping[str, object], actor: ProjectContextActor,
        scope: ProjectContextScope,
    ) -> EngineeringContextProjection:
        context_id = response.get("id")
        project_id = response.get("project_id")
        workspace_id = response.get("workspace_id")
        if type(context_id) is not int or context_id < 1:
            raise ValueError("owner context selector is invalid")
        if project_id != scope.project_id:
            raise ContextForbidden()
        if scope.workspace_id is not None and workspace_id != scope.workspace_id:
            raise ContextForbidden()
        if response.get("lifecycle") != "current":
            raise ContextForbidden()
        payload = response.get("payload")
        kind = response.get("kind")
        if kind == "qualified_fact" and isinstance(payload, Mapping):
            typed_payload = ContextFactPayload(
                statement=EngineeringContextProjectContextAdapter._text(payload, "statement"),
                uncertainty=EngineeringContextProjectContextAdapter._optional_text(payload, "uncertainty"),
            )
        elif kind == "qualified_engineering_value" and isinstance(payload, Mapping):
            typed_payload = ContextEngineeringValuePayload(
                numeric_value=EngineeringContextProjectContextAdapter._optional_text(payload, "numeric_value"),
                unit=EngineeringContextProjectContextAdapter._optional_text(payload, "unit"),
                quantity_type=EngineeringContextProjectContextAdapter._optional_text(payload, "quantity_type"),
                basis=EngineeringContextProjectContextAdapter._optional_text(payload, "basis"),
            )
        elif kind == "assumption" and isinstance(payload, Mapping):
            typed_payload = ContextAssumptionPayload(
                statement=EngineeringContextProjectContextAdapter._text(payload, "statement"),
                reason=EngineeringContextProjectContextAdapter._optional_text(payload, "reason"),
                consequence=EngineeringContextProjectContextAdapter._optional_text(payload, "consequence"),
                confirmation_condition=EngineeringContextProjectContextAdapter._optional_text(payload, "confirmation_condition"),
            )
        else:
            typed_payload = ContextPayloadAbsent()
        created_at = response.get("created_at")
        updated_at = response.get("updated_at")
        if not isinstance(created_at, datetime) or not isinstance(updated_at, datetime):
            raise ValueError("owner timestamps are invalid")
        authority = EngineeringContextProjectContextAdapter._text(response, "authority")
        return EngineeringContextProjection(
            context_id=context_id,
            context_key=EngineeringContextProjectContextAdapter._text(response, "context_key"),
            project_id=scope.project_id,
            workspace_id=workspace_id if type(workspace_id) is int else None,
            kind=EngineeringContextProjectContextAdapter._text(response, "kind"),
            authority=authority,
            lifecycle="current",
            purpose=EngineeringContextProjectContextAdapter._optional_text(response, "purpose"),
            version=EngineeringContextProjectContextAdapter._positive(response, "version"),
            payload=typed_payload,
            created_at=created_at,
            updated_at=updated_at,
            provenance=FactProvenance(
                owner_kind="engineering_context", selector=str(context_id),
                version=EngineeringContextProjectContextAdapter._positive(response, "version"),
                standing="current", source_observed_at=updated_at,
                observed_at=datetime.now(timezone.utc),
                authority_class=(
                    AuthorityClassification.CONTEXTUAL_ADVISORY
                    if authority == "assumption"
                    else AuthorityClassification.HUMAN_AUTHORITATIVE
                ),
                temporal_class=TemporalClassification.CURRENT,
            ),
        )

    @staticmethod
    def _text(source: Mapping[str, object], key: str) -> str:
        value = source.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"owner {key} is invalid")
        return value

    @staticmethod
    def _optional_text(source: Mapping[str, object], key: str) -> str | None:
        value = source.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"owner {key} is invalid")
        return value

    @staticmethod
    def _positive(source: Mapping[str, object], key: str) -> int:
        value = source.get(key)
        if type(value) is not int or value < 1:
            raise ValueError(f"owner {key} is invalid")
        return value

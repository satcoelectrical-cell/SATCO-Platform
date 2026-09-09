"""Authorization-first ADR-025 Identifier application service."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
import hmac
import json
import time
from uuid import UUID

from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.config import settings
from app.discipline_packages.descriptors.eic_v1 import (
    ELECTRICAL_OBJECT_DECLARATIONS,
    INSTRUMENTATION_OBJECT_DECLARATIONS,
)
from app.exceptions.engineering_identifier import (
    EngineeringIdentifierConflict,
    EngineeringIdentifierError,
    EngineeringIdentifierLimitExceeded,
    EngineeringIdentifierProtectedNotFound,
)
from app.models.audit_log import AuditLog
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_identifier_command import (
    EngineeringIdentifierIdempotency,
    EngineeringIdentifierOutbox,
)
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.schemas.engineering_identifier import EngineeringIdentifierResponse


_RETRYABLE_SQLSTATES = {"23505", "40001", "40P01"}


def _retry_identifier_races(function):
    """Retry only governed uniqueness/serialization/deadlock races twice."""

    @wraps(function)
    def wrapped(*args, **kwargs):
        for attempt in range(3):
            try:
                return function(*args, **kwargs)
            except DBAPIError as exc:
                sqlstate = getattr(exc.orig, "pgcode", None) or getattr(
                    exc.orig, "sqlstate", None
                )
                if sqlstate in _RETRYABLE_SQLSTATES and attempt < 2:
                    continue
                if isinstance(exc, IntegrityError) or sqlstate in _RETRYABLE_SQLSTATES:
                    raise EngineeringIdentifierConflict() from exc
                raise
        raise EngineeringIdentifierConflict()

    return wrapped


class EngineeringIdentifierService:
    """Own Identifier mutations; repositories never commit independently."""

    def __init__(self, uow_factory):
        self._uow_factory = uow_factory

    @staticmethod
    def _authorize(session, *, actor_id: int, organization_id: UUID, item, mutate: bool) -> None:
        user = session.get(User, actor_id)
        project = session.query(Project).filter_by(
            id=item.project_id, organization_id=organization_id,
        ).one_or_none()
        if user is None or not user.is_active or project is None:
            raise EngineeringIdentifierProtectedNotFound()
        if user.role == "admin" or actor_id in {project.owner_id, project.primary_assignee_id}:
            return
        workspace = session.get(EngineeringWorkspace, item.workspace_id)
        if workspace is None or workspace.project_id != project.id:
            raise EngineeringIdentifierProtectedNotFound()
        permitted = actor_id in {workspace.owner_id, workspace.primary_assignee_id}
        if not permitted and not mutate:
            permitted = session.get(EngineeringWorkspaceMember, (workspace.id, actor_id)) is not None
        if not permitted:
            raise EngineeringIdentifierProtectedNotFound()

    @staticmethod
    def _response(item):
        return EngineeringIdentifierResponse.model_validate(item)

    @staticmethod
    def _required_package_primary(item) -> str | None:
        if item.origin_package_key is None:
            return None
        declarations = {
            "electrical": ELECTRICAL_OBJECT_DECLARATIONS,
            "instrumentation": INSTRUMENTATION_OBJECT_DECLARATIONS,
        }.get(item.origin_package_key)
        if declarations is None:
            raise EngineeringIdentifierConflict()
        declaration = next(
            (
                value
                for value in declarations
                if value.declaration_id == item.origin_declaration_id
            ),
            None,
        )
        if declaration is None:
            raise EngineeringIdentifierConflict()
        return declaration.required_primary_identifier_kind

    @staticmethod
    def _cursor_secret() -> bytes:
        return settings.resolved_secret_key().encode()

    @classmethod
    def _encode_cursor(cls, *, actor_id: int, organization_id: UUID,
                       object_id: UUID, project_id: int, item) -> str:
        payload = json.dumps({
            "actor_id": actor_id,
            "organization_id": str(organization_id),
            "object_id": str(object_id),
            "project_id": project_id,
            "created_at": item.created_at.astimezone(timezone.utc).isoformat(),
            "identifier_id": str(item.identifier_id),
            "expires_at": int(time.time()) + 900,
        }, sort_keys=True, separators=(",", ":")).encode()
        body = base64.urlsafe_b64encode(payload).rstrip(b"=")
        signature = hmac.new(cls._cursor_secret(), body, "sha256").hexdigest().encode()
        return (body + b"." + signature).decode()

    @classmethod
    def _decode_cursor(cls, cursor: str, *, actor_id: int,
                       organization_id: UUID, object_id: UUID, project_id: int):
        try:
            body, supplied = cursor.encode().split(b".", 1)
            expected = hmac.new(cls._cursor_secret(), body, "sha256").hexdigest().encode()
            if not hmac.compare_digest(supplied, expected):
                raise ValueError
            raw = base64.urlsafe_b64decode(body + b"=" * (-len(body) % 4))
            payload = json.loads(raw)
            if payload != {
                **payload,
                "actor_id": actor_id,
                "organization_id": str(organization_id),
                "object_id": str(object_id),
                "project_id": project_id,
            } or payload["expires_at"] < int(time.time()):
                raise ValueError
            return datetime.fromisoformat(payload["created_at"]), UUID(payload["identifier_id"])
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise EngineeringIdentifierError("Identifier history cursor is invalid") from exc

    @staticmethod
    def _fingerprint(operation: str, target_id: UUID, data) -> str:
        payload = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
        canonical = json.dumps(
            {"operation": operation, "target_id": str(target_id), "data": payload},
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _idempotency(session, *, actor_id: int, organization_id: UUID,
                     operation: str, idempotency_key: UUID, fingerprint: str):
        prior = session.get(EngineeringIdentifierIdempotency, (
            organization_id, actor_id, operation, idempotency_key,
        ))
        if prior is not None and (
            prior.request_fingerprint != fingerprint or prior.result is None
        ):
            raise EngineeringIdentifierConflict()
        return prior

    @staticmethod
    def _record_idempotency(session, *, actor_id: int, organization_id: UUID,
                            operation: str, idempotency_key: UUID,
                            fingerprint: str, identifier_id: UUID | None,
                            result: dict) -> None:
        session.add(EngineeringIdentifierIdempotency(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            identifier_id=identifier_id,
            result=result,
        ))

    @staticmethod
    def _outbox(session, *, item: EngineeringIdentifier, event_type: str,
                correlation_id: UUID, now: datetime) -> None:
        session.add(EngineeringIdentifierOutbox(
            identifier_id=item.identifier_id,
            aggregate_version=item.version,
            event_type=event_type,
            payload={
                "engineering_object_id": str(item.engineering_object_id),
                "organization_id": str(item.organization_id),
                "project_id": item.project_id,
                "workspace_id": item.workspace_id,
                "lifecycle": item.lifecycle,
                "primary_role": item.primary_role,
                "correlation_id": str(correlation_id),
            },
            occurred_at=now,
        ))

    @staticmethod
    def _audit(session, *, actor_id: int, identifier_id: UUID, action: str,
               object_id: UUID, correlation_id: UUID, before: int | None, after: int) -> None:
        session.add(AuditLog(
            user_id=actor_id,
            action=action,
            entity="ENGINEERING_IDENTIFIER",
            entity_uuid=identifier_id,
            details={
                "engineering_object_id": str(object_id),
                "correlation_id": str(correlation_id),
                "previous_version": before,
                "version": after,
                "outcome": "success",
            },
        ))

    def current_set(self, *, actor_id: int, organization_id: UUID, object_id: UUID):
        with self._uow_factory() as uow:
            obj = uow.identifiers.get_object_locked(object_id, organization_id)
            if obj is None:
                raise EngineeringIdentifierProtectedNotFound()
            self._authorize(uow.session, actor_id=actor_id, organization_id=organization_id, item=obj, mutate=False)
            return tuple(self._response(item) for item in uow.identifiers.current_set_locked(object_id, organization_id))

    def history(self, *, actor_id: int, organization_id: UUID, object_id: UUID,
                limit: int = 50, cursor: str | None = None):
        if not 1 <= limit <= 100:
            raise EngineeringIdentifierError()
        with self._uow_factory() as uow:
            obj = uow.identifiers.get_object_locked(object_id, organization_id)
            if obj is None:
                raise EngineeringIdentifierProtectedNotFound()
            self._authorize(uow.session, actor_id=actor_id, organization_id=organization_id, item=obj, mutate=False)
            before = None if cursor is None else self._decode_cursor(
                cursor, actor_id=actor_id, organization_id=organization_id,
                object_id=object_id, project_id=obj.project_id,
            )
            rows = uow.identifiers.history(
                object_id, organization_id, limit=limit + 1, before=before,
            )
            page = rows[:limit]
            next_cursor = None
            if len(rows) > limit:
                next_cursor = self._encode_cursor(
                    actor_id=actor_id, organization_id=organization_id,
                    object_id=object_id, project_id=obj.project_id, item=page[-1],
                )
            return tuple(self._response(item) for item in page), next_cursor

    @_retry_identifier_races
    def create(self, *, actor_id: int, organization_id: UUID, object_id: UUID,
               data, correlation_id: UUID, idempotency_key: UUID):
        operation = "CreateEngineeringIdentifier"
        fingerprint = self._fingerprint(operation, object_id, data)
        try:
            with self._uow_factory() as uow:
                obj = uow.identifiers.get_object_locked(object_id, organization_id)
                if obj is None:
                    raise EngineeringIdentifierProtectedNotFound()
                self._authorize(uow.session, actor_id=actor_id, organization_id=organization_id, item=obj, mutate=True)
                prior = self._idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                )
                if prior is not None:
                    try:
                        return EngineeringIdentifierResponse.model_validate(
                            prior.result["response"]
                        )
                    except (KeyError, TypeError, ValueError):
                        raise EngineeringIdentifierConflict()
                if obj.version != data.expected_object_version:
                    raise EngineeringIdentifierConflict()
                current = uow.identifiers.current_set_locked(object_id, organization_id)
                if len(current) >= 16:
                    raise EngineeringIdentifierLimitExceeded()
                item = EngineeringIdentifier(
                    engineering_object_id=obj.id,
                    organization_id=obj.organization_id,
                    project_id=obj.project_id,
                    workspace_id=obj.workspace_id,
                    identifier_kind=data.identifier_kind.value,
                    display_value=data.display_value,
                    issuing_scope_kind="project",
                    issuing_scope_value=str(obj.project_id),
                    primary_role="alternate",
                    evidence_references=[str(value) for value in data.evidence_references],
                    creator_id=actor_id,
                    steward_id=actor_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                uow.identifiers.add(item)
                self._outbox(uow.session, item=item, event_type="EngineeringIdentifierCreated",
                             correlation_id=correlation_id, now=item.created_at)
                self._audit(uow.session, actor_id=actor_id, identifier_id=item.identifier_id,
                            action=operation, object_id=obj.id,
                            correlation_id=correlation_id, before=None, after=1)
                self._record_idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint, identifier_id=item.identifier_id,
                    result={
                        "identifier_id": str(item.identifier_id),
                        "response": self._response(item).model_dump(mode="json"),
                    },
                )
                uow.commit()
                return self._response(item)
        except DBAPIError:
            raise

    @_retry_identifier_races
    def replace(self, *, actor_id: int, organization_id: UUID, identifier_id: UUID,
                data, correlation_id: UUID, idempotency_key: UUID):
        operation = "ReplaceEngineeringIdentifier"
        fingerprint = self._fingerprint(operation, identifier_id, data)
        try:
            with self._uow_factory() as uow:
                object_id = uow.identifiers.get_object_id(identifier_id, organization_id)
                if object_id is None:
                    raise EngineeringIdentifierProtectedNotFound()
                obj = uow.identifiers.get_object_locked(object_id, organization_id)
                if obj is None:
                    raise EngineeringIdentifierProtectedNotFound()
                prior = uow.identifiers.get_locked(identifier_id, organization_id)
                if prior is None or prior.engineering_object_id != obj.id:
                    raise EngineeringIdentifierProtectedNotFound()
                self._authorize(uow.session, actor_id=actor_id, organization_id=organization_id, item=obj, mutate=True)
                replay = self._idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                )
                if replay is not None:
                    try:
                        return EngineeringIdentifierResponse.model_validate(
                            replay.result["response"]
                        )
                    except (KeyError, TypeError, ValueError):
                        raise EngineeringIdentifierConflict()
                if (prior.lifecycle != "current" or prior.version != data.expected_identifier_version
                        or obj.version != data.expected_object_version):
                    raise EngineeringIdentifierConflict()
                required_kind = self._required_package_primary(prior)
                if (
                    prior.primary_role == "primary"
                    and required_kind is not None
                    and data.identifier_kind.value != required_kind
                ):
                    raise EngineeringIdentifierConflict()
                now = datetime.now(timezone.utc)
                previous_version = prior.version
                prior.lifecycle = "superseded"
                prior.version += 1
                prior.updated_at = now
                uow.session.flush()
                successor = EngineeringIdentifier(
                    engineering_object_id=prior.engineering_object_id,
                    organization_id=prior.organization_id,
                    project_id=prior.project_id,
                    workspace_id=prior.workspace_id,
                    identifier_kind=data.identifier_kind.value,
                    display_value=data.display_value,
                    issuing_scope_kind=prior.issuing_scope_kind,
                    issuing_scope_value=prior.issuing_scope_value,
                    primary_role=prior.primary_role,
                    evidence_references=[str(value) for value in data.evidence_references],
                    predecessor_identifier_id=prior.identifier_id,
                    creator_id=actor_id,
                    steward_id=actor_id,
                    created_at=now,
                    updated_at=now,
                    origin_package_key=prior.origin_package_key,
                    origin_project_configuration_revision=prior.origin_project_configuration_revision,
                    origin_declaration_id=prior.origin_declaration_id,
                )
                uow.identifiers.add(successor)
                prior.successor_identifier_id = successor.identifier_id
                self._outbox(uow.session, item=prior, event_type="EngineeringIdentifierSuperseded",
                             correlation_id=correlation_id, now=now)
                self._outbox(uow.session, item=successor, event_type="EngineeringIdentifierCreated",
                             correlation_id=correlation_id, now=now)
                self._audit(uow.session, actor_id=actor_id, identifier_id=prior.identifier_id,
                            action=operation, object_id=obj.id,
                            correlation_id=correlation_id, before=previous_version, after=prior.version)
                self._record_idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint, identifier_id=successor.identifier_id,
                    result={
                        "identifier_id": str(successor.identifier_id),
                        "response": self._response(successor).model_dump(mode="json"),
                    },
                )
                uow.commit()
                return self._response(successor)
        except DBAPIError:
            raise

    @_retry_identifier_races
    def withdraw(self, *, actor_id: int, organization_id: UUID, identifier_id: UUID,
                 expected_version: int, rationale: str, correlation_id: UUID,
                 idempotency_key: UUID):
        operation = "WithdrawEngineeringIdentifier"
        fingerprint = self._fingerprint(operation, identifier_id, {
            "expected_identifier_version": expected_version, "rationale": rationale,
        })
        try:
            with self._uow_factory() as uow:
                object_id = uow.identifiers.get_object_id(identifier_id, organization_id)
                if object_id is None:
                    raise EngineeringIdentifierProtectedNotFound()
                obj = uow.identifiers.get_object_locked(object_id, organization_id)
                if obj is None:
                    raise EngineeringIdentifierProtectedNotFound()
                item = uow.identifiers.get_locked(identifier_id, organization_id)
                if item is None or item.engineering_object_id != obj.id:
                    raise EngineeringIdentifierProtectedNotFound()
                self._authorize(uow.session, actor_id=actor_id, organization_id=organization_id, item=obj, mutate=True)
                replay = self._idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                )
                if replay is not None:
                    try:
                        return EngineeringIdentifierResponse.model_validate(
                            replay.result["response"]
                        )
                    except (KeyError, TypeError, ValueError):
                        raise EngineeringIdentifierConflict()
                if item.lifecycle != "current" or item.version != expected_version:
                    raise EngineeringIdentifierConflict()
                if item.primary_role == "primary" and obj.origin_package_key is not None:
                    raise EngineeringIdentifierConflict()
                before = item.version
                item.lifecycle = "withdrawn"
                item.version += 1
                item.updated_at = datetime.now(timezone.utc)
                self._outbox(uow.session, item=item, event_type="EngineeringIdentifierWithdrawn",
                             correlation_id=correlation_id, now=item.updated_at)
                self._audit(uow.session, actor_id=actor_id, identifier_id=item.identifier_id,
                            action=operation, object_id=obj.id,
                            correlation_id=correlation_id, before=before, after=item.version)
                self._record_idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint, identifier_id=item.identifier_id,
                    result={
                        "identifier_id": str(item.identifier_id),
                        "response": self._response(item).model_dump(mode="json"),
                    },
                )
                uow.commit()
                return self._response(item)
        except DBAPIError:
            raise

    @_retry_identifier_races
    def reassign_primary(self, *, actor_id: int, organization_id: UUID, object_id: UUID,
                         data, correlation_id: UUID, idempotency_key: UUID):
        operation = "ReassignPrimaryEngineeringIdentifier"
        fingerprint = self._fingerprint(operation, object_id, data)
        try:
            with self._uow_factory() as uow:
                obj = uow.identifiers.get_object_locked(object_id, organization_id)
                if obj is None:
                    raise EngineeringIdentifierProtectedNotFound()
                self._authorize(uow.session, actor_id=actor_id, organization_id=organization_id, item=obj, mutate=True)
                replay = self._idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                )
                if replay is not None:
                    try:
                        return tuple(
                            EngineeringIdentifierResponse.model_validate(item)
                            for item in replay.result["responses"]
                        )
                    except (KeyError, TypeError, ValueError):
                        raise EngineeringIdentifierConflict()
                if obj.version != data.expected_object_version:
                    raise EngineeringIdentifierConflict()
                current = uow.identifiers.current_set_locked(object_id, organization_id)
                expected = {item.identifier_id: item.version for item in current}
                if expected != data.expected_identifier_versions:
                    raise EngineeringIdentifierConflict()
                target = next((item for item in current if item.identifier_id == data.target_identifier_id), None)
                if target is None:
                    raise EngineeringIdentifierProtectedNotFound()
                if target.primary_role == "primary":
                    raise EngineeringIdentifierConflict()
                required_kind = self._required_package_primary(obj)
                if required_kind is not None and (
                    target.identifier_kind != required_kind
                    or target.origin_package_key != obj.origin_package_key
                    or target.origin_project_configuration_revision
                    != obj.origin_project_configuration_revision
                    or target.origin_declaration_id != obj.origin_declaration_id
                ):
                    raise EngineeringIdentifierConflict()
                now = datetime.now(timezone.utc)
                for item in current:
                    role = "primary" if item is target else "alternate"
                    if item.primary_role != role:
                        before = item.version
                        item.primary_role = role
                        item.version += 1
                        item.updated_at = now
                        self._outbox(uow.session, item=item,
                                     event_type="EngineeringIdentifierPrimaryRoleChanged",
                                     correlation_id=correlation_id, now=now)
                        self._audit(uow.session, actor_id=actor_id, identifier_id=item.identifier_id,
                                    action=operation, object_id=obj.id,
                                    correlation_id=correlation_id, before=before, after=item.version)
                ordered = tuple(sorted(
                    current,
                    key=lambda item: (
                        item.primary_role != "primary",
                        item.identifier_kind,
                        item.normalized_value,
                        str(item.identifier_id),
                    ),
                ))
                self._record_idempotency(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    operation=operation, idempotency_key=idempotency_key,
                    fingerprint=fingerprint, identifier_id=target.identifier_id,
                    result={
                        "identifier_id": str(target.identifier_id),
                        "responses": [
                            self._response(item).model_dump(mode="json")
                            for item in ordered
                        ],
                    },
                )
                uow.commit()
                return tuple(self._response(item) for item in ordered)
        except DBAPIError:
            raise

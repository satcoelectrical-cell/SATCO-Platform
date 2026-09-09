"""Canonical-owner integration for the PATCH-052 Electrical V1 package."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import UUID, uuid4
from functools import wraps

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.discipline_packages.descriptors.eic_v1 import (
    DESCRIPTORS_V1,
    DESCRIPTOR_DIGESTS_V1,
    ELECTRICAL_OBJECT_DECLARATIONS,
    ELECTRICAL_RELATIONSHIP_DECLARATIONS,
)
from app.discipline_packages.operational import execute_package_rule
from app.models.audit_log import AuditLog
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_identifier_command import EngineeringIdentifierOutbox
from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import EngineeringObjectIdempotency, EngineeringObjectOutbox
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_relationship_command import (
    EngineeringRelationshipIdempotency,
    EngineeringRelationshipOutbox,
)
from app.models.engineering_experience_capture import (
    EngineeringExperienceCapture,
    normalize_capture_text,
    normalize_single_line_text,
)
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureIdempotency,
    EngineeringExperienceCaptureOutbox,
)
from app.repositories.patch_052_operation_unit_of_work import Patch052OperationUnitOfWork
from app.services.patch_052_mutation_guard import (
    Patch052MutationProtected,
    Patch052MutationUnavailable,
    lock_and_authorize_workspaces,
    lock_package_context,
)
from app.schemas.engineering_identifier import EngineeringIdentifierResponse
from app.schemas.engineering_object import EngineeringObjectResponse
from app.schemas.engineering_relationship import EngineeringRelationshipResponse
from app.schemas.engineering_experience_capture import EngineeringExperienceCaptureResponse


class PackageProtectedNotFound(LookupError):
    pass


class PackageUnavailable(RuntimeError):
    pass


class PackageDeclarationMismatch(ValueError):
    pass


class PackageConflict(RuntimeError):
    pass


_RETRYABLE_SQLSTATES = {"23505", "40001", "40P01"}


def _retry_package_races(function):
    """Run at most two retries, each through a newly opened outer UoW."""

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
                    raise PackageConflict() from exc
                raise
        raise PackageConflict()

    return wrapped


def _fingerprint(operation: str, data) -> str:
    payload = data.model_dump(mode="json")
    return sha256(json.dumps({"operation": operation, "data": payload}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ElectricalPackageService:
    """Stages Object/Identifier or Relationship/Audit/outbox in one Session."""

    PACKAGE_KEY = "electrical"
    PACKAGE_TITLE = "Electrical"
    OBJECT_FAMILY = "electrical"
    OWNER_DISCIPLINE = "electrical"
    RELATIONSHIP_FAMILY = "electrical"
    OBJECT_DECLARATIONS = ELECTRICAL_OBJECT_DECLARATIONS
    RELATIONSHIP_DECLARATIONS = ELECTRICAL_RELATIONSHIP_DECLARATIONS

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def _context(self, uow, *, actor_id: int, organization_id: UUID, auth_version: int,
                 project_id: int, workspace_id: int):
        try:
            return lock_package_context(
                uow,
                package_key=self.PACKAGE_KEY,
                actor_id=actor_id,
                organization_id=organization_id,
                auth_version=auth_version,
                project_id=project_id,
                workspace_id=workspace_id,
            )
        except Patch052MutationProtected as exc:
            raise PackageProtectedNotFound() from exc
        except Patch052MutationUnavailable as exc:
            raise PackageUnavailable() from exc

    def _audit(self, session, *, actor_id: int, action: str, aggregate_id: UUID,
               correlation_id: UUID, declaration_id: str, selection, registry,
               outcome: str = "success", result_digest: str | None = None):
        session.add(AuditLog(
            user_id=actor_id,
            action=action,
            entity="DISCIPLINE_PACKAGE_OPERATION",
            entity_uuid=aggregate_id,
            details={
                "package_key": self.PACKAGE_KEY,
                "package_version": selection.package_version,
                "descriptor_digest": selection.descriptor_digest,
                "registry_digest": registry.registry_digest,
                "project_configuration_revision": selection.configuration_revision,
                "declaration_id": declaration_id,
                "actor_id": actor_id,
                "correlation_id": str(correlation_id),
                "result_digest": result_digest,
                "outcome": outcome,
            },
        ))

    @_retry_package_races
    def create_object(self, *, actor_id: int, organization_id: UUID, auth_version: int = 1,
                      project_id: int,
                      workspace_id: int, data, correlation_id: UUID,
                      idempotency_key: UUID):
        operation = f"Package{self.PACKAGE_TITLE}ObjectCreate"
        fingerprint = _fingerprint(operation, data)
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            context = self._context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version,
                project_id=project_id, workspace_id=workspace_id,
            )
            session = uow.session
            project, workspace = context.project, context.workspace
            selection, registry = context.selection, context.registry
            prior = session.scalar(select(EngineeringObjectIdempotency).where(
                EngineeringObjectIdempotency.actor_id == actor_id,
                EngineeringObjectIdempotency.command_type == operation,
                EngineeringObjectIdempotency.idempotency_id == idempotency_key,
            ).with_for_update())
            if prior is not None:
                if prior.request_fingerprint != fingerprint or prior.status != "completed":
                    raise PackageConflict()
                try:
                    return (
                        EngineeringObjectResponse.model_validate(prior.result["object"]),
                        EngineeringIdentifierResponse.model_validate(
                            prior.result["primary_identifier"]
                        ),
                    )
                except (KeyError, TypeError, ValueError):
                    raise PackageConflict() from None
            declaration = next((item for item in self.OBJECT_DECLARATIONS if item.declaration_id == data.declaration_id), None)
            if declaration is None:
                raise PackageDeclarationMismatch()
            # The trusted adapter gate is deterministic and validation-blocking.
            gate = execute_package_rule(
                package_key=self.PACKAGE_KEY,
                hook_id=f"{self.PACKAGE_KEY}.object_relationship_integrity",
                hook_version="1.0.0",
                envelope={"objects": [{"object_type": declaration.object_type}], "violations": []},
            )
            if gate.status != "PASS":
                raise PackageDeclarationMismatch()
            now = datetime.now(timezone.utc)
            origin = {
                "origin_package_key": self.PACKAGE_KEY,
                "origin_project_configuration_revision": selection.configuration_revision,
                "origin_declaration_id": declaration.declaration_id,
            }
            obj = EngineeringObject(
                organization_id=organization_id,
                customer_id=project.customer_id,
                project_id=project_id,
                workspace_id=workspace_id,
                family=self.OBJECT_FAMILY,
                discipline=self.OWNER_DISCIPLINE,
                object_type=declaration.object_type,
                creator_id=actor_id,
                steward_id=data.steward_id or actor_id,
                created_at=now,
                updated_at=now,
                **origin,
            )
            session.add(obj)
            session.flush()
            identifier = EngineeringIdentifier(
                engineering_object_id=obj.id,
                organization_id=organization_id,
                project_id=project_id,
                workspace_id=workspace_id,
                identifier_kind=declaration.required_primary_identifier_kind,
                display_value=data.primary_identifier_display_value,
                issuing_scope_kind="project",
                issuing_scope_value=str(project_id),
                primary_role="primary",
                evidence_references=[str(value) for value in data.primary_identifier_evidence_references],
                creator_id=actor_id,
                steward_id=data.steward_id or actor_id,
                created_at=now,
                updated_at=now,
                **origin,
            )
            session.add(identifier)
            session.flush()
            event_id = uuid4()
            session.add(EngineeringObjectOutbox(
                event_id=event_id, aggregate_id=obj.id, aggregate_version=1,
                event_type=f"Package{self.PACKAGE_TITLE}ObjectCreated", schema_version=1,
                payload={"identifier_id": str(identifier.identifier_id), **self._audit_payload(selection, registry, declaration.declaration_id, correlation_id)},
                occurred_at=now,
            ))
            session.add(EngineeringIdentifierOutbox(
                event_id=uuid4(), identifier_id=identifier.identifier_id,
                aggregate_version=1, event_type="EngineeringIdentifierCreated",
                payload={"causation_id": str(event_id), **self._audit_payload(selection, registry, declaration.declaration_id, correlation_id)},
                occurred_at=now,
            ))
            self._audit(session, actor_id=actor_id, action=operation,
                        aggregate_id=obj.id, correlation_id=correlation_id,
                        declaration_id=declaration.declaration_id, selection=selection,
                        registry=registry, result_digest=gate.result_digest)
            reservation = EngineeringObjectIdempotency(
                actor_id=actor_id, command_type=operation,
                idempotency_id=idempotency_key, request_fingerprint=fingerprint,
                status="completed", aggregate_id=obj.id,
                result={
                    "object_id": str(obj.id),
                    "identifier_id": str(identifier.identifier_id),
                    "object": EngineeringObjectResponse.model_validate(obj).model_dump(mode="json"),
                    "primary_identifier": EngineeringIdentifierResponse.model_validate(
                        identifier
                    ).model_dump(mode="json"),
                },
            )
            session.add(reservation)
            uow.commit()
            return EngineeringObjectResponse.model_validate(obj), EngineeringIdentifierResponse.model_validate(identifier)

    def _audit_payload(self, selection, registry, declaration_id: str, correlation_id: UUID):
        return {
            "package_key": self.PACKAGE_KEY, "package_version": selection.package_version,
            "descriptor_digest": selection.descriptor_digest,
            "registry_digest": registry.registry_digest,
            "project_configuration_revision": selection.configuration_revision,
            "declaration_id": declaration_id,
            "correlation_id": str(correlation_id),
        }

    @_retry_package_races
    def create_relationship(self, *, actor_id: int, organization_id: UUID,
                            auth_version: int = 1,
                            project_id: int, workspace_id: int, data,
                            correlation_id: UUID, idempotency_key: UUID):
        operation = f"Package{self.PACKAGE_TITLE}RelationshipCreate"
        fingerprint = _fingerprint(operation, data)
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            context = self._context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id,
                workspace_id=workspace_id,
            )
            session = uow.session
            workspace = context.workspace
            selection, registry = context.selection, context.registry
            # Resolve endpoint Workspace identities only after primary scope
            # authorization; then lock/authorize every Workspace before Objects.
            endpoint_ids = sorted((data.source_object_id, data.target_object_id), key=str)
            endpoint_workspace_ids = set(session.scalars(select(EngineeringObject.workspace_id).where(
                EngineeringObject.id.in_(endpoint_ids),
                EngineeringObject.organization_id == organization_id,
                EngineeringObject.project_id == project_id,
            )))
            if len(endpoint_workspace_ids) == 0:
                raise PackageProtectedNotFound()
            try:
                lock_and_authorize_workspaces(
                    session, context=context, workspace_ids=endpoint_workspace_ids,
                )
            except Patch052MutationProtected as exc:
                raise PackageProtectedNotFound() from exc
            endpoints = list(session.scalars(select(EngineeringObject).where(
                EngineeringObject.id.in_(endpoint_ids),
                EngineeringObject.organization_id == organization_id,
                EngineeringObject.project_id == project_id,
            ).order_by(EngineeringObject.id).with_for_update()))
            if len(endpoints) != 2 or endpoints[0].id == endpoints[-1].id:
                raise PackageProtectedNotFound()
            by_id = {item.id: item for item in endpoints}
            source, target = by_id[data.source_object_id], by_id[data.target_object_id]
            declaration = next((item for item in self.RELATIONSHIP_DECLARATIONS if item.declaration_id == data.declaration_id), None)
            cross_workspace = source.workspace_id != target.workspace_id
            if (
                declaration is None
                or source.workspace_id != workspace_id
                or not declaration.permits(
                    source.object_type, target.object_type,
                    cross_workspace=cross_workspace,
                )
            ):
                raise PackageDeclarationMismatch()
            prior = session.scalar(select(EngineeringRelationshipIdempotency).where(
                EngineeringRelationshipIdempotency.actor_id == actor_id,
                EngineeringRelationshipIdempotency.command_type == operation,
                EngineeringRelationshipIdempotency.idempotency_id == idempotency_key,
            ).with_for_update())
            if prior is not None:
                if prior.request_fingerprint != fingerprint or prior.status != "completed":
                    raise PackageConflict()
                try:
                    return EngineeringRelationshipResponse.model_validate(
                        prior.result["response"]
                    )
                except (KeyError, TypeError, ValueError):
                    raise PackageConflict() from None
            gate = execute_package_rule(package_key=self.PACKAGE_KEY, hook_id=f"{self.PACKAGE_KEY}.object_relationship_integrity", hook_version="1.0.0", envelope={"relationships": [{"relationship_type": declaration.relationship_type}], "violations": []})
            if gate.status != "PASS":
                raise PackageDeclarationMismatch()
            now = datetime.now(timezone.utc)
            relationship = EngineeringRelationship(
                organization_id=organization_id, project_id=project_id,
                workspace_id=workspace_id, source_object_id=source.id,
                target_object_id=target.id, relationship_family=self.RELATIONSHIP_FAMILY,
                relationship_type=declaration.relationship_type,
                evidence_references=[str(value) for value in data.evidence_references],
                creator_id=actor_id, steward_id=data.steward_id or actor_id,
                created_at=now, updated_at=now,
                origin_package_key=self.PACKAGE_KEY,
                origin_project_configuration_revision=selection.configuration_revision,
                origin_declaration_id=declaration.declaration_id,
            )
            session.add(relationship)
            session.flush()
            session.add(EngineeringRelationshipOutbox(
                event_id=uuid4(), aggregate_id=relationship.id, aggregate_version=1,
                event_type=f"Package{self.PACKAGE_TITLE}RelationshipCreated", schema_version=1,
                payload=self._audit_payload(selection, registry, declaration.declaration_id, correlation_id),
                occurred_at=now,
            ))
            self._audit(session, actor_id=actor_id, action=operation, aggregate_id=relationship.id, correlation_id=correlation_id, declaration_id=declaration.declaration_id, selection=selection, registry=registry, result_digest=gate.result_digest)
            session.add(EngineeringRelationshipIdempotency(
                actor_id=actor_id, command_type=operation,
                idempotency_id=idempotency_key, request_fingerprint=fingerprint,
                status="completed", aggregate_id=relationship.id,
                result={
                    "relationship_id": str(relationship.id),
                    "response": EngineeringRelationshipResponse.model_validate(
                        relationship
                    ).model_dump(mode="json"),
                },
            ))
            uow.commit()
            return EngineeringRelationshipResponse.model_validate(relationship)

    @_retry_package_races
    def create_capture(self, *, actor_id: int, organization_id: UUID,
                       auth_version: int = 1,
                       project_id: int, workspace_id: int, data,
                       correlation_id: UUID, idempotency_key: UUID):
        operation = f"Package{self.PACKAGE_TITLE}CaptureCreate"
        fingerprint = _fingerprint(operation, data)
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            context = self._context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version,
                project_id=project_id, workspace_id=workspace_id,
            )
            session = uow.session
            selection, registry = context.selection, context.registry
            descriptor = next(item for item in DESCRIPTORS_V1 if item.package_key == self.PACKAGE_KEY)
            declarations = {item.id for item in descriptor.contributions.engineering_inputs}
            if data.declaration_id not in declarations:
                raise PackageDeclarationMismatch()
            object_row = None
            if data.engineering_object_id is not None:
                object_row = session.scalar(select(EngineeringObject).where(
                    EngineeringObject.id == data.engineering_object_id,
                    EngineeringObject.organization_id == organization_id,
                    EngineeringObject.project_id == project_id,
                    EngineeringObject.workspace_id == workspace_id,
                ).with_for_update())
                if object_row is None:
                    raise PackageProtectedNotFound()
            prior = session.scalar(select(EngineeringExperienceCaptureIdempotency).where(
                EngineeringExperienceCaptureIdempotency.organization_id == organization_id,
                EngineeringExperienceCaptureIdempotency.actor_id == actor_id,
                EngineeringExperienceCaptureIdempotency.command_type == operation,
                EngineeringExperienceCaptureIdempotency.idempotency_id == idempotency_key,
            ).with_for_update())
            if prior is not None:
                if prior.request_fingerprint != fingerprint or prior.status != "completed":
                    raise PackageConflict()
                try:
                    return EngineeringExperienceCaptureResponse.model_validate(
                        prior.result["response"]
                    )
                except (KeyError, TypeError, ValueError):
                    raise PackageConflict() from None
            now = datetime.now(timezone.utc)
            content = normalize_capture_text(
                data.original_content, field="original_content", maximum=10_000,
            )
            reference = None if data.source_reference is None else normalize_single_line_text(
                data.source_reference, field="source_reference", maximum=512,
            )
            row = EngineeringExperienceCapture(
                organization_id=organization_id, project_id=project_id,
                workspace_id=workspace_id, discipline=self.OWNER_DISCIPLINE,
                engineering_object_id=None if object_row is None else object_row.id,
                source_kind=data.source_kind.value, original_content=content,
                source_reference=reference, creator_id=actor_id,
                lifecycle="captured", version=1, created_at=now, updated_at=now,
                origin_package_key=self.PACKAGE_KEY,
                origin_project_configuration_revision=selection.configuration_revision,
                origin_declaration_id=data.declaration_id,
            )
            session.add(row)
            session.flush()
            event_id = uuid4()
            session.add(EngineeringExperienceCaptureOutbox(
                event_id=event_id, aggregate_id=row.id, aggregate_version=1,
                event_type=f"Package{self.PACKAGE_TITLE}CaptureCreated", schema_version=1,
                payload=self._audit_payload(
                    selection, registry, data.declaration_id, correlation_id,
                ), occurred_at=now,
            ))
            self._audit(
                session, actor_id=actor_id, action=operation,
                aggregate_id=row.id, correlation_id=correlation_id,
                declaration_id=data.declaration_id, selection=selection,
                registry=registry,
            )
            session.add(EngineeringExperienceCaptureIdempotency(
                organization_id=organization_id, actor_id=actor_id,
                command_type=operation, idempotency_id=idempotency_key,
                request_fingerprint=fingerprint, status="completed",
                aggregate_id=row.id,
                result={
                    "capture_id": str(row.id),
                    "response": EngineeringExperienceCaptureResponse.model_validate(
                        row
                    ).model_dump(mode="json"),
                },
            ))
            uow.commit()
            return EngineeringExperienceCaptureResponse.model_validate(row)

    @_retry_package_races
    def evaluate_rule(self, *, actor_id: int, organization_id: UUID,
                      auth_version: int = 1,
                      project_id: int, workspace_id: int, data,
                      correlation_id: UUID):
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            context = self._context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id,
                workspace_id=workspace_id,
            )
            selection, registry = context.selection, context.registry
            result = execute_package_rule(package_key=self.PACKAGE_KEY, hook_id=data.hook_id, hook_version=data.hook_version, envelope=data.envelope)
            self._audit(uow.session, actor_id=actor_id, action=f"Package{self.PACKAGE_TITLE}RuleEvaluate", aggregate_id=correlation_id, correlation_id=correlation_id, declaration_id=data.hook_id, selection=selection, registry=registry, result_digest=result.result_digest)
            uow.commit()
            return result

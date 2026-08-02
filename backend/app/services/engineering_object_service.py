"""Application orchestration for approved EngineeringObject use cases."""

from dataclasses import asdict
from hashlib import sha256
import json
from typing import Callable, Mapping
from uuid import UUID, uuid4

from app.exceptions.engineering_object import EngineeringObjectAuthorizationDenied
from app.exceptions.engineering_object import EngineeringObjectInvalidDomainTransition
from app.exceptions.engineering_object import EngineeringObjectProtectedNotFound
from app.exceptions.engineering_object import EngineeringObjectVersionConflict
from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import AuthenticatedActor
from app.models.engineering_object_command import AuthorizationContext
from app.models.engineering_object_command import CommandMetadata
from app.models.engineering_object_command import CreateEngineeringObject
from app.models.engineering_object_command import EngineeringObjectCommandError
from app.models.engineering_object_command import EngineeringObjectCommandResult
from app.models.engineering_object_command import EngineeringObjectVersionMismatch
from app.models.engineering_object_command import ReclassifyEngineeringObject
from app.models.engineering_object_command import TransferEngineeringObjectSteward
from app.models.engineering_object_command import TransitionEngineeringObjectAuthority
from app.models.engineering_object_command import TransitionEngineeringObjectLifecycle
from app.ports.engineering_object import AuthorizationPolicy, Clock
from app.ports.engineering_object import ReferenceValidator, UnitOfWork
from app.schemas.engineering_object import EngineeringObjectCreate
from app.schemas.engineering_object import EngineeringObjectFilter
from app.schemas.engineering_object import EngineeringObjectListResponse
from app.schemas.engineering_object import EngineeringObjectResponse
from app.schemas.engineering_object import ReclassifyEngineeringObjectRequest
from app.schemas.engineering_object import TransferEngineeringObjectStewardRequest
from app.schemas.engineering_object import TransitionEngineeringObjectAuthorityRequest
from app.schemas.engineering_object import TransitionEngineeringObjectLifecycleRequest


def _fingerprint(command_type: str, data: Mapping) -> str:
    payload = json.dumps(
        {"command_type": command_type, "data": data},
        sort_keys=True, default=str, separators=(",", ":"),
    )
    return sha256(payload.encode()).hexdigest()


class EngineeringObjectService:
    """Coordinate policy, references, aggregate, and one atomic Unit of Work."""

    def __init__(self, *, uow_factory: Callable[[], UnitOfWork],
                 authorization: AuthorizationPolicy,
                 references: ReferenceValidator, clock: Clock):
        self.uow_factory = uow_factory
        self.authorization = authorization
        self.references = references
        self.clock = clock

    @staticmethod
    def _metadata(actor, context, rationale, correlation_id,
                  idempotency_id, evidence=()) -> CommandMetadata:
        return CommandMetadata(
            actor=actor, authorization=context, rationale=rationale,
            correlation_id=correlation_id, idempotency_id=idempotency_id,
            command_id=uuid4(), evidence_references=tuple(evidence),
        )

    def create(self, *, data: EngineeringObjectCreate,
               actor: AuthenticatedActor, context: AuthorizationContext,
               correlation_id: UUID, idempotency_id: UUID):
        target = {"project_id": data.project_id}
        if not self.authorization.authorize(
            actor=actor, context=context, current_state=None,
            target_state=target,
        ):
            raise EngineeringObjectAuthorizationDenied()
        derived = self.references.validate_creation_references(
            actor=actor, project_id=data.project_id,
            steward_id=data.steward_id,
            evidence_references=tuple(data.evidence_references),
            discipline=data.discipline,
        )
        fingerprint = _fingerprint("CreateEngineeringObject", data.model_dump())
        metadata = self._metadata(
            actor, context, data.rationale, correlation_id, idempotency_id,
            data.evidence_references,
        )
        with self.uow_factory() as uow:
            prior = uow.idempotency.find(
                actor_id=actor.actor_id,
                command_type="CreateEngineeringObject",
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            if prior is not None:
                return EngineeringObjectResponse.model_validate(
                    prior.authorized_state
                )
            uow.idempotency.reserve(
                actor_id=actor.actor_id,
                command_type="CreateEngineeringObject",
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            aggregate, result = EngineeringObject.create(
                CreateEngineeringObject(
                    metadata=metadata, project_id=data.project_id,
                    family=data.family, discipline=data.discipline,
                    object_type=data.object_type, **derived,
                ), self.clock.now(),
            )
            uow.engineering_objects.add(aggregate)
            self._stage(uow, result, metadata, aggregate)
            uow.commit()
            return EngineeringObjectResponse.model_validate(aggregate)

    def reclassify(self, object_id, data, actor, context,
                   correlation_id, idempotency_id):
        return self._mutate(
            object_id, data, actor, context, correlation_id, idempotency_id,
            "ReclassifyEngineeringObject",
            lambda metadata: ReclassifyEngineeringObject(
                metadata=metadata, object_id=object_id,
                expected_version=data.expected_version,
                family=data.family, discipline=data.discipline,
                object_type=data.object_type,
            ), "reclassify",
        )

    def transition_lifecycle(self, object_id, data, actor, context,
                             correlation_id, idempotency_id):
        return self._mutate(
            object_id, data, actor, context, correlation_id, idempotency_id,
            "TransitionEngineeringObjectLifecycle",
            lambda metadata: TransitionEngineeringObjectLifecycle(
                metadata=metadata, object_id=object_id,
                expected_version=data.expected_version,
                lifecycle=data.lifecycle,
                replacement_object_id=data.replacement_object_id,
            ), "transition_lifecycle",
        )

    def transition_authority(self, object_id, data, actor, context,
                             correlation_id, idempotency_id):
        return self._mutate(
            object_id, data, actor, context, correlation_id, idempotency_id,
            "TransitionEngineeringObjectAuthority",
            lambda metadata: TransitionEngineeringObjectAuthority(
                metadata=metadata, object_id=object_id,
                expected_version=data.expected_version,
                authority_standing=data.authority_standing,
            ), "transition_authority",
        )

    def transfer_steward(self, object_id, data, actor, context,
                         correlation_id, idempotency_id):
        return self._mutate(
            object_id, data, actor, context, correlation_id, idempotency_id,
            "TransferEngineeringObjectSteward",
            lambda metadata: TransferEngineeringObjectSteward(
                metadata=metadata, object_id=object_id,
                expected_version=data.expected_version,
                steward_id=data.steward_id,
            ), "transfer_steward",
        )

    def _mutate(self, object_id, data, actor, context, correlation_id,
                idempotency_id, command_type, command_factory, method_name):
        fingerprint = _fingerprint(command_type, data.model_dump())
        evidence = getattr(data, "evidence_references", ())
        metadata = self._metadata(
            actor, context, data.rationale, correlation_id,
            idempotency_id, evidence,
        )
        with self.uow_factory() as uow:
            prior = uow.idempotency.find(
                actor_id=actor.actor_id, command_type=command_type,
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            aggregate = uow.engineering_objects.get_authorized(
                object_id, actor.organization_id
            )
            if aggregate is None:
                raise EngineeringObjectProtectedNotFound(object_id)
            if not self.authorization.authorize(
                actor=actor, context=context, current_state=aggregate,
                target_state=data.model_dump(),
            ):
                raise EngineeringObjectProtectedNotFound(object_id)
            references = {}
            for name in (
                "discipline", "steward_id", "replacement_object_id"
            ):
                value = getattr(data, name, None)
                if value is not None:
                    references[name] = getattr(value, "value", value)
            self.references.validate_mutation_references(
                actor=actor, object_id=object_id, references=references,
            )
            if prior is not None:
                return EngineeringObjectResponse.model_validate(
                    prior.authorized_state
                )
            uow.idempotency.reserve(
                actor_id=actor.actor_id, command_type=command_type,
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            try:
                result = getattr(aggregate, method_name)(
                    command_factory(metadata), self.clock.now()
                )
            except EngineeringObjectVersionMismatch as exc:
                raise EngineeringObjectVersionConflict() from exc
            except EngineeringObjectCommandError as exc:
                raise EngineeringObjectInvalidDomainTransition(str(exc)) from exc
            if not uow.engineering_objects.persist_expected_version(
                aggregate, data.expected_version
            ):
                raise EngineeringObjectVersionConflict()
            self._stage(uow, result, metadata, aggregate)
            uow.commit()
            return EngineeringObjectResponse.model_validate(aggregate)

    @staticmethod
    def _stage(uow, result: EngineeringObjectCommandResult,
               metadata: CommandMetadata,
               aggregate: EngineeringObject) -> None:
        scope = {}
        if result.events:
            event = result.events[0]
            scope = {
                "organization_id": event.organization_id,
                "project_id": event.project_id,
                "workspace_id": event.workspace_id,
            }
        uow.audit.record(
            command_type=result.command_type, actor=metadata.actor,
            object_id=result.object_id,
            correlation_id=metadata.correlation_id,
            idempotency_id=metadata.idempotency_id,
            rationale=metadata.rationale,
            previous_version=result.previous_version, version=result.version,
            details={"event_count": len(result.events), **scope},
        )
        uow.domain_events.record(result.events)
        state = EngineeringObjectResponse.model_validate(aggregate).model_dump()
        uow.idempotency.record_result(result, state)

    def get(self, object_id: UUID, actor: AuthenticatedActor,
            context: AuthorizationContext):
        with self.uow_factory() as uow:
            item = uow.engineering_objects.get_authorized(
                object_id, actor.organization_id
            )
            return self._authorized_response(item, actor, context)

    def _authorized_response(self, item, actor, context):
        if item is None or not self.authorization.authorize(
            actor=actor, context=context, current_state=item, target_state={},
        ):
            raise EngineeringObjectProtectedNotFound(
                getattr(item, "id", None)
            )
        return EngineeringObjectResponse.model_validate(item)

    def list(self, *, project_id: int, filters: EngineeringObjectFilter,
             page: int, size: int, actor: AuthenticatedActor,
             context: AuthorizationContext):
        if not self.authorization.authorize(
            actor=actor, context=context, current_state=None,
            target_state={"project_id": project_id},
        ):
            raise EngineeringObjectProtectedNotFound()
        with self.uow_factory() as uow:
            items, total = uow.engineering_objects.list_authorized(
                organization_id=actor.organization_id,
                project_id=project_id,
                filters=filters.model_dump(exclude_none=True),
                page=page, size=size,
            )
            visible = [
                EngineeringObjectResponse.model_validate(item)
                for item in items
                if self.authorization.authorize(
                    actor=actor, context=context, current_state=item,
                    target_state={},
                )
            ]
            return EngineeringObjectListResponse(
                items=visible, total=total, page=page, size=size
            )

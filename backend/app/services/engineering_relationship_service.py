"""PATCH-026 EngineeringRelationship application orchestration."""

from hashlib import sha256
import json
from uuid import UUID, uuid4

from app.enums import EngineeringRelationshipLifecycle, RelationshipFamily, RelationshipType
from app.exceptions.engineering_relationship import (
    EngineeringRelationshipCycleRejected,
    EngineeringRelationshipDuplicate,
    EngineeringRelationshipInvalidDomainTransition,
    EngineeringRelationshipProtectedNotFound,
    EngineeringRelationshipVersionConflict,
)
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_relationship_command import (
    ApproveEngineeringRelationship, CreateEngineeringRelationship,
    DisputeEngineeringRelationship, EngineeringRelationshipCommandError,
    EngineeringRelationshipInvariantViolation,
    EngineeringRelationshipVersionMismatch, RelationshipCommandMetadata,
    RejectEngineeringRelationship, ReviewEngineeringRelationship,
    SubmitEngineeringRelationshipForReview,
    TransferEngineeringRelationshipSteward,
    TransitionEngineeringRelationshipLifecycle,
)
from app.schemas.engineering_relationship import (
    EngineeringRelationshipListResponse, EngineeringRelationshipResponse,
    EngineeringRelationshipTraversalResponse,
)


def _fingerprint(command_type, data):
    return sha256(json.dumps(
        {"command_type": command_type, "data": data}, sort_keys=True,
        default=str, separators=(",", ":"),
    ).encode()).hexdigest()


def _allowed(item):
    actions = ["transfer_steward"]
    by_authority = {
        "draft": ["submit"], "proposed": ["review", "reject"],
        "reviewed": ["approve", "reject"], "approved": ["dispute"],
        "disputed": ["review", "reject"],
    }
    actions.extend(by_authority.get(item.authority_standing, ()))
    if item.lifecycle not in ("superseded", "rejected"):
        actions.append("transition_lifecycle")
    return actions


def _response(item):
    data = {column.name: getattr(item, column.name) for column in item.__table__.columns}
    data["allowed_actions"] = _allowed(item)
    return EngineeringRelationshipResponse.model_validate(data)


class EngineeringRelationshipService:
    def __init__(self, *, uow_factory, authorization, validator, clock):
        self.uow_factory = uow_factory
        self.authorization = authorization
        self.validator = validator
        self.clock = clock

    @staticmethod
    def _metadata(actor, context, data, correlation_id, idempotency_id):
        return RelationshipCommandMetadata(
            actor=actor, authorization=context, rationale=data.rationale,
            correlation_id=correlation_id, idempotency_id=idempotency_id,
            command_id=uuid4(),
            evidence_references=tuple(data.evidence_references),
        )

    def create(self, *, data, actor, context, correlation_id, idempotency_id):
        target = data.model_dump()
        if not self.authorization.authorize(
            actor=actor, context=context, current_state=None, target_state=target
        ):
            raise EngineeringRelationshipProtectedNotFound()
        metadata = self._metadata(
            actor, context, data, correlation_id, idempotency_id
        )
        fingerprint = _fingerprint("CreateEngineeringRelationship", target)
        with self.uow_factory() as uow:
            prior = uow.idempotency.find(
                actor_id=actor.actor_id,
                command_type="CreateEngineeringRelationship",
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            if prior is not None:
                return EngineeringRelationshipResponse.model_validate(
                    prior.authorized_state
                )
            validation = getattr(uow, "validator", self.validator).validate_creation(
                actor=actor, source_object_id=data.source_object_id,
                target_object_id=data.target_object_id,
                relationship_family=data.relationship_family,
                relationship_type=data.relationship_type,
                steward_id=data.steward_id,
                evidence_references=tuple(data.evidence_references),
            )
            if validation.active_duplicate_exists:
                raise EngineeringRelationshipDuplicate()
            if validation.prohibited_cycle_exists:
                raise EngineeringRelationshipCycleRejected()
            uow.idempotency.reserve(
                actor_id=actor.actor_id,
                command_type="CreateEngineeringRelationship",
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            try:
                aggregate, result = EngineeringRelationship.create(
                    CreateEngineeringRelationship(
                        metadata=metadata,
                        relationship_family=data.relationship_family,
                        relationship_type=data.relationship_type,
                        source_object_id=data.source_object_id,
                        target_object_id=data.target_object_id,
                        organization_id=actor.organization_id,
                        project_id=validation.source_project_id,
                        workspace_id=validation.source_workspace_id,
                        creator_id=actor.actor_id,
                        steward_id=data.steward_id or actor.actor_id,
                        validation=validation,
                    ), self.clock.now(),
                )
            except EngineeringRelationshipInvariantViolation as exc:
                raise EngineeringRelationshipInvalidDomainTransition(str(exc)) from exc
            uow.engineering_relationships.add(aggregate)
            response = _response(aggregate)
            self._stage(uow, result, metadata, response)
            uow.commit()
            return response

    def submit_for_review(self, *args, **kwargs):
        return self._named_mutation(*args, command_cls=SubmitEngineeringRelationshipForReview,
                                    aggregate_method="submit_for_review", **kwargs)
    def review(self, *args, **kwargs):
        return self._named_mutation(*args, command_cls=ReviewEngineeringRelationship,
                                    aggregate_method="review", **kwargs)
    def approve(self, *args, **kwargs):
        return self._named_mutation(*args, command_cls=ApproveEngineeringRelationship,
                                    aggregate_method="approve", **kwargs)
    def dispute(self, *args, **kwargs):
        return self._named_mutation(*args, command_cls=DisputeEngineeringRelationship,
                                    aggregate_method="dispute", **kwargs)
    def reject(self, *args, **kwargs):
        return self._named_mutation(*args, command_cls=RejectEngineeringRelationship,
                                    aggregate_method="reject", **kwargs)
    def transition_lifecycle(self, *args, **kwargs):
        return self._named_mutation(
            *args, command_cls=TransitionEngineeringRelationshipLifecycle,
            aggregate_method="transition_lifecycle",
            extra=lambda data: {
                "lifecycle": data.lifecycle,
                "replacement_relationship_id": data.replacement_relationship_id,
            }, **kwargs,
        )
    def transfer_steward(self, *args, **kwargs):
        return self._named_mutation(
            *args, command_cls=TransferEngineeringRelationshipSteward,
            aggregate_method="transfer_steward",
            extra=lambda data: {"steward_id": data.steward_id}, **kwargs,
        )

    def _named_mutation(self, relationship_id, data, actor, context,
                        correlation_id, idempotency_id, *, command_cls,
                        aggregate_method, extra=lambda data: {}):
        command_type = command_cls.__name__
        fingerprint = _fingerprint(command_type, data.model_dump())
        metadata = self._metadata(actor, context, data, correlation_id, idempotency_id)
        with self.uow_factory() as uow:
            aggregate = uow.engineering_relationships.get_authorized(
                relationship_id, actor.organization_id
            )
            if aggregate is None or not self.authorization.authorize(
                actor=actor, context=context, current_state=aggregate,
                target_state=data.model_dump(),
            ):
                raise EngineeringRelationshipProtectedNotFound(relationship_id)
            prior = uow.idempotency.find(
                actor_id=actor.actor_id, command_type=command_type,
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            if prior is not None:
                return EngineeringRelationshipResponse.model_validate(
                    prior.authorized_state
                )
            references = {
                "evidence_references": tuple(data.evidence_references),
                **extra(data),
            }
            getattr(uow, "validator", self.validator).validate_mutation(
                actor=actor, relationship_id=relationship_id,
                references=references,
            )
            uow.idempotency.reserve(
                actor_id=actor.actor_id, command_type=command_type,
                idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            command = command_cls(
                metadata=metadata, relationship_id=relationship_id,
                relationship_family=RelationshipFamily(
                    aggregate.relationship_family
                ), relationship_type=RelationshipType(
                    aggregate.relationship_type
                ), expected_version=data.expected_version, **extra(data),
            )
            try:
                result = getattr(aggregate, aggregate_method)(
                    command, self.clock.now()
                )
            except EngineeringRelationshipVersionMismatch as exc:
                raise EngineeringRelationshipVersionConflict() from exc
            except EngineeringRelationshipCommandError as exc:
                raise EngineeringRelationshipInvalidDomainTransition(str(exc)) from exc
            if not uow.engineering_relationships.persist_expected_version(
                aggregate, data.expected_version
            ):
                raise EngineeringRelationshipVersionConflict()
            response = _response(aggregate)
            self._stage(uow, result, metadata, response)
            uow.commit()
            return response

    def get(self, relationship_id: UUID, actor, context):
        with self.uow_factory() as uow:
            item = uow.engineering_relationships.get_authorized(
                relationship_id, actor.organization_id
            )
            if item is None or not self.authorization.authorize(
                actor=actor, context=context, current_state=item, target_state={}
            ):
                raise EngineeringRelationshipProtectedNotFound(relationship_id)
            return _response(item)

    def list_for_endpoint(self, *, object_id, filters, page, size, actor, context):
        return self._query_edges(
            "list_for_endpoint", actor, context, object_id=object_id,
            filters=filters.model_dump(), page=page, size=size,
        )

    def neighborhood(self, *, object_id, traversal, actor, context):
        return self._traversal(
            "bounded_neighborhood", actor, context, object_id=object_id,
            filters=traversal.model_dump(), max_depth=traversal.max_depth,
            max_results=traversal.max_results,
        )

    def path(self, *, object_id, target_object_id, traversal, actor, context):
        return self._traversal(
            "bounded_path", actor, context, source_object_id=object_id,
            target_object_id=target_object_id, filters=traversal.model_dump(),
            max_depth=traversal.max_depth, max_results=traversal.max_results,
        )

    def _query_edges(self, method, actor, context, **kwargs):
        with self.uow_factory() as uow:
            items, total = getattr(uow.engineering_relationships, method)(
                organization_id=actor.organization_id, **kwargs
            )
            visible = [item for item in items if self.authorization.authorize(
                actor=actor, context=context, current_state=item, target_state={}
            )]
            return EngineeringRelationshipListResponse(
                items=[_response(item) for item in visible],
                total=len(visible),
                page=kwargs["page"], size=kwargs["size"],
            )

    def _traversal(self, method, actor, context, **kwargs):
        with self.uow_factory() as uow:
            edges, _, truncated = getattr(
                uow.engineering_relationships, method
            )(organization_id=actor.organization_id, **kwargs)
            visible = [edge for edge in edges if self.authorization.authorize(
                actor=actor, context=context, current_state=edge, target_state={}
            )]
            nodes = sorted({node for edge in visible for node in (
                edge.source_object_id, edge.target_object_id
            )}, key=str)
            return EngineeringRelationshipTraversalResponse(
                node_ids=nodes, relationships=[_response(edge) for edge in visible],
                bounded_depth=kwargs["max_depth"],
                truncated=len(visible) >= kwargs["max_results"],
                continuation_token=None,
            )

    @staticmethod
    def _stage(uow, result, metadata, response):
        event = result.events[0]
        uow.audit.record(
            command_type=result.command_type, actor=metadata.actor,
            relationship_id=result.relationship_id,
            correlation_id=metadata.correlation_id,
            idempotency_id=metadata.idempotency_id,
            rationale=metadata.rationale,
            previous_version=result.previous_version, version=result.version,
            relationship_family=event.relationship_family,
            relationship_type=event.relationship_type,
        )
        uow.domain_events.record(result.events)
        uow.idempotency.record_result(result, response.model_dump())

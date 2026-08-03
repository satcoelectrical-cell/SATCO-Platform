"""Application orchestration for Universal Engineering Capture."""

from hashlib import sha256
import json
from uuid import UUID, uuid4

from app.exceptions.engineering_experience_capture import (
    EngineeringExperienceCaptureInvalidContext,
    EngineeringExperienceCaptureInvalidLifecycleTransition,
    EngineeringExperienceCaptureInvalidSupersession,
    EngineeringExperienceCaptureProtectedNotFound,
    EngineeringExperienceCaptureValidationError,
    EngineeringExperienceCaptureVersionConflict,
)
from app.models.engineering_experience_capture import (
    EngineeringExperienceCapture,
    normalize_capture_text,
    normalize_single_line_text,
)
from app.models.engineering_experience_capture_command import (
    CreateEngineeringExperienceCapture,
    EngineeringExperienceCaptureCommandError,
    EngineeringExperienceCaptureContentRejected,
    EngineeringExperienceCaptureContextRejected,
    EngineeringExperienceCaptureMetadata,
    EngineeringExperienceCaptureSupersessionRejected,
    EngineeringExperienceCaptureTransitionRejected,
    EngineeringExperienceCaptureVersionMismatch,
    SupersedeEngineeringExperienceCapture,
    WithdrawEngineeringExperienceCapture,
)
from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureListResponse,
    EngineeringExperienceCaptureResponse,
    EngineeringExperienceCaptureSupersessionChainResponse,
)


def _fingerprint(command_type: str, data: dict[str, object]) -> str:
    encoded = json.dumps(
        {"command_type": command_type, "data": data},
        sort_keys=True, default=str, separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _state(capture: EngineeringExperienceCapture, allowed_actions=()):
    values = {column.name: getattr(capture, column.name) for column in capture.__table__.columns}
    values["allowed_actions"] = tuple(allowed_actions)
    return EngineeringExperienceCaptureResponse.model_validate(values)


class EngineeringExperienceCaptureService:
    def __init__(self, *, uow_factory) -> None:
        self.uow_factory = uow_factory

    @staticmethod
    def _metadata(actor, rationale: str, correlation_id: UUID, idempotency_id: UUID):
        return EngineeringExperienceCaptureMetadata(
            actor=actor, rationale=rationale, correlation_id=correlation_id,
            idempotency_id=idempotency_id, command_id=uuid4(),
        )

    @staticmethod
    def _actions(uow, capture, actor):
        if capture.lifecycle != "captured":
            return ()
        return tuple(
            action for action in ("withdraw", "supersede")
            if uow.authorization.authorize(
                actor=actor, operation=action, capture=capture,
            )
        )

    @staticmethod
    def _require_visible(uow, capture_id, actor, operation="read"):
        capture = uow.captures.get_scoped(capture_id, actor.organization_id)
        if capture is None or not uow.authorization.authorize(
            actor=actor, operation=operation, capture=capture,
        ):
            raise EngineeringExperienceCaptureProtectedNotFound()
        return capture

    @staticmethod
    def _stage(uow, result, metadata, response):
        uow.audit.record(
            actor=metadata.actor, capture_id=result.capture_id,
            command_type=result.command_type, lifecycle=response.lifecycle.value,
            version=result.version, project_id=response.project_id,
            workspace_id=response.workspace_id,
            engineering_object_id=response.engineering_object_id,
            correlation_id=metadata.correlation_id,
            idempotency_id=metadata.idempotency_id,
            previous_version=result.previous_version,
            replacement_capture_id=response.superseded_by_capture_id,
        )
        uow.domain_events.record(result.events)
        uow.idempotency.record_result(result, response.model_dump())

    @classmethod
    def _replay(cls, uow, prior, capture, actor):
        safe_state = dict(prior.authorized_state)
        safe_state["original_content"] = capture.original_content
        safe_state["source_reference"] = capture.source_reference
        safe_state["allowed_actions"] = cls._actions(uow, capture, actor)
        return EngineeringExperienceCaptureResponse.model_validate(safe_state)

    def create(self, *, data, actor, correlation_id, idempotency_id):
        try:
            content = normalize_capture_text(data.original_content, field="original_content", maximum=10_000)
            reference = None if data.source_reference is None else normalize_single_line_text(
                data.source_reference, field="source_reference", maximum=512
            )
        except EngineeringExperienceCaptureContentRejected as exc:
            raise EngineeringExperienceCaptureValidationError() from exc
        fingerprint = _fingerprint("CreateEngineeringExperienceCapture", {
            "project_id": data.project_id, "workspace_id": data.workspace_id,
            "engineering_object_id": data.engineering_object_id,
            "source_kind": data.source_kind.value, "original_content": content,
            "source_reference": reference,
        })
        metadata = self._metadata(actor, "capture submitted", correlation_id, idempotency_id)
        with self.uow_factory() as uow:
            if not uow.authorization.authorize(
                actor=actor, operation="create", project_id=data.project_id,
                workspace_id=data.workspace_id,
                engineering_object_id=data.engineering_object_id,
            ):
                raise EngineeringExperienceCaptureProtectedNotFound()
            context = uow.context.validate(
                actor=actor, project_id=data.project_id, workspace_id=data.workspace_id,
                engineering_object_id=data.engineering_object_id,
            )
            prior = uow.idempotency.find(
                organization_id=actor.organization_id, actor_id=actor.actor_id,
                command_type="CreateEngineeringExperienceCapture",
                idempotency_id=idempotency_id, request_fingerprint=fingerprint,
            )
            if prior is not None:
                capture = self._require_visible(
                    uow, prior.result.capture_id, actor, "read"
                )
                return self._replay(uow, prior, capture, actor)
            uow.idempotency.reserve(
                organization_id=actor.organization_id, actor_id=actor.actor_id,
                command_type="CreateEngineeringExperienceCapture",
                idempotency_id=idempotency_id, request_fingerprint=fingerprint,
            )
            command = CreateEngineeringExperienceCapture(
                metadata=metadata, organization_id=actor.organization_id,
                project_id=data.project_id, workspace_id=data.workspace_id,
                discipline=context["discipline"],
                engineering_object_id=data.engineering_object_id,
                source_kind=data.source_kind, original_content=content,
                source_reference=reference, creator_id=actor.actor_id,
            )
            aggregate, result = EngineeringExperienceCapture.create(command, uow.clock.now())
            uow.captures.add(aggregate)
            response = _state(aggregate, ("withdraw", "supersede"))
            self._stage(uow, result, metadata, response)
            uow.commit()
            return response

    def get(self, capture_id, actor):
        with self.uow_factory() as uow:
            capture = self._require_visible(uow, capture_id, actor)
            return _state(capture, self._actions(uow, capture, actor))

    def list_project(self, project_id, filters, page, size, actor):
        with self.uow_factory() as uow:
            workspace_scope = uow.authorization.project_list_workspace_scope(
                actor=actor, project_id=project_id
            )
            if workspace_scope == ():
                raise EngineeringExperienceCaptureProtectedNotFound()
            items, total = uow.captures.list_project_scoped(
                organization_id=actor.organization_id, project_id=project_id,
                filters=filters.model_dump(), page=page, size=size,
                authorized_workspace_ids=workspace_scope,
            )
            responses = [_state(item, self._actions(uow, item, actor)) for item in items]
            return EngineeringExperienceCaptureListResponse(
                items=responses, total=total, page=page, size=size,
            )

    def list_workspace(self, workspace_id, filters, page, size, actor):
        with self.uow_factory() as uow:
            try:
                context = uow.context.resolve_workspace(actor=actor, workspace_id=workspace_id)
            except EngineeringExperienceCaptureInvalidContext as exc:
                raise EngineeringExperienceCaptureProtectedNotFound() from exc
            if not uow.authorization.authorize(
                actor=actor, operation="list", project_id=context["project_id"],
                workspace_id=workspace_id,
            ):
                raise EngineeringExperienceCaptureProtectedNotFound()
            items, total = uow.captures.list_workspace_scoped(
                organization_id=actor.organization_id,
                project_id=context["project_id"], workspace_id=workspace_id,
                filters=filters.model_dump(), page=page, size=size,
            )
            responses = [_state(item, self._actions(uow, item, actor)) for item in items]
            return EngineeringExperienceCaptureListResponse(
                items=responses, total=total, page=page, size=size,
            )

    def withdraw(self, capture_id, data, actor, correlation_id, idempotency_id):
        return self._mutate(
            capture_id=capture_id, data=data, actor=actor,
            correlation_id=correlation_id, idempotency_id=idempotency_id,
            command_type="WithdrawEngineeringExperienceCapture", operation="withdraw",
        )

    def supersede(self, capture_id, data, actor, correlation_id, idempotency_id):
        return self._mutate(
            capture_id=capture_id, data=data, actor=actor,
            correlation_id=correlation_id, idempotency_id=idempotency_id,
            command_type="SupersedeEngineeringExperienceCapture", operation="supersede",
        )

    def _mutate(self, *, capture_id, data, actor, correlation_id, idempotency_id,
                command_type, operation):
        try:
            rationale = normalize_single_line_text(data.rationale, field="rationale", maximum=1_000)
        except EngineeringExperienceCaptureContentRejected as exc:
            raise EngineeringExperienceCaptureValidationError() from exc
        fingerprint_data = {
            "capture_id": capture_id, "expected_version": data.expected_version,
            "rationale": rationale,
        }
        if operation == "supersede":
            fingerprint_data["replacement_capture_id"] = data.replacement_capture_id
        fingerprint = _fingerprint(command_type, fingerprint_data)
        metadata = self._metadata(actor, rationale, correlation_id, idempotency_id)
        with self.uow_factory() as uow:
            capture = self._require_visible(uow, capture_id, actor, operation)
            prior = uow.idempotency.find(
                organization_id=actor.organization_id, actor_id=actor.actor_id,
                command_type=command_type, idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            if prior is not None:
                return self._replay(uow, prior, capture, actor)
            if operation == "supersede":
                uow.supersession.validate(
                    original=capture, replacement_capture_id=data.replacement_capture_id,
                    actor=actor, authorization=uow.authorization,
                )
            uow.idempotency.reserve(
                organization_id=actor.organization_id, actor_id=actor.actor_id,
                command_type=command_type, idempotency_id=idempotency_id,
                request_fingerprint=fingerprint,
            )
            try:
                if operation == "withdraw":
                    result = capture.withdraw(
                        WithdrawEngineeringExperienceCapture(metadata, capture_id, data.expected_version),
                        uow.clock.now(),
                    )
                else:
                    result = capture.supersede(
                        SupersedeEngineeringExperienceCapture(
                            metadata, capture_id, data.expected_version, data.replacement_capture_id,
                        ), uow.clock.now(),
                    )
            except EngineeringExperienceCaptureVersionMismatch as exc:
                raise EngineeringExperienceCaptureVersionConflict() from exc
            except EngineeringExperienceCaptureTransitionRejected as exc:
                raise EngineeringExperienceCaptureInvalidLifecycleTransition() from exc
            except EngineeringExperienceCaptureSupersessionRejected as exc:
                raise EngineeringExperienceCaptureInvalidSupersession() from exc
            except (EngineeringExperienceCaptureContextRejected, EngineeringExperienceCaptureCommandError) as exc:
                raise EngineeringExperienceCaptureInvalidContext() from exc
            if not uow.captures.persist_expected_version(capture, data.expected_version):
                raise EngineeringExperienceCaptureVersionConflict()
            response = _state(capture, ())
            self._stage(uow, result, metadata, response)
            uow.commit()
            return response

    def supersession_chain(self, capture_id, actor):
        with self.uow_factory() as uow:
            current = self._require_visible(uow, capture_id, actor)
            items = []
            seen = set()
            while current is not None and len(items) < 20 and current.id not in seen:
                seen.add(current.id)
                items.append(_state(current, self._actions(uow, current, actor)))
                replacement_id = current.superseded_by_capture_id
                if replacement_id is None:
                    break
                current = self._require_visible(uow, replacement_id, actor)
            return EngineeringExperienceCaptureSupersessionChainResponse(items=items)

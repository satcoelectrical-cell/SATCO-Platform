from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy.orm import Session

from app.enums import CommitmentCriticality
from app.enums import CommitmentProviderKind
from app.enums import ContextConfidentiality
from app.enums import ContextRelationshipMeaning
from app.enums import InterfaceCommitmentState
from app.enums import RelationshipEndpointKind
from app.enums import RelationshipLifecycle
from app.enums import WorkspaceStatus
from app.exceptions.engineering_context_relationship import (
    CommitmentLifecycleConflict,
)
from app.exceptions.engineering_context_relationship import CommitmentNotFound
from app.exceptions.engineering_context_relationship import (
    CommitmentVersionConflict,
)
from app.exceptions.engineering_context_relationship import (
    DuplicateRelationship,
)
from app.exceptions.engineering_context_relationship import InvalidCommitment
from app.exceptions.engineering_context_relationship import InvalidRelationship
from app.exceptions.engineering_context_relationship import (
    RelationshipForbidden,
)
from app.exceptions.engineering_context_relationship import (
    RelationshipLifecycleConflict,
)
from app.exceptions.engineering_context_relationship import (
    RelationshipNotFound,
)
from app.exceptions.engineering_context_relationship import (
    RelationshipVersionConflict,
)
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
)
from app.models.engineering_context_relationship import InterfaceCommitment
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.user import User
from app.repositories.engineering_context_relationship_repository import (
    EngineeringContextRelationshipRepository,
)
from app.services.audit_service import create_audit_log


COMMITMENT_TRANSITIONS = {
    InterfaceCommitmentState.IDENTIFIED: {
        InterfaceCommitmentState.ACKNOWLEDGED_BY_PROVIDER,
        InterfaceCommitmentState.REJECTED,
        InterfaceCommitmentState.DISPUTED,
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.ACKNOWLEDGED_BY_PROVIDER: {
        InterfaceCommitmentState.INFORMATION_PROVIDED,
        InterfaceCommitmentState.REJECTED,
        InterfaceCommitmentState.DISPUTED,
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.INFORMATION_PROVIDED: {
        InterfaceCommitmentState.CONSUMER_REVIEW_REQUIRED,
        InterfaceCommitmentState.FULFILLED_FOR_STATED_USE,
        InterfaceCommitmentState.REJECTED,
        InterfaceCommitmentState.DISPUTED,
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.CONSUMER_REVIEW_REQUIRED: {
        InterfaceCommitmentState.FULFILLED_FOR_STATED_USE,
        InterfaceCommitmentState.REJECTED,
        InterfaceCommitmentState.DISPUTED,
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.DISPUTED: {
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.FULFILLED_FOR_STATED_USE: {
        InterfaceCommitmentState.DISPUTED,
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.REJECTED: {
        InterfaceCommitmentState.SUPERSEDED,
    },
    InterfaceCommitmentState.SUPERSEDED: set(),
}


class EngineeringContextRelationshipService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EngineeringContextRelationshipRepository(db)

    def create_relationship(
        self,
        *,
        data: dict,
        current_user: User,
    ) -> dict:
        project = self._project(data.get("project_id"), current_user)
        self._require_active(current_user)
        self._require_project_capability(project, current_user)
        meaning = self._enum(
            ContextRelationshipMeaning,
            data.get("meaning"),
            "Relationship meaning",
        )
        purpose = self._text(data.get("purpose"), "Relationship purpose")
        source = self._endpoint(
            project=project,
            values=data.get("source"),
            label="source",
        )
        target = self._endpoint(
            project=project,
            values=data.get("target"),
            label="target",
        )
        if source == target:
            raise InvalidRelationship("A relationship cannot reference itself")
        steward = self._active_user(data.get("steward_id"))
        values = {
            "relationship_key": str(uuid4()),
            "project_id": project.id,
            "meaning": meaning.value,
            "purpose": purpose,
            "applicability": self._optional_text(data.get("applicability")),
            "source_role": self._text(
                data.get("source_role"),
                "Source role",
            ),
            "target_role": self._text(
                data.get("target_role"),
                "Target role",
            ),
            **self._endpoint_columns("source", source),
            **self._endpoint_columns("target", target),
            "steward_id": steward.id,
            "created_by_id": current_user.id,
            "lifecycle": RelationshipLifecycle.CURRENT.value,
            "version": 1,
        }
        if self.repository.equivalent_current_exists(values):
            raise DuplicateRelationship()
        try:
            relationship_record = self.repository.create_relationship(values)
            self._audit(
                current_user=current_user,
                action="CONTEXT_RELATIONSHIP_CREATED",
                entity="CONTEXT_RELATIONSHIP",
                entity_id=relationship_record.id,
                details={
                    "project_id": project.id,
                    "meaning": meaning.value,
                    "source": source,
                    "target": target,
                    "version": 1,
                },
            )
        except Exception:
            self.db.rollback()
            raise
        return self._relationship_response(relationship_record)

    def get_relationship(
        self,
        *,
        relationship_id: int,
        current_user: User,
    ) -> dict:
        self._require_active(current_user)
        relationship_record = self.repository.get_visible_relationship(
            relationship_id,
            current_user,
        )
        if relationship_record is None:
            raise RelationshipNotFound()
        return self._relationship_response(relationship_record)

    def list_relationships(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
        page: int = 1,
        size: int = 50,
        include_withdrawn: bool = False,
    ) -> dict:
        self._require_active(current_user)
        self._bounded_page(page, size)
        items, total = self.repository.list_relationships(
            project_id=project_id,
            workspace_id=workspace_id,
            current_user=current_user,
            page=page,
            size=size,
            include_withdrawn=include_withdrawn,
        )
        return {
            "items": [self._relationship_response(item) for item in items],
            "total": total,
            "page": page,
            "size": size,
        }

    def update_relationship_metadata(
        self,
        *,
        relationship_id: int,
        expected_version: int,
        purpose: str,
        applicability: str | None,
        reason: str,
        current_user: User,
    ) -> dict:
        relationship_record = self._relationship_for_mutation(
            relationship_id,
            current_user,
        )
        values = {
            "purpose": self._text(purpose, "Relationship purpose"),
            "applicability": self._optional_text(applicability),
        }
        return self._mutate_relationship(
            relationship_record=relationship_record,
            expected_version=expected_version,
            values=values,
            action="CONTEXT_RELATIONSHIP_METADATA_CHANGED",
            reason=reason,
            current_user=current_user,
        )

    def change_relationship_steward(
        self,
        *,
        relationship_id: int,
        expected_version: int,
        steward_id: int,
        reason: str,
        current_user: User,
    ) -> dict:
        relationship_record = self._relationship_for_mutation(
            relationship_id,
            current_user,
            governance=True,
        )
        steward = self._active_user(steward_id)
        return self._mutate_relationship(
            relationship_record=relationship_record,
            expected_version=expected_version,
            values={"steward_id": steward.id},
            action="CONTEXT_RELATIONSHIP_RESPONSIBILITY_CHANGED",
            reason=reason,
            current_user=current_user,
        )

    def set_relationship_lifecycle(
        self,
        *,
        relationship_id: int,
        target: str,
        expected_version: int,
        reason: str,
        current_user: User,
    ) -> dict:
        relationship_record = self._relationship_for_mutation(
            relationship_id,
            current_user,
            governance=True,
        )
        target_state = self._enum(
            RelationshipLifecycle,
            target,
            "Relationship lifecycle",
        )
        current = RelationshipLifecycle(relationship_record.lifecycle)
        if current == target_state:
            raise RelationshipLifecycleConflict(
                current.value,
                target_state.value,
            )
        now = datetime.now(timezone.utc)
        withdrawing = target_state == RelationshipLifecycle.WITHDRAWN
        return self._mutate_relationship(
            relationship_record=relationship_record,
            expected_version=expected_version,
            values={
                "lifecycle": target_state.value,
                "withdrawal_reason": self._text(reason, "Reason")
                if withdrawing
                else None,
                "withdrawn_at": now if withdrawing else None,
            },
            action=(
                "CONTEXT_RELATIONSHIP_WITHDRAWN"
                if withdrawing
                else "CONTEXT_RELATIONSHIP_RESTORED"
            ),
            reason=reason,
            current_user=current_user,
        )

    def create_commitment(
        self,
        *,
        data: dict,
        current_user: User,
    ) -> dict:
        self._require_active(current_user)
        relationship_record = self.repository.get_relationship(
            data.get("relationship_id")
        )
        if relationship_record is None:
            raise InvalidCommitment("Governing relationship is invalid")
        if relationship_record.commitment is not None:
            raise InvalidCommitment(
                "Governing relationship already has a commitment"
            )
        if relationship_record.lifecycle != RelationshipLifecycle.CURRENT.value:
            raise InvalidCommitment("Governing relationship is withdrawn")
        project = relationship_record.project
        self._require_project_capability(project, current_user)
        provider = self._provider(project, data)
        consumer = self._workspace(
            data.get("consumer_workspace_id"),
            project.id,
            operational=True,
        )
        if (
            provider["kind"] == CommitmentProviderKind.WORKSPACE.value
            and provider["workspace_id"] == consumer.id
        ):
            raise InvalidCommitment(
                "Provider and consumer Workspace must be distinct"
            )
        steward = self._active_user(data.get("steward_id"))
        reviewer = self._active_user(data.get("consumer_reviewer_id"))
        if not self.repository.is_workspace_participant(consumer, reviewer.id):
            raise InvalidCommitment(
                "Consumer reviewer must participate in the consumer Workspace"
            )
        confidentiality = self._enum(
            ContextConfidentiality,
            data.get("confidentiality"),
            "Commitment confidentiality",
        )
        if (
            confidentiality == ContextConfidentiality.RESTRICTED
            and provider.get("user_id") != current_user.id
            and steward.id != current_user.id
        ):
            raise RelationshipForbidden()
        values = {
            "commitment_key": str(uuid4()),
            "relationship_id": relationship_record.id,
            "project_id": project.id,
            "provider_kind": provider["kind"],
            "provider_user_id": provider.get("user_id"),
            "provider_workspace_id": provider.get("workspace_id"),
            "provider_external_key": provider.get("external_key"),
            "consumer_workspace_id": consumer.id,
            "required_information": self._text(
                data.get("required_information"),
                "Required information",
            ),
            "intended_use": self._text(
                data.get("intended_use"),
                "Intended use",
            ),
            "completeness_expectation": self._text(
                data.get("completeness_expectation"),
                "Completeness expectation",
            ),
            "expected_source_basis": self._text(
                data.get("expected_source_basis"),
                "Expected source basis",
            ),
            "stage_or_due_condition": self._text(
                data.get("stage_or_due_condition"),
                "Stage or due condition",
            ),
            "criticality": self._enum(
                CommitmentCriticality,
                data.get("criticality"),
                "Commitment criticality",
            ).value,
            "confidentiality": confidentiality.value,
            "steward_id": steward.id,
            "consumer_reviewer_id": reviewer.id,
            "state": InterfaceCommitmentState.IDENTIFIED.value,
            "external_review_required": bool(
                data.get("external_review_required", False)
            ),
            "current_use": True,
            "reassessment_needed": False,
            "version": 1,
            "created_by_id": current_user.id,
        }
        try:
            commitment = self.repository.create_commitment(values)
            self._audit(
                current_user=current_user,
                action="INTERFACE_COMMITMENT_CREATED",
                entity="INTERFACE_COMMITMENT",
                entity_id=commitment.id,
                details={
                    "project_id": project.id,
                    "relationship_id": relationship_record.id,
                    "provider_kind": provider["kind"],
                    "consumer_workspace_id": consumer.id,
                    "state": commitment.state,
                    "version": 1,
                },
            )
        except Exception:
            self.db.rollback()
            raise
        return self._commitment_response(commitment)

    def get_commitment(
        self,
        *,
        commitment_id: int,
        current_user: User,
    ) -> dict:
        self._require_active(current_user)
        commitment = self.repository.get_visible_commitment(
            commitment_id,
            current_user,
        )
        if commitment is None:
            raise CommitmentNotFound()
        return self._commitment_response(commitment)

    def list_commitments(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
        page: int = 1,
        size: int = 50,
        include_withdrawn: bool = False,
    ) -> dict:
        self._require_active(current_user)
        self._bounded_page(page, size)
        items, total = self.repository.list_commitments(
            project_id=project_id,
            workspace_id=workspace_id,
            current_user=current_user,
            page=page,
            size=size,
            include_withdrawn=include_withdrawn,
        )
        return {
            "items": [self._commitment_response(item) for item in items],
            "total": total,
            "page": page,
            "size": size,
        }

    def transition_commitment(
        self,
        *,
        commitment_id: int,
        target: str,
        expected_version: int,
        reason: str,
        current_user: User,
        supplied_source_key: str | None = None,
        supplied_revision: str | None = None,
        fulfilment_use: str | None = None,
        external_review_evidence: str | None = None,
        successor_commitment_id: int | None = None,
    ) -> dict:
        commitment = self._commitment_for_mutation(
            commitment_id,
            current_user,
        )
        target_state = self._enum(
            InterfaceCommitmentState,
            target,
            "Commitment state",
        )
        current_state = InterfaceCommitmentState(commitment.state)
        if target_state not in COMMITMENT_TRANSITIONS[current_state]:
            raise CommitmentLifecycleConflict(
                current_state.value,
                target_state.value,
            )
        self._authorize_transition(commitment, target_state, current_user)
        values: dict = {"state": target_state.value}
        if target_state == InterfaceCommitmentState.INFORMATION_PROVIDED:
            values.update(
                supplied_source_key=self._text(
                    supplied_source_key,
                    "Supplied source",
                ),
                supplied_revision=self._text(
                    supplied_revision,
                    "Supplied revision",
                ),
            )
        if target_state == InterfaceCommitmentState.FULFILLED_FOR_STATED_USE:
            if not commitment.supplied_source_key:
                raise InvalidCommitment(
                    "Information must be provided before fulfilment"
                )
            if commitment.reassessment_needed:
                raise InvalidCommitment(
                    "Reassessment must be cleared before fulfilment"
                )
            values["fulfilment_use"] = self._text(
                fulfilment_use,
                "Fulfilment use",
            )
            if (
                commitment.external_review_required
                and external_review_evidence is None
            ):
                raise InvalidCommitment(
                    "External review evidence is required for fulfilment"
                )
            if external_review_evidence is not None:
                values["external_review_evidence"] = self._text(
                    external_review_evidence,
                    "External review evidence",
                )
        if target_state == InterfaceCommitmentState.SUPERSEDED:
            successor = self.repository.get_commitment(
                successor_commitment_id
            )
            if (
                successor is None
                or successor.id == commitment.id
                or successor.project_id != commitment.project_id
            ):
                raise InvalidCommitment(
                    "A distinct same-Project successor is required"
                )
            values["successor_commitment_id"] = successor.id
        return self._mutate_commitment(
            commitment=commitment,
            expected_version=expected_version,
            values=values,
            action=f"INTERFACE_COMMITMENT_{target_state.value.upper()}",
            reason=reason,
            current_user=current_user,
        )

    def set_commitment_current_use(
        self,
        *,
        commitment_id: int,
        current_use: bool,
        expected_version: int,
        reason: str,
        current_user: User,
    ) -> dict:
        commitment = self._commitment_for_mutation(
            commitment_id,
            current_user,
            governance=True,
        )
        if commitment.current_use == current_use:
            raise InvalidCommitment("Commitment current-use standing is unchanged")
        now = datetime.now(timezone.utc)
        return self._mutate_commitment(
            commitment=commitment,
            expected_version=expected_version,
            values={
                "current_use": current_use,
                "withdrawal_reason": None
                if current_use
                else self._text(reason, "Reason"),
                "withdrawn_at": None if current_use else now,
            },
            action=(
                "INTERFACE_COMMITMENT_RESTORED"
                if current_use
                else "INTERFACE_COMMITMENT_WITHDRAWN"
            ),
            reason=reason,
            current_user=current_user,
        )

    def set_reassessment(
        self,
        *,
        commitment_id: int,
        needed: bool,
        expected_version: int,
        trigger: str | None,
        reason: str,
        current_user: User,
    ) -> dict:
        commitment = self._commitment_for_mutation(
            commitment_id,
            current_user,
        )
        return self._mutate_commitment(
            commitment=commitment,
            expected_version=expected_version,
            values={
                "reassessment_needed": needed,
                "reassessment_trigger": self._text(
                    trigger,
                    "Reassessment trigger",
                )
                if needed
                else None,
                "reassessment_reason": self._text(reason, "Reason")
                if needed
                else None,
            },
            action=(
                "INTERFACE_COMMITMENT_REASSESSMENT_RECORDED"
                if needed
                else "INTERFACE_COMMITMENT_REASSESSMENT_CLEARED"
            ),
            reason=reason,
            current_user=current_user,
        )

    def change_commitment_responsibility(
        self,
        *,
        commitment_id: int,
        expected_version: int,
        field: str,
        value,
        reason: str,
        current_user: User,
    ) -> dict:
        commitment = self._commitment_for_mutation(
            commitment_id,
            current_user,
            governance=True,
        )
        allowed = {
            "steward_id",
            "consumer_reviewer_id",
            "provider_user_id",
            "provider_workspace_id",
            "consumer_workspace_id",
            "criticality",
        }
        if field not in allowed:
            raise InvalidCommitment("Unsupported responsibility change")
        values = self._responsibility_value(commitment, field, value)
        return self._mutate_commitment(
            commitment=commitment,
            expected_version=expected_version,
            values=values,
            action="INTERFACE_COMMITMENT_RESPONSIBILITY_CHANGED",
            reason=reason,
            current_user=current_user,
        )

    def change_supplied_source(
        self,
        *,
        commitment_id: int,
        expected_version: int,
        source_key: str,
        revision: str,
        reason: str,
        current_user: User,
    ) -> dict:
        commitment = self._commitment_for_mutation(
            commitment_id,
            current_user,
        )
        self._require_provider_action(commitment, current_user)
        return self._mutate_commitment(
            commitment=commitment,
            expected_version=expected_version,
            values={
                "supplied_source_key": self._text(
                    source_key,
                    "Supplied source",
                ),
                "supplied_revision": self._text(
                    revision,
                    "Supplied revision",
                ),
                "reassessment_needed": True,
                "reassessment_trigger": f"source:{source_key}@{revision}",
                "reassessment_reason": self._text(reason, "Reason"),
            },
            action="INTERFACE_COMMITMENT_SOURCE_REVISION_CHANGED",
            reason=reason,
            current_user=current_user,
        )

    def _mutate_relationship(
        self,
        *,
        relationship_record: EngineeringContextRelationship,
        expected_version: int,
        values: dict,
        action: str,
        reason: str,
        current_user: User,
    ) -> dict:
        self._positive_version(expected_version)
        before = self._relationship_response(relationship_record)
        try:
            if not self.repository.update_relationship_versioned(
                relationship_id=relationship_record.id,
                expected_version=expected_version,
                values=values,
            ):
                raise RelationshipVersionConflict()
            self._audit(
                current_user=current_user,
                action=action,
                entity="CONTEXT_RELATIONSHIP",
                entity_id=relationship_record.id,
                details={
                    "project_id": relationship_record.project_id,
                    "reason": self._text(reason, "Reason"),
                    "before": before,
                    "after": {**values, "version": expected_version + 1},
                },
            )
        except Exception:
            self.db.rollback()
            raise
        self.db.expire_all()
        return self._relationship_response(
            self.repository.get_relationship(relationship_record.id)
        )

    def _mutate_commitment(
        self,
        *,
        commitment: InterfaceCommitment,
        expected_version: int,
        values: dict,
        action: str,
        reason: str,
        current_user: User,
    ) -> dict:
        self._positive_version(expected_version)
        before = self._commitment_response(commitment)
        try:
            if not self.repository.update_commitment_versioned(
                commitment_id=commitment.id,
                expected_version=expected_version,
                values=values,
            ):
                raise CommitmentVersionConflict()
            self._audit(
                current_user=current_user,
                action=action,
                entity="INTERFACE_COMMITMENT",
                entity_id=commitment.id,
                details={
                    "project_id": commitment.project_id,
                    "provider_workspace_id": commitment.provider_workspace_id,
                    "consumer_workspace_id":
                        commitment.consumer_workspace_id,
                    "reason": self._text(reason, "Reason"),
                    "before": before,
                    "after": {**values, "version": expected_version + 1},
                },
            )
        except Exception:
            self.db.rollback()
            raise
        self.db.expire_all()
        return self._commitment_response(
            self.repository.get_commitment(commitment.id)
        )

    def _relationship_for_mutation(
        self,
        relationship_id: int,
        current_user: User,
        *,
        governance: bool = False,
    ) -> EngineeringContextRelationship:
        self._require_active(current_user)
        relationship_record = self.repository.get_relationship(
            relationship_id
        )
        if relationship_record is None:
            raise RelationshipNotFound()
        allowed = current_user.id in {
            relationship_record.steward_id,
            relationship_record.project.owner_id,
            relationship_record.project.primary_assignee_id,
        }
        if governance:
            allowed = allowed or current_user.role == "admin"
        if not allowed:
            raise RelationshipForbidden()
        return relationship_record

    def _commitment_for_mutation(
        self,
        commitment_id: int,
        current_user: User,
        *,
        governance: bool = False,
    ) -> InterfaceCommitment:
        self._require_active(current_user)
        commitment = self.repository.get_commitment(commitment_id)
        if commitment is None:
            raise CommitmentNotFound()
        allowed = current_user.id in {
            commitment.steward_id,
            commitment.consumer_reviewer_id,
            commitment.provider_user_id,
            commitment.project.owner_id,
            commitment.project.primary_assignee_id,
        }
        for workspace in (
            commitment.provider_workspace,
            commitment.consumer_workspace,
        ):
            if workspace is not None:
                allowed = allowed or self.repository.is_workspace_participant(
                    workspace,
                    current_user.id,
                )
        if governance:
            allowed = allowed or current_user.role == "admin"
        if not allowed:
            raise RelationshipForbidden()
        return commitment

    def _authorize_transition(
        self,
        commitment: InterfaceCommitment,
        target: InterfaceCommitmentState,
        current_user: User,
    ) -> None:
        provider_actions = {
            InterfaceCommitmentState.ACKNOWLEDGED_BY_PROVIDER,
            InterfaceCommitmentState.INFORMATION_PROVIDED,
        }
        consumer_actions = {
            InterfaceCommitmentState.CONSUMER_REVIEW_REQUIRED,
            InterfaceCommitmentState.FULFILLED_FOR_STATED_USE,
        }
        if target in provider_actions:
            self._require_provider_action(commitment, current_user)
        elif target in consumer_actions:
            self._require_consumer_action(commitment, current_user)

    def _require_provider_action(
        self,
        commitment: InterfaceCommitment,
        current_user: User,
    ) -> None:
        allowed = commitment.provider_user_id == current_user.id
        if commitment.provider_workspace is not None:
            allowed = allowed or self.repository.is_workspace_participant(
                commitment.provider_workspace,
                current_user.id,
            )
        if not allowed:
            raise RelationshipForbidden()

    def _require_consumer_action(
        self,
        commitment: InterfaceCommitment,
        current_user: User,
    ) -> None:
        if current_user.id != commitment.consumer_reviewer_id:
            raise RelationshipForbidden()
        if not self.repository.is_workspace_participant(
            commitment.consumer_workspace,
            current_user.id,
        ):
            raise RelationshipForbidden()

    def _endpoint(
        self,
        *,
        project: Project,
        values: dict | None,
        label: str,
    ) -> dict:
        if not isinstance(values, dict):
            raise InvalidRelationship(f"Relationship {label} is required")
        kind = self._enum(
            RelationshipEndpointKind,
            values.get("kind"),
            f"{label.title()} kind",
        )
        endpoint = {"kind": kind.value}
        if kind == RelationshipEndpointKind.CONTEXT:
            context = self.repository.get_context(values.get("context_id"))
            if context is None or context.project_id != project.id:
                raise InvalidRelationship(f"Invalid {label} Context")
            endpoint["context_id"] = context.id
        elif kind == RelationshipEndpointKind.PROJECT:
            if values.get("project_id") != project.id:
                raise InvalidRelationship(f"Invalid {label} Project")
            endpoint["project_id"] = project.id
        elif kind == RelationshipEndpointKind.WORKSPACE:
            workspace = self._workspace(
                values.get("workspace_id"),
                project.id,
                operational=False,
            )
            endpoint["workspace_id"] = workspace.id
        elif kind == RelationshipEndpointKind.DISCIPLINE:
            endpoint["discipline"] = self._text(
                values.get("discipline"),
                f"{label.title()} discipline",
            )
        else:
            endpoint["external_key"] = self._text(
                values.get("external_key"),
                f"{label.title()} external source",
            )
        return endpoint

    @staticmethod
    def _endpoint_columns(prefix: str, endpoint: dict) -> dict:
        return {
            f"{prefix}_kind": endpoint["kind"],
            f"{prefix}_context_id": endpoint.get("context_id"),
            f"{prefix}_project_id": endpoint.get("project_id"),
            f"{prefix}_workspace_id": endpoint.get("workspace_id"),
            f"{prefix}_discipline": endpoint.get("discipline"),
            f"{prefix}_external_key": endpoint.get("external_key"),
        }

    def _provider(self, project: Project, data: dict) -> dict:
        kind = self._enum(
            CommitmentProviderKind,
            data.get("provider_kind"),
            "Provider kind",
        )
        provider = {"kind": kind.value}
        if kind == CommitmentProviderKind.USER:
            provider["user_id"] = self._active_user(
                data.get("provider_user_id")
            ).id
        elif kind == CommitmentProviderKind.WORKSPACE:
            provider["workspace_id"] = self._workspace(
                data.get("provider_workspace_id"),
                project.id,
                operational=True,
            ).id
        else:
            provider["external_key"] = self._text(
                data.get("provider_external_key"),
                "External provider",
            )
        return provider

    def _responsibility_value(
        self,
        commitment: InterfaceCommitment,
        field: str,
        value,
    ) -> dict:
        if field in {"steward_id", "consumer_reviewer_id", "provider_user_id"}:
            return {field: self._active_user(value).id}
        if field in {"provider_workspace_id", "consumer_workspace_id"}:
            workspace = self._workspace(
                value,
                commitment.project_id,
                operational=True,
            )
            if field == "consumer_workspace_id":
                return {field: workspace.id}
            return {
                "provider_kind": CommitmentProviderKind.WORKSPACE.value,
                "provider_workspace_id": workspace.id,
                "provider_user_id": None,
                "provider_external_key": None,
            }
        return {
            "criticality": self._enum(
                CommitmentCriticality,
                value,
                "Commitment criticality",
            ).value
        }

    def _project(self, project_id, current_user: User) -> Project:
        project = self.repository.get_project(project_id, current_user)
        if project is None:
            raise InvalidRelationship("Governing Project is invalid")
        return project

    def _workspace(
        self,
        workspace_id,
        project_id: int,
        *,
        operational: bool,
    ) -> EngineeringWorkspace:
        workspace = self.repository.get_workspace(workspace_id)
        if workspace is None or workspace.project_id != project_id:
            raise InvalidRelationship("Workspace is outside governing Project")
        if operational and workspace.status == WorkspaceStatus.ARCHIVED.value:
            raise InvalidCommitment("Archived Workspace is not operational")
        return workspace

    def _active_user(self, user_id) -> User:
        user = self.repository.get_user(user_id)
        if user is None or not user.is_active:
            raise InvalidRelationship(
                "Responsibility requires an active internal User"
            )
        return user

    @staticmethod
    def _require_active(current_user: User) -> None:
        if not current_user.is_active:
            raise RelationshipForbidden()

    @staticmethod
    def _require_project_capability(
        project: Project,
        current_user: User,
    ) -> None:
        if current_user.role == "admin":
            return
        if current_user.id in {
            project.owner_id,
            project.primary_assignee_id,
        }:
            return
        raise RelationshipForbidden()

    @staticmethod
    def _positive_version(expected_version: int) -> None:
        if not isinstance(expected_version, int) or expected_version < 1:
            raise InvalidRelationship("Expected version must be positive")

    @staticmethod
    def _bounded_page(page: int, size: int) -> None:
        if page < 1 or size < 1 or size > 100:
            raise InvalidRelationship("Pagination is outside bounded limits")

    @staticmethod
    def _enum(enum_type, value, label: str):
        try:
            return enum_type(value)
        except (TypeError, ValueError) as exc:
            raise InvalidRelationship(f"{label} is unsupported") from exc

    @staticmethod
    def _text(value, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidRelationship(f"{label} is required")
        return value.strip()

    @staticmethod
    def _optional_text(value) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidRelationship("Text value is invalid")
        return value.strip() or None

    def _audit(
        self,
        *,
        current_user: User,
        action: str,
        entity: str,
        entity_id: int,
        details: dict,
    ) -> None:
        create_audit_log(
            db=self.db,
            user_id=current_user.id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=self._serialized(details),
        )

    @classmethod
    def _serialized(cls, value):
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: cls._serialized(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialized(item) for item in value]
        return value

    @staticmethod
    def _relationship_response(
        relationship_record: EngineeringContextRelationship,
    ) -> dict:
        return {
            "id": relationship_record.id,
            "relationship_key": relationship_record.relationship_key,
            "project_id": relationship_record.project_id,
            "meaning": relationship_record.meaning,
            "purpose": relationship_record.purpose,
            "applicability": relationship_record.applicability,
            "source_kind": relationship_record.source_kind,
            "source_context_id": relationship_record.source_context_id,
            "source_project_id": relationship_record.source_project_id,
            "source_workspace_id": relationship_record.source_workspace_id,
            "source_discipline": relationship_record.source_discipline,
            "source_external_key": relationship_record.source_external_key,
            "target_kind": relationship_record.target_kind,
            "target_context_id": relationship_record.target_context_id,
            "target_project_id": relationship_record.target_project_id,
            "target_workspace_id": relationship_record.target_workspace_id,
            "target_discipline": relationship_record.target_discipline,
            "target_external_key": relationship_record.target_external_key,
            "steward_id": relationship_record.steward_id,
            "lifecycle": relationship_record.lifecycle,
            "version": relationship_record.version,
            "withdrawal_reason": relationship_record.withdrawal_reason,
        }

    @staticmethod
    def _commitment_response(commitment: InterfaceCommitment) -> dict:
        return {
            "id": commitment.id,
            "commitment_key": commitment.commitment_key,
            "relationship_id": commitment.relationship_id,
            "project_id": commitment.project_id,
            "provider_kind": commitment.provider_kind,
            "provider_user_id": commitment.provider_user_id,
            "provider_workspace_id": commitment.provider_workspace_id,
            "provider_external_key": commitment.provider_external_key,
            "consumer_workspace_id": commitment.consumer_workspace_id,
            "required_information": commitment.required_information,
            "intended_use": commitment.intended_use,
            "completeness_expectation": commitment.completeness_expectation,
            "expected_source_basis": commitment.expected_source_basis,
            "stage_or_due_condition": commitment.stage_or_due_condition,
            "criticality": commitment.criticality,
            "confidentiality": commitment.confidentiality,
            "steward_id": commitment.steward_id,
            "consumer_reviewer_id": commitment.consumer_reviewer_id,
            "state": commitment.state,
            "supplied_source_key": commitment.supplied_source_key,
            "supplied_revision": commitment.supplied_revision,
            "fulfilment_use": commitment.fulfilment_use,
            "external_review_evidence": commitment.external_review_evidence,
            "external_review_required": commitment.external_review_required,
            "successor_commitment_id": commitment.successor_commitment_id,
            "current_use": commitment.current_use,
            "withdrawal_reason": commitment.withdrawal_reason,
            "reassessment_needed": commitment.reassessment_needed,
            "reassessment_trigger": commitment.reassessment_trigger,
            "reassessment_reason": commitment.reassessment_reason,
            "version": commitment.version,
        }

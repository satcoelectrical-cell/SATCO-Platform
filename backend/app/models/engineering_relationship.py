"""PATCH-026 EngineeringRelationship Aggregate Root and persistence model."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index
from sqlalchemy import Integer, JSON, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import validates
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import ACYCLIC_RELATIONSHIP_PAIRS
from app.enums import CROSS_WORKSPACE_RELATIONSHIP_FAMILIES
from app.enums import EngineeringAuthorityStanding
from app.enums import RELATIONSHIP_TYPES_BY_FAMILY
from app.enums import EngineeringRelationshipLifecycle as RelationshipLifecycle
from app.enums import RelationshipFamily, RelationshipType
from app.enums import validate_relationship_pair
from app.models.engineering_relationship_command import (
    ApproveEngineeringRelationship,
    CreateEngineeringRelationship,
    DisputeEngineeringRelationship,
    EngineeringRelationshipCommandResult,
    EngineeringRelationshipDomainEvent,
    EngineeringRelationshipInvariantViolation,
    EngineeringRelationshipMutation,
    EngineeringRelationshipNoOp,
    EngineeringRelationshipTransitionRejected,
    EngineeringRelationshipVersionMismatch,
    RejectEngineeringRelationship,
    ReviewEngineeringRelationship,
    SubmitEngineeringRelationshipForReview,
    TransferEngineeringRelationshipSteward,
    TransitionEngineeringRelationshipLifecycle,
)


LIFECYCLE_TRANSITIONS = {
    RelationshipLifecycle.PROPOSED: {
        RelationshipLifecycle.CURRENT,
        RelationshipLifecycle.WITHDRAWN,
        RelationshipLifecycle.REJECTED,
    },
    RelationshipLifecycle.CURRENT: {
        RelationshipLifecycle.SUPERSEDED,
        RelationshipLifecycle.WITHDRAWN,
    },
    RelationshipLifecycle.WITHDRAWN: {RelationshipLifecycle.PROPOSED},
    RelationshipLifecycle.SUPERSEDED: set(),
    RelationshipLifecycle.REJECTED: set(),
}


def _quoted(values) -> str:
    return ", ".join(f"'{value.value}'" for value in values)


def _family_type_constraint() -> str:
    clauses = []
    for family, relationship_types in RELATIONSHIP_TYPES_BY_FAMILY.items():
        types = _quoted(sorted(relationship_types, key=lambda item: item.value))
        clauses.append(
            f"(relationship_family = '{family.value}' "
            f"AND relationship_type IN ({types}))"
        )
    return " OR ".join(clauses)


class EngineeringRelationship(Base):
    """Governed directional edge between two EngineeringObject UUIDs."""

    __tablename__ = "engineering_relationships"
    __table_args__ = (
        CheckConstraint(
            f"relationship_family IN ({_quoted(RelationshipFamily)})",
            name="ck_engineering_relationships_family",
        ),
        CheckConstraint(
            f"relationship_type IN ({_quoted(RelationshipType)})",
            name="ck_engineering_relationships_type",
        ),
        CheckConstraint(
            _family_type_constraint(),
            name="ck_engineering_relationships_family_type",
        ),
        CheckConstraint(
            f"lifecycle IN ({_quoted(RelationshipLifecycle)})",
            name="ck_engineering_relationships_lifecycle",
        ),
        CheckConstraint(
            f"authority_standing IN ({_quoted(EngineeringAuthorityStanding)})",
            name="ck_engineering_relationships_authority",
        ),
        CheckConstraint(
            "source_object_id <> target_object_id",
            name="ck_engineering_relationships_distinct_endpoints",
        ),
        CheckConstraint("version >= 1", name="ck_engineering_relationships_version"),
        CheckConstraint(
            "reviewer_id IS NULL OR approver_id IS NULL "
            "OR reviewer_id <> approver_id",
            name="ck_engineering_relationships_review_approval_separation",
        ),
        CheckConstraint(
            "approver_id IS NULL OR approver_id <> creator_id",
            name="ck_engineering_relationships_creator_approval_separation",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_engineering_relationships_timestamp_order",
        ),
        Index(
            "ix_engineering_relationships_source_scope",
            "organization_id", "project_id", "workspace_id", "source_object_id",
        ),
        Index(
            "ix_engineering_relationships_target_scope",
            "organization_id", "project_id", "workspace_id", "target_object_id",
        ),
        Index(
            "ix_engineering_relationships_vocabulary_lifecycle",
            "relationship_family", "relationship_type", "lifecycle",
        ),
        Index(
            "uq_engineering_relationships_active_identity",
            "organization_id", "project_id", "workspace_id",
            "source_object_id", "target_object_id",
            "relationship_family", "relationship_type",
            unique=True,
            postgresql_where=text("lifecycle IN ('proposed','current')"),
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_object_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("engineering_objects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_object_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("engineering_objects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    relationship_family = Column(String(32), nullable=False)
    relationship_type = Column(String(64), nullable=False)
    lifecycle = Column(
        String(16), nullable=False,
        default=RelationshipLifecycle.PROPOSED.value,
        server_default=RelationshipLifecycle.PROPOSED.value,
    )
    authority_standing = Column(
        String(16), nullable=False,
        default=EngineeringAuthorityStanding.DRAFT.value,
        server_default=EngineeringAuthorityStanding.DRAFT.value,
    )
    evidence_references = Column(JSON, nullable=False, default=list)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    creator_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    steward_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reviewer_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    approver_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    def __init__(self, **values):
        for key in (
            "relationship_family", "relationship_type", "lifecycle",
            "authority_standing",
        ):
            value = values.get(key)
            if isinstance(value, StrEnum):
                values[key] = value.value
        values.setdefault("id", uuid4())
        values.setdefault("lifecycle", RelationshipLifecycle.PROPOSED.value)
        values.setdefault(
            "authority_standing", EngineeringAuthorityStanding.DRAFT.value
        )
        values.setdefault("evidence_references", [])
        values.setdefault("version", 1)
        super().__init__(**values)
        self._validate_state()

    @validates(
        "relationship_family", "relationship_type", "lifecycle",
        "authority_standing",
    )
    def _validate_controlled(self, key: str, value: StrEnum | str) -> str:
        value = value.value if isinstance(value, StrEnum) else value
        enum_by_key = {
            "relationship_family": RelationshipFamily,
            "relationship_type": RelationshipType,
            "lifecycle": RelationshipLifecycle,
            "authority_standing": EngineeringAuthorityStanding,
        }
        enum_by_key[key](value)
        return value

    def _validate_state(self) -> None:
        family = RelationshipFamily(self.relationship_family)
        relationship_type = RelationshipType(self.relationship_type)
        validate_relationship_pair(family, relationship_type)
        if self.source_object_id == self.target_object_id:
            raise EngineeringRelationshipInvariantViolation(
                "relationship endpoints must be distinct"
            )
        if self.version < 1:
            raise EngineeringRelationshipInvariantViolation(
                "version must be positive"
            )
        if len(self.evidence_references) != len(set(self.evidence_references)):
            raise EngineeringRelationshipInvariantViolation(
                "evidence references must be unique"
            )

    @classmethod
    def create(
        cls, command: CreateEngineeringRelationship, now: datetime
    ) -> tuple["EngineeringRelationship", EngineeringRelationshipCommandResult]:
        """Create an aggregate after trusted reference and graph validation."""

        validation = command.validation
        if command.metadata.actor.organization_id != command.organization_id:
            raise EngineeringRelationshipInvariantViolation(
                "actor and relationship Organization scopes differ"
            )
        if {
            validation.source_organization_id,
            validation.target_organization_id,
            command.organization_id,
        } != {command.organization_id}:
            raise EngineeringRelationshipInvariantViolation(
                "cross-organization relationships are prohibited"
            )
        if {
            validation.source_project_id,
            validation.target_project_id,
            command.project_id,
        } != {command.project_id}:
            raise EngineeringRelationshipInvariantViolation(
                "cross-project relationships are prohibited"
            )
        if command.workspace_id != validation.source_workspace_id:
            raise EngineeringRelationshipInvariantViolation(
                "governing Workspace must be the source Workspace"
            )
        family = RelationshipFamily(command.relationship_family)
        if (
            validation.source_workspace_id != validation.target_workspace_id
            and family not in CROSS_WORKSPACE_RELATIONSHIP_FAMILIES
        ):
            raise EngineeringRelationshipInvariantViolation(
                "relationship family does not permit cross-Workspace scope"
            )
        if validation.active_duplicate_exists:
            raise EngineeringRelationshipInvariantViolation(
                "active duplicate relationship exists"
            )
        pair = (family, RelationshipType(command.relationship_type))
        if validation.prohibited_cycle_exists and pair in ACYCLIC_RELATIONSHIP_PAIRS:
            raise EngineeringRelationshipInvariantViolation(
                "relationship would create a prohibited cycle"
            )
        if command.creator_id != command.metadata.actor.actor_id:
            raise EngineeringRelationshipInvariantViolation(
                "Creator must be the authenticated actor"
            )
        aggregate = cls(
            id=uuid4(), organization_id=command.organization_id,
            project_id=command.project_id, workspace_id=command.workspace_id,
            source_object_id=command.source_object_id,
            target_object_id=command.target_object_id,
            relationship_family=family,
            relationship_type=command.relationship_type,
            evidence_references=[str(item) for item in command.metadata.evidence_references],
            creator_id=command.creator_id, steward_id=command.steward_id,
            created_at=now, updated_at=now,
        )
        return aggregate, aggregate._creation_result(command, now)

    def _creation_result(self, command, now):
        event = self._event(
            command, "EngineeringRelationshipCreated", now,
            {"source_object_id": self.source_object_id,
             "target_object_id": self.target_object_id},
        )
        return EngineeringRelationshipCommandResult(
            relationship_id=self.id, previous_version=None, version=1,
            command_type="CreateEngineeringRelationship",
            correlation_id=command.metadata.correlation_id, events=(event,),
        )

    def _check_mutation(self, command: EngineeringRelationshipMutation) -> None:
        if command.relationship_id != self.id:
            raise EngineeringRelationshipInvariantViolation(
                "command relationship identity does not match aggregate"
            )
        pair = (
            RelationshipFamily(command.relationship_family),
            RelationshipType(command.relationship_type),
        )
        if pair != (
            RelationshipFamily(self.relationship_family),
            RelationshipType(self.relationship_type),
        ):
            raise EngineeringRelationshipInvariantViolation(
                "command vocabulary pair does not match aggregate"
            )
        if command.expected_version != self.version:
            raise EngineeringRelationshipVersionMismatch(
                "expected version does not match current version"
            )

    def _merge_evidence(self, command: EngineeringRelationshipMutation) -> None:
        merged = list(self.evidence_references)
        for reference in command.metadata.evidence_references:
            value = str(reference)
            if value not in merged:
                merged.append(value)
        self.evidence_references = merged

    def _apply(self, command, now, event_type, payload):
        previous_version = self.version
        self.version += 1
        self.updated_at = now
        event = self._event(command, event_type, now, payload)
        return EngineeringRelationshipCommandResult(
            relationship_id=self.id, previous_version=previous_version,
            version=self.version, command_type=type(command).__name__,
            correlation_id=command.metadata.correlation_id, events=(event,),
        )

    def _event(self, command, event_type, now, payload):
        return EngineeringRelationshipDomainEvent(
            event_id=uuid4(), event_type=event_type, schema_version=1,
            relationship_id=self.id, aggregate_version=self.version,
            occurred_at=now, actor_id=command.metadata.actor.actor_id,
            correlation_id=command.metadata.correlation_id,
            causation_id=command.metadata.command_id,
            organization_id=self.organization_id, project_id=self.project_id,
            workspace_id=self.workspace_id,
            relationship_family=RelationshipFamily(self.relationship_family),
            relationship_type=RelationshipType(self.relationship_type),
            payload=payload,
        )

    def submit_for_review(self, command, now):
        self._check_mutation(command)
        if self.authority_standing != EngineeringAuthorityStanding.DRAFT.value:
            raise EngineeringRelationshipTransitionRejected(
                "only draft authority may be submitted"
            )
        self._merge_evidence(command)
        if not self.evidence_references:
            raise EngineeringRelationshipTransitionRejected(
                "review submission requires Evidence"
            )
        self.authority_standing = EngineeringAuthorityStanding.PROPOSED.value
        return self._apply(command, now, "EngineeringRelationshipSubmitted", {})

    def review(self, command: ReviewEngineeringRelationship, now: datetime):
        self._check_mutation(command)
        if self.authority_standing not in {
            EngineeringAuthorityStanding.PROPOSED.value,
            EngineeringAuthorityStanding.DISPUTED.value,
        }:
            raise EngineeringRelationshipTransitionRejected(
                "relationship is not reviewable"
            )
        self._merge_evidence(command)
        if not self.evidence_references:
            raise EngineeringRelationshipTransitionRejected(
                "review requires Evidence"
            )
        self.reviewer_id = command.metadata.actor.actor_id
        self.authority_standing = EngineeringAuthorityStanding.REVIEWED.value
        return self._apply(command, now, "EngineeringRelationshipReviewed", {})

    def approve(self, command: ApproveEngineeringRelationship, now: datetime):
        self._check_mutation(command)
        actor_id = command.metadata.actor.actor_id
        if self.authority_standing != EngineeringAuthorityStanding.REVIEWED.value:
            raise EngineeringRelationshipTransitionRejected(
                "only reviewed authority may be approved"
            )
        if actor_id in {self.creator_id, self.reviewer_id}:
            raise EngineeringRelationshipTransitionRejected(
                "Approver must differ from Creator and Reviewer"
            )
        self.approver_id = actor_id
        self.authority_standing = EngineeringAuthorityStanding.APPROVED.value
        return self._apply(command, now, "EngineeringRelationshipApproved", {})

    def dispute(self, command: DisputeEngineeringRelationship, now: datetime):
        self._check_mutation(command)
        if self.authority_standing != EngineeringAuthorityStanding.APPROVED.value:
            raise EngineeringRelationshipTransitionRejected(
                "only approved authority may be disputed"
            )
        self.authority_standing = EngineeringAuthorityStanding.DISPUTED.value
        return self._apply(command, now, "EngineeringRelationshipDisputed", {})

    def reject(self, command: RejectEngineeringRelationship, now: datetime):
        self._check_mutation(command)
        if self.authority_standing not in {
            EngineeringAuthorityStanding.PROPOSED.value,
            EngineeringAuthorityStanding.REVIEWED.value,
            EngineeringAuthorityStanding.DISPUTED.value,
        }:
            raise EngineeringRelationshipTransitionRejected(
                "authority standing cannot be rejected"
            )
        self.authority_standing = EngineeringAuthorityStanding.REJECTED.value
        self.lifecycle = RelationshipLifecycle.REJECTED.value
        return self._apply(command, now, "EngineeringRelationshipRejected", {})

    def transition_lifecycle(
        self, command: TransitionEngineeringRelationshipLifecycle, now: datetime
    ):
        self._check_mutation(command)
        current = RelationshipLifecycle(self.lifecycle)
        target = RelationshipLifecycle(command.lifecycle)
        if target not in LIFECYCLE_TRANSITIONS[current]:
            raise EngineeringRelationshipTransitionRejected(
                f"transition from {current.value} to {target.value} is prohibited"
            )
        self._merge_evidence(command)
        if target is RelationshipLifecycle.CURRENT and (
            self.authority_standing != EngineeringAuthorityStanding.APPROVED.value
            or not self.evidence_references
        ):
            raise EngineeringRelationshipTransitionRejected(
                "current lifecycle requires approved authority and Evidence"
            )
        if target is RelationshipLifecycle.SUPERSEDED and (
            command.replacement_relationship_id is None
            or command.replacement_relationship_id == self.id
        ):
            raise EngineeringRelationshipTransitionRejected(
                "supersession requires a distinct replacement relationship"
            )
        self.lifecycle = target.value
        if target is RelationshipLifecycle.PROPOSED:
            self.authority_standing = EngineeringAuthorityStanding.DRAFT.value
            self.reviewer_id = None
            self.approver_id = None
        return self._apply(
            command, now, "EngineeringRelationshipLifecycleTransitioned",
            {"lifecycle": target.value},
        )

    def transfer_steward(
        self, command: TransferEngineeringRelationshipSteward, now: datetime
    ):
        self._check_mutation(command)
        if command.steward_id == self.steward_id:
            raise EngineeringRelationshipNoOp("Steward is unchanged")
        self.steward_id = command.steward_id
        return self._apply(
            command, now, "EngineeringRelationshipStewardTransferred",
            {"steward_id": command.steward_id},
        )

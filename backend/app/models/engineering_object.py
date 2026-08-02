from enum import StrEnum
from datetime import datetime
from uuid import UUID
from uuid import uuid4

from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType
from app.models.engineering_object_command import CreateEngineeringObject
from app.models.engineering_object_command import EngineeringObjectCommandResult
from app.models.engineering_object_command import EngineeringObjectDomainEvent
from app.models.engineering_object_command import EngineeringObjectNoOp
from app.models.engineering_object_command import EngineeringObjectTransitionRejected
from app.models.engineering_object_command import EngineeringObjectVersionMismatch
from app.models.engineering_object_command import MutationCommand
from app.models.engineering_object_command import ReclassifyEngineeringObject
from app.models.engineering_object_command import TransferEngineeringObjectSteward
from app.models.engineering_object_command import TransitionEngineeringObjectAuthority
from app.models.engineering_object_command import TransitionEngineeringObjectLifecycle


def _values(enum_type: type[StrEnum]) -> str:
    return ", ".join(f"'{item.value}'" for item in enum_type)


FAMILY_VALUES = _values(EngineeringObjectFamily)
DISCIPLINE_VALUES = _values(EngineeringDiscipline)
OBJECT_TYPE_VALUES = _values(EngineeringObjectType)
LIFECYCLE_VALUES = _values(EngineeringLifecycle)
AUTHORITY_VALUES = _values(EngineeringAuthorityStanding)

FAMILY_DISCIPLINE = {
    EngineeringObjectFamily.INSTRUMENTATION.value: (
        EngineeringDiscipline.INSTRUMENTATION.value
    ),
    EngineeringObjectFamily.ELECTRICAL.value: (
        EngineeringDiscipline.ELECTRICAL.value
    ),
    EngineeringObjectFamily.AUTOMATION.value: (
        EngineeringDiscipline.INDUSTRIAL_AUTOMATION.value
    ),
    EngineeringObjectFamily.SHARED.value: (
        EngineeringDiscipline.SHARED_ENGINEERING.value
    ),
}

FAMILY_OBJECT_TYPES = {
    EngineeringObjectFamily.INSTRUMENTATION.value: {
        EngineeringObjectType.INSTRUMENT.value,
        EngineeringObjectType.TRANSMITTER.value,
        EngineeringObjectType.ANALYZER.value,
        EngineeringObjectType.FLOWMETER.value,
        EngineeringObjectType.CONTROL_VALVE.value,
        EngineeringObjectType.INSTRUMENT_LOOP.value,
        EngineeringObjectType.JUNCTION_BOX.value,
        EngineeringObjectType.INSTRUMENT_PANEL.value,
    },
    EngineeringObjectFamily.ELECTRICAL.value: {
        EngineeringObjectType.MOTOR.value,
        EngineeringObjectType.TRANSFORMER.value,
        EngineeringObjectType.MCC.value,
        EngineeringObjectType.SWITCHGEAR.value,
        EngineeringObjectType.ELECTRICAL_PANEL.value,
        EngineeringObjectType.ELECTRICAL_CABLE.value,
    },
    EngineeringObjectFamily.AUTOMATION.value: {
        EngineeringObjectType.PLC.value,
        EngineeringObjectType.DCS_CONTROLLER.value,
        EngineeringObjectType.ESD_CONTROLLER.value,
        EngineeringObjectType.CONTROL_CABINET.value,
        EngineeringObjectType.IO_CHANNEL.value,
        EngineeringObjectType.HMI.value,
        EngineeringObjectType.CONTROL_LOGIC.value,
    },
    EngineeringObjectFamily.SHARED.value: {
        EngineeringObjectType.PROJECT.value,
        EngineeringObjectType.VENDOR.value,
        EngineeringObjectType.REQUIREMENT.value,
        EngineeringObjectType.STANDARD.value,
        EngineeringObjectType.DATASHEET.value,
        EngineeringObjectType.DRAWING.value,
        EngineeringObjectType.TECHNICAL_DECISION.value,
    },
}

LIFECYCLE_TRANSITIONS = {
    EngineeringLifecycle.PROPOSED: {
        EngineeringLifecycle.ACTIVE,
        EngineeringLifecycle.WITHDRAWN,
    },
    EngineeringLifecycle.ACTIVE: {
        EngineeringLifecycle.SUPERSEDED,
        EngineeringLifecycle.WITHDRAWN,
        EngineeringLifecycle.RETIRED,
    },
    EngineeringLifecycle.WITHDRAWN: {
        EngineeringLifecycle.PROPOSED,
    },
    EngineeringLifecycle.SUPERSEDED: {
        EngineeringLifecycle.RETIRED,
    },
    EngineeringLifecycle.RETIRED: set(),
}

AUTHORITY_TRANSITIONS = {
    EngineeringAuthorityStanding.DRAFT: {
        EngineeringAuthorityStanding.PROPOSED,
    },
    EngineeringAuthorityStanding.PROPOSED: {
        EngineeringAuthorityStanding.REVIEWED,
        EngineeringAuthorityStanding.DISPUTED,
        EngineeringAuthorityStanding.REJECTED,
    },
    EngineeringAuthorityStanding.REVIEWED: {
        EngineeringAuthorityStanding.APPROVED,
        EngineeringAuthorityStanding.PROPOSED,
        EngineeringAuthorityStanding.DISPUTED,
        EngineeringAuthorityStanding.REJECTED,
    },
    EngineeringAuthorityStanding.APPROVED: {
        EngineeringAuthorityStanding.PROPOSED,
        EngineeringAuthorityStanding.DISPUTED,
    },
    EngineeringAuthorityStanding.DISPUTED: {
        EngineeringAuthorityStanding.PROPOSED,
        EngineeringAuthorityStanding.REVIEWED,
        EngineeringAuthorityStanding.REJECTED,
    },
    EngineeringAuthorityStanding.REJECTED: {
        EngineeringAuthorityStanding.DRAFT,
    },
}


def _classification_constraint() -> str:
    clauses = []
    for family, object_types in FAMILY_OBJECT_TYPES.items():
        values = ", ".join(f"'{value}'" for value in sorted(object_types))
        clauses.append(
            f"(family = '{family}' AND object_type IN ({values}))"
        )
    return " OR ".join(clauses)


def _family_discipline_constraint() -> str:
    return " OR ".join(
        (
            f"(family = '{family}' AND discipline = '{discipline}')"
            for family, discipline in FAMILY_DISCIPLINE.items()
        )
    )


class EngineeringObject(Base):
    __tablename__ = "engineering_objects"
    __table_args__ = (
        CheckConstraint(
            f"family IN ({FAMILY_VALUES})",
            name="ck_engineering_objects_family",
        ),
        CheckConstraint(
            f"discipline IN ({DISCIPLINE_VALUES})",
            name="ck_engineering_objects_discipline",
        ),
        CheckConstraint(
            f"object_type IN ({OBJECT_TYPE_VALUES})",
            name="ck_engineering_objects_object_type",
        ),
        CheckConstraint(
            _family_discipline_constraint(),
            name="ck_engineering_objects_family_discipline",
        ),
        CheckConstraint(
            _classification_constraint(),
            name="ck_engineering_objects_family_object_type",
        ),
        CheckConstraint(
            "subtype IS NULL",
            name="ck_engineering_objects_subtype_v1",
        ),
        CheckConstraint(
            f"lifecycle IN ({LIFECYCLE_VALUES})",
            name="ck_engineering_objects_lifecycle",
        ),
        CheckConstraint(
            f"authority_standing IN ({AUTHORITY_VALUES})",
            name="ck_engineering_objects_authority_standing",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_engineering_objects_version",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_engineering_objects_timestamp_order",
        ),
        Index(
            "ix_engineering_objects_organization_project",
            "organization_id",
            "project_id",
        ),
        Index(
            "ix_engineering_objects_project_workspace",
            "project_id",
            "workspace_id",
        ),
        Index(
            "ix_engineering_objects_classification",
            "family",
            "discipline",
            "object_type",
        ),
        Index(
            "ix_engineering_objects_lifecycle_authority",
            "lifecycle",
            "authority_standing",
        ),
    )

    id = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
    )
    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            name="fk_engineering_objects_customer_id_customers",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    project_id = Column(
        Integer,
        ForeignKey(
            "projects.id",
            name="fk_engineering_objects_project_id_projects",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey(
            "engineering_workspaces.id",
            name=(
                "fk_engineering_objects_workspace_id_"
                "engineering_workspaces"
            ),
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    family = Column(String(32), nullable=False)
    discipline = Column(String(32), nullable=False)
    object_type = Column(String(64), nullable=False)
    subtype = Column(String(64), nullable=True)
    lifecycle = Column(
        String(16),
        nullable=False,
        default=EngineeringLifecycle.PROPOSED.value,
        server_default=EngineeringLifecycle.PROPOSED.value,
    )
    authority_standing = Column(
        String(16),
        nullable=False,
        default=EngineeringAuthorityStanding.DRAFT.value,
        server_default=EngineeringAuthorityStanding.DRAFT.value,
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    creator_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_objects_creator_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    steward_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_objects_steward_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    customer = relationship("Customer")
    project = relationship("Project")
    workspace = relationship("EngineeringWorkspace")
    creator = relationship("User", foreign_keys=[creator_id])
    steward = relationship("User", foreign_keys=[steward_id])

    def __init__(self, **values):
        values.setdefault("id", uuid4())
        values.setdefault(
            "lifecycle",
            EngineeringLifecycle.PROPOSED.value,
        )
        values.setdefault(
            "authority_standing",
            EngineeringAuthorityStanding.DRAFT.value,
        )
        values.setdefault("version", 1)
        super().__init__(**values)
        self._validate_required_state()
        self._validate_classification()

    @staticmethod
    def _enum_value(value: StrEnum | str) -> str:
        return value.value if isinstance(value, StrEnum) else value

    @validates(
        "family",
        "discipline",
        "object_type",
        "lifecycle",
        "authority_standing",
    )
    def _validate_controlled_value(self, key: str, value: StrEnum | str):
        normalized = self._enum_value(value)
        allowed = {
            "family": {item.value for item in EngineeringObjectFamily},
            "discipline": {
                item.value for item in EngineeringDiscipline
            },
            "object_type": {
                item.value for item in EngineeringObjectType
            },
            "lifecycle": {item.value for item in EngineeringLifecycle},
            "authority_standing": {
                item.value for item in EngineeringAuthorityStanding
            },
        }[key]
        if normalized not in allowed:
            raise ValueError(f"Invalid Engineering Object {key}")
        if (
            key in {"family", "discipline", "object_type"}
            and not getattr(
                self,
                "_classification_mutation_in_progress",
                False,
            )
        ):
            self._validate_classification_candidate(key, normalized)
        return normalized

    @validates("subtype")
    def _validate_subtype(self, _key: str, value: str | None):
        if value is not None:
            raise ValueError(
                "Blueprint v1.0 has no approved subtype vocabulary"
            )
        return None

    @validates("id", "creator_id", "created_at")
    def _validate_immutable(self, key: str, value):
        current = self.__dict__.get(key)
        if current is not None and current != value:
            raise ValueError(
                f"Engineering Object {key} is immutable"
            )
        if key == "id" and not isinstance(value, UUID):
            raise ValueError("Engineering Object id must be a UUID")
        if key == "creator_id":
            self._validate_positive_reference(key, value)
        return value

    @validates("organization_id")
    def _validate_organization_id(self, _key: str, value):
        if not isinstance(value, UUID):
            raise ValueError(
                "Engineering Object organization_id must be a UUID"
            )
        return value

    @validates("customer_id")
    def _validate_customer_id(self, key: str, value: int | None):
        if value is not None:
            self._validate_positive_reference(key, value)
        return value

    @validates("version")
    def _validate_version(self, _key: str, value: int):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                "Engineering Object version must be a positive integer"
            )
        return value

    @validates("project_id", "workspace_id", "steward_id")
    def _validate_required_reference(self, key: str, value: int):
        self._validate_positive_reference(key, value)
        return value

    @staticmethod
    def _validate_positive_reference(key: str, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                f"Engineering Object {key} must be a positive integer"
            )

    def _validate_required_state(self) -> None:
        required = (
            "id",
            "organization_id",
            "project_id",
            "workspace_id",
            "family",
            "discipline",
            "object_type",
            "lifecycle",
            "authority_standing",
            "version",
            "creator_id",
            "steward_id",
        )
        missing = [
            key for key in required if getattr(self, key, None) is None
        ]
        if missing:
            raise ValueError(
                "Engineering Object is missing required state: "
                + ", ".join(missing)
            )

    def _validate_classification(self) -> None:
        values = {
            key: getattr(self, key, None)
            for key in ("family", "discipline", "object_type")
        }
        self._validate_classification_values(values)

    def _validate_classification_candidate(
        self,
        key: str,
        value: str,
    ) -> None:
        values = {
            name: getattr(self, name, None)
            for name in ("family", "discipline", "object_type")
        }
        values[key] = value
        self._validate_classification_values(values)

    @staticmethod
    def _validate_classification_values(values: dict[str, str | None]):
        if any(value is None for value in values.values()):
            return
        expected_discipline = FAMILY_DISCIPLINE[values["family"]]
        if values["discipline"] != expected_discipline:
            raise ValueError(
                "Engineering Object family and discipline are incompatible"
            )
        if values["object_type"] not in FAMILY_OBJECT_TYPES[
            values["family"]
        ]:
            raise ValueError(
                "Engineering Object family and object_type are incompatible"
            )

    @classmethod
    def create(
        cls,
        command: CreateEngineeringObject,
        occurred_at: datetime,
    ) -> tuple["EngineeringObject", EngineeringObjectCommandResult]:
        """Establish one complete aggregate in its approved initial state."""

        cls._validate_command_time(occurred_at)
        if command.organization_id != command.metadata.actor.organization_id:
            raise ValueError(
                "organization_id must match the authenticated actor scope"
            )
        if command.creator_id != command.metadata.actor.actor_id:
            raise ValueError(
                "creator_id must match the authenticated actor"
            )
        engineering_object = cls(
            organization_id=command.organization_id,
            customer_id=command.customer_id,
            project_id=command.project_id,
            workspace_id=command.workspace_id,
            family=command.family,
            discipline=command.discipline,
            object_type=command.object_type,
            subtype=None,
            lifecycle=EngineeringLifecycle.PROPOSED,
            authority_standing=EngineeringAuthorityStanding.DRAFT,
            version=1,
            creator_id=command.creator_id,
            steward_id=command.steward_id,
            created_at=occurred_at,
            updated_at=occurred_at,
        )
        event = engineering_object._event(
            command.metadata,
            "EngineeringObjectCreated",
            occurred_at,
            {
                "family": engineering_object.family,
                "discipline": engineering_object.discipline,
                "object_type": engineering_object.object_type,
                "lifecycle": engineering_object.lifecycle,
                "authority_standing": (
                    engineering_object.authority_standing
                ),
                "creator_id": engineering_object.creator_id,
                "steward_id": engineering_object.steward_id,
            },
        )
        return engineering_object, engineering_object._result(
            "CreateEngineeringObject",
            command.metadata.correlation_id,
            previous_version=None,
            events=(event,),
        )

    def reclassify(
        self,
        command: ReclassifyEngineeringObject,
        occurred_at: datetime,
    ) -> EngineeringObjectCommandResult:
        """Apply a complete valid classification and reassess authority."""

        previous_version = self._prepare_mutation(command, occurred_at)
        target = {
            "family": command.family.value,
            "discipline": command.discipline.value,
            "object_type": command.object_type.value,
        }
        self._validate_classification_values(target)
        previous = {
            "family": self.family,
            "discipline": self.discipline,
            "object_type": self.object_type,
        }
        if previous == target:
            raise EngineeringObjectNoOp(
                "Reclassification must change the complete classification"
            )

        prior_authority = self.authority_standing
        self._classification_mutation_in_progress = True
        try:
            self.family = target["family"]
            self.discipline = target["discipline"]
            self.object_type = target["object_type"]
        finally:
            self._classification_mutation_in_progress = False
        self._validate_classification()
        if prior_authority in {
            EngineeringAuthorityStanding.REVIEWED.value,
            EngineeringAuthorityStanding.APPROVED.value,
        }:
            self.authority_standing = EngineeringAuthorityStanding.PROPOSED

        self._complete_mutation(previous_version, occurred_at)
        events = [
            self._event(
                command.metadata,
                "EngineeringObjectReclassified",
                occurred_at,
                {
                    **target,
                    "previous_family": previous["family"],
                    "previous_discipline": previous["discipline"],
                    "previous_object_type": previous["object_type"],
                },
            )
        ]
        if self.authority_standing != prior_authority:
            events.append(
                self._event(
                    command.metadata,
                    "EngineeringObjectAuthorityTransitioned",
                    occurred_at,
                    {
                        "previous_authority_standing": prior_authority,
                        "authority_standing": self.authority_standing,
                        "reason": "material_reclassification",
                    },
                )
            )
        return self._result(
            "ReclassifyEngineeringObject",
            command.metadata.correlation_id,
            previous_version,
            tuple(events),
        )

    def transition_lifecycle(
        self,
        command: TransitionEngineeringObjectLifecycle,
        occurred_at: datetime,
    ) -> EngineeringObjectCommandResult:
        """Apply exactly one Blueprint-approved lifecycle transition."""

        previous_version = self._prepare_mutation(command, occurred_at)
        current = EngineeringLifecycle(self.lifecycle)
        target = command.lifecycle
        if target not in LIFECYCLE_TRANSITIONS[current]:
            raise EngineeringObjectTransitionRejected(
                f"Lifecycle transition {current.value} -> {target.value} "
                "is prohibited"
            )
        if target is EngineeringLifecycle.SUPERSEDED:
            if command.replacement_object_id is None:
                raise EngineeringObjectTransitionRejected(
                    "Supersession requires a replacement Engineering Object"
                )
            if command.replacement_object_id == self.id:
                raise EngineeringObjectTransitionRejected(
                    "An Engineering Object cannot supersede itself"
                )
        elif command.replacement_object_id is not None:
            raise EngineeringObjectTransitionRejected(
                "replacement_object_id is valid only for supersession"
            )

        self.lifecycle = target
        self._complete_mutation(previous_version, occurred_at)
        event = self._event(
            command.metadata,
            "EngineeringObjectLifecycleTransitioned",
            occurred_at,
            {
                "previous_lifecycle": current.value,
                "lifecycle": target.value,
                "replacement_object_id": command.replacement_object_id,
            },
        )
        return self._result(
            "TransitionEngineeringObjectLifecycle",
            command.metadata.correlation_id,
            previous_version,
            (event,),
        )

    def transition_authority(
        self,
        command: TransitionEngineeringObjectAuthority,
        occurred_at: datetime,
    ) -> EngineeringObjectCommandResult:
        """Apply exactly one Blueprint-approved authority transition."""

        previous_version = self._prepare_mutation(command, occurred_at)
        current = EngineeringAuthorityStanding(self.authority_standing)
        target = command.authority_standing
        if target not in AUTHORITY_TRANSITIONS[current]:
            raise EngineeringObjectTransitionRejected(
                f"Authority transition {current.value} -> {target.value} "
                "is prohibited"
            )
        self.authority_standing = target
        self._complete_mutation(previous_version, occurred_at)
        event = self._event(
            command.metadata,
            "EngineeringObjectAuthorityTransitioned",
            occurred_at,
            {
                "previous_authority_standing": current.value,
                "authority_standing": target.value,
            },
        )
        return self._result(
            "TransitionEngineeringObjectAuthority",
            command.metadata.correlation_id,
            previous_version,
            (event,),
        )

    def transfer_steward(
        self,
        command: TransferEngineeringObjectSteward,
        occurred_at: datetime,
    ) -> EngineeringObjectCommandResult:
        """Transfer stewardship without changing any unrelated state."""

        previous_version = self._prepare_mutation(command, occurred_at)
        if command.steward_id == self.steward_id:
            raise EngineeringObjectNoOp(
                "Steward transfer must select a different Human"
            )
        previous_steward_id = self.steward_id
        self.steward_id = command.steward_id
        self._complete_mutation(previous_version, occurred_at)
        event = self._event(
            command.metadata,
            "EngineeringObjectStewardTransferred",
            occurred_at,
            {
                "previous_steward_id": previous_steward_id,
                "steward_id": self.steward_id,
            },
        )
        return self._result(
            "TransferEngineeringObjectSteward",
            command.metadata.correlation_id,
            previous_version,
            (event,),
        )

    def _prepare_mutation(
        self,
        command: MutationCommand,
        occurred_at: datetime,
    ) -> int:
        """Validate aggregate identity, version, and controlled time."""

        self._validate_command_time(occurred_at)
        if command.object_id != self.id:
            raise ValueError("Command target does not match aggregate identity")
        if command.expected_version != self.version:
            raise EngineeringObjectVersionMismatch(
                "Engineering Object expected version is stale"
            )
        if occurred_at < self.updated_at:
            raise ValueError("Command time cannot precede updated_at")
        return self.version

    def _complete_mutation(
        self,
        previous_version: int,
        occurred_at: datetime,
    ) -> None:
        """Advance version and modification time once after accepted change."""

        self.version = previous_version + 1
        self.updated_at = occurred_at
        self._validate_required_state()
        self._validate_classification()

    @staticmethod
    def _validate_command_time(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Command time must be timezone-aware")

    def _event(
        self,
        metadata,
        event_type: str,
        occurred_at: datetime,
        payload: dict,
    ) -> EngineeringObjectDomainEvent:
        """Build the immutable Blueprint event envelope for current state."""

        return EngineeringObjectDomainEvent(
            event_id=uuid4(),
            event_type=event_type,
            schema_version=1,
            object_id=self.id,
            aggregate_version=self.version,
            occurred_at=occurred_at,
            actor_id=metadata.actor.actor_id,
            correlation_id=metadata.correlation_id,
            causation_id=metadata.command_id,
            organization_id=self.organization_id,
            project_id=self.project_id,
            workspace_id=self.workspace_id,
            payload=payload,
        )

    def _result(
        self,
        command_type: str,
        correlation_id: UUID,
        previous_version: int | None,
        events: tuple[EngineeringObjectDomainEvent, ...],
    ) -> EngineeringObjectCommandResult:
        """Build a bounded result without exposing uncommitted internals."""

        return EngineeringObjectCommandResult(
            object_id=self.id,
            previous_version=previous_version,
            version=self.version,
            command_type=command_type,
            correlation_id=correlation_id,
            events=events,
        )

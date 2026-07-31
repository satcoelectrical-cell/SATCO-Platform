from enum import StrEnum
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
        if key in {"family", "discipline", "object_type"}:
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

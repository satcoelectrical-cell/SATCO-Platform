from datetime import UTC
from datetime import datetime
from uuid import UUID
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import configure_mappers

from app.core.database import Base
from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType
from app.models import EngineeringObject


EXPECTED_COLUMNS = {
    "id",
    "organization_id",
    "customer_id",
    "project_id",
    "workspace_id",
    "family",
    "discipline",
    "object_type",
    "subtype",
    "lifecycle",
    "authority_standing",
    "version",
    "creator_id",
    "steward_id",
    "created_at",
    "updated_at",
}

REQUIRED_COLUMNS = EXPECTED_COLUMNS - {"customer_id", "subtype"}

EXPECTED_CHECKS = {
    "ck_engineering_objects_family",
    "ck_engineering_objects_discipline",
    "ck_engineering_objects_object_type",
    "ck_engineering_objects_family_discipline",
    "ck_engineering_objects_family_object_type",
    "ck_engineering_objects_subtype_v1",
    "ck_engineering_objects_lifecycle",
    "ck_engineering_objects_authority_standing",
    "ck_engineering_objects_version",
    "ck_engineering_objects_timestamp_order",
}

EXPECTED_INDEXES = {
    "ix_engineering_objects_organization_project",
    "ix_engineering_objects_project_workspace",
    "ix_engineering_objects_classification",
    "ix_engineering_objects_lifecycle_authority",
}

EXPECTED_FOREIGN_KEYS = {
    "customer_id": (
        "customers.id",
        "fk_engineering_objects_customer_id_customers",
    ),
    "project_id": (
        "projects.id",
        "fk_engineering_objects_project_id_projects",
    ),
    "workspace_id": (
        "engineering_workspaces.id",
        (
            "fk_engineering_objects_workspace_id_"
            "engineering_workspaces"
        ),
    ),
    "creator_id": (
        "users.id",
        "fk_engineering_objects_creator_id_users",
    ),
    "steward_id": (
        "users.id",
        "fk_engineering_objects_steward_id_users",
    ),
}


def _object(**overrides):
    values = {
        "organization_id": uuid4(),
        "customer_id": 1,
        "project_id": 2,
        "workspace_id": 3,
        "family": EngineeringObjectFamily.ELECTRICAL,
        "discipline": EngineeringDiscipline.ELECTRICAL,
        "object_type": EngineeringObjectType.MOTOR,
        "creator_id": 4,
        "steward_id": 5,
    }
    values.update(overrides)
    return EngineeringObject(**values)


def test_engineering_object_model_is_registered():
    assert EngineeringObject.__tablename__ == "engineering_objects"
    assert Base.metadata.tables["engineering_objects"] is (
        EngineeringObject.__table__
    )


def test_engineering_object_columns_match_approved_contract():
    columns = EngineeringObject.__table__.columns

    assert set(columns.keys()) == EXPECTED_COLUMNS
    assert all(not columns[name].nullable for name in REQUIRED_COLUMNS)
    assert columns.customer_id.nullable is True
    assert columns.subtype.nullable is True
    assert columns.id.primary_key is True
    assert isinstance(columns.id.type, PostgreSQLUUID)
    assert columns.id.type.as_uuid is True
    assert isinstance(columns.organization_id.type, PostgreSQLUUID)
    assert columns.organization_id.type.as_uuid is True
    for name in (
        "customer_id",
        "project_id",
        "workspace_id",
        "creator_id",
        "steward_id",
        "version",
    ):
        assert isinstance(columns[name].type, Integer)
    assert columns.created_at.type.timezone is True
    assert columns.updated_at.type.timezone is True


def test_engineering_object_foreign_keys_are_restrictive():
    columns = EngineeringObject.__table__.columns

    assert not columns.organization_id.foreign_keys
    for column_name, (target, constraint_name) in (
        EXPECTED_FOREIGN_KEYS.items()
    ):
        foreign_key = next(iter(columns[column_name].foreign_keys))
        assert foreign_key.target_fullname == target
        assert foreign_key.constraint.name == constraint_name
        assert foreign_key.ondelete == "RESTRICT"


def test_engineering_object_mapper_relationships_are_unambiguous():
    configure_mappers()
    relationships = EngineeringObject.__mapper__.relationships

    assert relationships.creator.mapper.class_.__name__ == "User"
    assert relationships.creator.local_columns == {
        EngineeringObject.__table__.columns.creator_id
    }
    assert relationships.steward.mapper.class_.__name__ == "User"
    assert relationships.steward.local_columns == {
        EngineeringObject.__table__.columns.steward_id
    }


def test_engineering_object_constraints_and_indexes_are_declared():
    table = EngineeringObject.__table__
    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert check_names == EXPECTED_CHECKS
    assert {index.name for index in table.indexes} == EXPECTED_INDEXES


def test_engineering_object_defaults_are_governed():
    columns = EngineeringObject.__table__.columns
    record = _object()

    assert isinstance(record.id, UUID)
    assert record.lifecycle == "proposed"
    assert record.authority_standing == "draft"
    assert record.version == 1
    assert columns.lifecycle.default.arg == "proposed"
    assert str(columns.lifecycle.server_default.arg) == "proposed"
    assert columns.authority_standing.default.arg == "draft"
    assert str(columns.authority_standing.server_default.arg) == "draft"
    assert columns.version.default.arg == 1
    assert str(columns.version.server_default.arg) == "1"
    assert columns.created_at.server_default is not None
    assert columns.updated_at.server_default is not None
    assert columns.updated_at.onupdate is not None


@pytest.mark.parametrize(
    ("family", "discipline", "object_type"),
    [
        (
            EngineeringObjectFamily.INSTRUMENTATION,
            EngineeringDiscipline.INSTRUMENTATION,
            EngineeringObjectType.TRANSMITTER,
        ),
        (
            EngineeringObjectFamily.ELECTRICAL,
            EngineeringDiscipline.ELECTRICAL,
            EngineeringObjectType.MOTOR,
        ),
        (
            EngineeringObjectFamily.AUTOMATION,
            EngineeringDiscipline.INDUSTRIAL_AUTOMATION,
            EngineeringObjectType.PLC,
        ),
        (
            EngineeringObjectFamily.SHARED,
            EngineeringDiscipline.SHARED_ENGINEERING,
            EngineeringObjectType.TECHNICAL_DECISION,
        ),
    ],
)
def test_approved_classifications_are_accepted(
    family,
    discipline,
    object_type,
):
    record = _object(
        family=family,
        discipline=discipline,
        object_type=object_type,
    )

    assert record.family == family.value
    assert record.discipline == discipline.value
    assert record.object_type == object_type.value


@pytest.mark.parametrize(
    "overrides",
    [
        {"family": "mechanical"},
        {"discipline": "process"},
        {"object_type": "pump"},
        {
            "family": EngineeringObjectFamily.ELECTRICAL,
            "discipline": EngineeringDiscipline.INSTRUMENTATION,
        },
        {
            "family": EngineeringObjectFamily.ELECTRICAL,
            "object_type": EngineeringObjectType.TRANSMITTER,
        },
        {"subtype": "custom"},
        {"lifecycle": "identified"},
        {"authority_standing": "ai_approved"},
        {"version": 0},
        {"version": True},
        {"id": "not-a-uuid"},
        {"organization_id": "not-a-uuid"},
        {"customer_id": 0},
        {"customer_id": -1},
        {"customer_id": True},
        {"customer_id": "1"},
        {"project_id": None},
        {"workspace_id": None},
        {"creator_id": None},
        {"steward_id": None},
    ],
    ids=[
        "future-family",
        "future-discipline",
        "unapproved-type",
        "family-discipline-mismatch",
        "family-type-mismatch",
        "unapproved-subtype",
        "invalid-lifecycle",
        "invalid-authority",
        "non-positive-version",
        "boolean-version",
        "invalid-identity",
        "invalid-organization-identity",
        "zero-customer",
        "negative-customer",
        "boolean-customer",
        "string-customer",
        "missing-project",
        "missing-workspace",
        "missing-creator",
        "missing-steward",
    ],
)
def test_invalid_engineering_object_state_is_rejected(overrides):
    with pytest.raises(ValueError):
        _object(**overrides)


def test_customer_id_may_be_absent():
    record = _object(customer_id=None)

    assert record.customer_id is None


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("discipline", EngineeringDiscipline.INSTRUMENTATION),
        ("family", EngineeringObjectFamily.INSTRUMENTATION),
    ],
    ids=[
        "discipline-mismatch",
        "family-mismatch",
    ],
)
def test_post_construction_family_discipline_mismatch_is_rejected(
    attribute,
    value,
):
    record = _object()

    with pytest.raises(ValueError):
        setattr(record, attribute, value)

    assert record.family == EngineeringObjectFamily.ELECTRICAL.value
    assert record.discipline == EngineeringDiscipline.ELECTRICAL.value


def test_post_construction_family_object_type_mismatch_is_rejected():
    record = _object()

    with pytest.raises(ValueError):
        record.object_type = EngineeringObjectType.TRANSMITTER

    assert record.family == EngineeringObjectFamily.ELECTRICAL.value
    assert record.object_type == EngineeringObjectType.MOTOR.value


def test_identity_creator_and_creation_time_are_immutable():
    created_at = datetime.now(UTC)
    record = _object(created_at=created_at)

    with pytest.raises(ValueError):
        record.id = uuid4()
    with pytest.raises(ValueError):
        record.creator_id = record.creator_id + 1
    with pytest.raises(ValueError):
        record.created_at = datetime.now(UTC)


def test_model_introduces_no_adjacent_ekg_tables():
    prohibited = {
        "engineering_object_identifiers",
        "engineering_object_relationships",
        "engineering_object_events",
    }

    assert prohibited.isdisjoint(Base.metadata.tables)

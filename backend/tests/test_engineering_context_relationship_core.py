import pytest

from app.enums import ContextRelationshipMeaning
from app.enums import RelationshipEndpointKind
from app.enums import RelationshipLifecycle
from app.exceptions.engineering_context_relationship import (
    DuplicateRelationship,
)
from app.exceptions.engineering_context_relationship import (
    RelationshipLifecycleConflict,
)
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
)
from app.services.engineering_context_relationship_service import (
    EngineeringContextRelationshipService,
)


def test_relationship_taxonomy_is_finite():
    assert {item.value for item in ContextRelationshipMeaning} == {
        "requires",
        "provided_by",
        "consumed_by",
        "potentially_affects",
    }
    assert {item.value for item in RelationshipEndpointKind} == {
        "context",
        "project",
        "workspace",
        "discipline",
        "external_source",
    }
    assert {item.value for item in RelationshipLifecycle} == {
        "current",
        "withdrawn",
    }


def test_relationship_model_has_stable_identity_and_no_delete_api():
    columns = EngineeringContextRelationship.__table__.columns
    assert columns.relationship_key.nullable is False
    assert columns.version.nullable is False
    assert not hasattr(
        EngineeringContextRelationshipService,
        "delete_relationship",
    )


def test_duplicate_and_self_transition_are_controlled():
    assert DuplicateRelationship().status_code == 409
    conflict = RelationshipLifecycleConflict("current", "current")
    assert conflict.status_code == 409


@pytest.mark.parametrize(
    "value",
    ["depends_on", "related_to", "custom", ""],
)
def test_arbitrary_relationship_meaning_is_rejected(value):
    with pytest.raises(ValueError):
        ContextRelationshipMeaning(value)

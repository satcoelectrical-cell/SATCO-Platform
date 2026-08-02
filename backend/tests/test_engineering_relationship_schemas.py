"""PATCH-026 Sprint-1 strict schema tests."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.engineering_relationship import (
    EngineeringRelationshipCreate,
    EngineeringRelationshipFilter,
    EngineeringRelationshipPagination,
    EngineeringRelationshipTraversal,
    TransferEngineeringRelationshipStewardRequest,
    TransitionEngineeringRelationshipLifecycleRequest,
)


def create_payload(**overrides):
    values = {
        "source_object_id": str(uuid4()),
        "target_object_id": str(uuid4()),
        "relationship_family": "instrumentation",
        "relationship_type": "monitored_by",
        "rationale": "  Approved monitoring relationship  ",
    }
    values.update(overrides)
    return values


def test_create_requires_explicit_family_and_type() -> None:
    schema = EngineeringRelationshipCreate.model_validate(create_payload())
    assert schema.relationship_family.value == "instrumentation"
    assert schema.relationship_type.value == "monitored_by"
    assert schema.rationale == "Approved monitoring relationship"

    for field in ("relationship_family", "relationship_type"):
        payload = create_payload()
        payload.pop(field)
        with pytest.raises(ValidationError):
            EngineeringRelationshipCreate.model_validate(payload)


def test_monitored_by_family_semantics_are_unambiguous() -> None:
    EngineeringRelationshipCreate.model_validate(
        create_payload(relationship_family="automation")
    )
    with pytest.raises(ValidationError):
        EngineeringRelationshipCreate.model_validate(
            create_payload(relationship_family="electrical")
        )


def test_create_rejects_self_link_and_trusted_fields() -> None:
    object_id = str(uuid4())
    with pytest.raises(ValidationError):
        EngineeringRelationshipCreate.model_validate(
            create_payload(
                source_object_id=object_id,
                target_object_id=object_id,
            )
        )
    with pytest.raises(ValidationError):
        EngineeringRelationshipCreate.model_validate(
            create_payload(organization_id=str(uuid4()))
        )
    with pytest.raises(ValidationError):
        EngineeringRelationshipCreate.model_validate(
            create_payload(confidentiality="project")
        )


def test_mutation_requires_pair_and_positive_expected_version() -> None:
    payload = {
        "relationship_family": "electrical",
        "relationship_type": "powered_by",
        "steward_id": 9,
        "expected_version": 1,
        "rationale": "Transfer accountable stewardship",
    }
    schema = TransferEngineeringRelationshipStewardRequest.model_validate(payload)
    assert schema.expected_version == 1

    with pytest.raises(ValidationError):
        TransferEngineeringRelationshipStewardRequest.model_validate(
            {**payload, "expected_version": 0}
        )
    with pytest.raises(ValidationError):
        TransferEngineeringRelationshipStewardRequest.model_validate(
            {key: value for key, value in payload.items() if key != "relationship_family"}
        )


def test_supersession_requires_replacement_only_for_superseded() -> None:
    base = {
        "relationship_family": "dependency",
        "relationship_type": "supersedes",
        "expected_version": 2,
        "rationale": "Superseded by approved replacement",
    }
    with pytest.raises(ValidationError):
        TransitionEngineeringRelationshipLifecycleRequest.model_validate(
            {**base, "lifecycle": "superseded"}
        )
    with pytest.raises(ValidationError):
        TransitionEngineeringRelationshipLifecycleRequest.model_validate(
            {
                **base,
                "lifecycle": "withdrawn",
                "replacement_relationship_id": str(uuid4()),
            }
        )


def test_filters_and_traversal_are_pair_aware_and_bounded() -> None:
    with pytest.raises(ValidationError):
        EngineeringRelationshipFilter(relationship_type="monitored_by")
    assert EngineeringRelationshipPagination().model_dump() == {
        "page": 1, "size": 20,
    }
    with pytest.raises(ValidationError):
        EngineeringRelationshipTraversal(max_depth=6)
    with pytest.raises(ValidationError):
        EngineeringRelationshipTraversal(max_results=101)

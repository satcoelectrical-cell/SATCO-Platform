"""Sprint-1 tests for strict EngineeringObject Pydantic contracts."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.engineering_object import EngineeringObjectCreate
from app.schemas.engineering_object import EngineeringObjectPagination
from app.schemas.engineering_object import ReclassifyEngineeringObjectRequest
from app.schemas.engineering_object import TransferEngineeringObjectStewardRequest


def test_create_accepts_only_client_managed_values() -> None:
    schema = EngineeringObjectCreate.model_validate(
        {
            "project_id": 3,
            "family": "electrical",
            "discipline": "electrical",
            "object_type": "motor",
            "rationale": "  Required for the approved motor scope  ",
        }
    )

    assert schema.rationale == "Required for the approved motor scope"
    assert "expected_version" not in schema.model_fields_set

    with pytest.raises(ValidationError):
        EngineeringObjectCreate.model_validate(
            {
                **schema.model_dump(mode="json"),
                "organization_id": str(uuid4()),
            }
        )


def test_post_creation_command_requires_positive_version() -> None:
    with pytest.raises(ValidationError):
        TransferEngineeringObjectStewardRequest.model_validate(
            {
                "steward_id": 9,
                "expected_version": 0,
                "rationale": "Transfer responsibility",
            }
        )


def test_reclassification_requires_complete_enum_classification() -> None:
    schema = ReclassifyEngineeringObjectRequest.model_validate(
        {
            "family": "automation",
            "discipline": "industrial_automation",
            "object_type": "plc",
            "expected_version": 4,
            "rationale": "Approved material reclassification",
            "evidence_references": [str(uuid4())],
        }
    )

    assert schema.expected_version == 4
    assert schema.object_type.value == "plc"


def test_evidence_references_must_be_unique() -> None:
    evidence_id = uuid4()
    with pytest.raises(ValidationError):
        ReclassifyEngineeringObjectRequest.model_validate(
            {
                "family": "automation",
                "discipline": "industrial_automation",
                "object_type": "plc",
                "expected_version": 4,
                "rationale": "Approved material reclassification",
                "evidence_references": [evidence_id, evidence_id],
            }
        )


def test_pagination_uses_standard_bounds() -> None:
    assert EngineeringObjectPagination().model_dump() == {
        "page": 1,
        "size": 20,
    }
    with pytest.raises(ValidationError):
        EngineeringObjectPagination(page=1, size=101)


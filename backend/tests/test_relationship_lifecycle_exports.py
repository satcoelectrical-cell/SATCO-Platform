from app.enums import EngineeringContextRelationshipLifecycle
from app.enums import EngineeringRelationshipLifecycle
from app.enums import RelationshipLifecycle


def test_relationship_lifecycle_exports_are_domain_qualified():
    assert RelationshipLifecycle is EngineeringContextRelationshipLifecycle
    assert {item.value for item in EngineeringContextRelationshipLifecycle} == {
        "current", "withdrawn",
    }
    assert {item.value for item in EngineeringRelationshipLifecycle} == {
        "proposed", "current", "superseded", "withdrawn", "rejected",
    }
    assert EngineeringContextRelationshipLifecycle is not EngineeringRelationshipLifecycle

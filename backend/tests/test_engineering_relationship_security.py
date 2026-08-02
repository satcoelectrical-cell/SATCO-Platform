from pathlib import Path


def test_derived_visibility_is_an_intersection_and_not_persisted():
    policy = Path("app/repositories/engineering_relationship_unit_of_work.py").read_text()
    model = Path("app/models/engineering_relationship.py").read_text()
    migration = Path("migrations/versions/e02600000001_engineering_relationship_engine.py").read_text()
    assert "source_object_id" in policy and "target_object_id" in policy
    assert "Evidence" in policy and "_workspace_access" in policy
    assert "return False" in policy
    assert "confidentiality = Column" not in model
    assert 'sa.Column("confidentiality"' not in migration


def test_authorization_precedes_relationship_disclosure_in_service():
    source = Path("app/services/engineering_relationship_service.py").read_text()
    get_method = source[source.index("    def get("):source.index("    def list_for_endpoint(")]
    assert get_method.index("authorization.authorize") < get_method.index("return _response")
    assert "EngineeringRelationshipProtectedNotFound" in get_method

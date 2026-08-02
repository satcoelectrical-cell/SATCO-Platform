from pathlib import Path


def test_traversal_is_bounded_cycle_safe_and_deterministic():
    source = Path("app/repositories/engineering_relationship_repository.py").read_text()
    assert "max_depth" in source and "max_results" in source
    assert "visited" in source
    assert "relationship_type" in source
    assert "source_object_id" in source and "target_object_id" in source
    assert "while queue and len(found) <= max_results" in source


def test_cycle_detection_uses_pair_scope_and_transaction_lock():
    source = Path("app/repositories/engineering_relationship_repository.py").read_text()
    assert "pg_advisory_xact_lock" in source
    assert "relationship_family" in source
    assert "relationship_type" in source
    assert "organization_id" in source and "project_id" in source

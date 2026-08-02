from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from app.repositories.engineering_relationship_repository import (
    SqlAlchemyEngineeringRelationshipRepository,
)


def test_repository_has_required_contract_without_forbidden_ownership():
    source = Path("app/repositories/engineering_relationship_repository.py").read_text()
    for method in (
        "get_authorized", "add", "persist_expected_version",
        "active_duplicate_exists", "creates_cycle", "list_for_endpoint",
        "bounded_neighborhood", "bounded_path",
    ):
        assert f"def {method}" in source
    assert ".commit(" not in source
    assert "authorize(" not in source
    assert ".delete(" not in source


def test_expected_version_write_reports_compare_and_change_result():
    session = MagicMock()
    session.execute.return_value.rowcount = 0
    repository = SqlAlchemyEngineeringRelationshipRepository(session)
    relationship = MagicMock(
        id=uuid4(), organization_id=uuid4(), lifecycle="current",
        authority_standing="approved", evidence_references=[], version=2,
        steward_id=1, reviewer_id=2, approver_id=3, updated_at=None,
    )
    assert repository.persist_expected_version(relationship, 1) is False
    session.flush.assert_called_once()

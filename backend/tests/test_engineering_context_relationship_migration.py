from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
)
from app.models.engineering_context_relationship import InterfaceCommitment


MIGRATION = (
    Path(__file__).parents[1]
    / "migrations"
    / "versions"
    / "b2022c0202f2_create_context_relationships_and_commitments.py"
)


def test_migration_is_single_additive_revision_from_approved_base():
    text = MIGRATION.read_text()
    assert 'revision: str = "b2022c0202f2"' in text
    assert 'down_revision: str | None = "c2021f0c0a01"' in text
    assert "op.create_table(" in text
    assert "op.alter_column(" not in text
    assert "UPDATE engineering_context" not in text


def test_models_register_only_patch_owned_tables():
    assert (
        EngineeringContextRelationship.__tablename__
        == "engineering_context_relationships"
    )
    assert InterfaceCommitment.__tablename__ == "interface_commitments"


def test_native_references_are_restrictive():
    text = MIGRATION.read_text()
    assert text.count('ondelete="RESTRICT"') >= 10
    assert "backfill" not in text.lower()


def test_database_contract_includes_scope_and_fulfilment_protection():
    inspector = inspect(engine)
    relationship_checks = {
        item["name"]
        for item in inspector.get_check_constraints(
            "engineering_context_relationships"
        )
    }
    commitment_checks = {
        item["name"]
        for item in inspector.get_check_constraints(
            "interface_commitments"
        )
    }
    assert "ck_context_relationships_no_self_reference" in relationship_checks
    assert {
        "ck_interface_commitments_fulfilment",
        "ck_interface_commitments_review_evidence",
        "ck_interface_commitments_required_contract",
        "ck_interface_commitments_distinct_workspaces",
    } <= commitment_checks
    with engine.connect() as connection:
        triggers = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE NOT tgisinternal AND tgrelid IN "
                    "('engineering_context_relationships'::regclass, "
                    "'interface_commitments'::regclass)"
                )
            )
        }
    assert {
        "trg_context_relationship_scope",
        "trg_interface_commitment_scope",
    } <= triggers


def test_direct_postgresql_rejects_cross_project_scope(
    relationship_domain,
):
    domain = relationship_domain
    values = {
        "relationship_key": "direct-cross-project",
        "project_id": domain["project"].id,
        "meaning": "requires",
        "purpose": "Invalid direct scope",
        "source_role": "provider",
        "target_role": "consumer",
        "source_kind": "workspace",
        "source_workspace_id": domain["provider_workspace"].id,
        "target_kind": "workspace",
        "target_workspace_id": domain["other_workspace"].id,
        "steward_id": domain["actors"]["steward"].id,
        "created_by_id": domain["actors"]["project_owner"].id,
        "lifecycle": "current",
        "version": 1,
    }
    with pytest.raises(IntegrityError):
        with domain["service"].db.begin_nested():
            domain["service"].db.add(
                EngineeringContextRelationship(**values)
            )
            domain["service"].db.flush()


def test_direct_postgresql_rejects_required_review_without_evidence(
    relationship_domain,
):
    domain = relationship_domain
    relationship_record = domain["service"].create_relationship(
        data={
            "project_id": domain["project"].id,
            "meaning": "requires",
            "purpose": "Direct review constraint",
            "source_role": "provider",
            "target_role": "consumer",
            "source": {
                "kind": "workspace",
                "workspace_id": domain["provider_workspace"].id,
            },
            "target": {
                "kind": "workspace",
                "workspace_id": domain["consumer_workspace"].id,
            },
            "steward_id": domain["actors"]["steward"].id,
        },
        current_user=domain["actors"]["project_owner"],
    )
    with pytest.raises(IntegrityError):
        with domain["service"].db.begin_nested():
            domain["service"].db.add(
                InterfaceCommitment(
                    commitment_key="direct-review-required",
                    relationship_id=relationship_record["id"],
                    project_id=domain["project"].id,
                    provider_kind="workspace",
                    provider_workspace_id=domain["provider_workspace"].id,
                    consumer_workspace_id=domain["consumer_workspace"].id,
                    required_information="Reviewed information",
                    intended_use="Design",
                    completeness_expectation="Complete",
                    expected_source_basis="Calculation",
                    stage_or_due_condition="Before use",
                    criticality="critical",
                    confidentiality="project",
                    steward_id=domain["actors"]["steward"].id,
                    consumer_reviewer_id=domain["actors"]["consumer"].id,
                    state="fulfilled_for_stated_use",
                    supplied_source_key="SRC",
                    supplied_revision="A",
                    fulfilment_use="Design",
                    external_review_required=True,
                    external_review_evidence=None,
                    current_use=True,
                    reassessment_needed=False,
                    version=1,
                    created_by_id=domain["actors"]["project_owner"].id,
                )
            )
            domain["service"].db.flush()


# ---------------------------------------------------------------------------
# PATCH-020.2.2 Final Review remediation:
# complete direct PostgreSQL invalid-state and integrity coverage.
# ---------------------------------------------------------------------------

from datetime import datetime, timezone
from uuid import uuid4


def _direct_relationship_values(domain, **overrides):
    values = {
        "relationship_key": f"rel-{uuid4().hex}",
        "project_id": domain["project"].id,
        "meaning": "requires",
        "purpose": f"Direct integrity test {uuid4()}",
        "applicability": None,
        "source_role": "provider",
        "target_role": "consumer",
        "source_kind": "workspace",
        "source_context_id": None,
        "source_project_id": None,
        "source_workspace_id": domain["provider_workspace"].id,
        "source_discipline": None,
        "source_external_key": None,
        "target_kind": "workspace",
        "target_context_id": None,
        "target_project_id": None,
        "target_workspace_id": domain["consumer_workspace"].id,
        "target_discipline": None,
        "target_external_key": None,
        "steward_id": domain["actors"]["steward"].id,
        "created_by_id": domain["actors"]["project_owner"].id,
        "lifecycle": "current",
        "version": 1,
        "withdrawal_reason": None,
        "withdrawn_at": None,
    }
    values.update(overrides)
    return values


def _create_direct_relationship(domain, **overrides):
    record = EngineeringContextRelationship(
        **_direct_relationship_values(domain, **overrides)
    )
    domain["service"].db.add(record)
    domain["service"].db.flush()
    return record


def _direct_commitment_values(
    domain,
    relationship_id,
    **overrides,
):
    values = {
        "commitment_key": f"com-{uuid4().hex}",
        "relationship_id": relationship_id,
        "project_id": domain["project"].id,
        "provider_kind": "workspace",
        "provider_user_id": None,
        "provider_workspace_id": domain["provider_workspace"].id,
        "provider_external_key": None,
        "consumer_workspace_id": domain["consumer_workspace"].id,
        "required_information": "Governed engineering information",
        "intended_use": "Consumer engineering design",
        "completeness_expectation": "Complete and revision identified",
        "expected_source_basis": "Governed project evidence",
        "stage_or_due_condition": "Before consumer design use",
        "criticality": "important",
        "confidentiality": "project",
        "steward_id": domain["actors"]["steward"].id,
        "consumer_reviewer_id": domain["actors"]["consumer"].id,
        "state": "identified",
        "supplied_source_key": None,
        "supplied_revision": None,
        "fulfilment_use": None,
        "external_review_evidence": None,
        "external_review_required": False,
        "successor_commitment_id": None,
        "current_use": True,
        "withdrawal_reason": None,
        "withdrawn_at": None,
        "reassessment_needed": False,
        "reassessment_trigger": None,
        "reassessment_reason": None,
        "version": 1,
        "created_by_id": domain["actors"]["project_owner"].id,
    }
    values.update(overrides)
    return values


def _assert_relationship_rejected(domain, **overrides):
    with pytest.raises(IntegrityError):
        with domain["service"].db.begin_nested():
            domain["service"].db.add(
                EngineeringContextRelationship(
                    **_direct_relationship_values(domain, **overrides)
                )
            )
            domain["service"].db.flush()


def _assert_commitment_rejected(
    domain,
    relationship_id,
    **overrides,
):
    with pytest.raises(IntegrityError):
        with domain["service"].db.begin_nested():
            domain["service"].db.add(
                InterfaceCommitment(
                    **_direct_commitment_values(
                        domain,
                        relationship_id,
                        **overrides,
                    )
                )
            )
            domain["service"].db.flush()


@pytest.mark.parametrize(
    "overrides",
    [
        {"meaning": "unsupported_relationship"},
        {"lifecycle": "bad_lifecycle"},
        {"version": 0},
        {
            "source_kind": "workspace",
            "source_workspace_id": None,
            "source_project_id": 1,
        },
        {
            "source_workspace_id": 1,
            "source_project_id": 1,
        },
        {
            "target_kind": "workspace",
            "target_workspace_id": None,
            "target_project_id": 1,
        },
        {
            "target_workspace_id": 1,
            "target_project_id": 1,
        },
        {
            "source_kind": "workspace",
            "source_workspace_id": None,
            "source_external_key": "SRC-MISMATCH",
        },
        {
            "target_kind": "workspace",
            "target_workspace_id": None,
            "target_external_key": "TGT-MISMATCH",
        },
        {
            "lifecycle": "current",
            "withdrawal_reason": "must not exist",
            "withdrawn_at": datetime.now(timezone.utc),
        },
        {
            "lifecycle": "withdrawn",
            "withdrawal_reason": None,
            "withdrawn_at": None,
        },
    ],
)
def test_direct_postgresql_rejects_invalid_relationship_contracts(
    relationship_domain,
    overrides,
):
    _assert_relationship_rejected(
        relationship_domain,
        **overrides,
    )


def test_direct_postgresql_rejects_relationship_self_reference(
    relationship_domain,
):
    domain = relationship_domain
    _assert_relationship_rejected(
        domain,
        source_kind="workspace",
        source_workspace_id=domain["provider_workspace"].id,
        target_kind="workspace",
        target_workspace_id=domain["provider_workspace"].id,
    )


def test_direct_postgresql_rejects_duplicate_current_relationship_identity(
    relationship_domain,
):
    domain = relationship_domain
    first = _create_direct_relationship(domain)

    duplicate_values = {
        "project_id": first.project_id,
        "meaning": first.meaning,
        "purpose": first.purpose,
        "source_role": first.source_role,
        "target_role": first.target_role,
        "source_kind": first.source_kind,
        "source_context_id": first.source_context_id,
        "source_project_id": first.source_project_id,
        "source_workspace_id": first.source_workspace_id,
        "source_discipline": first.source_discipline,
        "source_external_key": first.source_external_key,
        "target_kind": first.target_kind,
        "target_context_id": first.target_context_id,
        "target_project_id": first.target_project_id,
        "target_workspace_id": first.target_workspace_id,
        "target_discipline": first.target_discipline,
        "target_external_key": first.target_external_key,
    }

    _assert_relationship_rejected(
        domain,
        **duplicate_values,
    )


def test_direct_postgresql_rejects_project_endpoint_outside_relationship_scope(
    relationship_domain,
):
    domain = relationship_domain
    _assert_relationship_rejected(
        domain,
        source_kind="project",
        source_workspace_id=None,
        source_project_id=domain["other_project"].id,
    )


def _create_relationship_for_commitment(domain):
    return _create_direct_relationship(
        domain,
        purpose=f"Commitment integrity {uuid4()}",
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"provider_kind": "unsupported_provider"},
        {"state": "unsupported_state"},
        {"criticality": "bad_criticality"},
        {"confidentiality": "unsupported_confidentiality"},
        {"version": 0},
        {
            "provider_kind": "workspace",
            "provider_workspace_id": None,
            "provider_user_id": 1,
        },
        {
            "provider_workspace_id": 1,
            "provider_user_id": 1,
        },
        {
            "current_use": False,
            "withdrawal_reason": None,
            "withdrawn_at": None,
        },
        {
            "current_use": True,
            "withdrawal_reason": "invalid current-use withdrawal",
            "withdrawn_at": datetime.now(timezone.utc),
        },
        {
            "reassessment_needed": True,
            "reassessment_trigger": None,
            "reassessment_reason": None,
        },
        {
            "reassessment_needed": False,
            "reassessment_trigger": "must not exist",
            "reassessment_reason": "must not exist",
        },
        {
            "state": "fulfilled_for_stated_use",
            "supplied_source_key": None,
            "supplied_revision": None,
            "fulfilment_use": None,
        },
    ],
)
def test_direct_postgresql_rejects_invalid_commitment_states(
    relationship_domain,
    overrides,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)
    _assert_commitment_rejected(
        domain,
        relationship.id,
        **overrides,
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "required_information",
        "intended_use",
        "completeness_expectation",
        "expected_source_basis",
        "stage_or_due_condition",
    ],
)
def test_direct_postgresql_rejects_blank_commitment_contract_fields(
    relationship_domain,
    field_name,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)
    _assert_commitment_rejected(
        domain,
        relationship.id,
        **{field_name: "   "},
    )


def test_direct_postgresql_rejects_same_provider_and_consumer_workspace(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)
    _assert_commitment_rejected(
        domain,
        relationship.id,
        provider_workspace_id=domain["consumer_workspace"].id,
        consumer_workspace_id=domain["consumer_workspace"].id,
    )


def test_direct_postgresql_rejects_commitment_project_mismatch(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)
    _assert_commitment_rejected(
        domain,
        relationship.id,
        project_id=domain["other_project"].id,
    )


def test_direct_postgresql_rejects_provider_workspace_from_other_project(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)
    _assert_commitment_rejected(
        domain,
        relationship.id,
        provider_workspace_id=domain["other_workspace"].id,
    )


def test_direct_postgresql_rejects_consumer_workspace_from_other_project(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)
    _assert_commitment_rejected(
        domain,
        relationship.id,
        consumer_workspace_id=domain["other_workspace"].id,
    )


def test_direct_postgresql_rejects_duplicate_commitment_for_relationship(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)

    first = InterfaceCommitment(
        **_direct_commitment_values(
            domain,
            relationship.id,
        )
    )
    domain["service"].db.add(first)
    domain["service"].db.flush()

    _assert_commitment_rejected(
        domain,
        relationship.id,
    )


def test_direct_postgresql_rejects_fulfilment_missing_required_evidence(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)

    _assert_commitment_rejected(
        domain,
        relationship.id,
        state="fulfilled_for_stated_use",
        supplied_source_key="SRC-001",
        supplied_revision="A",
        fulfilment_use="Consumer engineering design",
        external_review_required=True,
        external_review_evidence=None,
    )


@pytest.mark.parametrize(
    "actor_key",
    ["inactive"],
)
def test_direct_postgresql_rejects_inactive_commitment_responsibilities(
    relationship_domain,
    actor_key,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)

    _assert_commitment_rejected(
        domain,
        relationship.id,
        steward_id=domain["actors"][actor_key].id,
    )

    _assert_commitment_rejected(
        domain,
        relationship.id,
        consumer_reviewer_id=domain["actors"][actor_key].id,
    )


def test_history_protection_restricts_deleting_referenced_workspaces(
    relationship_domain,
):
    domain = relationship_domain
    relationship = _create_relationship_for_commitment(domain)

    commitment = InterfaceCommitment(
        **_direct_commitment_values(
            domain,
            relationship.id,
        )
    )
    domain["service"].db.add(commitment)
    domain["service"].db.flush()

    with pytest.raises(IntegrityError):
        with domain["service"].db.begin_nested():
            domain["service"].db.execute(
                text(
                    "DELETE FROM engineering_workspaces "
                    "WHERE id = :workspace_id"
                ),
                {
                    "workspace_id": domain["provider_workspace"].id,
                },
            )
            domain["service"].db.flush()

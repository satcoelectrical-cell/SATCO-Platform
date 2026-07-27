import pytest

from app.models.audit_log import AuditLog
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
)
from app.services import engineering_context_relationship_service as module


def _data(domain, purpose="Audited relationship"):
    return {
        "project_id": domain["project"].id,
        "meaning": "requires",
        "purpose": purpose,
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
    }


def test_relationship_creation_and_audit_commit_together(
    relationship_domain,
):
    domain = relationship_domain
    created = domain["service"].create_relationship(
        data=_data(domain),
        current_user=domain["actors"]["project_owner"],
    )
    event = (
        domain["service"].db.query(AuditLog)
        .filter(
            AuditLog.entity == "CONTEXT_RELATIONSHIP",
            AuditLog.entity_id == created["id"],
        )
        .one()
    )
    assert event.action == "CONTEXT_RELATIONSHIP_CREATED"
    assert event.details["project_id"] == domain["project"].id
    assert event.details["version"] == 1


def test_forced_audit_failure_rolls_back_relationship_creation(
    relationship_domain,
    monkeypatch,
):
    domain = relationship_domain
    before_rows = domain["service"].db.query(
        EngineeringContextRelationship
    ).count()
    before_audits = domain["service"].db.query(AuditLog).count()

    def fail_audit(**_kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(module, "create_audit_log", fail_audit)
    with pytest.raises(RuntimeError, match="forced audit failure"):
        domain["service"].create_relationship(
            data=_data(domain, "Rolled back creation"),
            current_user=domain["actors"]["project_owner"],
        )
    assert (
        domain["service"].db.query(EngineeringContextRelationship).count()
        == before_rows
    )
    assert domain["service"].db.query(AuditLog).count() == before_audits


def test_forced_audit_failure_rolls_back_versioned_mutation(
    relationship_domain,
    monkeypatch,
):
    domain = relationship_domain
    created = domain["service"].create_relationship(
        data=_data(domain),
        current_user=domain["actors"]["project_owner"],
    )
    before_audits = domain["service"].db.query(AuditLog).count()

    def fail_audit(**_kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(module, "create_audit_log", fail_audit)
    with pytest.raises(RuntimeError, match="forced audit failure"):
        domain["service"].update_relationship_metadata(
            relationship_id=created["id"],
            expected_version=created["version"],
            purpose="Must roll back",
            applicability=None,
            reason="Forced failure",
            current_user=domain["actors"]["steward"],
        )
    unchanged = domain["service"].repository.get_relationship(created["id"])
    assert unchanged.purpose == created["purpose"]
    assert unchanged.version == created["version"]
    assert domain["service"].db.query(AuditLog).count() == before_audits


def test_forced_persistence_failure_creates_no_audit(
    relationship_domain,
    monkeypatch,
):
    domain = relationship_domain
    before_audits = domain["service"].db.query(AuditLog).count()

    def fail_persistence(_values):
        raise RuntimeError("forced persistence failure")

    monkeypatch.setattr(
        domain["service"].repository,
        "create_relationship",
        fail_persistence,
    )
    with pytest.raises(RuntimeError, match="forced persistence failure"):
        domain["service"].create_relationship(
            data=_data(domain),
            current_user=domain["actors"]["project_owner"],
        )
    assert domain["service"].db.query(AuditLog).count() == before_audits


# ---------------------------------------------------------------------------
# PATCH-020.2.2 Final Review remediation:
# complete audit/persistence rollback coverage for governed mutations.
# ---------------------------------------------------------------------------

from app.models.engineering_context_relationship import InterfaceCommitment


def _remediation_relationship(domain, purpose="Rollback relationship"):
    return domain["service"].create_relationship(
        data={
            "project_id": domain["project"].id,
            "meaning": "requires",
            "purpose": purpose,
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


def _remediation_commitment(
    domain,
    relationship_id,
    *,
    external_review_required=False,
):
    return domain["service"].create_commitment(
        data={
            "relationship_id": relationship_id,
            "provider_kind": "workspace",
            "provider_workspace_id": domain["provider_workspace"].id,
            "consumer_workspace_id": domain["consumer_workspace"].id,
            "required_information": "Qualified engineering information",
            "intended_use": "Consumer engineering design",
            "completeness_expectation": "Complete and revision identified",
            "expected_source_basis": "Governed project evidence",
            "stage_or_due_condition": "Before consumer design use",
            "criticality": "important",
            "confidentiality": "project",
            "steward_id": domain["actors"]["steward"].id,
            "consumer_reviewer_id": domain["actors"]["consumer"].id,
            "external_review_required": external_review_required,
        },
        current_user=domain["actors"]["project_owner"],
    )


def _column_snapshot(record):
    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }


def _fresh_relationship(domain, relationship_id):
    domain["service"].db.expire_all()
    return domain["service"].db.get(
        EngineeringContextRelationship,
        relationship_id,
    )


def _fresh_commitment(domain, commitment_id):
    domain["service"].db.expire_all()
    return domain["service"].db.get(
        InterfaceCommitment,
        commitment_id,
    )


def _prepare_audit_case(domain, case_name):
    service = domain["service"]
    actors = domain["actors"]

    relationship = _remediation_relationship(
        domain,
        purpose=f"Audit rollback {case_name}",
    )

    if case_name.startswith("relationship_"):
        return relationship, None

    if case_name == "commitment_create":
        return relationship, None

    commitment = _remediation_commitment(
        domain,
        relationship["id"],
        external_review_required=(case_name == "commitment_fulfilment"),
    )

    if case_name in {
        "commitment_information_provided",
        "commitment_fulfilment",
    }:
        commitment = service.transition_commitment(
            commitment_id=commitment["id"],
            target="acknowledged_by_provider",
            expected_version=commitment["version"],
            reason="Prepare provider acknowledgement",
            current_user=actors["provider"],
        )

    if case_name == "commitment_fulfilment":
        commitment = service.transition_commitment(
            commitment_id=commitment["id"],
            target="information_provided",
            expected_version=commitment["version"],
            reason="Prepare supplied information",
            supplied_source_key="SRC-AUDIT",
            supplied_revision="A",
            current_user=actors["provider"],
        )

    if case_name == "commitment_restoration":
        commitment = service.set_commitment_current_use(
            commitment_id=commitment["id"],
            current_use=False,
            expected_version=commitment["version"],
            reason="Prepare withdrawn commitment",
            current_user=actors["project_owner"],
        )

    return relationship, commitment


def _invoke_audit_case(domain, case_name, relationship, commitment):
    service = domain["service"]
    actors = domain["actors"]

    if case_name == "relationship_metadata":
        return service.update_relationship_metadata(
            relationship_id=relationship["id"],
            expected_version=relationship["version"],
            purpose="Audit failure metadata",
            applicability="Audit failure applicability",
            reason="Forced audit failure",
            current_user=actors["steward"],
        )

    if case_name == "relationship_steward":
        return service.change_relationship_steward(
            relationship_id=relationship["id"],
            expected_version=relationship["version"],
            steward_id=actors["project_owner"].id,
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "relationship_withdrawal":
        return service.set_relationship_lifecycle(
            relationship_id=relationship["id"],
            target="withdrawn",
            expected_version=relationship["version"],
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "commitment_create":
        return _remediation_commitment(domain, relationship["id"])

    if case_name == "commitment_provider_change":
        return service.change_commitment_responsibility(
            commitment_id=commitment["id"],
            expected_version=commitment["version"],
            field="provider_workspace_id",
            value=domain["unrelated_workspace"].id,
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "commitment_consumer_change":
        return service.change_commitment_responsibility(
            commitment_id=commitment["id"],
            expected_version=commitment["version"],
            field="consumer_workspace_id",
            value=domain["unrelated_workspace"].id,
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "commitment_steward_change":
        return service.change_commitment_responsibility(
            commitment_id=commitment["id"],
            expected_version=commitment["version"],
            field="steward_id",
            value=actors["project_owner"].id,
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "commitment_information_provided":
        return service.transition_commitment(
            commitment_id=commitment["id"],
            target="information_provided",
            expected_version=commitment["version"],
            reason="Forced audit failure",
            supplied_source_key="SRC-ROLLBACK",
            supplied_revision="B",
            current_user=actors["provider"],
        )

    if case_name == "commitment_fulfilment":
        return service.transition_commitment(
            commitment_id=commitment["id"],
            target="fulfilled_for_stated_use",
            expected_version=commitment["version"],
            reason="Forced audit failure",
            fulfilment_use="Consumer engineering design",
            external_review_evidence="EXT-REVIEW-001",
            current_user=actors["consumer"],
        )

    if case_name == "commitment_withdrawal":
        return service.set_commitment_current_use(
            commitment_id=commitment["id"],
            current_use=False,
            expected_version=commitment["version"],
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "commitment_restoration":
        return service.set_commitment_current_use(
            commitment_id=commitment["id"],
            current_use=True,
            expected_version=commitment["version"],
            reason="Forced audit failure",
            current_user=actors["project_owner"],
        )

    if case_name == "commitment_source_revision":
        return service.change_supplied_source(
            commitment_id=commitment["id"],
            expected_version=commitment["version"],
            source_key="SRC-REVISION",
            revision="C",
            reason="Forced audit failure",
            current_user=actors["provider"],
        )

    if case_name == "commitment_reassessment":
        return service.set_reassessment(
            commitment_id=commitment["id"],
            needed=True,
            expected_version=commitment["version"],
            trigger="source revision changed",
            reason="Forced audit failure",
            current_user=actors["steward"],
        )

    raise AssertionError(f"Unsupported audit remediation case: {case_name}")


AUDIT_MUTATION_CASES = [
    "relationship_metadata",
    "relationship_steward",
    "relationship_withdrawal",
    "commitment_create",
    "commitment_provider_change",
    "commitment_consumer_change",
    "commitment_steward_change",
    "commitment_information_provided",
    "commitment_fulfilment",
    "commitment_withdrawal",
    "commitment_restoration",
    "commitment_source_revision",
    "commitment_reassessment",
]


@pytest.mark.parametrize("case_name", AUDIT_MUTATION_CASES)
def test_forced_audit_failure_rolls_back_every_governed_mutation(
    relationship_domain,
    monkeypatch,
    case_name,
):
    domain = relationship_domain
    relationship, commitment = _prepare_audit_case(domain, case_name)

    relationship_before = _column_snapshot(
        _fresh_relationship(domain, relationship["id"])
    )
    commitment_before = (
        _column_snapshot(_fresh_commitment(domain, commitment["id"]))
        if commitment is not None
        else None
    )
    relationship_count_before = domain["service"].db.query(
        EngineeringContextRelationship
    ).count()
    commitment_count_before = domain["service"].db.query(
        InterfaceCommitment
    ).count()
    audit_count_before = domain["service"].db.query(AuditLog).count()

    def fail_audit(**_kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(module, "create_audit_log", fail_audit)

    with pytest.raises(RuntimeError, match="forced audit failure"):
        _invoke_audit_case(
            domain,
            case_name,
            relationship,
            commitment,
        )

    assert (
        domain["service"].db.query(EngineeringContextRelationship).count()
        == relationship_count_before
    )
    assert (
        domain["service"].db.query(InterfaceCommitment).count()
        == commitment_count_before
    )
    assert domain["service"].db.query(AuditLog).count() == audit_count_before

    relationship_after = _column_snapshot(
        _fresh_relationship(domain, relationship["id"])
    )
    assert relationship_after == relationship_before

    if commitment is not None:
        commitment_after = _column_snapshot(
            _fresh_commitment(domain, commitment["id"])
        )
        assert commitment_after == commitment_before


@pytest.mark.parametrize("case_name", AUDIT_MUTATION_CASES)
def test_forced_persistence_failure_creates_no_partial_change_or_audit(
    relationship_domain,
    monkeypatch,
    case_name,
):
    domain = relationship_domain
    relationship, commitment = _prepare_audit_case(domain, case_name)

    relationship_before = _column_snapshot(
        _fresh_relationship(domain, relationship["id"])
    )
    commitment_before = (
        _column_snapshot(_fresh_commitment(domain, commitment["id"]))
        if commitment is not None
        else None
    )
    relationship_count_before = domain["service"].db.query(
        EngineeringContextRelationship
    ).count()
    commitment_count_before = domain["service"].db.query(
        InterfaceCommitment
    ).count()
    audit_count_before = domain["service"].db.query(AuditLog).count()

    def fail_persistence(*_args, **_kwargs):
        raise RuntimeError("forced persistence failure")

    if case_name == "commitment_create":
        monkeypatch.setattr(
            domain["service"].repository,
            "create_commitment",
            fail_persistence,
        )
    elif case_name.startswith("relationship_"):
        monkeypatch.setattr(
            domain["service"].repository,
            "update_relationship_versioned",
            fail_persistence,
        )
    else:
        monkeypatch.setattr(
            domain["service"].repository,
            "update_commitment_versioned",
            fail_persistence,
        )

    with pytest.raises(RuntimeError, match="forced persistence failure"):
        _invoke_audit_case(
            domain,
            case_name,
            relationship,
            commitment,
        )

    assert (
        domain["service"].db.query(EngineeringContextRelationship).count()
        == relationship_count_before
    )
    assert (
        domain["service"].db.query(InterfaceCommitment).count()
        == commitment_count_before
    )
    assert domain["service"].db.query(AuditLog).count() == audit_count_before

    relationship_after = _column_snapshot(
        _fresh_relationship(domain, relationship["id"])
    )
    assert relationship_after == relationship_before

    if commitment is not None:
        commitment_after = _column_snapshot(
            _fresh_commitment(domain, commitment["id"])
        )
        assert commitment_after == commitment_before

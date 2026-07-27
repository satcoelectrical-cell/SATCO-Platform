import pytest

from app.exceptions.engineering_context_relationship import CommitmentNotFound
from app.exceptions.engineering_context_relationship import (
    RelationshipForbidden,
)
from app.exceptions.engineering_context_relationship import (
    RelationshipNotFound,
)


def _relationship(domain, *, actor=None):
    actor = actor or domain["actors"]["project_owner"]
    return domain["service"].create_relationship(
        data={
            "project_id": domain["project"].id,
            "meaning": "requires",
            "purpose": "Permission matrix dependency",
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
        current_user=actor,
    )


def _commitment(domain, relationship_id, *, confidentiality="project"):
    return domain["service"].create_commitment(
        data={
            "relationship_id": relationship_id,
            "provider_kind": "workspace",
            "provider_workspace_id": domain["provider_workspace"].id,
            "consumer_workspace_id": domain["consumer_workspace"].id,
            "required_information": "Qualified load schedule",
            "intended_use": "Consumer design",
            "completeness_expectation": "Complete and revision identified",
            "expected_source_basis": "Approved calculation",
            "stage_or_due_condition": "Before design use",
            "criticality": "important",
            "confidentiality": confidentiality,
            "steward_id": (
                domain["actors"]["project_owner"].id
                if confidentiality == "restricted"
                else domain["actors"]["steward"].id
            ),
            "consumer_reviewer_id": domain["actors"]["consumer"].id,
        },
        current_user=domain["actors"]["project_owner"],
    )


@pytest.mark.parametrize("actor_name", ["unrelated", "inactive"])
def test_unauthorized_actor_cannot_create_relationship(
    relationship_domain,
    actor_name,
):
    with pytest.raises(RelationshipForbidden):
        _relationship(
            relationship_domain,
            actor=relationship_domain["actors"][actor_name],
        )


def test_same_project_participants_have_bounded_non_transitive_visibility(
    relationship_domain,
):
    domain = relationship_domain
    relationship_record = _relationship(domain)
    service = domain["service"]
    assert service.get_relationship(
        relationship_id=relationship_record["id"],
        current_user=domain["actors"]["provider"],
    )["id"] == relationship_record["id"]
    assert service.get_relationship(
        relationship_id=relationship_record["id"],
        current_user=domain["actors"]["consumer"],
    )["id"] == relationship_record["id"]
    with pytest.raises(RelationshipNotFound):
        service.get_relationship(
            relationship_id=relationship_record["id"],
            current_user=domain["actors"]["unrelated"],
        )
    listing = service.list_relationships(
        project_id=domain["project"].id,
        workspace_id=domain["unrelated_workspace"].id,
        current_user=domain["actors"]["unrelated"],
    )
    assert listing["total"] == 0
    assert listing["items"] == []


def test_cross_project_and_cross_customer_endpoints_are_rejected(
    relationship_domain,
):
    domain = relationship_domain
    with pytest.raises(Exception):
        domain["service"].create_relationship(
            data={
                "project_id": domain["project"].id,
                "meaning": "requires",
                "purpose": "Invalid cross-customer dependency",
                "source_role": "provider",
                "target_role": "consumer",
                "source": {
                    "kind": "workspace",
                    "workspace_id": domain["provider_workspace"].id,
                },
                "target": {
                    "kind": "workspace",
                    "workspace_id": domain["other_workspace"].id,
                },
                "steward_id": domain["actors"]["steward"].id,
            },
            current_user=domain["actors"]["project_owner"],
        )


def test_restricted_commitment_hides_identifier_from_non_owner_and_admin(
    relationship_domain,
):
    domain = relationship_domain
    relationship_record = _relationship(domain)
    commitment = _commitment(
        domain,
        relationship_record["id"],
        confidentiality="restricted",
    )
    service = domain["service"]
    assert service.get_commitment(
        commitment_id=commitment["id"],
        current_user=domain["actors"]["project_owner"],
    )["id"] == commitment["id"]
    for actor in (
        domain["actors"]["consumer"],
        domain["actors"]["unrelated"],
        domain["actors"]["admin"],
    ):
        with pytest.raises(CommitmentNotFound):
            service.get_commitment(
                commitment_id=commitment["id"],
                current_user=actor,
            )


def test_provider_and_consumer_actions_do_not_transfer_authority(
    relationship_domain,
):
    domain = relationship_domain
    relationship_record = _relationship(domain)
    commitment = _commitment(domain, relationship_record["id"])
    service = domain["service"]
    with pytest.raises(RelationshipForbidden):
        service.transition_commitment(
            commitment_id=commitment["id"],
            target="acknowledged_by_provider",
            expected_version=1,
            reason="Consumer cannot acknowledge",
            current_user=domain["actors"]["consumer"],
        )
    acknowledged = service.transition_commitment(
        commitment_id=commitment["id"],
        target="acknowledged_by_provider",
        expected_version=1,
        reason="Provider acknowledgement",
        current_user=domain["actors"]["provider"],
    )
    with pytest.raises(RelationshipForbidden):
        service.transition_commitment(
            commitment_id=commitment["id"],
            target="information_provided",
            expected_version=acknowledged["version"],
            reason="Consumer cannot provide",
            supplied_source_key="SRC-1",
            supplied_revision="A",
            current_user=domain["actors"]["consumer"],
        )


def test_governed_changes_require_bounded_authority(relationship_domain):
    domain = relationship_domain
    relationship_record = _relationship(domain)
    commitment = _commitment(domain, relationship_record["id"])
    service = domain["service"]
    with pytest.raises(RelationshipForbidden):
        service.update_relationship_metadata(
            relationship_id=relationship_record["id"],
            expected_version=1,
            purpose="Unauthorized update",
            applicability=None,
            reason="Not authorized",
            current_user=domain["actors"]["provider"],
        )
    with pytest.raises(RelationshipForbidden):
        service.change_commitment_responsibility(
            commitment_id=commitment["id"],
            expected_version=1,
            field="provider_workspace_id",
            value=domain["consumer_workspace"].id,
            reason="Unauthorized provider change",
            current_user=domain["actors"]["unrelated"],
        )

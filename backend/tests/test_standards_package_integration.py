"""PATCH-054 Batch-3 applicability and package-advisory conformance evidence."""

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1
from app.models.standards import ProjectStandardApplicability, StandardsOutbox
from app.repositories.standards_repository import StandardsRepository
from app.schemas.standards import ApplicabilityDeclaration, ApplicabilityRetirement
from app.services.standards_service import StandardsError, StandardsService
from app.standards.canonical import canonical_digest


class _Candidates:
    def __init__(self, candidate: dict):
        self.candidate = candidate

    def candidates(self, *, organization_id, project_id, package_version=None):
        if package_version and package_version != self.candidate["package_version"]:
            return []
        return [self.candidate] if (str(organization_id), project_id) == (self.candidate["organization_id"], self.candidate["project_id"]) else []


def _fixture(db_session, admin_user):
    from tests.test_standards_migrations import _foundation_fixture

    return _foundation_fixture(db_session, admin_user)


def _candidate(values):
    semantic = {
        "organization_id": str(values["organization"]), "project_id": values["project"], "workspace_id": 1,
        "package_key": "electrical", "package_version": "1.0.0", "descriptor_digest": "a" * 64,
        "configuration_revision": 1, "hook_id": "electrical.standards_applicability",
        "designation_key": "electrical.design_basis.standard", "family_key": "electrical",
        "suggested_role": "design_basis", "rationale_code": "package_design_basis_advisory",
    }
    candidate_id = uuid4()
    return {"candidate_id": str(candidate_id), "candidate_digest": canonical_digest({"candidate_id": candidate_id, **semantic}),
            **semantic, "standard_identity_id": None, "standard_edition_id": None, "emitted_at": "2026-01-01T00:00:00+00:00"}


def _declaration(values, **overrides):
    base = {
        "edition_id": values["edition"], "status": "declared_applicable", "applicability_role": "design_basis",
        "rationale_code": "human_review", "rationale": "Human Project applicability decision", "expected_revision": 0,
    }
    return ApplicabilityDeclaration(**(base | overrides))


def _service(db_session, candidate):
    return StandardsService(db_session, StandardsRepository(db_session), candidates=_Candidates(candidate))


def test_app01_package_contract_is_static_bounded_and_non_authoritative():
    hooks = tuple(hook for descriptor in DESCRIPTORS_V1 for hook in descriptor.contributions.standards_hooks)
    assert hooks and all(1 <= hook.max_results <= 64 and hook.timeout_ms <= 60_000 for hook in hooks)
    candidates = tuple(candidate for hook in hooks for candidate in hook.candidates)
    assert candidates and all(candidate.suggested_role in {"informative", "design_basis"} for candidate in candidates)
    assert all("url" not in candidate.model_dump() and "mandatory" not in candidate.model_dump().values() for candidate in candidates)


def test_app02_to_app05_candidate_human_declaration_mandatory_and_audit(db_session, admin_user):
    values, candidate = _fixture(db_session, admin_user), None
    candidate = _candidate(values)
    service = _service(db_session, candidate)
    data = _declaration(values, candidate_id=UUID(candidate["candidate_id"]), candidate_digest=candidate["candidate_digest"])
    status, body = service.declare_applicability(actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"], data=data, idempotency_key="app-candidate")
    assert status == 201 and body["status"] == "declared_applicable"
    mandatory_status, mandatory = service.declare_applicability(
        actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"],
        data=_declaration(values, applicability_role="mandatory", expected_revision=1,
            mandatory_source_kind="contract", mandatory_source_reference="project-contract-1",
            mandatory_source_digest="b" * 64), idempotency_key="app-mandatory")
    assert mandatory_status == 201 and mandatory["applicability_role"] == "mandatory"
    rows = list(db_session.scalars(select(ProjectStandardApplicability).where(ProjectStandardApplicability.project_id == values["project"]).order_by(ProjectStandardApplicability.created_at)))
    assert [row.status for row in rows] == ["candidate_advisory", "declared_applicable", "declared_applicable"]
    assert {event.event_id for event in db_session.scalars(select(StandardsOutbox).where(StandardsOutbox.aggregate_type == "project_standard_applicability"))} == {"standards.applicability.candidate_recorded", "standards.applicability.declared"}
    with pytest.raises(ValidationError):
        _declaration(values, applicability_role="mandatory")


def test_app03_app04_app06_app07_app08_history_cas_and_retirement(db_session, admin_user):
    values = _fixture(db_session, admin_user)
    candidate = _candidate(values)
    service = _service(db_session, candidate)
    first_status, first = service.declare_applicability(actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"], data=_declaration(values), idempotency_key="app-first")
    assert first_status == 201
    second_status, second = service.declare_applicability(actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"], data=_declaration(values, status="declared_not_applicable", expected_revision=1), idempotency_key="app-second")
    assert second_status == 201 and second["predecessor_id"] == first["applicability_id"]
    with pytest.raises(StandardsError, match="VERSION_CONFLICT"):
        service.declare_applicability(actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"], data=_declaration(values, expected_revision=1), idempotency_key="app-stale")
    retired_status, retired = service.retire_applicability(actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"], applicability_id=UUID(second["applicability_id"]), data=ApplicabilityRetirement(expected_revision=2, reason="Human retirement"), idempotency_key="app-retire")
    assert retired_status == 201 and retired["status"] == "retired" and retired["predecessor_id"] == second["applicability_id"]
    with pytest.raises(StandardsError, match="PROTECTED_NOT_FOUND"):
        service.declare_applicability(actor_id=admin_user.id, organization_id=values["organization"], project_id=values["project"], data=_declaration(values, edition_id=uuid4(), expected_revision=0), idempotency_key="app-unresolved")
    events = {event.event_id for event in db_session.scalars(select(StandardsOutbox).where(StandardsOutbox.aggregate_type == "project_standard_applicability"))}
    assert events == {"standards.applicability.declared", "standards.applicability.retired"}

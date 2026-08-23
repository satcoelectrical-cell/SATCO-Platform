"""Focused S15 transport and prohibited-route evidence for PATCH-032."""

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.organization import Organization, UserOrganizationMembership
from app.api.v1.routers import technical_reports as technical_report_router
from app.api.v1.routers.technical_reports import (
    TechnicalReportApplication, get_technical_report_application,
    _provenance_dto,
)
from app.api.v1.routers.engineering_experience_captures import (
    EngineeringExperienceCaptureApplication,
    get_engineering_experience_capture_application,
)
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
)
from app.main import app
from app.models.technical_report import TechnicalReport
from app.models.technical_report_command import TechnicalReportActor
from app.models.technical_report_command import TechnicalReportCommandMetadata
from app.ports.technical_report import TechnicalReportReadPage
from test_technical_report_service import NOW, command


ACTOR = TechnicalReportActor(7, UUID("03200000-0000-4000-8000-000000000001"))


class FakeService:
    def __init__(self):
        base = command()
        metadata = TechnicalReportCommandMetadata(
            ACTOR, base.metadata.rationale, base.metadata.correlation_id,
            base.metadata.idempotency_id, base.metadata.command_id,
        )
        base = type(base)(metadata, ACTOR.organization_id, base.workspace_id,
                          base.project_id, ACTOR.actor_id, base.purpose,
                          base.content, base.qualification, base.provenance)
        self.report, _ = TechnicalReport.create(base, NOW)
        self.criteria = None

    def create_draft(self, value): return SimpleNamespace(report=self.report)
    def get_report(self, actor, report_id): return self.report
    def list_report_details(self, actor, criteria):
        self.criteria = criteria
        return SimpleNamespace(items=(self.report,), total=1, page=criteria.page, size=criteria.size)
    def revise_draft(self, value): return SimpleNamespace(report=self.report)
    def accept_exact_draft(self, value):
        self.report.accept_exact_draft(value, NOW)
        return SimpleNamespace(report=self.report)
    def create_successor(self, value): return SimpleNamespace(report=self.report)
    def retrieve_lineage_details(self, actor, report_id, page, size):
        return SimpleNamespace(subject=self.report, predecessor=None,
            successors=SimpleNamespace(items=(), total=0, page=page, size=size))
    def request_ai_proposal(self, *args, **kwargs):
        return SimpleNamespace(proposal_text="Advisory proposal", attribution="test-provider")


def _application():
    service = FakeService()
    return TechnicalReportApplication(service, ACTOR), service


def _create_body(service):
    report = service.report
    return {
        "workspace_id": report.workspace_id,
        "project_id": report.project_id,
        "purpose": report.purpose.value,
        "content": {
            "engineering_scope": report.content.engineering_scope,
            "technical_content": report.content.technical_content,
            "assumptions": list(report.content.assumptions),
            "uncertainty": report.content.uncertainty,
            "limitations": list(report.content.limitations),
            "conclusions": report.content.conclusions,
            "recommendations": list(report.content.recommendations),
        },
        "qualification": {
            "is_preliminary": report.qualification.is_preliminary,
            "evidence_deficiencies": list(report.qualification.evidence_deficiencies),
            "unresolved_issues": list(report.qualification.unresolved_issues),
            "follow_up_requirements": list(report.qualification.follow_up_requirements),
        },
        "provenance": [_provenance_dto(item).model_dump(mode="json") for item in report.provenance],
    }


def _client():
    application, service = _application()
    app.dependency_overrides[get_technical_report_application] = lambda: application
    return TestClient(app), service


def test_exact_approved_route_surface_and_prohibited_routes():
    expected = {
        ("/technical-reports", "post"), ("/technical-reports", "get"),
        ("/technical-reports/capture-source-candidates", "get"),
        ("/technical-reports/evidence-source-candidates", "get"),
        ("/technical-reports/{report_id}", "get"),
        ("/technical-reports/{report_id}/draft-revisions", "post"),
        ("/technical-reports/{report_id}/acceptance", "post"),
        ("/technical-reports/{report_id}/successors", "post"),
        ("/technical-reports/{report_id}/lineage", "get"),
        ("/technical-reports/{report_id}/ai-draft-proposals", "post"),
        (
            "/technical-reports/{report_id}/evidence/{evidence_id}/supporting-files/{asset_id}/download",
            "get",
        ),
    }
    actual = {(path, method) for path, item in app.openapi()["paths"].items()
              if path.startswith("/technical-reports") for method in item}
    assert actual == expected
    client, service = _client()
    try:
        identifier = service.report.id
        for method in ("put", "patch", "delete"):
            assert getattr(client, method)(f"/technical-reports/{identifier}").status_code == 405
        for suffix in ("publish", "approve", "review", "supersede", "archive"):
            assert client.post(f"/technical-reports/{identifier}/{suffix}").status_code == 404
    finally: app.dependency_overrides.clear()


def test_capture_candidate_static_route_precedes_report_uuid_route_and_returns_authorized_source():
    capture_id = UUID("1d1b2b20-4ce2-4568-821b-1f935d92eaa2")

    class CaptureService:
        def list_workspace(self, workspace_id, filters, page, size, actor):
            assert (workspace_id, page, size) == (1, 1, 20)
            assert filters.lifecycle is EngineeringExperienceCaptureLifecycle.CAPTURED
            assert actor.organization_id == ACTOR.organization_id
            return SimpleNamespace(
                items=[SimpleNamespace(
                    id=capture_id,
                    organization_id=ACTOR.organization_id,
                    project_id=11,
                    workspace_id=1,
                    discipline="electrical",
                    engineering_object_id=None,
                    source_kind=EngineeringExperienceSourceKind.OBSERVATION,
                    original_content="Observed abnormal terminal temperature rise.",
                    source_reference=None,
                    creator_id=ACTOR.actor_id,
                    lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED,
                    version=1,
                    created_at=datetime(2026, 8, 20, 10, 47, tzinfo=timezone.utc),
                )],
                total=1,
                page=page,
                size=size,
            )

    capture_app = EngineeringExperienceCaptureApplication(
        CaptureService(),
        EngineeringExperienceCaptureActor(ACTOR.actor_id, ACTOR.organization_id),
    )
    app.dependency_overrides[get_engineering_experience_capture_application] = (
        lambda: capture_app
    )
    client = TestClient(app)
    try:
        response = client.get(
            "/technical-reports/capture-source-candidates",
            params={"project_id": 11, "workspace_id": 1, "page": 1, "size": 20},
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["capture_id"] == str(capture_id)
        assert response.json()["items"][0]["project_id"] == 11
        assert response.json()["items"][0]["workspace_id"] == 1
    finally:
        app.dependency_overrides.clear()


def test_create_get_list_lineage_and_ai_transport_mapping():
    client, service = _client()
    headers = {"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())}
    try:
        created = client.post("/technical-reports", headers=headers, json=_create_body(service))
        assert created.status_code == 201
        assert created.json()["id"] == str(service.report.id)
        assert client.get(f"/technical-reports/{service.report.id}").status_code == 200
        listed = client.get("/technical-reports", params={"workspace_id": 1, "purpose": "engineering_analysis", "lifecycle": "draft"})
        assert listed.status_code == 200 and listed.json()["total"] == 1
        assert service.criteria.purpose.value == "engineering_analysis"
        assert service.criteria.lifecycle.value == "draft"
        assert client.get(f"/technical-reports/{service.report.id}/lineage").status_code == 200
        proposal = client.post(f"/technical-reports/{service.report.id}/ai-draft-proposals", json={
            "expected_version": 1, "expected_draft_revision_id": str(service.report.draft_revision_id),
            "human_instruction": "Improve clarity", "selected_source_entry_ids": [],
        })
        assert proposal.status_code == 200
        assert proposal.json()["authoritative"] is False
    finally: app.dependency_overrides.clear()


def test_all_mutation_routes_and_lifecycle_specific_responses():
    headers = {"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())}
    client, service = _client()
    try:
        body = _create_body(service)
        revise = {key: value for key, value in body.items() if key not in {"workspace_id", "project_id", "purpose"}}
        revise.update(expected_version=1, expected_draft_revision_id=str(service.report.draft_revision_id), rationale="Revise")
        assert client.post(f"/technical-reports/{service.report.id}/draft-revisions", headers=headers, json=revise).status_code == 200
    finally: app.dependency_overrides.clear()
    client, service = _client()
    try:
        accepted = client.post(f"/technical-reports/{service.report.id}/acceptance", headers=headers, json={
            "expected_version": 1, "exact_draft_revision_id": str(service.report.draft_revision_id),
            "confirmed": True, "rationale": "Accept exact draft",
        })
        assert accepted.status_code == 200 and accepted.json()["lifecycle"] == "accepted"
    finally: app.dependency_overrides.clear()
    client, service = _client()
    try:
        successor = _create_body(service)
        successor.update(expected_predecessor_version=1, selected_copy_references=[], rationale="Create successor")
        assert client.post(f"/technical-reports/{service.report.id}/successors", headers=headers, json=successor).status_code == 201
    finally: app.dependency_overrides.clear()


def test_protected_error_mapping_does_not_disclose_exception_text():
    class Denied(FakeService):
        def get_report(self, *_):
            from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
            raise TechnicalReportAuthorizationDenied()
    service = Denied()
    app.dependency_overrides[get_technical_report_application] = lambda: TechnicalReportApplication(service, ACTOR)
    try:
        response = TestClient(app).get(f"/technical-reports/{service.report.id}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TECHNICAL_REPORT_NOT_FOUND"
        assert "not authorized" not in response.text.lower()
    finally: app.dependency_overrides.clear()


def test_client_scope_and_invalid_pagination_are_stably_rejected_without_plaintext():
    client, service = _client()
    secret = "PROTECTED-TECHNICAL-PLAINTEXT"
    headers = {"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())}
    try:
        body = _create_body(service)
        body["organization_id"] = str(ACTOR.organization_id)
        body["content"]["technical_content"] = secret
        response = client.post("/technical-reports", headers=headers, json=body)
        assert response.status_code == 422 and secret not in response.text
        response = client.get("/technical-reports", params={"workspace_id": 1, "size": 101})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "TECHNICAL_REPORT_VALIDATION_ERROR"
    finally: app.dependency_overrides.clear()


def test_real_http_authentication_organization_context_and_protected_outcomes(
    db_session, relationship_domain, monkeypatch,
):
    """Exercise the real JWT and selected-Organization dependency boundary."""
    actor = relationship_domain["actors"]["project_owner"]
    inactive = relationship_domain["actors"]["inactive"]
    unrelated = relationship_domain["actors"]["unrelated"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    other_workspace = relationship_domain["other_workspace"]
    organization_id = project.organization_id
    factory = sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    monkeypatch.setattr(technical_report_router, "SessionLocal", factory)

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    seed = FakeService()
    body = _create_body(seed)
    body.update(workspace_id=workspace.id, project_id=project.id)
    body["provenance"] = [{
        "entry_id": str(uuid4()), "ordinal": 0,
        "source_class": "contextual_non_material", "source_type": "contextual",
        "is_material": False, "owning_capability": None,
        "reliance_role": "context only", "verification_status": "unverified",
        "availability_status": "available", "origin_attribution": "authenticated engineer",
        "limitations": [],
        "locator": {"locator_type": "contextual", "context_id": str(uuid4()), "owning_context": "test context"},
        "integrity_algorithm": None, "integrity_digest": None,
    }]
    headers = {
        "Authorization": f"Bearer {create_access_token(actor.id)}",
        "X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4()),
    }
    secret = "AUTHORIZED-REPORT-PLAINTEXT"
    body["content"]["technical_content"] = secret
    try:
        with TestClient(app) as client:
            unauthenticated = client.post("/technical-reports", json=body)
            assert unauthenticated.status_code == 401
            assert unauthenticated.json() == {"detail": "Not authenticated"}
            assert secret not in unauthenticated.text
            created = client.post("/technical-reports", headers=headers, json=body)
            assert created.status_code == 201
            report_id = created.json()["id"]
            assert created.json()["content"]["technical_content"] == secret
            assert created.json()["allowed_actions"] == ["revise", "accept", "request_ai_proposal"]
            authorized = client.get(f"/technical-reports/{report_id}", headers=headers)
            assert authorized.status_code == 200
            assert authorized.json()["content"]["technical_content"] == secret

            inactive_response = client.get(
                f"/technical-reports/{report_id}",
                headers={"Authorization": f"Bearer {create_access_token(inactive.id)}"},
            )
            assert inactive_response.status_code == 403
            assert inactive_response.json() == {"detail": "Inactive user"}
            assert secret not in inactive_response.text

            unrelated_membership = db_session.get(
                UserOrganizationMembership, (unrelated.id, organization_id)
            )
            db_session.delete(unrelated_membership)
            db_session.flush()
            nonmember = client.get(
                f"/technical-reports/{report_id}",
                headers={"Authorization": f"Bearer {create_access_token(unrelated.id)}"},
            )
            expected_context_error = {
                "success": False,
                "error": {
                    "code": "ACTIVE_ORGANIZATION_CONTEXT_REQUIRED",
                    "message": "An active Organization context is required",
                },
            }
            assert nonmember.status_code == 403
            assert nonmember.json() == expected_context_error
            assert secret not in nonmember.text

            # Restore membership so this actor exercises application-level non-owner denial.
            db_session.add(UserOrganizationMembership(
                user_id=unrelated.id, organization_id=organization_id,
                is_enabled=True, is_selected=True,
            ))
            db_session.flush()

            absent = client.get(f"/technical-reports/{uuid4()}", headers=headers)
            denied = client.get(
                f"/technical-reports/{report_id}",
                headers={"Authorization": f"Bearer {create_access_token(unrelated.id)}"},
            )
            assert absent.status_code == denied.status_code == 404
            assert absent.json() == denied.json()
            assert secret not in denied.text

            cross_scope = dict(body)
            cross_scope["workspace_id"] = other_workspace.id
            cross_scope["project_id"] = relationship_domain["other_project"].id
            cross_headers = dict(headers, **{"Idempotency-Key": str(uuid4())})
            response = client.post("/technical-reports", headers=cross_headers, json=cross_scope)
            assert response.status_code == 404 and secret not in response.text

            membership = db_session.get(UserOrganizationMembership, (actor.id, organization_id))
            membership.is_enabled = False
            membership.is_selected = False
            db_session.flush()
            response = client.get(f"/technical-reports/{report_id}", headers=headers)
            assert response.status_code == 403
            assert response.json() == expected_context_error
            assert secret not in response.text
            membership.is_enabled = True
            membership.is_selected = True
            db_session.flush()

            organization = db_session.get(Organization, organization_id)
            organization.is_active = False
            db_session.flush()
            response = client.get(f"/technical-reports/{report_id}", headers=headers)
            assert response.status_code == 403
            assert response.json() == expected_context_error
            assert secret not in response.text
    finally:
        app.dependency_overrides.clear()

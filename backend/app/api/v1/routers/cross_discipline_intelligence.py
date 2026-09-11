"""Authorization-first HTTP foundation for 15 PATCH-053 Batch-1 operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.dependencies.cross_discipline_intelligence import (
    CrossDisciplineApplication, decode_cross_discipline_cursor,
    encode_cross_discipline_cursor, get_cross_discipline_application,
)
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.schemas.cross_discipline_intelligence import (
    AssessmentCreate, DispositionAppend, EligibilityQuery, ReassessmentCreate,
    SupersessionCreate, VerificationQuery, AIExplanationRequest, PotentialImpactRequest,
)
router = APIRouter(tags=["Cross-Discipline Intelligence"])
PREFIX = "/projects/{project_id}/cross-discipline"


def _protected():
    return JSONResponse(status_code=404, content={"outcome": "protected_not_found"})


def _project_guard(application, project_id: int, *, mutate=False):
    context = application.context
    project = application.db.scalar(select(Project).where(
        Project.id == project_id, Project.organization_id == context.organization_id,
    ))
    if project is None:
        return None
    permitted = context.user.role == "admin" or context.user.id in {
        project.owner_id, project.primary_assignee_id,
    }
    return project if permitted and (not mutate or permitted) else None


def _workspace_guard(application, project_id: int, workspace_ids: tuple[int, ...], *, mutate=False):
    if _project_guard(application, project_id, mutate=mutate) is None:
        return None
    rows = tuple(application.db.scalars(select(EngineeringWorkspace).where(
        EngineeringWorkspace.project_id == project_id,
        EngineeringWorkspace.id.in_(workspace_ids),
    ).order_by(EngineeringWorkspace.id)))
    if tuple(item.id for item in rows) != workspace_ids:
        return None
    memberships = set(application.db.scalars(select(EngineeringWorkspaceMember.workspace_id).where(
        EngineeringWorkspaceMember.workspace_id.in_(workspace_ids),
        EngineeringWorkspaceMember.user_id == application.context.user.id,
    )))
    for row in rows:
        mutator = application.context.user.role == "admin" or application.context.user.id in {
            row.owner_id, row.primary_assignee_id,
        }
        if (mutate and not mutator) or (not mutate and not (mutator or row.id in memberships)):
            return None
    return rows


def _assessment_guard(application, project_id, assessment_id, *, mutate=False):
    if _project_guard(application, project_id, mutate=mutate) is None:
        return None
    root = application.repository.get_assessment(
        assessment_id, application.context.organization_id, project_id,
        lock=mutate,
    )
    if root is None:
        return None
    workspace_ids = application.repository.assessment_workspace_ids(
        assessment_id=assessment_id,
        organization_id=application.context.organization_id,
        project_id=project_id,
    )
    if _workspace_guard(application, project_id, workspace_ids, mutate=mutate) is None:
        return None
    return root


def _assessment_summary(row, snapshot):
    return {
        "assessment_id": str(row.id), "aggregate_version": row.aggregate_version,
        "status": row.status, "reason_code": row.reason_code,
        "result_digest": snapshot.result_digest,
        "completed_at": row.completed_at,
    }


@router.get(PREFIX + "/definitions", operation_id="list_cross_discipline_definitions")
def definitions(project_id: int, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _project_guard(application, project_id) is None:
        return _protected()
    return application.service.definitions()


@router.get(PREFIX + "/runtime-readiness", operation_id="get_cross_discipline_runtime_readiness")
def readiness(project_id: int, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _project_guard(application, project_id) is None:
        return _protected()
    return application.service.readiness(application.db)


@router.post(PREFIX + "/eligibility", operation_id="evaluate_cross_discipline_eligibility")
def eligibility(project_id: int, data: EligibilityQuery, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    rows = _workspace_guard(application, project_id, data.scope.workspace_ids)
    if rows is None:
        return _protected()
    project = _project_guard(application, project_id)
    return application.service.eligibility(
        data.scope.workspace_ids, combination_id=data.scope.combination_id,
        project_status=project.status,
        package_keys=tuple(
            row.bound_package_key or row.canonical_discipline_id or row.discipline
            for row in rows
        ),
    )


@router.post(PREFIX + "/assessments", operation_id="create_cross_discipline_assessment")
def create_assessment(project_id: int, data: AssessmentCreate, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _workspace_guard(application, project_id, data.scope.workspace_ids, mutate=True) is None:
        return _protected()
    result = application.service.create_foundation_assessment(
        session_factory=application.session_factory,
        actor_id=application.context.user.id,
        actor_role=application.context.user.role,
        organization_id=application.context.organization_id,
        project_id=project_id, data=data,
    )
    status = 201 if result.get("outcome") == "success" else 404 if result.get("outcome") == "protected_not_found" else 409 if result.get("outcome") == "idempotency_conflict" else 422 if result.get("outcome") == "invalid_request" else 503
    return JSONResponse(status_code=status, content=result)


@router.get(PREFIX + "/assessments", operation_id="list_cross_discipline_assessments")
def list_assessments(project_id: int, cursor: str | None = Query(None, max_length=2048), limit: int = Query(50, ge=1, le=100), application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _project_guard(application, project_id) is None:
        return _protected()
    scope = {"kind": "assessments", "organization_id": str(application.context.organization_id), "project_id": project_id, "limit": limit}
    position = decode_cross_discipline_cursor(cursor, scope=scope)
    before = None
    if position:
        before = (datetime.fromisoformat(position[0]), UUID(position[1]))
    rows = application.repository.list_assessments(
        organization_id=application.context.organization_id,
        project_id=project_id, limit=limit, before=before,
    )
    visible = rows[:limit]
    next_cursor = None
    if len(rows) > limit and visible:
        last = visible[-1]
        next_cursor = encode_cross_discipline_cursor(
            scope=scope, position=[last.completed_at.isoformat(), str(last.id)],
        )
    snapshots = tuple(application.repository.snapshot(
        assessment_id=row.id,
        organization_id=application.context.organization_id,
        project_id=project_id,
    ) for row in visible)
    if any(snapshot is None for snapshot in snapshots):
        return JSONResponse(status_code=503, content={"outcome": "unavailable", "reason_code": "integrity_failure"})
    return {
        "items": tuple(_assessment_summary(row, snapshot) for row, snapshot in zip(visible, snapshots)),
        "next_cursor": next_cursor,
    }


@router.get(PREFIX + "/assessments/{assessment_id}", operation_id="get_cross_discipline_assessment")
def get_assessment(project_id: int, assessment_id: UUID, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    row = _assessment_guard(application, project_id, assessment_id)
    if row is None:
        return _protected()
    snapshot = application.repository.snapshot(
        assessment_id=assessment_id, organization_id=application.context.organization_id,
        project_id=project_id,
    )
    if snapshot is None:
        return JSONResponse(status_code=503, content={"outcome": "unavailable", "reason_code": "integrity_failure"})
    result = _assessment_summary(row, snapshot)
    result.update({
        "organization_id": str(row.organization_id), "project_id": row.project_id,
        "execution_id": str(snapshot.execution_id), "snapshot_id": str(snapshot.snapshot_id),
        "snapshot_digest": snapshot.snapshot_digest,
        "definition_digest": snapshot.definition_digest,
        "workspace_ids": tuple(snapshot.payload.get("workspace_ids", ())),
        "advisory": True,
    })
    return result


@router.get(PREFIX + "/assessments/{assessment_id}/findings", operation_id="list_cross_discipline_findings")
def list_findings(project_id: int, assessment_id: UUID, cursor: str | None = Query(None, max_length=2048), limit: int = Query(50, ge=1, le=100), application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    scope = {"kind": "findings", "organization_id": str(application.context.organization_id), "project_id": project_id, "assessment_id": str(assessment_id), "limit": limit}
    position = decode_cross_discipline_cursor(cursor, scope=scope)
    rows = application.repository.findings(
        assessment_id=assessment_id, organization_id=application.context.organization_id,
        project_id=project_id, limit=limit,
        after_ordinal=int(position[0]) if position else None,
    )
    visible = rows[:limit]
    items = tuple({
        "finding_id": str(row.id), "assessment_id": str(assessment_id),
        "ordinal": row.ordinal, "category": row.category, "subcode": row.subcode,
        "severity": row.severity, "fingerprint": row.fingerprint,
        "recurrence_key": row.recurrence_key, "current_state": "open",
        "allowed_actions": (), "provenance": row.payload.get("provenance", {}),
        "advisory": True,
    } for row in visible)
    next_cursor = encode_cross_discipline_cursor(scope=scope, position=[str(visible[-1].ordinal)]) if len(rows) > limit and visible else None
    return {"items": items, "next_cursor": next_cursor}


@router.get(PREFIX + "/assessments/{assessment_id}/findings/{finding_id}", operation_id="get_cross_discipline_finding")
def get_finding(project_id: int, assessment_id: UUID, finding_id: UUID, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    row = application.repository.finding(
        assessment_id=assessment_id, finding_id=finding_id,
        organization_id=application.context.organization_id, project_id=project_id,
    )
    if row is None:
        return _protected()
    current = application.repository.current_view(
        assessment_id=assessment_id, finding_id=finding_id,
        organization_id=application.context.organization_id, project_id=project_id,
    )
    return {
        "finding_id": str(row.id), "assessment_id": str(assessment_id),
        "ordinal": row.ordinal, "category": row.category, "subcode": row.subcode,
        "severity": row.severity, "fingerprint": row.fingerprint,
        "recurrence_key": row.recurrence_key,
        "current_state": current.current_state if current else "open",
        "allowed_actions": tuple(), "provenance": row.payload.get("provenance", {}),
        "advisory": True,
    }


@router.post(PREFIX + "/assessments/{assessment_id}/findings/{finding_id}/dispositions", operation_id="append_finding_disposition")
def append_disposition(project_id: int, assessment_id: UUID, finding_id: UUID, data: DispositionAppend, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    result = application.service.append_disposition(
        session_factory=application.session_factory,
        actor_id=application.context.user.id,
        actor_role=application.context.user.role,
        organization_id=application.context.organization_id,
        project_id=project_id, assessment_id=assessment_id,
        finding_id=finding_id, data=data,
    )
    status = 201 if result.get("outcome") == "success" else 404 if result.get("outcome") == "protected_not_found" else 409 if result.get("outcome") in {"version_conflict", "idempotency_conflict"} else 422 if result.get("outcome") == "invalid_request" else 503
    return JSONResponse(status_code=status, content=result)


@router.get(PREFIX + "/assessments/{assessment_id}/findings/{finding_id}/dispositions", operation_id="list_finding_dispositions")
def list_dispositions(project_id: int, assessment_id: UUID, finding_id: UUID, limit: int = Query(50, ge=1, le=100), application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    if application.repository.finding(assessment_id=assessment_id, finding_id=finding_id, organization_id=application.context.organization_id, project_id=project_id) is None:
        return _protected()
    rows = application.repository.dispositions(assessment_id=assessment_id, finding_id=finding_id, organization_id=application.context.organization_id, project_id=project_id, limit=limit)
    return {"items": tuple({"disposition_id": str(row.id), "sequence": row.sequence, "action": row.action, "resulting_view_state": row.resulting_view_state, "actor_id": row.actor_id, "rationale": row.rationale, "occurred_at": row.created_at, "view_version": row.resulting_view_version} for row in rows[:limit]), "next_cursor": None}


@router.get(PREFIX + "/assessments/{assessment_id}/lineage", operation_id="get_assessment_lineage")
def lineage(project_id: int, assessment_id: UUID, direction: str = Query("successors", pattern="^(successors|predecessors)$"), limit: int = Query(50, ge=1, le=100), application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    rows = application.repository.lineage(assessment_id=assessment_id, organization_id=application.context.organization_id, project_id=project_id, direction=direction, limit=limit)
    return {"items": tuple({"lineage_id": str(row.id), "kind": row.kind, "predecessor_id": str(row.predecessor_id), "successor_id": str(row.successor_id), "occurred_at": row.created_at} for row in rows[:limit]), "next_cursor": None}


@router.post(PREFIX + "/assessments/{assessment_id}/historical-verification", operation_id="verify_historical_assessment")
def verify_history(project_id: int, assessment_id: UUID, data: VerificationQuery, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    result = application.service.verify_historical(
        session_factory=application.session_factory,
        actor_id=application.context.user.id,
        actor_role=application.context.user.role,
        organization_id=application.context.organization_id,
        project_id=project_id, assessment_id=assessment_id, data=data,
    )
    if result.get("outcome") == "protected_not_found":
        return _protected()
    return result


@router.post(PREFIX + "/assessments/{assessment_id}/reassessments", operation_id="create_cross_discipline_reassessment")
def reassess(project_id: int, assessment_id: UUID, data: ReassessmentCreate, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None or _workspace_guard(application, project_id, data.scope.workspace_ids, mutate=True) is None:
        return _protected()
    result = application.service.create_foundation_assessment(
        session_factory=application.session_factory,
        actor_id=application.context.user.id,
        actor_role=application.context.user.role,
        organization_id=application.context.organization_id,
        project_id=project_id, data=data, operation="create_reassessment",
        predecessor_id=assessment_id,
        expected_predecessor_version=data.expected_predecessor_version,
        declare_supersession=data.declare_supersession,
    )
    status = 201 if result.get("outcome") == "success" else 404 if result.get("outcome") == "protected_not_found" else 409 if result.get("outcome") in {"version_conflict", "idempotency_conflict"} else 422 if result.get("outcome") == "invalid_request" else 503
    return JSONResponse(status_code=status, content=result)


@router.post(PREFIX + "/assessments/{assessment_id}/supersessions", operation_id="supersede_cross_discipline_assessment")
def supersede(project_id: int, assessment_id: UUID, data: SupersessionCreate, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None or _assessment_guard(application, project_id, data.successor_assessment_id) is None:
        return _protected()
    result = application.service.supersede_assessment(
        session_factory=application.session_factory,
        actor_id=application.context.user.id,
        actor_role=application.context.user.role,
        organization_id=application.context.organization_id,
        project_id=project_id, predecessor_id=assessment_id, data=data,
    )
    status = 201 if result.get("outcome") == "success" else 404 if result.get("outcome") == "protected_not_found" else 409 if result.get("outcome") in {"version_conflict", "idempotency_conflict"} else 422 if result.get("outcome") == "invalid_request" else 503
    return JSONResponse(status_code=status, content=result)


@router.get(PREFIX + "/assessments/{assessment_id}/findings/{finding_id}/dependency-explanation", operation_id="get_finding_dependency_explanation")
def dependency(project_id: int, assessment_id: UUID, finding_id: UUID, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    result = get_finding(project_id, assessment_id, finding_id, application)
    if isinstance(result, JSONResponse):
        return result
    return {"assessment_id": str(assessment_id), "finding_id": str(finding_id), "path": tuple(result["provenance"].get("path", ()))[:4], "advisory": True}


@router.post(PREFIX + "/assessments/{assessment_id}/findings/{finding_id}/potential-impact", operation_id="create_cross_discipline_potential_impact")
def potential_impact(project_id: int, assessment_id: UUID, finding_id: UUID, data: PotentialImpactRequest, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if data.assessment_id != assessment_id or data.finding_id != finding_id or _assessment_guard(application, project_id, assessment_id, mutate=True) is None:
        return _protected()
    result = application.service.handoff_potential_impact(
        session_factory=application.session_factory, actor_id=application.context.user.id,
        actor_role=application.context.user.role, organization_id=application.context.organization_id,
        project_id=project_id, assessment_id=assessment_id, finding_id=finding_id, data=data,
    )
    status = 201 if result.get("outcome") == "success" else 404 if result.get("outcome") == "protected_not_found" else 422 if result.get("outcome") == "invalid_request" else 503
    return JSONResponse(status_code=status, content=result)


@router.get(PREFIX + "/assessments/{assessment_id}/report-projection", operation_id="get_cross_discipline_report_projection")
def report_projection(project_id: int, assessment_id: UUID, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    root = _assessment_guard(application, project_id, assessment_id)
    if root is None:
        return _protected()
    snapshot = application.repository.snapshot(assessment_id=assessment_id, organization_id=application.context.organization_id, project_id=project_id)
    if snapshot is None:
        return JSONResponse(status_code=503, content={"outcome": "unavailable"})
    return {"assessment_id": str(assessment_id), "snapshot_digest": snapshot.snapshot_digest, "advisory": True}


@router.post(PREFIX + "/assessments/{assessment_id}/ai-explanation", operation_id="create_cross_discipline_ai_explanation")
def ai_explanation(project_id: int, assessment_id: UUID, data: AIExplanationRequest, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    rows = tuple(application.repository.finding(assessment_id=assessment_id, finding_id=item, organization_id=application.context.organization_id, project_id=project_id) for item in data.finding_ids)
    if any(row is None for row in rows):
        return _protected()
    return application.service.explain_findings(tuple({"category": row.category, "subcode": row.subcode} for row in rows))


@router.get(PREFIX + "/assessments/{assessment_id}/integrated-path", operation_id="get_cross_discipline_integrated_path")
def integrated_path(project_id: int, assessment_id: UUID, application: CrossDisciplineApplication = Depends(get_cross_discipline_application)):
    if _assessment_guard(application, project_id, assessment_id) is None:
        return _protected()
    return {"assessment_id": str(assessment_id), "path_id": "xdi.path.eic.change.v1", "advisory": True}

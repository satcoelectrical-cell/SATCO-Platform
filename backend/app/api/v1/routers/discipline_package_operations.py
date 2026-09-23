"""Authorization-first Electrical V1 package operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.schemas.discipline_package_operations import (
    PackageObjectCreateRequest,
    PackageCaptureCreateRequest,
    PackageDeliverableCreateRequest,
    PackageRelationshipCreateRequest,
    PackageRuleEvaluationRequest,
    PackageRuleEvaluationResponse,
    PackageContextBindingRequest,
    PackageContextBindingResponse,
    PackageEvidenceBindingRequest,
    PackageEvidenceBindingResponse,
    PackageContextEvaluationResponse,
    PackageReadinessResponse,
    PackageTransitionRequest,
)
from app.schemas.engineering_identifier import EngineeringIdentifierResponse
from app.schemas.engineering_object import EngineeringObjectResponse
from app.schemas.engineering_relationship import EngineeringRelationshipResponse
from app.schemas.engineering_experience_capture import EngineeringExperienceCaptureResponse
from app.dependencies.engineering_deliverable import (
    EngineeringDeliverableApplication,
    get_engineering_deliverable_application,
)
from app.services.electrical_package_service import (
    ElectricalPackageService,
    PackageConflict,
    PackageDeclarationMismatch,
    PackageProtectedNotFound,
    PackageUnavailable,
)
from app.services.instrumentation_package_service import InstrumentationPackageService
from app.services.control_automation_package_service import ControlAutomationPackageService
from app.services.package_declaration_binding_service import PackageDeclarationBindingService
from app.services.engineering_context_service import EngineeringContextService
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_object import EngineeringObject
from app.repositories.patch_052_operation_unit_of_work import Patch052OperationUnitOfWork
from app.services.patch_052_mutation_guard import (
    Patch052MutationProtected,
    lock_owner_mutation_scope,
)


router = APIRouter(prefix="/projects/{project_id}/discipline-packages", tags=["Discipline Package Operations"])
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyKey = Annotated[UUID, Header(alias="Idempotency-Key")]


def _service(declaration_id: str) -> ElectricalPackageService:
    if declaration_id.startswith("electrical."):
        return ElectricalPackageService(SessionLocal)
    if declaration_id.startswith("instrumentation."):
        return InstrumentationPackageService(SessionLocal)
    if declaration_id.startswith("control_automation."):
        return ControlAutomationPackageService(SessionLocal)
    raise PackageDeclarationMismatch()


def _workspace_binding_service(*, project_id, workspace_id, context):
    """Derive PackageKey only after owner-scope authorization."""
    try:
        with Patch052OperationUnitOfWork(SessionLocal) as uow:
            locked = lock_owner_mutation_scope(
                uow.session, actor_id=context.user.id,
                organization_id=context.organization_id,
                auth_version=context.user.auth_version, project_id=project_id,
                workspace_id=workspace_id,
            )
            package_key = locked.workspace.bound_package_key
    except Patch052MutationProtected as exc:
        raise PackageProtectedNotFound() from exc
    if package_key not in {"electrical", "instrumentation", "control_automation"}:
        raise PackageUnavailable()
    return PackageDeclarationBindingService(SessionLocal, package_key=package_key)


def _translate(call):
    try:
        return call()
    except PackageProtectedNotFound as exc:
        raise HTTPException(status_code=404, detail="PROTECTED_NOT_FOUND") from exc
    except PackageUnavailable as exc:
        raise HTTPException(status_code=503, detail="PACKAGE_UNAVAILABLE") from exc
    except PackageDeclarationMismatch as exc:
        raise HTTPException(status_code=422, detail="PACKAGE_DECLARATION_MISMATCH") from exc
    except PackageConflict as exc:
        raise HTTPException(status_code=409, detail="PACKAGE_OPERATION_CONFLICT") from exc


@router.post(
    "/workspaces/{workspace_id}/operations/objects",
    status_code=status.HTTP_201_CREATED,
)
def create_package_object(
    project_id: int,
    workspace_id: int,
    data: PackageObjectCreateRequest,
    correlation_id: CorrelationId,
    idempotency_key: IdempotencyKey,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    obj, identifier = _translate(lambda: _service(data.declaration_id).create_object(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version,
        project_id=project_id, workspace_id=workspace_id, data=data,
        correlation_id=correlation_id, idempotency_key=idempotency_key,
    ))
    return {"object": EngineeringObjectResponse.model_validate(obj), "primary_identifier": EngineeringIdentifierResponse.model_validate(identifier)}


@router.post(
    "/workspaces/{workspace_id}/operations/relationships",
    response_model=EngineeringRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_package_relationship(
    project_id: int,
    workspace_id: int,
    data: PackageRelationshipCreateRequest,
    correlation_id: CorrelationId,
    idempotency_key: IdempotencyKey,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _service(data.declaration_id).create_relationship(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version,
        project_id=project_id, workspace_id=workspace_id, data=data,
        correlation_id=correlation_id, idempotency_key=idempotency_key,
    ))


@router.post(
    "/workspaces/{workspace_id}/operations/captures",
    response_model=EngineeringExperienceCaptureResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_package_capture(
    project_id: int,
    workspace_id: int,
    data: PackageCaptureCreateRequest,
    correlation_id: CorrelationId,
    idempotency_key: IdempotencyKey,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _service(data.declaration_id).create_capture(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version,
        project_id=project_id, workspace_id=workspace_id, data=data,
        correlation_id=correlation_id, idempotency_key=idempotency_key,
    ))


@router.post("/workspaces/{workspace_id}/operations/deliverables")
def create_package_deliverable(
    project_id: int,
    workspace_id: int,
    data: PackageDeliverableCreateRequest,
    correlation_id: CorrelationId,
    idempotency_key: IdempotencyKey,
    application: EngineeringDeliverableApplication = Depends(get_engineering_deliverable_application),
):
    if data.workspace_id != workspace_id:
        raise HTTPException(status_code=422, detail="PACKAGE_DECLARATION_MISMATCH")
    creators = {
        "electrical": application.service.create_package_electrical,
        "instrumentation": application.service.create_package_instrumentation,
        "control_automation": application.service.create_package_control_automation,
    }
    package_key = data.declaration_id.partition(".")[0]
    creator = creators.get(package_key)
    if creator is None:
        raise HTTPException(status_code=422, detail="PACKAGE_DECLARATION_MISMATCH")
    result = creator(
        project_id=project_id, data=data, actor=application.actor,
        idempotency_key=idempotency_key, correlation_id=correlation_id,
    )
    outcome = getattr(result, "outcome", "success")
    code = {
        "protected_not_found": 404, "invalid_request": 422,
        "version_conflict": 409, "idempotency_conflict": 409,
        "unavailable": 503,
    }.get(outcome)
    if code is not None:
        raise HTTPException(status_code=code, detail=outcome.upper())
    return result


@router.post(
    "/workspaces/{workspace_id}/rule-evaluations",
    response_model=PackageRuleEvaluationResponse,
)
def evaluate_package_rule(
    project_id: int,
    workspace_id: int,
    data: PackageRuleEvaluationRequest,
    correlation_id: CorrelationId,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _service(data.hook_id).evaluate_rule(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version,
        project_id=project_id, workspace_id=workspace_id, data=data,
        correlation_id=correlation_id,
    ))


@router.post(
    "/workspaces/{workspace_id}/context-bindings",
    response_model=PackageContextBindingResponse,
    status_code=status.HTTP_201_CREATED,
)
def bind_package_context(
    project_id: int, workspace_id: int, data: PackageContextBindingRequest,
    correlation_id: CorrelationId, idempotency_key: IdempotencyKey,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _workspace_binding_service(
        project_id=project_id, workspace_id=workspace_id, context=context,
    ).bind_context(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version, project_id=project_id,
        workspace_id=workspace_id, data=data, correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    ))


@router.get("/workspaces/{workspace_id}/context-binding-options")
def context_binding_options(
    project_id: int,
    workspace_id: int,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    db: Session = Depends(get_db),
):
    """Bounded read-only selector for exact canonical Context subjects."""
    response = EngineeringContextService(db).list_for_scope(
        project_id=project_id,
        workspace_id=workspace_id,
        current_user=context.user,
        page=1,
        size=100,
        include_withdrawn=False,
    )
    contexts = response["items"]
    object_ids = tuple({
        subject["engineering_object_id"]
        for item in contexts
        for subject in item.get("subjects", [])
        if subject.get("subject_kind") == "engineering_object"
        and subject.get("engineering_object_id") is not None
    })
    object_labels = {}
    if object_ids:
        rows = db.execute(select(
            EngineeringObject.id,
            EngineeringObject.object_type,
            EngineeringIdentifier.display_value,
        ).outerjoin(
            EngineeringIdentifier,
            (EngineeringIdentifier.engineering_object_id == EngineeringObject.id)
            & (EngineeringIdentifier.lifecycle == "current")
            & (EngineeringIdentifier.primary_role == "primary"),
        ).where(
            EngineeringObject.id.in_(object_ids),
            EngineeringObject.organization_id == context.organization_id,
            EngineeringObject.project_id == project_id,
            EngineeringObject.workspace_id == workspace_id,
        ))
        object_labels = {
            object_id: display_value or str(object_type).replace("_", " ")
            for object_id, object_type, display_value in rows
        }
    items = []
    for item in contexts:
        context_label = item.get("purpose") or str(item["kind"]).replace("_", " ")
        context_key = str(item["context_key"]).replace("_", " ")
        for subject in item.get("subjects", []):
            subject_label = None
            if subject.get("subject_kind") == "workspace" and subject.get("workspace_id") == workspace_id:
                subject_label = "selected engineering workspace"
            elif subject.get("subject_kind") == "engineering_object":
                subject_label = object_labels.get(subject.get("engineering_object_id"))
            if not subject_label:
                continue
            items.append({
                "context_handle": item["id"],
                "subject_handle": subject["id"],
                "context_version": item["version"],
                "label": f"{context_label} — {subject_label} · {context_key}",
            })
            if len(items) == 100:
                return {"items": items}
    return {"items": items}


@router.post(
    "/workspaces/{workspace_id}/evidence-bindings",
    response_model=PackageEvidenceBindingResponse,
    status_code=status.HTTP_201_CREATED,
)
def bind_package_evidence(
    project_id: int, workspace_id: int, data: PackageEvidenceBindingRequest,
    correlation_id: CorrelationId, idempotency_key: IdempotencyKey,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _workspace_binding_service(
        project_id=project_id, workspace_id=workspace_id, context=context,
    ).bind_evidence(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version, project_id=project_id,
        workspace_id=workspace_id, data=data, correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    ))


@router.get(
    "/workspaces/{workspace_id}/context-evaluation",
    response_model=PackageContextEvaluationResponse,
)
def evaluate_package_context(
    project_id: int, workspace_id: int,
    expected_configuration_revision: int = Query(gt=0),
    object_ids: list[UUID] = Query(default=[]),
    correlation_id: CorrelationId = None,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _workspace_binding_service(
        project_id=project_id, workspace_id=workspace_id, context=context,
    ).evaluate_context(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version, project_id=project_id,
        workspace_id=workspace_id,
        expected_configuration_revision=expected_configuration_revision,
        object_ids=object_ids, correlation_id=correlation_id,
    ))


@router.get(
    "/workspaces/{workspace_id}/deliverables/{deliverable_id}/revisions/{revision_id}/readiness",
    response_model=PackageReadinessResponse,
)
def package_deliverable_readiness(
    project_id: int, workspace_id: int, deliverable_id: UUID, revision_id: UUID,
    expected_configuration_revision: int = Query(gt=0),
    object_ids: list[UUID] = Query(default=[]),
    evidence_ids: list[UUID] = Query(default=[]),
    correlation_id: CorrelationId = None,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _workspace_binding_service(
        project_id=project_id, workspace_id=workspace_id, context=context,
    ).readiness(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version, project_id=project_id,
        workspace_id=workspace_id, deliverable_id=deliverable_id,
        revision_id=revision_id,
        expected_configuration_revision=expected_configuration_revision,
        object_ids=object_ids, evidence_ids=evidence_ids,
        correlation_id=correlation_id,
    ))


@router.post(
    "/workspaces/{workspace_id}/deliverables/{deliverable_id}/revisions/{revision_id}/package-transition",
    response_model=PackageReadinessResponse,
)
def package_deliverable_transition(
    project_id: int, workspace_id: int, deliverable_id: UUID, revision_id: UUID,
    data: PackageTransitionRequest, correlation_id: CorrelationId,
    idempotency_key: IdempotencyKey,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    return _translate(lambda: _workspace_binding_service(
        project_id=project_id, workspace_id=workspace_id, context=context,
    ).transition(
        actor_id=context.user.id, organization_id=context.organization_id,
        auth_version=context.user.auth_version, project_id=project_id,
        workspace_id=workspace_id, deliverable_id=deliverable_id,
        revision_id=revision_id, data=data, correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    ))

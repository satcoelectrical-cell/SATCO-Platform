"""Thin, bounded Batch-4 HTTP surface for trusted package configuration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.discipline_package import (
    decode_discipline_package_cursor,
    encode_discipline_package_cursor,
    get_discipline_package_configuration_service,
)
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.models.discipline_package import (
    OrganizationPackageConfigurationHead, OrganizationPackageSelection,
    PackageConfigurationAuditEvent, PackageDescriptor,
    ProjectPackageConfigurationHead, ProjectPackageConfigurationRevision,
    ProjectPackageConfigurationSelection, RegistryMembership, RegistryProfileMembership,
    RegistryRelease,
)
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.schemas.discipline_package import (
    CompatibilityPreflightInput, OrganizationConfigurationReplaceInput,
    ProjectConfigurationRemoveInput, ProjectConfigurationReplaceInput,
)
from app.services.discipline_package_configuration_service import (
    DisciplinePackageConfigurationService, ExactPackageSelection,
    GuardedRequestIdentity, OrganizationConfigurationRequest, ProjectConfigurationRequest,
)
from app.services.discipline_package_service import evaluate_persisted_exact_compatibility
from app.services.engineering_workspace_service import EngineeringWorkspaceService


router = APIRouter(tags=["Discipline Packages"])

_AUDIT_KNOWN_TIME = "KNOWN_TIME"
_AUDIT_HISTORICAL_UNKNOWN_TIME = "HISTORICAL_UNKNOWN_TIME"


def _identity(context: AuthenticatedOrganizationContext, correlation_id: UUID) -> GuardedRequestIdentity:
    return GuardedRequestIdentity(
        context.user.id, context.organization_id, context.user.auth_version,
        correlation_id,
    )


def _admin(context: AuthenticatedOrganizationContext) -> None:
    if context.user.role != "admin":
        raise HTTPException(status_code=403, detail="CONFIGURATION_ADMIN_REQUIRED")


def _project(db: Session, project_id: int, context: AuthenticatedOrganizationContext, *, mutate: bool = False) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == context.organization_id))
    if project is None:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
    permitted = context.user.role == "admin" or project.owner_id == context.user.id or (
        not mutate and project.primary_assignee_id == context.user.id
    )
    if not permitted:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
    return project


def _current_registry(db: Session) -> RegistryRelease:
    registry = db.scalar(select(RegistryRelease).where(RegistryRelease.is_current.is_(True)))
    if registry is None:
        raise HTTPException(status_code=503, detail="REGISTRY_UNAVAILABLE")
    return registry


def _exact_selections(db: Session, registry: RegistryRelease, selections) -> tuple[ExactPackageSelection, ...]:
    resolved: list[ExactPackageSelection] = []
    for item in selections:
        descriptor = db.get(PackageDescriptor, (item.package_key, item.package_version))
        membership = db.get(RegistryMembership, (registry.registry_digest, item.package_key, item.package_version))
        if descriptor is None or membership is None or membership.standing != "executable_supported":
            raise HTTPException(status_code=409, detail="PACKAGE_VERSION_UNAVAILABLE")
        resolved.append(ExactPackageSelection(item.package_key, item.package_version, descriptor.descriptor_digest))
    return tuple(resolved)


def _profile_digest(db: Session, registry: RegistryRelease, profile_id: str) -> str:
    row = db.scalar(select(RegistryProfileMembership).where(
        RegistryProfileMembership.registry_digest == registry.registry_digest,
        RegistryProfileMembership.profile_id == profile_id,
    ))
    if row is None:
        raise HTTPException(status_code=409, detail="INVALID_PACKAGE_CONFIGURATION")
    return row.profile_digest


def _selection_output(rows) -> list[dict[str, str]]:
    return [{"package_key": row.package_key, "package_version": row.package_version, "descriptor_digest": row.descriptor_digest} for row in rows]


def _audit_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION") from None
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timedelta(0)
        or parsed.isoformat() != value
    ):
        raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION")
    return parsed


def _audit_items(rows) -> list[dict[str, object]]:
    return [
        {
            "event_id": row.event_id,
            "project_id": row.project_id,
            "workspace_id": row.workspace_id,
            "category": row.category,
            "action": row.action,
            # Null is the explicit historical-unknown-time representation.
            "occurred_at": row.occurred_at,
        }
        for row in rows
    ]


def _known_time_audit_ordering():
    """The accepted physical order for every known-time Audit query shape."""

    return (
        PackageConfigurationAuditEvent.occurred_at.desc().nulls_last(),
        PackageConfigurationAuditEvent.event_id.desc(),
    )


@router.get("/discipline-packages/supported")
def supported_packages(
    cursor: str | None = Query(None, max_length=2048),
    limit: int = Query(50, ge=1, le=50),
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    db: Session = Depends(get_db),
):
    registry = _current_registry(db)
    scope = {"kind": "supported", "organization_id": str(context.organization_id), "registry_digest": registry.registry_digest, "limit": limit}
    position = decode_discipline_package_cursor(cursor, scope=scope)
    stmt = select(PackageDescriptor, RegistryMembership.standing).join(RegistryMembership).where(
        RegistryMembership.registry_digest == registry.registry_digest,
        RegistryMembership.standing == "executable_supported",
    )
    if position is not None and len(position) == 2:
        stmt = stmt.where(or_(
            PackageDescriptor.package_key > position[0],
            and_(PackageDescriptor.package_key == position[0], PackageDescriptor.package_version > position[1]),
        ))
    elif position is not None:
        raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION")
    rows = list(db.execute(stmt.order_by(PackageDescriptor.package_key, PackageDescriptor.package_version).limit(limit + 1)))
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_discipline_package_cursor(scope=scope, position=[rows[-1][0].package_key, rows[-1][0].package_version]) if has_more and rows else None
    return {"registry_digest": registry.registry_digest, "items": [
        {"package_key": descriptor.package_key, "package_version": descriptor.package_version,
         "primary_discipline_id": descriptor.primary_discipline_id, "standing": standing,
         "descriptor_digest": descriptor.descriptor_digest}
        for descriptor, standing in rows
    ], "next_cursor": next_cursor}


@router.get("/organizations/current/discipline-package-configuration")
def organization_configuration(context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)):
    _admin(context); registry = _current_registry(db)
    head = db.get(OrganizationPackageConfigurationHead, context.organization_id)
    rows = list(db.scalars(select(OrganizationPackageSelection).where(OrganizationPackageSelection.organization_id == context.organization_id).order_by(OrganizationPackageSelection.package_key, OrganizationPackageSelection.package_version)))
    return {"organization_id": context.organization_id, "configuration_version": 0 if head is None else head.configuration_version,
            "enabled_selections": [{"package_key": r.package_key, "package_version": r.package_version} for r in rows if r.state == "enabled"],
            "disabled_selections": [{"package_key": r.package_key, "package_version": r.package_version} for r in rows if r.state == "disabled"],
            "registry_digest": registry.registry_digest, "updated_at": None}


@router.put("/organizations/current/discipline-package-configuration")
def replace_organization_configuration(data: OrganizationConfigurationReplaceInput, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db), service: DisciplinePackageConfigurationService = Depends(get_discipline_package_configuration_service), correlation_id: UUID = Header(alias="X-Correlation-ID")):
    _admin(context); registry = _current_registry(db)
    try:
        version = service.replace_organization_configuration(_identity(context, correlation_id), OrganizationConfigurationRequest(data.expected_configuration_version, _exact_selections(db, registry, data.enabled_selections), data.rationale))
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail="CONFIGURATION_ADMIN_REQUIRED")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="INVALID_PACKAGE_CONFIGURATION") from exc
    return {"configuration_version": version, "registry_digest": registry.registry_digest}


@router.get("/organizations/current/discipline-package-configuration/audit")
def organization_configuration_audit(cursor: str | None = Query(None, max_length=2048), limit: int = Query(50, ge=1, le=100), category: str | None = None, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)):
    _admin(context)
    scope = {"kind": "organization_audit", "organization_id": str(context.organization_id), "category": category, "limit": limit}
    position = decode_discipline_package_cursor(cursor, scope=scope)
    stmt = select(PackageConfigurationAuditEvent).where(PackageConfigurationAuditEvent.organization_id == context.organization_id)
    if category is not None:
        stmt = stmt.where(PackageConfigurationAuditEvent.category == category)

    segment = None if position is None else position[0] if position else None
    if segment is None or segment == _AUDIT_KNOWN_TIME:
        known = stmt.where(PackageConfigurationAuditEvent.occurred_at.is_not(None))
        if position is not None:
            if len(position) != 3:
                raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION")
            occurred_at = _audit_timestamp(position[1])
            try:
                event_id = UUID(position[2])
            except ValueError:
                raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION") from None
            known = known.where(or_(
                PackageConfigurationAuditEvent.occurred_at < occurred_at,
                and_(
                    PackageConfigurationAuditEvent.occurred_at == occurred_at,
                    PackageConfigurationAuditEvent.event_id < event_id,
                ),
            ))
        rows = list(db.scalars(known.order_by(*_known_time_audit_ordering()).limit(limit + 1)))
        has_more_known = len(rows) > limit
        rows = rows[:limit]
        if rows:
            if has_more_known:
                last = rows[-1]
                next_cursor = encode_discipline_package_cursor(
                    scope=scope,
                    position=[_AUDIT_KNOWN_TIME, last.occurred_at.isoformat(), str(last.event_id)],
                )
            else:
                legacy_check = select(PackageConfigurationAuditEvent.event_id).where(
                    PackageConfigurationAuditEvent.organization_id == context.organization_id,
                    PackageConfigurationAuditEvent.occurred_at.is_(None),
                )
                if category is not None:
                    legacy_check = legacy_check.where(
                        PackageConfigurationAuditEvent.category == category
                    )
                legacy_exists = db.scalar(legacy_check.limit(1))
                next_cursor = (
                    encode_discipline_package_cursor(
                        scope=scope, position=[_AUDIT_HISTORICAL_UNKNOWN_TIME]
                    )
                    if legacy_exists is not None else None
                )
            return {"items": _audit_items(rows), "next_cursor": next_cursor}
        if position is not None:
            # A known-time continuation cannot silently fall through to legacy
            # when its state is malformed or stale; only an explicit boundary
            # cursor may enter the historical-unknown segment.
            return {"items": [], "next_cursor": None}

    if position is not None and (not position or position[0] != _AUDIT_HISTORICAL_UNKNOWN_TIME):
        raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION")
    legacy = stmt.where(PackageConfigurationAuditEvent.occurred_at.is_(None))
    if position is not None:
        if len(position) not in {1, 2}:
            raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION")
        if len(position) == 2:
            try:
                legacy = legacy.where(PackageConfigurationAuditEvent.event_id < UUID(position[1]))
            except ValueError:
                raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION") from None
    rows = list(db.scalars(legacy.order_by(
        PackageConfigurationAuditEvent.event_id.desc(),
    ).limit(limit + 1)))
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = (
        encode_discipline_package_cursor(
            scope=scope,
            position=[_AUDIT_HISTORICAL_UNKNOWN_TIME, str(rows[-1].event_id)],
        )
        if has_more and rows else None
    )
    return {"items": _audit_items(rows), "next_cursor": next_cursor}


def _project_configuration(db: Session, project: Project) -> dict:
    head = db.get(ProjectPackageConfigurationHead, project.id)
    if head is None:
        return {"state": "NOT_CONFIGURED", "project_id": project.id, "organization_id": project.organization_id, "configuration_version": 0, "selections": []}
    revision = db.get(ProjectPackageConfigurationRevision, (project.id, head.current_revision))
    rows = list(db.scalars(select(ProjectPackageConfigurationSelection).where(ProjectPackageConfigurationSelection.project_id == project.id, ProjectPackageConfigurationSelection.configuration_revision == head.current_revision).order_by(ProjectPackageConfigurationSelection.package_key)))
    return {"state": "CONFIGURED", "project_id": project.id, "organization_id": project.organization_id, "configuration_version": head.configuration_version, "configuration_revision": head.current_revision, "profile_id": revision.profile_id, "profile_digest": revision.profile_digest, "registry_digest": revision.observed_registry_digest, "selections": _selection_output(rows), "created_at": None}


@router.get("/projects/{project_id}/discipline-package-configuration")
def get_project_configuration(project_id: int, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)):
    return _project_configuration(db, _project(db, project_id, context))


@router.put("/projects/{project_id}/discipline-package-configuration")
def replace_project_configuration(project_id: int, data: ProjectConfigurationReplaceInput, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db), service: DisciplinePackageConfigurationService = Depends(get_discipline_package_configuration_service), correlation_id: UUID = Header(alias="X-Correlation-ID")):
    _project(db, project_id, context, mutate=True); registry = _current_registry(db)
    try:
        version = service.replace_project_configuration(_identity(context, correlation_id), project_id, ProjectConfigurationRequest(data.expected_configuration_version, data.profile_id, _profile_digest(db, registry, data.profile_id), _exact_selections(db, registry, data.selections), data.rationale))
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="INVALID_PACKAGE_CONFIGURATION") from exc
    return {**_project_configuration(db, _project(db, project_id, context)), "configuration_version": version}


@router.delete("/projects/{project_id}/discipline-package-configuration")
def remove_project_configuration(project_id: int, data: ProjectConfigurationRemoveInput, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db), service: DisciplinePackageConfigurationService = Depends(get_discipline_package_configuration_service), correlation_id: UUID = Header(alias="X-Correlation-ID")):
    _project(db, project_id, context, mutate=True)
    try:
        service.remove_project_configuration(_identity(context, correlation_id), project_id, expected_configuration_version=data.expected_configuration_version, rationale=data.rationale)
    except PermissionError:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="INVALID_PACKAGE_CONFIGURATION") from exc
    return _project_configuration(db, _project(db, project_id, context))


@router.post("/projects/{project_id}/discipline-package-configuration/preflight")
def preflight_project_configuration(project_id: int, data: CompatibilityPreflightInput, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)):
    _project(db, project_id, context, mutate=True); registry = _current_registry(db)
    selections = _exact_selections(db, registry, data.selections); profile_digest = _profile_digest(db, registry, data.profile_id)
    enabled = frozenset(db.scalars(select(OrganizationPackageSelection.package_key).where(OrganizationPackageSelection.organization_id == context.organization_id, OrganizationPackageSelection.state == "enabled")))
    compatible = evaluate_persisted_exact_compatibility(db, registry, profile_id=data.profile_id, profile_digest=profile_digest, selections=tuple((s.package_key, s.package_version, s.descriptor_digest) for s in selections), enabled_package_keys=enabled)
    return {"decision": "COMPATIBLE" if compatible else "INCOMPATIBLE", "normalized_selections": [{"package_key": s.package_key, "package_version": s.package_version, "descriptor_digest": s.descriptor_digest} for s in selections], "registry_digest": registry.registry_digest if compatible else None, "profile_digest": profile_digest if compatible else None, "reason_codes": [] if compatible else ["PROFILE_NOT_ALLOWED"]}


@router.get("/projects/{project_id}/effective-discipline-packages")
def effective_discipline_packages(project_id: int, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)):
    project = _project(db, project_id, context); configuration = _project_configuration(db, project)
    registry = _current_registry(db)
    selected = {item["package_key"]: item for item in configuration["selections"]}
    items = []
    for discipline_id, display_name, package_key in (("electrical", "Electrical", "electrical"), ("instrumentation", "Instrumentation", "instrumentation"), ("control_automation", "Control & Automation", "control_automation"), ("mechanical", "Mechanical", None), ("civil", "Civil", None), ("process", "Process", None)):
        item = selected.get(package_key) if package_key else None
        membership = None if item is None else db.get(RegistryMembership, (
            registry.registry_digest, item["package_key"], item["package_version"],
        ))
        executable = membership is not None and membership.standing == "executable_supported"
        historical = membership is not None and membership.standing == "historical_read_only"
        availability = "OPERATIONAL_AVAILABLE" if executable else "HISTORICAL_ONLY" if historical else "FUTURE_UNAVAILABLE"
        items.append({"discipline_id": discipline_id, "display_name": display_name, "availability": availability, "allowed_actions": ["create_workspace"] if executable or package_key is None else [], "binding_state": "OPERATIONAL_PACKAGE_BOUND" if item is not None else "FUTURE_UNAVAILABLE_UNBOUND", "package_key": package_key if item is not None else None, "package_version": None if item is None else item["package_version"], "descriptor_digest": None if item is None else item["descriptor_digest"], "project_configuration_revision": configuration.get("configuration_revision") if item is not None else None})
    return {"project_id": project_id, "items": items}


@router.get("/workspaces/{workspace_id}/package-applicability")
def workspace_package_applicability(workspace_id: int, context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)):
    # Reuse the established Workspace visibility predicate, which includes
    # authorized Workspace members and deliberately does not disclose a
    # Project merely because its Workspace ID was guessed.
    EngineeringWorkspaceService(db, context.organization_id).get(workspace_id, context.user)
    workspace = db.scalar(select(EngineeringWorkspace).join(Project).where(
        EngineeringWorkspace.id == workspace_id,
        Project.organization_id == context.organization_id,
    ))
    if workspace is None:
        raise HTTPException(status_code=404, detail="WORKSPACE_NOT_FOUND")
    selection = None
    if workspace.bound_package_key is not None and workspace.bound_project_configuration_revision is not None:
        selection = db.get(ProjectPackageConfigurationSelection, (
            workspace.project_id,
            workspace.bound_project_configuration_revision,
            workspace.bound_package_key,
        ))
    descriptor = None if selection is None else db.get(PackageDescriptor, (selection.package_key, selection.package_version))
    current_release = None if descriptor is None else db.scalar(
        select(RegistryRelease).where(RegistryRelease.is_current.is_(True))
    )
    membership = None if descriptor is None or current_release is None else db.get(
        RegistryMembership,
        (current_release.registry_digest, descriptor.package_key, descriptor.package_version),
    )
    return {"workspace_id": workspace.id, "project_id": workspace.project_id, "legacy_discipline": workspace.discipline, "canonical_discipline_id": workspace.canonical_discipline_id, "binding_state": workspace.package_binding_state, "package_key": workspace.bound_package_key, "package_version": None if descriptor is None else descriptor.package_version, "descriptor_digest": None if descriptor is None else descriptor.descriptor_digest, "project_configuration_revision": workspace.bound_project_configuration_revision, "effective_standing": None if membership is None else membership.standing}
